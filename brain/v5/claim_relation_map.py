"""Derived claim/evidence relation map for recovery briefs.

This surface is deliberately read-only.  It compiles existing typed records into
an explicit conclusion-boundary view, but it is never a source of claim trust.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from brain.v5.evidence import list_evidence_for_claim
from brain.v5.models import ClaimStatusRecord, EvidenceRecord, ObjectRelationRecord, ProofObligationRecord, ToolRunRecord
from brain.v5.physics_objects import list_object_relations_for_claim, object_relation_brief_payload
from brain.v5.research_state import list_proof_obligations_for_claim
from brain.v5.store import list_valid_records
from brain.v5.workspace import get_claim, get_session_binding

_SUPPORT_STATUSES = {"supports", "support", "supported", "passed", "pass", "valid", "positive", "supports_scoped_claim"}
_LIMIT_STATUSES = {"mixed", "inconclusive", "partial", "limited", "unreviewed", "diagnostic", "supports_with_limitations"}
_CONTRADICT_STATUSES = {"contradicts", "contradict", "refutes", "refute", "failed", "fail", "invalid", "negative"}
_RUNTIME_FAILURE_STATUSES = {
    "application_failure",
    "diagnostic",
    "failed",
    "fail",
    "falsifies_application",
    "negative",
    "runtime_failure",
}
_OPEN_STATUSES = {"open", "pending", "blocked", "incomplete", "inconclusive", "needs_revision", "partial"}
_PRE_DOMAIN_FAILURE_MARKERS = (
    "application",
    "runtime",
    "pre_ac",
    "pre-ac",
    "before analytic continuation",
    "before ac",
    "did not enter ac",
    "does not test algorithm",
    "does_not_test_algorithm",
    "falsifies_application",
    "scalapack",
    "executable",
    "slurm",
    "executable path",
)


def build_claim_relation_map(ws, session_id: str, *, registry_index: dict[str, dict[str, list[Any]]] | None = None) -> dict[str, Any]:
    """Build a read-only relation map for the session's active claim."""

    session = get_session_binding(ws, session_id)
    if not session.active_claim:
        return empty_claim_relation_map(
            topic_id=session.topic_id,
            session_id=session.session_id,
            reason="session has no active claim",
        )

    claim = get_claim(ws, session.active_claim)
    evidence_records = _indexed_claim_records(registry_index, "evidence", claim.claim_id)
    if evidence_records is None:
        evidence_records = list_evidence_for_claim(ws, claim.claim_id)
    tool_runs = _indexed_claim_records(registry_index, "tool_runs", claim.claim_id)
    if tool_runs is None:
        tool_runs = _tool_runs_for_claim(ws, claim.claim_id)
    claim_statuses = _indexed_claim_records(registry_index, "claim_statuses", claim.claim_id)
    if claim_statuses is None:
        claim_statuses = _claim_statuses_for_claim(ws, claim.claim_id)
    proof_obligations = _indexed_claim_records(registry_index, "proof_obligations", claim.claim_id)
    if proof_obligations is None:
        proof_obligations = list_proof_obligations_for_claim(ws, claim.claim_id)
    raw_object_relations = _indexed_claim_records(registry_index, "object_relations", claim.claim_id)
    if raw_object_relations is None:
        raw_object_relations = list_object_relations_for_claim(ws, claim.claim_id)
    object_relations = [
        object_relation_brief_payload(relation)
        for relation in raw_object_relations
    ]
    key_object_relations = _key_object_relation_summaries(object_relations)

    supported_by: list[dict[str, Any]] = []
    limited_by: list[dict[str, Any]] = []
    contradicted_by: list[dict[str, Any]] = []
    not_tested_by: list[dict[str, Any]] = []
    blockers: list[str] = []
    next_actions: list[str] = []

    for evidence in evidence_records:
        entry = _evidence_entry(evidence)
        bucket = _bucket_for_status(evidence.status, text=_evidence_text(evidence))
        if bucket == "not_tested_by":
            not_tested_by.append(entry)
            blockers.extend(_blocker_hints(_evidence_text(evidence)))
        elif bucket == "supported_by":
            supported_by.append(entry)
        elif bucket == "contradicted_by":
            contradicted_by.append(entry)
        else:
            limited_by.append(entry)

    for run in tool_runs:
        entry = _tool_run_entry(run)
        bucket = _bucket_for_status(run.evidence_status, text=_tool_run_text(run))
        if bucket == "not_tested_by":
            not_tested_by.append(entry)
            blockers.extend(_blocker_hints(_tool_run_text(run)))
        elif bucket == "supported_by":
            supported_by.append(entry)
        elif bucket == "contradicted_by":
            contradicted_by.append(entry)
        elif run.evidence_status:
            limited_by.append(entry)

    for status in claim_statuses:
        for gap in status.open_gaps:
            limited_by.append(_claim_status_gap_entry(status, gap))
            blockers.append(gap)
        if status.next_action:
            next_actions.append(status.next_action)

    for obligation in proof_obligations:
        if obligation.status.strip().lower() in _OPEN_STATUSES:
            limited_by.append(_proof_obligation_entry(obligation))
            blockers.append(obligation.statement)
            if obligation.next_action:
                next_actions.append(obligation.next_action)

    for relation in object_relations:
        if relation.get("failure_modes"):
            blockers.extend(str(item) for item in relation.get("failure_modes", []))

    blockers = _dedupe_clean(blockers)
    next_actions = _dedupe_clean(next_actions)
    next_actions = _prioritized_next_actions(next_actions, not_tested_by, blockers)
    latest_status = _latest_claim_status(claim_statuses)

    payload = {
        "kind": "claim_relation_map",
        "topic_id": session.topic_id,
        "session_id": session.session_id,
        "claim_id": claim.claim_id,
        "claim_statement": claim.statement,
        "confidence_state": claim.confidence_state,
        "evidence_profile": claim.evidence_profile,
        "key_object_relation_count": len(key_object_relations),
        "key_object_relations": key_object_relations,
        "latest_claim_status": _claim_status_payload(latest_status) if latest_status else {},
        "supported_by": supported_by,
        "limited_by": limited_by,
        "contradicted_by": contradicted_by,
        "not_tested_by": not_tested_by,
        "object_relations": object_relations,
        "current_conclusion": {
            "can_say": _can_say(claim, supported_by, limited_by, not_tested_by, blockers),
            "cannot_say": _cannot_say(supported_by, limited_by, contradicted_by, not_tested_by),
        },
        "current_blockers": blockers,
        "next_valid_actions": next_actions,
        "source_records": {
            "claims": [claim.claim_id],
            "evidence": [record.evidence_id for record in evidence_records],
            "tool_runs": [record.run_id for record in tool_runs],
            "claim_statuses": [record.status_id for record in claim_statuses],
            "proof_obligations": [record.obligation_id for record in proof_obligations],
            "object_relations": [str(record.get("relation_id") or "") for record in object_relations if record.get("relation_id")],
        },
        "derived_from": [
            "claim_status_records",
            "evidence_records",
            "tool_run_records",
            "object_relation_records",
            "proof_obligation_records",
        ],
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "trust_update_allowed": False,
    }
    return payload


