from __future__ import annotations

import errno
import importlib
import json
import os
import re
import signal
import shutil
import socket
import subprocess
import sys
import time
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .identity import default_events_path, health_payload, load_identity
from .pack_resolver import (
    CORE_PACKS,
    PACK_MODULES,
    auto_install_enabled,
    ensure_pack_pypi,
    ensure_real_deps,
    pack_for_scheme,
    pack_importable,
    scheme_for_uri,
)
from .runtime import Runtime, load_json


def _extend_pack_paths() -> None:
    """No-op — legacy vendored paths removed after tellmesh pack migration."""


def _pack_modules() -> dict[str, str]:
    """Fresh pack map (reloadable after pip install -U urisys-node)."""
    from urisysnode import pack_resolver as pr

    importlib.reload(pr)
    return pr.PACK_MODULES


def _register_pack(
    rt: Runtime,
    pack: str,
    *,
    try_install: bool = False,
    pack_modules: dict[str, str] | None = None,
) -> bool:
    """Import and register one capability pack. Optional packs that are not
    installed are skipped with a warning unless try_install triggers PyPI."""
    modules = pack_modules if pack_modules is not None else PACK_MODULES
    module_name = modules.get(pack)
    if module_name is None:
        warnings.warn(f"Unknown urisys-node pack '{pack}' — skipping.", stacklevel=2)
        return False
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        top = module_name.split(".", 1)[0]
        if exc.name not in (module_name, top):
            raise
        if pack in CORE_PACKS:
            raise
        if try_install and auto_install_enabled():
            pip_result = ensure_pack_pypi(pack, install=True)
            if pip_result.get("ok"):
                importlib.invalidate_caches()
                module = importlib.import_module(module_name)
            else:
                warnings.warn(
                    f"Skipping urisys-node pack '{pack}': pip install failed ({pip_result.get('error')})",
                    stacklevel=2,
                )
                return False
        else:
            warnings.warn(
                f"Skipping urisys-node pack '{pack}': module '{module_name}' is not "
                f"installed (pip install {top} or enable URISYS_NODE_AUTO_INSTALL=1).",
                stacklevel=2,
            )
            return False
    module.register(rt)
    return True


def build_runtime(config_path: str | None = None) -> Runtime:
    _extend_pack_paths()
    from urisysnode.env import load_urisys_env

    load_urisys_env()
    config_file = config_path or os.environ.get("URISYS_NODE_CONFIG", "config/node-profile.json")
    config = load_json(config_file) if Path(config_file).exists() else {}
    rt = Runtime(events_path=default_events_path(), config=config)
    rt._instance_id = f"{os.getpid()}:{time.time():.3f}"  # type: ignore[attr-defined]

    # Minimal boot: node (bundled), screen + shell (pip deps). kvm/him/ocr/llm on first URI.
    packs = os.environ.get("URISYS_NODE_PACKS", "node,screen,shell").split(",")
    packs = [p.strip() for p in packs if p.strip()]

    rt._loaded_packs = set()  # type: ignore[attr-defined]
    for pack in packs:
        if _register_pack(rt, pack, try_install=auto_install_enabled()):
            rt._loaded_packs.add(pack)  # type: ignore[attr-defined]

    try:
        from urisysnode.forward_config import load_forward_entries, wire_forward_packs

        forwards = load_forward_entries(config=config)
        if forwards:
            rt.config["forwards"] = forwards
            wire_forward_packs(rt, forwards)
    except Exception as exc:
        warnings.warn(f"forward pack wiring skipped: {exc}", stacklevel=2)

    try:
        from urisysnode.forward_config import (
            load_release_forward_entries,
            wire_release_forward_packs,
        )

        release_forwards = load_release_forward_entries(config=config)
        if release_forwards:
            rt.config["release_forwards"] = release_forwards
            for result in wire_release_forward_packs(rt, release_forwards):
                if not result.get("ok"):
                    warnings.warn(
                        f"release forward {result.get('contract_id')}@{result.get('version')} "
                        f"skipped at stage '{result.get('stage')}': {result.get('error')}",
                        stacklevel=2,
                    )
    except Exception as exc:
        warnings.warn(f"release forward wiring skipped: {exc}", stacklevel=2)

    try:
        _bootstrap_worker_packs(rt)
    except Exception as exc:
        warnings.warn(f"worker pack bootstrap skipped: {exc}", stacklevel=2)

    return rt


