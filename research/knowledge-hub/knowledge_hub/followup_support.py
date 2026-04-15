from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "aitp-topic"


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def return_shape_for_status(
    self,
    return_status: str,
    unresolved_statuses: set[str] | None = None,
) -> str:
    normalized = str(return_status or "").strip()
    unresolved = unresolved_statuses or set()
    if normalized == "recovered_units":
        return "recovered_units"
    if normalized == "resolved_gap_update":
        return "resolved_gap_update"
    if normalized in unresolved and normalized != "pending_reentry":
        return "still_unresolved_packet"
    return ""

def followup_return_packet_markdown(self, payload: dict[str, Any]) -> str:
    lines = [
        "# Follow-up return packet",
        "",
        f"- Child topic: `{payload.get('child_topic_slug') or '(missing)'}`",
        f"- Parent topic: `{payload.get('parent_topic_slug') or '(missing)'}`",
        f"- Parent run: `{payload.get('parent_run_id') or '(missing)'}`",
        f"- Receipt id: `{payload.get('receipt_id') or '(missing)'}`",
        f"- Query: `{payload.get('query') or '(missing)'}`",
        f"- Source id: `{payload.get('source_id') or '(missing)'}`",
        f"- arXiv id: `{payload.get('arxiv_id') or '(missing)'}`",
        f"- Return status: `{payload.get('return_status') or '(missing)'}`",
        f"- Accepted return shape: `{payload.get('accepted_return_shape') or '(pending)'}`",
        "",
        "## Parent reintegration context",
        "",
        f"- Parent gaps: `{', '.join(payload.get('parent_gap_ids') or []) or '(none)'}`",
        f"- Parent follow-up tasks: `{', '.join(payload.get('parent_followup_task_ids') or []) or '(none)'}`",
        f"- Reentry targets: `{', '.join(payload.get('reentry_targets') or []) or '(none)'}`",
        f"- Supporting regression questions: `{', '.join(payload.get('supporting_regression_question_ids') or []) or '(none)'}`",
        "",
        "## Return route contract",
        "",
        f"- Expected return route: `{payload.get('expected_return_route') or '(missing)'}`",
        f"- Acceptable return shapes: `{', '.join(payload.get('acceptable_return_shapes') or []) or '(none)'}`",
        f"- Unresolved statuses: `{', '.join(payload.get('unresolved_return_statuses') or []) or '(none)'}`",
        f"- Required output artifacts: `{', '.join(payload.get('required_output_artifacts') or []) or '(none)'}`",
        "",
        "## Return summary",
        "",
        payload.get("return_summary") or "(pending)",
        "",
        "## Return artifacts",
        "",
    ]
    for item in payload.get("return_artifact_paths") or ["(none)"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Reintegration requirements", ""])
    for key, value in sorted((payload.get("reintegration_requirements") or {}).items()):
        lines.append(f"- `{key}`: `{str(bool(value)).lower()}`")
    child_summary = str(payload.get("child_topic_summary") or "").strip()
    if child_summary:
        lines.extend(["", "## Child topic summary", "", child_summary, ""])
    return "\n".join(lines) + "\n"

def deferred_buffer_markdown(self, payload: dict[str, Any]) -> str:
    lines = [
        "# Deferred candidate buffer",
        "",
        f"- Topic slug: `{payload['topic_slug']}`",
        f"- Updated at: `{payload['updated_at']}`",
        f"- Updated by: `{payload['updated_by']}`",
        f"- Entry count: `{len(payload.get('entries') or [])}`",
        "",
    ]
    for entry in payload.get("entries") or []:
        lines.extend(
            [
                f"## `{entry.get('entry_id') or '(missing)'}`",
                "",
                f"- Source candidate: `{entry.get('source_candidate_id') or '(missing)'}`",
                f"- Title: `{entry.get('title') or '(missing)'}`",
                f"- Status: `{entry.get('status') or '(missing)'}`",
                f"- Reason: {entry.get('reason') or '(missing)'}",
            ]
        )
        required_l2_types = self._dedupe_strings(list(entry.get("required_l2_types") or []))
        if required_l2_types:
            lines.append(f"- Missing L2 types: `{', '.join(required_l2_types)}`")
        activated_candidate_id = str(entry.get("activated_candidate_id") or "").strip()
        if activated_candidate_id:
            lines.append(f"- Activated candidate: `{activated_candidate_id}`")
        conditions = entry.get("reactivation_conditions") or {}
        if conditions:
            lines.extend(["", "### Reactivation conditions", ""])
            for key in sorted(conditions):
                values = self._dedupe_strings(list(conditions.get(key) or []))
                if values:
                    lines.append(f"- `{key}`: `{', '.join(values)}`")
        notes = str(entry.get("notes") or "").strip()
        if notes:
            lines.extend(["", "### Notes", "", f"- {notes}"])
        lines.append("")
    if not (payload.get("entries") or []):
        lines.append("- No deferred entries are currently buffered.")
        lines.append("")
    return "\n".join(lines)

def followup_subtopics_markdown(self, rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Follow-up subtopics",
        "",
        f"- Entry count: `{len(rows)}`",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"## `{row.get('child_topic_slug') or '(missing)'}`",
                "",
                f"- Parent topic: `{row.get('parent_topic_slug') or '(missing)'}`",
                f"- Parent run: `{row.get('parent_run_id') or '(missing)'}`",
                f"- Query: `{row.get('query') or '(missing)'}`",
                f"- Source id: `{row.get('source_id') or '(missing)'}`",
                f"- arXiv id: `{row.get('arxiv_id') or '(missing)'}`",
                f"- Status: `{row.get('status') or '(missing)'}`",
                f"- Parent gaps: `{', '.join(row.get('parent_gap_ids') or []) or '(none)'}`",
                f"- Parent follow-up tasks: `{', '.join(row.get('parent_followup_task_ids') or []) or '(none)'}`",
                f"- Reentry targets: `{', '.join(row.get('reentry_targets') or []) or '(none)'}`",
                f"- Return packet: `{row.get('return_packet_path') or '(missing)'}`",
                "",
            ]
        )
    if not rows:
        lines.append("- No follow-up subtopics have been spawned yet.")
        lines.append("")
    return "\n".join(lines)

