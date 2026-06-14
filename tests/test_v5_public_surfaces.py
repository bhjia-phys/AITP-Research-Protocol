from __future__ import annotations


def test_public_surface_registry_names_all_runtime_facing_payloads():
    from brain.v5.public_surfaces import public_surface_names

    assert set(public_surface_names()) == {
        "adapter_packet",
        "adapter_protocol_registry",
        "artifact_record",
        "bounded_numerical_evidence_bundle",
        "claim_status_record",
        "claim_relation_map",
        "claim_trust_audit",
        "claude_code_hook_installation",
        "claude_code_hook_settings",
        "codex_hook_bridge",
        "codex_hook_installation",
        "code_state_record",
        "curated_rag_chunk",
        "curated_rag_corpus",
        "curated_rag_ingest_result",
        "evidence_record",
        "curated_rag_promotion_draft",
        "curated_rag_search_result",
        "execution_brief",
        "exploratory_record",
        "failure_mode_audit",
        "failure_mode_review_packet",
        "failure_mode_review_result_record",
        "final_engineering_readiness_audit",
        "final_output_profile",
        "human_checkpoint_record",
        "hook_trace_event_record",
        "interaction_recording_preview",
        "interaction_recording_worklist",
        "workspace_interaction_preview_bundle",
        "literature_comparison_draft",
        "literature_intake_record_result",
        "literature_intake_suggestion",
        "literature_source_review_handoff",
            "kimi_code_hook_config",
            "kimi_code_hook_installation",
            "knowledge_connector_catalog",
        "lane_exemplar_manifest",
        "lane_exemplar_record",
        "l2_obsidian_view_bundle",
        "l2_memory_audit",
        "legacy_executable_evidence_packet",
        "legacy_human_checkpoint_obsidian_view_bundle",
        "legacy_human_checkpoint_packet",
        "legacy_topic_question_backfill_packet",
        "canonical_legacy_l2_seed_audit",
        "legacy_l2_graph_manifest",
        "legacy_l2_obsidian_view_bundle",
        "legacy_l2_typed_migration_packet",
        "legacy_migration_coverage_audit",
        "legacy_migration_result",
        "legacy_runtime_log_marker_audit",
        "legacy_source_metadata_repair_packet",
        "legacy_source_reconstruction_apply",
        "legacy_source_reconstruction_manifest",
        "legacy_source_reconstruction_obsidian_view_bundle",
        "legacy_source_reconstruction_plan",
        "legacy_source_reconstruction_review_packet",
        "legacy_semantic_needs_revision_basis_obsidian_view_bundle",
        "legacy_semantic_needs_revision_basis_packet",
        "legacy_semantic_needs_revision_basis_queue",
        "legacy_semantic_review_manifest",
        "legacy_semantic_review_obsidian_view_bundle",
        "legacy_semantic_review_packet",
        "legacy_semantic_review_worklist",
        "legacy_semantic_repair_apply",
        "legacy_semantic_repair_manifest",
        "legacy_semantic_repair_plan",
        "legacy_semantic_review_result_record",
        "legacy_semantic_review_queue",
        "memory_entry_record",
        "object_relation_record",
        "operator_checkpoint_record",
        "opencode_hook_installation",
        "opencode_plugin_bridge",
        "host_agnostic_moment_policy",
        "physics_object_record",
        "pre_tool_policy_decision",
        "process_graph_slice",
        "promotion_packet_record",
        "proof_obligation_record",
        "qsgw_cockpit_bundle",
        "record_gate_coverage_audit",
        "record_ref_lookup",
        "reference_location_record",
        "research_route_record",
        "research_event_classification",
        "research_cockpit_bundle",
        "research_intent_packet",
        "research_run_event_record",
        "research_run_record",
        "run_iteration_record",
        "runtime_hook_installation_audit",
        "runtime_host_lifecycle_audit",
        "runtime_host_production_loop_audit",
        "runtime_host_readiness_audit",
        "runtime_bridge_target_manifest",
        "runtime_payload_profiles",
        "runtime_hook_installation_paths",
        "runtime_hook_smoke_coverage",
        "sensemaking_report_record",
        "session_summary_bundle",
        "source_reconstruction_audit",
        "source_asset_record",
        "source_stack_coverage_manifest",
        "source_reconstruction_manifest",
        "source_reconstruction_obsidian_view_bundle",
        "source_reconstruction_review_manifest",
        "source_reconstruction_review_packet",
        "source_reconstruction_review_result_record",
        "steering_decision_record",
        "strategy_memory_record",
        "summary_orientation",
        "tool_executor_catalog",
        "topic_status_bundle",
        "tool_recipe_record",
        "tool_run_record",
        "trust_update_record",
        "trust_update_apply",
        "trust_update_preflight",
        "validation_contract_record",
        "validation_result_record",
        "vnext_readiness_manifest",
        "workspace_file_migration_ledger",
        "workspace_file_migration_ledger_progress",
        "workspace_old_store_import_result",
        "workspace_replay_packet",
        "workspace_recovery_audit",
        "workspace_recovery_audit_progress",
        "workspace_recovery_binding_repair",
        "workspace_refresh_bundle",
        "workspace_summary_bundle",
        "goal_continuation_packet",
        "goal_continuation_list",
    }


