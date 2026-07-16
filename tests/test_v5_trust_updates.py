from __future__ import annotations

import json


def _seed_claim(tmp_path, *, evidence_profile: str = "toy_numeric"):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE Learning")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Finite-size counting identifies the FQHE edge sector.",
        evidence_profile=evidence_profile,
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifacts can mimic edge counting",
    )
    bind_session(
        ws,
        "s1",
        topic_id="fqhe",
        context_id="topological-order",
        active_claim=claim.claim_id,
    )
    return ws, claim


def _record_source_evidence(ws, claim):
    from brain.v5.evidence import record_evidence
    from brain.v5.models import ReferenceLocationRecord, SourceAssetRecord
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository

    repository = RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="trust-update-test", host="pytest"),
    )
    repository.write(
        "source_assets",
        SourceAssetRecord(
            asset_id="trust-source",
            topic_id=claim.topic_id,
            asset_type="paper",
            uri="file:///trust-source.pdf",
            title="Trust source",
            content_hash="a" * 64,
            hash_algorithm="sha256",
        ),
    )
    repository.write(
        "reference_locations",
        ReferenceLocationRecord(
            location_id="trust-source-equation",
            topic_id=claim.topic_id,
            claim_id=claim.claim_id,
            connector_id="local-source",
            location_type="equation_anchor",
            uri="file:///trust-source.pdf#eq=1",
            label="Equation 1",
            source_ref="source_asset:trust-source",
        ),
    )
    return record_evidence(
        ws,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        evidence_type="literature_equation",
        status="supports",
        summary="Pinned source support.",
        support_basis_refs=[
            pin_current_record(ws, "source_asset:trust-source"),
            pin_current_record(ws, "reference_location:trust-source-equation"),
        ],
        trace_context_refs=[],
    )


def _record_validated_evidence(ws, claim):
    from brain.v5.evidence import record_evidence
    from brain.v5.tools import record_tool_run
    from brain.v5.validation import create_validation_contract, record_validation_result

    contract = create_validation_contract(
        ws,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        required_checks=["bounded check"],
        failure_modes=["scope mismatch"],
        required_evidence_outputs=["bounded_result"],
    )
    run = record_tool_run(
        ws,
        recipe_id="bounded-check",
        tool_family="numerical",
        tool_name="pytest",
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        outputs={"bounded_result": True},
    )
    result = record_validation_result(
        ws,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        contract_id=contract.contract_id,
        tool_run_id=run.run_id,
        status="passed",
        checked_outputs=["bounded_result"],
        summary="Bounded check passed.",
    )
    return record_evidence(
        ws,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        evidence_type="validated_check",
        status="supports",
        summary="Self-contained validated support.",
        tool_run_ids=[run.run_id],
        validation_result_ids=[result.result_id],
    )


def _invoke(args, capsys):
    from brain.v5.cli import main

    assert main(args) == 0
    output = capsys.readouterr().out
    return json.loads(output)


def test_preflight_blocks_summary_sourced_confidence_change_without_mutating_claim(tmp_path):
    from brain.v5.contracts import validate_trust_update_preflight
    from brain.v5.trust_updates import TrustUpdateRequest, preflight_trust_update
    from brain.v5.workspace import get_claim

    ws, claim = _seed_claim(tmp_path)
    request = TrustUpdateRequest(
        request_id="trust-req-summary",
        action="change_claim_confidence",
        session_id="s1",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        requested_state="locally_checked",
        source_kind="derived_summary",
        source_ref=".aitp/surfaces/session_summaries/s1/findings.md",
        rationale="The summary text says this is checked.",
    )

    payload = preflight_trust_update(ws, request)
    persisted = get_claim(ws, claim.claim_id)

    assert payload["kind"] == "trust_update_preflight"
    assert payload["allowed"] is False
    assert payload["mutation_allowed_after_preflight"] is False
    assert payload["truth_source"] == "typed_records"
    assert payload["summary_inputs_trusted"] is False
    assert "query_execution_brief_or_typed_record" in payload["required_actions"]
    assert any(reason["policy_id"] == "no_summary_surface_as_truth_source" for reason in payload["policy_reasons"])
    assert persisted.confidence_state == "hypothesis"
    assert validate_trust_update_preflight(payload).ok is True


