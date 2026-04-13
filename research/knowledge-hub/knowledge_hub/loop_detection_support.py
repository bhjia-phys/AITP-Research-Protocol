from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


LOOP_DETECTION_RETRY_THRESHOLD = 3


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


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


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _dedupe_strings(values: list[str] | None) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        normalized = str(value or "").strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return deduped


def _theory_facing_lane(lane: str, selected_pending_action: dict[str, Any] | None) -> bool:
    if str(lane or "").strip() == "formal_theory":
        return True
    action_type = str((selected_pending_action or {}).get("action_type") or "").strip()
    action_summary = str((selected_pending_action or {}).get("summary") or "")
    if action_type in {"proof_review", "formal_theory_revision"}:
        return True
    return bool(re.search(r"(proof|theorem|formal|lean|derivation)", action_summary, flags=re.IGNORECASE))


def _loop_detection_paths(service: Any, topic_slug: str) -> dict[str, Path]:
    runtime_root = service._runtime_root(topic_slug)
    return {
        "json": runtime_root / "loop_detection.json",
        "note": runtime_root / "loop_detection.md",
        "metrics": runtime_root / "theory_operations.jsonl",
    }


def _strategy_suggestion(blocker_tags: list[str], source_operation_kind: str) -> tuple[str, str, list[str]]:
    lowered = {str(item).strip().lower() for item in blocker_tags}
    if "missing_source_anchors" in lowered:
        return (
            "source_recovery",
            "Return to source-anchor recovery before another theorem-facing retry. Do not rerun the same coverage path while anchors stay unresolved.",
            [
                "Recover the missing source anchors and cited dependencies first.",
                "Only then rerun the theory coverage path on the same candidate.",
            ],
        )
    if "prerequisite_closure_incomplete" in lowered or "formalization_blockers_present" in lowered:
        return (
            "prerequisite_closure",
            "Decompose the theorem packet or close prerequisites before retrying the same formal-theory route.",
            [
                "Split the current theorem-facing artifact into a narrower packet if the blockers are mixed.",
                "Close prerequisite proofs or obligations before another formal-theory audit pass.",
            ],
        )
    if source_operation_kind == "formal_theory_audit":
        return (
            "change_strategy",
            "The same formal-theory route keeps stalling. Change strategy or decompose the artifact before another retry.",
            [
                "Try a different theorem-facing strategy instead of repeating the same formal review pass.",
                "Narrow the artifact or open a bounded follow-up packet before retrying.",
            ],
        )
    return (
        "change_strategy",
        "The same theorem-facing route keeps repeating without progress. Change strategy or decompose the artifact before another retry.",
        [
            "Do not repeat the same approach again without a strategy change.",
            "Decompose the artifact or switch to a different supporting lane first.",
        ],
    )


def loop_detection_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Loop detection",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Retry threshold: `{payload.get('retry_threshold') or 0}`",
        f"- Retry count: `{payload.get('retry_count') or 0}`",
        f"- Candidate id: `{payload.get('candidate_id') or '(none)'}`",
        f"- Source operation kind: `{payload.get('source_operation_kind') or '(none)'}`",
        f"- Suggestion kind: `{payload.get('suggestion_kind') or '(none)'}`",
        "",
        payload.get("summary") or "(missing)",
        "",
        "## Suggested intervention",
        "",
        payload.get("strategy_change_suggestion") or "(none)",
        "",
        "## Recommended actions",
        "",
    ]
    for row in payload.get("recommended_actions") or ["(none)"]:
        lines.append(f"- {row}")
    lines.extend(["", "## Evidence events", ""])
    for row in payload.get("evidence_event_ids") or ["(none)"]:
        lines.append(f"- `{row}`" if row != "(none)" else "- (none)")
    return "\n".join(lines) + "\n"


def materialize_loop_detection(
    service: Any,
    *,
    topic_slug: str,
    updated_by: str,
    lane: str,
    selected_pending_action: dict[str, Any] | None,
) -> dict[str, Any]:
    paths = _loop_detection_paths(service, topic_slug)
    rows = _read_jsonl(paths["metrics"])
    retry_rows = [
        row
        for row in rows
        if str(row.get("operation_kind") or "").strip() == "derivation_retry"
    ]
    payload: dict[str, Any] = {
        "topic_slug": topic_slug,
        "status": "clear",
        "retry_threshold": LOOP_DETECTION_RETRY_THRESHOLD,
        "retry_count": 0,
        "candidate_id": "",
        "candidate_type": "",
        "source_operation_kind": "",
        "blocker_tags": [],
        "suggestion_kind": "none",
        "strategy_change_suggestion": "",
        "recommended_actions": [],
        "evidence_event_ids": [],
        "path": service._relativize(paths["json"]),
        "note_path": service._relativize(paths["note"]),
        "updated_at": _now_iso(),
        "updated_by": updated_by,
        "summary": "No repeated theorem-facing retry loop is currently active.",
    }

    if _theory_facing_lane(lane, selected_pending_action) and retry_rows:
        ranked = sorted(
            retry_rows,
            key=lambda row: (
                int((row.get("metric_values") or {}).get("attempt_index") or 0),
                str(row.get("recorded_at") or ""),
            ),
            reverse=True,
        )
        top = ranked[0]
        retry_count = int((top.get("metric_values") or {}).get("attempt_index") or 0)
        candidate_id = str(top.get("candidate_id") or "").strip()
        candidate_type = str(top.get("candidate_type") or "").strip()
        source_operation_kind = str((top.get("metric_values") or {}).get("source_operation_kind") or "").strip()
        blocker_tags = _dedupe_strings(list(top.get("blocker_tags") or []))
        evidence_event_ids = _dedupe_strings(
            [str(row.get("event_id") or "").strip() for row in ranked if str(row.get("candidate_id") or "").strip() == candidate_id]
        )
        if retry_count >= LOOP_DETECTION_RETRY_THRESHOLD:
            suggestion_kind, suggestion, recommended_actions = _strategy_suggestion(blocker_tags, source_operation_kind)
            payload.update(
                {
                    "status": "active",
                    "retry_count": retry_count,
                    "candidate_id": candidate_id,
                    "candidate_type": candidate_type,
                    "source_operation_kind": source_operation_kind,
                    "blocker_tags": blocker_tags,
                    "suggestion_kind": suggestion_kind,
                    "strategy_change_suggestion": suggestion,
                    "recommended_actions": recommended_actions,
                    "evidence_event_ids": evidence_event_ids,
                    "summary": (
                        f"Loop detected: `{candidate_id or 'candidate'}` has repeated `{source_operation_kind or 'theory'}` retries "
                        f"({retry_count} attempts) on the same theorem-facing approach."
                    ),
                }
            )
        else:
            payload.update(
                {
                    "retry_count": retry_count,
                    "candidate_id": candidate_id,
                    "candidate_type": candidate_type,
                    "source_operation_kind": source_operation_kind,
                    "blocker_tags": blocker_tags,
                    "evidence_event_ids": evidence_event_ids,
                    "summary": "Retry evidence exists, but the threshold for loop intervention is not yet met.",
                }
            )

    _write_json(paths["json"], payload)
    _write_text(paths["note"], loop_detection_markdown(payload))
    return payload
