"""Registry-independent pack resolution: local wheelhouse → GitHub → PyPI."""

from __future__ import annotations

import pytest

from urisysnode import pack_resolver as pr


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    # Keep GitHub resolution deterministic (no network) and clear the latest cache.
    monkeypatch.setenv("URISYS_OFFLINE", "1")
    pr._gh_latest_cache.clear()


def _wheelhouse(tmp_path, *names: str) -> str:
    for n in names:
        (tmp_path / n).write_bytes(b"")
    return str(tmp_path)


def test_dist_name_strips_constraints_and_extras():
    assert pr._dist_name("kv") == "urikv"
    assert pr._dist_name("llm") == "urillm"  # from "urillm[vision]>=0.1.0"


def test_local_wheel_picks_newest(tmp_path, monkeypatch):
    wh = _wheelhouse(
        tmp_path,
        "urikv-0.1.0-py3-none-any.whl",
        "urikv-0.1.3-py3-none-any.whl",
        "uribrowser-0.1.1-py3-none-any.whl",
    )
    monkeypatch.setenv("URISYS_WHEELHOUSE", wh)
    found = pr.local_wheel("kv")
    assert found is not None
    assert found.endswith("urikv-0.1.3-py3-none-any.whl")


def test_local_wheel_absent_when_no_match(tmp_path, monkeypatch):
    monkeypatch.setenv("URISYS_WHEELHOUSE", _wheelhouse(tmp_path, "other-1.0-py3-none-any.whl"))
    assert pr.local_wheel("kv") is None


def test_auto_prefers_local_over_github(tmp_path, monkeypatch):
    wh = _wheelhouse(tmp_path, "urikv-0.2.0-py3-none-any.whl")
    monkeypatch.setenv("URISYS_WHEELHOUSE", wh)
    monkeypatch.setenv("URISYS_PACK_SOURCE", "auto")
    src = pr.resolve_pack_source("kv")
    assert src["kind"] == "local"
    assert src["spec"].endswith("urikv-0.2.0-py3-none-any.whl")
    assert src["find_links"] == wh


def test_auto_falls_back_to_github_pinned_when_offline(tmp_path, monkeypatch):
    monkeypatch.setenv("URISYS_WHEELHOUSE", str(tmp_path))  # empty
    monkeypatch.setenv("URISYS_PACK_SOURCE", "auto")
    src = pr.resolve_pack_source("browser")
    assert src["kind"] == "github"
    assert "tellmesh/uribrowser/releases/download/v0.1.1/" in src["spec"]


def test_forced_pypi_source(tmp_path, monkeypatch):
    monkeypatch.setenv("URISYS_WHEELHOUSE", _wheelhouse(tmp_path, "urikv-9.9.9-py3-none-any.whl"))
    monkeypatch.setenv("URISYS_PACK_SOURCE", "pypi")
    src = pr.resolve_pack_source("kv")
    assert src["kind"] == "pypi"
    assert src["spec"] == "urikv>=0.1.0"


def test_offline_flag_sets_no_index(tmp_path, monkeypatch):
    monkeypatch.setenv("URISYS_WHEELHOUSE", _wheelhouse(tmp_path, "urikv-0.1.0-py3-none-any.whl"))
    monkeypatch.setenv("URISYS_WHEELHOUSE_OFFLINE", "1")
    src = pr.resolve_pack_source("kv")
    assert src["kind"] == "local"
    assert src.get("no_index") is True


def test_pip_install_adds_find_links(tmp_path, monkeypatch):
    monkeypatch.setenv("URISYS_WHEELHOUSE", _wheelhouse(tmp_path, "urikv-0.1.0-py3-none-any.whl"))
    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd

        class R:
            returncode = 0
            stdout = ""
            stderr = ""

        return R()

    monkeypatch.setattr(pr.subprocess, "run", fake_run)
    pr._pip_install(["urikv"])
    assert "--find-links" in captured["cmd"]
    assert str(tmp_path) in captured["cmd"]


def test_github_wheel_url_back_compat():
    # Existing behaviour: pinned version URL, no network.
    url = pr.github_wheel_url("browser")
    assert url.endswith("tellmesh/uribrowser/releases/download/v0.1.1/uribrowser-0.1.1-py3-none-any.whl")
