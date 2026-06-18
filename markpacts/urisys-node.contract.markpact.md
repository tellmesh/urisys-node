# urisys-node contract v0.1

Installable slave service. Two contract layers:

| File | Describes |
|------|-----------|
| [`urisys-node.contract.markpact.md`](urisys-node.contract.markpact.md) | HTTP transport (`GET /health`, `POST /uri/call`) |
| [`urisys-node.capabilities.markpact.md`](urisys-node.capabilities.markpact.md) | Capability routes (`node://`, `app://`) — generated from [`../urisysnode/manifest.yaml`](../urisysnode/manifest.yaml) |

## HTTP transport (edge binding)

```yaml markpact:contract
apiVersion: urisys.io/v1
kind: UriContract
metadata:
  id: urisys-node.service
  version: 0.1.0
  title: urisys-node HTTP edge service
scheme: urisys-node
resources:
  - pattern: urisys-node://local/http/health
  - pattern: urisys-node://local/http/uri/routes
  - pattern: urisys-node://local/http/events
  - pattern: urisys-node://local/http/uri/call
queries:
  - id: node.health
    pattern: urisys-node://local/http/query/health
  - id: node.routes
    pattern: urisys-node://local/http/query/routes
commands:
  - id: node.uri.call
    pattern: urisys-node://local/http/command/uri-call
    side_effects: true
    requires_approval: true
```

```txt
GET  /health
GET  /uri/routes
GET  /events
POST /uri/call
```

Identity:

```txt
node_id, fingerprint, public_key, paired, capabilities
```

Pairing required before mutating operations (unless `URISYS_NODE_SKIP_PAIRING=1` dev).

Transport is separate from URI command namespace — see **capabilities** contract for `node://` / `app://` routes used in flows (`spawn-worker`, `install-pack`, chat).
