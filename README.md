# urisysnode


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.25-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$0.35-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-15.4h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $0.3497 (20 commits)
- 👤 **Human dev:** ~$1536 (15.4h @ $100/h, 30min dedup)

Generated on 2026-06-18 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

urisys-node slave: screen/kvm/him URI server components.

Bundled: `urisysnode` only. Core deps: `uriscreen`, `urishell`. Other packs via lazy install.

Licensed under Apache-2.0.

## Ekosystem TellMesh

Orchestrator: **[urisys](https://github.com/tellmesh/urisys)** · Mapa: **[MESH.md](https://github.com/tellmesh/urisys/blob/main/docs/MESH.md)** · Model: **[ECOSYSTEM.md](https://github.com/tellmesh/urisys/blob/main/docs/ECOSYSTEM.md)**

| Pole | Wartość |
|------|---------|
| **Warstwa** | Slave / edge node |
| **Moduł** | `urisysnode` |
| **Orchestrator** | [urisys](https://github.com/tellmesh/urisys) |
| **Runtime** | `uri_control.edge` via `uricontrol` |
| **Port** | 8790 |
| **Rola** | screen/shell + lazy hot-load packów (kvm, him, …) |

Runtime edge: **`uri_control.edge`** w pakiecie **`uricontrol`** (legacy PyPI `uricore` / `urisysedge` usunięty 2026-06).
Resolver intencji: **`uriresolver`** (`uri_resolver`) + transport w **`uritransport`**; policy gate: **`uriguard`** (`uri_guard`).

## Remote CLI (dev host → lenovo)

```bash
urisys-node remote health --endpoint http://192.168.188.201:8790
urisys-node remote restart --endpoint http://192.168.188.201:8790
urisys-node remote wait --timeout 60
```

Alias w **urisys ≥0.1.78**: `urisys remote …` (ta sama implementacja).

<!-- end-ecosystem -->
