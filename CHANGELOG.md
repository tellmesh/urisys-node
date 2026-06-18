# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.35] - 2026-06-18

### Docs
- Update README.md

### Test
- Update tests/test_invalid_profile_tolerated.py

### Other
- Update data/events.jsonl
- Update urisysnode/serve.py
- Update uv.lock

## [0.1.34] - 2026-06-18

### Docs
- Update README.md

### Other
- Update data/events.jsonl
- Update uv.lock

## [0.1.31] - 2026-06-18

### Docs
- Update README.md

### Other
- Update config/node-profile.lenovo.json
- Update data/events.jsonl
- Update urisysnode/serve.py
- Update uv.lock

## [0.1.30] - 2026-06-18

### Docs
- Update README.md

### Other
- Update data/events.jsonl
- Update uv.lock

## [0.1.29] - 2026-06-18

### Docs
- Update README.md

### Other
- Update data/events.jsonl
- Update uv.lock

## [0.1.28] - 2026-06-18

### Docs
- Update README.md

### Other
- Update data/events.jsonl
- Update uv.lock

## [0.1.28] - 2026-06-18

### Docs
- Update README.md

### Other
- Update data/events.jsonl
- Update uv.lock

## [0.1.27] - 2026-06-18

### Docs
- Update README.md

### Other
- Update data/events.jsonl
- Update uv.lock

## [0.1.26] - 2026-06-18

### Docs
- Update README.md

### Test
- Update tests/test_remote_restart.py

### Other
- Update data/events.jsonl
- Update urisysnode/remote.py

## [0.1.25] - 2026-06-18

### Docs
- Update README.md

### Other
- Update data/events.jsonl
- Update uv.lock

## [0.1.24] - 2026-06-18

### Docs
- Update CHANGELOG.md
- Update README.md
- Update markpacts/urisys-node.capabilities.markpact.md
- Update markpacts/urisys-node.contract.markpact.md
- Update markpacts/urisysnode-app.markpact.md
- Update markpacts/urisysnode-node.markpact.md

### Test
- Update tests/integration/test_core_pack_boot_install.py
- Update tests/integration/test_host_trust.py
- Update tests/integration/test_uriscreen_auto.py
- Update tests/integration/test_urishell.py
- Update tests/test_remote_restart.py
- Update tests/test_supervisor_worker_env.py
- Update tests/test_worker_router_callback.py

### Other
- Update VERSION
- Update data/events.jsonl
- Update docker/Dockerfile.gui
- Update urisysnode/handlers.py
- Update urisysnode/identity.py
- Update urisysnode/manifest.yaml
- Update urisysnode/pack_resolver.py
- Update urisysnode/remote.py
- Update urisysnode/serve.py
- Update urisysnode/supervisor.py
- ... and 2 more files

## [0.1.23] - 2026-06-18

### Fixed
- `remote restart` — `--endpoint` / `--route-map` / `--port`; connection drop po `fuser -k` = sukces

### Docs
- Update CHANGELOG.md
- Update README.md

### Test
- Update tests/integration/test_pack_github.py
- Update tests/integration/test_pack_webrtc_hotload.py
- Update tests/test_pack_resolver_webrtc.py

### Other
- Update VERSION
- Update data/events.jsonl
- Update urisysnode/pack_resolver.py
- Update uv.lock

## [0.1.16] - 2026-06-17

### Added
- `urisys-node remote upgrade-node` — build wheel, pip install on lenovo, restart, verify `/app/chat/*`

### Changed
- `schedule_restart` — `fuser -k` port before detached `urisys node serve` (takeover when SSH unavailable)

## [0.1.15] - 2026-06-17

### Added
- **App chat API** for ifURI — `GET/POST /app/chat/messages`, `GET /app/chat/channels`
- URI routes: `app://{target}/chat/query/messages`, `query/channels`, `command/append`
- Storage: `~/.local/share/urisys/app-chat.jsonl` (`URISYS_NODE_APP_CHAT`)
- Tests: `tests/test_app_data.py`

## [0.1.14] - 2026-06-17

### Docs
- Update README.md

### Other
- Update data/events.jsonl
- Update uv.lock

## [0.1.13] - 2026-06-17

### Docs
- Update README.md

### Other
- Update config/node-profile.lenovo.json
- Update data/events.jsonl
- Update systemd/urisys-node-user.service
- Update systemd/urisys-node.service
- Update urisysnode/pack_resolver.py
- Update uv.lock

## [0.1.12] - 2026-06-17

### Docs
- Update CHANGELOG.md
- Update README.md

### Test
- Update tests/integration/test_serve_takeover.py

### Other
- Update VERSION
- Update config/node-profile.lenovo.json
- Update config/route-map.lenovo.yaml
- Update data/events.jsonl
- Update urisysnode/identity.py
- Update urisysnode/pack_resolver.py
- Update urisysnode/remote.py
- Update urisysnode/serve.py
- Update urisysnode/supervisor.py
- Update uv.lock

## [0.1.10] - 2026-06-17

### Fixed
- **`urisys node serve` port takeover** — kill only listeners on the port and confirmed node processes (pidfile); no longer kills bash/nohup wrappers or the parent shell; `killpg` for detached `setsid` serve; safe restart on re-run.

## [0.1.9] - 2026-06-17

### Docs
- Update README.md

### Test
- Update tests/integration/_fakepack.py
- Update tests/integration/test_serve_takeover.py
- Update tests/integration/test_worker_supervisor.py

### Other
- Update VERSION
- Update config/node.env.example
- Update data/events.jsonl
- Update data/workers.json
- Update urisysnode/cli.py
- Update urisysnode/handlers.py
- Update urisysnode/remote.py
- Update urisysnode/routes.py
- Update urisysnode/serve.py
- Update urisysnode/supervisor.py
- ... and 2 more files

## [0.1.7] - 2026-06-17

### Docs
- Update README.md

### Test
- Update tests/integration/test_urisys_node.py

### Other
- Update config/node.env.example
- Update config/route-map.lenovo.yaml
- Update data/events.jsonl
- Update systemd/urisys-node-user.service
- Update urisysnode/client.py
- Update urisysnode/router.py
- Update urisysnode/serve.py
- Update uv.lock

## [0.1.6] - 2026-06-17

### Docs
- Update README.md

### Test
- Update tests/integration/test_pack_auto_install.py

### Other
- Update VERSION
- Update data/events.jsonl
- Update urisysnode/cli.py
- Update urisysnode/identity.py
- Update urisysnode/serve.py
- Update uv.lock