def test_public_surface_validator_accepts_valid_adapter_registry():
    from brain.v5.adapter_protocols import adapter_protocol_registry
    from brain.v5.public_surfaces import require_valid_public_surface

    registry = adapter_protocol_registry()

    assert require_valid_public_surface("adapter_protocol_registry", registry) == registry


def test_public_surface_validator_accepts_tool_executor_catalog():
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.tool_executors import describe_tool_executors

    catalog = describe_tool_executors()

    assert require_valid_public_surface("tool_executor_catalog", catalog) == catalog


def test_public_surface_validator_accepts_codex_hook_bridge():
    from brain.v5.adapter_protocols import mandatory_gate_protocols
    from brain.v5.hook_entrypoint_schemas import (
        pre_tool_event_platform_schema,
        pre_tool_policy_input_schema,
    )
    from brain.v5.public_surfaces import require_valid_public_surface

    bridge = {
        "ok": True,
        "kind": "codex_hook_bridge",
        "runtime": "codex",
        "source_protocol_field": "runtime_hook_installation",
        "installation_mode": "explicit_guard_calls",
        "native_installer_available": False,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "pre_tool_policy_entrypoint": {
            "cli": "aitp-v5 policy pre-tool <args>",
            "mcp": "aitp_v5_evaluate_pre_tool_policy",
            "surface": "pre_tool_policy_decision",
            "truth_source": "typed_records",
            "summary_inputs_trusted": False,
            "can_update_kernel_state": False,
            "can_update_claim_trust": False,
            "input_schema": pre_tool_policy_input_schema(),
        },
        "pre_tool_event_entrypoint": {
            "cli": "aitp-v5 adapter pre-tool-event <runtime> <session-id> <args>",
            "mcp": "aitp_v5_evaluate_adapter_pre_tool_event",
            "surface": "pre_tool_policy_decision",
            "truth_source": "typed_records",
            "summary_inputs_trusted": False,
            "can_update_kernel_state": False,
            "can_update_claim_trust": False,
            "requires_bridge_payload": True,
            "requires_platform_event": True,
            "platform_event_schema": pre_tool_event_platform_schema(),
        },
        "gate_protocols": {
            "source_protocol_field": "runtime_gate_protocols",
            **mandatory_gate_protocols(),
        },
        "path": "AITP_V5_HOOK_BRIDGE.md",
        "guard_calls": [
            {
                "hook_name": "pre_tool",
                "when": "before trust-changing actions",
                "command": "python hooks/aitp_v5_hook.py pre-tool",
                "required_inputs": ["action", "risk_level", "policy_json"],
                "output_kind": "hook_decision",
                "may_block": True,
                "state_mutation": "none",
            }
        ],
    }

    assert require_valid_public_surface("codex_hook_bridge", bridge) == bridge


