"""Pack installation operations."""

from __future__ import annotations

from typing import Any

from .client import call_uri


def install_pack(
    pack: str,
    *,
    specs: list[str] | None = None,
    force: bool = True,
    route_map: str | None = None,
    nodes_registry: str | None = None,
    endpoint: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"pack": pack, "install": True, "force": force}
    if specs:
        payload["specs"] = specs
    return call_uri(
        "node://lenovo/command/install-pack",
        payload=payload,
        route_map=route_map,
        nodes_registry=nodes_registry,
        endpoint=endpoint,
    )
