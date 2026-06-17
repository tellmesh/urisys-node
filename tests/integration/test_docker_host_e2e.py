"""Host → Docker urisys-node GUI E2E (optional, requires Docker).

Run full stack:
  bash scripts/run-urisys-node-docker-e2e.sh

Or pytest gate:
  URISYS_NODE_DOCKER_E2E=1 pytest urisys-node/tests/test_docker_host_e2e.py -q
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "docker" / "docker-compose.gui.yml"
CFG = ROOT / "docker" / "config"
PORT = int(os.environ.get("URISYS_NODE_HOST_PORT", "8790"))
BASE = f"http://127.0.0.1:{PORT}"
CONTAINER = os.environ.get("URISYS_NODE_CONTAINER", "urisys-node-gui")

pytestmark = pytest.mark.skipif(
    os.environ.get("URISYS_NODE_DOCKER_E2E") != "1",
    reason="set URISYS_NODE_DOCKER_E2E=1 to run Docker host-control E2E",
)


def _http_get(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE}{path}", timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _remote_call(uri: str, payload: dict | None = None, context: dict | None = None) -> dict:
    body = json.dumps(
        {"uri": uri, "payload": payload or {}, "context": context or {"approved": True}}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}/uri/call",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


@pytest.fixture(scope="module")
def docker_stack():
    if not shutil.which("docker"):
        pytest.skip("docker not available")
    subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE), "build"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE), "up", "-d"],
        cwd=ROOT,
        check=True,
    )
    deadline = time.time() + 120
    while time.time() < deadline:
        try:
            data = _http_get("/health")
            if data.get("ok"):
                break
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(2)
    else:
        subprocess.run(["docker", "compose", "-f", str(COMPOSE), "logs"], cwd=ROOT)
        pytest.fail("urisys-node health timeout")
    yield _http_get("/health")
    if os.environ.get("URISYS_NODE_E2E_KEEP") != "1":
        subprocess.run(["docker", "compose", "-f", str(COMPOSE), "down", "-v"], cwd=ROOT)


def test_container_urisys_cli(docker_stack):
    proc = subprocess.run(
        ["docker", "exec", CONTAINER, "urisys", "--help"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "call" in proc.stdout


def test_host_health_and_routes(docker_stack):
    assert docker_stack.get("service") == "urisys-node"
    routes = _http_get("/uri/routes")
    patterns = " ".join(routes.get("routes") or [])
    assert "screen://" in patterns
    assert "node://" in patterns


def test_host_remote_identity(docker_stack):
    node_id = docker_stack["node_id"]
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT / 'urisys-node' / 'packages' / 'python'}:{ROOT / 'src'}"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "urisysnode.cli",
            "call",
            f"node://{node_id}/query/identity",
            "--route-map",
            str(CFG / "route-map.host.yaml"),
            "--nodes-registry",
            str(CFG / "nodes.registry.host.json"),
            "--approve",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=ROOT,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    data = json.loads(proc.stdout)
    assert data.get("ok") is True
    assert data["result"]["node_id"] == node_id


def test_host_screen_capture(docker_stack):
    res = _remote_call(
        "screen://local/monitor/primary/command/capture",
        {"monitor": 1},
        {"approved": True, "allow_real": True},
    )
    assert res.get("ok") is True
    path = (res.get("result") or {}).get("path")
    assert path
    size_proc = subprocess.run(
        ["docker", "exec", CONTAINER, "stat", "-c%s", path],
        capture_output=True,
        text=True,
    )
    assert int(size_proc.stdout.strip() or "0") > 500


def test_host_indicator_control():
    on = _remote_call("node://local/command/indicator-on", {"message": "pytest"})
    assert on.get("ok") is True
    assert (on.get("result") or {}).get("remote_control_active") is True
    off = _remote_call("node://local/command/indicator-off")
    assert off.get("ok") is True
    assert (off.get("result") or {}).get("remote_control_active") is False
