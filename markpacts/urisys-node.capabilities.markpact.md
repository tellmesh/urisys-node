# UriContract: urisysnode node capabilities

<!-- Per-scheme projection of urisysnode/manifest.yaml; verified by tests/test_capability_contracts.py. -->

```yaml markpact:contract
apiVersion: urisys.io/v1
kind: UriContract
metadata:
  id: urisysnode.contract
  version: 0.1.21
scheme: node
queries:
- id: node.health
  pattern: node://{target}/query/health
- id: node.identity
  pattern: node://{target}/query/identity
- id: node.packs
  pattern: node://{target}/query/packs
- id: node.workers
  pattern: node://{target}/query/workers
commands:
- id: node.indicator_on
  pattern: node://{target}/command/indicator-on
  side_effects: true
  requires_approval: true
- id: node.indicator_off
  pattern: node://{target}/command/indicator-off
  side_effects: true
  requires_approval: true
- id: node.install_pack
  pattern: node://{target}/command/install-pack
  side_effects: true
  requires_approval: true
- id: node.register_forward
  pattern: node://{target}/command/register-forward
  side_effects: true
  requires_approval: true
- id: node.spawn_worker
  pattern: node://{target}/command/spawn-worker
  side_effects: true
  requires_approval: true
- id: node.restart_worker
  pattern: node://{target}/command/restart-worker
  side_effects: true
  requires_approval: true
- id: node.stop_worker
  pattern: node://{target}/command/stop-worker
  side_effects: true
  requires_approval: true
```