def test_public_surface_validator_rejects_codex_hook_bridge_without_gate_protocols():
    import pytest

    from brain.v5.contracts import ContractError
    from brain.v5.public_surfaces import require_valid_public_surface

    with pytest.raises(ContractError) as error:
        require_valid_public_surface(
            "codex_hook_bridge",
            {
                "ok": True,
                "kind": "codex_hook_bridge",
                "runtime": "codex",
                "source_protocol_field": "runtime_hook_installation",
                "installation_mode": "explicit_guard_calls",
                "native_installer_available": False,
                "summary_inputs_trusted": False,
                "can_update_kernel_state": False,
                "pre_tool_policy_entrypoint": {
                    "cli": "aitp-v5 policy pre-tool <args>",
                    "mcp": "aitp_v5_evaluate_pre_tool_policy",
                    "surface": "pre_tool_policy_decision",
                    "truth_source": "typed_records",
                    "summary_inputs_trusted": False,
                    "can_update_kernel_state": False,
                    "can_update_claim_trust": False,
                },
                "path": "AITP_V5_HOOK_BRIDGE.md",
                "guard_calls": [],
            },
        )

    assert any(issue.path == "codex_hook_bridge.gate_protocols" for issue in error.value.result.issues)


def test_public_surface_validator_accepts_claude_code_hook_settings():
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = {
        "ok": True,
        "kind": "claude_code_hook_settings",
        "runtime": "claude_code",
        "source_protocol_field": "runtime_hook_installation",
        "installation_mode": "native_lifecycle_hooks",
        "native_installer_available": False,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "can_write_trace_events": True,
        "path": ".claude/settings.local.json",
        "events": [
            {
                "hook_event_name": "SessionStart",
                "matcher": "startup|resume",
                "protocol_hook": "session_start",
                "command": "python hooks/aitp_v5_claude_hook.py session-start",
            },
            {
                "hook_event_name": "PreToolUse",
                "matcher": "*",
                "protocol_hook": "pre_tool",
                "command": "python hooks/aitp_v5_claude_hook.py pre-tool",
            },
            {
                "hook_event_name": "PostToolUse",
                "matcher": "*",
                "protocol_hook": "post_tool",
                "command": "python hooks/aitp_v5_claude_hook.py post-tool",
            },
        ],
        "settings": {"hooks": {"SessionStart": [], "PreToolUse": [], "PostToolUse": []}},
    }

    assert require_valid_public_surface("claude_code_hook_settings", payload) == payload


def test_public_surface_validator_accepts_claude_code_hook_installation():
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = {
        "ok": True,
        "kind": "claude_code_hook_installation",
        "runtime": "claude_code",
        "source_protocol_field": "runtime_hook_installation",
        "settings_kind": "claude_code_hook_settings",
        "installation_mode": "native_lifecycle_hooks",
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "can_write_trace_events": True,
        "created": False,
        "merged": True,
        "added_hooks": 3,
        "path": ".claude/settings.local.json",
        "events": [
            {
                "hook_event_name": "SessionStart",
                "matcher": "startup|resume",
                "protocol_hook": "session_start",
                "command": "python hooks/aitp_v5_claude_hook.py session-start",
            },
            {
                "hook_event_name": "PreToolUse",
                "matcher": "*",
                "protocol_hook": "pre_tool",
                "command": "python hooks/aitp_v5_claude_hook.py pre-tool",
            },
            {
                "hook_event_name": "PostToolUse",
                "matcher": "*",
                "protocol_hook": "post_tool",
                "command": "python hooks/aitp_v5_claude_hook.py post-tool",
            },
        ],
        "settings": {"hooks": {"SessionStart": [], "PreToolUse": [], "PostToolUse": []}},
    }

    assert require_valid_public_surface("claude_code_hook_installation", payload) == payload


