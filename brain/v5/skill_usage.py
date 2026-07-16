"""Exact Skill-use provenance and evidence-backed patch proposals."""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from brain.v5.ids import prefixed_id
from brain.v5.models import (
    ExecutionBaselineRecord,
    FailureModeReviewResultRecord,
    SkillInstallReceiptRecord,
    SkillPackageArtifactRecord,
    SkillPatchProposalRecord,
    SkillProposalRecord,
    SkillUsageRecord,
    ToolRunRecord,
    ValidationResultRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
from brain.v5.query_index_locking import acquire_canonical_mutation_lease
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WritePolicy, WriteResult
from brain.v5.skill_install_plan_derivations import sha256_json
from brain.v5.skill_install_planning import semver


def record_skill_usage(
    ws: WorkspacePaths,
    record: SkillUsageRecord,
    *,
    actor: RecordActor,
) -> WriteResult:
    """Persist exact use and add trust-neutral backlinks to its consumers."""

    if not isinstance(record, SkillUsageRecord):
        raise TypeError("record must be a SkillUsageRecord")
    run, baseline = _validate_usage(ws, record)
    repository = RecordRepository(ws, actor=actor)
    with acquire_canonical_mutation_lease(ws):
        write = repository.write(
            "skill_usage_records",
            record,
            body="# Skill Usage\n\nExact procedural package use; no scientific trust effect.\n",
        )
        _link_usage(repository, run.run_id, "tool_run", write.record_ref)
        if baseline is not None:
            _link_usage(repository, baseline.baseline_id, "execution_baseline", write.record_ref)
    return write


def build_skill_patch_proposal(
    ws: WorkspacePaths,
    usage_refs: Sequence[PinnedRecordRef | Mapping[str, Any]],
    *,
    proposed_package_ref: PinnedRecordRef | Mapping[str, Any],
    patch_summary: str,
    patch_diff: Sequence[Mapping[str, Any]],
    actor: RecordActor,
) -> SkillPatchProposalRecord:
    """Create, but never apply, an exact package patch intent from Skill uses."""

    if not usage_refs:
        raise ValueError("Skill patch proposal requires at least one Skill usage")
    if not patch_summary.strip() or not patch_diff:
        raise ValueError("Skill patch proposal requires a summary and non-empty diff")
    pins: list[PinnedRecordRef] = []
    usages: list[SkillUsageRecord] = []
    for value in usage_refs:
        pin = _pin(value)
        version = get_record_version(ws, pin)
        if isinstance(version.record, SkillPatchProposalRecord):
            raise ValueError("Harness Feedback and prior patch proposals are inadmissible patch evidence")
        if not isinstance(version.record, SkillUsageRecord):
            raise ValueError("Harness Feedback and non-usage records are inadmissible patch evidence")
        if not pin.record_ref.startswith("skill_usage:"):
            raise ValueError("Harness Feedback and non-usage records are inadmissible patch evidence")
        _validate_usage(ws, version.record, require_current_install=True)
        pins.append(pin)
        usages.append(version.record)

    identity = {
        (item.skill_id, item.skill_name, item.semantic_version, item.package_hash)
        for item in usages
    }
    if len(identity) != 1:
        raise ValueError("Skill patch usages must describe one exact installed package")
    skill_id, skill_name, current_version, old_package_hash = next(iter(identity))
    new_pin = _pin(proposed_package_ref)
    new_proposal = get_record_version(ws, new_pin).record
    if not isinstance(new_proposal, SkillProposalRecord):
        raise ValueError("proposed_package_ref must pin a SkillProposalRecord")
    if new_proposal.skill_id != skill_id or new_proposal.name != skill_name:
        raise ValueError("Skill patch cannot change the Skill identity")
    if semver(new_proposal.semantic_version) <= semver(current_version):
        raise ValueError("Skill patch proposed version must increase monotonically")
    if new_proposal.package_hash == old_package_hash:
        raise ValueError("Skill patch must bind different old and new package hashes")

    old_refs = {_pin(item.proposal_ref) for item in usages}
    if len(old_refs) != 1:
        raise ValueError("Skill patch usages disagree on the old package proposal")
    old_pin = next(iter(old_refs))
    old_proposal = get_record_version(ws, old_pin).record
    if not isinstance(old_proposal, SkillProposalRecord):
        raise ValueError("Skill usage old package proposal is invalid")
    if (
        old_proposal.skill_id,
        old_proposal.semantic_version,
        old_proposal.package_hash,
    ) != (skill_id, current_version, old_package_hash):
        raise ValueError("Skill usage old package proposal identity drifted")

    normalized_diff = [dict(item) for item in patch_diff]
    diff_projection = {
        "skill_id": skill_id,
        "old_version": current_version,
        "new_version": new_proposal.semantic_version,
        "old_package_hash": old_package_hash,
        "new_package_hash": new_proposal.package_hash,
        "old_package_proposal_ref": asdict(old_pin),
        "new_package_proposal_ref": asdict(new_pin),
        "patch_diff": normalized_diff,
        "source_usage_refs": [asdict(pin) for pin in pins],
    }
    diff_hash = sha256_json(diff_projection)
    validation_refs = _unique_pins(
        raw for usage in usages for raw in usage.validation_refs
    )
    failure_refs = _unique_pins(raw for usage in usages for raw in usage.failure_refs)
    execution_refs = _unique_pins(
        usage.consuming_tool_run_ref for usage in usages
    )
    topic_ids = sorted({usage.topic_id for usage in usages})
    applicability = sorted(
        {
            f"{key}:{value}"
            for usage in usages
            for key, values in usage.selected_selectors.items()
            for value in _values(values)
        }
    )
    proposal = SkillPatchProposalRecord(
        proposal_id=prefixed_id("skill-patch", diff_hash, max_slug=64),
        skill_id=skill_id,
        skill_name=skill_name,
        current_version=current_version,
        proposed_version=new_proposal.semantic_version,
        old_package_hash=old_package_hash,
        new_package_hash=new_proposal.package_hash,
        old_package_proposal_ref=asdict(old_pin),
        new_package_proposal_ref=asdict(new_pin),
        patch_summary=patch_summary.strip(),
        patch_body=_patch_body(patch_summary, normalized_diff),
        patch_diff=normalized_diff,
        diff_hash=diff_hash,
        source_usage_refs=[asdict(pin) for pin in pins],
        topic_ids=topic_ids,
        supporting_records=[pin.record_ref for pin in pins],
        applicability=applicability,
        preconditions=[
            "Review the exact old/new package hashes and structured diff.",
            "Apply only through a bound apply_aitp_skill_patch checkpoint.",
        ],
        validation_refs=validation_refs,
        failure_refs=failure_refs,
        execution_refs=execution_refs,
        source_refs=[asdict(pin) for pin in pins],
        review_status="draft",
        application_status="not_applied",
        requires_human_review=True,
        can_update_claim_trust=False,
        summary_inputs_trusted=False,
        orientation_only=True,
        evidence_lane="m4_skill_usage",
        created_at=datetime.now(UTC).isoformat(),
    )
    validate_skill_patch_proposal(ws, proposal)
    RecordRepository(ws, actor=actor).write(
        "skill_patch_proposals",
        proposal,
        body="# Skill Patch Proposal\n\nReview-gated package change derived from exact Skill usage.\n",
    )
    return proposal


def validate_skill_patch_proposal(
    ws: WorkspacePaths,
    proposal: SkillPatchProposalRecord,
) -> None:
    """Re-prove every M4 patch identity and evidence projection before use."""

    if proposal.evidence_lane != "m4_skill_usage":
        raise ValueError("Harness Feedback cannot authorize a Skill patch")
    if not proposal.source_usage_refs or not proposal.patch_diff:
        raise ValueError("Skill patch requires exact usage evidence and a structured diff")
    usage_pins = [_pin(raw) for raw in proposal.source_usage_refs]
    usages: list[SkillUsageRecord] = []
    for pin in usage_pins:
        record = get_record_version(ws, pin).record
        if not isinstance(record, SkillUsageRecord) or not pin.record_ref.startswith("skill_usage:"):
            raise ValueError("Skill patch source refs must pin SkillUsageRecord values")
        _validate_usage(ws, record, require_current_install=False)
        usages.append(record)
    identities = {
        (item.skill_id, item.skill_name, item.semantic_version, item.package_hash)
        for item in usages
    }
    expected_identity = {
        (
            proposal.skill_id,
            proposal.skill_name,
            proposal.current_version,
            proposal.old_package_hash,
        )
    }
    if identities != expected_identity:
        raise ValueError("Skill patch source usage package identity drifted")
    old_pin = _pin(proposal.old_package_proposal_ref)
    new_pin = _pin(proposal.new_package_proposal_ref)
    old_package = get_record_version(ws, old_pin).record
    new_package = get_record_version(ws, new_pin).record
    if not isinstance(old_package, SkillProposalRecord) or not isinstance(
        new_package, SkillProposalRecord
    ):
        raise ValueError("Skill patch package refs must pin SkillProposalRecord values")
    if (
        old_package.skill_id,
        old_package.name,
        old_package.semantic_version,
        old_package.package_hash,
    ) != (
        proposal.skill_id,
        proposal.skill_name,
        proposal.current_version,
        proposal.old_package_hash,
    ):
        raise ValueError("Skill patch old package identity drifted")
    if (
        new_package.skill_id,
        new_package.name,
        new_package.semantic_version,
        new_package.package_hash,
    ) != (
        proposal.skill_id,
        proposal.skill_name,
        proposal.proposed_version,
        proposal.new_package_hash,
    ):
        raise ValueError("Skill patch new package identity drifted")
    if semver(proposal.proposed_version) <= semver(proposal.current_version):
        raise ValueError("Skill patch version must increase monotonically")
    diff_projection = {
        "skill_id": proposal.skill_id,
        "old_version": proposal.current_version,
        "new_version": proposal.proposed_version,
        "old_package_hash": proposal.old_package_hash,
        "new_package_hash": proposal.new_package_hash,
        "old_package_proposal_ref": asdict(old_pin),
        "new_package_proposal_ref": asdict(new_pin),
        "patch_diff": [dict(item) for item in proposal.patch_diff],
        "source_usage_refs": [asdict(pin) for pin in usage_pins],
    }
    if sha256_json(diff_projection) != proposal.diff_hash:
        raise ValueError("Skill patch structured diff hash is invalid")
    expected_validations = _unique_pins(
        raw for usage in usages for raw in usage.validation_refs
    )
    expected_failures = _unique_pins(raw for usage in usages for raw in usage.failure_refs)
    expected_runs = _unique_pins(usage.consuming_tool_run_ref for usage in usages)
    if proposal.validation_refs != expected_validations:
        raise ValueError("Skill patch validation evidence projection drifted")
    if proposal.failure_refs != expected_failures:
        raise ValueError("Skill patch failure evidence projection drifted")
    if proposal.execution_refs != expected_runs:
        raise ValueError("Skill patch execution evidence projection drifted")


def _validate_usage(
    ws: WorkspacePaths,
    record: SkillUsageRecord,
    *,
    require_current_install: bool = True,
) -> tuple[ToolRunRecord, ExecutionBaselineRecord | None]:
    receipt = get_record_version(ws, _pin(record.install_receipt_ref)).record
    if not isinstance(receipt, SkillInstallReceiptRecord) or receipt.status != "completed":
        raise ValueError("Skill usage must pin a completed install receipt")
    package_identity = (
        record.skill_id,
        record.semantic_version,
        record.package_hash,
        record.proposal_ref,
        record.package_artifact_ref,
    )
    receipt_identity = (
        receipt.skill_id,
        receipt.semantic_version,
        receipt.package_hash,
        receipt.proposal_ref,
        receipt.package_artifact_ref,
    )
    if package_identity != receipt_identity:
        raise ValueError("Skill usage package identity disagrees with the install receipt")
    if require_current_install:
        from brain.v5.skill_install_planning import snapshot_target

        current_hash, manifest = snapshot_target(Path(receipt.target_path))
        if current_hash != receipt.after_hash or (
            manifest.get("skill_id"),
            manifest.get("semantic_version"),
            manifest.get("package_hash"),
        ) != (receipt.skill_id, receipt.semantic_version, receipt.package_hash):
            raise ValueError("Skill usage install receipt is no longer the current package")
    proposal = get_record_version(ws, _pin(record.proposal_ref)).record
    if not isinstance(proposal, SkillProposalRecord):
        raise ValueError("Skill usage proposal ref is invalid")
    if (
        proposal.skill_id,
        proposal.name,
        proposal.semantic_version,
        proposal.package_hash,
    ) != (
        record.skill_id,
        record.skill_name,
        record.semantic_version,
        record.package_hash,
    ):
        raise ValueError("Skill usage package identity disagrees with the proposal")
    artifact = get_record_version(ws, _pin(record.package_artifact_ref)).record
    if not isinstance(artifact, SkillPackageArtifactRecord):
        raise ValueError("Skill usage package artifact ref is invalid")
    if (
        artifact.skill_id,
        artifact.semantic_version,
        artifact.package_hash,
    ) != (record.skill_id, record.semantic_version, record.package_hash):
        raise ValueError("Skill usage package artifact identity drifted")
    run = get_record_version(ws, _pin(record.consuming_tool_run_ref)).record
    if not isinstance(run, ToolRunRecord):
        raise ValueError("Skill usage must pin a consuming ToolRunRecord")
    if run.topic_id != record.topic_id:
        raise ValueError("Skill usage topic must match the consuming run")
    baseline = None
    if record.consuming_baseline_ref:
        baseline = get_record_version(ws, _pin(record.consuming_baseline_ref)).record
        if not isinstance(baseline, ExecutionBaselineRecord):
            raise ValueError("Skill usage baseline ref is invalid")
        if baseline.topic_id != record.topic_id:
            raise ValueError("Skill usage topic must match the consuming baseline")
        if baseline.run_ref != record.consuming_tool_run_ref["record_ref"]:
            raise ValueError("Skill usage baseline does not consume the pinned run")
    validations = [get_record_version(ws, _pin(raw)).record for raw in record.validation_refs]
    if any(not isinstance(item, ValidationResultRecord) for item in validations):
        raise ValueError("Skill usage validation refs must pin ValidationResultRecord values")
    if any(
        item.tool_run_id != run.run_id
        or (item.tool_run_ref and item.tool_run_ref != record.consuming_tool_run_ref["record_ref"])
        for item in validations
    ):
        raise ValueError("Skill usage validations must belong to the consuming run")
    if record.outcome == "success":
        if not validations or any(item.status != "passed" for item in validations):
            raise ValueError("Skill usage validated success requires passed validation refs")
    failures = [get_record_version(ws, _pin(raw)).record for raw in record.failure_refs]
    allowed_failure_types = (ValidationResultRecord, FailureModeReviewResultRecord)
    if any(not isinstance(item, allowed_failure_types) for item in failures):
        raise ValueError("Skill usage failure refs must pin typed failure evidence")
    if record.outcome in {"failure", "boundary_observed"} and not failures:
        raise ValueError("failed or boundary Skill usage requires typed failure refs")
    if not record.selected_selectors:
        raise ValueError("Skill usage must record the selected applicability selectors")
    _validate_selected_selectors(record.selected_selectors, proposal.applicability_selectors)
    return run, baseline


def _link_usage(
    repository: RecordRepository,
    record_id: str,
    kind: str,
    usage_ref: str,
) -> None:
    current = repository.read(f"{kind}:{record_id}")
    if current.status != "found" or current.record is None or current.frontmatter is None:
        raise ValueError(f"cannot link Skill usage to {kind}:{record_id}")
    refs = list(current.record.skill_usage_refs)
    if usage_ref in refs:
        return
    refs.append(usage_ref)
    revised = replace(current.record, skill_usage_refs=refs)
    from brain.v5.record_repository import _stored_content_hash

    repository.write(
        f"{kind}s" if kind == "tool_run" else "execution_baselines",
        revised,
        policy=WritePolicy(
            mode="revision",
            expected_hash=_stored_content_hash(current.frontmatter, current.body),
        ),
    )


def _pin(value: PinnedRecordRef | Mapping[str, Any]) -> PinnedRecordRef:
    if isinstance(value, PinnedRecordRef):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("exact Skill evidence refs must be pinned mappings")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=value.get("revision"),
    )


