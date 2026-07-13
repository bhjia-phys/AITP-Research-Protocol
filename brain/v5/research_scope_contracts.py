"""Validation contracts for bounded M1 research scope records."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any, Mapping

from brain.v5.lifecycle_models import (
    CrossTopicRelationRecord,
    ResearchProgramRecord,
    SessionFocusSetRecord,
)
from brain.v5.record_family_registry import RecordFamilySpec, record_family_specs
from brain.v5.record_repository import RecordReadResult, RecordRepository


FOCUS_REF_FAMILIES: dict[str, frozenset[str]] = {
    "question": frozenset({"questions"}),
    "claim": frozenset({"claims"}),
    "route": frozenset({"routes"}),
    "work_package": frozenset({"research_runs"}),
    "source_set": frozenset({"source_assets"}),
    "code_change": frozenset({"code_states"}),
    "run_campaign": frozenset({"research_runs"}),
}

FOCUS_SCOPE_STATUSES = frozenset({"active", "closed", "superseded"})
PROGRAM_REVIEW_STATUSES = frozenset(
    {"pending_review", "reviewed", "approved", "rejected", "retired"}
)
SCOPED_PROGRAM_REVIEW_STATUSES = frozenset({"reviewed", "approved"})
BRIDGE_STATUSES = frozenset(
    {"pending_review", "reviewed", "approved", "pending_target", "rejected", "retired"}
)
SUPPORTING_BRIDGE_STATUSES = frozenset({"reviewed", "approved"})


def canonical_typed_ref(ref: str) -> tuple[str, RecordFamilySpec, str]:
    """Normalize one generated-registry ref or reject it precisely."""

    raw = str(ref or "").strip()
    parts = raw.split(":")
    if len(parts) == 3 and parts[0] == "aitp":
        raw_kind, record_id = parts[1:]
    elif len(parts) == 2:
        raw_kind, record_id = parts
    else:
        raise ValueError(f"malformed typed ref: {raw!r}")
    normalized_kind = raw_kind.strip().replace("-", "_")
    record_id = record_id.strip()
    if not normalized_kind or not record_id:
        raise ValueError(f"malformed typed ref: {raw!r}")
    for spec in record_family_specs().values():
        aliases = {alias.replace("-", "_") for alias in spec.exact_ref_aliases}
        if normalized_kind in aliases:
            return f"{spec.ref_kind}:{record_id}", spec, record_id
    raise ValueError(f"unsupported typed ref kind: {raw_kind!r}")


def inspect_existing_ref(
    repository: RecordRepository,
    ref: str,
    *,
    allow_missing: bool = False,
) -> tuple[str, RecordFamilySpec, RecordReadResult]:
    canonical, spec, _record_id = canonical_typed_ref(ref)
    result = repository.read(canonical)
    if result.status == "found" and result.record is not None:
        return canonical, spec, result
    if allow_missing and result.status == "not_found":
        return canonical, spec, result
    detail = result.issue.message if result.issue else result.status
    raise ValueError(f"typed ref {canonical!r} is not readable: {detail}")


def record_payload(result: RecordReadResult) -> dict[str, Any]:
    if result.record is None:
        return {}
    if is_dataclass(result.record):
        return asdict(result.record)
    if isinstance(result.record, Mapping):
        return dict(result.record)
    return {}


def validate_research_program(
    repository: RecordRepository,
    record: ResearchProgramRecord,
) -> None:
    _require_nonempty(record.program_id, "program_id")
    _require_nonempty(record.title, "title")
    _require_nonempty_list(record.primary_topic_ids, "primary_topic_ids")
    _require_unique(record.primary_topic_ids, "primary_topic_ids")
    _require_unique(record.supporting_topic_ids, "supporting_topic_ids")
    overlap = set(record.primary_topic_ids) & set(record.supporting_topic_ids)
    if overlap:
        raise ValueError(f"program primary and supporting topics overlap: {sorted(overlap)}")
    if record.review_status not in PROGRAM_REVIEW_STATUSES:
        raise ValueError(f"unsupported program review_status: {record.review_status}")
    require_timestamp_if_set(record.created_at, "created_at")
    for topic_id in [*record.primary_topic_ids, *record.supporting_topic_ids]:
        inspect_existing_ref(repository, f"topic:{topic_id}")
    _validate_ref_list(repository, record.source_refs, "source_refs")


def validate_session_focus_set(
    repository: RecordRepository,
    record: SessionFocusSetRecord,
) -> None:
    _require_nonempty(record.focus_set_id, "focus_set_id")
    _require_nonempty(record.session_id, "session_id")
    _require_nonempty(record.primary_topic_id, "primary_topic_id")
    if record.focus_kind not in FOCUS_REF_FAMILIES:
        raise ValueError(f"unsupported focus_kind: {record.focus_kind}")
    if record.scope_status not in FOCUS_SCOPE_STATUSES:
        raise ValueError(f"unsupported scope_status: {record.scope_status}")
    require_timestamp_if_set(record.created_at, "created_at")
    _canonical, spec, focus_result = inspect_existing_ref(repository, record.focus_ref)
    if spec.family not in FOCUS_REF_FAMILIES[record.focus_kind]:
        raise ValueError(
            f"focus_kind {record.focus_kind!r} requires one of "
            f"{sorted(FOCUS_REF_FAMILIES[record.focus_kind])}, got {spec.family!r}"
        )
    session_ref, _session_spec, session_result = inspect_existing_ref(
        repository, f"session:{record.session_id}"
    )
    session_payload = record_payload(session_result)
    if session_payload.get("topic_id") != record.primary_topic_id:
        raise ValueError(
            f"focus primary topic must equal session topic for {session_ref}"
        )
    inspect_existing_ref(repository, f"topic:{record.primary_topic_id}")
    focus_topic = str(record_payload(focus_result).get("topic_id") or "")
    if focus_topic and focus_topic != record.primary_topic_id:
        raise ValueError("focus_ref belongs to a different topic than primary_topic_id")
    if set(record.supporting_refs) & set(record.excluded_refs):
        raise ValueError("supporting_refs and excluded_refs must not overlap")
    for name, refs in (
        ("supporting_refs", record.supporting_refs),
        ("excluded_refs", record.excluded_refs),
        ("objective_refs", record.objective_refs),
        ("source_refs", record.source_refs),
    ):
        _validate_ref_list(repository, refs, name)
    if record.program_id:
        _program_ref, _program_spec, program_result = inspect_existing_ref(
            repository, f"research_program:{record.program_id}"
        )
        program = record_payload(program_result)
        if record.primary_topic_id not in program.get("primary_topic_ids", []):
            raise ValueError("focus primary topic is not a primary topic of the program")


def validate_cross_topic_relation(
    repository: RecordRepository,
    record: CrossTopicRelationRecord,
) -> None:
    _require_nonempty(record.relation_id, "relation_id")
    _require_nonempty(record.source_topic_id, "source_topic_id")
    _require_nonempty(record.target_topic_id, "target_topic_id")
    if record.source_topic_id == record.target_topic_id:
        raise ValueError("cross-topic relation requires different topics")
    if record.status not in BRIDGE_STATUSES:
        raise ValueError(f"unsupported cross-topic relation status: {record.status}")
    require_timestamp_if_set(record.created_at, "created_at")
    _require_nonempty(record.relation_kind, "relation_kind")
    _require_nonempty(record.transfer_rationale, "transfer_rationale")
    _require_nonempty(record.applicability_boundary, "applicability_boundary")
    _require_nonempty_list(record.revalidation_requirements, "revalidation_requirements")
    inspect_existing_ref(repository, f"topic:{record.source_topic_id}")
    inspect_existing_ref(repository, f"topic:{record.target_topic_id}")
    _source_ref, _source_spec, source_result = inspect_existing_ref(
        repository, record.source_ref
    )
    _target_ref, _target_spec, target_result = inspect_existing_ref(
        repository,
        record.target_ref,
        allow_missing=record.status == "pending_target",
    )
    _require_record_topic(source_result, record.source_topic_id, "source_ref")
    if target_result.status == "found":
        _require_record_topic(target_result, record.target_topic_id, "target_ref")
    elif record.status != "pending_target":
        raise ValueError("missing target_ref requires status pending_target")
    _validate_ref_list(repository, record.source_refs, "source_refs")


def _require_record_topic(result: RecordReadResult, expected: str, label: str) -> None:
    actual = str(record_payload(result).get("topic_id") or "")
    if not actual:
        raise ValueError(f"{label} must establish topic ownership")
    if actual != expected:
        raise ValueError(f"{label} belongs to topic {actual!r}, expected {expected!r}")


def _validate_ref_list(
    repository: RecordRepository,
    refs: list[str],
    label: str,
) -> None:
    _require_unique(refs, label)
    for ref in refs:
        inspect_existing_ref(repository, ref)


def _require_nonempty(value: str, label: str) -> None:
    if not str(value or "").strip():
        raise ValueError(f"{label} must be non-empty")


def _require_nonempty_list(values: list[str], label: str) -> None:
    if not values or any(not str(value or "").strip() for value in values):
        raise ValueError(f"{label} must contain non-empty values")


def _require_unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must not contain duplicates")


def require_timestamp_if_set(value: str, label: str) -> None:
    text = str(value or "").strip()
    if not text:
        return
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
