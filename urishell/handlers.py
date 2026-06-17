"""shell:// — subprocess on urisys-node (bootstrap pip when PyPI unavailable)."""

from __future__ import annotations

import os
import subprocess
from typing import Any


def _allow_real(context: dict[str, Any]) -> bool:
    return bool(context.get("allow_real") or os.environ.get("URISYS_ALLOW_REAL") == "1")


def _detect_display(context: dict[str, Any]) -> str | None:
    if context.get("display"):
        return str(context["display"])
    env = context.get("env_config") or {}
    display = env.get("display") or os.environ.get("DISPLAY")
    return str(display) if display else None


def _mock(command: str, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    args = payload.get("args") or []
    return {
        "driver": "mock",
        "command": command,
        "args": args,
        "display": _detect_display(context),
        "ok": True,
    }


def shell_run(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    params = context.get("params") or {}
    command = str(params.get("command") or payload.get("command") or "")
    args = [str(a) for a in (payload.get("args") or [])]
    if not command:
        raise ValueError("shell command required")

    if context.get("dry_run") or not _allow_real(context):
        return _mock(command, payload, context)

    if command == "apt-get" and os.geteuid() != 0:
        args = [command, *args]
        command = "sudo"

    env = os.environ.copy()
    display = _detect_display(context)
    if display:
        env["DISPLAY"] = display
    xauth = context.get("xauthority")
    if xauth:
        env["XAUTHORITY"] = str(xauth)

    proc = subprocess.run(
        [command, *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=float(payload.get("timeout_s") or 600),
    )
    return {
        "driver": "subprocess",
        "command": command,
        "args": args,
        "exit_code": proc.returncode,
        "stdout": (proc.stdout or "")[-4000:],
        "stderr": (proc.stderr or "")[-2000:],
        "ok": proc.returncode == 0,
    }