def followup_reintegration_markdown(self, rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Follow-up reintegration",
        "",
        f"- Receipt count: `{len(rows)}`",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"## `{row.get('child_topic_slug') or '(missing)'}`",
                "",
                f"- Parent topic: `{row.get('parent_topic_slug') or '(missing)'}`",
                f"- Parent run: `{row.get('parent_run_id') or '(missing)'}`",
                f"- Return status: `{row.get('return_status') or '(missing)'}`",
                f"- Accepted return shape: `{row.get('accepted_return_shape') or '(missing)'}`",
                f"- Receipt id: `{row.get('receipt_id') or '(missing)'}`",
                f"- Return packet: `{row.get('return_packet_path') or '(missing)'}`",
                f"- Reentry targets: `{', '.join(row.get('reentry_targets') or []) or '(none)'}`",
                f"- Parent gaps: `{', '.join(row.get('parent_gap_ids') or []) or '(none)'}`",
                f"- Child completion: `{row.get('child_topic_completion_status') or 'not_assessed'}`",
                f"- Gap writeback required: `{str(bool(row.get('gap_writeback_required'))).lower()}`",
                "",
                row.get("summary") or "(missing)",
                "",
            ]
        )
    if not rows:
        lines.append("- No follow-up reintegration receipts have been recorded yet.")
        lines.append("")
    return "\n".join(lines)

def followup_gap_writeback_markdown(self, rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Follow-up gap writeback",
        "",
        f"- Entry count: `{len(rows)}`",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"## `{row.get('child_topic_slug') or '(missing)'}`",
                "",
                f"- Parent topic: `{row.get('parent_topic_slug') or '(missing)'}`",
                f"- Parent run: `{row.get('parent_run_id') or '(missing)'}`",
                f"- Return status: `{row.get('return_status') or '(missing)'}`",
                f"- Parent gaps: `{', '.join(row.get('parent_gap_ids') or []) or '(none)'}`",
                f"- Parent follow-up tasks: `{', '.join(row.get('parent_followup_task_ids') or []) or '(none)'}`",
                f"- Reentry targets: `{', '.join(row.get('reentry_targets') or []) or '(none)'}`",
                "",
                row.get("summary") or "(missing)",
                "",
            ]
        )
    if not rows:
        lines.append("- No unresolved child follow-up gap writeback is currently pending.")
        lines.append("")
    return "\n".join(lines)

def load_deferred_buffer(self, topic_slug: str) -> dict[str, Any]:
    paths = self._deferred_buffer_paths(topic_slug)
    return _read_json(paths["json"]) or {
        "buffer_version": 1,
        "topic_slug": topic_slug,
        "updated_at": _now_iso(),
        "updated_by": "aitp-cli",
        "entries": [],
    }

def write_deferred_buffer(self, topic_slug: str, payload: dict[str, Any]) -> dict[str, str]:
    paths = self._deferred_buffer_paths(topic_slug)
    payload["buffer_version"] = 1
    payload["topic_slug"] = topic_slug
    _write_json(paths["json"], payload)
    _write_text(paths["note"], deferred_buffer_markdown(self, payload))
    return {
        "deferred_buffer_path": str(paths["json"]),
        "deferred_buffer_note_path": str(paths["note"]),
    }

def load_followup_subtopic_rows(self, topic_slug: str) -> list[dict[str, Any]]:
    return _read_jsonl(self._followup_subtopics_paths(topic_slug)["jsonl"])

def write_followup_subtopic_rows(self, topic_slug: str, rows: list[dict[str, Any]]) -> dict[str, str]:
    paths = self._followup_subtopics_paths(topic_slug)
    _write_jsonl(paths["jsonl"], rows)
    _write_text(paths["note"], followup_subtopics_markdown(self, rows))
    return {
        "followup_subtopics_path": str(paths["jsonl"]),
        "followup_subtopics_note_path": str(paths["note"]),
    }

def write_followup_return_packet(self, topic_slug: str, payload: dict[str, Any]) -> str:
    path = self._followup_return_packet_path(topic_slug)
    _write_json(path, payload)
    _write_text(self._followup_return_packet_note_path(topic_slug), followup_return_packet_markdown(self, payload))
    return str(path)

def load_followup_reintegration_rows(self, topic_slug: str) -> list[dict[str, Any]]:
    return _read_jsonl(self._followup_reintegration_paths(topic_slug)["jsonl"])

def write_followup_reintegration_rows(self, topic_slug: str, rows: list[dict[str, Any]]) -> dict[str, str]:
    paths = self._followup_reintegration_paths(topic_slug)
    _write_jsonl(paths["jsonl"], rows)
    _write_text(paths["note"], followup_reintegration_markdown(self, rows))
    return {
        "followup_reintegration_path": str(paths["jsonl"]),
        "followup_reintegration_note_path": str(paths["note"]),
    }

