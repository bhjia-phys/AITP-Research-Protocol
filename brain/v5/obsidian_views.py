"""Orientation-only Obsidian-friendly views over typed L2 memory."""

from __future__ import annotations

import re
from pathlib import Path

from brain.v5.markdown import write_md
from brain.v5.memory_index import scan_memory_entry_summaries
from brain.v5.models import (
    ClaimRecord,
    EvidenceRecord,
    MemoryEntryRecord,
    ObjectRelationRecord,
    PhysicsObjectRecord,
    SensemakingReportRecord,
)
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
    graph = _graph_context(ws, entries)
    entry_files = []
    for entry in entries:
        path = entries_dir / f"{_slug(entry.entry_id)}.md"
        entry_files.append(str(path))
        write_md(
            path,
            _frontmatter("l2_memory_entry", entry.entry_id),
            _entry_body(entry, claims, evidence, graph),
        )
    overview_path = view_dir / "L2 Memory Overview.md"
    graph_path = view_dir / "L2 Typed Graph.md"
    write_md(overview_path, _frontmatter("l2_memory_overview", "workspace"), _overview_body(entries, claims, graph))
    write_md(graph_path, _frontmatter("l2_graph_overview", "workspace"), _graph_body(graph))
    return {
        "ok": True,
        "kind": "l2_obsidian_view_bundle",
        "view_dir": str(view_dir),
        "files": {"overview": str(overview_path), "graph": str(graph_path), "entries": entry_files},
        "memory_entry_count": len(entries),
        "physics_object_count": len(graph["objects"]),
        "object_relation_count": len(graph["relations"]),
        "sensemaking_report_count": len(graph["reports"]),
        "source_records": {
            "memory_entries": [entry.entry_id for entry in entries],
            "claims": _unique([entry.source_claim_id for entry in entries]),
            "evidence": _unique([evidence_id for entry in entries for evidence_id in entry.evidence_refs]),
            "validation_results": _unique([result_id for entry in entries for result_id in entry.validation_result_ids]),
            "physics_objects": [obj.object_id for obj in graph["objects"]],
            "object_relations": [rel.relation_id for rel in graph["relations"]],
            "sensemaking_reports": [report.report_id for report in graph["reports"]],
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


def _overview_body(
    entries: list[MemoryEntryRecord],
    claims: dict[str, ClaimRecord],
    graph: dict[str, list],
) -> str:
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
    lines.extend([
        "",
        "## Typed Graph",
        "",
        f"- Physics objects: {len(graph['objects'])}",
        f"- Object relations: {len(graph['relations'])}",
        f"- Sensemaking reports: {len(graph['reports'])}",
        f"- Graph overview: [[{_slug('L2 Typed Graph')}|L2 Typed Graph]]",
    ])
    for relation in graph["relations"]:
        lines.append(f"- `{relation.relation_id}`: {relation.statement}")
    return "\n".join(lines) + "\n"


def _entry_body(
    entry: MemoryEntryRecord,
    claims: dict[str, ClaimRecord],
    evidence: dict[str, EvidenceRecord],
    graph: dict[str, list],
) -> str:
    claim = claims.get(entry.source_claim_id)
    objects = _objects_for_entry(entry, graph)
    relations = _relations_for_entry(entry, graph)
    reports = _reports_for_entry(entry, graph)
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
    lines.extend(["", "## Linked Physics Objects", ""])
    if objects:
        lines.extend(f"- `{obj.object_id}` ({obj.object_type}): {obj.name}" for obj in objects)
    else:
        lines.append("- No linked physics objects recorded.")
    lines.extend(["", "## Object Relations", ""])
    if relations:
        lines.extend(f"- `{relation.relation_id}` ({relation.relation_type}): {relation.statement}" for relation in relations)
    else:
        lines.append("- No object relations recorded.")
    lines.extend(["", "## Sensemaking Reports", ""])
    if reports:
        lines.extend(f"- `{report.report_id}`: {report.title}" for report in reports)
    else:
        lines.append("- No sensemaking reports recorded.")
    return "\n".join(lines) + "\n"


def _graph_context(ws: WorkspacePaths, entries: list[MemoryEntryRecord]) -> dict[str, list]:
    claim_ids = {entry.source_claim_id for entry in entries if entry.source_claim_id}
    topic_ids = {entry.topic_id for entry in entries if entry.topic_id}
    objects = [
        obj
        for obj in list_records(ws.registry_dir("physics_objects"), PhysicsObjectRecord)
        if obj.topic_id in topic_ids and obj.status == "active"
    ]
    object_ids = {obj.object_id for obj in objects}
    relations = [
        relation
        for relation in list_records(ws.registry_dir("object_relations"), ObjectRelationRecord)
        if relation.claim_id in claim_ids
        or relation.topic_id in topic_ids
        or relation.subject_id in object_ids
        or relation.object_id in object_ids
    ]
    relation_ids = {relation.relation_id for relation in relations}
    reports = [
        report
        for report in list_records(ws.registry_dir("sensemaking_reports"), SensemakingReportRecord)
        if report.claim_id in claim_ids
        or report.topic_id in topic_ids
        or any(object_id in object_ids for object_id in report.object_ids)
        or any(relation_id in relation_ids for relation_id in report.relation_ids)
    ]
    return {
        "claim_ids": list(claim_ids),
        "topic_ids": list(topic_ids),
        "objects": objects,
        "relations": relations,
        "reports": reports,
    }


def _graph_body(graph: dict[str, list]) -> str:
    object_by_id = {obj.object_id: obj for obj in graph["objects"]}
    lines = [
        "# L2 Typed Graph",
        "",
        "This Obsidian graph view is orientation-only. Use typed AITP records for trust updates.",
        "",
        "## Physics Objects",
        "",
    ]
    if graph["objects"]:
        for obj in graph["objects"]:
            lines.append(f"- `{obj.object_id}` ({obj.object_type}) **{obj.name}**: {obj.definition}")
    else:
        lines.append("- No typed physics objects linked to active L2 entries.")
    lines.extend(["", "## Object Relations", ""])
    if graph["relations"]:
        for relation in graph["relations"]:
            subject = object_by_id.get(relation.subject_id)
            obj = object_by_id.get(relation.object_id)
            subject_label = subject.name if subject else relation.subject_id
            object_label = obj.name if obj else relation.object_id
            lines.append(
                f"- `{relation.relation_id}` ({relation.relation_type}): "
                f"{subject_label} -> {object_label}; {relation.statement}"
            )
    else:
        lines.append("- No typed object relations linked to active L2 entries.")
    lines.extend(["", "## Sensemaking Reports", ""])
    if graph["reports"]:
        for report in graph["reports"]:
            lines.append(f"- `{report.report_id}` **{report.title}**: {report.summary}")
    else:
        lines.append("- No sensemaking reports linked to active L2 entries.")
    return "\n".join(lines) + "\n"


def _objects_for_entry(entry: MemoryEntryRecord, graph: dict[str, list]) -> list[PhysicsObjectRecord]:
    relations = _relations_for_entry(entry, graph)
    relation_object_ids = {value for rel in relations for value in (rel.subject_id, rel.object_id)}
    return [
        obj
        for obj in graph["objects"]
        if obj.topic_id == entry.topic_id or obj.object_id in relation_object_ids
    ]


def _relations_for_entry(entry: MemoryEntryRecord, graph: dict[str, list]) -> list[ObjectRelationRecord]:
    return [
        relation
        for relation in graph["relations"]
        if relation.claim_id == entry.source_claim_id or relation.topic_id == entry.topic_id
    ]


def _reports_for_entry(entry: MemoryEntryRecord, graph: dict[str, list]) -> list[SensemakingReportRecord]:
    return [
        report
        for report in graph["reports"]
        if report.claim_id == entry.source_claim_id or report.topic_id == entry.topic_id
    ]


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
