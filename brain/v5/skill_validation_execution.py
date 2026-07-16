"""No-execution validation policy for reviewed AITP-generated Skill packages."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from brain.v5.project_skill_contracts import canonical_package_path
from brain.v5.skill_models import SkillValidationExecutionRequest


_BUILTIN_KIND = "aitp_builtin_declarative"


def classify_skill_validation_policy(
    commands: Sequence[Mapping[str, Any]],
) -> SkillValidationExecutionRequest:
    normalized = tuple(_normalized_command(command) for command in commands)
    external = any(command["kind"] != _BUILTIN_KIND for command in normalized)
    timeout = max((command["timeout_seconds"] for command in normalized), default=0)
    writable = tuple(sorted({
        str(path)
        for command in normalized
        for path in command.get("writes", [])
    }))
    network = "forbidden" if all(
        command.get("network") == "forbidden" for command in normalized
    ) else "requested"
    return SkillValidationExecutionRequest(
        command_digest=_sha256_json(list(normalized)),
        commands=normalized,
        requires_m2_execution=external,
        risk_class="high" if external else "none",
        network_policy=network,
        writable_roots=writable,
        environment_allowlist=(),
        timeout_seconds=timeout,
    )


def validate_staged_skill_package(
    files: Mapping[str, bytes],
    commands: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Parse built-in fixtures only; never invoke project or package code."""

    policy = classify_skill_validation_policy(commands)
    if policy.requires_m2_execution:
        raise ValueError("arbitrary validation commands require an M2 high-risk execution request")
    results: list[dict[str, Any]] = []
    for command in policy.commands:
        if command["network"] != "forbidden":
            raise ValueError("built-in Skill validation network must be forbidden")
        if command["writes"] != []:
            raise ValueError("built-in Skill validation writes must be empty")
        if command["timeout_seconds"] < 1 or command["timeout_seconds"] > 300:
            raise ValueError("built-in Skill validation timeout must be between 1 and 300 seconds")
        fixture_path = canonical_package_path(str(command.get("fixture") or ""))
        try:
            fixture_bytes = files[fixture_path]
            fixture = json.loads(fixture_bytes.decode("utf-8"))
        except (KeyError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("built-in Skill validation fixture is missing or invalid") from exc
        if not isinstance(fixture, dict):
            raise ValueError("built-in Skill validation fixture must be an object")
        if fixture.get("validator_id") != command.get("validator_id"):
            raise ValueError("built-in Skill validation fixture validator_id does not match")
        if fixture.get("network") != "forbidden" or fixture.get("writes") != []:
            raise ValueError("built-in Skill validation fixture must forbid network and writes")
        if fixture.get("expected_status") != "passed":
            raise ValueError("built-in Skill validation fixture must declare expected_status passed")
        results.append(
            {
                "validator_id": command["validator_id"],
                "fixture": fixture_path,
                "fixture_hash": hashlib.sha256(fixture_bytes).hexdigest(),
                "status": "passed",
                "execution_mode": "declarative_parse_only",
                "network": "forbidden",
                "writes": [],
            }
        )
    return results


def _normalized_command(command: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(command, Mapping):
        raise TypeError("Skill validation command must be a mapping")
    timeout = command.get("timeout_seconds", 0)
    if isinstance(timeout, bool) or not isinstance(timeout, int):
        raise ValueError("Skill validation timeout must be an integer")
    writes = command.get("writes", [])
    if not isinstance(writes, list) or not all(isinstance(item, str) for item in writes):
        raise ValueError("Skill validation writes must be a string list")
    return {
        key: value
        for key, value in {
            **dict(command),
            "kind": str(command.get("kind") or ""),
            "network": str(command.get("network") or ""),
            "writes": list(writes),
            "timeout_seconds": timeout,
        }.items()
    }


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "classify_skill_validation_policy",
    "validate_staged_skill_package",
]
