"""urishell pack (standalone tellmesh/urishell)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from uri_control.edge.runtime import Runtime

urishell = pytest.importorskip("urishell", reason="urishell pack not installed in this env")


def test_shell_route_registered():
    rt = Runtime()
    urishell.register(rt)
    assert any("shell://" in r.pattern for r in rt.routes)


def test_shell_pip_dry_run():
    rt = Runtime()
    urishell.register(rt)
    out = rt.call(
        "shell://pip",
        {"args": ["install", "-U", "urihim"]},
        {"approved": True, "dry_run": True},
    )
    assert out["ok"] is True
    assert out["result"]["driver"] == "mock"
    assert out["result"]["command"] == "pip"


def test_shell_requires_allow_real():
    rt = Runtime()
    urishell.register(rt)
    with patch("urishell.handlers.subprocess.run") as run:
        run.return_value.returncode = 0
        run.return_value.stdout = "ok"
        run.return_value.stderr = ""
        out = rt.call(
            "shell://pip",
            {"args": ["--version"]},
            {"approved": True, "allow_real": True},
        )
    assert out["ok"] is True
    assert out["result"]["driver"] == "subprocess"
