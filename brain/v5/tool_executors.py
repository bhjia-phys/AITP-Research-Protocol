"""Safe built-in tool executors that materialize ToolRunRecord outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from brain.v5.evidence import record_evidence
from brain.v5.models import EvidenceRecord, ToolRunRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.tool_executor_kernels import (
    infer_evidence_status,
    run_checklist_consistency_check,
    run_failure_mode_basis_check,
    run_formula_code_invariant_check,
    run_metric_table_check,
    run_scalar_tolerance_check,
)
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
            run=run_scalar_tolerance_check,
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
            run=run_metric_table_check,
        ),
        ToolExecutorSpec(
            executor_id="formula_code_invariant_check",
            tool_family="sanity_check",
            tool_name="formula_code_invariant_check",
            execution_mode="safe_builtin",
            version="1",
            purpose="Check that formula references, code references, and expected formula-code invariants are explicitly matched.",
            evidence_profiles=("code_method", "mixed"),
            input_schema={
                "type": "object",
                "required": ["invariants"],
                "properties": {
                    "invariants": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "formula_ref", "code_ref", "expected_relation", "status"],
                            "properties": {
                                "name": {"type": "string"},
                                "formula_ref": {"type": "string"},
                                "code_ref": {"type": "string"},
                                "expected_relation": {"type": "string"},
                                "observed_relation": {"type": "string"},
                                "status": {"type": "string"},
                            },
                        },
                    },
                },
            },
            output_schema={
                "type": "object",
                "required": ["all_invariants_checked", "matched_invariants", "unchecked_invariants", "failed_invariants"],
                "properties": {
                    "all_invariants_checked": {"type": "boolean"},
                    "matched_invariants": {"type": "array"},
                    "unchecked_invariants": {"type": "array"},
                    "failed_invariants": {"type": "array"},
                    "invariants": {"type": "array"},
                },
            },
            run=run_formula_code_invariant_check,
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
            run=run_checklist_consistency_check,
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
            run=run_failure_mode_basis_check,
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
    status = evidence_status or infer_evidence_status(outputs)
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
