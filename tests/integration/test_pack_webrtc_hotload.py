"""Hot-load webrtc pack from standalone uriwebrtc wheel."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

PKG = Path(__file__).resolve().parents[1] / "packages" / "python"
TELLMESH = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PKG))
for _rel in ("uriwebrtc", "uristt", "uricore"):
    _p = TELLMESH / _rel
    if _p.is_dir():
        sys.path.insert(0, str(_p))

from uri_control.edge.runtime import Runtime  # noqa: E402
import urisysnode.routes as node_routes  # noqa: E402
from urisysnode.serve import load_pack_into_runtime  # noqa: E402


def _node_only_runtime(tmp_path) -> Runtime:
    rt = Runtime(events_path=str(tmp_path / "events.jsonl"))
    node_routes.register(rt)
    rt._loaded_packs = {"node"}
    return rt


@patch("urisysnode.serve.auto_install_enabled", return_value=False)
def test_hotload_webrtc_adds_routes(_auto, tmp_path):
    rt = _node_only_runtime(tmp_path)
    result = load_pack_into_runtime(rt, "webrtc")
    assert result["ok"] is True
    assert result["loaded"] is True
    assert any(p.startswith("webrtc://") for p in result["new_routes"])


@patch("urisysnode.serve.auto_install_enabled", return_value=False)
def test_webrtc_session_start_after_hotload(_auto, tmp_path):
    rt = _node_only_runtime(tmp_path)
    load_pack_into_runtime(rt, "webrtc")
    out = rt.call(
        "webrtc://local/session/rdp-chat/command/start",
        {"room": "rdp-lab"},
        {"approved": True},
    )
    assert out["ok"] is True
    assert out["result"]["webrtc"]["room"] == "rdp-lab"
