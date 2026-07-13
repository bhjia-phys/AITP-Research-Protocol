from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import os
import pytest


def test_qft_qg_grounded_knowledge_and_speculative_insight_remain_separate(
    tmp_path,
    monkeypatch,
):
    from brain.v5.context_compiler import ContextRequest, compile_research_context
    from brain.v5.exploration import record_exploratory_record
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.record_repository import RecordRepository
    from brain.v5.research_state import create_proof_obligation, register_source
    from brain.v5.source_assets import register_source_asset
    from brain.v5.workspace import bind_session, create_claim, create_topic, get_claim, init_workspace

    ws = init_workspace(tmp_path)
    topic_id = "quantum-gravity-von-neumann"
    session_id = "session-qft-qg-e2e"
    create_topic(ws, topic_id, context_id="formal-theory", title="Quantum gravity algebras")
    claim = create_claim(
        ws,
        topic_id=topic_id,
        statement="A Type III to Type II transition is controlled by the stated algebraic regime.",
        evidence_profile="formal_derivation",
        confidence_state="hypothesis",
        active_uncertainty="The cross-paper bridge is interpretive and the derivation remains incomplete.",
    )
    bind_session(
        ws,
        session_id,
        topic_id=topic_id,
        context_id="formal-theory",
        active_claim=claim.claim_id,
    )

    canonical_before = _canonical_snapshot(ws)
    repository_writes = []
    original_write = RecordRepository.write

    def tracked_write(self, family, record, *, body="", policy=None):
        result = original_write(self, family, record, body=body, policy=policy)
        repository_writes.append((family, result))
        return result

    monkeypatch.setattr(RecordRepository, "write", tracked_write)

    first_location = register_source(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        uri="https://arxiv.org/pdf/2605.15180",
        label="Wormholes and Averaging over N, section 3",
        connector_id="arxiv",
        summary="Pinned source for the large-N algebraic setup.",
    )
    second_location = register_source(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        uri="https://arxiv.org/pdf/2510.06376",
        label="Emergent Mixed States, section 4",
        connector_id="arxiv",
        summary="Pinned source for the baby-universe mixed-state construction.",
    )
    first_asset = register_source_asset(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        asset_type="paper",
        uri=first_location.uri,
        title="Wormholes and Averaging over N",
        content_hash="a" * 64,
        hash_algorithm="sha256",
        version_anchor={"arxiv": "2605.15180v1"},
        reference_location_ids=[first_location.location_id],
    )
    second_asset = register_source_asset(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        asset_type="paper",
        uri=second_location.uri,
        title="Emergent Mixed States for Baby Universes and Black Holes",
        content_hash="b" * 64,
        hash_algorithm="sha256",
        version_anchor={"arxiv": "2510.06376v1"},
        reference_location_ids=[second_location.location_id],
    )
    algebra = record_physics_object(
        ws,
        topic_id=topic_id,
        object_type="von_neumann_algebra",
        name="Semifinite crossed-product algebra",
        definition="The algebra obtained only after the stated large-N and observer extension.",
        notation="M_crossed",
        assumptions=["large N", "specified observer algebra", "fixed convention for the trace"],
        source_refs=[f"source_asset:{first_asset.asset_id}"],
        metadata={"framework": "operator algebra", "regime": "large N"},
    )
    mixed_state = record_physics_object(
        ws,
        topic_id=topic_id,
        object_type="state",
        name="Baby-universe mixed state",
        definition="A source-grounded mixed state with no automatic identification with the crossed product.",
        notation="rho_BU",
        assumptions=["baby-universe sector", "source convention fixed"],
        source_refs=[f"source_asset:{second_asset.asset_id}"],
        metadata={"framework": "baby universes", "regime": "semiclassical"},
    )
    grounded_relation = record_object_relation(
        ws,
        topic_id=topic_id,
        relation_type="source_grounded_implication",
        subject_id=algebra.object_id,
        object_id=mixed_state.object_id,
        statement="The two constructions share a bounded algebra/state comparison problem.",
        claim_id=claim.claim_id,
        assumptions=["No equivalence is asserted across frameworks."],
        source_refs=[
            f"source_asset:{first_asset.asset_id}",
            f"source_asset:{second_asset.asset_id}",
        ],
        status="source_grounded",
    )
    obligation = create_proof_obligation(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        statement="Derive whether the comparison preserves the relevant trace and algebra type.",
        obligation_type="cross_framework_derivation",
        status="open",
        maturity_level="theorem-candidate",
        next_action="Write the convention-matched derivation with exact equation anchors.",
        required_evidence=["equation-level anchors from both papers"],
        failure_modes=["framework mismatch", "trace convention mismatch"],
        source_refs=[
            f"reference_location:{first_location.location_id}",
            f"reference_location:{second_location.location_id}",
        ],
    )
    insight = record_exploratory_record(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        session_id=session_id,
        exploration_type="relation_path_brainstorm",
        title="Speculative bridge between averaging and emergent mixedness",
        focal_question="Could the two mechanisms share an operator-algebraic explanation?",
        summary="A cross-paper interpretation, explicitly not source evidence or a proved relation.",
        object_ids=[algebra.object_id, mixed_state.object_id],
        relation_ids=[grounded_relation.relation_id],
        source_refs=[
            f"source_asset:{first_asset.asset_id}",
            f"source_asset:{second_asset.asset_id}",
        ],
        unresolved_points=[obligation.statement],
        metadata={
            "epistemic_role": "speculative_insight",
            "framework_boundary": "large-N crossed product versus baby-universe state",
            "can_be_used_as_evidence": False,
        },
    )

    bundle = compile_research_context(
        ws,
        ContextRequest(
            session_id=session_id,
            objective_text="Compare the paired quantum-gravity papers without crossing framework or speculation boundaries.",
            exact_refs=(
                f"source_asset:{first_asset.asset_id}",
                f"source_asset:{second_asset.asset_id}",
                f"physics_object:{algebra.object_id}",
                f"physics_object:{mixed_state.object_id}",
                f"object_relation:{grounded_relation.relation_id}",
                f"proof_obligation:{obligation.obligation_id}",
                f"exploratory_record:{insight.record_id}",
            ),
            max_tokens=1200,
            max_bytes=6000,
            candidate_limit=20,
        ),
    )

    assert bundle.read_errors == ()
    assert bundle.not_found_refs == ()
    assert bundle.index_status == "fresh"
    assert f"source_asset:{first_asset.asset_id}" in bundle.record_refs
    assert f"source_asset:{second_asset.asset_id}" in bundle.record_refs
    assert f"exploratory_record:{insight.record_id}" in bundle.record_refs
    assert any(
        item["record_ref"] == f"exploratory_record:{insight.record_id}"
        for item in bundle.candidate_summaries
    )
    assert get_claim(ws, claim.claim_id).confidence_state == "hypothesis"
    assert insight.metadata["can_be_used_as_evidence"] is False
    assert obligation.status == "open"
    assert bundle.can_update_claim_trust is False

    normal_bundle = compile_research_context(
        ws,
        ContextRequest(
            session_id=session_id,
            objective_text="Recover the speculative bridge between averaging and emergent mixedness.",
            max_tokens=1200,
            max_bytes=6000,
            candidate_limit=20,
        ),
    )
    assert any(
        item["record_ref"] == f"exploratory_record:{insight.record_id}"
        for item in normal_bundle.candidate_summaries
    )

    written_families = {family for family, _ in repository_writes}
    assert {
        "reference_locations",
        "source_assets",
        "physics_objects",
        "object_relations",
        "proof_obligations",
        "exploratory_records",
    }.issubset(written_families)

    canonical_after = _canonical_snapshot(ws)
    changed_canonical_paths = {
        path
        for path in set(canonical_before) | set(canonical_after)
        if canonical_before.get(path) != canonical_after.get(path)
    }
    successful_repository_paths = {
        Path(result.path).resolve()
        for _, result in repository_writes
        if result.status in {"created", "revised"}
    }
    successful_repository_paths.update(
        Path(result.archive_path).resolve()
        for _, result in repository_writes
        if result.archive_path
    )
    assert changed_canonical_paths == successful_repository_paths