def build_claim_relation_registry_index(ws) -> dict[str, dict[str, list[Any]]]:
    """Preload registry records by claim for workspace-scale recovery audits."""

    return {
        "evidence": _group_by_claim(list_valid_records(ws.registry_dir("evidence"), EvidenceRecord)),
        "tool_runs": _group_by_claim(list_valid_records(ws.registry_dir("tool_runs"), ToolRunRecord)),
        "claim_statuses": _group_by_claim(list_valid_records(ws.registry_dir("claim_statuses"), ClaimStatusRecord)),
        "proof_obligations": _group_by_claim(list_valid_records(ws.registry_dir("proof_obligations"), ProofObligationRecord)),
        "object_relations": _group_by_claim(list_valid_records(ws.registry_dir("object_relations"), ObjectRelationRecord)),
    }


def empty_claim_relation_map(*, topic_id: str, session_id: str, reason: str) -> dict[str, Any]:
    return {
        "kind": "claim_relation_map",
        "topic_id": topic_id or "unbound-session",
        "session_id": session_id or "unbound-session",
        "claim_id": "",
        "claim_statement": "",
        "confidence_state": "",
        "evidence_profile": "",
        "key_object_relation_count": 0,
        "key_object_relations": [],
        "latest_claim_status": {},
        "supported_by": [],
        "limited_by": [],
        "contradicted_by": [],
        "not_tested_by": [],
        "object_relations": [],
        "current_conclusion": {
            "can_say": [reason],
            "cannot_say": ["cannot infer claim support, failure, or trust state without an active claim"],
        },
        "current_blockers": [reason],
        "next_valid_actions": ["bind a session to a topic and active claim before restoring research state"],
        "source_records": {
            "claims": [],
            "evidence": [],
            "tool_runs": [],
            "claim_statuses": [],
            "proof_obligations": [],
            "object_relations": [],
        },
        "derived_from": [],
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "trust_update_allowed": False,
    }


