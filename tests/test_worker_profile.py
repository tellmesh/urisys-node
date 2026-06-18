"""Worker runtime must load the node profile (URISYS_NODE_CONFIG).

Without it, packs hosted out-of-process (kvm/screen/him) fall back to mock drivers
because the profile's driver/policy config never reaches context['config'].
"""

from __future__ import annotations

import json

from urisysnode import worker


def _write_fake_module(tmp_path):
    mod = tmp_path / "wp_fakepack.py"
    mod.write_text(
        "def register(rt):\n"
        "    rt.register('fake://{t}/query/ping', 'python://wp_fakepack:_p',"
        " kind='query', operation='fake.ping')\n"
        "def _p(payload, context):\n"
        "    return {'ok': True, 'config_seen': context.get('config')}\n"
    )
    return mod


def test_worker_runtime_loads_profile(tmp_path, monkeypatch):
    prof = tmp_path / "node-profile.json"
    prof.write_text(json.dumps({"kvm": {"driver": "mss"}, "policy": {"require_pairing": False}}))
    monkeypatch.setenv("URISYS_NODE_CONFIG", str(prof))
    _write_fake_module(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))

    rt, info = worker.build_worker_runtime(module="wp_fakepack")

    assert info["ok"] is True
    # profile reached the worker runtime config (was {} before the fix → mock drivers)
    assert rt.config.get("kvm", {}).get("driver") == "mss"

    # and it flows into the call context the handlers read
    out = rt.call("fake://x/query/ping", {}, {})
    assert out["ok"] is True
    assert out["result"]["config_seen"]["kvm"]["driver"] == "mss"


def test_missing_profile_is_empty_not_error(tmp_path, monkeypatch):
    # isolate discovery: nonexistent env + empty HOME + cwd without config/ → nothing found
    monkeypatch.setenv("URISYS_NODE_CONFIG", str(tmp_path / "does-not-exist.json"))
    monkeypatch.delenv("URISYS_NODE_DATA", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
    monkeypatch.chdir(tmp_path)
    assert worker._load_node_profile() == {}
