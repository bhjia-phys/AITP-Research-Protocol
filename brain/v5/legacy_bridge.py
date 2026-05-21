"""Read-only bridge from legacy AITP topic folders into v5 seeds."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from brain.v5.brief import build_execution_brief
from brain.v5.evidence import record_evidence
from brain.v5.legacy_migration_records import (
    legacy_l1_intake_candidates,
    legacy_l2_migration_candidates,
    legacy_source_metadata_anchor_candidates,
    migrate_legacy_l1_understanding,
    migrate_legacy_l2_memory,
    migrate_legacy_runtime_log,
    migrate_legacy_source_reference_locations,
)
from brain.v5.legacy_l3_process_records import (
    legacy_l3_process_audit_candidates,
    migrate_legacy_l3_process_notes,
)
from brain.v5.legacy_record_bodies import legacy_evidence_body
from brain.v5.markdown import read_md
from brain.v5.paths import WorkspacePaths
from brain.v5.sensemaking import record_sensemaking_report
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


def migrate_legacy_topic_to_v5(
    ws: WorkspacePaths,
    topic_dir: str | Path,
    *,
    context_id: str,
    session_id: str,
) -> dict:
    """Explicitly migrate a legacy topic into v5 typed records."""

    root = Path(topic_dir)
    summary = scan_legacy_topic(root)
    create_context(ws, context_id, title=context_id)
    create_topic(ws, summary.topic_slug, context_id=context_id, title=summary.title)

    candidate_records = _legacy_candidate_records(root)
    if not candidate_records:
        candidate_records = [
            {
                "path": root / "state.md",
                "statement": summary.question,
                "evidence_summary": "Legacy topic question imported as candidate claim.",
                "body_summary": summary.question,
                "candidate_id": "legacy-question",
            }
        ]

    claims = []
    evidence_ids: list[str] = []
    sensemaking_report_ids: list[str] = []
    for candidate in candidate_records:
        claim = create_claim(
            ws,
            topic_id=summary.topic_slug,
            statement=candidate["statement"],
            evidence_profile=_evidence_profile_for_lane(summary.lane),
            confidence_state="legacy_seed",
            active_uncertainty=summary.question or "legacy topic imported for v5 review",
        )
        claims.append(claim)
        candidate_source_ref = f"legacy_candidate:{candidate['path'].as_posix()}"
        candidate_evidence = record_evidence(
            ws,
            topic_id=summary.topic_slug,
            claim_id=claim.claim_id,
            evidence_type="legacy_candidate",
            status="legacy_seed",
            summary=candidate["evidence_summary"],
            supports_outputs=["evidence_or_provenance"],
            source_refs=[candidate_source_ref],
        )
        evidence_ids.append(candidate_evidence.evidence_id)
        report = record_sensemaking_report(
            ws,
            topic_id=summary.topic_slug,
            claim_id=claim.claim_id,
            title=f"Legacy candidate: {candidate['candidate_id']}",
            summary=candidate["body_summary"],
            evidence_refs=[candidate_evidence.evidence_id],
            next_actions=["review_legacy_candidate_in_v5"],
        )
        sensemaking_report_ids.append(report.report_id)

    active_claim = claims[0]
    preserved_refs = [f"legacy_source:{path}" for path in summary.source_paths]
    for source_ref in preserved_refs:
        source_evidence = record_evidence(
            ws,
            topic_id=summary.topic_slug,
            claim_id=active_claim.claim_id,
            evidence_type="legacy_source",
            status="legacy_seed",
            summary="Legacy source path preserved for v5 review.",
            supports_outputs=["evidence_or_provenance"],
            source_refs=[source_ref],
        )
        evidence_ids.append(source_evidence.evidence_id)

    reference_location_ids = migrate_legacy_source_reference_locations(
        ws,
        topic_id=summary.topic_slug,
        claim_id=active_claim.claim_id,
        source_paths=summary.source_paths,
    )

    l1_evidence_ids, l1_report_ids = migrate_legacy_l1_understanding(
        ws,
        root,
        topic_id=summary.topic_slug,
        claim_id=active_claim.claim_id,
    )
    evidence_ids.extend(l1_evidence_ids)
    sensemaking_report_ids.extend(l1_report_ids)

    l3_evidence_ids, l3_report_ids = migrate_legacy_l3_process_notes(
        ws,
        root,
        topic_id=summary.topic_slug,
        claim_id=active_claim.claim_id,
    )
    evidence_ids.extend(l3_evidence_ids)
    sensemaking_report_ids.extend(l3_report_ids)

    for review in _legacy_review_records(root):
        review_evidence = record_evidence(
            ws,
            topic_id=summary.topic_slug,
            claim_id=active_claim.claim_id,
            evidence_type="legacy_l4_review",
            status=review["status"],
            summary=review["summary"],
            supports_outputs=["evidence_or_provenance", "minimal_check"],
            source_refs=[f"legacy_l4_review:{review['path'].as_posix()}"],
            body=legacy_evidence_body(
                title="Legacy L4 review evidence",
                summary=review["summary"],
                display_path=review["display_path"],
                body=review["body"],
            ),
        )
        evidence_ids.append(review_evidence.evidence_id)

    trace_event_ids = migrate_legacy_runtime_log(
        ws,
        root,
        session_id=session_id,
        topic_id=summary.topic_slug,
        claim_id=active_claim.claim_id,
    )
    memory_entry_ids = migrate_legacy_l2_memory(
        ws,
        root,
        topic_id=summary.topic_slug,
        claim_id=active_claim.claim_id,
    )

    bind_session(
        ws,
        session_id,
        topic_id=summary.topic_slug,
        context_id=context_id,
        active_claim=active_claim.claim_id,
    )

    return {
        "kind": "legacy_topic_migration_result",
        "topic_id": summary.topic_slug,
        "context_id": context_id,
        "session_id": session_id,
        "active_claim_id": active_claim.claim_id,
        "written_records": {
            "topics": [summary.topic_slug],
            "claims": [claim.claim_id for claim in claims],
            "evidence": evidence_ids,
            "reference_locations": reference_location_ids,
            "sensemaking_reports": sensemaking_report_ids,
            "trace_events": trace_event_ids,
            "memory_entries": memory_entry_ids,
        },
        "preserved_source_refs": preserved_refs,
        "summary_inputs_trusted": False,
    }


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
        "L1/question_contract.md": "l1/question contract candidate",
        "L1/source_basis.md": "source basis/evidence orientation",
        "L1/convention_snapshot.md": "understanding/conventions candidate",
        "L1/derivation_anchor_map.md": "understanding/derivation anchor candidate",
        "L1/contradiction_register.md": "understanding/contradiction candidate",
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
    for display_path, label in legacy_source_metadata_anchor_candidates(root):
        mapped_paths[display_path] = label

    for candidate in sorted((root / "L3" / "candidates").glob("*.md")):
        mapped_paths[candidate.relative_to(root).as_posix()] = "claim/candidate seed"

    for review in sorted((root / "L4" / "reviews").glob("*.md")):
        mapped_paths[review.relative_to(root).as_posix()] = "validation evidence candidate"

    if (root / "L1" / "question_contract.md").exists():
        mapped_paths["L1/question_contract.md"] = _PATH_MAP["L1/question_contract.md"]
    for _path, display_path in legacy_l1_intake_candidates(root):
        mapped_paths[display_path] = "l1/intake note candidate"
    for rel in (
        "L1/convention_snapshot.md",
        "L1/derivation_anchor_map.md",
        "L1/contradiction_register.md",
    ):
        if (root / rel).exists():
            mapped_paths[rel] = _PATH_MAP[rel]

    for _path, display_path, label in legacy_l2_migration_candidates(root):
        mapped_paths[display_path] = label
    for display_path, label in legacy_l3_process_audit_candidates(root):
        mapped_paths[display_path] = label

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


def _legacy_candidate_records(root: Path) -> list[dict]:
    records = []
    for candidate_path in sorted((root / "L3" / "candidates").glob("*.md")):
        fm, body = read_md(candidate_path)
        statement = str(fm.get("claim") or _first_nonempty_body_line(body))
        if not statement:
            continue
        body_summary = _first_paragraph(body) or statement
        records.append(
            {
                "path": candidate_path,
                "statement": statement,
                "evidence_summary": str(fm.get("evidence") or body_summary),
                "body_summary": body_summary,
                "candidate_id": str(fm.get("candidate_id") or candidate_path.stem),
            }
        )
    return records


def _legacy_review_records(root: Path) -> list[dict]:
    records = []
    for review_path in sorted((root / "L4" / "reviews").glob("*.md")):
        fm, body = read_md(review_path)
        summary = str(fm.get("summary") or _first_paragraph(body) or review_path.stem)
        records.append(
            {
                "path": review_path,
                "display_path": review_path.relative_to(root).as_posix(),
                "status": str(fm.get("status") or "legacy_review"),
                "summary": summary,
                "body": body,
            }
        )
    return records


def _first_paragraph(body: str) -> str:
    lines = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            if lines:
                break
            continue
        if stripped.startswith("#"):
            continue
        lines.append(stripped)
    return " ".join(lines)
