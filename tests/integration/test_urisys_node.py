import json
import os
import tempfile
from pathlib import Path

import pytest

os.environ["URISYS_NODE_SKIP_PAIRING"] = "1"
os.environ["URISYS_NODE_DATA"] = tempfile.mkdtemp()
os.environ["URISYS_NODE_PACKS"] = "node,screen"
os.environ["URISYS_NODE_ISOLATION"] = "off"



def test_identity_and_enroll():
    from urisysnode.identity import enroll, load_identity, load_pairing

    identity = load_identity()
    assert identity["node_id"]
    assert identity["fingerprint"]
    pairing = enroll("https://controller.local", code="482913")
    assert pairing["paired"] is True
    assert load_pairing()["controller"] == "https://controller.local"


def test_screen_capture_mock():
    from urisysnode.serve import build_runtime

    rt = build_runtime()
    res = rt.call(
        "screen://local/monitor/1/command/capture",
        {"monitor": 1, "output": os.environ["URISYS_NODE_DATA"]},
        {"approved": True, "dry_run": True},
    )
    assert res["ok"]
    assert res["result"]["backend"] == "mock"
    assert Path(res["result"]["path"]).exists()


def test_rewrite_uri_for_slave():
    from urisysnode.router import rewrite_uri_for_slave

    uri = rewrite_uri_for_slave("kvm://slave-01/task/command/click-text", "slave-01", "local")
    assert uri == "kvm://local/task/command/click-text"
    assert rewrite_uri_for_slave("kv://lenovo/runtime/query/health", "lenovo", "local") == "kv://runtime/query/health"
    assert rewrite_uri_for_slave("log://lenovo/events/query/summarize", "lenovo", "local") == "log://events/query/summarize"
    assert rewrite_uri_for_slave("urioffice://lenovo/writer/command/render", "lenovo", "local") == "urioffice://local/writer/command/render"


def test_health_payload():
    from urisysnode.identity import health_payload

    data = health_payload()
    assert data["ok"] is True
    assert data["service"] == "urisys-node"
    assert "python" in data
    assert "python_executable" in data
    assert "urisys" in data


def test_health_payload_with_runtime():
    from urisysnode.identity import health_payload
    from urisysnode.serve import build_runtime

    rt = build_runtime()
    data = health_payload(runtime=rt)
    assert "packs_loaded" in data
    assert "node" in data["packs_loaded"]
    assert "routes_count" in data