def _bootstrap_worker_packs(rt: Runtime) -> None:
    """Spawn the packs listed in URISYS_NODE_WORKER_PACKS as out-of-process
    workers and wire their routes to forward into this router. Existing workers
    from a previous run are re-attached instead of re-spawned."""
    raw = os.environ.get("URISYS_NODE_WORKER_PACKS", "").strip()
    worker_packs = [p.strip() for p in raw.split(",") if p.strip()]
    if not worker_packs:
        return

    from .supervisor import PackSupervisor

    sup = PackSupervisor(rt)
    rt._supervisor = sup  # type: ignore[attr-defined]
    sup.restore()
    for pack in worker_packs:
        if pack in sup.workers and sup.workers[pack].alive():
            continue
        sup.spawn(pack=pack, install=not pack_importable(pack))
    sup.start_monitor()


def load_pack_into_runtime(
    runtime: Runtime,
    pack: str,
    *,
    install: bool = False,
    specs: list[str] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Hot-load a capability pack. With install=True or auto-install, pip install first."""
    pack = (pack or "").strip()
    if not pack:
        return {"ok": False, "error": "pack name is required"}
    loaded = getattr(runtime, "_loaded_packs", None)
    if loaded is None:
        loaded = set()
        runtime._loaded_packs = loaded  # type: ignore[attr-defined]
    pack_routes: dict[str, set[str]] = getattr(runtime, "_pack_route_patterns", {})
    if not hasattr(runtime, "_pack_route_patterns"):
        runtime._pack_route_patterns = pack_routes  # type: ignore[attr-defined]
    if pack in loaded and not force:
        return {"ok": True, "pack": pack, "loaded": True, "already_loaded": True, "new_routes": []}

    pip_result = None
    if install or (auto_install_enabled() and not pack_importable(pack)):
        pip_result = ensure_pack_pypi(pack, install=True, specs=specs)
        if not pip_result.get("ok"):
            return {"ok": False, "pack": pack, "loaded": False, "pip": pip_result}
        if pip_result.get("ok") and not pip_result.get("skipped"):
            importlib.invalidate_caches()

    if pack in loaded and force:
        drop = pack_routes.get(pack, set())
        if drop:
            runtime.routes = [r for r in runtime.routes if r.pattern not in drop]
        loaded.discard(pack)
        pack_routes.pop(pack, None)
        from urisysnode import pack_resolver as pr

        importlib.reload(pr)
        module_name = pr.PACK_MODULES.get(pack, "").split(".", 1)[0]
        if module_name and module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        importlib.invalidate_caches()

    before = {r.pattern for r in runtime.routes}
    try:
        ok = _register_pack(runtime, pack, try_install=False, pack_modules=_pack_modules())
    except ModuleNotFoundError as exc:
        return {"ok": False, "pack": pack, "loaded": False, "error": str(exc), "pip": pip_result}
    except Exception as exc:
        return {"ok": False, "pack": pack, "loaded": False, "error": str(exc), "pip": pip_result}
    if ok:
        loaded.add(pack)
        added = {r.pattern for r in runtime.routes} - before
        if added:
            pack_routes[pack] = added
    new_routes = sorted({r.pattern for r in runtime.routes} - before)
    out: dict[str, Any] = {"ok": bool(ok), "pack": pack, "loaded": bool(ok), "new_routes": new_routes}
    if not ok:
        mod = PACK_MODULES.get(pack, pack)
        out["error"] = out.get("error") or f"failed to import/register pack module {mod!r}"
    if pip_result:
        out["pip"] = pip_result
    return out


def ensure_pack_for_uri(runtime: Runtime, uri: str) -> dict[str, Any] | None:
    """If URI scheme maps to an unloaded pack, install (PyPI) and register it."""
    scheme = scheme_for_uri(uri)
    pack = pack_for_scheme(scheme)
    if not pack:
        return None
    loaded = getattr(runtime, "_loaded_packs", set())
    if pack in loaded:
        return None
    return load_pack_into_runtime(runtime, pack, install=not pack_importable(pack))


def call_uri(runtime: Runtime, uri: str, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Runtime.call with lazy pack install and real-backend deps on first use."""
    result = runtime.call(uri, payload, context)
    if (
        not result.get("ok")
        and result.get("type") == "route_not_found"
        and auto_install_enabled()
    ):
        prep = ensure_pack_for_uri(runtime, uri)
        if prep and prep.get("loaded"):
            result = runtime.call(uri, payload, context)
            result.setdefault("auto_install", {})["pack"] = prep
    err = str(result.get("error") or "")
    if not result.get("ok") and auto_install_enabled() and "pip install" in err.lower():
        scheme = scheme_for_uri(uri)
        pack = pack_for_scheme(scheme) or ("screen" if scheme == "screen" else None)
        if pack and (context.get("allow_real") or os.environ.get("URISYS_ALLOW_REAL") == "1"):
            real = ensure_real_deps(pack, install=True)
            if real.get("ok"):
                importlib.invalidate_caches()
                result = runtime.call(uri, payload, context)
                result.setdefault("auto_install", {})["real"] = real
        elif scheme == "screen" and (context.get("allow_real") or os.environ.get("URISYS_ALLOW_REAL") == "1"):
            real = ensure_real_deps("screen", install=True)
            if real.get("ok"):
                importlib.invalidate_caches()
                result = runtime.call(uri, payload, context)
                result.setdefault("auto_install", {})["real"] = real
    return result


def register_forward_pack(
    runtime: Runtime,
    scheme: str,
    endpoint: str,
    patterns: list[str],
) -> dict[str, Any]:
    """Make a capability served by an out-of-process worker available on this
    node: route each of the contract's declared URI patterns to a forwarding
    handler that calls the worker at ``endpoint``. This is how an artifact
    resolved from a markpact.com release (OCI image on GitHub) is wired in."""
    scheme = (scheme or "").strip()
    endpoint = (endpoint or "").strip()
    if not scheme or not endpoint:
        return {"ok": False, "error": "scheme and endpoint are required"}
    if not patterns:
        return {"ok": False, "error": "at least one uri pattern is required"}
    loaded = getattr(runtime, "_loaded_packs", None)
    if loaded is None:
        loaded = set()
        runtime._loaded_packs = loaded  # type: ignore[attr-defined]
    runtime.config.setdefault("forward_targets", {})[scheme] = endpoint
    before = {r.pattern for r in runtime.routes}
    for pattern in patterns:
        if pattern in before:
            continue
        kind = "command" if "/command/" in pattern else "query"
        runtime.register(
            pattern,
            "python://urisysnode.forward:forward_call",
            kind=kind,
            operation="forward",
            approval="required" if kind == "command" else "not_required",
            side_effects=kind == "command",
        )
    loaded.add(scheme)
    new_routes = sorted({r.pattern for r in runtime.routes} - before)
    return {"ok": True, "scheme": scheme, "endpoint": endpoint, "new_routes": new_routes}


def _release_forward_spec(
    release: dict[str, Any],
    scheme: str | None,
    patterns: list[str] | None,
) -> tuple[str, list[str]]:
    """Resolve the URI scheme and patterns to wire for a release. Precedence:
    caller-supplied > inline on the release payload > parsed from the contract
    the release references. The contract is the source of truth, so we fall back
    to it whenever the catalog response does not already carry the patterns."""
    out_scheme = (scheme or release.get("scheme") or "").strip()
    out_patterns = patterns or release.get("patterns") or []
    clean = [str(p).strip() for p in out_patterns if str(p).strip()]
    if out_scheme and clean:
        return out_scheme, clean

    from .artifact_resolver import contract_spec_from_release

    spec = contract_spec_from_release(release)
    return (out_scheme or spec["scheme"], clean or spec["patterns"])


def hotload_release_pack(
    runtime: Runtime,
    contract_id: str,
    version: str,
    *,
    catalog_url: str,
    profile_path: str | Path,
    context: dict[str, Any] | None = None,
    container: str = "urisys-stepper-worker",
    port: int = 8791,
    scheme: str | None = None,
    patterns: list[str] | None = None,
) -> dict[str, Any]:
    """Hot-load a capability from a markpact.com release: pairing-gated and
    signature-gated, fetch the release, pull/run its OCI worker, then wire the
    contract's URI patterns to forward to that worker. This is the glue over
    resolve_from_release + register_forward_pack."""
    from .artifact_resolver import fetch_release, run_release
    from .identity import require_paired
    from .release_verify import verify_release

    ctx = context or {}
    contract_id = (contract_id or "").strip()
    version = (version or "").strip()
    if not contract_id or not version:
        return {"ok": False, "stage": "request", "error": "contract and version are required"}

    try:
        require_paired(ctx)
    except PermissionError as exc:
        return {"ok": False, "stage": "pairing", "error": str(exc)}

    try:
        release = fetch_release(catalog_url, contract_id, version)
    except Exception as exc:
        return {"ok": False, "stage": "fetch", "error": str(exc)}

    verdict = verify_release(release, context=ctx)
    if not verdict.get("ok"):
        return {"ok": False, "stage": "verify", "error": verdict.get("error"), "signature": verdict}

    try:
        fwd_scheme, fwd_patterns = _release_forward_spec(release, scheme, patterns)
    except Exception as exc:
        return {"ok": False, "stage": "spec", "error": str(exc), "signature": verdict}
    if not fwd_scheme or not fwd_patterns:
        return {
            "ok": False,
            "stage": "spec",
            "error": "release does not declare scheme/patterns; pass them explicitly",
            "signature": verdict,
        }

    try:
        run = run_release(release, profile_path, container=container, port=port)
    except Exception as exc:
        return {"ok": False, "stage": "run", "error": str(exc), "signature": verdict}

    endpoint = f"http://127.0.0.1:{run['port']}"
    reg = register_forward_pack(runtime, fwd_scheme, endpoint, fwd_patterns)
    return {
        "ok": bool(reg.get("ok")),
        "stage": "registered" if reg.get("ok") else "register",
        "contract_id": contract_id,
        "version": version,
        "scheme": fwd_scheme,
        "endpoint": endpoint,
        "worker": run,
        "forward": reg,
        "signature": verdict,
    }


def _app_chat_store(runtime: Runtime):
    from .app_data import AppChatStore

    store = getattr(runtime, "_app_chat_store", None)
    if store is None:
        store = AppChatStore()
        runtime._app_chat_store = store  # type: ignore[attr-defined]
    return store


def _app_chat_get(path: str, runtime: Runtime) -> tuple[int, dict[str, Any]]:
    parsed = urlparse(path)
    qs = parse_qs(parsed.query)
    if parsed.path == "/app/chat/messages":
        channel_id = (qs.get("channel_id") or qs.get("channel") or [""])[0]
        if not channel_id:
            return 400, {"ok": False, "error": "channel_id required"}
        try:
            limit = int((qs.get("limit") or ["200"])[0])
        except ValueError:
            limit = 200
        messages = _app_chat_store(runtime).list_messages(channel_id, limit=limit)
        return 200, {"ok": True, "channel_id": channel_id, "messages": messages, "count": len(messages)}
    if parsed.path == "/app/chat/channels":
        try:
            limit = int((qs.get("limit") or ["100"])[0])
        except ValueError:
            limit = 100
        channels = _app_chat_store(runtime).list_channels(limit=limit)
        return 200, {"ok": True, "channels": channels, "count": len(channels)}
    return 404, {"ok": False, "error": "not found"}


def _app_chat_post(body: dict[str, Any], runtime: Runtime) -> tuple[int, dict[str, Any]]:
    channel_id = str(body.get("channel_id") or body.get("channel") or "").strip()
    role = str(body.get("role") or "user").strip() or "user"
    text = str(body.get("text") or "").strip()
    meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
    if not channel_id or not text:
        return 400, {"ok": False, "error": "channel_id and text required"}
    row = _app_chat_store(runtime).append(channel_id, role, text, meta=meta)
    return 200, {"ok": True, "message": row}


def make_handler(runtime: Runtime):
    allow_pack_load = (
        os.environ.get("URISYS_NODE_ALLOW_PACK_LOAD", "1" if auto_install_enabled() else "0") == "1"
    )

    class Handler(BaseHTTPRequestHandler):
        def _json(self, status: int, data: dict[str, Any]) -> None:
            raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:
            if self.path == "/health":
                return self._json(200, health_payload(runtime=runtime))
            if self.path in ("/uri/routes", "/routes"):
                return self._json(200, {"ok": True, "routes": [r.pattern for r in runtime.routes]})
            if self.path.startswith("/events"):
                limit = 50
                if "limit=" in self.path:
                    try:
                        limit = int(self.path.split("limit=", 1)[1])
                    except ValueError:
                        pass
                return self._json(200, {"ok": True, "events": runtime.events.tail(limit)})
            if self.path.startswith("/app/chat/"):
                status, data = _app_chat_get(self.path, runtime)
                return self._json(status, data)
            return self._json(404, {"ok": False, "error": "not found"})

        def do_POST(self) -> None:
            if self.path == "/uri/pack":
                if not allow_pack_load:
                    return self._json(403, {
                        "ok": False,
                        "error": "pack loading disabled; set URISYS_NODE_ALLOW_PACK_LOAD=1",
                    })
                length = int(self.headers.get("Content-Length") or "0")
                req = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                contract = str(req.get("contract") or req.get("contract_id") or "").strip()
                if contract:
                    # Release hot-load: resolve a markpact.com release to an OCI
                    # worker and forward its scheme. Pairing/signature gated.
                    ctx = req.get("context") if isinstance(req.get("context"), dict) else {}
                    catalog = str(
                        req.get("catalog")
                        or req.get("catalog_url")
                        or os.environ.get("MARKPACT_CATALOG_URL", "https://markpact.com")
                    )
                    profile = str(
                        req.get("profile")
                        or os.environ.get("URISYS_NODE_PROFILE", "config/node-profile.json")
                    )
                    req_patterns = req.get("patterns")
                    result = hotload_release_pack(
                        runtime,
                        contract,
                        str(req.get("version") or ""),
                        catalog_url=catalog,
                        profile_path=profile,
                        context=ctx,
                        scheme=str(req.get("scheme")).strip() if req.get("scheme") else None,
                        patterns=[str(p) for p in req_patterns] if isinstance(req_patterns, list) else None,
                    )
                    status = 200 if result.get("ok") else (403 if result.get("stage") == "pairing" else 400)
                    return self._json(status, result)
                install = bool(req.get("install", True))
                force = bool(req.get("force", False))
                specs = req.get("specs")
                override = [str(s) for s in specs] if isinstance(specs, list) else None
                result = load_pack_into_runtime(
                    runtime,
                    str(req.get("pack") or ""),
                    install=install,
                    specs=override,
                    force=force,
                )
                return self._json(200 if result.get("ok") else 400, result)
            if self.path == "/app/chat/messages":
                length = int(self.headers.get("Content-Length") or "0")
                req = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                status, data = _app_chat_post(req, runtime)
                return self._json(status, data)
            if self.path != "/uri/call":
                return self._json(404, {"ok": False, "error": "not found"})
            length = int(self.headers.get("Content-Length") or "0")
            body = self.rfile.read(length).decode("utf-8")
            req = json.loads(body or "{}")
            result = call_uri(
                runtime,
                req.get("uri", ""),
                req.get("payload") or {},
                req.get("context") or {},
            )
            return self._json(200 if result.get("ok") else 400, result)

    return Handler


def _pidfile_path(port: int) -> Path:
    from .identity import default_events_path

    return Path(default_events_path()).parent / f"urisys-node.{port}.pid"


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError as exc:
        return exc.errno == errno.EPERM


def _read_cmdline(pid: int) -> str:
    try:
        raw = (Path("/proc") / str(pid) / "cmdline").read_bytes()
    except OSError:
        return ""
    return raw.replace(b"\0", b" ").decode("utf-8", errors="replace")


def _pids_serve_cmdline(port: int) -> list[int]:
    """PIDs whose cmdline looks like ``urisys node serve`` / ``urisys-node serve`` on ``port``."""
    port_s = str(port)
    pids: list[int] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        cmd = _read_cmdline(pid).lower()
        if "serve" not in cmd:
            continue
        if port_s not in cmd:
            continue
        if "urisys" not in cmd and "urisys-node" not in cmd:
            continue
        pids.append(pid)
    return pids


def _pids_on_port_ss(port: int) -> list[int]:
    """Parse ``ss -ltnp`` for listeners on ``port`` (fallback when /proc/fd scan misses)."""
    try:
        proc = subprocess.run(
            ["ss", "-ltnp", f"sport = :{port}"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []
    pids: list[int] = []
    for match in re.finditer(r"pid=(\d+)", proc.stdout or ""):
        try:
            pids.append(int(match.group(1)))
        except ValueError:
            continue
    return pids


def _fuser_kill_port(port: int) -> bool:
    """Last-resort: ``fuser -k PORT/tcp`` when pid discovery failed."""
    if not shutil.which("fuser"):
        return False
    try:
        subprocess.run(
            [shutil.which("fuser") or "fuser", "-k", f"{port}/tcp"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return True
    except (subprocess.TimeoutExpired, OSError):
        return False


def _pids_on_port(port: int) -> list[int]:
    """Find PIDs holding a LISTEN socket on ``port`` via /proc (no deps)."""
    inodes: set[str] = set()
    for proto in ("tcp", "tcp6"):
        try:
            lines = Path(f"/proc/net/{proto}").read_text(encoding="utf-8").splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            parts = line.split()
            if len(parts) < 10 or parts[3] != "0A":  # 0A = LISTEN
                continue
            try:
                if int(parts[1].rsplit(":", 1)[1], 16) == port:
                    inodes.add(parts[9])
            except (ValueError, IndexError):
                continue
    if not inodes:
        return []
    pids: list[int] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            for fd in (entry / "fd").iterdir():
                try:
                    target = os.readlink(fd)
                except OSError:
                    continue
                if target.startswith("socket:[") and target[8:-1] in inodes:
                    pids.append(int(entry.name))
                    break
        except OSError:
            continue
    return pids


def _kill_pid(pid: int, *, timeout: float = 6.0) -> None:
    try:
        pgid = os.getpgid(pid)
        if pgid == pid:
            os.killpg(pgid, signal.SIGTERM)
        else:
            os.kill(pid, signal.SIGTERM)
    except OSError:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not _pid_alive(pid):
            return
        time.sleep(0.2)
    try:
        pgid = os.getpgid(pid)
        if pgid == pid:
            os.killpg(pgid, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGKILL)
    except OSError:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    time.sleep(0.1)


def _worker_pids_from_state() -> list[int]:
    """PIDs persisted by PackSupervisor (out-of-process pack workers)."""
    state = Path("data/workers.json")
    if not state.is_file():
        alt = Path(default_events_path()).parent / "workers.json"
        if alt.is_file():
            state = alt
        else:
            return []
    try:
        records = json.loads(state.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    pids: list[int] = []
    for rec in records if isinstance(records, list) else []:
        try:
            pid = int(rec.get("pid") or 0)
        except (TypeError, ValueError):
            continue
        if pid > 0 and _pid_alive(pid):
            pids.append(pid)
    return pids


def _wait_port_free(host: str, port: int, *, timeout: float = 10.0) -> bool:
    bind_host = host if host not in ("", "0.0.0.0") else "0.0.0.0"
    deadline = time.time() + timeout
    while time.time() < deadline:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((bind_host, port))
            s.close()
            return True
        except OSError:
            s.close()
            time.sleep(0.25)
    return False


def _is_node_serve_process(pid: int, port: int, *, listeners: set[int] | None = None) -> bool:
    """True if ``pid`` is the urisys node HTTP listener (not a shell one-liner)."""
    if listeners and pid in listeners:
        return True
    cmd = _read_cmdline(pid)
    if not cmd:
        return False
    low = cmd.lower()
    argv0 = low.split(" ", 1)[0]
    if argv0.endswith(("bash", "sh", "dash", "zsh", "fish", "nohup", "setsid")):
        return False
    if " -c " in low and ("bash" in argv0 or "/bin/sh" in argv0):
        return False
    if "serve" not in low:
        return False
    if "urisys" not in low and "urisys-node" not in low and "urisysnode" not in low:
        return False
    if str(port) in cmd:
        return True
    try:
        for chunk in Path(f"/proc/{pid}/environ").read_bytes().split(b"\0"):
            if chunk.startswith(b"URISYS_NODE_PORT="):
                return int(chunk.split(b"=", 1)[1]) == port
    except (OSError, ValueError, IndexError):
        pass
    return False


def _collect_takeover_targets(port: int, self_pid: int) -> set[int]:
    listeners = set(_pids_on_port(port)) | set(_pids_on_port_ss(port))
    targets: set[int] = set()

    for pid in listeners:
        if pid != self_pid:
            targets.add(pid)

    pidfile = _pidfile_path(port)
    try:
        old = int(pidfile.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        old = 0
    if old and old != self_pid and _pid_alive(old):
        if old in listeners or _is_node_serve_process(old, port, listeners=listeners):
            targets.add(old)

    if targets:
        for pid in _worker_pids_from_state():
            if pid != self_pid:
                targets.add(pid)

    return targets


def takeover_port(host: str, port: int) -> dict[str, Any]:
    """Kill any existing urisys node on ``port`` so a fresh serve can bind it.

    This makes ``urisys node serve`` behave like an atomic restart: the old
    instance is terminated (pidfile, port listeners, cmdline match, workers),
    we wait for the port to free, then the caller binds. No external bash."""
    self_pid = os.getpid()
    killed: list[int] = []
    used_fuser = False

    for attempt in range(3):
        targets = _collect_takeover_targets(port, self_pid)
        for pid in sorted(targets):
            if pid not in killed:
                _kill_pid(pid)
                killed.append(pid)
        if _wait_port_free(host, port, timeout=6.0):
            return {"killed": killed, "port_free": True, "attempts": attempt + 1, "fuser": used_fuser}
        time.sleep(0.4)

    if not _wait_port_free(host, port, timeout=1.0):
        used_fuser = _fuser_kill_port(port)
        time.sleep(0.5)

    freed = _wait_port_free(host, port, timeout=8.0)
    return {"killed": killed, "port_free": freed, "attempts": 3, "fuser": used_fuser}


class _ReuseHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def serve(runtime: Runtime, host: str, port: int, *, takeover: bool = True) -> None:
    if takeover:
        info = takeover_port(host, port)
        if info["killed"]:
            print(f"takeover: terminated old instance pid(s) {info['killed']}")
        elif info.get("fuser"):
            print(f"takeover: fuser -k {port}/tcp")
        if not info["port_free"]:
            raise OSError(
                f"port {port} still in use after takeover "
                f"(killed={info['killed']}, fuser={info.get('fuser')}); "
                f"check: ss -ltnp 'sport = :{port}'"
            )

    pidfile = _pidfile_path(port)
    pidfile.parent.mkdir(parents=True, exist_ok=True)
    pidfile.write_text(str(os.getpid()), encoding="utf-8")

    def _cleanup(*_args: Any) -> None:
        sup = getattr(runtime, "_supervisor", None)
        if sup is not None:
            try:
                sup.shutdown()
            except Exception:
                pass
        try:
            if pidfile.read_text(encoding="utf-8").strip() == str(os.getpid()):
                pidfile.unlink()
        except OSError:
            pass

    import atexit

    atexit.register(_cleanup)
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, lambda *_a: sys.exit(0))
        except (ValueError, OSError):
            pass

    identity = load_identity()
    bootstrap = None
    try:
        from urisysnode.display_bootstrap import bootstrap_wayland_capture

        bootstrap = bootstrap_wayland_capture()
        runtime.config["display_bootstrap"] = bootstrap
    except Exception as exc:
        warnings.warn(f"display bootstrap skipped: {exc}", stacklevel=2)
    try:
        server = _ReuseHTTPServer((host, port), make_handler(runtime))
    except OSError as exc:
        if takeover and exc.errno in (errno.EADDRINUSE, 98):
            info = takeover_port(host, port)
            if info["killed"]:
                print(f"takeover (late): terminated pid(s) {info['killed']}")
            if info["port_free"]:
                server = _ReuseHTTPServer((host, port), make_handler(runtime))
            else:
                raise OSError(
                    f"port {port} in use and takeover failed (killed={info['killed']})"
                ) from exc
        else:
            raise
    print(f"urisys-node listening on http://{host}:{port}")
    print(f"node_id={identity['node_id']} fingerprint={identity.get('fingerprint')}")
    print("endpoints: GET /health  GET /uri/routes  GET /events  POST /uri/call  POST /uri/pack")
    print(f"auto_install={'on' if auto_install_enabled() else 'off'} (URISYS_NODE_AUTO_INSTALL)")
    if bootstrap:
        print(f"display_bootstrap={bootstrap.get('ok')} session={bootstrap.get('session', bootstrap.get('reason', '-'))}")
    for route in runtime.routes:
        print(" -", route.pattern)
    server.serve_forever()
