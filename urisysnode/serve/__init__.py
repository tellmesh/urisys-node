"""HTTP serving for urisys-node.

This package contains the HTTP server, handlers, and forwarding logic.
"""

from .app_chat import _app_chat_get, _app_chat_post, _app_chat_store
from .forwarding import (
    _release_forward_spec,
    hotload_release_pack,
    register_forward_pack,
)
from .handlers import make_handler
from .server import _ReuseHTTPServer, serve, call_uri

# Re-export from runtime for backward compatibility
from ..runtime import build_runtime, load_pack_into_runtime
from ..runtime.config import _default_real_config, resolve_node_config

# Re-export from port for backward compatibility
from ..port.manager import _collect_takeover_targets, _pids_on_port, takeover_port

# Re-export from pack_resolver for backward compatibility
from ..pack_resolver import auto_install_enabled

__all__ = [
    # Server
    "serve",
    "_ReuseHTTPServer",
    "call_uri",
    # Handlers
    "make_handler",
    # Forwarding
    "register_forward_pack",
    "hotload_release_pack",
    "_release_forward_spec",
    # App chat
    "_app_chat_store",
    "_app_chat_get",
    "_app_chat_post",
    # Config (backward compatibility)
    "resolve_node_config",
    "_default_real_config",
    # Runtime (backward compatibility)
    "build_runtime",
    "load_pack_into_runtime",
    # Port (backward compatibility)
    "_collect_takeover_targets",
    "_pids_on_port",
    "takeover_port",
    # pack_resolver (backward compatibility)
    "auto_install_enabled",
]