def load_followup_gap_writeback_rows(self, topic_slug: str) -> list[dict[str, Any]]:
    return _read_jsonl(self._followup_gap_writeback_paths(topic_slug)["jsonl"])

def write_followup_gap_writeback_rows(self, topic_slug: str, rows: list[dict[str, Any]]) -> dict[str, str]:
    paths = self._followup_gap_writeback_paths(topic_slug)
    _write_jsonl(paths["jsonl"], rows)
    _write_text(paths["note"], followup_gap_writeback_markdown(self, rows))
    return {
        "followup_gap_writeback_path": str(paths["jsonl"]),
        "followup_gap_writeback_note_path": str(paths["note"]),
    }

def reactivation_context(self, topic_slug: str) -> tuple[set[str], str, set[str]]:
    source_rows = _read_jsonl(self._l0_root(topic_slug) / "source_index.jsonl")
    source_ids = {
        str(row.get("source_id") or "").strip()
        for row in source_rows
        if str(row.get("source_id") or "").strip()
    }
    source_text = " ".join(
        self._dedupe_strings(
            [
                str(row.get("title") or "")
                for row in source_rows
            ]
            + [
                str(row.get("summary") or "")
                for row in source_rows
            ]
        )
    ).lower()
    child_topics = {
        str(row.get("child_topic_slug") or "").strip()
        for row in self._load_followup_subtopic_rows(topic_slug)
        if str(row.get("child_topic_slug") or "").strip()
    }
    return source_ids, source_text, child_topics

def buffer_entry_ready_for_reactivation(
    self,
    entry: dict[str, Any],
    *,
    source_ids: set[str],
    source_text: str,
    child_topics: set[str],
) -> bool:
    conditions = entry.get("reactivation_conditions") or {}
    source_id_rules = {
        str(value).strip()
        for value in (conditions.get("source_ids_any") or [])
        if str(value).strip()
    }
    if source_id_rules and source_ids.intersection(source_id_rules):
        return True
    text_rules = [
        str(value).strip().lower()
        for value in (conditions.get("text_contains_any") or [])
        if str(value).strip()
    ]
    if text_rules and any(rule in source_text for rule in text_rules):
        return True
    child_topic_rules = {
        str(value).strip()
        for value in (conditions.get("child_topics_any") or [])
        if str(value).strip()
    }
    if child_topic_rules and child_topics.intersection(child_topic_rules):
        return True
    return not source_id_rules and not text_rules and not child_topic_rules

