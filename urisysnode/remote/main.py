"""CLI entry point for remote operations."""

from __future__ import annotations

import json
import sys
from typing import Any


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="urisys-node remote", description="Remote lenovo ops via URI (Python CLI, no bash scripts).")
    sub = p.add_subparsers(dest="cmd", required=True)

    h = sub.add_parser("health", help="GET /health on remote node")
    h.add_argument("--endpoint", default=None)

    w = sub.add_parser("wait", help="Wait until node /health is ok")
    w.add_argument("--endpoint", default=None)
    w.add_argument("--timeout", type=float, default=60.0)

    c = sub.add_parser("call", help="Call URI via route-map (or --endpoint direct)")
    c.add_argument("uri")
    c.add_argument("--payload", default="{}")
    c.add_argument("--endpoint", default=None)
    c.add_argument("--route-map", default=None)
    c.add_argument("--nodes-registry", default=None)
    c.add_argument("--approve", action="store_true", default=True)
    c.add_argument("--allow-real", action="store_true", default=True)

    pi = sub.add_parser("pip-install", help="shell://pip install -U on remote node")
    pi.add_argument("specs", nargs="+")
    pi.add_argument("--route-map", default=None)

    ip = sub.add_parser("install-pack", help="node://lenovo/command/install-pack")
    ip.add_argument("pack")
    ip.add_argument("--spec", action="append", default=[])
    ip.add_argument("--force", action="store_true", default=True)
    ip.add_argument("--route-map", default=None)
    ip.add_argument("--nodes-registry", default=None)
    ip.add_argument("--endpoint", default=None)

    rs = sub.add_parser("restart", help="Schedule delayed urisys node restart on remote")
    rs.add_argument("--endpoint", default=None)
    rs.add_argument("--route-map", default=None)
    rs.add_argument("--nodes-registry", default=None)
    rs.add_argument("--port", type=int, default=8790)

    sw = sub.add_parser("spawn-worker", help="Spawn a pack as an out-of-process worker")
    sw.add_argument("pack", nargs="?", default=None)
    sw.add_argument("--module", default=None)
    sw.add_argument("--spec", action="append", default=[])
    sw.add_argument("--no-install", dest="install", action="store_false", default=True)
    sw.add_argument("--force", action="store_true", default=False)
    sw.add_argument("--target", default="lenovo")
    sw.add_argument("--endpoint", default=None)

    rw = sub.add_parser("restart-worker", help="Restart a worker by name")
    rw.add_argument("name")
    rw.add_argument("--target", default="lenovo")
    rw.add_argument("--endpoint", default=None)

    stw = sub.add_parser("stop-worker", help="Stop and unregister a worker by name")
    stw.add_argument("name")
    stw.add_argument("--target", default="lenovo")
    stw.add_argument("--endpoint", default=None)

    lw = sub.add_parser("workers", help="List live capability workers")
    lw.add_argument("--target", default="lenovo")
    lw.add_argument("--endpoint", default=None)

    uk = sub.add_parser("upgrade-kv", help="Build wheels, upgrade urisys-node, restart, install urikv")
    uk.add_argument("--tellmesh-root", default=None)
    uk.add_argument("--wheel-host", default=None)

    un = sub.add_parser("upgrade-node", help="Build urisys-node wheel, upgrade lenovo, verify /app/chat")
    un.add_argument("--tellmesh-root", default=None)
    un.add_argument("--wheel-host", default=None)
    un.add_argument("--endpoint", default=None)
    un.add_argument("--wait", type=float, default=90.0)

    args = p.parse_args(argv)

    # Import here to avoid circular imports
    from .client import call_uri, health, pip_install, wait_health
    from .pack import install_pack
    from .restart import _restart_scheduled, schedule_restart
    from .upgrade import upgrade_lenovo_kv, upgrade_lenovo_node
    from .worker import restart_worker, spawn_worker, stop_worker, workers

    try:
        if args.cmd == "health":
            print(json.dumps(health(endpoint=args.endpoint), indent=2, ensure_ascii=False))
            return 0
        if args.cmd == "wait":
            print(json.dumps(wait_health(endpoint=args.endpoint, timeout_s=args.timeout), indent=2, ensure_ascii=False))
            return 0
        if args.cmd == "call":
            out = call_uri(
                args.uri,
                payload=json.loads(args.payload),
                route_map=args.route_map,
                nodes_registry=args.nodes_registry,
                endpoint=args.endpoint,
            )
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0 if out.get("ok", True) else 1
        if args.cmd == "pip-install":
            out = pip_install(list(args.specs), route_map=args.route_map)
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0 if out.get("ok", True) else 1
        if args.cmd == "install-pack":
            out = install_pack(
                args.pack,
                specs=args.spec or None,
                force=args.force,
                route_map=args.route_map,
                nodes_registry=args.nodes_registry,
                endpoint=args.endpoint,
            )
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0 if out.get("result", out).get("ok", out.get("ok")) else 1
        if args.cmd == "restart":
            out = _restart_scheduled(
                schedule_restart(
                    route_map=args.route_map,
                    nodes_registry=args.nodes_registry,
                    endpoint=args.endpoint,
                    port=args.port,
                )
            )
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0 if out.get("ok") else 1
        if args.cmd == "spawn-worker":
            out = spawn_worker(
                args.pack,
                module=args.module,
                install=args.install,
                specs=args.spec or None,
                force=args.force,
                target=args.target,
                endpoint=args.endpoint,
            )
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0 if out.get("ok") else 1
        if args.cmd == "restart-worker":
            out = restart_worker(args.name, target=args.target, endpoint=args.endpoint)
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0 if out.get("ok") else 1
        if args.cmd == "stop-worker":
            out = stop_worker(args.name, target=args.target, endpoint=args.endpoint)
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0 if out.get("ok") else 1
        if args.cmd == "workers":
            out = workers(target=args.target, endpoint=args.endpoint)
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0 if out.get("ok", True) else 1
        if args.cmd == "upgrade-kv":
            out = upgrade_lenovo_kv(tellmesh_root=args.tellmesh_root, wheel_host=args.wheel_host)
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0 if out.get("ok") else 1
        if args.cmd == "upgrade-node":
            out = upgrade_lenovo_node(
                tellmesh_root=args.tellmesh_root,
                wheel_host=args.wheel_host,
                endpoint=args.endpoint,
                wait_s=args.wait,
            )
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0 if out.get("ok") else 1
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
