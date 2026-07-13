from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


def test_new_research_utility_onboards_from_execution_to_reviewed_skill_candidate(
    tmp_path,
    monkeypatch,
):
    from brain.v5.code import record_code_state
    from brain.v5.evidence import record_artifact_ref
    from brain.v5.checkpoints import decide_human_checkpoint
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository
    from brain.v5 import mcp_tools
    from brain.v5.skill_distillation import (
        build_procedural_skill_candidates,
        propose_detected_procedural_skill,
    )
    from brain.v5.source_assets import register_source_asset
    from brain.v5.tools import (
        capture_tool_run_from_local_path,
        link_artifact_to_run,
        link_code_state_to_run,
        register_tool_recipe,
    )
    from brain.v5.validation import create_validation_contract, record_validation_result
    from brain.v5.workspace import create_claim, create_topic, get_claim, init_workspace

    ws = init_workspace(tmp_path / "workspace")
    topic_id = "new-finite-size-utility"
    create_topic(ws, topic_id, context_id="numerics", title="Finite-size utility onboarding")
    claim = create_claim(
        ws,
        topic_id=topic_id,
        statement="The disposable utility reproduces the pinned inverse-size fit.",
        evidence_profile="numerical",
        confidence_state="hypothesis",
        active_uncertainty="The workflow is validated only for the pinned JSON schema and dataset.",
    )
    assert list(ws.registry_dir("tool_recipes").glob("*.md")) == []
    assert list(ws.registry_dir("skill_patch_proposals").glob("*.md")) == []
    canonical_before = _canonical_snapshot(ws)
    repository_writes = []
    original_write = RecordRepository.write

    def tracked_write(self, family, record, *, body="", policy=None):
        result = original_write(self, family, record, body=body, policy=policy)
        repository_writes.append((family, result))
        return result

    monkeypatch.setattr(RecordRepository, "write", tracked_write)

    utility = (
        Path(__file__).parent
        / "fixtures"
        / "v5_e2e"
        / "new_software"
        / "finite_size_fit.py"
    ).resolve()
    utility_hash = _sha256(utility)
    input_path = tmp_path / "fit_input.json"
    output_path = tmp_path / "fit_output.json"
    input_path.write_text(
        json.dumps(
            {
                "sizes": [8.0, 12.0, 16.0, 24.0],
                "values": [1.25, 1.1666666667, 1.125, 1.0833333333],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [sys.executable, str(utility), str(input_path), str(output_path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    metrics = json.loads(output_path.read_text(encoding="utf-8"))
    assert abs(metrics["intercept"] - 1.0) < 1e-9
    assert metrics["rmse"] < 1e-9

    source = register_source_asset(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        asset_type="code_snapshot",
        uri=utility.as_uri(),
        title="Disposable inverse-size fitting utility",
        content_hash=utility_hash,
        hash_algorithm="sha256",
        version_anchor={"sha256": utility_hash, "python": sys.version.split()[0]},
        summary="Exact utility source used by the onboarding run.",
    )
    code_state = record_code_state(
        ws,
        repo_id="aitp-new-software-fixture",
        upstream_remote="local-fixture",
        upstream_branch="main",
        upstream_commit=utility_hash,
        local_branch="disposable-run",
        worktree_path=str(utility.parent),
        dirty=False,
        runtime_environment={"python": sys.version.split()[0], "platform": sys.platform},
        linked_records={"topic_id": topic_id, "claim_id": claim.claim_id},
    )
    recipe = register_tool_recipe(
        ws,
        recipe_id="finite-size-fit-json-v1",
        tool_family="local_research_cli",
        tool_name="finite_size_fit.py",
        purpose="Fit y(L)=intercept+slope/L from a pinned JSON dataset.",
        required_inputs=["JSON sizes", "JSON values", "utility SHA-256"],
        expected_outputs=["JSON intercept", "JSON slope", "JSON RMSE"],
        invariants=["at least three positive distinct sizes", "exact utility hash"],
    )
    run = capture_tool_run_from_local_path(
        ws,
        path=str(output_path),
        recipe_id=recipe.recipe_id,
        tool_family="local_research_cli",
        tool_name="finite_size_fit.py",
        topic_id=topic_id,
        claim_id=claim.claim_id,
        inputs={
            "command": [sys.executable, str(utility), str(input_path), str(output_path)],
            "input_sha256": _sha256(input_path),
        },
        outputs=metrics,
        environment={"python": sys.version.split()[0], "utility_sha256": utility_hash},
        evidence_status="supports",
        source_refs=[f"source_asset:{source.asset_id}"],
        scientific_run_id="finite-size-fit-onboarding-1",
        lane="final",
    )
    artifact = record_artifact_ref(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        artifact_type="result_json",
        uri=output_path.as_uri(),
        summary="Pinned inverse-size fit output.",
        size_bytes=output_path.stat().st_size,
        metadata={"sha256": _sha256(output_path), "utility_sha256": utility_hash},
    )
    run = link_code_state_to_run(ws, run_id=run.run_id, code_state_id=code_state.code_state_id)
    run = link_artifact_to_run(ws, run_id=run.run_id, artifact_id=artifact.artifact_id)
    contract = create_validation_contract(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        required_checks=["intercept equals 1 within 1e-9", "RMSE below 1e-9"],
        required_evidence_outputs=["intercept", "rmse"],
        tool_recipe_ids=[recipe.recipe_id],
        executor_ids=["scalar_tolerance_check"],
    )
    validation = record_validation_result(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        contract_id=contract.contract_id,
        tool_run_id=run.run_id,
        status="passed",
        checked_outputs=["intercept", "rmse"],
        artifact_ids=[artifact.artifact_id],
        summary="Pinned disposable utility run passed the bounded scalar checks.",
    )
    distillation = build_procedural_skill_candidates(ws, topic_id=topic_id)
    assert distillation["candidate_count"] == 1
    detected = distillation["candidates"][0]
    assert detected["candidate_kind"] == "procedural_skill_candidate"
    assert detected["eligible_for_proposal"] is True
    assert detected["maturity"] == "single_validated_workflow"
    assert "exploratory_record" in distillation["excluded_record_kinds"]
    candidate = propose_detected_procedural_skill(
        ws,
        topic_id=topic_id,
        candidate_id=detected["candidate_id"],
        skill_name="finite-size-json-fit",
        current_version="0.0.0",
        proposed_version="0.1.0",
    )

    assert candidate.topic_ids == [topic_id]
    assert candidate.requires_human_review is True
    assert candidate.review_status == "draft"
    assert candidate.application_status == "not_applied"
    assert candidate.can_update_claim_trust is False
    mcp_candidate = mcp_tools.aitp_v5_propose_detected_procedural_skill(
        str(ws.base),
        topic_id=topic_id,
        candidate_id=detected["candidate_id"],
        skill_name="finite-size-json-fit",
    )
    assert mcp_candidate["proposal_id"] == candidate.proposal_id
    assert mcp_candidate["application_status"] == "not_applied"
    assert get_claim(ws, claim.claim_id).confidence_state == "hypothesis"
    assert not (ws.base / ".agents" / "skills" / candidate.skill_name).exists()

    with pytest.raises(ValueError, match="human checkpoint not found"):
        mcp_tools.aitp_v5_apply_project_skill(
            str(ws.base),
            proposal_id=candidate.proposal_id,
            checkpoint_id="checkpoint-missing",
        )
    checkpoint = mcp_tools.aitp_v5_request_skill_install_review(
        str(ws.base),
        proposal_id=candidate.proposal_id,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        requested_by="new-software-e2e",
    )
    with pytest.raises(ValueError, match="host-verified approve_install"):
        mcp_tools.aitp_v5_apply_project_skill(
            str(ws.base),
            proposal_id=candidate.proposal_id,
            checkpoint_id=checkpoint["checkpoint_id"],
        )
    decided = decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint["checkpoint_id"],
        decision="approve_install",
        rationale="Reviewed the exact workflow, provenance, boundaries, and generated SKILL.md.",
        decided_by="test-reviewer",
    )
    assert decided.decision_verified is True
    installed = mcp_tools.aitp_v5_apply_project_skill(
        str(ws.base),
        proposal_id=candidate.proposal_id,
        checkpoint_id=checkpoint["checkpoint_id"],
    )
    skill_path = Path(str(installed["skill_path"]))
    skill_text = skill_path.read_text(encoding="utf-8")
    assert skill_path == ws.base / ".agents" / "skills" / candidate.skill_name / "SKILL.md"
    assert "name: finite-size-json-fit" in skill_text
    assert "Use when Fit y(L)=intercept+slope/L" in skill_text
    assert f"tool_run:{run.run_id}" in skill_text
    assert "cannot update scientific claim trust" in skill_text

    proposal = RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="test-reader", host="pytest"),
    ).read(f"skill_patch_proposal:{candidate.proposal_id}").record
    assert proposal.review_status == "approved"
    assert proposal.application_status == "applied"
    assert proposal.review_checkpoint_id == checkpoint["checkpoint_id"]
    assert proposal.approved_content_hash
    assert get_claim(ws, claim.claim_id).confidence_state == "hypothesis"

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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def test_incomplete_workflow_reports_recording_gaps_instead_of_drafting_skill(tmp_path):
    from brain.v5.skill_distillation import (
        build_procedural_skill_candidates,
        propose_detected_procedural_skill,
    )
    from brain.v5.tools import record_tool_run, register_tool_recipe
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "incomplete-tool", context_id="numerics", title="Incomplete tool")
    claim = create_claim(
        ws,
        topic_id="incomplete-tool",
        statement="The new tool may be useful.",
        evidence_profile="numerical",
        confidence_state="hypothesis",
        active_uncertainty="No final validated run exists.",
    )
    recipe = register_tool_recipe(
        ws,
        recipe_id="incomplete-recipe",
        tool_family="python",
        tool_name="incomplete_tool",
        purpose="Explore one unvalidated calculation.",
    )
    record_tool_run(
        ws,
        recipe_id=recipe.recipe_id,
        tool_family="python",
        tool_name="incomplete_tool",
        topic_id="incomplete-tool",
        claim_id=claim.claim_id,
        lane="diagnostic",
    )

    report = build_procedural_skill_candidates(ws, topic_id="incomplete-tool")
    candidate = report["candidates"][0]
    assert candidate["eligible_for_proposal"] is False
    assert {
        "final_tool_run",
        "passed_validation_for_final_run",
        "artifact_provenance",
        "code_or_source_provenance",
        "applicability_or_failure_boundaries",
    }.issubset(candidate["missing_requirements"])
    assert report["trigger_policy"][2] == (
        "record missing requirements instead of drafting an incomplete skill"
    )
    with pytest.raises(ValueError, match="procedural skill candidate is incomplete"):
        propose_detected_procedural_skill(
            ws,
            topic_id="incomplete-tool",
            candidate_id=candidate["candidate_id"],
            skill_name="must-not-exist",
        )
    assert list(ws.registry_dir("skill_patch_proposals").glob("*.md")) == []
