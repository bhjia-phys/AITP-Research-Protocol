"""L2 memory and promotion packet management for AITP v5."""

from __future__ import annotations

from dataclasses import asdict

from brain.v5.contracts import ContractError
from brain.v5.evidence_basis_policy import persisted_evidence_basis_is_trust_admissible
from brain.v5.evidence_support_policy import evidence_support_record_ids
from brain.v5.human_approval import checkpoint_can_authorize_trust
from brain.v5.ids import prefixed_id
from brain.v5.models import (
    EvidenceRecord,
    FailureModeReviewResultRecord,
    HumanCheckpointRecord,
    MemoryEntryRecord,
    PromotionPacketRecord,
    ToolRunRecord,
    ValidationResultRecord,
)
from brain.v5.promotion_checkpoints import (
    request_promotion_checkpoint,
    require_approved_promotion_checkpoint,
)
from brain.v5.record_contracts import require_valid_memory_entry_record, require_valid_promotion_packet_record
from brain.v5.record_envelope import RecordActor, canonical_record_hash
from brain.v5.record_repository import RecordRepository, WritePolicy
from brain.v5.store import list_records, read_record
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
    failure_mode_review_checkpoint_id: str,
    failure_mode_review_result_id: str,
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
            "failure_mode_review_checkpoint:" + failure_mode_review_checkpoint_id,
            "failure_mode_review_result:" + failure_mode_review_result_id,
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
    failure_mode_review_checkpoint_id: str = "",
    failure_mode_review_result_id: str = "",
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
    _require_admissible_evidence_refs(ws, claim_id, evidence_refs or [])
    if failure_mode_review_checkpoint_id or failure_mode_review_result_id:
        _ensure_passed_failure_mode_review_result(
            ws,
            topic_id=topic_id,
            claim_id=claim_id,
            checkpoint_id=failure_mode_review_checkpoint_id,
            result_id=failure_mode_review_result_id,
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
            failure_mode_review_checkpoint_id=failure_mode_review_checkpoint_id,
            failure_mode_review_result_id=failure_mode_review_result_id,
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
        failure_mode_review_checkpoint_id=failure_mode_review_checkpoint_id,
        failure_mode_review_result_id=failure_mode_review_result_id,
    )
    _require_valid_promotion_packet(packet)
    _repository(ws, actor_id="create_promotion_packet").write(
        "promotion_packets",
        packet,
        body=f"# Promotion Packet\n\nClaim: `{claim_id}`\n",
    )
    return packet


def apply_promotion_packet(
    ws: WorkspacePaths,
    *,
    packet_id: str,
    checkpoint_id: str,
) -> MemoryEntryRecord:
    if not checkpoint_id:
        raise ValueError("approved human checkpoint is required to apply a promotion packet")

    repository = _repository(ws, actor_id="apply_promotion_packet")
    # This transition lock is distinct from the packet's own repository lock.
    with repository.lock_record("promotion_packets", f"{packet_id}-application"):
        packet_read = repository.read(f"promotion_packet:{packet_id}")
        if packet_read.status != "found" or not isinstance(
            packet_read.record, PromotionPacketRecord
        ):
            raise ValueError(f"promotion packet not found or malformed: {packet_id}")
        packet = packet_read.record
        _require_valid_promotion_packet(packet)
        _validate_promotion_basis(ws, packet)

        checkpoint_read = repository.read(f"human_checkpoint:{checkpoint_id}")
        if checkpoint_read.status != "found" or not isinstance(
            checkpoint_read.record, HumanCheckpointRecord
        ):
            raise ValueError(f"approved human checkpoint not found or malformed: {checkpoint_id}")
        checkpoint = checkpoint_read.record
        require_approved_promotion_checkpoint(ws, packet, checkpoint)

        claim = get_claim(ws, packet.claim_id)
        entry = _memory_entry_for_packet(packet, checkpoint_id, claim.statement)
        entry_read = repository.read(f"memory_entry:{entry.entry_id}")

        if packet.status == "promoted":
            if packet.human_checkpoint_id != checkpoint_id:
                raise ValueError("promotion packet is already promoted by a different checkpoint")
            if entry_read.status == "found":
                if not isinstance(entry_read.record, MemoryEntryRecord) or asdict(
                    entry_read.record
                ) != asdict(entry):
                    raise ValueError("promoted packet has a conflicting memory entry")
                raise ValueError("promotion packet is already promoted")
            if entry_read.status != "not_found":
                raise ValueError("promoted packet memory entry is malformed")
            repository.write(
                "memory_entries",
                entry,
                body=f"# Memory Entry\n\nSource packet: `{packet_id}`\n",
            )
            return entry

        if entry_read.status != "not_found":
            raise ValueError("unpromoted packet already has a canonical memory entry")

        packet.status = "promoted"
        packet.human_checkpoint_id = checkpoint_id
        _require_valid_promotion_packet(packet)
        repository.write(
            "promotion_packets",
            packet,
            body=packet_read.body,
            policy=WritePolicy(
                mode="revision",
                expected_hash=_read_content_hash(packet_read.frontmatter, packet_read.body),
            ),
        )
        # The packet is the authorization commit. If materialization is
        # interrupted, a retry enters the recovery branch above.
        repository.write(
            "memory_entries",
            entry,
            body=f"# Memory Entry\n\nSource packet: `{packet_id}`\n",
        )
        return entry


