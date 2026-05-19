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
