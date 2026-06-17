#!/usr/bin/env bash
# GUI slave: Xvfb desktop + visible zenity target + urisys-node serve :8790
set -euo pipefail

export DISPLAY="${DISPLAY:-:99}"
export URISYS_ALLOW_REAL="${URISYS_ALLOW_REAL:-1}"
export URISYS_NODE_SKIP_PAIRING="${URISYS_NODE_SKIP_PAIRING:-1}"
export URISYS_NODE_ID="${URISYS_NODE_ID:-docker-slave}"
export URISYS_NODE_CONFIG="${URISYS_NODE_CONFIG:-/opt/urisys-node/config/node-profile.docker.json}"
export URISYS_NODE_EVENTS="${URISYS_NODE_EVENTS:-/opt/urisys-node/data/events.jsonl}"
export URISYS_NODE_DATA="${URISYS_NODE_DATA:-/opt/urisys-node/data}"
export URISYS_NODE_PACKS="${URISYS_NODE_PACKS:-node,screen,kvm,him,ocr}"

log() { echo "[urisys-node-gui] $*"; }

start_xvfb() {
  if xdpyinfo >/dev/null 2>&1; then
    log "display ${DISPLAY} already up"
    return 0
  fi
  log "starting Xvfb on ${DISPLAY}"
  Xvfb "${DISPLAY}" -screen 0 1280x720x24 -ac >/tmp/xvfb.log 2>&1 &
  echo $! >/tmp/xvfb.pid
  for _ in $(seq 1 30); do
    if xdpyinfo >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.2
  done
  log "Xvfb failed"; tail -20 /tmp/xvfb.log 2>/dev/null || true
  return 1
}

show_gui_target() {
  log "showing automation target on ${DISPLAY}"
  pkill -f "zenity --info --title=Urisys Node" 2>/dev/null || true
  zenity --info \
    --title="Urisys Node" \
    --text="Remote control ready" \
    --no-wrap \
    --width=360 \
    --height=140 \
    >/tmp/zenity.log 2>&1 &
  sleep 1
  xdotool search --name "Urisys Node" windowactivate 2>/dev/null || true
}

verify_cli() {
  log "urisys --help (smoke)"
  urisys --help >/tmp/urisys-help.txt
  log "urisys-node identity: $(urisys-node identity | head -1)"
}

mkdir -p "${URISYS_NODE_DATA}/screens" "${URISYS_NODE_DATA}"

start_xvfb
show_gui_target
verify_cli

PORT="${URISYS_NODE_PORT:-8790}"
HOST="${URISYS_NODE_HOST:-0.0.0.0}"
log "starting urisys-node serve on ${HOST}:${PORT}"
exec urisys-node serve --host "${HOST}" --port "${PORT}"
