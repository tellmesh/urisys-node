"""PackSupervisor must pass URISYS_NODE_CONFIG into worker subprocesses."""

from __future__ import annotations

import json
import os
from pathlib import Path

from uri_control.edge.runtime import Runtime
from urisysnode.supervisor import PackSupervisor


def test_default_worker_env_uses_runtime_config_path(tmp_path, monkeypatch):
    monkeypatch.delenv("URISYS_NODE_CONFIG", raising=False)
    prof = tmp_path / "node-profile.json"
    prof.write_text(json.dumps({"kvm": {"driver": "mss"}}))
    rt = Runtime(events_path=str(tmp_path / "events.jsonl"), config=json.loads(prof.read_text()))
    rt._config_path = str(prof)  # type: ignore[attr-defined]
    sup = PackSupervisor(rt, state_path=tmp_path / "workers.json")
    env = sup._default_worker_env()
    assert env["URISYS_NODE_CONFIG"] == str(prof.resolve())
    assert env.get("URISYS_ALLOW_REAL") == "1"
    assert env.get("URISYS_NODE_ROUTER") == "http://127.0.0.1:8790"
