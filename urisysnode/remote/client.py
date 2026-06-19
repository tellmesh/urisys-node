"""Remote client operations."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from urisysnode.client import call_via_route_map, remote_call

from .config import default_endpoint, default_nodes_registry, default_route_map


def health(*, endpoint: str | None = None, timeout: float = 5.0) -> dict[str, Any]:
    url = (endpoint or default_endpoint()) + "/health"
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def wait_health(*, endpoint: str | None = None, timeout_s: float = 60.0, interval_s: float = 2.0) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    last_error = "unreachable"
    ep = endpoint or default_endpoint()
    while time.time() < deadline:
        try:
            return health(endpoint=ep)
        except Exception as exc:
            last_error = str(exc)
            time.sleep(interval_s)
    raise TimeoutError(f"node not healthy at {ep}: {last_error}")


def call_uri(
    uri: str,
    *,
    payload: dict[str, Any] | None = None,
    approved: bool = True,
    allow_real: bool = True,
    dry_run: bool = False,
    route_map: str | None = None,
    nodes_registry: str | None = None,
    endpoint: str | None = None,
) -> dict[str, Any]:
    ctx = {"approved": approved, "allow_real": allow_real, "dry_run": dry_run}
    if endpoint:
        return remote_call(endpoint, uri, payload, ctx)
    return call_via_route_map(
        uri,
        route_map_path=route_map or default_route_map(),
        nodes_registry_path=nodes_registry or default_nodes_registry(),
        payload=payload,
        context=ctx,
    )


def pip_install(
    specs: list[str],
    *,
    route_map: str | None = None,
    nodes_registry: str | None = None,
    endpoint: str | None = None,
) -> dict[str, Any]:
    return call_uri(
        "shell://pip",
        payload={"args": ["install", "-U", *specs]},
        route_map=route_map,
        nodes_registry=nodes_registry,
        endpoint=endpoint,
    )
