# Pairing

```bash
urisys-node enroll --controller https://controller.local --code 482913
# lub
urisys-node enroll --controller https://controller.local --token usn_...
```

Po enroll slave zapisuje `data/node-pairing.json`:

```json
{
  "paired": true,
  "controller": "https://controller.local",
  "node_id": "slave-01",
  "capabilities": ["screen", "kvm", "him", "ocr", "llm"]
}
```

Master registry: `config/nodes.registry.json`

Dev bypass (tylko lokalnie):

```bash
export URISYS_NODE_SKIP_PAIRING=1
```
