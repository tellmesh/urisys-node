#!/usr/bin/env bash
# Build tellmesh URI packages into a local wheelhouse — registry-independent.
#
# The node resolver (pack_resolver.py) prefers this directory over GitHub and PyPI
# via `pip --find-links`, so a freshly built wheel is what gets installed/loaded.
# This sidesteps PyPI publish rate-limits entirely: build once, load anywhere.
#
# Usage:
#   bash scripts/build-wheelhouse.sh                  # default control-plane + packs
#   bash scripts/build-wheelhouse.sh urikv uribrowser # subset (dir names under tellmesh/)
#   URISYS_WHEELHOUSE=/srv/wheels bash scripts/build-wheelhouse.sh
#
# Then, on this or any node:
#   export URISYS_WHEELHOUSE=~/.urisys/wheelhouse      # (default)
#   urisys node serve ...                              # auto-installs from wheelhouse first
#   # fully offline (wheelhouse must be complete):
#   export URISYS_WHEELHOUSE_OFFLINE=1
set -euo pipefail

NODE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TELLMESH_ROOT="${TELLMESH_ROOT:-$(dirname "$NODE_ROOT")}"
WHEELHOUSE="${URISYS_WHEELHOUSE:-$HOME/.urisys/wheelhouse}"
WHEELHOUSE="${WHEELHOUSE/#\~/$HOME}"

# Control-plane first (uricontrol provides uri_control), then capability packs.
DEFAULT_PKGS=(
  uricontrol uriguard uriresolver urisys urisys-node
  urishell uriscreen urikvm urihim uriocr urillm urioffice urimail
  urivql uriimg2nl uribrowser urikv uristt uriwebrtc urimessage urichat
  urirdp urirdpedge urienv
)
PKGS=("${@:-${DEFAULT_PKGS[@]}}")

mkdir -p "$WHEELHOUSE"
python3 -m pip install -q build 2>/dev/null || python3 -m pip install --user -q build

built=0 skipped=0 failed=0
for pkg in "${PKGS[@]}"; do
  dir="$TELLMESH_ROOT/$pkg"
  if [ ! -f "$dir/pyproject.toml" ]; then
    echo "skip $pkg: no pyproject.toml at $dir" >&2
    skipped=$((skipped + 1))
    continue
  fi
  echo "build $pkg → $WHEELHOUSE"
  if python3 -m build -w -o "$WHEELHOUSE" "$dir" >/tmp/build-"$pkg".log 2>&1; then
    built=$((built + 1))
  else
    echo "FAIL $pkg (see /tmp/build-$pkg.log)" >&2
    failed=$((failed + 1))
  fi
done

echo "wheelhouse: $WHEELHOUSE"
ls -1 "$WHEELHOUSE"/*.whl 2>/dev/null | sed 's#.*/#  - #' || true
echo "built=$built skipped=$skipped failed=$failed"
[ "$failed" -eq 0 ]
