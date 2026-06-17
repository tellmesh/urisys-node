"""Auto-start vdisplay-agent + screencast on Wayland when node boots."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any


def _ensure_session_env() -> None:
    uid = os.getuid()
    os.environ.setdefault("XDG_RUNTIME_DIR", f"/run/user/{uid}")
    if not os.environ.get("WAYLAND_DISPLAY") and os.path.isdir(os.environ["XDG_RUNTIME_DIR"]):
        for name in ("wayland-0", "wayland-1"):
            if (Path := __import__("pathlib").Path)(os.environ["XDG_RUNTIME_DIR"], name).exists():
                os.environ.setdefault("WAYLAND_DISPLAY", name)
                break


def _agent_url() -> str:
    return os.environ.get("VDISPLAY_AGENT_URL", "http://127.0.0.1:8765").rstrip("/")


def _agent_up() -> bool:
    try:
        with urllib.request.urlopen(f"{_agent_url()}/health", timeout=1.5) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


def _screencast_ready() -> bool:
    try:
        with urllib.request.urlopen(f"{_agent_url()}/session/screencast/status", timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        payload = data.get("result") or data
        return bool(payload.get("ready") or payload.get("capture_ready"))
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return False


def _start_agent(port: int) -> dict[str, Any]:
    if shutil.which("vdisplay-agent") is None:
        return {"ok": False, "error": "vdisplay-agent not installed (pip install vdisplay-agent)"}
    log = os.environ.get("URISYS_VDISPLAY_AGENT_LOG", "/tmp/vdisplay-agent.log")
    proc = subprocess.Popen(
        ["vdisplay-agent", "serve", "--port", str(port)],
        stdout=open(log, "a", encoding="utf-8"),
        stderr=subprocess.STDOUT,
        env=os.environ.copy(),
        start_new_session=True,
    )
    for _ in range(30):
        if _agent_up():
            return {"ok": True, "pid": proc.pid, "log": log, "started": True}
        time.sleep(0.2)
    return {"ok": False, "error": "vdisplay-agent did not become healthy", "pid": proc.pid, "log": log}


def _start_screencast() -> dict[str, Any]:
    if shutil.which("vdisplay") is None:
        return {"ok": False, "error": "vdisplay CLI not installed", "skipped": True}
    if _screencast_ready():
        return {"ok": True, "already_ready": True}
    env = os.environ.copy()
    env.setdefault("VDISPLAY_AGENT_URL", _agent_url())
    proc = subprocess.run(
        ["vdisplay", "agent", "screencast", "start", "--force"],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
        check=False,
    )
    ready = _screencast_ready()
    return {
        "ok": ready,
        "exit_code": proc.returncode,
        "stdout": (proc.stdout or "")[-500:],
        "stderr": (proc.stderr or "")[-500:],
        "capture_ready": ready,
        "note": "first run may need portal consent on the physical display",
    }


def bootstrap_wayland_capture() -> dict[str, Any]:
    """Called once when urisys node serve starts. Idempotent."""
    if os.environ.get("URISYS_DISPLAY_BOOTSTRAP", "1") != "1":
        return {"ok": True, "skipped": True, "reason": "URISYS_DISPLAY_BOOTSTRAP=0"}
    if (os.environ.get("XDG_SESSION_TYPE") or "").lower() != "wayland":
        return {"ok": True, "skipped": True, "reason": "not wayland"}

    _ensure_session_env()
    port = int(os.environ.get("VDISPLAY_AGENT_PORT", "8765"))
    os.environ.setdefault("VDISPLAY_AGENT_URL", f"http://127.0.0.1:{port}")

    out: dict[str, Any] = {"session": "wayland", "agent_url": _agent_url()}
    if not _agent_up():
        out["agent"] = _start_agent(port)
    else:
        out["agent"] = {"ok": True, "already_running": True}

    if out.get("agent", {}).get("ok") and os.environ.get("URISYS_AUTO_SCREENCAST", "1") == "1":
        out["screencast"] = _start_screencast()
    else:
        out["screencast"] = {"ok": False, "skipped": True}

    out["ok"] = bool(out.get("agent", {}).get("ok"))
    return out
