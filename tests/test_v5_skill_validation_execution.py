from __future__ import annotations

import json

import pytest


def test_builtin_declarative_validator_parses_fixture_without_executing_code(tmp_path):
    from brain.v5.skill_validation_execution import validate_staged_skill_package

    marker = tmp_path / "must-not-exist"
    files = {
        "SKILL.md": b"# Test\n",
        "tests/smoke.json": json.dumps(
            {
                "validator_id": "aitp-pinned-validation-replay",
                "expected_status": "passed",
                "network": "forbidden",
                "writes": [],
                "payload": f"$(New-Item {marker})",
            }
        ).encode("utf-8"),
    }
    commands = [
        {
            "kind": "aitp_builtin_declarative",
            "validator_id": "aitp-pinned-validation-replay",
            "fixture": "tests/smoke.json",
            "network": "forbidden",
            "writes": [],
            "timeout_seconds": 30,
        }
    ]

    result = validate_staged_skill_package(files, commands)

    assert result[0]["status"] == "passed"
    assert result[0]["execution_mode"] == "declarative_parse_only"
    assert not marker.exists()


@pytest.mark.parametrize(
    "mutation, match",
    [
        ({"network": "allowed"}, "network"),
        ({"writes": ["."]}, "writes"),
        ({"timeout_seconds": 0}, "timeout"),
    ],
)
def test_builtin_validator_rejects_effectful_policy(mutation, match):
    from brain.v5.skill_validation_execution import validate_staged_skill_package

    files = {
        "SKILL.md": b"# Test\n",
        "tests/smoke.json": b'{"validator_id":"safe","expected_status":"passed","network":"forbidden","writes":[]}',
    }
    command = {
        "kind": "aitp_builtin_declarative",
        "validator_id": "safe",
        "fixture": "tests/smoke.json",
        "network": "forbidden",
        "writes": [],
        "timeout_seconds": 30,
        **mutation,
    }

    with pytest.raises(ValueError, match=match):
        validate_staged_skill_package(files, [command])


def test_arbitrary_command_becomes_m2_request_and_is_never_executed(tmp_path):
    from brain.v5.skill_validation_execution import classify_skill_validation_policy

    marker = tmp_path / "must-not-exist"
    request = classify_skill_validation_policy(
        [
            {
                "kind": "shell",
                "command": f"New-Item {marker}",
                "network": "forbidden",
                "writes": [],
                "timeout_seconds": 30,
            }
        ]
    )

    assert request.requires_m2_execution is True
    assert request.risk_class == "high"
    assert request.can_execute is False
    assert not marker.exists()
