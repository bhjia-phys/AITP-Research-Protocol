from __future__ import annotations


def _seed_workspace(tmp_path):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "bi2se3-nonsoc-qsgw-topology", context_id="librpa", title="Bi2Se3 non-SOC topology")
    claim = create_claim(
        ws,
        topic_id="bi2se3-nonsoc-qsgw-topology",
        statement="Bi2Se3 non-SOC QSGW/PYATB topology needs separated KS controls and QSGW validation.",
        evidence_profile="code_numerical",
        confidence_state="hypothesis",
        active_uncertainty="QSGW topology invariant is not validated",
    )
    bind_session(
        ws,
        "s-bi2se3",
        topic_id="bi2se3-nonsoc-qsgw-topology",
        context_id="librpa",
        active_claim=claim.claim_id,
    )
    return ws, claim


def test_summary_only_closeout_is_weak_checkpoint_without_artifact_recommendation(tmp_path):
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.quiet_checkpoint import preview_quiet_checkpoint_batch

    ws, _claim = _seed_workspace(tmp_path)
    preview = preview_quiet_checkpoint_batch(
        ws,
        "s-bi2se3",
        summary="Discussed topic status without durable files or validation claims.",
    )

    require_valid_public_surface("quiet_checkpoint_preview", preview)
    audit = preview["record_completeness_audit"]
    assert audit["checkpoint_strength"] == "weak_checkpoint"
    assert audit["recording_complete"] is True
    assert audit["missing_recommended_slots"] == []
    assert audit["recommended_next_records"] == []
    assert "artifact" not in audit["missing_recommended_slots"]
    assert audit["trust_boundary"]["do_not_promote_trust"] is True


def test_durable_generated_files_recommend_artifact_attach_with_provenance(tmp_path):
    from brain.v5.quiet_checkpoint import preview_quiet_checkpoint_batch

    ws, _claim = _seed_workspace(tmp_path)
    preview = preview_quiet_checkpoint_batch(
        ws,
        "s-bi2se3",
        summary="Wrote a note and data outputs.",
        generated_artifacts=[
            {
                "path": "research/librpa/reports/bi2se3_nonsoc_qsgw_topology_note.pdf",
                "artifact_type": "pdf_note",
                "summary": "Compiled topology note.",
            },
            {"path": "research/librpa/reports/fig2_colored.png", "summary": "Colored Figure 2."},
            {"path": "research/librpa/results/ks_local_fhs.json", "summary": "KS local FHS output."},
        ],
    )

    audit = preview["record_completeness_audit"]
    assert "artifact" in audit["missing_recommended_slots"]
    artifact_plan = next(item for item in audit["recommended_next_records"] if item["slot"] == "artifact")
    paths = {item["uri"] for item in artifact_plan["canonical_provenance"]}
    assert "research/librpa/reports/bi2se3_nonsoc_qsgw_topology_note.pdf" in paths
    assert "research/librpa/reports/fig2_colored.png" in paths
    assert "research/librpa/results/ks_local_fhs.json" in paths
    assert artifact_plan["plan_only"] is True
    assert audit["trust_boundary"]["unresolved_artifact_refs_are_not_evidence"] is True


def test_changed_files_and_repo_paths_recommend_code_state(tmp_path):
    from brain.v5.quiet_checkpoint import preview_quiet_checkpoint_batch

    ws, _claim = _seed_workspace(tmp_path)
    preview = preview_quiet_checkpoint_batch(
        ws,
        "s-bi2se3",
        summary="Updated scripts and regenerated data.",
        changed_files=["research/librpa/scripts/bi2se3_local_fhs.py"],
        generated_artifacts=[
            {
                "path": "research/librpa/results/ks_local_fhs.md",
                "repo_path": "F:/AI_Workspace/Theoretical-Physics",
            }
        ],
    )

    audit = preview["record_completeness_audit"]
    assert "code_state" in audit["missing_recommended_slots"]
    code_plan = next(item for item in audit["recommended_next_records"] if item["slot"] == "code_state")
    assert code_plan["recommended_tool"] == "aitp_v5_capture_code_state_auto"
    assert "changed_files_present" in code_plan["triggers"]
    assert "repo_path_present" in code_plan["triggers"]


def test_validation_commands_recommend_validation_result_without_trust_promotion(tmp_path):
    from brain.v5.quiet_checkpoint import preview_quiet_checkpoint_batch

    ws, _claim = _seed_workspace(tmp_path)
    preview = preview_quiet_checkpoint_batch(
        ws,
        "s-bi2se3",
        summary="Compiled the note and checked logs.",
        validation_commands=[
            "pdflatex bi2se3_nonsoc_qsgw_topology_note.tex",
            "pdflatex bi2se3_nonsoc_qsgw_topology_note.tex",
            "Select-String -Path bi2se3_nonsoc_qsgw_topology_note.log -Pattern 'Warning|Error'",
        ],
        claim_boundary={"validated": ["PDF compiles without fatal errors"]},
    )

    audit = preview["record_completeness_audit"]
    assert "validation_result" in audit["missing_recommended_slots"]
    validation_plan = next(item for item in audit["recommended_next_records"] if item["slot"] == "validation_result")
    assert validation_plan["recommended_tool"] == "aitp_v5_record_validation_result"
    assert validation_plan["do_not_promote_trust"] is True
    assert audit["trust_boundary"]["do_not_promote_trust"] is True


