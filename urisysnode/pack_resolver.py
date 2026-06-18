"""Lazy install for optional urisys-node capability packs (PyPI or GitHub Releases)."""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from typing import Any

# pack alias -> module exposing register(runtime)
PACK_MODULES: dict[str, str] = {
    "node": "urisysnode.routes",
    "screen": "uriscreen",
    "shell": "urishell",
    "kvm": "urikvm",
    "him": "urihim",
    "ocr": "uriocr",
    "llm": "urillm",
    "office": "urioffice",
    "mail": "urimail",
    "vql": "urivql",
    "img2nl": "uriimg2nl",
    "browser": "uribrowserdocker",
    "kv": "urikv",
    "stt": "uristt",
    "uristt": "uristt",
    "tts": "uristt",
    "voice-lab": "uristt",
    "webrtc": "uriwebrtc",
    "uriwebrtc": "uriwebrtc",
    "message": "urimessage",
    "chat": "urichat",
    "rdp": "urirdp",
    "rdpedge": "urirdpedge",
    "env": "urienv",
}

CORE_PACKS = frozenset({"node", "screen", "shell"})
BUNDLED_PACKS = frozenset({"node"})
CORE_RUNTIME_PACKS = ("uricontrol",)
PACK_PYPI: dict[str, str] = {
    "shell": "urishell>=0.1.0",
    "screen": "uriscreen>=0.1.0",
    "kvm": "urikvm>=0.1.0",
    "him": "urihim>=0.1.0",
    "ocr": "uriocr>=0.1.0",
    "llm": "urillm[vision]>=0.1.0",
    "office": "urioffice>=0.1.0",
    "mail": "urimail>=0.1.0",
    "vql": "urivql>=0.1.0",
    "img2nl": "uriimg2nl>=0.1.0",
    "browser": "uribrowser>=0.1.0",
    "kv": "urikv>=0.1.0",
    "stt": "uristt>=0.1.0",
    "webrtc": "uriwebrtc>=0.1.0",
    "message": "urimessage>=0.1.0",
    "chat": "urichat>=0.1.0",
    "rdp": "urirdp>=0.1.0",
    "rdpedge": "urirdpedge>=0.1.0",
    "env": "urienv>=0.1.0",
}

# GitHub Releases wheel (PyPI alternative) — tellmesh/<repo>/releases/download/vX/Y.whl
PACK_GITHUB_VERSION: dict[str, str] = {
    "uricontrol": "0.1.14",
    "shell": "0.1.0",
    "screen": "0.1.0",
    "kvm": "0.1.1",
    "him": "0.1.3",
    "ocr": "0.1.0",
    "llm": "0.1.0",
    "office": "0.1.1",
    "mail": "0.1.3",
    "vql": "0.1.1",
    "img2nl": "0.1.2",
    "browser": "0.1.1",
    "kv": "0.1.0",
    "stt": "0.1.0",
    "webrtc": "0.1.0",
    "message": "0.1.0",
    "chat": "0.1.0",
    "rdp": "0.1.0",
    "rdpedge": "0.1.0",
    "env": "0.1.0",
}
PACK_GITHUB_REPO: dict[str, str] = {
    "uricontrol": "uricontrol",
    "shell": "urishell",
    "screen": "uriscreen",
    "kvm": "urikvm",
    "him": "urihim",
    "ocr": "uriocr",
    "llm": "urillm",
    "office": "urioffice",
    "mail": "urimail",
    "vql": "urivql",
    "img2nl": "uriimg2nl",
    "browser": "uribrowser",
    "kv": "urikv",
    "stt": "uristt",
    "webrtc": "uriwebrtc",
    "message": "urimessage",
    "chat": "urichat",
    "rdp": "urirdp",
    "rdpedge": "urirdpedge",
    "env": "urienv",
}
# PyPI wheel basename when it differs from repo name (e.g. underscores).
PACK_GITHUB_WHEEL: dict[str, str] = {}
# Prefer GitHub in auto mode until PyPI publish succeeds
GITHUB_PREFERRED_PACKS = frozenset({"him", "ocr", "llm", "office", "mail", "vql", "img2nl", "browser", "kv", "stt", "webrtc", "message", "chat", "rdp", "rdpedge", "env", "screen"})

# URI scheme -> pack alias (node only bundled; screen/shell via pip deps)
SCHEME_TO_PACK: dict[str, str] = {
    "screen": "screen",
    "shell": "shell",
    "kvm": "kvm",
    "him": "him",
    "ocr": "ocr",
    "llm": "llm",
    "urioffice": "office",
    "urimail": "mail",
    "vql": "vql",
    "img2nl": "img2nl",
    "browser": "browser",
    "kv": "kv",
    "log": "kv",
    "stt": "stt",
    "tts": "stt",
    "voice": "stt",
    "webrtc": "webrtc",
    "message": "message",
    "chat": "chat",
    "rdp": "rdp",
    "env": "env",
}

# Real backends: extra pip specs when handler needs mss/pyautogui/etc.
REAL_PIP: dict[str, list[str]] = {
    "screen": ["mss>=9.0", "Pillow>=10.0"],
    "kvm": ["mss>=9.0", "Pillow>=10.0"],
    "him": ["pyautogui>=0.9.54"],
    "ocr": ["pytesseract>=0.3.10", "Pillow>=10.0"],
    "llm": ["litellm>=1.40"],
}


def auto_install_enabled() -> bool:
    return os.environ.get("URISYS_NODE_AUTO_INSTALL", "1") == "1"


def pack_install_source() -> str:
    """pypi | github | auto (github for him/ocr/llm, else pypi)."""
    return os.environ.get("URISYS_PACK_SOURCE", "auto").strip().lower()


