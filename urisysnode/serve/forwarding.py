"""Forward pack registration and release handling."""

from __future__ import annotations

from typing import Any

from uri_control.edge.runtime import Runtime


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

    from ..artifact_resolver import contract_spec_from_release

    spec = contract_spec_from_release(release)
    return (out_scheme or spec["scheme"], clean or spec["patterns"])


def hotload_release_pack(
    runtime: Runtime,
    contract_id: str,
    version: str,
    *,
    catalog_url: str,
    profile_path: str | None = None,
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
    from ..artifact_resolver import fetch_release, run_release
    from ..identity import require_paired
    from ..release_verify import verify_release

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
