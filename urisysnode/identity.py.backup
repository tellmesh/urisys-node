from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import socket
import sys
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
    root = default_data_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _identity_path() -> Path:
    return _data_dir() / "node-identity.json"


def _pairing_path() -> Path:
    return _data_dir() / "node-pairing.json"


def _hostname() -> str:
    return socket.gethostname()


def load_identity() -> dict[str, Any]:
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
    _identity_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_pairing() -> dict[str, Any]:
    path = _pairing_path()
    if not path.exists():
        return {"paired": False}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {"paired": False}


def enroll(controller: str, code: str | None = None, token: str | None = None) -> dict[str, Any]:
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
    _pairing_path().write_text(json.dumps(pairing, indent=2), encoding="utf-8")
    return pairing


def save_pairing(data: dict[str, Any]) -> None:
    _pairing_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def set_remote_control(active: bool, message: str | None = None) -> dict[str, Any]:
    pairing = load_pairing()
    pairing["remote_control_active"] = active
    if message is not None:
        pairing["indicator_message"] = message
    save_pairing(pairing)
    return pairing


def require_paired(context: dict[str, Any]) -> None:
    if os.environ.get("URISYS_NODE_SKIP_PAIRING") == "1":
        return
    if context.get("skip_pairing"):
        return
    if not load_pairing().get("paired"):
        raise PermissionError("node is not paired — run: urisys-node enroll --controller …")


def health_payload(version: str | None = None, runtime: Any | None = None) -> dict[str, Any]:
    identity = load_identity()
    pairing = load_pairing()

    urisys_version = version
    if urisys_version is None:
        try:
            import urisys

            urisys_version = getattr(urisys, "__version__", None)
        except Exception:
            urisys_version = None

    uricontrol_version = None
    try:
        from importlib.metadata import version as pkg_version

        uricontrol_version = pkg_version("uricontrol")
    except Exception:
        pass

    payload: dict[str, Any] = {
        "ok": True,
        "service": "urisys-node",
        "node_id": identity["node_id"],
        "fingerprint": identity.get("fingerprint"),
        "version": urisys_version or "0.1.0",
        "urisys": urisys_version,
        "uricontrol": uricontrol_version,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "python_executable": sys.executable,
        "paired": bool(pairing.get("paired")),
        "controller": pairing.get("controller"),
        "remote_control_active": bool((pairing.get("remote_control_active"))),
    }

    config = getattr(runtime, "config", None) if runtime is not None else None
    if isinstance(config, dict):
        him_cfg = config.get("him") or {}
        if isinstance(him_cfg, dict) and him_cfg.get("driver"):
            payload["him_driver"] = him_cfg["driver"]
    if payload.get("him_driver") is None:
        payload["him_driver"] = os.environ.get("URISYS_HIM_DRIVER") or _detect_him_driver()

    # Profile / mock visibility — so a controller can see at a glance whether the node runs
    # on a real profile or fell back to default/mock drivers (the "node on mock" trap).
    if runtime is not None:
        config_path = getattr(runtime, "_config_path", None) or None
        cfg = config if isinstance(config, dict) else {}
        if cfg.get("_source"):
            source = cfg["_source"]
        elif config_path and cfg:
            source = f"profile:{config_path}"
        else:
            source = "mock (no profile)"
        payload["profile_path"] = config_path
        payload["config_source"] = source
        kvm_cfg = cfg.get("kvm") or {}
        payload["kvm_driver"] = kvm_cfg.get("driver", "mock") if isinstance(kvm_cfg, dict) else "mock"
        screen_cfg = cfg.get("screen") or {}
        payload["screen_backend"] = (
            screen_cfg.get("default_backend", "mock") if isinstance(screen_cfg, dict) else "mock"
        )
        payload["mock_mode"] = payload["kvm_driver"] in ("mock", None) and not config_path

    if runtime is not None:
        instance_id = getattr(runtime, "_instance_id", None)
        if instance_id:
            payload["instance_id"] = instance_id
        loaded = sorted(getattr(runtime, "_loaded_packs", set()) or [])
        payload["packs_loaded"] = loaded
        try:
            payload["routes_count"] = len(runtime.routes)
        except Exception:
            pass

    return payload


def _detect_him_driver() -> str:
    if os.environ.get("WAYLAND_DISPLAY") and shutil.which("ydotool"):
        return "ydotool"
    if os.environ.get("DISPLAY") and shutil.which("xdotool"):
        return "xdotool"
    if shutil.which("ydotool"):
        return "ydotool"
    return "pyautogui"
