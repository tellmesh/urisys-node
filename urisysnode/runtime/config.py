"""Configuration resolution for urisys-node runtime."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def resolve_node_config(config_path: str | None = None) -> str:
    """Find the node profile so a freshly-started node never silently falls back to mock
    drivers. Search order: explicit arg → URISYS_NODE_CONFIG → CWD config/ → XDG
    (~/.config/urisys) → URISYS_NODE_DATA → /etc/urisys. Returns the first existing path
    (absolute) or "" when none exists.
    """
    candidates: list[Path] = []
    if config_path:
        candidates.append(Path(config_path))
    env = os.environ.get("URISYS_NODE_CONFIG", "").strip()
    if env:
        candidates.append(Path(env))
    candidates.append(Path("config/node-profile.json"))
    candidates.append(Path.home() / ".config" / "urisys" / "node-profile.json")
    data = os.environ.get("URISYS_NODE_DATA", "").strip()
    if data:
        candidates.append(Path(data) / "node-profile.json")
    candidates.append(Path("/etc/urisys/node-profile.json"))
    for cand in candidates:
        try:
            p = cand.expanduser()
            if p.is_file():
                return str(p.resolve())
        except Exception:
            continue
    return ""


def _default_real_config() -> dict[str, Any]:
    """Auto-detected real-driver defaults used when no profile exists but the operator opted
    into real side-effects (URISYS_ALLOW_REAL=1). Keeps a freshly-started node off mock:
    kvm 'auto' → uriscreen portal on Wayland / mss on X11; him → ydotool (Wayland) else xdotool.
    """
    wayland = (
        os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
        or bool(os.environ.get("WAYLAND_DISPLAY"))
    )
    return {
        "screen": {"default_backend": "auto"},
        "kvm": {"driver": "auto"},
        "him": {"driver": os.environ.get("URISYS_HIM_DRIVER") or ("ydotool" if wayland else "xdotool")},
        "_source": "auto-default (no profile; URISYS_ALLOW_REAL=1)",
    }
