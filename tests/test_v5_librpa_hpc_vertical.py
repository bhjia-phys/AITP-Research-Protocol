from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path

import pytest


def test_librpa_hpc_vertical_routes_exercised_canonical_writes_through_repository(
    tmp_path,
    monkeypatch,
):
    from brain.v5.code import record_code_state
    from brain.v5.evidence import record_artifact_ref
    from brain.v5.failure_mode_review import request_failure_mode_review_checkpoint
    from brain.v5.markdown import read_md
    from brain.v5.pretool_policy import evaluate_context_pre_tool_policy
    from brain.v5.quiet_checkpoint import apply_quiet_checkpoint_batch
    from brain.v5.record_repository import RecordCollisionError, RecordRepository
    from brain.v5.recovery_session import recover_session_binding_for_read
    from brain.v5.research_state import register_source
    from brain.v5.source_assets import register_source_asset
    from brain.v5.tools import (
        link_artifact_to_run,
        link_code_state_to_run,
        record_tool_run,
        register_tool_recipe,
    )
    from brain.v5.validation import create_validation_contract, record_validation_result
    from brain.v5.workspace import bind_session, create_claim, create_topic, get_claim, init_workspace

    ws = init_workspace(tmp_path)
    topic_id = "qsgw-headwing-update-librpa"
    session_id = "session-librpa-hpc-vertical"
    create_topic(ws, topic_id, context_id="librpa", title="LibRPA headwing update")
    claim = create_claim(
        ws,
        topic_id=topic_id,
        statement="The recorded LibRPA branch reproduces the bounded Si QSGW headwing check.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="The final and diagnostic lanes still need explicit separation.",
        strongest_failure_mode="frequency grid mismatch",
    )
    bind_session(
        ws,
        session_id,
        topic_id=topic_id,
        context_id="librpa",
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

    recovered = recover_session_binding_for_read(ws, session_id)
    assert recovered.session.topic_id == topic_id
    assert recovered.session.active_claim == claim.claim_id

    source = register_source(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        uri="https://example.invalid/librpa/qsgw-headwing",
        label="Pinned LibRPA QSGW headwing method note",
        connector_id="manual",
        summary="Exact source pointer for the bounded workflow.",
    )
    code_state = record_code_state(
        ws,
        repo_id="librpa",
        upstream_remote="origin",
        upstream_branch="main",
        upstream_commit="0123456789abcdef",
        local_branch="topic/qsgw-headwing",
        worktree_path="/work/librpa-qsgw-headwing",
        dirty=False,
        build_config={"compiler": "gcc-13", "mpi": "openmpi-4.1"},
        runtime_environment={"cluster": "dongfang", "partition": "cpu"},
        linked_records={"topic_id": topic_id, "claim_id": claim.claim_id},
    )
    source_asset = register_source_asset(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        asset_type="code_snapshot",
        uri="git+https://example.invalid/librpa@0123456789abcdef",
        title="LibRPA source snapshot for the QSGW headwing run",
        version_anchor={"commit": "0123456789abcdef", "branch": "topic/qsgw-headwing"},
        code_state_ids=[code_state.code_state_id],
        reference_location_ids=[source.location_id],
        summary="Pinned code and method provenance for the bounded run.",
    )
    recipe = register_tool_recipe(
        ws,
        recipe_id="recipe-librpa-qsgw-headwing",
        tool_family="hpc_slurm",
        tool_name="librpa_qsgw",
        purpose="Run the bounded Si QSGW headwing validation workflow.",
        required_inputs=["STRU", "qsgw.in", "pinned code state"],
        expected_outputs=["qsgw.log", "headwing_metrics.json"],
        invariants=["diagnostic attempts must not be used as final evidence"],
    )
    artifact = record_artifact_ref(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        artifact_type="hpc_output",
        uri="ssh://dongfang/work/qsgw-headwing/headwing_metrics.json",
        summary="Pinned final-lane metric output from Slurm job 4243.",
        size_bytes=2048,
        metadata={"sha256": "a" * 64, "job_id": "4243", "lane": "final"},
    )
    contract = create_validation_contract(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        required_checks=["headwing metrics remain within the recorded tolerance"],
        failure_modes=["frequency grid mismatch"],
        required_evidence_outputs=["headwing_metrics_within_tolerance"],
        tool_recipe_ids=[recipe.recipe_id],
        executor_ids=["metric_table_check"],
    )
    failed_attempt = record_tool_run(
        ws,
        recipe_id=recipe.recipe_id,
        tool_family="hpc_slurm",
        tool_name="sbatch librpa_qsgw.slurm",
        topic_id=topic_id,
        claim_id=claim.claim_id,
        inputs={"command": "sbatch librpa_qsgw.slurm", "frequency_grid": 12},
        outputs={"job_id": "4242", "scheduler_state": "FAILED", "exit_code": 1},
        environment={"cluster": "dongfang", "partition": "cpu", "modules": ["gcc/13", "openmpi/4.1"]},
        evidence_status="contradicts",
        code_state_ids=[code_state.code_state_id],
        scientific_run_id="scientific-run-si-qsgw-headwing",
        lane="diagnostic",
    )
    final_attempt = record_tool_run(
        ws,
        recipe_id=recipe.recipe_id,
        tool_family="hpc_slurm",
        tool_name="sbatch librpa_qsgw.slurm",
        topic_id=topic_id,
        claim_id=claim.claim_id,
        inputs={"command": "sbatch librpa_qsgw.slurm", "frequency_grid": 24},
        outputs={"job_id": "4243", "scheduler_state": "COMPLETED", "exit_code": 0},
        environment={"cluster": "dongfang", "partition": "cpu", "modules": ["gcc/13", "openmpi/4.1"]},
        evidence_status="supports",
        source_refs=[f"reference_location:{source.location_id}", f"source_asset:{source_asset.asset_id}"],
        scientific_run_id="scientific-run-si-qsgw-headwing",
        supersedes=failed_attempt.run_id,
        lane="final",
    )
    final_attempt = link_code_state_to_run(
        ws,
        run_id=final_attempt.run_id,
        code_state_id=code_state.code_state_id,
    )
    final_attempt = link_artifact_to_run(
        ws,
        run_id=final_attempt.run_id,
        artifact_id=artifact.artifact_id,
    )
    validation = record_validation_result(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        contract_id=contract.contract_id,
        tool_run_id=final_attempt.run_id,
        status="passed",
        checked_outputs=["headwing_metrics_within_tolerance"],
        covered_failure_modes=["frequency grid mismatch"],
        artifact_ids=[artifact.artifact_id],
        summary="The final-lane metrics passed for the pinned commit and HPC environment.",
    )

    checkpoint = request_failure_mode_review_checkpoint(ws, claim_id=claim.claim_id)
    blocked_trust = evaluate_context_pre_tool_policy(
        ws,
        session_id=session_id,
        action="apply_promotion_packet",
        claim_id=claim.claim_id,
        risk_level="adversarial",
        human_checkpoint_id=checkpoint.checkpoint_id,
    )
    closeout = apply_quiet_checkpoint_batch(
        ws,
        session_id,
        summary="Closed the bounded LibRPA HPC validation burst without trust promotion.",
        inputs=["STRU", "qsgw.in", "commit 0123456789abcdef"],
        outputs=[artifact.uri],
        changed_files=["src/qsgw/headwing.cpp"],
        validation_commands=["python check_headwing_metrics.py headwing_metrics.json"],
        durable_observations=["The 24-point final lane passed; the 12-point diagnostic attempt failed."],
        claim_boundary={"cannot_say": ["No validation beyond the pinned Si input and commit."]},
        next_blockers=["Repeat on the second convergence fixture before any trust update."],
        source_refs=[f"reference_location:{source.location_id}", f"source_asset:{source_asset.asset_id}"],
    )

    reader = RecordRepository(ws, actor=_test_actor())
    failed_read = reader.read(f"tool_run:{failed_attempt.run_id}")
    final_read = reader.read(f"tool_run:{final_attempt.run_id}")
    assert failed_read.status == "found"
    assert failed_read.record.superseded_by == ""
    assert final_read.status == "found"
    assert final_read.record.supersedes_run_id == failed_attempt.run_id
    assert final_read.record.supersedes == failed_attempt.run_id

    checkpoint_frontmatter, _ = read_md(ws.registry_dir("checkpoints") / f"{checkpoint.checkpoint_id}.md")
    final_frontmatter, _ = read_md(ws.registry_dir("tool_runs") / f"{final_attempt.run_id}.md")
    assert checkpoint_frontmatter["revision"] == 1
    assert not (ws.root / "revisions" / "checkpoints" / checkpoint.checkpoint_id).exists()
    assert final_frontmatter["revision"] == 3
    assert len(list((ws.root / "revisions" / "tool_runs" / final_attempt.run_id).glob("*.md"))) == 2

    assert checkpoint.status == "open"
    assert blocked_trust["block"] is True
    assert "adversarial_trust_change_requires_human_checkpoint" in {
        item["policy_id"] for item in blocked_trust["policy_reasons"]
    }
    assert closeout["status"] == "recorded_without_trust_promotion"
    assert closeout["can_update_claim_trust"] is False
    assert get_claim(ws, claim.claim_id).confidence_state == "hypothesis"

    same_code_state = record_code_state(
        ws,
        repo_id="librpa",
        upstream_remote="origin",
        upstream_branch="main",
        upstream_commit="0123456789abcdef",
        local_branch="topic/qsgw-headwing",
        worktree_path="/work/librpa-qsgw-headwing",
        dirty=False,
        build_config={"compiler": "gcc-13", "mpi": "openmpi-4.1"},
        runtime_environment={"cluster": "dongfang", "partition": "cpu"},
        linked_records={"topic_id": topic_id, "claim_id": claim.claim_id},
    )
    assert same_code_state.code_state_id == code_state.code_state_id
    with pytest.raises(RecordCollisionError, match=code_state.code_state_id):
        record_code_state(
            ws,
            repo_id="librpa",
            upstream_remote="origin",
            upstream_branch="main",
            upstream_commit="0123456789abcdef",
            local_branch="topic/qsgw-headwing",
            worktree_path="/different/worktree",
            dirty=True,
            build_config={"compiler": "gcc-13", "mpi": "openmpi-4.1"},
            runtime_environment={"cluster": "dongfang", "partition": "cpu"},
            linked_records={"topic_id": topic_id, "claim_id": claim.claim_id},
        )

    expected_families = {
        "reference_locations",
        "source_assets",
        "code_states",
        "tool_recipes",
        "tool_runs",
        "artifacts",
        "validation_contracts",
        "validation_results",
        "checkpoints",
        "quiet_checkpoints",
    }
    counts = Counter(family for family, _ in repository_writes)
    assert set(counts) == expected_families
    assert counts["tool_runs"] == 4
    assert counts["checkpoints"] == 1
    assert counts["code_states"] == 2

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


def _test_actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="librpa_vertical_test_reader", host="pytest")


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


