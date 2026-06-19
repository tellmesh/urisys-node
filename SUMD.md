# urisysnode

urisys-node slave: screen/kvm/him URI server components

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Workflows](#workflows)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Makefile Targets](#makefile-targets)
- [Code Analysis](#code-analysis)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `urisys-node`
- **version**: `0.1.40`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Makefile, testql(2), app.doql.less, goal.yaml, .env.example, docker-compose.gui.yml, project/(3 analysis files)

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

## Interfaces

### CLI Entry Points

- `urisys-node`

### testql Scenarios

#### `testql-scenarios/generated-cli-tests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-cli-tests.testql.toon.yaml
# SCENARIO: CLI Command Tests
# TYPE: cli
# GENERATED: true

CONFIG[2]{key, value}:
  cli_command, python -m urisys-node
  timeout_ms, 10000

# Test 1: CLI help command
SHELL "python -m urisys-node --help" 5000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "usage"

# Test 2: CLI version command
SHELL "python -m urisys-node --version" 5000
ASSERT_EXIT_CODE 0

# Test 3: CLI main workflow (dry-run)
SHELL "python -m urisys-node --help" 10000
ASSERT_EXIT_CODE 0
```

#### `testql-scenarios/generated-from-pytests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-from-pytests.testql.toon.yaml
# SCENARIO: Auto-generated from Python Tests
# TYPE: integration
# GENERATED: true

CONFIG[2]{key, value}:
  base_url, ${api_url:-http://localhost:8101}
  timeout_ms, 10000

# Converted 80 assertions from pytest
ASSERT[80]{field, operator, expected}:
  seen.endpoint, ==, "http://192.168.188.201:8790"
  env.URISYS_NODE_CONFIG, ==, str(prof.resolve())
  env.URISYS_ALLOW_REAL, ==, "1"
  env.URISYS_NODE_ROUTER, ==, "http://127.0.0.1:8790"
  calls, ==, [("http://127.0.0.1:8790"
  load_pairing().controller, ==, "https://controller.local"
  docker_stack.service, ==, "urisys-node"
  len(entries), ==, 1
  entries[0].scheme, ==, "imgl"
  entries[0].scheme, ==, "vql"
  len(entries), ==, 2
  entries[0].contract, ==, "urihim.contract"
  entries[0].catalog, ==, fc.DEFAULT_CATALOG_URL
  entries[1].catalog, ==, "https://cat"
  calls, ==, [("urihim.contract"
  rt.config.forward_targets.stepper, ==, "http://127.0.0.1:8791"
  move.approval, ==, "required" and move.side_effects is True
  pos.approval, ==, "not_required"
  captured.endpoint, ==, "http://worker:8791"
  captured.uri, ==, "stepper://x/query/position"
  captured.payload, ==, {"unit": "mm"}
  out.result.type, ==, "forward_no_target"
  url, ==, "https://github.com/tellmesh/urihim/releases/download/v0.1.3/urihim-0.1.3-py3-none-any.whl"
  url, ==, "https://github.com/tellmesh/uristt/releases/download/v0.1.0/uristt-0.1.0-py3-none-any.whl"
  url, ==, "https://github.com/tellmesh/uriwebrtc/releases/download/v0.1.0/uriwebrtc-0.1.0-py3-none-any.whl"
  out.stage, ==, "pairing"
  out.stage, ==, "registered"
  out.scheme, ==, "stepper"
  out.endpoint, ==, "http://127.0.0.1:8791"
  rt.config.forward_targets.stepper, ==, "http://127.0.0.1:8791"
  move.approval, ==, "required" and move.side_effects is True
  out.stage, ==, "verify"
  out.stage, ==, "spec"
  out.scheme, ==, "him"
  rt.config.forward_targets.him, ==, "http://127.0.0.1:8792"
  click.approval, ==, "required" and click.side_effects is True
  artifacts[0].ref, ==, "img:1"
  captured.container_port, ==, 8794
  captured.host_port, ==, 8895
  out.container_port, ==, 8794
  seen.endpoint, ==, "http://192.168.188.201:8790"
  env.URISYS_NODE_CONFIG, ==, str(prof.resolve())
  env.URISYS_ALLOW_REAL, ==, "1"
  env.URISYS_NODE_ROUTER, ==, "http://127.0.0.1:8790"
  calls, ==, [("http://127.0.0.1:8790"
  load_pairing().controller, ==, "https://controller.local"
  docker_stack.service, ==, "urisys-node"
  len(entries), ==, 1
  entries[0].scheme, ==, "imgl"
  entries[0].scheme, ==, "vql"
  len(entries), ==, 2
  entries[0].contract, ==, "urihim.contract"
  entries[0].catalog, ==, fc.DEFAULT_CATALOG_URL
  entries[1].catalog, ==, "https://cat"
  calls, ==, [("urihim.contract"
  rt.config.forward_targets.stepper, ==, "http://127.0.0.1:8791"
  move.approval, ==, "required" and move.side_effects is True
  pos.approval, ==, "not_required"
  captured.endpoint, ==, "http://worker:8791"
  captured.uri, ==, "stepper://x/query/position"
  captured.payload, ==, {"unit": "mm"}
  out.result.type, ==, "forward_no_target"
  url, ==, "https://github.com/tellmesh/urihim/releases/download/v0.1.3/urihim-0.1.3-py3-none-any.whl"
  url, ==, "https://github.com/tellmesh/uristt/releases/download/v0.1.0/uristt-0.1.0-py3-none-any.whl"
  url, ==, "https://github.com/tellmesh/uriwebrtc/releases/download/v0.1.0/uriwebrtc-0.1.0-py3-none-any.whl"
  out.stage, ==, "pairing"
  out.stage, ==, "registered"
  out.scheme, ==, "stepper"
  out.endpoint, ==, "http://127.0.0.1:8791"
  rt.config.forward_targets.stepper, ==, "http://127.0.0.1:8791"
  move.approval, ==, "required" and move.side_effects is True
  out.stage, ==, "verify"
  out.stage, ==, "spec"
  out.scheme, ==, "him"
  rt.config.forward_targets.him, ==, "http://127.0.0.1:8792"
  click.approval, ==, "required" and click.side_effects is True
  artifacts[0].ref, ==, "img:1"
  captured.container_port, ==, 8794
  captured.host_port, ==, 8895
  out.container_port, ==, 8794
```

## Workflows

## Configuration

```yaml
project:
  name: urisys-node
  version: 0.1.40
  env: local
```

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

## Deployment

```bash markpact:run
pip install urisys-node

# development install
pip install -e .[dev]
```

### Docker Compose (`docker-compose.gui.yml`)

- **urisys-node-gui** image=`{'context': '../../..', 'dockerfile': 'urisys-node/docker/Dockerfile.gui'}` ports: `${URISYS_NODE_HOST_PORT:-8790}:8790`

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `*(not set)*` | Required: OpenRouter API key (https://openrouter.ai/keys) |
| `LLM_MODEL` | `openrouter/qwen/qwen3-coder-next` | Model (default: openrouter/qwen/qwen3-coder-next) |
| `PFIX_AUTO_APPLY` | `true` | true = apply fixes without asking |
| `PFIX_AUTO_INSTALL_DEPS` | `true` | true = auto pip/uv install |
| `PFIX_AUTO_RESTART` | `false` | true = os.execv restart after fix |
| `PFIX_MAX_RETRIES` | `3` |  |
| `PFIX_DRY_RUN` | `false` |  |
| `PFIX_ENABLED` | `true` |  |
| `PFIX_GIT_COMMIT` | `false` | true = auto-commit fixes |
| `PFIX_GIT_PREFIX` | `pfix:` | commit message prefix |
| `PFIX_CREATE_BACKUPS` | `false` | false = disable .pfix_backups/ directory |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`urisys-node`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `venv/lib/python3.13/site-packages/pip/__init__.py:__version__`

## Makefile Targets

- `help`
- `install`
- `test`
- `test-all`
- `test-integration`
- `test-coverage`
- `test-watch`
- `serve`
- `health`
- `app-chat-smoke`
- `publish` — Release helpers
- `publish-test`
- `version`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# urisys-node | 69f 7363L | python:63,shell:5,less:1 | 2026-06-19
# stats: 317 func | 6 cls | 69 mod | CC̄=4.4 | critical:31 | cycles:0
# alerts[5]: CC load_pack_into_runtime=30; CC main=26; CC main=22; CC call_uri=22; fan-out main=33
# hotspots[5]: main fan=33; make_handler fan=27; main fan=24; build_runtime fan=24; build_runtime fan=24
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[69]:
  app.doql.less,122
  docker/entrypoint.sh,64
  project.sh,63
  scripts/enable-host-trust.sh,143
  scripts/install-linux.sh,17
  tests/integration/_fakepack.py,20
  tests/integration/test_artifact_resolver.py,96
  tests/integration/test_core_pack_boot_install.py,61
  tests/integration/test_docker_host_e2e.py,157
  tests/integration/test_forward_config.py,150
  tests/integration/test_forward_pack.py,75
  tests/integration/test_host_trust.py,57
  tests/integration/test_pack_auto_install.py,112
  tests/integration/test_pack_github.py,38
  tests/integration/test_pack_hotload.py,65
  tests/integration/test_pack_office_mail.py,30
  tests/integration/test_pack_rdpedge.py,15
  tests/integration/test_pack_webrtc_hotload.py,49
  tests/integration/test_release_hotload.py,259
  tests/integration/test_serve_takeover.py,74
  tests/integration/test_uriscreen_auto.py,35
  tests/integration/test_urishell.py,46
  tests/integration/test_urisys_node.py,68
  tests/integration/test_worker_supervisor.py,92
  tests/test_app_data.py,61
  tests/test_health_profile_visibility.py,40
  tests/test_import_urisysnode.py,4
  tests/test_invalid_profile_tolerated.py,47
  tests/test_node_config_discovery.py,66
  tests/test_pack_resolver_browser.py,26
  tests/test_pack_resolver_kv.py,9
  tests/test_pack_resolver_webrtc.py,9
  tests/test_remote_restart.py,42
  tests/test_supervisor_worker_env.py,24
  tests/test_worker_profile.py,52
  tests/test_worker_router_callback.py,67
  tree.sh,2
  urisysnode/__init__.py,1
  urisysnode/app_data.py,86
  urisysnode/app_handlers.py,45
  urisysnode/artifact_resolver.py,306
  urisysnode/cli.py,197
  urisysnode/client.py,93
  urisysnode/display_bootstrap.py,115
  urisysnode/env.py,6
  urisysnode/forward.py,34
  urisysnode/forward_config.py,145
  urisysnode/handlers.py,155
  urisysnode/identity/__init__.py,39
  urisysnode/identity/core.py,82
  urisysnode/identity/health.py,196
  urisysnode/identity/pairing.py,101
  urisysnode/identity.py,58
  urisysnode/pack_resolver.py,324
  urisysnode/port/__init__.py,36
  urisysnode/port/manager.py,212
  urisysnode/port/utils.py,93
  urisysnode/release_verify.py,139
  urisysnode/remote.py,517
  urisysnode/router.py,53
  urisysnode/routes.py,91
  urisysnode/runtime/__init__.py,35
  urisysnode/runtime/builder.py,170
  urisysnode/runtime/config.py,53
  urisysnode/runtime/packs.py,153
  urisysnode/runtime.py,6
  urisysnode/serve.py,857
  urisysnode/supervisor.py,421
  urisysnode/worker.py,187
D:
  tests/integration/_fakepack.py:
    e: _ping,register
    _ping(payload;context)
    register(rt)
  tests/integration/test_artifact_resolver.py:
    e: test_select_artifact_by_platform,test_load_artifact_index_from_file,test_load_artifact_index_from_url,test_fetch_release,test_release_api_url,test_run_release_honors_artifact_container_port
    test_select_artifact_by_platform(tmp_path)
    test_load_artifact_index_from_file(tmp_path)
    test_load_artifact_index_from_url()
    test_fetch_release()
    test_release_api_url()
    test_run_release_honors_artifact_container_port(monkeypatch;tmp_path)
  tests/integration/test_core_pack_boot_install.py:
    e: _screen_import_once_then_ok,test_core_pack_auto_install_on_boot,test_core_pack_boot_raises_when_auto_install_disabled,test_core_pack_boot_raises_when_pip_fails
    _screen_import_once_then_ok(name)
    test_core_pack_auto_install_on_boot(tmp_path)
    test_core_pack_boot_raises_when_auto_install_disabled(tmp_path)
    test_core_pack_boot_raises_when_pip_fails(tmp_path)
  tests/integration/test_docker_host_e2e.py:
    e: _http_get,_remote_call,docker_stack,test_container_urisys_cli,test_host_health_and_routes,test_host_remote_identity,test_host_screen_capture,test_host_indicator_control
    _http_get(path)
    _remote_call(uri;payload;context)
    docker_stack()
    test_container_urisys_cli(docker_stack)
    test_host_health_and_routes(docker_stack)
    test_host_remote_identity(docker_stack)
    test_host_screen_capture(docker_stack)
    test_host_indicator_control()
  tests/integration/test_forward_config.py:
    e: _runtime,test_load_forward_entries_from_config,test_load_forward_entries_env_inline,test_wire_forward_packs_registers_routes,test_command_register_forward,test_load_release_forward_entries_from_config,test_load_release_forward_entries_env_inline,test_wire_release_forward_packs_calls_hotload,test_wire_release_forward_packs_is_best_effort,test_build_runtime_wires_config_forwards
    _runtime(tmp_path)
    test_load_forward_entries_from_config()
    test_load_forward_entries_env_inline()
    test_wire_forward_packs_registers_routes(tmp_path)
    test_command_register_forward(tmp_path)
    test_load_release_forward_entries_from_config()
    test_load_release_forward_entries_env_inline()
    test_wire_release_forward_packs_calls_hotload(tmp_path;monkeypatch)
    test_wire_release_forward_packs_is_best_effort(tmp_path;monkeypatch)
    test_build_runtime_wires_config_forwards(tmp_path;monkeypatch)
  tests/integration/test_forward_pack.py:
    e: _runtime,test_register_forward_adds_routes_and_target,test_call_forwards_to_worker,test_forward_without_target_fails_cleanly
    _runtime(tmp_path)
    test_register_forward_adds_routes_and_target(tmp_path)
    test_call_forwards_to_worker(tmp_path;monkeypatch)
    test_forward_without_target_fails_cleanly(tmp_path)
  tests/integration/test_host_trust.py:
    e: _runtime,test_no_policy_keeps_caller_approval_default,test_empty_list_grants_full_trust,test_matching_pattern_still_requires_approval,test_caller_can_still_approve_when_gated
    _runtime(policy)
    test_no_policy_keeps_caller_approval_default()
    test_empty_list_grants_full_trust()
    test_matching_pattern_still_requires_approval()
    test_caller_can_still_approve_when_gated()
  tests/integration/test_pack_auto_install.py:
    e: _node_only_runtime,test_install_pack_uri,test_install_pack_requires_approval,test_query_packs,test_call_uri_lazy_pack_route_not_found,test_load_pack_with_mock_pip,test_ensure_pack_for_uri_skips_pip_when_importable,test_force_reload_reregister_pack,test_pack_importable_uses_import_pack_module
    _node_only_runtime(tmp_path)
    test_install_pack_uri(tmp_path)
    test_install_pack_requires_approval(tmp_path)
    test_query_packs(tmp_path)
    test_call_uri_lazy_pack_route_not_found(tmp_path)
    test_load_pack_with_mock_pip(tmp_path)
    test_ensure_pack_for_uri_skips_pip_when_importable(tmp_path)
    test_force_reload_reregister_pack(tmp_path)
    test_pack_importable_uses_import_pack_module()
  tests/integration/test_pack_github.py:
    e: test_github_wheel_url_him,test_resolve_pack_spec_auto_prefers_github_for_him,test_resolve_pack_spec_kvm_stays_pypi,test_github_wheel_url_stt,test_github_wheel_url_webrtc
    test_github_wheel_url_him()
    test_resolve_pack_spec_auto_prefers_github_for_him()
    test_resolve_pack_spec_kvm_stays_pypi()
    test_github_wheel_url_stt()
    test_github_wheel_url_webrtc()
  tests/integration/test_pack_hotload.py:
    e: _node_only_runtime,test_hotload_adds_routes,test_hotload_is_idempotent,test_hotload_empty_pack_name_rejected,test_hotload_unknown_pack_reports_failure
    _node_only_runtime(tmp_path)
    test_hotload_adds_routes(tmp_path)
    test_hotload_is_idempotent(tmp_path)
    test_hotload_empty_pack_name_rejected(tmp_path)
    test_hotload_unknown_pack_reports_failure(tmp_path)
  tests/integration/test_pack_office_mail.py:
    e: test_scheme_to_pack_office_mail_vql,test_pack_modules_office_mail_vql
    test_scheme_to_pack_office_mail_vql()
    test_pack_modules_office_mail_vql()
  tests/integration/test_pack_rdpedge.py:
    e: test_pack_modules_rdpedge
    test_pack_modules_rdpedge()
  tests/integration/test_pack_webrtc_hotload.py:
    e: _node_only_runtime,test_hotload_webrtc_adds_routes,test_webrtc_session_start_after_hotload
    _node_only_runtime(tmp_path)
    test_hotload_webrtc_adds_routes(_auto;tmp_path)
    test_webrtc_session_start_after_hotload(_auto;tmp_path)
  tests/integration/test_release_hotload.py:
    e: _runtime,_release,test_canonical_digest_ignores_signature_block,test_disabled_policy_passes_through,test_required_but_unsigned_fails,test_required_untrusted_key_fails,test_required_no_crypto_backend_fails_closed,test_required_good_signature_verifies,test_required_mismatched_signature_fails,test_hotload_requires_pairing,test_hotload_happy_path_wires_forward,test_hotload_bad_signature_skips_run,test_hotload_missing_scheme_patterns,test_parse_contract_spec_extracts_scheme_and_patterns,test_parse_contract_spec_rejects_block_without_scheme,test_contract_url_from_release_variants,test_hotload_derives_spec_from_contract
    _runtime(tmp_path)
    _release()
    test_canonical_digest_ignores_signature_block()
    test_disabled_policy_passes_through(monkeypatch)
    test_required_but_unsigned_fails(monkeypatch)
    test_required_untrusted_key_fails(monkeypatch)
    test_required_no_crypto_backend_fails_closed(monkeypatch)
    test_required_good_signature_verifies(monkeypatch)
    test_required_mismatched_signature_fails(monkeypatch)
    test_hotload_requires_pairing(tmp_path;monkeypatch)
    test_hotload_happy_path_wires_forward(tmp_path;monkeypatch)
    test_hotload_bad_signature_skips_run(tmp_path;monkeypatch)
    test_hotload_missing_scheme_patterns(tmp_path;monkeypatch)
    test_parse_contract_spec_extracts_scheme_and_patterns()
    test_parse_contract_spec_rejects_block_without_scheme()
    test_contract_url_from_release_variants()
    test_hotload_derives_spec_from_contract(tmp_path;monkeypatch)
  tests/integration/test_serve_takeover.py:
    e: _free_port,_wait_listen,test_takeover_does_not_target_shell_wrappers,test_takeover_kills_old_listener
    _free_port()
    _wait_listen(port;timeout)
    test_takeover_does_not_target_shell_wrappers()
    test_takeover_kills_old_listener()
  tests/integration/test_uriscreen_auto.py:
    e: test_resolve_backend_auto_x11,test_resolve_backend_auto_wayland,test_is_black_png
    test_resolve_backend_auto_x11(monkeypatch)
    test_resolve_backend_auto_wayland(monkeypatch)
    test_is_black_png(tmp_path)
  tests/integration/test_urishell.py:
    e: test_shell_route_registered,test_shell_pip_dry_run,test_shell_requires_allow_real
    test_shell_route_registered()
    test_shell_pip_dry_run()
    test_shell_requires_allow_real()
  tests/integration/test_urisys_node.py:
    e: test_identity_and_enroll,test_screen_capture_mock,test_rewrite_uri_for_slave,test_health_payload,test_health_payload_with_runtime
    test_identity_and_enroll()
    test_screen_capture_mock()
    test_rewrite_uri_for_slave()
    test_health_payload()
    test_health_payload_with_runtime()
  tests/integration/test_worker_supervisor.py:
    e: _router,_worker_env,test_build_worker_runtime_loads_module,test_supervisor_spawns_and_router_forwards,test_supervisor_restart_keeps_routes,test_supervisor_stop_terminates_worker
    _router(tmp_path)
    _worker_env()
    test_build_worker_runtime_loads_module()
    test_supervisor_spawns_and_router_forwards(tmp_path)
    test_supervisor_restart_keeps_routes(tmp_path)
    test_supervisor_stop_terminates_worker(tmp_path)
  tests/test_app_data.py:
    e: chat_path,test_append_and_list_messages,test_list_channels,test_uri_handlers
    chat_path(tmp_path;monkeypatch)
    test_append_and_list_messages(chat_path)
    test_list_channels(chat_path)
    test_uri_handlers(chat_path)
  tests/test_health_profile_visibility.py:
    e: test_profile_loaded_is_visible,test_mock_when_no_profile,test_auto_default_source_visible,_RT
    _RT: __init__(2)
    test_profile_loaded_is_visible()
    test_mock_when_no_profile()
    test_auto_default_source_visible()
  tests/test_import_urisysnode.py:
    e: test_import_urisysnode
    test_import_urisysnode()
  tests/test_invalid_profile_tolerated.py:
    e: _minimal_node,test_empty_profile_does_not_crash,test_garbage_profile_does_not_crash,test_empty_profile_with_allow_real_uses_defaults
    _minimal_node(tmp_path;monkeypatch)
    test_empty_profile_does_not_crash(tmp_path;monkeypatch)
    test_garbage_profile_does_not_crash(tmp_path;monkeypatch)
    test_empty_profile_with_allow_real_uses_defaults(tmp_path;monkeypatch)
  tests/test_node_config_discovery.py:
    e: test_env_var_wins,test_discovers_xdg_profile_when_env_unset,test_explicit_arg_beats_env,test_returns_empty_when_none,test_default_real_config_wayland,test_default_real_config_x11
    test_env_var_wins(tmp_path;monkeypatch)
    test_discovers_xdg_profile_when_env_unset(tmp_path;monkeypatch)
    test_explicit_arg_beats_env(tmp_path;monkeypatch)
    test_returns_empty_when_none(tmp_path;monkeypatch)
    test_default_real_config_wayland(monkeypatch)
    test_default_real_config_x11(monkeypatch)
  tests/test_pack_resolver_browser.py:
    e: test_browser_pack_mapping,test_browser_github_wheel_url,test_browser_importable_when_installed
    test_browser_pack_mapping()
    test_browser_github_wheel_url()
    test_browser_importable_when_installed()
  tests/test_pack_resolver_kv.py:
    e: test_kv_and_log_scheme_mapping
    test_kv_and_log_scheme_mapping()
  tests/test_pack_resolver_webrtc.py:
    e: test_webrtc_scheme_mapping
    test_webrtc_scheme_mapping()
  tests/test_remote_restart.py:
    e: test_restart_scheduled_treats_connection_drop_as_ok,test_schedule_restart_maps_connection_exception,test_restart_scheduled_passes_through_real_errors,test_schedule_restart_forwards_endpoint
    test_restart_scheduled_treats_connection_drop_as_ok()
    test_schedule_restart_maps_connection_exception(monkeypatch)
    test_restart_scheduled_passes_through_real_errors()
    test_schedule_restart_forwards_endpoint(monkeypatch)
  tests/test_supervisor_worker_env.py:
    e: test_default_worker_env_uses_runtime_config_path
    test_default_worker_env_uses_runtime_config_path(tmp_path;monkeypatch)
  tests/test_worker_profile.py:
    e: _write_fake_module,test_worker_runtime_loads_profile,test_missing_profile_is_empty_not_error
    _write_fake_module(tmp_path)
    test_worker_runtime_loads_profile(tmp_path;monkeypatch)
    test_missing_profile_is_empty_not_error(tmp_path;monkeypatch)
  tests/test_worker_router_callback.py:
    e: _write_chain_module,test_worker_forwards_non_local_scheme_to_router,test_worker_keeps_local_scheme_in_process
    _write_chain_module(tmp_path)
    test_worker_forwards_non_local_scheme_to_router(tmp_path;monkeypatch)
    test_worker_keeps_local_scheme_in_process(tmp_path;monkeypatch)
  urisysnode/__init__.py:
  urisysnode/app_data.py:
    e: default_app_chat_path,AppChatStore
    AppChatStore: __init__(1),append(3),list_messages(1),list_channels(0)
    default_app_chat_path()
  urisysnode/app_handlers.py:
    e: _store,query_chat_messages,command_chat_append,query_chat_channels
    _store(context)
    query_chat_messages(payload;context)
    command_chat_append(payload;context)
    query_chat_channels(payload;context)
  urisysnode/artifact_resolver.py:
    e: is_url,_auth_opener,fetch_json,fetch_text,_contract_yaml_block,parse_contract_spec,contract_url_from_release,contract_spec_from_release,load_node_profile,load_artifact_index,release_api_url,fetch_release,select_artifact,docker_pull,docker_run_worker,wait_health,resolve_and_run,run_release,resolve_from_release,_GitHubHeaderAuth
    _GitHubHeaderAuth: __init__(1),https_request(1)
    is_url(source)
    _auth_opener(for_url)
    fetch_json(url)
    fetch_text(url)
    _contract_yaml_block(contract_text)
    parse_contract_spec(contract_text)
    contract_url_from_release(release)
    contract_spec_from_release(release)
    load_node_profile(path)
    load_artifact_index(source)
    release_api_url(catalog_url;contract_id;version)
    fetch_release(catalog_url;contract_id;version)
    select_artifact(index;node_profile)
    docker_pull(ref)
    docker_run_worker(ref)
    wait_health(port;attempts;container)
    resolve_and_run(index_source;profile_path)
    run_release(release;profile_path)
    resolve_from_release(catalog_url;contract_id;version;profile_path)
  urisysnode/cli.py:
    e: main
    main(argv)
  urisysnode/client.py:
    e: discover_mdns,remote_call,call_via_route_map
    discover_mdns(timeout_s)
    remote_call(endpoint;uri;payload;context)
    call_via_route_map(uri)
  urisysnode/display_bootstrap.py:
    e: _ensure_session_env,_agent_url,_agent_up,_screencast_ready,_start_agent,_start_screencast,bootstrap_wayland_capture
    _ensure_session_env()
    _agent_url()
    _agent_up()
    _screencast_ready()
    _start_agent(port)
    _start_screencast()
    bootstrap_wayland_capture()
  urisysnode/env.py:
  urisysnode/forward.py:
    e: forward_call
    forward_call(payload;context)
  urisysnode/forward_config.py:
    e: _normalize_entry,load_forward_entries,wire_forward_packs,_normalize_release_entry,load_release_forward_entries,wire_release_forward_packs
    _normalize_entry(raw)
    load_forward_entries()
    wire_forward_packs(runtime;entries)
    _normalize_release_entry(raw)
    load_release_forward_entries()
    wire_release_forward_packs(runtime;entries)
  urisysnode/handlers.py:
    e: query_health,query_identity,command_indicator_on,command_indicator_off,query_packs,command_install_pack,_get_supervisor,command_spawn_worker,query_workers,command_restart_worker,command_stop_worker,command_register_forward
    query_health(payload;context)
    query_identity(payload;context)
    command_indicator_on(payload;context)
    command_indicator_off(payload;context)
    query_packs(payload;context)
    command_install_pack(payload;context)
    _get_supervisor(context)
    command_spawn_worker(payload;context)
    query_workers(payload;context)
    command_restart_worker(payload;context)
    command_stop_worker(payload;context)
    command_register_forward(payload;context)
  urisysnode/identity/__init__.py:
  urisysnode/identity/core.py:
    e: default_data_root,default_events_path,_data_dir,_identity_path,_hostname,load_identity,save_identity
    default_data_root()
    default_events_path()
    _data_dir()
    _identity_path()
    _hostname()
    load_identity()
    save_identity(data)
  urisysnode/identity/health.py:
    e: _detect_him_driver,_get_urisys_version,_get_uricontrol_version,_get_python_info,_get_pairing_info,_detect_him_driver,_get_him_driver,_get_config_source,_get_driver_info,_get_runtime_info,health_payload
    _detect_him_driver()
    _get_urisys_version()
    _get_uricontrol_version()
    _get_python_info()
    _get_pairing_info()
    _detect_him_driver()
    _get_him_driver(config)
    _get_config_source(config;config_path)
    _get_driver_info(config)
    _get_runtime_info(runtime)
    health_payload(version;runtime)
  urisysnode/identity/pairing.py:
    e: _pairing_path,load_pairing,save_pairing,enroll,set_remote_control,require_paired
    _pairing_path()
    load_pairing()
    save_pairing(data)
    enroll(controller;code;token)
    set_remote_control(active;message)
    require_paired(context)
  urisysnode/identity.py:
  urisysnode/pack_resolver.py:
    e: auto_install_enabled,pack_install_source,github_owner,github_wheel_url,resolve_pack_spec,pack_module,scheme_for_uri,pack_for_scheme,_pip_install,ensure_pip_specs,pack_install_specs,ensure_pack_pypi,ensure_boot_pack,ensure_real_deps,github_wheel_urls,import_pack_module,pack_importable
    auto_install_enabled()
    pack_install_source()
    github_owner()
    github_wheel_url(pack)
    resolve_pack_spec(pack)
    pack_module(pack)
    scheme_for_uri(uri)
    pack_for_scheme(scheme)
    _pip_install(specs)
    ensure_pip_specs(specs)
    pack_install_specs(pack;override_specs)
    ensure_pack_pypi(pack)
    ensure_boot_pack(pack)
    ensure_real_deps(pack)
    github_wheel_urls()
    import_pack_module(pack)
    pack_importable(pack)
  urisysnode/port/__init__.py:
  urisysnode/port/manager.py:
    e: _pids_on_port,_kill_pid,_worker_pids_from_state,_wait_port_free,_is_node_serve_process,_collect_takeover_targets,takeover_port
    _pids_on_port(port)
    _kill_pid(pid)
    _worker_pids_from_state()
    _wait_port_free(host;port)
    _is_node_serve_process(pid;port)
    _collect_takeover_targets(port;self_pid)
    takeover_port(host;port)
  urisysnode/port/utils.py:
    e: _pidfile_path,_pid_alive,_read_cmdline,_pids_serve_cmdline,_pids_on_port_ss,_fuser_kill_port
    _pidfile_path(port)
    _pid_alive(pid)
    _read_cmdline(pid)
    _pids_serve_cmdline(port)
    _pids_on_port_ss(port)
    _fuser_kill_port(port)
  urisysnode/release_verify.py:
    e: signature_required,canonical_digest,load_trusted_keys,_ed25519_verify,verify_release
    signature_required(context)
    canonical_digest(release)
    load_trusted_keys()
    _ed25519_verify(public_key_b64;message;signature_b64)
    verify_release(release)
  urisysnode/remote.py:
    e: default_route_map,default_nodes_registry,default_endpoint,default_wheel_host,health,wait_health,call_uri,pip_install,install_pack,spawn_worker,restart_worker,stop_worker,workers,schedule_restart,_restart_scheduled,build_wheel,serve_wheels,wheel_url,upgrade_lenovo_node,upgrade_lenovo_kv,main
    default_route_map()
    default_nodes_registry()
    default_endpoint()
    default_wheel_host()
    health()
    wait_health()
    call_uri(uri)
    pip_install(specs)
    install_pack(pack)
    spawn_worker(pack)
    restart_worker(name)
    stop_worker(name)
    workers()
    schedule_restart()
    _restart_scheduled(out)
    build_wheel(project_dir)
    serve_wheels(directory)
    wheel_url(wheel_path)
    upgrade_lenovo_node()
    upgrade_lenovo_kv()
    main(argv)
  urisysnode/router.py:
    e: load_route_map,_match_pattern,resolve_remote_route,rewrite_uri_for_slave,node_endpoint
    load_route_map(path)
    _match_pattern(pattern;uri)
    resolve_remote_route(uri;route_map)
    rewrite_uri_for_slave(uri;node_id;target_node)
    node_endpoint(route;nodes_registry)
  urisysnode/routes.py:
    e: register
    register(rt)
  urisysnode/runtime/__init__.py:
  urisysnode/runtime/builder.py:
    e: _extend_pack_paths,_pack_modules,_register_pack,build_runtime
    _extend_pack_paths()
    _pack_modules()
    _register_pack(rt;pack)
    build_runtime(config_path)
  urisysnode/runtime/config.py:
    e: resolve_node_config,_default_real_config
    resolve_node_config(config_path)
    _default_real_config()
  urisysnode/runtime/packs.py:
    e: _bootstrap_worker_packs,load_pack_into_runtime,ensure_pack_for_uri,apply_host_trust
    _bootstrap_worker_packs(rt)
    load_pack_into_runtime(runtime;pack)
    ensure_pack_for_uri(runtime;uri)
    apply_host_trust(runtime;uri;context)
  urisysnode/runtime.py:
  urisysnode/serve.py:
    e: _extend_pack_paths,_pack_modules,_register_pack,resolve_node_config,_default_real_config,build_runtime,_bootstrap_worker_packs,load_pack_into_runtime,isolation_mode,get_supervisor,ensure_isolated_pack,ensure_pack_for_uri,apply_host_trust,call_uri,register_forward_pack,_release_forward_spec,hotload_release_pack,_app_chat_store,_app_chat_get,_app_chat_post,make_handler,serve,_ReuseHTTPServer
    _ReuseHTTPServer:
    _extend_pack_paths()
    _pack_modules()
    _register_pack(rt;pack)
    resolve_node_config(config_path)
    _default_real_config()
    build_runtime(config_path)
    _bootstrap_worker_packs(rt)
    load_pack_into_runtime(runtime;pack)
    isolation_mode(context)
    get_supervisor(runtime)
    ensure_isolated_pack(runtime;uri;payload;context)
    ensure_pack_for_uri(runtime;uri)
    apply_host_trust(runtime;uri;context)
    call_uri(runtime;uri;payload;context)
    register_forward_pack(runtime;scheme;endpoint;patterns)
    _release_forward_spec(release;scheme;patterns)
    hotload_release_pack(runtime;contract_id;version)
    _app_chat_store(runtime)
    _app_chat_get(path;runtime)
    _app_chat_post(body;runtime)
    make_handler(runtime)
    serve(runtime;host;port)
  urisysnode/supervisor.py:
    e: _free_port,_http_get,_schemes_of,Worker,PackSupervisor
    Worker: alive(0),to_record(0)
    PackSupervisor: __init__(1),_default_worker_env(0),spawn(0),call_ephemeral(3),restart(1),_needs_install(1),stop(1),status(0),shutdown(0),start_monitor(1),_reap(0),restore(0),_wait_health(1),_fetch_patterns(1),_wire(1),_terminate(1),_persist(0)
    _free_port(host)
    _http_get(url;timeout)
    _schemes_of(patterns)
  urisysnode/worker.py:
    e: _load_node_profile,_local_schemes,_wire_router_callback,build_worker_runtime,serve_worker,main
    _load_node_profile()
    _local_schemes(runtime)
    _wire_router_callback(runtime)
    build_worker_runtime()
    serve_worker()
    main(argv)
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('urisys-node', '0.1.40', 'python').

% ── Project Files ────────────────────────────────────────
project_file('app.doql.less', 122, 'less').
project_file('docker/entrypoint.sh', 64, 'shell').
project_file('project.sh', 63, 'shell').
project_file('scripts/enable-host-trust.sh', 143, 'shell').
project_file('scripts/install-linux.sh', 17, 'shell').
project_file('tests/integration/_fakepack.py', 20, 'python').
project_file('tests/integration/test_artifact_resolver.py', 96, 'python').
project_file('tests/integration/test_core_pack_boot_install.py', 61, 'python').
project_file('tests/integration/test_docker_host_e2e.py', 157, 'python').
project_file('tests/integration/test_forward_config.py', 150, 'python').
project_file('tests/integration/test_forward_pack.py', 75, 'python').
project_file('tests/integration/test_host_trust.py', 57, 'python').
project_file('tests/integration/test_pack_auto_install.py', 112, 'python').
project_file('tests/integration/test_pack_github.py', 38, 'python').
project_file('tests/integration/test_pack_hotload.py', 65, 'python').
project_file('tests/integration/test_pack_office_mail.py', 30, 'python').
project_file('tests/integration/test_pack_rdpedge.py', 15, 'python').
project_file('tests/integration/test_pack_webrtc_hotload.py', 49, 'python').
project_file('tests/integration/test_release_hotload.py', 259, 'python').
project_file('tests/integration/test_serve_takeover.py', 74, 'python').
project_file('tests/integration/test_uriscreen_auto.py', 35, 'python').
project_file('tests/integration/test_urishell.py', 46, 'python').
project_file('tests/integration/test_urisys_node.py', 68, 'python').
project_file('tests/integration/test_worker_supervisor.py', 92, 'python').
project_file('tests/test_app_data.py', 61, 'python').
project_file('tests/test_health_profile_visibility.py', 40, 'python').
project_file('tests/test_import_urisysnode.py', 4, 'python').
project_file('tests/test_invalid_profile_tolerated.py', 47, 'python').
project_file('tests/test_node_config_discovery.py', 66, 'python').
project_file('tests/test_pack_resolver_browser.py', 26, 'python').
project_file('tests/test_pack_resolver_kv.py', 9, 'python').
project_file('tests/test_pack_resolver_webrtc.py', 9, 'python').
project_file('tests/test_remote_restart.py', 42, 'python').
project_file('tests/test_supervisor_worker_env.py', 24, 'python').
project_file('tests/test_worker_profile.py', 52, 'python').
project_file('tests/test_worker_router_callback.py', 67, 'python').
project_file('tree.sh', 2, 'shell').
project_file('urisysnode/__init__.py', 1, 'python').
project_file('urisysnode/app_data.py', 86, 'python').
project_file('urisysnode/app_handlers.py', 45, 'python').
project_file('urisysnode/artifact_resolver.py', 306, 'python').
project_file('urisysnode/cli.py', 197, 'python').
project_file('urisysnode/client.py', 93, 'python').
project_file('urisysnode/display_bootstrap.py', 115, 'python').
project_file('urisysnode/env.py', 6, 'python').
project_file('urisysnode/forward.py', 34, 'python').
project_file('urisysnode/forward_config.py', 145, 'python').
project_file('urisysnode/handlers.py', 155, 'python').
project_file('urisysnode/identity/__init__.py', 39, 'python').
project_file('urisysnode/identity/core.py', 82, 'python').
project_file('urisysnode/identity/health.py', 196, 'python').
project_file('urisysnode/identity/pairing.py', 101, 'python').
project_file('urisysnode/identity.py', 58, 'python').
project_file('urisysnode/pack_resolver.py', 324, 'python').
project_file('urisysnode/port/__init__.py', 36, 'python').
project_file('urisysnode/port/manager.py', 212, 'python').
project_file('urisysnode/port/utils.py', 93, 'python').
project_file('urisysnode/release_verify.py', 139, 'python').
project_file('urisysnode/remote.py', 517, 'python').
project_file('urisysnode/router.py', 53, 'python').
project_file('urisysnode/routes.py', 91, 'python').
project_file('urisysnode/runtime/__init__.py', 35, 'python').
project_file('urisysnode/runtime/builder.py', 170, 'python').
project_file('urisysnode/runtime/config.py', 53, 'python').
project_file('urisysnode/runtime/packs.py', 153, 'python').
project_file('urisysnode/runtime.py', 6, 'python').
project_file('urisysnode/serve.py', 857, 'python').
project_file('urisysnode/supervisor.py', 421, 'python').
project_file('urisysnode/worker.py', 187, 'python').

% ── Python Functions ─────────────────────────────────────
python_function('tests/integration/_fakepack.py', '_ping', 2, 1, 1).
python_function('tests/integration/_fakepack.py', 'register', 1, 1, 1).
python_function('tests/integration/test_artifact_resolver.py', 'test_select_artifact_by_platform', 1, 2, 4).
python_function('tests/integration/test_artifact_resolver.py', 'test_load_artifact_index_from_file', 1, 2, 3).
python_function('tests/integration/test_artifact_resolver.py', 'test_load_artifact_index_from_url', 0, 2, 2).
python_function('tests/integration/test_artifact_resolver.py', 'test_fetch_release', 0, 2, 3).
python_function('tests/integration/test_artifact_resolver.py', 'test_release_api_url', 0, 2, 1).
python_function('tests/integration/test_artifact_resolver.py', 'test_run_release_honors_artifact_container_port', 2, 4, 3).
python_function('tests/integration/test_core_pack_boot_install.py', '_screen_import_once_then_ok', 1, 3, 3).
python_function('tests/integration/test_core_pack_boot_install.py', 'test_core_pack_auto_install_on_boot', 1, 2, 5).
python_function('tests/integration/test_core_pack_boot_install.py', 'test_core_pack_boot_raises_when_auto_install_disabled', 1, 1, 6).
python_function('tests/integration/test_core_pack_boot_install.py', 'test_core_pack_boot_raises_when_pip_fails', 1, 1, 5).
python_function('tests/integration/test_docker_host_e2e.py', '_http_get', 1, 1, 4).
python_function('tests/integration/test_docker_host_e2e.py', '_remote_call', 3, 3, 7).
python_function('tests/integration/test_docker_host_e2e.py', 'docker_stack', 0, 7, 10).
python_function('tests/integration/test_docker_host_e2e.py', 'test_container_urisys_cli', 1, 3, 1).
python_function('tests/integration/test_docker_host_e2e.py', 'test_host_health_and_routes', 1, 5, 3).
python_function('tests/integration/test_docker_host_e2e.py', 'test_host_remote_identity', 1, 4, 5).
python_function('tests/integration/test_docker_host_e2e.py', 'test_host_screen_capture', 1, 5, 5).
python_function('tests/integration/test_docker_host_e2e.py', 'test_host_indicator_control', 0, 5, 2).
python_function('tests/integration/test_forward_config.py', '_runtime', 1, 1, 3).
python_function('tests/integration/test_forward_config.py', 'test_load_forward_entries_from_config', 0, 3, 2).
python_function('tests/integration/test_forward_config.py', 'test_load_forward_entries_env_inline', 0, 2, 3).
python_function('tests/integration/test_forward_config.py', 'test_wire_forward_packs_registers_routes', 1, 4, 4).
python_function('tests/integration/test_forward_config.py', 'test_command_register_forward', 1, 3, 2).
python_function('tests/integration/test_forward_config.py', 'test_load_release_forward_entries_from_config', 0, 5, 2).
python_function('tests/integration/test_forward_config.py', 'test_load_release_forward_entries_env_inline', 0, 2, 3).
python_function('tests/integration/test_forward_config.py', 'test_wire_release_forward_packs_calls_hotload', 2, 3, 4).
python_function('tests/integration/test_forward_config.py', 'test_wire_release_forward_packs_is_best_effort', 2, 2, 3).
python_function('tests/integration/test_forward_config.py', 'test_build_runtime_wires_config_forwards', 2, 2, 7).
python_function('tests/integration/test_forward_pack.py', '_runtime', 1, 1, 3).
python_function('tests/integration/test_forward_pack.py', 'test_register_forward_adds_routes_and_target', 1, 10, 6).
python_function('tests/integration/test_forward_pack.py', 'test_call_forwards_to_worker', 2, 7, 6).
python_function('tests/integration/test_forward_pack.py', 'test_forward_without_target_fails_cleanly', 1, 3, 4).
python_function('tests/integration/test_host_trust.py', '_runtime', 1, 2, 2).
python_function('tests/integration/test_host_trust.py', 'test_no_policy_keeps_caller_approval_default', 0, 3, 3).
python_function('tests/integration/test_host_trust.py', 'test_empty_list_grants_full_trust', 0, 3, 2).
python_function('tests/integration/test_host_trust.py', 'test_matching_pattern_still_requires_approval', 0, 3, 3).
python_function('tests/integration/test_host_trust.py', 'test_caller_can_still_approve_when_gated', 0, 2, 2).
python_function('tests/integration/test_pack_auto_install.py', '_node_only_runtime', 1, 1, 3).
python_function('tests/integration/test_pack_auto_install.py', 'test_install_pack_uri', 1, 2, 4).
python_function('tests/integration/test_pack_auto_install.py', 'test_install_pack_requires_approval', 1, 2, 2).
python_function('tests/integration/test_pack_auto_install.py', 'test_query_packs', 1, 4, 2).
python_function('tests/integration/test_pack_auto_install.py', 'test_call_uri_lazy_pack_route_not_found', 1, 3, 5).
python_function('tests/integration/test_pack_auto_install.py', 'test_load_pack_with_mock_pip', 1, 3, 3).
python_function('tests/integration/test_pack_auto_install.py', 'test_ensure_pack_for_uri_skips_pip_when_importable', 1, 2, 4).
python_function('tests/integration/test_pack_auto_install.py', 'test_force_reload_reregister_pack', 1, 4, 5).
python_function('tests/integration/test_pack_auto_install.py', 'test_pack_importable_uses_import_pack_module', 0, 3, 2).
python_function('tests/integration/test_pack_github.py', 'test_github_wheel_url_him', 0, 2, 1).
python_function('tests/integration/test_pack_github.py', 'test_resolve_pack_spec_auto_prefers_github_for_him', 0, 2, 2).
python_function('tests/integration/test_pack_github.py', 'test_resolve_pack_spec_kvm_stays_pypi', 0, 2, 1).
python_function('tests/integration/test_pack_github.py', 'test_github_wheel_url_stt', 0, 2, 1).
python_function('tests/integration/test_pack_github.py', 'test_github_wheel_url_webrtc', 0, 2, 1).
python_function('tests/integration/test_pack_hotload.py', '_node_only_runtime', 1, 1, 3).
python_function('tests/integration/test_pack_hotload.py', 'test_hotload_adds_routes', 1, 6, 4).
python_function('tests/integration/test_pack_hotload.py', 'test_hotload_is_idempotent', 1, 4, 3).
python_function('tests/integration/test_pack_hotload.py', 'test_hotload_empty_pack_name_rejected', 1, 2, 2).
python_function('tests/integration/test_pack_hotload.py', 'test_hotload_unknown_pack_reports_failure', 1, 3, 2).
python_function('tests/integration/test_pack_office_mail.py', 'test_scheme_to_pack_office_mail_vql', 0, 5, 1).
python_function('tests/integration/test_pack_office_mail.py', 'test_pack_modules_office_mail_vql', 0, 5, 1).
python_function('tests/integration/test_pack_rdpedge.py', 'test_pack_modules_rdpedge', 0, 6, 2).
python_function('tests/integration/test_pack_webrtc_hotload.py', '_node_only_runtime', 1, 1, 3).
python_function('tests/integration/test_pack_webrtc_hotload.py', 'test_hotload_webrtc_adds_routes', 2, 4, 5).
python_function('tests/integration/test_pack_webrtc_hotload.py', 'test_webrtc_session_start_after_hotload', 2, 3, 4).
python_function('tests/integration/test_release_hotload.py', '_runtime', 1, 1, 3).
python_function('tests/integration/test_release_hotload.py', '_release', 0, 1, 1).
python_function('tests/integration/test_release_hotload.py', 'test_canonical_digest_ignores_signature_block', 0, 2, 2).
python_function('tests/integration/test_release_hotload.py', 'test_disabled_policy_passes_through', 1, 4, 3).
python_function('tests/integration/test_release_hotload.py', 'test_required_but_unsigned_fails', 1, 3, 3).
python_function('tests/integration/test_release_hotload.py', 'test_required_untrusted_key_fails', 1, 3, 3).
python_function('tests/integration/test_release_hotload.py', 'test_required_no_crypto_backend_fails_closed', 1, 3, 5).
python_function('tests/integration/test_release_hotload.py', 'test_required_good_signature_verifies', 1, 4, 4).
python_function('tests/integration/test_release_hotload.py', 'test_required_mismatched_signature_fails', 1, 3, 4).
python_function('tests/integration/test_release_hotload.py', 'test_hotload_requires_pairing', 2, 4, 6).
python_function('tests/integration/test_release_hotload.py', 'test_hotload_happy_path_wires_forward', 2, 10, 10).
python_function('tests/integration/test_release_hotload.py', 'test_hotload_bad_signature_skips_run', 2, 3, 7).
python_function('tests/integration/test_release_hotload.py', 'test_hotload_missing_scheme_patterns', 2, 3, 8).
python_function('tests/integration/test_release_hotload.py', 'test_parse_contract_spec_extracts_scheme_and_patterns', 0, 3, 1).
python_function('tests/integration/test_release_hotload.py', 'test_parse_contract_spec_rejects_block_without_scheme', 0, 1, 2).
python_function('tests/integration/test_release_hotload.py', 'test_contract_url_from_release_variants', 0, 4, 1).
python_function('tests/integration/test_release_hotload.py', 'test_hotload_derives_spec_from_contract', 2, 7, 9).
python_function('tests/integration/test_serve_takeover.py', '_free_port', 0, 1, 3).
python_function('tests/integration/test_serve_takeover.py', '_wait_listen', 2, 3, 3).
python_function('tests/integration/test_serve_takeover.py', 'test_takeover_does_not_target_shell_wrappers', 0, 3, 4).
python_function('tests/integration/test_serve_takeover.py', 'test_takeover_kills_old_listener', 0, 7, 12).
python_function('tests/integration/test_uriscreen_auto.py', 'test_resolve_backend_auto_x11', 1, 2, 2).
python_function('tests/integration/test_uriscreen_auto.py', 'test_resolve_backend_auto_wayland', 1, 2, 2).
python_function('tests/integration/test_uriscreen_auto.py', 'test_is_black_png', 1, 3, 4).
python_function('tests/integration/test_urishell.py', 'test_shell_route_registered', 0, 2, 3).
python_function('tests/integration/test_urishell.py', 'test_shell_pip_dry_run', 0, 4, 3).
python_function('tests/integration/test_urishell.py', 'test_shell_requires_allow_real', 0, 3, 4).
python_function('tests/integration/test_urisys_node.py', 'test_identity_and_enroll', 0, 5, 3).
python_function('tests/integration/test_urisys_node.py', 'test_screen_capture_mock', 0, 4, 4).
python_function('tests/integration/test_urisys_node.py', 'test_rewrite_uri_for_slave', 0, 5, 1).
python_function('tests/integration/test_urisys_node.py', 'test_health_payload', 0, 6, 1).
python_function('tests/integration/test_urisys_node.py', 'test_health_payload_with_runtime', 0, 4, 2).
python_function('tests/integration/test_worker_supervisor.py', '_router', 1, 1, 3).
python_function('tests/integration/test_worker_supervisor.py', '_worker_env', 0, 1, 3).
python_function('tests/integration/test_worker_supervisor.py', 'test_build_worker_runtime_loads_module', 0, 3, 3).
python_function('tests/integration/test_worker_supervisor.py', 'test_supervisor_spawns_and_router_forwards', 1, 8, 9).
python_function('tests/integration/test_worker_supervisor.py', 'test_supervisor_restart_keeps_routes', 1, 5, 7).
python_function('tests/integration/test_worker_supervisor.py', 'test_supervisor_stop_terminates_worker', 1, 4, 6).
python_function('tests/test_app_data.py', 'chat_path', 2, 1, 3).
python_function('tests/test_app_data.py', 'test_append_and_list_messages', 1, 4, 4).
python_function('tests/test_app_data.py', 'test_list_channels', 1, 4, 3).
python_function('tests/test_app_data.py', 'test_uri_handlers', 1, 4, 3).
python_function('tests/test_health_profile_visibility.py', 'test_profile_loaded_is_visible', 0, 6, 4).
python_function('tests/test_health_profile_visibility.py', 'test_mock_when_no_profile', 0, 4, 2).
python_function('tests/test_health_profile_visibility.py', 'test_auto_default_source_visible', 0, 3, 2).
python_function('tests/test_import_urisysnode.py', 'test_import_urisysnode', 0, 2, 0).
python_function('tests/test_invalid_profile_tolerated.py', '_minimal_node', 2, 1, 4).
python_function('tests/test_invalid_profile_tolerated.py', 'test_empty_profile_does_not_crash', 2, 3, 4).
python_function('tests/test_invalid_profile_tolerated.py', 'test_garbage_profile_does_not_crash', 2, 2, 4).
python_function('tests/test_invalid_profile_tolerated.py', 'test_empty_profile_with_allow_real_uses_defaults', 2, 2, 5).
python_function('tests/test_node_config_discovery.py', 'test_env_var_wins', 2, 2, 7).
python_function('tests/test_node_config_discovery.py', 'test_discovers_xdg_profile_when_env_unset', 2, 2, 9).
python_function('tests/test_node_config_discovery.py', 'test_explicit_arg_beats_env', 2, 2, 5).
python_function('tests/test_node_config_discovery.py', 'test_returns_empty_when_none', 2, 2, 5).
python_function('tests/test_node_config_discovery.py', 'test_default_real_config_wayland', 1, 4, 3).
python_function('tests/test_node_config_discovery.py', 'test_default_real_config_x11', 1, 2, 3).
python_function('tests/test_pack_resolver_browser.py', 'test_browser_pack_mapping', 0, 5, 1).
python_function('tests/test_pack_resolver_browser.py', 'test_browser_github_wheel_url', 0, 3, 1).
python_function('tests/test_pack_resolver_browser.py', 'test_browser_importable_when_installed', 0, 2, 1).
python_function('tests/test_pack_resolver_kv.py', 'test_kv_and_log_scheme_mapping', 0, 5, 1).
python_function('tests/test_pack_resolver_webrtc.py', 'test_webrtc_scheme_mapping', 0, 5, 1).
python_function('tests/test_remote_restart.py', 'test_restart_scheduled_treats_connection_drop_as_ok', 0, 3, 1).
python_function('tests/test_remote_restart.py', 'test_schedule_restart_maps_connection_exception', 1, 3, 4).
python_function('tests/test_remote_restart.py', 'test_restart_scheduled_passes_through_real_errors', 0, 2, 1).
python_function('tests/test_remote_restart.py', 'test_schedule_restart_forwards_endpoint', 1, 3, 3).
python_function('tests/test_supervisor_worker_env.py', 'test_default_worker_env_uses_runtime_config_path', 2, 4, 11).
python_function('tests/test_worker_profile.py', '_write_fake_module', 1, 1, 1).
python_function('tests/test_worker_profile.py', 'test_worker_runtime_loads_profile', 2, 5, 9).
python_function('tests/test_worker_profile.py', 'test_missing_profile_is_empty_not_error', 2, 2, 5).
python_function('tests/test_worker_router_callback.py', '_write_chain_module', 1, 1, 1).
python_function('tests/test_worker_router_callback.py', 'test_worker_forwards_non_local_scheme_to_router', 2, 5, 8).
python_function('tests/test_worker_router_callback.py', 'test_worker_keeps_local_scheme_in_process', 2, 3, 8).
python_function('urisysnode/app_data.py', 'default_app_chat_path', 0, 2, 4).
python_function('urisysnode/app_handlers.py', '_store', 1, 4, 3).
python_function('urisysnode/app_handlers.py', 'query_chat_messages', 2, 5, 7).
python_function('urisysnode/app_handlers.py', 'command_chat_append', 2, 9, 6).
python_function('urisysnode/app_handlers.py', 'query_chat_channels', 2, 2, 5).
python_function('urisysnode/artifact_resolver.py', 'is_url', 1, 1, 1).
python_function('urisysnode/artifact_resolver.py', '_auth_opener', 1, 4, 7).
python_function('urisysnode/artifact_resolver.py', 'fetch_json', 1, 1, 6).
python_function('urisysnode/artifact_resolver.py', 'fetch_text', 1, 1, 5).
python_function('urisysnode/artifact_resolver.py', '_contract_yaml_block', 1, 6, 5).
python_function('urisysnode/artifact_resolver.py', 'parse_contract_spec', 1, 12, 7).
python_function('urisysnode/artifact_resolver.py', 'contract_url_from_release', 1, 6, 3).
python_function('urisysnode/artifact_resolver.py', 'contract_spec_from_release', 1, 2, 4).
python_function('urisysnode/artifact_resolver.py', 'load_node_profile', 1, 3, 4).
python_function('urisysnode/artifact_resolver.py', 'load_artifact_index', 1, 3, 8).
python_function('urisysnode/artifact_resolver.py', 'release_api_url', 3, 1, 2).
python_function('urisysnode/artifact_resolver.py', 'fetch_release', 3, 5, 6).
python_function('urisysnode/artifact_resolver.py', 'select_artifact', 2, 15, 6).
python_function('urisysnode/artifact_resolver.py', 'docker_pull', 1, 4, 3).
python_function('urisysnode/artifact_resolver.py', 'docker_run_worker', 1, 3, 3).
python_function('urisysnode/artifact_resolver.py', 'wait_health', 3, 4, 6).
python_function('urisysnode/artifact_resolver.py', 'resolve_and_run', 2, 4, 9).
python_function('urisysnode/artifact_resolver.py', 'run_release', 2, 8, 10).
python_function('urisysnode/artifact_resolver.py', 'resolve_from_release', 4, 1, 2).
python_function('urisysnode/cli.py', 'main', 1, 22, 33).
python_function('urisysnode/client.py', 'discover_mdns', 1, 2, 12).
python_function('urisysnode/client.py', 'remote_call', 4, 3, 8).
python_function('urisysnode/client.py', 'call_via_route_map', 1, 6, 12).
python_function('urisysnode/display_bootstrap.py', '_ensure_session_env', 0, 5, 6).
python_function('urisysnode/display_bootstrap.py', '_agent_url', 0, 1, 2).
python_function('urisysnode/display_bootstrap.py', '_agent_up', 0, 2, 2).
python_function('urisysnode/display_bootstrap.py', '_screencast_ready', 0, 4, 7).
python_function('urisysnode/display_bootstrap.py', '_start_agent', 1, 4, 9).
python_function('urisysnode/display_bootstrap.py', '_start_screencast', 0, 5, 6).
python_function('urisysnode/display_bootstrap.py', 'bootstrap_wayland_capture', 0, 7, 10).
python_function('urisysnode/forward.py', 'forward_call', 2, 9, 5).
python_function('urisysnode/forward_config.py', '_normalize_entry', 1, 11, 4).
python_function('urisysnode/forward_config.py', 'load_forward_entries', 0, 15, 11).
python_function('urisysnode/forward_config.py', 'wire_forward_packs', 2, 2, 2).
python_function('urisysnode/forward_config.py', '_normalize_release_entry', 1, 11, 4).
python_function('urisysnode/forward_config.py', 'load_release_forward_entries', 0, 11, 9).
python_function('urisysnode/forward_config.py', 'wire_release_forward_packs', 2, 3, 3).
python_function('urisysnode/handlers.py', 'query_health', 2, 1, 2).
python_function('urisysnode/handlers.py', 'query_identity', 2, 2, 4).
python_function('urisysnode/handlers.py', 'command_indicator_on', 2, 1, 3).
python_function('urisysnode/handlers.py', 'command_indicator_off', 2, 1, 2).
python_function('urisysnode/handlers.py', 'query_packs', 2, 2, 6).
python_function('urisysnode/handlers.py', 'command_install_pack', 2, 6, 6).
python_function('urisysnode/handlers.py', '_get_supervisor', 1, 2, 2).
python_function('urisysnode/handlers.py', 'command_spawn_worker', 2, 11, 8).
python_function('urisysnode/handlers.py', 'query_workers', 2, 2, 2).
python_function('urisysnode/handlers.py', 'command_restart_worker', 2, 6, 5).
python_function('urisysnode/handlers.py', 'command_stop_worker', 2, 6, 5).
python_function('urisysnode/handlers.py', 'command_register_forward', 2, 7, 5).
python_function('urisysnode/identity/core.py', 'default_data_root', 0, 3, 3).
python_function('urisysnode/identity/core.py', 'default_events_path', 0, 2, 3).
python_function('urisysnode/identity/core.py', '_data_dir', 0, 1, 2).
python_function('urisysnode/identity/core.py', '_identity_path', 0, 1, 1).
python_function('urisysnode/identity/core.py', '_hostname', 0, 1, 1).
python_function('urisysnode/identity/core.py', 'load_identity', 0, 4, 14).
python_function('urisysnode/identity/core.py', 'save_identity', 1, 1, 3).
python_function('urisysnode/identity/health.py', '_detect_him_driver', 0, 3, 2).
python_function('urisysnode/identity/health.py', '_get_urisys_version', 0, 2, 1).
python_function('urisysnode/identity/health.py', '_get_uricontrol_version', 0, 2, 1).
python_function('urisysnode/identity/health.py', '_get_python_info', 0, 1, 0).
python_function('urisysnode/identity/health.py', '_get_pairing_info', 0, 1, 3).
python_function('urisysnode/identity/health.py', '_detect_him_driver', 0, 3, 3).
python_function('urisysnode/identity/health.py', '_get_him_driver', 1, 6, 3).
python_function('urisysnode/identity/health.py', '_get_config_source', 2, 6, 2).
python_function('urisysnode/identity/health.py', '_get_driver_info', 1, 7, 2).
python_function('urisysnode/identity/health.py', '_get_runtime_info', 1, 7, 8).
python_function('urisysnode/identity/health.py', 'health_payload', 2, 4, 10).
python_function('urisysnode/identity/pairing.py', '_pairing_path', 0, 1, 1).
python_function('urisysnode/identity/pairing.py', 'load_pairing', 0, 3, 5).
python_function('urisysnode/identity/pairing.py', 'save_pairing', 1, 1, 3).
python_function('urisysnode/identity/pairing.py', 'enroll', 3, 3, 4).
python_function('urisysnode/identity/pairing.py', 'set_remote_control', 2, 2, 2).
python_function('urisysnode/identity/pairing.py', 'require_paired', 1, 4, 3).
python_function('urisysnode/pack_resolver.py', 'auto_install_enabled', 0, 1, 1).
python_function('urisysnode/pack_resolver.py', 'pack_install_source', 0, 1, 3).
python_function('urisysnode/pack_resolver.py', 'github_owner', 0, 1, 2).
python_function('urisysnode/pack_resolver.py', 'github_wheel_url', 1, 4, 4).
python_function('urisysnode/pack_resolver.py', 'resolve_pack_spec', 1, 10, 3).
python_function('urisysnode/pack_resolver.py', 'pack_module', 1, 1, 1).
python_function('urisysnode/pack_resolver.py', 'scheme_for_uri', 1, 2, 2).
python_function('urisysnode/pack_resolver.py', 'pack_for_scheme', 1, 1, 1).
python_function('urisysnode/pack_resolver.py', '_pip_install', 1, 4, 4).
python_function('urisysnode/pack_resolver.py', 'ensure_pip_specs', 1, 4, 2).
python_function('urisysnode/pack_resolver.py', 'pack_install_specs', 2, 8, 4).
python_function('urisysnode/pack_resolver.py', 'ensure_pack_pypi', 1, 3, 3).
python_function('urisysnode/pack_resolver.py', 'ensure_boot_pack', 1, 7, 5).
python_function('urisysnode/pack_resolver.py', 'ensure_real_deps', 1, 1, 2).
python_function('urisysnode/pack_resolver.py', 'github_wheel_urls', 0, 6, 2).
python_function('urisysnode/pack_resolver.py', 'import_pack_module', 1, 1, 2).
python_function('urisysnode/pack_resolver.py', 'pack_importable', 1, 2, 1).
python_function('urisysnode/port/manager.py', '_pids_on_port', 1, 16, 14).
python_function('urisysnode/port/manager.py', '_kill_pid', 1, 9, 6).
python_function('urisysnode/port/manager.py', '_worker_pids_from_state', 0, 10, 10).
python_function('urisysnode/port/manager.py', '_wait_port_free', 2, 4, 6).
python_function('urisysnode/port/manager.py', '_is_node_serve_process', 2, 16, 9).
python_function('urisysnode/port/manager.py', '_collect_takeover_targets', 2, 12, 11).
python_function('urisysnode/port/manager.py', 'takeover_port', 2, 6, 9).
python_function('urisysnode/port/utils.py', '_pidfile_path', 1, 1, 2).
python_function('urisysnode/port/utils.py', '_pid_alive', 1, 2, 1).
python_function('urisysnode/port/utils.py', '_read_cmdline', 1, 2, 5).
python_function('urisysnode/port/utils.py', '_pids_serve_cmdline', 1, 7, 8).
python_function('urisysnode/port/utils.py', '_pids_on_port_ss', 1, 5, 5).
python_function('urisysnode/port/utils.py', '_fuser_kill_port', 1, 4, 2).
python_function('urisysnode/release_verify.py', 'signature_required', 1, 3, 1).
python_function('urisysnode/release_verify.py', 'canonical_digest', 1, 3, 5).
python_function('urisysnode/release_verify.py', 'load_trusted_keys', 0, 6, 11).
python_function('urisysnode/release_verify.py', '_ed25519_verify', 3, 3, 4).
python_function('urisysnode/release_verify.py', 'verify_release', 1, 14, 8).
python_function('urisysnode/remote.py', 'default_route_map', 0, 1, 4).
python_function('urisysnode/remote.py', 'default_nodes_registry', 0, 1, 4).
python_function('urisysnode/remote.py', 'default_endpoint', 0, 1, 2).
python_function('urisysnode/remote.py', 'default_wheel_host', 0, 1, 2).
python_function('urisysnode/remote.py', 'health', 0, 2, 5).
python_function('urisysnode/remote.py', 'wait_health', 0, 4, 6).
python_function('urisysnode/remote.py', 'call_uri', 1, 4, 4).
python_function('urisysnode/remote.py', 'pip_install', 1, 1, 1).
python_function('urisysnode/remote.py', 'install_pack', 1, 2, 1).
python_function('urisysnode/remote.py', 'spawn_worker', 1, 4, 1).
python_function('urisysnode/remote.py', 'restart_worker', 1, 1, 1).
python_function('urisysnode/remote.py', 'stop_worker', 1, 1, 1).
python_function('urisysnode/remote.py', 'workers', 0, 1, 1).
python_function('urisysnode/remote.py', 'schedule_restart', 0, 2, 2).
python_function('urisysnode/remote.py', '_restart_scheduled', 1, 5, 4).
python_function('urisysnode/remote.py', 'build_wheel', 1, 3, 9).
python_function('urisysnode/remote.py', 'serve_wheels', 1, 1, 2).
python_function('urisysnode/remote.py', 'wheel_url', 1, 2, 2).
python_function('urisysnode/remote.py', 'upgrade_lenovo_node', 0, 7, 19).
python_function('urisysnode/remote.py', 'upgrade_lenovo_kv', 0, 4, 15).
python_function('urisysnode/remote.py', 'main', 1, 26, 24).
python_function('urisysnode/router.py', 'load_route_map', 1, 3, 4).
python_function('urisysnode/router.py', '_match_pattern', 2, 1, 3).
python_function('urisysnode/router.py', 'resolve_remote_route', 2, 5, 2).
python_function('urisysnode/router.py', 'rewrite_uri_for_slave', 3, 8, 4).
python_function('urisysnode/router.py', 'node_endpoint', 2, 5, 1).
python_function('urisysnode/routes.py', 'register', 1, 1, 1).
python_function('urisysnode/runtime/builder.py', '_extend_pack_paths', 0, 1, 0).
python_function('urisysnode/runtime/builder.py', '_pack_modules', 0, 1, 1).
python_function('urisysnode/runtime/builder.py', '_register_pack', 2, 14, 9).
python_function('urisysnode/runtime/builder.py', 'build_runtime', 1, 18, 24).
python_function('urisysnode/runtime/config.py', 'resolve_node_config', 1, 7, 9).
python_function('urisysnode/runtime/config.py', '_default_real_config', 0, 4, 3).
python_function('urisysnode/runtime/packs.py', '_bootstrap_worker_packs', 1, 7, 9).
python_function('urisysnode/runtime/packs.py', 'load_pack_into_runtime', 2, 30, 19).
python_function('urisysnode/runtime/packs.py', 'ensure_pack_for_uri', 2, 3, 6).
python_function('urisysnode/runtime/packs.py', 'apply_host_trust', 3, 10, 6).
python_function('urisysnode/serve.py', '_extend_pack_paths', 0, 1, 0).
python_function('urisysnode/serve.py', '_pack_modules', 0, 1, 1).
python_function('urisysnode/serve.py', '_register_pack', 2, 14, 9).
python_function('urisysnode/serve.py', 'resolve_node_config', 1, 7, 9).
python_function('urisysnode/serve.py', '_default_real_config', 0, 4, 3).
python_function('urisysnode/serve.py', 'build_runtime', 1, 18, 24).
python_function('urisysnode/serve.py', '_bootstrap_worker_packs', 1, 7, 9).
python_function('urisysnode/serve.py', 'load_pack_into_runtime', 2, 30, 19).
python_function('urisysnode/serve.py', 'isolation_mode', 1, 6, 4).
python_function('urisysnode/serve.py', 'get_supervisor', 1, 2, 3).
python_function('urisysnode/serve.py', 'ensure_isolated_pack', 4, 9, 12).
python_function('urisysnode/serve.py', 'ensure_pack_for_uri', 2, 3, 6).
python_function('urisysnode/serve.py', 'apply_host_trust', 3, 10, 6).
python_function('urisysnode/serve.py', 'call_uri', 4, 22, 13).
python_function('urisysnode/serve.py', 'register_forward_pack', 4, 13, 7).
python_function('urisysnode/serve.py', '_release_forward_spec', 3, 11, 4).
python_function('urisysnode/serve.py', 'hotload_release_pack', 3, 14, 10).
python_function('urisysnode/serve.py', '_app_chat_store', 1, 2, 2).
python_function('urisysnode/serve.py', '_app_chat_get', 2, 10, 8).
python_function('urisysnode/serve.py', '_app_chat_post', 2, 9, 6).
python_function('urisysnode/serve.py', 'make_handler', 1, 2, 27).
python_function('urisysnode/serve.py', 'serve', 3, 16, 24).
python_function('urisysnode/supervisor.py', '_free_port', 1, 1, 3).
python_function('urisysnode/supervisor.py', '_http_get', 2, 1, 4).
python_function('urisysnode/supervisor.py', '_schemes_of', 1, 4, 3).
python_function('urisysnode/worker.py', '_load_node_profile', 0, 5, 5).
python_function('urisysnode/worker.py', '_local_schemes', 1, 4, 4).
python_function('urisysnode/worker.py', '_wire_router_callback', 1, 3, 7).
python_function('urisysnode/worker.py', 'build_worker_runtime', 0, 5, 13).
python_function('urisysnode/worker.py', 'serve_worker', 0, 5, 10).
python_function('urisysnode/worker.py', 'main', 1, 4, 7).

% ── Python Classes ───────────────────────────────────────
python_class('tests/test_health_profile_visibility.py', '_RT').
python_method('_RT', '__init__', 2, 1, 0).
python_class('urisysnode/app_data.py', 'AppChatStore').
python_method('AppChatStore', '__init__', 1, 2, 3).
python_method('AppChatStore', 'append', 3, 2, 7).
python_method('AppChatStore', 'list_messages', 1, 7, 10).
python_method('AppChatStore', 'list_channels', 0, 9, 12).
python_class('urisysnode/artifact_resolver.py', '_GitHubHeaderAuth').
python_method('_GitHubHeaderAuth', '__init__', 1, 1, 0).
python_method('_GitHubHeaderAuth', 'https_request', 1, 1, 1).
python_class('urisysnode/serve.py', '_ReuseHTTPServer').
python_class('urisysnode/supervisor.py', 'Worker').
python_method('Worker', 'alive', 0, 3, 2).
python_method('Worker', 'to_record', 0, 2, 0).
python_class('urisysnode/supervisor.py', 'PackSupervisor').
python_method('PackSupervisor', '__init__', 1, 3, 3).
python_method('PackSupervisor', '_default_worker_env', 0, 8, 9).
python_method('PackSupervisor', 'spawn', 0, 15, 16).
python_method('PackSupervisor', 'call_ephemeral', 3, 16, 14).
python_method('PackSupervisor', 'restart', 1, 2, 3).
python_method('PackSupervisor', '_needs_install', 1, 3, 1).
python_method('PackSupervisor', 'stop', 1, 2, 3).
python_method('PackSupervisor', 'status', 0, 2, 3).
python_method('PackSupervisor', 'shutdown', 0, 2, 4).
python_method('PackSupervisor', 'start_monitor', 1, 3, 6).
python_method('PackSupervisor', '_reap', 0, 3, 5).
python_method('PackSupervisor', 'restore', 0, 11, 13).
python_method('PackSupervisor', '_wait_health', 1, 5, 4).
python_method('PackSupervisor', '_fetch_patterns', 1, 3, 3).
python_method('PackSupervisor', '_wire', 1, 2, 4).
python_method('PackSupervisor', '_terminate', 1, 4, 3).
python_method('PackSupervisor', '_persist', 0, 3, 5).

% ── Dependencies ─────────────────────────────────────────

% ── Makefile Targets ─────────────────────────────────────
makefile_target('help', '').
makefile_target('install', '').
makefile_target('test', '').
makefile_target('test-all', '').
makefile_target('test-integration', '').
makefile_target('test-coverage', '').
makefile_target('test-watch', '').
makefile_target('serve', '').
makefile_target('health', '').
makefile_target('app-chat-smoke', '').
makefile_target('publish', 'Release helpers').
makefile_target('publish-test', '').
makefile_target('version', '').

% ── Taskfile Tasks ───────────────────────────────────────

% ── Environment Variables ────────────────────────────────
env_variable('OPENROUTER_API_KEY', '*(not set)*', 'Required: OpenRouter API key (https://openrouter.ai/keys)').
env_variable('LLM_MODEL', 'openrouter/qwen/qwen3-coder-next', 'Model (default: openrouter/qwen/qwen3-coder-next)').
env_variable('PFIX_AUTO_APPLY', 'true', 'true = apply fixes without asking').
env_variable('PFIX_AUTO_INSTALL_DEPS', 'true', 'true = auto pip/uv install').
env_variable('PFIX_AUTO_RESTART', 'false', 'true = os.execv restart after fix').
env_variable('PFIX_MAX_RETRIES', '3', '').
env_variable('PFIX_DRY_RUN', 'false', '').
env_variable('PFIX_ENABLED', 'true', '').
env_variable('PFIX_GIT_COMMIT', 'false', 'true = auto-commit fixes').
env_variable('PFIX_GIT_PREFIX', 'pfix:', 'commit message prefix').
env_variable('PFIX_CREATE_BACKUPS', 'false', 'false = disable .pfix_backups/ directory').

% ── TestQL Scenarios ─────────────────────────────────────
testql_scenario('generated-cli-tests.testql.toon.yaml', 'cli').
testql_scenario('generated-from-pytests.testql.toon.yaml', 'integration').

% ── Semantic Facts from SUMD.md ──────────────────────────
sumd_declared_file('app.doql.less', 'doql').
sumd_declared_file('testql-scenarios/generated-cli-tests.testql.toon.yaml', 'testql').
sumd_declared_file('testql-scenarios/generated-from-pytests.testql.toon.yaml', 'testql').
sumd_declared_file('project/map.toon.yaml', 'analysis').
sumd_declared_file('project/logic.pl', 'analysis').
sumd_declared_file('project/calls.toon.yaml', 'analysis').
sumd_interface('cli', 'argparse').
sumd_interface('cli', '').
sumd_workflow('install', 'manual').
sumd_workflow_step('install', 1, '$(PYTHON) -m pip install -e .').
sumd_workflow('test', 'manual').
sumd_workflow_step('test', 1, '$(PYTHON) -m pytest -q').
sumd_workflow('test-all', 'manual').
sumd_workflow_step('test-all', 1, '$(PYTHON) -m pytest -v').
sumd_workflow('test-integration', 'manual').
sumd_workflow_step('test-integration', 1, '$(PYTHON) -m pytest tests/integration/ -v').
sumd_workflow('test-coverage', 'manual').
sumd_workflow_step('test-coverage', 1, '.venv/bin/pip install -q pytest-cov > /dev/null 2>&1 || true').
sumd_workflow_step('test-coverage', 2, '$(PYTHON) -m pytest --cov=urisysnode --cov-report=term-missing -v').
sumd_workflow('test-watch', 'manual').
sumd_workflow_step('test-watch', 1, '.venv/bin/pip install -q pytest-watch > /dev/null 2>&1 || true').
sumd_workflow_step('test-watch', 2, '$(PYTHON) -m ptw tests/ --pattern "test_*.py" --ignore "tests/integration/"').
sumd_workflow('serve', 'manual').
sumd_workflow_step('serve', 1, 'URISYS_NODE_SKIP_PAIRING=1 urisys-node serve --host 0.0.0.0 --port $(PORT)').
sumd_workflow('health', 'manual').
sumd_workflow_step('health', 1, 'curl -fsS "http://127.0.0.1:$(PORT)/health" | $(PYTHON) -m json.tool | head -15').
sumd_workflow('app-chat-smoke', 'manual').
sumd_workflow_step('app-chat-smoke', 1, 'curl -fsS -X POST "http://127.0.0.1:$(PORT)/app/chat/messages" \').
sumd_workflow_step('app-chat-smoke', 2, '-H \'Content-Type: application/json\' \').
sumd_workflow('publish', 'manual').
sumd_workflow_step('publish', 1, 'echo "📦 Publishing to PyPI..."').
sumd_workflow_step('publish', 2, 'command -v .venv/bin/twine > /dev/null 2>&1 || (.venv/bin/pip install --upgrade twine build)').
sumd_workflow_step('publish', 3, 'rm -rf dist/ build/ *.egg-info/').
sumd_workflow_step('publish', 4, '.venv/bin/python -m build').
sumd_workflow_step('publish', 5, '.venv/bin/twine check dist/*').
sumd_workflow_step('publish', 6, 'echo "🚀 Uploading to PyPI..."').
sumd_workflow_step('publish', 7, '.venv/bin/twine upload dist/*').
sumd_workflow('publish-test', 'manual').
sumd_workflow_step('publish-test', 1, 'echo "📦 Publishing to TestPyPI..."').
sumd_workflow_step('publish-test', 2, 'command -v .venv/bin/twine > /dev/null 2>&1 || (.venv/bin/pip install --upgrade twine build)').
sumd_workflow_step('publish-test', 3, 'rm -rf dist/ build/ *.egg-info/').
sumd_workflow_step('publish-test', 4, '.venv/bin/python -m build').
sumd_workflow_step('publish-test', 5, '.venv/bin/twine upload --repository testpypi dist/*').
sumd_workflow('version', 'manual').
sumd_workflow_step('version', 1, 'echo "📦 Version information..."').
sumd_workflow_step('version', 2, 'cat VERSION').
sumd_workflow_step('version', 3, '.venv/bin/python -c "from importlib.metadata import version').
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

## Intent

urisys-node slave: screen/kvm/him URI server components