def apply_candidate_split_contract(
    self,
    *,
    topic_slug: str,
    run_id: str | None = None,
    updated_by: str = "aitp-cli",
) -> dict[str, Any]:
    resolved_run_id = self._resolve_run_id(topic_slug, run_id)
    if not resolved_run_id:
        raise FileNotFoundError(f"Unable to resolve a feedback run for topic {topic_slug}")
    contract_path = self._candidate_split_contract_path(topic_slug, resolved_run_id)
    contract_payload = _read_json(contract_path)
    if contract_payload is None:
        raise FileNotFoundError(f"Candidate split contract missing: {contract_path}")

    ledger_path = self._candidate_ledger_path(topic_slug, resolved_run_id)
    ledger_rows = _read_jsonl(ledger_path)
    ledger_index = {
        str(row.get("candidate_id") or "").strip(): row
        for row in ledger_rows
        if str(row.get("candidate_id") or "").strip()
    }
    receipts_path = self._candidate_split_receipts_path(topic_slug, resolved_run_id)
    receipt_rows = _read_jsonl(receipts_path)
    deferred_buffer = self._load_deferred_buffer(topic_slug)
    deferred_index = {
        str(entry.get("entry_id") or "").strip(): entry
        for entry in deferred_buffer.get("entries") or []
        if str(entry.get("entry_id") or "").strip()
    }

    applied_source_candidates: list[str] = []
    child_candidate_ids: list[str] = []
    buffered_entry_ids: list[str] = []
    skipped_sources: list[str] = []

    for split_payload in contract_payload.get("splits") or []:
        source_candidate_id = str(split_payload.get("source_candidate_id") or "").strip()
        if not source_candidate_id:
            continue
        fingerprint = self._fingerprint_payload(split_payload)
        if any(
            str(row.get("source_candidate_id") or "") == source_candidate_id
            and str(row.get("fingerprint") or "") == fingerprint
            for row in receipt_rows
        ):
            skipped_sources.append(source_candidate_id)
            continue

        source_candidate = ledger_index.get(source_candidate_id)
        if source_candidate is None:
            raise FileNotFoundError(
                f"Split contract references missing source candidate {source_candidate_id} in {ledger_path}"
            )

        split_child_ids: list[str] = []
        split_buffer_ids: list[str] = []
        for child_payload in split_payload.get("child_candidates") or []:
            child_candidate_id = str(child_payload.get("candidate_id") or "").strip()
            if not child_candidate_id:
                continue
            existing_child = ledger_index.get(child_candidate_id) or {}
            child_row = dict(existing_child)
            child_row.update(
                {
                "candidate_id": child_candidate_id,
                "candidate_type": str(child_payload.get("candidate_type") or existing_child.get("candidate_type") or source_candidate.get("candidate_type") or ""),
                "title": str(child_payload.get("title") or existing_child.get("title") or child_candidate_id),
                "summary": str(child_payload.get("summary") or existing_child.get("summary") or ""),
                "topic_slug": topic_slug,
                "run_id": resolved_run_id,
                "origin_refs": list(child_payload.get("origin_refs") or existing_child.get("origin_refs") or source_candidate.get("origin_refs") or []),
                "question": str(child_payload.get("question") or existing_child.get("question") or source_candidate.get("question") or ""),
                "assumptions": list(child_payload.get("assumptions") or existing_child.get("assumptions") or source_candidate.get("assumptions") or []),
                "proposed_validation_route": str(child_payload.get("proposed_validation_route") or existing_child.get("proposed_validation_route") or source_candidate.get("proposed_validation_route") or ""),
                "intended_l2_targets": list(child_payload.get("intended_l2_targets") or existing_child.get("intended_l2_targets") or []),
                "status": str(child_payload.get("status") or existing_child.get("status") or "ready_for_validation"),
                "split_parent_id": source_candidate_id,
                }
            )
            if str(existing_child.get("status") or "") in {"promoted", "auto_promoted"}:
                child_row = existing_child
            else:
                self._replace_candidate_row(topic_slug, resolved_run_id, child_candidate_id, child_row)
                ledger_index[child_candidate_id] = child_row
            split_child_ids.append(child_candidate_id)
            child_candidate_ids.append(child_candidate_id)

        for deferred_payload in split_payload.get("deferred_fragments") or []:
            entry_id = str(deferred_payload.get("entry_id") or "").strip()
            if not entry_id:
                continue
            existing_entry = deferred_index.get(entry_id) or {}
            entry_row = {
                "entry_id": entry_id,
                "source_candidate_id": source_candidate_id,
                "title": str(deferred_payload.get("title") or existing_entry.get("title") or entry_id),
                "summary": str(deferred_payload.get("summary") or existing_entry.get("summary") or ""),
                "reason": str(deferred_payload.get("reason") or existing_entry.get("reason") or ""),
                "status": str(existing_entry.get("status") or "buffered"),
                "required_l2_types": self._dedupe_strings(list(deferred_payload.get("required_l2_types") or existing_entry.get("required_l2_types") or [])),
                "reactivation_conditions": deferred_payload.get("reactivation_conditions") or existing_entry.get("reactivation_conditions") or {},
                "reactivation_candidate": deferred_payload.get("reactivation_candidate") or existing_entry.get("reactivation_candidate") or {},
                "activated_candidate_id": str(existing_entry.get("activated_candidate_id") or ""),
                "activated_at": str(existing_entry.get("activated_at") or ""),
                "notes": str(deferred_payload.get("notes") or existing_entry.get("notes") or ""),
            }
            deferred_index[entry_id] = entry_row
            split_buffer_ids.append(entry_id)
            buffered_entry_ids.append(entry_id)

        updated_source = dict(source_candidate)
        updated_source["status"] = "split_into_children" if split_child_ids else "deferred_buffered"
        updated_source["split_child_ids"] = self._dedupe_strings(
            list(updated_source.get("split_child_ids") or []) + split_child_ids
        )
        updated_source["buffer_entry_ids"] = self._dedupe_strings(
            list(updated_source.get("buffer_entry_ids") or []) + split_buffer_ids
        )
        self._replace_candidate_row(topic_slug, resolved_run_id, source_candidate_id, updated_source)
        ledger_index[source_candidate_id] = updated_source
        applied_source_candidates.append(source_candidate_id)

        receipt_rows.append(
            {
                "event": "applied",
                "source_candidate_id": source_candidate_id,
                "fingerprint": fingerprint,
                "child_candidate_ids": split_child_ids,
                "buffer_entry_ids": split_buffer_ids,
                "updated_at": _now_iso(),
                "updated_by": updated_by,
                "reason": str(split_payload.get("reason") or ""),
            }
        )

    deferred_payload = {
        "buffer_version": 1,
        "topic_slug": topic_slug,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
        "entries": list(deferred_index.values()),
    }
    buffer_paths = self._write_deferred_buffer(topic_slug, deferred_payload)
    _write_jsonl(receipts_path, receipt_rows)
    return {
        "topic_slug": topic_slug,
        "run_id": resolved_run_id,
        "contract_path": str(contract_path),
        "candidate_ledger_path": str(ledger_path),
        "candidate_split_receipts_path": str(receipts_path),
        "applied_source_candidates": applied_source_candidates,
        "child_candidate_ids": child_candidate_ids,
        "buffered_entry_ids": buffered_entry_ids,
        "skipped_source_candidates": skipped_sources,
        **buffer_paths,
    }

