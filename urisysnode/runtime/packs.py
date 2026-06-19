"""Pack loading and management for urisys-node runtime."""

from __future__ import annotations

import importlib
import sys
from typing import Any


from urisysnode.pack_resolver import (
    CORE_PACKS,
    PACK_MODULES,
    auto_install_enabled,
    ensure_pack_pypi,
    pack_importable,
)


def _bootstrap_worker_packs(rt: Any) -> None:
    """Spawn the packs listed in URISYS_NODE_WORKER_PACKS as out-of-process
    workers and wire their routes to forward into this router. Existing workers
    from a previous run are re-attached instead of re-spawned."""
    import os

    from urisysnode.supervisor import PackSupervisor

    raw = os.environ.get("URISYS_NODE_WORKER_PACKS", "").strip()
    worker_packs = [p.strip() for p in raw.split(",") if p.strip()]
    if not worker_packs:
        return

    sup = PackSupervisor(rt)
    rt._supervisor = sup  # type: ignore[attr-defined]
    sup.restore()
    for pack in worker_packs:
        if pack in sup.workers and sup.workers[pack].alive():
            continue
        sup.spawn(pack=pack, install=not pack_importable(pack))
    sup.start_monitor()


def load_pack_into_runtime(
    runtime: Any,
    pack: str,
    *,
    install: bool = False,
    specs: list[str] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Hot-load a capability pack. With install=True or auto-install, pip install first."""
    from urisysnode.runtime.builder import _pack_modules, _register_pack

    pack = (pack or "").strip()
    if not pack:
        return {"ok": False, "error": "pack name is required"}
    loaded = getattr(runtime, "_loaded_packs", None)
    if loaded is None:
        loaded = set()
        runtime._loaded_packs = loaded  # type: ignore[attr-defined]
    pack_routes: dict[str, set[str]] = getattr(runtime, "_pack_route_patterns", {})
    if not hasattr(runtime, "_pack_route_patterns"):
        runtime._pack_route_patterns = pack_routes  # type: ignore[attr-defined]
    if pack in loaded and not force:
        return {"ok": True, "pack": pack, "loaded": True, "already_loaded": True, "new_routes": []}

    pip_result = None
    if install or (auto_install_enabled() and not pack_importable(pack)):
        pip_result = ensure_pack_pypi(pack, install=True, specs=specs)
        if not pip_result.get("ok"):
            return {"ok": False, "pack": pack, "loaded": False, "pip": pip_result}
        if pip_result.get("ok") and not pip_result.get("skipped"):
            importlib.invalidate_caches()

    if pack in loaded and force:
        drop = pack_routes.get(pack, set())
        if drop:
            runtime.routes = [r for r in runtime.routes if r.pattern not in drop]
        loaded.discard(pack)
        pack_routes.pop(pack, None)
        from urisysnode import pack_resolver as pr

        importlib.reload(pr)
        module_name = pr.PACK_MODULES.get(pack, "").split(".", 1)[0]
        if module_name and module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        importlib.invalidate_caches()

    before = {r.pattern for r in runtime.routes}
    try:
        ok = _register_pack(runtime, pack, try_install=False, pack_modules=_pack_modules())
    except ModuleNotFoundError as exc:
        return {"ok": False, "pack": pack, "loaded": False, "error": str(exc), "pip": pip_result}
    except Exception as exc:
        return {"ok": False, "pack": pack, "loaded": False, "error": str(exc), "pip": pip_result}
    if ok:
        loaded.add(pack)
        added = {r.pattern for r in runtime.routes} - before
        if added:
            pack_routes[pack] = added
    new_routes = sorted({r.pattern for r in runtime.routes} - before)
    out: dict[str, Any] = {"ok": bool(ok), "pack": pack, "loaded": bool(ok), "new_routes": new_routes}
    if not ok:
        mod = PACK_MODULES.get(pack, pack)
        out["error"] = out.get("error") or f"failed to import/register pack module {mod!r}"
    if pip_result:
        out["pip"] = pip_result
    return out


def isolation_mode(context: dict[str, Any] | None = None) -> str:
    """Resolve the process-isolation policy for a URI call.

    Returns one of ``persistent`` (default), ``ephemeral`` or ``off``. A non-core
    pack is, by default, served from its own worker process so its crash cannot
    take the node router (and the session) down. Override per-call via
    ``context['isolation']`` or globally via ``URISYS_NODE_ISOLATION``.

    - ``persistent``: spawn one long-lived worker per pack (auto-respawned).
    - ``ephemeral``:  spawn a throwaway worker for each call, then tear it down.
    - ``off``:        load the pack in-process in the router (legacy behaviour).
    """
    import os as _os

    ctx = context or {}
    val = str(ctx.get("isolation") or _os.environ.get("URISYS_NODE_ISOLATION") or "persistent").strip().lower()
    if val in ("off", "none", "inprocess", "in-process", "0", "false", "no"):
        return "off"
    if val in ("ephemeral", "oneshot", "one-shot", "per-call", "percall"):
        return "ephemeral"
    return "persistent"


def get_supervisor(runtime: Any) -> Any:
    """Return the runtime's pack-worker supervisor, creating (and starting the
    liveness monitor for) it on first use. Single source of truth shared by the
    node command handlers and the isolated lazy-load path in :func:`call_uri`."""
    sup = getattr(runtime, "_supervisor", None)
    if sup is None:
        from urisysnode.supervisor import PackSupervisor

        sup = PackSupervisor(runtime)
        runtime._supervisor = sup  # type: ignore[attr-defined]
        sup.start_monitor()
    return sup


def ensure_isolated_pack(
    runtime: Any, uri: str, payload: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any] | None:
    """Ensure the pack for ``uri`` runs out-of-process, per the isolation policy.

    Returns:
      * ``None``    — isolation does not apply (mode off, core/unknown pack, or the
                      pack is already loaded/wired); the caller proceeds in-process.
      * a sentinel  — for ``persistent`` mode once a worker is spawned and its
                      forward routes are wired; the caller should re-dispatch via
                      ``runtime.call`` (which now forwards to the worker).
      * a full call result — for ``ephemeral`` mode the call already ran in the
                      throwaway worker; the caller returns this verbatim.
    """
    import warnings as _warnings

    from urisysnode.pack_resolver import pack_for_scheme, scheme_for_uri

    mode = isolation_mode(context)
    if mode == "off":
        return None
    scheme = scheme_for_uri(uri)
    pack = pack_for_scheme(scheme)
    if not pack or pack in CORE_PACKS:
        return None
    loaded = getattr(runtime, "_loaded_packs", set()) or set()
    if pack in loaded or scheme in loaded:
        return None
    sup = get_supervisor(runtime)
    install = not pack_importable(pack)
    if mode == "ephemeral":
        return {"ephemeral_result": sup.call_ephemeral(
            uri, payload, context, pack=pack, install=install,
        )}
    spawned = sup.spawn(pack=pack, install=install)
    if spawned.get("ok"):
        loaded.add(pack)
        return {"isolated": True, "worker": spawned}
    _warnings.warn(
        f"isolated spawn for pack {pack!r} failed ({spawned.get('error')}); "
        "falling back to in-process load",
        stacklevel=2,
    )
    return None


def ensure_pack_for_uri(runtime: Any, uri: str) -> dict[str, Any] | None:
    """If URI scheme maps to an unloaded pack, install (PyPI) and register it."""
    from urisysnode.pack_resolver import pack_for_scheme, scheme_for_uri

    scheme = scheme_for_uri(uri)
    pack = pack_for_scheme(scheme)
    if not pack:
        return None
    loaded = getattr(runtime, "_loaded_packs", set())
    if pack in loaded:
        return None
    return load_pack_into_runtime(runtime, pack, install=not pack_importable(pack))


def apply_host_trust(runtime: Any, uri: str, context: dict[str, Any]) -> dict[str, Any]:
    """Auto-approve trusted operations based on the node profile's approval policy.

    The runtime's gate (``Route.approval == "required"`` + ``side_effects``) blocks any
    command unless the caller supplies ``context["approved"]``. On a trusted desktop slave
    that is supposed to "grant all rights to the host", we let the *profile* decide instead
    of the caller: when ``policy.require_approval_for`` is present in node-profile.json, the
    node auto-approves every operation that does NOT match one of those glob patterns
    (``[]`` = full trust). A profile WITHOUT that key keeps the safe default — the caller
    must still pass ``approved`` — so this never silently loosens an unconfigured node.
    """
    import fnmatch

    policy = (getattr(runtime, "config", None) or {}).get("policy") or {}
    if "require_approval_for" not in policy:
        return context
    ctx = dict(context or {})
    if ctx.get("approved"):
        return ctx
    try:
        route, _ = runtime.resolve(uri)
        operation = route.operation
    except Exception:
        return ctx  # unresolved (route_not_found etc.) — leave it to runtime.call
    gated = policy.get("require_approval_for") or []
    if not any(fnmatch.fnmatch(operation, pattern) for pattern in gated):
        ctx["approved"] = True
    return ctx
