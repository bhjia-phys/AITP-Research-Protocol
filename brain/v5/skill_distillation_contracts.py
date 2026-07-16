"""Contracts for procedural-only Skill distillation candidates."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import re
from typing import Any, Mapping

from brain.v5.contracts import (
    ContractError,
    ContractResult,
    _require_bool_value,
    _require_list,
    _require_mapping,
    _require_nonempty_str,
)


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_INPUT_KINDS = frozenset(
    {
        "definition",
        "formula",
        "derivation",
        "literature_summary",
        "source_summary",
        "interpretation",
        "insight",
    }
)
_PIN_FIELDS = (
    "recipe_refs",
    "execution_refs",
    "validation_refs",
    "artifact_refs",
    "code_state_refs",
    "environment_refs",
    "source_program_refs",
    "source_refs",
)


def validate_skill_distillation_candidate(
    value: Any,
    *,
    path: str = "skill_distillation_candidate",
) -> ContractResult:
    payload = asdict(value) if is_dataclass(value) else value
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, Mapping):
        return result
    for key in (
        "candidate_id",
        "title",
        "summary",
        "workflow_kind",
        "workflow_signature",
        "transfer_boundary",
        "status",
        "created_at",
        "kind",
    ):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("kind") != "skill_distillation_candidate":
        result.add(f"{path}.kind", "must be 'skill_distillation_candidate'")
    if not _SHA256.fullmatch(str(payload.get("workflow_signature") or "")):
        result.add(f"{path}.workflow_signature", "must be lowercase sha256")
    if payload.get("status") not in {"draft", "reviewed", "rejected", "superseded"}:
        result.add(f"{path}.status", "must be a supported candidate status")
    for key in (
        "input_kinds",
        "source_topic_ids",
        "ordered_steps",
        "inputs",
        "outputs",
        "prerequisites",
        "stop_rules",
        "known_failures",
        "independent_execution_keys",
        "package_requirements",
        *_PIN_FIELDS,
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in (
        "input_kinds",
        "source_topic_ids",
        "ordered_steps",
        "inputs",
        "outputs",
        "prerequisites",
        "stop_rules",
        "known_failures",
        "independent_execution_keys",
        "package_requirements",
        "recipe_refs",
        "execution_refs",
        "validation_refs",
        "artifact_refs",
        "code_state_refs",
        "environment_refs",
    ):
        if isinstance(payload.get(key), list) and not payload[key]:
            result.add(f"{path}.{key}", "must not be empty")
    _require_mapping(payload.get("parameter_contract"), f"{path}.parameter_contract", result)
    _require_mapping(
        payload.get("applicability_selectors"),
        f"{path}.applicability_selectors",
        result,
    )
    if isinstance(payload.get("parameter_contract"), Mapping) and not payload["parameter_contract"]:
        result.add(f"{path}.parameter_contract", "must not be empty")
    if isinstance(payload.get("applicability_selectors"), Mapping) and not payload["applicability_selectors"]:
        result.add(f"{path}.applicability_selectors", "must not be empty")
    forbidden = sorted(set(payload.get("input_kinds") or ()) & _FORBIDDEN_INPUT_KINDS)
    if forbidden:
        result.add(f"{path}.input_kinds", f"semantic kinds must route to M3: {forbidden}")
    _validate_steps(payload.get("ordered_steps"), f"{path}.ordered_steps", result)
    _validate_failures(payload.get("known_failures"), f"{path}.known_failures", result)
    for field in _PIN_FIELDS:
        _validate_pins(payload.get(field), f"{path}.{field}", result)
    for field, expected in (
        ("requires_human_review", True),
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(field), expected, f"{path}.{field}", result)
    return result


def require_valid_skill_distillation_candidate(value: Any):
    result = validate_skill_distillation_candidate(value)
    if not result.ok:
        raise ContractError(result)
    return value


def _validate_pins(value: Any, path: str, result: ContractResult) -> None:
    if not isinstance(value, list):
        return
    for index, pin in enumerate(value):
        item_path = f"{path}[{index}]"
        _require_mapping(pin, item_path, result)
        if not isinstance(pin, Mapping):
            continue
        _require_nonempty_str(pin, "record_ref", item_path, result)
        if not _SHA256.fullmatch(str(pin.get("content_hash") or "")):
            result.add(f"{item_path}.content_hash", "must be lowercase sha256")
        revision = pin.get("revision")
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
            result.add(f"{item_path}.revision", "must be a positive integer")


def _validate_steps(value: Any, path: str, result: ContractResult) -> None:
    if not isinstance(value, list):
        return
    for index, step in enumerate(value):
        item_path = f"{path}[{index}]"
        _require_mapping(step, item_path, result)
        if isinstance(step, Mapping):
            _require_nonempty_str(step, "step_id", item_path, result)
            _require_nonempty_str(step, "action", item_path, result)


def _validate_failures(value: Any, path: str, result: ContractResult) -> None:
    if not isinstance(value, list):
        return
    for index, failure in enumerate(value):
        item_path = f"{path}[{index}]"
        _require_mapping(failure, item_path, result)
        if not isinstance(failure, Mapping):
            continue
        _require_nonempty_str(failure, "failure", item_path, result)
        _require_nonempty_str(failure, "detection", item_path, result)
        _require_list(failure.get("recovery"), f"{item_path}.recovery", result)
        if isinstance(failure.get("recovery"), list) and not failure["recovery"]:
            result.add(f"{item_path}.recovery", "must not be empty")