def github_owner() -> str:
    return os.environ.get("URISYS_PACK_GITHUB_OWNER", "tellmesh").strip()


def github_wheel_url(pack: str) -> str | None:
    repo = PACK_GITHUB_REPO.get(pack)
    version = os.environ.get(f"URISYS_PACK_GITHUB_{pack.upper()}_VERSION") or PACK_GITHUB_VERSION.get(pack)
    if not repo or not version:
        return None
    ver = version.lstrip("v")
    tag = f"v{ver}"
    wheel_base = PACK_GITHUB_WHEEL.get(pack, repo)
    wheel = f"{wheel_base}-{ver}-py3-none-any.whl"
    return f"https://github.com/{github_owner()}/{repo}/releases/download/{tag}/{wheel}"


def resolve_pack_spec(pack: str) -> str | None:
    pypi = PACK_PYPI.get(pack)
    github = github_wheel_url(pack)
    source = pack_install_source()
    if source == "github":
        return github or pypi
    if source == "pypi":
        return pypi or github
    if pack in CORE_RUNTIME_PACKS and github:
        return github
    if pack in GITHUB_PREFERRED_PACKS and github:
        return github
    return pypi or github


def pack_module(pack: str) -> str:
    return PACK_MODULES.get(pack, pack)


def scheme_for_uri(uri: str) -> str:
    return uri.split("://", 1)[0].lower() if "://" in uri else ""


def pack_for_scheme(scheme: str) -> str | None:
    return SCHEME_TO_PACK.get(scheme)


def _pip_install(specs: list[str], *, no_deps: bool = False) -> dict[str, Any]:
    cmd = [sys.executable, "-m", "pip", "install", "-U"]
    if no_deps:
        cmd.append("--no-deps")
    cmd.extend(specs)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    return {
        "ok": proc.returncode == 0,
        "command": " ".join(cmd),
        "stdout": (proc.stdout or "")[-2000:],
        "stderr": (proc.stderr or "")[-2000:],
        "exit_code": proc.returncode,
    }


def ensure_pip_specs(specs: list[str], *, install: bool = True) -> dict[str, Any]:
    if not specs:
        return {"ok": True, "installed": [], "skipped": True}
    if not install or not auto_install_enabled():
        return {
            "ok": False,
            "error": "auto install disabled (URISYS_NODE_AUTO_INSTALL=0)",
            "specs": specs,
        }
    result = _pip_install(specs)
    result["specs"] = specs
    return result


def pack_install_specs(pack: str, override_specs: list[str] | None = None) -> list[str]:
    if override_specs:
        return [str(s).strip() for s in override_specs if str(s).strip()]
    specs: list[str] = []
    for core in CORE_RUNTIME_PACKS:
        if pack != core:
            core_spec = resolve_pack_spec(core)
            if core_spec:
                specs.append(core_spec)
    spec = resolve_pack_spec(pack)
    if spec:
        specs.append(spec)
    return specs


def ensure_pack_pypi(pack: str, *, install: bool = True, specs: list[str] | None = None) -> dict[str, Any]:
    """Install pack + uricontrol from GitHub Releases when import would fail."""
    resolved = pack_install_specs(pack, specs)
    if not resolved:
        if pack in BUNDLED_PACKS:
            return {"ok": True, "pack": pack, "skipped": True, "reason": "bundled in urisys"}
        return {"ok": False, "error": f"no install mapping for pack {pack!r}"}
    out = ensure_pip_specs(resolved, install=install)
    out["pack"] = pack
    out["source"] = pack_install_source()
    return out


def ensure_boot_pack(pack: str, *, install: bool = True) -> dict[str, Any]:
    """Install screen/shell only — uricontrol is already a urisys-node dependency."""
    if pack in BUNDLED_PACKS:
        return {"ok": True, "pack": pack, "skipped": True, "reason": "bundled in urisys-node"}
    if not install or not auto_install_enabled():
        return {"ok": False, "pack": pack, "error": "auto install disabled (URISYS_NODE_AUTO_INSTALL=0)"}

    github = github_wheel_url(pack)
    pypi = PACK_PYPI.get(pack)
    attempts: list[dict[str, Any]] = []

    if github:
        out = _pip_install([github], no_deps=True)
        attempts.append({"spec": github, "no_deps": True, **out})
        if out.get("ok"):
            out["pack"] = pack
            out["specs"] = [github]
            out["attempts"] = attempts
            out["source"] = "github"
            return out

    if pypi:
        out = _pip_install([pypi])
        attempts.append({"spec": pypi, **out})
        out["pack"] = pack
        out["specs"] = [pypi]
        out["attempts"] = attempts
        out["source"] = "pypi"
        return out

    return {"ok": False, "pack": pack, "error": f"no install mapping for pack {pack!r}", "attempts": attempts}


def ensure_real_deps(pack: str, *, install: bool = True) -> dict[str, Any]:
    specs = REAL_PIP.get(pack, [])
    out = ensure_pip_specs(specs, install=install)
    out["pack"] = pack
    out["real"] = True
    return out


def github_wheel_urls(*packs: str) -> list[str]:
    """Pip install specs (uricontrol + wheels) for shell:// bootstrap flows."""
    specs: list[str] = []
    for core in CORE_RUNTIME_PACKS:
        spec = resolve_pack_spec(core)
        if spec:
            specs.append(spec)
    for pack in packs:
        spec = resolve_pack_spec(pack)
        if spec and spec not in specs:
            specs.append(spec)
    return specs


def import_pack_module(pack: str):
    module_name = pack_module(pack)
    return importlib.import_module(module_name)


def pack_importable(pack: str) -> bool:
    try:
        import_pack_module(pack)
        return True
    except ModuleNotFoundError:
        return False
