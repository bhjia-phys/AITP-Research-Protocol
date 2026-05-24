"""Fast frontmatter index helpers for L2 memory entries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from brain.v5.paths import WorkspacePaths


@dataclass(frozen=True)
class MemoryEntrySummary:
    path: Path
    entry_id: str
    source_claim_id: str
    status: str
    evidence_refs: list[str]
    validation_result_ids: list[str]


def scan_memory_entry_summaries(
    ws: WorkspacePaths,
    *,
    claim_ids: Iterable[str] | None = None,
    active_only: bool = False,
) -> list[MemoryEntrySummary]:
    """Scan memory-entry frontmatter without parsing every full Markdown file."""

    wanted = set(claim_ids or [])
    entries_dir = ws.root / "memory" / "l2" / "entries"
    if not entries_dir.exists():
        return []
    summaries = []
    for path in sorted(entries_dir.glob("*.md")):
        summary = read_memory_entry_summary(path)
        if summary is None:
            continue
        if wanted and summary.source_claim_id not in wanted:
            continue
        if active_only and summary.status != "active":
            continue
        summaries.append(summary)
    return summaries


def read_memory_entry_summary(path: str | Path) -> MemoryEntrySummary | None:
    data = _read_frontmatter_subset(Path(path))
    if not data.get("entry_id") or not data.get("source_claim_id"):
        return None
    return MemoryEntrySummary(
        path=Path(path),
        entry_id=data["entry_id"],
        source_claim_id=data["source_claim_id"],
        status=data.get("status", ""),
        evidence_refs=data.get("evidence_refs", []),
        validation_result_ids=data.get("validation_result_ids", []),
    )


def _read_frontmatter_subset(path: Path) -> dict[str, str | list[str]]:
    data: dict[str, str | list[str]] = {
        "evidence_refs": [],
        "validation_result_ids": [],
    }
    current_list = ""
    with path.open("r", encoding="utf-8") as handle:
        if handle.readline().strip() != "---":
            return data
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            if line.strip() == "---":
                break
            stripped = line.strip()
            if current_list and stripped.startswith("- "):
                _append_list_item(data, current_list, stripped[2:].strip())
                continue
            current_list = ""
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            if key in {"evidence_refs", "validation_result_ids"}:
                current_list = key
                data[key] = _inline_list(value.strip())
            elif key in {"entry_id", "source_claim_id", "status"}:
                data[key] = _clean_scalar(value.strip())
    return data


def _append_list_item(data: dict[str, str | list[str]], key: str, raw: str) -> None:
    value = _clean_scalar(raw)
    if not value:
        return
    values = data.setdefault(key, [])
    if isinstance(values, list):
        values.append(value)


def _inline_list(raw: str) -> list[str]:
    if raw in {"", "[]"}:
        return []
    if raw.startswith("[") and raw.endswith("]"):
        return [_clean_scalar(item.strip()) for item in raw[1:-1].split(",") if item.strip()]
    return []


def _clean_scalar(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
