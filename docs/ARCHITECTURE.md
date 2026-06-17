# Architecture — urisys-node

## Zasada

```txt
URL  = transport (http://slave:8790/uri/call)
URI  = komenda   (kvm://slave-01/task/command/click-text)
```

`urisys` nie „przejmuje” hosta — wymaga **software node** albo **hardware KVM**.

## Warstwy

| Warstwa | Pakiet | Status |
|---------|--------|--------|
| Slave runtime | `urisys-node` | MVP |
| Controller routing | route-map.master.yaml | MVP |
| Identity / pairing | `urisysnode.identity` | MVP |
| Discovery mDNS | `_urisys._tcp.local` | optional (zeroconf) |
| Relay / tunnel | `urisys-relay` | planned |
| screen:// mss | `uriscreen` | MVP |

## Pipeline kvm

```txt
screen:// → ocr:// → llm:// → him://
         ↘ kvm:// (orkiestracja)
```

## Bezpieczeństwo

Mutujące URI wymagają:

- `approved: true`
- node sparowany (`enroll`)
- capability w policy
- audit w `/events`
- widoczny indicator (`node://local/command/indicator-on`)
- kill switch (hotkey — planned)
