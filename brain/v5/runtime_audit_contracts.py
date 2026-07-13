"""Contracts for the read-only AITP runtime capability audit."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import (
    ContractError,
    ContractResult,
    _require_bool_value,
    _require_list,
    _require_mapping,
    _require_nonempty_str,
)
from brain.v5.runtime_audit import _CLASSIFICATIONS
from brain.v5.writer_scan import (
    DIRECT_MUTATION_MECHANISMS,
    WRITER_SOURCE_SCOPES,
)


_FAMILY_LIST_KEYS = (
    "layout",
    "literal_uses",
    "actual_workspace",
    "used_not_layout",
    "actual_not_layout",
    "layout_not_used",
)
_CAPABILITY_LIST_KEYS = (
    "catalog_operations",
    "catalog_mcp",
    "catalog_surfaces",
    "registry_operations",
    "registry_mcp",
    "registry_surfaces",
    "public_surfaces",
    "mcp_wrappers",
    "compact_allowlist",
    "catalog_mcp_not_wrapped",
    "wrapped_not_catalog",
    "catalog_surface_not_public",
    "public_not_catalog",
    "compact_not_wrapped",
    "compact_not_catalog",
    "registry_mcp_not_wrapped",
    "wrapped_not_registry",
    "registry_surface_not_public",
    "compact_not_registry",
)


def validate_runtime_capability_audit(
    payload: dict[str, Any],
    *,
    path: str = "runtime_capability_audit",
) -> ContractResult:
    """Validate a complete trust-neutral runtime audit payload."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "runtime_capability_audit":
        result.add(f"{path}.kind", "must be 'runtime_capability_audit'")
    _require_nonempty_str(payload, "repo_root", path, result)
    if payload.get("truth_source") != "static_source_and_filesystem_inventory":
        result.add(
            f"{path}.truth_source",
            "must be 'static_source_and_filesystem_inventory'",
        )
    _require_bool_value(
        payload.get("summary_inputs_trusted"),
        False,
        f"{path}.summary_inputs_trusted",
        result,
    )
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(
        payload.get("can_update_kernel_state"),
        False,
        f"{path}.can_update_kernel_state",
        result,
    )
    _require_bool_value(
        payload.get("can_update_claim_trust"),
        False,
        f"{path}.can_update_claim_trust",
        result,
    )

    inventory = payload.get("inventory")
    _require_mapping(inventory, f"{path}.inventory", result)
    if isinstance(inventory, dict):
        if not isinstance(inventory.get("file_count"), int) or inventory["file_count"] < 0:
            result.add(f"{path}.inventory.file_count", "must be a non-negative integer")
        if not isinstance(inventory.get("writer_count"), int) or inventory["writer_count"] < 0:
            result.add(f"{path}.inventory.writer_count", "must be a non-negative integer")
        if (
            not isinstance(inventory.get("direct_mutation_candidate_count"), int)
            or inventory["direct_mutation_candidate_count"] < 0
        ):
            result.add(
                f"{path}.inventory.direct_mutation_candidate_count",
                "must be a non-negative integer",
            )
        if (
            not isinstance(inventory.get("direct_mutation_file_count"), int)
            or inventory["direct_mutation_file_count"] < 0
        ):
            result.add(
                f"{path}.inventory.direct_mutation_file_count",
                "must be a non-negative integer",
            )
        if (
            not isinstance(inventory.get("actual_registry_record_count"), int)
            or inventory["actual_registry_record_count"] < 0
        ):
            result.add(
                f"{path}.inventory.actual_registry_record_count",
                "must be a non-negative integer",
            )
        counts = inventory.get("classification_counts")
        _require_mapping(counts, f"{path}.inventory.classification_counts", result)
        if isinstance(counts, dict):
            for key, value in counts.items():
                if key not in _CLASSIFICATIONS:
                    result.add(f"{path}.inventory.classification_counts.{key}", "unknown classification")
                if not isinstance(value, int) or value < 0:
                    result.add(
                        f"{path}.inventory.classification_counts.{key}",
                        "must be a non-negative integer",
                    )

    files = payload.get("files")
    _require_list(files, f"{path}.files", result)
    if isinstance(files, list):
        for index, row in enumerate(files):
            _validate_file_row(row, f"{path}.files[{index}]", result)
        if isinstance(inventory, dict) and inventory.get("file_count") != len(files):
            result.add(f"{path}.inventory.file_count", "must equal the number of file rows")

    writers = payload.get("writers")
    _require_list(writers, f"{path}.writers", result)
    if isinstance(writers, list):
        for index, row in enumerate(writers):
            _validate_writer_row(row, f"{path}.writers[{index}]", result)
        if isinstance(inventory, dict) and inventory.get("writer_count") != len(writers):
            result.add(f"{path}.inventory.writer_count", "must equal the number of writer rows")

    direct_mutations = payload.get("direct_mutation_candidates")
    _require_list(direct_mutations, f"{path}.direct_mutation_candidates", result)
    if isinstance(direct_mutations, list):
        for index, row in enumerate(direct_mutations):
            _validate_direct_mutation_row(
                row,
                f"{path}.direct_mutation_candidates[{index}]",
                result,
            )
        if isinstance(inventory, dict):
            if inventory.get("direct_mutation_candidate_count") != len(direct_mutations):
                result.add(
                    f"{path}.inventory.direct_mutation_candidate_count",
                    "must equal the number of direct mutation rows",
                )
            mutation_files = {
                row.get("path")
                for row in direct_mutations
                if isinstance(row, dict) and isinstance(row.get("path"), str)
            }
            if inventory.get("direct_mutation_file_count") != len(mutation_files):
                result.add(
                    f"{path}.inventory.direct_mutation_file_count",
                    "must equal the number of files with direct mutation rows",
                )

    scan_policy = payload.get("writer_scan_policy")
    _validate_writer_scan_policy(scan_policy, f"{path}.writer_scan_policy", result)

    capabilities = payload.get("capabilities")
    _require_mapping(capabilities, f"{path}.capabilities", result)
    if isinstance(capabilities, dict):
        for key in _CAPABILITY_LIST_KEYS:
            _require_list(capabilities.get(key), f"{path}.capabilities.{key}", result)

    families = payload.get("record_families")
    _require_mapping(families, f"{path}.record_families", result)
    if isinstance(families, dict):
        for key in _FAMILY_LIST_KEYS:
            _require_list(families.get(key), f"{path}.record_families.{key}", result)
        _require_mapping(
            families.get("literal_users"),
            f"{path}.record_families.literal_users",
            result,
        )
        actual_counts = families.get("actual_workspace_counts")
        _require_mapping(
            actual_counts,
            f"{path}.record_families.actual_workspace_counts",
            result,
        )
        if isinstance(actual_counts, dict):
            for family, count in actual_counts.items():
                if not isinstance(family, str) or not family:
                    result.add(
                        f"{path}.record_families.actual_workspace_counts",
                        "family names must be non-empty strings",
                    )
                if not isinstance(count, int) or count < 0:
                    result.add(
                        f"{path}.record_families.actual_workspace_counts.{family}",
                        "must be a non-negative integer",
                    )
            if (
                isinstance(inventory, dict)
                and all(isinstance(count, int) and count >= 0 for count in actual_counts.values())
                and inventory.get("actual_registry_record_count") != sum(actual_counts.values())
            ):
                result.add(
                    f"{path}.inventory.actual_registry_record_count",
                    "must equal the sum of actual workspace family counts",
                )
    return result


