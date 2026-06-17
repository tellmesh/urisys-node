"""Gate a markpact.com release before it is hot-loaded onto this node.

The hot-load path (POST /uri/pack with {contract, version, catalog}) pulls and
runs an OCI worker resolved from a release. That is a privileged, side-effecting
operation, so the release must clear two gates first:

* pairing  — the node must be enrolled to a controller (handled by
  ``urisysnode.identity.require_paired``); the caller does that before us.
* signature — the release metadata must carry a signature from a key this node
  trusts (the markpact.com root + GitHub provenance model).

Signature checking is *fail-closed when required*: if a signature is demanded by
policy but missing, made with an untrusted key, or unverifiable because no crypto
backend is installed, this returns ``ok: False``. When the policy does not require
a signature it passes through with ``verified: False`` so existing flows keep
working until keys are provisioned on the live fleet.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any

SIGNATURE_KEY = "signature"


def signature_required(context: dict[str, Any] | None = None) -> bool:
    """Policy: is a verified signature mandatory for a release hot-load?

    Defaults to off so packs resolve on fleets that have not provisioned keys
    yet; turn on with URISYS_NODE_REQUIRE_SIGNATURE=1 or context.require_signature.
    """
    if context and context.get("require_signature"):
        return True
    return os.environ.get("URISYS_NODE_REQUIRE_SIGNATURE", "0") == "1"


def canonical_digest(release: dict[str, Any]) -> str:
    """SHA-256 over the release with its signature block removed, canonicalised
    (sorted keys, tight separators) so signer and verifier hash the same bytes."""
    body = {k: v for k, v in release.items() if k != SIGNATURE_KEY}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def load_trusted_keys() -> dict[str, str]:
    """Map of keyid -> base64 ed25519 public key trusted by this node.

    Source is URISYS_NODE_TRUSTED_KEYS: either inline JSON ({"keyid": "b64key"})
    or a path to a JSON file with the same shape.
    """
    raw = os.environ.get("URISYS_NODE_TRUSTED_KEYS", "").strip()
    if not raw:
        return {}
    if not raw.startswith("{"):
        path = Path(raw)
        if not path.exists():
            raise ValueError(f"URISYS_NODE_TRUSTED_KEYS path not found: {raw}")
        raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("trusted keys must be a JSON object of keyid -> public key")
    return {str(k): str(v) for k, v in data.items()}


def _ed25519_verify(public_key_b64: str, message: bytes, signature_b64: str) -> bool:
    """Verify a detached ed25519 signature. Raises RuntimeError if no crypto
    backend is installed, so the caller can fail closed rather than silently pass."""
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on host
        raise RuntimeError(
            "signature required but no crypto backend; pip install cryptography"
        ) from exc

    key = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64))
    try:
        key.verify(base64.b64decode(signature_b64), message)
        return True
    except InvalidSignature:
        return False


def verify_release(
    release: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
    trusted_keys: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Decide whether ``release`` may be hot-loaded. Returns a verdict dict with
    ``ok`` plus diagnostics; never raises for an untrusted release."""
    required = signature_required(context)
    sig = release.get(SIGNATURE_KEY)

    if not required:
        return {
            "ok": True,
            "verified": False,
            "required": False,
            "reason": "signature check disabled (URISYS_NODE_REQUIRE_SIGNATURE=0)",
        }

    if not isinstance(sig, dict):
        return {"ok": False, "verified": False, "required": True, "error": "release is unsigned"}

    alg = str(sig.get("alg") or "ed25519")
    if alg != "ed25519":
        return {"ok": False, "verified": False, "required": True, "error": f"unsupported signature alg: {alg}"}

    keyid = str(sig.get("keyid") or "")
    sig_b64 = str(sig.get("sig") or "")
    if not keyid or not sig_b64:
        return {"ok": False, "verified": False, "required": True, "error": "signature missing keyid or sig"}

    try:
        keys = trusted_keys if trusted_keys is not None else load_trusted_keys()
    except (ValueError, json.JSONDecodeError) as exc:
        return {"ok": False, "verified": False, "required": True, "error": f"trusted keys unavailable: {exc}"}

    public_key = keys.get(keyid)
    if not public_key:
        return {"ok": False, "verified": False, "required": True, "error": f"untrusted signing key: {keyid}"}

    digest = canonical_digest(release)
    try:
        ok = _ed25519_verify(public_key, digest.encode("utf-8"), sig_b64)
    except RuntimeError as exc:
        return {"ok": False, "verified": False, "required": True, "error": str(exc)}

    if not ok:
        return {"ok": False, "verified": False, "required": True, "keyid": keyid, "error": "signature mismatch"}

    return {"ok": True, "verified": True, "required": True, "keyid": keyid, "digest": digest}
