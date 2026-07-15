"""Conservative typed materialization for pre-envelope schema-v1 records."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Any, Mapping


_ID_FIELDS = {
    "CodeStateRecord": ("code_state_id", ("id",)),
    "EvidenceRecord": ("evidence_id", ("id",)),
    "ReferenceLocationRecord": (
        "location_id",
        ("reference_location_id", "id"),
    ),
    "SensemakingReportRecord": ("report_id", ("id",)),
    "ToolRunRecord": ("run_id", ("id",)),
    "ValidationResultRecord": (
        "result_id",
        ("validation_result_id", "id"),
    ),
}


def materialize_record_class(
    frontmatter: Mapping[str, Any],
    record_class: type,
    *,
    id_field: str = "",
    legacy_id_fields: tuple[str, ...] = (),
    path: str | Path | None = None,
    allow_legacy: bool = True,
) -> Any:
    """Construct one typed record without hiding legacy compatibility choices."""

    values = dict(frontmatter)
    if record_class.__name__ == "ToolRunRecord":
        _tool_run_supersession_compat(values)
        _tool_run_execution_aliases(values)
    legacy = allow_legacy and _is_pre_envelope_record(values)
    configured_id, configured_aliases = _ID_FIELDS.get(
        record_class.__name__,
        ("", ()),
    )
    canonical_id = id_field or configured_id
    aliases = legacy_id_fields or configured_aliases

    if legacy:
        _fill_record_id(values, canonical_id, aliases, path)
        if "topic_id" not in values and values.get("topic"):
            values["topic_id"] = values["topic"]
        _apply_schema_v1_defaults(values, record_class.__name__)

    allowed = {field.name for field in fields(record_class)}
    return record_class(**{key: value for key, value in values.items() if key in allowed})


def _is_pre_envelope_record(values: Mapping[str, Any]) -> bool:
    return not any(
        values.get(field)
        for field in ("record_family", "record_content_hash", "created_by")
    )


def _fill_record_id(
    values: dict[str, Any],
    id_field: str,
    aliases: tuple[str, ...],
    path: str | Path | None,
) -> None:
    if not id_field or values.get(id_field):
        return
    for alias in aliases:
        if values.get(alias):
            values[id_field] = str(values[alias])
            return
    if path is not None:
        values[id_field] = Path(path).stem


def _apply_schema_v1_defaults(values: dict[str, Any], class_name: str) -> None:
    if class_name == "CodeStateRecord":
        _code_state_defaults(values)
    elif class_name == "EvidenceRecord":
        _evidence_defaults(values)
    elif class_name == "ReferenceLocationRecord":
        _reference_location_defaults(values)
    elif class_name == "SensemakingReportRecord":
        _sensemaking_defaults(values)
    elif class_name == "ToolRunRecord":
        _tool_run_defaults(values)
    elif class_name == "ValidationResultRecord":
        _validation_result_defaults(values)


def _code_state_defaults(values: dict[str, Any]) -> None:
    for field in (
        "repo_id",
        "upstream_remote",
        "upstream_branch",
        "upstream_commit",
        "local_branch",
        "worktree_path",
    ):
        values.setdefault(field, "")
    values.setdefault("dirty", True)
    values.setdefault(
        "linked_records",
        {"legacy_source_refs": _string_list(values.get("source_refs"))},
    )
    values.setdefault(
        "runtime_environment",
        {
            "legacy_scope": values.get("scope") or [],
            "legacy_verification": values.get("verification") or [],
        },
    )
    values.setdefault(
        "known_divergence",
        str(values.get("state_summary") or "legacy schema-v1 code state is incomplete"),
    )


def _evidence_defaults(values: dict[str, Any]) -> None:
    values.setdefault("claim_id", "")
    values.setdefault("evidence_type", "legacy_unclassified")
    values.setdefault("status", "unreviewed")
    values.setdefault(
        "summary",
        "Legacy schema-v1 evidence placeholder; exact support requires review.",
    )


def _reference_location_defaults(values: dict[str, Any]) -> None:
    values.setdefault("connector_id", "legacy_unspecified")
    values.setdefault("location_type", "legacy_reference_bundle")
    values.setdefault("uri", _first_string(values.get("paths")) or _first_string(values.get("remote_locations")))
    values.setdefault("label", str(values.get("title") or values.get("location_id") or "legacy reference"))
    values.setdefault("summary", _joined_text(values.get("notes")))
    values.setdefault(
        "metadata",
        {
            "legacy_paths": values.get("paths") or [],
            "legacy_remote_locations": values.get("remote_locations") or [],
        },
    )
    values.setdefault("orientation_only", True)


def _sensemaking_defaults(values: dict[str, Any]) -> None:
    values.setdefault("claim_id", "")
    values.setdefault("title", str(values.get("report_id") or "legacy sensemaking report"))
    values.setdefault(
        "summary",
        "Legacy schema-v1 sensemaking placeholder; inspect the canonical record.",
    )
    values.setdefault("validation_status", "not_validation")


def _tool_run_defaults(values: dict[str, Any]) -> None:
    values.setdefault("recipe_id", "legacy-unresolved")
    values.setdefault("tool_family", "legacy_unclassified")
    values.setdefault("tool_name", "legacy-unresolved")
    values.setdefault("claim_id", "")
    values.setdefault("evidence_status", "unreviewed")
    values.setdefault("lane", "diagnostic")


def _tool_run_supersession_compat(values: dict[str, Any]) -> None:
    if values.get("supersedes_run_id"):
        return
    raw = values.get("supersedes")
    items = raw if isinstance(raw, (list, tuple, set, frozenset)) else [raw]
    for item in items:
        candidate = str(item or "").strip()
        if not candidate or "@sha256:" in candidate or candidate.startswith("tool_run:"):
            continue
        values["supersedes_run_id"] = candidate
        return


def _tool_run_execution_aliases(values: dict[str, Any]) -> None:
    if not values.get("recorded_maturity") and values.get("maturity"):
        values["recorded_maturity"] = str(values["maturity"])


def _validation_result_defaults(values: dict[str, Any]) -> None:
    values.setdefault("tool_run_id", "")
    values.setdefault("summary", str(values.get("result_summary") or ""))
    if "checked_outputs" not in values and "checks" in values:
        values["checked_outputs"] = _check_lines(values["checks"])
    values.setdefault("evidence_refs", _string_list(values.get("source_refs")))


def _check_lines(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        return [f"{key}: {item}" for key, item in sorted(value.items())]
    return _string_list(value)


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    items = value if isinstance(value, (list, tuple, set, frozenset)) else [value]
    return [str(item) for item in items if str(item)]


def _first_string(value: Any) -> str:
    items = _string_list(value)
    return items[0] if items else ""


def _joined_text(value: Any) -> str:
    return "; ".join(_string_list(value))
