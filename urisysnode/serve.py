from __future__ import annotations

import errno
import fnmatch
import importlib
import json
import os
import re
import signal
import shutil
import socket
import subprocess
import sys
import time
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from uri_control.edge.runtime import Runtime, load_json

from .identity import default_events_path, health_payload, load_identity
from .pack_resolver import (
    CORE_PACKS,
    PACK_MODULES,
    auto_install_enabled,
    ensure_pack_pypi,
    ensure_boot_pack,
    ensure_real_deps,
    pack_for_scheme,
    pack_importable,
    scheme_for_uri,
)
from .port import (
    _collect_takeover_targets,
    _fuser_kill_port,
    _is_node_serve_process,
    _kill_pid,
    _pid_alive,
    _pidfile_path,
    _pids_on_port,
    _pids_on_port_ss,
    _pids_serve_cmdline,
    _read_cmdline,
    _wait_port_free,
    _worker_pids_from_state,
    takeover_port,
)
from .runtime import (
    _bootstrap_worker_packs,
    _default_real_config,
    apply_host_trust,
    build_runtime,
    ensure_isolated_pack,
    ensure_pack_for_uri,
    get_supervisor,
    isolation_mode,
    load_pack_into_runtime,
    resolve_node_config,
)


def call_uri(runtime: Runtime, uri: str, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Runtime.call with lazy pack install and real-backend deps on first use.

    By default each non-core capability is dispatched to its own worker process
    (see :func:`isolation_mode`) so a pack crash cannot take the router down. Set
    ``URISYS_NODE_ISOLATION=off`` (or ``context['isolation']='off'``) for the
    legacy in-process behaviour."""
    context = apply_host_trust(runtime, uri, context)
    isolated = ensure_isolated_pack(runtime, uri, payload, context)
    if isolated is not None and "ephemeral_result" in isolated:
        return isolated["ephemeral_result"]
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


def _app_chat_store(runtime: Runtime):
    from .app_data import AppChatStore

    store = getattr(runtime, "_app_chat_store", None)
    if store is None:
        store = AppChatStore()
        runtime._app_chat_store = store  # type: ignore[attr-defined]
    return store


def _app_chat_get(path: str, runtime: Runtime) -> tuple[int, dict[str, Any]]:
    parsed = urlparse(path)
    qs = parse_qs(parsed.query)
    if parsed.path == "/app/chat/messages":
        channel_id = (qs.get("channel_id") or qs.get("channel") or [""])[0]
        if not channel_id:
            return 400, {"ok": False, "error": "channel_id required"}
        try:
            limit = int((qs.get("limit") or ["200"])[0])
        except ValueError:
            limit = 200
        messages = _app_chat_store(runtime).list_messages(channel_id, limit=limit)
        return 200, {"ok": True, "channel_id": channel_id, "messages": messages, "count": len(messages)}
    if parsed.path == "/app/chat/channels":
        try:
            limit = int((qs.get("limit") or ["100"])[0])
        except ValueError:
            limit = 100
        channels = _app_chat_store(runtime).list_channels(limit=limit)
        return 200, {"ok": True, "channels": channels, "count": len(channels)}
    return 404, {"ok": False, "error": "not found"}


def _app_chat_post(body: dict[str, Any], runtime: Runtime) -> tuple[int, dict[str, Any]]:
    channel_id = str(body.get("channel_id") or body.get("channel") or "").strip()
    role = str(body.get("role") or "user").strip() or "user"
    text = str(body.get("text") or "").strip()
    meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
    if not channel_id or not text:
        return 400, {"ok": False, "error": "channel_id and text required"}
    row = _app_chat_store(runtime).append(channel_id, role, text, meta=meta)
    return 200, {"ok": True, "message": row}


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
            if self.path.startswith("/app/chat/"):
                status, data = _app_chat_get(self.path, runtime)
                return self._json(status, data)
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
            if self.path == "/app/chat/messages":
                length = int(self.headers.get("Content-Length") or "0")
                req = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                status, data = _app_chat_post(req, runtime)
                return self._json(status, data)
            if self.path != "/uri/call":
                return self._json(404, {"ok": False, "error": "not found"})
            length = int(self.headers.get("Content-Length") or "0")
            body = self.rfile.read(length).decode("utf-8")
            try:
                req = json.loads(body or "{}")
            except json.JSONDecodeError as exc:
                return self._json(
                    400,
                    {"ok": False, "error": f"invalid JSON body: {exc}", "hint": "escape backslashes in shell payloads or use lenovo_remote_session.py"},
                )
            result = call_uri(
                runtime,
                req.get("uri", ""),
                req.get("payload") or {},
                req.get("context") or {},
            )
            return self._json(200 if result.get("ok") else 400, result)

    return Handler



class _ReuseHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def serve(runtime: Runtime, host: str, port: int, *, takeover: bool = True) -> None:
    if takeover:
        info = takeover_port(host, port)
        if info["killed"]:
            print(f"takeover: terminated old instance pid(s) {info['killed']}")
        elif info.get("fuser"):
            print(f"takeover: fuser -k {port}/tcp")
        if not info["port_free"]:
            raise OSError(
                f"port {port} still in use after takeover "
                f"(killed={info['killed']}, fuser={info.get('fuser')}); "
                f"check: ss -ltnp 'sport = :{port}'"
            )

    pidfile = _pidfile_path(port)
    pidfile.parent.mkdir(parents=True, exist_ok=True)
    pidfile.write_text(str(os.getpid()), encoding="utf-8")

    def _cleanup(*_args: Any) -> None:
        sup = getattr(runtime, "_supervisor", None)
        if sup is not None:
            try:
                sup.shutdown()
            except Exception:
                pass
        try:
            if pidfile.read_text(encoding="utf-8").strip() == str(os.getpid()):
                pidfile.unlink()
        except OSError:
            pass

    import atexit

    atexit.register(_cleanup)
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, lambda *_a: sys.exit(0))
        except (ValueError, OSError):
            pass

    identity = load_identity()
    bootstrap = None
    try:
        from urisysnode.display_bootstrap import bootstrap_wayland_capture

        bootstrap = bootstrap_wayland_capture()
        runtime.config["display_bootstrap"] = bootstrap
    except Exception as exc:
        warnings.warn(f"display bootstrap skipped: {exc}", stacklevel=2)
    try:
        server = _ReuseHTTPServer((host, port), make_handler(runtime))
    except OSError as exc:
        if takeover and exc.errno in (errno.EADDRINUSE, 98):
            info = takeover_port(host, port)
            if info["killed"]:
                print(f"takeover (late): terminated pid(s) {info['killed']}")
            if info["port_free"]:
                server = _ReuseHTTPServer((host, port), make_handler(runtime))
            else:
                raise OSError(
                    f"port {port} in use and takeover failed (killed={info['killed']})"
                ) from exc
        else:
            raise
    print(f"urisys-node listening on http://{host}:{port}")
    print(f"node_id={identity['node_id']} fingerprint={identity.get('fingerprint')}")
    print("endpoints: GET /health  GET /uri/routes  GET /events  POST /uri/call  POST /uri/pack")
    print(f"auto_install={'on' if auto_install_enabled() else 'off'} (URISYS_NODE_AUTO_INSTALL)")
    if bootstrap:
        print(f"display_bootstrap={bootstrap.get('ok')} session={bootstrap.get('session', bootstrap.get('reason', '-'))}")
    for route in runtime.routes:
        print(" -", route.pattern)
    server.serve_forever()
