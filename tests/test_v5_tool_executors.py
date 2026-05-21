from __future__ import annotations


def test_safe_scalar_tolerance_executor_records_tool_run(tmp_path):
    from brain.v5.tool_executors import execute_registered_tool
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The Si GW benchmark is within tolerance.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="benchmark tolerance",
    )

    run = execute_registered_tool(
        ws,
        executor_id="scalar_tolerance_check",
        recipe_id="recipe-librpa-si-gap",
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        inputs={"observed": 1.24, "expected": 1.23, "tolerance": 0.02, "quantity": "gap_ev"},
        code_state_ids=["code-state-librpa-clean"],
        source_refs=["benchmark:si-reference"],
    )

    assert run.tool_name == "scalar_tolerance_check"
    assert run.outputs["within_tolerance"] is True
    assert run.outputs["absolute_error"] == 0.01
    assert run.outputs["quantity"] == "gap_ev"
    assert run.environment["executor_id"] == "scalar_tolerance_check"
    assert run.environment["execution_mode"] == "safe_builtin"
    assert run.evidence_status == "supports"
    assert run.code_state_ids == ["code-state-librpa-clean"]
    assert (ws.registry_dir("tool_runs") / f"{run.run_id}.md").exists()


def test_cli_tool_execute_returns_valid_tool_run_record(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The finite-size counting difference is zero.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size drift",
    )

    assert main(
        [
            "--base",
            str(tmp_path),
            "tool",
            "execute",
            "scalar_tolerance_check",
            "--recipe",
            "recipe-counting-check",
            "--topic",
            "fqhe",
            "--claim",
            claim.claim_id,
            "--inputs-json",
            '{"observed":6,"expected":6,"tolerance":0,"quantity":"edge_count"}',
            "--artifact-id",
            "artifact-counting-table",
        ]
    ) == 0
    output = capsys.readouterr().out

    import json

    payload = json.loads(output)
    assert payload["ok"] is True
    assert payload["kind"] == "tool_run"
    assert payload["outputs"]["within_tolerance"] is True
    assert payload["artifact_ids"] == ["artifact-counting-table"]


def test_mcp_tool_execute_wrapper_returns_valid_tool_run_record(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_execute_tool
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "toy", context_id="model-checks", title="Toy Numerics")
    claim = create_claim(
        ws,
        topic_id="toy",
        statement="The toy model energy is reproduced.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="normalization convention",
    )

    payload = aitp_v5_execute_tool(
        str(tmp_path),
        executor_id="scalar_tolerance_check",
        recipe_id="recipe-energy-check",
        topic_id="toy",
        claim_id=claim.claim_id,
        inputs={"observed": -1.0, "expected": -1.0, "tolerance": 0.0},
    )

    assert payload["ok"] is True
    assert payload["kind"] == "tool_run"
    assert payload["outputs"]["absolute_error"] == 0.0
    assert payload["evidence_status"] == "supports"


