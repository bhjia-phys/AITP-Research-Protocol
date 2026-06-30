from __future__ import annotations


def _seed_focus_workspace(tmp_path):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "hs-chain", context_id="quantum-chaos", title="Long-range spin-chain chaos")
    old_claim = create_claim(
        ws,
        topic_id="hs-chain",
        statement="The A2 Schur tail proof closes the all-L upper-bound gap.",
        evidence_profile="semi_formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="A2 replacement sufficiency remains open",
    )
    hidden_claim = create_claim(
        ws,
        topic_id="hs-chain",
        statement="Hidden symmetry discovery and irreducible sector partitions organize current spectral statistics work.",
        evidence_profile="mixed_theory_numeric",
        confidence_state="hypothesis",
        active_uncertainty="physical charge identification and all-L proof remain open",
    )
    level_claim = create_claim(
        ws,
        topic_id="hs-chain",
        statement="Level spacing statistics are validated only after symmetry-resolved sector gates are fixed.",
        evidence_profile="bounded_numerical",
        confidence_state="hypothesis",
        active_uncertainty="sector leakage may spoil raw r-ratio conclusions",
    )
    bind_session(
        ws,
        "codex-hs-alpha-axis-20260605",
        topic_id="hs-chain",
        context_id="quantum-chaos",
        active_claim=old_claim.claim_id,
        interaction_steering="continue A2 Schur-tail proof",
    )
    return ws, old_claim, hidden_claim, level_claim


def _write_source(ws, claim, suffix: str, *, summary: str = "hidden symmetry sector source"):
    from brain.v5.models import SourceAssetRecord
    from brain.v5.store import write_record

    record = SourceAssetRecord(
        asset_id=f"source-{suffix}",
        topic_id=claim.topic_id,
        asset_type="local_file",
        uri=f"file:///{suffix}.json",
        title=f"{suffix} hidden sector data",
        claim_id=claim.claim_id,
        summary=summary,
    )
    write_record(ws.registry_dir("source_assets") / f"{record.asset_id}.md", record)
    return record


def _write_tool_run(ws, claim, suffix: str, *, summary: str = "sector export"):
    from brain.v5.models import ToolRunRecord
    from brain.v5.store import write_record

    record = ToolRunRecord(
        run_id=f"tool-run-{suffix}",
        recipe_id="sector-export",
        tool_family="local_python",
        tool_name="sector_export",
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        inputs={"goal": summary},
        outputs={"summary": summary},
        evidence_status="diagnostic",
    )
    write_record(ws.registry_dir("tool_runs") / f"{record.run_id}.md", record)
    return record


def _write_evidence(ws, claim, suffix: str, *, summary: str = "finite-size hidden symmetry evidence"):
    from brain.v5.models import EvidenceRecord
    from brain.v5.store import write_record

    record = EvidenceRecord(
        evidence_id=f"evidence-{suffix}",
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        evidence_type="bounded_numerical",
        status="mixed",
        summary=summary,
    )
    write_record(ws.registry_dir("evidence") / f"{record.evidence_id}.md", record)
    return record


def _write_authority(ws, claim, suffix: str):
    from brain.v5.models import AuthorityRecord
    from brain.v5.store import write_record

    record = AuthorityRecord(
        authority_id=f"authority-{suffix}",
        topic_id=claim.topic_id,
        authority_type="sector_authority",
        authority_statement="Use irreducible sector partitions before raw level statistics.",
        claim_id=claim.claim_id,
    )
    write_record(ws.registry_dir("authorities") / f"{record.authority_id}.md", record)
    return record


def _write_sensemaking(ws, claim, suffix: str):
    from brain.v5.models import SensemakingReportRecord
    from brain.v5.store import write_record

    record = SensemakingReportRecord(
        report_id=f"sensemaking-{suffix}",
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        title="Hidden-symmetry sector route",
        summary="Matrix-unit route finds hidden symmetry sectors; use as orientation only before final P(r).",
    )
    write_record(ws.registry_dir("sensemaking_reports") / f"{record.report_id}.md", record)
    return record


def test_active_claim_focus_no_drift_when_active_claim_has_recent_records(tmp_path):
    from brain.v5.active_claim_focus import detect_active_claim_focus_drift
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, old_claim, hidden_claim, _ = _seed_focus_workspace(tmp_path)
    _write_tool_run(ws, old_claim, "old-a")
    _write_evidence(ws, old_claim, "old-b")
    _write_source(ws, hidden_claim, "hidden-a")

    payload = require_valid_public_surface(
        "active_claim_focus_reconciliation",
        detect_active_claim_focus_drift(ws, "codex-hs-alpha-axis-20260605"),
    )

    assert payload["status"] == "no_active_claim_focus_drift"
    assert payload["warnings"] == []
    assert payload["not_authoritative_for_current_goal_if_rebind_needed"] is False
    assert payload["active_claim"]["claim_id"] == old_claim.claim_id


