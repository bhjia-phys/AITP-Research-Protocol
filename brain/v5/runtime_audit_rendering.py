"""Markdown rendering for the AITP runtime capability audit."""

from __future__ import annotations

from typing import Any

from brain.v5.runtime_audit import _CLASSIFICATIONS


def render_runtime_capability_audit_markdown(payload: dict[str, Any]) -> str:
    """Render an audit payload as a stable human-review document."""

    inventory = payload.get("inventory") if isinstance(payload.get("inventory"), dict) else {}
    counts = (
        inventory.get("classification_counts")
        if isinstance(inventory.get("classification_counts"), dict)
        else {}
    )
    families = (
        payload.get("record_families")
        if isinstance(payload.get("record_families"), dict)
        else {}
    )
    capabilities = (
        payload.get("capabilities") if isinstance(payload.get("capabilities"), dict) else {}
    )
    lines = [
        "# AITP Runtime Capability Audit",
        "",
        "This report is read-only structural evidence. It cannot update canonical research state or claim trust.",
        "",
        f"- repo_root: `{payload.get('repo_root', '')}`",
        f"- workspace_base: `{payload.get('workspace_base') or 'not inspected'}`",
        f"- file_count: `{inventory.get('file_count', 0)}`",
        f"- legacy_writer_helper_count: `{inventory.get('writer_count', 0)}`",
        f"- direct_mutation_candidate_count: `{inventory.get('direct_mutation_candidate_count', 0)}`",
        f"- direct_mutation_file_count: `{inventory.get('direct_mutation_file_count', 0)}`",
        f"- actual_registry_record_count: `{inventory.get('actual_registry_record_count', 0)}`",
        f"- truth_source: `{payload.get('truth_source', '')}`",
        f"- summary_inputs_trusted: {str(payload.get('summary_inputs_trusted', True)).lower()}",
        f"- orientation_only: {str(payload.get('orientation_only', False)).lower()}",
        f"- can_update_kernel_state: {str(payload.get('can_update_kernel_state', True)).lower()}",
        f"- can_update_claim_trust: {str(payload.get('can_update_claim_trust', True)).lower()}",
        "",
        "## File Classification Summary",
        "",
    ]
    for classification in _CLASSIFICATIONS:
        lines.append(f"- {classification}: `{counts.get(classification, 0)}`")
    lines.extend(_capability_and_family_lines(capabilities, families))
    lines.extend(_writer_lines(payload.get("writers")))
    lines.extend(
        _direct_mutation_lines(
            payload.get("direct_mutation_candidates"),
            payload.get("writer_scan_policy"),
        )
    )
    lines.extend(_file_lines(payload.get("files")))
    lines.append("")
    return "\n".join(lines)


def _capability_and_family_lines(
    capabilities: dict[str, Any],
    families: dict[str, Any],
) -> list[str]:
    lines = [
        "",
        "## Runtime Capability Drift",
        "",
        f"- catalog_operations: `{len(capabilities.get('catalog_operations') or [])}`",
        f"- catalog_mcp: `{len(capabilities.get('catalog_mcp') or [])}`",
        f"- registry_operations: `{len(capabilities.get('registry_operations') or [])}`",
        f"- registry_mcp: `{len(capabilities.get('registry_mcp') or [])}`",
        f"- public_surfaces: `{len(capabilities.get('public_surfaces') or [])}`",
        f"- mcp_wrappers: `{len(capabilities.get('mcp_wrappers') or [])}`",
        f"- compact_allowlist: `{len(capabilities.get('compact_allowlist') or [])}`",
    ]
    for key in (
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
    ):
        lines.append(f"- {key}: `{_inline_list(capabilities.get(key))}`")
    lines.extend(
        [
            "",
            "## Registry Family Drift",
            "",
        ]
    )
    for key in (
        "layout",
        "literal_uses",
        "actual_workspace",
        "used_not_layout",
        "actual_not_layout",
        "layout_not_used",
    ):
        lines.append(f"- {key}: `{_inline_list(families.get(key))}`")
    lines.extend(
        [
            "",
            "### Actual Family Counts",
            "",
            "| Family | Records |",
            "|---|---:|",
        ]
    )
    actual_counts = (
        families.get("actual_workspace_counts")
        if isinstance(families.get("actual_workspace_counts"), dict)
        else {}
    )
    if actual_counts:
        lines.extend(
            f"| {_escape_table(str(family))} | {count} |"
            for family, count in sorted(actual_counts.items())
        )
    else:
        lines.append("| none | 0 |")
    return lines


