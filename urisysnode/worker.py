"""Out-of-process capability worker: serves exactly one pack on loopback.

A worker is a thin urisys runtime that loads a single capability pack and exposes
it over HTTP (``/uri/call``, ``/health``, ``/uri/routes``). The node router
forwards matching URI calls here via ``register_forward_pack``. Because the pack
lives in its own process, it can be upgraded, restarted or crash independently
without taking the node router down — this removes the whole-node-restart races
that plagued the in-process pack model.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from uri_control.edge.runtime import Runtime, load_json, make_handler

from .identity import default_events_path

# Context keys safe to forward worker → router (JSON-serializable; no runtime/state).
_ROUTER_CALLBACK_CTX_KEYS = ("approved", "allow_real", "dry_run", "environment", "approval")


def _load_node_profile() -> dict[str, Any]:
    """Load the node profile (URISYS_NODE_CONFIG) so a worker runtime gets the same
    driver/policy config as the main node — without it kvm/screen/him fall back to mock."""
    config_file = os.environ.get("URISYS_NODE_CONFIG", "config/node-profile.json")
    try:
        return load_json(config_file) if Path(config_file).exists() else {}
    except Exception:
        return {}


def _local_schemes(runtime: Runtime) -> set[str]:
    schemes: set[str] = set()
    for route in runtime.routes:
        pat = getattr(route, "pattern", "") or ""
        if "://" in pat:
            schemes.add(pat.split("://", 1)[0])
    return schemes


def _wire_router_callback(runtime: Runtime) -> None:
    """Forward runtime.call for non-local schemes to the main node router.

    KVM workers call ocr:// / llm:// / him:// via context['runtime'].call; without
  this hook those schemes are route_not_found inside the isolated worker process.
    """
    router = os.environ.get("URISYS_NODE_ROUTER", "").strip()
    if not router:
        return
    local = _local_schemes(runtime)
    if not local:
        return
    original_call = runtime.call

    def call(
        uri: str,
        payload: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        scheme = uri.split("://", 1)[0] if "://" in uri else ""
        if scheme in local:
            return original_call(uri, payload, context)
        from urisysnode.client import remote_call

        ctx = dict(context or {})
        fwd = {k: ctx[k] for k in _ROUTER_CALLBACK_CTX_KEYS if k in ctx}
        return remote_call(router, uri, payload or {}, fwd)

    runtime.call = call  # type: ignore[method-assign]


def build_worker_runtime(
    *,
    pack: str | None = None,
    module: str | None = None,
    install: bool = False,
    specs: list[str] | None = None,
) -> tuple[Runtime, dict[str, Any]]:
    """Build a minimal runtime hosting exactly one capability.

    ``module`` (a dotted path exposing ``register(runtime)``) takes precedence;
    otherwise ``pack`` is resolved through the node pack registry, with optional
    pip install of the pack wheel.
    """
    from urisysnode.env import load_urisys_env

    load_urisys_env()
    rt = Runtime(events_path=default_events_path(), config=_load_node_profile())
    rt._loaded_packs = set()  # type: ignore[attr-defined]

    if module:
        mod = importlib.import_module(module)
        mod.register(rt)
        info: dict[str, Any] = {"ok": True, "module": module, "loaded": True}
        rt._loaded_packs.add(module)  # type: ignore[attr-defined]
    elif pack:
        from urisysnode.serve import load_pack_into_runtime

        info = load_pack_into_runtime(rt, pack, install=install, specs=specs, force=False)
        if not info.get("ok"):
            raise RuntimeError(f"worker failed to load pack {pack!r}: {info}")
    else:
        raise ValueError("worker requires --pack or --module")

    info["routes"] = [r.pattern for r in rt.routes]
    _wire_router_callback(rt)
    return rt, info


def serve_worker(
    *,
    pack: str | None = None,
    module: str | None = None,
    host: str = "127.0.0.1",
    port: int = 8801,
    install: bool = False,
    specs: list[str] | None = None,
) -> None:
    rt, info = build_worker_runtime(pack=pack, module=module, install=install, specs=specs)
    server = ThreadingHTTPServer((host, port), make_handler(rt))
    name = module or pack

    def _stop(*_args: Any) -> None:
        server.shutdown()
        raise SystemExit(0)

    import signal

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _stop)
        except (ValueError, OSError):
            pass

    print(f"urisys-worker[{name}] listening on http://{host}:{port}")
    for pattern in info.get("routes", []):
        print(" -", pattern)
    sys.stdout.flush()
    server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="urisys-worker", description="Serve one urisys capability pack out-of-process.")
    p.add_argument("--pack", default=None, help="Pack alias (browser, kv, office, ...)")
    p.add_argument("--module", default=None, help="Dotted module exposing register(runtime)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8801)
    p.add_argument("--install", action="store_true", help="pip install the pack wheel before loading")
    p.add_argument("--spec", action="append", default=[], help="Explicit pip spec(s) for --install")
    p.add_argument("--print-routes", action="store_true", help="Build runtime, print routes as JSON, exit")
    args = p.parse_args(argv)

    if args.print_routes:
        _, info = build_worker_runtime(
            pack=args.pack, module=args.module, install=args.install, specs=args.spec or None
        )
        print(json.dumps(info, ensure_ascii=False))
        return 0

    serve_worker(
        pack=args.pack,
        module=args.module,
        host=args.host,
        port=args.port,
        install=args.install,
        specs=args.spec or None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
