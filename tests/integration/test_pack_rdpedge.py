def test_pack_modules_rdpedge():
    from urisysnode.pack_resolver import (
        PACK_GITHUB_REPO,
        PACK_PYPI,
        github_wheel_url,
        pack_module,
    )

    assert pack_module("rdp") == "urirdp"
    assert pack_module("rdpedge") == "urirdpedge"
    assert "urirdpedge" in PACK_PYPI["rdpedge"]
    assert PACK_GITHUB_REPO["rdpedge"] == "urirdpedge"
    url = github_wheel_url("rdpedge")
    assert url and "urirdpedge-0.1.0" in url
