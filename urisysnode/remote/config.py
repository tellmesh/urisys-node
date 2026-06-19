"""Default configuration for remote operations."""

from __future__ import annotations

import os
from pathlib import Path


def default_route_map() -> str:
    node_root = Path(__file__).resolve().parents[2]
    return os.environ.get(
        "URISYS_ROUTE_MAP",
        str(node_root / "config" / "route-map.lenovo.yaml"),
    )


def default_nodes_registry() -> str:
    node_root = Path(__file__).resolve().parents[2]
    return os.environ.get(
        "URISYS_NODES_REGISTRY",
        str(node_root / "config" / "nodes.registry.json"),
    )


def default_endpoint() -> str:
    return os.environ.get("URISYS_LENOVO_ENDPOINT", "http://192.168.188.201:8790").rstrip("/")


def default_wheel_host() -> str:
    return os.environ.get("URISYS_WHEEL_HOST", "http://192.168.188.212:8765").rstrip("/")