def test_source_asset_identity_is_reused_without_implicit_revision(tmp_path):
    from brain.v5.markdown import read_md
    from brain.v5.source_assets import register_source_asset
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    first = register_source_asset(
        ws,
        topic_id="librpa",
        claim_id="claim-librpa",
        asset_type="code_snapshot",
        uri="git+https://example.invalid/librpa@abc123",
        title="LibRPA snapshot",
        content_hash="a" * 64,
        hash_algorithm="sha256",
        summary="Initial registration.",
    )
    revised = register_source_asset(
        ws,
        topic_id="librpa",
        claim_id="claim-librpa",
        asset_type="code_snapshot",
        uri="git+https://example.invalid/librpa@abc123",
        title="LibRPA snapshot with reviewed label",
        content_hash="a" * 64,
        hash_algorithm="sha256",
        summary="Reviewed registration metadata.",
    )

    assert revised.asset_id == first.asset_id
    assert revised.title == first.title
    assert revised.summary == first.summary
    frontmatter, _ = read_md(ws.registry_dir("source_assets") / f"{first.asset_id}.md")
    assert frontmatter["revision"] == 1
    assert not (ws.root / "revisions" / "source_assets" / first.asset_id).exists()


def test_artifact_identity_is_reused_without_implicit_revision(tmp_path):
    from brain.v5.evidence import record_artifact_ref
    from brain.v5.markdown import read_md
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    first = record_artifact_ref(
        ws,
        topic_id="librpa",
        claim_id="claim-librpa",
        artifact_type="result_json",
        uri="ssh://cluster/run/result.json",
        summary="Pinned bounded result.",
        metadata={"sha256": "a" * 64},
    )
    reused = record_artifact_ref(
        ws,
        topic_id="librpa",
        claim_id="claim-librpa",
        artifact_type="result_json",
        uri="ssh://cluster/run/result.json",
        summary="A later generic attachment label.",
        metadata={"sha256": "a" * 64, "note": "must not overwrite"},
    )

    assert reused.artifact_id == first.artifact_id
    assert reused.summary == first.summary
    frontmatter, _ = read_md(ws.registry_dir("artifacts") / f"{first.artifact_id}.md")
    assert frontmatter["revision"] == 1
    assert "note" not in frontmatter["metadata"]


