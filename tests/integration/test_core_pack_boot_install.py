"""Boot-time auto-install for core packs (screen, shell)."""

from __future__ import annotations

import importlib
from unittest.mock import MagicMock, patch

import pytest

from uri_control.edge.runtime import Runtime  # noqa: E402
from urisysnode.runtime.builder import _register_pack  # noqa: E402


def _screen_import_once_then_ok(name, *args, **kwargs):
    if name == "uriscreen":
        if _screen_import_once_then_ok.fail:
            _screen_import_once_then_ok.fail = False
            raise ModuleNotFoundError("uriscreen", name="uriscreen")
        mod = MagicMock()
        mod.register = MagicMock()
        return mod
    return importlib.import_module(name, *args, **kwargs)


_screen_import_once_then_ok.fail = True


def test_core_pack_auto_install_on_boot(tmp_path):
    _screen_import_once_then_ok.fail = True
    rt = Runtime(events_path=str(tmp_path / "events.jsonl"))
    with patch("urisysnode.runtime.builder.auto_install_enabled", return_value=True):
        with patch("urisysnode.runtime.builder.ensure_boot_pack", return_value={"ok": True}) as pip:
            with patch("urisysnode.runtime.builder.importlib.import_module", side_effect=_screen_import_once_then_ok):
                ok = _register_pack(rt, "screen", try_install=True)
    assert ok is True
    pip.assert_called_once_with("screen", install=True)


def test_core_pack_boot_raises_when_auto_install_disabled(tmp_path):
    rt = Runtime(events_path=str(tmp_path / "events.jsonl"))
    with patch("urisysnode.runtime.builder.auto_install_enabled", return_value=False):
        with patch(
            "urisysnode.runtime.builder.importlib.import_module",
            side_effect=ModuleNotFoundError("uriscreen", name="uriscreen"),
        ):
            with pytest.raises(ModuleNotFoundError, match="uriscreen"):
                _register_pack(rt, "screen", try_install=True)


def test_core_pack_boot_raises_when_pip_fails(tmp_path):
    _screen_import_once_then_ok.fail = True
    rt = Runtime(events_path=str(tmp_path / "events.jsonl"))
    with patch("urisysnode.runtime.builder.auto_install_enabled", return_value=True):
        with patch(
            "urisysnode.runtime.builder.ensure_boot_pack",
            return_value={"ok": False, "error": "network"},
        ):
            with patch("urisysnode.runtime.builder.importlib.import_module", side_effect=_screen_import_once_then_ok):
                with pytest.raises(ModuleNotFoundError, match="core pack 'screen'"):
                    _register_pack(rt, "screen", try_install=True)