def test_open_gap_validation_boundary_recommends_validation_gap_and_no_trust_promotion(tmp_path):
    from brain.v5.quiet_checkpoint import preview_quiet_checkpoint_batch

    ws, _claim = _seed_workspace(tmp_path)
    preview = preview_quiet_checkpoint_batch(
        ws,
        "s-bi2se3",
        summary="KS control was checked but QSGW invariant remains open.",
        validation_commands=["python research/librpa/scripts/bi2se3_local_fhs.py --ks-control"],
        claim_boundary={
            "validated": ["KS local FHS control is zero"],
            "cannot_say": ["QSGW topology invariant not validated"],
            "open_gaps": ["Need QSGW topology invariant validation"],
        },
    )

    audit = preview["record_completeness_audit"]
    validation_plan = next(item for item in audit["recommended_next_records"] if item["slot"] == "validation_result")
    assert validation_plan["record_kind"] == "validation_result_or_validation_gap"
    assert validation_plan["status_hint"] == "inconclusive_or_partial"
    assert "validation_result" in audit["missing_recommended_slots"]
    assert audit["can_update_claim_trust"] is False
    assert audit["trust_boundary"]["requires_trust_preflight_for_promotion"] is True


def test_bi2se3_note_case_recommends_artifact_code_state_and_validation_boundary(tmp_path):
    from brain.v5.codex_facade import codex_closeout

    ws, claim = _seed_workspace(tmp_path)
    closeout = codex_closeout(
        ws,
        session_id="s-bi2se3",
        claim_id=claim.claim_id,
        summary="Recorded Bi2Se3 non-SOC QSGW/PYATB topology note outputs and validation boundary.",
        generated_artifacts=[
            {
                "path": "research/librpa/reports/bi2se3_nonsoc_qsgw_topology_note.pdf",
                "artifact_type": "pdf_note",
                "summary": "Compiled PDF note.",
            },
            {
                "path": "research/librpa/reports/bi2se3_nonsoc_qsgw_topology_note.tex",
                "artifact_type": "tex_source",
                "summary": "LaTeX source for the note.",
            },
            {
                "path": "research/librpa/reports/bi2se3_figure2_colored.png",
                "artifact_type": "figure",
                "summary": "Colored Figure 2.",
            },
            {
                "path": "research/librpa/results/bi2se3_ks_local_fhs.json",
                "artifact_type": "result_json",
                "summary": "KS local FHS data.",
            },
            {
                "path": "research/librpa/results/bi2se3_ks_local_fhs.md",
                "artifact_type": "result_report",
                "summary": "KS local FHS markdown summary.",
            },
        ],
        changed_files=[
            "research/librpa/scripts/bi2se3_local_fhs.py",
            "research/librpa/reports/bi2se3_nonsoc_qsgw_topology_note.tex",
        ],
        validation_commands=[
            "pdflatex bi2se3_nonsoc_qsgw_topology_note.tex",
            "pdflatex bi2se3_nonsoc_qsgw_topology_note.tex",
            "Select-String -Path bi2se3_nonsoc_qsgw_topology_note.log -Pattern 'Warning|Error'",
            "python research/librpa/scripts/bi2se3_local_fhs.py --input ks_hr.dat --output bi2se3_ks_local_fhs.json",
        ],
        claim_boundary={
            "validated": ["PDF compiles", "KS local FHS control is zero"],
            "cannot_say": ["QSGW topology invariant not validated"],
            "open_gaps": ["QSGW topology invariant still needs validation"],
        },
    )

    assert closeout["kind"] == "codex_closeout"
    audit = closeout["record_completeness_audit"]
    assert {"artifact", "code_state", "validation_result"}.issubset(set(audit["missing_recommended_slots"]))
    assert audit["recording_complete"] is False
    assert audit["requires_user_confirmation"] is True
    assert audit["trust_boundary"]["do_not_promote_trust"] is True
    assert closeout["missing_recommended_slots"] == audit["missing_recommended_slots"]
    artifact_plan = next(item for item in audit["recommended_next_records"] if item["slot"] == "artifact")
    provenance_paths = {item["uri"] for item in artifact_plan["canonical_provenance"]}
    assert "research/librpa/reports/bi2se3_nonsoc_qsgw_topology_note.pdf" in provenance_paths
    assert "research/librpa/results/bi2se3_ks_local_fhs.md" in provenance_paths
