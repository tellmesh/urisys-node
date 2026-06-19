"""Port utility functions for process management."""

from __future__ import annotations

import errno
import os
import re
import shutil
import subprocess
from pathlib import Path

from urisysnode.identity import default_events_path


def _pidfile_path(port: int) -> Path:
    """Get the path to the PID file for a given port."""
    return Path(default_events_path()).parent / f"urisys-node.{port}.pid"


def _pid_alive(pid: int) -> bool:
    """Check if a process with the given PID is alive."""
    try:
        os.kill(pid, 0)
        return True
    except OSError as exc:
        return exc.errno == errno.EPERM


def _read_cmdline(pid: int) -> str:
    """Read the command line of a process from /proc."""
    try:
        raw = (Path("/proc") / str(pid) / "cmdline").read_bytes()
    except OSError:
        return ""
    return raw.replace(b"\0", b" ").decode("utf-8", errors="replace")


def _pids_serve_cmdline(port: int) -> list[int]:
    """PIDs whose cmdline looks like ``urisys node serve`` / ``urisys-node serve`` on ``port``."""
    port_s = str(port)
    pids: list[int] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        cmd = _read_cmdline(pid).lower()
        if "serve" not in cmd:
            continue
        if port_s not in cmd:
            continue
        if "urisys" not in cmd and "urisys-node" not in cmd:
            continue
        pids.append(pid)
    return pids


def _pids_on_port_ss(port: int) -> list[int]:
    """Parse ``ss -ltnp`` for listeners on ``port`` (fallback when /proc/fd scan misses)."""
    try:
        proc = subprocess.run(
            ["ss", "-ltnp", f"sport = :{port}"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []
    pids: list[int] = []
    for match in re.finditer(r"pid=(\d+)", proc.stdout or ""):
        try:
            pids.append(int(match.group(1)))
        except ValueError:
            continue
    return pids


def _fuser_kill_port(port: int) -> bool:
    """Last-resort: ``fuser -k PORT/tcp`` when pid discovery failed."""
    if not shutil.which("fuser"):
        return False
    try:
        subprocess.run(
            [shutil.which("fuser") or "fuser", "-k", f"{port}/tcp"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return True
    except (subprocess.TimeoutExpired, OSError):
        return False
