"""pack_resolver GitHub Releases install specs."""

from __future__ import annotations

import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "packages" / "python"
sys.path.insert(0, str(PKG))

from urisysnode.pack_resolver import (  # noqa: E402
    github_wheel_url,
    resolve_pack_spec,
)


def test_github_wheel_url_him():
    url = github_wheel_url("him")
    assert url == "https://github.com/tellmesh/urihim/releases/download/v0.1.3/urihim-0.1.3-py3-none-any.whl"


def test_resolve_pack_spec_auto_prefers_github_for_him():
    assert resolve_pack_spec("him").startswith("https://github.com/tellmesh/urihim/")


def test_resolve_pack_spec_kvm_stays_pypi():
    assert resolve_pack_spec("kvm") == "urikvm>=0.1.0"
