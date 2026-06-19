"""Health payload generation for urisys-node."""

from __future__ import annotations

import os
import shutil
import sys
from typing import Any

from .core import load_identity
from .pairing import load_pairing


def _detect_him_driver() -> str:
    """Detect the HIM driver based on available tools and environment."""
    if os.environ.get("WAYLAND_DISPLAY") and shutil.which("ydotool"):
        return "ydotool"
    if os.environ.get("DISPLAY") and shutil.which("xdotool"):
        return "xdotool"
    if shutil.which("ydotool"):
        return "ydotool"
    return "pyautogui"


def _get_urisys_version() -> str | None:
    """Get urisys package version."""
    try:
        import urisys
        return getattr(urisys, "__version__", None)
    except Exception:
        return None


def _get_uricontrol_version() -> str | None:
    """Get uricontrol package version."""
    try:
        from importlib.metadata import version as pkg_version
        return pkg_version("uricontrol")
    except Exception:
        return None


def _get_python_info() -> dict[str, str]:
    """Get Python version information."""
    return {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "python_executable": sys.executable,
    }


def _get_pairing_info() -> dict[str, Any]:
    """Get pairing-related information."""
    pairing = load_pairing()
    return {
        "paired": bool(pairing.get("paired")),
        "controller": pairing.get("controller"),
        "remote_control_active": bool(pairing.get("remote_control_active")),
    }


def _detect_him_driver() -> str:
    """Detect the HIM driver based on environment."""
    wayland = (
        os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
        or bool(os.environ.get("WAYLAND_DISPLAY"))
    )
    return "ydotool" if wayland else "xdotool"


def _get_him_driver(config: dict[str, Any] | None) -> str:
    """Get HIM driver from config or environment."""
    if config:
        him_cfg = config.get("him") or {}
        if isinstance(him_cfg, dict) and him_cfg.get("driver"):
            return him_cfg["driver"]
    him_driver = os.environ.get("URISYS_HIM_DRIVER")
    if him_driver:
        return him_driver
    return _detect_him_driver()


def _get_config_source(config: dict[str, Any] | None, config_path: str | None) -> str:
    """Determine the configuration source."""
    if config and isinstance(config, dict):
        if config.get("_source"):
            return config["_source"]
        if config_path and config:
            return f"profile:{config_path}"
    return "mock (no profile)"


def _get_driver_info(config: dict[str, Any] | None) -> dict[str, str]:
    """Extract driver information from config."""
    result: dict[str, str] = {}
    
    if config and isinstance(config, dict):
        kvm_cfg = config.get("kvm") or {}
        result["kvm_driver"] = kvm_cfg.get("driver", "mock") if isinstance(kvm_cfg, dict) else "mock"
        
        screen_cfg = config.get("screen") or {}
        result["screen_backend"] = (
            screen_cfg.get("default_backend", "mock") if isinstance(screen_cfg, dict) else "mock"
        )
    else:
        result["kvm_driver"] = "mock"
        result["screen_backend"] = "mock"
    
    return result


def _get_runtime_info(runtime: Any) -> dict[str, Any]:
    """Extract runtime-specific information."""
    result: dict[str, Any] = {}
    
    if runtime is None:
        return result
    
    config_path = getattr(runtime, "_config_path", None)
    config = getattr(runtime, "config", None)
    
    if config_path:
        result["profile_path"] = config_path
    
    driver_info = _get_driver_info(config)
    result.update(driver_info)
    
    config_source = _get_config_source(config, config_path)
    result["config_source"] = config_source
    
    # Mock mode detection
    result["mock_mode"] = (
        result.get("kvm_driver") in ("mock", None) and not config_path
    )
    
    # Instance and pack information
    instance_id = getattr(runtime, "_instance_id", None)
    if instance_id:
        result["instance_id"] = instance_id
    
    loaded = sorted(getattr(runtime, "_loaded_packs", set()) or [])
    result["packs_loaded"] = loaded
    
    # Routes count
    try:
        result["routes_count"] = len(runtime.routes)
    except Exception:
        pass
    
    return result


def health_payload(version: str | None = None, runtime: Any | None = None) -> dict[str, Any]:
    """Generate a comprehensive health payload for the node.

    This function gathers version information, identity, pairing status,
    configuration details, and runtime state into a single dictionary.

    Args:
        version: Optional explicit version string (falls back to urisys.__version__)
        runtime: Optional Runtime instance for extracting runtime-specific info

    Returns:
        Dictionary containing all health-related information
    """
    identity = load_identity()
    
    # Version information
    urisys_version = version or _get_urisys_version() or "0.1.0"
    uricontrol_version = _get_uricontrol_version()
    
    # Build base payload
    payload: dict[str, Any] = {
        "ok": True,
        "service": "urisys-node",
        "node_id": identity["node_id"],
        "fingerprint": identity.get("fingerprint"),
        "version": urisys_version,
        "urisys": urisys_version,
        "uricontrol": uricontrol_version,
    }
    
    # Add Python info
    payload.update(_get_python_info())
    
    # Add pairing info
    payload.update(_get_pairing_info())
    
    # Add HIM driver info
    config = getattr(runtime, "config", None) if runtime is not None else None
    payload["him_driver"] = _get_him_driver(config)
    
    # Add runtime-specific info
    payload.update(_get_runtime_info(runtime))
    
    return payload
