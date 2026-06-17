# screen:// backends

Kontrakt:

```txt
screen://{node}/monitor/{monitor}/query/frame
screen://{node}/monitor/{monitor}/command/capture
screen://{node}/capture/command/loop
```

## Implementacje

| Backend | Platform | Paczka |
|---------|----------|--------|
| `mss` | Linux/Win/macOS | `uriscreen-mss-python` (default) |
| `mock` | all | dry-run/tests |
| `pyscreenshot` | fallback | planned |
| `sharex` | Windows | planned |

## Przykład

```bash
urisys-node call screen://local/monitor/1/command/capture \
  --payload '{"backend":"mss","output":"./screens"}' \
  --approve --allow-real
```

W `kvm://` pipeline:

```yaml
do:
  - screen://local/monitor/primary/command/capture
  - ocr://local/image/latest/query/text
  - llm://local/vision/query/analyze
```