def _unique_pins(values) -> list[dict]:
    pins = {_pin(value) for value in values}
    return [asdict(pin) for pin in sorted(pins)]


def _values(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        value = value.values()
    if isinstance(value, (str, bytes)):
        value = [value]
    return [str(item) for item in value]


def _patch_body(summary: str, patch_diff: Sequence[Mapping[str, Any]]) -> str:
    rows = "\n".join(f"- `{sha256_json(dict(item))}`: {dict(item)}" for item in patch_diff)
    return f"{summary.strip()}\n\nStructured diff:\n{rows}"


def _validate_selected_selectors(selected: Mapping[str, Any], declared: Mapping[str, Any]) -> None:
    declared_values = {
        _selector_key(key): {str(item).strip().lower() for item in _values(value)}
        for key, value in declared.items()
    }
    for key, value in selected.items():
        normalized_key = _selector_key(key)
        observed = {str(item).strip().lower() for item in _values(value)}
        if normalized_key not in declared_values or not observed <= declared_values[normalized_key]:
            raise ValueError("Skill usage selected selectors are not declared by the package")


def _selector_key(value: Any) -> str:
    key = str(value).strip().lower().replace("-", "_")
    return {
        "tasks": "task",
        "domains": "domain",
        "repositories": "repository",
        "environments": "environment",
    }.get(key, key)