def compact_claim_relation_map(payload: dict[str, Any]) -> dict[str, Any]:
    conclusion = payload.get("current_conclusion") or {}
    return {
        "kind": "claim_relation_map_progress",
        "claim_id": str(payload.get("claim_id") or ""),
        "claim_statement_excerpt": _excerpt(payload.get("claim_statement") or ""),
        "confidence_state": str(payload.get("confidence_state") or ""),
        "supported_count": len(payload.get("supported_by") or []),
        "limited_count": len(payload.get("limited_by") or []),
        "contradicted_count": len(payload.get("contradicted_by") or []),
        "not_tested_count": len(payload.get("not_tested_by") or []),
        "object_relation_count": len(payload.get("object_relations") or []),
        "key_object_relations": list(payload.get("key_object_relations") or [])[:5],
        "can_say": list(conclusion.get("can_say") or [])[:5],
        "cannot_say": list(conclusion.get("cannot_say") or [])[:5],
        "current_blockers": list(payload.get("current_blockers") or [])[:5],
        "next_valid_actions": list(payload.get("next_valid_actions") or [])[:5],
        "orientation_only": True,
        "can_update_claim_trust": False,
        "trust_update_allowed": False,
    }


def render_claim_relation_map_markdown(payload: dict[str, Any]) -> str:
    conclusion = payload.get("current_conclusion") or {}
    lines = [
        "# Current Relation Map\n\n",
        f"Claim: `{payload.get('claim_id', '')}`\n\n",
        f"{payload.get('claim_statement', '')}\n\n",
        "## Supported By\n\n",
        _entry_bullets(payload.get("supported_by") or []),
        "\n## Limited By\n\n",
        _entry_bullets(payload.get("limited_by") or []),
        "\n## Not Tested By\n\n",
        _entry_bullets(payload.get("not_tested_by") or []),
        "\n## Contradicted By\n\n",
        _entry_bullets(payload.get("contradicted_by") or []),
        "\n## Key Object Relations\n\n",
        _bullets(payload.get("key_object_relations") or []),
        "\n## Can Say\n\n",
        _bullets(conclusion.get("can_say") or []),
        "\n## Cannot Say\n\n",
        _bullets(conclusion.get("cannot_say") or []),
        "\n## Current Blockers\n\n",
        _bullets(payload.get("current_blockers") or []),
        "\n## Next Valid Actions\n\n",
        _bullets(payload.get("next_valid_actions") or []),
        "\nThis surface is orientation-only and cannot update claim trust.\n",
    ]
    return "".join(lines)


