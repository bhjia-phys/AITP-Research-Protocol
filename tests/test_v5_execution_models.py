from __future__ import annotations

from dataclasses import asdict


def test_execution_v1_shapes_remain_constructible_with_v2_defaults():
    from brain.v5.models import (
        ArtifactRecord,
        CodeStateRecord,
        HumanCheckpointRecord,
        MonitorSnapshotRecord,
        ToolRecipeRecord,
        ToolRunRecord,
        ValidationContractRecord,
        ValidationResultRecord,
    )

    recipe = ToolRecipeRecord(
        recipe_id="recipe-v1",
        tool_family="python",
        tool_name="check.py",
        purpose="Historical recipe",
    )
    run = ToolRunRecord(
        run_id="run-v1",
        recipe_id=recipe.recipe_id,
        tool_family="python",
        tool_name="check.py",
        topic_id="topic-v1",
        claim_id="claim-v1",
    )
    code = CodeStateRecord(
        code_state_id="code-v1",
        repo_id="repo",
        upstream_remote="origin",
        upstream_branch="main",
        upstream_commit="a" * 40,
        local_branch="main",
        worktree_path="/work/repo",
        dirty=False,
    )
    artifact = ArtifactRecord(
        artifact_id="artifact-v1",
        topic_id="topic-v1",
        claim_id="claim-v1",
        artifact_type="result",
        uri="file:///result.dat",
        summary="Historical result",
    )
    monitor = MonitorSnapshotRecord(
        snapshot_id="snapshot-v1",
        topic_id="topic-v1",
        claim_id="claim-v1",
        tool_run_id=run.run_id,
        run_dir="/run",
        job_id="42",
    )
    contract = ValidationContractRecord(
        contract_id="contract-v1",
        topic_id="topic-v1",
        claim_id="claim-v1",
    )
    result = ValidationResultRecord(
        result_id="result-v1",
        topic_id="topic-v1",
        claim_id="claim-v1",
        contract_id=contract.contract_id,
        tool_run_id=run.run_id,
        status="passed",
    )
    checkpoint = HumanCheckpointRecord(
        checkpoint_id="checkpoint-v1",
        topic_id="topic-v1",
        claim_id="claim-v1",
        reason="Historical review",
        requested_by="model",
    )

    assert recipe.recipe_version == "v1-compat"
    assert run.recorded_maturity == "diagnostic"
    assert run.maturity == "diagnostic"
    assert code.patch_manifest_ref == ""
    assert artifact.storage_mode == "reference_only"
    assert monitor.immutable is True
    assert contract.tool_recipe_refs == []
    assert result.contract_ref == ""
    assert checkpoint.action == ""


