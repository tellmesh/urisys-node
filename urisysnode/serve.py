"""HTTP serving for urisys-node.

This module is now a compatibility shim. All functionality has been moved to
the urisysnode.serve subpackage for better organization and reduced complexity.

Please import from urisysnode.serve directly, which re-exports all symbols.
"""

from urisysnode.serve import (
    _ReuseHTTPServer,
    _app_chat_get,
    _app_chat_post,
    _app_chat_store,
    _release_forward_spec,
    call_uri,
    hotload_release_pack,
    make_handler,
    register_forward_pack,
    serve,
)

__all__ = [
    "serve",
    "_ReuseHTTPServer",
    "call_uri",
    "make_handler",
    "register_forward_pack",
    "hotload_release_pack",
    "_release_forward_spec",
    "_app_chat_store",
    "_app_chat_get",
    "_app_chat_post",
]