def require_valid_runtime_capability_audit(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a runtime audit payload or raise a contract error."""

    result = validate_runtime_capability_audit(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_file_row(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    _require_nonempty_str(value, "path", path, result)
    classification = value.get("classification")
    if classification not in _CLASSIFICATIONS:
        result.add(f"{path}.classification", "must be a registered audit classification")
    if not isinstance(value.get("parse_error"), str):
        result.add(f"{path}.parse_error", "must be a string")


def _validate_writer_row(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in ("path", "function", "call"):
        _require_nonempty_str(value, key, path, result)
    if not isinstance(value.get("line"), int) or value["line"] < 0:
        result.add(f"{path}.line", "must be a non-negative integer")
    _require_list(value.get("registry_families"), f"{path}.registry_families", result)
    if not isinstance(value.get("dynamic_registry_family"), bool):
        result.add(f"{path}.dynamic_registry_family", "must be a boolean")


def _validate_direct_mutation_row(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in (
        "path",
        "function",
        "call",
        "mechanism",
        "source_scope",
    ):
        _require_nonempty_str(value, key, path, result)
    for key in ("mode", "target_expression", "detail"):
        if not isinstance(value.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    if not isinstance(value.get("line"), int) or value["line"] < 0:
        result.add(f"{path}.line", "must be a non-negative integer")
    if value.get("mechanism") not in DIRECT_MUTATION_MECHANISMS:
        result.add(f"{path}.mechanism", "must be a recognized mutation mechanism")
    if value.get("source_scope") not in WRITER_SOURCE_SCOPES:
        result.add(f"{path}.source_scope", "must be a recognized writer source scope")


def _validate_writer_scan_policy(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in (
        "included_source_prefixes",
        "excluded_source_prefixes",
        "recognized_mechanisms",
        "known_gaps",
        "excluded_mechanisms",
        "parse_error_paths",
    ):
        items = value.get(key)
        _require_list(items, f"{path}.{key}", result)
        if isinstance(items, list) and not all(
            isinstance(item, str) and item for item in items
        ):
            result.add(f"{path}.{key}", "must contain only non-empty strings")
    if set(value.get("recognized_mechanisms") or []) != set(DIRECT_MUTATION_MECHANISMS):
        result.add(
            f"{path}.recognized_mechanisms",
            "must enumerate every recognized direct mutation mechanism",
        )
    if not isinstance(value.get("coverage_complete"), bool):
        result.add(f"{path}.coverage_complete", "must be a boolean")
    if not isinstance(value.get("bounded_coverage_complete"), bool):
        result.add(f"{path}.bounded_coverage_complete", "must be a boolean")
    if value.get("closure_scope") != "declared_python_source_prefixes":
        result.add(
            f"{path}.closure_scope",
            "must identify the declared Python source-prefix boundary",
        )
    counts = {}
    for key in (
        "scanned_source_file_count",
        "parsed_source_file_count",
        "parse_error_count",
    ):
        count = value.get(key)
        if not isinstance(count, int) or count < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
        else:
            counts[key] = count
    parse_error_paths = value.get("parse_error_paths")
    if isinstance(parse_error_paths, list):
        if counts.get("parse_error_count") != len(parse_error_paths):
            result.add(
                f"{path}.parse_error_count",
                "must equal the number of parse_error_paths",
            )
    if len(counts) == 3:
        if counts["parsed_source_file_count"] + counts["parse_error_count"] != counts[
            "scanned_source_file_count"
        ]:
            result.add(
                f"{path}.parsed_source_file_count",
                "parsed plus parse-error counts must equal scanned count",
            )
    if value.get("bounded_coverage_complete") is True and (
        counts.get("scanned_source_file_count", 0) == 0
        or counts.get("parse_error_count") != 0
    ):
        result.add(
            f"{path}.bounded_coverage_complete",
            "requires at least one scanned source and zero parse errors",
        )
    if value.get("excluded_mechanisms") != value.get("known_gaps"):
        result.add(
            f"{path}.excluded_mechanisms",
            "must explicitly mirror the known out-of-scope mechanisms",
        )