def _canonical_snapshot(ws) -> dict[Path, str]:
    patterns = [
        (ws.root / "registry", "**/*.md"),
        (ws.root / "contexts", "*/context.md"),
        (ws.root / "topics", "*/topic.md"),
        (ws.root / "runtime" / "sessions", "*.md"),
        (ws.root / "memory" / "l2" / "entries", "*.md"),
        (ws.root / "revisions", "**/*.md"),
    ]
    return {
        path.resolve(): hashlib.sha256(path.read_bytes()).hexdigest()
        for root, pattern in patterns
        if root.exists()
        for path in root.glob(pattern)
    }


def test_qft_qg_derivation_coverage_requires_both_pinned_sources():
    from brain.v5.real_vertical_probes import _assess_qft_qg_derivation_coverage

    first_source = "source_asset:paper-a"
    second_source = "source_asset:paper-b"
    locations = [
        SimpleNamespace(location_id="location-a", source_ref=first_source),
        SimpleNamespace(location_id="location-b", source_ref=second_source),
    ]
    objects = [
        SimpleNamespace(object_id="object-a", source_refs=[first_source]),
        SimpleNamespace(object_id="object-b", source_refs=[second_source]),
    ]
    relations = [
        SimpleNamespace(
            relation_id="relation-real",
            claim_id="claim-real",
            subject_id="object-a",
            object_id="object-b",
            source_refs=[first_source, second_source],
            evidence_refs=[],
            status="hypothesis",
            metadata={"can_be_used_as_evidence": False},
        )
    ]
    partial_obligation = SimpleNamespace(
        claim_id="claim-real",
        source_refs=["reference_location:location-a"],
        status="open",
        maturity_level="formula-identified",
        required_evidence=["both source anchors"],
        proof_strategy=["derive"],
        failure_modes=["framework mismatch"],
        human_gate_required=True,
        can_update_claim_trust=False,
    )
    insight = SimpleNamespace(
        claim_id="claim-real",
        exploration_type="relation_path_brainstorm",
        status="open",
        object_ids=["object-a", "object-b"],
        relation_ids=["relation-real"],
        source_refs=[first_source, second_source],
        metadata={
            "epistemic_role": "speculative_insight",
            "can_be_used_as_evidence": False,
            "can_update_claim_trust": False,
        },
        orientation_only=True,
        can_update_claim_trust=False,
    )

    partial = _assess_qft_qg_derivation_coverage(
        source_refs=[first_source, second_source],
        claim_id="claim-real",
        proof_obligations=[partial_obligation],
        relations=relations,
        objects=objects,
        locations=locations,
        exploratory_records=[insight],
    )
    assert partial["source_grounded_proof_obligation_count"] == 0
    assert partial["ready"] is False

    duplicate_first_source_locations = _assess_qft_qg_derivation_coverage(
        source_refs=[first_source, second_source],
        claim_id="claim-real",
        proof_obligations=[partial_obligation],
        relations=relations,
        objects=objects,
        locations=[
            SimpleNamespace(location_id="location-a1", source_ref=first_source),
            SimpleNamespace(location_id="location-a2", source_ref=first_source),
        ],
        exploratory_records=[insight],
    )
    assert duplicate_first_source_locations["exact_reference_location_count"] == 2
    assert duplicate_first_source_locations["exact_reference_source_count"] == 1
    assert duplicate_first_source_locations["ready"] is False

    complete_obligation = SimpleNamespace(
        claim_id="claim-real",
        source_refs=[
            "reference_location:location-a",
            "reference_location:location-b",
        ],
        status="open",
        maturity_level="formula-identified",
        required_evidence=["both source anchors"],
        proof_strategy=["derive"],
        failure_modes=["framework mismatch"],
        human_gate_required=True,
        can_update_claim_trust=False,
    )
    complete = _assess_qft_qg_derivation_coverage(
        source_refs=[first_source, second_source],
        claim_id="claim-real",
        proof_obligations=[complete_obligation],
        relations=relations,
        objects=objects,
        locations=locations,
        exploratory_records=[insight],
    )
    assert complete["ready"] is True
    assert complete["covered_source_refs"] == [first_source, second_source]


