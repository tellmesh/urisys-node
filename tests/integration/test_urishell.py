"""urishell bundled with urisys node."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

PKG = Path(__file__).resolve().parents[1] / "packages" / "python"
sys.path.insert(0, str(PKG))

from urisysedge.runtime import Runtime  # noqa: E402
import urishell.routes as shell_routes  # noqa: E402


def test_shell_route_registered():
    rt = Runtime()
    shell_routes.register(rt)
    assert any("shell://" in r.pattern for r in rt.routes)


def test_shell_pip_dry_run():
    rt = Runtime()
    shell_routes.register(rt)
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
    shell_routes.register(rt)
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
