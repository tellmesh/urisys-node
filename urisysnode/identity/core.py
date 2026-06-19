"""Core identity management functions."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def default_data_root() -> Path:
    """Per-user runtime data root, stable regardless of the process CWD.

    Precedence: ``URISYS_NODE_DATA`` > ``$XDG_DATA_HOME/urisys`` > ``~/.local/share/urisys``.
    The old CWD-relative ``data/`` default was a footgun — a node started from a
    different directory generated a fresh identity and lost its pairing.
    """
    override = os.environ.get("URISYS_NODE_DATA")
    if override:
        return Path(override)
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "urisys"


def default_events_path() -> str:
    """Default audit-log path: ``URISYS_NODE_EVENTS`` or ``<data root>/events.jsonl``."""
    override = os.environ.get("URISYS_NODE_EVENTS")
    if override:
        return override
    return str(default_data_root() / "events.jsonl")


def _data_dir() -> Path:
    """Ensure data directory exists and return its path."""
    root = default_data_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _identity_path() -> Path:
    """Get path to node identity JSON file."""
    return _data_dir() / "node-identity.json"


def _hostname() -> str:
    """Get the hostname of the current machine."""
    return socket.gethostname()


def load_identity() -> dict[str, Any]:
    """Load node identity from file or create a new one.

    Returns a dictionary with node_id, hostname, created_at, public_key, and fingerprint.
    If the identity file doesn't exist, a new identity is generated and saved.
    """
    path = _identity_path()
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data

    node_id = os.environ.get("URISYS_NODE_ID") or _hostname()
    identity = {
        "node_id": node_id,
        "hostname": _hostname(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "public_key": secrets.token_hex(16),
    }
    identity["fingerprint"] = hashlib.sha256(identity["public_key"].encode()).hexdigest()[:16]
    save_identity(identity)
    return identity


def save_identity(data: dict[str, Any]) -> None:
    """Save node identity to file."""
    _identity_path().write_text(json.dumps(data, indent=2), encoding="utf-8")
