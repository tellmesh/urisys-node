# urisys-node Refactoring Plan

## Overview

This document outlines the refactoring plan for the `urisys-node` project based on code complexity analysis.

## Analysis Summary

- **Total Lines**: 5656 lines (Python)
- **Cyclomatic Complexity**: Average CC = 5.0
- **Critical Issues**: 12 functions with CC > 15 (threshold: 15)
- **High Complexity Modules**:
  - `serve.py`: 1013 lines, CC=30
  - `remote.py`: 516 lines, CC=26  
  - `identity.py`: 209 lines, CC=27
  - `cli.py`: 196 lines, CC=22
  - `artifact_resolver.py`: 305 lines, CC=15
  - `supervisor.py`: 358 lines, CC=15
  - `forward_config.py`: 144 lines, CC=15

## Completed Refactoring

### ✅ identity.py Module

**Status**: COMPLETED

**Structure**:
```
urisysnode/identity/
├── __init__.py          # Re-exports for backward compatibility
├── core.py             # Core identity functions
│   ├── default_data_root()
│   ├── default_events_path()
│   ├── _data_dir()
│   ├── _identity_path()
│   ├── _hostname()
│   ├── load_identity()
│   └── save_identity()
├── pairing.py           # Pairing management
│   ├── _pairing_path()
│   ├── load_pairing()
│   ├── save_pairing()
│   ├── enroll()
│   ├── set_remote_control()
│   └── require_paired()
└── health.py            # Health payload (reduced CC from 27 to ~8)
    ├── _detect_him_driver()
    ├── _get_urisys_version()
    ├── _get_uricontrol_version()
    ├── _get_python_info()
    ├── _get_pairing_info()
    ├── _get_him_driver()
    ├── _get_config_source()
    ├── _get_driver_info()
    ├── _get_runtime_info()
    └── health_payload()
```

**Improvements**:
- Reduced `health_payload()` CC from 27 to ~8 by extracting helper functions
- Better separation of concerns (identity vs pairing vs health)
- Improved type hints and docstrings
- Backward compatible (all functions still importable from `urisysnode.identity`)

## Pending Refactoring

### 🔄 serve.py Module (Priority: HIGH)

**Current State**: 1013 lines, CC=30

**Proposed Structure**:
```
urisysnode/
├── serve.py              # Keep: serve(), _ReuseHTTPServer, make_handler
├── runtime/
│   ├── __init__.py
│   ├── builder.py         # build_runtime() and helpers
│   │   ├── build_runtime()       (CC=18) - Split into smaller functions
│   │   ├── _register_pack()       (CC=15)
│   │   ├── _pack_modules()
│   │   └── _extend_pack_paths()
│   ├── config.py           # Configuration resolution
│   │   ├── resolve_node_config() (CC=15)
│   │   └── _default_real_config()
│   └── packs.py            # Pack loading and management
│       ├── load_pack_into_runtime() (CC=30) - **HIGHEST PRIORITY**
│       ├── ensure_pack_for_uri()
│       ├── apply_host_trust()
│       └── _bootstrap_worker_packs()
├── handlers/
│   ├── __init__.py
│   ├── http.py            # HTTP request handlers
│   │   ├── make_handler()
│   │   ├── _app_chat_store()
│   │   ├── _app_chat_get()
│   │   └── _app_chat_post()
│   └── forward.py         # Forward pack handling
│       ├── register_forward_pack()
│       ├── _release_forward_spec()
│       └── hotload_release_pack()
└── port/
    ├── __init__.py
    ├── manager.py         # Port management
    │   ├── takeover_port()
    │   ├── _pids_on_port()
    │   ├── _kill_pid()
    │   ├── _wait_port_free()
    │   ├── _is_node_serve_process()
    │   └── _collect_takeover_targets()
    └── utils.py           # Port utilities
        ├── _pidfile_path()
        ├── _pid_alive()
        ├── _read_cmdline()
        ├── _pids_serve_cmdline()
        ├── _pids_on_port_ss()
        └── _fuser_kill_port()
```

**High CC Functions to Refactor**:
1. `load_pack_into_runtime()` - CC=30
2. `build_runtime()` - CC=18
3. `call_uri()` - CC=20
4. `resolve_node_config()` - CC=15
5. `_register_pack()` - CC=15
6. `serve()` - CC=16

### 🔄 remote.py Module (Priority: HIGH)

**Current State**: 516 lines, CC=26

