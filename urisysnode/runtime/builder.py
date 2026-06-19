"""Runtime builder functions for urisys-node."""

from __future__ import annotations

import importlib
import os
import sys
import time
import warnings
from typing import Any

from uri_control.edge.runtime import Runtime, load_json

from urisysnode.identity import default_events_path
from urisysnode.pack_resolver import (
    CORE_PACKS,
    PACK_MODULES,
    auto_install_enabled,
    ensure_boot_pack,
    ensure_pack_pypi,
)


def _extend_pack_paths() -> None:
    """No-op — legacy vendored paths removed after tellmesh pack migration."""


def _pack_modules() -> dict[str, str]:
    """Fresh pack map (reloadable after pip install -U urisys-node)."""
    from urisysnode import pack_resolver as pr

    importlib.reload(pr)
    return pr.PACK_MODULES


def _register_pack(
    rt: Any,
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
        if exc.name and exc.name not in (module_name, top):
            raise
        if try_install and auto_install_enabled():
            pip_fn = ensure_boot_pack if pack in CORE_PACKS else ensure_pack_pypi
            pip_result = pip_fn(pack, install=True)
            if pip_result.get("ok"):
                importlib.invalidate_caches()
                module = importlib.import_module(module_name)
            elif pack in CORE_PACKS:
                detail = pip_result.get("error") or pip_result.get("stderr") or "pip install failed"
                raise ModuleNotFoundError(
                    f"core pack '{pack}' requires module '{module_name}' (pip install failed: {detail})"
                ) from exc
            else:
                warnings.warn(
                    f"Skipping urisys-node pack '{pack}': pip install failed ({pip_result.get('error')})",
                    stacklevel=2,
                )
                return False
        elif pack in CORE_PACKS:
            raise
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
    """Build and configure a Runtime instance for urisys-node."""
    from urisysnode.runtime.config import _default_real_config, resolve_node_config
    from urisysnode.runtime.packs import _bootstrap_worker_packs

    _extend_pack_paths()
    from urisysnode.env import load_urisys_env

    load_urisys_env()
    config_file = resolve_node_config(config_path)
    config = {}
    if config_file:
        try:
            config = load_json(config_file) or {}
            if not isinstance(config, dict):
                raise ValueError("profile is not a JSON object")
        except Exception as exc:
            warnings.warn(
                f"urisys-node: profile {config_file} is invalid JSON ({exc}) — ignoring it",
                stacklevel=2,
            )
            config, config_file = {}, ""
    if config_file:
        os.environ["URISYS_NODE_CONFIG"] = config_file
    elif os.environ.get("URISYS_ALLOW_REAL") == "1":
        config = _default_real_config()
        warnings.warn(
            "urisys-node: no node profile found — using auto-detected real-driver defaults "
            "(URISYS_ALLOW_REAL=1). Create ~/.config/urisys/node-profile.json to customize.",
            stacklevel=2,
        )
    else:
        warnings.warn(
            "urisys-node: no node profile found and URISYS_ALLOW_REAL unset — running on mock "
            "drivers. Run scripts/enable-host-trust.sh or set URISYS_ALLOW_REAL=1 for real screen/kvm/him.",
            stacklevel=2,
        )
    rt = Runtime(events_path=default_events_path(), config=config)
    rt._config_path = config_file  # type: ignore[attr-defined]
    rt._instance_id = f"{os.getpid()}:{time.time():.3f}"  # type: ignore[attr-defined]

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
