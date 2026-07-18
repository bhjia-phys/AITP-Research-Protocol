"""Canonical Harness Feedback cases and their read-only repeated-problem view."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any, Mapping

from brain.v5.harness_feedback_case_contracts import (
    HarnessFeedbackCaseRequest,
    require_valid_harness_feedback_case,
    require_valid_harness_feedback_request,
)
from brain.v5.harness_feedback_models import HarnessFeedbackCaseRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WritePolicy, WriteResult


class HarnessFeedbackCaseConflict(RuntimeError):
    """Raised when changed facts are presented as an idempotent replay."""


def record_harness_feedback_case(
    ws: WorkspacePaths,
    request: HarnessFeedbackCaseRequest,
    *,
    actor: RecordActor,
    now: datetime | None = None,
    update_mode: str = "create_or_idempotent",
    expected_hash: str = "",
) -> WriteResult:
    """Persist observed friction without entering any Skill or trust lifecycle."""

    if update_mode not in {"create_or_idempotent", "revision", "related"}:
        raise ValueError("update_mode must be create_or_idempotent, revision, or related")
    require_valid_harness_feedback_request(request)
    timestamp = _timestamp(now)
    source_fingerprint = harness_feedback_source_fingerprint(request)
    content_fingerprint = harness_feedback_content_fingerprint(request)
    base_case_id = f"harness-feedback-{source_fingerprint[:24]}"
    repository = RecordRepository(ws, actor=actor)

    with repository.lock_record("harness_feedback_cases", base_case_id):
        base_read = repository.read(f"harness_feedback_case:{base_case_id}")
        base_record = _case_record_or_none(base_read)
        if base_read.status not in {"found", "not_found"}:
            raise HarnessFeedbackCaseConflict(
                f"base Harness Feedback case is not readable: {base_read.status}"
            )
        if base_record and base_record.content_fingerprint == content_fingerprint:
            return _write_existing(repository, base_record)

        if update_mode == "related":
            if base_record is None:
                raise HarnessFeedbackCaseConflict(
                    "related case requires an existing case with the same source fingerprint"
                )
            related_case_id = f"{base_case_id}-{content_fingerprint[:12]}"
            related_read = repository.read(f"harness_feedback_case:{related_case_id}")
            related_record = _case_record_or_none(related_read)
            if related_read.status not in {"found", "not_found"}:
                raise HarnessFeedbackCaseConflict(
                    f"related Harness Feedback case is not readable: {related_read.status}"
                )
            if related_record:
                if related_record.content_fingerprint != content_fingerprint:
                    raise HarnessFeedbackCaseConflict(
                        "related case identity collides with different content"
                    )
                return _write_existing(repository, related_record)
            record = _build_record(
                request,
                case_id=related_case_id,
                source_fingerprint=source_fingerprint,
                content_fingerprint=content_fingerprint,
                created_at=timestamp,
                updated_at=timestamp,
                related_case_refs=_merge_refs(
                    request.related_case_refs,
                    (f"harness_feedback_case:{base_case_id}",),
                ),
            )
            return _write_new(repository, record)

        if base_record is None:
            if update_mode == "revision":
                raise HarnessFeedbackCaseConflict("cannot revise a missing Harness Feedback case")
            record = _build_record(
                request,
                case_id=base_case_id,
                source_fingerprint=source_fingerprint,
                content_fingerprint=content_fingerprint,
                created_at=timestamp,
                updated_at=timestamp,
            )
            return _write_new(repository, record)

        if update_mode != "revision":
            raise HarnessFeedbackCaseConflict(
                "changed information requires an explicit revision or related case"
            )
        if not expected_hash:
            raise HarnessFeedbackCaseConflict("revision requires the current expected hash")
        predecessor_ref = f"harness_feedback_case:{base_case_id}@sha256:{expected_hash}"
        record = _build_record(
            request,
            case_id=base_case_id,
            source_fingerprint=source_fingerprint,
            content_fingerprint=content_fingerprint,
            created_at=base_record.created_at,
            updated_at=timestamp,
            supersedes_case_refs=_merge_refs(
                base_record.supersedes_case_refs,
                (predecessor_ref,),
            ),
        )
        result = repository.write(
            "harness_feedback_cases",
            record,
            body=render_harness_feedback_case(record),
            policy=WritePolicy(mode="revision", expected_hash=expected_hash),
        )
        return result


def harness_feedback_source_fingerprint(request: HarnessFeedbackCaseRequest) -> str:
    basis = {
        "topic_id": request.topic_id,
        "problem_type": request.problem_type,
        "host_id": request.host_id,
        "affected_capability": request.affected_capability,
        "affected_record_family": request.affected_record_family,
        "source_refs": sorted(set(request.source_refs)),
    }
    return _fingerprint(basis)


def harness_feedback_content_fingerprint(request: HarnessFeedbackCaseRequest) -> str:
    return _fingerprint(asdict(request))


def render_harness_feedback_case(record: HarnessFeedbackCaseRecord) -> str:
    """Render facts and review direction only; authority flags stay in frontmatter."""

    require_valid_harness_feedback_case(record)
    lines = [
        f"# Harness Feedback Case: {record.case_id}",
        "",
        f"Status: `{record.status}`",
        f"Problem type: `{record.problem_type}`",
        f"Topic: `{record.topic_id or 'unscoped'}`",
        f"Host: `{record.host_id}`",
        f"Affected capability: `{record.affected_capability}`",
        f"Affected record family: `{record.affected_record_family}`",
        f"Source fingerprint: `{record.source_fingerprint}`",
        "",
        "## Observed Friction",
        "",
        record.friction,
        "",
        "## Expected Behavior",
        "",
        record.expected_behavior,
        "",
        "## Actual Behavior",
        "",
        record.actual_behavior,
        "",
        "## Impact",
        "",
        record.impact,
        "",
        "## Reproduction",
        "",
    ]
    lines.extend(f"{index}. {step}" for index, step in enumerate(record.reproduction_steps, 1))
    lines.extend(["", "## Runtime Context", ""])
    lines.extend(
        f"- `{key}`: `{_render_runtime_value(value)}`"
        for key, value in sorted(record.runtime_context.items())
    )
    lines.extend(["", "## Source References", ""])
    lines.extend(f"- `{record_ref}`" for record_ref in record.source_refs)
    lines.extend(
        [
            "",
            "## Proposed Direction",
            "",
            record.proposed_direction,
            "",
            "## Review Boundary",
            "",
            "This is an observation-only review input. It cannot change research records or runtime behavior.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_harness_feedback_review_view(ws: WorkspacePaths) -> dict[str, Any]:
    """Group recurring source fingerprints without creating derived canonical records."""

    repository = RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="harness-feedback-view", host="aitp"),
    )
    report = repository.list("harness_feedback_cases")
    grouped: dict[str, list[HarnessFeedbackCaseRecord]] = {}
    for record in report.records:
        if isinstance(record, HarnessFeedbackCaseRecord):
            grouped.setdefault(record.source_fingerprint, []).append(record)
    groups: list[dict[str, Any]] = []
    for fingerprint, records in sorted(grouped.items()):
        if len(records) < 2:
            continue
        records.sort(key=lambda item: (item.created_at, item.case_id))
        first = records[0]
        groups.append(
            {
                "source_fingerprint": fingerprint,
                "problem_type": first.problem_type,
                "affected_capability": first.affected_capability,
                "affected_record_family": first.affected_record_family,
                "case_refs": sorted(
                    f"harness_feedback_case:{record.case_id}" for record in records
                ),
                "count": len(records),
                "statuses": sorted({record.status for record in records}),
                "first_seen": records[0].created_at,
                "last_seen": max(record.updated_at for record in records),
                "impacts": sorted({record.impact for record in records}),
                "source_refs": sorted(
                    {record_ref for record in records for record_ref in record.source_refs}
                ),
                "unresolved_case_refs": sorted(
                    f"harness_feedback_case:{record.case_id}"
                    for record in records
                    if record.status not in {"duplicate", "rejected", "resolved", "superseded"}
                ),
                "unresolved_count": sum(
                    record.status not in {"duplicate", "rejected", "resolved", "superseded"}
                    for record in records
                ),
            }
        )
    return {
        "ok": not report.malformed,
        "kind": "harness_feedback_repeated_case_view",
        "groups": groups,
        "checked_count": report.checked_count,
        "errors": [
            f"{issue.path}: {issue.error_type}: {issue.message}" for issue in report.malformed
        ],
        "orientation_only": True,
        "can_update_claim_trust": False,
    }


def _build_record(
    request: HarnessFeedbackCaseRequest,
    *,
    case_id: str,
    source_fingerprint: str,
    content_fingerprint: str,
    created_at: str,
    updated_at: str,
    related_case_refs: tuple[str, ...] | None = None,
    supersedes_case_refs: tuple[str, ...] = (),
) -> HarnessFeedbackCaseRecord:
    return require_valid_harness_feedback_case(
        HarnessFeedbackCaseRecord(
            case_id=case_id,
            topic_id=request.topic_id,
            source_fingerprint=source_fingerprint,
            content_fingerprint=content_fingerprint,
            problem_type=request.problem_type,
            friction=request.friction,
            expected_behavior=request.expected_behavior,
            actual_behavior=request.actual_behavior,
            impact=request.impact,
            reproduction_steps=request.reproduction_steps,
            host_id=request.host_id,
            runtime_context=request.runtime_context,
            source_refs=request.source_refs,
            proposed_direction=request.proposed_direction,
            affected_capability=request.affected_capability,
            affected_record_family=request.affected_record_family,
            status=request.status,
            reviewer=request.reviewer,
            duplicate_of_refs=request.duplicate_of_refs,
            related_case_refs=(
                related_case_refs
                if related_case_refs is not None
                else request.related_case_refs
            ),
            supersedes_case_refs=supersedes_case_refs,
            created_at=created_at,
            updated_at=updated_at,
        )
    )


def _write_new(
    repository: RecordRepository,
    record: HarnessFeedbackCaseRecord,
) -> WriteResult:
    return repository.write(
        "harness_feedback_cases",
        record,
        body=render_harness_feedback_case(record),
    )


def _write_existing(
    repository: RecordRepository,
    record: HarnessFeedbackCaseRecord,
) -> WriteResult:
    return repository.write(
        "harness_feedback_cases",
        record,
        body=render_harness_feedback_case(record),
    )


def _case_record_or_none(read_result: Any) -> HarnessFeedbackCaseRecord | None:
    if read_result.status == "not_found":
        return None
    if read_result.status == "found" and isinstance(
        read_result.record, HarnessFeedbackCaseRecord
    ):
        return read_result.record
    if read_result.status == "found":
        raise HarnessFeedbackCaseConflict("Harness Feedback case has the wrong record type")
    return None


def _timestamp(value: datetime | None) -> str:
    current = value or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    return current.astimezone(UTC).isoformat()


def _fingerprint(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _merge_refs(*groups: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item for group in groups for item in group if item))


def _render_runtime_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