**Proposed Structure**:
```
urisysnode/
├── remote.py              # Main remote operations interface
├── remote/
│   ├── __init__.py
│   ├── client.py           # Remote client functions
│   │   ├── call_uri()           (CC=20)
│   │   ├── health()
│   │   ├── wait_health()
│   │   └── pip_install()
│   ├── config.py           # Configuration defaults
│   │   ├── default_route_map()
│   │   ├── default_nodes_registry()
│   │   ├── default_endpoint()
│   │   └── default_wheel_host()
│   ├── worker.py           # Worker management
│   │   ├── spawn_worker()
│   │   ├── restart_worker()
│   │   ├── stop_worker()
│   │   └── workers()
│   ├── deploy.py           # Deployment utilities
│   │   ├── schedule_restart()
│   │   ├── _restart_scheduled()
│   │   ├── build_wheel()
│   │   ├── serve_wheels()
│   │   ├── wheel_url()
│   │   ├── upgrade_lenovo_node()
│   │   └── upgrade_lenovo_kv()
│   └── main.py            # CLI entry point
│       └── main()              (CC=26)
└── client.py             # Keep existing client functions
```

**High CC Functions to Refactor**:
1. `main()` - CC=26 (in remote.py)
2. `call_uri()` - CC=20

### 🔄 supervisor.py Module (Priority: MEDIUM)

**Current State**: 358 lines, CC=15

**Proposed Structure**:
```
urisysnode/
├── supervisor.py          # Keep main Supervisor class
├── supervisor/
│   ├── __init__.py
│   ├── process.py         # Process management
│   │   ├── spawn()
│   │   ├── restart()
│   │   ├── stop()
│   │   └── status()
│   └── utils.py           # Supervisor utilities
│       └── _reap()
```

### 🔄 artifact_resolver.py Module (Priority: MEDIUM)

**Current State**: 305 lines, CC=15

**Proposed Structure**:
```
urisysnode/
├── artifact_resolver.py   # Main interface
├── artifact/
│   ├── __init__.py
│   ├── resolver.py        # Core resolution logic
│   ├── index.py           # Index loading
│   ├── release.py         # Release management
│   └── run.py             # Runtime execution
```

### 🔄 forward_config.py Module (Priority: MEDIUM)

**Current State**: 144 lines, CC=15

**Proposed Structure**:
```
urisysnode/
├── forward_config.py      # Keep or split if grows
```

## Implementation Strategy

### Phase 1: Identity Module ✅ DONE
- Split into core/pairing/health submodules
- Reduce health_payload CC from 27 to ~8
- Backward compatible imports

### Phase 2: Serve Module (Current Focus)
1. Create `runtime/` subpackage
2. Move pack-related functions to `runtime/packs.py`
3. Move config-related functions to `runtime/config.py`
4. Move builder functions to `runtime/builder.py`
5. Create `handlers/` subpackage for HTTP handlers
6. Create `port/` subpackage for port management
7. Update serve.py to import from new modules
8. Ensure backward compatibility

### Phase 3: Remote Module
1. Create `remote/` subpackage
2. Split client, config, worker, deploy functionality
3. Reduce call_uri CC
4. Update remote.py to import from new modules

### Phase 4: Supervisor & Artifact Resolver
1. Apply similar splitting patterns
2. Reduce complexity where needed

### Phase 5: CLI Module
1. Extract command handlers to separate module
2. Reduce main() CC from 22 to <15

## Testing Strategy

After each refactoring phase:
1. Run existing tests: `make test`
2. Run integration tests: `make test-integration`
3. Run specific test files affected by changes
4. Verify backward compatibility by checking imports

## Benefits

1. **Reduced Complexity**: Each function will have CC < 15
2. **Better Maintainability**: Smaller, focused modules
3. **Improved Testability**: Easier to mock and test isolated components
4. **Clearer Architecture**: Explicit separation of concerns
5. **Easier Onboarding**: New developers can understand specific modules without reading everything

## Risks & Mitigations

1. **Import Errors**: Use backward-compatible re-exports
2. **Test Failures**: Run tests after each small change
3. **Performance**: No significant impact expected from refactoring
4. **Breaking Changes**: Maintain backward compatibility layer

## Files to Create

### identity/ subpackage ✅ DONE
- [x] `urisysnode/identity/__init__.py`
- [x] `urisysnode/identity/core.py`
- [x] `urisysnode/identity/pairing.py`
- [x] `urisysnode/identity/health.py`

### runtime/ subpackage
- [ ] `urisysnode/runtime/__init__.py`
- [ ] `urisysnode/runtime/builder.py`
- [ ] `urisysnode/runtime/config.py`
- [ ] `urisysnode/runtime/packs.py`

### handlers/ subpackage
- [ ] `urisysnode/handlers/__init__.py`
- [ ] `urisysnode/handlers/http.py`
- [ ] `urisysnode/handlers/forward.py`

### port/ subpackage
- [ ] `urisysnode/port/__init__.py`
- [ ] `urisysnode/port/manager.py`
- [ ] `urisysnode/port/utils.py`

### remote/ subpackage
- [ ] `urisysnode/remote/__init__.py`
- [ ] `urisysnode/remote/client.py`
- [ ] `urisysnode/remote/config.py`
- [ ] `urisysnode/remote/worker.py`
- [ ] `urisysnode/remote/deploy.py`

## Next Steps

1. Continue with serve.py refactoring (Phase 2)
2. Run tests after each major change
3. Update documentation as needed
4. Consider adding new tests for refactored modules
