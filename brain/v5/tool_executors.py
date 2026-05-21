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
    purpose: str
    evidence_profiles: tuple[str, ...]
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    run: Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class ToolExecutionResult:
    run: ToolRunRecord
    evidence: EvidenceRecord | None = None


def builtin_tool_executors() -> dict[str, ToolExecutorSpec]:
    """Return deterministic in-process executors available without shell access."""

    specs = [
        ToolExecutorSpec(
            executor_id="scalar_tolerance_check",
            tool_family="sanity_check",
            tool_name="scalar_tolerance_check",
            execution_mode="safe_builtin",
            version="1",
            purpose="Check one scalar observable against an expected value and tolerance.",
            evidence_profiles=("toy_numeric", "code_method", "mixed"),
            input_schema={
                "type": "object",
                "required": ["observed", "expected", "tolerance"],
                "properties": {
                    "observed": {"type": "number"},
                    "expected": {"type": "number"},
                    "tolerance": {"type": "number", "minimum": 0},
                    "quantity": {"type": "string"},
                },
            },
            output_schema={
                "type": "object",
                "required": ["absolute_error", "within_tolerance"],
                "properties": {
                    "absolute_error": {"type": "number"},
                    "within_tolerance": {"type": "boolean"},
                },
            },
            run=_run_scalar_tolerance_check,
        ),
        ToolExecutorSpec(
            executor_id="metric_table_check",
            tool_family="sanity_check",
            tool_name="metric_table_check",
            execution_mode="safe_builtin",
            version="1",
            purpose="Check a table of scalar metrics against expected values and tolerances.",
            evidence_profiles=("toy_numeric", "code_method", "mixed"),
            input_schema={
                "type": "object",
                "required": ["metrics"],
                "properties": {
                    "table_id": {"type": "string"},
                    "metrics": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "observed", "expected", "tolerance"],
                            "properties": {
                                "name": {"type": "string"},
                                "observed": {"type": "number"},
                                "expected": {"type": "number"},
                                "tolerance": {"type": "number", "minimum": 0},
                            },
                        },
                    },
                },
            },
            output_schema={
                "type": "object",
                "required": ["all_within_tolerance", "failed_metrics", "metrics"],
                "properties": {
                    "all_within_tolerance": {"type": "boolean"},
                    "failed_metrics": {"type": "array"},
                    "metrics": {"type": "array"},
                },
            },
            run=_run_metric_table_check,
        ),
        ToolExecutorSpec(
            executor_id="checklist_consistency_check",
            tool_family="sanity_check",
            tool_name="checklist_consistency_check",
            execution_mode="safe_builtin",
            version="1",
            purpose="Check that formal definitions, assumptions, derivation steps, or counterexample searches are explicitly recorded.",
            evidence_profiles=("formal_theory", "mixed"),
            input_schema={
                "type": "object",
                "required": ["checks"],
                "properties": {
                    "checks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "status", "note"],
                            "properties": {
                                "name": {"type": "string"},
                                "status": {"type": "string"},
                                "note": {"type": "string"},
                            },
                        },
                    },
                },
            },
            output_schema={
                "type": "object",
                "required": ["all_checked", "unchecked_items", "failed_items", "checks"],
                "properties": {
                    "all_checked": {"type": "boolean"},
                    "unchecked_items": {"type": "array"},
                    "failed_items": {"type": "array"},
                    "checks": {"type": "array"},
                },
            },
            run=_run_checklist_consistency_check,
        ),
        ToolExecutorSpec(
            executor_id="failure_mode_basis_check",
            tool_family="sanity_check",
            tool_name="failure_mode_basis_check",
            execution_mode="safe_builtin",
            version="1",
            purpose="Check that every named failure mode has an explicit review basis before promotion.",
            evidence_profiles=("toy_numeric", "code_method", "formal_theory", "mixed"),
            input_schema={
                "type": "object",
                "required": ["failure_modes", "basis_items"],
                "properties": {
                    "failure_modes": {"type": "array", "items": {"type": "string"}},
                    "basis_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["failure_mode", "basis_ref", "basis_type", "question_answered"],
                            "properties": {
                                "failure_mode": {"type": "string"},
                                "basis_ref": {"type": "string"},
                                "basis_type": {"type": "string"},
                                "question_answered": {"type": "string"},
                            },
                        },
                    },
                },
            },
            output_schema={
                "type": "object",
                "required": ["all_failure_modes_covered", "covered_failure_modes", "uncovered_failure_modes"],
                "properties": {
                    "all_failure_modes_covered": {"type": "boolean"},
                    "covered_failure_modes": {"type": "array"},
                    "uncovered_failure_modes": {"type": "array"},
                    "basis_items": {"type": "array"},
                },
            },
            run=_run_failure_mode_basis_check,
        ),
    ]
    return {spec.executor_id: spec for spec in specs}


def describe_tool_executors() -> dict[str, Any]:
    """Return public metadata for available safe built-in executors."""

    executors = sorted(builtin_tool_executors().values(), key=lambda spec: spec.executor_id)
    return {
        "ok": True,
        "kind": "tool_executor_catalog",
        "truth_source": "builtin_executor_registry",
        "summary_inputs_trusted": False,
        "executor_count": len(executors),
        "executors": [
            {
                "executor_id": spec.executor_id,
                "tool_family": spec.tool_family,
                "tool_name": spec.tool_name,
                "execution_mode": spec.execution_mode,
                "version": spec.version,
                "purpose": spec.purpose,
                "evidence_profiles": list(spec.evidence_profiles),
                "input_schema": spec.input_schema,
                "output_schema": spec.output_schema,
            }
            for spec in executors
        ],
    }


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


