"""Single-source urisysedge: canonical copy lives in tellmesh/urisysedge."""

from __future__ import annotations

from pathlib import Path

import pytest

TELLMESH = Path(__file__).resolve().parents[3]
CANONICAL_EDGE = TELLMESH / "urisysedge" / "urisysedge"
GUARDED_MODULES = ["runtime.py", "env.py"]


def test_canonical_urisysedge_present():
    for module in GUARDED_MODULES:
        path = CANONICAL_EDGE / module
        assert path.is_file(), f"missing canonical urisysedge/{module} at {path}"


def test_urisysedge_imports_from_canonical():
    import urisysedge
    from urisysedge.runtime import JsonlEventStore, Runtime

    assert JsonlEventStore is not None
    assert Runtime is not None
    assert urisysedge.__file__


@pytest.mark.parametrize("module", GUARDED_MODULES)
def test_no_vendored_duplicate_module(module: str):
    vendored = Path(__file__).resolve().parents[1] / "packages" / "python" / "urisysedge" / module
    assert not vendored.is_file(), (
        f"vendored urisys-node copy {vendored} should not exist — "
        "use tellmesh/urisysedge (pack_sync promote)"
    )