def _tool_runs_for_claim(ws, claim_id: str) -> list[ToolRunRecord]:
    return [
        run
        for run in list_valid_records(ws.registry_dir("tool_runs"), ToolRunRecord)
        if run.claim_id == claim_id
    ]


def _claim_statuses_for_claim(ws, claim_id: str) -> list[ClaimStatusRecord]:
    return [
        record
        for record in list_valid_records(ws.registry_dir("claim_statuses"), ClaimStatusRecord)
        if record.claim_id == claim_id
    ]


def _indexed_claim_records(
    registry_index: dict[str, dict[str, list[Any]]] | None,
    bucket: str,
    claim_id: str,
) -> list[Any] | None:
    if registry_index is None:
        return None
    return list(registry_index.get(bucket, {}).get(claim_id, []))


def _group_by_claim(records: list[Any]) -> dict[str, list[Any]]:
    grouped: dict[str, list[Any]] = {}
    for record in records:
        claim_id = str(getattr(record, "claim_id", "") or "")
        if not claim_id:
            continue
        grouped.setdefault(claim_id, []).append(record)
    return grouped


def _latest_claim_status(records: list[ClaimStatusRecord]) -> ClaimStatusRecord | None:
    return records[-1] if records else None


def _claim_status_payload(record: ClaimStatusRecord) -> dict[str, Any]:
    return {
        "status_id": record.status_id,
        "maturity_level": record.maturity_level,
        "claim_status": record.claim_status,
        "scope": record.scope,
        "risk": record.risk,
        "next_action": record.next_action,
        "open_gaps": list(record.open_gaps),
        "evidence_refs": list(record.evidence_refs),
        "human_gate_required": bool(record.human_gate_required),
        "can_update_claim_trust": bool(record.can_update_claim_trust),
    }


def _key_object_relation_summaries(object_relations: list[dict[str, Any]]) -> list[str]:
    summaries: list[str] = []
    for relation in object_relations:
        relation_type = str(relation.get("relation_type") or "").strip()
        statement = str(relation.get("statement") or "").strip()
        subject_id = str(relation.get("subject_id") or "").strip()
        object_id = str(relation.get("object_id") or "").strip()
        status = str(relation.get("status") or "").strip()
        failure_modes = [
            str(item).strip()
            for item in relation.get("failure_modes", [])
            if str(item).strip()
        ]
        if statement:
            summary = f"{relation_type}: {statement}" if relation_type else statement
        else:
            summary = f"{subject_id} --{relation_type or 'relates_to'}-> {object_id}"
        if status:
            summary = f"{summary} (status={status})"
        if failure_modes:
            summary = f"{summary}; failure modes: {', '.join(failure_modes[:3])}"
        summaries.append(summary)
    return _dedupe_clean(summaries)


def _bucket_for_status(status: str, *, text: str) -> str:
    normalized = status.strip().lower().replace(" ", "_")
    lower = text.lower()
    if normalized in _SUPPORT_STATUSES:
        return "supported_by"
    if normalized in _LIMIT_STATUSES:
        return "limited_by"
    if any(marker in lower for marker in _PRE_DOMAIN_FAILURE_MARKERS) and (
        normalized in _RUNTIME_FAILURE_STATUSES or normalized not in _SUPPORT_STATUSES
    ):
        return "not_tested_by"
    if normalized in _CONTRADICT_STATUSES:
        return "contradicted_by"
    return "limited_by"


def _evidence_entry(record) -> dict[str, Any]:
    text = _evidence_text(record)
    return {
        "record_kind": "evidence",
        "record_id": record.evidence_id,
        "relation_to_claim": _relation_label(record.status, text=text),
        "status": record.status,
        "summary": record.summary,
        "reason": _relation_reason(record.status, text=text),
        "source_refs": list(record.source_refs),
        "evidence_refs": [record.evidence_id],
        "tool_run_ids": list(record.tool_run_ids),
        "artifact_ids": list(record.artifact_ids),
    }


