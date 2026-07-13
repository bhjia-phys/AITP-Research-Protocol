"""Review-gated procedural skill candidates derived from typed research records."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from brain.v5.checkpoints import request_human_checkpoint
from brain.v5.human_approval import checkpoint_can_authorize_trust
from brain.v5.ids import prefixed_id
from brain.v5.markdown import write_text_atomic
from brain.v5.models import SkillPatchProposalRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WritePolicy


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
    """Install one exact approved proposal into the AITP project workspace."""

    repository = _repository(ws, "apply_project_skill")
    proposal_result = repository.read(f"skill_patch_proposal:{proposal_id}")
    if proposal_result.status != "found" or not isinstance(
        proposal_result.record, SkillPatchProposalRecord
    ):
        raise ValueError(f"skill proposal not found: {proposal_id}")
    checkpoint_result = repository.read(f"human_checkpoint:{checkpoint_id}")
    if checkpoint_result.status != "found" or checkpoint_result.record is None:
        raise ValueError(f"human checkpoint not found: {checkpoint_id}")
    proposal = proposal_result.record
    checkpoint = checkpoint_result.record
    if proposal.installation_target != "project":
        raise ValueError("only project-local AITP skill installation is supported")
    if not _SKILL_NAME_RE.fullmatch(proposal.skill_name):
        raise ValueError("skill_name must contain only letters, numbers, and hyphens")

    current_hash = str((proposal_result.frontmatter or {}).get("record_content_hash") or "")
    approved_hash = proposal.approved_content_hash or current_hash
    if checkpoint.checkpoint_id != checkpoint_id:
        raise ValueError("checkpoint identity mismatch")
    if checkpoint.decision != "approve_install" or not checkpoint_can_authorize_trust(checkpoint):
        raise ValueError("skill installation requires a host-verified approve_install checkpoint")
    if checkpoint.reason != _review_reason(proposal, approved_hash):
        raise ValueError("skill checkpoint is not bound to the exact proposal content")

    content = render_skill_markdown(proposal)
    skill_path = ws.base / ".agents" / "skills" / proposal.skill_name / "SKILL.md"
    if skill_path.exists() and skill_path.read_text(encoding="utf-8") != content:
        raise ValueError(f"skill target already contains different content: {skill_path}")
    write_text_atomic(skill_path, content)

    if proposal.application_status != "applied":
        if not current_hash:
            raise ValueError(f"skill proposal lacks a revision hash: {proposal_id}")
        proposal.review_status = "approved"
        proposal.application_status = "applied"
        proposal.review_checkpoint_id = checkpoint_id
        proposal.approved_content_hash = approved_hash
        repository.write(
            "skill_patch_proposals",
            proposal,
            body=proposal_result.body,
            policy=WritePolicy(mode="revision", expected_hash=current_hash),
        )
    return {
        "ok": True,
        "status": "installed",
        "proposal_id": proposal_id,
        "checkpoint_id": checkpoint_id,
        "skill_path": str(skill_path),
        "can_update_claim_trust": False,
    }


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
