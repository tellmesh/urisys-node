"""Node profile auto-discovery — a freshly started node must not silently run on mock.

resolve_node_config searches URISYS_NODE_CONFIG → CWD → ~/.config/urisys → URISYS_NODE_DATA
→ /etc/urisys, so `urisys node serve` from any CWD finds the operator's profile.
"""

from __future__ import annotations

import json

from urisysnode.serve import resolve_node_config


def test_env_var_wins(tmp_path, monkeypatch):
    prof = tmp_path / "p.json"
    prof.write_text(json.dumps({"kvm": {"driver": "mss"}}))
    monkeypatch.setenv("URISYS_NODE_CONFIG", str(prof))
    monkeypatch.chdir(tmp_path)
    assert resolve_node_config() == str(prof.resolve())


def test_discovers_xdg_profile_when_env_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("URISYS_NODE_CONFIG", raising=False)
    monkeypatch.delenv("URISYS_NODE_DATA", raising=False)
    home = tmp_path / "home"
    cfg = home / ".config" / "urisys"
    cfg.mkdir(parents=True)
    prof = cfg / "node-profile.json"
    prof.write_text(json.dumps({"kvm": {"driver": "mss"}}))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(tmp_path)  # no CWD config/ here
    assert resolve_node_config() == str(prof.resolve())


def test_explicit_arg_beats_env(tmp_path, monkeypatch):
    arg = tmp_path / "arg.json"
    arg.write_text("{}")
    monkeypatch.setenv("URISYS_NODE_CONFIG", str(tmp_path / "env.json"))  # nonexistent
    assert resolve_node_config(str(arg)) == str(arg.resolve())


def test_returns_empty_when_none(tmp_path, monkeypatch):
    monkeypatch.delenv("URISYS_NODE_CONFIG", raising=False)
    monkeypatch.delenv("URISYS_NODE_DATA", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
    monkeypatch.chdir(tmp_path)
    assert resolve_node_config() == ""


def test_default_real_config_wayland(monkeypatch):
    from urisysnode.serve import _default_real_config
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.delenv("URISYS_HIM_DRIVER", raising=False)
    cfg = _default_real_config()
    assert cfg["kvm"]["driver"] == "auto"
    assert cfg["him"]["driver"] == "ydotool"
    assert cfg["screen"]["default_backend"] == "auto"


def test_default_real_config_x11(monkeypatch):
    from urisysnode.serve import _default_real_config
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.delenv("URISYS_HIM_DRIVER", raising=False)
    assert _default_real_config()["him"]["driver"] == "xdotool"
