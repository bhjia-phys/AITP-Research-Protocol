"""Read-only source reconstruction coverage audit for AITP v5 claims."""

from __future__ import annotations

from brain.v5.models import (
    EvidenceRecord,
    ObjectRelationRecord,
    PhysicsObjectRecord,
    ReferenceLocationRecord,
    ValidationContractRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_records
from brain.v5.workspace import get_claim

_REQUIRED_COMPONENTS = (
    "definitions",
    "assumptions_or_scope",
    "source_locations",
    "dependency_graph",
    "reconstruction_path",
    "failure_conditions",
)


def audit_source_reconstruction(ws: WorkspacePaths, *, claim_id: str) -> dict:
    """Check whether a claim has enough typed source stack to be reconstructable."""

    claim = get_claim(ws, claim_id)
    topic_id = claim.topic_id
    evidence = _claim_records(ws, EvidenceRecord, "evidence", claim_id=claim_id)
    references = _claim_records(ws, ReferenceLocationRecord, "reference_locations", claim_id=claim_id)
    objects = [record for record in list_records(ws.registry_dir("physics_objects"), PhysicsObjectRecord) if record.topic_id == topic_id]
    relations = [
        record
        for record in list_records(ws.registry_dir("object_relations"), ObjectRelationRecord)
        if record.topic_id == topic_id and (not record.claim_id or record.claim_id == claim_id)
    ]
    contracts = _claim_records(ws, ValidationContractRecord, "validation_contracts", claim_id=claim_id)

    source_refs = _source_refs(evidence, references, objects, relations)
    components = {
        "definitions": _component([record.object_id for record in objects if record.definition.strip()]),
        "assumptions_or_scope": _component(_assumption_refs(claim, objects, relations)),
        "source_locations": _component([record.location_id for record in references] + source_refs),
        "dependency_graph": _component([record.relation_id for record in relations]),
        "reconstruction_path": _component([
            record.evidence_id for record in evidence
            if "reconstruction_path" in set(record.supports_outputs)
        ]),
        "failure_conditions": _component(_failure_refs(claim, relations, contracts)),
    }
    missing = [name for name in _REQUIRED_COMPONENTS if components[name]["status"] == "missing"]
    return {
        "ok": True,
        "kind": "source_reconstruction_audit",
        "topic_id": topic_id,
        "claim_id": claim_id,
        "complete": not missing,
        "required_components": list(_REQUIRED_COMPONENTS),
        "missing_components": missing,
        "components": components,
        "source_refs": source_refs,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _claim_records(ws: WorkspacePaths, cls, registry_name: str, *, claim_id: str) -> list:
    return [record for record in list_records(ws.registry_dir(registry_name), cls) if record.claim_id == claim_id]


def _component(record_ids: list[str]) -> dict:
    ids = [record_id for record_id in record_ids if record_id]
    return {"status": "satisfied" if ids else "missing", "record_ids": ids}


def _source_refs(
    evidence: list[EvidenceRecord],
    references: list[ReferenceLocationRecord],
    objects: list[PhysicsObjectRecord],
    relations: list[ObjectRelationRecord],
) -> list[str]:
    refs: set[str] = set()
    for record in evidence:
        refs.update(record.source_refs)
    for record in references:
        if record.source_ref:
            refs.add(record.source_ref)
    for record in objects:
        refs.update(record.source_refs)
    for record in relations:
        refs.update(record.source_refs)
    return sorted(ref for ref in refs if ref)


def _assumption_refs(claim, objects: list[PhysicsObjectRecord], relations: list[ObjectRelationRecord]) -> list[str]:
    refs: list[str] = []
    if claim.scope.strip():
        refs.append("claim.scope")
    if claim.non_claims.strip():
        refs.append("claim.non_claims")
    refs.extend(record.object_id for record in objects if record.assumptions)
    refs.extend(record.relation_id for record in relations if record.assumptions)
    return refs


def _failure_refs(
    claim,
    relations: list[ObjectRelationRecord],
    contracts: list[ValidationContractRecord],
) -> list[str]:
    refs: list[str] = []
    if claim.strongest_failure_mode.strip():
        refs.append("claim.strongest_failure_mode")
    refs.extend(record.relation_id for record in relations if record.failure_modes)
    refs.extend(record.contract_id for record in contracts if record.failure_modes)
    return refs