def test_trust_update_preflight_contract_rejects_mutating_or_summary_trusted_payloads():
    from brain.v5.contracts import validate_trust_update_preflight

    payload = {
        "kind": "trust_update_preflight",
        "request": {"kind": "trust_update_request"},
        "request_id": "trust-req-invalid",
        "action": "change_claim_confidence",
        "session_id": "s1",
        "topic_id": "fqhe",
        "claim_id": "claim-fqhe",
        "allowed": True,
        "mutation_allowed_after_preflight": True,
        "policy_reasons": [],
        "required_actions": [],
        "evidence_refs": [],
        "code_state_ids": [],
        "truth_source": "summary_orientation",
        "summary_inputs_trusted": True,
        "can_update_kernel_state": True,
    }

    result = validate_trust_update_preflight(payload)

    assert result.ok is False
    assert any(issue.path == "trust_preflight.truth_source" for issue in result.issues)
    assert any(issue.path == "trust_preflight.summary_inputs_trusted" for issue in result.issues)
    assert any(issue.path == "trust_preflight.can_update_kernel_state" for issue in result.issues)


def test_preflight_blocks_code_method_validation_without_code_state(tmp_path):
    from brain.v5.trust_updates import TrustUpdateRequest, preflight_trust_update

    ws, claim = _seed_claim(tmp_path, evidence_profile="code_method")
    request = TrustUpdateRequest(
        request_id="trust-req-code",
        action="validate_claim",
        session_id="s1",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        source_kind="execution_brief",
        source_ref="brief:s1",
        evidence_refs=["tool_run:run-ed"],
        rationale="The code-method claim should be validated.",
    )

    payload = preflight_trust_update(ws, request)

    assert payload["allowed"] is False
    assert "record_code_state" in payload["required_actions"]
    assert any(reason["policy_id"] == "no_code_method_validation_without_code_state" for reason in payload["policy_reasons"])


def test_confidence_update_rejects_legacy_unchecked_evidence(tmp_path):
    from dataclasses import replace

    from brain.v5.evidence import record_evidence
    from brain.v5.trust_updates import TrustUpdateRequest, apply_trust_update, preflight_trust_update

    ws, claim = _seed_claim(tmp_path)
    legacy = record_evidence(
        ws,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        evidence_type="legacy_note",
        status="supports",
        summary="Unpinned historical support.",
    )
    request = TrustUpdateRequest(
        request_id="trust-req-unchecked-evidence",
        action="change_claim_confidence",
        session_id="s1",
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        requested_state="locally_checked",
        source_kind="typed_records",
        evidence_refs=[legacy.evidence_id],
        rationale="Unchecked evidence must not justify confidence.",
    )

    preflight = preflight_trust_update(ws, request)
    applied = apply_trust_update(
        ws,
        replace(request, preflight_token=preflight["preflight_token"]),
    )

    assert preflight["allowed"] is False
    assert "record_or_review_evidence_basis" in preflight["required_actions"]
    assert applied["applied"] is False


def test_checked_confidence_update_requires_evidence(tmp_path):
    from brain.v5.trust_updates import TrustUpdateRequest, preflight_trust_update

    ws, claim = _seed_claim(tmp_path)
    request = TrustUpdateRequest(
        request_id="trust-req-no-evidence",
        action="change_claim_confidence",
        session_id="s1",
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        requested_state="locally_checked",
        source_kind="typed_records",
    )

    preflight = preflight_trust_update(ws, request)

    assert preflight["allowed"] is False
    assert "record_supporting_evidence" in preflight["required_actions"]


def test_confidence_update_accepts_self_contained_validated_evidence(tmp_path):
    from brain.v5.trust_updates import TrustUpdateRequest, preflight_trust_update

    ws, claim = _seed_claim(tmp_path)
    evidence = _record_validated_evidence(ws, claim)
    request = TrustUpdateRequest(
        request_id="trust-req-validated-evidence",
        action="change_claim_confidence",
        session_id="s1",
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        requested_state="locally_checked",
        source_kind="typed_records",
        evidence_refs=[evidence.evidence_id],
    )

    preflight = preflight_trust_update(ws, request)

    assert preflight["allowed"] is True
    assert preflight["required_actions"] == []


