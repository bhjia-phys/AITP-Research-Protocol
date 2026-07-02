"""Host-facing runtime bridge target manifest for AITP v5 entrypoints."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from brain.v5.runtime_entrypoints import runtime_entrypoints


_MCP_ARGUMENT_SPECS: dict[str, dict[str, Any]] = {
    "process_graph_slice": {
        "required": ["base", "session_id"],
        "optional": ["claim_id", "limit"],
        "source": "aitp_v5_get_process_graph_slice",
    },
    "host_agnostic_moment_policy": {
        "required": ["base", "session_id"],
        "optional": ["claim_id", "limit"],
        "source": "aitp_v5_get_host_agnostic_moment_policy",
    },
    "runtime_payload_profiles": {
        "required": [],
        "optional": [],
        "source": "aitp_v5_get_runtime_payload_profiles",
    },
    "workspace_recording_audit": {
        "required": ["base"],
        "optional": ["migration_plan_json", "topics", "limit"],
        "source": "aitp_v5_build_workspace_recording_audit",
    },
    "recording_candidate_classification": {
        "required": ["base", "event_type"],
        "optional": [
            "session_id",
            "summary",
            "topic_id",
            "claim_id",
            "touched_refs",
            "produced_artifacts",
            "tool_call_id",
            "risk_hint",
            "payload",
        ],
        "source": "aitp_v5_classify_recording_candidate",
    },
    "recording_navigation_state": {
        "required": ["base", "session_id"],
        "optional": ["claim_id", "limit"],
        "source": "aitp_v5_get_recording_navigation_state",
        "navigation_mode": "lightweight_first_level",
        "does_not_replace": ["execution_brief", "process_graph_slice"],
    },
    "recording_slot_expansion": {
        "required": ["base", "session_id", "slot"],
        "optional": ["claim_id", "candidate"],
        "source": "aitp_v5_expand_recording_slot",
    },
    "recording_effect_verification": {
        "required": ["base", "session_id"],
        "optional": ["expected_refs", "before_node_ids", "before_edge_ids", "claim_id", "limit"],
        "source": "aitp_v5_verify_recording_effect",
    },
    "record_ref_lookup": {
        "required": ["base", "refs"],
        "optional": [],
        "source": "aitp_v5_lookup_record_refs",
    },
    "curated_rag_corpus": {
        "required": [],
        "optional": ["base"],
        "source": "aitp_v5_get_curated_rag_corpus",
    },
    "curated_rag_search": {
        "required": ["query"],
        "optional": ["base", "limit"],
        "source": "aitp_v5_search_curated_rag_corpus",
    },
    "curated_rag_chunk": {
        "required": ["chunk_id"],
        "optional": ["base"],
        "source": "aitp_v5_get_curated_rag_chunk",
    },
    "curated_rag_promotion_draft": {
        "required": ["chunk_id"],
        "optional": ["base", "topic_id", "claim_id", "connector_id", "promotion_intent"],
        "source": "aitp_v5_draft_curated_rag_promotion",
    },
    "literature_source_review_handoff": {
        "required": ["base", "session_id", "uri", "label", "short_summary", "detected_relevance"],
        "optional": ["external_id", "optional_claim_id", "scoped_output", "reviewed_refs"],
        "source": "aitp_v5_build_literature_source_review_handoff",
    },
    "literature_comparison_draft": {
        "required": ["base", "session_id", "comparison_question", "source_refs"],
        "optional": ["dimensions", "optional_claim_id", "rationale"],
        "source": "aitp_v5_build_literature_comparison_draft",
    },
    "literature_source_extraction_candidates": {
        "required": ["base", "session_id", "source_refs"],
        "optional": ["focus_terms", "extraction_modes", "optional_claim_id", "rationale"],
        "source": "aitp_v5_build_literature_source_extraction_candidates",
    },
    "domain_skill_shims": {
        "required": ["base"],
        "optional": ["pack_ids", "output_root", "apply", "overwrite"],
        "source": "aitp_v5_build_domain_skill_shim_manifest",
    },
}

_BRIDGE_TARGET_SPECS: tuple[tuple[str, str, str, str], ...] = (
    ("readProcessGraphSlice", "process_graph_slice", "read", "read_only"),
    ("readMomentPolicy", "host_agnostic_moment_policy", "read", "read_only"),
    ("readRuntimePayloadProfiles", "runtime_payload_profiles", "read", "read_only"),
    ("readWorkspaceRecordingAudit", "workspace_recording_audit", "read", "read_only"),
    ("classifyRecordingCandidate", "recording_candidate_classification", "read", "read_only"),
    ("readRecordingNavigationState", "recording_navigation_state", "read", "read_only"),
    ("expandRecordingSlot", "recording_slot_expansion", "read", "read_only"),
    ("verifyRecordingEffect", "recording_effect_verification", "read", "read_only"),
    ("lookupRecordRefs", "record_ref_lookup", "read", "read_only"),
    ("readCuratedRagCorpus", "curated_rag_corpus", "read", "read_only"),
    ("searchCuratedRagCorpus", "curated_rag_search", "read", "read_only"),
    ("readCuratedRagChunk", "curated_rag_chunk", "read", "read_only"),
    ("draftCuratedRagPromotion", "curated_rag_promotion_draft", "read", "read_only"),
    ("readLiteratureSourceReviewHandoff", "literature_source_review_handoff", "read", "read_only"),
    ("readLiteratureComparisonDraft", "literature_comparison_draft", "read", "read_only"),
    (
        "readLiteratureSourceExtractionCandidates",
        "literature_source_extraction_candidates",
        "read",
        "read_only",
    ),
    ("materializeDomainSkillShims", "domain_skill_shims", "write", "project_skill_shim_write"),
    ("ingestCuratedRagCorpus", "ingest_curated_rag_corpus", "write", "curated_rag_manifest_write"),
    ("startResearchRun", "start_research_run", "write", "typed_record_write"),
    ("updateResearchRun", "update_research_run", "write", "typed_record_write"),
    ("recordResearchRunEvent", "record_research_run_event", "write", "typed_record_write"),
    ("recordExploratoryRecord", "record_exploratory_record", "write", "typed_record_write"),
    ("registerSourceAsset", "register_source_asset", "write", "typed_record_write"),
    ("captureSourceAssetAuto", "capture_source_asset_auto", "write", "typed_record_write"),
    ("recordEvidence", "record_evidence", "write", "typed_record_write"),
    ("recordToolRun", "record_tool_run", "write", "typed_record_write"),
    ("captureToolRunAuto", "capture_tool_run_auto", "write", "typed_record_write"),
    ("captureCodeStateAuto", "capture_code_state_auto", "write", "typed_record_write"),
    ("attachArtifact", "attach_artifact", "write", "typed_record_write"),
    ("attachArtifactAuto", "attach_artifact_auto", "write", "typed_record_write"),
    ("recordReferenceLocation", "record_reference_location", "write", "typed_record_write"),
    ("createProofObligation", "create_proof_obligation", "write", "typed_record_write"),
    ("createValidationContract", "create_validation_contract", "write", "typed_record_write"),
    ("recordValidationResult", "record_validation_result", "write", "typed_record_write"),
    (
        "recordSourceReconstructionReviewResult",
        "record_source_reconstruction_review_result",
        "write",
        "typed_record_write",
    ),
    ("requestHumanCheckpoint", "request_human_checkpoint", "write", "typed_record_write"),
    ("preflightTrustUpdate", "trust_preflight", "preflight", "preflight_only"),
)


def runtime_bridge_target_manifest() -> dict[str, Any]:
    """Return MCP-first host bridge targets derived from runtime_entrypoints()."""

    entrypoints = runtime_entrypoints()
    targets = [
        _target_payload(
            operation=operation,
            entrypoint_key=entrypoint_key,
            execution_role=execution_role,
            state_effect=state_effect,
            entrypoint=entrypoints[entrypoint_key],
        )
        for operation, entrypoint_key, execution_role, state_effect in _BRIDGE_TARGET_SPECS
    ]
    return {
        "kind": "runtime_bridge_target_manifest",
        "target_count": len(targets),
        "targets": targets,
        "target_groups": {
            "read": [target["operation"] for target in targets if target["execution_role"] == "read"],
            "write": [target["operation"] for target in targets if target["execution_role"] == "write"],
            "preflight": [
                target["operation"] for target in targets if target["execution_role"] == "preflight"
            ],
        },
        "excluded_entrypoints": {
            "trust_apply": "claim trust mutation remains AITP-owned and is not exposed as a host write bridge target",
        },
        "preferred_transport": "mcp",
        "fallback_transport": "cli",
        "mcp_argument_style": "json_object",
        "mcp_base_argument": "base",
        "mcp_payload_key_case": "snake_case",
        "mcp_result_content_type": "json_object",
        "fallback_policy": "use_cli_when_mcp_transport_unavailable_or_call_fails",
        "canonical_store": ".aitp",
        "truth_source": "runtime_entrypoint_catalog",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_claim_trust": False,
    }


def runtime_bridge_target_by_operation(operation: str) -> dict[str, Any] | None:
    """Return one bridge target by host operation name."""

    for target in runtime_bridge_target_manifest()["targets"]:
        if target["operation"] == operation:
            return deepcopy(target)
    return None


def _target_payload(
    *,
    operation: str,
    entrypoint_key: str,
    execution_role: str,
    state_effect: str,
    entrypoint: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "operation": operation,
        "entrypoint_key": entrypoint_key,
        "mcp_tool": entrypoint["mcp"],
        "cli_fallback": entrypoint["cli"],
        "surface": entrypoint["surface"],
        "preferred_transport": "mcp",
        "fallback_transport": "cli",
        "mcp_invocation": {
            "tool": entrypoint["mcp"],
            "argument_style": "json_object",
            "base_argument": "base",
            "payload_key_case": "snake_case",
            "result_surface": entrypoint["surface"],
            "result_content_type": "json_object",
            "fallback_policy": "use_cli_when_mcp_transport_unavailable_or_call_fails",
        },
        "execution_role": execution_role,
        "state_effect": state_effect,
        "canonical_store": ".aitp",
        "claim_trust_mutation": "none",
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }
    mcp_arguments = _MCP_ARGUMENT_SPECS.get(entrypoint_key)
    if mcp_arguments is not None:
        payload["mcp_arguments"] = deepcopy(mcp_arguments)
    return payload