def test_public_surface_validator_accepts_kimi_code_hook_config():
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = {
        "ok": True,
        "kind": "kimi_code_hook_config",
        "runtime": "kimi_code",
        "source_protocol_field": "runtime_hook_installation",
        "installation_mode": "native_lifecycle_hooks",
        "native_installer_available": False,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "can_write_trace_events": True,
        "path": ".kimi/config.toml",
        "events": [
            {
                "hook_event_name": "SessionStart",
                "matcher": "startup|resume",
                "protocol_hook": "session_start",
                "command": "python hooks/aitp_v5_kimi_hook.py session-start",
            },
            {
                "hook_event_name": "PreToolUse",
                "matcher": "*",
                "protocol_hook": "pre_tool",
                "command": "python hooks/aitp_v5_kimi_hook.py pre-tool",
            },
            {
                "hook_event_name": "PostToolUse",
                "matcher": "*",
                "protocol_hook": "post_tool",
                "command": "python hooks/aitp_v5_kimi_hook.py post-tool",
            },
        ],
        "config_text": '[[hooks]]\nevent = "SessionStart"\ncommand = "python hooks/aitp_v5_kimi_hook.py session-start"\n[[hooks]]\nevent = "PreToolUse"\ncommand = "python hooks/aitp_v5_kimi_hook.py pre-tool"\n[[hooks]]\nevent = "PostToolUse"\ncommand = "python hooks/aitp_v5_kimi_hook.py post-tool"\n',
    }

    assert require_valid_public_surface("kimi_code_hook_config", payload) == payload


def test_public_surface_validator_accepts_kimi_code_hook_installation():
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = {
        "ok": True,
        "kind": "kimi_code_hook_installation",
        "runtime": "kimi_code",
        "source_protocol_field": "runtime_hook_installation",
        "config_kind": "kimi_code_hook_config",
        "installation_mode": "native_lifecycle_hooks",
        "native_installer_available": False,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "can_write_trace_events": True,
        "created": False,
        "merged": True,
        "added_hooks": 3,
        "path": ".kimi/config.toml",
        "events": [
            {
                "hook_event_name": "SessionStart",
                "matcher": "startup|resume",
                "protocol_hook": "session_start",
                "command": "python hooks/aitp_v5_kimi_hook.py session-start",
            },
            {
                "hook_event_name": "PreToolUse",
                "matcher": "*",
                "protocol_hook": "pre_tool",
                "command": "python hooks/aitp_v5_kimi_hook.py pre-tool",
            },
            {
                "hook_event_name": "PostToolUse",
                "matcher": "*",
                "protocol_hook": "post_tool",
                "command": "python hooks/aitp_v5_kimi_hook.py post-tool",
            },
        ],
        "config_text": '[[hooks]]\nevent = "SessionStart"\ncommand = "python hooks/aitp_v5_kimi_hook.py session-start"\n[[hooks]]\nevent = "PreToolUse"\ncommand = "python hooks/aitp_v5_kimi_hook.py pre-tool"\n[[hooks]]\nevent = "PostToolUse"\ncommand = "python hooks/aitp_v5_kimi_hook.py post-tool"\n',
    }

    assert require_valid_public_surface("kimi_code_hook_installation", payload) == payload


def test_public_surface_validator_accepts_opencode_plugin_bridge():
    from brain.v5.adapter_protocols import mandatory_gate_protocols
    from brain.v5.hook_entrypoint_schemas import (
        pre_tool_event_platform_schema,
        pre_tool_policy_input_schema,
    )
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = {
        "ok": True,
        "kind": "opencode_plugin_bridge",
        "runtime": "opencode",
        "source_protocol_field": "runtime_hook_installation",
        "installation_mode": "plugin_bridge",
        "native_installer_available": False,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "path": ".opencode/AITP_V5_PLUGIN_BRIDGE.md",
        "plugin_bridge": {
            "persistence_entrypoint": "aitp_v5_persist_hook_trace_event",
            "pre_tool_policy_entrypoint": {
                "cli": "aitp-v5 policy pre-tool <args>",
                "mcp": "aitp_v5_evaluate_pre_tool_policy",
                "surface": "pre_tool_policy_decision",
                "truth_source": "typed_records",
                "summary_inputs_trusted": False,
                "can_update_kernel_state": False,
                "can_update_claim_trust": False,
                "input_schema": pre_tool_policy_input_schema(),
            },
            "pre_tool_event_entrypoint": {
                "cli": "aitp-v5 adapter pre-tool-event <runtime> <session-id> <args>",
                "mcp": "aitp_v5_evaluate_adapter_pre_tool_event",
                "surface": "pre_tool_policy_decision",
                "truth_source": "typed_records",
                "summary_inputs_trusted": False,
                "can_update_kernel_state": False,
                "can_update_claim_trust": False,
                "requires_bridge_payload": True,
                "requires_platform_event": True,
                "platform_event_schema": pre_tool_event_platform_schema(),
            },
            "gate_protocols": {
                "source_protocol_field": "runtime_gate_protocols",
                **mandatory_gate_protocols(),
            },
            "lifecycle_calls": [
                {
                    "hook_name": "pre_tool",
                    "lifecycle_event": "pre_tool",
                    "command": "python hooks/aitp_v5_hook.py pre-tool",
                    "required_inputs": ["action", "risk_level", "policy_json"],
                    "output_kind": "hook_decision",
                    "may_block": True,
                    "state_mutation": "none",
                }
            ],
        },
    }

    assert require_valid_public_surface("opencode_plugin_bridge", payload) == payload


