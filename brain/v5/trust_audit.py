"""Read-only claim trust audit surfaces."""

from __future__ import annotations

from brain.v5.evidence import list_evidence_for_claim
from brain.v5.memory import list_memory_entries_for_claim
from brain.v5.models import CodeStateRecord, ToolRunRecord, TrustUpdateRecord, ValidationResultRecord
from brain.v5.store import list_valid_records
from brain.v5.workspace import WorkspacePaths, get_claim


_BASELINE_CONFIDENCE_STATES = {"hypothesis", "learning", "legacy_seed"}
_CHECKED_CONFIDENCE_STATES = {"locally_checked", "validated", "human_accepted"}


def audit_claim_trust(ws: WorkspacePaths, *, claim_id: str) -> dict:
    """Return a typed-record-derived support audit for a claim confidence state."""

    claim = get_claim(ws, claim_id)
    evidence_records = list_evidence_for_claim(ws, claim_id)
    supporting_evidence_refs = [
        evidence.evidence_id for evidence in evidence_records if _is_supporting_evidence(evidence.status)
    ]
    challenging_evidence_refs = [
        evidence.evidence_id for evidence in evidence_records if _is_challenging_evidence(evidence.status)
    ]
    validation_results = [
        record
        for record in list_valid_records(ws.registry_dir("validation_results"), ValidationResultRecord)
        if record.claim_id == claim_id
    ]
    passed_validation_result_ids = [
        result.result_id
        for result in validation_results
        if result.status == "passed" and not result.missing_outputs and not result.failure_modes_observed
    ]
    failed_validation_result_ids = [
        result.result_id
        for result in validation_results
        if result.status in {"failed", "inconclusive", "partial"} or result.missing_outputs or result.failure_modes_observed
    ]
    memory_entries = list_memory_entries_for_claim(ws, claim_id)
    code_state_ids = _code_state_ids_for_claim(ws, claim_id, evidence_records)
    trust_update_record_ids = _trust_update_record_ids_for_claim(ws, claim_id)
    support_state = _support_state(
        supporting_evidence_refs=supporting_evidence_refs,
        passed_validation_result_ids=passed_validation_result_ids,
        l2_memory_entry_ids=[entry.entry_id for entry in memory_entries],
    )
    return {
        "ok": True,
        "kind": "claim_trust_audit",
        "claim_id": claim_id,
        "topic_id": claim.topic_id,
        "confidence_state": claim.confidence_state,
        "evidence_profile": claim.evidence_profile,
        "support_state": support_state,
        "supporting_evidence_refs": supporting_evidence_refs,
        "challenging_evidence_refs": challenging_evidence_refs,
        "passed_validation_result_ids": passed_validation_result_ids,
        "failed_validation_result_ids": failed_validation_result_ids,
        "l2_memory_entry_ids": [entry.entry_id for entry in memory_entries],
        "code_state_ids": code_state_ids,
        "trust_update_record_ids": trust_update_record_ids,
        "review_actions": _review_actions(
            confidence_state=claim.confidence_state,
            evidence_profile=claim.evidence_profile,
            supporting_evidence_refs=supporting_evidence_refs,
            passed_validation_result_ids=passed_validation_result_ids,
            l2_memory_entry_ids=[entry.entry_id for entry in memory_entries],
            code_state_ids=code_state_ids,
        ),
        "mutation_history_available": bool(trust_update_record_ids),
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _code_state_ids_for_claim(ws: WorkspacePaths, claim_id: str, evidence_records) -> list[str]:
    tool_runs_by_id = {
        record.run_id: record
        for record in list_valid_records(ws.registry_dir("tool_runs"), ToolRunRecord)
        if record.claim_id == claim_id
    }
    result: list[str] = []
    for evidence in evidence_records:
        for run_id in evidence.tool_run_ids:
            run = tool_runs_by_id.get(run_id)
            if run is not None:
                _append_unique(result, run.code_state_ids)
    for state in list_valid_records(ws.registry_dir("code_states"), CodeStateRecord):
        if _record_links_to_claim(state.linked_records, claim_id):
            _append_unique(result, [state.code_state_id])
    return result


def _trust_update_record_ids_for_claim(ws: WorkspacePaths, claim_id: str) -> list[str]:
    records = [
        record
        for record in list_valid_records(ws.registry_dir("trust_updates"), TrustUpdateRecord)
        if record.claim_id == claim_id
    ]
    return [record.update_id for record in sorted(records, key=lambda item: item.update_id)]


def _support_state(
    *,
    supporting_evidence_refs: list[str],
    passed_validation_result_ids: list[str],
    l2_memory_entry_ids: list[str],
) -> str:
    if supporting_evidence_refs and passed_validation_result_ids and l2_memory_entry_ids:
        return "validated_memory_backed"
    if supporting_evidence_refs and passed_validation_result_ids:
        return "validated"
    if supporting_evidence_refs:
        return "evidence_only"
    return "unsupported"


def _review_actions(
    *,
    confidence_state: str,
    evidence_profile: str,
    supporting_evidence_refs: list[str],
    passed_validation_result_ids: list[str],
    l2_memory_entry_ids: list[str],
    code_state_ids: list[str],
) -> list[str]:
    actions: list[str] = []
    if confidence_state not in _BASELINE_CONFIDENCE_STATES and not supporting_evidence_refs:
        actions.append("record_supporting_evidence")
    if confidence_state in _CHECKED_CONFIDENCE_STATES and not passed_validation_result_ids:
        actions.append("record_validation_result")
    if confidence_state == "human_accepted" and not l2_memory_entry_ids:
        actions.append("audit_l2_memory_context")
    if evidence_profile == "code_method" and not code_state_ids:
        actions.append("record_code_state")
    return actions


def _is_supporting_evidence(status: str) -> bool:
    return status.strip().lower() in {
        "supports",
        "support",
        "passed",
        "valid",
        "supports_claim_within_scope",
        "supports_reconstruction_boundary",
        "supports_scoped_claim",
        "supports_with_scope_limits",
        "supports_with_limitations",
    }


def _is_challenging_evidence(status: str) -> bool:
    return status.strip().lower() in {"refutes", "failed", "invalid"}


def _record_links_to_claim(linked_records: dict, claim_id: str) -> bool:
    for value in linked_records.values():
        if value == claim_id or (isinstance(value, list) and claim_id in value):
            return True
    return False


def _append_unique(target: list[str], values: list[str]) -> None:
    seen = set(target)
    for value in values:
        if value and value not in seen:
            seen.add(value)
            target.append(value)
