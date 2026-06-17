"""Hot-load webrtc pack from urisys-automation-lab wheel layout."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PKG = Path(__file__).resolve().parents[1] / "packages" / "python"
LAB = Path(__file__).resolve().parents[3] / "urisys-automation-lab"
sys.path.insert(0, str(PKG))
if LAB.is_dir():
    sys.path.insert(0, str(LAB))

from urisysedge.runtime import Runtime  # noqa: E402
import urisysnode.routes as node_routes  # noqa: E402
from urisysnode.serve import load_pack_into_runtime  # noqa: E402

pytestmark = pytest.mark.skipif(
    not (LAB / "uriwebrtc" / "routes.py").is_file(),
    reason="urisys-automation-lab not available",
)


def _node_only_runtime(tmp_path) -> Runtime:
    rt = Runtime(events_path=str(tmp_path / "events.jsonl"))
    node_routes.register(rt)
    rt._loaded_packs = {"node"}
    return rt


def test_hotload_webrtc_adds_routes(tmp_path):
    rt = _node_only_runtime(tmp_path)
    result = load_pack_into_runtime(rt, "webrtc")
    assert result["ok"] is True
    assert result["loaded"] is True
    assert any(p.startswith("webrtc://") for p in result["new_routes"])


def test_webrtc_session_start_after_hotload(tmp_path):
    rt = _node_only_runtime(tmp_path)
    load_pack_into_runtime(rt, "webrtc")
    out = rt.call(
        "webrtc://local/session/rdp-chat/command/start",
        {"room": "rdp-lab"},
        {"approved": True},
    )
    assert out["ok"] is True
    assert out["result"]["webrtc"]["room"] == "rdp-lab"
