"""`urisys node serve` takes over its port: the old listener is killed so a
fresh serve can bind, behaving like an atomic restart (no external pkill)."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "packages" / "python"
sys.path.insert(0, str(PKG))

from urisysnode.serve import _collect_takeover_targets, _pids_on_port, takeover_port  # noqa: E402

HERE = Path(__file__).resolve().parent


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_listen(port: int, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.2)
    return False


def test_takeover_does_not_target_shell_wrappers():
    """Shell one-liners that mention ``urisys node serve --port N`` must not be killed."""
    port = _free_port()
    self_pid = os.getpid()
    # Simulate a bash wrapper cmdline without holding the listen socket.
    targets = _collect_takeover_targets(port, self_pid)
    assert self_pid not in targets
    assert os.getppid() not in targets or os.getppid() == 1


def test_takeover_kills_old_listener():
    port = _free_port()
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(HERE), str(PKG), env.get("PYTHONPATH", "")])
    proc = subprocess.Popen(
        [sys.executable, "-m", "urisysnode.worker", "--module", "_fakepack", "--host", "127.0.0.1", "--port", str(port)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        assert _wait_listen(port), "old listener never came up"
        assert proc.pid in _pids_on_port(port)

        result = takeover_port("127.0.0.1", port)

        assert proc.pid in result["killed"]
        assert result["port_free"] is True
        # terminated (reaped here; in production the old proc is not our child
        # so init reaps it and _pid_alive would be False)
        assert proc.wait(timeout=5) is not None
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=5)
