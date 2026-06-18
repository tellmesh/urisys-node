"""Host-trust approval policy: node profile auto-approves trusted operations.

serve.apply_host_trust (wired into serve.call_uri) lets the node profile's
`policy.require_approval_for` decide approval instead of forcing the caller to pass
`approved` on every side-effecting command.
"""

from __future__ import annotations

from uri_control.edge.runtime import Runtime
import urishell

from urisysnode import serve

SHELL_URI = "shell://pip"
PAYLOAD = {"args": ["install", "-U", "urihim"]}


def _runtime(policy):
    config = {} if policy is None else {"policy": policy}
    rt = Runtime(config=config)
    urishell.register(rt)
    return rt


def test_no_policy_keeps_caller_approval_default():
    """Without `require_approval_for` in the profile, an unapproved command is denied."""
    rt = _runtime(None)
    out = serve.call_uri(rt, SHELL_URI, PAYLOAD, {"dry_run": True})
    assert out["ok"] is False
    assert out.get("type") == "policy_denied"


def test_empty_list_grants_full_trust():
    """`require_approval_for: []` → node auto-approves; no caller approval needed."""
    rt = _runtime({"require_approval_for": []})
    out = serve.call_uri(rt, SHELL_URI, PAYLOAD, {"dry_run": True})
    assert out["ok"] is True
    assert out["result"]["driver"] == "mock"


def test_matching_pattern_still_requires_approval():
    """An operation matching a gated glob is NOT auto-approved (stays denied)."""
    rt = _runtime({"require_approval_for": ["*"]})
    out = serve.call_uri(rt, SHELL_URI, PAYLOAD, {"dry_run": True})
    assert out["ok"] is False
    assert out.get("type") == "policy_denied"


def test_caller_can_still_approve_when_gated():
    """Even when gated by policy, an explicit caller approval goes through."""
    rt = _runtime({"require_approval_for": ["*"]})
    out = serve.call_uri(rt, SHELL_URI, PAYLOAD, {"dry_run": True, "approved": True})
    assert out["ok"] is True
