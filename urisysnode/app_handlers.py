"""URI handlers for app:// chat data exposed to ifURI and other clients."""

from __future__ import annotations

from typing import Any

from .app_data import AppChatStore


def _store(context: dict[str, Any]) -> AppChatStore:
    runtime = context.get("runtime")
    cached = getattr(runtime, "_app_chat_store", None) if runtime is not None else None
    if cached is not None:
        return cached
    store = AppChatStore()
    if runtime is not None:
        runtime._app_chat_store = store  # type: ignore[attr-defined]
    return store


def query_chat_messages(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    channel_id = str(payload.get("channel_id") or payload.get("channel") or "").strip()
    if not channel_id:
        return {"ok": False, "error": "channel_id required"}
    limit = int(payload.get("limit") or 200)
    messages = _store(context).list_messages(channel_id, limit=limit)
    return {"ok": True, "channel_id": channel_id, "messages": messages, "count": len(messages)}


def command_chat_append(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    channel_id = str(payload.get("channel_id") or payload.get("channel") or "").strip()
    role = str(payload.get("role") or "user").strip() or "user"
    text = str(payload.get("text") or "").strip()
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    if not channel_id or not text:
        return {"ok": False, "error": "channel_id and text required"}
    row = _store(context).append(channel_id, role, text, meta=meta)
    return {"ok": True, "message": row}


def query_chat_channels(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    limit = int(payload.get("limit") or 100)
    channels = _store(context).list_channels(limit=limit)
    return {"ok": True, "channels": channels, "count": len(channels)}
