"""Tests for urisys-node app chat storage."""

from __future__ import annotations

import os

import pytest

os.environ["URISYS_NODE_SKIP_PAIRING"] = "1"


@pytest.fixture()
def chat_path(tmp_path, monkeypatch):
    path = tmp_path / "app-chat.jsonl"
    monkeypatch.setenv("URISYS_NODE_DATA", str(tmp_path))
    monkeypatch.setenv("URISYS_NODE_APP_CHAT", str(path))
    return path


def test_append_and_list_messages(chat_path):
    from urisysnode.app_data import AppChatStore

    store = AppChatStore(chat_path)
    store.append("node:127.0.0.1:8790", "user", "hello")
    store.append("node:127.0.0.1:8790", "assistant", "world")
    store.append("mcp:fs", "user", "list files")

    msgs = store.list_messages("node:127.0.0.1:8790")
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["text"] == "world"


def test_list_channels(chat_path):
    from urisysnode.app_data import AppChatStore

    store = AppChatStore(chat_path)
    store.append("node:127.0.0.1:8790", "user", "ping")
    store.append("mcp:fs", "assistant", "pong")

    channels = store.list_channels()
    ids = {c["channel_id"] for c in channels}
    assert "node:127.0.0.1:8790" in ids
    assert "mcp:fs" in ids


def test_uri_handlers(chat_path):
    from urisysnode.app_handlers import command_chat_append, query_chat_messages
    from urisysnode.serve import build_runtime

    rt = build_runtime()
    ctx = {"runtime": rt}
    append = command_chat_append(
        {"channel_id": "node:test", "role": "user", "text": "status"},
        ctx,
    )
    assert append["ok"] is True
    listed = query_chat_messages({"channel_id": "node:test"}, ctx)
    assert listed["count"] == 1
    assert listed["messages"][0]["text"] == "status"