def test_qft_qg_derivation_coverage_requires_connected_guarded_trace_and_insight():
    from brain.v5.real_vertical_probes import _assess_qft_qg_derivation_coverage

    first_source = "source_asset:paper-a"
    second_source = "source_asset:paper-b"
    source_refs = [first_source, second_source]
    anchor_expectations = {
        first_source: {
            "arxiv_version": "v1",
            "section_number": "2",
            "equation_labels": ["2.5", "2.6", "2.7", "2.8", "2.9"],
            "uri": "anchor:a",
        },
        second_source: {
            "arxiv_version": "v2",
            "section_number": "2",
            "equation_labels": ["2.1", "2.2"],
            "uri": "anchor:b",
        },
    }
    locations = [
        SimpleNamespace(
            location_id="location-a",
            source_ref=first_source,
            location_type="paper_equation_range",
            status="located",
            uri="anchor:a",
            metadata=anchor_expectations[first_source],
        ),
        SimpleNamespace(
            location_id="location-b",
            source_ref=second_source,
            location_type="paper_equation_range",
            status="located",
            uri="anchor:b",
            metadata=anchor_expectations[second_source],
        ),
    ]
    objects = [
        SimpleNamespace(object_id="object-a", source_refs=[first_source]),
        SimpleNamespace(object_id="object-b", source_refs=[second_source]),
    ]
    valid_relation = SimpleNamespace(
        relation_id="relation-valid",
        claim_id="claim-real",
        subject_id="object-a",
        object_id="object-b",
        source_refs=source_refs,
        evidence_refs=[],
        status="hypothesis",
        metadata={"can_be_used_as_evidence": False},
    )
    unconnected_relation = SimpleNamespace(
        relation_id="relation-unconnected",
        claim_id="claim-real",
        subject_id="unrelated-a",
        object_id="unrelated-b",
        source_refs=source_refs,
        evidence_refs=[],
        status="hypothesis",
        metadata={"can_be_used_as_evidence": False},
    )
    location_refs = [
        "reference_location:location-a",
        "reference_location:location-b",
    ]
    valid_obligation = SimpleNamespace(
        obligation_id="proof-valid",
        claim_id="claim-real",
        source_refs=location_refs,
        status="open",
        maturity_level="formula-identified",
        required_evidence=["both source anchors"],
        proof_strategy=["one", "two", "three", "four", "five"],
        failure_modes=["framework mismatch"],
        human_gate_required=True,
        can_update_claim_trust=False,
    )
    strategyless_obligation = SimpleNamespace(
        obligation_id="proof-strategyless",
        claim_id="claim-real",
        source_refs=location_refs,
        status="open",
        maturity_level="formula-identified",
        required_evidence=["both source anchors"],
        proof_strategy=[],
        failure_modes=["framework mismatch"],
        human_gate_required=False,
        can_update_claim_trust=False,
    )
    valid_insight = SimpleNamespace(
        claim_id="claim-real",
        exploration_type="relation_path_brainstorm",
        status="open",
        object_ids=["object-a", "object-b"],
        relation_ids=["relation-valid"],
        source_refs=source_refs,
        metadata={
            "epistemic_role": "speculative_insight",
            "can_be_used_as_evidence": False,
            "can_update_claim_trust": False,
        },
        orientation_only=True,
        can_update_claim_trust=False,
    )

    incomplete = _assess_qft_qg_derivation_coverage(
        source_refs=source_refs,
        claim_id="claim-real",
        anchor_expectations=anchor_expectations,
        required_proof_strategy=["one", "two", "three", "four", "five"],
        proof_obligations=[strategyless_obligation],
        relations=[unconnected_relation],
        objects=objects,
        locations=locations,
        exploratory_records=[],
    )
    assert incomplete["source_grounded_proof_obligation_count"] == 0
    assert incomplete["source_grounded_object_relation_count"] == 0
    assert incomplete["source_linked_speculative_insight_count"] == 0
    assert incomplete["ready"] is False

    complete = _assess_qft_qg_derivation_coverage(
        source_refs=source_refs,
        claim_id="claim-real",
        anchor_expectations=anchor_expectations,
        required_proof_strategy=["one", "two", "three", "four", "five"],
        proof_obligations=[valid_obligation],
        relations=[valid_relation],
        objects=objects,
        locations=locations,
        exploratory_records=[valid_insight],
    )
    assert complete["source_grounded_proof_obligation_count"] == 1
    assert complete["source_grounded_object_relation_count"] == 1
    assert complete["source_linked_speculative_insight_count"] == 1
    assert complete["ready"] is True


