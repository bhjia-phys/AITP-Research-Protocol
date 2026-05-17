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
    request = TrustUpdateRequest(
        request_id="trust-req-promote",
        action="promote_to_l2",
        session_id="s1",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        source_kind="execution_brief",
        source_ref="brief:s1",
        evidence_refs=["evidence:si-gw-benchmark"],
        code_state_ids=[code_state.code_state_id],
        rationale="Promotion request cites evidence and exact code provenance.",
    )

    payload = preflight_trust_update(ws, request)

    assert payload["allowed"] is True
    assert payload["mutation_allowed_after_preflight"] is True
    assert payload["required_actions"] == []
    assert payload["code_state_ids"] == [code_state.code_state_id]


def test_apply_confidence_change_updates_registry_and_topic_ledger(tmp_path):
    from brain.v5.contracts import validate_trust_update_apply
    from brain.v5.models import ClaimRecord
    from brain.v5.store import read_record
    from brain.v5.trust_updates import TrustUpdateRequest, apply_trust_update
    from brain.v5.workspace import get_claim

    ws, claim = _seed_claim(tmp_path)
    request = TrustUpdateRequest(
        request_id="trust-req-apply",
        action="change_claim_confidence",
        session_id="s1",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        requested_state="locally_checked",
        source_kind="execution_brief",
        source_ref="brief:s1",
        rationale="A typed kernel brief and evidence review justify the confidence update.",
    )

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
    assert registry_claim.confidence_state == "locally_checked"
    assert ledger_claim.confidence_state == "locally_checked"
    assert validate_trust_update_apply(payload).ok is True


def test_apply_confidence_change_blocks_summary_source_without_mutating(tmp_path):
    from brain.v5.contracts import validate_trust_update_apply
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
    assert validate_trust_update_preflight(payload).ok is True


def test_cli_trust_apply_confidence_change_updates_claim(tmp_path, capsys):
    from brain.v5.contracts import validate_trust_update_apply
    from brain.v5.workspace import get_claim, init_workspace

    _, claim = _seed_claim(tmp_path)

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
        ],
        capsys,
    )

    persisted = get_claim(init_workspace(tmp_path), claim.claim_id)

    assert payload["ok"] is True
    assert payload["kind"] == "trust_update_apply"
    assert payload["applied"] is True
    assert persisted.confidence_state == "locally_checked"
    assert validate_trust_update_apply(payload).ok is True


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
    assert validate_trust_update_preflight(payload).ok is True


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
