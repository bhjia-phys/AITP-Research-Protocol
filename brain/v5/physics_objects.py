"""Physics object and relation records for AITP v5."""

from __future__ import annotations

from brain.v5.ids import prefixed_id
from brain.v5.models import ObjectRelationRecord, PhysicsObjectRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.store import list_records


def record_physics_object(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    object_type: str,
    name: str,
    definition: str,
    notation: str = "",
    assumptions: list[str] | None = None,
    source_refs: list[str] | None = None,
    metadata: dict | None = None,
    linked_records: dict | None = None,
    status: str = "active",
) -> PhysicsObjectRecord:
    object_id = prefixed_id("physics-object", f"{topic_id}:{object_type}:{name}", max_slug=64)
    record = PhysicsObjectRecord(
        object_id=object_id,
        topic_id=topic_id,
        object_type=object_type,
        name=name,
        definition=definition,
        notation=notation,
        assumptions=assumptions or [],
        source_refs=source_refs or [],
        metadata=metadata or {},
        linked_records=linked_records or {},
        status=status,
    )
    _repository(ws, "record_physics_object").write(
        "physics_objects",
        record,
        body=f"# Physics Object: {name}\n\n{definition}\n",
    )
    return record


def list_physics_objects_for_topic(ws: WorkspacePaths, topic_id: str) -> list[PhysicsObjectRecord]:
    return [
        obj
        for obj in list_records(ws.registry_dir("physics_objects"), PhysicsObjectRecord)
        if obj.topic_id == topic_id
    ]


def record_object_relation(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    relation_type: str,
    subject_id: str,
    object_id: str,
    statement: str,
    claim_id: str = "",
    assumptions: list[str] | None = None,
    failure_modes: list[str] | None = None,
    source_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    metadata: dict | None = None,
    status: str = "hypothesis",
) -> ObjectRelationRecord:
    relation_id = prefixed_id(
        "object-relation",
        f"{topic_id}:{relation_type}:{subject_id}:{object_id}:{statement}",
        max_slug=64,
    )
    record = ObjectRelationRecord(
        relation_id=relation_id,
        topic_id=topic_id,
        relation_type=relation_type,
        subject_id=subject_id,
        object_id=object_id,
        statement=statement,
        claim_id=claim_id,
        assumptions=assumptions or [],
        failure_modes=failure_modes or [],
        source_refs=source_refs or [],
        evidence_refs=evidence_refs or [],
        metadata=metadata or {},
        status=status,
    )
    _repository(ws, "record_object_relation").write(
        "object_relations",
        record,
        body=f"# Object Relation: {relation_type}\n\n{statement}\n",
    )
    return record


def list_object_relations_for_claim(ws: WorkspacePaths, claim_id: str) -> list[ObjectRelationRecord]:
    return [
        relation
        for relation in list_records(ws.registry_dir("object_relations"), ObjectRelationRecord)
        if relation.claim_id == claim_id
    ]


def object_relation_brief_payload(relation: ObjectRelationRecord) -> dict:
    payload = {
        "relation_id": relation.relation_id,
        "relation_type": relation.relation_type,
        "subject_id": relation.subject_id,
        "object_id": relation.object_id,
        "statement": relation.statement,
        "failure_modes": list(relation.failure_modes),
        "status": relation.status,
    }
    metadata = relation.metadata if isinstance(relation.metadata, dict) else {}
    if metadata.get("schema_version") == "formula-code-relation/v1":
        code_state_ref = metadata.get("code_state_ref")
        payload["formula_code"] = {
            "module": str(metadata.get("module") or ""),
            "function": str(metadata.get("function") or ""),
            "parameter": str(metadata.get("parameter") or ""),
            "output": str(metadata.get("output") or ""),
            "applicability_boundary": str(metadata.get("applicability_boundary") or ""),
            "code_state_ref": (
                str(code_state_ref.get("record_ref") or "")
                if isinstance(code_state_ref, dict)
                else ""
            ),
        }
    return payload


def _repository(ws: WorkspacePaths, actor_id: str) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id=actor_id, host="aitp-v5"),
    )
