"""Out-of-process pack workers wired into a thin router.

A capability runs in its own worker process; the router forwards matching URI
calls to it. This is the replacement for whole-node-restart pack upgrades: a
worker can be restarted/replaced independently while the router keeps its routes.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "packages" / "python"
sys.path.insert(0, str(PKG))

from urisysedge.runtime import Runtime  # noqa: E402
import urisysnode.routes as node_routes  # noqa: E402
from urisysnode.supervisor import PackSupervisor  # noqa: E402
from urisysnode.worker import build_worker_runtime  # noqa: E402

HERE = Path(__file__).resolve().parent


def _router(tmp_path) -> Runtime:
    rt = Runtime(events_path=str(tmp_path / "events.jsonl"))
    node_routes.register(rt)
    rt._loaded_packs = {"node"}
    return rt


def _worker_env() -> dict[str, str]:
    return {"PYTHONPATH": os.pathsep.join([str(HERE), str(PKG), os.environ.get("PYTHONPATH", "")])}


def test_build_worker_runtime_loads_module():
    rt, info = build_worker_runtime(module="urisysnode.routes")
    assert info["ok"] is True
    assert any(r.pattern.startswith("node://") for r in rt.routes)


def test_supervisor_spawns_and_router_forwards(tmp_path):
    rt = _router(tmp_path)
    assert not any(r.pattern.startswith("fake://") for r in rt.routes)

    sup = PackSupervisor(rt, state_path=tmp_path / "workers.json")
    try:
        res = sup.spawn(module="_fakepack", env=_worker_env())
        assert res["ok"], res

        # forward route is now live on the thin router
        assert any(r.pattern.startswith("fake://") for r in rt.routes)

        out = rt.call("fake://node/query/ping", {"msg": "hi"}, {"approved": True})
        assert out["ok"] is True
        assert out["result"]["result"]["pong"] is True
        assert out["result"]["result"]["echo"] == "hi"

        status = sup.status()
        assert any(w["name"] == "_fakepack" and w["alive"] for w in status["workers"])
    finally:
        sup.shutdown()


def test_supervisor_restart_keeps_routes(tmp_path):
    rt = _router(tmp_path)
    sup = PackSupervisor(rt, state_path=tmp_path / "workers.json")
    try:
        assert sup.spawn(module="_fakepack", env=_worker_env())["ok"]
        first_port = sup.workers["_fakepack"].port

        restarted = sup.restart("_fakepack")
        assert restarted["ok"], restarted
        assert sup.workers["_fakepack"].port != first_port  # fresh process

        out = rt.call("fake://node/query/ping", {}, {"approved": True})
        assert out["ok"] is True
    finally:
        sup.shutdown()


def test_supervisor_stop_terminates_worker(tmp_path):
    rt = _router(tmp_path)
    sup = PackSupervisor(rt, state_path=tmp_path / "workers.json")
    try:
        assert sup.spawn(module="_fakepack", env=_worker_env())["ok"]
        stopped = sup.stop("_fakepack")
        assert stopped["ok"] is True
        assert "_fakepack" not in sup.workers
    finally:
        sup.shutdown()
