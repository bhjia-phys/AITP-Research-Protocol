from __future__ import annotations


def _candidate(*kinds: str, **overrides):
    from brain.v5.knowledge_candidates import KnowledgeCandidate

    values = {
        "candidate_id": "candidate-1",
        "content_kinds": kinds,
        "statement": "Candidate statement.",
    }
    values.update(overrides)
    return KnowledgeCandidate(**values)


def test_grounded_physics_content_routes_to_knowledge_not_skill():
    from brain.v5.knowledge_candidates import route_knowledge_candidate

    for kind in ("definition", "formula", "convention", "relation", "derivation"):
        route = route_knowledge_candidate(_candidate(kind))
        assert route.lane == "grounded_knowledge"
        assert route.eligible_for_skill is False
        assert route.can_update_claim_trust is False


def test_interpretive_content_routes_to_non_evidence_insight():
    from brain.v5.knowledge_candidates import route_knowledge_candidate

    for kind in (
        "interpretation",
        "analogy",
        "conjecture",
        "failed_route_lesson",
        "counterexample_direction",
        "conceptual_bridge",
        "open_research_direction",
    ):
        route = route_knowledge_candidate(_candidate(kind))
        assert route.lane == "speculative_insight"
        assert route.evidence_role == "forbidden"
        assert route.eligible_for_skill is False


def test_only_complete_procedural_workflow_can_route_to_skill_review():
    from brain.v5.knowledge_candidates import route_knowledge_candidate

    incomplete = route_knowledge_candidate(_candidate("procedural_workflow"))
    complete = route_knowledge_candidate(
        _candidate(
            "procedural_workflow",
            procedural_steps=("prepare input", "run solver", "validate output"),
            validation_refs=("validation_result:solver-pass",),
            applicability_boundary="LibRPA QSGW run with matching code and environment pins.",
        )
    )

    assert incomplete.lane == "procedural_skill"
    assert incomplete.eligible_for_skill is False
    assert complete.eligible_for_skill is True
    assert complete.requires_human_review is True


def test_mixed_physics_and_workflow_candidate_requires_explicit_split():
    from brain.v5.knowledge_candidates import route_knowledge_candidate

    route = route_knowledge_candidate(
        _candidate(
            "formula",
            "procedural_workflow",
            procedural_steps=("run solver",),
            validation_refs=("validation_result:solver-pass",),
            applicability_boundary="bounded fixture",
        )
    )

    assert route.lane == "mixed_split_required"
    assert route.split_required is True
    assert route.eligible_for_skill is False
    assert set(route.target_lanes) == {"grounded_knowledge", "procedural_skill"}
