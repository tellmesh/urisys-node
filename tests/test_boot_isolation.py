"""Boot-time comms/execution separation: only the control plane runs in-process."""

from __future__ import annotations

import urisysnode.runtime.builder as builder


def _record_attempts(monkeypatch):
    attempted: list[str] = []

    def fake_register(rt, pack, **kw):
        attempted.append(pack)
        return True

    monkeypatch.setattr(builder, "_register_pack", fake_register)
    monkeypatch.setenv("URISYS_NODE_AUTO_INSTALL", "0")
    monkeypatch.setenv("URISYS_NODE_PACKS", "node,screen,shell")
    return attempted


def test_default_isolation_boots_only_control_plane(monkeypatch):
    monkeypatch.delenv("URISYS_NODE_ISOLATION", raising=False)  # default = persistent
    attempted = _record_attempts(monkeypatch)
    rt = builder.build_runtime()
    # Execution packs (screen, shell) are NOT loaded in the router process; they
    # isolate into workers lazily on first use.
    assert attempted == ["node"]
    assert rt._loaded_packs == {"node"}


def test_isolation_off_boots_all_in_process(monkeypatch):
    monkeypatch.setenv("URISYS_NODE_ISOLATION", "off")
    attempted = _record_attempts(monkeypatch)
    builder.build_runtime()
    assert attempted == ["node", "screen", "shell"]
