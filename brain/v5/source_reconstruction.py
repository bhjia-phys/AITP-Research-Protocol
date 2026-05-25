"""Read-only source reconstruction coverage audit for AITP v5 claims."""

from __future__ import annotations

from brain.v5.models import (
    ClaimRecord,
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

    return audit_source_reconstruction_batch(ws, [claim_id])[claim_id]


def build_source_reconstruction_manifest(ws: WorkspacePaths) -> dict:
    """Build an actionable read-only manifest for source reconstruction gaps."""

    claims = list_records(ws.registry_dir("claims"), ClaimRecord)
    audits = audit_source_reconstruction_batch(ws, [claim.claim_id for claim in claims])
    references_by_claim = _group_by_claim(list_records(ws.registry_dir("reference_locations"), ReferenceLocationRecord))
    items = [
        _manifest_item(
            claim,
            audits[claim.claim_id],
            has_direct_reference=bool(references_by_claim.get(claim.claim_id)),
        )
        for claim in claims
    ]
    items.sort(key=lambda item: (item["status"] == "complete", item["topic_id"], item["claim_id"]))
    incomplete = [item for item in items if item["status"] == "incomplete"]
    complete = [item for item in items if item["status"] == "complete"]
    return {
        "kind": "source_reconstruction_manifest",
        "claim_count": len(items),
        "complete_claim_count": len(complete),
        "incomplete_claim_count": len(incomplete),
        "missing_component_counts": _missing_component_counts(incomplete),
        "items": items,
        "next_actions": [f"source_reconstruction:{item['claim_id']}" for item in incomplete],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def audit_source_reconstruction_batch(ws: WorkspacePaths, claim_ids: list[str]) -> dict[str, dict]:
    """Batch source reconstruction audits without repeated registry scans."""

    wanted = _unique(claim_ids)
    if not wanted:
        return {}
    claims_by_id = {claim.claim_id: claim for claim in list_records(ws.registry_dir("claims"), ClaimRecord)}
    evidence_by_claim = _group_by_claim(list_records(ws.registry_dir("evidence"), EvidenceRecord))
    references_by_claim = _group_by_claim(list_records(ws.registry_dir("reference_locations"), ReferenceLocationRecord))
    objects_by_topic = _group_by_topic(list_records(ws.registry_dir("physics_objects"), PhysicsObjectRecord))
    relations = list_records(ws.registry_dir("object_relations"), ObjectRelationRecord)
    contracts_by_claim = _group_by_claim(list_records(ws.registry_dir("validation_contracts"), ValidationContractRecord))
    audits = {}
    for claim_id in wanted:
        claim = claims_by_id.get(claim_id) or get_claim(ws, claim_id)
        topic_id = claim.topic_id
        audits[claim_id] = _audit_claim_source_reconstruction(
            claim,
            evidence=evidence_by_claim.get(claim_id, []),
            references=references_by_claim.get(claim_id, []),
            objects=objects_by_topic.get(topic_id, []),
            relations=[
                record
                for record in relations
                if record.topic_id == topic_id and (not record.claim_id or record.claim_id == claim_id)
            ],
            contracts=contracts_by_claim.get(claim_id, []),
        )
    return audits


def _manifest_item(claim: ClaimRecord, audit: dict, *, has_direct_reference: bool) -> dict:
    missing_components = list(audit["missing_components"])
    complete = bool(audit["complete"])
    return {
        "topic_id": claim.topic_id,
        "claim_id": claim.claim_id,
        "claim_statement": claim.statement,
        "status": "complete" if complete else "incomplete",
        "review_priority": "low" if complete else "high",
        "missing_components": missing_components,
        "satisfied_components": [
            name for name in audit["required_components"] if name not in set(missing_components)
        ],
        "source_refs": list(audit["source_refs"]),
        "recommended_actions": _recommended_actions_for_missing(
            missing_components,
            has_direct_reference=has_direct_reference,
        ),
        "audit_cli": f"aitp-v5 source reconstruction-audit --claim {claim.claim_id}",
        "audit_mcp": "aitp_v5_audit_source_reconstruction",
        "can_update_claim_trust": False,
    }


def _recommended_actions_for_missing(missing_components: list[str], *, has_direct_reference: bool = True) -> list[str]:
    action_map = {
        "definitions": "record_physics_object",
        "assumptions_or_scope": "record_claim_scope_or_object_assumptions",
        "source_locations": "record_reference_location",
        "dependency_graph": "record_object_relation",
        "reconstruction_path": "record_evidence_with_reconstruction_path",
        "failure_conditions": "record_failure_conditions_or_validation_contract",
    }
    actions = [action_map[component] for component in missing_components if component in action_map]
    if not has_direct_reference:
        actions.append("record_reference_location")
    return _unique(actions)


def _missing_component_counts(items: list[dict]) -> dict[str, int]:
    counts = {component: 0 for component in _REQUIRED_COMPONENTS}
    for item in items:
        for component in item["missing_components"]:
            if component in counts:
                counts[component] += 1
    return counts


def _audit_claim_source_reconstruction(
    claim: ClaimRecord,
    *,
    evidence: list[EvidenceRecord],
    references: list[ReferenceLocationRecord],
    objects: list[PhysicsObjectRecord],
    relations: list[ObjectRelationRecord],
    contracts: list[ValidationContractRecord],
) -> dict:
    topic_id = claim.topic_id
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
        "claim_id": claim.claim_id,
        "complete": not missing,
        "required_components": list(_REQUIRED_COMPONENTS),
        "missing_components": missing,
        "components": components,
        "source_refs": source_refs,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


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


def _group_by_claim(records) -> dict[str, list]:
    grouped: dict[str, list] = {}
    for record in records:
        grouped.setdefault(record.claim_id, []).append(record)
    return grouped


def _group_by_topic(records) -> dict[str, list]:
    grouped: dict[str, list] = {}
    for record in records:
        grouped.setdefault(record.topic_id, []).append(record)
    return grouped


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


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
