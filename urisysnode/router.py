from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml


def load_route_map(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _match_pattern(pattern: str, uri: str) -> bool:
    regex = "^" + re.escape(pattern).replace("\\*\\*", ".*").replace("\\*", "[^/]+") + "$"
    return re.match(regex, uri) is not None


def resolve_remote_route(uri: str, route_map: dict[str, Any]) -> dict[str, Any] | None:
    for entry in route_map.get("routes") or []:
        pattern = entry.get("match") or ""
        if _match_pattern(pattern, uri):
            return entry
    return None


HOSTLESS_SCHEMES = frozenset({"kv", "log", "env"})


def rewrite_uri_for_slave(uri: str, node_id: str, target_node: str = "local") -> str:
    if node_id == target_node:
        return uri
    parsed = urlparse(uri)
    scheme = parsed.scheme
    rest = uri.split("://", 1)[1]
    parts = rest.split("/", 1)
    if parts and parts[0] == node_id:
        tail = parts[1] if len(parts) > 1 else ""
        if scheme in HOSTLESS_SCHEMES:
            return f"{scheme}://{tail}" if tail else f"{scheme}://"
        return f"{scheme}://{target_node}/{tail}" if tail else f"{scheme}://{target_node}"
    return uri.replace(f"{scheme}://{node_id}", f"{scheme}://{target_node}", 1)


def node_endpoint(route: dict[str, Any], nodes_registry: dict[str, Any]) -> str | None:
    node = route.get("node")
    if not node:
        return route.get("target")
    entry = (nodes_registry.get("nodes") or {}).get(node) or {}
    return entry.get("endpoint") or route.get("target")
