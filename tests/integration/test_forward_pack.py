"""Forwarding a hot-loaded capability to a resolved worker.

This is the bridge between ArtifactResolver (resolve contract -> platform OCI
image -> run worker) and the node serving the scheme: once a worker is running,
register_forward_pack wires the contract's URI patterns so calls to the node
transparently forward to the worker.
"""

from __future__ import annotations

import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "packages" / "python"
sys.path.insert(0, str(PKG))

from urisysedge.runtime import Runtime  # noqa: E402
import urisysnode.forward as forward  # noqa: E402
from urisysnode.serve import register_forward_pack  # noqa: E402


def _runtime(tmp_path) -> Runtime:
    rt = Runtime(events_path=str(tmp_path / "events.jsonl"))
    rt._loaded_packs = set()
    return rt


def test_register_forward_adds_routes_and_target(tmp_path):
    rt = _runtime(tmp_path)
    result = register_forward_pack(
        rt, "stepper", "http://127.0.0.1:8791",
        ["stepper://{axis}/command/move", "stepper://{axis}/query/position"],
    )
    assert result["ok"] is True
    assert rt.config["forward_targets"]["stepper"] == "http://127.0.0.1:8791"
    assert any(r.pattern.startswith("stepper://") for r in rt.routes)
    # command pattern must require approval (side-effecting), query must not
    move = next(r for r in rt.routes if r.pattern.endswith("/command/move"))
    pos = next(r for r in rt.routes if r.pattern.endswith("/query/position"))
    assert move.approval == "required" and move.side_effects is True
    assert pos.approval == "not_required"


def test_call_forwards_to_worker(tmp_path, monkeypatch):
    rt = _runtime(tmp_path)
    register_forward_pack(rt, "stepper", "http://worker:8791", ["stepper://{axis}/query/position"])

    captured = {}

    def fake_remote_call(endpoint, uri, payload, context):
        captured.update(endpoint=endpoint, uri=uri, payload=payload, context=context)
        return {"ok": True, "result": {"position": 42}}

    monkeypatch.setattr(forward, "remote_call", fake_remote_call)

    out = rt.call("stepper://x/query/position", {"unit": "mm"}, {"approved": True, "runtime": "leaked?"})

    assert out["ok"] is True
    assert captured["endpoint"] == "http://worker:8791"
    assert captured["uri"] == "stepper://x/query/position"
    assert captured["payload"] == {"unit": "mm"}
    # runtime-injected / non-whitelisted context keys must not leak to the worker
    assert "runtime" not in captured["context"]
    assert captured["context"].get("approved") is True


def test_forward_without_target_fails_cleanly(tmp_path):
    rt = _runtime(tmp_path)
    register_forward_pack(rt, "stepper", "http://worker:8791", ["stepper://{axis}/query/position"])
    # a scheme with a route but no configured target (simulate by clearing targets)
    rt.config["forward_targets"].clear()
    out = rt.call("stepper://x/query/position", {}, {})
    assert out["ok"] is False
    assert out["result"]["type"] == "forward_no_target"
