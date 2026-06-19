"""Remote operations package."""

from urisysnode.remote.client import (
    call_uri,
    health,
    pip_install,
    wait_health,
)
from urisysnode.remote.config import (
    default_endpoint,
    default_nodes_registry,
    default_route_map,
    default_wheel_host,
)
from urisysnode.remote.deploy import (
    build_wheel,
    serve_wheels,
    wheel_url,
)
from urisysnode.remote.main import main
from urisysnode.remote.pack import install_pack
from urisysnode.remote.restart import (
    _restart_scheduled,
    schedule_restart,
)
from urisysnode.remote.upgrade import (
    upgrade_lenovo_kv,
    upgrade_lenovo_node,
)
from urisysnode.remote.worker import (
    restart_worker,
    spawn_worker,
    stop_worker,
    workers,
)

__all__ = [
    # Config
    "default_route_map",
    "default_nodes_registry",
    "default_endpoint",
    "default_wheel_host",
    # Client
    "health",
    "wait_health",
    "call_uri",
    "pip_install",
    # Pack
    "install_pack",
    # Worker
    "spawn_worker",
    "restart_worker",
    "stop_worker",
    "workers",
    # Restart
    "schedule_restart",
    "_restart_scheduled",
    # Deploy
    "build_wheel",
    "serve_wheels",
    "wheel_url",
    # Upgrade
    "upgrade_lenovo_node",
    "upgrade_lenovo_kv",
    # Main
    "main",
]