def test_preflight_allows_code_method_promotion_with_evidence_and_code_state(tmp_path):
    from brain.v5.code import record_code_state
    from brain.v5.trust_updates import TrustUpdateRequest, preflight_trust_update

    ws, claim = _seed_claim(tmp_path, evidence_profile="code_method")
    code_state = record_code_state(
        ws,
        repo_id="librpa",
        upstream_remote="origin",
        upstream_branch="master",
        upstream_commit="abc123",
        local_branch="topic/self-energy",
        worktree_path="D:/worktrees/librpa/self-energy",
        dirty=False,
        linked_records={"claim_id": claim.claim_id},
    )
    evidence = _record_source_evidence(ws, claim)
    request = TrustUpdateRequest(
        request_id="trust-req-promote",
        action="promote_to_l2",
        session_id="s1",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        source_kind="execution_brief",
        source_ref="brief:s1",
        evidence_refs=[evidence.evidence_id],
        code_state_ids=[code_state.code_state_id],
        rationale="Promotion request cites evidence and exact code provenance.",
    )

    payload = preflight_trust_update(ws, request)

    assert payload["allowed"] is True
    assert payload["mutation_allowed_after_preflight"] is True
    assert payload["required_actions"] == []
    assert payload["code_state_ids"] == [code_state.code_state_id]
    assert payload["preflight_token"].startswith("trust-preflight-")
    assert payload["preflight_proof"]["token"] == payload["preflight_token"]
    assert payload["preflight_proof"]["request_id"] == "trust-req-promote"


def test_apply_confidence_change_requires_matching_preflight_token(tmp_path):
    from brain.v5.trust_updates import TrustUpdateRequest, apply_trust_update
    from brain.v5.workspace import get_claim

    ws, claim = _seed_claim(tmp_path)
    evidence = _record_validated_evidence(ws, claim)
    request = TrustUpdateRequest(
        request_id="trust-req-apply",
        action="change_claim_confidence",
        session_id="s1",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        requested_state="locally_checked",
        source_kind="execution_brief",
        source_ref="brief:s1",
        evidence_refs=[evidence.evidence_id],
        rationale="A typed preflight is required before a confidence update.",
    )

    payload = apply_trust_update(ws, request)
    persisted = get_claim(ws, claim.claim_id)

    assert payload["kind"] == "trust_update_apply"
    assert payload["applied"] is False
    assert payload["preflight"]["allowed"] is True
    assert payload["preflight_token"] == ""
    assert payload["required_actions"] == ["pass_matching_preflight_token"]
    assert persisted.confidence_state == "hypothesis"


def test_apply_confidence_change_updates_registry_and_topic_ledger(tmp_path):
    from dataclasses import asdict
    from dataclasses import replace

    from brain.v5.contracts import validate_trust_update_apply
    from brain.v5.models import ClaimRecord, TrustUpdateRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import list_records, read_record
    from brain.v5.trust_updates import TrustUpdateRequest, apply_trust_update, preflight_trust_update
    from brain.v5.workspace import get_claim

    ws, claim = _seed_claim(tmp_path)
    evidence = _record_validated_evidence(ws, claim)
    request = TrustUpdateRequest(
        request_id="trust-req-apply",
        action="change_claim_confidence",
        session_id="s1",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        requested_state="locally_checked",
        source_kind="execution_brief",
        source_ref="brief:s1",
        evidence_refs=[evidence.evidence_id],
        rationale="A typed kernel brief and evidence review justify the confidence update.",
    )
    preflight = preflight_trust_update(ws, request)
    request = replace(request, preflight_token=preflight["preflight_token"])

    payload = apply_trust_update(ws, request)
    registry_claim = get_claim(ws, claim.claim_id)
    ledger_claim = read_record(
        ws.topic_dir("fqhe") / "claims" / "ledger" / f"{claim.claim_id}.md",
        ClaimRecord,
    )

    assert payload["kind"] == "trust_update_apply"
    assert payload["applied"] is True
    assert payload["previous_state"] == "hypothesis"
    assert payload["new_state"] == "locally_checked"
    assert payload["preflight"]["allowed"] is True
    assert payload["preflight_token"] == preflight["preflight_token"]
    assert registry_claim.confidence_state == "locally_checked"
    assert ledger_claim.confidence_state == "locally_checked"
    assert validate_trust_update_apply(payload).ok is True
    records = list_records(ws.registry_dir("trust_updates"), TrustUpdateRecord)
    assert len(records) == 1
    record = records[0]
    assert payload["trust_update_record_id"] == record.update_id
    assert record.applied is True
    assert record.status == "applied"
    assert record.previous_state == "hypothesis"
    assert record.new_state == "locally_checked"
    assert record.preflight_allowed is True
    assert record.preflight_token == preflight["preflight_token"]
    assert require_valid_public_surface("trust_update_record", {"ok": True, **asdict(record)})


