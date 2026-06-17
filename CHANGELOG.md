# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

