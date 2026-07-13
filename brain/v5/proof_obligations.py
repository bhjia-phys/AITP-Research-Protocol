"""Repository-backed proof-obligation lifecycle."""

from __future__ import annotations

from brain.v5.ids import prefixed_id
from brain.v5.models import ProofObligationRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WritePolicy
from brain.v5.workspace import get_claim


MATURITY_LEVELS = {
    "exploratory",
    "finite-size evidence",
    "formula-identified",
    "theorem-candidate",
    "publishable",
}


def get_proof_obligation(ws: WorkspacePaths, obligation_id: str) -> ProofObligationRecord:
    result = _repository(ws, "get_proof_obligation").read(
        f"proof_obligation:{obligation_id}"
    )
    if result.status != "found" or not isinstance(result.record, ProofObligationRecord):
        raise FileNotFoundError(f"proof obligation not found: {obligation_id}")
    return result.record


def list_proof_obligations_for_claim(
    ws: WorkspacePaths,
    claim_id: str,
) -> list[ProofObligationRecord]:
    report = _repository(ws, "list_proof_obligations").list("proof_obligations")
    if report.malformed:
        raise ValueError("cannot list proof obligations while records are malformed")
    return [record for record in report.records if record.claim_id == claim_id]


def create_proof_obligation(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str,
    statement: str,
    obligation_type: str,
    status: str,
    maturity_level: str,
    next_action: str,
    required_evidence: list[str] | None = None,
    proof_strategy: list[str] | None = None,
    failure_modes: list[str] | None = None,
    source_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    human_gate_required: bool = True,
) -> ProofObligationRecord:
    _require_known_claim(ws, claim_id, topic_id)
    _require_maturity(maturity_level)
    basis = f"{topic_id}:{claim_id}:{obligation_type}:{statement}:{next_action}"
    obligation_id = prefixed_id("proof-obligation", basis, max_slug=76)
    record = ProofObligationRecord(
        obligation_id=obligation_id,
        topic_id=topic_id,
        claim_id=claim_id,
        statement=statement,
        obligation_type=obligation_type,
        status=status,
        maturity_level=maturity_level,
        next_action=next_action,
        required_evidence=required_evidence or [],
        proof_strategy=proof_strategy or [],
        failure_modes=failure_modes or [],
        source_refs=source_refs or [],
        evidence_refs=evidence_refs or [],
        artifact_ids=artifact_ids or [],
        human_gate_required=human_gate_required,
        can_update_claim_trust=False,
    )
    _repository(ws, "create_proof_obligation").write(
        "proof_obligations",
        record,
        body=_body(record),
    )
    return record


def update_proof_obligation(
    ws: WorkspacePaths,
    *,
    obligation_id: str,
    topic_id: str = "",
    claim_id: str = "",
    statement: str = "",
    obligation_type: str = "",
    status: str = "",
    maturity_level: str = "",
    next_action: str = "",
    required_evidence: list[str] | None = None,
    proof_strategy: list[str] | None = None,
    failure_modes: list[str] | None = None,
    source_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    replace_lists: bool = False,
) -> ProofObligationRecord:
    repository = _repository(ws, "update_proof_obligation")
    current = repository.read(f"proof_obligation:{obligation_id}")
    if current.status != "found" or not isinstance(current.record, ProofObligationRecord):
        raise FileNotFoundError(f"proof obligation not found: {obligation_id}")
    record = current.record
    if topic_id and record.topic_id != topic_id:
        raise ValueError(
            f"proof obligation {obligation_id} belongs to topic {record.topic_id}, not {topic_id}"
        )
    if claim_id and record.claim_id != claim_id:
        raise ValueError(
            f"proof obligation {obligation_id} belongs to claim {record.claim_id}, not {claim_id}"
        )
    _require_known_claim(ws, record.claim_id, record.topic_id)
    if maturity_level:
        _require_maturity(maturity_level)

    record.statement = statement or record.statement
    record.obligation_type = obligation_type or record.obligation_type
    record.status = status or record.status
    record.maturity_level = maturity_level or record.maturity_level
    record.next_action = next_action or record.next_action
    record.required_evidence = _merge_list(
        record.required_evidence, required_evidence, replace=replace_lists
    )
    record.proof_strategy = _merge_list(
        record.proof_strategy, proof_strategy, replace=replace_lists
    )
    record.failure_modes = _merge_list(
        record.failure_modes, failure_modes, replace=replace_lists
    )
    record.source_refs = _merge_list(record.source_refs, source_refs, replace=replace_lists)
    record.evidence_refs = _merge_list(
        record.evidence_refs, evidence_refs, replace=replace_lists
    )
    record.artifact_ids = _merge_list(record.artifact_ids, artifact_ids, replace=replace_lists)
    record.human_gate_required = True
    record.can_update_claim_trust = False

    expected_hash = str((current.frontmatter or {}).get("record_content_hash") or "")
    if not expected_hash:
        raise ValueError(f"proof obligation lacks a revision hash: {obligation_id}")
    repository.write(
        "proof_obligations",
        record,
        body=_body(record),
        policy=WritePolicy(mode="revision", expected_hash=expected_hash),
    )
    return record


def _body(record: ProofObligationRecord) -> str:
    return (
        "# Proof Obligation\n\n"
        f"{record.statement}\n\n"
        f"Claim: `{record.claim_id}`\n\n"
        f"Status: `{record.status}`\n\n"
        f"Next action: {record.next_action}\n"
    )


def _repository(ws: WorkspacePaths, actor_id: str) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id=actor_id, host="aitp-v5"),
    )


def _require_known_claim(ws: WorkspacePaths, claim_id: str, topic_id: str) -> None:
    claim = get_claim(ws, claim_id)
    if claim.topic_id != topic_id:
        raise ValueError(f"claim {claim_id} belongs to topic {claim.topic_id}, not {topic_id}")


def _require_maturity(maturity_level: str) -> None:
    if maturity_level not in MATURITY_LEVELS:
        raise ValueError(f"maturity_level must be one of {sorted(MATURITY_LEVELS)}")


def _merge_list(
    current: list[str],
    values: list[str] | None,
    *,
    replace: bool,
) -> list[str]:
    if values is None:
        return list(current)
    if replace:
        return list(dict.fromkeys(values))
    return list(dict.fromkeys([*current, *values]))
