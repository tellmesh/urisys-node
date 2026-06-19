# urisysnode

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Dependencies](#dependencies)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `urisys-node`
- **version**: `0.1.40`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Makefile, testql(2), app.doql.less, goal.yaml, .env.example, docker-compose.gui.yml, project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: urisys-node;
  version: 0.1.40;
}

dependencies {
  runtime: "pyyaml>=6.0, uricontrol>=0.1.8, pygments>=2.20.0";
  boot: "uriscreen>=0.1.0, urishell>=0.1.0";
  real: "mss>=9.0, Pillow>=10.0, pyautogui>=0.9.54, pytesseract>=0.3.10, litellm>=1.40";
  kvm: "urikvm[real]>=0.1.0, urihim[real]>=0.1.0, uriocr[real]>=0.1.0, urillm[vision]>=0.1.0";
  discovery: zeroconf>=0.131.0;
  dev: "pytest>=8.0, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60, uristt, uriwebrtc, uriscreen, urishell";
}

interface[type="cli"] {
  framework: argparse;
}
interface[type="cli"] page[name="urisys-node"] {
  entry: urisysnode.cli:main;
}

workflow[name="install"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pip install -e .;
}

workflow[name="test"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pytest -q;
}

workflow[name="test-all"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pytest -v;
}

workflow[name="test-integration"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pytest tests/integration/ -v;
}

workflow[name="test-coverage"] {
  trigger: manual;
  step-1: run cmd=.venv/bin/pip install -q pytest-cov > /dev/null 2>&1 || true;
  step-2: run cmd=$(PYTHON) -m pytest --cov=urisysnode --cov-report=term-missing -v;
}

workflow[name="test-watch"] {
  trigger: manual;
  step-1: run cmd=.venv/bin/pip install -q pytest-watch > /dev/null 2>&1 || true;
  step-2: run cmd=$(PYTHON) -m ptw tests/ --pattern "test_*.py" --ignore "tests/integration/";
}

workflow[name="serve"] {
  trigger: manual;
  step-1: run cmd=URISYS_NODE_SKIP_PAIRING=1 urisys-node serve --host 0.0.0.0 --port $(PORT);
}

workflow[name="health"] {
  trigger: manual;
  step-1: run cmd=curl -fsS "http://127.0.0.1:$(PORT)/health" | $(PYTHON) -m json.tool | head -15;
}

workflow[name="app-chat-smoke"] {
  trigger: manual;
  step-1: run cmd=curl -fsS -X POST "http://127.0.0.1:$(PORT)/app/chat/messages" \;
  step-2: run cmd=-H 'Content-Type: application/json' \;
  step-3: run cmd=-d '{"channel_id":"smoke","role":"user","text":"ping"}' | $(PYTHON) -m json.tool;
  step-4: run cmd=curl -fsS "http://127.0.0.1:$(PORT)/app/chat/messages?channel_id=smoke" | $(PYTHON) -m json.tool;
}

workflow[name="publish"] {
  trigger: manual;
  step-1: run cmd=echo "📦 Publishing to PyPI...";
  step-2: run cmd=command -v .venv/bin/twine > /dev/null 2>&1 || (.venv/bin/pip install --upgrade twine build);
  step-3: run cmd=rm -rf dist/ build/ *.egg-info/;
  step-4: run cmd=.venv/bin/python -m build;
  step-5: run cmd=.venv/bin/twine check dist/*;
  step-6: run cmd=echo "🚀 Uploading to PyPI...";
  step-7: run cmd=.venv/bin/twine upload dist/*;
}

workflow[name="publish-test"] {
  trigger: manual;
  step-1: run cmd=echo "📦 Publishing to TestPyPI...";
  step-2: run cmd=command -v .venv/bin/twine > /dev/null 2>&1 || (.venv/bin/pip install --upgrade twine build);
  step-3: run cmd=rm -rf dist/ build/ *.egg-info/;
  step-4: run cmd=.venv/bin/python -m build;
  step-5: run cmd=.venv/bin/twine upload --repository testpypi dist/*;
}

workflow[name="version"] {
  trigger: manual;
  step-1: run cmd=echo "📦 Version information...";
  step-2: run cmd=cat VERSION;
  step-3: run cmd=.venv/bin/python -c "from importlib.metadata import version; print(f'Installed version: {version(\"sumd\")}')";
}

tests {
  import: testql-scenarios/**/*.testql.toon.yaml;
}

env_vars {
  keys: OPENROUTER_API_KEY, LLM_MODEL, PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_MAX_RETRIES, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_CREATE_BACKUPS;
}

