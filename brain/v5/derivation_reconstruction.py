"""Independent derivation coverage projected into source reconstruction audits."""

from __future__ import annotations

from dataclasses import asdict
from typing import Sequence

from brain.v5.derivation_models import DerivationChainRecord
from brain.v5.derivation_reviews import project_derivation_status
from brain.v5.models import ClaimRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import pin_current_record
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository


def build_derivation_coverage_batch(
    ws: WorkspacePaths,
    claims: Sequence[ClaimRecord],
) -> dict[str, dict]:
    """Project four derivation dimensions without changing source-stack completeness."""

    report = _repository(ws).list("derivation_chains")
    chains_by_claim: dict[str, list[DerivationChainRecord]] = {}
    for record in report.records:
        if isinstance(record, DerivationChainRecord):
            chains_by_claim.setdefault(record.claim_id, []).append(record)
    read_errors = [
        f"{issue.path}: {issue.error_type}: {issue.message}"
        for issue in report.malformed
    ]
    return {
        claim.claim_id: _claim_coverage(
            ws,
            claim,
            chains_by_claim.get(claim.claim_id, []),
            read_errors,
        )
        for claim in claims
    }


def recommended_derivation_actions(coverage: dict) -> list[str]:
    """Return independent next actions for applicable derivation coverage gaps."""

    if not coverage.get("applicable"):
        return []
    actions: list[str] = []
    if coverage["structural_closure"]["status"] == "missing":
        actions.append("complete_derivation_structure")
    if coverage["source_anchor_completeness"]["status"] == "missing":
        actions.append("complete_derivation_source_anchors")
    if coverage["review_coverage"]["status"] == "missing":
        actions.append("review_derivation")
    if coverage["validation_coverage"]["status"] == "missing":
        actions.append("validate_derivation")
    return actions


def _claim_coverage(
    ws: WorkspacePaths,
    claim: ClaimRecord,
    chains: list[DerivationChainRecord],
    read_errors: list[str],
) -> dict:
    workspace_health = {
        "status": "degraded" if read_errors else "healthy",
        "read_errors": list(read_errors),
    }
    applicable = claim.evidence_profile == "formal_derivation" or bool(chains)
    if not applicable:
        return {
            "applicable": False,
            "status": "not_applicable",
            "chain_refs": [],
            "structural_closure": _component(False, []),
            "source_anchor_completeness": _component(False, []),
            "review_coverage": _component(False, []),
            "validation_coverage": _component(False, []),
            "can_render_as_proved": False,
            "can_use_as_evidence_basis": False,
            "read_errors": [],
            "workspace_health": workspace_health,
            "can_update_claim_trust": False,
        }
    projections = []
    errors: list[str] = []
    for chain in chains:
        try:
            pin = pin_current_record(ws, f"derivation_chain:{chain.chain_id}")
            projections.append((pin, project_derivation_status(ws, pin)))
        except Exception as exc:  # noqa: BLE001 - coverage remains fail-closed.
            errors.append(f"derivation_chain:{chain.chain_id}: {exc}")
    structural_refs = [pin.record_ref for pin, item in projections if item.structurally_closed]
    source_refs = [pin.record_ref for pin, item in projections if item.source_complete]
    review_refs = [item.active_review_ref for _pin, item in projections if item.reviewed]
    validation_refs = [item.active_review_ref for _pin, item in projections if item.validated]
    has_projections = bool(projections)
    structural_complete = has_projections and not errors and all(
        item.structurally_closed for _pin, item in projections
    )
    source_complete = has_projections and not errors and all(
        item.source_complete for _pin, item in projections
    )
    review_complete = has_projections and not errors and all(
        item.reviewed for _pin, item in projections
    )
    validation_complete = has_projections and not errors and all(
        item.validated for _pin, item in projections
    )
    complete = validation_complete and not errors
    return {
        "applicable": True,
        "status": "complete" if complete else "incomplete",
        "chain_refs": [pin.record_ref for pin, _item in projections],
        "projections": [asdict(item) for _pin, item in projections],
        "structural_closure": _component(structural_complete, structural_refs),
        "source_anchor_completeness": _component(source_complete, source_refs),
        "review_coverage": _component(review_complete, review_refs),
        "validation_coverage": _component(validation_complete, validation_refs),
        "can_render_as_proved": False,
        "can_use_as_evidence_basis": complete,
        "read_errors": errors,
        "workspace_health": workspace_health,
        "can_update_claim_trust": False,
    }


def _component(satisfied: bool, refs: list[str]) -> dict:
    return {
        "status": "satisfied" if satisfied else "missing",
        "record_refs": list(dict.fromkeys(refs)),
    }


def _repository(ws: WorkspacePaths) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="system",
            actor_id="derivation-reconstruction-read",
            host="aitp",
        ),
    )
