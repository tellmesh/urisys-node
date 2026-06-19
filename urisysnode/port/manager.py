"""Port management functions for process takeover and control."""

from __future__ import annotations

import errno
import json
import os
import signal
import socket
import time
from pathlib import Path
from typing import Any

from urisysnode.identity import default_events_path
from .utils import _fuser_kill_port, _pid_alive, _pidfile_path, _pids_on_port_ss, _pids_serve_cmdline, _read_cmdline


def _pids_on_port(port: int) -> list[int]:
    """Find PIDs holding a LISTEN socket on ``port`` via /proc (no deps)."""
    inodes: set[str] = set()
    for proto in ("tcp", "tcp6"):
        try:
            lines = Path(f"/proc/net/{proto}").read_text(encoding="utf-8").splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            parts = line.split()
            if len(parts) < 10 or parts[3] != "0A":  # 0A = LISTEN
                continue
            try:
                if int(parts[1].rsplit(":", 1)[1], 16) == port:
                    inodes.add(parts[9])
            except (ValueError, IndexError):
                continue
    if not inodes:
        return []
    pids: list[int] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            for fd in (entry / "fd").iterdir():
                try:
                    target = os.readlink(fd)
                except OSError:
                    continue
                if target.startswith("socket:[") and target[8:-1] in inodes:
                    pids.append(int(entry.name))
                    break
        except OSError:
            continue
    return pids


def _kill_pid(pid: int, *, timeout: float = 6.0) -> None:
    """Kill a process and wait for it to terminate."""
    try:
        pgid = os.getpgid(pid)
        if pgid == pid:
            os.killpg(pgid, signal.SIGTERM)
        else:
            os.kill(pid, signal.SIGTERM)
    except OSError:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not _pid_alive(pid):
            return
        time.sleep(0.2)
    try:
        pgid = os.getpgid(pid)
        if pgid == pid:
            os.killpg(pgid, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGKILL)
    except OSError:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    time.sleep(0.1)


def _worker_pids_from_state() -> list[int]:
    """PIDs persisted by PackSupervisor (out-of-process pack workers)."""
    state = Path("data/workers.json")
    if not state.is_file():
        alt = Path(default_events_path()).parent / "workers.json"
        if alt.is_file():
            state = alt
        else:
            return []
    try:
        records = json.loads(state.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    pids: list[int] = []
    for rec in records if isinstance(records, list) else []:
        try:
            pid = int(rec.get("pid") or 0)
        except (TypeError, ValueError):
            continue
        if pid > 0 and _pid_alive(pid):
            pids.append(pid)
    return pids


def _wait_port_free(host: str, port: int, *, timeout: float = 10.0) -> bool:
    """Wait for a port to become free."""
    bind_host = host if host not in ("", "0.0.0.0") else "0.0.0.0"
    deadline = time.time() + timeout
    while time.time() < deadline:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((bind_host, port))
            s.close()
            return True
        except OSError:
            s.close()
            time.sleep(0.25)
    return False


def _is_node_serve_process(pid: int, port: int, *, listeners: set[int] | None = None) -> bool:
    """True if ``pid`` is the urisys node HTTP listener (not a shell one-liner)."""
    if listeners and pid in listeners:
        return True
    cmd = _read_cmdline(pid)
    if not cmd:
        return False
    low = cmd.lower()
    argv0 = low.split(" ", 1)[0]
    if argv0.endswith(("bash", "sh", "dash", "zsh", "fish", "nohup", "setsid")):
        return False
    if " -c " in low and ("bash" in argv0 or "/bin/sh" in argv0):
        return False
    if "serve" not in low:
        return False
    if "urisys" not in low and "urisys-node" not in low and "urisysnode" not in low:
        return False
    if str(port) in cmd:
        return True
    try:
        for chunk in Path(f"/proc/{pid}/environ").read_bytes().split(b"\0"):
            if chunk.startswith(b"URISYS_NODE_PORT="):
                return int(chunk.split(b"=", 1)[1]) == port
    except (OSError, ValueError, IndexError):
        pass
    return False


def _collect_takeover_targets(port: int, self_pid: int) -> set[int]:
    """Collect PIDs that should be killed during port takeover."""
    listeners = set(_pids_on_port(port)) | set(_pids_on_port_ss(port))
    targets: set[int] = set()

    for pid in listeners:
        if pid != self_pid:
            targets.add(pid)

    pidfile = _pidfile_path(port)
    try:
        old = int(pidfile.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        old = 0
    if old and old != self_pid and _pid_alive(old):
        if old in listeners or _is_node_serve_process(old, port, listeners=listeners):
            targets.add(old)

    if targets:
        for pid in _worker_pids_from_state():
            if pid != self_pid:
                targets.add(pid)

    return targets


def takeover_port(host: str, port: int) -> dict[str, Any]:
    """Kill any existing urisys node on ``port`` so a fresh serve can bind it.

    This makes ``urisys node serve`` behave like an atomic restart: the old
    instance is terminated (pidfile, port listeners, cmdline match, workers),
    we wait for the port to free, then the caller binds. No external bash.
    """
    import os as _os
    import time as _time

    self_pid = _os.getpid()
    killed: list[int] = []
    used_fuser = False

    for attempt in range(3):
        targets = _collect_takeover_targets(port, self_pid)
        for pid in sorted(targets):
            if pid not in killed:
                _kill_pid(pid)
                killed.append(pid)
        if _wait_port_free(host, port, timeout=6.0):
            return {"killed": killed, "port_free": True, "attempts": attempt + 1, "fuser": used_fuser}
        _time.sleep(0.4)

    if not _wait_port_free(host, port, timeout=1.0):
        used_fuser = _fuser_kill_port(port)
        _time.sleep(0.5)

    freed = _wait_port_free(host, port, timeout=8.0)
    return {"killed": killed, "port_free": freed, "attempts": 3, "fuser": used_fuser}
