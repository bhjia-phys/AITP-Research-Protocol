from __future__ import annotations


def test_pre_tool_use_allows_and_logs_by_default():
    from brain.v5.hooks import decide_pre_tool_use
    from brain.v5.policy import PolicyDecision

    decision = decide_pre_tool_use(
        action="run_toy_numeric_check",
        risk_level="guided",
        policy_decision=PolicyDecision(allowed=True, action="run_toy_numeric_check"),
    )

    assert decision.block is False
    assert decision.mode == "log"
    assert "logged" in decision.message
    assert len(decision.message) <= 160


def test_pre_tool_use_blocks_high_risk_policy_violation():
    from brain.v5.hooks import decide_pre_tool_use
    from brain.v5.models import ClaimRecord
    from brain.v5.policy import evaluate_policy

    claim = ClaimRecord(
        claim_id="claim-promote",
        topic_id="fqhe",
        statement="Promote this claim to L2.",
        evidence_profile="toy_numeric",
        confidence_state="locally_checked",
        active_uncertainty="ready for memory",
    )
    policy = evaluate_policy(action="promote_to_l2", claim=claim, evidence_refs=[])

    decision = decide_pre_tool_use(
        action="promote_to_l2",
        risk_level="adversarial",
        policy_decision=policy,
    )

    assert decision.block is True
    assert decision.mode == "block"
    assert "attach_evidence_ref" in decision.required_actions
    assert len(decision.message) <= 160


def test_guided_noncritical_policy_issue_warns_not_blocks():
    from brain.v5.hooks import decide_pre_tool_use
    from brain.v5.models import ClaimRecord
    from brain.v5.policy import evaluate_policy

    claim = ClaimRecord(
        claim_id="claim-code",
        topic_id="librpa-gw",
        statement="Check a code-method result.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="code state not recorded yet",
    )
    policy = evaluate_policy(action="validate_claim", claim=claim, code_states=[])

    decision = decide_pre_tool_use(
        action="validate_claim",
        risk_level="guided",
        policy_decision=policy,
    )

    assert decision.block is False
    assert decision.mode == "warn"
    assert "record_code_state" in decision.required_actions


def test_pre_tool_use_hard_blocks_summary_based_trust_update_even_when_guided():
    from brain.v5.hooks import decide_pre_tool_use
    from brain.v5.policy import evaluate_policy

    policy = evaluate_policy(
        action="change_claim_confidence",
        context={"source_kind": "derived_summary", "orientation_only": True},
    )

    decision = decide_pre_tool_use(
        action="change_claim_confidence",
        risk_level="guided",
        policy_decision=policy,
    )

    assert decision.block is True
    assert decision.mode == "block"
    assert "query_execution_brief_or_typed_record" in decision.required_actions
    assert "summary" in decision.message


def test_post_tool_use_creates_short_trace_event():
    from brain.v5.hooks import post_tool_use_trace_event

    event = post_tool_use_trace_event(
        session_id="s1",
        topic_id="fqhe",
        risk_level="guided",
        claim_id="claim-fqhe",
        tool_name="exact-diagonalization",
        evidence_status="supports",
    )

    assert event.event_type == "tool_run_recorded"
    assert event.payload["tool_name"] == "exact-diagonalization"
    assert len(event.payload["summary"]) <= 120


def test_pre_commit_harness_patch_requires_tests_and_evolution_note():
    from brain.v5.hooks import decide_pre_commit

    blocked = decide_pre_commit(
        changed_files=["brain/v5/policy.py"],
        test_refs=[],
        evolution_note="",
    )
    allowed = decide_pre_commit(
        changed_files=["brain/v5/policy.py", "tests/test_v5_policy.py"],
        test_refs=["tests/test_v5_policy.py"],
        evolution_note="tighten policy after repeated incident",
    )

    assert blocked.block is True
    assert "add_regression_test" in blocked.required_actions
    assert "add_evolution_note" in blocked.required_actions
    assert allowed.block is False
    assert allowed.mode == "log"


def test_hook_adapter_payload_is_short_json_friendly():
    from brain.v5.hook_adapters import hook_decision_payload
    from brain.v5.hooks import decide_pre_commit

    decision = decide_pre_commit(
        changed_files=["brain/v5/policy.py"],
        test_refs=[],
        evolution_note="",
    )

    payload = hook_decision_payload(decision, hook_name="pre_commit")

    assert payload == {
        "kind": "hook_decision",
        "hook_name": "pre_commit",
        "mode": "block",
        "block": True,
        "message": "blocked harness commit; required: add_regression_test, add_evolution_note",
        "required_actions": ["add_regression_test", "add_evolution_note"],
        "exit_code": 2,
        "summary_inputs_trusted": False,
    }
    assert len(payload["message"]) <= 160


def test_v5_hook_script_pre_commit_blocks_harness_change_without_tests():
    import json
    import subprocess
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "hooks" / "aitp_v5_hook.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "pre-commit",
            "--changed-file",
            "brain/v5/policy.py",
        ],
        capture_output=True,
        encoding="utf-8",
        check=False,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 2
    assert payload["kind"] == "hook_decision"
    assert payload["hook_name"] == "pre_commit"
    assert payload["block"] is True
    assert payload["required_actions"] == ["add_regression_test", "add_evolution_note"]


def test_v5_hook_script_pre_tool_blocks_from_policy_json():
    import json
    import subprocess
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "hooks" / "aitp_v5_hook.py"
    policy_json = json.dumps({
        "allowed": False,
        "action": "promote_to_l2",
        "reasons": [
            {
                "policy_id": "no_l2_promotion_without_evidence_ref",
                "message": "L2 promotion requires evidence.",
                "severity": "block",
            }
        ],
        "required_actions": ["attach_evidence_ref"],
    })

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "pre-tool",
            "--action",
            "promote_to_l2",
            "--risk-level",
            "adversarial",
            "--policy-json",
            policy_json,
        ],
        capture_output=True,
        encoding="utf-8",
        check=False,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 2
    assert payload["kind"] == "hook_decision"
    assert payload["hook_name"] == "pre_tool"
    assert payload["block"] is True
    assert payload["required_actions"] == ["attach_evidence_ref"]
    assert payload["summary_inputs_trusted"] is False