def _writer_lines(value: Any) -> list[str]:
    lines = [
        "",
        "## Canonical Writer Candidates",
        "",
        "| Path | Function | Call | Registry Families | Dynamic Family |",
        "|---|---|---|---|---:|",
    ]
    for row in value if isinstance(value, list) else []:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| `{path}` | `{function}` | `{call}` | {families} | {dynamic} |".format(
                path=_escape_table(str(row.get("path") or "")),
                function=_escape_table(str(row.get("function") or "")),
                call=_escape_table(str(row.get("call") or "")),
                families=_escape_table(_inline_list(row.get("registry_families"))),
                dynamic=str(row.get("dynamic_registry_family", False)).lower(),
            )
        )
    return lines


def _direct_mutation_lines(value: Any, policy_value: Any) -> list[str]:
    policy = policy_value if isinstance(policy_value, dict) else {}
    lines = [
        "",
        "## Direct Filesystem Mutation Candidates",
        "",
        f"- writer_scan_coverage_complete: {str(policy.get('coverage_complete', False)).lower()}",
        f"- writer_scan_bounded_coverage_complete: {str(policy.get('bounded_coverage_complete', False)).lower()}",
        f"- closure_scope: `{policy.get('closure_scope', '')}`",
        f"- scanned_source_file_count: `{policy.get('scanned_source_file_count', 0)}`",
        f"- parsed_source_file_count: `{policy.get('parsed_source_file_count', 0)}`",
        f"- parse_error_count: `{policy.get('parse_error_count', 0)}`",
        f"- parse_error_paths: `{_inline_list(policy.get('parse_error_paths'))}`",
        f"- included_source_prefixes: `{_inline_list(policy.get('included_source_prefixes'))}`",
        f"- excluded_source_prefixes: `{_inline_list(policy.get('excluded_source_prefixes'))}`",
        f"- recognized_mechanisms: `{_inline_list(policy.get('recognized_mechanisms'))}`",
        f"- excluded_mechanisms: `{_inline_list(policy.get('excluded_mechanisms'))}`",
        f"- known_gaps: `{_inline_list(policy.get('known_gaps'))}`",
        "",
        "| Path | Function | Line | Mechanism | Call | Mode | Target | Detail | Scope |",
        "|---|---|---:|---|---|---|---|---|---|",
    ]
    for row in value if isinstance(value, list) else []:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| `{path}` | `{function}` | {line} | {mechanism} | `{call}` | {mode} | `{target}` | {detail} | {scope} |".format(
                path=_escape_table(str(row.get("path") or "")),
                function=_escape_table(str(row.get("function") or "")),
                line=int(row.get("line") or 0),
                mechanism=_escape_table(str(row.get("mechanism") or "")),
                call=_escape_table(str(row.get("call") or "")),
                mode=_escape_table(str(row.get("mode") or "")) or "none",
                target=_escape_table(str(row.get("target_expression") or "")),
                detail=_escape_table(str(row.get("detail") or "")) or "none",
                scope=_escape_table(str(row.get("source_scope") or "")),
            )
        )
    return lines


def _file_lines(value: Any) -> list[str]:
    files = value if isinstance(value, list) else []
    lines = ["", "## Parse Errors", ""]
    parse_errors = [row for row in files if isinstance(row, dict) and row.get("parse_error")]
    if parse_errors:
        lines.extend(
            f"- `{row.get('path', '')}`: {_escape_table(str(row.get('parse_error') or ''))}"
            for row in parse_errors
        )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## File Coverage",
            "",
            "| Path | Classification | Parse Error |",
            "|---|---|---|",
        ]
    )
    for row in files:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| `{path}` | {classification} | {parse_error} |".format(
                path=_escape_table(str(row.get("path") or "")),
                classification=_escape_table(str(row.get("classification") or "")),
                parse_error=_escape_table(str(row.get("parse_error") or "")) or "none",
            )
        )
    return lines


def _inline_list(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return "none"
    return ", ".join(str(item) for item in value)


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", " ").replace("\n", " ")
