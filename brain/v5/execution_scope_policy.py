"""Fail-closed scope policy for consuming exact execution dependencies."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from typing import Any, Mapping, Sequence

from brain.v5.human_approval import checkpoint_can_authorize_trust
from brain.v5.lifecycle_models import CrossTopicRelationRecord
from brain.v5.models import (
    HumanCheckpointRecord,
    ScopeRevalidationDecisionRecord,
    ValidationResultRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository


@dataclass(frozen=True)
class ExecutionScopeDecision:
    operation: str
    consumer_scope: tuple[str, ...]
    dependency_refs: tuple[PinnedRecordRef, ...]
    decision: str
    same_scope_dependency_refs: tuple[PinnedRecordRef, ...]
    foreign_dependency_refs: tuple[PinnedRecordRef, ...]
    accepted_revalidation_refs: tuple[PinnedRecordRef, ...]
    reasons: tuple[str, ...]
    checked_refs: tuple[str, ...]
    read_errors: tuple[str, ...]
    can_update_claim_trust: bool = False


def assess_execution_scope(
    ws: WorkspacePaths,
    *,
    operation: str,
    consumer_scope: Sequence[str],
    dependency_refs: Sequence[PinnedRecordRef | Mapping[str, Any]],
    revalidation_decision_refs: Sequence[PinnedRecordRef | Mapping[str, Any]] = (),
    now: datetime | None = None,
) -> ExecutionScopeDecision:
    """Assess use permission without treating a bridge as target validation."""

    if not isinstance(operation, str) or not operation.strip():
        raise ValueError("operation must be a non-empty string")
    scopes = tuple(sorted(set(_nonempty_strings(consumer_scope, "consumer_scope"))))
    consumer_topics = {
        value.partition(":")[2]
        for value in scopes
        if value.startswith("topic:") and value.partition(":")[2]
    }
    if len(consumer_topics) != 1:
        raise ValueError("consumer_scope must contain exactly one target topic")
    consumer_topic = next(iter(consumer_topics))
    dependencies = tuple(sorted({_coerce_pin(item) for item in dependency_refs}))
    if not dependencies:
        raise ValueError("dependency_refs must not be empty")
    checked: list[str] = []
    read_errors: list[str] = []
    same_scope: list[PinnedRecordRef] = []
    foreign: list[PinnedRecordRef] = []
    dependency_topics: dict[PinnedRecordRef, str] = {}
    for pinned in dependencies:
        checked.append(pinned.record_ref)
        try:
            version = get_record_version(ws, pinned)
        except Exception as exc:  # noqa: BLE001 - scope policy returns a fail-closed decision.
            read_errors.append(f"{pinned.record_ref}: {exc}")
            continue
        topic_id = _record_topic(version.record)
        dependency_topics[pinned] = topic_id
        if not topic_id or topic_id == consumer_topic:
            same_scope.append(pinned)
        else:
            foreign.append(pinned)
    if read_errors:
        return _decision(
            operation,
            scopes,
            dependencies,
            "denied",
            same_scope,
            foreign,
            [],
            ["one or more exact dependencies are unreadable"],
            checked,
            read_errors,
        )
    if not foreign:
        return _decision(
            operation,
            scopes,
            dependencies,
            "allowed",
            same_scope,
            foreign,
            [],
            ["all dependencies are target-local or scope-neutral"],
            checked,
            [],
        )

    decision_pins = tuple(
        sorted({_coerce_pin(item) for item in revalidation_decision_refs})
    )
    decisions: list[tuple[PinnedRecordRef, ScopeRevalidationDecisionRecord]] = []
    for pinned in decision_pins:
        checked.append(pinned.record_ref)
        try:
            version = get_record_version(ws, pinned)
        except Exception as exc:  # noqa: BLE001 - invalid review input denies execution.
            read_errors.append(f"{pinned.record_ref}: {exc}")
            continue
        if not isinstance(version.record, ScopeRevalidationDecisionRecord):
            read_errors.append(f"{pinned.record_ref}: not a scope revalidation decision")
            continue
        decisions.append((pinned, version.record))
    if read_errors:
        return _decision(
            operation,
            scopes,
            dependencies,
            "denied",
            same_scope,
            foreign,
            [],
            ["one or more revalidation decisions are unreadable"],
            checked,
            read_errors,
        )

    superseded, supersession_errors = _superseded_decision_pins(ws)
    if supersession_errors:
        return _decision(
            operation,
            scopes,
            dependencies,
            "denied",
            same_scope,
            foreign,
            [],
            ["scope revalidation supersession state is unreadable"],
            checked,
            supersession_errors,
        )

    current_time = _utc(now)
    accepted: set[PinnedRecordRef] = set()
    uncovered = set(foreign)
    reasons: list[str] = []
    for decision_pin, record in decisions:
        if decision_pin in superseded:
            reasons.append("scope revalidation decision has been superseded")
            continue
        covered, reason, error = _covered_foreign_dependencies(
            ws,
            decision_pin=decision_pin,
            record=record,
            operation=operation.strip(),
            consumer_topic=consumer_topic,
            consumer_scope=scopes,
            foreign=uncovered,
            dependency_topics=dependency_topics,
            now=current_time,
            checked=checked,
        )
        if error:
            read_errors.append(error)
            continue
        if reason:
            reasons.append(reason)
        if covered:
            uncovered.difference_update(covered)
            accepted.add(decision_pin)
    if read_errors:
        return _decision(
            operation,
            scopes,
            dependencies,
            "denied",
            same_scope,
            foreign,
            accepted,
            reasons or ["scope revalidation verification failed"],
            checked,
            read_errors,
        )
    if uncovered:
        if not decisions:
            reasons.append("bridge presence is not target validation")
        return _decision(
            operation,
            scopes,
            dependencies,
            "requires_revalidation",
            same_scope,
            foreign,
            accepted,
            reasons or ["foreign dependencies lack target-side revalidation"],
            checked,
            [],
        )
    return _decision(
        operation,
        scopes,
        dependencies,
        "allowed",
        same_scope,
        foreign,
        accepted,
        ["every foreign dependency has exact target-side revalidation"],
        checked,
        [],
    )


def _superseded_decision_pins(
    ws: WorkspacePaths,
) -> tuple[set[PinnedRecordRef], list[str]]:
    repository = RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="system",
            actor_id="execution-scope-policy",
            host="local",
        ),
    )
    report = repository.list("scope_revalidation_decisions")
    errors = [
        f"{issue.path}: {issue.error_type}: {issue.message}"
        for issue in report.malformed
    ]
    superseded: set[PinnedRecordRef] = set()
    successors: dict[PinnedRecordRef, list[str]] = {}
    for record in report.records:
        if not isinstance(record, ScopeRevalidationDecisionRecord):
            errors.append("scope_revalidation_decisions contains an unexpected record type")
            continue
        if not record.supersedes_decision_ref:
            continue
        try:
            prior = PinnedRecordRef(
                record_ref=record.supersedes_decision_ref,
                content_hash=record.supersedes_decision_hash,
                revision=record.supersedes_decision_revision,
            )
            superseded.add(prior)
            successors.setdefault(prior, []).append(record.decision_id)
        except (TypeError, ValueError) as exc:
            errors.append(f"{record.decision_id}: invalid supersession pin: {exc}")
    for prior, decision_ids in successors.items():
        if len(decision_ids) > 1:
            errors.append(
                f"{prior.record_ref}: multiple successors for exact scope decision"
            )
    return superseded, errors


def _covered_foreign_dependencies(
    ws: WorkspacePaths,
    *,
    decision_pin: PinnedRecordRef,
    record: ScopeRevalidationDecisionRecord,
    operation: str,
    consumer_topic: str,
    consumer_scope: tuple[str, ...],
    foreign: set[PinnedRecordRef],
    dependency_topics: Mapping[PinnedRecordRef, str],
    now: datetime,
    checked: list[str],
) -> tuple[set[PinnedRecordRef], str, str]:
    if record.decision != "approved":
        return set(), "scope revalidation decision is not approved", ""
    if _parse_timestamp(record.expires_at) <= now:
        return set(), "scope revalidation decision has expired", ""
    if operation not in record.allowed_operations:
        return set(), "operation is outside the reviewed applicability", ""
    if record.topic_id != consumer_topic or not set(consumer_scope) <= set(record.target_scope_refs):
        return set(), "consumer scope is outside the reviewed target", ""
    try:
        bridge_pin = PinnedRecordRef(
            record_ref=record.bridge_ref,
            content_hash=record.bridge_hash,
            revision=record.bridge_revision,
        )
        checked.append(bridge_pin.record_ref)
        bridge = get_record_version(ws, bridge_pin).record
    except Exception as exc:  # noqa: BLE001 - malformed canonical review denies use.
        return set(), "", f"{decision_pin.record_ref}: bridge pin is invalid: {exc}"
    if not isinstance(bridge, CrossTopicRelationRecord):
        return set(), "", f"{decision_pin.record_ref}: bridge is not cross-topic"
    if bridge.status not in {"reviewed", "approved"} or bridge.target_topic_id != consumer_topic:
        return set(), "bridge is not approved for the consumer topic", ""
    try:
        source_refs = {_coerce_pin(item) for item in record.source_refs}
        validation_refs = [_coerce_pin(item) for item in record.validation_refs]
        checkpoint_refs = [_coerce_pin(item) for item in record.checkpoint_refs]
    except (TypeError, ValueError) as exc:
        return set(), "", f"{decision_pin.record_ref}: invalid pinned review refs: {exc}"
    if not validation_refs or not checkpoint_refs:
        return set(), "", f"{decision_pin.record_ref}: review basis is incomplete"
    for validation_ref in validation_refs:
        checked.append(validation_ref.record_ref)
        try:
            validation = get_record_version(ws, validation_ref).record
        except Exception as exc:  # noqa: BLE001
            return set(), "", f"{decision_pin.record_ref}: validation pin is invalid: {exc}"
        if (
            not isinstance(validation, ValidationResultRecord)
            or validation.status != "passed"
            or validation.topic_id != consumer_topic
        ):
            return set(), "", f"{decision_pin.record_ref}: validation is not target-passed"
    for checkpoint_ref in checkpoint_refs:
        checked.append(checkpoint_ref.record_ref)
        try:
            checkpoint = get_record_version(ws, checkpoint_ref).record
        except Exception as exc:  # noqa: BLE001
            return set(), "", f"{decision_pin.record_ref}: checkpoint pin is invalid: {exc}"
        if (
            not isinstance(checkpoint, HumanCheckpointRecord)
            or checkpoint.action != "approve_scope_revalidation"
            or not checkpoint_can_authorize_trust(checkpoint)
        ):
            return set(), "", f"{decision_pin.record_ref}: checkpoint is not authorizing"
    covered = {
        dependency
        for dependency in foreign
        if dependency in source_refs
        and dependency_topics.get(dependency) == bridge.source_topic_id
    }
    return covered, "", ""


def _decision(
    operation: str,
    scopes: tuple[str, ...],
    dependencies: tuple[PinnedRecordRef, ...],
    decision: str,
    same_scope: Sequence[PinnedRecordRef],
    foreign: Sequence[PinnedRecordRef],
    accepted: Sequence[PinnedRecordRef],
    reasons: Sequence[str],
    checked: Sequence[str],
    read_errors: Sequence[str],
) -> ExecutionScopeDecision:
    return ExecutionScopeDecision(
        operation=operation.strip(),
        consumer_scope=scopes,
        dependency_refs=dependencies,
        decision=decision,
        same_scope_dependency_refs=tuple(sorted(set(same_scope))),
        foreign_dependency_refs=tuple(sorted(set(foreign))),
        accepted_revalidation_refs=tuple(sorted(set(accepted))),
        reasons=tuple(dict.fromkeys(reasons)),
        checked_refs=tuple(dict.fromkeys(checked)),
        read_errors=tuple(read_errors),
    )


def _record_topic(record: Any) -> str:
    if is_dataclass(record):
        return str(asdict(record).get("topic_id") or "")
    if isinstance(record, Mapping):
        return str(record.get("topic_id") or "")
    return ""


def _coerce_pin(value: PinnedRecordRef | Mapping[str, Any]) -> PinnedRecordRef:
    if isinstance(value, PinnedRecordRef):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("execution scope refs must be exact pinned refs")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=value.get("revision"),
    )


def _nonempty_strings(values: Sequence[str], field_name: str) -> list[str]:
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must contain non-empty strings")
        normalized.append(value.strip())
    return normalized


def _parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("scope decision expires_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("scope decision expires_at must include a timezone")
    return parsed.astimezone(UTC)


def _utc(value: datetime | None) -> datetime:
    current = value or datetime.now(UTC)
    if current.tzinfo is None:
        raise ValueError("now must include a timezone")
    return current.astimezone(UTC)