def test_execution_v2_shapes_preserve_structured_reproducibility_fields():
    from brain.v5.models import (
        ArtifactRecord,
        CodeStateRecord,
        HumanCheckpointRecord,
        ToolRecipeRecord,
        ToolRunRecord,
        ValidationResultRecord,
    )

    recipe = ToolRecipeRecord(
        recipe_id="recipe-v2",
        tool_family="hpc_slurm",
        tool_name="librpa",
        purpose="Pinned LibRPA run",
        recipe_version="2.0.0",
        command_template=["librpa", "--input", "{input}"],
        parameter_schema={"frequency_points": {"type": "integer", "minimum": 1}},
        parameter_roles={"frequency_points": "imaginary-frequency quadrature"},
        units={"energy_cutoff": "eV"},
        defaults={"frequency_points": 24},
        allowed_ranges={"frequency_points": [1, 256]},
        physical_meanings={"frequency_points": "resolution of W(iomega)"},
        input_roles={"STRU": "material structure"},
        output_roles={"qsgw.log": "execution transcript"},
        script_refs=["artifact:submit-script"],
        environment_requirements=["execution_environment:dongfang-gcc13"],
        failure_modes=["frequency grid mismatch"],
        stop_rules=["stop on non-zero exit"],
        validation_contract_refs=["validation_contract:headwing-check"],
        applicability_boundary="Si fixture at the pinned code state",
    )
    run = ToolRunRecord(
        run_id="run-v2",
        recipe_id=recipe.recipe_id,
        tool_family="hpc_slurm",
        tool_name="librpa",
        topic_id="librpa",
        claim_id="claim-librpa",
        argv=["librpa", "--input", "qsgw.in"],
        cwd="/scratch/run-42",
        actual_parameters={"frequency_points": 24},
        parameter_provenance={"frequency_points": "qsgw.in:12"},
        input_manifest=[{"role": "input", "artifact_ref": "artifact:qsgw-input"}],
        input_hashes={"qsgw.in": "b" * 64},
        script_hashes={"submit.slurm": "c" * 64},
        recipe_ref="tool_recipe:recipe-v2",
        code_state_ref="code_state:code-v2",
        environment_ref="execution_environment:dongfang-gcc13",
        executor_id="slurm-manifest-adapter",
        executor_version="1.0.0",
        executor_hash="d" * 64,
        scheduler={"kind": "slurm", "partition": "cpu"},
        job_id="42",
        exit_status={"code": 0, "state": "COMPLETED"},
        output_manifest=[{"role": "log", "artifact_ref": "artifact:qsgw-log"}],
        validation_result_refs=["validation_result:run-v2-check"],
        monitor_snapshot_refs=["monitor_snapshot:run-v2-1"],
        artifact_refs=["artifact:qsgw-log"],
        skill_usage_refs=["skill_usage:librpa-run"],
        recorded_maturity="reproducible_candidate",
        non_claims=["scheduler completion is not scientific validation"],
    )
    code = CodeStateRecord(
        code_state_id="code-v2",
        repo_id="librpa",
        upstream_remote="origin",
        upstream_branch="main",
        upstream_commit="e" * 40,
        local_branch="topic/headwing",
        worktree_path="/work/librpa",
        dirty=True,
        patch_manifest_ref="code_patch_manifest:patch-v2",
        patch_manifest_hash="f" * 64,
    )
    artifact = ArtifactRecord(
        artifact_id="artifact-v2",
        topic_id="librpa",
        claim_id="claim-librpa",
        artifact_type="result",
        uri="file:///result.dat",
        summary="Pinned result bytes",
        content_hash="1" * 64,
        hash_algorithm="sha256",
        storage_mode="local_sha256",
        artifact_blob_receipt_ref="artifact_blob_receipt:artifact-blob-sha256-x",
        artifact_blob_receipt_hash="2" * 64,
        role="validated_output",
        provenance_refs=["tool_run:run-v2"],
    )
    validation = ValidationResultRecord(
        result_id="validation-v2",
        topic_id="librpa",
        claim_id="claim-librpa",
        contract_id="headwing-check",
        tool_run_id="run-v2",
        status="passed",
        contract_ref="validation_contract:headwing-check",
        contract_hash="3" * 64,
        tool_run_ref="tool_run:run-v2",
        tool_run_hash="4" * 64,
        recipe_ref="tool_recipe:recipe-v2",
        recipe_hash="5" * 64,
        executor_id="metric-check",
        executor_version="1.0.0",
        executor_hash="6" * 64,
        output_manifest_hash="7" * 64,
        failure_contract_hash="8" * 64,
        checked_artifact_hashes={"artifact:qsgw-log": "1" * 64},
    )
    checkpoint = HumanCheckpointRecord(
        checkpoint_id="checkpoint-v2",
        topic_id="librpa",
        claim_id="claim-librpa",
        reason="Accept exact execution baseline",
        requested_by="model",
        action="accept_execution_baseline",
        subject_refs=[
            {
                "record_ref": "tool_run:run-v2",
                "content_hash": "4" * 64,
                "revision": 1,
            }
        ],
        request_hash="9" * 64,
        payload_hash="a" * 64,
        expires_at="2099-01-01T00:00:00+00:00",
        replay_policy="once",
        target_scope_refs=["topic:librpa", "claim:claim-librpa"],
        effect_policy="execution_maturity_only",
    )

    assert asdict(recipe)["command_template"] == ["librpa", "--input", "{input}"]
    assert run.maturity == "reproducible_candidate"
    assert run.superseded_by == ""
    assert code.patch_manifest_ref == "code_patch_manifest:patch-v2"
    assert artifact.storage_mode == "local_sha256"
    assert validation.checked_artifact_hashes["artifact:qsgw-log"] == "1" * 64
    assert checkpoint.effect_policy == "execution_maturity_only"


def test_m2_foundation_registers_only_families_with_writers_in_this_slice():
    from brain.v5.record_family_registry import record_family_specs

    specs = record_family_specs()
    expected = {
        "artifact_blob_receipts": ("artifact_blob_receipt", "ArtifactBlobReceiptRecord"),
        "checkpoint_application_receipts": (
            "checkpoint_application_receipt",
            "CheckpointApplicationReceiptRecord",
        ),
        "code_patch_manifests": ("code_patch_manifest", "CodePatchManifestRecord"),
        "scope_revalidation_decisions": (
            "scope_revalidation_decision",
            "ScopeRevalidationDecisionRecord",
        ),
    }

    for family, (record_kind, class_name) in expected.items():
        spec = specs[family]
        assert spec.record_kind == record_kind
        assert spec.record_class.__name__ == class_name
        assert spec.schema_version == "v2"
        assert spec.lifecycle_policy == "append_only"
        assert spec.trust_effect == "none"
        assert {"exact_ref", "inventory", "query_index", "context_compiler"} <= set(
            spec.participates_in
        )

    assert "execution_environments" not in specs
    assert "execution_baselines" not in specs


def test_schema_v1_execution_aliases_survive_repository_materialization(tmp_path):
    from brain.v5.markdown import write_md
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    write_md(
        ws.registry_dir("tool_runs") / "legacy-run.md",
        {
            "kind": "tool_run",
            "run_id": "legacy-run",
            "recipe_id": "legacy-recipe",
            "tool_family": "python",
            "tool_name": "legacy.py",
            "topic_id": "legacy-topic",
            "claim_id": "legacy-claim",
            "maturity": "accepted_baseline",
        },
        "# Legacy Tool Run\n",
    )
    write_md(
        ws.registry_dir("tool_recipes") / "legacy-recipe.md",
        {
            "kind": "tool_recipe",
            "recipe_id": "legacy-recipe",
            "tool_family": "python",
            "tool_name": "legacy.py",
            "purpose": "Legacy compatibility fixture",
            "validation_contract_ids": ["legacy-contract"],
        },
        "# Legacy Tool Recipe\n",
    )
    repository = RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="alias-read-test", host="pytest"),
    )

    run = repository.read("tool_run:legacy-run")
    recipe = repository.read("tool_recipe:legacy-recipe")

    assert run.status == "found"
    assert run.record.recorded_maturity == "accepted_baseline"
    assert run.record.maturity == "accepted_baseline"
    assert recipe.status == "found"
    assert recipe.record.validation_contract_ids == ["legacy-contract"]
    assert recipe.record.validation_contract_refs == []
