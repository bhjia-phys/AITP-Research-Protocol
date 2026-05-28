"""Read-only vNext control-plane readiness manifest."""

from __future__ import annotations

from typing import Any

from brain.v5.lane_exemplars import build_lane_exemplar_manifest
from brain.v5.paths import WorkspacePaths
from brain.v5.public_surfaces import public_surface_names
from brain.v5.runtime_entrypoints import runtime_entrypoints

STABLE_OUTPUT_SPINE = [
    "core_claim_or_current_focus",
    "verified_or_validated_content",
    "hypotheses_uncertainty_and_known_failure_modes",
    "aitp_records_written_or_referenced",
    "next_actions",
    "long_term_memory_candidates_and_non_promotable_content",
]


def build_vnext_readiness_manifest(ws: WorkspacePaths) -> dict[str, Any]:
    """Summarize vNext control-plane implementation without promoting content."""

    entrypoints = runtime_entrypoints()
    surfaces = set(public_surface_names())
    lane_manifest = build_lane_exemplar_manifest(ws)
    workstreams = [
        _workstream(
            "research_intent_gate",
            "phase_1_research_intent_and_steering",
            ["record_research_intent_packet"],
            ["research_intent_packet"],
            "new or materially redefined topics enter an idea packet before execution",
            entrypoints,
            surfaces,
        ),
        _workstream(
            "steering_surface_hardening",
            "phase_1_research_intent_and_steering",
            ["materialize_steering_redirect"],
            ["steering_decision_record"],
            "material steering redirects land as durable topic runtime state",
            entrypoints,
            surfaces,
        ),
        _workstream(
            "operator_checkpoint_protocol",
            "phase_2_operator_checkpoint",
            ["request_operator_checkpoint", "answer_operator_checkpoint"],
            ["operator_checkpoint_record"],
            "human choices survive restarts as active checkpoint records",
            entrypoints,
            surfaces,
        ),
        _workstream(
            "topic_status_explainability",
            "phase_3_topic_status_explainability",
            ["topic_status"],
            ["topic_status_bundle"],
            "later sessions can read current route, blockers, evidence return, and operator needs",
            entrypoints,
            surfaces,
        ),
        _workstream(
            "run_iteration_continuity",
            "phase_3_topic_status_explainability",
            ["record_run_iteration"],
            ["run_iteration_record"],
            "one L3/L4/L3 run can expose per-iteration plan, return, and synthesis records",
            entrypoints,
            surfaces,
        ),
        _workstream(
            "strategy_memory",
            "phase_4_strategy_memory",
            ["record_strategy_memory"],
            ["strategy_memory_record"],
            "future bounded steps can reuse workflow lessons without treating them as L2 truth",
            entrypoints,
            surfaces,
        ),
        _workstream(
            "literature_intake_assistant",
            "literature_intake_assistant",
            ["suggest_literature_intake", "record_literature_candidate"],
            ["literature_intake_suggestion", "literature_intake_record_result"],
            "literature discoveries become reference candidates before evidence or trust changes",
            entrypoints,
            surfaces,
        ),
        _workstream(
            "human_output_stability",
            "human_output_stability",
            ["record_final_output_profile"],
            ["final_output_profile"],
            "final and handoff reports keep a versioned stable section spine",
            entrypoints,
            surfaces,
        ),
        _workstream(
            "adapter_bootstrap_conformance",
            "adapter_bootstrap_conformance",
            ["runtime_host_production_loop_audit", "final_engineering_readiness_audit"],
            ["runtime_host_production_loop_audit", "final_engineering_readiness_audit"],
            "Codex, Claude Code, and Kimi Code have priority-host readiness surfaces; OpenCode is deferred",
            entrypoints,
            surfaces,
            implemented_status="priority_hosts_ready_opencode_deferred",
        ),
    ]
    lane_stream = _lane_workstream(lane_manifest, entrypoints, surfaces)
    workstreams.append(lane_stream)
    phase_statuses = _phase_statuses(workstreams)
    missing_workstreams = [item["name"] for item in workstreams if item["status"] == "surface_gap"]
    backlog_workstreams = [item["name"] for item in workstreams if item["status"] == "backlog"]
    return {
        "kind": "vnext_readiness_manifest",
        "control_plane_status": _control_plane_status(missing_workstreams, backlog_workstreams),
        "phase_statuses": phase_statuses,
        "workstreams": workstreams,
        "missing_workstreams": missing_workstreams,
        "backlog_workstreams": backlog_workstreams,
        "lane_exemplar_manifest": lane_manifest,
        "stable_output_spine": list(STABLE_OUTPUT_SPINE),
        "stable_output_contract_doc": "docs/AITP_SPEC.md#human-facing-output-stability-contract",
        "priority_hosts": ["codex", "claude_code", "kimi_code"],
        "deferred_hosts": ["opencode"],
        "trust_update_forbidden": True,
        "truth_source": "runtime_entrypoint_catalog_and_typed_lane_exemplar_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def compact_vnext_readiness_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a host-friendly vNext readiness projection without bulky item lists."""

    lane_manifest = payload.get("lane_exemplar_manifest")
    if not isinstance(lane_manifest, dict):
        lane_manifest = {}
    return {
        "kind": "vnext_readiness_manifest_progress",
        "source_surface": "vnext_readiness_manifest",
        "control_plane_status": str(payload.get("control_plane_status") or ""),
        "phase_statuses": dict(payload.get("phase_statuses") or {}),
        "missing_workstreams": _limited_strings(payload.get("missing_workstreams"), limit=20),
        "backlog_workstreams": _limited_strings(payload.get("backlog_workstreams"), limit=20),
        "covered_lanes": _limited_strings(lane_manifest.get("covered_lanes"), limit=10),
        "missing_lanes": _limited_strings(lane_manifest.get("missing_lanes"), limit=10),
        "stable_output_spine": _limited_strings(payload.get("stable_output_spine"), limit=20),
        "stable_output_contract_doc": str(payload.get("stable_output_contract_doc") or ""),
        "priority_hosts": _limited_strings(payload.get("priority_hosts"), limit=10),
        "deferred_hosts": _limited_strings(payload.get("deferred_hosts"), limit=10),
        "trust_update_forbidden": bool(payload.get("trust_update_forbidden", False)),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def _workstream(
    name: str,
    phase: str,
    entrypoint_keys: list[str],
    surface_names: list[str],
    acceptance: str,
    entrypoints: dict[str, dict[str, Any]],
    surfaces: set[str],
    *,
    implemented_status: str = "implemented",
) -> dict[str, Any]:
    missing_entrypoints = [key for key in entrypoint_keys if key not in entrypoints]
    missing_surfaces = [surface for surface in surface_names if surface not in surfaces]
    status = implemented_status if not missing_entrypoints and not missing_surfaces else "surface_gap"
    return {
        "name": name,
        "phase": phase,
        "status": status,
        "runtime_entrypoints": list(entrypoint_keys),
        "surfaces": list(surface_names),
        "acceptance": acceptance,
        "missing_entrypoints": missing_entrypoints,
        "missing_surfaces": missing_surfaces,
        "can_update_claim_trust": False,
    }


def _lane_workstream(
    lane_manifest: dict[str, Any],
    entrypoints: dict[str, dict[str, Any]],
    surfaces: set[str],
) -> dict[str, Any]:
    stream = _workstream(
        "lane_exemplars",
        "phase_5_lane_exemplars",
        ["record_lane_exemplar", "lane_exemplar_manifest"],
        ["lane_exemplar_record", "lane_exemplar_manifest"],
        "toy numeric, semi-formal theory, and code-backed algorithm lanes each have accepted exemplars",
        entrypoints,
        surfaces,
    )
    if stream["status"] == "implemented" and lane_manifest.get("missing_lanes"):
        stream["status"] = "backlog"
    stream["covered_lanes"] = list(lane_manifest.get("covered_lanes") or [])
    stream["missing_lanes"] = list(lane_manifest.get("missing_lanes") or [])
    return stream


def _phase_statuses(workstreams: list[dict[str, Any]]) -> dict[str, str]:
    by_name = {item["name"]: item["status"] for item in workstreams}
    return {
        "phase_1_research_intent_and_steering": _combined(
            [by_name.get("research_intent_gate", ""), by_name.get("steering_surface_hardening", "")]
        ),
        "phase_2_operator_checkpoint": by_name.get("operator_checkpoint_protocol", ""),
        "phase_3_topic_status_explainability": _combined(
            [by_name.get("topic_status_explainability", ""), by_name.get("run_iteration_continuity", "")]
        ),
        "phase_4_strategy_memory": by_name.get("strategy_memory", ""),
        "phase_5_lane_exemplars": by_name.get("lane_exemplars", ""),
        "adapter_bootstrap_conformance": by_name.get("adapter_bootstrap_conformance", ""),
        "human_output_stability": by_name.get("human_output_stability", ""),
        "literature_intake_assistant": by_name.get("literature_intake_assistant", ""),
    }


def _combined(statuses: list[str]) -> str:
    if any(status == "surface_gap" for status in statuses):
        return "surface_gap"
    if any(status == "backlog" for status in statuses):
        return "backlog"
    return "implemented"


def _control_plane_status(missing_workstreams: list[str], backlog_workstreams: list[str]) -> str:
    if missing_workstreams:
        return "surface_gaps"
    if backlog_workstreams:
        return "ready_with_lane_exemplar_backlog"
    return "ready"


def _limited_strings(value: Any, *, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value[:limit] if str(item)]