def reactivate_deferred_candidates(
    self,
    *,
    topic_slug: str,
    run_id: str | None = None,
    entry_id: str | None = None,
    updated_by: str = "aitp-cli",
) -> dict[str, Any]:
    resolved_run_id = self._resolve_run_id(topic_slug, run_id)
    if not resolved_run_id:
        raise FileNotFoundError(f"Unable to resolve a feedback run for topic {topic_slug}")

    deferred_buffer = self._load_deferred_buffer(topic_slug)
    entries = list(deferred_buffer.get("entries") or [])
    source_ids, source_text, child_topics = self._reactivation_context(topic_slug)
    reactivated_candidate_ids: list[str] = []
    reactivated_entry_ids: list[str] = []

    for row in entries:
        current_entry_id = str(row.get("entry_id") or "").strip()
        if not current_entry_id:
            continue
        if entry_id and current_entry_id != entry_id:
            continue
        if str(row.get("status") or "") != "buffered":
            continue
        if not self._buffer_entry_ready_for_reactivation(
            row,
            source_ids=source_ids,
            source_text=source_text,
            child_topics=child_topics,
        ):
            continue
        candidate_payload = row.get("reactivation_candidate") or {}
        candidate_id = str(candidate_payload.get("candidate_id") or "").strip()
        if not candidate_id:
            continue
        child_row = {
            "candidate_id": candidate_id,
            "candidate_type": str(candidate_payload.get("candidate_type") or ""),
            "title": str(candidate_payload.get("title") or candidate_id),
            "summary": str(candidate_payload.get("summary") or ""),
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "origin_refs": list(candidate_payload.get("origin_refs") or []),
            "question": str(candidate_payload.get("question") or ""),
            "assumptions": list(candidate_payload.get("assumptions") or []),
            "proposed_validation_route": str(candidate_payload.get("proposed_validation_route") or ""),
            "intended_l2_targets": list(candidate_payload.get("intended_l2_targets") or []),
            "status": str(candidate_payload.get("status") or "reactivated"),
            "reactivated_from": current_entry_id,
        }
        self._replace_candidate_row(topic_slug, resolved_run_id, candidate_id, child_row)
        row["status"] = "reactivated"
        row["activated_candidate_id"] = candidate_id
        row["activated_at"] = _now_iso()
        reactivated_candidate_ids.append(candidate_id)
        reactivated_entry_ids.append(current_entry_id)

    deferred_buffer["updated_at"] = _now_iso()
    deferred_buffer["updated_by"] = updated_by
    deferred_buffer["entries"] = entries
    buffer_paths = self._write_deferred_buffer(topic_slug, deferred_buffer)
    return {
        "topic_slug": topic_slug,
        "run_id": resolved_run_id,
        "reactivated_entry_ids": reactivated_entry_ids,
        "reactivated_candidate_ids": reactivated_candidate_ids,
        **buffer_paths,
    }

