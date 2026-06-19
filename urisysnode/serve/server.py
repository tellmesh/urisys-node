"""HTTP server for urisys-node."""

from __future__ import annotations

import errno
import importlib
import os
import signal
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from uri_control.edge.runtime import Runtime

from ..identity import load_identity
from ..pack_resolver import (
    auto_install_enabled,
    ensure_real_deps,
    pack_for_scheme,
    scheme_for_uri,
)
from ..runtime import ensure_pack_for_uri
from ..port import takeover_port


class _ReuseHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def call_uri(runtime: Runtime, uri: str, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Runtime.call with lazy pack install and real-backend deps on first use.

    By default each non-core capability is dispatched to its own worker process
    (see :func:`isolation_mode`) so a pack crash cannot take the router down. Set
    ``URISYS_NODE_ISOLATION=off`` (or ``context['isolation']='off'``) for the
    legacy in-process behaviour."""
    from ..runtime import (
        apply_host_trust,
        ensure_isolated_pack,
    )

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
        from ..display_bootstrap import bootstrap_wayland_capture

        bootstrap = bootstrap_wayland_capture()
        runtime.config["display_bootstrap"] = bootstrap
    except Exception as exc:
        import warnings

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


def _pidfile_path(port: int) -> Path:
    from ..env import URISYS_NODE_RUNTIME_DIR

    runtime_dir = Path(URISYS_NODE_RUNTIME_DIR)
    return runtime_dir / f"urisys-node-{port}.pid"
