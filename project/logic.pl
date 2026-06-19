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
project_file('tests/integration/test_pack_auto_install.py', 117, 'python').
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