deploy {
  target: docker;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  template_file: .env.example;
  python_version: >=3.10;
  vars: LLM_MODEL, OPENROUTER_API_KEY, PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_CREATE_BACKUPS, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_MAX_RETRIES;
  runtime_llm: OPENROUTER_API_KEY;
  runtime_pfix: PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_CREATE_BACKUPS, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_MAX_RETRIES;
}
```

## Workflows

## Dependencies

### Runtime

```text markpact:deps python
pyyaml>=6.0
uricontrol>=0.1.8
pygments>=2.20.0
```

### Development

```text markpact:deps python scope=dev
pytest>=8.0
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
uristt
uriwebrtc
uriscreen
urishell
```

## Call Graph

*170 nodes · 202 edges · 22 modules · CC̄=5.1*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `make_handler` *(in urisysnode.serve)* | 2 | 3 | 88 | **91** |
| `serve` *(in urisysnode.serve)* | 16 ⚠ | 1 | 43 | **44** |
| `build_runtime` *(in urisysnode.serve)* | 18 ⚠ | 2 | 37 | **39** |
| `build_runtime` *(in urisysnode.runtime.builder)* | 18 ⚠ | 0 | 37 | **37** |
| `load_pack_into_runtime` *(in urisysnode.serve)* | 30 ⚠ | 4 | 31 | **35** |
| `load_pack_into_runtime` *(in urisysnode.runtime.packs)* | 30 ⚠ | 1 | 31 | **32** |
| `call_uri` *(in urisysnode.serve)* | 20 ⚠ | 1 | 30 | **31** |
| `upgrade_lenovo_node` *(in urisysnode.remote)* | 7 | 1 | 23 | **24** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/tellmesh/urisys-node
# generated in 0.07s
# nodes: 170 | edges: 202 | modules: 22
# CC̄=5.1

HUBS[20]:
  urisysnode.serve.make_handler
    CC=2  in:3  out:88  total:91
  urisysnode.serve.serve
    CC=16  in:1  out:43  total:44
  urisysnode.serve.build_runtime
    CC=18  in:2  out:37  total:39
  urisysnode.runtime.builder.build_runtime
    CC=18  in:0  out:37  total:37
  urisysnode.serve.load_pack_into_runtime
    CC=30  in:4  out:31  total:35
  urisysnode.runtime.packs.load_pack_into_runtime
    CC=30  in:1  out:31  total:32
  urisysnode.serve.call_uri
    CC=20  in:1  out:30  total:31
  urisysnode.remote.upgrade_lenovo_node
    CC=7  in:1  out:23  total:24
  urisysnode.serve.resolve_node_config
    CC=7  in:3  out:20  total:23
  urisysnode.forward_config.load_forward_entries
    CC=15  in:2  out:20  total:22
  urisysnode.identity.core.load_identity
    CC=4  in:6  out:15  total:21
  urisysnode.supervisor.PackSupervisor.spawn
    CC=15  in:0  out:21  total:21
  urisysnode.handlers.command_spawn_worker
    CC=11  in:0  out:21  total:21
  urisysnode.artifact_resolver.run_release
    CC=8  in:2  out:19  total:21
  urisysnode.remote.upgrade_lenovo_kv
    CC=4  in:1  out:19  total:20
  urisysnode.serve.hotload_release_pack
    CC=14  in:2  out:17  total:19
  urisysnode.serve._register_pack
    CC=14  in:3  out:16  total:19
  urisysnode.port.manager._pids_on_port
    CC=16  in:1  out:17  total:18
  urisysnode.display_bootstrap.bootstrap_wayland_capture
    CC=7  in:1  out:17  total:18
  urisysnode.artifact_resolver.select_artifact
    CC=15  in:3  out:14  total:17

MODULES:
  urisysnode.app_data  [2 funcs]
    __init__  CC=2  out:3
    default_app_chat_path  CC=2  out:4
  urisysnode.app_handlers  [4 funcs]
    _store  CC=4  out:3
    command_chat_append  CC=9  out:15
    query_chat_channels  CC=2  out:5
    query_chat_messages  CC=5  out:9
  urisysnode.artifact_resolver  [19 funcs]
    _auth_opener  CC=4  out:11
    _contract_yaml_block  CC=6  out:6
    contract_spec_from_release  CC=2  out:4
    contract_url_from_release  CC=6  out:8
    docker_pull  CC=4  out:4
    docker_run_worker  CC=3  out:4
    fetch_json  CC=1  out:6
    fetch_release  CC=5  out:11
    fetch_text  CC=1  out:5
    is_url  CC=1  out:1
  urisysnode.client  [2 funcs]
    call_via_route_map  CC=6  out:14
    remote_call  CC=3  out:8
  urisysnode.display_bootstrap  [7 funcs]
    _agent_up  CC=2  out:2
    _agent_url  CC=1  out:2
    _ensure_session_env  CC=5  out:7
    _screencast_ready  CC=4  out:9
    _start_agent  CC=4  out:9
    _start_screencast  CC=5  out:7
    bootstrap_wayland_capture  CC=7  out:17
  urisysnode.forward  [1 funcs]
    forward_call  CC=9  out:8
  urisysnode.forward_config  [6 funcs]
    _normalize_entry  CC=11  out:13
    _normalize_release_entry  CC=11  out:15
    load_forward_entries  CC=15  out:20
    load_release_forward_entries  CC=11  out:12
    wire_forward_packs  CC=2  out:2
    wire_release_forward_packs  CC=3  out:4
  urisysnode.handlers  [12 funcs]
    _get_supervisor  CC=3  out:4
    command_indicator_off  CC=1  out:2
    command_indicator_on  CC=1  out:4
    command_install_pack  CC=6  out:13
    command_register_forward  CC=7  out:12
    command_restart_worker  CC=6  out:7
    command_spawn_worker  CC=11  out:21
    command_stop_worker  CC=6  out:7
    query_health  CC=1  out:2
    query_identity  CC=2  out:8
  urisysnode.identity.core  [7 funcs]
    _data_dir  CC=1  out:2
    _hostname  CC=1  out:1
    _identity_path  CC=1  out:1
    default_data_root  CC=3  out:5
    default_events_path  CC=2  out:3
    load_identity  CC=4  out:15
    save_identity  CC=1  out:3
  urisysnode.identity.health  [10 funcs]
    _detect_him_driver  CC=3  out:4
    _get_config_source  CC=6  out:2
    _get_driver_info  CC=7  out:7
    _get_him_driver  CC=6  out:5
    _get_pairing_info  CC=1  out:6
    _get_python_info  CC=1  out:0
    _get_runtime_info  CC=7  out:11
    _get_uricontrol_version  CC=2  out:1
    _get_urisys_version  CC=2  out:1
    health_payload  CC=4  out:12
  urisysnode.identity.pairing  [6 funcs]
    _pairing_path  CC=1  out:1
    enroll  CC=3  out:4
    load_pairing  CC=3  out:5
    require_paired  CC=4  out:5
    save_pairing  CC=1  out:3
    set_remote_control  CC=2  out:2
  urisysnode.pack_resolver  [17 funcs]
    _pip_install  CC=4  out:4
    auto_install_enabled  CC=1  out:1
    ensure_boot_pack  CC=7  out:8
    ensure_pack_pypi  CC=3  out:3
    ensure_pip_specs  CC=4  out:2
    ensure_real_deps  CC=1  out:2
    github_owner  CC=1  out:2
    github_wheel_url  CC=4  out:7
    github_wheel_urls  CC=6  out:4
    import_pack_module  CC=1  out:2
  urisysnode.port.manager  [7 funcs]
    _collect_takeover_targets  CC=12  out:15
    _is_node_serve_process  CC=16  out:11
    _kill_pid  CC=9  out:13
    _pids_on_port  CC=16  out:17
    _wait_port_free  CC=4  out:8
    _worker_pids_from_state  CC=10  out:12
    takeover_port  CC=6  out:12
  urisysnode.port.utils  [6 funcs]
    _fuser_kill_port  CC=4  out:3
    _pid_alive  CC=2  out:1
    _pidfile_path  CC=1  out:2
    _pids_on_port_ss  CC=5  out:5
    _pids_serve_cmdline  CC=7  out:8
    _read_cmdline  CC=2  out:5
  urisysnode.release_verify  [4 funcs]
    _ed25519_verify  CC=3  out:5
    canonical_digest  CC=3  out:5
    signature_required  CC=3  out:2
    verify_release  CC=14  out:15
  urisysnode.remote  [19 funcs]
    build_wheel  CC=3  out:11
    call_uri  CC=4  out:4
    default_endpoint  CC=1  out:2
    default_nodes_registry  CC=1  out:4
    default_route_map  CC=1  out:4
    default_wheel_host  CC=1  out:2
    health  CC=2  out:5
    install_pack  CC=2  out:1
    pip_install  CC=1  out:1
    restart_worker  CC=1  out:1
  urisysnode.router  [5 funcs]
    _match_pattern  CC=1  out:4
    load_route_map  CC=3  out:4
    node_endpoint  CC=5  out:6
    resolve_remote_route  CC=5  out:3
    rewrite_uri_for_slave  CC=8  out:5
  urisysnode.runtime.builder  [3 funcs]
    _extend_pack_paths  CC=1  out:0
    _register_pack  CC=14  out:16
    build_runtime  CC=18  out:37
  urisysnode.runtime.packs  [2 funcs]
    ensure_pack_for_uri  CC=3  out:6
    load_pack_into_runtime  CC=30  out:31
  urisysnode.serve  [16 funcs]
    _app_chat_get  CC=10  out:14
    _app_chat_post  CC=9  out:15
    _app_chat_store  CC=2  out:2
    _extend_pack_paths  CC=1  out:0
    _register_pack  CC=14  out:16
    _release_forward_spec  CC=11  out:8
    apply_host_trust  CC=10  out:8
    build_runtime  CC=18  out:37
    call_uri  CC=20  out:30
    ensure_pack_for_uri  CC=3  out:6
  urisysnode.supervisor  [9 funcs]
    _fetch_patterns  CC=3  out:3
    _needs_install  CC=3  out:1
    _wait_health  CC=5  out:5
    _wire  CC=2  out:5
    spawn  CC=15  out:21
    alive  CC=3  out:2
    _free_port  CC=1  out:3
    _http_get  CC=1  out:4
    _schemes_of  CC=4  out:3
  urisysnode.worker  [6 funcs]
    _load_node_profile  CC=5  out:5
    _local_schemes  CC=4  out:4
    _wire_router_callback  CC=3  out:7
    build_worker_runtime  CC=5  out:13
    main  CC=4  out:13
    serve_worker  CC=5  out:11

EDGES:
  urisysnode.release_verify.verify_release → urisysnode.release_verify.signature_required
  urisysnode.release_verify.verify_release → urisysnode.release_verify.canonical_digest
  urisysnode.release_verify.verify_release → urisysnode.release_verify._ed25519_verify
  urisysnode.forward_config.load_forward_entries → urisysnode.forward_config._normalize_entry
  urisysnode.forward_config.wire_forward_packs → urisysnode.serve.register_forward_pack
  urisysnode.forward_config.load_release_forward_entries → urisysnode.forward_config._normalize_release_entry
  urisysnode.forward_config.wire_release_forward_packs → urisysnode.serve.hotload_release_pack
  urisysnode.supervisor.Worker.alive → urisysnode.supervisor._http_get
  urisysnode.supervisor.PackSupervisor.spawn → urisysnode.supervisor._free_port
  urisysnode.supervisor.PackSupervisor._needs_install → urisysnode.pack_resolver.pack_importable
  urisysnode.supervisor.PackSupervisor._wait_health → urisysnode.supervisor._http_get
  urisysnode.supervisor.PackSupervisor._fetch_patterns → urisysnode.supervisor._http_get
  urisysnode.supervisor.PackSupervisor._wire → urisysnode.serve.register_forward_pack
  urisysnode.supervisor.PackSupervisor._wire → urisysnode.supervisor._schemes_of
  urisysnode.client.call_via_route_map → urisysnode.router.load_route_map
  urisysnode.client.call_via_route_map → urisysnode.router.resolve_remote_route
  urisysnode.client.call_via_route_map → urisysnode.router.node_endpoint
  urisysnode.client.call_via_route_map → urisysnode.router.rewrite_uri_for_slave
  urisysnode.client.call_via_route_map → urisysnode.client.remote_call
  urisysnode.forward.forward_call → urisysnode.client.remote_call
  urisysnode.remote.health → urisysnode.remote.default_endpoint
  urisysnode.remote.wait_health → urisysnode.remote.default_endpoint
  urisysnode.remote.wait_health → urisysnode.remote.health
  urisysnode.remote.call_uri → urisysnode.client.call_via_route_map
  urisysnode.remote.call_uri → urisysnode.client.remote_call
  urisysnode.remote.call_uri → urisysnode.remote.default_route_map
  urisysnode.remote.call_uri → urisysnode.remote.default_nodes_registry
  urisysnode.remote.pip_install → urisysnode.remote.call_uri
  urisysnode.remote.install_pack → urisysnode.remote.call_uri
  urisysnode.remote.spawn_worker → urisysnode.remote.call_uri
  urisysnode.remote.restart_worker → urisysnode.remote.call_uri
  urisysnode.remote.stop_worker → urisysnode.remote.call_uri
  urisysnode.remote.workers → urisysnode.remote.call_uri
  urisysnode.remote.schedule_restart → urisysnode.remote.call_uri
  urisysnode.remote.wheel_url → urisysnode.remote.default_wheel_host
  urisysnode.remote.upgrade_lenovo_node → urisysnode.remote.build_wheel
  urisysnode.remote.upgrade_lenovo_node → urisysnode.remote.serve_wheels
  urisysnode.remote.upgrade_lenovo_node → urisysnode.remote.default_wheel_host
  urisysnode.remote.upgrade_lenovo_node → urisysnode.remote.default_endpoint
  urisysnode.remote.upgrade_lenovo_node → urisysnode.remote.health
  urisysnode.remote.upgrade_lenovo_node → urisysnode.remote.pip_install
  urisysnode.remote.upgrade_lenovo_node → urisysnode.remote.schedule_restart
  urisysnode.remote.upgrade_lenovo_kv → urisysnode.remote.build_wheel
  urisysnode.remote.upgrade_lenovo_kv → urisysnode.remote.serve_wheels
  urisysnode.remote.upgrade_lenovo_kv → urisysnode.remote.default_wheel_host
  urisysnode.remote.upgrade_lenovo_kv → urisysnode.remote.health
  urisysnode.remote.upgrade_lenovo_kv → urisysnode.remote.pip_install
  urisysnode.remote.upgrade_lenovo_kv → urisysnode.remote.schedule_restart
  urisysnode.handlers.query_health → urisysnode.identity.health.health_payload
  urisysnode.handlers.query_identity → urisysnode.identity.core.load_identity
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

### Integration (1)

**`Auto-generated from Python Tests`**
- assert `calls == [("http://127.0.0.1:8790"`
- assert `calls == [("urihim.contract"`
- assert `url == "https://github.com/tellmesh/urihim/releases/download/v0.1.3/urihim-0.1.3-py3-none-any.whl"`

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/tellmesh/urisys-node
# generated in 0.07s
# nodes: 170 | edges: 202 | modules: 22
# CC̄=5.1

HUBS[20]:
  urisysnode.serve.make_handler
    CC=2  in:3  out:88  total:91
  urisysnode.serve.serve
    CC=16  in:1  out:43  total:44
  urisysnode.serve.build_runtime
    CC=18  in:2  out:37  total:39
  urisysnode.runtime.builder.build_runtime
    CC=18  in:0  out:37  total:37
  urisysnode.serve.load_pack_into_runtime
    CC=30  in:4  out:31  total:35
  urisysnode.runtime.packs.load_pack_into_runtime
    CC=30  in:1  out:31  total:32
  urisysnode.serve.call_uri
    CC=20  in:1  out:30  total:31
  urisysnode.remote.upgrade_lenovo_node
    CC=7  in:1  out:23  total:24
  urisysnode.serve.resolve_node_config
    CC=7  in:3  out:20  total:23
  urisysnode.forward_config.load_forward_entries
    CC=15  in:2  out:20  total:22
  urisysnode.identity.core.load_identity
    CC=4  in:6  out:15  total:21
  urisysnode.supervisor.PackSupervisor.spawn
    CC=15  in:0  out:21  total:21
  urisysnode.handlers.command_spawn_worker
    CC=11  in:0  out:21  total:21
  urisysnode.artifact_resolver.run_release
    CC=8  in:2  out:19  total:21
  urisysnode.remote.upgrade_lenovo_kv
    CC=4  in:1  out:19  total:20
  urisysnode.serve.hotload_release_pack
    CC=14  in:2  out:17  total:19
  urisysnode.serve._register_pack
    CC=14  in:3  out:16  total:19
  urisysnode.port.manager._pids_on_port
    CC=16  in:1  out:17  total:18
  urisysnode.display_bootstrap.bootstrap_wayland_capture
    CC=7  in:1  out:17  total:18
  urisysnode.artifact_resolver.select_artifact
    CC=15  in:3  out:14  total:17

MODULES:
  urisysnode.app_data  [2 funcs]
    __init__  CC=2  out:3
    default_app_chat_path  CC=2  out:4
  urisysnode.app_handlers  [4 funcs]
    _store  CC=4  out:3
    command_chat_append  CC=9  out:15
    query_chat_channels  CC=2  out:5
    query_chat_messages  CC=5  out:9
  urisysnode.artifact_resolver  [19 funcs]
    _auth_opener  CC=4  out:11
    _contract_yaml_block  CC=6  out:6
    contract_spec_from_release  CC=2  out:4
    contract_url_from_release  CC=6  out:8
    docker_pull  CC=4  out:4
    docker_run_worker  CC=3  out:4
    fetch_json  CC=1  out:6
    fetch_release  CC=5  out:11
    fetch_text  CC=1  out:5
    is_url  CC=1  out:1
  urisysnode.client  [2 funcs]
    call_via_route_map  CC=6  out:14
    remote_call  CC=3  out:8
  urisysnode.display_bootstrap  [7 funcs]
    _agent_up  CC=2  out:2
    _agent_url  CC=1  out:2
    _ensure_session_env  CC=5  out:7
    _screencast_ready  CC=4  out:9
    _start_agent  CC=4  out:9
    _start_screencast  CC=5  out:7
    bootstrap_wayland_capture  CC=7  out:17
  urisysnode.forward  [1 funcs]
    forward_call  CC=9  out:8
  urisysnode.forward_config  [6 funcs]
    _normalize_entry  CC=11  out:13
    _normalize_release_entry  CC=11  out:15
    load_forward_entries  CC=15  out:20
    load_release_forward_entries  CC=11  out:12
    wire_forward_packs  CC=2  out:2
    wire_release_forward_packs  CC=3  out:4
  urisysnode.handlers  [12 funcs]
    _get_supervisor  CC=3  out:4
    command_indicator_off  CC=1  out:2
    command_indicator_on  CC=1  out:4
    command_install_pack  CC=6  out:13
    command_register_forward  CC=7  out:12
    command_restart_worker  CC=6  out:7
    command_spawn_worker  CC=11  out:21
    command_stop_worker  CC=6  out:7
    query_health  CC=1  out:2
    query_identity  CC=2  out:8
  urisysnode.identity.core  [7 funcs]
    _data_dir  CC=1  out:2
    _hostname  CC=1  out:1
    _identity_path  CC=1  out:1
    default_data_root  CC=3  out:5
    default_events_path  CC=2  out:3
    load_identity  CC=4  out:15
    save_identity  CC=1  out:3
  urisysnode.identity.health  [10 funcs]
    _detect_him_driver  CC=3  out:4
    _get_config_source  CC=6  out:2
    _get_driver_info  CC=7  out:7
    _get_him_driver  CC=6  out:5
    _get_pairing_info  CC=1  out:6
    _get_python_info  CC=1  out:0
    _get_runtime_info  CC=7  out:11
    _get_uricontrol_version  CC=2  out:1
    _get_urisys_version  CC=2  out:1
    health_payload  CC=4  out:12
  urisysnode.identity.pairing  [6 funcs]
    _pairing_path  CC=1  out:1
    enroll  CC=3  out:4
    load_pairing  CC=3  out:5
    require_paired  CC=4  out:5
    save_pairing  CC=1  out:3
    set_remote_control  CC=2  out:2
  urisysnode.pack_resolver  [17 funcs]
    _pip_install  CC=4  out:4
    auto_install_enabled  CC=1  out:1
    ensure_boot_pack  CC=7  out:8
    ensure_pack_pypi  CC=3  out:3
    ensure_pip_specs  CC=4  out:2
    ensure_real_deps  CC=1  out:2
    github_owner  CC=1  out:2
    github_wheel_url  CC=4  out:7
    github_wheel_urls  CC=6  out:4
    import_pack_module  CC=1  out:2
  urisysnode.port.manager  [7 funcs]
    _collect_takeover_targets  CC=12  out:15
    _is_node_serve_process  CC=16  out:11
    _kill_pid  CC=9  out:13
    _pids_on_port  CC=16  out:17
    _wait_port_free  CC=4  out:8
    _worker_pids_from_state  CC=10  out:12
    takeover_port  CC=6  out:12
  urisysnode.port.utils  [6 funcs]
    _fuser_kill_port  CC=4  out:3
    _pid_alive  CC=2  out:1
    _pidfile_path  CC=1  out:2
    _pids_on_port_ss  CC=5  out:5
    _pids_serve_cmdline  CC=7  out:8
    _read_cmdline  CC=2  out:5
  urisysnode.release_verify  [4 funcs]
    _ed25519_verify  CC=3  out:5
    canonical_digest  CC=3  out:5
    signature_required  CC=3  out:2
    verify_release  CC=14  out:15
  urisysnode.remote  [19 funcs]
    build_wheel  CC=3  out:11
    call_uri  CC=4  out:4
    default_endpoint  CC=1  out:2
    default_nodes_registry  CC=1  out:4
    default_route_map  CC=1  out:4
    default_wheel_host  CC=1  out:2
    health  CC=2  out:5
    install_pack  CC=2  out:1
    pip_install  CC=1  out:1
    restart_worker  CC=1  out:1
  urisysnode.router  [5 funcs]
    _match_pattern  CC=1  out:4
    load_route_map  CC=3  out:4
    node_endpoint  CC=5  out:6
    resolve_remote_route  CC=5  out:3
    rewrite_uri_for_slave  CC=8  out:5
  urisysnode.runtime.builder  [3 funcs]
    _extend_pack_paths  CC=1  out:0
    _register_pack  CC=14  out:16
    build_runtime  CC=18  out:37
  urisysnode.runtime.packs  [2 funcs]
    ensure_pack_for_uri  CC=3  out:6
    load_pack_into_runtime  CC=30  out:31
  urisysnode.serve  [16 funcs]
    _app_chat_get  CC=10  out:14
    _app_chat_post  CC=9  out:15
    _app_chat_store  CC=2  out:2
    _extend_pack_paths  CC=1  out:0
    _register_pack  CC=14  out:16
    _release_forward_spec  CC=11  out:8
    apply_host_trust  CC=10  out:8
    build_runtime  CC=18  out:37
    call_uri  CC=20  out:30
    ensure_pack_for_uri  CC=3  out:6
  urisysnode.supervisor  [9 funcs]
    _fetch_patterns  CC=3  out:3
    _needs_install  CC=3  out:1
    _wait_health  CC=5  out:5
    _wire  CC=2  out:5
    spawn  CC=15  out:21
    alive  CC=3  out:2
    _free_port  CC=1  out:3
    _http_get  CC=1  out:4
    _schemes_of  CC=4  out:3
  urisysnode.worker  [6 funcs]
    _load_node_profile  CC=5  out:5
    _local_schemes  CC=4  out:4
    _wire_router_callback  CC=3  out:7
    build_worker_runtime  CC=5  out:13
    main  CC=4  out:13
    serve_worker  CC=5  out:11

EDGES:
  urisysnode.release_verify.verify_release → urisysnode.release_verify.signature_required
  urisysnode.release_verify.verify_release → urisysnode.release_verify.canonical_digest
  urisysnode.release_verify.verify_release → urisysnode.release_verify._ed25519_verify
  urisysnode.forward_config.load_forward_entries → urisysnode.forward_config._normalize_entry
  urisysnode.forward_config.wire_forward_packs → urisysnode.serve.register_forward_pack
  urisysnode.forward_config.load_release_forward_entries → urisysnode.forward_config._normalize_release_entry
  urisysnode.forward_config.wire_release_forward_packs → urisysnode.serve.hotload_release_pack
  urisysnode.supervisor.Worker.alive → urisysnode.supervisor._http_get
  urisysnode.supervisor.PackSupervisor.spawn → urisysnode.supervisor._free_port
  urisysnode.supervisor.PackSupervisor._needs_install → urisysnode.pack_resolver.pack_importable
  urisysnode.supervisor.PackSupervisor._wait_health → urisysnode.supervisor._http_get
  urisysnode.supervisor.PackSupervisor._fetch_patterns → urisysnode.supervisor._http_get
  urisysnode.supervisor.PackSupervisor._wire → urisysnode.serve.register_forward_pack
  urisysnode.supervisor.PackSupervisor._wire → urisysnode.supervisor._schemes_of
  urisysnode.client.call_via_route_map → urisysnode.router.load_route_map
  urisysnode.client.call_via_route_map → urisysnode.router.resolve_remote_route
  urisysnode.client.call_via_route_map → urisysnode.router.node_endpoint
  urisysnode.client.call_via_route_map → urisysnode.router.rewrite_uri_for_slave
  urisysnode.client.call_via_route_map → urisysnode.client.remote_call
  urisysnode.forward.forward_call → urisysnode.client.remote_call
  urisysnode.remote.health → urisysnode.remote.default_endpoint
  urisysnode.remote.wait_health → urisysnode.remote.default_endpoint
  urisysnode.remote.wait_health → urisysnode.remote.health
  urisysnode.remote.call_uri → urisysnode.client.call_via_route_map
  urisysnode.remote.call_uri → urisysnode.client.remote_call
  urisysnode.remote.call_uri → urisysnode.remote.default_route_map
  urisysnode.remote.call_uri → urisysnode.remote.default_nodes_registry
  urisysnode.remote.pip_install → urisysnode.remote.call_uri
  urisysnode.remote.install_pack → urisysnode.remote.call_uri
  urisysnode.remote.spawn_worker → urisysnode.remote.call_uri
  urisysnode.remote.restart_worker → urisysnode.remote.call_uri
  urisysnode.remote.stop_worker → urisysnode.remote.call_uri
  urisysnode.remote.workers → urisysnode.remote.call_uri
  urisysnode.remote.schedule_restart → urisysnode.remote.call_uri
  urisysnode.remote.wheel_url → urisysnode.remote.default_wheel_host
  urisysnode.remote.upgrade_lenovo_node → urisysnode.remote.build_wheel
  urisysnode.remote.upgrade_lenovo_node → urisysnode.remote.serve_wheels
  urisysnode.remote.upgrade_lenovo_node → urisysnode.remote.default_wheel_host
  urisysnode.remote.upgrade_lenovo_node → urisysnode.remote.default_endpoint
  urisysnode.remote.upgrade_lenovo_node → urisysnode.remote.health
  urisysnode.remote.upgrade_lenovo_node → urisysnode.remote.pip_install
  urisysnode.remote.upgrade_lenovo_node → urisysnode.remote.schedule_restart
  urisysnode.remote.upgrade_lenovo_kv → urisysnode.remote.build_wheel
  urisysnode.remote.upgrade_lenovo_kv → urisysnode.remote.serve_wheels
  urisysnode.remote.upgrade_lenovo_kv → urisysnode.remote.default_wheel_host
  urisysnode.remote.upgrade_lenovo_kv → urisysnode.remote.health
  urisysnode.remote.upgrade_lenovo_kv → urisysnode.remote.pip_install
  urisysnode.remote.upgrade_lenovo_kv → urisysnode.remote.schedule_restart
  urisysnode.handlers.query_health → urisysnode.identity.health.health_payload
  urisysnode.handlers.query_identity → urisysnode.identity.core.load_identity
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 61f 7869L | python:30,yaml:15,json:7,shell:5,toml:1,yml:1,gui:1 | 2026-06-19
# generated in 0.01s
# CC̅=5.1 | critical:13/204 | dups:0 | cycles:0

HEALTH[13]:
  🟡 CC    main CC=22 (limit:15)
  🟡 CC    load_forward_entries CC=15 (limit:15)
  🟡 CC    spawn CC=15 (limit:15)
  🟡 CC    main CC=26 (limit:15)
  🟡 CC    select_artifact CC=15 (limit:15)
  🟡 CC    build_runtime CC=18 (limit:15)
  🟡 CC    load_pack_into_runtime CC=30 (limit:15)
  🟡 CC    call_uri CC=20 (limit:15)
  🟡 CC    serve CC=16 (limit:15)
  🟡 CC    _pids_on_port CC=16 (limit:15)
  🟡 CC    _is_node_serve_process CC=16 (limit:15)
  🟡 CC    load_pack_into_runtime CC=30 (limit:15)
  🟡 CC    build_runtime CC=18 (limit:15)

REFACTOR[1]:
  1. split 13 high-CC methods  (CC>15)

PIPELINES[51]:
  [1] Src [main]: main → build_runtime → _extend_pack_paths
      PURITY: 100% pure
  [2] Src [register]: register
      PURITY: 100% pure
  [3] Src [alive]: alive → _http_get
      PURITY: 100% pure
  [4] Src [__init__]: __init__
      PURITY: 100% pure
  [5] Src [_default_worker_env]: _default_worker_env
      PURITY: 100% pure
  [6] Src [spawn]: spawn → _free_port
      PURITY: 100% pure
  [7] Src [restart]: restart
      PURITY: 100% pure
  [8] Src [_needs_install]: _needs_install → pack_importable → import_pack_module → pack_module
      PURITY: 100% pure
  [9] Src [stop]: stop
      PURITY: 100% pure
  [10] Src [status]: status
      PURITY: 100% pure
  [11] Src [shutdown]: shutdown
      PURITY: 100% pure
  [12] Src [start_monitor]: start_monitor
      PURITY: 100% pure
  [13] Src [_reap]: _reap
      PURITY: 100% pure
  [14] Src [restore]: restore
      PURITY: 100% pure
  [15] Src [_wait_health]: _wait_health → _http_get
      PURITY: 100% pure
  [16] Src [_fetch_patterns]: _fetch_patterns → _http_get
      PURITY: 100% pure
  [17] Src [_wire]: _wire → register_forward_pack
      PURITY: 100% pure
  [18] Src [_terminate]: _terminate
      PURITY: 100% pure
  [19] Src [_persist]: _persist
      PURITY: 100% pure
  [20] Src [forward_call]: forward_call → remote_call
      PURITY: 100% pure
  [21] Src [main]: main → call_uri → call_via_route_map → load_route_map
      PURITY: 100% pure
  [22] Src [query_health]: query_health → health_payload → load_identity → _identity_path → ...(2 more)
      PURITY: 100% pure
  [23] Src [query_identity]: query_identity → load_identity → _identity_path → _data_dir → ...(1 more)
      PURITY: 100% pure
  [24] Src [command_indicator_on]: command_indicator_on → require_paired → load_pairing → _pairing_path → ...(2 more)
      PURITY: 100% pure
  [25] Src [command_indicator_off]: command_indicator_off → require_paired → load_pairing → _pairing_path → ...(2 more)
      PURITY: 100% pure
  [26] Src [query_packs]: query_packs → auto_install_enabled
      PURITY: 100% pure
  [27] Src [command_install_pack]: command_install_pack → load_pack_into_runtime → ensure_pack_pypi → pack_install_specs → ...(3 more)
      PURITY: 100% pure
  [28] Src [command_spawn_worker]: command_spawn_worker → _get_supervisor
      PURITY: 100% pure
  [29] Src [query_workers]: query_workers → _get_supervisor
      PURITY: 100% pure
  [30] Src [command_restart_worker]: command_restart_worker → _get_supervisor
      PURITY: 100% pure
  [31] Src [command_stop_worker]: command_stop_worker → _get_supervisor
      PURITY: 100% pure
  [32] Src [command_register_forward]: command_register_forward → register_forward_pack
      PURITY: 100% pure
  [33] Src [ensure_boot_pack]: ensure_boot_pack → github_wheel_url → github_owner
      PURITY: 100% pure
  [34] Src [github_wheel_urls]: github_wheel_urls → resolve_pack_spec → github_wheel_url → github_owner
      PURITY: 100% pure
  [35] Src [https_request]: https_request
      PURITY: 100% pure
  [36] Src [__init__]: __init__ → default_app_chat_path → default_data_root
      PURITY: 100% pure
  [37] Src [append]: append
      PURITY: 100% pure
  [38] Src [list_messages]: list_messages
      PURITY: 100% pure
  [39] Src [list_channels]: list_channels
      PURITY: 100% pure
  [40] Src [query_chat_messages]: query_chat_messages → _store
      PURITY: 100% pure
  [41] Src [command_chat_append]: command_chat_append → _store
      PURITY: 100% pure
  [42] Src [query_chat_channels]: query_chat_channels → _store
      PURITY: 100% pure
  [43] Src [main]: main → serve_worker → build_worker_runtime → _wire_router_callback → ...(1 more)
      PURITY: 100% pure
  [44] Src [_pids_serve_cmdline]: _pids_serve_cmdline → _read_cmdline
      PURITY: 100% pure
  [45] Src [resolve_node_config]: resolve_node_config
      PURITY: 100% pure
  [46] Src [_default_real_config]: _default_real_config
      PURITY: 100% pure
  [47] Src [_bootstrap_worker_packs]: _bootstrap_worker_packs → pack_importable → import_pack_module → pack_module
      PURITY: 100% pure
  [48] Src [ensure_pack_for_uri]: ensure_pack_for_uri → scheme_for_uri
      PURITY: 100% pure
  [49] Src [apply_host_trust]: apply_host_trust
      PURITY: 100% pure
  [50] Src [_pack_modules]: _pack_modules
      PURITY: 100% pure

LAYERS:
  urisysnode/                     CC̄=5.2    ←in:18  →out:21  !! split
  │ !! serve                      761L  1C   19m  CC=30     ←7
  │ !! remote                     516L  0C   21m  CC=26     ←0
  │ !! supervisor                 358L  2C   21m  CC=15     ←0
  │ pack_resolver              323L  0C   17m  CC=10     ←5
  │ !! artifact_resolver          305L  1C   21m  CC=15     ←2
  │ !! manager                    211L  0C    7m  CC=16     ←1
  │ !! cli                        196L  0C    1m  CC=22     ←0
  │ health                     195L  0C   10m  CC=7      ←2
  │ worker                     186L  0C    6m  CC=5      ←0
  │ !! builder                    168L  0C    4m  CC=18     ←0
  │ handlers                   159L  0C   12m  CC=11     ←0
  │ !! packs                      150L  0C    4m  CC=30     ←0
  │ !! forward_config             144L  0C    6m  CC=15     ←2
  │ release_verify             138L  0C    5m  CC=14     ←1
  │ display_bootstrap          114L  0C    7m  CC=7      ←1
  │ pairing                    100L  0C    6m  CC=4      ←4
  │ manifest.yaml               96L  0C    0m  CC=0.0    ←0
  │ client                      92L  0C    3m  CC=6      ←4
  │ utils                       92L  0C    6m  CC=7      ←2
  │ routes                      90L  0C    1m  CC=1      ←0
  │ app_data                    85L  1C    5m  CC=9      ←0
  │ core                        81L  0C    7m  CC=4      ←10
  │ router                      52L  0C    5m  CC=8      ←2
  │ config                      52L  0C    2m  CC=7      ←0
  │ app_handlers                44L  0C    4m  CC=9      ←0
  │ __init__                    38L  0C    0m  CC=0.0    ←0
  │ __init__                    35L  0C    0m  CC=0.0    ←0
  │ __init__                    34L  0C    0m  CC=0.0    ←0
  │ forward                     33L  0C    1m  CC=9      ←0
  │ env                          5L  0C    0m  CC=0.0    ←0
  │ __init__                     0L  0C    0m  CC=0.0    ←0
  │
  docker/                         CC̄=0.0    ←in:0  →out:0
  │ entrypoint.sh               63L  0C    3m  CC=0.0    ←0
  │ Dockerfile.gui              61L  0C    0m  CC=0.0    ←0
  │ docker-compose.gui.yml      33L  0C    0m  CC=0.0    ←0
  │ node-profile.docker.json    33L  0C    0m  CC=0.0    ←0
  │ route-map.host.yaml         23L  0C    0m  CC=0.0    ←0
  │ nodes.registry.host.json     9L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! planfile.yaml             1319L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  525L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              99L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                94L  0C    0m  CC=0.0    ←0
  │ Makefile                    74L  0C    0m  CC=0.0    ←0
  │ project.sh                  63L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │
  scripts/                        CC̄=0.0    ←in:0  →out:0
  │ enable-host-trust.sh       142L  0C    0m  CC=0.0    ←0
  │ install-linux.sh            16L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-from-pytests.testql.toon.yaml    90L  0C    0m  CC=0.0    ←0
  │ generated-cli-tests.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │
  config/                         CC̄=0.0    ←in:0  →out:0
  │ route-map.lenovo.yaml       72L  0C    0m  CC=0.0    ←0
  │ node-profile.lenovo.json    68L  0C    0m  CC=0.0    ←0
  │ node-profile.json           32L  0C    0m  CC=0.0    ←0
  │ node-profile.full-trust.json    24L  0C    0m  CC=0.0    ←0
  │ route-map.master.yaml       19L  0C    0m  CC=0.0    ←0
  │ nodes.registry.json         18L  0C    0m  CC=0.0    ←0
  │ route-map.slave.yaml        14L  0C    0m  CC=0.0    ←0
  │
  data/                           CC̄=0.0    ←in:0  →out:0
  │ workers.json                16L  0C    0m  CC=0.0    ←0
  │
  flows/                          CC̄=0.0    ←in:0  →out:0
  │ bootstrap-kvm-github.uri.flow.yaml    28L  0C    0m  CC=0.0    ←0
  │ bootstrap-kvm-pypi.uri.flow.yaml    18L  0C    0m  CC=0.0    ←0
  │ remote-probe.uri.flow.yaml    17L  0C    0m  CC=0.0    ←0
  │ slave-kvm-demo.uri.flow.yaml    13L  0C    0m  CC=0.0    ←0
  │ screen-capture-mss.uri.flow.yaml    12L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     urisysnode/__init__.py                    0L

COUPLING:
                                urisysnode  urisysnode.identity   urisysnode.runtime      urisysnode.port
           urisysnode                   ──                   18                  ←18                    3  hub
  urisysnode.identity                  ←18                   ──                   ←1                   ←2  hub
   urisysnode.runtime                   18                    1                   ──                       !! fan-out
      urisysnode.port                   ←3                    2                                        ──
  CYCLES: none
  HUB: urisysnode/ (fan-in=18)
  HUB: urisysnode.identity/ (fan-in=21)
  SMELL: urisysnode/ fan-out=21 → split needed
  SMELL: urisysnode.runtime/ fan-out=19 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 9 groups | 31f 4814L | 2026-06-19

SUMMARY:
  files_scanned: 31
  total_lines:   4814
  dup_groups:    9
  dup_fragments: 18
  saved_lines:   132
  scan_ms:       2406

HOTSPOTS[7] (files with most duplication):
  urisysnode/serve.py  dup=93L  groups=4  frags=4  (1.9%)
  urisysnode/runtime/builder.py  dup=54L  groups=2  frags=2  (1.1%)
  urisysnode/remote.py  dup=42L  groups=2  frags=4  (0.9%)
  urisysnode/runtime/config.py  dup=41L  groups=2  frags=2  (0.9%)
  urisysnode/handlers.py  dup=20L  groups=1  frags=2  (0.4%)
  urisysnode/identity/core.py  dup=6L  groups=2  frags=2  (0.1%)
  urisysnode/identity/pairing.py  dup=6L  groups=2  frags=2  (0.1%)

DUPLICATES[9] (ranked by impact):
  [4cebb0856c93d3f3] ! STRU  _register_pack  L=48 N=2 saved=48 sim=1.00
      urisysnode/runtime/builder.py:35-82  (_register_pack)
      urisysnode/serve.py:63-110  (_register_pack)
  [58aed6403bd60707]   STRU  resolve_node_config  L=26 N=2 saved=26 sim=1.00
      urisysnode/runtime/config.py:10-35  (resolve_node_config)
      urisysnode/serve.py:113-137  (resolve_node_config)
  [cb23d0816fd169ac]   STRU  restart_worker  L=15 N=2 saved=15 sim=1.00
      urisysnode/remote.py:150-164  (restart_worker)
      urisysnode/remote.py:167-181  (stop_worker)
  [b1521bd8056e7dcd]   STRU  _default_real_config  L=15 N=2 saved=15 sim=1.00
      urisysnode/runtime/config.py:38-52  (_default_real_config)
      urisysnode/serve.py:140-153  (_default_real_config)
  [fdd6fc4fa011d5fa]   STRU  command_restart_worker  L=10 N=2 saved=10 sim=1.00
      urisysnode/handlers.py:122-131  (command_restart_worker)
      urisysnode/handlers.py:134-143  (command_stop_worker)
  [5cee5009a08b5fc2]   EXAC  _pack_modules  L=6 N=2 saved=6 sim=1.00
      urisysnode/runtime/builder.py:27-32  (_pack_modules)
      urisysnode/serve.py:55-60  (_pack_modules)
  [518765db9b27fb75]   STRU  default_route_map  L=6 N=2 saved=6 sim=1.00
      urisysnode/remote.py:18-23  (default_route_map)
      urisysnode/remote.py:26-31  (default_nodes_registry)
  [e4780f2ec2601c63]   STRU  _identity_path  L=3 N=2 saved=3 sim=1.00
      urisysnode/identity/core.py:45-47  (_identity_path)
      urisysnode/identity/pairing.py:14-16  (_pairing_path)
  [983e1a3bc0d9896f]   STRU  save_identity  L=3 N=2 saved=3 sim=1.00
      urisysnode/identity/core.py:79-81  (save_identity)
      urisysnode/identity/pairing.py:32-34  (save_pairing)

REFACTOR[9] (ranked by priority):
  [1] ◐ extract_function   → urisysnode/utils/_register_pack.py
      WHY: 2 occurrences of 48-line block across 2 files — saves 48 lines
      FILES: urisysnode/runtime/builder.py, urisysnode/serve.py
  [2] ○ extract_function   → urisysnode/utils/resolve_node_config.py
      WHY: 2 occurrences of 26-line block across 2 files — saves 26 lines
      FILES: urisysnode/runtime/config.py, urisysnode/serve.py
  [3] ○ extract_function   → urisysnode/utils/restart_worker.py
      WHY: 2 occurrences of 15-line block across 1 files — saves 15 lines
      FILES: urisysnode/remote.py
  [4] ○ extract_function   → urisysnode/utils/_default_real_config.py
      WHY: 2 occurrences of 15-line block across 2 files — saves 15 lines
      FILES: urisysnode/runtime/config.py, urisysnode/serve.py
  [5] ○ extract_function   → urisysnode/utils/command_restart_worker.py
      WHY: 2 occurrences of 10-line block across 1 files — saves 10 lines
      FILES: urisysnode/handlers.py
  [6] ○ extract_function   → urisysnode/utils/_pack_modules.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: urisysnode/runtime/builder.py, urisysnode/serve.py
  [7] ○ extract_function   → urisysnode/utils/default_route_map.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: urisysnode/remote.py
  [8] ○ extract_function   → urisysnode/identity/utils/_identity_path.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: urisysnode/identity/core.py, urisysnode/identity/pairing.py
  [9] ○ extract_function   → urisysnode/identity/utils/save_identity.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: urisysnode/identity/core.py, urisysnode/identity/pairing.py

QUICK_WINS[6] (low risk, high savings — do first):
  [2] extract_function   saved=26L  → urisysnode/utils/resolve_node_config.py
      FILES: config.py, serve.py
  [3] extract_function   saved=15L  → urisysnode/utils/restart_worker.py
      FILES: remote.py
  [4] extract_function   saved=15L  → urisysnode/utils/_default_real_config.py
      FILES: config.py, serve.py
  [5] extract_function   saved=10L  → urisysnode/utils/command_restart_worker.py
      FILES: handlers.py
  [6] extract_function   saved=6L  → urisysnode/utils/_pack_modules.py
      FILES: builder.py, serve.py
  [7] extract_function   saved=6L  → urisysnode/utils/default_route_map.py
      FILES: remote.py

EFFORT_ESTIMATE (total ≈ 5.2h):
  hard   _register_pack                      saved=48L  ~144min
  medium resolve_node_config                 saved=26L  ~52min
  medium restart_worker                      saved=15L  ~30min
  medium _default_real_config                saved=15L  ~30min
  easy   command_restart_worker              saved=10L  ~20min
  easy   _pack_modules                       saved=6L  ~12min
  easy   default_route_map                   saved=6L  ~12min
  easy   _identity_path                      saved=3L  ~6min
  easy   save_identity                       saved=3L  ~6min

METRICS-TARGET:
  dup_groups:  9 → 0
  saved_lines: 132 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 204 func | 26f | 2026-06-19
# generated in 0.00s

NEXT[10] (ranked by impact):
  [1] !! SPLIT           urisysnode/serve.py
      WHY: 761L, 1 classes, max CC=30
      EFFORT: ~4h  IMPACT: 22830

  [2] !  SPLIT-FUNC      main  CC=22  fan=48
      WHY: CC=22 exceeds 15
      EFFORT: ~1h  IMPACT: 1056

  [3] !! SPLIT-FUNC      main  CC=26  fan=36
      WHY: CC=26 exceeds 15
      EFFORT: ~1h  IMPACT: 936

  [4] !! SPLIT-FUNC      load_pack_into_runtime  CC=30  fan=23
      WHY: CC=30 exceeds 15
      EFFORT: ~1h  IMPACT: 690

  [5] !! SPLIT-FUNC      load_pack_into_runtime  CC=30  fan=23
      WHY: CC=30 exceeds 15
      EFFORT: ~1h  IMPACT: 690

  [6] !  SPLIT-FUNC      build_runtime  CC=18  fan=25
      WHY: CC=18 exceeds 15
      EFFORT: ~1h  IMPACT: 450

  [7] !  SPLIT-FUNC      build_runtime  CC=18  fan=25
      WHY: CC=18 exceeds 15
      EFFORT: ~1h  IMPACT: 450

  [8] !  SPLIT-FUNC      serve  CC=16  fan=26
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 416

  [9] !  SPLIT-FUNC      call_uri  CC=20  fan=16
      WHY: CC=20 exceeds 15
      EFFORT: ~1h  IMPACT: 320

  [10] !  SPLIT-FUNC      PackSupervisor.spawn  CC=15  fan=17
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 255


RISKS[3]:
  ⚠ Splitting planfile.yaml may break 0 import paths
  ⚠ Splitting urisysnode/serve.py may break 19 import paths
  ⚠ Splitting goal.yaml may break 0 import paths

METRICS-TARGET:
  CC̄:          5.1 → ≤3.6
  max-CC:      30 → ≤15
  god-modules: 4 → 0
  high-CC(≥15): 13 → ≤6
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=4.9 → now CC̄=5.1
```

## Intent

urisys-node slave: screen/kvm/him URI server components
