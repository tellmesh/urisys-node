"""Forwarding handler for capabilities served by a resolved worker.

When a node hot-loads a capability as an out-of-process worker (e.g. an OCI
image resolved via the artifact-index from a markpact.com release), it registers
the contract's URI patterns to this handler. Calls are then forwarded to the
worker over HTTP, so the node transparently "gains" the capability.
"""

from __future__ import annotations

from typing import Any

from .client import remote_call

# Only user-meaningful context travels to the worker; runtime-injected keys
# (runtime/state/event_store) are dropped so the body stays JSON-serializable.
_FORWARD_CONTEXT_KEYS = ("approved", "allow_real", "dry_run", "environment", "approval")


def forward_call(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    uri = str(context.get("uri") or "")
    scheme = uri.split("://", 1)[0] if "://" in uri else ""
    targets = (context.get("config") or {}).get("forward_targets") or {}
    endpoint = targets.get(scheme)
    if not endpoint:
        return {"ok": False, "uri": uri, "type": "forward_no_target",
                "error": f"no forward target for scheme {scheme!r}"}
    fwd_ctx = {k: context[k] for k in _FORWARD_CONTEXT_KEYS if k in context}
    try:
        return remote_call(endpoint, uri, payload, fwd_ctx)
    except Exception as exc:  # network/worker errors surface as a clean failure
        return {"ok": False, "uri": uri, "type": "forward_failed",
                "error": f"{type(exc).__name__}: {exc}", "endpoint": endpoint}
