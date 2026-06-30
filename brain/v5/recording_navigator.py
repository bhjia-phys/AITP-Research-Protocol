"""Progressive read-only navigator for AITP v5 recording decisions."""

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


def build_recording_navigation_state(
    ws: WorkspacePaths,
    session_id: str,
    *,
    claim_id: str = "",
    limit: int = 40,
) -> dict[str, Any]:
    """Return the shallow navigation state for a session/claim before choosing a slot."""

    focus = _lightweight_focus(ws, session_id, claim_id=claim_id)
    relation_map = _safe_relation_map(ws, session_id)
    relation_conclusion = relation_map.get("current_conclusion", {}) if isinstance(relation_map, dict) else {}
    focus_reconciliation = (
        relation_map.get("active_claim_focus_reconciliation", {})
        if isinstance(relation_map, dict)
        else detect_active_claim_focus_drift(ws, session_id)
    )
    drift_detected = bool(
        (relation_map or {}).get("not_authoritative_for_current_goal_if_rebind_needed")
        if isinstance(relation_map, dict)
        else focus_reconciliation.get("not_authoritative_for_current_goal_if_rebind_needed")
    )
    warnings = ["active_claim_focus_drift_detected"] if drift_detected else []
    focus["can_say"] = relation_conclusion.get("can_say", []) if isinstance(relation_conclusion, dict) else []
    focus["cannot_say"] = relation_conclusion.get("cannot_say", []) if isinstance(relation_conclusion, dict) else []
    record_counts = _lightweight_slot_counts(ws, focus["topic_id"], focus["claim_id"])
    slots = [_slot_summary_from_counts(slot, record_counts) for slot in _FIRST_LEVEL_SLOT_ORDER]
    recommended_slots = _recommended_slots_from_counts(record_counts)
    if not recommended_slots:
        recommended_slots = ["source_asset", "reference_location", "proof_obligation", "evidence"]

    return {
        "ok": True,
        "kind": "recording_navigation_state",
        "navigation_mode": "lightweight_first_level",
        "session_id": focus["session_id"] or session_id,
        "requested_session_id": focus["requested_session_id"] or session_id,
        "recovery_selection_source": focus["recovery_selection_source"],
        "topic_id": focus["topic_id"],
        "claim_id": focus["claim_id"],
        "warnings": warnings,
        "active_claim_focus_reconciliation": focus_reconciliation,
        "current_position": focus,
        "first_level_slots": slots,
        "recommended_slots": recommended_slots,
        "graph_context": {
            "mode": "lightweight_slot_counts",
            "node_count": 0,
            "edge_count": 0,
            "record_counts": record_counts,
            "recommended_moments": _lightweight_recommended_moments(record_counts),
            "provenance_gaps": _lightweight_provenance_gaps(record_counts)[: max(1, min(limit, 20))],
            "open_obligations": _lightweight_open_obligation_hints(relation_map)[: max(1, min(limit, 20))],
            "route_state": {},
            "moment_policy": {
                "mode": "lightweight_first_level",
                "next_read_tool": "aitp_v5_expand_recording_slot",
                "agent_should_not_record_every_step": True,
            },
        },
        "brief_context": {
            "available": False,
            "current_focus": {
                "active_claim": focus["claim_id"],
                "active_route": focus["active_route"],
                "active_cycle": focus["active_cycle"],
                "claim_statement": focus["claim_statement"],
                "confidence_state": focus["confidence_state"],
                "evidence_profile": focus["evidence_profile"],
                "main_uncertainty": focus["main_uncertainty"],
            },
            "flow_profile": {},
            "evidence_coverage": {},
            "next_action_candidates": [],
            "forbidden_now": ["lightweight_navigation_state_does_not_replace_execution_brief"],
        },
        "relation_context": {
            "available": bool(relation_map and relation_map.get("kind") != "recording_navigation_error"),
            "relation_map_scope": (relation_map or {}).get("relation_map_scope", "active_claim_only"),
            "not_authoritative_for_current_goal_if_rebind_needed": drift_detected,
            "current_conclusion": (relation_map or {}).get("current_conclusion", {}),
            "current_blockers": (relation_map or {}).get("current_blockers", []),
            "next_valid_actions": (relation_map or {}).get("next_valid_actions", []),
        },
        "next_step": {
            "read_tool": "aitp_v5_expand_recording_slot",
            "write_boundary": "only the expanded deepest slot names the write/preflight tool",
            "verify_tool": "aitp_v5_verify_recording_effect",
        },
        "trust_boundary_reasons": [
            "recording_navigation_state is read-only",
            "recording_navigation_state uses lightweight first-level slot counts by default",
            "call process graph or execution brief separately when full graph context is needed",
            "slot expansion can recommend typed writes but cannot perform them",
            "active-claim focus drift warnings are read-only and cannot rebind without confirmation",
        ],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def expand_recording_slot(
    ws: WorkspacePaths,
    session_id: str,
    slot: str,
    *,
    claim_id: str = "",
    candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Expand one first-level recording slot into concrete write/preflight guidance."""

    normalized_slot = _clean_slot(slot)
    if normalized_slot not in _SLOT_EXPANSIONS:
        return _unknown_slot_expansion(session_id, slot)

    focus = _lightweight_focus(ws, session_id, claim_id=claim_id)
    expansion = deepcopy(_SLOT_EXPANSIONS[normalized_slot])
    expanded_required = _fill_known_field_hints(expansion["required_fields"], focus)
    expanded_optional = _fill_known_field_hints(expansion["optional_fields"], focus)
    candidate = dict(candidate or {})

    return {
        "ok": True,
        "kind": "recording_slot_expansion",
        "slot": normalized_slot,
        "navigation_mode": "lightweight_slot_expansion",
        "session_id": focus["session_id"] or session_id,
        "requested_session_id": focus["requested_session_id"] or session_id,
        "topic_id": focus["topic_id"],
        "claim_id": focus["claim_id"],
        "recommended_write_tool": expansion["recommended_write_tool"],
        "cli_template": expansion["cli_template"],
        "record_kind": expansion["record_kind"],
        "required_fields": expanded_required,
        "optional_fields": expanded_optional,
        "recommended_links": expansion["recommended_links"],
        "graph_edges_created": expansion["graph_edges_created"],
        "when_to_use": expansion["when_to_use"],
        "candidate_context": {
            "event_type": str(candidate.get("event_type") or ""),
            "decision": str(candidate.get("decision") or ""),
            "suggested_slots": list(candidate.get("suggested_slots") or []),
            "candidate_refs": list(candidate.get("candidate_refs") or candidate.get("touched_refs") or []),
            "produced_artifacts": list(candidate.get("produced_artifacts") or []),
        },
        "recording_sequence": [
            "read recording_navigation_state",
            "expand one slot",
            "call the recommended existing typed write/preflight tool with complete fields",
            "call aitp_v5_verify_recording_effect with expected refs or before graph ids",
        ],
        "trust_effect": {
            "writes_kernel_state": bool(expansion["writes_kernel_state"]),
            "can_update_claim_trust": False,
            "claim_trust_mutation": "none",
            "trust_preflight_required_for_trust_change": normalized_slot == "trust_preflight",
        },
        "warnings": _slot_warnings(normalized_slot),
        "verify_with": "aitp_v5_verify_recording_effect",
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def verify_recording_effect(
    ws: WorkspacePaths,
    session_id: str,
    *,
    expected_refs: list[str] | None = None,
    before_node_ids: list[str] | None = None,
    before_edge_ids: list[str] | None = None,
    claim_id: str = "",
    limit: int = 80,
) -> dict[str, Any]:
    """Read back typed records and graph deltas after a write step."""

    expected_refs = _clean_list(expected_refs)
    before_node_ids = _clean_list(before_node_ids)
    before_edge_ids = _clean_list(before_edge_ids)
    ref_lookup = lookup_record_refs(ws, expected_refs)
    graph = build_process_graph_slice(ws, session_id, claim_id=claim_id, limit=limit)
    node_ids = {str(node.get("id")) for node in graph.get("nodes", [])}
    edge_ids = {str(edge.get("id")) for edge in graph.get("edges", [])}
    new_node_ids = sorted(node_ids - set(before_node_ids)) if before_node_ids else []
    new_edge_ids = sorted(edge_ids - set(before_edge_ids)) if before_edge_ids else []
    found_refs = [item["ref"] for item in ref_lookup["refs"] if item["status"] == "found"]
    missing_refs = [item["ref"] for item in ref_lookup["refs"] if item["status"] != "found"]
    verified = (not expected_refs or not missing_refs) and (not before_node_ids or bool(new_node_ids) or bool(found_refs))

    return {
        "ok": True,
        "kind": "recording_effect_verification",
        "verified": verified,
        "session_id": graph.get("session_id") or session_id,
        "requested_session_id": graph.get("requested_session_id", session_id),
        "topic_id": graph.get("topic_id", ""),
        "claim_id": graph.get("claim_id", claim_id),
        "expected_refs": expected_refs,
        "found_refs": found_refs,
        "missing_refs": missing_refs,
        "record_ref_lookup": ref_lookup,
        "graph_delta": {
            "before_node_count": len(before_node_ids),
            "after_node_count": len(node_ids),
            "new_node_ids": new_node_ids,
            "before_edge_count": len(before_edge_ids),
            "after_edge_count": len(edge_ids),
            "new_edge_ids": new_edge_ids,
        },
        "current_recommended_slots": _recommended_slots_from_graph(graph),
        "failure_reasons": _verification_failures(expected_refs, missing_refs, before_node_ids, new_node_ids, found_refs),
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def recording_slot_names() -> list[str]:
    return list(_FIRST_LEVEL_SLOT_ORDER)


def _decision_for_event(
    event_type: str,
    summary: str,
    risk_hint: str,
    touched_refs: list[str],
    produced_artifacts: list[str],
    tool_call_id: str,
) -> str:
    lowered = " ".join([event_type, summary, risk_hint]).lower()
    if event_type in _TRUST_CHANGING_EVENT_TYPES or "trust" in lowered or "promote" in lowered or "confidence" in lowered:
        return DECISION_CHECKPOINT
    if event_type in _NAVIGATION_EVENT_TYPES:
        if event_type in _DEFER_EVENT_TYPES and not touched_refs and not produced_artifacts and not tool_call_id:
            return DECISION_DEFER
        return DECISION_NAVIGATE
    if touched_refs or produced_artifacts or tool_call_id:
        return DECISION_NAVIGATE
    if "without durable" in lowered or "no durable" in lowered:
        return DECISION_DEFER
    if any(token in lowered for token in ("maybe later", "brainstorm", "casual", "explain", "explanation", "question")):
        return DECISION_DEFER
    if any(token in lowered for token in ("evidence", "validation", "proof", "gap", "artifact", "source", "claim", "result")):
        return DECISION_NAVIGATE
    return DECISION_IGNORE


def _suggested_slots(
    event_type: str,
    summary: str,
    touched_refs: list[str],
    produced_artifacts: list[str],
    tool_call_id: str,
) -> list[str]:
    slots = list(_EVENT_SLOT_HINTS.get(event_type, []))
    lowered = summary.lower()
    if touched_refs:
        slots.extend(["reference_location", "source_asset"])
    if produced_artifacts:
        slots.extend(["artifact", "source_asset"])
    if tool_call_id:
        slots.extend(["tool_run", "code_state"])
    if "validation" in lowered or "checked" in lowered or "passed" in lowered or "failed" in lowered:
        slots.extend(["validation_result", "evidence"])
    if "proof" in lowered or "gap" in lowered or "missing" in lowered:
        slots.append("proof_obligation")
    if "route" in lowered or "pivot" in lowered or "abandon" in lowered:
        slots.append("research_route")
    return _unique_slots(slots)


def _trigger_reasons(
    event_type: str,
    summary: str,
    risk_hint: str,
    touched_refs: list[str],
    produced_artifacts: list[str],
    tool_call_id: str,
) -> list[str]:
    reasons: list[str] = []
    if event_type in _RECORDING_EVENT_TYPES:
        reasons.append(f"recognized event_type:{event_type}")
    if event_type in _TRUST_CHANGING_EVENT_TYPES:
        reasons.append("trust-changing event requires checkpoint/preflight navigation")
    if touched_refs:
        reasons.append("candidate includes touched typed/source refs")
    if produced_artifacts:
        reasons.append("candidate includes produced artifacts")
    if tool_call_id:
        reasons.append("candidate includes a tool call id")
    lowered = " ".join([summary, risk_hint]).lower()
    for token in ("evidence", "validation", "proof", "gap", "artifact", "source", "claim", "result", "trust"):
        if token in lowered:
            reasons.append(f"summary_or_risk_mentions:{token}")
    return list(dict.fromkeys(reasons))


def _next_read_tool(decision: str) -> str:
    if decision == DECISION_NAVIGATE:
        return "aitp_v5_get_recording_navigation_state"
    if decision == DECISION_CHECKPOINT:
        return "aitp_v5_expand_recording_slot"
    if decision == DECISION_DEFER:
        return "aitp_v5_get_recording_navigation_state"
    return ""


def _clean_event_type(event_type: str) -> str:
    return str(event_type or "").strip().lower().replace("-", "_").replace(" ", "_")


def _clean_slot(slot: str) -> str:
    return str(slot or "").strip().lower().replace("-", "_").replace(" ", "_")


def _clean_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    return [str(value).strip() for value in values if str(value).strip()]


def _unique_slots(slots: list[str]) -> list[str]:
    seen: set[str] = set()
    clean: list[str] = []
    for slot in slots:
        normalized = _clean_slot(slot)
        if normalized in _SLOT_EXPANSIONS and normalized not in seen:
            seen.add(normalized)
            clean.append(normalized)
    return clean


def _safe_brief(ws: WorkspacePaths, session_id: str) -> dict[str, Any]:
    try:
        return build_execution_brief(ws, session_id)
    except (FileNotFoundError, TypeError, ValueError, OSError) as error:
        return {
            "kind": "recording_navigation_error",
            "surface": "execution_brief",
            "reason": str(error) or error.__class__.__name__,
        }


def _safe_relation_map(ws: WorkspacePaths, session_id: str) -> dict[str, Any]:
    try:
        return build_claim_relation_map(ws, session_id)
    except (FileNotFoundError, TypeError, ValueError, OSError) as error:
        return {
            "kind": "recording_navigation_error",
            "surface": "claim_relation_map",
            "reason": str(error) or error.__class__.__name__,
        }


def _lightweight_focus(ws: WorkspacePaths, session_id: str, *, claim_id: str) -> dict[str, Any]:
    try:
        recovered = recover_session_binding_for_read(ws, session_id)
        session = recovered.session
        focus_claim_id = str(claim_id or session.active_claim or "")
        claim = get_claim(ws, focus_claim_id) if focus_claim_id else None
        return {
            "requested_session_id": recovered.requested_session_id,
            "recovery_selection_source": recovered.recovery_selection_source,
            "session_id": session.session_id,
            "topic_id": session.topic_id,
            "claim_id": focus_claim_id,
            "active_route": session.active_route,
            "active_cycle": session.active_cycle,
            "claim_statement": claim.statement if claim else "",
            "confidence_state": claim.confidence_state if claim else "",
            "evidence_profile": claim.evidence_profile if claim else "",
            "main_uncertainty": claim.active_uncertainty if claim else "",
            "can_say": [],
            "cannot_say": [],
        }
    except (FileNotFoundError, TypeError, ValueError, OSError):
        return {
            "requested_session_id": session_id,
            "recovery_selection_source": "unbound_session",
            "session_id": session_id,
            "topic_id": "unbound-session",
            "claim_id": claim_id,
            "active_route": "",
            "active_cycle": "",
            "claim_statement": "",
            "confidence_state": "",
            "evidence_profile": "",
            "main_uncertainty": "",
            "can_say": [],
            "cannot_say": [],
        }


def _focus_from_surfaces(
    graph: dict[str, Any],
    brief: dict[str, Any] | None,
    relation_map: dict[str, Any] | None,
    claim_id: str,
) -> dict[str, Any]:
    recovered = (brief or {}).get("recovered_focus", {}) if isinstance(brief, dict) else {}
    current_focus = (brief or {}).get("current_focus", {}) if isinstance(brief, dict) else {}
    relation_conclusion = (relation_map or {}).get("current_conclusion", {}) if isinstance(relation_map, dict) else {}
    return {
        "session_id": str(graph.get("session_id") or recovered.get("session_id") or ""),
        "topic_id": str(graph.get("topic_id") or recovered.get("topic_id") or ""),
        "claim_id": str(claim_id or graph.get("claim_id") or recovered.get("active_claim") or current_focus.get("active_claim") or ""),
        "active_route": str(recovered.get("active_route") or current_focus.get("active_route") or ""),
        "active_cycle": str(recovered.get("active_cycle") or current_focus.get("active_cycle") or ""),
        "claim_statement": str(recovered.get("claim_statement") or current_focus.get("claim_statement") or ""),
        "confidence_state": str(recovered.get("confidence_state") or ""),
        "evidence_profile": str(recovered.get("evidence_profile") or ""),
        "main_uncertainty": str(current_focus.get("main_uncertainty") or ""),
        "can_say": relation_conclusion.get("can_say", []) if isinstance(relation_conclusion, dict) else [],
        "cannot_say": relation_conclusion.get("cannot_say", []) if isinstance(relation_conclusion, dict) else [],
    }


def _lightweight_slot_counts(ws: WorkspacePaths, topic_id: str, claim_id: str) -> dict[str, int]:
    counts = {slot: 0 for slot in _SLOT_COUNT_FAMILIES}
    counts["trust_preflight"] = 0
    if not topic_id:
        return counts
    for slot, family in _SLOT_COUNT_FAMILIES.items():
        root = ws.registry_dir(family)
        if not root.exists():
            continue
        for path in root.glob("*.md"):
            try:
                frontmatter, _body = read_md(path)
            except (OSError, TypeError, ValueError):
                continue
            record_topic = str(frontmatter.get("topic_id") or frontmatter.get("topic") or "")
            if record_topic != topic_id:
                continue
            record_claim = str(
                frontmatter.get("claim_id")
                or frontmatter.get("active_claim_id")
                or frontmatter.get("source_claim_id")
                or ""
            )
            if claim_id and record_claim and record_claim != claim_id:
                continue
            counts[slot] = counts.get(slot, 0) + 1
    return counts


def _slot_summary_from_counts(slot: str, counts: dict[str, int]) -> dict[str, Any]:
    expansion = _SLOT_EXPANSIONS[slot]
    count_key = expansion["record_kind"]
    if count_key == "trust_update_preflight":
        current_count = 0
    else:
        current_count = int(counts.get(slot, counts.get(count_key, 0)) or 0)
    return {
        "slot": slot,
        "record_kind": expansion["record_kind"],
        "current_count": current_count,
        "recommended_write_tool": expansion["recommended_write_tool"],
        "expand_with": "aitp_v5_expand_recording_slot",
        "read_only_at_this_layer": True,
        "can_update_claim_trust": False,
        "when_to_use": expansion["when_to_use"],
    }


def _recommended_slots_from_counts(counts: dict[str, int]) -> list[str]:
    slots: list[str] = []
    for slot in (
        "reference_location",
        "source_asset",
        "code_state",
        "artifact",
        "evidence",
        "proof_obligation",
        "source_reconstruction_review",
        "validation_contract",
        "validation_result",
    ):
        if int(counts.get(slot, 0) or 0) == 0:
            slots.append(slot)
    return _unique_slots(slots)


def _lightweight_provenance_gaps(counts: dict[str, int]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    if int(counts.get("reference_location", 0) or 0) == 0:
        gaps.append(
            {
                "gap_type": "missing_reference_location",
                "summary": "No reference location is recorded for the current topic/claim focus.",
                "recommended_entrypoints": ["aitp_v5_record_reference_location"],
            }
        )
    if int(counts.get("source_asset", 0) or 0) == 0:
        gaps.append(
            {
                "gap_type": "missing_source_asset",
                "summary": "No source asset is recorded for the current topic/claim focus.",
                "recommended_entrypoints": ["aitp_v5_register_source_asset"],
            }
        )
    if int(counts.get("evidence", 0) or 0) == 0:
        gaps.append(
            {
                "gap_type": "missing_evidence",
                "summary": "No evidence record is linked to the current topic/claim focus.",
                "recommended_entrypoints": ["aitp_v5_record_evidence"],
            }
        )
    if int(counts.get("validation_contract", 0) or 0) == 0:
        gaps.append(
            {
                "gap_type": "missing_validation_contract",
                "summary": "No validation contract is recorded for the current topic/claim focus.",
                "recommended_entrypoints": ["aitp_v5_create_validation_contract"],
            }
        )
    return gaps


def _lightweight_recommended_moments(counts: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {
            "moment": gap["gap_type"],
            "why": gap["summary"],
            "recommended_entrypoints": gap["recommended_entrypoints"],
        }
        for gap in _lightweight_provenance_gaps(counts)
    ]


def _lightweight_open_obligation_hints(relation_map: dict[str, Any]) -> list[dict[str, Any]]:
    source_records = relation_map.get("source_records") if isinstance(relation_map, dict) else {}
    obligation_ids = source_records.get("proof_obligations", []) if isinstance(source_records, dict) else []
    blockers = relation_map.get("current_blockers", []) if isinstance(relation_map, dict) else []
    out: list[dict[str, Any]] = []
    for obligation_id in obligation_ids:
        out.append({"obligation_id": str(obligation_id), "status": "open_or_relevant"})
    for blocker in blockers:
        text = str(blocker)
        if text and text not in {item.get("obligation_id") for item in out}:
            out.append({"summary": text, "status": "open_or_relevant"})
    return out


def _slot_summary(slot: str, graph: dict[str, Any]) -> dict[str, Any]:
    expansion = _SLOT_EXPANSIONS[slot]
    counts = dict(graph.get("record_counts") or {})
    count_key = expansion["record_kind"]
    if count_key == "trust_update_preflight":
        current_count = 0
    else:
        current_count = int(counts.get(count_key, 0) or 0)
    return {
        "slot": slot,
        "record_kind": expansion["record_kind"],
        "current_count": current_count,
        "recommended_write_tool": expansion["recommended_write_tool"],
        "expand_with": "aitp_v5_expand_recording_slot",
        "read_only_at_this_layer": True,
        "can_update_claim_trust": False,
        "when_to_use": expansion["when_to_use"],
    }


def _recommended_slots_from_graph(graph: dict[str, Any]) -> list[str]:
    counts = dict(graph.get("record_counts") or {})
    gaps = list(graph.get("provenance_gaps") or [])
    moments = list(graph.get("recommended_moments") or [])
    slots: list[str] = []
    for gap in gaps:
        for entrypoint in gap.get("recommended_entrypoints", []) if isinstance(gap, dict) else []:
            slots.extend(_slots_for_entrypoint(str(entrypoint)))
    for moment in moments:
        if isinstance(moment, dict):
            for entrypoint in moment.get("recommended_entrypoints", []):
                slots.extend(_slots_for_entrypoint(str(entrypoint)))
    if int(counts.get("reference_location", 0) or 0) == 0:
        slots.append("reference_location")
    if int(counts.get("source_asset", 0) or 0) == 0:
        slots.append("source_asset")
    if int(counts.get("evidence", 0) or 0) == 0:
        slots.append("evidence")
    if int(counts.get("proof_obligation", 0) or 0) == 0:
        slots.append("proof_obligation")
    return _unique_slots(slots)


def _slots_for_entrypoint(entrypoint: str) -> list[str]:
    table = {
        "aitp_v5_record_reference_location": ["reference_location"],
        "aitp_v5_register_source_asset": ["source_asset"],
        "aitp_v5_capture_source_asset_auto": ["source_asset"],
        "aitp_v5_record_tool_run": ["tool_run"],
        "aitp_v5_capture_tool_run_auto": ["tool_run"],
        "aitp_v5_record_evidence": ["evidence"],
        "aitp_v5_record_code_state": ["code_state"],
        "aitp_v5_capture_code_state_auto": ["code_state"],
        "aitp_v5_attach_artifact": ["artifact"],
        "aitp_v5_record_physics_object": ["physics_object"],
        "aitp_v5_record_object_relation": ["object_relation"],
        "aitp_v5_record_research_route": ["research_route"],
        "aitp_v5_start_research_run": ["research_run"],
        "aitp_v5_record_research_run_event": ["research_run_event"],
        "aitp_v5_create_proof_obligation": ["proof_obligation"],
        "aitp_v5_record_source_reconstruction_review_result": ["source_reconstruction_review"],
        "aitp_v5_create_validation_contract": ["validation_contract"],
        "aitp_v5_record_validation_result": ["validation_result"],
        "aitp_v5_request_human_checkpoint": ["human_checkpoint"],
        "aitp_v5_record_sensemaking_report": ["sensemaking_report"],
        "aitp_v5_preflight_trust_update": ["trust_preflight"],
    }
    return table.get(entrypoint, [])


def _fill_known_field_hints(fields: list[str], focus: dict[str, Any]) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    for field in fields:
        value = ""
        if field in {"topic_id", "topic"}:
            value = focus.get("topic_id", "")
        elif field in {"claim_id", "claim"}:
            value = focus.get("claim_id", "")
        elif field in {"session_id", "session"}:
            value = focus.get("session_id", "")
        hints.append(
            {
                "name": field,
                "known_value": value,
                "source": "current_position" if value else "agent_or_human_must_supply",
            }
        )
    return hints


def _unknown_slot_expansion(session_id: str, slot: str) -> dict[str, Any]:
    return {
        "ok": False,
        "kind": "recording_slot_expansion",
        "slot": str(slot or ""),
        "session_id": str(session_id or ""),
        "requested_session_id": str(session_id or ""),
        "topic_id": "",
        "claim_id": "",
        "recommended_write_tool": "",
        "cli_template": "",
        "record_kind": "",
        "required_fields": [],
        "optional_fields": [],
        "recommended_links": [],
        "graph_edges_created": [],
        "when_to_use": "",
        "candidate_context": {},
        "recording_sequence": [],
        "trust_effect": {
            "writes_kernel_state": False,
            "can_update_claim_trust": False,
            "claim_trust_mutation": "none",
            "trust_preflight_required_for_trust_change": False,
        },
        "warnings": [f"unknown slot; supported slots are: {', '.join(_FIRST_LEVEL_SLOT_ORDER)}"],
        "verify_with": "aitp_v5_verify_recording_effect",
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _slot_warnings(slot: str) -> list[str]:
    warnings = [
        "slot expansion is read-only guidance; it does not write a record",
        "verify with aitp_v5_verify_recording_effect after the typed write/preflight tool returns",
    ]
    if slot in {"reference_location", "source_asset", "sensemaking_report", "research_route", "research_run", "research_run_event"}:
        warnings.append("this record is orientation/process context and is not claim evidence by itself")
    if slot == "trust_preflight":
        warnings.append("preflight cannot apply trust; trust application remains excluded from host bridge targets")
    if slot == "evidence":
        warnings.append("evidence records should point to source/tool/validation/artifact provenance where available")
    if slot == "source_reconstruction_review":
        warnings.append("source reconstruction review records audit reconstructability and do not promote claim trust")
    if slot == "validation_result":
        warnings.append("validation results should be tied to an explicit validation contract and tool run")
    return warnings


def _verification_failures(
    expected_refs: list[str],
    missing_refs: list[str],
    before_node_ids: list[str],
    new_node_ids: list[str],
    found_refs: list[str],
) -> list[str]:
    failures: list[str] = []
    if expected_refs and missing_refs:
        failures.append("some expected refs were not found in the typed store")
    if before_node_ids and not new_node_ids and not found_refs:
        failures.append("no new graph nodes were observed and no expected refs were confirmed")
    return failures
