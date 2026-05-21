"""L2 memory and promotion packet management for AITP v5."""

from __future__ import annotations

from brain.v5.ids import prefixed_id
from brain.v5.models import (
    EvidenceRecord,
    HumanCheckpointRecord,
    MemoryEntryRecord,
    PromotionPacketRecord,
    ToolRunRecord,
    ValidationResultRecord,
)
from brain.v5.store import list_records, read_record, write_record
from brain.v5.workspace import WorkspacePaths, get_claim


def _promotion_packet_identity(
    *,
    claim_id: str,
    proposed_memory_kind: str,
    scope: str,
    evidence_refs: list[str],
    validation_result_ids: list[str],
    non_claims: list[str],
    known_failure_modes: list[str],
) -> str:
    return "\n".join(
        [
            claim_id,
            proposed_memory_kind,
            scope,
            "evidence:" + "|".join(evidence_refs),
            "validation_results:" + "|".join(validation_result_ids),
            "non_claims:" + "|".join(non_claims),
            "failure_modes:" + "|".join(known_failure_modes),
        ]
    )


def create_promotion_packet(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str,
    proposed_memory_kind: str = "scoped_claim",
    scope: str = "",
    evidence_refs: list[str] | None = None,
    validation_result_ids: list[str] | None = None,
    non_claims: list[str] | None = None,
    known_failure_modes: list[str] | None = None,
) -> PromotionPacketRecord:
    if not proposed_memory_kind:
        raise ValueError("proposed_memory_kind must not be empty")
    if not scope:
        raise ValueError("promotion packet scope must not be empty")
    if not evidence_refs:
        raise ValueError("promotion packet evidence_refs must not be empty")
    if not known_failure_modes:
        raise ValueError("promotion packet known_failure_modes must not be empty")
    _ensure_tool_evidence_has_passed_validation_results(
        ws,
        claim_id=claim_id,
        evidence_refs=evidence_refs or [],
        validation_result_ids=validation_result_ids or [],
    )

    packet_id = prefixed_id(
        "packet",
        _promotion_packet_identity(
            claim_id=claim_id,
            proposed_memory_kind=proposed_memory_kind,
            scope=scope,
            evidence_refs=evidence_refs,
            validation_result_ids=validation_result_ids or [],
            non_claims=non_claims or [],
            known_failure_modes=known_failure_modes,
        ),
    )
    packet = PromotionPacketRecord(
        packet_id=packet_id,
        topic_id=topic_id,
        claim_id=claim_id,
        proposed_memory_kind=proposed_memory_kind,
        scope=scope,
        evidence_refs=evidence_refs or [],
        validation_result_ids=validation_result_ids or [],
        non_claims=non_claims or [],
        known_failure_modes=known_failure_modes or [],
    )
    write_record(ws.registry_dir("promotion_packets") / f"{packet_id}.md", packet)
    return packet


def apply_promotion_packet(
    ws: WorkspacePaths,
    *,
    packet_id: str,
    checkpoint_id: str,
) -> MemoryEntryRecord:
    if not checkpoint_id:
        raise ValueError("approved human checkpoint is required to apply a promotion packet")

    packet_path = ws.registry_dir("promotion_packets") / f"{packet_id}.md"
    packet = read_record(packet_path, PromotionPacketRecord)

    if packet.status == "promoted":
        raise ValueError("promotion packet is already promoted")
    if not packet.scope:
        raise ValueError("promotion packet scope must not be empty")
    if not packet.evidence_refs:
        raise ValueError("promotion packet evidence_refs must not be empty")
    if not packet.known_failure_modes:
        raise ValueError("promotion packet known_failure_modes must not be empty")
    _ensure_tool_evidence_has_passed_validation_results(
        ws,
        claim_id=packet.claim_id,
        evidence_refs=packet.evidence_refs,
        validation_result_ids=packet.validation_result_ids,
    )

    chk_path = ws.registry_dir("checkpoints") / f"{checkpoint_id}.md"
    checkpoint = read_record(chk_path, HumanCheckpointRecord)

    if checkpoint.topic_id != packet.topic_id or checkpoint.claim_id != packet.claim_id:
        raise ValueError("approved human checkpoint must belong to the same topic and claim as the promotion packet")
    if checkpoint.status != "decided":
        raise ValueError("approved human checkpoint is required — checkpoint not decided")
    if checkpoint.decision != "approve":
        raise ValueError(f"approved human checkpoint is required — decision was {checkpoint.decision!r}")

    claim = get_claim(ws, packet.claim_id)

    entry_id = prefixed_id("memory", packet_id)
    entry = MemoryEntryRecord(
        entry_id=entry_id,
        topic_id=packet.topic_id,
        source_claim_id=packet.claim_id,
        source_topic_id=packet.topic_id,
        statement=claim.statement,
        memory_kind=packet.proposed_memory_kind,
        scope=packet.scope,
        evidence_refs=list(packet.evidence_refs),
        non_claims=list(packet.non_claims),
        known_failure_modes=list(packet.known_failure_modes),
        source_packet_id=packet_id,
        human_checkpoint_id=checkpoint_id,
        status="active",
    )
    write_record(ws.root / "memory" / "l2" / "entries" / f"{entry_id}.md", entry)

    packet.status = "promoted"
    packet.human_checkpoint_id = checkpoint_id
    write_record(packet_path, packet)

    return entry


