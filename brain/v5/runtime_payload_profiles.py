"""Host runtime payload profiles for AITP v5 bridge writes."""

from __future__ import annotations

from typing import Any


def runtime_payload_profiles() -> dict[str, Any]:
    """Return canonical host-event to AITP write payload profiles.

    These profiles tell host runtimes how to turn host-native execution results
    into typed AITP record writes without inventing trust or validation rules.
    """

    profiles = [
        {
            "profile_id": "benchmark_adapter_run_to_tool_run",
            "host_event": "benchmark_adapter_run",
            "target_operation": "recordToolRun",
            "target_entrypoint": "aitp_v5_record_tool_run",
            "target_record_action": "record_tool_run",
            "target_surface": "tool_run_record",
            "required_host_fields": [
                "adapter_id",
                "case_id",
                "action_id",
                "outcome",
                "observation",
                "output",
                "topic_id",
                "claim_id",
            ],
            "optional_host_fields": [
                "benchmark_payload",
                "check_results",
                "evidence_refs",
                "artifact_refs",
                "source_refs",
                "primitive_tool_call_ids",
            ],
            "payload_key_case": "camel_or_snake",
            "capture_policy": {
                "capture_mode": "controlled_auto",
                "host_trigger": "ResearchAction.run_benchmark_adapter",
                "requires_configured_bridge": True,
                "requires_scoped_topic_and_claim": True,
                "requires_tool_call_id": False,
                "capture_granularity": "one_tool_run_per_adapter_run",
                "missing_scope_behavior": "skip_with_reason",
                "bulk_auto_capture": False,
                "records_validation_result": False,
                "claim_trust_mutation": "none",
                "summary_inputs_trusted": False,
                "can_update_claim_trust": False,
            },
            "payload_template": {
                "recipe_id": "benchmark_adapter:<adapter_id>:<case_id>",
                "tool_family": "benchmark_adapter",
                "tool_name": "<adapter_id>",
                "topic_id": "<topic_id>",
                "claim_id": "<claim_id>",
                "inputs": {
                    "benchmark_payload": "<benchmark_payload>",
                    "case_id": "<case_id>",
                    "source_refs": "<source_refs>",
                },
                "outputs": {
                    "adapter_id": "<adapter_id>",
                    "case_id": "<case_id>",
                    "action_id": "<action_id>",
                    "outcome": "<outcome>",
                    "observation": "<observation>",
                    "output": "<output>",
                    "evidence_refs": "<evidence_refs>",
                    "artifact_refs": "<artifact_refs>",
                    "check_results": "<check_results>",
                },
                "environment": {
                    "capture_tool": "hakimi.run_benchmark_adapter",
                    "payload_profile": "benchmark_adapter_run_to_tool_run",
                    "summary_inputs_trusted": False,
                    "can_update_claim_trust": False,
                },
                "evidence_status": "unreviewed",
                "artifact_ids": "<artifact_refs_normalized_to_artifact_ids>",
                "source_refs": "<source_refs_plus_benchmark_evidence_refs>",
            },
            "result_semantics": {
                "record_kind": "tool_run",
                "evidence_ref_prefix": "aitp:tool_run",
                "records_validation_result": False,
                "claim_trust_mutation": "none",
                "can_update_claim_trust": False,
                "summary_inputs_trusted": False,
            },
            "strict_boundary": (
                "benchmark adapter outcome is tool-run provenance only; "
                "a validation result still requires an AITP validation contract "
                "and explicit record_validation_result"
            ),
        },
        {
            "profile_id": "primitive_tool_lifecycle_to_tool_run",
            "host_event": "primitive_tool_lifecycle_completed",
            "target_operation": "recordToolRun",
            "target_entrypoint": "aitp_v5_record_tool_run",
            "target_record_action": "record_tool_run",
            "target_surface": "tool_run_record",
            "required_host_fields": [
                "tool_call_id",
                "tool_name",
                "status",
                "output_summary",
                "topic_id",
                "claim_id",
            ],
            "optional_host_fields": [
                "args_summary",
                "cwd",
                "turn_id",
                "step_uuid",
                "duration_ms",
                "artifact_refs",
                "source_refs",
                "workframe_id",
                "action_call_id",
            ],
            "payload_key_case": "camel_or_snake",
            "capture_policy": {
                "capture_mode": "explicit_request",
                "host_trigger": "ResearchAction.capture_primitive_tool_run",
                "requires_configured_bridge": True,
                "requires_scoped_topic_and_claim": True,
                "requires_tool_call_id": True,
                "capture_granularity": "one_tool_run_per_explicit_tool_call_id",
                "missing_scope_behavior": "skip_with_reason",
                "bulk_auto_capture": False,
                "records_validation_result": False,
                "claim_trust_mutation": "none",
                "summary_inputs_trusted": False,
                "can_update_claim_trust": False,
            },
            "payload_template": {
                "recipe_id": "primitive_tool:<tool_name>:<tool_call_id>",
                "tool_family": "primitive_tool",
                "tool_name": "<tool_name>",
                "topic_id": "<topic_id>",
                "claim_id": "<claim_id>",
                "inputs": {
                    "args_summary": "<args_summary>",
                    "cwd": "<cwd>",
                    "source_refs": "<source_refs>",
                },
                "outputs": {
                    "tool_call_id": "<tool_call_id>",
                    "tool_name": "<tool_name>",
                    "status": "<status>",
                    "output_summary": "<output_summary>",
                    "turn_id": "<turn_id>",
                    "step_uuid": "<step_uuid>",
                    "duration_ms": "<duration_ms>",
                    "artifact_refs": "<artifact_refs>",
                    "workframe_id": "<workframe_id>",
                    "action_call_id": "<action_call_id>",
                },
                "environment": {
                    "capture_tool": "hakimi.primitive_tool_lifecycle",
                    "payload_profile": "primitive_tool_lifecycle_to_tool_run",
                    "summary_inputs_trusted": False,
                    "can_update_claim_trust": False,
                },
                "evidence_status": "unreviewed",
                "artifact_ids": "<artifact_refs_normalized_to_artifact_ids>",
                "source_refs": "<source_refs_plus_tool_call_ref>",
            },
            "result_semantics": {
                "record_kind": "tool_run",
                "evidence_ref_prefix": "aitp:tool_run",
                "records_validation_result": False,
                "claim_trust_mutation": "none",
                "can_update_claim_trust": False,
                "summary_inputs_trusted": False,
            },
            "strict_boundary": (
                "primitive tool lifecycle output is tool-run provenance only; "
                "hosts must still create explicit evidence or validation records "
                "before using it for claim support or trust changes"
            ),
        },
    ]

    return {
        "kind": "runtime_payload_profiles",
        "catalog_version": "aitp.v5.runtime_payload_profiles.v1",
        "truth_source": "runtime_payload_profile_catalog",
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "profile_count": len(profiles),
        "profile_index": [profile["profile_id"] for profile in profiles],
        "profiles": profiles,
    }


def runtime_payload_profile_by_id(profile_id: str) -> dict[str, Any]:
    for profile in runtime_payload_profiles()["profiles"]:
        if profile["profile_id"] == profile_id:
            return profile
    raise KeyError(profile_id)
