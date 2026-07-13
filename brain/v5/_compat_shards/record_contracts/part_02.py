# Compatibility shard 2 for record_contracts.
from __future__ import annotations

import re

def validate_research_run_event_record(
    payload: dict[str, Any],
    *,
    path: str = "research_run_event_record",
) -> ContractResult:
    result = _validate_base_record(payload, path, kind="research_run_event")
    if result.issues:
        return result
    for key in ("event_id", "run_id", "topic_id", "operator", "event_type", "summary", "status"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("event_type") not in {
        "run_started",
        "context_refreshed",
        "action_selected",
        "action_started",
        "action_completed",
        "operator_checkpoint",
        "status_changed",
        "answer_drafted",
        "answer_finalized",
        "blocked",
        "run_stopped",
    }:
        result.add(f"{path}.event_type", "must be a known research-run event type")
    if payload.get("status") not in {"recorded", "blocked", "failed", "superseded"}:
        result.add(f"{path}.status", "must be recorded, blocked, failed, or superseded")
    phase = payload.get("phase")
    if phase and phase not in {
        "planning",
        "context_refresh",
        "action_selection",
        "source_review",
        "validation",
        "answer_drafting",
        "awaiting_approval",
        "blocked",
        "complete",
    }:
        result.add(f"{path}.phase", "must be empty or a known research-run phase")
    for key in ("source_refs", "evidence_refs", "validation_refs", "artifact_refs"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("payload"), f"{path}.payload", result)
    for key, expected in (
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", True),
        ("can_update_claim_trust", False),
    ):
        if payload.get(key) is not expected:
            result.add(f"{path}.{key}", f"must be {str(expected).lower()}")
    return result

def require_valid_research_run_event_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_research_run_event_record(payload), payload)

