"""An empty/corrupt node profile must not crash `urisys node serve` (build_runtime).

Regression: resolve_node_config found a profile file, load_json hit JSONDecodeError on an
empty file, and the whole node failed to start.
"""

from __future__ import annotations

import pytest

from urisysnode import serve


@pytest.fixture(autouse=True)
def _minimal_node(tmp_path, monkeypatch):
    monkeypatch.setenv("URISYS_NODE_PACKS", "node")
    monkeypatch.delenv("URISYS_NODE_WORKER_PACKS", raising=False)
    monkeypatch.delenv("URISYS_ALLOW_REAL", raising=False)
    monkeypatch.setenv("URISYS_NODE_EVENTS", str(tmp_path / "events.jsonl"))


def test_empty_profile_does_not_crash(tmp_path, monkeypatch):
    prof = tmp_path / "node-profile.json"
    prof.write_text("")  # empty file → previously JSONDecodeError at startup
    monkeypatch.setenv("URISYS_NODE_CONFIG", str(prof))
    rt = serve.build_runtime()
    assert rt is not None
    assert rt.config == {}


def test_garbage_profile_does_not_crash(tmp_path, monkeypatch):
    prof = tmp_path / "node-profile.json"
    prof.write_text("not json {{{")
    monkeypatch.setenv("URISYS_NODE_CONFIG", str(prof))
    rt = serve.build_runtime()
    assert rt.config == {}


def test_empty_profile_with_allow_real_uses_defaults(tmp_path, monkeypatch):
    prof = tmp_path / "node-profile.json"
    prof.write_text("")
    monkeypatch.setenv("URISYS_NODE_CONFIG", str(prof))
    monkeypatch.setenv("URISYS_ALLOW_REAL", "1")
    rt = serve.build_runtime()
    # invalid profile ignored → falls through to real-driver defaults, not a crash
    assert rt.config.get("kvm", {}).get("driver") == "auto"