def test_active_claim_focus_drift_warns_without_rebinding(tmp_path):
    from brain.v5.active_claim_focus import detect_active_claim_focus_drift
    from brain.v5.claim_relation_map import build_claim_relation_map
    from brain.v5.context_pack import build_aitp_context_pack
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.recording_navigator import build_recording_navigation_state
    from brain.v5.workspace import get_session_binding

    ws, old_claim, hidden_claim, _ = _seed_focus_workspace(tmp_path)
    _write_source(ws, hidden_claim, "hidden-source")
    _write_tool_run(ws, hidden_claim, "hidden-run")
    _write_evidence(ws, hidden_claim, "hidden-evidence")
    _write_authority(ws, hidden_claim, "hidden-authority")
    _write_sensemaking(ws, hidden_claim, "hidden-sensemaking")

    drift = detect_active_claim_focus_drift(
        ws,
        "codex-hs-alpha-axis-20260605",
        user_goal="hidden symmetry discovery irreducible sector level statistics",
    )
    relation_map = require_valid_public_surface(
        "claim_relation_map",
        build_claim_relation_map(
            ws,
            "codex-hs-alpha-axis-20260605",
            user_goal="hidden symmetry discovery irreducible sector level statistics",
        ),
    )
    context_pack = require_valid_public_surface(
        "aitp_context_pack",
        build_aitp_context_pack(
            ws,
            "codex-hs-alpha-axis-20260605",
            user_goal="hidden symmetry discovery irreducible sector level statistics",
        ),
    )
    navigation = require_valid_public_surface(
        "recording_navigation_state",
        build_recording_navigation_state(ws, "codex-hs-alpha-axis-20260605"),
    )

    assert drift["warning_code"] == "active_claim_focus_drift_detected"
    assert drift["candidate_sibling_claims"][0]["claim_id"] == hidden_claim.claim_id
    assert get_session_binding(ws, "codex-hs-alpha-axis-20260605").active_claim == old_claim.claim_id
    assert relation_map["claim_id"] == old_claim.claim_id
    assert relation_map["relation_map_scope"] == "active_claim_only"
    assert relation_map["not_authoritative_for_current_goal_if_rebind_needed"] is True
    assert "active_claim_focus_drift_detected" in relation_map["warnings"]
    assert context_pack["not_authoritative_for_current_goal_if_rebind_needed"] is True
    assert any("active_claim_focus_drift_detected" in line for line in context_pack["context_lines"])
    assert "active_claim_focus_drift_detected" in navigation["warnings"]


def test_active_claim_rebind_requires_confirmation_and_writes_audit(tmp_path):
    from brain.v5.active_claim_focus import confirm_active_claim_rebind
    from brain.v5.claim_relation_map import build_claim_relation_map
    from brain.v5.models import ActiveClaimRebindAuditRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import list_valid_records
    from brain.v5.workspace import get_claim, get_session_binding

    ws, old_claim, hidden_claim, _ = _seed_focus_workspace(tmp_path)
    _write_source(ws, hidden_claim, "hidden-source")
    _write_tool_run(ws, hidden_claim, "hidden-run")
    old_confidence = get_claim(ws, old_claim.claim_id).confidence_state
    new_confidence = get_claim(ws, hidden_claim.claim_id).confidence_state

    result = require_valid_public_surface(
        "active_claim_rebind_confirmation",
        confirm_active_claim_rebind(
            ws,
            "codex-hs-alpha-axis-20260605",
            new_claim_id=hidden_claim.claim_id,
            reason="User confirmed current work is hidden symmetry sector discovery.",
            user_confirmation="确认切换到 hidden symmetry claim",
            operator="test-user",
        ),
    )
    relation_map = build_claim_relation_map(ws, "codex-hs-alpha-axis-20260605")
    audits = list_valid_records(ws.registry_dir("active_claim_rebind_audits"), ActiveClaimRebindAuditRecord)

    assert result["status"] == "applied"
    assert result["old_claim_id"] == old_claim.claim_id
    assert result["new_claim_id"] == hidden_claim.claim_id
    assert get_session_binding(ws, "codex-hs-alpha-axis-20260605").active_claim == hidden_claim.claim_id
    assert relation_map["claim_id"] == hidden_claim.claim_id
    assert len(audits) == 1
    assert audits[0].old_claim_id == old_claim.claim_id
    assert audits[0].new_claim_id == hidden_claim.claim_id
    assert get_claim(ws, old_claim.claim_id).confidence_state == old_confidence
    assert get_claim(ws, hidden_claim.claim_id).confidence_state == new_confidence