def validate_validation_contract_record(payload: dict[str, Any], *, path: str = "validation_contract_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="validation_contract")
    if result.issues:
        return result
    for key in ("contract_id", "topic_id", "claim_id", "validator_role", "status"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("required_checks", "failure_modes", "required_evidence_outputs"):
        lst = payload.get(key)
        _require_list(lst, f"{path}.{key}", result)
        if isinstance(lst, list) and len(lst) == 0:
            result.add(f"{path}.{key}", "must not be empty — validation requires explicit failure hypotheses")
    for key in ("tool_recipe_ids", "executor_ids"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    return result

def require_valid_validation_contract_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_validation_contract_record(payload), payload)

def validate_validation_result_record(payload: dict[str, Any], *, path: str = "validation_result_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="validation_result")
    if result.issues:
        return result
    for key in ("result_id", "topic_id", "claim_id", "contract_id", "tool_run_id", "status", "summary"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("status") not in {"passed", "failed", "inconclusive", "partial"}:
        result.add(f"{path}.status", "must be passed, failed, inconclusive, or partial")
    for key in ("checked_outputs", "missing_outputs", "covered_failure_modes", "failure_modes_observed", "evidence_refs", "artifact_ids"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if payload.get("status") == "passed" and payload.get("missing_outputs"):
        result.add(f"{path}.missing_outputs", "must be empty when status is passed")
    if payload.get("status") == "passed" and payload.get("failure_modes_observed"):
        result.add(f"{path}.failure_modes_observed", "must be empty when status is passed")
    return result

def require_valid_validation_result_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_validation_result_record(payload), payload)

def validate_human_checkpoint_record(payload: dict[str, Any], *, path: str = "human_checkpoint_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="human_checkpoint")
    if result.issues:
        return result
    for key in ("checkpoint_id", "topic_id", "claim_id", "reason", "requested_by"):
        _require_nonempty_str(payload, key, path, result)
    options = payload.get("options")
    _require_list(options, f"{path}.options", result)
    if isinstance(options, list) and len(options) == 0:
        result.add(f"{path}.options", "must not be empty — checkpoint requires at least one option")
    status = payload.get("status")
    if status not in ("open", "decided"):
        result.add(f"{path}.status", "must be 'open' or 'decided'")
    decision_verified = payload.get("decision_verified", False)
    can_authorize_trust = payload.get("can_authorize_trust", False)
    for key, value in (
        ("decision_verified", decision_verified),
        ("can_authorize_trust", can_authorize_trust),
    ):
        if not isinstance(value, bool):
            result.add(f"{path}.{key}", "must be boolean")
    for key in ("decision_verification", "decision_receipt_hash", "decision_receipt_nonce"):
        if not isinstance(payload.get(key, ""), str):
            result.add(f"{path}.{key}", "must be a string")
    if status == "open" and (decision_verified is True or can_authorize_trust is True):
        result.add(f"{path}.can_authorize_trust", "must be false while checkpoint is open")
    if status == "decided":
        for key in ("decision", "rationale", "decided_by"):
            _require_nonempty_str(payload, key, path, result)
        if isinstance(options, list) and isinstance(payload.get("decision"), str) and payload["decision"] not in options:
            result.add(f"{path}.decision", f"must be one of options {options}")
        if can_authorize_trust is True and decision_verified is not True:
            result.add(f"{path}.can_authorize_trust", "requires decision_verified=true")
        if decision_verified is True:
            for key in ("decision_verification", "decision_receipt_hash", "decision_receipt_nonce"):
                _require_nonempty_str(payload, key, path, result)
            if payload.get("decision_verification") != "hmac_sha256_v1":
                result.add(f"{path}.decision_verification", "must be hmac_sha256_v1")
            receipt_hash = payload.get("decision_receipt_hash")
            if not isinstance(receipt_hash, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", receipt_hash):
                result.add(f"{path}.decision_receipt_hash", "must be a sha256-prefixed lowercase digest")
    return result

def require_valid_human_checkpoint_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_human_checkpoint_record(payload), payload)

def validate_failure_mode_review_result_record(
    payload: dict[str, Any], *, path: str = "failure_mode_review_result_record"
) -> ContractResult:
    result = _validate_base_record(payload, path, kind="failure_mode_review_result")
    if result.issues:
        return result
    for key in ("result_id", "topic_id", "claim_id", "checkpoint_id", "status", "reviewer_role", "summary"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("status") not in {"passed", "needs_revision", "inconclusive"}:
        result.add(f"{path}.status", "must be passed, needs_revision, or inconclusive")
    for key in (
        "reviewed_failure_modes",
        "basis_refs",
        "evidence_refs",
        "validation_result_ids",
        "tool_run_ids",
        "reference_location_ids",
        "artifact_ids",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if isinstance(payload.get("reviewed_failure_modes"), list) and len(payload["reviewed_failure_modes"]) == 0:
        result.add(f"{path}.reviewed_failure_modes", "must not be empty")
    basis_keys = ("basis_refs", "evidence_refs", "validation_result_ids", "tool_run_ids", "reference_location_ids", "artifact_ids")
    if all(isinstance(payload.get(key), list) and len(payload[key]) == 0 for key in basis_keys):
        result.add(f"{path}.basis_refs", "review basis must cite at least one typed/literature/tool reference")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    return result

def require_valid_failure_mode_review_result_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_failure_mode_review_result_record(payload), payload)

def validate_promotion_packet_record(payload: dict[str, Any], *, path: str = "promotion_packet_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="promotion_packet")
    if result.issues:
        return result
    for key in ("packet_id", "topic_id", "claim_id", "proposed_memory_kind", "scope"):
        _require_nonempty_str(payload, key, path, result)
    evidence = payload.get("evidence_refs")
    _require_list(evidence, f"{path}.evidence_refs", result)
    if isinstance(evidence, list) and len(evidence) == 0:
        result.add(f"{path}.evidence_refs", "must not be empty — promotion requires evidence")
    _require_list(payload.get("validation_result_ids"), f"{path}.validation_result_ids", result)
    failure_modes = payload.get("known_failure_modes")
    _require_list(failure_modes, f"{path}.known_failure_modes", result)
    if isinstance(failure_modes, list) and len(failure_modes) == 0:
        result.add(f"{path}.known_failure_modes", "must not be empty — promotion requires known failure modes")
    for key in ("failure_mode_review_checkpoint_id", "failure_mode_review_result_id"):
        if not isinstance(payload.get(key, ""), str):
            result.add(f"{path}.{key}", "must be a string")
    return result

def require_valid_promotion_packet_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_promotion_packet_record(payload), payload)

def validate_memory_entry_record(payload: dict[str, Any], *, path: str = "memory_entry_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="memory_entry")
    if result.issues:
        return result
    for key in (
        "entry_id",
        "topic_id",
        "source_claim_id",
        "source_topic_id",
        "statement",
        "memory_kind",
        "scope",
        "source_packet_id",
        "human_checkpoint_id",
        "status",
    ):
        _require_nonempty_str(payload, key, path, result)
    evidence = payload.get("evidence_refs")
    _require_list(evidence, f"{path}.evidence_refs", result)
    if isinstance(evidence, list) and len(evidence) == 0:
        result.add(f"{path}.evidence_refs", "must not be empty — memory entries require evidence")
    _require_list(payload.get("validation_result_ids"), f"{path}.validation_result_ids", result)
    for key in ("non_claims", "known_failure_modes"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in ("failure_mode_review_checkpoint_id", "failure_mode_review_result_id"):
        if not isinstance(payload.get(key, ""), str):
            result.add(f"{path}.{key}", "must be a string")
    return result

def require_valid_memory_entry_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_memory_entry_record(payload), payload)

def validate_lifecycle_event_record(payload: dict[str, Any], *, path: str = "lifecycle_event_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="lifecycle_event")
    if result.issues:
        return result
    for key in ("event_id", "event_type", "subject_record_id", "subject_kind", "lifecycle_status", "reason", "operator", "timestamp"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("event_type") not in {"rehome", "supersede"}:
        result.add(f"{path}.event_type", "must be rehome or supersede")
    if payload.get("subject_kind") not in {"claim", "evidence", "tool_run", "session"}:
        result.add(f"{path}.subject_kind", "must be claim, evidence, tool_run, or session")
    if payload.get("event_type") == "rehome" and not payload.get("to_topic"):
        result.add(f"{path}.to_topic", "must be non-empty for rehome events")
    valid_status = {"active", "misrouted", "voided", "superseded", "duplicate", "rehomed"}
    if payload.get("lifecycle_status") not in valid_status:
        result.add(f"{path}.lifecycle_status", "must be a known lifecycle status")
    return result

def require_valid_lifecycle_event_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_lifecycle_event_record(payload), payload)

def validate_trust_update_record(payload: dict[str, Any], *, path: str = "trust_update_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="trust_update")
    if result.issues:
        return result
    for key in ("update_id", "request_id", "action", "session_id", "topic_id", "claim_id", "previous_state", "new_state", "status", "preflight_token"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("status") not in {"applied", "blocked"}:
        result.add(f"{path}.status", "must be 'applied' or 'blocked'")
    for key in ("applied", "preflight_allowed"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    if payload.get("applied") is True and payload.get("status") != "applied":
        result.add(f"{path}.status", "must be 'applied' when applied is true")
    if payload.get("applied") is False and payload.get("status") != "blocked":
        result.add(f"{path}.status", "must be 'blocked' when applied is false")
    for key in ("evidence_refs", "code_state_ids", "required_actions", "policy_reason_ids"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    return result

def require_valid_trust_update_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_trust_update_record(payload), payload)

def _validate_base_record(payload: Any, path: str, *, kind: str) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != kind:
        result.add(f"{path}.kind", f"must be {kind!r}")
    return result

def _require_valid(result: ContractResult, payload: dict[str, Any]) -> dict[str, Any]:
    if not result.ok:
        raise ContractError(result)
    return payload
