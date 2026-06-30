"""Read-only compiler from research records to reusable-block candidates."""

from __future__ import annotations

import json
import re
from typing import Any

from brain.v5.brief import build_execution_brief
from brain.v5.claim_relation_map import build_claim_relation_map
from brain.v5.models import ClaimRecord
from brain.v5.objective_graph import build_objective_graph
from brain.v5.output_stability import load_final_output_profile
from brain.v5.paths import WorkspacePaths
from brain.v5.recovery_session import recover_session_binding_for_read
from brain.v5.store import list_valid_records

_DEFAULT_LIMIT = 8
_CANDIDATE_KINDS = {
    "workflow_recipe_candidate",
    "physics_semantic_fragment_candidate",
    "method_capsule_candidate",
    "failure_playbook_candidate",
    "handoff_profile_candidate",
}


def build_research_distillation_candidates(
    ws: WorkspacePaths,
    session_id: str,
    *,
    limit: int = _DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Build reusable-workflow and physics-fragment candidates from typed records.

    This surface intentionally does not materialize skills, L2 memories, or trust
    updates. It only reports whether the recorded research has enough structured
    support to draft a reusable block, and which typed records are still missing.
    """

    recovered = recover_session_binding_for_read(ws, session_id)
    session = recovered.session
    objective_graph = build_objective_graph(ws, session_id)
    execution_brief = build_execution_brief(ws, session_id)
    relation_map = execution_brief.get("claim_relation_map") or build_claim_relation_map(ws, session_id)
    claims_by_id = {
        claim["claim_id"]: claim
        for claim in objective_graph.get("claims", [])
        if isinstance(claim, dict) and claim.get("claim_id")
    }
    active_claim = claims_by_id.get(session.active_claim, {})
    iteration_items, read_errors = _read_iteration_items(ws, session.topic_id)
    profile = load_final_output_profile(ws, session.topic_id)

    candidates: list[dict[str, Any]] = []
    for item in iteration_items[-max(1, limit):]:
        claim = claims_by_id.get(str(item.get("claim_id") or ""), active_claim)
        candidates.append(_iteration_candidate(item, claim=claim, relation_map=relation_map))
    if profile.get("present"):
        candidates.append(_profile_candidate(profile, active_claim))
    if not candidates and active_claim:
        candidates.append(_claim_candidate(active_claim, relation_map=relation_map))

    candidates = candidates[: max(1, limit)]
    candidate_source_records = _candidate_source_records(candidates)
    source_records = {
        "sessions": [session.session_id],
        "requested_sessions": [recovered.requested_session_id],
        "topics": [session.topic_id],
        "claims": _dedupe(
            [session.active_claim]
            + list(candidate_source_records.get("claims", []))
            + [claim.get("claim_id", "") for claim in objective_graph.get("claims", []) if isinstance(claim, dict)]
        ),
        "run_iterations": list(candidate_source_records.get("run_iterations", [])),
        "artifacts": list(candidate_source_records.get("artifacts", [])),
        "source_refs": list(candidate_source_records.get("source_refs", [])),
        "derived_surfaces": [
            "objective_graph",
            "execution_brief",
            "claim_relation_map",
            "run_iteration_journals",
            "final_output_profile",
        ],
    }

    return {
        "ok": True,
        "kind": "research_distillation_candidates",
        "topic_id": session.topic_id,
        "session_id": session.session_id,
        "requested_session_id": recovered.requested_session_id,
        "recovery_selection_source": recovered.recovery_selection_source,
        "active_claim_id": session.active_claim,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "gate_policy": _gate_policy(),
        "summary": _summary(candidates),
        "next_valid_actions": _next_valid_actions(candidates, relation_map),
        "source_records": source_records,
        "read_errors": read_errors,
        "distillation_boundary": {
            "does_not_create_skills": True,
            "does_not_create_l2_memory": True,
            "does_not_update_claim_trust": True,
            "requires_human_review_before_materialization": True,
            "compile_is_not_summary": (
                "The compiler checks typed dependency, provenance, validation, "
                "scope, and failure-boundary fields before marking a reusable draft."
            ),
        },
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _iteration_candidate(
    item: dict[str, Any],
    *,
    claim: dict[str, Any],
    relation_map: dict[str, Any],
) -> dict[str, Any]:
    text = _candidate_text(item, claim)
    candidate_kind = _infer_candidate_kind(text)
    evidence_refs = _typed_refs(item, prefixes=("evidence:", "evidence-"))
    source_refs = _dedupe(
        list(item.get("source_refs") or [])
        + list((item.get("source_records") or {}).get("source_refs") or [])
    )
    artifact_refs = _dedupe(list(item.get("l4_artifact_refs") or []))
    gates = _quality_gates(
        candidate_kind=candidate_kind,
        claim=claim,
        relation_map=relation_map,
        plan_summary=str(item.get("plan_summary") or ""),
        l3_synthesis_summary=str(item.get("l3_synthesis_summary") or ""),
        l4_return_summary=str(item.get("l4_return_summary") or ""),
        decision=str(item.get("decision") or ""),
        checks=list(item.get("checks") or []),
        deliverables=list(item.get("deliverables") or []),
        stop_rules=list(item.get("stop_rules") or []),
        source_refs=source_refs,
        artifact_refs=artifact_refs,
        evidence_refs=evidence_refs,
    )
    missing = _missing_requirements(gates)
    return {
        "candidate_id": _candidate_id("distill", item.get("run_id"), item.get("iteration_id")),
        "candidate_kind": candidate_kind,
        "title": _title_from_iteration(item),
        "summary": _excerpt(
            item.get("l3_synthesis_summary")
            or item.get("l4_return_summary")
            or item.get("plan_summary")
            or "",
            limit=360,
        ),
        "distillation_state": _distillation_state(candidate_kind, missing, relation_map),
        "can_draft_reusable_block": not missing,
        "can_materialize_without_human_review": False,
        "can_promote_claim_trust": False,
        "target_surfaces": _target_surfaces(candidate_kind),
        "quality_gates": gates,
        "missing_requirements": missing,
        "recommended_record_actions": _recommended_record_actions(candidate_kind, missing),
        "reuse_boundary": _reuse_boundary(claim, item, relation_map),
        "trust_boundary": "Candidate only; use typed records, validation results, and human gates before promotion.",
        "source_records": {
            "claims": [str(item.get("claim_id") or claim.get("claim_id") or "")] if (item.get("claim_id") or claim.get("claim_id")) else [],
            "run_iterations": [f"{item.get('run_id', '')}:{item.get('iteration_id', '')}"],
            "artifacts": artifact_refs,
            "source_refs": source_refs,
            "evidence": evidence_refs,
        },
        "orientation_only": True,
    }


def _profile_candidate(profile: dict[str, Any], claim: dict[str, Any]) -> dict[str, Any]:
    stable_sections = list(profile.get("stable_sections") or [])
    flexible_sections = list(profile.get("flexible_sections") or [])
    gates = [
        _gate("stable_output_shape", bool(stable_sections), stable_sections, ["stable_sections"]),
        _gate("audience_and_scope", bool(profile.get("audience")), [str(profile.get("audience") or "")], ["audience"]),
        _gate("change_policy", bool(profile.get("change_policy")), [str(profile.get("change_policy") or "")], ["change_policy"]),
        _gate(
            "trust_boundary",
            profile.get("can_update_claim_trust") is False,
            ["can_update_claim_trust=false"],
            ["explicit no-trust boundary"],
        ),
    ]
    missing = _missing_requirements(gates)
    return {
        "candidate_id": _candidate_id("distill-profile", profile.get("profile_id"), profile.get("output_version")),
        "candidate_kind": "handoff_profile_candidate",
        "title": str(profile.get("output_version") or "final output profile"),
        "summary": _excerpt("; ".join(stable_sections[:4]) or str(profile.get("audience") or ""), limit=360),
        "distillation_state": "draftable" if not missing else "needs_more_records",
        "can_draft_reusable_block": not missing,
        "can_materialize_without_human_review": False,
        "can_promote_claim_trust": False,
        "target_surfaces": ["final_output_profile", "strategy_memory_record", "lane_exemplar_record"],
        "quality_gates": gates,
        "missing_requirements": missing,
        "recommended_record_actions": _recommended_record_actions("handoff_profile_candidate", missing),
        "reuse_boundary": {
            "scope": str(claim.get("scope") or ""),
            "non_claims": _as_list(claim.get("non_claims")),
            "change_policy": str(profile.get("change_policy") or ""),
            "flexible_sections": flexible_sections,
        },
        "trust_boundary": "Output profile only; stable report shape does not support claim trust.",
        "source_records": {
            "claims": [str(claim.get("claim_id") or "")] if claim.get("claim_id") else [],
            "run_iterations": [],
            "artifacts": [str(profile.get("artifact_path") or "")] if profile.get("artifact_path") else [],
            "source_refs": [],
            "evidence": [],
        },
        "orientation_only": True,
    }


def _claim_candidate(claim: dict[str, Any], *, relation_map: dict[str, Any]) -> dict[str, Any]:
    gates = _quality_gates(
        candidate_kind="physics_semantic_fragment_candidate",
        claim=claim,
        relation_map=relation_map,
        plan_summary="",
        l3_synthesis_summary=str(claim.get("statement") or ""),
        l4_return_summary="",
        decision="",
        checks=[],
        deliverables=[],
        stop_rules=[],
        source_refs=[],
        artifact_refs=[],
        evidence_refs=[],
    )
    missing = _missing_requirements(gates)
    return {
        "candidate_id": _candidate_id("distill-claim", claim.get("claim_id")),
        "candidate_kind": "physics_semantic_fragment_candidate",
        "title": _excerpt(claim.get("statement") or claim.get("claim_id") or "claim", limit=120),
        "summary": _excerpt(claim.get("statement") or "", limit=360),
        "distillation_state": _distillation_state("physics_semantic_fragment_candidate", missing, relation_map),
        "can_draft_reusable_block": not missing,
        "can_materialize_without_human_review": False,
        "can_promote_claim_trust": False,
        "target_surfaces": _target_surfaces("physics_semantic_fragment_candidate"),
        "quality_gates": gates,
        "missing_requirements": missing,
        "recommended_record_actions": _recommended_record_actions("physics_semantic_fragment_candidate", missing),
        "reuse_boundary": _reuse_boundary(claim, {}, relation_map),
        "trust_boundary": "Claim candidate only; relation map and trust audit decide promotion readiness.",
        "source_records": {
            "claims": [str(claim.get("claim_id") or "")],
            "run_iterations": [],
            "artifacts": [],
            "source_refs": [],
            "evidence": [],
        },
        "orientation_only": True,
    }


def _quality_gates(
    *,
    candidate_kind: str,
    claim: dict[str, Any],
    relation_map: dict[str, Any],
    plan_summary: str,
    l3_synthesis_summary: str,
    l4_return_summary: str,
    decision: str,
    checks: list[str],
    deliverables: list[str],
    stop_rules: list[str],
    source_refs: list[str],
    artifact_refs: list[str],
    evidence_refs: list[str],
) -> list[dict[str, Any]]:
    claim_boundary = _claim_boundary(claim, relation_map)
    validation_refs = _validation_refs(relation_map)
    relation_boundaries = _relation_boundaries(relation_map)
    return [
        _gate(
            "scoped_problem",
            bool(claim.get("claim_id") and (claim.get("scope") or claim.get("statement"))),
            _dedupe([claim.get("claim_id", ""), claim.get("scope", ""), claim.get("statement", "")]),
            ["claim_id", "claim scope or statement"],
        ),
        _gate(
            "reproducible_steps",
            bool(plan_summary and (checks or deliverables)),
            _dedupe([plan_summary] + checks[:3] + deliverables[:3]),
            ["plan_summary plus checks or deliverables"],
        ),
        _gate(
            "provenance_refs",
            bool(source_refs or artifact_refs or evidence_refs),
            _dedupe(source_refs[:4] + artifact_refs[:4] + evidence_refs[:4]),
            ["source_refs, artifact refs, or evidence refs"],
        ),
        _gate(
            "validation_boundary",
            bool(checks or validation_refs or l4_return_summary),
            _dedupe(checks[:4] + validation_refs[:4] + [l4_return_summary]),
            ["checks, validation result refs, or L4 return summary"],
        ),
        _gate(
            "failure_modes_and_stop_rules",
            bool(stop_rules or claim_boundary or relation_boundaries),
            _dedupe(stop_rules[:4] + claim_boundary[:4] + relation_boundaries[:4]),
            ["stop_rules, non_claims, strongest_failure_mode, or relation-map cannot_say/blockers"],
        ),
        _gate(
            "reuse_boundary",
            bool(decision or stop_rules or claim.get("scope") or claim.get("non_claims")),
            _dedupe([decision, claim.get("scope", "")] + _as_list(claim.get("non_claims")) + stop_rules[:3]),
            ["decision, scope, non_claims, or stop_rules"],
        ),
        _gate(
            "physics_semantics",
            bool(
                candidate_kind not in {"physics_semantic_fragment_candidate", "method_capsule_candidate"}
                or l3_synthesis_summary
                or claim.get("statement")
            ),
            _dedupe([l3_synthesis_summary, claim.get("statement", "")]),
            ["l3_synthesis_summary or claim statement"],
        ),
    ]


def _gate(name: str, passed: bool, evidence: list[str], missing: list[str]) -> dict[str, Any]:
    clean_evidence = _dedupe([_excerpt(value, limit=220) for value in evidence if str(value).strip()])
    return {
        "gate": name,
        "status": "passed" if passed else "missing",
        "evidence": clean_evidence,
        "missing": [] if passed else missing,
    }


def _missing_requirements(gates: list[dict[str, Any]]) -> list[str]:
    missing: list[str] = []
    for gate in gates:
        if gate.get("status") == "missing":
            missing.append(str(gate.get("gate") or "unknown_gate"))
    return missing


def _distillation_state(candidate_kind: str, missing: list[str], relation_map: dict[str, Any]) -> str:
    if missing:
        return "needs_more_records"
    blockers = list(relation_map.get("current_blockers") or [])
    if candidate_kind == "physics_semantic_fragment_candidate" and blockers:
        return "semantic_fragment_with_open_gaps"
    return "draftable"


def _target_surfaces(candidate_kind: str) -> list[str]:
    if candidate_kind == "workflow_recipe_candidate":
        return ["lane_exemplar_record", "tool_recipe_record", "strategy_memory_record"]
    if candidate_kind == "physics_semantic_fragment_candidate":
        return ["authority_record", "physics_object_record", "object_relation_record", "sensemaking_report_record"]
    if candidate_kind == "failure_playbook_candidate":
        return ["strategy_memory_record", "proof_obligation_record", "failure_mode_review_packet"]
    if candidate_kind == "handoff_profile_candidate":
        return ["final_output_profile", "strategy_memory_record", "lane_exemplar_record"]
    return ["lane_exemplar_record", "tool_recipe_record", "sensemaking_report_record", "validation_contract_record"]


def _recommended_record_actions(candidate_kind: str, missing: list[str]) -> list[dict[str, str]]:
    if missing:
        return [
            {
                "action": "complete_first_layer_records",
                "why": f"missing gates: {', '.join(missing)}",
                "surface": "typed_records",
            }
        ]
    if candidate_kind == "physics_semantic_fragment_candidate":
        return [
            {"action": "draft_sensemaking_report", "why": "semantic gates are explicit", "surface": "sensemaking_report_record"},
            {"action": "record_physics_objects_or_relations", "why": "preserve physics semantics as typed graph nodes", "surface": "physics_object_record/object_relation_record"},
        ]
    if candidate_kind == "failure_playbook_candidate":
        return [
            {"action": "record_strategy_memory", "why": "failure boundary is reusable for later sessions", "surface": "strategy_memory_record"},
            {"action": "request_failure_mode_review", "why": "human/adversarial review should check failure basis", "surface": "failure_mode_review_packet"},
        ]
    return [
        {"action": "draft_lane_exemplar", "why": "workflow gates are explicit enough for a reviewed exemplar", "surface": "lane_exemplar_record"},
        {"action": "draft_tool_recipe_if_executable", "why": "turn repeated commands/checks into a reusable recipe after review", "surface": "tool_recipe_record"},
    ]


def _reuse_boundary(claim: dict[str, Any], item: dict[str, Any], relation_map: dict[str, Any]) -> dict[str, Any]:
    conclusion = relation_map.get("current_conclusion") if isinstance(relation_map.get("current_conclusion"), dict) else {}
    return {
        "scope": str(claim.get("scope") or ""),
        "non_claims": _as_list(claim.get("non_claims")),
        "confidence_state": str(claim.get("confidence_state") or ""),
        "strongest_failure_mode": str(claim.get("strongest_failure_mode") or ""),
        "decision": str(item.get("decision") or ""),
        "stop_rules": list(item.get("stop_rules") or []),
        "cannot_say": list(conclusion.get("cannot_say") or [])[:6],
        "current_blockers": list(relation_map.get("current_blockers") or [])[:6],
    }


def _gate_policy() -> list[dict[str, str]]:
    return [
        {"gate": "scoped_problem", "required_for": "all candidates"},
        {"gate": "reproducible_steps", "required_for": "workflow and method candidates"},
        {"gate": "provenance_refs", "required_for": "all candidates"},
        {"gate": "validation_boundary", "required_for": "all candidates"},
        {"gate": "failure_modes_and_stop_rules", "required_for": "all candidates"},
        {"gate": "reuse_boundary", "required_for": "all candidates"},
        {"gate": "physics_semantics", "required_for": "physics semantic fragments and method capsules"},
    ]


def _next_valid_actions(candidates: list[dict[str, Any]], relation_map: dict[str, Any]) -> list[str]:
    actions = list(relation_map.get("next_valid_actions") or [])
    for candidate in candidates:
        if candidate.get("can_draft_reusable_block"):
            actions.append(f"review candidate {candidate.get('candidate_id')} before materializing reusable block")
        else:
            actions.append(f"complete missing gates for {candidate.get('candidate_id')}: {', '.join(candidate.get('missing_requirements') or [])}")
    return _dedupe([_excerpt(action, limit=240) for action in actions if action])


def _summary(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    state_counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    draftable = 0
    for candidate in candidates:
        state = str(candidate.get("distillation_state") or "")
        kind = str(candidate.get("candidate_kind") or "")
        state_counts[state] = state_counts.get(state, 0) + 1
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        if candidate.get("can_draft_reusable_block"):
            draftable += 1
    return {
        "candidate_count": len(candidates),
        "draftable_count": draftable,
        "needs_more_records_count": state_counts.get("needs_more_records", 0),
        "state_counts": state_counts,
        "kind_counts": kind_counts,
    }


def _read_iteration_items(ws: WorkspacePaths, topic_id: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    run_root = ws.topic_dir(topic_id) / "L3" / "runs"
    if not run_root.exists():
        return [], []
    items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for path in sorted(run_root.glob("*/iteration_journal.json")):
        try:
            journal = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append({"path": str(path), "error_type": type(exc).__name__, "message": _excerpt(str(exc), limit=240)})
            continue
        for item in journal.get("iterations", []):
            if not isinstance(item, dict):
                continue
            item = dict(item)
            item.setdefault("run_id", str(journal.get("run_id") or path.parent.name))
            item.setdefault("topic_id", str(journal.get("topic_id") or topic_id))
            items.append(item)
    return items, errors


def _claim_boundary(claim: dict[str, Any], relation_map: dict[str, Any]) -> list[str]:
    conclusion = relation_map.get("current_conclusion") if isinstance(relation_map.get("current_conclusion"), dict) else {}
    return _dedupe(
        _as_list(claim.get("non_claims"))
        + [str(claim.get("strongest_failure_mode") or "")]
        + list(conclusion.get("cannot_say") or [])[:4]
    )


def _relation_boundaries(relation_map: dict[str, Any]) -> list[str]:
    conclusion = relation_map.get("current_conclusion") if isinstance(relation_map.get("current_conclusion"), dict) else {}
    return _dedupe(list(relation_map.get("current_blockers") or [])[:4] + list(conclusion.get("cannot_say") or [])[:4])


def _validation_refs(relation_map: dict[str, Any]) -> list[str]:
    source_records = relation_map.get("source_records") if isinstance(relation_map.get("source_records"), dict) else {}
    refs = []
    for key in ("validation_results", "validation_contracts"):
        refs.extend(str(value) for value in source_records.get(key, []) if value)
    return _dedupe(refs)


def _candidate_text(item: dict[str, Any], claim: dict[str, Any]) -> str:
    groups = [
        [item.get("plan_summary"), item.get("l3_synthesis_summary"), item.get("l4_return_summary"), item.get("decision")],
        item.get("checks") or [],
        item.get("deliverables") or [],
        item.get("stop_rules") or [],
        [claim.get("statement"), claim.get("scope"), claim.get("strongest_failure_mode")],
    ]
    return " ".join(str(value or "") for group in groups for value in group).lower()


def _infer_candidate_kind(text: str) -> str:
    workflow = _contains_any(text, ("workflow", "script", "pipeline", "sbatch", "plot", "parse", "compiled", "job", "run", "recipe", "audit", "reproduce", "refresh"))
    physics = _contains_any(text, ("proof", "theorem", "lemma", "derive", "formula", "operator", "schur", "yangian", "symmetry", "kernel", "rank", "green", "self-energy", "pade", "qsgw", "rational"))
    failure = _contains_any(text, ("failure", "failed", "bias", "warning", "contradict", "deprecated", "blocked", "does not prove", "do not", "not prove"))
    if failure and not workflow and not physics:
        return "failure_playbook_candidate"
    if workflow and physics:
        return "method_capsule_candidate"
    if physics:
        return "physics_semantic_fragment_candidate"
    if workflow:
        return "workflow_recipe_candidate"
    return "workflow_recipe_candidate"


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _typed_refs(item: dict[str, Any], *, prefixes: tuple[str, ...]) -> list[str]:
    refs: list[str] = []
    groups = [
        item.get("source_refs") or [],
        item.get("l4_artifact_refs") or [],
        (item.get("source_records") or {}).get("source_refs") or [],
    ]
    for value in [ref for group in groups for ref in group]:
        text = str(value or "")
        if any(text.startswith(prefix) for prefix in prefixes):
            refs.append(text.removeprefix("evidence:"))
    return _dedupe(refs)


def _title_from_iteration(item: dict[str, Any]) -> str:
    iteration_id = str(item.get("iteration_id") or "iteration")
    summary = str(item.get("plan_summary") or item.get("l3_synthesis_summary") or "")
    return f"{iteration_id}: {_excerpt(summary, limit=96)}" if summary else iteration_id


def _candidate_source_records(candidates: list[dict[str, Any]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"claims": [], "run_iterations": [], "artifacts": [], "source_refs": []}
    for candidate in candidates:
        source_records = candidate.get("source_records") if isinstance(candidate.get("source_records"), dict) else {}
        for key in out:
            out[key].extend(str(value) for value in source_records.get(key, []) if value)
    return {key: _dedupe(values) for key, values in out.items()}


def _candidate_id(prefix: str, *parts: Any) -> str:
    raw = "-".join(str(part or "") for part in parts if str(part or ""))
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", raw).strip(".-").lower()
    slug = slug[:120] or "candidate"
    return f"{prefix}-{slug}"


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in out:
            out.append(text)
    return out


def _excerpt(value: Any, *, limit: int = 180) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def list_topic_claim_records(ws: WorkspacePaths, topic_id: str) -> list[ClaimRecord]:
    """Expose a small helper for tests and downstream read-only integrations."""

    return [claim for claim in list_valid_records(ws.registry_dir("claims"), ClaimRecord) if claim.topic_id == topic_id]
