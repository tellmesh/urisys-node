from __future__ import annotations

import importlib
import json
import os
import sys
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .identity import default_events_path, health_payload, load_identity
from .pack_resolver import (
    CORE_PACKS,
    PACK_MODULES,
    auto_install_enabled,
    ensure_pack_pypi,
    ensure_real_deps,
    pack_for_scheme,
    pack_importable,
    scheme_for_uri,
)
from .runtime import Runtime, load_json


def _extend_pack_paths() -> None:
    root = Path(__file__).resolve().parents[3]
    for rel in ("../urikvm-docker/packages/python", "../urirdp-docker/packages/python"):
        path = (root / rel).resolve()
        if path.is_dir() and str(path) not in sys.path:
            sys.path.insert(0, str(path))


def _register_pack(rt: Runtime, pack: str, *, try_install: bool = False) -> bool:
    """Import and register one capability pack. Optional packs that are not
    installed are skipped with a warning unless try_install triggers PyPI."""
    module_name = PACK_MODULES.get(pack)
    if module_name is None:
        warnings.warn(f"Unknown urisys-node pack '{pack}' — skipping.", stacklevel=2)
        return False
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        top = module_name.split(".", 1)[0]
        if exc.name not in (module_name, top):
            raise
        if pack in CORE_PACKS:
            raise
        if try_install and auto_install_enabled():
            pip_result = ensure_pack_pypi(pack, install=True)
            if pip_result.get("ok"):
                importlib.invalidate_caches()
                module = importlib.import_module(module_name)
            else:
                warnings.warn(
                    f"Skipping urisys-node pack '{pack}': pip install failed ({pip_result.get('error')})",
                    stacklevel=2,
                )
                return False
        else:
            warnings.warn(
                f"Skipping urisys-node pack '{pack}': module '{module_name}' is not "
                f"installed (pip install {top} or enable URISYS_NODE_AUTO_INSTALL=1).",
                stacklevel=2,
            )
            return False
    module.register(rt)
    return True


def build_runtime(config_path: str | None = None) -> Runtime:
    _extend_pack_paths()
    from urisysnode.env import load_urisys_env

    load_urisys_env()
    config_file = config_path or os.environ.get("URISYS_NODE_CONFIG", "config/node-profile.json")
    config = load_json(config_file) if Path(config_file).exists() else {}
    rt = Runtime(events_path=default_events_path(), config=config)

    # Minimal boot: node + screen + shell (bundled). kvm/him/ocr/llm on first URI or shell://pip.
    packs = os.environ.get("URISYS_NODE_PACKS", "node,screen,shell").split(",")
    packs = [p.strip() for p in packs if p.strip()]

    rt._loaded_packs = set()  # type: ignore[attr-defined]
    for pack in packs:
        if _register_pack(rt, pack, try_install=auto_install_enabled()):
            rt._loaded_packs.add(pack)  # type: ignore[attr-defined]

    try:
        from urisysnode.forward_config import load_forward_entries, wire_forward_packs

        forwards = load_forward_entries(config=config)
        if forwards:
            rt.config["forwards"] = forwards
            wire_forward_packs(rt, forwards)
    except Exception as exc:
        warnings.warn(f"forward pack wiring skipped: {exc}", stacklevel=2)

    try:
        from urisysnode.forward_config import (
            load_release_forward_entries,
            wire_release_forward_packs,
        )

        release_forwards = load_release_forward_entries(config=config)
        if release_forwards:
            rt.config["release_forwards"] = release_forwards
            for result in wire_release_forward_packs(rt, release_forwards):
                if not result.get("ok"):
                    warnings.warn(
                        f"release forward {result.get('contract_id')}@{result.get('version')} "
                        f"skipped at stage '{result.get('stage')}': {result.get('error')}",
                        stacklevel=2,
                    )
    except Exception as exc:
        warnings.warn(f"release forward wiring skipped: {exc}", stacklevel=2)

    return rt


