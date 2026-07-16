"""Review-gated procedural skill candidates derived from typed research records."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from brain.v5.checkpoints import request_human_checkpoint
from brain.v5.ids import prefixed_id
from brain.v5.models import SkillPatchProposalRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository


_SKILL_NAME_RE = re.compile(r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")


def propose_procedural_skill(
    ws: WorkspacePaths,
    *,
    skill_name: str,
    current_version: str,
    proposed_version: str,
    patch_summary: str,
    patch_body: str,
    topic_ids: list[str],
    supporting_records: list[str],
    applicability: list[str],
    preconditions: list[str],
    validation_refs: list[str],
    execution_refs: list[str],
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    installation_target: str = "project",
) -> SkillPatchProposalRecord:
    """Create a non-installed candidate only when its workflow basis is explicit."""

    required = {
        "topic_ids": topic_ids,
        "supporting_records": supporting_records,
        "applicability": applicability,
        "preconditions": preconditions,
        "validation_refs": validation_refs,
        "execution_refs": execution_refs,
    }
    missing = [name for name, values in required.items() if not values]
    if missing:
        raise ValueError(f"procedural skill candidate requires: {', '.join(missing)}")
    if installation_target not in {"project", "user"}:
        raise ValueError("installation_target must be project or user")

    basis = ":".join(
        [skill_name, proposed_version, *sorted(topic_ids), *sorted(supporting_records)]
    )
    record = SkillPatchProposalRecord(
        proposal_id=prefixed_id("skill-proposal", basis, max_slug=72),
        skill_name=skill_name,
        current_version=current_version,
        proposed_version=proposed_version,
        patch_summary=patch_summary,
        patch_body=patch_body,
        topic_ids=list(dict.fromkeys(topic_ids)),
        supporting_records=list(dict.fromkeys(supporting_records)),
        applicability=list(dict.fromkeys(applicability)),
        preconditions=list(dict.fromkeys(preconditions)),
        validation_refs=list(dict.fromkeys(validation_refs)),
        execution_refs=list(dict.fromkeys(execution_refs)),
        source_refs=list(dict.fromkeys(source_refs or [])),
        artifact_ids=list(dict.fromkeys(artifact_ids or [])),
        installation_target=installation_target,
        trust_level="open",
        review_status="draft",
        application_status="not_applied",
        requires_human_review=True,
        can_update_claim_trust=False,
        summary_inputs_trusted=False,
        orientation_only=True,
    )
    _repository(ws, "propose_procedural_skill").write(
        "skill_patch_proposals",
        record,
        body=f"# Skill Candidate: {skill_name}\n\n{patch_body}\n",
    )
    return record


def request_skill_install_review(
    ws: WorkspacePaths,
    *,
    proposal_id: str,
    topic_id: str,
    claim_id: str,
    requested_by: str,
):
    repository = _repository(ws, "request_skill_install_review")
    current = repository.read(f"skill_patch_proposal:{proposal_id}")
    if current.status != "found" or not isinstance(current.record, SkillPatchProposalRecord):
        raise ValueError(f"skill proposal not found: {proposal_id}")
    content_hash = str((current.frontmatter or {}).get("record_content_hash") or "")
    if not content_hash:
        raise ValueError(f"skill proposal lacks a content hash: {proposal_id}")
    proposal = current.record
    if topic_id not in proposal.topic_ids:
        raise ValueError(f"skill proposal {proposal_id} is not linked to topic {topic_id}")
    return request_human_checkpoint(
        ws,
        topic_id=topic_id,
        claim_id=claim_id,
        reason=_review_reason(proposal, content_hash),
        requested_by=requested_by,
        options=["approve_install", "reject"],
    )


def apply_project_skill(
    ws: WorkspacePaths,
    *,
    proposal_id: str,
    checkpoint_id: str,
) -> dict[str, str | bool]:
    """Reject the retired one-file writer; M4 package transactions own installs."""

    del ws, proposal_id, checkpoint_id
    raise ValueError(
        "legacy apply_project_skill is disabled; build a package install plan and "
        "use a bound install checkpoint (checkpoint_required)"
    )


def render_skill_markdown(proposal: SkillPatchProposalRecord) -> str:
    description = f"Use when {proposal.applicability[0].rstrip('.')}"
    frontmatter = yaml.safe_dump(
        {"name": proposal.skill_name, "description": description[:500]},
        allow_unicode=True,
        sort_keys=False,
    ).rstrip()
    return (
        f"---\n{frontmatter}\n---\n\n"
        f"# {proposal.skill_name}\n\n"
        "## Applicability\n\n"
        f"{_bullets(proposal.applicability)}\n\n"
        "## Preconditions\n\n"
        f"{_bullets(proposal.preconditions)}\n\n"
        "## Procedure\n\n"
        f"{proposal.patch_body.strip()}\n\n"
        "## Validation\n\n"
        f"{_bullets(proposal.validation_refs)}\n\n"
        "## AITP Provenance\n\n"
        f"Topics:\n{_bullets(proposal.topic_ids)}\n\n"
        f"Execution records:\n{_bullets(proposal.execution_refs)}\n\n"
        f"Supporting records:\n{_bullets(proposal.supporting_records)}\n\n"
        "## Boundaries\n\n"
        "- Apply only within the stated applicability and preconditions.\n"
        "- Revalidate after code, environment, input-schema, or scientific-regime changes.\n"
        "- This skill is procedural memory and cannot update scientific claim trust.\n"
    )


def _review_reason(proposal: SkillPatchProposalRecord, content_hash: str) -> str:
    return (
        f"Review skill proposal {proposal.proposal_id}@sha256:{content_hash} "
        f"for {proposal.installation_target} installation."
    )


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) or "- None"


def _repository(ws: WorkspacePaths, actor_id: str) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id=actor_id, host="aitp-v5"),
    )
