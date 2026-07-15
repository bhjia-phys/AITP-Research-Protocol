from __future__ import annotations


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="execution-memory-test", host="pytest")


def test_execution_redaction_covers_keys_argv_uri_and_allowlist():
    from brain.v5.execution_contracts import RedactionPolicy, redact_execution_payload

    payload = {
        "environment": {
            "PATH": "/opt/librpa/bin",
            "OMP_NUM_THREADS": "32",
            "API_TOKEN": "token-secret",
            "UNREVIEWED_FLAG": "private-flag",
        },
        "argv": ["collector", "--credential", "argv-secret"],
        "remote_uri": "https://alice:uri-secret@cluster.invalid/run/42",
    }
    result = redact_execution_payload(
        payload,
        RedactionPolicy(
            environment_allowlist=("PATH", "OMP_NUM_THREADS", "API_TOKEN"),
            sensitive_argv_positions=(2,),
        ),
    )

    rendered = repr(result.payload)
    assert result.payload["environment"]["PATH"] == "/opt/librpa/bin"
    assert result.payload["environment"]["API_TOKEN"] == "[REDACTED]"
    assert "UNREVIEWED_FLAG" not in result.payload["environment"]
    assert result.payload["argv"][2] == "[REDACTED]"
    assert result.payload["remote_uri"] == "https://cluster.invalid/run/42"
    assert {"token-secret", "private-flag", "argv-secret", "uri-secret"}.isdisjoint(
        rendered
    )
    assert result.can_update_claim_trust is False


def test_execution_environment_writer_persists_only_redacted_exact_provenance(tmp_path):
    from brain.v5.execution_contracts import RedactionPolicy
    from brain.v5.execution_environments import record_execution_environment
    from brain.v5.models import ExecutionEnvironmentRecord
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa", context_id="theory", title="LibRPA")
    topic_ref = pin_current_record(ws, "topic:librpa")
    record = ExecutionEnvironmentRecord(
        environment_id="dongfang-gcc13-openmpi4",
        host="dongfang",
        operating_system="Rocky Linux 9",
        architecture="x86_64",
        compiler={"name": "gcc", "version": "13.2"},
        mpi={"name": "openmpi", "version": "4.1"},
        executable_paths={"librpa": "/opt/librpa/bin/librpa"},
        executable_hashes={"librpa": "a" * 64},
        redacted_environment={
            "PATH": "/opt/librpa/bin",
            "API_TOKEN": "must-not-persist",
            "UNREVIEWED": "also-private",
        },
        source_refs=[topic_ref],
        created_at="2026-07-15T00:00:00+00:00",
    )

    write = record_execution_environment(
        ws,
        record,
        actor=_actor(),
        redaction_policy=RedactionPolicy(
            environment_allowlist=("PATH", "API_TOKEN"),
        ),
    )
    stored = RecordRepository(ws, actor=_actor()).read(write.record_ref)
    markdown = (ws.registry_dir("execution_environments") / f"{record.environment_id}.md").read_text(
        encoding="utf-8"
    )

    assert write.record_ref == "execution_environment:dongfang-gcc13-openmpi4"
    assert stored.record.redacted_environment == {
        "API_TOKEN": "[REDACTED]",
        "PATH": "/opt/librpa/bin",
    }
    assert stored.record.source_refs == [
        {
            "record_ref": topic_ref.record_ref,
            "content_hash": topic_ref.content_hash,
            "revision": topic_ref.revision,
        }
    ]
    assert "must-not-persist" not in markdown
    assert "also-private" not in markdown


def test_execution_environment_writer_rejects_bare_sources_and_unhashed_executables(
    tmp_path,
):
    import pytest

    from brain.v5.execution_environments import record_execution_environment
    from brain.v5.models import ExecutionEnvironmentRecord
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    base = ExecutionEnvironmentRecord(
        environment_id="invalid-environment",
        host="cluster",
        operating_system="Linux",
        architecture="x86_64",
        executable_paths={"solver": "/opt/solver"},
        executable_hashes={"solver": "not-a-sha256"},
        source_refs=["topic:bare-ref"],
        created_at="2026-07-15T00:00:00+00:00",
    )

    with pytest.raises(ValueError, match="executable hash"):
        record_execution_environment(ws, base, actor=_actor())


