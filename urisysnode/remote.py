"""Remote node operations via URI (no shell scripts)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .client import call_via_route_map, remote_call


def default_route_map() -> str:
    node_root = Path(__file__).resolve().parents[1]
    return os.environ.get(
        "URISYS_ROUTE_MAP",
        str(node_root / "config" / "route-map.lenovo.yaml"),
    )


def default_nodes_registry() -> str:
    node_root = Path(__file__).resolve().parents[1]
    return os.environ.get(
        "URISYS_NODES_REGISTRY",
        str(node_root / "config" / "nodes.registry.json"),
    )


def default_endpoint() -> str:
    return os.environ.get("URISYS_LENOVO_ENDPOINT", "http://192.168.188.201:8790").rstrip("/")


def default_wheel_host() -> str:
    return os.environ.get("URISYS_WHEEL_HOST", "http://192.168.188.212:8765").rstrip("/")


def health(*, endpoint: str | None = None, timeout: float = 5.0) -> dict[str, Any]:
    url = (endpoint or default_endpoint()) + "/health"
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def wait_health(*, endpoint: str | None = None, timeout_s: float = 60.0, interval_s: float = 2.0) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    last_error = "unreachable"
    ep = endpoint or default_endpoint()
    while time.time() < deadline:
        try:
            return health(endpoint=ep)
        except Exception as exc:
            last_error = str(exc)
            time.sleep(interval_s)
    raise TimeoutError(f"node not healthy at {ep}: {last_error}")


def call_uri(
    uri: str,
    *,
    payload: dict[str, Any] | None = None,
    approved: bool = True,
    allow_real: bool = True,
    dry_run: bool = False,
    route_map: str | None = None,
    nodes_registry: str | None = None,
    endpoint: str | None = None,
) -> dict[str, Any]:
    ctx = {"approved": approved, "allow_real": allow_real, "dry_run": dry_run}
    if endpoint:
        return remote_call(endpoint, uri, payload, ctx)
    return call_via_route_map(
        uri,
        route_map_path=route_map or default_route_map(),
        nodes_registry_path=nodes_registry or default_nodes_registry(),
        payload=payload,
        context=ctx,
    )


def pip_install(
    specs: list[str],
    *,
    route_map: str | None = None,
    nodes_registry: str | None = None,
    endpoint: str | None = None,
) -> dict[str, Any]:
    return call_uri(
        "shell://pip",
        payload={"args": ["install", "-U", *specs]},
        route_map=route_map,
        nodes_registry=nodes_registry,
        endpoint=endpoint,
    )


def install_pack(
    pack: str,
    *,
    specs: list[str] | None = None,
    force: bool = True,
    route_map: str | None = None,
    nodes_registry: str | None = None,
    endpoint: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"pack": pack, "install": True, "force": force}
    if specs:
        payload["specs"] = specs
    return call_uri(
        "node://lenovo/command/install-pack",
        payload=payload,
        route_map=route_map,
        nodes_registry=nodes_registry,
        endpoint=endpoint,
    )


def spawn_worker(
    pack: str | None = None,
    *,
    module: str | None = None,
    install: bool = True,
    specs: list[str] | None = None,
    force: bool = False,
    target: str = "lenovo",
    route_map: str | None = None,
    nodes_registry: str | None = None,
    endpoint: str | None = None,
) -> dict[str, Any]:
    """Spawn a capability as an out-of-process worker; the router forwards to it."""
    payload: dict[str, Any] = {"install": install, "force": force}
    if pack:
        payload["pack"] = pack
    if module:
        payload["module"] = module
    if specs:
        payload["specs"] = specs
    return call_uri(
        f"node://{target}/command/spawn-worker",
        payload=payload,
        route_map=route_map,
        nodes_registry=nodes_registry,
        endpoint=endpoint,
    )


def restart_worker(
    name: str,
    *,
    target: str = "lenovo",
    route_map: str | None = None,
    nodes_registry: str | None = None,
    endpoint: str | None = None,
) -> dict[str, Any]:
    return call_uri(
        f"node://{target}/command/restart-worker",
        payload={"name": name},
        route_map=route_map,
        nodes_registry=nodes_registry,
        endpoint=endpoint,
    )


def stop_worker(
    name: str,
    *,
    target: str = "lenovo",
    route_map: str | None = None,
    nodes_registry: str | None = None,
    endpoint: str | None = None,
) -> dict[str, Any]:
    return call_uri(
        f"node://{target}/command/stop-worker",
        payload={"name": name},
        route_map=route_map,
        nodes_registry=nodes_registry,
        endpoint=endpoint,
    )


def workers(
    *,
    target: str = "lenovo",
    route_map: str | None = None,
    nodes_registry: str | None = None,
    endpoint: str | None = None,
) -> dict[str, Any]:
    return call_uri(
        f"node://{target}/query/workers",
        route_map=route_map,
        nodes_registry=nodes_registry,
        endpoint=endpoint,
    )


def schedule_restart(*, route_map: str | None = None, nodes_registry: str | None = None, endpoint: str | None = None, port: int = 8790) -> dict[str, Any]:
    # Kill listener on the node port, then start fresh `urisys node serve` (takeover in-process).
    cmd = (
        f"fuser -k {port}/tcp 2>/dev/null || true; "
        "sleep 2; "
        "( source ~/venv/bin/activate 2>/dev/null || true; "
        "export URISYS_ALLOW_REAL=1; "
        "export URISYS_NODE_CONFIG=\"${URISYS_NODE_CONFIG:-$HOME/.config/urisys/node-profile.lenovo.json}\"; "
        "mkdir -p ~/.config/urisys; "
        f"setsid urisys node serve --host 0.0.0.0 --port {port} "
        "--config \"$URISYS_NODE_CONFIG\" >> /tmp/urisys-node.log 2>&1 < /dev/null & "
        ") >/dev/null 2>&1 &"
    )
    return call_uri(
        "shell://bash",
        payload={"args": ["-lc", cmd]},
        route_map=route_map,
        nodes_registry=nodes_registry,
        endpoint=endpoint,
    )


def _restart_scheduled(out: dict[str, Any]) -> dict[str, Any]:
    """Treat listener kill mid-request as success (HTTP connection drops when fuser runs)."""
    if out.get("ok"):
        return {**out, "scheduled": True}
    err = str(out.get("error") or "")
    lowered = err.lower()
    if any(token in lowered for token in ("closed connection", "connection reset", "broken pipe")):
        return {
            "ok": True,
            "scheduled": True,
            "note": "connection closed while killing listener (expected)",
            "hint": "urisys remote wait  # or: urisys-node remote wait",
        }
    return out


def build_wheel(project_dir: str | Path, *, out_dir: str | Path = "/tmp/urisys-deploy") -> Path:
    import tomllib

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    meta = tomllib.loads(Path(project_dir, "pyproject.toml").read_text(encoding="utf-8"))["project"]
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", "-w", str(out), str(project_dir), "-q"],
        check=True,
    )
    pkg_name = meta["name"]
    ver = meta["version"]
    for candidate in (out / f"{pkg_name.replace('-', '_')}-{ver}-py3-none-any.whl", out / f"{pkg_name}-{ver}-py3-none-any.whl"):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"wheel not found in {out} for {pkg_name} {ver}")


def serve_wheels(
    directory: str | Path = "/tmp/urisys-deploy",
    *,
    host: str = "192.168.188.212",
    port: int = 8765,
) -> subprocess.Popen[Any]:
    return subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", host, "--directory", str(directory)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wheel_url(wheel_path: Path, *, base: str | None = None) -> str:
    base = (base or default_wheel_host()).rstrip("/")
    return f"{base}/{wheel_path.name}"


def upgrade_lenovo_node(
    *,
    tellmesh_root: str | Path | None = None,
    wheel_host: str | None = None,
    endpoint: str | None = None,
    wait_s: float = 90.0,
) -> dict[str, Any]:
    """Build urisys-node wheel, pip install on lenovo, restart, verify /app/chat/*."""
    root = Path(tellmesh_root or os.environ.get("TELLMESH_ROOT", "/home/tom/github/tellmesh"))
    deploy = Path("/tmp/urisys-deploy")
    host_base = wheel_host or default_wheel_host()
    ep = endpoint or default_endpoint()

    node_wheel = build_wheel(root / "urisys-node", out_dir=deploy)
    server = serve_wheels(deploy)
    time.sleep(1)
    steps: dict[str, Any] = {}
    try:
        steps["health_before"] = health(endpoint=ep)
        steps["pip_node"] = pip_install([wheel_url(node_wheel, base=host_base)], endpoint=ep)
        steps["restart"] = schedule_restart(endpoint=ep)
        steps["health_after"] = wait_health(endpoint=ep, timeout_s=wait_s)
        hb = steps["health_after"]
        if hb.get("instance_id") == steps["health_before"].get("instance_id"):
            steps["warn"] = "instance_id unchanged — restart may not have taken over the port"
        try:
            with urllib.request.urlopen(f"{ep}/app/chat/messages?channel_id=__ifuri_probe__", timeout=10) as resp:
                steps["app_chat_probe"] = json.loads(resp.read().decode("utf-8"))
            chat_ok = bool(steps["app_chat_probe"].get("ok"))
        except urllib.error.HTTPError as exc:
            steps["app_chat_probe"] = {"ok": False, "error": f"HTTP {exc.code}"}
            chat_ok = False
        return {"ok": chat_ok, "steps": steps, "endpoint": ep}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "ok": False,
            "error": str(exc),
            "steps": steps,
            "hint": "verify lenovo: urisys node serve --host 0.0.0.0 --port 8790",
        }
    finally:
        server.terminate()


def upgrade_lenovo_kv(
    *,
    tellmesh_root: str | Path | None = None,
    wheel_host: str | None = None,
    wait_s: float = 90.0,
) -> dict[str, Any]:
    """Build urisys-node + urikv wheels, serve HTTP, upgrade node, restart, install kv pack."""
    root = Path(tellmesh_root or os.environ.get("TELLMESH_ROOT", "/home/tom/github/tellmesh"))
    deploy = Path("/tmp/urisys-deploy")
    host_base = wheel_host or default_wheel_host()

    node_wheel = build_wheel(root / "urisys-node", out_dir=deploy)
    kv_wheel = build_wheel(root / "urikv", out_dir=deploy)
    server = serve_wheels(deploy)
    time.sleep(1)
    steps: dict[str, Any] = {}
    try:
        steps["health_before"] = health()
        steps["pip_node"] = pip_install([wheel_url(node_wheel, base=host_base)])
        steps["restart"] = schedule_restart()
        steps["health_after"] = wait_health(timeout_s=wait_s)
        steps["install_kv"] = install_pack(
            "kv",
            specs=[wheel_url(kv_wheel, base=host_base)],
        )
        steps["discover"] = call_uri("kv://lenovo/runtime/query/discover")
        steps["log_summary"] = call_uri("log://lenovo/events/query/summarize", payload={"limit": 10})
        return {"ok": True, "steps": steps}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "error": str(exc), "steps": steps, "hint": "start on lenovo: source ~/venv/bin/activate && urisys node serve --host 0.0.0.0 --port 8790"}
    finally:
        server.terminate()


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
