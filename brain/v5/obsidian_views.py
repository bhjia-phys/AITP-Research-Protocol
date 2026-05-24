"""Orientation-only Obsidian-friendly views over typed L2 memory."""

from __future__ import annotations

import re
from pathlib import Path

from brain.v5.markdown import write_md
from brain.v5.memory_index import scan_memory_entry_summaries
from brain.v5.models import ClaimRecord, EvidenceRecord, MemoryEntryRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_records, read_record


def write_l2_obsidian_view(
    ws: WorkspacePaths,
    *,
    output_dir: str = "",
    claim_ids: list[str] | None = None,
) -> dict:
    """Write Markdown review notes for active L2 memory entries."""

    view_dir = Path(output_dir) if output_dir else ws.root / "surfaces" / "obsidian_l2"
    entries_dir = view_dir / "entries"
    entries = _active_memory_entries(ws, claim_ids=claim_ids)
    claims = {claim.claim_id: claim for claim in list_records(ws.registry_dir("claims"), ClaimRecord)}
    evidence = {record.evidence_id: record for record in list_records(ws.registry_dir("evidence"), EvidenceRecord)}
    entry_files = []
    for entry in entries:
        path = entries_dir / f"{_slug(entry.entry_id)}.md"
        entry_files.append(str(path))
        write_md(path, _frontmatter("l2_memory_entry", entry.entry_id), _entry_body(entry, claims, evidence))
    overview_path = view_dir / "L2 Memory Overview.md"
    write_md(overview_path, _frontmatter("l2_memory_overview", "workspace"), _overview_body(entries, claims))
    return {
        "ok": True,
        "kind": "l2_obsidian_view_bundle",
        "view_dir": str(view_dir),
        "files": {"overview": str(overview_path), "entries": entry_files},
        "memory_entry_count": len(entries),
        "source_records": {
            "memory_entries": [entry.entry_id for entry in entries],
            "claims": _unique([entry.source_claim_id for entry in entries]),
            "evidence": _unique([evidence_id for entry in entries for evidence_id in entry.evidence_refs]),
            "validation_results": _unique([result_id for entry in entries for result_id in entry.validation_result_ids]),
        },
        "derived_from": "kernel_state",
        "truth_source": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _frontmatter(role: str, source_id: str) -> dict:
    return {
        "kind": "derived_obsidian_view",
        "view_role": role,
        "source_id": source_id,
        "derived_from": "kernel_state",
        "truth_source": False,
        "orientation_only": True,
        "adapter_rule": "read_for_orientation_then_call_kernel_before_trust_updates",
    }


def _active_memory_entries(ws: WorkspacePaths, *, claim_ids: list[str] | None) -> list[MemoryEntryRecord]:
    if claim_ids is None:
        return [
            entry
            for entry in list_records(ws.root / "memory" / "l2" / "entries", MemoryEntryRecord)
            if entry.status == "active"
        ]
    return [
        read_record(summary.path, MemoryEntryRecord)
        for summary in scan_memory_entry_summaries(ws, claim_ids=claim_ids, active_only=True)
    ]


def _overview_body(entries: list[MemoryEntryRecord], claims: dict[str, ClaimRecord]) -> str:
    lines = [
        "# L2 Memory Overview",
        "",
        "This Obsidian view is generated from typed AITP records. Use typed AITP records for trust updates.",
        "",
    ]
    if not entries:
        lines.append("- No active L2 memory entries.")
        return "\n".join(lines) + "\n"
    for entry in entries:
        claim = claims.get(entry.source_claim_id)
        statement = claim.statement if claim else entry.statement
        lines.append(f"- [[{_slug(entry.entry_id)}|{entry.entry_id}]]: {statement}")
    return "\n".join(lines) + "\n"


def _entry_body(
    entry: MemoryEntryRecord,
    claims: dict[str, ClaimRecord],
    evidence: dict[str, EvidenceRecord],
) -> str:
    claim = claims.get(entry.source_claim_id)
    lines = [
        f"# {entry.entry_id}",
        "",
        "This note is an orientation-only Obsidian view. Use typed AITP records for trust updates.",
        "",
        "## Statement",
        "",
        claim.statement if claim else entry.statement,
        "",
        "## Scope",
        "",
        entry.scope or "No scope recorded.",
        "",
        "## Evidence",
        "",
    ]
    if entry.evidence_refs:
        for evidence_id in entry.evidence_refs:
            record = evidence.get(evidence_id)
            summary = f" - {record.summary}" if record else ""
            lines.append(f"- `{evidence_id}`{summary}")
    else:
        lines.append("- No evidence refs recorded.")
    lines.extend(["", "## Validation Results", ""])
    if entry.validation_result_ids:
        lines.extend(f"- `{result_id}`" for result_id in entry.validation_result_ids)
    else:
        lines.append("- No validation result refs recorded.")
    lines.extend(["", "## Known Failure Modes", ""])
    if entry.known_failure_modes:
        lines.extend(f"- {mode}" for mode in entry.known_failure_modes)
    else:
        lines.append("- No known failure modes recorded.")
    return "\n".join(lines) + "\n"


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")
    return slug or "entry"


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
