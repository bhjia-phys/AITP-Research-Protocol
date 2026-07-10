"""Projection helpers from a bounded context bundle to the legacy pack shape."""

from __future__ import annotations

import re
from typing import Any

from brain.v5.context_compiler import estimate_context_tokens


def compact_from_bundle(bundle) -> dict[str, Any]:
    boundary = bundle.current_boundary
    relevant_claims = []
    if boundary.get("claim_id"):
        relevant_claims.append(
            {
                "claim_id": boundary.get("claim_id"),
                "statement": boundary.get("statement"),
                "confidence_state": boundary.get("confidence_state"),
                "active_uncertainty": boundary.get("active_uncertainty"),
                "scope": boundary.get("scope"),
                "lifecycle_status": "active",
            }
        )
    for candidate in bundle.candidate_summaries:
        if candidate.get("family") != "claims":
            continue
        claim_id = candidate.get("claim_id")
        if not claim_id or any(item.get("claim_id") == claim_id for item in relevant_claims):
            continue
        relevant_claims.append(
            {
                "claim_id": claim_id,
                "statement": candidate.get("title"),
                "confidence_state": candidate.get("status") or "unknown",
                "active_uncertainty": "exact expansion required",
                "lifecycle_status": "active",
            }
        )
    uncertainty = str(boundary.get("active_uncertainty") or "")
    blockers = list(bundle.read_errors)
    if bundle.index_status != "fresh":
        blockers.append("stale index: prior-result recall is partial")
    if uncertainty:
        blockers.append(uncertainty)
    artifacts = [
        candidate
        for candidate in bundle.candidate_summaries
        if candidate.get("family") == "artifacts"
    ][:5]
    return {
        "session_id": bundle.session_id,
        "topic_id": bundle.topic_id,
        "current_objective": bundle.current_objective,
        "active_work_package": {
            "work_package_id": f"claim:{boundary.get('claim_id')}" if boundary.get("claim_id") else "",
            "title": boundary.get("statement") or bundle.current_objective.get("title"),
            "claim_ids": [boundary.get("claim_id")] if boundary.get("claim_id") else [],
            "status": "active",
        },
        "relevant_claims": relevant_claims[:5],
        "can_say": [],
        "cannot_say": [
            "compiled summaries cannot establish evidence, validation, or claim trust",
            *([uncertainty] if uncertainty else []),
        ],
        "blockers": blockers[:6],
        "previous_failed_attempts": _previous_failed_attempts(bundle.candidate_summaries),
        "next_valid_actions": [
            "expand the relevant typed record refs before trust-sensitive conclusions",
        ],
        "recent_relevant_artifacts": artifacts,
        "relation_map_scope": "active_claim_only",
        "not_authoritative_for_current_goal_if_rebind_needed": False,
        "warnings": [],
        "active_claim_focus_reconciliation": {},
        "lines": bundle.markdown.splitlines(),
        "expand": {
            "full_execution_brief_cli": f"aitp-v5 brief {bundle.session_id}",
            "full_relation_map_cli": f"aitp-v5 relation-map {bundle.session_id}",
            "research_timeline_cli": f"aitp-v5 timeline {bundle.session_id}",
            "objective_graph_cli": f"aitp-v5 status objective-graph {bundle.session_id}",
            "mcp_full_execution_brief": "aitp_v5_get_execution_brief",
            "mcp_full_relation_map": "aitp_v5_get_claim_relation_map",
            "mcp_research_timeline": "aitp_v5_get_research_timeline",
            "mcp_objective_graph": "aitp_v5_get_objective_graph",
        },
        "source_records": {
            "record_refs": list(bundle.record_refs),
            "derived_surfaces": ["query_index", "context_compiler"],
        },
    }


def compiler_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    record_ref = str(candidate.get("record_ref") or "")
    return {
        "candidate_id": record_ref,
        "candidate_kind": str(candidate.get("family") or "typed_record"),
        "title": str(candidate.get("title") or record_ref),
        "distillation_state": "needs_more_records",
        "can_draft_reusable_block": False,
        "can_materialize_without_human_review": False,
        "can_promote_claim_trust": False,
        "missing_requirements": [
            "exact typed-record expansion",
            "human review before reusable materialization",
        ],
        "trust_boundary": "orientation_only_exact_expansion_required",
        "source_records": {"record_refs": [record_ref]},
        "orientation_only": True,
    }


