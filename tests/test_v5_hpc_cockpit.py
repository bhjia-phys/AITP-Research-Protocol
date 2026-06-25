"""Tests for the AITP v5 HPC cockpit surface (tool_run-based, lane-contract-aware).

This replaces the earlier parallel-family design. HPC job state lives in
``tool_run`` records; these tests cover attempt chains (supersedes /
superseded_by + scientific_run_id), lane contracts, the orientation-only
cockpit aggregation, and the code_state / artifact back-link helpers.
"""

from __future__ import annotations

from pathlib import Path


def _setup_workspace(tmp_path: Path):
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "si8-gw", context_id="librpa", title="Si8 G0W0 dataset")
    claim = create_claim(
        ws,
        topic_id="si8-gw",
        statement="Si8 G0W0 eigenvalues form a dataset entry per structure.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="Dataset generation not complete.",
    )
    return ws, claim


def test_tool_run_supersedes_backfills_chain(tmp_path):
    from brain.v5.models import ToolRunRecord
    from brain.v5.store import read_record
    from brain.v5.tools import record_tool_run

    ws, claim = _setup_workspace(tmp_path)
    j1 = record_tool_run(
        ws, recipe_id="gw-submit-v1", tool_family="hpc_workflow", tool_name="sbatch",
        topic_id="si8-gw", claim_id=claim.claim_id,
        inputs={"remote_dir": "/scratch/r1"}, outputs={"slurm_job_id": "100"},
        evidence_status="submitted_pending", scientific_run_id="run-A", lane="diagnostic",
    )
    j2 = record_tool_run(
        ws, recipe_id="gw-submit-v2", tool_family="hpc_workflow", tool_name="sbatch",
        topic_id="si8-gw", claim_id=claim.claim_id,
        inputs={"remote_dir": "/scratch/r2"}, outputs={"slurm_job_id": "101"},
        evidence_status="running", supersedes=j1.run_id, lane="diagnostic",
    )
    reloaded = read_record(ws.registry_dir("tool_runs") / f"{j1.run_id}.md", ToolRunRecord)
    assert reloaded.superseded_by == j2.run_id
    assert j2.supersedes == j1.run_id
    # scientific_run_id is inherited from the superseded attempt when not given
    assert j2.scientific_run_id == "run-A"
    # default lane is diagnostic so an unmarked run can never be mistaken for final
    assert j2.lane == "diagnostic"


def test_lane_contract_record_and_effective(tmp_path):
    from brain.v5.lane_contracts import (
        get_effective_lane_contract,
        lane_contract_payload,
        record_lane_contract,
    )
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _setup_workspace(tmp_path)
    contract = record_lane_contract(
        ws, topic_id="si8-gw", campaign="archivefaithful", claim_id=claim.claim_id,
        forbidden_roots=["/data/home/bad/mgo-1135"],
        preferred_clean_roots=["/data/home/good/mgo-1210"],
        final_rules=["No noiter/unfinished/nonconverged as final."],
        trust_update_forbidden=True,
    )
    require_valid_public_surface("lane_contract_record", lane_contract_payload(contract))
    assert contract.forbidden_roots == ["/data/home/bad/mgo-1135"]
    assert contract.trust_update_forbidden is True
    assert get_effective_lane_contract(ws, "si8-gw").contract_id == contract.contract_id


