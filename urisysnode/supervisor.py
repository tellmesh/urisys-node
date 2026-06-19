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
        health_timeout: float = 90.0,
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

    def _default_worker_env(self) -> dict[str, str]:
        """Propagate node profile + display session vars into pack worker subprocesses."""
        env: dict[str, str] = {}
        config_file = os.environ.get("URISYS_NODE_CONFIG") or getattr(self.runtime, "_config_path", None)
        if not config_file:
            config_file = "config/node-profile.json"
        config_path = Path(str(config_file)).expanduser()
        if config_path.is_file():
            env["URISYS_NODE_CONFIG"] = str(config_path.resolve())
        if os.environ.get("URISYS_ALLOW_REAL"):
            env["URISYS_ALLOW_REAL"] = os.environ["URISYS_ALLOW_REAL"]
        else:
            env.setdefault("URISYS_ALLOW_REAL", "1")
        for key in ("DISPLAY", "WAYLAND_DISPLAY", "XDG_RUNTIME_DIR", "XDG_SESSION_TYPE", "URISYS_HIM_DRIVER"):
            if os.environ.get(key):
                env[key] = os.environ[key]
        if not os.environ.get("URISYS_NODE_ROUTER"):
            port = int(os.environ.get("URISYS_NODE_PORT", "8790"))
            env["URISYS_NODE_ROUTER"] = f"http://{self.host}:{port}"
        return env

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
            proc_env.update(self._default_worker_env())
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

    def call_ephemeral(
        self,
        uri: str,
        payload: dict[str, Any] | None,
        context: dict[str, Any] | None,
        *,
        pack: str | None = None,
        module: str | None = None,
        install: bool = False,
        specs: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Run a single URI call in a throwaway worker process, then tear it down.

        Unlike :meth:`spawn`, this never registers the worker, never wires forward
        routes and is never respawned by the monitor: the process exists only for
        the duration of one call. A crash therefore cannot affect the router or any
        other in-flight task — the strongest isolation boundary available."""
        name = module or pack or ""
        if not name:
            return {"ok": False, "error": "ephemeral call requires pack or module"}

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
        proc_env.update(self._default_worker_env())
        if env:
            proc_env.update(env)
        proc = subprocess.Popen(cmd, env=proc_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        worker = Worker(
            name=name, endpoint=f"http://{self.host}:{port}", port=port,
            pack=pack, module=module, proc=proc, install=install, specs=specs, env=env,
        )
        try:
            if not self._wait_health(worker):
                return {"ok": False, "name": name, "type": "ephemeral_unhealthy",
                        "error": "ephemeral worker did not become healthy", "endpoint": worker.endpoint}
            from .forward import _FORWARD_CONTEXT_KEYS
            from .client import remote_call

            ctx = context or {}
            fwd = {k: ctx[k] for k in _FORWARD_CONTEXT_KEYS if k in ctx}
            try:
                out = remote_call(worker.endpoint, uri, payload or {}, fwd)
            except Exception as exc:
                return {"ok": False, "uri": uri, "type": "ephemeral_failed",
                        "error": f"{type(exc).__name__}: {exc}", "endpoint": worker.endpoint}
            if isinstance(out, dict):
                out.setdefault("isolation", "ephemeral")
            return out
        finally:
            self._terminate(worker)

    def restart(self, name: str) -> dict[str, Any]:
        with self._lock:
            worker = self.workers.get(name)
            if not worker:
                return {"ok": False, "error": f"no worker named {name!r}"}
            # The wheel was already pip-installed on first spawn, so a restart
            # must NOT re-run pip (that exceeds the health window and wedges the
            # restart). Re-install only if the pack is no longer importable.
            return self.spawn(
                pack=worker.pack,
                module=worker.module,
                install=self._needs_install(worker),
                specs=worker.specs,
                env=worker.env,
                force=True,
            )

    def _needs_install(self, worker: Worker) -> bool:
        if not worker.pack:
            return False
        try:
            from .pack_resolver import pack_importable

            return not pack_importable(worker.pack)
        except Exception:
            return worker.install

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
                    install=self._needs_install(worker),
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
