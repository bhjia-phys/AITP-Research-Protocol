"""Read-only L2 memory audit surfaces."""

from __future__ import annotations

from brain.v5.memory import list_memory_entries_for_claim
from brain.v5.models import (
    EvidenceRecord,
    HumanCheckpointRecord,
    PromotionPacketRecord,
    ToolRunRecord,
    ValidationResultRecord,
)
from brain.v5.store import list_records
from brain.v5.workspace import WorkspacePaths, get_claim


def audit_l2_memory_context(ws: WorkspacePaths, *, claim_id: str) -> dict:
    """Return a typed-record-derived audit of L2 memory for one claim."""

    claim = get_claim(ws, claim_id)
    evidence_by_id = {
        record.evidence_id: record
        for record in list_records(ws.registry_dir("evidence"), EvidenceRecord)
        if record.claim_id == claim_id
    }
    runs_by_id = {
        record.run_id: record
        for record in list_records(ws.registry_dir("tool_runs"), ToolRunRecord)
        if record.claim_id == claim_id
    }
    validations_by_id = {
        record.result_id: record
        for record in list_records(ws.registry_dir("validation_results"), ValidationResultRecord)
        if record.claim_id == claim_id
    }
    packets_by_id = {
        record.packet_id: record
        for record in list_records(ws.registry_dir("promotion_packets"), PromotionPacketRecord)
        if record.claim_id == claim_id
    }
    checkpoints_by_id = {
        record.checkpoint_id: record
        for record in list_records(ws.registry_dir("checkpoints"), HumanCheckpointRecord)
        if record.claim_id == claim_id
    }

    entries = [
        _audit_entry(
            entry,
            evidence_by_id=evidence_by_id,
            runs_by_id=runs_by_id,
            validations_by_id=validations_by_id,
            packets_by_id=packets_by_id,
            checkpoints_by_id=checkpoints_by_id,
        )
        for entry in list_memory_entries_for_claim(ws, claim_id)
    ]
    return {
        "ok": True,
        "kind": "l2_memory_audit",
        "claim_id": claim_id,
        "topic_id": claim.topic_id,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "entry_count": len(entries),
        "memory_entries": entries,
    }


def _audit_entry(
    entry,
    *,
    evidence_by_id: dict[str, EvidenceRecord],
    runs_by_id: dict[str, ToolRunRecord],
    validations_by_id: dict[str, ValidationResultRecord],
    packets_by_id: dict[str, PromotionPacketRecord],
    checkpoints_by_id: dict[str, HumanCheckpointRecord],
) -> dict:
    missing_links: list[str] = []
    packet = packets_by_id.get(entry.source_packet_id)
    checkpoint = checkpoints_by_id.get(entry.human_checkpoint_id)
    if entry.source_packet_id and packet is None:
        missing_links.append(f"promotion_packet:{entry.source_packet_id}")
    if entry.human_checkpoint_id and checkpoint is None:
        missing_links.append(f"human_checkpoint:{entry.human_checkpoint_id}")

    validation_result_ids: list[str] = []
    code_state_ids: list[str] = []
    if packet is not None:
        _append_unique(validation_result_ids, packet.validation_result_ids)
    for evidence_id in entry.evidence_refs:
        evidence = evidence_by_id.get(evidence_id)
        if evidence is None:
            missing_links.append(f"evidence:{evidence_id}")
            continue
        _append_unique(validation_result_ids, evidence.validation_result_ids)
        for run_id in evidence.tool_run_ids:
            run = runs_by_id.get(run_id)
            if run is None:
                missing_links.append(f"tool_run:{run_id}")
                continue
            _append_unique(code_state_ids, run.code_state_ids)
    for result_id in validation_result_ids:
        if result_id not in validations_by_id:
            missing_links.append(f"validation_result:{result_id}")

    return {
        "entry_id": entry.entry_id,
        "topic_id": entry.topic_id,
        "source_claim_id": entry.source_claim_id,
        "source_topic_id": entry.source_topic_id,
        "statement": entry.statement,
        "memory_kind": entry.memory_kind,
        "scope": entry.scope,
        "evidence_refs": list(entry.evidence_refs),
        "validation_result_ids": validation_result_ids,
        "code_state_ids": code_state_ids,
        "non_claims": list(entry.non_claims),
        "known_failure_modes": list(entry.known_failure_modes),
        "source_packet_id": entry.source_packet_id,
        "promotion_packet_status": packet.status if packet is not None else "",
        "human_checkpoint_id": entry.human_checkpoint_id,
        "failure_mode_review_checkpoint_id": entry.failure_mode_review_checkpoint_id,
        "human_checkpoint_decision": checkpoint.decision if checkpoint is not None else "",
        "missing_links": missing_links,
        "orientation_only": True,
    }


def _append_unique(target: list[str], values: list[str]) -> None:
    seen = set(target)
    for value in values:
        if value and value not in seen:
            seen.add(value)
            target.append(value)