def test_public_surface_validator_accepts_hook_trace_event_record():
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = {
        "ok": True,
        "kind": "hook_trace_event_record",
        "event_id": "event-s1-fqhe-claim-tool",
        "session_id": "s1",
        "topic_id": "fqhe",
        "claim_id": "claim-fqhe",
        "event_type": "tool_run_recorded",
        "risk_level": "guided",
        "source_kind": "hook_trace_event",
        "source_hook": "post_tool",
        "trace_path": ".aitp/runtime/hook_trace_events.jsonl",
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "writes_trace_event": True,
    }

    assert require_valid_public_surface("hook_trace_event_record", payload) == payload


def test_public_surface_validator_accepts_pre_tool_policy_decision():
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = {
        "ok": True,
        "kind": "hook_decision",
        "hook_name": "pre_tool",
        "action": "promote_to_l2",
        "session_id": "s1",
        "claim_id": "claim-fqhe",
        "risk_level": "adversarial",
        "human_checkpoint_id": "checkpoint-fqhe",
        "mode": "block",
        "block": True,
        "message": "blocked promote_to_l2; no_l2_promotion_without_evidence_ref; required: attach_evidence_ref",
        "policy_reasons": [
            {
                "policy_id": "no_l2_promotion_without_evidence_ref",
                "severity": "block",
                "message": "L2 promotion requires at least one evidence reference",
            }
        ],
        "required_actions": ["attach_evidence_ref"],
        "exit_code": 2,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "evidence_refs": ["evidence-counting"],
        "validation_contract_ids": [],
        "tool_run_ids": [],
        "validation_result_ids": [],
        "known_failure_modes": [],
    }

    assert require_valid_public_surface("pre_tool_policy_decision", payload) == payload


def test_public_surface_validator_rejects_invalid_pre_tool_policy_risk_level():
    from brain.v5.hook_protocol_contracts import validate_pre_tool_policy_decision

    payload = {
        "ok": True,
        "kind": "hook_decision",
        "hook_name": "pre_tool",
        "action": "promote_to_l2",
        "session_id": "s1",
        "claim_id": "claim-fqhe",
        "risk_level": "casual",
        "mode": "block",
        "block": True,
        "message": "blocked promote_to_l2",
        "policy_reasons": [],
        "required_actions": ["request_human_checkpoint"],
        "exit_code": 2,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }

    result = validate_pre_tool_policy_decision(payload)

    assert any(issue.path == "pre_tool_policy_decision.risk_level" for issue in result.issues)


