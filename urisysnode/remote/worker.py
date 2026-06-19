"""Worker management operations."""

from __future__ import annotations

from typing import Any

from .client import call_uri


def spawn_worker(
    pack: str | None = None,
    *,
    module: str | None = None,
    install: bool = True,
    specs: list[str] | None = None,
    force: bool = False,
    target: str = "lenovo",
    route_map: str | None = None,
    nodes_registry: str | None = None,
    endpoint: str | None = None,
) -> dict[str, Any]:
    """Spawn a capability as an out-of-process worker; the router forwards to it."""
    payload: dict[str, Any] = {"install": install, "force": force}
    if pack:
        payload["pack"] = pack
    if module:
        payload["module"] = module
    if specs:
        payload["specs"] = specs
    return call_uri(
        f"node://{target}/command/spawn-worker",
        payload=payload,
        route_map=route_map,
        nodes_registry=nodes_registry,
        endpoint=endpoint,
    )


def restart_worker(
    name: str,
    *,
    target: str = "lenovo",
    route_map: str | None = None,
    nodes_registry: str | None = None,
    endpoint: str | None = None,
) -> dict[str, Any]:
    return call_uri(
        f"node://{target}/command/restart-worker",
        payload={"name": name},
        route_map=route_map,
        nodes_registry=nodes_registry,
        endpoint=endpoint,
    )


def stop_worker(
    name: str,
    *,
    target: str = "lenovo",
    route_map: str | None = None,
    nodes_registry: str | None = None,
    endpoint: str | None = None,
) -> dict[str, Any]:
    return call_uri(
        f"node://{target}/command/stop-worker",
        payload={"name": name},
        route_map=route_map,
        nodes_registry=nodes_registry,
        endpoint=endpoint,
    )


def workers(
    *,
    target: str = "lenovo",
    route_map: str | None = None,
    nodes_registry: str | None = None,
    endpoint: str | None = None,
) -> dict[str, Any]:
    return call_uri(
        f"node://{target}/query/workers",
        route_map=route_map,
        nodes_registry=nodes_registry,
        endpoint=endpoint,
    )
