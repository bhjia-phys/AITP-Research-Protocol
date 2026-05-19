"""Safe built-in tool executors that materialize ToolRunRecord outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from brain.v5.evidence import record_evidence
from brain.v5.models import EvidenceRecord, ToolRunRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.tools import record_tool_run


@dataclass(frozen=True)
class ToolExecutorSpec:
    executor_id: str
    tool_family: str
    tool_name: str
    execution_mode: str
    version: str
    run: Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class ToolExecutionResult:
    run: ToolRunRecord
    evidence: EvidenceRecord | None = None


def builtin_tool_executors() -> dict[str, ToolExecutorSpec]:
    """Return deterministic in-process executors available without shell access."""

    spec = ToolExecutorSpec(
        executor_id="scalar_tolerance_check",
        tool_family="sanity_check",
        tool_name="scalar_tolerance_check",
        execution_mode="safe_builtin",
        version="1",
        run=_run_scalar_tolerance_check,
    )
    return {spec.executor_id: spec}


def execute_registered_tool(
    ws: WorkspacePaths,
    *,
    executor_id: str,
    recipe_id: str,
    topic_id: str,
    claim_id: str,
    inputs: dict[str, Any],
    evidence_status: str = "",
    code_state_ids: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    source_refs: list[str] | None = None,
    supports_outputs: list[str] | None = None,
    evidence_type: str = "tool_run",
    evidence_summary: str = "",
) -> ToolRunRecord:
    """Execute a safe built-in tool and record its provenance as a ToolRunRecord."""

    return execute_registered_tool_result(
        ws,
        executor_id=executor_id,
        recipe_id=recipe_id,
        topic_id=topic_id,
        claim_id=claim_id,
        inputs=inputs,
        evidence_status=evidence_status,
        code_state_ids=code_state_ids,
        artifact_ids=artifact_ids,
        source_refs=source_refs,
        supports_outputs=supports_outputs,
        evidence_type=evidence_type,
        evidence_summary=evidence_summary,
    ).run


def execute_registered_tool_result(
    ws: WorkspacePaths,
    *,
    executor_id: str,
    recipe_id: str,
    topic_id: str,
    claim_id: str,
    inputs: dict[str, Any],
    evidence_status: str = "",
    code_state_ids: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    source_refs: list[str] | None = None,
    supports_outputs: list[str] | None = None,
    evidence_type: str = "tool_run",
    evidence_summary: str = "",
) -> ToolExecutionResult:
    """Execute a safe built-in tool and optionally record evidence coverage."""

    spec = _resolve_executor(executor_id)
    outputs = spec.run(inputs)
    status = evidence_status or _infer_evidence_status(outputs)
    environment = {
        "executor_id": spec.executor_id,
        "executor_version": spec.version,
        "execution_mode": spec.execution_mode,
    }
    run = record_tool_run(
        ws,
        recipe_id=recipe_id,
        tool_family=spec.tool_family,
        tool_name=spec.tool_name,
        topic_id=topic_id,
        claim_id=claim_id,
        inputs=inputs,
        outputs=outputs,
        environment=environment,
        evidence_status=status,
        code_state_ids=code_state_ids,
        artifact_ids=artifact_ids,
        source_refs=source_refs,
    )
    evidence = None
    if supports_outputs:
        evidence = record_evidence(
            ws,
            topic_id=topic_id,
            claim_id=claim_id,
            evidence_type=evidence_type,
            status=status,
            summary=evidence_summary or f"Tool run {run.run_id} completed via {executor_id}.",
            supports_outputs=supports_outputs,
            source_refs=source_refs,
            tool_run_ids=[run.run_id],
            artifact_ids=artifact_ids,
        )
    return ToolExecutionResult(run=run, evidence=evidence)


def _resolve_executor(executor_id: str) -> ToolExecutorSpec:
    executors = builtin_tool_executors()
    try:
        return executors[executor_id]
    except KeyError as exc:
        known = ", ".join(sorted(executors))
        raise ValueError(f"unknown tool executor {executor_id!r}; known executors: {known}") from exc


def _run_scalar_tolerance_check(inputs: dict[str, Any]) -> dict[str, Any]:
    observed = _number(inputs, "observed")
    expected = _number(inputs, "expected")
    tolerance = _number(inputs, "tolerance")
    absolute_error = round(abs(observed - expected), 12)
    return {
        "quantity": str(inputs.get("quantity", "scalar")),
        "observed": observed,
        "expected": expected,
        "tolerance": tolerance,
        "absolute_error": absolute_error,
        "within_tolerance": absolute_error <= tolerance,
    }


def _number(inputs: dict[str, Any], key: str) -> float:
    value = inputs.get(key)
    if not isinstance(value, int | float):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _infer_evidence_status(outputs: dict[str, Any]) -> str:
    if outputs.get("within_tolerance") is True:
        return "supports"
    if outputs.get("within_tolerance") is False:
        return "refutes"
    return "unreviewed"
