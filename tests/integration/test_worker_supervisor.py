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

from uri_control.edge.runtime import Runtime  # noqa: E402
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


def test_call_ephemeral_runs_and_tears_down(tmp_path):
    """A per-call worker executes the call, returns its result, then is gone:
    no persistent worker is registered and no forward route leaks onto the router."""
    rt = _router(tmp_path)
    sup = PackSupervisor(rt, state_path=tmp_path / "workers.json")
    try:
        out = sup.call_ephemeral(
            "fake://node/query/ping", {"msg": "yo"}, {"approved": True},
            module="_fakepack", env=_worker_env(),
        )
        assert out["ok"] is True, out
        assert out["result"]["pong"] is True
        assert out["result"]["echo"] == "yo"
        assert out.get("isolation") == "ephemeral"
        # nothing persisted: no registered worker, no forward route on the router
        assert "_fakepack" not in sup.workers
        assert not any(r.pattern.startswith("fake://") for r in rt.routes)
    finally:
        sup.shutdown()


def test_persistent_worker_crash_is_isolated_and_respawned(tmp_path):
    """Killing a pack worker must NOT take the router down; the monitor respawns
    it and forwarding resumes — the core guarantee behind default separation."""
    import os
    import signal
    import time

    rt = _router(tmp_path)
    sup = PackSupervisor(rt, state_path=tmp_path / "workers.json")
    try:
        assert sup.spawn(module="_fakepack", env=_worker_env())["ok"]
        first_pid = sup.workers["_fakepack"].proc.pid

        # Hard-kill the worker process (simulated crash).
        os.kill(first_pid, signal.SIGKILL)
        deadline = time.time() + 10
        while time.time() < deadline and sup.workers["_fakepack"].alive():
            time.sleep(0.1)
        assert not sup.workers["_fakepack"].alive()

        # Router itself is untouched: its route table still resolves.
        assert any(r.pattern.startswith("fake://") for r in rt.routes)

        # Monitor reaps the dead worker and brings the capability back.
        sup._reap()
        assert sup.workers["_fakepack"].proc.pid != first_pid
        out = rt.call("fake://node/query/ping", {"msg": "back"}, {"approved": True})
        assert out["ok"] is True
        assert out["result"]["result"]["echo"] == "back"
    finally:
        sup.shutdown()
