"""Validation contracts for grounded physics assertions."""

from __future__ import annotations

from brain.v5.physics_knowledge_models import PhysicsAssertionRecord


def validate_physics_assertion(
    assertion: PhysicsAssertionRecord,
    *,
    require_reviewed_grounding: bool = False,
) -> PhysicsAssertionRecord:
    if not assertion.object_ref.startswith("physics_object:"):
        raise ValueError("physics assertion object_ref must be a typed physics_object ref")
    if not assertion.predicate.strip() or not (assertion.value.strip() or assertion.expression.strip()):
        raise ValueError("physics assertion requires a predicate and value or expression")
    if require_reviewed_grounding and assertion.review_status == "reviewed":
        if not assertion.source_asset_refs or not assertion.source_location_refs:
            raise ValueError("reviewed assertion requires source asset and source location grounding")
    return assertion