def test_real_qft_qg_probe_accepts_source_grounded_derivation_gap_without_trust_inflation():
    if os.environ.get("AITP_RUN_REAL_VERTICAL_PROBES") != "1":
        pytest.skip("set AITP_RUN_REAL_VERTICAL_PROBES=1 on the authorized research machine")

    from brain.v5.real_vertical_probes import run_qft_qg_real_probe

    repo_root = Path(__file__).resolve().parents[1]
    receipt = run_qft_qg_real_probe(
        topics_root=Path(r"F:\AI_Workspace\Theoretical-Physics\research\aitp-topics"),
        manifest_path=(
            repo_root / "tests" / "fixtures" / "v5_e2e" / "qft_qg" / "real_probe_manifest.json"
        ),
    )

    assert receipt["status"] == "passed"
    assert receipt["ok"] is True
    assert receipt["proof_obligation_count"] >= 1
    assert receipt["source_grounded_proof_obligation_count"] >= 1
    assert receipt["source_grounded_object_relation_count"] >= 1
    assert receipt["source_grounded_physics_object_count"] >= 2
    assert receipt["source_linked_speculative_insight_count"] >= 1
    assert receipt["exact_reference_location_count"] >= 2
    assert receipt["exact_reference_source_count"] == 2
    assert receipt["object_relation_count"] > 0
    assert receipt["physics_object_count"] > 0
    assert receipt["reference_location_count"] > 0
    assert len(receipt["sources"]) == 2
    assert receipt["blockers"] == []
    assert receipt["can_update_claim_trust"] is False
