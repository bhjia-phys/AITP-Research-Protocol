"""Codex-friendly read-only context pack over AITP v5 research state."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from brain.v5.objective_graph import build_compact_brief
from brain.v5.paths import WorkspacePaths
from brain.v5.research_distillation import build_research_distillation_candidates

_DEFAULT_MAX_LINES = 60
_DEFAULT_CANDIDATE_LIMIT = 3


def build_aitp_context_pack(
    ws: WorkspacePaths,
    session_id: str,
    *,
    max_lines: int = _DEFAULT_MAX_LINES,
    candidate_limit: int = _DEFAULT_CANDIDATE_LIMIT,
    objective_text: str = "",
    user_goal: str = "",
) -> dict[str, Any]:
    """Build the bounded research-state slice intended for Codex turn input.

    This is not a memory, evidence, validation, or trust surface. It compiles the
    already-typed graph into a short, fingerprinted context fragment that a host
    runtime can inject once per changed research state and expand explicitly.
    """

    line_limit = max(12, min(int(max_lines), 80))
    candidate_limit = max(1, min(int(candidate_limit), 8))
    compact = build_compact_brief(
        ws,
        session_id,
        max_lines=min(line_limit, 40),
        objective_text=objective_text,
        user_goal=user_goal,
    )
    distillation = build_research_distillation_candidates(ws, session_id, limit=candidate_limit)
    top_candidates = [
        _candidate_summary(candidate)
        for candidate in list(distillation.get("candidates") or [])[:candidate_limit]
        if isinstance(candidate, dict)
    ]
    source_records = _merge_source_records(
        compact.get("source_records") if isinstance(compact.get("source_records"), dict) else {},
        distillation.get("source_records") if isinstance(distillation.get("source_records"), dict) else {},
        {
            "derived_surfaces": [
                "compact_execution_brief",
                "objective_graph",
                "research_distillation_candidates",
            ]
        },
    )

    payload: dict[str, Any] = {
        "ok": True,
        "kind": "aitp_context_pack",
        "context_pack_version": "v1",
        "designed_for_host": "codex",
        "session_id": str(compact.get("session_id") or ""),
        "topic_id": str(compact.get("topic_id") or ""),
        "current_objective": compact.get("current_objective") or {},
        "active_work_package": compact.get("active_work_package") or {},
        "relevant_claims": list(compact.get("relevant_claims") or []),
        "can_say": list(compact.get("can_say") or []),
        "cannot_say": list(compact.get("cannot_say") or []),
        "blockers": list(compact.get("blockers") or []),
        "next_valid_actions": list(compact.get("next_valid_actions") or []),
        "recent_relevant_artifacts": list(compact.get("recent_relevant_artifacts") or []),
        "relation_map_scope": str(compact.get("relation_map_scope") or "active_claim_only"),
        "not_authoritative_for_current_goal_if_rebind_needed": bool(
            compact.get("not_authoritative_for_current_goal_if_rebind_needed")
        ),
        "warnings": list(compact.get("warnings") or []),
        "active_claim_focus_reconciliation": compact.get("active_claim_focus_reconciliation") or {},
        "distillation_status": {
            "summary": distillation.get("summary") or {},
            "top_candidates": top_candidates,
            "gate_policy": list(distillation.get("gate_policy") or []),
            "next_valid_actions": list(distillation.get("next_valid_actions") or [])[:8],
        },
        "materialization_boundary": {
            **(distillation.get("distillation_boundary") or {}),
            "can_create_skill": False,
            "can_create_l2_memory": False,
            "can_update_claim_trust": False,
            "requires_human_review_before_materialization": True,
        },
        "injection_policy": {
            "host": "codex",
            "recommended_hook": "TurnInputContributor",
            "recommended_authority": "contextual_user_fragment",
            "max_lines": line_limit,
            "inject_when": [
                "session is first restored",
                "pack fingerprint changes",
                "user explicitly asks to restore AITP context",
            ],
            "avoid_reinjecting_when": [
                "same pack fingerprint is already present in the current turn context",
            ],
            "requires_explicit_expand_for": [
                "claim trust updates",
                "evidence support decisions",
                "validation status decisions",
                "full relation-map audit",
                "active claim rebind or claim split",
                "workflow or skill materialization",
            ],
        },
        "expand": {
            **(compact.get("expand") or {}),
            "context_pack_cli": f"aitp-v5 status context-pack {session_id}",
            "distillation_candidates_cli": f"aitp-v5 status distillation-candidates {session_id}",
            "mcp_context_pack": "aitp_v5_get_context_pack",
            "mcp_research_distillation_candidates": "aitp_v5_get_research_distillation_candidates",
            "mcp_detect_active_claim_focus_drift": "aitp_v5_detect_active_claim_focus_drift",
            "mcp_confirm_active_claim_rebind": "aitp_v5_confirm_active_claim_rebind",
        },
        "source_records": source_records,
        "read_errors": list(distillation.get("read_errors") or []),
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "can_materialize_without_human_review": False,
    }
    payload["context_lines"] = _context_lines(payload, compact)[:line_limit]
    payload["line_count"] = len(payload["context_lines"])
    payload["markdown"] = "\n".join(payload["context_lines"]) + "\n"
    payload["fingerprint"] = _fingerprint(payload)
    payload["pack_id"] = f"aitp-context-pack-{payload['session_id']}-{payload['fingerprint'][:12]}"
    return payload


def _candidate_summary(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": str(candidate.get("candidate_id") or ""),
        "candidate_kind": str(candidate.get("candidate_kind") or ""),
        "title": str(candidate.get("title") or ""),
        "distillation_state": str(candidate.get("distillation_state") or ""),
        "can_draft_reusable_block": bool(candidate.get("can_draft_reusable_block")),
        "can_materialize_without_human_review": False,
        "can_promote_claim_trust": False,
        "missing_requirements": list(candidate.get("missing_requirements") or []),
        "trust_boundary": str(candidate.get("trust_boundary") or ""),
        "source_records": candidate.get("source_records") or {},
        "orientation_only": True,
    }


def _context_lines(payload: dict[str, Any], compact: dict[str, Any]) -> list[str]:
    objective = payload.get("current_objective") or {}
    package = payload.get("active_work_package") or {}
    distillation = payload.get("distillation_status") or {}
    summary = distillation.get("summary") if isinstance(distillation.get("summary"), dict) else {}
    lines = [
        "AITP context pack for Codex turn input.",
        f"Session: {payload.get('session_id')} | Topic: {payload.get('topic_id')}",
        f"Current objective: {objective.get('title') or payload.get('topic_id')}",
        f"Active work package: {package.get('title') or 'none'}",
        "Boundary: orientation-only; cannot update claim trust, evidence, validation, L2 memory, or skills.",
        "",
    ]
    if payload.get("not_authoritative_for_current_goal_if_rebind_needed"):
        reconciliation = payload.get("active_claim_focus_reconciliation") or {}
        lines.extend(
            [
                "WARNING: active_claim_focus_drift_detected.",
                "The active-claim relation map is scoped to active_claim_only and may be stale for the current goal.",
                "Candidate sibling claims:",
            ]
        )
        candidates = list(reconciliation.get("candidate_sibling_claims") or [])[:3]
        if candidates:
            lines.extend(
                f"- {candidate.get('claim_id')}: {_excerpt(candidate.get('statement_excerpt') or '', limit=110)}"
                for candidate in candidates
            )
        else:
            lines.append("- none")
        lines.append("")
    lines.extend(list(compact.get("lines") or []))
    lines.append("")
    lines.append(
        "Reusable-block candidates: "
        f"{summary.get('draftable_count', 0)} draftable / "
        f"{summary.get('needs_more_records_count', 0)} need more records."
    )
    for candidate in distillation.get("top_candidates") or []:
        missing = ", ".join(candidate.get("missing_requirements") or [])
        state = candidate.get("distillation_state") or "unknown"
        lines.append(
            f"- {candidate.get('candidate_id')}: {state}; "
            f"missing={missing or 'none'}; human review required"
        )
    lines.append("Expand explicitly before trust, validation, evidence, or materialization decisions.")
    return lines


def _merge_source_records(*groups: dict[str, Any]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for group in groups:
        for key, value in group.items():
            values = value if isinstance(value, list) else [value]
            bucket = out.setdefault(str(key), [])
            for item in values:
                text = str(item or "").strip()
                if text and text not in bucket:
                    bucket.append(text)
    return out


def _fingerprint(payload: dict[str, Any]) -> str:
    fingerprint_payload = {
        key: value
        for key, value in payload.items()
        if key not in {"fingerprint", "pack_id", "markdown"}
    }
    encoded = json.dumps(fingerprint_payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _excerpt(value: str, *, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."