def test_artifact_identity_is_concurrently_idempotent(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from brain.v5.evidence import record_artifact_ref
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    barrier = Barrier(2)

    def record(label):
        barrier.wait()
        return record_artifact_ref(
            ws,
            topic_id="librpa",
            claim_id="claim-librpa",
            artifact_type="result_json",
            uri="ssh://cluster/run/concurrent-result.json",
            summary=label,
            size_bytes=1024,
            metadata={"sha256": "b" * 64, "label": label},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(record, "first label"), pool.submit(record, "second label")]
        records = [future.result() for future in futures]

    assert records[0].artifact_id == records[1].artifact_id


@pytest.mark.parametrize(
    ("first_size", "first_hash", "second_size", "second_hash", "conflict_field"),
    [
        (128, "a" * 64, 128, "b" * 64, "sha256"),
        (128, "a" * 64, 256, "a" * 64, "size_bytes"),
    ],
)
def test_artifact_identity_rejects_conflicting_immutable_observations(
    tmp_path,
    first_size,
    first_hash,
    second_size,
    second_hash,
    conflict_field,
):
    from brain.v5.evidence import record_artifact_ref
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    record_artifact_ref(
        ws,
        topic_id="librpa",
        claim_id="claim-librpa",
        artifact_type="result_json",
        uri="ssh://cluster/run/result.json",
        summary="Pinned bounded result.",
        size_bytes=first_size,
        metadata={"sha256": first_hash},
    )

    with pytest.raises(ValueError, match=conflict_field):
        record_artifact_ref(
            ws,
            topic_id="librpa",
            claim_id="claim-librpa",
            artifact_type="result_json",
            uri="ssh://cluster/run/result.json",
            summary="Conflicting observation of the same artifact identity.",
            size_bytes=second_size,
            metadata={"sha256": second_hash},
        )


def test_distinct_validation_reports_get_distinct_immutable_ids(tmp_path):
    from brain.v5.tools import record_tool_run, register_tool_recipe
    from brain.v5.validation import create_validation_contract, record_validation_result
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa", context_id="gw", title="LibRPA")
    claim = create_claim(
        ws,
        topic_id="librpa",
        statement="The benchmark is bounded to one pinned input.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="cross-input behavior is open",
    )
    recipe = register_tool_recipe(
        ws,
        recipe_id="recipe-librpa-validation-id",
        tool_family="python",
        tool_name="check_metrics",
        purpose="Check one pinned metric table.",
    )
    run = record_tool_run(
        ws,
        recipe_id=recipe.recipe_id,
        tool_family="python",
        tool_name="check_metrics",
        topic_id="librpa",
        claim_id=claim.claim_id,
        outputs={"status": "passed"},
    )
    contract = create_validation_contract(
        ws,
        topic_id="librpa",
        claim_id=claim.claim_id,
        required_evidence_outputs=["metric_table"],
    )
    first = record_validation_result(
        ws,
        topic_id="librpa",
        claim_id=claim.claim_id,
        contract_id=contract.contract_id,
        tool_run_id=run.run_id,
        status="passed",
        checked_outputs=["metric_table"],
        summary="CLI validation interpretation.",
    )
    second = record_validation_result(
        ws,
        topic_id="librpa",
        claim_id=claim.claim_id,
        contract_id=contract.contract_id,
        tool_run_id=run.run_id,
        status="passed",
        checked_outputs=["metric_table"],
        summary="MCP validation interpretation.",
    )

    assert second.result_id != first.result_id
    assert len(list(ws.registry_dir("validation_results").glob("*.md"))) == 2