def spawn_followup_subtopics(
    self,
    *,
    topic_slug: str,
    run_id: str | None = None,
    query: str | None = None,
    receipt_id: str | None = None,
    updated_by: str = "aitp-cli",
) -> dict[str, Any]:
    resolved_run_id = self._resolve_run_id(topic_slug, run_id)
    if not resolved_run_id:
        raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")
    policy = self._load_runtime_policy().get("followup_subtopic_policy") or {}
    allowed_source_types = {
        str(value).strip()
        for value in (policy.get("spawn_target_source_types") or [])
        if str(value).strip()
    }
    max_subtopics = int(policy.get("max_subtopics_per_receipt") or 2)
    bounded_gap_required = bool(policy.get("bounded_gap_required"))
    statement_template = str(policy.get("statement_template") or "")
    human_request_template = str(policy.get("human_request_template") or "")
    expected_return_route = str(policy.get("expected_return_route") or "L0->L1->L3->L4->L2")
    acceptable_return_shapes = self._dedupe_strings(
        list(policy.get("acceptable_return_shapes") or ["recovered_units", "resolved_gap_update", "still_unresolved_packet"])
    )
    required_output_artifacts = self._dedupe_strings(
        list(policy.get("required_output_artifacts") or ["candidate_ledger_or_recovered_units", "gap_or_followup_writeback", "reintegration_summary"])
    )
    unresolved_return_statuses = self._dedupe_strings(
        list(policy.get("unresolved_return_statuses") or ["pending_reentry", "returned_with_gap", "returned_unresolved"])
    )
    reintegration_requirements = policy.get("reintegration_requirements") or {
        "must_write_back_parent_gaps": True,
        "must_update_reentry_targets": True,
        "must_not_patch_parent_directly": True,
        "requires_child_topic_summary": True,
    }

    receipts_path = self._validation_run_root(topic_slug, resolved_run_id) / "literature_followup_receipts.jsonl"
    receipt_rows = _read_jsonl(receipts_path)
    followup_rows = self._load_followup_subtopic_rows(topic_slug)
    existing_keys = {
        (str(row.get("query") or ""), str(row.get("arxiv_id") or ""))
        for row in followup_rows
    }
    spawned_rows: list[dict[str, Any]] = []

    for row in receipt_rows:
        if receipt_id and str(row.get("receipt_id") or "") != receipt_id:
            continue
        if query and str(row.get("query") or "") != query:
            continue
        target_source_type = str(row.get("target_source_type") or "paper").strip() or "paper"
        if allowed_source_types and target_source_type not in allowed_source_types:
            continue
        if str(row.get("status") or "") != "completed":
            continue
        parent_gap_ids = self._dedupe_strings(list(row.get("parent_gap_ids") or []))
        raw_parent_followups = row.get("parent_followup_task_ids")
        if raw_parent_followups is None:
            single_parent_followup = str(row.get("parent_followup_task_id") or "").strip()
            raw_parent_followups = [single_parent_followup] if single_parent_followup else []
        parent_followup_task_ids = self._dedupe_strings(list(raw_parent_followups or []))
        reentry_targets = self._dedupe_strings(list(row.get("reentry_targets") or []))
        supporting_regression_question_ids = self._dedupe_strings(
            list(row.get("supporting_regression_question_ids") or [])
        )
        if bounded_gap_required and not (
            parent_gap_ids
            or parent_followup_task_ids
            or reentry_targets
            or supporting_regression_question_ids
        ):
            continue
        for match in list(row.get("matches") or [])[:max_subtopics]:
            arxiv_id = str(match.get("arxiv_id") or "").strip()
            if not arxiv_id:
                continue
            dedupe_key = (str(row.get("query") or ""), arxiv_id)
            if dedupe_key in existing_keys:
                continue
            child_topic_slug = f"{topic_slug}--followup--{_slugify(arxiv_id)}"
            statement = (
                statement_template.format(
                    query=str(row.get("query") or ""),
                    topic_slug=topic_slug,
                    arxiv_id=arxiv_id,
                )
                if statement_template
                else f"Follow up the cited-literature gap `{row.get('query') or ''}` through source `{arxiv_id}`."
            )
            human_request = (
                human_request_template.format(
                    query=str(row.get("query") or ""),
                    topic_slug=topic_slug,
                    arxiv_id=arxiv_id,
                )
                if human_request_template
                else f"Study arXiv:{arxiv_id} for the bounded follow-up gap `{row.get('query') or ''}`."
            )
            bootstrap = self.orchestrate(
                topic_slug=child_topic_slug,
                statement=statement,
                updated_by=updated_by,
                arxiv_ids=[arxiv_id],
                human_request=human_request,
            )
            source_id = ""
            child_source_rows = _read_jsonl(
                self._l0_root(child_topic_slug) / "source_index.jsonl"
            )
            if child_source_rows:
                source_id = str(child_source_rows[-1].get("source_id") or "")
            return_packet = {
                "return_packet_version": 1,
                "child_topic_slug": child_topic_slug,
                "parent_topic_slug": topic_slug,
                "parent_run_id": resolved_run_id,
                "receipt_id": str(row.get("receipt_id") or ""),
                "query": str(row.get("query") or ""),
                "parent_gap_ids": parent_gap_ids,
                "parent_followup_task_ids": parent_followup_task_ids,
                "reentry_targets": reentry_targets,
                "supporting_regression_question_ids": supporting_regression_question_ids,
                "source_id": source_id,
                "arxiv_id": arxiv_id,
                "expected_return_route": expected_return_route,
                "acceptable_return_shapes": acceptable_return_shapes,
                "required_output_artifacts": required_output_artifacts,
                "unresolved_return_statuses": unresolved_return_statuses,
                "return_status": "pending_reentry",
                "reintegration_requirements": reintegration_requirements,
                "updated_at": _now_iso(),
                "updated_by": updated_by,
            }
            return_packet_path = self._write_followup_return_packet(child_topic_slug, return_packet)
            spawned_row = {
                "parent_topic_slug": topic_slug,
                "parent_run_id": resolved_run_id,
                "receipt_id": str(row.get("receipt_id") or ""),
                "query": str(row.get("query") or ""),
                "target_source_type": target_source_type,
                "triggered_by_result_id": str(row.get("result_id") or row.get("triggered_by_result_id") or ""),
                "parent_gap_ids": parent_gap_ids,
                "parent_followup_task_ids": parent_followup_task_ids,
                "reentry_targets": reentry_targets,
                "supporting_regression_question_ids": supporting_regression_question_ids,
                "arxiv_id": arxiv_id,
                "source_id": source_id,
                "child_topic_slug": child_topic_slug,
                "status": "spawned",
                "statement": statement,
                "human_request": human_request,
                "runtime_root": str(bootstrap.get("runtime_root") or ""),
                "return_packet_path": return_packet_path,
                "updated_at": _now_iso(),
                "updated_by": updated_by,
            }
            followup_rows.append(spawned_row)
            spawned_rows.append(spawned_row)
            existing_keys.add(dedupe_key)

    followup_paths = self._write_followup_subtopic_rows(topic_slug, followup_rows)
    return {
        "topic_slug": topic_slug,
        "run_id": resolved_run_id,
        "literature_followup_receipts_path": str(receipts_path),
        "spawned_subtopics": spawned_rows,
        **followup_paths,
    }

