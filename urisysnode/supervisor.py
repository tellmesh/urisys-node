"""Router-side supervisor for out-of-process capability workers.

The node router stays thin: it owns the route table and forwards URI calls. Each
heavy/independent capability runs as its own worker process (see ``worker.py``).
The supervisor spawns workers, polls them healthy, discovers their URI patterns,
wires forward routes into the router, monitors liveness (respawning the dead),
and persists bindings so a router restart re-attaches instead of losing packs.

This generalises the existing ``register_forward_pack`` (built for OCI release
workers) to locally spawned pack workers.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _free_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]


def _http_get(url: str, timeout: float = 2.0) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _schemes_of(patterns: list[str]) -> dict[str, list[str]]:
    by_scheme: dict[str, list[str]] = {}
    for pattern in patterns:
        scheme = pattern.split("://", 1)[0] if "://" in pattern else ""
        if not scheme:
            continue
        by_scheme.setdefault(scheme, []).append(pattern)
    return by_scheme


@dataclass
class Worker:
    name: str
    endpoint: str
    port: int
    pack: str | None = None
    module: str | None = None
    patterns: list[str] = field(default_factory=list)
    schemes: list[str] = field(default_factory=list)
    proc: subprocess.Popen[Any] | None = None
    pid: int | None = None
    install: bool = False
    specs: list[str] | None = None
    env: dict[str, str] | None = None

    def alive(self) -> bool:
        if self.proc is not None:
            return self.proc.poll() is None
        try:
            _http_get(self.endpoint + "/health")
            return True
        except Exception:
            return False

    def to_record(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "endpoint": self.endpoint,
            "port": self.port,
            "pack": self.pack,
            "module": self.module,
            "patterns": self.patterns,
            "schemes": self.schemes,
            "pid": self.proc.pid if self.proc else self.pid,
        }


class PackSupervisor:
    def __init__(
        self,
        runtime: Any,
        *,
        host: str = "127.0.0.1",
        python_exe: str | None = None,
        state_path: str | Path | None = None,
        health_timeout: float = 30.0,
    ) -> None:
        self.runtime = runtime
        self.host = host
        self.python_exe = python_exe or sys.executable
        self.state_path = Path(state_path) if state_path else Path("data/workers.json")
        self.health_timeout = health_timeout
        self.workers: dict[str, Worker] = {}
        self._lock = threading.RLock()
        self._monitor: threading.Thread | None = None
        self._monitor_stop = threading.Event()

    # -- lifecycle ---------------------------------------------------------
    def spawn(
        self,
        *,
        pack: str | None = None,
        module: str | None = None,
        install: bool = False,
        specs: list[str] | None = None,
        env: dict[str, str] | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        name = module or pack or ""
        if not name:
            return {"ok": False, "error": "spawn requires pack or module"}
        with self._lock:
            existing = self.workers.get(name)
            if existing and existing.alive() and not force:
                return {"ok": True, "name": name, "already_running": True, **existing.to_record()}
            if existing:
                self._terminate(existing)

            port = _free_port(self.host)
            cmd = [self.python_exe, "-m", "urisysnode.worker", "--host", self.host, "--port", str(port)]
            if module:
                cmd += ["--module", module]
            else:
                cmd += ["--pack", str(pack)]
            if install:
                cmd.append("--install")
            for spec in specs or []:
                cmd += ["--spec", spec]

            proc_env = dict(os.environ)
            if env:
                proc_env.update(env)
            proc = subprocess.Popen(
                cmd,
                env=proc_env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            endpoint = f"http://{self.host}:{port}"
            worker = Worker(
                name=name,
                endpoint=endpoint,
                port=port,
                pack=pack,
                module=module,
                proc=proc,
                install=install,
                specs=specs,
                env=env,
            )

            ready = self._wait_health(worker)
            if not ready:
                self._terminate(worker)
                return {"ok": False, "name": name, "error": "worker did not become healthy", "endpoint": endpoint}

            try:
                patterns = self._fetch_patterns(worker)
            except Exception as exc:
                self._terminate(worker)
                return {"ok": False, "name": name, "error": f"route discovery failed: {exc}"}

            worker.patterns = patterns
            wired = self._wire(worker)
            self.workers[name] = worker
            self._persist()
            return {"ok": True, "name": name, **worker.to_record(), "wired": wired}

    def restart(self, name: str) -> dict[str, Any]:
        with self._lock:
            worker = self.workers.get(name)
            if not worker:
                return {"ok": False, "error": f"no worker named {name!r}"}
            return self.spawn(
                pack=worker.pack,
                module=worker.module,
                install=worker.install,
                specs=worker.specs,
                env=worker.env,
                force=True,
            )

    def stop(self, name: str) -> dict[str, Any]:
        with self._lock:
            worker = self.workers.pop(name, None)
            if not worker:
                return {"ok": False, "error": f"no worker named {name!r}"}
            self._terminate(worker)
            self._persist()
            return {"ok": True, "name": name, "stopped": True}

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "ok": True,
                "workers": [
                    {**w.to_record(), "alive": w.alive()} for w in self.workers.values()
                ],
            }

    def shutdown(self) -> None:
        self._monitor_stop.set()
        with self._lock:
            for worker in self.workers.values():
                self._terminate(worker)
            self.workers.clear()

    # -- monitor -----------------------------------------------------------
    def start_monitor(self, interval_s: float = 5.0) -> None:
        if self._monitor and self._monitor.is_alive():
            return

        def _loop() -> None:
            while not self._monitor_stop.wait(interval_s):
                self._reap()

        self._monitor_stop.clear()
        self._monitor = threading.Thread(target=_loop, name="pack-supervisor", daemon=True)
        self._monitor.start()

    def _reap(self) -> None:
        with self._lock:
            for name, worker in list(self.workers.items()):
                if worker.alive():
                    continue
                self.spawn(
                    pack=worker.pack,
                    module=worker.module,
                    install=worker.install,
                    specs=worker.specs,
                    env=worker.env,
                    force=True,
                )

    # -- restore -----------------------------------------------------------
    def restore(self) -> list[dict[str, Any]]:
        if not self.state_path.exists():
            return []
        try:
            records = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        results: list[dict[str, Any]] = []
        for rec in records if isinstance(records, list) else []:
            name = rec.get("name")
            endpoint = rec.get("endpoint")
            if not name or not endpoint:
                continue
            worker = Worker(
                name=name,
                endpoint=endpoint,
                port=int(rec.get("port") or 0),
                pack=rec.get("pack"),
                module=rec.get("module"),
                patterns=list(rec.get("patterns") or []),
                pid=rec.get("pid"),
            )
            if worker.alive():
                worker.patterns = worker.patterns or self._fetch_patterns(worker)
                self._wire(worker)
                self.workers[name] = worker
                results.append({"name": name, "reattached": True})
            else:
                results.append(self.spawn(pack=worker.pack, module=worker.module, force=True))
        return results

    # -- internals ---------------------------------------------------------
    def _wait_health(self, worker: Worker) -> bool:
        deadline = time.time() + self.health_timeout
        while time.time() < deadline:
            if worker.proc is not None and worker.proc.poll() is not None:
                return False
            try:
                _http_get(worker.endpoint + "/health")
                return True
            except Exception:
                time.sleep(0.25)
        return False

    def _fetch_patterns(self, worker: Worker) -> list[str]:
        data = _http_get(worker.endpoint + "/uri/routes")
        return [str(p) for p in (data.get("routes") or [])]

    def _wire(self, worker: Worker) -> list[dict[str, Any]]:
        from .serve import register_forward_pack

        results: list[dict[str, Any]] = []
        worker.schemes = []
        for scheme, patterns in _schemes_of(worker.patterns).items():
            reg = register_forward_pack(self.runtime, scheme, worker.endpoint, patterns)
            worker.schemes.append(scheme)
            results.append(reg)
        return results

    def _terminate(self, worker: Worker) -> None:
        proc = worker.proc
        if proc is None:
            return
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    def _persist(self) -> None:
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            records = [w.to_record() for w in self.workers.values()]
            self.state_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass
