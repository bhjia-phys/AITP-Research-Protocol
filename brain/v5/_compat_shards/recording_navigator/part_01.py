# Compatibility shard 1 for recording_navigator.
from __future__ import annotations

from copy import deepcopy

from typing import Any

from brain.v5.active_claim_focus import detect_active_claim_focus_drift

from brain.v5.brief import build_execution_brief

from brain.v5.claim_relation_map import build_claim_relation_map

from brain.v5.markdown import read_md

from brain.v5.paths import WorkspacePaths

from brain.v5.process_graph import build_process_graph_slice

from brain.v5.record_refs import lookup_record_refs

from brain.v5.recovery_session import recover_session_binding_for_read

from brain.v5.workspace import get_claim

DECISION_IGNORE = "ignore"

DECISION_DEFER = "defer"

DECISION_NAVIGATE = "navigate"

DECISION_CHECKPOINT = "checkpoint"

_RECORDING_EVENT_TYPES = {
    "session_start",
    "claim_created_or_changed",
    "source_touched",
    "tool_run_completed",
    "artifact_created",
    "result_observed",
    "gap_found",
    "route_changed",
    "final_answer_about_claim",
    "trust_change_requested",
    "session_end",
}

_FIRST_LEVEL_SLOT_ORDER = [
    "source_asset",
    "reference_location",
    "tool_run",
    "code_state",
    "artifact",
    "evidence",
    "physics_object",
    "object_relation",
    "research_route",
    "research_run",
    "research_run_event",
    "proof_obligation",
    "source_reconstruction_review",
    "validation_contract",
    "validation_result",
    "human_checkpoint",
    "sensemaking_report",
    "trust_preflight",
]

_SLOT_COUNT_FAMILIES = {
    "source_asset": "source_assets",
    "reference_location": "reference_locations",
    "tool_run": "tool_runs",
    "code_state": "code_states",
    "artifact": "artifacts",
    "evidence": "evidence",
    "physics_object": "physics_objects",
    "object_relation": "object_relations",
    "research_route": "routes",
    "research_run": "research_runs",
    "research_run_event": "research_run_events",
    "proof_obligation": "proof_obligations",
    "source_reconstruction_review": "source_reconstruction_reviews",
    "validation_contract": "validation_contracts",
    "validation_result": "validation_results",
    "human_checkpoint": "checkpoints",
    "sensemaking_report": "sensemaking_reports",
}

_EVENT_SLOT_HINTS: dict[str, list[str]] = {
    "session_start": ["research_run", "research_run_event"],
    "claim_created_or_changed": ["proof_obligation", "sensemaking_report", "validation_contract"],
    "source_touched": ["reference_location", "source_asset"],
    "tool_run_completed": ["tool_run", "code_state", "artifact", "evidence", "validation_result"],
    "artifact_created": ["artifact", "source_asset", "tool_run"],
    "result_observed": ["evidence", "validation_result", "source_reconstruction_review", "sensemaking_report"],
    "gap_found": ["proof_obligation", "human_checkpoint", "research_route"],
    "route_changed": ["research_route", "research_run_event"],
    "final_answer_about_claim": ["sensemaking_report", "evidence", "validation_result", "trust_preflight"],
    "trust_change_requested": ["trust_preflight", "human_checkpoint", "validation_result"],
    "session_end": ["research_run_event", "sensemaking_report"],
}

_TRUST_CHANGING_EVENT_TYPES = {"trust_change_requested"}

_NAVIGATION_EVENT_TYPES = set(_EVENT_SLOT_HINTS) - {"trust_change_requested"}

_DEFER_EVENT_TYPES = {"session_start", "session_end"}

