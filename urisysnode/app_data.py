"""Persistent app data for ifURI and other clients (chat history)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .identity import default_data_root


def default_app_chat_path() -> Path:
    override = __import__("os").environ.get("URISYS_NODE_APP_CHAT")
    if override:
        return Path(override)
    return default_data_root() / "app-chat.jsonl"


class AppChatStore:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else default_app_chat_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        channel_id: str,
        role: str,
        text: str,
        *,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = {
            "message_id": str(uuid.uuid4()),
            "channel_id": channel_id,
            "role": role,
            "text": text,
            "meta": meta or {},
            "at": datetime.now(timezone.utc).isoformat(),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def list_messages(self, channel_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
        if not channel_id or not self.path.exists():
            return []
        limit = max(1, min(int(limit), 500))
        matched: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("channel_id") == channel_id:
                matched.append(row)
        return matched[-limit:]

    def list_channels(self, *, limit: int = 100) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        limit = max(1, min(int(limit), 500))
        by_id: dict[str, dict[str, Any]] = {}
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            cid = row.get("channel_id")
            if not cid:
                continue
            by_id[str(cid)] = {
                "channel_id": str(cid),
                "last_at": row.get("at"),
                "last_role": row.get("role"),
                "preview": str(row.get("text") or "")[:120],
                "message_count": int(by_id.get(str(cid), {}).get("message_count") or 0) + 1,
            }
        items = sorted(by_id.values(), key=lambda x: x.get("last_at") or "", reverse=True)
        return items[:limit]
