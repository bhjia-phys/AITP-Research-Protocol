"""Assess procedural independence, failure coverage, fixtures, and Skill overlap."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

from brain.v5.checkpoint_bindings import (
    CheckpointSubjectBinding,
    hash_action_payload,
    validate_checkpoint_binding,
)
from brain.v5.domain_packs import builtin_domain_packs
from brain.v5.ids import prefixed_id
from brain.v5.models import HumanCheckpointRecord, SkillDistillationCandidateRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WriteResult
from brain.v5.skill_distillation_contracts import require_valid_skill_distillation_candidate
from brain.v5.skill_models import SkillReadinessReportRecord
from brain.v5.skill_readiness_contracts import require_valid_skill_readiness_report


_MAX_MANIFEST_BYTES = 256 * 1024
_OVERLAP_PRIORITY = {"new": 0, "extension_candidate": 1, "duplicate": 2, "conflict": 3}


def assess_skill_readiness(
    ws: WorkspacePaths,
    candidate_ref: PinnedRecordRef | Mapping[str, Any],
    *,
    expert_exception_ref: PinnedRecordRef | Mapping[str, Any] | None = None,
) -> SkillReadinessReportRecord:
    candidate_pin = _coerce_pin(candidate_ref)
    candidate_version = get_record_version(ws, candidate_pin)
    candidate = candidate_version.record
    if not isinstance(candidate, SkillDistillationCandidateRecord):
        raise ValueError("candidate_ref must pin a skill distillation candidate")
    require_valid_skill_distillation_candidate(candidate)

    exception_pin = _coerce_pin(expert_exception_ref) if expert_exception_ref else None
    exception_payload = {}
    independent_count = len(candidate.independent_execution_keys)
    readiness_basis = "two_independent_validated_uses"
    if exception_pin is not None:
        _validate_expert_exception(ws, candidate_pin, candidate, exception_pin)
        exception_payload = asdict(exception_pin)
        readiness_basis = "single_narrow_use_with_expert_exception"

    fixture_refs = sorted(
        value
        for value in candidate.package_requirements
        if value.startswith(("tests/", "fixtures/"))
    )
    failure_coverage = _failure_coverage(candidate)
    overlap = _audit_overlap(ws, candidate)
    blockers = []
    if candidate.status in {"rejected", "superseded"}:
        blockers.append("candidate_not_active")
    if independent_count < 2 and not (independent_count == 1 and exception_pin):
        blockers.append("insufficient_independent_uses")
    if failure_coverage["status"] == "missing":
        blockers.append("missing_failure_coverage")
    if not candidate.stop_rules:
        blockers.append("missing_stop_rules")
    if not candidate.applicability_selectors:
        blockers.append("unstable_applicability")
    if not fixture_refs:
        blockers.append("missing_validation_fixture")
    if overlap["classification"] == "duplicate":
        blockers.append("duplicate_skill")
    if overlap["classification"] == "conflict":
        blockers.append("conflicting_skill")
    if overlap["errors"]:
        blockers.append("overlap_catalog_incomplete")
    blockers = list(dict.fromkeys(blockers))
    required_actions = _required_actions(blockers, overlap)
    status = "blocked" if blockers else "ready"
    identity = {
        "candidate_ref": asdict(candidate_pin),
        "expert_exception_ref": exception_payload,
        "overlap": overlap,
        "blockers": blockers,
    }
    digest = _sha256_json(identity)
    report = SkillReadinessReportRecord(
        report_id=prefixed_id(
            "skill-readiness",
            f"{candidate.candidate_id}:{digest}",
            max_slug=72,
        ),
        candidate_ref=asdict(candidate_pin),
        candidate_id=candidate.candidate_id,
        candidate_signature=candidate.workflow_signature,
        status=status,
        readiness_basis=readiness_basis,
        independent_use_count=independent_count,
        checked_execution_refs=list(candidate.execution_refs),
        validation_fixture_refs=fixture_refs,
        failure_coverage=failure_coverage,
        overlap=overlap,
        blockers=blockers,
        required_actions=required_actions,
        expert_exception_ref=exception_payload,
        created_at=str(candidate_version.frontmatter.get("created_at") or candidate.created_at),
        ready_for_package_preview=status == "ready",
    )
    return require_valid_skill_readiness_report(report)


def record_skill_readiness_report(
    ws: WorkspacePaths,
    report: SkillReadinessReportRecord,
    *,
    actor: RecordActor,
) -> WriteResult:
    report = require_valid_skill_readiness_report(report)
    current = assess_skill_readiness(
        ws,
        report.candidate_ref,
        expert_exception_ref=report.expert_exception_ref or None,
    )
    if asdict(current) != asdict(report):
        raise ValueError("skill readiness report does not match the current assessment")
    body = (
        f"# Skill Readiness: {report.status}\n\n"
        f"Independent validated uses: {report.independent_use_count}.\n\n"
        "This report is advisory and cannot install a Skill or update claim trust.\n"
    )
    return RecordRepository(ws, actor=actor).write(
        "skill_readiness_reports",
        report,
        body=body,
    )


def _validate_expert_exception(
    ws: WorkspacePaths,
    candidate_pin: PinnedRecordRef,
    candidate: SkillDistillationCandidateRecord,
    checkpoint_pin: PinnedRecordRef,
) -> None:
    version = get_record_version(ws, checkpoint_pin)
    checkpoint = version.record
    if not isinstance(checkpoint, HumanCheckpointRecord):
        raise ValueError("expert exception ref must pin a human checkpoint")
    payload_hash = hash_action_payload(
        {
            "candidate_id": candidate.candidate_id,
            "candidate_hash": candidate_pin.content_hash,
            "exception": "single_narrow_validated_use",
        }
    )
    expected_scopes = tuple(sorted({candidate_pin.record_ref, *(
        f"topic:{topic_id}" for topic_id in candidate.source_topic_ids
    )}))
    expected = CheckpointSubjectBinding(
        intent=candidate_pin,
        subjects=(candidate_pin,),
        action="approve_skill_readiness_exception",
        action_payload_hash=payload_hash,
        request_hash=checkpoint.request_hash,
        target_scope_refs=expected_scopes,
        effect_policy="skill_readiness_exception_only_no_claim_trust",
        replay_policy="exact_once",
    )
    validate_checkpoint_binding(ws, checkpoint_pin, expected, require_decided=True)


def _failure_coverage(candidate: SkillDistillationCandidateRecord) -> dict[str, Any]:
    if candidate.known_failures:
        return {
            "status": "covered",
            "failure_count": len(candidate.known_failures),
            "boundary": candidate.transfer_boundary,
        }
    if candidate.failure_boundary.strip():
        return {
            "status": "none_known_justified",
            "failure_count": 0,
            "boundary": candidate.failure_boundary.strip(),
        }
    return {"status": "missing", "failure_count": 0, "boundary": ""}


def _audit_overlap(
    ws: WorkspacePaths,
    candidate: SkillDistillationCandidateRecord,
) -> dict[str, Any]:
    descriptors, errors = _installed_descriptors(ws)
    descriptors.extend(_external_descriptors())
    matches = [
        match
        for descriptor in descriptors
        if (match := _match_descriptor(candidate, descriptor)) is not None
    ]
    matches.sort(
        key=lambda item: (
            -_OVERLAP_PRIORITY[item["classification"]],
            item["source_kind"],
            item["ref"],
        )
    )
    classification = matches[0]["classification"] if matches else "new"
    return {"classification": classification, "matches": matches, "errors": errors}


def _installed_descriptors(ws: WorkspacePaths) -> tuple[list[dict], list[dict]]:
    roots = (
        ws.base / ".agents" / "skills" / "aitp-generated",
        ws.root / "tools" / "skills" / "catalog",
    )
    descriptors = []
    errors = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("manifest.json"))[:1000]:
            try:
                if not path.is_file() or path.stat().st_size > _MAX_MANIFEST_BYTES:
                    raise ValueError("manifest is missing, special, or too large")
                payload = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("manifest must contain a JSON object")
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
                errors.append({"path": str(path), "error": str(exc)})
                continue
            descriptors.append(
                {
                    **payload,
                    "source_kind": "installed_aitp_skill",
                    "ref": str(payload.get("skill_id") or path.parent.name),
                    "manifest_path": str(path),
                }
            )
    return descriptors, errors


def _external_descriptors() -> list[dict]:
    descriptors = []
    for pack_id, pack in builtin_domain_packs().items():
        for ref in pack.skill_refs:
            descriptors.append(
                {
                    "source_kind": "external_domain_skill",
                    "ref": f"domain_pack:{pack_id}#skill:{ref.get('skill_id', '')}",
                    "name": str(ref.get("skill_id") or ""),
                    "purpose": " ".join(
                        [str(ref.get("role") or ""), *map(str, ref.get("load_when") or [])]
                    ),
                    "domain": pack.domain,
                    "workflow_signature": "",
                }
            )
    return descriptors


def _match_descriptor(
    candidate: SkillDistillationCandidateRecord,
    descriptor: Mapping[str, Any],
) -> dict[str, Any] | None:
    candidate_name = _slug(candidate.title)
    descriptor_name = _slug(str(descriptor.get("name") or descriptor.get("skill_id") or ""))
    signature = str(descriptor.get("workflow_signature") or "")
    if signature and signature == candidate.workflow_signature:
        classification = "duplicate"
        reasons = ["exact_workflow_signature"]
    elif descriptor_name and descriptor_name == candidate_name:
        classification = "conflict"
        reasons = ["same_normalized_name_different_signature"]
    elif _procedural_overlap(candidate, descriptor):
        classification = "extension_candidate"
        reasons = ["overlapping_domain_or_selector_with_distinct_workflow"]
    else:
        return None
    result = {
        "classification": classification,
        "source_kind": str(descriptor.get("source_kind") or "unknown"),
        "ref": str(descriptor.get("ref") or descriptor_name),
        "reasons": reasons,
    }
    if descriptor.get("manifest_path"):
        result["manifest_path"] = str(descriptor["manifest_path"])
    return result


def _procedural_overlap(
    candidate: SkillDistillationCandidateRecord,
    descriptor: Mapping[str, Any],
) -> bool:
    text = " ".join(
        str(descriptor.get(key) or "") for key in ("name", "purpose", "domain", "skill_id")
    ).lower()
    selector_values = {
        str(value).lower()
        for values in candidate.applicability_selectors.values()
        for value in (values if isinstance(values, list) else [values])
        if str(value).strip()
    }
    if any(value in text for value in selector_values if len(value) >= 3):
        return True
    candidate_tokens = set(re.findall(r"[a-z0-9]+", candidate.title.lower()))
    descriptor_tokens = set(re.findall(r"[a-z0-9]+", text))
    return len(candidate_tokens & descriptor_tokens) >= 2


def _required_actions(blockers: list[str], overlap: Mapping[str, Any]) -> list[str]:
    actions = [f"resolve:{blocker}" for blocker in blockers]
    if overlap.get("classification") == "extension_candidate":
        actions.append("review_existing_skill_extension_boundary")
    return actions


def _coerce_pin(value: Any) -> PinnedRecordRef:
    if isinstance(value, PinnedRecordRef):
        return value
    if is_dataclass(value):
        value = asdict(value)
    if not isinstance(value, Mapping):
        raise TypeError("readiness refs must be exact record pins")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=value.get("revision"),
    )


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


__all__ = ["assess_skill_readiness", "record_skill_readiness_report"]