def load_pack_into_runtime(
    runtime: Runtime,
    pack: str,
    *,
    install: bool = False,
    specs: list[str] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Hot-load a capability pack. With install=True or auto-install, pip install first."""
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

    if pack in loaded and force:
        drop = pack_routes.get(pack, set())
        if drop:
            runtime.routes = [r for r in runtime.routes if r.pattern not in drop]
        loaded.discard(pack)
        pack_routes.pop(pack, None)
        module_name = PACK_MODULES.get(pack, "").split(".", 1)[0]
        if module_name and module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        importlib.invalidate_caches()

    before = {r.pattern for r in runtime.routes}
    try:
        ok = _register_pack(runtime, pack, try_install=False)
    except ModuleNotFoundError as exc:
        return {"ok": False, "pack": pack, "loaded": False, "error": str(exc), "pip": pip_result}
    if ok:
        loaded.add(pack)
        added = {r.pattern for r in runtime.routes} - before
        if added:
            pack_routes[pack] = added
    new_routes = sorted({r.pattern for r in runtime.routes} - before)
    out: dict[str, Any] = {"ok": bool(ok), "pack": pack, "loaded": bool(ok), "new_routes": new_routes}
    if pip_result:
        out["pip"] = pip_result
    return out


def ensure_pack_for_uri(runtime: Runtime, uri: str) -> dict[str, Any] | None:
    """If URI scheme maps to an unloaded pack, install (PyPI) and register it."""
    scheme = scheme_for_uri(uri)
    pack = pack_for_scheme(scheme)
    if not pack:
        return None
    loaded = getattr(runtime, "_loaded_packs", set())
    if pack in loaded:
        return None
    return load_pack_into_runtime(runtime, pack, install=not pack_importable(pack))


def call_uri(runtime: Runtime, uri: str, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Runtime.call with lazy pack install and real-backend deps on first use."""
    result = runtime.call(uri, payload, context)
    if (
        not result.get("ok")
        and result.get("type") == "route_not_found"
        and auto_install_enabled()
    ):
        prep = ensure_pack_for_uri(runtime, uri)
        if prep and prep.get("loaded"):
            result = runtime.call(uri, payload, context)
            result.setdefault("auto_install", {})["pack"] = prep
    err = str(result.get("error") or "")
    if not result.get("ok") and auto_install_enabled() and "pip install" in err.lower():
        scheme = scheme_for_uri(uri)
        pack = pack_for_scheme(scheme) or ("screen" if scheme == "screen" else None)
        if pack and (context.get("allow_real") or os.environ.get("URISYS_ALLOW_REAL") == "1"):
            real = ensure_real_deps(pack, install=True)
            if real.get("ok"):
                importlib.invalidate_caches()
                result = runtime.call(uri, payload, context)
                result.setdefault("auto_install", {})["real"] = real
        elif scheme == "screen" and (context.get("allow_real") or os.environ.get("URISYS_ALLOW_REAL") == "1"):
            real = ensure_real_deps("screen", install=True)
            if real.get("ok"):
                importlib.invalidate_caches()
                result = runtime.call(uri, payload, context)
                result.setdefault("auto_install", {})["real"] = real
    return result


def register_forward_pack(
    runtime: Runtime,
    scheme: str,
    endpoint: str,
    patterns: list[str],
) -> dict[str, Any]:
    """Make a capability served by an out-of-process worker available on this
    node: route each of the contract's declared URI patterns to a forwarding
    handler that calls the worker at ``endpoint``. This is how an artifact
    resolved from a markpact.com release (OCI image on GitHub) is wired in."""
    scheme = (scheme or "").strip()
    endpoint = (endpoint or "").strip()
    if not scheme or not endpoint:
        return {"ok": False, "error": "scheme and endpoint are required"}
    if not patterns:
        return {"ok": False, "error": "at least one uri pattern is required"}
    loaded = getattr(runtime, "_loaded_packs", None)
    if loaded is None:
        loaded = set()
        runtime._loaded_packs = loaded  # type: ignore[attr-defined]
    runtime.config.setdefault("forward_targets", {})[scheme] = endpoint
    before = {r.pattern for r in runtime.routes}
    for pattern in patterns:
        if pattern in before:
            continue
        kind = "command" if "/command/" in pattern else "query"
        runtime.register(
            pattern,
            "python://urisysnode.forward:forward_call",
            kind=kind,
            operation="forward",
            approval="required" if kind == "command" else "not_required",
            side_effects=kind == "command",
        )
    loaded.add(scheme)
    new_routes = sorted({r.pattern for r in runtime.routes} - before)
    return {"ok": True, "scheme": scheme, "endpoint": endpoint, "new_routes": new_routes}


def _release_forward_spec(
    release: dict[str, Any],
    scheme: str | None,
    patterns: list[str] | None,
) -> tuple[str, list[str]]:
    """Resolve the URI scheme and patterns to wire for a release. Precedence:
    caller-supplied > inline on the release payload > parsed from the contract
    the release references. The contract is the source of truth, so we fall back
    to it whenever the catalog response does not already carry the patterns."""
    out_scheme = (scheme or release.get("scheme") or "").strip()
    out_patterns = patterns or release.get("patterns") or []
    clean = [str(p).strip() for p in out_patterns if str(p).strip()]
    if out_scheme and clean:
        return out_scheme, clean

    from .artifact_resolver import contract_spec_from_release

    spec = contract_spec_from_release(release)
    return (out_scheme or spec["scheme"], clean or spec["patterns"])


def hotload_release_pack(
    runtime: Runtime,
    contract_id: str,
    version: str,
    *,
    catalog_url: str,
    profile_path: str | Path,
    context: dict[str, Any] | None = None,
    container: str = "urisys-stepper-worker",
    port: int = 8791,
    scheme: str | None = None,
    patterns: list[str] | None = None,
) -> dict[str, Any]:
    """Hot-load a capability from a markpact.com release: pairing-gated and
    signature-gated, fetch the release, pull/run its OCI worker, then wire the
    contract's URI patterns to forward to that worker. This is the glue over
    resolve_from_release + register_forward_pack."""
    from .artifact_resolver import fetch_release, run_release
    from .identity import require_paired
    from .release_verify import verify_release

    ctx = context or {}
    contract_id = (contract_id or "").strip()
    version = (version or "").strip()
    if not contract_id or not version:
        return {"ok": False, "stage": "request", "error": "contract and version are required"}

    try:
        require_paired(ctx)
    except PermissionError as exc:
        return {"ok": False, "stage": "pairing", "error": str(exc)}

    try:
        release = fetch_release(catalog_url, contract_id, version)
    except Exception as exc:
        return {"ok": False, "stage": "fetch", "error": str(exc)}

    verdict = verify_release(release, context=ctx)
    if not verdict.get("ok"):
        return {"ok": False, "stage": "verify", "error": verdict.get("error"), "signature": verdict}

    try:
        fwd_scheme, fwd_patterns = _release_forward_spec(release, scheme, patterns)
    except Exception as exc:
        return {"ok": False, "stage": "spec", "error": str(exc), "signature": verdict}
    if not fwd_scheme or not fwd_patterns:
        return {
            "ok": False,
            "stage": "spec",
            "error": "release does not declare scheme/patterns; pass them explicitly",
            "signature": verdict,
        }

    try:
        run = run_release(release, profile_path, container=container, port=port)
    except Exception as exc:
        return {"ok": False, "stage": "run", "error": str(exc), "signature": verdict}

    endpoint = f"http://127.0.0.1:{run['port']}"
    reg = register_forward_pack(runtime, fwd_scheme, endpoint, fwd_patterns)
    return {
        "ok": bool(reg.get("ok")),
        "stage": "registered" if reg.get("ok") else "register",
        "contract_id": contract_id,
        "version": version,
        "scheme": fwd_scheme,
        "endpoint": endpoint,
        "worker": run,
        "forward": reg,
        "signature": verdict,
    }


def make_handler(runtime: Runtime):
    allow_pack_load = (
        os.environ.get("URISYS_NODE_ALLOW_PACK_LOAD", "1" if auto_install_enabled() else "0") == "1"
    )

    class Handler(BaseHTTPRequestHandler):
        def _json(self, status: int, data: dict[str, Any]) -> None:
            raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:
            if self.path == "/health":
                return self._json(200, health_payload(runtime=runtime))
            if self.path in ("/uri/routes", "/routes"):
                return self._json(200, {"ok": True, "routes": [r.pattern for r in runtime.routes]})
            if self.path.startswith("/events"):
                limit = 50
                if "limit=" in self.path:
                    try:
                        limit = int(self.path.split("limit=", 1)[1])
                    except ValueError:
                        pass
                return self._json(200, {"ok": True, "events": runtime.events.tail(limit)})
            return self._json(404, {"ok": False, "error": "not found"})

        def do_POST(self) -> None:
            if self.path == "/uri/pack":
                if not allow_pack_load:
                    return self._json(403, {
                        "ok": False,
                        "error": "pack loading disabled; set URISYS_NODE_ALLOW_PACK_LOAD=1",
                    })
                length = int(self.headers.get("Content-Length") or "0")
                req = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                contract = str(req.get("contract") or req.get("contract_id") or "").strip()
                if contract:
                    # Release hot-load: resolve a markpact.com release to an OCI
                    # worker and forward its scheme. Pairing/signature gated.
                    ctx = req.get("context") if isinstance(req.get("context"), dict) else {}
                    catalog = str(
                        req.get("catalog")
                        or req.get("catalog_url")
                        or os.environ.get("MARKPACT_CATALOG_URL", "https://markpact.com")
                    )
                    profile = str(
                        req.get("profile")
                        or os.environ.get("URISYS_NODE_PROFILE", "config/node-profile.json")
                    )
                    req_patterns = req.get("patterns")
                    result = hotload_release_pack(
                        runtime,
                        contract,
                        str(req.get("version") or ""),
                        catalog_url=catalog,
                        profile_path=profile,
                        context=ctx,
                        scheme=str(req.get("scheme")).strip() if req.get("scheme") else None,
                        patterns=[str(p) for p in req_patterns] if isinstance(req_patterns, list) else None,
                    )
                    status = 200 if result.get("ok") else (403 if result.get("stage") == "pairing" else 400)
                    return self._json(status, result)
                install = bool(req.get("install", True))
                force = bool(req.get("force", False))
                specs = req.get("specs")
                override = [str(s) for s in specs] if isinstance(specs, list) else None
                result = load_pack_into_runtime(
                    runtime,
                    str(req.get("pack") or ""),
                    install=install,
                    specs=override,
                    force=force,
                )
                return self._json(200 if result.get("ok") else 400, result)
            if self.path != "/uri/call":
                return self._json(404, {"ok": False, "error": "not found"})
            length = int(self.headers.get("Content-Length") or "0")
            body = self.rfile.read(length).decode("utf-8")
            req = json.loads(body or "{}")
            result = call_uri(
                runtime,
                req.get("uri", ""),
                req.get("payload") or {},
                req.get("context") or {},
            )
            return self._json(200 if result.get("ok") else 400, result)

    return Handler


def serve(runtime: Runtime, host: str, port: int) -> None:
    identity = load_identity()
    bootstrap = None
    try:
        from urisysnode.display_bootstrap import bootstrap_wayland_capture

        bootstrap = bootstrap_wayland_capture()
        runtime.config["display_bootstrap"] = bootstrap
    except Exception as exc:
        warnings.warn(f"display bootstrap skipped: {exc}", stacklevel=2)
    server = ThreadingHTTPServer((host, port), make_handler(runtime))
    print(f"urisys-node listening on http://{host}:{port}")
    print(f"node_id={identity['node_id']} fingerprint={identity.get('fingerprint')}")
    print("endpoints: GET /health  GET /uri/routes  GET /events  POST /uri/call  POST /uri/pack")
    print(f"auto_install={'on' if auto_install_enabled() else 'off'} (URISYS_NODE_AUTO_INSTALL)")
    if bootstrap:
        print(f"display_bootstrap={bootstrap.get('ok')} session={bootstrap.get('session', bootstrap.get('reason', '-'))}")
    for route in runtime.routes:
        print(" -", route.pattern)
    server.serve_forever()
