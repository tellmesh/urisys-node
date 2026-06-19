from __future__ import annotations

from typing import Any

from urisysnode.identity import load_pairing, require_paired, set_remote_control
from urisysnode.pack_resolver import PACK_MODULES, auto_install_enabled


def query_health(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del payload
    from urisysnode.identity import health_payload

    return health_payload(runtime=context.get("runtime"))


def query_identity(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del payload, context
    from urisysnode.identity import load_identity

    identity = load_identity()
    pairing = load_pairing()
    return {
        "node_id": identity["node_id"],
        "fingerprint": identity.get("fingerprint"),
        "hostname": identity.get("hostname"),
        "paired": bool(pairing.get("paired")),
        "controller": pairing.get("controller"),
        "capabilities": pairing.get("capabilities") or ["screen", "kvm", "him"],
    }


def command_indicator_on(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    require_paired(context)
    pairing = set_remote_control(True, payload.get("message", "Urisys remote control active"))
    return {"remote_control_active": True, "message": pairing.get("indicator_message")}


def command_indicator_off(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del payload
    require_paired(context)
    set_remote_control(False)
    return {"remote_control_active": False}


def query_packs(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del payload
    runtime = context.get("runtime")
    loaded = sorted(getattr(runtime, "_loaded_packs", set()) or [])
    return {
        "loaded": loaded,
        "available": sorted(PACK_MODULES.keys()),
        "auto_install": auto_install_enabled(),
    }


def command_install_pack(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if not context.get("approved"):
        return {"ok": False, "error": "approval required for install-pack"}
    pack = str(payload.get("pack") or "").strip()
    runtime = context.get("runtime")
    if runtime is None:
        return {"ok": False, "error": "no runtime in context"}
    from urisysnode.serve import load_pack_into_runtime

    specs = payload.get("specs")
    override = [str(s) for s in specs] if isinstance(specs, list) else None
    return load_pack_into_runtime(
        runtime,
        pack,
        install=bool(payload.get("install", True)),
        specs=override,
        force=bool(payload.get("force", False)),
    )


def _get_supervisor(context: dict[str, Any]) -> Any:
    """Return the router's worker supervisor, creating it on first use so that
    workers can be spawned on demand even when none were enabled at boot."""
    runtime = context.get("runtime")
    if runtime is None:
        return None
    from urisysnode.serve import get_supervisor

    return get_supervisor(runtime)


def command_spawn_worker(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if not context.get("approved"):
        return {"ok": False, "error": "approval required for spawn-worker"}
    sup = _get_supervisor(context)
    if sup is None:
        return {"ok": False, "error": "no runtime in context"}
    pack = str(payload.get("pack") or "").strip() or None
    module = str(payload.get("module") or "").strip() or None
    specs = payload.get("specs")
    override = [str(s) for s in specs] if isinstance(specs, list) else None
    raw_env = payload.get("env")
    worker_env = {str(k): str(v) for k, v in raw_env.items()} if isinstance(raw_env, dict) else None
    return sup.spawn(
        pack=pack,
        module=module,
        install=bool(payload.get("install", False)),
        specs=override,
        env=worker_env,
        force=bool(payload.get("force", False)),
    )


def query_workers(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del payload
    sup = _get_supervisor(context)
    if sup is None:
        return {"ok": False, "error": "no runtime in context"}
    return sup.status()


def command_restart_worker(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if not context.get("approved"):
        return {"ok": False, "error": "approval required for restart-worker"}
    sup = _get_supervisor(context)
    if sup is None:
        return {"ok": False, "error": "no runtime in context"}
    name = str(payload.get("name") or payload.get("pack") or "").strip()
    if not name:
        return {"ok": False, "error": "worker name is required"}
    return sup.restart(name)


def command_stop_worker(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if not context.get("approved"):
        return {"ok": False, "error": "approval required for stop-worker"}
    sup = _get_supervisor(context)
    if sup is None:
        return {"ok": False, "error": "no runtime in context"}
    name = str(payload.get("name") or payload.get("pack") or "").strip()
    if not name:
        return {"ok": False, "error": "worker name is required"}
    return sup.stop(name)


def command_register_forward(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if not context.get("approved"):
        return {"ok": False, "error": "approval required for register-forward"}
    runtime = context.get("runtime")
    if runtime is None:
        return {"ok": False, "error": "no runtime in context"}
    scheme = str(payload.get("scheme") or "").strip()
    endpoint = str(payload.get("endpoint") or "").strip()
    patterns = payload.get("patterns")
    if not isinstance(patterns, list):
        return {"ok": False, "error": "patterns must be a list of URI patterns"}
    from urisysnode.serve import register_forward_pack

    return register_forward_pack(runtime, scheme, endpoint, [str(p) for p in patterns])
