from __future__ import annotations


def test_final_lane_allowlist_and_forbidden_root_are_fail_closed():
    from brain.v5.lane_contracts import assess_run_lane
    from brain.v5.models import LaneContractRecord, ToolRunRecord

    contract = LaneContractRecord(
        contract_id="lane-1",
        topic_id="compute",
        campaign="benchmark",
        forbidden_roots=["/scratch/untrusted"],
        final_allowlist=["production-grid"],
    )
    base = ToolRunRecord(
        run_id="run-1",
        recipe_id="recipe-1",
        tool_family="hpc_slurm",
        tool_name="solver",
        topic_id="compute",
        claim_id="claim-1",
        lane="final",
        cwd="/scratch/clean/run-1",
        actual_parameters={"lane_key": "production-grid"},
    )

    allowed = assess_run_lane(base, contract)
    missing_key = assess_run_lane(
        ToolRunRecord(**{**base.__dict__, "actual_parameters": {}}),
        contract,
    )
    forbidden = assess_run_lane(
        ToolRunRecord(**{**base.__dict__, "cwd": "/scratch/untrusted/run-1"}),
        contract,
    )
    diagnostic = assess_run_lane(
        ToolRunRecord(**{**base.__dict__, "lane": "diagnostic"}),
        contract,
    )

    assert allowed.status == "final_eligible"
    assert missing_key.status == "blocked"
    assert "not in the final allowlist" in missing_key.reasons[0]
    assert forbidden.status == "blocked"
    assert "forbidden root" in forbidden.reasons[0]
    assert diagnostic.status == "diagnostic_only"
    assert diagnostic.can_update_claim_trust is False
