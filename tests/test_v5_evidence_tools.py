from __future__ import annotations


def test_tool_run_records_inputs_outputs_environment_linked_claim_and_status(tmp_path):
    from brain.v5.tools import record_tool_run, register_tool_recipe
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The Si GW benchmark is reproduced by this run.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="benchmark tolerance",
    )
    recipe = register_tool_recipe(
        ws,
        recipe_id="recipe-librpa-si-gw",
        tool_family="domain",
        tool_name="librpa-gw-runner",
        purpose="Run a LibRPA Si GW benchmark.",
        required_inputs=["code_state_id", "input_deck", "benchmark_reference"],
        expected_outputs=["evidence_or_provenance", "benchmark_consistency"],
    )

    run = record_tool_run(
        ws,
        recipe_id=recipe.recipe_id,
        tool_family="domain",
        tool_name="librpa-gw-runner",
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        inputs={"input_deck": "Si-gw.in", "code_state_id": "code-state-librpa-clean"},
        outputs={"gap_ev": 1.23, "within_tolerance": True},
        environment={"host": "fisher", "mpi_ranks": 32},
        evidence_status="supports",
    )

    assert run.claim_id == claim.claim_id
    assert run.inputs["code_state_id"] == "code-state-librpa-clean"
    assert run.outputs["within_tolerance"] is True
    assert run.environment["host"] == "fisher"
    assert run.evidence_status == "supports"
    assert (ws.root / "registry" / "tool_runs" / f"{run.run_id}.md").exists()


def test_cli_and_mcp_capture_tool_run_auto_from_local_transcript(tmp_path, capsys):
    import hashlib

    from brain.v5.mcp_tools import aitp_v5_capture_tool_run_auto
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The Si GW benchmark is reproducible from this transcript.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="tool transcript identity not captured",
    )
    transcript = tmp_path / "si-gw-transcript.txt"
    transcript.write_text("pytest tests/test_si_gw.py\nPASSED gap=1.23\n", encoding="utf-8")
    expected_hash = hashlib.sha256(transcript.read_bytes()).hexdigest()

    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "tool",
            "run",
            "capture-auto",
            "--path",
            str(transcript),
            "--recipe",
            "recipe-librpa-si-gw",
            "--family",
            "code",
            "--name",
            "pytest",
            "--topic",
            "librpa-gw",
            "--claim",
            claim.claim_id,
            "--inputs-json",
            '{"test":"tests/test_si_gw.py"}',
            "--summary",
            "Local benchmark transcript.",
            "--max-preview-chars",
            "20",
        ],
        capsys,
    )
    mcp_payload = aitp_v5_capture_tool_run_auto(
        str(tmp_path),
        path=str(transcript),
        recipe_id="recipe-librpa-si-gw",
        tool_family="code",
        tool_name="pytest",
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        inputs={"test": "tests/test_si_gw.py"},
    )

    assert payload["ok"] is True
    assert payload["kind"] == "tool_run"
    assert payload["topic_id"] == "librpa-gw"
    assert payload["claim_id"] == claim.claim_id
    assert payload["inputs"]["test"] == "tests/test_si_gw.py"
    assert payload["outputs"]["transcript_sha256"] == expected_hash
    assert payload["outputs"]["transcript_hash_algorithm"] == "sha256"
    assert payload["outputs"]["transcript_size_bytes"] == transcript.stat().st_size
    assert payload["outputs"]["transcript_preview"] == "pytest tests/test_si"
    assert payload["outputs"]["transcript_preview_truncated"] is True
    assert payload["environment"]["capture_tool"] == "aitp_v5_capture_tool_run_auto"
    assert payload["environment"]["summary_inputs_trusted"] is False
    assert payload["environment"]["can_update_claim_trust"] is False
    assert payload["evidence_status"] == "unreviewed"
    assert mcp_payload["run_id"].startswith("tool-run-recipe-librpa-si-gw-")
    assert mcp_payload["outputs"]["transcript_sha256"] == expected_hash