def _tool_run_entry(record: ToolRunRecord) -> dict[str, Any]:
    text = _tool_run_text(record)
    return {
        "record_kind": "tool_run",
        "record_id": record.run_id,
        "relation_to_claim": _relation_label(record.evidence_status, text=text),
        "status": record.evidence_status,
        "summary": _excerpt(text, limit=360),
        "reason": _relation_reason(record.evidence_status, text=text),
        "source_refs": list(record.source_refs),
        "evidence_refs": [],
        "tool_run_ids": [record.run_id],
        "artifact_ids": list(record.artifact_ids),
    }


def _claim_status_gap_entry(record: ClaimStatusRecord, gap: str) -> dict[str, Any]:
    return {
        "record_kind": "claim_status",
        "record_id": record.status_id,
        "relation_to_claim": "limits_claim_scope",
        "status": record.claim_status,
        "summary": gap,
        "reason": f"recorded open gap under scope: {record.scope}",
        "source_refs": list(record.source_refs),
        "evidence_refs": list(record.evidence_refs),
        "tool_run_ids": [],
        "artifact_ids": list(record.artifact_ids),
    }


def _proof_obligation_entry(record: ProofObligationRecord) -> dict[str, Any]:
    return {
        "record_kind": "proof_obligation",
        "record_id": record.obligation_id,
        "relation_to_claim": "open_proof_or_validation_gap",
        "status": record.status,
        "summary": record.statement,
        "reason": record.next_action,
        "source_refs": list(record.source_refs),
        "evidence_refs": list(record.evidence_refs),
        "tool_run_ids": [],
        "artifact_ids": list(record.artifact_ids),
    }


def _relation_label(status: str, *, text: str) -> str:
    bucket = _bucket_for_status(status, text=text)
    if bucket == "not_tested_by":
        return "does_not_test_core_claim"
    if bucket == "supported_by":
        return "supports_claim_within_scope"
    if bucket == "contradicted_by":
        return "challenges_or_refutes_claim"
    return "limits_or_does_not_close_claim"


def _relation_reason(status: str, *, text: str) -> str:
    if _bucket_for_status(status, text=text) == "not_tested_by":
        return "classified as application/runtime/pre-domain failure, so it cannot support or refute the core claim"
    if status.strip().lower() in _SUPPORT_STATUSES:
        return "record status is supporting"
    if status.strip().lower() in _CONTRADICT_STATUSES:
        return "record status is challenging and no pre-domain failure marker was found"
    return "record is mixed, inconclusive, diagnostic, or scope-limiting"


def _evidence_text(record) -> str:
    return " ".join(
        [
            str(record.evidence_type),
            str(record.status),
            str(record.summary),
            " ".join(record.supports_outputs),
            " ".join(record.source_refs),
            " ".join(record.tool_run_ids),
            " ".join(record.artifact_ids),
        ]
    )


def _tool_run_text(record: ToolRunRecord) -> str:
    return " ".join(
        [
            str(record.tool_family),
            str(record.tool_name),
            str(record.evidence_status),
            _json_text(record.inputs),
            _json_text(record.outputs),
            _json_text(record.environment),
            " ".join(record.source_refs),
        ]
    )


