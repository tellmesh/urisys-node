#!/usr/bin/env bash
set -euo pipefail
# enable-host-trust.sh — one command to turn the current Linux user account into a
# FULL-TRUST urisys-node desktop slave: real screen capture + real shell:// + him/kvm,
# executing without per-call approval, started by the user's systemd session so it has
# the live Wayland/X11 display and input.
#
# Usage:
#   scripts/enable-host-trust.sh [--node-id NAME] [--venv PATH] [--port 8790] [--host 0.0.0.0]
#
# Re-runnable: only writes node.env / node-profile.json if absent (won't clobber edits);
# always refreshes the systemd unit and restarts the service.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

NODE_ID="$(hostname -s 2>/dev/null || hostname)"
VENV_BIN=""
PORT="8790"
BIND="0.0.0.0"
while [ $# -gt 0 ]; do
  case "$1" in
    --node-id) NODE_ID="$2"; shift 2 ;;
    --venv)    VENV_BIN="$2/bin/urisys-node"; shift 2 ;;
    --port)    PORT="$2"; shift 2 ;;
    --host)    BIND="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

# Resolve the urisys-node executable (explicit --venv wins, else PATH, else common venvs).
if [ -z "$VENV_BIN" ]; then
  VENV_BIN="$(command -v urisys-node || true)"
fi
for cand in "$HOME/venv/bin/urisys-node" "$HOME/.venv/bin/urisys-node" "$ROOT/.venv/bin/urisys-node"; do
  [ -n "$VENV_BIN" ] && break
  [ -x "$cand" ] && VENV_BIN="$cand"
done
if [ -z "$VENV_BIN" ] || [ ! -x "$VENV_BIN" ]; then
  echo "ERROR: urisys-node executable not found. Pass --venv /path/to/venv (the dir containing bin/urisys-node)." >&2
  exit 1
fi
echo "→ urisys-node: $VENV_BIN"
echo "→ node id:     $NODE_ID   (bind ${BIND}:${PORT})"

CFG="$HOME/.config/urisys"
DATA="$HOME/.local/share/urisys"
UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$CFG" "$DATA"/{screens,office,browser} "$UNIT_DIR"

# 1) behaviour env (real backends + lazy pack install). Don't clobber operator edits.
if [ ! -f "$CFG/node.env" ]; then
  cat > "$CFG/node.env" <<EOF
URISYS_ALLOW_REAL=1
URISYS_NODE_AUTO_INSTALL=1
URISYS_PACK_SOURCE=auto
URISYS_NODE_PACKS=node,screen,shell,browser,kv
URISYS_NODE_ID=$NODE_ID
URISYS_HIM_DRIVER=ydotool
EOF
  echo "→ wrote $CFG/node.env"
else
  echo "→ kept existing $CFG/node.env"
fi

# 2) full-trust profile (require_approval_for: [] → no per-call approval). Substitute node_id.
if [ ! -f "$CFG/node-profile.json" ]; then
  sed "s/\${URISYS_NODE_ID:-host}/$NODE_ID/" \
    "$ROOT/config/node-profile.full-trust.json" > "$CFG/node-profile.json"
  echo "→ wrote $CFG/node-profile.json (full-trust)"
else
  echo "→ kept existing $CFG/node-profile.json"
fi

# 3) systemd user unit, ExecStart pinned to the resolved venv + host/port.
sed -e "s#%h/venv/bin/urisys-node serve --host 0.0.0.0 --port 8790#$VENV_BIN serve --host $BIND --port $PORT#" \
    "$ROOT/systemd/urisys-node-user.service" > "$UNIT_DIR/urisys-node.service"
echo "→ installed $UNIT_DIR/urisys-node.service"

# 4) enable + survive logout, then (re)start.
systemctl --user daemon-reload
systemctl --user enable urisys-node.service >/dev/null 2>&1 || true
loginctl enable-linger "$USER" >/dev/null 2>&1 || true
systemctl --user restart urisys-node.service

sleep 2
echo "→ health:"
curl -fsS "http://127.0.0.1:${PORT}/health" || { echo "  (no response yet — check: systemctl --user status urisys-node)"; exit 1; }
echo
echo "Done. Host '$NODE_ID' now grants full rights on ${BIND}:${PORT}."
echo "Secure it beyond LAN: set URISYS_NODE_REQUIRE_SIGNATURE=1 + trusted keys in $CFG/secrets.env,"
echo "or narrow trust by adding operation globs to policy.require_approval_for in $CFG/node-profile.json."
