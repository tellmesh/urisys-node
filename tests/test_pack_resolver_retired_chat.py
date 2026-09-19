from types import SimpleNamespace
from unittest.mock import patch

import pytest

from urisysnode import pack_resolver as resolver
from urisysnode.runtime.packs import ensure_pack_for_uri, load_pack_into_runtime


@pytest.mark.parametrize("pack", ["chat", "urichat"])
def test_retired_pack_never_imports_or_installs(pack, tmp_path, monkeypatch):
    monkeypatch.setenv("URISYS_WHEELHOUSE", str(tmp_path))
    (tmp_path / f"{pack}-99.0.0-py3-none-any.whl").touch()
    with patch.object(resolver.importlib, "import_module") as imported, patch.object(resolver, "_pip_install") as pip:
        assert resolver.resolve_pack_source(pack) is None
        assert resolver.pack_install_specs(pack, ["urichat>=0.1.0"]) == []
        assert resolver.pack_importable(pack) is False
        assert resolver.ensure_boot_pack(pack)["ok"] is False
        result = resolver.ensure_pack_pypi(pack, specs=["urichat>=0.1.0"])
        assert not result["ok"]
        assert "retired" in result["error"]
        imported.assert_not_called()
        pip.assert_not_called()


@pytest.mark.parametrize("pack", ["chat", "urichat"])
def test_hot_load_rejects_retired_pack_before_mutating_runtime(pack):
    runtime = SimpleNamespace()
    with patch.object(resolver, "_pip_install") as pip:
        result = load_pack_into_runtime(runtime, pack, install=True, force=True)
    assert not result["ok"]
    assert "llm" in result["error"] and "message" in result["error"]
    assert not hasattr(runtime, "_loaded_packs")
    pip.assert_not_called()


def test_chat_uri_does_not_trigger_lazy_loading():
    with patch("urisysnode.runtime.packs.load_pack_into_runtime") as load:
        assert ensure_pack_for_uri(SimpleNamespace(), "chat://local/uri/command/execute") is None
    load.assert_not_called()
    assert resolver.pack_for_scheme("llm") == "llm"
    assert resolver.pack_for_scheme("message") == "message"
    assert resolver.pack_module("llm") == "urillm"
    assert resolver.pack_module("message") == "urimessage"
