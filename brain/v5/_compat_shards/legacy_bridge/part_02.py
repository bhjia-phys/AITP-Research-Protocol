# Compatibility shard 2 for legacy_bridge.
from __future__ import annotations

def _write_generic_migration_index(
    ws: WorkspacePaths,
    *,
    summary: LegacyTopicSummary,
    context_id: str,
    session_id: str,
    active_claim_id: str,
    claims: list[str],
    evidence_ids: list[str],
    reference_location_ids: list[str],
    sensemaking_report_ids: list[str],
    trace_event_ids: list[str],
    memory_entry_ids: list[str],
    preserved_refs: list[str],
) -> Path:
    path = ws.topic_dir(summary.topic_slug) / "indexes" / "legacy_v5_generic_migration.md"
    lines = [
        "---",
        "kind: legacy_v5_generic_migration_index",
        f"topic_id: {summary.topic_slug}",
        f"context_id: {context_id}",
        f"session_id: {session_id}",
        f"active_claim_id: {active_claim_id}",
        "summary_inputs_trusted: false",
        "---",
        f"# Generic Legacy v5 Migration: {summary.topic_slug}",
        "",
        "This index records a preservation-only v5 migration of a legacy topic.",
        "It does not validate the scientific claim and does not promote L2 memory.",
        "",
        "## Status",
        "",
        "- Confidence state: `legacy_seed`",
        f"- Legacy stage: `{summary.stage or 'unknown'}`",
        f"- Legacy lane: `{summary.lane or 'unknown'}`",
        "- Trust: orientation only until reviewed through v5 validation/trust gates.",
        "",
        "## Written Records",
        "",
        f"- Claims: {len(claims)}",
        f"- Evidence records: {len(evidence_ids)}",
        f"- Reference locations: {len(reference_location_ids)}",
        f"- Sensemaking reports: {len(sensemaking_report_ids)}",
        f"- Trace events: {len(trace_event_ids)}",
        f"- Topic-local legacy L2 memory entries: {len(memory_entry_ids)}",
        f"- Preserved source refs: {len(preserved_refs)}",
        "",
        "## Next Required Review",
        "",
        "- Confirm the active claim scope before using it as a scientific claim.",
        "- Review migrated evidence and source provenance.",
        "- Run validation checks required by the v5 execution brief.",
        "- Use dedicated legacy L2 migration surfaces for global L2 memory; do not trust imported legacy seeds directly.",
        "",
    ]
    write_text_atomic(path, "\n".join(lines))
    return path

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
