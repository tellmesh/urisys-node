from __future__ import annotations

import json
import os
from unittest import mock

import urisysnode.forward_config as fc
from uri_control.edge.runtime import Runtime
from urisysnode.serve import build_runtime


def _runtime(tmp_path) -> Runtime:
    rt = Runtime(events_path=str(tmp_path / "events.jsonl"))
    rt._loaded_packs = set()
    return rt


def test_load_forward_entries_from_config():
    config = {
        "forwards": [
            {
                "scheme": "imgl",
                "endpoint": "http://127.0.0.1:8219",
                "patterns": ["imgl://{host}/image/latest/query/layout"],
            }
        ]
    }
    entries = fc.load_forward_entries(config=config)
    assert len(entries) == 1
    assert entries[0]["scheme"] == "imgl"


def test_load_forward_entries_env_inline():
    payload = json.dumps([
        {
            "scheme": "vql",
            "endpoint": "http://127.0.0.1:8220",
            "patterns": ["vql://{host}/ui/latest/query/compare"],
        }
    ])
    with mock.patch.dict(os.environ, {"URISYS_NODE_FORWARDS": payload}, clear=False):
        entries = fc.load_forward_entries()
    assert entries[0]["scheme"] == "vql"


def test_wire_forward_packs_registers_routes(tmp_path):
    rt = _runtime(tmp_path)
    results = fc.wire_forward_packs(
        rt,
        [{
            "scheme": "imgl",
            "endpoint": "http://127.0.0.1:8219",
            "patterns": ["imgl://{host}/image/latest/query/layout"],
        }],
    )
    assert results[0]["ok"] is True
    assert "imgl" in rt._loaded_packs
    assert any(r.pattern.startswith("imgl://") for r in rt.routes)


def test_command_register_forward(tmp_path):
    rt = _runtime(tmp_path)
    import urisysnode.handlers as handlers

    out = handlers.command_register_forward(
        {
            "scheme": "vql",
            "endpoint": "http://127.0.0.1:8220",
            "patterns": ["vql://{host}/ui/latest/query/detect"],
        },
        {"approved": True, "runtime": rt},
    )
    assert out["ok"] is True
    assert "vql" in rt._loaded_packs


def test_load_release_forward_entries_from_config():
    config = {
        "release_forwards": [
            {"contract": "urihim.contract", "version": "1.0.0"},
            {"contract_id": "urikvm.contract", "version": "1.0.0", "catalog": "https://cat"},
            {"version": "1.0.0"},  # no contract — dropped
        ]
    }
    entries = fc.load_release_forward_entries(config=config)
    assert len(entries) == 2
    assert entries[0]["contract"] == "urihim.contract"
    assert entries[0]["catalog"] == fc.DEFAULT_CATALOG_URL
    assert entries[1]["catalog"] == "https://cat"


def test_load_release_forward_entries_env_inline():
    payload = json.dumps({"contract": "urihim.contract", "version": "1.0.0"})
    with mock.patch.dict(os.environ, {"URISYS_NODE_RELEASE_FORWARDS": payload}, clear=False):
        entries = fc.load_release_forward_entries()
    assert entries[0]["contract"] == "urihim.contract"


def test_wire_release_forward_packs_calls_hotload(tmp_path, monkeypatch):
    rt = _runtime(tmp_path)
    calls = []

    def fake_hotload(runtime, contract, version, *, catalog_url, profile_path):
        calls.append((contract, version, catalog_url))
        return {"ok": True, "stage": "registered", "contract_id": contract, "version": version}

    monkeypatch.setattr(fc, "hotload_release_pack", fake_hotload)
    results = fc.wire_release_forward_packs(
        rt, [{"contract": "urihim.contract", "version": "1.0.0", "catalog": "https://cat"}]
    )
    assert results[0]["ok"] is True
    assert calls == [("urihim.contract", "1.0.0", "https://cat")]


def test_wire_release_forward_packs_is_best_effort(tmp_path, monkeypatch):
    rt = _runtime(tmp_path)

    def fake_hotload(runtime, contract, version, **k):
        if contract == "bad.contract":
            return {"ok": False, "stage": "run", "error": "docker missing", "contract_id": contract}
        return {"ok": True, "stage": "registered", "contract_id": contract}

    monkeypatch.setattr(fc, "hotload_release_pack", fake_hotload)
    results = fc.wire_release_forward_packs(
        rt,
        [
            {"contract": "bad.contract", "version": "1.0.0", "catalog": "c"},
            {"contract": "good.contract", "version": "1.0.0", "catalog": "c"},
        ],
    )
    assert [r["ok"] for r in results] == [False, True]  # one failure does not abort the rest


def test_build_runtime_wires_config_forwards(tmp_path, monkeypatch):
    config_path = tmp_path / "profile.json"
    config_path.write_text(
        json.dumps({
            "forwards": [{
                "scheme": "imgl",
                "endpoint": "http://127.0.0.1:8219",
                "patterns": ["imgl://{host}/image/latest/query/layout"],
            }],
        }),
        encoding="utf-8",
    )
    monkeypatch.setenv("URISYS_NODE_CONFIG", str(config_path))
    monkeypatch.setenv("URISYS_NODE_PACKS", "node")
    rt = build_runtime(str(config_path))
    assert any(r.pattern.startswith("imgl://") for r in rt.routes)
