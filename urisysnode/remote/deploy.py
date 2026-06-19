"""Deployment utilities for wheel building and serving."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from .config import default_wheel_host


def build_wheel(project_dir: str | Path, *, out_dir: str | Path = "/tmp/urisys-deploy") -> Path:
    import tomllib

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    meta = tomllib.loads(Path(project_dir, "pyproject.toml").read_text(encoding="utf-8"))["project"]
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", "-w", str(out), str(project_dir), "-q"],
        check=True,
    )
    pkg_name = meta["name"]
    ver = meta["version"]
    for candidate in (out / f"{pkg_name.replace('-', '_')}-{ver}-py3-none-any.whl", out / f"{pkg_name}-{ver}-py3-none-any.whl"):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"wheel not found in {out} for {pkg_name} {ver}")


def serve_wheels(
    directory: str | Path = "/tmp/urisys-deploy",
    *,
    host: str = "192.168.188.212",
    port: int = 8765,
) -> subprocess.Popen[Any]:
    return subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", host, "--directory", str(directory)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wheel_url(wheel_path: Path, *, base: str | None = None) -> str:
    base = (base or default_wheel_host()).rstrip("/")
    return f"{base}/{wheel_path.name}"
