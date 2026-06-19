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
# CONTROL_PACKS: the communication / control plane that runs IN-PROCESS in the
# router. Everything else (all execution — shell, screen, kvm, …) is isolated into
# worker processes so an execution crash can never take the router (and therefore
# /health, /events and worker supervision) down. Keep this minimal: just `node`.
CONTROL_PACKS = frozenset({"node"})
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
    """local | github | pypi | auto.

    ``auto`` (default) is registry-independent and resolves in priority order:
    **local wheelhouse → GitHub Releases → PyPI**. This means a freshly *built*
    wheel is always preferred, GitHub is used before PyPI (PyPI publishing is
    rate-limited / name-squatted), and PyPI is only a last resort. Force a single
    channel with ``URISYS_PACK_SOURCE=local|github|pypi``.
    """
    return os.environ.get("URISYS_PACK_SOURCE", "auto").strip().lower()


# ── Local wheelhouse (registry-independent, build-first) ─────────────────────
def wheelhouse_dir() -> str:
    """Directory of locally built wheels, preferred over any registry.

    Populate it with ``scripts/build-wheelhouse.sh``. Default ``~/.urisys/wheelhouse``;
    override with ``URISYS_WHEELHOUSE``. When it exists, every pip install gets
    ``--find-links <dir>`` so locally built wheels win without touching a registry."""
    return os.path.expanduser(os.environ.get("URISYS_WHEELHOUSE", "~/.urisys/wheelhouse"))


def wheelhouse_offline() -> bool:
    """When set, installs use ``--no-index`` — fully offline, wheelhouse only."""
    return os.environ.get("URISYS_WHEELHOUSE_OFFLINE", "").strip() not in ("", "0", "false", "no")


def wheelhouse_find_links() -> str | None:
    """Value for ``pip --find-links``: a local dir OR an ``http(s)://`` URL.

    A URL lets a node pull built wheels from a wheel server (e.g. the
    ``wheel_server`` in session.manifest.yaml — ``python -m http.server`` over a
    wheelhouse) with zero copying. Returns ``None`` when neither a dir exists nor a
    URL is configured."""
    wh = os.environ.get("URISYS_WHEELHOUSE", "~/.urisys/wheelhouse")
    if wh.startswith(("http://", "https://")):
        return wh
    d = os.path.expanduser(wh)
    return d if os.path.isdir(d) else None


def _dist_name(pack: str) -> str:
    """PyPI/GitHub distribution name for a pack alias (no version constraint)."""
    pypi = PACK_PYPI.get(pack)
    if pypi:
        # "urillm[vision]>=0.1.0" → "urillm"
        return pypi.split("[", 1)[0].split(">", 1)[0].split("=", 1)[0].split("<", 1)[0].strip()
    return PACK_GITHUB_REPO.get(pack) or PACK_GITHUB_WHEEL.get(pack) or pack


def local_wheel(pack: str) -> str | None:
    """Newest locally built wheel for ``pack`` in the wheelhouse, or ``None``.

    Matches the dist name normalised to PEP 427 (hyphens → underscores) and picks
    the highest version, so a rebuilt wheel supersedes older copies automatically."""
    wh = wheelhouse_dir()
    if not os.path.isdir(wh):
        return None
    base = _dist_name(pack).replace("-", "_").lower()
    best: tuple[tuple[int, ...], str] | None = None
    for name in os.listdir(wh):
        low = name.lower()
        if not low.endswith(".whl") or not low.startswith(base + "-"):
            continue
        ver = name[len(base) + 1 :].split("-", 1)[0]
        key = _parse_ver(ver)
        if best is None or key > best[0]:
            best = (key, name)
    return os.path.join(wh, best[1]) if best else None


def _parse_ver(text: str) -> tuple[int, ...]:
    parts: list[int] = []
    for piece in (text or "").strip().lstrip("v").split("."):
        num = ""
        for ch in piece:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num) if num else 0)
    return tuple(parts) or (0,)


def github_owner() -> str:
    return os.environ.get("URISYS_PACK_GITHUB_OWNER", "tellmesh").strip()


_gh_latest_cache: dict[str, str | None] = {}


def github_dynamic_enabled() -> bool:
    """Query GitHub for the *latest* release tag instead of the pinned version.

    On by default (the point is to respect whatever is newest on GitHub). Disabled
    by ``URISYS_OFFLINE`` or ``URISYS_PACK_GITHUB_DYNAMIC=0`` so installs/tests never
    block on the network — the pinned ``PACK_GITHUB_VERSION`` is the fallback."""
    if os.environ.get("URISYS_OFFLINE", "").strip():
        return False
    return os.environ.get("URISYS_PACK_GITHUB_DYNAMIC", "1").strip() not in ("0", "false", "no")


def github_latest_version(pack: str) -> str | None:
    """Newest release version on GitHub for ``pack`` (best-effort, cached)."""
    repo = PACK_GITHUB_REPO.get(pack)
    if not repo or not github_dynamic_enabled():
        return None
    if repo in _gh_latest_cache:
        return _gh_latest_cache[repo]
    import json
    import urllib.request

    url = f"https://api.github.com/repos/{github_owner()}/{repo}/releases/latest"
    headers = {"Accept": "application/json", "User-Agent": "urisys-node"}
    token = (
        os.environ.get("URISYS_GITHUB_TOKEN")
        or os.environ.get("GH_TOKEN")
        or os.environ.get("GITHUB_TOKEN")
    )
    if token:
        headers["Authorization"] = f"Bearer {token.strip()}"
    version: str | None = None
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as resp:  # nosec - fixed host
            tag = (json.loads(resp.read().decode("utf-8")) or {}).get("tag_name")
            version = tag.lstrip("v") if tag else None
    except Exception:
        version = None
    _gh_latest_cache[repo] = version
    return version