def test_tool_execute_can_record_evidence_and_update_brief_coverage(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.tool_executors import execute_registered_tool_result
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The counting table matches the expected edge sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifact",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)

    result = execute_registered_tool_result(
        ws,
        executor_id="scalar_tolerance_check",
        recipe_id="recipe-counting-check",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        inputs={"observed": 6, "expected": 6, "tolerance": 0, "quantity": "edge_count"},
        supports_outputs=["evidence_or_provenance", "minimal_check"],
        evidence_type="toy_numeric",
        evidence_summary="The edge counting table matches within tolerance.",
    )

    assert result.evidence is not None
    assert result.evidence.tool_run_ids == [result.run.run_id]
    assert result.evidence.supports_outputs == ["evidence_or_provenance", "minimal_check"]

    brief = build_execution_brief(ws, "s1")
    assert "evidence_or_provenance" in brief["evidence_coverage"]["satisfied_outputs"]
    assert "minimal_check" in brief["evidence_coverage"]["satisfied_outputs"]


def test_cli_tool_execute_can_return_evidence_id(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The finite-size counting difference is zero.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size drift",
    )

    assert main(
        [
            "--base",
            str(tmp_path),
            "tool",
            "execute",
            "scalar_tolerance_check",
            "--recipe",
            "recipe-counting-check",
            "--topic",
            "fqhe",
            "--claim",
            claim.claim_id,
            "--inputs-json",
            '{"observed":6,"expected":6,"tolerance":0,"quantity":"edge_count"}',
            "--supports-output",
            "minimal_check",
            "--evidence-type",
            "toy_numeric",
            "--evidence-summary",
            "The counting check matches exactly.",
        ]
    ) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["kind"] == "tool_run"
    assert payload["evidence_id"].startswith("evidence-fqhe-")


def test_mcp_tool_execute_can_return_evidence_record(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_execute_tool
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "toy", context_id="model-checks", title="Toy Numerics")
    claim = create_claim(
        ws,
        topic_id="toy",
        statement="The toy model energy is reproduced.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="normalization convention",
    )

    payload = aitp_v5_execute_tool(
        str(tmp_path),
        executor_id="scalar_tolerance_check",
        recipe_id="recipe-energy-check",
        topic_id="toy",
        claim_id=claim.claim_id,
        inputs={"observed": -1.0, "expected": -1.0, "tolerance": 0.0},
        supports_outputs=["minimal_check"],
        evidence_type="toy_numeric",
        evidence_summary="The toy-model energy check passed.",
    )

    assert payload["evidence"]["supports_outputs"] == ["minimal_check"]
    assert payload["evidence"]["tool_run_ids"] == [payload["run_id"]]


def test_metric_table_executor_records_multi_metric_evidence_coverage(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.tool_executors import execute_registered_tool_result
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The edge-sector counting table matches the expected sequence.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifact may mimic counting",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)

    result = execute_registered_tool_result(
        ws,
        executor_id="metric_table_check",
        recipe_id="recipe-fqhe-counting-table",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        inputs={
            "table_id": "fqhe-edge-counting",
            "metrics": [
                {"name": "L10_edge_count", "observed": 6, "expected": 6, "tolerance": 0},
                {"name": "L12_edge_count", "observed": 10, "expected": 10, "tolerance": 0},
            ],
        },
        supports_outputs=["evidence_or_provenance", "minimal_check"],
        evidence_type="toy_numeric",
        evidence_summary="The FQHE edge-counting table matches the expected sequence.",
    )

    assert result.run.tool_name == "metric_table_check"
    assert result.run.evidence_status == "supports"
    assert result.run.outputs["all_within_tolerance"] is True
    assert result.run.outputs["metric_count"] == 2
    assert result.run.outputs["failed_metrics"] == []
    assert result.run.outputs["metrics"][0]["absolute_error"] == 0.0
    assert result.evidence is not None
    assert result.evidence.tool_run_ids == [result.run.run_id]

    brief = build_execution_brief(ws, "s1")
    assert "evidence_or_provenance" in brief["evidence_coverage"]["satisfied_outputs"]
    assert "minimal_check" in brief["evidence_coverage"]["satisfied_outputs"]


def test_cli_metric_table_executor_reports_failed_metrics(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The GW benchmark table is reproduced.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="benchmark window",
    )

    assert main(
        [
            "--base",
            str(tmp_path),
            "tool",
            "execute",
            "metric_table_check",
            "--recipe",
            "recipe-librpa-gw-table",
            "--topic",
            "librpa-gw",
            "--claim",
            claim.claim_id,
            "--inputs-json",
            (
                '{"table_id":"si-gw",'
                '"metrics":['
                '{"name":"gap_ev","observed":1.31,"expected":1.23,"tolerance":0.02},'
                '{"name":"sigma_norm","observed":0.5,"expected":0.5,"tolerance":0.0}'
                ']}'
            ),
        ]
    ) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["kind"] == "tool_run"
    assert payload["evidence_status"] == "refutes"
    assert payload["outputs"]["all_within_tolerance"] is False
    assert payload["outputs"]["failed_metrics"] == ["gap_ev"]
    assert payload["outputs"]["passed_count"] == 1


def test_tool_executor_catalog_exposes_input_contracts():
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.tool_executors import describe_tool_executors

    catalog = describe_tool_executors()
    executors = {executor["executor_id"]: executor for executor in catalog["executors"]}

    assert require_valid_public_surface("tool_executor_catalog", catalog) == catalog
    assert catalog["kind"] == "tool_executor_catalog"
    assert catalog["truth_source"] == "builtin_executor_registry"
    assert catalog["summary_inputs_trusted"] is False
    assert set(executors) == {
        "checklist_consistency_check",
        "failure_mode_basis_check",
        "metric_table_check",
        "scalar_tolerance_check",
    }
    assert executors["checklist_consistency_check"]["input_schema"]["required"] == ["checks"]
    assert executors["failure_mode_basis_check"]["input_schema"]["required"] == ["failure_modes", "basis_items"]
    assert "code_method" in executors["failure_mode_basis_check"]["evidence_profiles"]
    assert "formal_theory" in executors["checklist_consistency_check"]["evidence_profiles"]
    assert executors["scalar_tolerance_check"]["input_schema"]["required"] == ["observed", "expected", "tolerance"]
    assert executors["metric_table_check"]["input_schema"]["required"] == ["metrics"]
    assert "toy_numeric" in executors["metric_table_check"]["evidence_profiles"]
    assert "code_method" in executors["metric_table_check"]["evidence_profiles"]


def test_cli_tool_executors_returns_catalog(tmp_path, capsys):
    import json

    from brain.v5.cli import main

    assert main(["--base", str(tmp_path), "tool", "executors"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["kind"] == "tool_executor_catalog"
    assert {executor["executor_id"] for executor in payload["executors"]} == {
        "checklist_consistency_check",
        "failure_mode_basis_check",
        "metric_table_check",
        "scalar_tolerance_check",
    }


def test_mcp_tool_executor_catalog_returns_valid_surface():
    from brain.v5.mcp_tools import aitp_v5_list_tool_executors
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = aitp_v5_list_tool_executors()

    assert payload["ok"] is True
    assert require_valid_public_surface("tool_executor_catalog", payload) == payload


def test_failure_mode_basis_executor_checks_each_mode_has_review_basis(tmp_path):
    from brain.v5.tool_executors import execute_registered_tool_result
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The self-energy code path reproduces the GW benchmark.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="formula-code translation",
        strongest_failure_mode="frequency grid mismatch",
    )

    result = execute_registered_tool_result(
        ws,
        executor_id="failure_mode_basis_check",
        recipe_id="recipe-librpa-gw-failure-mode-review-basis",
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        inputs={
            "failure_modes": ["frequency grid mismatch", "basis cutoff mismatch"],
            "basis_items": [
                {
                    "failure_mode": "frequency grid mismatch",
                    "basis_ref": "validation:freq-grid-scan",
                    "basis_type": "validation_result",
                    "question_answered": "Changing grid density does not move the benchmark outside tolerance.",
                }
            ],
        },
        supports_outputs=["failure_mode_review_basis"],
        evidence_type="code_method",
        evidence_summary="Failure-mode review basis was checked against GW diagnostics.",
    )

    assert result.run.evidence_status == "refutes"
    assert result.run.outputs["all_failure_modes_covered"] is False
    assert result.run.outputs["covered_failure_modes"] == ["frequency grid mismatch"]
    assert result.run.outputs["uncovered_failure_modes"] == ["basis cutoff mismatch"]
    assert result.evidence is not None
    assert result.evidence.supports_outputs == ["failure_mode_review_basis"]
