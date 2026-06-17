"""Test-only capability pack: registers a trivial fake:// scheme."""

from __future__ import annotations

from typing import Any


def _ping(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del context
    return {"ok": True, "pong": True, "echo": payload.get("msg")}


def register(rt: Any) -> None:
    rt.register(
        "fake://{target}/query/ping",
        "python://_fakepack:_ping",
        kind="query",
        operation="fake.ping",
    )
