"""Focused record writers for legacy-topic migration."""

from __future__ import annotations

from pathlib import Path

from brain.v5.evidence import record_evidence
from brain.v5.ids import prefixed_id
from brain.v5.markdown import read_md
from brain.v5.models import MemoryEntryRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.sensemaking import record_sensemaking_report
from brain.v5.store import write_record
from brain.v5.trace import TraceEvent, append_trace_event


def migrate_legacy_l1_understanding(
    ws: WorkspacePaths,
    root: Path,
    *,
    topic_id: str,
    claim_id: str,
) -> tuple[list[str], list[str]]:
    specs = [
        ("source_basis.md", "legacy_l1_source_basis", "Legacy L1 source basis"),
        (
            "convention_snapshot.md",
            "legacy_l1_convention_snapshot",
            "Legacy L1 convention snapshot",
        ),
        (
            "derivation_anchor_map.md",
            "legacy_l1_derivation_anchor_map",
            "Legacy L1 derivation anchor map",
        ),
        (
            "contradiction_register.md",
            "legacy_l1_contradiction_register",
            "Legacy L1 contradiction register",
        ),
    ]
    evidence_ids: list[str] = []
    report_ids: list[str] = []
    for filename, evidence_type, title in specs:
        path = root / "L1" / filename
        if not path.exists():
            continue
        fm, body = read_md(path)
        summary = str(fm.get("summary") or _first_paragraph(body) or title)
        evidence = record_evidence(
            ws,
            topic_id=topic_id,
            claim_id=claim_id,
            evidence_type=evidence_type,
            status="legacy_seed",
            summary=summary,
            supports_outputs=["evidence_or_provenance"],
            source_refs=[f"legacy_l1:{path.as_posix()}"],
        )
        report = record_sensemaking_report(
            ws,
            topic_id=topic_id,
            claim_id=claim_id,
            title=title,
            summary=summary,
            evidence_refs=[evidence.evidence_id],
            next_actions=["review_legacy_l1_understanding"],
        )
        evidence_ids.append(evidence.evidence_id)
        report_ids.append(report.report_id)
    return evidence_ids, report_ids


def migrate_legacy_runtime_log(
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
        event_id = prefixed_id(
            "event",
            f"legacy-runtime-log:{topic_id}:{index}:{summary}",
            max_slug=64,
        )
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


def migrate_legacy_l2_memory(
    ws: WorkspacePaths,
    root: Path,
    *,
    topic_id: str,
    claim_id: str,
) -> list[str]:
    entry_ids: list[str] = []
    for path, display_path, _label in legacy_l2_migration_candidates(root):
        fm, body = read_md(path)
        statement, memory_kind, scope = _legacy_l2_memory_fields(path, fm, body)
        entry_id = prefixed_id(
            "memory",
            f"legacy-l2:{topic_id}:{display_path}:{statement}",
            max_slug=80,
        )
        entry = MemoryEntryRecord(
            entry_id=entry_id,
            topic_id=topic_id,
            source_claim_id=claim_id,
            source_topic_id=topic_id,
            statement=statement,
            memory_kind=memory_kind,
            scope=scope,
            evidence_refs=[f"legacy_l2:{path.as_posix()}"],
            non_claims=[
                "Legacy L2 import is preserved as a seed, not newly validated by v5 migration."
            ],
            known_failure_modes=["Legacy L2 import requires review before trusted reuse."],
            source_packet_id=f"legacy_l2:{path.as_posix()}",
            human_checkpoint_id="legacy_migration_review_required",
            status="legacy_seed",
        )
        write_record(
            ws.root / "memory" / "l2" / "entries" / f"{entry_id}.md",
            entry,
            body=_legacy_l2_memory_body(path, body),
        )
        entry_ids.append(entry_id)
    return entry_ids


def legacy_l2_migration_candidates(root: Path) -> list[tuple[Path, str, str]]:
    candidates: list[tuple[Path, str, str]] = []
    seen: set[str] = set()
    for l2_root in _legacy_l2_roots(root):
        for pattern, label in (
            ("entries/*.md", "l2/memory entry candidate"),
            ("graph/nodes/*.md", "l2/graph node memory candidate"),
            ("graph/edges/*.md", "l2/graph edge memory candidate"),
        ):
            for path in sorted(l2_root.glob(pattern)):
                if path.stem.startswith("INDEX") or path.name.lower() in {"index.md", "log.md"}:
                    continue
                resolved = str(path.resolve())
                if resolved in seen:
                    continue
                seen.add(resolved)
                candidates.append((path, _legacy_l2_display_path(root, l2_root, path), label))
    return candidates


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


def _legacy_l2_roots(root: Path) -> list[Path]:
    candidates = [root / "L2", root.parent / "L2"]
    if root.parent.name == "topics":
        candidates.append(root.parent.parent / "L2")

    roots: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate.exists():
            continue
        resolved = str(candidate.resolve())
        if resolved not in seen:
            seen.add(resolved)
            roots.append(candidate)
    return roots


def _legacy_l2_display_path(root: Path, l2_root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        pass
    try:
        return path.relative_to(l2_root.parent).as_posix()
    except ValueError:
        return path.as_posix()


def _legacy_l2_memory_fields(path: Path, fm: dict, body: str) -> tuple[str, str, str]:
    parts = path.parts
    if "entries" in parts:
        role = str(fm.get("role") or "unknown")
        statement = _first_value(
            fm,
            "statement",
            "question_statement",
            "symptom",
            "formula_or_identifier",
            "title",
        ) or _first_paragraph(body) or path.stem
        scope = str(fm.get("regime") or fm.get("status") or "legacy L2 entry")
        return statement, f"legacy_l2_entry:{role}", scope
    if "nodes" in parts:
        node_type = str(fm.get("type") or "unknown")
        statement = _first_value(
            fm,
            "physical_meaning",
            "mathematical_expression",
            "title",
            "node_id",
        ) or _first_paragraph(body) or path.stem
        scope = str(
            fm.get("regime_of_validity")
            or fm.get("domain")
            or fm.get("trust_scope")
            or "legacy L2 node"
        )
        return statement, f"legacy_l2_graph_node:{node_type}", scope
    if "edges" in parts:
        edge_type = str(fm.get("type") or fm.get("edge_type") or "unknown")
        from_node = str(fm.get("from_node") or "unknown")
        to_node = str(fm.get("to_node") or "unknown")
        statement = f"{from_node} --[{edge_type}]--> {to_node}"
        scope = str(fm.get("regime_condition") or "legacy L2 graph edge")
        return statement, f"legacy_l2_graph_edge:{edge_type}", scope
    statement = (
        _first_value(fm, "title", "claim", "statement")
        or _first_paragraph(body)
        or path.stem
    )
    return statement, "legacy_l2_unknown", "legacy L2 import"


def _first_value(fm: dict, *keys: str) -> str:
    for key in keys:
        value = fm.get(key)
        if value:
            return str(value)
    return ""


def _legacy_l2_memory_body(path: Path, body: str) -> str:
    original = body.strip()
    if original:
        original = original[:4000]
        return (
            f"# Legacy L2 Import\n\nSource: `{path.as_posix()}`\n\n"
            f"## Original Body\n\n{original}\n"
        )
    return f"# Legacy L2 Import\n\nSource: `{path.as_posix()}`\n"


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
