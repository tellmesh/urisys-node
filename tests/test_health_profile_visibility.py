"""/health exposes whether the node runs on a real profile or fell back to mock."""

from __future__ import annotations

from urisysnode.identity import health_payload


class _RT:
    def __init__(self, config, config_path):
        self.config = config
        self._config_path = config_path
        self._loaded_packs = {"node"}
        self.routes = []
        self._instance_id = "test"


def test_profile_loaded_is_visible():
    rt = _RT({"kvm": {"driver": "mss"}, "screen": {"default_backend": "portal"}},
             "/home/u/.config/urisys/node-profile.json")
    h = health_payload(runtime=rt)
    assert h["config_source"].startswith("profile:")
    assert h["profile_path"].endswith("node-profile.json")
    assert h["kvm_driver"] == "mss"
    assert h["screen_backend"] == "portal"
    assert h["mock_mode"] is False


def test_mock_when_no_profile():
    h = health_payload(runtime=_RT({}, ""))
    assert h["config_source"] == "mock (no profile)"
    assert h["kvm_driver"] == "mock"
    assert h["mock_mode"] is True


def test_auto_default_source_visible():
    rt = _RT({"_source": "auto-default (no profile; URISYS_ALLOW_REAL=1)", "kvm": {"driver": "auto"}}, "")
    h = health_payload(runtime=rt)
    assert "auto-default" in h["config_source"]
    assert h["kvm_driver"] == "auto"