def _previous_failed_attempts(candidates) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        fields = candidate.get("summary_fields")
        selected = fields if isinstance(fields, dict) else {}
        status = str(candidate.get("status") or selected.get("evidence_status") or "").lower()
        text = " ".join(
            str(value)
            for value in (
                selected.get("summary"),
                selected.get("outputs"),
                selected.get("pivot_reason"),
                selected.get("failure_modes"),
            )
            if value
        )
        superseded = bool(selected.get("superseded_by"))
        failed = status in {"failed", "fail", "negative", "invalid", "contradicted"}
        not_testing = any(
            marker in text.lower()
            for marker in ("does not test", "runtime failure", "setup failure", "wrong route")
        )
        if not (failed or superseded or not_testing):
            continue
        record_ref = str(candidate.get("record_ref") or "")
        record_id = record_ref.partition(":")[2]
        classification = (
            "superseded_or_duplicate_route"
            if superseded
            else "failed_attempt_not_testing_claim"
            if not_testing
            else "contradicted_or_failed_claim_route"
        )
        rows.append(
            {
                "record_ref": record_ref,
                "record_kind": str(candidate.get("family") or ""),
                "record_id": record_id,
                "classification": classification,
                "status": status,
                "summary": text[:240],
                "continuation_boundary": "orientation_only_exact_expansion_required",
                "can_update_claim_trust": False,
            }
        )
    return rows[:6]


def distillation_from_candidates(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "summary": {
            "candidate_count": len(candidates),
            "draftable_count": 0,
            "needs_more_records_count": len(candidates),
        },
        "top_candidates": candidates,
        "gate_policy": [
            "exact records and validation must be reviewed before skill or memory materialization",
        ],
        "next_valid_actions": ["expand candidate record refs"],
        "distillation_boundary": {
            "source": "compiled_candidate_projection",
            "orientation_only": True,
        },
    }


def focus_reconciliation_from_bundle(
    bundle,
    *,
    objective_text: str,
    user_goal: str,
) -> dict[str, Any]:
    goal = " ".join(part for part in (objective_text, user_goal) if part).strip()
    active_id = str(bundle.current_boundary.get("claim_id") or "")
    candidates = [
        candidate
        for candidate in bundle.candidate_summaries
        if candidate.get("family") == "claims" and candidate.get("claim_id") != active_id
    ]
    if not goal or not candidates:
        return {
            "status": "no_active_claim_focus_drift",
            "active_claim": {"claim_id": active_id},
            "candidate_sibling_claims": [],
            "orientation_only": True,
        }
    goal_terms = set(_focus_terms(goal))
    active_overlap = len(goal_terms.intersection(_focus_terms(bundle.current_boundary.get("statement") or "")))
    ranked = sorted(
        (
            (len(goal_terms.intersection(_focus_terms(candidate.get("title") or ""))), candidate)
            for candidate in candidates
        ),
        key=lambda item: (-item[0], str(item[1].get("claim_id") or "")),
    )
    best_score, best = ranked[0]
    drift = best_score >= 2 and best_score > active_overlap
    return {
        "status": "active_claim_focus_drift_detected" if drift else "no_active_claim_focus_drift",
        "warning_code": "active_claim_focus_drift_detected" if drift else "",
        "active_claim": {"claim_id": active_id},
        "candidate_sibling_claims": (
            [
                {
                    "claim_id": best.get("claim_id"),
                    "statement_excerpt": best.get("title"),
                    "record_ref": best.get("record_ref"),
                }
            ]
            if drift
            else []
        ),
        "orientation_only": True,
    }


def bounded_context_lines(
    lines: list[str],
    *,
    line_limit: int,
    max_bytes: int,
    max_tokens: int,
) -> list[str]:
    accepted: list[str] = []
    for line in lines[:line_limit]:
        candidate = "\n".join([*accepted, line]) + "\n"
        if len(candidate.encode("utf-8")) > max_bytes or estimate_context_tokens(candidate) > max_tokens:
            break
        accepted.append(line)
    return accepted


def _focus_terms(text: Any) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z0-9_]+|[\u3400-\u4dbf\u4e00-\u9fff]", str(text or "").lower()))
