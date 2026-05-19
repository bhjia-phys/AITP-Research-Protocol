"""Physics object and relation records for AITP v5."""

from __future__ import annotations

from brain.v5.ids import prefixed_id
from brain.v5.models import ObjectRelationRecord, PhysicsObjectRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_records, write_record


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
    write_record(
        ws.registry_dir("physics_objects") / f"{object_id}.md",
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
    write_record(
        ws.registry_dir("object_relations") / f"{relation_id}.md",
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
