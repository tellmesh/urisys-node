"""Load forward-pack definitions from node config or environment."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .serve import hotload_release_pack, register_forward_pack

DEFAULT_CATALOG_URL = "https://markpact.com"


def _normalize_entry(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    scheme = str(raw.get("scheme") or "").strip()
    endpoint = str(raw.get("endpoint") or "").strip()
    patterns = raw.get("patterns")
    if not scheme or not endpoint or not isinstance(patterns, list) or not patterns:
        return None
    clean_patterns = [str(p).strip() for p in patterns if str(p).strip()]
    if not clean_patterns:
        return None
    return {"scheme": scheme, "endpoint": endpoint, "patterns": clean_patterns}


def load_forward_entries(*, config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Collect forward definitions from config.forwards, env JSON, or env file path."""
    entries: list[dict[str, Any]] = []

    if config:
        for item in config.get("forwards") or []:
            norm = _normalize_entry(item)
            if norm:
                entries.append(norm)

    inline = os.environ.get("URISYS_NODE_FORWARDS", "").strip()
    if inline:
        try:
            parsed = json.loads(inline)
        except json.JSONDecodeError as exc:
            raise ValueError(f"URISYS_NODE_FORWARDS is not valid JSON: {exc}") from exc
        items = parsed if isinstance(parsed, list) else [parsed]
        for item in items:
            norm = _normalize_entry(item)
            if norm:
                entries.append(norm)

    file_path = os.environ.get("URISYS_NODE_FORWARDS_FILE", "").strip()
    if file_path:
        data = json.loads(Path(file_path).read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else [data]
        for item in items:
            norm = _normalize_entry(item)
            if norm:
                entries.append(norm)

    # de-dupe by scheme (last wins)
    by_scheme: dict[str, dict[str, Any]] = {}
    for entry in entries:
        by_scheme[entry["scheme"]] = entry
    return list(by_scheme.values())


def wire_forward_packs(runtime: Any, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for entry in entries:
        results.append(
            register_forward_pack(
                runtime,
                entry["scheme"],
                entry["endpoint"],
                entry["patterns"],
            )
        )
    return results


def _normalize_release_entry(raw: Any) -> dict[str, Any] | None:
    """A release-forward entry self-provisions a capability from a markpact.com
    release at boot: {contract, version, catalog?, profile?}."""
    if not isinstance(raw, dict):
        return None
    contract = str(raw.get("contract") or raw.get("contract_id") or "").strip()
    version = str(raw.get("version") or "").strip()
    if not contract or not version:
        return None
    entry: dict[str, Any] = {
        "contract": contract,
        "version": version,
        "catalog": str(raw.get("catalog") or raw.get("catalog_url") or DEFAULT_CATALOG_URL).strip(),
    }
    profile = raw.get("profile") or raw.get("profile_path")
    if profile:
        entry["profile"] = str(profile)
    return entry


def load_release_forward_entries(*, config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Collect release-forward definitions from config.release_forwards or env JSON."""
    entries: list[dict[str, Any]] = []
    if config:
        for item in config.get("release_forwards") or []:
            norm = _normalize_release_entry(item)
            if norm:
                entries.append(norm)

    inline = os.environ.get("URISYS_NODE_RELEASE_FORWARDS", "").strip()
    if inline:
        try:
            parsed = json.loads(inline)
        except json.JSONDecodeError as exc:
            raise ValueError(f"URISYS_NODE_RELEASE_FORWARDS is not valid JSON: {exc}") from exc
        items = parsed if isinstance(parsed, list) else [parsed]
        for item in items:
            norm = _normalize_release_entry(item)
            if norm:
                entries.append(norm)

    # de-dupe by (contract, version) — last wins
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in entries:
        by_key[(entry["contract"], entry["version"])] = entry
    return list(by_key.values())


def wire_release_forward_packs(runtime: Any, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolve and wire each release-forward at boot. Best-effort: a failure for
    one entry (catalog down, docker missing, unpaired) does not abort the others."""
    default_profile = os.environ.get("URISYS_NODE_PROFILE", "config/node-profile.json")
    results: list[dict[str, Any]] = []
    for entry in entries:
        results.append(
            hotload_release_pack(
                runtime,
                entry["contract"],
                entry["version"],
                catalog_url=entry["catalog"],
                profile_path=entry.get("profile") or default_profile,
            )
        )
    return results