def _run_metric_table_check(inputs: dict[str, Any]) -> dict[str, Any]:
    raw_metrics = inputs.get("metrics")
    if not isinstance(raw_metrics, list) or not raw_metrics:
        raise ValueError("metrics must be a non-empty list")

    metrics = [_metric_result(row, index) for index, row in enumerate(raw_metrics)]
    failed_metrics = [metric["name"] for metric in metrics if not metric["within_tolerance"]]
    absolute_errors = [metric["absolute_error"] for metric in metrics]
    return {
        "table_id": str(inputs.get("table_id", "metric_table")),
        "metric_count": len(metrics),
        "passed_count": len(metrics) - len(failed_metrics),
        "failed_count": len(failed_metrics),
        "all_within_tolerance": not failed_metrics,
        "max_absolute_error": max(absolute_errors),
        "failed_metrics": failed_metrics,
        "metrics": metrics,
    }


def _run_checklist_consistency_check(inputs: dict[str, Any]) -> dict[str, Any]:
    raw_checks = inputs.get("checks")
    if not isinstance(raw_checks, list) or not raw_checks:
        raise ValueError("checks must be a non-empty list")

    checks = [_checklist_item(row, index) for index, row in enumerate(raw_checks)]
    unchecked = [item["name"] for item in checks if item["status"] in {"unchecked", "unknown"}]
    failed = [item["name"] for item in checks if item["status"] in {"failed", "invalid"}]
    return {
        "check_count": len(checks),
        "checked_count": len(checks) - len(unchecked) - len(failed),
        "unchecked_items": unchecked,
        "failed_items": failed,
        "all_checked": not unchecked and not failed,
        "checks": checks,
    }


def _run_failure_mode_basis_check(inputs: dict[str, Any]) -> dict[str, Any]:
    raw_modes = inputs.get("failure_modes")
    raw_items = inputs.get("basis_items")
    if not isinstance(raw_modes, list) or not raw_modes:
        raise ValueError("failure_modes must be a non-empty list")
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("basis_items must be a non-empty list")
    modes = [_nonempty_string(value, f"failure_modes[{index}]") for index, value in enumerate(raw_modes)]
    items = [_basis_item(row, index) for index, row in enumerate(raw_items)]
    covered = []
    for mode in modes:
        if any(item["failure_mode"] == mode for item in items):
            covered.append(mode)
    uncovered = [mode for mode in modes if mode not in covered]
    return {
        "failure_mode_count": len(modes),
        "basis_item_count": len(items),
        "all_failure_modes_covered": not uncovered,
        "covered_failure_modes": covered,
        "uncovered_failure_modes": uncovered,
        "basis_items": items,
    }


def _basis_item(row: Any, index: int) -> dict[str, str]:
    if not isinstance(row, dict):
        raise ValueError(f"basis_items[{index}] must be an object")
    return {
        "failure_mode": _nonempty_string(row.get("failure_mode"), f"basis_items[{index}].failure_mode"),
        "basis_ref": _nonempty_string(row.get("basis_ref"), f"basis_items[{index}].basis_ref"),
        "basis_type": _nonempty_string(row.get("basis_type"), f"basis_items[{index}].basis_type"),
        "question_answered": _nonempty_string(row.get("question_answered"), f"basis_items[{index}].question_answered"),
    }


def _checklist_item(row: Any, index: int) -> dict[str, str]:
    if not isinstance(row, dict):
        raise ValueError(f"checks[{index}] must be an object")
    name = row.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError(f"checks[{index}].name must be a non-empty string")
    status = str(row.get("status", "")).strip().lower()
    if status not in {"checked", "unchecked", "unknown", "failed", "invalid"}:
        raise ValueError(f"checks[{index}].status must be checked, unchecked, unknown, failed, or invalid")
    note = row.get("note")
    if not isinstance(note, str) or not note.strip():
        raise ValueError(f"checks[{index}].note must be a non-empty string")
    return {"name": name, "status": status, "note": note.strip()}


def _nonempty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path} must be a non-empty string")
    return value.strip()


def _metric_result(row: Any, index: int) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise ValueError(f"metrics[{index}] must be an object")
    name = row.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError(f"metrics[{index}].name must be a non-empty string")
    observed = _number_from(row, "observed", f"metrics[{index}]")
    expected = _number_from(row, "expected", f"metrics[{index}]")
    tolerance = _number_from(row, "tolerance", f"metrics[{index}]")
    if tolerance < 0:
        raise ValueError(f"metrics[{index}].tolerance must be non-negative")
    absolute_error = round(abs(observed - expected), 12)
    return {
        "name": name,
        "observed": observed,
        "expected": expected,
        "tolerance": tolerance,
        "absolute_error": absolute_error,
        "within_tolerance": absolute_error <= tolerance,
    }


def _number(inputs: dict[str, Any], key: str) -> float:
    return _number_from(inputs, key, "inputs")


def _number_from(inputs: dict[str, Any], key: str, path: str) -> float:
    value = inputs.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{path}.{key} must be numeric")
    return float(value)


def _infer_evidence_status(outputs: dict[str, Any]) -> str:
    if outputs.get("all_checked") is True:
        return "supports"
    if outputs.get("all_checked") is False:
        return "refutes"
    if outputs.get("all_within_tolerance") is True:
        return "supports"
    if outputs.get("all_within_tolerance") is False:
        return "refutes"
    if outputs.get("all_failure_modes_covered") is True:
        return "supports"
    if outputs.get("all_failure_modes_covered") is False:
        return "refutes"
    if outputs.get("within_tolerance") is True:
        return "supports"
    if outputs.get("within_tolerance") is False:
        return "refutes"
    return "unreviewed"
