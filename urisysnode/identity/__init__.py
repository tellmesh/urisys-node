"""Identity management for urisys-node.

This module provides functionality for managing node identity, pairing,
and health information.
"""

from urisysnode.identity.core import (
    default_data_root,
    default_events_path,
    load_identity,
    save_identity,
)
from urisysnode.identity.pairing import (
    enroll,
    load_pairing,
    require_paired,
    save_pairing,
    set_remote_control,
)
from urisysnode.identity.health import health_payload

__all__ = [
    "default_data_root",
    "default_events_path",
    "load_identity",
    "save_identity",
    "enroll",
    "load_pairing",
    "save_pairing",
    "set_remote_control",
    "require_paired",
    "health_payload",
]

# Re-export for backward compatibility
from urisysnode.identity.core import _data_dir, _hostname, _identity_path
from urisysnode.identity.pairing import _pairing_path
from urisysnode.identity.health import _detect_him_driver
