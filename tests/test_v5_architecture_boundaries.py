from __future__ import annotations

from pathlib import Path


MAX_V5_SOURCE_MODULE_LINES = 500


def test_v5_source_modules_stay_bounded():
    repo_root = Path(__file__).resolve().parents[1]
    source_root = repo_root / "brain" / "v5"

    oversized = {}
    for module_path in sorted(source_root.glob("*.py")):
        line_count = len(module_path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_V5_SOURCE_MODULE_LINES:
            oversized[module_path.name] = line_count

    assert oversized == {}


def test_cli_adapter_dispatch_lives_in_focused_module():
    import brain.v5.cli_adapters as cli_adapters

    repo_root = Path(__file__).resolve().parents[1]
    cli_path = repo_root / "brain" / "v5" / "cli.py"

    assert hasattr(cli_adapters, "dispatch_adapter_command")
    assert len(cli_path.read_text(encoding="utf-8").splitlines()) <= 480


def test_hook_install_template_module_stays_renderer_free():
    repo_root = Path(__file__).resolve().parents[1]
    template_path = repo_root / "brain" / "v5" / "hook_install_templates.py"

    assert len(template_path.read_text(encoding="utf-8").splitlines()) <= 450


def test_trust_update_contracts_live_behind_contracts_facade():
    import brain.v5.contracts as contracts
    from brain.v5 import trust_contracts

    invalid_payload = {
        "kind": "trust_update_preflight",
        "request": {},
        "request_id": "",
        "action": "",
        "session_id": "",
        "topic_id": "",
        "claim_id": "",
        "allowed": False,
        "mutation_allowed_after_preflight": False,
        "policy_reasons": [],
        "required_actions": [],
        "evidence_refs": [],
        "code_state_ids": [],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
    }

    facade_result = contracts.validate_trust_update_preflight(invalid_payload)
    focused_result = trust_contracts.validate_trust_update_preflight(invalid_payload)

    assert [issue.path for issue in facade_result.issues] == [
        issue.path for issue in focused_result.issues
    ]


def test_risk_contracts_live_behind_contracts_facade():
    import brain.v5.contracts as contracts
    from brain.v5 import risk_contracts

    invalid_payload = {
        "level": "fluid",
        "score": -1,
        "signals": [
            {
                "kind": "finite_size",
                "severity": 0,
                "reason": "",
                "evidence_ref": "",
                "suggested_action": "",
            }
        ],
        "action_budget": {
            "level": "guided",
            "max_questions": 4,
            "required_outputs": [""],
            "allowed_actions": [""],
            "requires_human_checkpoint": "no",
        },
        "human_checkpoint_needed": "no",
        "summary": "",
    }

    facade_result = contracts.validate_risk_assessment(invalid_payload)
    focused_result = risk_contracts.validate_risk_assessment(invalid_payload)

    assert [issue.path for issue in facade_result.issues] == [
        issue.path for issue in focused_result.issues
    ]