def test_public_surface_validator_accepts_typed_write_records():
    from brain.v5.public_surfaces import require_valid_public_surface

    evidence = {
        "ok": True,
        "kind": "evidence",
        "evidence_id": "evidence-fqhe-counting",
        "topic_id": "fqhe",
        "claim_id": "claim-fqhe-counting",
        "evidence_type": "toy_numeric",
        "status": "supports",
        "summary": "Finite-size counting check.",
        "supports_outputs": ["minimal_check"],
        "source_refs": ["paper:example"],
        "tool_run_ids": ["tool-run-ed"],
        "validation_result_ids": ["validation-result-ed"],
        "artifact_ids": ["artifact-spectrum"],
    }
    tool_run = {
        "ok": True,
        "kind": "tool_run",
        "run_id": "tool-run-ed",
        "recipe_id": "recipe-ed",
        "tool_family": "numerical",
        "tool_name": "exact-diagonalization",
        "topic_id": "fqhe",
        "claim_id": "claim-fqhe-counting",
        "inputs": {"system_size": 10},
        "outputs": {"counting_matches": True},
        "environment": {"python": "3.12"},
        "evidence_status": "supports",
        "code_state_ids": ["code-state-ed"],
        "artifact_ids": ["artifact-spectrum"],
        "source_refs": ["paper:example"],
    }
    code_state = {
        "ok": True,
        "kind": "code_state",
        "code_state_id": "code-state-librpa-abc123",
        "repo_id": "librpa",
        "upstream_remote": "origin",
        "upstream_branch": "master",
        "upstream_commit": "abc123",
        "local_branch": "topic/gw",
        "worktree_path": "D:/worktrees/librpa/gw",
        "dirty": False,
        "patch_id": "",
        "diff_hash": "",
        "build_config": {},
        "runtime_environment": {},
        "linked_records": {"claim_id": "claim-gw"},
        "known_divergence": "",
    }
    recipe = {
        "ok": True,
        "kind": "tool_recipe",
        "recipe_id": "recipe-librpa-gw",
        "tool_family": "domain",
        "tool_name": "librpa-gw-runner",
        "purpose": "Run a LibRPA GW benchmark.",
        "required_inputs": ["code_state_id"],
        "expected_outputs": ["benchmark_consistency"],
        "invariants": ["same upstream commit"],
    }
    memory = {
        "ok": True,
        "kind": "memory_entry",
        "entry_id": "memory-fqhe-counting",
        "topic_id": "fqhe",
        "source_claim_id": "claim-fqhe-counting",
        "source_topic_id": "fqhe",
        "statement": "Counting identifies the edge CFT in the recorded sector.",
        "memory_kind": "scoped_claim",
        "scope": "N<=10 ED",
        "evidence_refs": ["evidence-counting"],
        "validation_result_ids": ["validation-result-ed"],
        "non_claims": ["Does not prove thermodynamic limit."],
        "known_failure_modes": ["sector misassignment"],
        "source_packet_id": "packet-fqhe-counting",
        "human_checkpoint_id": "checkpoint-fqhe-counting",
        "status": "active",
    }
    source_asset = {
        "ok": True,
        "kind": "source_asset",
        "asset_id": "source-asset-fqhe-paper",
        "topic_id": "fqhe",
        "claim_id": "claim-fqhe-counting",
        "asset_type": "paper",
        "uri": "arxiv:2601.00001",
        "title": "Edge counting source",
        "label": "",
        "content_hash": "",
        "hash_algorithm": "",
        "version_anchor": {"arxiv_version": "v1"},
        "acquired_at": "",
        "source_kind": "literature",
        "summary": "Canonical raw paper identity.",
        "source_refs": ["paper:edge-counting"],
        "artifact_ids": [],
        "code_state_ids": [],
        "reference_location_ids": [],
        "derived_from": [],
        "metadata": {},
        "linked_records": {"claim_id": "claim-fqhe-counting"},
        "orientation_only": True,
        "can_update_claim_trust": False,
    }

    assert require_valid_public_surface("evidence_record", evidence) == evidence
    assert require_valid_public_surface("tool_run_record", tool_run) == tool_run
    assert require_valid_public_surface("code_state_record", code_state) == code_state
    assert require_valid_public_surface("tool_recipe_record", recipe) == recipe
    assert require_valid_public_surface("memory_entry_record", memory) == memory
    assert require_valid_public_surface("source_asset_record", source_asset) == source_asset


def test_adapter_registry_exposes_public_surface_contract_names():
    from brain.v5.adapter_protocols import adapter_protocol_registry
    from brain.v5.public_surfaces import public_surface_names

    assert adapter_protocol_registry()["public_surface_contracts"] == list(public_surface_names())


def test_public_surface_validator_ref_names_shared_helper():
    from brain.v5.public_surfaces import public_surface_validator_ref

    assert public_surface_validator_ref() == "brain.v5.public_surfaces.require_valid_public_surface"


