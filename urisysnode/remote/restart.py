"""Restart scheduling operations."""

from __future__ import annotations

import subprocess
import sys
from typing import Any


def schedule_restart(*, route_map: str | None = None, nodes_registry: str | None = None, endpoint: str | None = None, port: int = 8790) -> dict[str, Any]:
    # Import here to allow monkeypatching from urisysnode.remote
    from .client import call_uri
    # Standalone script in /tmp/restart-urisys.sh to prevent killing ourselves mid-execution
    cmd = (
        "cat << 'EOF' > /tmp/restart-urisys.sh\n"
        "#!/bin/bash\n"
        "sleep 1\n"
        f"pids=$(pgrep -f \"[u]risys.*serve --host 0.0.0.0 --port {port}\" || pgrep -f \"[u]risys.*serve\")\n"
        "for p in $pids; do\n"
        "  if [ \"$p\" != \"$$\" ] && [ \"$p\" != \"$BASHPID\" ] && [ \"$p\" != \"$PPID\" ]; then\n"
        "    kill -9 $p || true\n"
        "  fi\n"
        "done\n"
        "sleep 2\n"
        "source ~/venv/bin/activate 2>/dev/null || true\n"
        "export URISYS_ALLOW_REAL=1\n"
        f"export URISYS_NODE_CONFIG=\"${{URISYS_NODE_CONFIG:-$HOME/.config/urisys/node-profile.lenovo.json}}\"\n"
        "mkdir -p ~/.config/urisys\n"
        f"nohup urisys node serve --host 0.0.0.0 --port {port} --config \"$URISYS_NODE_CONFIG\" >> /tmp/urisys-node.log 2>&1 &\n"
        "EOF\n"
        "chmod +x /tmp/restart-urisys.sh\n"
        "setsid /tmp/restart-urisys.sh >/dev/null 2>&1 &\n"
        "echo scheduled"
    )
    try:
        return call_uri(
            "shell://bash",
            payload={"args": ["-lc", cmd]},
            route_map=route_map,
            nodes_registry=nodes_registry,
            endpoint=endpoint,
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


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