def update_followup_return_packet(
    self,
    *,
    topic_slug: str,
    run_id: str | None = None,
    return_status: str,
    accepted_return_shape: str | None = None,
    return_summary: str | None = None,
    child_topic_summary: str | None = None,
    return_artifact_paths: list[str] | None = None,
    updated_by: str = "aitp-cli",
    refresh_runtime_bundle: bool = True,
) -> dict[str, Any]:
    packet_path = self._followup_return_packet_path(topic_slug)
    packet = _read_json(packet_path)
    if packet is None:
        raise FileNotFoundError(f"Follow-up return packet missing for child topic {topic_slug}")

    normalized_status = str(return_status or "").strip()
    if not normalized_status:
        raise ValueError("Return status is required.")

    policy = self._load_runtime_policy().get("followup_subtopic_policy") or {}
    unresolved_statuses = {
        str(value).strip()
        for value in (policy.get("unresolved_return_statuses") or [])
        if str(value).strip()
    }
    if not unresolved_statuses:
        unresolved_statuses = {"pending_reentry", "returned_with_gap", "returned_unresolved"}
    supported_statuses = {"pending_reentry", "recovered_units", "resolved_gap_update"} | unresolved_statuses
    if normalized_status not in supported_statuses:
        raise ValueError(f"Unsupported follow-up return status: {normalized_status}")

    acceptable_return_shapes = self._dedupe_strings(list(packet.get("acceptable_return_shapes") or []))
    resolved_return_shape = (
        str(accepted_return_shape or "").strip()
        or self._return_shape_for_status(normalized_status, unresolved_statuses)
    )
    if normalized_status == "pending_reentry":
        resolved_return_shape = ""
    if resolved_return_shape and acceptable_return_shapes and resolved_return_shape not in acceptable_return_shapes:
        raise ValueError(
            f"Return shape {resolved_return_shape} is not allowed for child topic {topic_slug}."
        )

    resolved_artifact_paths = self._dedupe_strings(list(return_artifact_paths or []))
    if not resolved_artifact_paths:
        resolved_artifact_paths = self._dedupe_strings(list(packet.get("return_artifact_paths") or []))

    resolved_summary = str(return_summary or packet.get("return_summary") or "").strip()
    resolved_child_summary = str(child_topic_summary or packet.get("child_topic_summary") or "").strip()
    if normalized_status in {"recovered_units", "resolved_gap_update"} and not resolved_artifact_paths:
        raise ValueError(
            "Recovered follow-up returns must name at least one durable return artifact path."
        )
    if normalized_status in unresolved_statuses and normalized_status != "pending_reentry" and not resolved_summary:
        raise ValueError("Unresolved follow-up returns must provide a return summary.")

    resolved_child_run_id = self._resolve_run_id(topic_slug, run_id)
    updated_packet = dict(packet)
    updated_packet["return_status"] = normalized_status
    if resolved_return_shape:
        updated_packet["accepted_return_shape"] = resolved_return_shape
    else:
        updated_packet.pop("accepted_return_shape", None)
    if resolved_summary:
        updated_packet["return_summary"] = resolved_summary
    elif normalized_status == "pending_reentry":
        updated_packet.pop("return_summary", None)
    if resolved_artifact_paths:
        updated_packet["return_artifact_paths"] = resolved_artifact_paths
    elif normalized_status == "pending_reentry":
        updated_packet.pop("return_artifact_paths", None)
    if resolved_child_summary:
        updated_packet["child_topic_summary"] = resolved_child_summary
    if resolved_child_run_id:
        updated_packet["child_run_id"] = resolved_child_run_id
    updated_packet["updated_at"] = _now_iso()
    updated_packet["updated_by"] = updated_by
    updated_packet["return_updated_at"] = updated_packet["updated_at"]
    updated_packet["return_updated_by"] = updated_by
    self._write_followup_return_packet(topic_slug, updated_packet)

    result = {
        **updated_packet,
        "topic_slug": topic_slug,
        "return_packet_path": str(packet_path),
        "return_packet_note_path": str(self._followup_return_packet_note_path(topic_slug)),
    }
    if refresh_runtime_bundle:
        result["runtime_protocol"] = self._materialize_runtime_protocol_bundle(
            topic_slug=topic_slug,
            updated_by=updated_by,
        )
    return result

