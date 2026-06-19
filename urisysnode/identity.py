"""Identity management for urisys-node.

This module provides functionality for managing node identity, pairing,
and health information.

The module is organized into submodules:
- core: Core identity functions (load_identity, save_identity, etc.)
- pairing: Pairing-related functions (enroll, load_pairing, etc.)
- health: Health payload generation

For backward compatibility, all functions are re-exported from this module.
"""

# Re-export everything for backward compatibility
from urisysnode.identity.core import (
    _data_dir,
    _hostname,
    _identity_path,
    default_data_root,
    default_events_path,
    load_identity,
    save_identity,
)
from urisysnode.identity.pairing import (
    _pairing_path,
    enroll,
    load_pairing,
    require_paired,
    save_pairing,
    set_remote_control,
)
from urisysnode.identity.health import (
    _detect_him_driver,
    health_payload,
)

__all__ = [
    # Core
    "default_data_root",
    "default_events_path",
    "load_identity",
    "save_identity",
    # Pairing
    "enroll",
    "load_pairing",
    "save_pairing",
    "set_remote_control",
    "require_paired",
    # Health
    "health_payload",
    # Private (for internal use)
    "_data_dir",
    "_hostname",
    "_identity_path",
    "_pairing_path",
    "_detect_him_driver",
]