_SLOT_EXPANSIONS: dict[str, dict[str, Any]] = {
    "source_asset": {
        "recommended_write_tool": "aitp_v5_register_source_asset",
        "cli_template": "aitp-v5 asset register --topic <topic-id> --type <asset-type> --uri <uri> --title <title> --claim <claim-id>",
        "record_kind": "source_asset",
        "required_fields": ["base", "topic_id", "asset_type", "uri", "title"],
        "optional_fields": [
            "claim_id",
            "label",
            "content_hash",
            "hash_algorithm",
            "version_anchor",
            "acquired_at",
            "source_kind",
            "summary",
            "source_refs",
            "artifact_ids",
            "code_state_ids",
            "reference_location_ids",
            "derived_from",
            "metadata",
            "linked_records",
        ],
        "recommended_links": ["claim:<claim_id>", "reference_location:<location_id>", "artifact:<artifact_id>", "code_state:<code_state_id>"],
        "graph_edges_created": [
            "claim --has_source_asset--> source_asset",
            "source_asset --has_reference_location--> reference_location",
            "source_asset --has_code_state--> code_state",
            "source_asset --derived_from--> source_asset",
        ],
        "when_to_use": "Record canonical identity for a paper, local file, dataset, code snapshot, generated artifact, or other source-like object.",
        "writes_kernel_state": True,
    },
    "reference_location": {
        "recommended_write_tool": "aitp_v5_record_reference_location",
        "cli_template": "aitp-v5 reference location record --topic <topic-id> --connector <connector> --type <type> --uri <uri> --label <label>",
        "record_kind": "reference_location",
        "required_fields": ["base", "topic_id", "connector_id", "location_type", "uri", "label"],
        "optional_fields": ["claim_id", "source_ref", "external_id", "status", "summary", "metadata", "linked_records"],
        "recommended_links": ["claim:<claim_id>", "source_asset:<asset_id>"],
        "graph_edges_created": ["claim --has_reference_location--> reference_location"],
        "when_to_use": "Record a pointer into literature, notes, source code, or a knowledge connector before treating it as source context.",
        "writes_kernel_state": True,
    },
    "tool_run": {
        "recommended_write_tool": "aitp_v5_record_tool_run",
        "cli_template": "aitp-v5 tool run record --recipe <recipe-id> --family <family> --name <name> --topic <topic-id> --claim <claim-id>",
        "record_kind": "tool_run",
        "required_fields": ["base", "recipe_id", "tool_family", "tool_name", "topic_id", "claim_id"],
        "optional_fields": ["inputs", "outputs", "environment", "evidence_status", "code_state_ids", "artifact_ids", "source_refs"],
        "recommended_links": ["claim:<claim_id>", "code_state:<code_state_id>", "artifact:<artifact_id>", "reference_location:<location_id>"],
        "graph_edges_created": [
            "claim --has_tool_run--> tool_run",
            "tool_run --uses_code_state--> code_state",
            "tool_run --produced_artifact--> artifact",
            "tool_run --uses_source--> reference_location",
        ],
        "when_to_use": "Record execution provenance after a script, solver, theorem checker, benchmark, or diagnostic has actually run.",
        "writes_kernel_state": True,
    },
    "code_state": {
        "recommended_write_tool": "aitp_v5_capture_code_state_auto",
        "cli_template": "aitp-v5 code state auto --worktree-path <path> --topic <topic-id> --claim <claim-id> --session <session-id>",
        "record_kind": "code_state",
        "required_fields": ["base", "worktree_path"],
        "optional_fields": ["repo_id", "topic_id", "claim_id", "session_id", "build_config", "runtime_environment", "linked_records", "known_divergence", "write_patch_artifact"],
        "recommended_links": ["claim:<claim_id>", "tool_run:<run_id>", "source_asset:<asset_id>"],
        "graph_edges_created": [
            "tool_run --uses_code_state--> code_state",
            "source_asset --has_code_state--> code_state",
        ],
        "when_to_use": "Record git/worktree provenance before using code-dependent outputs as research evidence.",
        "writes_kernel_state": True,
    },
    "artifact": {
        "recommended_write_tool": "aitp_v5_attach_artifact",
        "cli_template": "aitp-v5 artifact attach <args>",
        "record_kind": "artifact",
        "required_fields": ["base", "topic_id", "claim_id", "artifact_type", "uri", "summary"],
        "optional_fields": ["size_bytes", "metadata"],
        "recommended_links": ["claim:<claim_id>", "tool_run:<run_id>", "evidence:<evidence_id>", "source_asset:<asset_id>"],
        "graph_edges_created": [
            "claim --has_artifact--> artifact",
            "tool_run --produced_artifact--> artifact",
            "evidence --uses_artifact--> artifact",
        ],
        "when_to_use": "Record durable by-reference files: logs, plots, dumps, reports, notebooks, generated tables, or raw outputs.",
        "writes_kernel_state": True,
    },
    "evidence": {
        "recommended_write_tool": "aitp_v5_record_evidence",
        "cli_template": "aitp-v5 evidence record --topic <topic-id> --claim <claim-id> --type <type> --status <status> --summary <summary>",
        "record_kind": "evidence",
        "required_fields": ["base", "topic_id", "claim_id", "evidence_type", "status", "summary"],
        "optional_fields": ["supports_outputs", "source_refs", "tool_run_ids", "validation_result_ids", "artifact_ids"],
        "recommended_links": ["claim:<claim_id>", "tool_run:<run_id>", "validation_result:<result_id>", "reference_location:<location_id>", "artifact:<artifact_id>"],
        "graph_edges_created": [
            "claim --has_evidence--> evidence",
            "evidence --uses_tool_run--> tool_run",
            "evidence --uses_validation_result--> validation_result",
            "evidence --uses_source--> reference_location",
        ],
        "when_to_use": "Record a typed support, contradiction, diagnostic, or negative result after its provenance exists.",
        "writes_kernel_state": True,
    },
    "physics_object": {
        "recommended_write_tool": "aitp_v5_record_physics_object",
        "cli_template": "aitp-v5 object record --topic <topic-id> --type <object-type> --name <name> --definition <definition>",
        "record_kind": "physics_object",
        "required_fields": ["base", "topic_id", "object_type", "name", "definition"],
        "optional_fields": ["notation", "assumptions", "source_refs", "metadata", "linked_records", "status"],
        "recommended_links": ["reference_location:<location_id>", "object_relation:<relation_id>"],
        "graph_edges_created": ["object_relation --relation_subject/relation_object--> physics_object"],
        "when_to_use": "Record definitions, systems, operators, sectors, observables, models, or theoretical objects.",
        "writes_kernel_state": True,
    },
    "object_relation": {
        "recommended_write_tool": "aitp_v5_record_object_relation",
        "cli_template": "aitp-v5 relation record --topic <topic-id> --type <relation-type> --subject <object-id> --object <object-id> --statement <statement>",
        "record_kind": "object_relation",
        "required_fields": ["base", "topic_id", "relation_type", "subject_id", "object_id", "statement"],
        "optional_fields": ["claim_id", "assumptions", "failure_modes", "source_refs", "evidence_refs", "status"],
        "recommended_links": ["claim:<claim_id>", "physics_object:<subject_id>", "physics_object:<object_id>", "evidence:<evidence_id>", "reference_location:<location_id>"],
        "graph_edges_created": [
            "claim --has_object_relation--> object_relation",
            "object_relation --relation_subject--> physics_object",
            "object_relation --relation_object--> physics_object",
            "object_relation --supported_by_evidence--> evidence",
        ],
        "when_to_use": "Record an equation, dependency, map, limitation, mechanism, or typed relation between physics objects.",
        "writes_kernel_state": True,
    },
    "research_route": {
        "recommended_write_tool": "aitp_v5_record_research_route",
        "cli_template": "aitp-v5 route record --topic <topic-id> --type <route-type> --status <status> --title <title> --rationale <rationale>",
        "record_kind": "research_route",
        "required_fields": ["base", "topic_id", "route_type", "status", "title", "rationale"],
        "optional_fields": [
            "claim_id",
            "session_id",
            "current_question",
            "next_action",
            "failure_modes",
            "source_refs",
            "evidence_refs",
            "artifact_ids",
            "parent_route_ids",
            "checkpoint_ids",
            "exploratory_record_ids",
            "object_ids",
            "relation_ids",
            "decision_rationale",
            "pivot_reason",
            "metadata",
        ],
        "recommended_links": ["claim:<claim_id>", "session:<session_id>", "human_checkpoint:<checkpoint_id>", "exploratory_record:<record_id>"],
        "graph_edges_created": [
            "session --has_research_route--> research_route",
            "research_route --route_checkpoint--> human_checkpoint",
            "research_route --route_exploration--> exploratory_record",
        ],
        "when_to_use": "Record a branch, pivot, abandoned path, route choice, failed attempt, or current route state.",
        "writes_kernel_state": True,
    },
    "research_run": {
        "recommended_write_tool": "aitp_v5_start_research_run",
        "cli_template": "aitp-v5 run research start <args>",
        "record_kind": "research_run",
        "required_fields": ["base", "topic_id", "objective", "research_question", "operator", "status", "phase"],
        "optional_fields": ["title", "claim_id", "session_id", "hypothesis", "terminal_answer_state", "stop_reason", "aitp_slice_refs", "action_refs", "evidence_refs", "validation_refs", "source_refs", "event_ids", "operator_trail", "answer_packet_ref", "metadata"],
        "recommended_links": ["claim:<claim_id>", "session:<session_id>", "research_run_event:<event_id>", "evidence:<evidence_id>", "validation_result:<result_id>"],
        "graph_edges_created": [
            "session --has_research_run--> research_run",
            "research_run --run_has_event--> research_run_event",
            "research_run --run_uses_evidence--> evidence",
        ],
        "when_to_use": "Record the durable run envelope for a multi-step research attempt.",
        "writes_kernel_state": True,
    },
    "research_run_event": {
        "recommended_write_tool": "aitp_v5_record_research_run_event",
        "cli_template": "aitp-v5 run event record <args>",
        "record_kind": "research_run_event",
        "required_fields": ["base", "run_id", "topic_id", "operator", "event_type", "summary"],
        "optional_fields": ["status", "phase", "claim_id", "session_id", "action_id", "action_ref", "source_refs", "evidence_refs", "validation_refs", "artifact_refs", "payload"],
        "recommended_links": ["research_run:<run_id>", "claim:<claim_id>", "session:<session_id>", "evidence:<evidence_id>", "artifact:<artifact_id>"],
        "graph_edges_created": ["research_run --run_has_event--> research_run_event"],
        "when_to_use": "Record a significant step inside an existing research run without forcing every chat turn into memory.",
        "writes_kernel_state": True,
    },
    "proof_obligation": {
        "recommended_write_tool": "aitp_v5_create_proof_obligation",
        "cli_template": "aitp-v5 research-state proof-obligation create <args>",
        "record_kind": "proof_obligation",
        "required_fields": ["base", "topic_id", "claim_id", "statement", "obligation_type", "status", "maturity_level", "next_action"],
        "optional_fields": ["required_evidence", "proof_strategy", "failure_modes", "source_refs", "evidence_refs", "artifact_ids", "human_gate_required"],
        "recommended_links": ["claim:<claim_id>", "evidence:<evidence_id>", "reference_location:<location_id>"],
        "graph_edges_created": [
            "claim --has_proof_obligation--> proof_obligation",
            "proof_obligation --supported_by_evidence--> evidence",
        ],
        "when_to_use": "Record an open theorem, missing proof step, finite audit gap, unresolved assumption, or required validation condition.",
        "writes_kernel_state": True,
    },
    "source_reconstruction_review": {
        "recommended_write_tool": "aitp_v5_record_source_reconstruction_review_result",
        "cli_template": "aitp-v5 source reconstruction-review-result --claim <claim-id> --status <status> --reviewed-component <component> --summary <summary>",
        "record_kind": "source_reconstruction_review",
        "required_fields": ["base", "claim_id", "status", "reviewed_components", "summary"],
        "optional_fields": [
            "basis_refs",
            "evidence_refs",
            "validation_result_ids",
            "reference_location_ids",
            "object_ids",
            "relation_ids",
            "remaining_actions",
            "reviewer_role",
        ],
        "recommended_links": [
            "claim:<claim_id>",
            "evidence:<evidence_id>",
            "reference_location:<location_id>",
            "physics_object:<object_id>",
            "object_relation:<relation_id>",
        ],
        "graph_edges_created": [
            "claim --has_source_reconstruction_review--> source_reconstruction_review",
            "source_reconstruction_review --review_basis_evidence--> evidence",
            "source_reconstruction_review --review_basis_source--> reference_location",
            "source_reconstruction_review --review_basis_object_relation--> object_relation",
        ],
        "when_to_use": "Record a review result after a source reconstruction audit packet has been checked component by component.",
        "writes_kernel_state": True,
    },
    "validation_contract": {
        "recommended_write_tool": "aitp_v5_create_validation_contract",
        "cli_template": "aitp-v5 validation contract create <args>",
        "record_kind": "validation_contract",
        "required_fields": ["base", "topic_id", "claim_id", "required_checks", "failure_modes", "required_evidence_outputs"],
        "optional_fields": ["tool_recipe_ids", "executor_ids", "validator_role", "status"],
        "recommended_links": ["claim:<claim_id>", "tool_recipe:<recipe_id>"],
        "graph_edges_created": ["claim --has_validation_contract--> validation_contract"],
        "when_to_use": "Record what must be checked before evidence can be considered adequate.",
        "writes_kernel_state": True,
    },
    "validation_result": {
        "recommended_write_tool": "aitp_v5_record_validation_result",
        "cli_template": "aitp-v5 validation result record <args>",
        "record_kind": "validation_result",
        "required_fields": ["base", "topic_id", "claim_id", "contract_id", "tool_run_id", "status"],
        "optional_fields": ["checked_outputs", "missing_outputs", "covered_failure_modes", "failure_modes_observed", "evidence_refs", "artifact_ids", "summary"],
        "recommended_links": ["claim:<claim_id>", "validation_contract:<contract_id>", "tool_run:<run_id>", "evidence:<evidence_id>", "artifact:<artifact_id>"],
        "graph_edges_created": [
            "claim --has_validation_result--> validation_result",
            "validation_result --satisfies_contract--> validation_contract",
            "validation_result --uses_tool_run--> tool_run",
        ],
        "when_to_use": "Record the outcome of an explicit check against a validation contract.",
        "writes_kernel_state": True,
    },
    "human_checkpoint": {
        "recommended_write_tool": "aitp_v5_request_human_checkpoint",
        "cli_template": "aitp-v5 checkpoint request --topic <topic-id> --claim <claim-id> --reason <reason> --requested-by <agent>",
        "record_kind": "human_checkpoint",
        "required_fields": ["base", "topic_id", "claim_id", "reason", "requested_by", "options"],
        "optional_fields": [],
        "recommended_links": ["claim:<claim_id>", "research_route:<route_id>"],
        "graph_edges_created": ["claim --has_human_checkpoint--> human_checkpoint", "research_route --route_checkpoint--> human_checkpoint"],
        "when_to_use": "Ask the human for a route, scope, trust, or ambiguous-source decision before continuing.",
        "writes_kernel_state": True,
    },
    "sensemaking_report": {
        "recommended_write_tool": "aitp_v5_record_sensemaking_report",
        "cli_template": "aitp-v5 sensemaking report --topic <topic-id> --claim <claim-id> --title <title> --summary <summary>",
        "record_kind": "sensemaking_report",
        "required_fields": ["base", "topic_id", "claim_id", "title", "summary"],
        "optional_fields": ["object_ids", "relation_ids", "evidence_refs", "open_questions", "next_actions"],
        "recommended_links": ["claim:<claim_id>", "physics_object:<object_id>", "object_relation:<relation_id>", "evidence:<evidence_id>"],
        "graph_edges_created": ["claim --has_sensemaking_report--> sensemaking_report"],
        "when_to_use": "Record interpretation, synthesis, or handoff orientation without treating it as validation.",
        "writes_kernel_state": True,
    },
    "trust_preflight": {
        "recommended_write_tool": "aitp_v5_preflight_trust_update",
        "cli_template": "aitp-v5 trust preflight <args>",
        "record_kind": "trust_update_preflight",
        "required_fields": ["base", "request_id", "action", "session_id", "topic_id", "claim_id"],
        "optional_fields": ["requested_state", "source_kind", "source_ref", "evidence_refs", "code_state_ids", "rationale", "preflight_token"],
        "recommended_links": ["claim:<claim_id>", "evidence:<evidence_id>", "validation_result:<result_id>", "human_checkpoint:<checkpoint_id>"],
        "graph_edges_created": [],
        "when_to_use": "Check whether a trust-changing action is allowed; this surface still does not apply trust changes.",
        "writes_kernel_state": False,
    },
}