def test_hpc_cockpit_aggregates_runs(tmp_path):
    from brain.v5.hpc_cockpit import build_hpc_cockpit
    from brain.v5.lane_contracts import record_lane_contract
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.tools import record_tool_run

    ws, claim = _setup_workspace(tmp_path)
    j1 = record_tool_run(
        ws, recipe_id="gw-submit-v1", tool_family="hpc_workflow", tool_name="sbatch",
        topic_id="si8-gw", claim_id=claim.claim_id, inputs={"remote_dir": "/r1"},
        outputs={"slurm_job_id": "200"}, evidence_status="submitted_pending",
        scientific_run_id="run-A", lane="diagnostic",
    )
    record_tool_run(
        ws, recipe_id="gw-submit-v2", tool_family="hpc_workflow", tool_name="sbatch",
        topic_id="si8-gw", claim_id=claim.claim_id, inputs={"remote_dir": "/r2"},
        outputs={"slurm_job_id": "201"}, evidence_status="running",
        scientific_run_id="run-A", supersedes=j1.run_id, lane="diagnostic",
    )
    record_tool_run(
        ws, recipe_id="gw-fail", tool_family="hpc_workflow", tool_name="sbatch",
        topic_id="si8-gw", claim_id=claim.claim_id, inputs={"remote_dir": "/r3"},
        outputs={"slurm_job_id": "202"}, evidence_status="failed_setup",
        scientific_run_id="run-B", lane="diagnostic",
    )
    record_lane_contract(
        ws, topic_id="si8-gw", campaign="archivefaithful",
        forbidden_roots=["/bad"], trust_update_forbidden=True,
    )

    cockpit = build_hpc_cockpit(ws, "si8-gw")
    require_valid_public_surface("hpc_cockpit", cockpit)
    active = [job["scheduler_job_id"] for job in cockpit["active_jobs"]]
    # j1 was superseded -> not current; j2 running -> active; j3 failed -> failure history
    assert "201" in active and "200" not in active
    assert any(fail["scheduler_job_id"] == "202" for fail in cockpit["failure_history"])
    assert cockpit["lane_counts"]["diagnostic"] == 2
    assert cockpit["lane_contract"]["forbidden_roots"] == ["/bad"]
    assert cockpit["conclusions_not_allowed"]  # active job + failure + diagnostic-only + trust forbidden
    assert cockpit["next_valid_actions"]
    assert "# HPC Cockpit" in cockpit["markdown"]


def test_link_helpers_fill_provenance(tmp_path):
    from brain.v5.hpc_cockpit import build_hpc_cockpit
    from brain.v5.tools import (
        link_artifact_to_run,
        link_code_state_to_run,
        record_tool_run,
    )

    ws, claim = _setup_workspace(tmp_path)
    j = record_tool_run(
        ws, recipe_id="r", tool_family="hpc_workflow", tool_name="sbatch",
        topic_id="si8-gw", claim_id=claim.claim_id, outputs={"slurm_job_id": "300"},
        evidence_status="completed", lane="diagnostic",
    )
    before = build_hpc_cockpit(ws, "si8-gw")
    assert before["provenance_gaps"]["missing_code_state_run_ids"] == [j.run_id]

    link_code_state_to_run(ws, run_id=j.run_id, code_state_id="code-state-librpa-abc")
    link_code_state_to_run(ws, run_id=j.run_id, code_state_id="code-state-librpa-abc")  # idempotent
    link_artifact_to_run(ws, run_id=j.run_id, artifact_id="source-asset-gw-xyz")

    after = build_hpc_cockpit(ws, "si8-gw")
    assert after["provenance_gaps"]["missing_code_state_run_ids"] == []
    assert after["provenance_gaps"]["missing_artifact_run_ids"] == []


def test_hpc_cockpit_mcp_surface(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_hpc_cockpit, aitp_v5_record_lane_contract
    from brain.v5.tools import record_tool_run

    ws, claim = _setup_workspace(tmp_path)
    record_tool_run(
        ws, recipe_id="r", tool_family="hpc_workflow", tool_name="sbatch",
        topic_id="si8-gw", claim_id=claim.claim_id, outputs={"slurm_job_id": "400"},
        evidence_status="running", lane="diagnostic",
    )
    aitp_v5_record_lane_contract(
        str(ws.root), topic_id="si8-gw", campaign="bench", final_allowlist=["c", "bp"],
    )
    cockpit = aitp_v5_hpc_cockpit(str(ws.root), topic_id="si8-gw")
    assert cockpit["kind"] == "hpc_cockpit"
    assert cockpit["active_jobs"]
    assert cockpit["lane_contract"]["final_allowlist"] == ["c", "bp"]
