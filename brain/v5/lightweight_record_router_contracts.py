"""Contract for the lightweight record write plan surface.

The plan surface is strictly read-only / orientation-only. This contract enforces
the hard trust boundaries from the spec and the structural requirements of each
plan item. It never approves a payload that could update claim trust.
"""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_list, _require_mapping


_DECISIONS = {"no_write", "plan_write", "needs_human_target_claim", "unsupported"}


def validate_lightweight_record_write_plan(
    payload: dict[str, Any],
    *,
    path: str = "lightweight_record_write_plan",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result

    if payload.get("kind") != "lightweight_record_write_plan":
        result.add(f"{path}.kind", "must be 'lightweight_record_write_plan'")

    if payload.get("decision") not in _DECISIONS:
        result.add(f"{path}.decision", "must be one of no_write/plan_write/needs_human_target_claim/unsupported")

    for key in ("typed_write_plan", "selected_record_types", "write_reasons"):
        _require_list(payload.get(key), f"{path}.{key}", result)

    # trust boundary block must forbid claim-trust updates
    boundary = payload.get("trust_boundary")
    _require_mapping(boundary, f"{path}.trust_boundary", result)
    if isinstance(boundary, dict) and boundary.get("can_update_claim_trust") is not False:
        result.add(f"{path}.trust_boundary.can_update_claim_trust", "must be false")

    _require_read_only(payload, path, result)

    decision = payload.get("decision")
    plan = payload.get("typed_write_plan")

    if decision == "no_write":
        if plan != []:
            result.add(f"{path}.typed_write_plan", "must be empty for no_write")
        if not str(payload.get("no_write_reason", "")).strip():
            result.add(f"{path}.no_write_reason", "must be non-empty for no_write")

    if decision == "plan_write":
        target = payload.get("target_claim")
        _require_mapping(target, f"{path}.target_claim", result)
        if isinstance(target, dict) and not str(target.get("target_claim_id", "")).strip():
            result.add(f"{path}.target_claim.target_claim_id", "must be non-empty for plan_write")
        if not payload.get("selected_record_types"):
            result.add(f"{path}.selected_record_types", "must be non-empty for plan_write")
        if not plan:
            result.add(f"{path}.typed_write_plan", "must be non-empty for plan_write")

    if isinstance(plan, list):
        for index, item in enumerate(plan):
            _validate_plan_item(item, f"{path}.typed_write_plan[{index}]", result)

    return result


def require_valid_lightweight_record_write_plan(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_lightweight_record_write_plan(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


# --------------------------------------------------------------------------- #
# internal helpers
# --------------------------------------------------------------------------- #

def _validate_plan_item(item: Any, path: str, result: ContractResult) -> None:
    _require_mapping(item, path, result)
    if not isinstance(item, dict):
        return
    for key in ("record_type", "target_claim_id", "summary", "recommended_mcp_tool"):
        if not isinstance(item.get(key), str) or not str(item.get(key, "")).strip():
            result.add(f"{path}.{key}", "must be a non-empty string")
    _require_mapping(item.get("required_fields"), f"{path}.required_fields", result)
    _require_list(item.get("verification_refs"), f"{path}.verification_refs", result)
    if item.get("execute_now") is not False:
        result.add(f"{path}.execute_now", "must be false (plan-only surface)")


def _require_read_only(payload: dict[str, Any], path: str, result: ContractResult) -> None:
    if payload.get("truth_source") != "event_metadata_and_typed_records":
        result.add(f"{path}.truth_source", "must be event_metadata_and_typed_records")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("can_update_kernel_state") is not False:
        result.add(f"{path}.can_update_kernel_state", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