def reintegrate_followup_subtopic(
    self,
    *,
    topic_slug: str,
    child_topic_slug: str,
    run_id: str | None = None,
    updated_by: str = "aitp-cli",
) -> dict[str, Any]:
    resolved_run_id = self._resolve_run_id(topic_slug, run_id)
    if not resolved_run_id:
        raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")
    followup_rows = self._load_followup_subtopic_rows(topic_slug)
    matching_row = next(
        (
            row
            for row in followup_rows
            if str(row.get("child_topic_slug") or "").strip() == child_topic_slug
        ),
        None,
    )
    if matching_row is None:
        raise FileNotFoundError(f"Follow-up child topic not registered under parent topic {topic_slug}: {child_topic_slug}")
    return_packet_path = str(matching_row.get("return_packet_path") or "").strip() or str(
        self._followup_return_packet_path(child_topic_slug)
    )
    return_packet = _read_json(Path(return_packet_path))
    if return_packet is None:
        raise FileNotFoundError(f"Follow-up return packet missing for child topic {child_topic_slug}")
    if str(return_packet.get("parent_topic_slug") or "").strip() != topic_slug:
        raise ValueError("Follow-up return packet parent topic does not match the requested parent topic.")
    return_status = str(return_packet.get("return_status") or "").strip() or "pending_reentry"
    if return_status == "pending_reentry":
        raise ValueError("Child topic still reports pending_reentry and cannot be reintegrated yet.")
    acceptable_return_shapes = self._dedupe_strings(list(return_packet.get("acceptable_return_shapes") or []))
    policy = self._load_runtime_policy().get("followup_subtopic_policy") or {}
    unresolved_statuses = {
        str(value).strip()
        for value in (policy.get("unresolved_return_statuses") or [])
        if str(value).strip()
    }
    if not unresolved_statuses:
        unresolved_statuses = {"pending_reentry", "returned_with_gap", "returned_unresolved"}
    unresolved_statuses.discard("pending_reentry")
    accepted_return_shape = str(return_packet.get("accepted_return_shape") or "").strip()
    if not accepted_return_shape:
        accepted_return_shape = self._return_shape_for_status(return_status, unresolved_statuses)
        if not accepted_return_shape and acceptable_return_shapes and return_status != "pending_reentry":
            accepted_return_shape = acceptable_return_shapes[0]
    if accepted_return_shape and acceptable_return_shapes and accepted_return_shape not in acceptable_return_shapes:
        raise ValueError(
            f"Accepted return shape {accepted_return_shape} is not allowed by the child return packet."
        )
    return_artifact_paths = self._dedupe_strings(list(return_packet.get("return_artifact_paths") or []))
    if return_status in {"recovered_units", "resolved_gap_update"} and not return_artifact_paths:
        raise ValueError("Recovered child follow-up returns must provide durable return artifact paths before reintegration.")
    parent_status = "returned_with_gap" if return_status in unresolved_statuses else "reintegrated"
    child_completion = _read_json(self._topic_completion_paths(child_topic_slug)["json"]) or {}
    reintegration_requirements = dict(return_packet.get("reintegration_requirements") or {})
    summary = (
        str(return_packet.get("return_summary") or "").strip()
        or str(return_packet.get("summary") or "").strip()
        or (
            "Child topic returned with unresolved gaps."
            if parent_status == "returned_with_gap"
            else "Child topic return packet was reintegrated into the parent topic."
        )
    )
    receipt_row = {
        "parent_topic_slug": topic_slug,
        "parent_run_id": resolved_run_id,
        "child_topic_slug": child_topic_slug,
        "receipt_id": str(return_packet.get("receipt_id") or matching_row.get("receipt_id") or ""),
        "return_status": return_status,
        "accepted_return_shape": accepted_return_shape,
        "source_id": str(return_packet.get("source_id") or matching_row.get("source_id") or ""),
        "arxiv_id": str(return_packet.get("arxiv_id") or matching_row.get("arxiv_id") or ""),
        "reentry_targets": self._dedupe_strings(list(return_packet.get("reentry_targets") or matching_row.get("reentry_targets") or [])),
        "parent_gap_ids": self._dedupe_strings(list(return_packet.get("parent_gap_ids") or matching_row.get("parent_gap_ids") or [])),
        "parent_followup_task_ids": self._dedupe_strings(
            list(return_packet.get("parent_followup_task_ids") or matching_row.get("parent_followup_task_ids") or [])
        ),
        "supporting_regression_question_ids": self._dedupe_strings(
            list(return_packet.get("supporting_regression_question_ids") or matching_row.get("supporting_regression_question_ids") or [])
        ),
        "return_packet_path": return_packet_path,
        "return_artifact_paths": return_artifact_paths,
        "child_topic_completion_status": str(child_completion.get("status") or "not_assessed"),
        "child_topic_summary": str(return_packet.get("child_topic_summary") or "").strip(),
        "gap_writeback_required": parent_status == "returned_with_gap"
        and bool(reintegration_requirements.get("must_write_back_parent_gaps")),
        "reentry_update_required": bool(reintegration_requirements.get("must_update_reentry_targets")),
        "summary": summary,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    reintegration_rows = [
        row
        for row in self._load_followup_reintegration_rows(topic_slug)
        if str(row.get("child_topic_slug") or "").strip() != child_topic_slug
    ]
    reintegration_rows.append(receipt_row)
    reintegration_paths = self._write_followup_reintegration_rows(topic_slug, reintegration_rows)

    gap_writeback_rows = [
        row
        for row in self._load_followup_gap_writeback_rows(topic_slug)
        if str(row.get("child_topic_slug") or "").strip() != child_topic_slug
    ]
    if receipt_row["gap_writeback_required"]:
        gap_writeback_rows.append(
            {
                "parent_topic_slug": topic_slug,
                "parent_run_id": resolved_run_id,
                "child_topic_slug": child_topic_slug,
                "receipt_id": receipt_row["receipt_id"],
                "return_status": return_status,
                "parent_gap_ids": receipt_row["parent_gap_ids"],
                "parent_followup_task_ids": receipt_row["parent_followup_task_ids"],
                "reentry_targets": receipt_row["reentry_targets"],
                "summary": summary,
                "return_packet_path": return_packet_path,
                "return_artifact_paths": return_artifact_paths,
                "updated_at": _now_iso(),
                "updated_by": updated_by,
            }
        )
    gap_writeback_paths = self._write_followup_gap_writeback_rows(topic_slug, gap_writeback_rows)

    updated_followup_rows: list[dict[str, Any]] = []
    for row in followup_rows:
        if str(row.get("child_topic_slug") or "").strip() != child_topic_slug:
            updated_followup_rows.append(row)
            continue
        updated_row = dict(row)
        updated_row["status"] = parent_status
        updated_row["reintegrated_at"] = _now_iso()
        updated_row["reintegrated_by"] = updated_by
        updated_row["reintegration_receipt_path"] = reintegration_paths["followup_reintegration_path"]
        updated_row["return_status"] = return_status
        updated_followup_rows.append(updated_row)
    followup_paths = self._write_followup_subtopic_rows(topic_slug, updated_followup_rows)
    completion = self.assess_topic_completion(
        topic_slug=topic_slug,
        run_id=resolved_run_id,
        updated_by=updated_by,
        refresh_runtime_bundle=False,
    )
    runtime_protocol = self._materialize_runtime_protocol_bundle(
        topic_slug=topic_slug,
        updated_by=updated_by,
    )
    return {
        "topic_slug": topic_slug,
        "run_id": resolved_run_id,
        "child_topic_slug": child_topic_slug,
        "parent_followup_status": parent_status,
        "reintegration_receipt": receipt_row,
        **reintegration_paths,
        **gap_writeback_paths,
        **followup_paths,
        "topic_completion": completion,
        "runtime_protocol": runtime_protocol,
    }
