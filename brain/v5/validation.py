"""Validation contract records for AITP v5."""

from __future__ import annotations

from brain.v5.ids import prefixed_id
from brain.v5.models import ToolRunRecord, ValidationContractRecord, ValidationResultRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_records, write_record


def create_validation_contract(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str,
    required_checks: list[str] | None = None,
    failure_modes: list[str] | None = None,
    required_evidence_outputs: list[str] | None = None,
    tool_recipe_ids: list[str] | None = None,
    executor_ids: list[str] | None = None,
    validator_role: str = "adversarial_reviewer",
) -> ValidationContractRecord:
    contract_id = prefixed_id(
        "validation-contract",
        f"{topic_id}:{claim_id}:{validator_role}",
        max_slug=64,
    )
    record = ValidationContractRecord(
        contract_id=contract_id,
        topic_id=topic_id,
        claim_id=claim_id,
        required_checks=required_checks or [],
        failure_modes=failure_modes or [],
        required_evidence_outputs=required_evidence_outputs or [],
        tool_recipe_ids=tool_recipe_ids or [],
        executor_ids=executor_ids or [],
        validator_role=validator_role,
    )
    write_record(
        ws.registry_dir("validation_contracts") / f"{contract_id}.md",
        record,
        body=f"# Validation Contract: {contract_id}\n\n"
        f"Required checks: {', '.join(record.required_checks)}\n"
        f"Failure modes: {', '.join(record.failure_modes)}\n"
        f"Tool recipes: {', '.join(record.tool_recipe_ids)}\n"
        f"Executors: {', '.join(record.executor_ids)}\n",
    )
    return record


def record_validation_result(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str,
    contract_id: str,
    tool_run_id: str,
    status: str,
    checked_outputs: list[str] | None = None,
    summary: str = "",
    evidence_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    failure_modes_observed: list[str] | None = None,
) -> ValidationResultRecord:
    """Record whether a tool run satisfied a typed validation contract."""

    clean_status = status.strip().lower()
    if clean_status not in {"passed", "failed", "inconclusive"}:
        raise ValueError("validation result status must be passed, failed, or inconclusive")
    if not summary.strip():
        raise ValueError("validation result summary must not be empty")
    contract = _find_contract(ws, contract_id)
    if contract.topic_id != topic_id or contract.claim_id != claim_id:
        raise ValueError("validation contract must belong to the same topic and claim")
    run = _find_tool_run(ws, tool_run_id)
    if run.topic_id != topic_id or run.claim_id != claim_id:
        raise ValueError("tool run must belong to the same topic and claim")
    checked = checked_outputs or []
    missing = [output for output in contract.required_evidence_outputs if output not in checked]
    failures = failure_modes_observed or []
    if clean_status == "passed" and missing:
        raise ValueError(f"missing required evidence outputs: {', '.join(missing)}")
    if clean_status == "passed" and failures:
        raise ValueError("passed validation result cannot include observed failure modes")
    result_id = prefixed_id(
        "validation-result",
        f"{topic_id}:{claim_id}:{contract_id}:{tool_run_id}:{clean_status}:{checked}",
        max_slug=72,
    )
    record = ValidationResultRecord(
        result_id=result_id,
        topic_id=topic_id,
        claim_id=claim_id,
        contract_id=contract_id,
        tool_run_id=tool_run_id,
        status=clean_status,
        checked_outputs=checked,
        missing_outputs=missing,
        failure_modes_observed=failures,
        evidence_refs=evidence_refs or [],
        artifact_ids=artifact_ids or [],
        summary=summary,
    )
    write_record(
        ws.registry_dir("validation_results") / f"{result_id}.md",
        record,
        body=f"# Validation Result: {result_id}\n\n"
        f"Status: {clean_status}\n"
        f"Summary: {summary}\n",
    )
    return record


def _find_contract(ws: WorkspacePaths, contract_id: str) -> ValidationContractRecord:
    for record in list_records(ws.registry_dir("validation_contracts"), ValidationContractRecord):
        if record.contract_id == contract_id:
            return record
    raise ValueError(f"validation contract not found: {contract_id}")


def _find_tool_run(ws: WorkspacePaths, tool_run_id: str) -> ToolRunRecord:
    for record in list_records(ws.registry_dir("tool_runs"), ToolRunRecord):
        if record.run_id == tool_run_id:
            return record
    raise ValueError(f"tool run not found: {tool_run_id}")
