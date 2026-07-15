"""Canonical writers for source-specific physics assertions."""

from __future__ import annotations

from brain.v5.paths import WorkspacePaths
from brain.v5.physics_knowledge_contracts import validate_physics_assertion
from brain.v5.physics_knowledge_models import PhysicsAssertionRecord
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WriteResult


def record_physics_assertion(
    ws: WorkspacePaths,
    assertion: PhysicsAssertionRecord,
    *,
    actor: RecordActor,
) -> WriteResult:
    validate_physics_assertion(assertion, require_reviewed_grounding=True)
    repository = RecordRepository(ws, actor=actor)
    for ref in (
        assertion.object_ref,
        *assertion.source_asset_refs,
        *assertion.source_location_refs,
        *assertion.contradiction_refs,
    ):
        if repository.read(ref).status != "found":
            raise ValueError(f"physics assertion dependency does not resolve: {ref}")
    return repository.write(
        "physics_assertions",
        assertion,
        body=f"# Physics Assertion: {assertion.predicate}\n\n{assertion.value or assertion.expression}\n",
    )
