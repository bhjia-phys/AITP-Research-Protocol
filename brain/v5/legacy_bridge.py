"""Read-only bridge from legacy AITP topic folders into v5 seeds."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from brain.v5.brief import build_execution_brief
from brain.v5.evidence import record_evidence
from brain.v5.markdown import read_md
from brain.v5.paths import WorkspacePaths
from brain.v5.workspace import bind_session, create_claim, create_context, create_topic, init_workspace


@dataclass
class LegacyTopicSummary:
    topic_slug: str
    title: str
    question: str
    stage: str = ""
    lane: str = ""
    source_paths: list[str] = field(default_factory=list)
    candidate_claims: list[str] = field(default_factory=list)


@dataclass
class LegacySeedResult:
    topic_id: str
    context_id: str
    session_id: str
    active_claim_id: str
    preserved_source_refs: list[str] = field(default_factory=list)


def scan_legacy_topic(topic_dir: str | Path) -> LegacyTopicSummary:
    """Read a legacy topic directory without modifying it."""

    root = Path(topic_dir)
    state_fm, _ = read_md(root / "state.md")
    source_paths = [str(path) for path in sorted((root / "L0" / "sources").glob("*/source.md"))]
    candidate_claims = []
    for candidate_path in sorted((root / "L3" / "candidates").glob("*.md")):
        fm, body = read_md(candidate_path)
        claim = fm.get("claim") or _first_nonempty_body_line(body)
        if claim:
            candidate_claims.append(str(claim))

    return LegacyTopicSummary(
        topic_slug=root.name,
        title=str(state_fm.get("title") or root.name),
        question=str(state_fm.get("question") or ""),
        stage=str(state_fm.get("stage") or ""),
        lane=str(state_fm.get("lane") or ""),
        source_paths=source_paths,
        candidate_claims=candidate_claims,
    )


def seed_v5_from_legacy(
    ws: WorkspacePaths,
    topic_dir: str | Path,
    *,
    context_id: str,
    session_id: str,
) -> LegacySeedResult:
    """Seed v5 records from a legacy topic, preserving legacy paths as provenance."""

    summary = scan_legacy_topic(topic_dir)
    create_context(ws, context_id, title=context_id)
    create_topic(ws, summary.topic_slug, context_id=context_id, title=summary.title)
    claim_statement = summary.candidate_claims[0] if summary.candidate_claims else summary.question
    claim = create_claim(
        ws,
        topic_id=summary.topic_slug,
        statement=claim_statement,
        evidence_profile=_evidence_profile_for_lane(summary.lane),
        confidence_state="legacy_seed",
        active_uncertainty=summary.question or "legacy topic imported for v5 review",
    )
    preserved_refs = [f"legacy_source:{path}" for path in summary.source_paths]
    for source_ref in preserved_refs:
        record_evidence(
            ws,
            topic_id=summary.topic_slug,
            claim_id=claim.claim_id,
            evidence_type="legacy_source",
            status="legacy_seed",
            summary="Legacy source path preserved for v5 review.",
            supports_outputs=["evidence_or_provenance"],
            source_refs=[source_ref],
        )
    bind_session(
        ws,
        session_id,
        topic_id=summary.topic_slug,
        context_id=context_id,
        active_claim=claim.claim_id,
    )
    return LegacySeedResult(
        topic_id=summary.topic_slug,
        context_id=context_id,
        session_id=session_id,
        active_claim_id=claim.claim_id,
        preserved_source_refs=preserved_refs,
    )


def audit_legacy_topic_migration(topic_path: str | Path) -> dict:
    """Dry-run audit of what a legacy topic migration would preserve."""

    root = Path(topic_path)
    mapped_paths: dict[str, str] = {}
    missing_expected_paths: list[str] = []

    _EXPECTED_PATHS = [
        "state.md",
        "L0/sources",
        "L1/question_contract.md",
        "L1/source_basis.md",
    ]
    _PATH_MAP = {
        "state.md": "topic/runtime metadata",
    }

    for rel in _EXPECTED_PATHS:
        full = root / rel
        if full.exists():
            if rel in _PATH_MAP:
                mapped_paths[rel] = _PATH_MAP[rel]
        else:
            missing_expected_paths.append(rel)

    for src in sorted((root / "L0" / "sources").glob("*/source.md")):
        mapped_paths[src.relative_to(root).as_posix()] = "reference_location/source evidence candidate"

    if root / "L1" / "question_contract.md" in (root / "L1" / "question_contract.md").parent.glob("*"):
        mapped_paths["L1/question_contract.md"] = "claim/question or claim contract"

    can_write = len(missing_expected_paths) == 0

    return {
        "kind": "legacy_topic_migration_audit",
        "topic_path": str(root),
        "mapped_paths": mapped_paths,
        "missing_expected_paths": missing_expected_paths,
        "can_write_v5_records": can_write,
        "summary_inputs_trusted": False,
    }


def build_v5_brief_from_legacy(
    base: str | Path,
    topic_dir: str | Path,
    *,
    context_id: str,
    session_id: str,
) -> dict:
    """Seed a v5 workspace from a legacy topic and return its execution brief."""

    ws = init_workspace(base)
    seed_v5_from_legacy(ws, topic_dir, context_id=context_id, session_id=session_id)
    return build_execution_brief(ws, session_id)


def _evidence_profile_for_lane(lane: str) -> str:
    if lane in {"toy_numeric", "code_method", "formal_theory", "code_and_materials"}:
        return lane
    return "legacy"


def _first_nonempty_body_line(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip("# ").strip()
        if stripped:
            return stripped
    return ""
