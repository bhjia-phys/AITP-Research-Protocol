from __future__ import annotations

import hashlib
from pathlib import Path

import pytest


def test_multi_topic_reuse_requires_bridge_and_target_validation(tmp_path, monkeypatch):
    from brain.v5.context_compiler import ContextRequest, compile_research_context
    from brain.v5.exploration import record_exploratory_record
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.record_repository import RecordRepository
    from brain.v5.source_assets import register_source_asset
    from brain.v5.tools import record_tool_run, register_tool_recipe
    from brain.v5.validation import create_validation_contract, record_validation_result
    from brain.v5.workspace import bind_session, create_claim, create_topic, get_claim, init_workspace

    ws = init_workspace(tmp_path)
    source_topic = "shared-finite-size-method"
    target_topic = "new-spin-chain-application"
    create_topic(ws, source_topic, context_id="numerics", title="Shared finite-size method")
    create_topic(ws, target_topic, context_id="numerics", title="Spin-chain application")
    source_claim = create_claim(
        ws,
        topic_id=source_topic,
        statement="The inverse-size workflow passes on its source benchmark.",
        evidence_profile="numerical",
        confidence_state="validated",
        active_uncertainty="Transfer to other Hamiltonians is not established.",
    )
    target_claim = create_claim(
        ws,
        topic_id=target_topic,
        statement="The inverse-size workflow is valid for the target spin-chain observable.",
        evidence_profile="numerical",
        confidence_state="hypothesis",
        active_uncertainty="The target correction exponent may differ from one.",
    )
    bind_session(
        ws,
        "session-multi-topic-target",
        topic_id=target_topic,
        context_id="numerics",
        active_claim=target_claim.claim_id,
    )
    canonical_before = _canonical_snapshot(ws)
    repository_writes = []
    original_write = RecordRepository.write

    def tracked_write(self, family, record, *, body="", policy=None):
        result = original_write(self, family, record, body=body, policy=policy)
        repository_writes.append((family, result))
        return result

    monkeypatch.setattr(RecordRepository, "write", tracked_write)

    source_asset = register_source_asset(
        ws,
        topic_id=source_topic,
        claim_id=source_claim.claim_id,
        asset_type="note",
        uri="https://example.invalid/finite-size-method-v1",
        title="Inverse-size extrapolation method note",
        content_hash="c" * 64,
        hash_algorithm="sha256",
        version_anchor={"version": "1"},
    )
    source_object = record_physics_object(
        ws,
        topic_id=source_topic,
        object_type="workflow_assumption",
        name="Leading inverse-size correction",
        definition="The leading correction is proportional to 1/L in the source benchmark.",
        assumptions=["source benchmark only"],
        source_refs=[f"source_asset:{source_asset.asset_id}"],
    )
    source_insight = record_exploratory_record(
        ws,
        topic_id=source_topic,
        claim_id=source_claim.claim_id,
        exploration_type="relation_path_brainstorm",
        title="Speculative universality of the inverse-size exponent",
        focal_question="Could the same exponent apply to unrelated spin chains?",
        summary="Source-topic speculation only; it is not transferable evidence.",
        object_ids=[source_object.object_id],
        metadata={"epistemic_role": "speculative_insight", "transferable": False},
    )
    target_object = record_physics_object(
        ws,
        topic_id=target_topic,
        object_type="observable",
        name="Target spin-chain gap",
        definition="The finite-size spectral gap measured in the target Hamiltonian.",
        assumptions=["target Hamiltonian and boundary conditions fixed"],
    )
    bridge = record_object_relation(
        ws,
        topic_id=target_topic,
        relation_type="cross_topic_grounded_reference",
        subject_id=source_object.object_id,
        object_id=target_object.object_id,
        statement="The source workflow may be reused only as a target-side test candidate.",
        claim_id=target_claim.claim_id,
        assumptions=["Target correction exponent must be revalidated."],
        source_refs=[f"source_asset:{source_asset.asset_id}"],
        failure_modes=["source benchmark assumptions do not hold for the target Hamiltonian"],
        metadata={
            "source_topic_id": source_topic,
            "target_topic_id": target_topic,
            "requires_target_revalidation": True,
            "can_transfer_claim_trust": False,
            "source_insight_ref": f"exploratory_record:{source_insight.record_id}",
        },
        status="bridge_requires_revalidation",
    )

    recipe = register_tool_recipe(
        ws,
        recipe_id="shared-inverse-size-fit-v1",
        tool_family="python",
        tool_name="fit_inverse_size",
        purpose="Fit one bounded observable against 1/L.",
        required_inputs=["sizes", "values", "observable definition"],
        expected_outputs=["intercept", "fit residual"],
        invariants=["target topic validates its own correction model"],
    )
    source_run = record_tool_run(
        ws,
        recipe_id=recipe.recipe_id,
        tool_family="python",
        tool_name="fit_inverse_size",
        topic_id=source_topic,
        claim_id=source_claim.claim_id,
        inputs={"dataset": "source-benchmark"},
        outputs={"intercept": 1.0, "rmse": 1e-10},
        scientific_run_id="source-fit",
        lane="final",
        evidence_status="supports",
    )
    target_run = record_tool_run(
        ws,
        recipe_id=recipe.recipe_id,
        tool_family="python",
        tool_name="fit_inverse_size",
        topic_id=target_topic,
        claim_id=target_claim.claim_id,
        inputs={"dataset": "target-spin-chain", "candidate_exponent": 1.0},
        outputs={"intercept": 0.2, "rmse": 0.03},
        scientific_run_id="target-fit",
        lane="diagnostic",
        evidence_status="inconclusive",
        source_refs=[f"object_relation:{bridge.relation_id}"],
    )
    target_contract = create_validation_contract(
        ws,
        topic_id=target_topic,
        claim_id=target_claim.claim_id,
        required_checks=["compare competing correction exponents", "residual below target tolerance"],
        failure_modes=["wrong correction exponent"],
        required_evidence_outputs=["model comparison", "target residual"],
        tool_recipe_ids=[recipe.recipe_id],
    )
    target_validation = record_validation_result(
        ws,
        topic_id=target_topic,
        claim_id=target_claim.claim_id,
        contract_id=target_contract.contract_id,
        tool_run_id=target_run.run_id,
        status="inconclusive",
        checked_outputs=["target residual"],
        covered_failure_modes=[],
        summary="Target-side validation remains open; source trust is not reused.",
    )

    normal = compile_research_context(
        ws,
        ContextRequest(
            session_id="session-multi-topic-target",
            objective_text="Reuse the finite-size workflow for the target spin chain with explicit boundaries.",
            candidate_limit=20,
        ),
    )
    normal_refs = set(normal.record_refs)
    assert f"object_relation:{bridge.relation_id}" in normal_refs
    assert f"tool_run:{target_run.run_id}" in normal_refs
    assert f"validation_result:{target_validation.result_id}" in normal_refs
    assert f"tool_run:{source_run.run_id}" not in normal_refs
    assert f"exploratory_record:{source_insight.record_id}" not in normal_refs

    expanded = compile_research_context(
        ws,
        ContextRequest(
            session_id="session-multi-topic-target",
            objective_text="Inspect the exact source method note referenced by the target bridge.",
            exact_refs=(f"source_asset:{source_asset.asset_id}",),
            candidate_limit=20,
        ),
    )
    assert f"source_asset:{source_asset.asset_id}" in expanded.record_refs
    assert bridge.metadata["requires_target_revalidation"] is True
    assert bridge.metadata["can_transfer_claim_trust"] is False
    assert get_claim(ws, source_claim.claim_id).confidence_state == "validated"
    assert get_claim(ws, target_claim.claim_id).confidence_state == "hypothesis"

    with pytest.raises(ValueError, match="same topic and claim"):
        record_tool_run(
            ws,
            recipe_id=recipe.recipe_id,
            tool_family="python",
            tool_name="fit_inverse_size",
            topic_id=target_topic,
            claim_id=target_claim.claim_id,
            inputs={"dataset": "illegal-cross-topic-successor"},
            scientific_run_id="source-fit",
            supersedes=source_run.run_id,
            lane="diagnostic",
        )

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
