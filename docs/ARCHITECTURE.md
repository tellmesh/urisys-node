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

Licensed components: see sibling repos under `tellmesh/`.
