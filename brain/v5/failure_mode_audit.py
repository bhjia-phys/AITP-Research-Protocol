"""Read-only failure-mode coverage audit surfaces."""

from __future__ import annotations

import re

from brain.v5.models import FailureModeReviewResultRecord, PromotionPacketRecord, ValidationContractRecord
from brain.v5.store import list_records
from brain.v5.workspace import WorkspacePaths, get_claim


def audit_failure_mode_coverage(ws: WorkspacePaths, *, claim_id: str) -> dict:
    """Return a typed-record-derived audit of failure-mode coverage for one claim."""

    claim = get_claim(ws, claim_id)
    contracts = [
        record
        for record in list_records(ws.registry_dir("validation_contracts"), ValidationContractRecord)
        if record.claim_id == claim_id
    ]
    packets = [
        record
        for record in list_records(ws.registry_dir("promotion_packets"), PromotionPacketRecord)
        if record.claim_id == claim_id
    ]
    review_results = [
        record
        for record in list_records(ws.registry_dir("failure_mode_reviews"), FailureModeReviewResultRecord)
        if record.claim_id == claim_id
    ]
    claim_modes = [claim.strongest_failure_mode] if claim.strongest_failure_mode.strip() else []
    contract_modes = _unique(mode for contract in contracts for mode in contract.failure_modes)
    packet_modes = _unique(mode for packet in packets for mode in packet.known_failure_modes)
    reviewed_modes = _unique(mode for result in review_results for mode in result.reviewed_failure_modes)
    uncovered_claim = [mode for mode in claim_modes if not _covered_by_modes(mode, packet_modes)]
    uncovered_contract = [mode for mode in contract_modes if not _covered_by_modes(mode, packet_modes)]
    actions: list[str] = []
    if uncovered_claim:
        actions.append("align_promotion_failure_modes_with_claim_risk")
    if uncovered_contract:
        actions.append("cover_validation_contract_failure_modes")
    return {
        "ok": True,
        "kind": "failure_mode_audit",
        "claim_id": claim_id,
        "topic_id": claim.topic_id,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "active_uncertainty": claim.active_uncertainty,
        "strongest_failure_mode": claim.strongest_failure_mode,
        "validation_contract_ids": [contract.contract_id for contract in contracts],
        "promotion_packet_ids": [packet.packet_id for packet in packets],
        "failure_mode_review_result_ids": [result.result_id for result in review_results],
        "validation_contract_failure_modes": contract_modes,
        "promotion_packet_failure_modes": packet_modes,
        "reviewed_failure_modes": reviewed_modes,
        "failure_mode_review_results": [_review_result_payload(result) for result in review_results],
        "uncovered_claim_failure_modes": uncovered_claim,
        "uncovered_validation_failure_modes": uncovered_contract,
        "coverage_status": "covered" if not uncovered_claim and not uncovered_contract else "gap",
        "recommended_actions": actions,
    }


def _covered_by_modes(target: str, modes: list[str]) -> bool:
    target_tokens = _tokens(target)
    if not target_tokens:
        return True
    mode_tokens: set[str] = set()
    for mode in modes:
        mode_tokens.update(_tokens(mode))
    return target_tokens.issubset(mode_tokens)


def _review_result_payload(record: FailureModeReviewResultRecord) -> dict:
    return {
        "result_id": record.result_id,
        "checkpoint_id": record.checkpoint_id,
        "status": record.status,
        "reviewed_failure_modes": list(record.reviewed_failure_modes),
        "basis_refs": list(record.basis_refs),
        "evidence_refs": list(record.evidence_refs),
        "validation_result_ids": list(record.validation_result_ids),
        "tool_run_ids": list(record.tool_run_ids),
        "reference_location_ids": list(record.reference_location_ids),
        "artifact_ids": list(record.artifact_ids),
        "summary_inputs_trusted": record.summary_inputs_trusted,
        "can_update_claim_trust": record.can_update_claim_trust,
    }


def _tokens(text: str) -> set[str]:
    generic = {"failure", "mode", "modes", "risk", "mismatch", "artifact", "possible", "may", "can"}
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2 and token not in generic}


def _unique(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        clean = str(value).strip()
        if clean and clean not in seen:
            seen.add(clean)
            result.append(clean)
    return result