def test_can_read_persisted_trust_update_record_by_id(tmp_path):
    from dataclasses import replace

    from brain.v5.trust_updates import (
        TrustUpdateRequest,
        apply_trust_update,
        get_trust_update_record,
        preflight_trust_update,
    )

    ws, claim = _seed_claim(tmp_path)
    evidence = _record_validated_evidence(ws, claim)
    request = TrustUpdateRequest(
        request_id="trust-req-read-record",
        action="change_claim_confidence",
        session_id="s1",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        requested_state="locally_checked",
        source_kind="execution_brief",
        source_ref="brief:s1",
        evidence_refs=[evidence.evidence_id],
        rationale="Read back the typed trust-update history record.",
    )
    preflight = preflight_trust_update(ws, request)
    request = replace(request, preflight_token=preflight["preflight_token"])

    payload = apply_trust_update(ws, request)
    record = get_trust_update_record(ws, payload["trust_update_record_id"])

    assert record.update_id == payload["trust_update_record_id"]
    assert record.request_id == "trust-req-read-record"
    assert record.applied is True


def test_apply_confidence_change_blocks_summary_source_without_mutating(tmp_path):
    from brain.v5.contracts import validate_trust_update_apply
    from brain.v5.models import TrustUpdateRecord
    from brain.v5.store import list_records
    from brain.v5.trust_updates import TrustUpdateRequest, apply_trust_update
    from brain.v5.workspace import get_claim

    ws, claim = _seed_claim(tmp_path)
    request = TrustUpdateRequest(
        request_id="trust-req-summary-apply",
        action="change_claim_confidence",
        session_id="s1",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        requested_state="locally_checked",
        source_kind="derived_summary",
        source_ref="findings.md",
        rationale="A summary claims the state was checked.",
    )

    payload = apply_trust_update(ws, request)
    persisted = get_claim(ws, claim.claim_id)

    assert payload["kind"] == "trust_update_apply"
    assert payload["applied"] is False
    assert payload["preflight"]["allowed"] is False
    assert "query_execution_brief_or_typed_record" in payload["required_actions"]
    assert persisted.confidence_state == "hypothesis"
    assert validate_trust_update_apply(payload).ok is True
    records = list_records(ws.registry_dir("trust_updates"), TrustUpdateRecord)
    assert len(records) == 1
    assert payload["trust_update_record_id"] == records[0].update_id
    assert records[0].applied is False
    assert records[0].status == "blocked"
    assert records[0].required_actions == ["query_execution_brief_or_typed_record"]


def test_trust_update_apply_contract_rejects_summary_trusted_or_invalid_preflight_payloads():
    from brain.v5.contracts import validate_trust_update_apply

    payload = {
        "kind": "trust_update_apply",
        "request": {"kind": "trust_update_request"},
        "request_id": "trust-req-invalid-apply",
        "action": "change_claim_confidence",
        "session_id": "s1",
        "topic_id": "fqhe",
        "claim_id": "claim-fqhe",
        "applied": True,
        "previous_state": "hypothesis",
        "new_state": "locally_checked",
        "required_actions": ["should_be_empty_when_applied"],
        "preflight": {"kind": "not_a_valid_preflight"},
        "truth_source": "summary_orientation",
        "summary_inputs_trusted": True,
    }

    result = validate_trust_update_apply(payload)

    assert result.ok is False
    paths = {issue.path for issue in result.issues}
    assert "trust_apply.truth_source" in paths
    assert "trust_apply.summary_inputs_trusted" in paths
    assert "trust_apply.required_actions" in paths
    assert any(path.startswith("trust_apply.preflight") for path in paths)


