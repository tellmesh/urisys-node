"""pack_resolver mappings for office/mail/vql MVP packs."""

from __future__ import annotations

import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "packages" / "python"
sys.path.insert(0, str(PKG))

from urisysnode.pack_resolver import (  # noqa: E402
    PACK_MODULES,
    pack_for_scheme,
    pack_module,
)


def test_scheme_to_pack_office_mail_vql():
    assert pack_for_scheme("urioffice") == "office"
    assert pack_for_scheme("urimail") == "mail"
    assert pack_for_scheme("vql") == "vql"
    assert pack_for_scheme("browser") == "browser"


def test_pack_modules_office_mail_vql():
    assert pack_module("office") == "urioffice"
    assert pack_module("mail") == "urimail"
    assert pack_module("vql") == "urivql"
    assert "office" in PACK_MODULES