def list_memory_entries_for_claim(ws: WorkspacePaths, claim_id: str) -> list[MemoryEntryRecord]:
    """Return active L2 memory entries derived from a claim."""

    return [
        entry
        for entry in list_records(ws.root / "memory" / "l2" / "entries", MemoryEntryRecord)
        if entry.source_claim_id == claim_id and entry.status == "active"
    ]


def memory_entry_brief_payload(
    entry: MemoryEntryRecord,
    *,
    evidence_records: list[EvidenceRecord] | None = None,
    tool_run_records: list[ToolRunRecord] | None = None,
) -> dict:
    """Return orientation-only L2 memory context for execution briefs."""

    payload = {
        "entry_id": entry.entry_id,
        "memory_kind": entry.memory_kind,
        "scope": entry.scope,
        "evidence_refs": list(entry.evidence_refs),
        "source_packet_id": entry.source_packet_id,
        "human_checkpoint_id": entry.human_checkpoint_id,
        "orientation_only": True,
    }
    code_state_ids = _code_state_ids_for_memory_entry(
        entry,
        evidence_records or [],
        tool_run_records or [],
    )
    if code_state_ids:
        payload["code_state_ids"] = code_state_ids
    return payload


def _code_state_ids_for_memory_entry(
    entry: MemoryEntryRecord,
    evidence_records: list[EvidenceRecord],
    tool_run_records: list[ToolRunRecord],
) -> list[str]:
    wanted = set(entry.evidence_refs)
    runs_by_id = {run.run_id: run for run in tool_run_records}
    seen = set()
    result = []
    for evidence in evidence_records:
        if evidence.evidence_id not in wanted:
            continue
        for run_id in evidence.tool_run_ids:
            run = runs_by_id.get(run_id)
            if not run:
                continue
            for code_state_id in run.code_state_ids:
                if code_state_id and code_state_id not in seen:
                    seen.add(code_state_id)
                    result.append(code_state_id)
    return result


def _ensure_tool_evidence_has_passed_validation_results(
    ws: WorkspacePaths,
    *,
    claim_id: str,
    evidence_refs: list[str],
    validation_result_ids: list[str],
) -> None:
    evidence_records = _resolve_evidence_records(ws, claim_id, evidence_refs)
    tool_run_ids = {
        run_id
        for evidence in evidence_records
        for run_id in getattr(evidence, "tool_run_ids", [])
        if run_id
    }
    if not tool_run_ids:
        return
    if not validation_result_ids:
        raise ValueError("promotion packet validation_result_ids must cover tool-derived evidence")
    validation_results = _resolve_validation_results(ws, claim_id, validation_result_ids)
    passed_tool_runs = {
        result.tool_run_id
        for result in validation_results
        if result.status == "passed"
        and not result.missing_outputs
        and not result.failure_modes_observed
    }
    if not tool_run_ids.issubset(passed_tool_runs):
        raise ValueError("promotion packet validation_result_ids must include passed results for every tool-derived evidence run")


def _resolve_evidence_records(ws: WorkspacePaths, claim_id: str, evidence_refs: list[str]) -> list[EvidenceRecord]:
    if not evidence_refs:
        return []
    wanted = set(evidence_refs)
    return [
        evidence
        for evidence in list_records(ws.registry_dir("evidence"), EvidenceRecord)
        if evidence.evidence_id in wanted and evidence.claim_id == claim_id
    ]


def _resolve_validation_results(
    ws: WorkspacePaths,
    claim_id: str,
    validation_result_ids: list[str],
) -> list[ValidationResultRecord]:
    if not validation_result_ids:
        return []
    wanted = set(validation_result_ids)
    return [
        result
        for result in list_records(ws.registry_dir("validation_results"), ValidationResultRecord)
        if result.result_id in wanted and result.claim_id == claim_id
    ]