def test_cli_trust_preflight_returns_policy_payload(tmp_path, capsys):
    from brain.v5.contracts import validate_trust_update_preflight

    _, claim = _seed_claim(tmp_path)

    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "trust",
            "preflight",
            "change_claim_confidence",
            "--session",
            "s1",
            "--topic",
            "fqhe",
            "--claim",
            claim.claim_id,
            "--requested-state",
            "locally_checked",
            "--source-kind",
            "derived_summary",
            "--source-ref",
            "findings.md",
        ],
        capsys,
    )

    assert payload["ok"] is True
    assert payload["kind"] == "trust_update_preflight"
    assert payload["allowed"] is False
    assert payload["mutation_allowed_after_preflight"] is False
    assert payload["preflight_token"].startswith("trust-preflight-")
    assert validate_trust_update_preflight(payload).ok is True


def test_cli_trust_apply_confidence_change_updates_claim(tmp_path, capsys):
    from brain.v5.contracts import validate_trust_update_apply
    from brain.v5.workspace import get_claim, init_workspace

    ws, claim = _seed_claim(tmp_path)
    evidence = _record_validated_evidence(ws, claim)
    preflight = _invoke(
        [
            "--base",
            str(tmp_path),
            "trust",
            "preflight",
            "change_claim_confidence",
            "--session",
            "s1",
            "--topic",
            "fqhe",
            "--claim",
            claim.claim_id,
            "--requested-state",
            "locally_checked",
            "--source-kind",
            "execution_brief",
            "--source-ref",
            "brief:s1",
            "--evidence-ref",
            evidence.evidence_id,
        ],
        capsys,
    )

    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "trust",
            "apply",
            "change_claim_confidence",
            "--session",
            "s1",
            "--topic",
            "fqhe",
            "--claim",
            claim.claim_id,
            "--requested-state",
            "locally_checked",
            "--source-kind",
            "execution_brief",
            "--source-ref",
            "brief:s1",
            "--evidence-ref",
            evidence.evidence_id,
            "--preflight-token",
            preflight["preflight_token"],
        ],
        capsys,
    )

    persisted = get_claim(init_workspace(tmp_path), claim.claim_id)

    assert payload["ok"] is True
    assert payload["kind"] == "trust_update_apply"
    assert payload["applied"] is True
    assert payload["preflight_token"] == preflight["preflight_token"]
    assert persisted.confidence_state == "locally_checked"
    assert validate_trust_update_apply(payload).ok is True


def test_cli_trust_update_record_returns_contract_payload(tmp_path, capsys):
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _seed_claim(tmp_path)
    evidence = _record_validated_evidence(ws, claim)
    preflight = _invoke(
        [
            "--base",
            str(tmp_path),
            "trust",
            "preflight",
            "change_claim_confidence",
            "--session",
            "s1",
            "--topic",
            "fqhe",
            "--claim",
            claim.claim_id,
            "--requested-state",
            "locally_checked",
            "--source-kind",
            "execution_brief",
            "--source-ref",
            "brief:s1",
            "--evidence-ref",
            evidence.evidence_id,
        ],
        capsys,
    )
    applied = _invoke(
        [
            "--base",
            str(tmp_path),
            "trust",
            "apply",
            "change_claim_confidence",
            "--session",
            "s1",
            "--topic",
            "fqhe",
            "--claim",
            claim.claim_id,
            "--requested-state",
            "locally_checked",
            "--source-kind",
            "execution_brief",
            "--source-ref",
            "brief:s1",
            "--evidence-ref",
            evidence.evidence_id,
            "--preflight-token",
            preflight["preflight_token"],
        ],
        capsys,
    )

    record = _invoke(
        ["--base", str(tmp_path), "trust", "update-record", applied["trust_update_record_id"]],
        capsys,
    )

    assert record["ok"] is True
    assert record["update_id"] == applied["trust_update_record_id"]
    assert require_valid_public_surface("trust_update_record", record) == record


