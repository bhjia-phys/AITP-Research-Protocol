"""Read-only bridge from legacy AITP topic folders into v5 seeds."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from brain.v5.brief import build_execution_brief
from brain.v5.evidence import record_evidence
from brain.v5.ids import prefixed_id
from brain.v5.markdown import read_md
from brain.v5.paths import WorkspacePaths
from brain.v5.references import record_reference_location
from brain.v5.sensemaking import record_sensemaking_report
from brain.v5.trace import TraceEvent, append_trace_event
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

    reference_location_ids: list[str] = []
    for source_ref in preserved_refs:
        source_path = Path(source_ref.removeprefix("legacy_source:"))
        location = record_reference_location(
            ws,
            topic_id=summary.topic_slug,
            claim_id=active_claim.claim_id,
            connector_id="legacy_topic",
            location_type="legacy_source_file",
            uri=source_path.resolve().as_uri(),
            label=source_path.name,
            source_ref=source_ref,
            summary="Legacy source file preserved during explicit v5 migration.",
        )
        reference_location_ids.append(location.location_id)

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
        )
        evidence_ids.append(review_evidence.evidence_id)

    trace_event_ids = _migrate_legacy_runtime_log(
        ws,
        root,
        session_id=session_id,
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
        "L1/source_basis.md": "source basis/evidence orientation",
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

    for candidate in sorted((root / "L3" / "candidates").glob("*.md")):
        mapped_paths[candidate.relative_to(root).as_posix()] = "claim/candidate seed"

    for review in sorted((root / "L4" / "reviews").glob("*.md")):
        mapped_paths[review.relative_to(root).as_posix()] = "validation evidence candidate"

    if (root / "L1" / "question_contract.md").exists():
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
                "status": str(fm.get("status") or "legacy_review"),
                "summary": summary,
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


def _migrate_legacy_runtime_log(
    ws: WorkspacePaths,
    root: Path,
    *,
    session_id: str,
    topic_id: str,
    claim_id: str,
) -> list[str]:
    log_path = root / "runtime" / "log.md"
    summaries = _legacy_runtime_log_summaries(log_path)
    if not summaries:
        return []

    trace_path = ws.root / "runtime" / "legacy_migration_trace.jsonl"
    event_ids: list[str] = []
    for index, summary in enumerate(summaries, start=1):
        event_id = prefixed_id("event", f"legacy-runtime-log:{topic_id}:{index}:{summary}", max_slug=64)
        event = TraceEvent(
            event_id=event_id,
            session_id=session_id,
            topic_id=topic_id,
            event_type="legacy_runtime_log",
            risk_level="legacy",
            claim_id=claim_id,
            payload={
                "source_ref": f"legacy_runtime_log:{log_path.as_posix()}#{index}",
                "summary": summary,
                "orientation_only": True,
            },
        )
        append_trace_event(trace_path, event)
        event_ids.append(event_id)
    return event_ids


def _legacy_runtime_log_summaries(log_path: Path) -> list[str]:
    if not log_path.exists():
        return []
    summaries = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "---":
            continue
        if stripped.startswith("-"):
            stripped = stripped[1:].strip()
        if stripped:
            summaries.append(stripped)
    return summaries
