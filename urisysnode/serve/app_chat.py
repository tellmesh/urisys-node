"""App chat endpoint handlers."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse

from uri_control.edge.runtime import Runtime


def _app_chat_store(runtime: Runtime):
    from ..app_data import AppChatStore

    store = getattr(runtime, "_app_chat_store", None)
    if store is None:
        store = AppChatStore()
        runtime._app_chat_store = store  # type: ignore[attr-defined]
    return store


def _app_chat_get(path: str, runtime: Runtime) -> tuple[int, dict[str, Any]]:
    parsed = urlparse(path)
    qs = parse_qs(parsed.query)
    if parsed.path == "/app/chat/messages":
        channel_id = (qs.get("channel_id") or qs.get("channel") or [""])[0]
        if not channel_id:
            return 400, {"ok": False, "error": "channel_id required"}
        try:
            limit = int((qs.get("limit") or ["200"])[0])
        except ValueError:
            limit = 200
        messages = _app_chat_store(runtime).list_messages(channel_id, limit=limit)
        return 200, {"ok": True, "channel_id": channel_id, "messages": messages, "count": len(messages)}
    if parsed.path == "/app/chat/channels":
        try:
            limit = int((qs.get("limit") or ["100"])[0])
        except ValueError:
            limit = 100
        channels = _app_chat_store(runtime).list_channels(limit=limit)
        return 200, {"ok": True, "channels": channels, "count": len(channels)}
    return 404, {"ok": False, "error": "not found"}


def _app_chat_post(body: dict[str, Any], runtime: Runtime) -> tuple[int, dict[str, Any]]:
    channel_id = str(body.get("channel_id") or body.get("channel") or "").strip()
    role = str(body.get("role") or "user").strip() or "user"
    text = str(body.get("text") or "").strip()
    meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
    if not channel_id or not text:
        return 400, {"ok": False, "error": "channel_id and text required"}
    row = _app_chat_store(runtime).append(channel_id, role, text, meta=meta)
    return 200, {"ok": True, "message": row}
