"""Hot-loading capability packs into a live node runtime.

This is the mechanism that lets a minimally-installed node gain new URI handlers
over the wire (POST /uri/pack) and then run those tasks autonomously, without a
restart. The runtime extension itself is tested here; the HTTP endpoint is a
thin, env-gated wrapper around load_pack_into_runtime.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PKG = Path(__file__).resolve().parents[1] / "packages" / "python"
sys.path.insert(0, str(PKG))

from uri_control.edge.runtime import Runtime  # noqa: E402
import urisysnode.routes as node_routes  # noqa: E402
from urisysnode.serve import load_pack_into_runtime  # noqa: E402


def _node_only_runtime(tmp_path) -> Runtime:
    rt = Runtime(events_path=str(tmp_path / "events.jsonl"))
    node_routes.register(rt)
    rt._loaded_packs = {"node"}
    return rt


def test_hotload_adds_routes(tmp_path):
    rt = _node_only_runtime(tmp_path)
    assert not any(r.pattern.startswith("screen://") for r in rt.routes)

    result = load_pack_into_runtime(rt, "screen")

    assert result["ok"] is True
    assert result["loaded"] is True
    assert any(p.startswith("screen://") for p in result["new_routes"])
    # the new capability is now live on the runtime
    assert any(r.pattern.startswith("screen://") for r in rt.routes)


def test_hotload_is_idempotent(tmp_path):
    rt = _node_only_runtime(tmp_path)
    load_pack_into_runtime(rt, "screen")
    n_after_first = len(rt.routes)

    again = load_pack_into_runtime(rt, "screen")

    assert again["already_loaded"] is True
    assert again["new_routes"] == []
    assert len(rt.routes) == n_after_first  # no duplicate routes


def test_hotload_empty_pack_name_rejected(tmp_path):
    result = load_pack_into_runtime(_node_only_runtime(tmp_path), "")
    assert result["ok"] is False


def test_hotload_unknown_pack_reports_failure(tmp_path):
    result = load_pack_into_runtime(_node_only_runtime(tmp_path), "does-not-exist")
    assert result["ok"] is False
    assert result["loaded"] is False
