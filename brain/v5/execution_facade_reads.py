"""Read-only dispatch for the full M2 execution facade."""

from __future__ import annotations

from typing import Any, Mapping

from brain.v5.compute_run_intake import build_compute_run_intake
from brain.v5.compute_run_intake_contracts import ComputeRunIntakeRequest
from brain.v5.derivation_reviews import project_derivation_status
from brain.v5.effective_attempts import resolve_effective_attempt_state
from brain.v5.execution_baselines import (
    BaselineAcceptanceRequest,
    assess_baseline_readiness,
    project_execution_maturity,
)
from brain.v5.execution_facade_common import coerce_pin, coerce_pins
from brain.v5.execution_scope_policy import assess_execution_scope
from brain.v5.formula_code_contracts import CodeEditCapsuleRequest
from brain.v5.formula_code_map import build_code_edit_execution_capsule
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import get_record_version


def dispatch_execution_read(
    ws: WorkspacePaths,
    operation: str,
    payload: Mapping[str, Any],
) -> Any:
    if operation == "execution_get_record_version":
        return get_record_version(ws, coerce_pin(payload.get("record_ref")))
    if operation == "execution_assess_scope":
        return assess_execution_scope(
            ws,
            operation=str(payload.get("scope_operation") or ""),
            consumer_scope=_strings(payload.get("consumer_scope"), "consumer_scope"),
            dependency_refs=coerce_pins(payload.get("dependency_refs"), "dependency_refs"),
            revalidation_decision_refs=coerce_pins(
                payload.get("revalidation_decision_refs", []),
                "revalidation_decision_refs",
            ),
        )
    if operation == "execution_build_compute_intake":
        return build_compute_run_intake(
            ComputeRunIntakeRequest(_mapping(payload.get("manifest"), "manifest"))
        )
    if operation == "execution_resolve_effective_attempt":
        return resolve_effective_attempt_state(ws, coerce_pin(payload.get("run_ref"), "run_ref"))
    if operation == "execution_assess_baseline_readiness":
        return assess_baseline_readiness(
            ws,
            BaselineAcceptanceRequest(
                run_ref=coerce_pin(payload.get("run_ref"), "run_ref"),
                validation_refs=coerce_pins(
                    payload.get("validation_refs", []),
                    "validation_refs",
                ),
            ),
        )
    if operation == "execution_project_maturity":
        return project_execution_maturity(ws, coerce_pin(payload.get("run_ref"), "run_ref"))
    if operation == "execution_build_formula_code_capsule":
        relation_ref = coerce_pin(payload.get("relation_ref"), "relation_ref")
        capsule = build_code_edit_execution_capsule(
            ws,
            CodeEditCapsuleRequest(
                relation_ref=relation_ref,
                topic_id=str(payload.get("topic_id") or ""),
                claim_id=str(payload.get("claim_id") or ""),
                revalidation_decision_refs=coerce_pins(
                    payload.get("revalidation_decision_refs", []),
                    "revalidation_decision_refs",
                ),
            ),
        )
        return {
            **capsule,
            "relation_ref": {
                "record_ref": relation_ref.record_ref,
                "content_hash": relation_ref.content_hash,
                "revision": relation_ref.revision,
            },
            "ready_for_edit": bool(capsule.get("can_execute_edit")),
        }
    if operation == "execution_project_derivation_status":
        chain_ref = coerce_pin(payload.get("chain_ref"), "chain_ref")
        projection = project_derivation_status(ws, chain_ref)
        return {
            **projection.__dict__,
            "requested_chain_ref": {
                "record_ref": chain_ref.record_ref,
                "content_hash": chain_ref.content_hash,
                "revision": chain_ref.revision,
            },
        }
    raise ValueError(f"unsupported execution read operation: {operation}")


def _mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def _strings(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field_name} must contain non-empty strings")
    return tuple(value)
