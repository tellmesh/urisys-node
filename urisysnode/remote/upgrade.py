"""Upgrade operations for lenovo node and KV."""

from __future__ import annotations

import json
import os
import time
import urllib.error
from pathlib import Path
from typing import Any

from .client import health, pip_install, wait_health
from .config import default_endpoint, default_wheel_host
from .deploy import build_wheel, serve_wheels, wheel_url
from .restart import schedule_restart


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
        steps["install_kv"] = __install_pack(
            "kv",
            specs=[wheel_url(kv_wheel, base=host_base)],
        )
        steps["discover"] = __call_uri("kv://lenovo/runtime/query/discover")
        steps["log_summary"] = __call_uri("log://lenovo/events/query/summarize", payload={"limit": 10})
        return {"ok": True, "steps": steps}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "error": str(exc), "steps": steps, "hint": "start on lenovo: source ~/venv/bin/activate && urisys node serve --host 0.0.0.0 --port 8790"}
    finally:
        server.terminate()


# Local imports to avoid circular dependencies
def __call_uri(uri: str, *, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    from .client import call_uri
    return call_uri(uri, payload=payload)


def __install_pack(pack: str, *, specs: list[str] | None = None) -> dict[str, Any]:
    from .pack import install_pack
    return install_pack(pack, specs=specs)
