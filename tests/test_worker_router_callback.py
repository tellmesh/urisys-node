"""Worker runtime forwards non-local schemes to the main node router."""

from __future__ import annotations

from urisysnode import worker


def _write_chain_module(tmp_path):
    mod = tmp_path / "wp_chainpack.py"
    mod.write_text(
        "def register(rt):\n"
        "    rt.register(\n"
        "        'kvm://{h}/task/command/chain',\n"
        "        'python://wp_chainpack:chain',\n"
        "        kind='command',\n"
        "        operation='kvm.chain',\n"
        "    )\n"
        "def chain(payload, context):\n"
        "    ocr = context['runtime'].call('ocr://local/image/query/text', {}, context)\n"
        "    return {'ocr_ok': ocr.get('ok'), 'ocr_uri': ocr.get('uri')}\n"
    )
    return mod


def test_worker_forwards_non_local_scheme_to_router(tmp_path, monkeypatch):
    _write_chain_module(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setenv("URISYS_NODE_ROUTER", "http://127.0.0.1:8790")

    calls: list[tuple[str, str]] = []

    def fake_remote(endpoint, uri, payload=None, context=None):
        calls.append((endpoint, uri))
        return {"ok": True, "uri": uri, "result": {"text": "mock"}}

    monkeypatch.setattr("urisysnode.client.remote_call", fake_remote)

    rt, info = worker.build_worker_runtime(module="wp_chainpack")
    assert info["ok"] is True

    out = rt.call("kvm://lenovo/task/command/chain", {}, {"approved": True})
    assert out["ok"] is True
    assert out["result"]["ocr_ok"] is True
    assert calls == [("http://127.0.0.1:8790", "ocr://local/image/query/text")]


def test_worker_keeps_local_scheme_in_process(tmp_path, monkeypatch):
    mod = tmp_path / "wp_local.py"
    mod.write_text(
        "def register(rt):\n"
        "    rt.register('kvm://{h}/query/ping', 'python://wp_local:ping', kind='query', operation='kvm.ping')\n"
        "def ping(payload, context):\n"
        "    return {'pong': True}\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setenv("URISYS_NODE_ROUTER", "http://127.0.0.1:8790")

    def fail_remote(*_a, **_k):
        raise AssertionError("local kvm call must not hit router")

    monkeypatch.setattr("urisysnode.client.remote_call", fail_remote)

    rt, _ = worker.build_worker_runtime(module="wp_local")
    out = rt.call("kvm://lenovo/query/ping", {}, {})
    assert out["ok"] is True
    assert out["result"]["pong"] is True