def test_large_artifact_is_stored_by_reference_not_inline_frontmatter(tmp_path):
    from brain.v5.evidence import record_artifact_ref
    from brain.v5.markdown import read_md
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Exact diagonalization output supports the finite-size trend.",
        evidence_profile="toy_numeric",
        confidence_state="locally_checked",
        active_uncertainty="finite-size drift",
    )

    artifact = record_artifact_ref(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        artifact_type="ed-spectrum",
        uri="D:/runs/fqhe/ed-spectrum-L12.h5",
        summary="Large HDF5 spectrum output for L=12.",
        size_bytes=4_200_000_000,
        metadata={"sha256": "abc123"},
    )

    fm, body = read_md(ws.registry_dir("artifacts") / f"{artifact.artifact_id}.md")

    assert fm["uri"] == "D:/runs/fqhe/ed-spectrum-L12.h5"
    assert "raw_content" not in fm
    assert "Large HDF5" in body


def test_evidence_records_satisfy_action_budget_required_outputs(tmp_path):
    from brain.v5.evidence import record_evidence, required_output_coverage
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Finite-size counting identifies the edge sector.",
        evidence_profile="toy_numeric",
        confidence_state="locally_checked",
        active_uncertainty="minimal check coverage",
    )
    evidence = record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="toy_numeric",
        status="supports",
        summary="Finite-size comparison and provenance were recorded.",
        supports_outputs=["evidence_or_provenance", "minimal_check"],
        source_refs=["tool_run:run-ed-L10-L12"],
    )

    coverage = required_output_coverage(
        [evidence],
        required_outputs=["evidence_or_provenance", "failure_mode", "minimal_check"],
    )

    assert coverage.satisfied_outputs == ["evidence_or_provenance", "minimal_check"]
    assert coverage.missing_outputs == ["failure_mode"]


def test_code_method_tool_run_can_link_code_state_and_artifact(tmp_path):
    from brain.v5.evidence import record_artifact_ref
    from brain.v5.tools import record_tool_run
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The self-energy patch preserves the benchmark invariant.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="formula-code invariant",
    )
    artifact = record_artifact_ref(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        artifact_type="benchmark-log",
        uri="D:/runs/librpa/si-gw/log.txt",
        summary="Benchmark log.",
    )

    run = record_tool_run(
        ws,
        recipe_id="recipe-librpa-benchmark",
        tool_family="code",
        tool_name="pytest",
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        inputs={"test": "tests/test_si_gw.py"},
        outputs={"passed": True},
        environment={"python": "3.12"},
        evidence_status="supports",
        code_state_ids=["code-state-librpa-clean"],
        artifact_ids=[artifact.artifact_id],
    )

    assert run.code_state_ids == ["code-state-librpa-clean"]
    assert run.artifact_ids == [artifact.artifact_id]


def test_execution_brief_exposes_evidence_coverage_for_active_claim(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.evidence import record_evidence
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Finite-size counting identifies the edge sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifact may mimic counting",
    )
    record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="toy_numeric",
        status="supports",
        summary="A finite-size check with provenance exists.",
        supports_outputs=["evidence_or_provenance", "minimal_check"],
        source_refs=["tool_run:run-ed"],
    )
    bind_session(
        ws,
        "s1",
        topic_id="fqhe",
        context_id="topological-order",
        active_claim=claim.claim_id,
    )

    brief = build_execution_brief(ws, "s1")

    assert "evidence_coverage" in brief
    assert "evidence_or_provenance" in brief["evidence_coverage"]["satisfied_outputs"]
    assert "minimal_check" in brief["evidence_coverage"]["satisfied_outputs"]


def test_checklist_executor_records_formal_theory_evidence(tmp_path):
    from brain.v5.tool_executors import execute_registered_tool_result
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum Gravity")
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="The proposed constraint algebra closes under the bracket.",
        evidence_profile="formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="definition and hidden-assumption audit",
    )

    result = execute_registered_tool_result(
        ws,
        executor_id="checklist_consistency_check",
        recipe_id="recipe-formal-theory-checklist",
        topic_id="qg",
        claim_id=claim.claim_id,
        inputs={
            "checks": [
                {"name": "definition domain", "status": "checked", "note": "Domain of the bracket is explicit."},
                {"name": "counterexample search", "status": "checked", "note": "No small counterexample found."},
            ]
        },
        evidence_status="supports",
        supports_outputs=["evidence_or_provenance", "minimal_check"],
        evidence_type="formal_theory",
    )

    assert result.run.outputs["all_checked"] is True
    assert result.run.outputs["unchecked_items"] == []
    assert result.evidence is not None
    assert result.evidence.evidence_type == "formal_theory"
    assert result.evidence.status == "supports"


def _invoke(argv, capsys):
    from brain.v5.cli import main

    assert main(argv) == 0
    return __import__("json").loads(capsys.readouterr().out)
