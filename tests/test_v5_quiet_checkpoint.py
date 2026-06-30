from __future__ import annotations

import json


def _invoke(args, capsys):
    from brain.v5.cli import main

    assert main(args) == 0
    return json.loads(capsys.readouterr().out)


def test_quiet_checkpoint_preview_is_read_only_and_apply_writes_batch_refs(tmp_path):
    from brain.v5.quiet_checkpoint import apply_quiet_checkpoint_batch, preview_quiet_checkpoint_batch
    from brain.v5.recording_navigator import verify_recording_effect
    from brain.v5.workspace import bind_session, create_claim, create_topic, get_claim, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "quantum-chaos-long-range-spin-chains", context_id="spin-chains", title="HS hidden symmetry")
    claim = create_claim(
        ws,
        topic_id="quantum-chaos-long-range-spin-chains",
        statement="Sector-resolved statistics should wait for explicit sector authority and open proof gaps.",
        evidence_profile="semi_formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="sector convention and all-L proof remain open",
    )
    bind_session(
        ws,
        "s-hs-burst",
        topic_id="quantum-chaos-long-range-spin-chains",
        context_id="spin-chains",
        active_claim=claim.claim_id,
    )

    preview = preview_quiet_checkpoint_batch(
        ws,
        "s-hs-burst",
        summary="Alpha=2 sector burst produced finite certificates and a proof-gap note.",
        inputs=["alpha2 notebook", "finite certificate table"],
        outputs=["sector_gap_audit.md"],
        changed_files=["notebook/alpha2_sector_gap.md"],
        validation_commands=["python scripts/check_alpha2_sector_table.py --dry-run"],
        durable_observations=["Finite certificates are useful orientation but not an all-L proof."],
        claim_boundary={
            "cannot_say": ["No theorem-level all-L closure"],
            "non_claims": ["No final P(r) until statistics convention is fixed"],
        },
        next_blockers=["Record sector authority before final statistics."],
        artifact_specs=[
            {
                "uri": "results/alpha2_sector_gap.json",
                "artifact_type": "result_json",
                "summary": "Finite certificate summary.",
            }
        ],
        source_specs=[
            {
                "uri": "notebook://alpha2-sector-gap",
                "asset_type": "note",
                "title": "Alpha=2 sector gap notebook",
                "summary": "Burst notebook with convention notes.",
            }
        ],
        tool_run_specs=[
            {
                "recipe_id": "recipe-alpha2-check",
                "tool_family": "local_python",
                "tool_name": "check_alpha2_sector_table",
                "inputs": {"table": "alpha2"},
                "outputs": {"status": "dry_run"},
            }
        ],
        sensemaking_summary="The burst clarified the sector-convention boundary but did not close the proof.",
        source_refs=["source:hs-alpha-notebook"],
    )

    assert preview["kind"] == "quiet_checkpoint_preview"
    assert preview["can_update_kernel_state"] is False
    assert preview["can_update_claim_trust"] is False
    assert list(ws.registry_dir("quiet_checkpoints").glob("*.md")) == []

    batch = apply_quiet_checkpoint_batch(
        ws,
        "s-hs-burst",
        summary=preview["summary"],
        inputs=preview["inputs"],
        outputs=preview["outputs"],
        changed_files=preview["changed_files"],
        validation_commands=preview["validation_commands"],
        durable_observations=preview["durable_observations"],
        claim_boundary=preview["claim_boundary"],
        next_blockers=preview["next_blockers"],
        artifact_specs=[
            {
                "uri": "results/alpha2_sector_gap.json",
                "artifact_type": "result_json",
                "summary": "Finite certificate summary.",
            }
        ],
        source_specs=[
            {
                "uri": "notebook://alpha2-sector-gap",
                "asset_type": "note",
                "title": "Alpha=2 sector gap notebook",
                "summary": "Burst notebook with convention notes.",
            }
        ],
        tool_run_specs=[
            {
                "recipe_id": "recipe-alpha2-check",
                "tool_family": "local_python",
                "tool_name": "check_alpha2_sector_table",
                "inputs": {"table": "alpha2"},
                "outputs": {"status": "dry_run"},
            }
        ],
        sensemaking_summary="The burst clarified the sector-convention boundary but did not close the proof.",
        source_refs=["source:hs-alpha-notebook"],
    )

    assert batch["kind"] == "quiet_checkpoint_batch"
    assert batch["status"] == "recorded_without_trust_promotion"
    assert batch["can_update_claim_trust"] is False
    assert any(ref.startswith("artifact:") for ref in batch["written_refs"])
    assert any(ref.startswith("source_asset:") for ref in batch["written_refs"])
    assert any(ref.startswith("tool_run:") for ref in batch["written_refs"])
    assert any(ref.startswith("sensemaking_report:") for ref in batch["written_refs"])
    assert f"quiet_checkpoint:{batch['checkpoint_id']}" in batch["written_refs"]

    verification = verify_recording_effect(
        ws,
        "s-hs-burst",
        claim_id=claim.claim_id,
        expected_refs=batch["written_refs"],
    )
    assert verification["verified"] is True
    assert verification["missing_refs"] == []
    assert get_claim(ws, claim.claim_id).confidence_state == "hypothesis"


def test_quiet_checkpoint_cli_and_mcp_surfaces(tmp_path, capsys):
    from brain.v5.mcp_tools import aitp_v5_apply_quiet_checkpoint_batch, aitp_v5_preview_quiet_checkpoint_batch
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qsgw-headwing-update-librpa", context_id="librpa", title="LibRPA headwing")
    claim = create_claim(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        statement="Final-lane headwing reuse needs batch provenance before a trust update.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="final and diagnostic lanes need separation",
    )
    bind_session(
        ws,
        "s-headwing-burst",
        topic_id="qsgw-headwing-update-librpa",
        context_id="librpa",
        active_claim=claim.claim_id,
    )

    cli_preview = _invoke(
        [
            "--base",
            str(tmp_path),
            "checkpoint",
            "preview-batch",
            "s-headwing-burst",
            "--summary",
            "Headwing final-lane audit burst.",
            "--artifact-json",
            '{"uri":"reports/headwing_final_lane.tsv","artifact_type":"table","summary":"Final-lane table pointer."}',
            "--source-json",
            '{"uri":"notebook://headwing-final-lane","asset_type":"note","title":"Headwing final lane note"}',
            "--tool-run-json",
            '{"recipe_id":"recipe-headwing-audit","tool_family":"python","tool_name":"refresh_headwing_dashboard"}',
        ],
        capsys,
    )
    mcp_preview = aitp_v5_preview_quiet_checkpoint_batch(
        str(tmp_path),
        session_id="s-headwing-burst",
        summary="Headwing final-lane audit burst.",
    )
    mcp_batch = aitp_v5_apply_quiet_checkpoint_batch(
        str(tmp_path),
        session_id="s-headwing-burst",
        summary="Headwing final-lane audit burst.",
        artifact_specs=[
            {
                "uri": "reports/headwing_final_lane.tsv",
                "artifact_type": "table",
                "summary": "Final-lane table pointer.",
            }
        ],
    )

    assert cli_preview["kind"] == "quiet_checkpoint_preview"
    assert cli_preview["planned_typed_writes"]
    assert mcp_preview["kind"] == "quiet_checkpoint_preview"
    assert mcp_batch["kind"] == "quiet_checkpoint_batch"
    assert mcp_batch["can_update_claim_trust"] is False