def classify_recording_candidate(
    ws: WorkspacePaths,
    *,
    session_id: str = "",
    event_type: str = "",
    summary: str = "",
    topic_id: str = "",
    claim_id: str = "",
    touched_refs: list[str] | None = None,
    produced_artifacts: list[str] | None = None,
    tool_call_id: str = "",
    risk_hint: str = "",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify whether a host event should enter progressive AITP navigation."""

    del ws  # Current classifier is deterministic over host-provided event metadata.
    clean_event = _clean_event_type(event_type)
    clean_summary = str(summary or "").strip()
    touched_refs = _clean_list(touched_refs)
    produced_artifacts = _clean_list(produced_artifacts)
    payload = dict(payload or {})

    decision = _decision_for_event(clean_event, clean_summary, risk_hint, touched_refs, produced_artifacts, tool_call_id)
    suggested_slots = _suggested_slots(clean_event, clean_summary, touched_refs, produced_artifacts, tool_call_id)
    trigger_reasons = _trigger_reasons(clean_event, clean_summary, risk_hint, touched_refs, produced_artifacts, tool_call_id)
    if not trigger_reasons:
        trigger_reasons = ["no durable AITP recording trigger detected"]

    return {
        "ok": True,
        "kind": "recording_candidate_classification",
        "decision": decision,
        "event_type": clean_event,
        "recognized_event_type": clean_event in _RECORDING_EVENT_TYPES,
        "trigger_reasons": trigger_reasons,
        "suggested_slots": suggested_slots if decision != DECISION_IGNORE else [],
        "next_read_tool": _next_read_tool(decision),
        "session_id": str(session_id or ""),
        "topic_id": str(topic_id or ""),
        "claim_id": str(claim_id or ""),
        "summary": clean_summary,
        "candidate_refs": touched_refs,
        "produced_artifacts": produced_artifacts,
        "tool_call_id": str(tool_call_id or ""),
        "risk_hint": str(risk_hint or ""),
        "payload_keys": sorted(str(key) for key in payload),
        "allowed_decisions": [DECISION_IGNORE, DECISION_DEFER, DECISION_NAVIGATE, DECISION_CHECKPOINT],
        "navigation_policy": {
            "write_at_classification": False,
            "write_at_navigation": False,
            "write_only_after_slot_expansion": True,
            "trust_change_requires_preflight": True,
            "agent_should_not_record_every_step": True,
        },
        "truth_source": "event_metadata_and_typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