def _json_text(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    except TypeError:
        return str(value)


def _blocker_hints(text: str) -> list[str]:
    lower = text.lower()
    hints: list[str] = []
    if "scalapack" in lower:
        hints.append("ScaLAPACK/runtime dependency failure")
    if "executable" in lower or "path" in lower:
        hints.append("executable path or executable selection blocker")
    if "slurm" in lower:
        hints.append("Slurm/runtime job failure")
    if "before analytic continuation" in lower or "pre_ac" in lower or "pre-ac" in lower or "before ac" in lower:
        hints.append("failure occurred before analytic continuation")
    if not hints and any(marker in lower for marker in _PRE_DOMAIN_FAILURE_MARKERS):
        hints.append("application/runtime failure before the core claim was tested")
    return hints


def _can_say(claim, supported_by: list[dict[str, Any]], limited_by: list[dict[str, Any]], not_tested_by: list[dict[str, Any]], blockers: list[str]) -> list[str]:
    statements: list[str] = [f"active claim remains {claim.confidence_state}"]
    if supported_by:
        statements.append("recorded support exists for the claim within the explicit recorded scope")
    if limited_by:
        statements.append("recorded limitations or open gaps bound how far the claim can be used")
    if not_tested_by:
        statements.append("some failed attempts are application/runtime failures and do not test the core claim")
    if blockers:
        statements.append(f"current blocker: {blockers[0]}")
    return _dedupe_clean(statements)


def _cannot_say(supported_by: list[dict[str, Any]], limited_by: list[dict[str, Any]], contradicted_by: list[dict[str, Any]], not_tested_by: list[dict[str, Any]]) -> list[str]:
    statements = ["cannot update or promote claim trust from this relation map alone"]
    if not supported_by:
        statements.append("cannot say the claim is supported until supporting evidence records exist")
    if limited_by:
        statements.append("cannot ignore scope limits, gap audits, or open proof obligations")
    if not_tested_by:
        statements.append("cannot say runtime/application failures prove the core algorithm works or fails")
    if contradicted_by:
        statements.append("cannot treat the claim as settled while challenging evidence remains unresolved")
    return _dedupe_clean(statements)


def _fallback_next_actions(not_tested_by: list[dict[str, Any]], blockers: list[str]) -> list[str]:
    if not_tested_by and blockers:
        text = " ".join(str(entry.get("summary") or "") for entry in not_tested_by).lower()
        if "thiele" in text and "ridge" in text:
            return [
                "resolve the runtime/application blocker, then rerun the same-executable Thiele baseline before interpreting ridge evidence"
            ]
        return [
            "resolve the runtime/application blocker, then rerun the same-executable baseline/control before interpreting algorithm evidence"
        ]
    if blockers:
        return ["resolve the recorded blocker before trust-changing interpretation"]
    return ["record explicit evidence, claim status, or proof obligation before drawing conclusions"]


def _prioritized_next_actions(
    recorded_actions: list[str],
    not_tested_by: list[dict[str, Any]],
    blockers: list[str],
) -> list[str]:
    fallback = _fallback_next_actions(not_tested_by, blockers)
    if not not_tested_by or not blockers:
        return recorded_actions or fallback
    if any(_is_specific_runtime_resolution_action(action) for action in recorded_actions):
        return recorded_actions
    return _dedupe_clean(fallback + recorded_actions)


def _is_specific_runtime_resolution_action(action: str) -> bool:
    lower = action.lower()
    if "baseline" in lower and ("same executable" in lower or "same-executable" in lower):
        return True
    if "thiele" in lower and "ridge" in lower and ("rerun" in lower or "reproduce" in lower or "run" in lower):
        return True
    if "control" in lower and ("runtime" in lower or "application" in lower):
        return True
    return False


def _entry_bullets(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "- None\n"
    lines = []
    for entry in entries:
        lines.append(
            f"- `{entry.get('record_id', '')}` ({entry.get('relation_to_claim', '')}, "
            f"status={entry.get('status', '')}): {entry.get('summary', '')}\n"
        )
    return "".join(lines)


def _bullets(values: list[str]) -> str:
    return "".join(f"- {value}\n" for value in values) if values else "- None\n"


def _dedupe_clean(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        clean = str(value or "").strip()
        if clean and clean not in out:
            out.append(clean)
    return out


def _excerpt(value: Any, *, limit: int = 260) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
