from urisysnode.pack_resolver import PACK_MODULES, SCHEME_TO_PACK, pack_for_scheme


def test_webrtc_scheme_mapping():
    assert pack_for_scheme("webrtc") == "webrtc"
    assert PACK_MODULES["webrtc"] == "uriwebrtc"
    assert PACK_MODULES["uriwebrtc"] == "uriwebrtc"
    assert SCHEME_TO_PACK["webrtc"] == "webrtc"
