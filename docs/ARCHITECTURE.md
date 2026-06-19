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

## Źródła paczek (registry-independent, build-first)

Rozwiązanie problemu „nie da się publikować na PyPI" (limity uploadu) i thrashingu
`pip install -U urisys`. Resolver ([pack_resolver.py](../urisysnode/pack_resolver.py))
wybiera źródło w kolejności **lokalny wheelhouse → GitHub Releases → PyPI**:

1. **Lokalny wheelhouse** — zbuduj raz, ładuj wszędzie bez żadnego registry:
   ```bash
   bash scripts/build-wheelhouse.sh            # → ~/.urisys/wheelhouse
   export URISYS_WHEELHOUSE=~/.urisys/wheelhouse
   ```
   Każdy `pip install` dostaje wtedy `--find-links <wheelhouse>`, więc świeżo
   zbudowane koło wygrywa i pip **nie enumeruje wersji z PyPI** (to właśnie zabija
   wielominutowy backtracking). `URISYS_WHEELHOUSE_OFFLINE=1` dodaje `--no-index`
   (pełny offline — wheelhouse musi być kompletny).
2. **GitHub Releases** — wersja **najnowsza** pobierana dynamicznie z API
   (`github_latest_version`), z fallbackiem do przypiętej `PACK_GITHUB_VERSION`.
   `URISYS_GITHUB_TOKEN`/`GH_TOKEN` podnosi limit API; `URISYS_OFFLINE=1` lub
   `URISYS_PACK_GITHUB_DYNAMIC=0` wyłącza zapytania sieciowe.
3. **PyPI** — tylko ostateczność.

Wymuszenie kanału: `URISYS_PACK_SOURCE=local|github|pypi` (domyślnie `auto`).
`urisys init` honoruje ten sam wheelhouse ([init_setup.py](../../urisys/src/urisys/init_setup.py)).

> Uwaga do błędu z logów: `pip install -U urisys` (czysty PyPI) nie ciągnie
> `urisys-node` → `ModuleNotFoundError: urisysnode`. Używaj `urisys init` albo
> wheelhouse, nie gołego instalu z PyPI.

Licensed components: see sibling repos under `tellmesh/`.