def test_mcp_preflight_trust_update_returns_contract_payload(tmp_path):
    from brain.v5.contracts import validate_trust_update_preflight
    from brain.v5.mcp_tools import aitp_v5_preflight_trust_update

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_preflight_trust_update(
        str(tmp_path),
        action="change_claim_confidence",
        session_id="s1",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        requested_state="locally_checked",
        source_kind="derived_summary",
        source_ref="findings.md",
    )

    assert payload["ok"] is True
    assert payload["kind"] == "trust_update_preflight"
    assert payload["allowed"] is False
    assert "query_execution_brief_or_typed_record" in payload["required_actions"]
    assert payload["preflight_token"].startswith("trust-preflight-")
    assert validate_trust_update_preflight(payload).ok is True


def test_mcp_apply_trust_update_accepts_matching_preflight_token(tmp_path):
    from brain.v5.contracts import validate_trust_update_apply
    from brain.v5.mcp_tools import aitp_v5_apply_trust_update, aitp_v5_preflight_trust_update
    from brain.v5.workspace import get_claim, init_workspace

    ws, claim = _seed_claim(tmp_path)
    evidence = _record_validated_evidence(ws, claim)
    preflight = aitp_v5_preflight_trust_update(
        str(tmp_path),
        action="change_claim_confidence",
        session_id="s1",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        requested_state="locally_checked",
        source_kind="execution_brief",
        source_ref="brief:s1",
        evidence_refs=[evidence.evidence_id],
    )

    payload = aitp_v5_apply_trust_update(
        str(tmp_path),
        action="change_claim_confidence",
        session_id="s1",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        requested_state="locally_checked",
        source_kind="execution_brief",
        source_ref="brief:s1",
        evidence_refs=[evidence.evidence_id],
        preflight_token=preflight["preflight_token"],
    )
    persisted = get_claim(init_workspace(tmp_path), claim.claim_id)

    assert payload["ok"] is True
    assert payload["kind"] == "trust_update_apply"
    assert payload["applied"] is True
    assert payload["preflight_token"] == preflight["preflight_token"]
    assert persisted.confidence_state == "locally_checked"
    assert validate_trust_update_apply(payload).ok is True


def test_mcp_get_trust_update_record_returns_contract_payload(tmp_path):
    from brain.v5.mcp_tools import (
        aitp_v5_apply_trust_update,
        aitp_v5_get_trust_update_record,
        aitp_v5_preflight_trust_update,
    )
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _seed_claim(tmp_path)
    evidence = _record_validated_evidence(ws, claim)
    preflight = aitp_v5_preflight_trust_update(
        str(tmp_path),
        action="change_claim_confidence",
        session_id="s1",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        requested_state="locally_checked",
        source_kind="execution_brief",
        source_ref="brief:s1",
        evidence_refs=[evidence.evidence_id],
    )
    applied = aitp_v5_apply_trust_update(
        str(tmp_path),
        action="change_claim_confidence",
        session_id="s1",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        requested_state="locally_checked",
        source_kind="execution_brief",
        source_ref="brief:s1",
        evidence_refs=[evidence.evidence_id],
        preflight_token=preflight["preflight_token"],
    )

    record = aitp_v5_get_trust_update_record(str(tmp_path), update_id=applied["trust_update_record_id"])

    assert record["ok"] is True
    assert record["update_id"] == applied["trust_update_record_id"]
    assert require_valid_public_surface("trust_update_record", record) == record


def test_mcp_apply_trust_update_blocks_summary_source(tmp_path):
    from brain.v5.contracts import validate_trust_update_apply
    from brain.v5.mcp_tools import aitp_v5_apply_trust_update
    from brain.v5.workspace import get_claim, init_workspace

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_apply_trust_update(
        str(tmp_path),
        action="change_claim_confidence",
        session_id="s1",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        requested_state="locally_checked",
        source_kind="derived_summary",
        source_ref="findings.md",
    )
    persisted = get_claim(init_workspace(tmp_path), claim.claim_id)

    assert payload["ok"] is True
    assert payload["kind"] == "trust_update_apply"
    assert payload["applied"] is False
    assert persisted.confidence_state == "hypothesis"
    assert validate_trust_update_apply(payload).ok is True
