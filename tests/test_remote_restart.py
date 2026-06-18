"""urisys-node remote restart helpers."""

from __future__ import annotations

from urisysnode.remote import _restart_scheduled, schedule_restart


def test_restart_scheduled_treats_connection_drop_as_ok():
    out = _restart_scheduled({"ok": False, "error": "Remote end closed connection without response"})
    assert out["ok"] is True
    assert out["scheduled"] is True


def test_restart_scheduled_passes_through_real_errors():
    out = _restart_scheduled({"ok": False, "error": "approval required"})
    assert out["ok"] is False


def test_schedule_restart_forwards_endpoint(monkeypatch):
    seen: dict = {}

    def fake_call_uri(uri, **kwargs):
        seen["uri"] = uri
        seen.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr("urisysnode.remote.call_uri", fake_call_uri)
    schedule_restart(endpoint="http://192.168.188.201:8790", port=8791)
    assert seen["endpoint"] == "http://192.168.188.201:8790"
    assert "8791/tcp" in seen["payload"]["args"][1]