def test_adapter_registry_exposes_public_surface_validator_ref():
    from brain.v5.adapter_protocols import adapter_protocol_registry
    from brain.v5.public_surfaces import public_surface_validator_ref

    assert adapter_protocol_registry()["public_surface_validator"] == public_surface_validator_ref()


def test_describe_public_surfaces_returns_auditable_contract_payload():
    from brain.v5.public_surfaces import (
        describe_public_surfaces,
        public_surface_names,
        public_surface_validator_ref,
    )

    payload = describe_public_surfaces()

    assert payload["kind"] == "public_surface_contracts"
    assert payload["validator"] == public_surface_validator_ref()
    assert payload["surface_names"] == list(public_surface_names())
    assert payload["truth_source"] == "contract_registry"
    assert payload["summary_inputs_trusted"] is False
    assert {surface["name"] for surface in payload["surfaces"]} == set(public_surface_names())
    for surface in payload["surfaces"]:
        assert surface["validator"] == public_surface_validator_ref()
        assert surface["purpose"]


def test_public_surface_validator_accepts_record_gate_coverage_audit():
    from brain.v5.adapter_protocols import record_gate_coverage_audit
    from brain.v5.public_surfaces import require_valid_public_surface

    audit = record_gate_coverage_audit()

    assert require_valid_public_surface("record_gate_coverage_audit", audit) == audit


def test_public_surface_validator_accepts_runtime_hook_installation_audit():
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = {
        "kind": "runtime_hook_installation_audit",
        "runtime": "codex",
        "truth_source": "runtime_files",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "status": "installed",
        "checked_paths": [".codex/hooks.json"],
        "findings": [
            {
                "path": ".codex/hooks.json",
                "exists": True,
                "status": "installed",
                "expected": ["PreToolUse pre-tool runner", "PostToolUse post-tool runner"],
                "observed": ["PreToolUse pre-tool runner", "PostToolUse post-tool runner"],
                "messages": [],
                "runtime_metadata_only": True,
            }
        ],
        "required_actions": [],
    }

    assert require_valid_public_surface("runtime_hook_installation_audit", payload) == payload


def test_public_surface_validator_accepts_runtime_hook_installation_paths():
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = {
        "kind": "runtime_hook_installation_paths",
        "truth_source": "workspace_conventions",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "workspace_base": "workspace",
        "paths": [
                {
                    "runtime": "codex",
                    "preferred": {
                        "path": "workspace/.codex/hooks.json",
                        "relative_path": ".codex/hooks.json",
                        "install_arg": "--settings",
                    },
                    "alternates": [
                        {
                            "path": "workspace/.codex/AITP_V5_HOOKS.json",
                            "relative_path": ".codex/AITP_V5_HOOKS.json",
                            "install_arg": "--output",
                        }
                    ],
                "install_command": "aitp-v5 --base workspace adapter install-hooks codex <session-id> --settings .codex/hooks.json",
                "audit_command": "aitp-v5 --base workspace adapter install-audit codex --settings .codex/hooks.json",
                "runtime_metadata_only": True,
            }
        ],
    }

    assert require_valid_public_surface("runtime_hook_installation_paths", payload) == payload


def test_runtime_entrypoint_surfaces_close_over_public_surface_contracts():
    from brain.v5.public_surfaces import public_surface_names
    from brain.v5.runtime_entrypoints import runtime_entrypoint_surfaces, runtime_entrypoints

    surfaces = runtime_entrypoint_surfaces()

    assert surfaces == set(public_surface_names()) | {"public_surface_contracts"}
    for entrypoint in runtime_entrypoints().values():
        assert entrypoint["surface"] in surfaces


def test_public_surface_validator_rejects_invalid_named_surface():
    import pytest

    from brain.v5.contracts import ContractError
    from brain.v5.public_surfaces import require_valid_public_surface

    with pytest.raises(ContractError):
        require_valid_public_surface("summary_orientation", {"kind": "summary_orientation"})


def test_public_surface_validator_rejects_unknown_surface():
    import pytest

    from brain.v5.public_surfaces import require_valid_public_surface

    with pytest.raises(ValueError, match="unknown public surface"):
        require_valid_public_surface("draft_notes", {})
