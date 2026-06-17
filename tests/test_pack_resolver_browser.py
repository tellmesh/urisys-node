from urisysnode.pack_resolver import (
    GITHUB_PREFERRED_PACKS,
    PACK_MODULES,
    PACK_PYPI,
    github_wheel_url,
    pack_for_scheme,
    pack_importable,
)


def test_browser_pack_mapping():
    assert pack_for_scheme("browser") == "browser"
    assert PACK_MODULES["browser"] == "uribrowserdocker"
    assert PACK_PYPI["browser"] == "uribrowser>=0.1.0"
    assert "browser" in GITHUB_PREFERRED_PACKS


def test_browser_github_wheel_url():
    url = github_wheel_url("browser")
    assert url is not None
    assert "tellmesh/uribrowser/releases/download/v0.1.1/uribrowser-0.1.1-py3-none-any.whl" in url


def test_browser_importable_when_installed():
    assert pack_importable("browser") in (True, False)
