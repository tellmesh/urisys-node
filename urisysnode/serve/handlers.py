"""HTTP request handlers for urisys-node."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler
from typing import Any

from uri_control.edge.runtime import Runtime

from ..pack_resolver import auto_install_enabled
from .app_chat import _app_chat_get, _app_chat_post


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
                from ..identity import health_payload

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
                    from .forwarding import hotload_release_pack

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
                from ..runtime import load_pack_into_runtime

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
            try:
                req = json.loads(body or "{}")
            except json.JSONDecodeError as exc:
                return self._json(
                    400,
                    {"ok": False, "error": f"invalid JSON body: {exc}", "hint": "escape backslashes in shell payloads or use lenovo_remote_session.py"},
                )
            from .server import call_uri

            result = call_uri(
                runtime,
                req.get("uri", ""),
                req.get("payload") or {},
                req.get("context") or {},
            )
            return self._json(200 if result.get("ok") else 400, result)

    return Handler
