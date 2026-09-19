# UriContract: urisysnode app capabilities

<!-- Per-scheme projection of urisysnode/manifest.yaml; verified by tests/test_capability_contracts.py. -->

```yaml markpact:contract
apiVersion: urisys.io/v1
kind: UriContract
metadata:
  id: urisysnode.app.contract
  version: 0.1.21
scheme: app
queries:
- id: app.chat.messages
  pattern: app://{target}/chat/query/messages
- id: app.chat.channels
  pattern: app://{target}/chat/query/channels
commands:
- id: app.chat.append
  pattern: app://{target}/chat/command/append
  side_effects: true
  requires_approval: true
```