def test_active_claim_focus_multiple_candidate_sibling_claims(tmp_path):
    from brain.v5.active_claim_focus import detect_active_claim_focus_drift

    ws, _, hidden_claim, level_claim = _seed_focus_workspace(tmp_path)
    _write_source(ws, hidden_claim, "hidden-source")
    _write_tool_run(ws, hidden_claim, "hidden-run")
    _write_evidence(ws, hidden_claim, "hidden-evidence")
    _write_source(ws, level_claim, "level-source", summary="level statistics r-ratio sector gate")
    _write_tool_run(ws, level_claim, "level-run", summary="level statistics r-ratio")

    payload = detect_active_claim_focus_drift(
        ws,
        "codex-hs-alpha-axis-20260605",
        user_goal="hidden symmetry and level statistics",
    )
    candidate_ids = [candidate["claim_id"] for candidate in payload["candidate_sibling_claims"]]

    assert hidden_claim.claim_id in candidate_ids
    assert level_claim.claim_id in candidate_ids
    assert candidate_ids.index(hidden_claim.claim_id) < candidate_ids.index(level_claim.claim_id)


def test_orientation_only_recent_records_detect_drift_without_promotion(tmp_path):
    from brain.v5.active_claim_focus import detect_active_claim_focus_drift
    from brain.v5.workspace import get_claim

    ws, old_claim, hidden_claim, _ = _seed_focus_workspace(tmp_path)
    _write_source(ws, hidden_claim, "hidden-source-a")
    _write_authority(ws, hidden_claim, "hidden-authority-a")
    _write_sensemaking(ws, hidden_claim, "hidden-sensemaking-a")
    old_confidence = get_claim(ws, hidden_claim.claim_id).confidence_state

    payload = detect_active_claim_focus_drift(
        ws,
        "codex-hs-alpha-axis-20260605",
        user_goal="hidden symmetry sector authority",
    )
    hidden_candidate = next(
        candidate for candidate in payload["candidate_sibling_claims"] if candidate["claim_id"] == hidden_claim.claim_id
    )

    assert payload["warning_code"] == "active_claim_focus_drift_detected"
    assert hidden_candidate["orientation_only_record_count"] == hidden_candidate["total_record_count"]
    assert hidden_candidate["trust_promotion_allowed"] is False
    assert payload["can_update_claim_trust"] is False
    assert get_claim(ws, old_claim.claim_id).confidence_state == "hypothesis"
    assert get_claim(ws, hidden_claim.claim_id).confidence_state == old_confidence


def test_active_claim_focus_mcp_wrappers_round_trip(tmp_path):
    from brain.v5.mcp_tools import (
        aitp_v5_confirm_active_claim_rebind,
        aitp_v5_detect_active_claim_focus_drift,
        aitp_v5_propose_active_claim_rebind,
    )

    ws, old_claim, hidden_claim, _ = _seed_focus_workspace(tmp_path)
    _write_source(ws, hidden_claim, "hidden-source")
    _write_tool_run(ws, hidden_claim, "hidden-run")

    drift = aitp_v5_detect_active_claim_focus_drift(
        str(tmp_path),
        session_id="codex-hs-alpha-axis-20260605",
        user_goal="hidden symmetry sectors",
    )
    proposal = aitp_v5_propose_active_claim_rebind(
        str(tmp_path),
        session_id="codex-hs-alpha-axis-20260605",
        candidate_claim_id=hidden_claim.claim_id,
        reason="current work moved to hidden symmetry",
    )
    confirmation = aitp_v5_confirm_active_claim_rebind(
        str(tmp_path),
        session_id="codex-hs-alpha-axis-20260605",
        new_claim_id=hidden_claim.claim_id,
        reason="current work moved to hidden symmetry",
        user_confirmation="confirmed in test",
        operator="test-user",
    )

    assert drift["warning_code"] == "active_claim_focus_drift_detected"
    assert proposal["status"] == "requires_user_confirmation"
    assert proposal["proposed_operation"]["will_update_claim_trust"] is False
    assert confirmation["status"] == "applied"
    assert confirmation["old_claim_id"] == old_claim.claim_id
    assert confirmation["new_claim_id"] == hidden_claim.claim_id
