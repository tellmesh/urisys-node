# Architecture — urisys-node

## Zasada

```txt
URL  = transport (http://slave:8790/uri/call)
URI  = komenda   (kvm://slave-01/task/command/click-text)
```

## Pack layout

```text
urisys-node/
  urisysnode/     runtime, CLI, pack_resolver, forward
  uriscreen       ← tellmesh/uriscreen (pip)
  urishell        ← tellmesh/urishell (pip)
```

Opcjonalne packi — lazy install z PyPI/GitHub Releases (`pack_resolver.py`).

## Pipeline kvm

```txt
screen:// → ocr:// → llm:// → him://
         ↘ kvm:// (orkiestracja)
```

## Izolacja procesowa packów (domyślnie ON)

Cienki router (`node`) trzyma tylko tablicę tras. Każdy **nie-core** pack jest
domyślnie obsługiwany w osobnym procesie-workerze, więc jego crash nie przewraca
routera ani sesji urisys-node. Granica izolacji = **pack** (nie pojedyncze
zadanie/flow; zadania tego samego packa dzielą jego proces).

Tryb wybiera `URISYS_NODE_ISOLATION` (lub `context["isolation"]`):

| Tryb | Zachowanie |
|------|-----------|
| `persistent` (domyślny) | jeden trwały worker na pack; martwy jest auto-respawnowany przez supervisor; bindingi w `data/workers.json` przeżywają restart routera |
| `ephemeral` | worker jednorazowy na **każde** wywołanie, niszczony po odpowiedzi — najsilniejsza izolacja (`PackSupervisor.call_ephemeral`) |
| `off` | legacy: pack ładowany in-process w routerze |

Core packs (`node`, `screen`, `shell`) zawsze działają in-process. Jeśli spawn
workera padnie, `call_uri` cofa się do ładowania in-process (degradacja, nie błąd).
Pre-spawn przy starcie: `URISYS_NODE_WORKER_PACKS=browser,office,kvm`.

Licensed components: see sibling repos under `tellmesh/`.