def _validate_promotion_basis(ws: WorkspacePaths, packet: PromotionPacketRecord) -> None:
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
    _require_admissible_evidence_refs(ws, packet.claim_id, packet.evidence_refs)
    if packet.failure_mode_review_checkpoint_id or packet.failure_mode_review_result_id:
        _ensure_passed_failure_mode_review_result(
            ws,
            topic_id=packet.topic_id,
            claim_id=packet.claim_id,
            checkpoint_id=packet.failure_mode_review_checkpoint_id,
            result_id=packet.failure_mode_review_result_id,
        )


def _memory_entry_for_packet(
    packet: PromotionPacketRecord,
    checkpoint_id: str,
    statement: str,
) -> MemoryEntryRecord:
    entry = MemoryEntryRecord(
        entry_id=prefixed_id("memory", packet.packet_id),
        topic_id=packet.topic_id,
        source_claim_id=packet.claim_id,
        source_topic_id=packet.topic_id,
        statement=statement,
        memory_kind=packet.proposed_memory_kind,
        scope=packet.scope,
        evidence_refs=list(packet.evidence_refs),
        validation_result_ids=list(packet.validation_result_ids),
        non_claims=list(packet.non_claims),
        known_failure_modes=list(packet.known_failure_modes),
        source_packet_id=packet.packet_id,
        human_checkpoint_id=checkpoint_id,
        failure_mode_review_checkpoint_id=packet.failure_mode_review_checkpoint_id,
        failure_mode_review_result_id=packet.failure_mode_review_result_id,
        status="active",
    )
    _require_valid_memory_entry(entry)
    return entry


def _read_content_hash(frontmatter: dict | None, body: str) -> str:
    payload = frontmatter or {}
    return str(payload.get("record_content_hash") or "") or canonical_record_hash(
        payload, body
    )


def _repository(ws: WorkspacePaths, *, actor_id: str) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id=actor_id, host="aitp"),
    )


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
    if entry.validation_result_ids:
        payload["validation_result_ids"] = list(entry.validation_result_ids)
    code_state_ids = _code_state_ids_for_memory_entry(
        entry,
        evidence_records or [],
        tool_run_records or [],
    )
    if code_state_ids:
        payload["code_state_ids"] = code_state_ids
    if entry.failure_mode_review_checkpoint_id:
        payload["failure_mode_review_checkpoint_id"] = entry.failure_mode_review_checkpoint_id
    if entry.failure_mode_review_result_id:
        payload["failure_mode_review_result_id"] = entry.failure_mode_review_result_id
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
        for run_id in evidence_support_record_ids(evidence, "tool_run")
    }
    exact_result_ids = {
        result_id
        for evidence in evidence_records
        for result_id in evidence_support_record_ids(evidence, "validation_result")
    }
    if set(validation_result_ids) != exact_result_ids:
        raise ValueError(
            "promotion packet validation_result_ids must match the exact evidence basis"
        )
    if not tool_run_ids:
        return
    validation_results = _resolve_validation_results(ws, claim_id, sorted(exact_result_ids))
    if {result.result_id for result in validation_results} != exact_result_ids:
        raise ValueError("promotion packet exact evidence basis contains unknown validation results")
    passed_tool_runs = {
        result.tool_run_id
        for result in validation_results
        if result.status == "passed"
        and not result.missing_outputs
        and not result.failure_modes_observed
    }
    if not tool_run_ids.issubset(passed_tool_runs):
        raise ValueError("promotion packet validation_result_ids must include passed results for every tool-derived evidence run")


