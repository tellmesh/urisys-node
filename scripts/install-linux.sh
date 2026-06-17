#!/usr/bin/env bash
set -euo pipefail
# Install urisys-node locally (dev/MVP — not a production installer)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 -m pip install --user -e ".[real]" || python3 -m pip install --user -e .

sudo useradd -r -m -s /bin/bash urisys 2>/dev/null || true
sudo mkdir -p /etc/urisys /var/lib/urisys-node
sudo cp config/node-profile.json /etc/urisys/node-profile.json
sudo cp systemd/urisys-node.service /etc/systemd/system/urisys-node.service

echo "Next:"
echo "  urisys-node enroll --controller https://master.local --code YOUR_CODE"
echo "  sudo systemctl enable --now urisys-node"
