from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

ALLOWED_ANALYTICAL_CHECK_KINDS = {
    "limiting_case",
    "dimensional_consistency",
    "symmetry",
    "self_consistency",
    "source_cross_reference",
}
ALLOWED_ANALYTICAL_CHECK_STATUSES = {
    "passed",
    "failed",
    "blocked",
    "not_run",
    "needs_followup",
}
ALLOWED_READING_DEPTHS = {"skim", "targeted", "deep"}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _dedupe_strings(values: Any) -> list[str]:
    if isinstance(values, (str, bytes)):
        values = [values]
    if not isinstance(values, list):
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in values:
        text = str(raw or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return normalized


def _normalize_checks(
    checks: list[dict[str, Any]] | None,
    *,
    default_source_anchors: list[str],
    default_assumption_refs: list[str],
    default_regime_note: str,
    default_reading_depth: str,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in checks or []:
        kind = str(row.get("kind") or "").strip()
        label = str(row.get("label") or "").strip()
        status = str(row.get("status") or "").strip().lower()
        notes = str(row.get("notes") or "").strip()
        if not kind or not label or not status:
            raise ValueError("analytical checks must include kind, label, and status")
        if kind not in ALLOWED_ANALYTICAL_CHECK_KINDS:
            raise ValueError(
                "analytical check kind must be one of: "
                + ", ".join(sorted(ALLOWED_ANALYTICAL_CHECK_KINDS))
            )
        if status not in ALLOWED_ANALYTICAL_CHECK_STATUSES:
            raise ValueError(
                "analytical check status must be one of: "
                + ", ".join(sorted(ALLOWED_ANALYTICAL_CHECK_STATUSES))
            )
        normalized.append(
            {
                "kind": kind,
                "label": label,
                "status": status,
                "notes": notes,
                "source_anchors": _dedupe_strings(row.get("source_anchors"))
                or list(default_source_anchors),
                "assumption_refs": _dedupe_strings(row.get("assumption_refs"))
                or list(default_assumption_refs),
                "regime_note": str(row.get("regime_note") or "").strip() or default_regime_note,
                "reading_depth": _normalize_reading_depth(
                    str(row.get("reading_depth") or "").strip() or default_reading_depth
                ),
            }
        )
    return normalized


def _normalize_reading_depth(reading_depth: str | None) -> str:
    normalized = str(reading_depth or "").strip().lower() or "targeted"
    if normalized not in ALLOWED_READING_DEPTHS:
        raise ValueError("reading_depth must be one of: skim, targeted, deep")
    return normalized


def _compute_blocking_reasons(
    *,
    checks: list[dict[str, Any]],
) -> list[str]:
    blockers: list[str] = []
    if not checks:
        blockers.append("missing_analytical_checks")
    if any(not row.get("source_anchors") for row in checks):
        blockers.append("missing_source_anchors")
    if any(not row.get("assumption_refs") and not row.get("regime_note") for row in checks):
        blockers.append("missing_assumption_or_regime_context")
    if not any(row["status"] == "passed" for row in checks):
        blockers.append("no_passed_analytical_check")
    for row in checks:
        if row["status"] in {"failed", "blocked"}:
            blockers.append(f"{row['kind']}:{row['label']}={row['status']}")
    deduped: list[str] = []
    seen: set[str] = set()
    for item in blockers:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _default_summary(
    *,
    overall_status: str,
    checks: list[dict[str, Any]],
    source_anchors: list[str],
) -> str:
    if checks:
        first_check = checks[0]
        return (
            f"Analytical review is `{overall_status}` with `{first_check['kind']}` "
            f"check `{first_check['label']}` and {len(source_anchors)} source anchor(s)."
        )
    return "Analytical review is blocked because no durable analytical checks were recorded."


def _rollup_source_anchors(checks: list[dict[str, Any]]) -> list[str]:
    anchors: list[str] = []
    for row in checks:
        anchors.extend(_dedupe_strings(row.get("source_anchors")))
    return _dedupe_strings(anchors)


def _rollup_assumption_refs(checks: list[dict[str, Any]]) -> list[str]:
    assumptions: list[str] = []
    for row in checks:
        assumptions.extend(_dedupe_strings(row.get("assumption_refs")))
    return _dedupe_strings(assumptions)


def _rollup_regime_note(checks: list[dict[str, Any]]) -> str:
    notes = [
        str(row.get("regime_note") or "").strip()
        for row in checks
        if str(row.get("regime_note") or "").strip()
    ]
    return "; ".join(_dedupe_strings(notes))


def _rollup_reading_depth(checks: list[dict[str, Any]], *, fallback: str) -> str:
    reading_depths = [
        str(row.get("reading_depth") or "").strip()
        for row in checks
        if str(row.get("reading_depth") or "").strip()
    ]
    deduped = _dedupe_strings(reading_depths)
    return deduped[0] if deduped else fallback


def _update_candidate_after_review(
    self,
    *,
    topic_slug: str,
    resolved_run_id: str,
    candidate_id: str,
    candidate: dict[str, Any],
    packet_paths: dict[str, Path],
    overall_status: str,
    checks: list[dict[str, Any]],
    source_anchors: list[str],
) -> None:
    updated_candidate = dict(candidate)
    updated_candidate["analytical_review_overall_status"] = overall_status
    updated_candidate["analytical_check_kinds"] = self._dedupe_strings(
        [row["kind"] for row in checks]
    )
    updated_candidate["analytical_source_anchors"] = self._dedupe_strings(source_anchors)
    theory_packet_refs = dict(updated_candidate.get("theory_packet_refs") or {})
    theory_packet_refs["analytical_review"] = self._relativize(packet_paths["analytical_review"])
    updated_candidate["theory_packet_refs"] = theory_packet_refs
    self._replace_candidate_row(topic_slug, resolved_run_id, candidate_id, updated_candidate)


def audit_analytical_review(
    self,
    *,
    topic_slug: str,
    candidate_id: str,
    run_id: str | None = None,
    updated_by: str = "aitp-cli",
    checks: list[dict[str, Any]] | None = None,
    source_anchors: list[str] | None = None,
    assumption_refs: list[str] | None = None,
    regime_note: str | None = None,
    reading_depth: str | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    resolved_run_id = self._resolve_run_id(topic_slug, run_id)
    if not resolved_run_id:
        raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")

    candidate = self._load_candidate(topic_slug, resolved_run_id, candidate_id)
    normalized_source_anchors = self._dedupe_strings(source_anchors)
    normalized_assumption_refs = self._dedupe_strings(assumption_refs)
    normalized_regime_note = str(regime_note or "").strip()
    normalized_reading_depth = _normalize_reading_depth(reading_depth)
    normalized_checks = _normalize_checks(
        checks,
        default_source_anchors=normalized_source_anchors,
        default_assumption_refs=normalized_assumption_refs,
        default_regime_note=normalized_regime_note,
        default_reading_depth=normalized_reading_depth,
    )
    normalized_source_anchors = _rollup_source_anchors(normalized_checks)
    normalized_assumption_refs = _rollup_assumption_refs(normalized_checks)
    normalized_regime_note = _rollup_regime_note(normalized_checks)
    normalized_reading_depth = _rollup_reading_depth(
        normalized_checks,
        fallback=normalized_reading_depth,
    )
    blocking_reasons = _compute_blocking_reasons(
        checks=normalized_checks,
    )
    overall_status = "ready" if not blocking_reasons else "blocked"
    updated_at = _now_iso()
    packet_paths = self._theory_packet_paths(topic_slug, resolved_run_id, candidate_id)
    analytical_review = {
        "schema_version": 1,
        "topic_slug": topic_slug,
        "run_id": resolved_run_id,
        "candidate_id": candidate_id,
        "candidate_type": str(candidate.get("candidate_type") or ""),
        "overall_status": overall_status,
        "blocking_reasons": blocking_reasons,
        "check_count": len(normalized_checks),
        "check_kinds": self._dedupe_strings([row["kind"] for row in normalized_checks]),
        "passed_check_count": sum(1 for row in normalized_checks if row["status"] == "passed"),
        "failed_check_count": sum(1 for row in normalized_checks if row["status"] == "failed"),
        "blocked_check_count": sum(1 for row in normalized_checks if row["status"] == "blocked"),
        "reading_depth": normalized_reading_depth,
        "source_anchors": normalized_source_anchors,
        "assumption_refs": normalized_assumption_refs,
        "regime_note": normalized_regime_note,
        "checks": normalized_checks,
        "summary": str(summary or "").strip()
        or _default_summary(
            overall_status=overall_status,
            checks=normalized_checks,
            source_anchors=normalized_source_anchors,
        ),
        "analytical_review_path": self._relativize(packet_paths["analytical_review"]),
        "updated_at": updated_at,
        "updated_by": updated_by,
    }
    _write_json(packet_paths["analytical_review"], analytical_review)
    _update_candidate_after_review(
        self,
        topic_slug=topic_slug,
        resolved_run_id=resolved_run_id,
        candidate_id=candidate_id,
        candidate=candidate,
        packet_paths=packet_paths,
        overall_status=overall_status,
        checks=normalized_checks,
        source_anchors=normalized_source_anchors,
    )
    return {
        "topic_slug": topic_slug,
        "run_id": resolved_run_id,
        "candidate_id": candidate_id,
        "candidate_type": str(candidate.get("candidate_type") or ""),
        "overall_status": overall_status,
        "blocking_reasons": blocking_reasons,
        "paths": {
            "analytical_review": str(packet_paths["analytical_review"]),
        },
        "artifacts": {
            "analytical_review": analytical_review,
        },
    }