def _ensure_passed_failure_mode_review_result(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str,
    checkpoint_id: str,
    result_id: str,
) -> FailureModeReviewResultRecord:
    if not checkpoint_id or not result_id:
        raise ValueError("promotion packet failure_mode_review_result_id must cite a passed failure-mode review result")
    checkpoint = _resolve_approved_failure_mode_review_checkpoint(ws, claim_id, checkpoint_id)
    if checkpoint.topic_id != topic_id:
        raise ValueError("failure-mode review checkpoint must belong to the promotion topic")
    records = list_records(ws.registry_dir("failure_mode_reviews"), FailureModeReviewResultRecord)
    result = next((record for record in records if record.result_id == result_id), None)
    if result is None:
        raise ValueError(f"unknown failure_mode_review_result_id: {result_id}")
    if result.topic_id != topic_id or result.claim_id != claim_id or result.checkpoint_id != checkpoint_id:
        raise ValueError("failure-mode review result must belong to the same topic, claim, and checkpoint as the promotion packet")
    if result.status != "passed":
        raise ValueError("promotion packet requires a passed failure-mode review result")
    return result


def _resolve_approved_failure_mode_review_checkpoint(
    ws: WorkspacePaths,
    claim_id: str,
    checkpoint_id: str,
) -> HumanCheckpointRecord:
    checkpoints = list_records(ws.registry_dir("checkpoints"), HumanCheckpointRecord)
    checkpoint = next((record for record in checkpoints if record.checkpoint_id == checkpoint_id), None)
    if checkpoint is None:
        raise ValueError(f"unknown failure-mode review checkpoint: {checkpoint_id}")
    if checkpoint.claim_id != claim_id or checkpoint.requested_by != "failure_mode_review_packet":
        raise ValueError("failure-mode review checkpoint must belong to the same claim")
    if checkpoint.status != "decided" or checkpoint.decision != "approve_failure_mode_review":
        raise ValueError("promotion packet requires an approved failure-mode review checkpoint")
    if not checkpoint_can_authorize_trust(checkpoint):
        raise ValueError("promotion packet requires a host-verified failure-mode review checkpoint")
    return checkpoint


def _resolve_evidence_records(ws: WorkspacePaths, claim_id: str, evidence_refs: list[str]) -> list[EvidenceRecord]:
    if not evidence_refs:
        return []
    wanted = set(evidence_refs)
    return [
        evidence
        for evidence in list_records(ws.registry_dir("evidence"), EvidenceRecord)
        if evidence.evidence_id in wanted and evidence.claim_id == claim_id
    ]


def _require_admissible_evidence_refs(
    ws: WorkspacePaths,
    claim_id: str,
    evidence_refs: list[str],
) -> None:
    records = _resolve_evidence_records(ws, claim_id, evidence_refs)
    resolved = {record.evidence_id for record in records}
    if set(evidence_refs) != resolved or any(
        not persisted_evidence_basis_is_trust_admissible(ws, record) for record in records
    ):
        raise ValueError(
            "promotion packet requires an admissible evidence basis; "
            "use a trust-admissible exact evidence basis"
        )


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


def _require_valid_promotion_packet(packet: PromotionPacketRecord) -> None:
    try:
        require_valid_promotion_packet_record({"ok": True, **asdict(packet)})
    except ContractError as exc:
        raise ValueError(str(exc)) from exc


def _require_valid_memory_entry(entry: MemoryEntryRecord) -> None:
    try:
        require_valid_memory_entry_record({"ok": True, **asdict(entry)})
    except ContractError as exc:
        raise ValueError(str(exc)) from exc
