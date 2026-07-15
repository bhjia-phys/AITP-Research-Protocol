"""Read-only compatibility audit for schema-v1 physics knowledge records."""

from __future__ import annotations

from dataclasses import asdict

from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository


def audit_physics_knowledge_v1_compatibility(ws: WorkspacePaths) -> dict:
    repository = RecordRepository(
        ws,
        actor=RecordActor(actor_type="migration", actor_id="physics-knowledge-audit", host="audit"),
    )
    object_report = repository.list("physics_objects")
    relation_report = repository.list("object_relations")
    candidates = []
    for record in object_report.records:
        if record.definition or record.notation or record.source_refs:
            candidates.append(
                {
                    "object_ref": f"physics_object:{record.object_id}",
                    "predicate": "definition",
                    "value": record.definition,
                    "expression": record.notation,
                    "legacy_source_refs": list(record.source_refs),
                    "missing_review_data": [
                        "source_asset_refs",
                        "source_location_refs",
                        "framework",
                        "regime",
                        "review_status",
                    ],
                }
            )
    malformed = [
        asdict(issue)
        for report in (object_report, relation_report)
        for issue in report.malformed
    ]
    return {
        "ok": not malformed,
        "kind": "physics_knowledge_v1_compatibility_audit",
        "object_count": object_report.loaded_count,
        "relation_count": relation_report.loaded_count,
        "candidate_assertion_count": len(candidates),
        "candidate_assertions": candidates,
        "malformed": malformed,
        "writes_records": False,
        "orientation_only": True,
        "can_update_claim_trust": False,
    }
