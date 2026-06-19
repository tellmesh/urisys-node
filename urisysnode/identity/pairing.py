"""Pairing and remote control management."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .core import _data_dir, _hostname, load_identity


def _pairing_path() -> Path:
    """Get path to node pairing JSON file."""
    return _data_dir() / "node-pairing.json"


def load_pairing() -> dict[str, Any]:
    """Load node pairing information from file.

    Returns a dictionary with pairing status. If the file doesn't exist,
    returns {'paired': False}.
    """
    path = _pairing_path()
    if not path.exists():
        return {"paired": False}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {"paired": False}


def save_pairing(data: dict[str, Any]) -> None:
    """Save pairing information to file."""
    _pairing_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def enroll(controller: str, code: str | None = None, token: str | None = None) -> dict[str, Any]:
    """Enroll node with a controller.

    Creates a pairing configuration and saves it to disk.

    Args:
        controller: The controller URL or identifier
        code: Optional pairing code
        token: Optional authentication token

    Returns:
        Dictionary with pairing information including node_id, capabilities, etc.
    """
    identity = load_identity()
    pairing = {
        "paired": True,
        "controller": controller,
        "enrolled_at": datetime.now(timezone.utc).isoformat(),
        "pair_code": code,
        "token_prefix": (token or "")[:8] or None,
        "node_id": identity["node_id"],
        "capabilities": ["screen", "kvm", "him", "ocr", "llm", "process", "service"],
    }
    save_pairing(pairing)
    return pairing


def set_remote_control(active: bool, message: str | None = None) -> dict[str, Any]:
    """Enable or disable remote control.

    Args:
        active: Whether remote control should be active
        message: Optional indicator message

    Returns:
        Updated pairing dictionary
    """
    pairing = load_pairing()
    pairing["remote_control_active"] = active
    if message is not None:
        pairing["indicator_message"] = message
    save_pairing(pairing)
    return pairing


def require_paired(context: dict[str, Any]) -> None:
    """Require that the node is paired with a controller.

    Raises PermissionError if the node is not paired and pairing is not skipped.

    Args:
        context: Dictionary that may contain 'skip_pairing' flag

    Raises:
        PermissionError: If node is not paired
    """
    if os.environ.get("URISYS_NODE_SKIP_PAIRING") == "1":
        return
    if context.get("skip_pairing"):
        return
    if not load_pairing().get("paired"):
        raise PermissionError(
            "node is not paired — run: urisys-node enroll --controller …"
        )
