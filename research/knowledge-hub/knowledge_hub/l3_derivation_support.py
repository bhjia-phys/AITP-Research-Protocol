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
    return lowered or "derivation"


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


def derivation_paths(run_root: Path) -> dict[str, Path]:
    return {
        "ledger": run_root / "derivation_records.jsonl",
        "note": run_root / "derivation_records.md",
    }


def _render_derivation_markdown(rows: list[dict[str, Any]]) -> str:
    lines = ["# L3 Derivation Records", ""]
    if not rows:
        lines.append("No L3 derivation records have been persisted for this run.")
        return "\n".join(lines).strip() + "\n"

    for row in rows:
        lines.append(f"## {row.get('title') or row.get('derivation_id') or 'Derivation'}")
        lines.append("")
        lines.append(f"- Derivation id: `{row.get('derivation_id') or '(missing)'}`")
        lines.append(f"- Derivation kind: `{row.get('derivation_kind') or '(missing)'}`")
        lines.append(f"- Epistemic status: `{row.get('epistemic_status') or '(missing)'}`")
        lines.append(f"- Status: `{row.get('status') or '(missing)'}`")
        lines.append(f"- Topic slug: `{row.get('topic_slug') or '(missing)'}`")
        lines.append(f"- Run id: `{row.get('run_id') or '(missing)'}`")
        lines.append("")
        provenance_note = str(row.get("provenance_note") or "").strip()
        if provenance_note:
            lines.append("### Provenance note")
            lines.append("")
            lines.append(provenance_note)
            lines.append("")
        source_refs = _string_list(row.get("source_refs"))
        if source_refs:
            lines.append("### Source refs")
            lines.append("")
            for item in source_refs:
                lines.append(f"- {item}")
            lines.append("")
        assumptions = _string_list(row.get("assumptions"))
        if assumptions:
            lines.append("### Assumptions")
            lines.append("")
            for item in assumptions:
                lines.append(f"- {item}")
            lines.append("")
        body = str(row.get("body") or "").strip()
        if body:
            lines.append("### Derivation body")
            lines.append("")
            lines.append(body)
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def record_l3_derivation_entry(
    *,
    run_root: Path,
    topic_slug: str,
    run_id: str,
    title: str,
    body: str = "",
    derivation_kind: str = "analysis_derivation",
    epistemic_status: str = "ai_provisional_reasoning",
    status: str = "",
    source_refs: list[str] | None = None,
    assumptions: list[str] | None = None,
    provenance_note: str = "",
    updated_by: str = "human",
    derivation_id: str | None = None,
    replace_existing: bool = False,
) -> dict[str, Any]:
    resolved_title = str(title or "").strip() or "Untitled derivation"
    resolved_id = str(derivation_id or "").strip() or f"derivation:{_slugify(resolved_title)}"
    row = {
        "timestamp": _now_iso(),
        "topic_slug": str(topic_slug or "").strip(),
        "run_id": str(run_id or "").strip(),
        "derivation_id": resolved_id,
        "title": resolved_title,
        "body": str(body or "").strip(),
        "derivation_kind": str(derivation_kind or "analysis_derivation").strip(),
        "epistemic_status": str(epistemic_status or "ai_provisional_reasoning").strip(),
        "status": str(status or "").strip(),
        "source_refs": _string_list(source_refs or []),
        "assumptions": _string_list(assumptions or []),
        "provenance_note": str(provenance_note or "").strip()
        or "This is an AI-authored provisional derivation record. It preserves reasoning detail and provenance, but it is not truth unless later validated.",
        "updated_by": str(updated_by or "").strip(),
    }

    paths = derivation_paths(run_root)
    rows = _read_jsonl(paths["ledger"])
    if replace_existing:
        replaced = False
        next_rows: list[dict[str, Any]] = []
        for existing in rows:
            if str(existing.get("derivation_id") or "").strip() == resolved_id:
                next_rows.append(row)
                replaced = True
            else:
                next_rows.append(existing)
        if not replaced:
            next_rows.append(row)
        rows = next_rows
    else:
        rows.append(row)
    _write_jsonl(paths["ledger"], rows)
    paths["note"].write_text(_render_derivation_markdown(rows), encoding="utf-8")

    try:
        from .research_notebook_support import append_notebook_entry

        l3_root = run_root.parent.parent
        append_notebook_entry(
            l3_root,
            kind="derivation_note",
            title=resolved_title,
            body=str(body or "").strip(),
            status=str(status or "").strip(),
            run_id=str(run_id or "").strip(),
            details={
                "derivation_id": resolved_id,
                "derivation_kind": str(derivation_kind or "analysis_derivation").strip(),
                "epistemic_status": str(epistemic_status or "ai_provisional_reasoning").strip(),
                "source_refs": _string_list(source_refs or []),
                "provenance_note": str(provenance_note or "").strip()
                or "This is an AI-authored provisional derivation record. It preserves reasoning detail and provenance, but it is not truth unless later validated.",
            },
        )
    except Exception:
        pass

    return {
        "derivation_id": resolved_id,
        "ledger_path": str(paths["ledger"]),
        "note_path": str(paths["note"]),
        "row": row,
    }
