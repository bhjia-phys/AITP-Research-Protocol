"""Derived, orientation-only matching for reviewed procedural Skill packages."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from brain.v5.models import (
    HumanCheckpointRecord,
    ScopeRevalidationDecisionRecord,
    SkillInstallReceiptRecord,
    SkillProposalRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository


@dataclass(frozen=True)
class SkillApplicabilityRequest:
    domains: tuple[str, ...] = ()
    tasks: tuple[str, ...] = ()
    software: tuple[str, ...] = ()
    repositories: tuple[str, ...] = ()
    code_paths: tuple[str, ...] = ()
    symbols: tuple[str, ...] = ()
    physics_objects: tuple[str, ...] = ()
    formulas: tuple[str, ...] = ()
    parameters: tuple[str, ...] = ()
    environments: tuple[str, ...] = ()
    clusters: tuple[str, ...] = ()
    focus_kinds: tuple[str, ...] = ()
    focus_refs: tuple[str, ...] = ()
    topic_ids: tuple[str, ...] = ()
    program_ids: tuple[str, ...] = ()
    input_kinds: tuple[str, ...] = ()
    available_record_refs: tuple[str, ...] = ()
    override_refs: tuple[PinnedRecordRef | Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class SelectorReason:
    selector: str
    required: tuple[str, ...]
    observed: tuple[str, ...]
    matched: bool
    reason: str
    confidence: float


@dataclass(frozen=True)
class ApplicableSkillMatch:
    skill_id: str
    name: str
    semantic_version: str
    package_hash: str
    proposal_ref: dict
    install_receipt_ref: dict
    selector_reasons: dict[str, SelectorReason]
    confidence: float
    matched: bool
    match_source: str = "derived"
    override_ref: dict = field(default_factory=dict)
    orientation_only: bool = True
    can_update_claim_trust: bool = False


@dataclass(frozen=True)
class SkillApplicabilityResult:
    matches: tuple[ApplicableSkillMatch, ...]
    rejected: tuple[ApplicableSkillMatch, ...]
    checked_count: int
    orientation_only: bool = True
    can_update_claim_trust: bool = False


_SELECTOR_REQUEST_FIELDS = {
    "domain": "domains",
    "task": "tasks",
    "task_kind": "tasks",
    "software": "software",
    "repository": "repositories",
    "code_path": "code_paths",
    "symbol": "symbols",
    "physics_object": "physics_objects",
    "formula": "formulas",
    "parameter": "parameters",
    "environment": "environments",
    "cluster": "clusters",
    "focus_kind": "focus_kinds",
    "focus_ref": "focus_refs",
    "topic": "topic_ids",
    "topic_id": "topic_ids",
    "program": "program_ids",
    "program_id": "program_ids",
    "required_inputs": "input_kinds",
    "required_records": "available_record_refs",
}


def match_applicable_skills(
    ws: WorkspacePaths,
    request: SkillApplicabilityRequest,
) -> SkillApplicabilityResult:
    """Match canonical package selectors without loading Skill bodies."""

    if not isinstance(request, SkillApplicabilityRequest):
        raise TypeError("request must be a SkillApplicabilityRequest")
    repository = _repository(ws)
    installed = _installed_proposals(ws, repository)
    override_versions = _load_overrides(ws, request.override_refs)
    matches: list[ApplicableSkillMatch] = []
    rejected: list[ApplicableSkillMatch] = []
    for receipt_ref, receipt, proposal_ref, proposal in installed:
        selectors = _proposal_selectors(proposal)
        reasons = evaluate_skill_selectors(selectors, request)
        derived_match = all(reason.matched for reason in reasons.values())
        override = _applicable_override(
            ws,
            receipt_ref,
            request,
            override_versions,
        )
        source = "derived"
        override_ref: dict[str, Any] = {}
        matched = derived_match
        if override is not None:
            override_pin, override_record = override
            source = "reviewed_override"
            override_ref = asdict(override_pin)
            matched = override_record.decision == "approved"
        confidence = 1.0 if matched else _confidence(reasons)
        item = ApplicableSkillMatch(
            skill_id=proposal.skill_id,
            name=proposal.name,
            semantic_version=proposal.semantic_version,
            package_hash=proposal.package_hash,
            proposal_ref=asdict(proposal_ref),
            install_receipt_ref=asdict(receipt_ref),
            selector_reasons=reasons,
            confidence=confidence,
            matched=matched,
            match_source=source,
            override_ref=override_ref,
        )
        (matches if matched else rejected).append(item)
    return SkillApplicabilityResult(
        matches=tuple(matches),
        rejected=tuple(rejected),
        checked_count=len(installed),
    )


def evaluate_skill_selectors(
    selectors: Mapping[str, Any],
    request: SkillApplicabilityRequest,
) -> dict[str, SelectorReason]:
    normalized = _normalize_selectors(selectors)
    reasons: dict[str, SelectorReason] = {}
    for selector, required in normalized.items():
        if selector == "exclusions":
            observed = _all_request_values(request)
            overlap = sorted(set(required) & set(observed))
            matched = not overlap
            reasons[selector] = SelectorReason(
                selector=selector,
                required=required,
                observed=observed,
                matched=matched,
                reason=(
                    "no declared exclusion is present"
                    if matched
                    else f"excluded values are present: {', '.join(overlap)}"
                ),
                confidence=1.0,
            )
            continue
        field_name = _SELECTOR_REQUEST_FIELDS.get(selector)
        if field_name is None:
            reasons[selector] = SelectorReason(
                selector=selector,
                required=required,
                observed=(),
                matched=False,
                reason="unsupported selector fails closed",
                confidence=1.0,
            )
            continue
        observed = _normalized_values(getattr(request, field_name))
        if selector in {"required_inputs", "required_records"}:
            missing = sorted(set(required) - set(observed))
            matched = not missing
            detail = (
                "all required values are available"
                if matched
                else f"missing required values: {', '.join(missing)}"
            )
        else:
            overlap = sorted(set(required) & set(observed))
            matched = bool(overlap)
            detail = (
                f"matched values: {', '.join(overlap)}"
                if matched
                else "no requested value matches the declared selector"
            )
        reasons[selector] = SelectorReason(
            selector=selector,
            required=required,
            observed=observed,
            matched=matched,
            reason=detail,
            confidence=1.0,
        )
    return reasons


def _proposal_selectors(proposal: SkillProposalRecord) -> Mapping[str, Any]:
    manifest_selectors = proposal.manifest.get("applicability_selectors")
    if not isinstance(manifest_selectors, Mapping):
        raise ValueError(f"Skill proposal {proposal.proposal_id} lacks manifest selectors")
    if dict(manifest_selectors) != proposal.applicability_selectors:
        raise ValueError(f"Skill proposal {proposal.proposal_id} selector projections disagree")
    return manifest_selectors


def _normalize_selectors(selectors: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    normalized: dict[str, list[str]] = {}
    for raw_key, raw_value in selectors.items():
        key = str(raw_key).strip().lower().replace("-", "_")
        canonical = {
            "tasks": "task",
            "domains": "domain",
            "repositories": "repository",
            "code_paths": "code_path",
            "symbols": "symbol",
            "physics_objects": "physics_object",
            "formulas": "formula",
            "parameters": "parameter",
            "environments": "environment",
            "clusters": "cluster",
            "topics": "topic",
            "programs": "program",
        }.get(key, key)
        values = raw_value.values() if isinstance(raw_value, Mapping) else raw_value
        if isinstance(values, (str, bytes)):
            values = [values]
        if not isinstance(values, Sequence):
            raise ValueError(f"Skill selector {raw_key!r} must be a sequence or mapping")
        items = list(_normalized_values(values))
        if not items:
            raise ValueError(f"Skill selector {raw_key!r} must not be empty")
        normalized.setdefault(canonical, []).extend(items)
    return {key: tuple(sorted(set(values))) for key, values in normalized.items()}


def _normalized_values(values: Sequence[Any]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                str(value).strip().replace("\\", "/").lower()
                for value in values
                if str(value).strip()
            }
        )
    )


def _all_request_values(request: SkillApplicabilityRequest) -> tuple[str, ...]:
    values: list[Any] = []
    for field_name in _SELECTOR_REQUEST_FIELDS.values():
        values.extend(getattr(request, field_name))
    return _normalized_values(values)


def _confidence(reasons: Mapping[str, SelectorReason]) -> float:
    if not reasons:
        return 0.0
    return round(sum(reason.matched for reason in reasons.values()) / len(reasons), 6)


def _load_overrides(ws, refs):
    versions: list[tuple[PinnedRecordRef, ScopeRevalidationDecisionRecord]] = []
    for value in refs:
        try:
            pin = value if isinstance(value, PinnedRecordRef) else PinnedRecordRef(**dict(value))
            record = get_record_version(ws, pin).record
        except Exception as exc:  # noqa: BLE001 - invalid review inputs fail closed.
            raise ValueError("override must pin a ScopeRevalidationDecisionRecord") from exc
        if not isinstance(record, ScopeRevalidationDecisionRecord):
            raise ValueError("override must pin a ScopeRevalidationDecisionRecord")
        versions.append((pin, record))
    return versions


def _applicable_override(ws, receipt_ref, request, overrides):
    for pin, record in overrides:
        if not _valid_override(ws, receipt_ref, request, record):
            continue
        return pin, record
    return None


def _valid_override(ws, receipt_ref, request, record) -> bool:
    if record.decision not in {"approved", "rejected"}:
        return False
    if (
        record.bridge_ref != receipt_ref.record_ref
        or record.bridge_hash != receipt_ref.content_hash
        or record.bridge_revision != receipt_ref.revision
    ):
        return False
    if "use_skill" not in record.allowed_operations:
        return False
    if (
        not record.target_scope_refs
        or not record.applicability_conditions
        or not record.source_refs
        or not record.validation_refs
    ):
        return False
    if record.topic_id and f"topic:{record.topic_id}" not in record.target_scope_refs:
        return False
    if request.topic_ids and record.topic_id not in request.topic_ids:
        return False
    if request.program_ids and record.program_id not in request.program_ids:
        return False
    try:
        expires = datetime.fromisoformat(record.expires_at)
        if expires.tzinfo is None or expires.astimezone(UTC) <= datetime.now(UTC):
            return False
    except ValueError:
        return False
    if not record.checkpoint_refs:
        return False
    try:
        source_pins = [PinnedRecordRef(**dict(raw)) for raw in record.source_refs]
        validation_pins = [PinnedRecordRef(**dict(raw)) for raw in record.validation_refs]
        for source_pin in (*source_pins, *validation_pins):
            get_record_version(ws, source_pin)
    except Exception:  # noqa: BLE001 - overrides require resolvable exact evidence.
        return False
    if receipt_ref not in source_pins:
        return False
    for raw in record.checkpoint_refs:
        try:
            checkpoint = get_record_version(ws, PinnedRecordRef(**dict(raw))).record
        except Exception:  # noqa: BLE001 - unresolved checkpoints cannot authorize overrides.
            return False
        if not isinstance(checkpoint, HumanCheckpointRecord):
            return False
        if not (
            checkpoint.status == "decided"
            and checkpoint.decision == "approve"
            and checkpoint.decision_verified
            and checkpoint.decision_receipt_hash
            and checkpoint.action == "approve_scope_revalidation"
            and checkpoint.effect_policy == "scope_revalidation_only"
        ):
            return False
    return True


def _installed_proposals(ws, repository):
    from brain.v5.skill_install_planning import snapshot_target

    current_by_target: dict[
        str,
        tuple[PinnedRecordRef, SkillInstallReceiptRecord, PinnedRecordRef, SkillProposalRecord],
    ] = {}
    receipts = [
        item
        for item in repository.list("skill_install_receipts").records
        if isinstance(item, SkillInstallReceiptRecord) and item.status == "completed"
    ]
    for receipt in receipts:
        receipt_ref = pin_current_record(
            ws,
            f"skill_install_receipt:{receipt.receipt_id}",
        )
        try:
            current_hash, manifest = snapshot_target(Path(receipt.target_path))
            proposal_ref = PinnedRecordRef(**dict(receipt.proposal_ref))
            proposal = get_record_version(ws, proposal_ref).record
        except Exception:  # noqa: BLE001 - stale or unreadable installs are not applicable.
            continue
        if not isinstance(proposal, SkillProposalRecord):
            continue
        if current_hash != receipt.after_hash:
            continue
        if (
            manifest.get("skill_id") != receipt.skill_id
            or manifest.get("semantic_version") != receipt.semantic_version
            or manifest.get("package_hash") != receipt.package_hash
        ):
            continue
        if (
            proposal.skill_id,
            proposal.semantic_version,
            proposal.package_hash,
        ) != (
            receipt.skill_id,
            receipt.semantic_version,
            receipt.package_hash,
        ):
            continue
        candidate = (receipt_ref, receipt, proposal_ref, proposal)
        previous = current_by_target.get(receipt.target_path)
        if previous is None or (receipt.completed_at, receipt.receipt_id) > (
            previous[1].completed_at,
            previous[1].receipt_id,
        ):
            current_by_target[receipt.target_path] = candidate
    return sorted(
        current_by_target.values(),
        key=lambda item: (item[3].skill_id, item[3].semantic_version, item[0].record_ref),
    )


def _repository(ws: WorkspacePaths) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="skill-applicability", host="aitp-v5"),
    )
