"""Deterministic built-in tool executor kernels for AITP v5."""

from __future__ import annotations

from typing import Any


def run_scalar_tolerance_check(inputs: dict[str, Any]) -> dict[str, Any]:
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


def run_metric_table_check(inputs: dict[str, Any]) -> dict[str, Any]:
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


def run_checklist_consistency_check(inputs: dict[str, Any]) -> dict[str, Any]:
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


def run_failure_mode_basis_check(inputs: dict[str, Any]) -> dict[str, Any]:
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


def run_formula_code_invariant_check(inputs: dict[str, Any]) -> dict[str, Any]:
    raw_invariants = inputs.get("invariants")
    if not isinstance(raw_invariants, list) or not raw_invariants:
        raise ValueError("invariants must be a non-empty list")

    invariants = [_invariant_item(row, index) for index, row in enumerate(raw_invariants)]
    matched = [item["name"] for item in invariants if item["status"] in {"matched", "checked", "verified"}]
    unchecked = [item["name"] for item in invariants if item["status"] in {"missing", "unchecked", "unknown"}]
    failed = [item["name"] for item in invariants if item["status"] in {"mismatch", "failed", "invalid"}]
    return {
        "invariant_count": len(invariants),
        "matched_count": len(matched),
        "unchecked_count": len(unchecked),
        "failed_count": len(failed),
        "all_invariants_checked": not unchecked and not failed,
        "matched_invariants": matched,
        "unchecked_invariants": unchecked,
        "failed_invariants": failed,
        "invariants": invariants,
    }


def infer_evidence_status(outputs: dict[str, Any]) -> str:
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
    if outputs.get("all_invariants_checked") is True:
        return "supports"
    if outputs.get("all_invariants_checked") is False:
        return "refutes"
    if outputs.get("within_tolerance") is True:
        return "supports"
    if outputs.get("within_tolerance") is False:
        return "refutes"
    return "unreviewed"


def _basis_item(row: Any, index: int) -> dict[str, str]:
    if not isinstance(row, dict):
        raise ValueError(f"basis_items[{index}] must be an object")
    return {
        "failure_mode": _nonempty_string(row.get("failure_mode"), f"basis_items[{index}].failure_mode"),
        "basis_ref": _nonempty_string(row.get("basis_ref"), f"basis_items[{index}].basis_ref"),
        "basis_type": _nonempty_string(row.get("basis_type"), f"basis_items[{index}].basis_type"),
        "question_answered": _nonempty_string(row.get("question_answered"), f"basis_items[{index}].question_answered"),
    }


def _invariant_item(row: Any, index: int) -> dict[str, str]:
    if not isinstance(row, dict):
        raise ValueError(f"invariants[{index}] must be an object")
    status = str(row.get("status", "")).strip().lower()
    if status not in {"matched", "checked", "verified", "mismatch", "failed", "invalid", "missing", "unchecked", "unknown"}:
        raise ValueError(f"invariants[{index}].status must describe a matched, failed, or unchecked invariant")
    observed = str(row.get("observed_relation", "")).strip()
    if status in {"matched", "checked", "verified", "mismatch", "failed", "invalid"} and not observed:
        raise ValueError(f"invariants[{index}].observed_relation must be non-empty for checked or failed invariants")
    return {
        "name": _nonempty_string(row.get("name"), f"invariants[{index}].name"),
        "formula_ref": _nonempty_string(row.get("formula_ref"), f"invariants[{index}].formula_ref"),
        "code_ref": _nonempty_string(row.get("code_ref"), f"invariants[{index}].code_ref"),
        "expected_relation": _nonempty_string(row.get("expected_relation"), f"invariants[{index}].expected_relation"),
        "observed_relation": observed,
        "status": status,
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