def test_v2_recipe_and_reproducible_run_require_exact_core_dependencies_and_redact(
    tmp_path,
):
    from brain.v5.code import record_code_state
    from brain.v5.execution_contracts import RedactionPolicy
    from brain.v5.execution_environments import record_execution_environment
    from brain.v5.execution_writers import record_tool_recipe_v2, record_tool_run_v2
    from brain.v5.models import ExecutionEnvironmentRecord, ToolRecipeRecord, ToolRunRecord
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "compute", context_id="theory", title="Compute")
    claim = create_claim(
        ws,
        topic_id="compute",
        statement="The pinned run is reproducible.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="baseline not accepted",
    )
    code = record_code_state(
        ws,
        repo_id="solver",
        upstream_remote="origin",
        upstream_branch="main",
        upstream_commit="a" * 40,
        local_branch="main",
        worktree_path="/work/solver",
        dirty=False,
    )
    environment = ExecutionEnvironmentRecord(
        environment_id="solver-env",
        host="cluster",
        operating_system="Linux",
        architecture="x86_64",
        executable_paths={"solver": "/opt/solver"},
        executable_hashes={"solver": "b" * 64},
        created_at="2026-07-15T00:00:00+00:00",
    )
    record_execution_environment(ws, environment, actor=_actor())
    recipe = ToolRecipeRecord(
        recipe_id="solver-v2",
        tool_family="solver",
        tool_name="solver",
        purpose="Run the pinned solver.",
        recipe_version="2.0.0",
        parameter_schema={"steps": {"type": "integer"}},
        command_template=["solver", "--steps", "{steps}"],
    )
    record_tool_recipe_v2(ws, recipe, actor=_actor())
    recipe_ref = pin_current_record(ws, "tool_recipe:solver-v2")
    code_ref = pin_current_record(ws, f"code_state:{code.code_state_id}")
    environment_ref = pin_current_record(ws, "execution_environment:solver-env")
    run = ToolRunRecord(
        run_id="solver-run-v2",
        recipe_id=recipe.recipe_id,
        tool_family="solver",
        tool_name="solver",
        topic_id="compute",
        claim_id=claim.claim_id,
        argv=["solver", "--credential", "argv-secret"],
        environment={"PATH": "/opt/solver", "API_TOKEN": "env-secret"},
        recipe_ref=recipe_ref.record_ref,
        recipe_hash=recipe_ref.content_hash,
        recipe_revision=recipe_ref.revision,
        code_state_ref=code_ref.record_ref,
        code_state_hash=code_ref.content_hash,
        code_state_revision=code_ref.revision,
        environment_ref=environment_ref.record_ref,
        environment_hash=environment_ref.content_hash,
        environment_revision=environment_ref.revision,
        recorded_maturity="reproducible_candidate",
    )

    write = record_tool_run_v2(
        ws,
        run,
        actor=_actor(),
        redaction_policy=RedactionPolicy(
            environment_allowlist=("PATH", "API_TOKEN"),
            sensitive_argv_positions=(2,),
        ),
    )
    stored = RecordRepository(ws, actor=_actor()).read(write.record_ref).record

    assert stored.argv[2] == "[REDACTED]"
    assert stored.environment == {"API_TOKEN": "[REDACTED]", "PATH": "/opt/solver"}
    assert stored.recorded_maturity == "reproducible_candidate"
    assert "argv-secret" not in str(stored)
    assert "env-secret" not in str(stored)


def test_v2_run_rejects_accepted_baseline_and_bare_candidate_refs(tmp_path):
    import pytest

    from brain.v5.execution_writers import record_tool_run_v2
    from brain.v5.models import ToolRunRecord
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    base = ToolRunRecord(
        run_id="invalid-run",
        recipe_id="recipe",
        tool_family="solver",
        tool_name="solver",
        topic_id="topic",
        claim_id="claim",
        recorded_maturity="accepted_baseline",
    )
    with pytest.raises(ValueError, match="accepted_baseline"):
        record_tool_run_v2(ws, base, actor=_actor())
    with pytest.raises(ValueError, match="exact recipe"):
        record_tool_run_v2(
            ws,
            ToolRunRecord(**{**base.__dict__, "recorded_maturity": "reproducible_candidate"}),
            actor=_actor(),
        )


def test_v2_code_state_requires_exact_patch_for_dirty_worktree(tmp_path):
    import pytest

    from brain.v5.execution_writers import record_code_state_v2
    from brain.v5.models import CodeStateRecord
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    dirty = CodeStateRecord(
        code_state_id="dirty-code",
        repo_id="solver",
        upstream_remote="origin",
        upstream_branch="main",
        upstream_commit="a" * 40,
        local_branch="feature",
        worktree_path="/work/solver",
        dirty=True,
    )
    with pytest.raises(ValueError, match="exact patch manifest"):
        record_code_state_v2(ws, dirty, actor=_actor())