def github_wheel_url(pack: str, *, version: str | None = None) -> str | None:
    repo = PACK_GITHUB_REPO.get(pack)
    version = (
        version
        or os.environ.get(f"URISYS_PACK_GITHUB_{pack.upper()}_VERSION")
        or PACK_GITHUB_VERSION.get(pack)
    )
    if not repo or not version:
        return None
    ver = version.lstrip("v")
    tag = f"v{ver}"
    wheel_base = PACK_GITHUB_WHEEL.get(pack, repo)
    wheel = f"{wheel_base}-{ver}-py3-none-any.whl"
    return f"https://github.com/{github_owner()}/{repo}/releases/download/{tag}/{wheel}"


def github_best_url(pack: str) -> str | None:
    """GitHub wheel URL using the latest release when reachable, else the pinned
    version. This is what makes the node respect a newer GitHub publish."""
    latest = github_latest_version(pack)
    pinned = os.environ.get(f"URISYS_PACK_GITHUB_{pack.upper()}_VERSION") or PACK_GITHUB_VERSION.get(pack)
    if latest and (pinned is None or _parse_ver(latest) >= _parse_ver(pinned)):
        return github_wheel_url(pack, version=latest)
    return github_wheel_url(pack)


def resolve_pack_source(pack: str) -> dict[str, Any] | None:
    """Resolve where to install ``pack`` from, registry-independent.

    Returns ``{"kind", "spec", "find_links"?, "no_index"?}`` or ``None``. Priority
    in ``auto``: **local wheelhouse → GitHub → PyPI**. A forced ``URISYS_PACK_SOURCE``
    pins one channel (with sensible fallback when that channel has nothing)."""
    source = pack_install_source()
    wh = wheelhouse_find_links()  # local dir or http(s):// wheel server, else None
    local = local_wheel(pack)  # only matches a local dir wheel (None for URL)
    pypi = PACK_PYPI.get(pack)

    def _local() -> dict[str, Any] | None:
        if not local:
            return None
        out: dict[str, Any] = {"kind": "local", "spec": local, "find_links": wh}
        if wheelhouse_offline():
            out["no_index"] = True
        return out

    def _github() -> dict[str, Any] | None:
        url = github_best_url(pack)
        return {"kind": "github", "spec": url, "find_links": wh} if url else None

    def _pypi() -> dict[str, Any] | None:
        return {"kind": "pypi", "spec": pypi, "find_links": wh} if pypi else None

    if source == "local":
        return _local() or _github() or _pypi()
    if source == "github":
        return _github() or _local() or _pypi()
    if source == "pypi":
        return _pypi() or _local() or _github()
    # auto: build-first, then GitHub-first, PyPI last.
    if pack in CORE_RUNTIME_PACKS or pack in GITHUB_PREFERRED_PACKS:
        return _local() or _github() or _pypi()
    return _local() or _pypi() or _github()


def resolve_pack_spec(pack: str) -> str | None:
    """Back-compat: the pip spec string only (URL, wheel path or ``dist>=x``)."""
    src = resolve_pack_source(pack)
    return src["spec"] if src else None


def pack_module(pack: str) -> str:
    return PACK_MODULES.get(pack, pack)


def scheme_for_uri(uri: str) -> str:
    return uri.split("://", 1)[0].lower() if "://" in uri else ""


def pack_for_scheme(scheme: str) -> str | None:
    return SCHEME_TO_PACK.get(scheme)


def _pip_install(
    specs: list[str],
    *,
    no_deps: bool = False,
    find_links: str | None = None,
    no_index: bool = False,
) -> dict[str, Any]:
    cmd = [sys.executable, "-m", "pip", "install", "-U"]
    if no_deps:
        cmd.append("--no-deps")
    # Build-first: prefer locally built wheels so installs never enumerate a registry
    # (this is what kills pip's PyPI version backtracking) and work registry-free.
    links = find_links if find_links is not None else wheelhouse_find_links()
    if links:
        cmd += ["--find-links", links]
    if no_index or (links and wheelhouse_offline()):
        cmd.append("--no-index")
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

    attempts: list[dict[str, Any]] = []
    # Try sources in registry-independent priority order; a local wheel or GitHub
    # wheel is installed --no-deps (its 3rd-party deps come from the wheelhouse/index
    # via the dep walk of the pack itself), PyPI as a normal resolved install.
    local = local_wheel(pack)
    github = github_best_url(pack)
    pypi = PACK_PYPI.get(pack)
    candidates: list[tuple[str, str, bool]] = []
    for kind, spec in (("local", local), ("github", github), ("pypi", pypi)):
        if spec:
            candidates.append((kind, spec, kind != "pypi"))
    # Honour a forced single channel.
    forced = pack_install_source()
    if forced in ("local", "github", "pypi"):
        candidates.sort(key=lambda c: 0 if c[0] == forced else 1)

    for kind, spec, no_deps in candidates:
        out = _pip_install([spec], no_deps=no_deps)
        attempts.append({"spec": spec, "source": kind, "no_deps": no_deps, **out})
        if out.get("ok"):
            out["pack"] = pack
            out["specs"] = [spec]
            out["attempts"] = attempts
            out["source"] = kind
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
