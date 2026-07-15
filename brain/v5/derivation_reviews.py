"""Hash-bound derivation reviews, supersession, and trust-neutral status projection."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any, Mapping, Sequence

from brain.v5.derivation_contracts import DerivationStatusProjection
from brain.v5.derivation_models import (
    DerivationChainRecord,
    DerivationReviewRecord,
    DerivationStepRecord,
)
from brain.v5.derivations import validate_derivation_dag
from brain.v5.models import HumanCheckpointRecord, ToolRunRecord, ValidationResultRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WriteResult


def record_derivation_review(
    ws: WorkspacePaths,
    review: DerivationReviewRecord,
    *,
    actor: RecordActor,
) -> WriteResult:
    """Record a new review; revision is represented only through supersession."""

    if review.supersedes_review_ref:
        raise ValueError("use supersede_derivation_review for review replacement")
    _validate_review(ws, review)
    return _write_review(ws, review, actor=actor)


def supersede_derivation_review(
    ws: WorkspacePaths,
    prior_review_ref: PinnedRecordRef | Mapping[str, Any],
    replacement: DerivationReviewRecord,
    *,
    actor: RecordActor,
) -> WriteResult:
    """Append one exact replacement and reject branched review history."""

    prior_pin = _coerce_pin(prior_review_ref)
    if pin_current_record(ws, prior_pin.record_ref) != prior_pin:
        raise ValueError("prior derivation review ref is stale")
    prior = get_record_version(ws, prior_pin).record
    if not isinstance(prior, DerivationReviewRecord):
        raise ValueError("prior review ref must pin DerivationReviewRecord")
    if _coerce_optional_pin(replacement.supersedes_review_ref) != prior_pin:
        raise ValueError("replacement must bind the exact prior derivation review")
    if replacement.topic_id != prior.topic_id or replacement.claim_id != prior.claim_id:
        raise ValueError("replacement review must preserve topic and claim")
    if _coerce_pin(replacement.chain_ref) != _coerce_pin(prior.chain_ref):
        raise ValueError("replacement review must preserve the exact derivation chain revision")
    successors = _successors(
        ws,
        chain_ref=_coerce_pin(prior.chain_ref),
    ).get(prior_pin, [])
    if successors:
        raise ValueError("prior derivation review already has a successor")
    _validate_review(ws, replacement)
    return _write_review(ws, replacement, actor=actor)


def project_derivation_status(
    ws: WorkspacePaths,
    chain_ref: PinnedRecordRef | Mapping[str, Any],
) -> DerivationStatusProjection:
    """Derive structural, source, review, and validation status without mutation."""

    chain_pin = _coerce_pin(chain_ref)
    blocking: list[str] = []
    try:
        if pin_current_record(ws, chain_pin.record_ref) != chain_pin:
            raise ValueError("derivation chain ref is stale")
        chain = get_record_version(ws, chain_pin).record
        if not isinstance(chain, DerivationChainRecord):
            raise ValueError("chain_ref must pin DerivationChainRecord")
        validate_derivation_dag(ws, chain)
        steps = [_current_step(ws, pin) for pin in _pins(chain.ordered_step_refs)]
    except Exception as exc:  # noqa: BLE001 - projection fails closed on any stale graph input.
        return DerivationStatusProjection(
            chain_ref=chain_pin.record_ref,
            structurally_closed=False,
            source_complete=False,
            reviewed=False,
            validated=False,
            blocking_reasons=(str(exc),),
        )
    structurally_closed = chain.status == "structurally_closed"
    source_complete = bool(chain.source_refs) and all(step.source_anchor_refs for step in steps)
    repository = _repository(ws)
    report = repository.list("derivation_reviews")
    if report.malformed:
        blocking.append("derivation review registry contains malformed records")
    review_pins = {
        review.review_id: pin_current_record(ws, f"derivation_review:{review.review_id}")
        for review in report.records
        if isinstance(review, DerivationReviewRecord)
    }
    successors, invalid_successors = _projection_successors(
        report.records,
        review_pins,
    )
    superseded = set(successors)
    relevant: list[tuple[PinnedRecordRef, DerivationReviewRecord]] = []
    target_history_invalid = False
    for review in report.records:
        if not isinstance(review, DerivationReviewRecord):
            blocking.append("derivation review registry contains an unexpected record type")
            continue
        if review.review_id in invalid_successors:
            try:
                if _coerce_pin(review.chain_ref) == chain_pin:
                    blocking.append(
                        f"derivation review has invalid supersedes pin: {review.review_id}"
                    )
                    target_history_invalid = True
            except (TypeError, ValueError):
                pass
            continue
        try:
            if _coerce_pin(review.chain_ref) == chain_pin:
                review_pin = review_pins[review.review_id]
                if review_pin not in superseded:
                    relevant.append((review_pin, review))
        except (TypeError, ValueError):
            blocking.append(f"derivation review has invalid chain pin: {review.review_id}")
    if target_history_invalid:
        relevant = []
    if len(relevant) > 1:
        blocking.append("derivation review history has multiple active branches")
        relevant = []
    active_pin, active = relevant[0] if relevant else (None, None)
    if active is not None:
        try:
            _validate_review(ws, active)
        except Exception as exc:  # noqa: BLE001 - repository bypasses fail closed.
            blocking.append(f"active derivation review is invalid: {exc}")
            active_pin, active = None, None
    reviewed = bool(active and active.decision == "passed" and structurally_closed and source_complete)
    validated = reviewed and _review_validation_is_current_and_passed(ws, active)
    return DerivationStatusProjection(
        chain_ref=chain_pin.record_ref,
        structurally_closed=structurally_closed,
        source_complete=source_complete,
        reviewed=reviewed,
        validated=validated,
        active_review_ref=active_pin.record_ref if active_pin else "",
        blocking_reasons=tuple(dict.fromkeys(blocking)),
    )


def _validate_review(ws: WorkspacePaths, review: DerivationReviewRecord) -> None:
    chain_pin = _require_current(ws, _coerce_pin(review.chain_ref), "chain")
    chain = get_record_version(ws, chain_pin).record
    if not isinstance(chain, DerivationChainRecord):
        raise ValueError("derivation review chain_ref must pin DerivationChainRecord")
    if chain.topic_id != review.topic_id or chain.claim_id != review.claim_id or chain.program_id != review.program_id:
        raise ValueError("derivation review scope must match chain topic, claim, and program")
    expected_steps = _pins(chain.ordered_step_refs)
    review_steps = _pins(review.step_refs)
    if review_steps != expected_steps:
        raise ValueError("derivation review step refs must exactly cover the chain steps")
    steps = [_current_step(ws, pin) for pin in review_steps]
    required_anchors = {
        *_pins(chain.source_refs),
        *(pin for step in steps for pin in _pins(step.source_anchor_refs)),
    }
    reviewed_anchors = set(_pins(review.source_anchor_refs))
    if not required_anchors or not required_anchors <= reviewed_anchors:
        raise ValueError("derivation review must cover every exact source anchor")
    for pin in reviewed_anchors:
        _require_current(ws, pin, "source anchor")
    checkpoint_pin = _require_current(ws, _coerce_pin(review.checkpoint_ref), "checkpoint")
    checkpoint = get_record_version(ws, checkpoint_pin).record
    if (
        not isinstance(checkpoint, HumanCheckpointRecord)
        or checkpoint.topic_id != review.topic_id
        or checkpoint.claim_id != review.claim_id
        or checkpoint.status != "decided"
        or checkpoint.action != "review_derivation"
    ):
        raise ValueError("derivation review checkpoint is not a decided matching review checkpoint")
    if review.decision == "passed" and checkpoint.decision not in {"approve", "passed"}:
        raise ValueError("passed derivation review requires an approving checkpoint")
    if review.decision == "passed":
        validate_derivation_dag(ws, chain)
        if chain.status != "structurally_closed":
            raise ValueError("passed derivation review requires structurally_closed chain")
    _validate_check_refs(ws, review)


def _validate_check_refs(ws: WorkspacePaths, review: DerivationReviewRecord) -> None:
    for pin in _pins(review.validation_check_refs):
        _require_current(ws, pin, "validation check")
        record = get_record_version(ws, pin).record
        if not isinstance(record, ValidationResultRecord):
            raise ValueError("derivation validation check must pin ValidationResultRecord")
        _require_review_scope(record, review, "validation check")
    for pin in _pins(review.tool_run_check_refs):
        _require_current(ws, pin, "tool-run check")
        record = get_record_version(ws, pin).record
        if not isinstance(record, ToolRunRecord):
            raise ValueError("derivation tool-run check must pin ToolRunRecord")
        _require_review_scope(record, review, "tool-run check")


def _review_validation_is_current_and_passed(
    ws: WorkspacePaths,
    review: DerivationReviewRecord,
) -> bool:
    pins = _pins(review.validation_check_refs)
    if not pins:
        return False
    try:
        for pin in pins:
            if pin_current_record(ws, pin.record_ref) != pin:
                return False
            record = get_record_version(ws, pin).record
            if not isinstance(record, ValidationResultRecord) or record.status != "passed":
                return False
        for pin in _pins(review.tool_run_check_refs):
            if pin_current_record(ws, pin.record_ref) != pin:
                return False
            if not isinstance(get_record_version(ws, pin).record, ToolRunRecord):
                return False
    except Exception:  # noqa: BLE001 - projection is fail-closed.
        return False
    return True


def _successors(
    ws: WorkspacePaths,
    records: Sequence[Any] | None = None,
    *,
    chain_ref: PinnedRecordRef | None = None,
) -> dict[PinnedRecordRef, list[str]]:
    reviews = records if records is not None else _repository(ws).list("derivation_reviews").records
    review_pins = {
        review.review_id: pin_current_record(ws, f"derivation_review:{review.review_id}")
        for review in reviews
        if isinstance(review, DerivationReviewRecord)
    }
    reviews_by_pin = {
        review_pins[review.review_id]: review
        for review in reviews
        if isinstance(review, DerivationReviewRecord)
    }
    result: dict[PinnedRecordRef, list[str]] = {}
    for review in reviews:
        if not isinstance(review, DerivationReviewRecord) or not review.supersedes_review_ref:
            continue
        try:
            successor_chain = _coerce_pin(review.chain_ref)
        except (TypeError, ValueError):
            continue
        if chain_ref is not None and successor_chain != chain_ref:
            continue
        try:
            prior = _coerce_pin(review.supersedes_review_ref)
        except (TypeError, ValueError):
            if chain_ref is None:
                raise
            raise ValueError("derivation review history has invalid supersedes history")
        predecessor = reviews_by_pin.get(prior)
        try:
            predecessor_chain = _coerce_pin(predecessor.chain_ref) if predecessor else None
        except (TypeError, ValueError):
            predecessor_chain = None
        if predecessor_chain != successor_chain:
            if chain_ref is not None:
                raise ValueError("derivation review history has invalid supersedes history")
            continue
        result.setdefault(prior, []).append(review.review_id)
    return result


def _projection_successors(
    records: Sequence[Any],
    review_pins: Mapping[str, PinnedRecordRef],
) -> tuple[dict[PinnedRecordRef, list[str]], set[str]]:
    reviews_by_pin = {
        review_pins[review.review_id]: review
        for review in records
        if isinstance(review, DerivationReviewRecord)
    }
    result: dict[PinnedRecordRef, list[str]] = {}
    invalid: set[str] = set()
    for review in records:
        if not isinstance(review, DerivationReviewRecord) or not review.supersedes_review_ref:
            continue
        try:
            successor_chain = _coerce_pin(review.chain_ref)
            prior = _coerce_pin(review.supersedes_review_ref)
        except (TypeError, ValueError):
            invalid.add(review.review_id)
            continue
        predecessor = reviews_by_pin.get(prior)
        try:
            predecessor_chain = _coerce_pin(predecessor.chain_ref) if predecessor else None
        except (TypeError, ValueError):
            predecessor_chain = None
        if predecessor_chain != successor_chain:
            invalid.add(review.review_id)
            continue
        result.setdefault(prior, []).append(review.review_id)
    return result, invalid


def _current_step(ws: WorkspacePaths, pin: PinnedRecordRef) -> DerivationStepRecord:
    _require_current(ws, pin, "step")
    record = get_record_version(ws, pin).record
    if not isinstance(record, DerivationStepRecord):
        raise ValueError("derivation review step ref must pin DerivationStepRecord")
    return record


def _require_current(
    ws: WorkspacePaths,
    pin: PinnedRecordRef,
    label: str,
) -> PinnedRecordRef:
    if pin_current_record(ws, pin.record_ref) != pin:
        raise ValueError(f"derivation review {label} ref is stale")
    return pin


def _require_review_scope(record: Any, review: DerivationReviewRecord, label: str) -> None:
    data = asdict(record) if hasattr(record, "__dataclass_fields__") else {}
    if data.get("topic_id") != review.topic_id or data.get("claim_id") != review.claim_id:
        raise ValueError(f"derivation review {label} has foreign scope")


def _write_review(
    ws: WorkspacePaths,
    review: DerivationReviewRecord,
    *,
    actor: RecordActor,
) -> WriteResult:
    if not review.created_at:
        review.created_at = datetime.now(UTC).isoformat()
    return RecordRepository(ws, actor=actor).write(
        "derivation_reviews",
        review,
        body=(
            f"# Derivation Review: {review.review_id}\n\n"
            f"Decision: `{review.decision}`\n\n{review.summary}\n"
        ),
    )


def _repository(ws: WorkspacePaths) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="system",
            actor_id="derivation-review-read",
            host="aitp",
        ),
    )


def _pins(values: Sequence[Mapping[str, Any]]) -> tuple[PinnedRecordRef, ...]:
    return tuple(_coerce_pin(value) for value in values)


def _coerce_optional_pin(value: Mapping[str, Any] | None) -> PinnedRecordRef | None:
    return None if not value else _coerce_pin(value)


def _coerce_pin(value: PinnedRecordRef | Mapping[str, Any]) -> PinnedRecordRef:
    if isinstance(value, PinnedRecordRef):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("derivation review refs must be exact pinned mappings")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=value.get("revision"),
    )
