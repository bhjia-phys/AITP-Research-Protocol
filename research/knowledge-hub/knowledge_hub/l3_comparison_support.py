from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _slugify(text: str) -> str:
    lowered = str(text or "").lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "comparison"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows)
    path.write_text(rendered, encoding="utf-8")


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def comparison_paths(run_root: Path) -> dict[str, Path]:
    return {
        "ledger": run_root / "l2_comparison_receipts.jsonl",
        "note": run_root / "l2_comparison_receipts.md",
    }


def _render_comparison_markdown(rows: list[dict[str, Any]]) -> str:
    lines = ["# L2 Comparison Receipts", ""]
    if not rows:
        lines.append("No L2 comparison receipts have been persisted for this run.")
        return "\n".join(lines).strip() + "\n"

    for row in rows:
        lines.append(f"## {row.get('title') or row.get('comparison_id') or 'Comparison'}")
        lines.append("")
        lines.append(f"- Comparison id: `{row.get('comparison_id') or '(missing)'}`")
        lines.append(f"- Candidate ref: `{row.get('candidate_ref_id') or '(missing)'}`")
        lines.append(f"- Comparison scope: `{row.get('comparison_scope') or '(missing)'}`")
        lines.append(f"- Outcome: `{row.get('outcome') or '(missing)'}`")
        lines.append("")
        summary = str(row.get("comparison_summary") or "").strip()
        if summary:
            lines.append(summary)
            lines.append("")
        compared_unit_ids = _string_list(row.get("compared_unit_ids"))
        if compared_unit_ids:
            lines.append("### Compared L2 units")
            lines.append("")
            for item in compared_unit_ids:
                lines.append(f"- {item}")
            lines.append("")
        limitations = _string_list(row.get("limitations"))
        if limitations:
            lines.append("### Limitations")
            lines.append("")
            for item in limitations:
                lines.append(f"- {item}")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def record_l2_derivation_comparison_entry(
    *,
    run_root: Path,
    topic_slug: str,
    run_id: str,
    candidate_id: str,
    title: str,
    comparison_summary: str,
    compared_unit_ids: list[str] | None = None,
    comparison_scope: str = "",
    outcome: str = "",
    limitations: list[str] | None = None,
    updated_by: str = "human",
    comparison_id: str | None = None,
) -> dict[str, Any]:
    resolved_title = str(title or "").strip() or "Untitled comparison"
    resolved_id = str(comparison_id or "").strip() or f"comparison:{_slugify(resolved_title)}"
    row = {
        "timestamp": _now_iso(),
        "topic_slug": str(topic_slug or "").strip(),
        "run_id": str(run_id or "").strip(),
        "comparison_id": resolved_id,
        "candidate_ref_id": str(candidate_id or "").strip(),
        "title": resolved_title,
        "comparison_summary": str(comparison_summary or "").strip(),
        "compared_unit_ids": _string_list(compared_unit_ids or []),
        "comparison_scope": str(comparison_scope or "").strip(),
        "outcome": str(outcome or "").strip(),
        "limitations": _string_list(limitations or []),
        "updated_by": str(updated_by or "").strip(),
    }

    paths = comparison_paths(run_root)
    rows = _read_jsonl(paths["ledger"])
    rows.append(row)
    _write_jsonl(paths["ledger"], rows)
    paths["note"].write_text(_render_comparison_markdown(rows), encoding="utf-8")

    try:
        from .research_notebook_support import append_notebook_entry

        l3_root = run_root.parent.parent
        append_notebook_entry(
            l3_root,
            kind="comparison_note",
            title=resolved_title,
            body=str(comparison_summary or "").strip(),
            status=str(outcome or "").strip(),
            run_id=str(run_id or "").strip(),
            details={
                "candidate_ref_id": str(candidate_id or "").strip(),
                "comparison_scope": str(comparison_scope or "").strip(),
                "compared_unit_ids": _string_list(compared_unit_ids or []),
            },
        )
    except Exception:
        pass

    return {
        "comparison_id": resolved_id,
        "ledger_path": str(paths["ledger"]),
        "note_path": str(paths["note"]),
        "row": row,
    }
