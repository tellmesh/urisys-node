"""Lazy pack install via URI (urisys node serve)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from urisysedge.runtime import Runtime  # noqa: E402
import urisysnode.routes as node_routes  # noqa: E402
from urisysnode.serve import call_uri, load_pack_into_runtime  # noqa: E402


def _node_only_runtime(tmp_path) -> Runtime:
    rt = Runtime(events_path=str(tmp_path / "events.jsonl"))
    node_routes.register(rt)
    rt._loaded_packs = {"node"}
    return rt


def test_install_pack_uri(tmp_path):
    rt = _node_only_runtime(tmp_path)
    with patch("urisysnode.pack_resolver._pip_install", return_value={"ok": True, "exit_code": 0}):
        with patch("urisysnode.serve._register_pack", return_value=True) as reg:
            result = rt.call(
                "node://local/command/install-pack",
                {"pack": "kvm"},
                {"approved": True, "runtime": rt},
            )
    assert result["ok"] is True
    reg.assert_called_once()


def test_install_pack_requires_approval(tmp_path):
    rt = _node_only_runtime(tmp_path)
    result = rt.call(
        "node://local/command/install-pack",
        {"pack": "kvm"},
        {"approved": False, "runtime": rt},
    )
    assert result["ok"] is False


def test_query_packs(tmp_path):
    rt = _node_only_runtime(tmp_path)
    rt._loaded_packs = {"node", "screen"}
    result = rt.call("node://local/query/packs", {}, {"runtime": rt})
    assert result["ok"] is True
    assert "node" in result["result"]["loaded"]
    assert "kvm" in result["result"]["available"]


def test_call_uri_lazy_pack_route_not_found(tmp_path):
    rt = _node_only_runtime(tmp_path)
    with patch("urisysnode.serve.ensure_pack_for_uri") as ensure:
        ensure.return_value = {"ok": True, "loaded": True, "pack": "kvm"}
        with patch.object(rt, "call", side_effect=[
            {"ok": False, "type": "route_not_found", "uri": "kvm://local/monitor/1/query/screenshot"},
            {"ok": True, "uri": "kvm://local/monitor/1/query/screenshot", "result": {}},
        ]) as mock_call:
            out = call_uri(rt, "kvm://local/monitor/1/query/screenshot", {}, {"approved": True})
    assert out["ok"] is True
    ensure.assert_called_once()
    assert mock_call.call_count == 2


def test_load_pack_with_mock_pip(tmp_path):
    rt = _node_only_runtime(tmp_path)
    with patch("urisysnode.pack_resolver._pip_install", return_value={"ok": True, "exit_code": 0}):
        with patch("urisysnode.serve._register_pack", return_value=True):
            result = load_pack_into_runtime(rt, "kvm", install=True)
    assert result["ok"] is True
    assert "pip" in result


def test_ensure_pack_for_uri_skips_pip_when_importable(tmp_path):
    from urisysnode.serve import ensure_pack_for_uri

    rt = _node_only_runtime(tmp_path)
    with patch("urisysnode.pack_resolver._pip_install") as pip:
        with patch("urisysnode.serve._register_pack", return_value=True):
            with patch("urisysnode.serve.pack_importable", return_value=True):
                ensure_pack_for_uri(rt, "him://local/mouse/query/status")
    pip.assert_not_called()
    assert "him" in rt._loaded_packs


def test_force_reload_reregister_pack(tmp_path):
    rt = _node_only_runtime(tmp_path)
    pattern = "him://{host}/mouse/query/status"
    rt.register(
        pattern,
        "python://urihim.handlers:mouse_status",
        kind="query",
        operation="him.mouse.status",
    )
    rt._loaded_packs.add("him")
    rt._pack_route_patterns = {"him": {pattern}}
    with patch("urisysnode.serve._register_pack", return_value=True) as reg:
        result = load_pack_into_runtime(rt, "him", force=True)
    assert result["ok"] is True
    assert reg.called
    assert "him" in rt._loaded_packs


def test_pack_importable_uses_import_pack_module():
    from urisysnode.pack_resolver import import_pack_module, pack_importable

    import_pack_module("node")
    assert pack_importable("node") is True
    assert pack_importable("no-such-pack-xyz") is False
