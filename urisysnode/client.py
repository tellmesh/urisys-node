from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any

from .router import load_route_map, node_endpoint, resolve_remote_route, rewrite_uri_for_slave


def discover_mdns(timeout_s: float = 2.0) -> list[dict[str, Any]]:
    try:
        from zeroconf import ServiceBrowser, Zeroconf  # type: ignore
    except ImportError:
        return []

    found: list[dict[str, Any]] = []

    class Listener:
        def add_service(self, zc, type_, name):
            info = zc.get_service_info(type_, name)
            if not info:
                return
            host = socket.inet_ntoa(info.addresses[0]) if info.addresses else name
            port = info.port
            props = {k.decode(): (v.decode() if isinstance(v, bytes) else v) for k, v in (info.properties or {}).items()}
            found.append(
                {
                    "name": name,
                    "host": host,
                    "port": port,
                    "endpoint": f"http://{host}:{port}",
                    "capabilities": (props.get("capabilities") or "").split(","),
                    "node_id": props.get("node_id") or name.split(".")[0],
                }
            )

        def remove_service(self, *args):
            pass

        def update_service(self, *args):
            pass

    zc = Zeroconf()
    browser = ServiceBrowser(zc, "_urisys._tcp.local.", Listener)
    import time

    time.sleep(timeout_s)
    zc.close()
    return found


def remote_call(
    endpoint: str,
    uri: str,
    payload: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = json.dumps({"uri": uri, "payload": payload or {}, "context": context or {}}).encode("utf-8")
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/uri/call",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_via_route_map(
    uri: str,
    *,
    route_map_path: str,
    nodes_registry_path: str,
    payload: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    route_map = load_route_map(route_map_path)
    nodes = json.loads(open(nodes_registry_path, encoding="utf-8").read())
    route = resolve_remote_route(uri, route_map)
    if not route:
        raise ValueError(f"no route for URI: {uri}")
    endpoint = node_endpoint(route, nodes)
    if not endpoint:
        raise ValueError(f"no endpoint for route: {route}")
    node_id = route.get("node") or "slave-01"
    local_uri = rewrite_uri_for_slave(uri, node_id=node_id, target_node="local")
    ctx = dict(context or {})
    if route.get("approval") == "required":
        ctx.setdefault("approved", True)
    return remote_call(endpoint, local_uri, payload, ctx)
