# urisysnode


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.18-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$0.24-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-5.4h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $0.2414 (9 commits)
- 👤 **Human dev:** ~$544 (5.4h @ $100/h, 30min dedup)

Generated on 2026-06-17 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

urisys-node slave: screen/kvm/him URI server components.

Bundled: `urisysnode` only. Core deps: `uriscreen`, `urishell`. Other packs via lazy install.

Licensed under Apache-2.0.

## Ekosystem TellMesh

Orchestrator: **[urisys](https://github.com/tellmesh/urisys)** · Mapa: **[MESH.md](https://github.com/tellmesh/urisys/blob/main/docs/MESH.md)** · Model: **[ECOSYSTEM.md](https://github.com/tellmesh/urisys/blob/main/../docs/ECOSYSTEM.md)**

| Pole | Wartość |
|------|---------|
| **Warstwa** | Slave / edge node |
| **Moduł** | `urisysnode` |
| **Orchestrator** | [urisys](https://github.com/tellmesh/urisys) |
| **Runtime** | `uri_control.edge` via `uricore` |
| **Port** | 8790 |
| **Rola** | screen/shell + lazy hot-load packów (kvm, him, …) |

Runtime edge: **`uri_control.edge`** w pakiecie **`uricore`** (legacy `urisysedge` usunięty 2026-06).
Router intencji: **`urirouter`** (`uri_router`) — resolve + HTTP/MQTT delegate.

<!-- end-ecosystem -->
