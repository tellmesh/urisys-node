from urisysnode.pack_resolver import PACK_MODULES, SCHEME_TO_PACK, pack_for_scheme


def test_kv_and_log_scheme_mapping():
    assert pack_for_scheme("kv") == "kv"
    assert pack_for_scheme("log") == "kv"
    assert PACK_MODULES["kv"] == "urikv"
    assert SCHEME_TO_PACK["log"] == "kv"
