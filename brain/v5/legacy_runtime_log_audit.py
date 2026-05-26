"""Read-only marker audit packets for legacy runtime logs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable


DEFAULT_MAX_MATCHES_PER_FILE = 20
MAX_SNIPPET_CHARS = 240


def build_legacy_runtime_log_marker_audit(
    ws: Any,
    *,
    topic: str,
    markers: Iterable[str],
    expected_min_count: int = 1,
    raw_log_files: Iterable[str | Path] | None = None,
    orientation_log_files: Iterable[str | Path] | None = None,
    migration_dir: str | Path = "",
    max_matches_per_file: int = DEFAULT_MAX_MATCHES_PER_FILE,
) -> dict[str, Any]:
    """Build a read-only audit over provided raw runtime logs.

    Orientation logs are scanned for reviewer context, but never count toward
    satisfying raw runtime marker requirements.
    """

    marker_specs = _marker_specs(markers, expected_min_count)
    max_matches = max(0, max_matches_per_file)
    raw_audits = [
        _scan_log_file(ws, path, role="raw", marker_specs=marker_specs, max_matches=max_matches)
        for path in (raw_log_files or [])
    ]
    orientation_audits = [
        _scan_log_file(ws, path, role="orientation", marker_specs=marker_specs, max_matches=max_matches)
        for path in (orientation_log_files or [])
    ]
    total_raw = _total_counts(raw_audits, marker_specs)
    total_orientation = _total_counts(orientation_audits, marker_specs)
    status = _status(marker_specs, raw_audits, total_raw)

    return {
        "kind": "legacy_runtime_log_marker_audit",
        "workspace": str(ws.base),
        "migration_dir": str(migration_dir),
        "topic": str(topic),
        "truth_source": "raw_runtime_logs",
        "marker_match_mode": "literal_substring_case_sensitive",
        "marker_specs": marker_specs,
        "raw_log_files": raw_audits,
        "orientation_log_files": orientation_audits,
        "total_raw_matches_by_marker": total_raw,
        "total_orientation_matches_by_marker": total_orientation,
        "status": status,
        "semantic_lossless_proven": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "next_actions": _next_actions(status),
    }


def _marker_specs(markers: Iterable[str], expected_min_count: int) -> list[dict[str, Any]]:
    if not isinstance(expected_min_count, int) or expected_min_count < 1:
        raise ValueError("expected_min_count must be a positive integer")
    unique_markers: list[str] = []
    seen: set[str] = set()
    for marker in markers:
        text = str(marker).strip()
        if text and text not in seen:
            unique_markers.append(text)
            seen.add(text)
    if not unique_markers:
        raise ValueError("at least one non-empty marker is required")
    return [{"marker": marker, "expected_min_count": expected_min_count} for marker in unique_markers]


def _scan_log_file(
    ws: Any,
    path: str | Path,
    *,
    role: str,
    marker_specs: list[dict[str, Any]],
    max_matches: int,
) -> dict[str, Any]:
    provided = str(path)
    resolved = _resolve_path(ws, path)
    counts = {spec["marker"]: 0 for spec in marker_specs}
    audit: dict[str, Any] = {
        "path": str(resolved),
        "provided_path": provided,
        "log_role": role,
        "exists": resolved.is_file(),
        "line_count": 0,
        "match_counts_by_marker": counts,
        "matched_lines": [],
        "truncated_matches": False,
        "read_error": "",
    }
    if not resolved.is_file():
        return audit
    try:
        lines = resolved.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        audit["read_error"] = str(exc)
        return audit

    audit["line_count"] = len(lines)
    matched_lines: list[dict[str, Any]] = []
    truncated = False
    for line_number, line in enumerate(lines, start=1):
        for spec in marker_specs:
            marker = spec["marker"]
            occurrences = line.count(marker)
            if occurrences <= 0:
                continue
            counts[marker] += occurrences
            if len(matched_lines) < max_matches:
                matched_lines.append(
                    {
                        "marker": marker,
                        "line_number": line_number,
                        "text": _snippet(line),
                    }
                )
            else:
                truncated = True
    audit["matched_lines"] = matched_lines
    audit["truncated_matches"] = truncated
    return audit


def _resolve_path(ws: Any, path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return Path(ws.base) / candidate


def _total_counts(log_audits: list[dict[str, Any]], marker_specs: list[dict[str, Any]]) -> dict[str, int]:
    totals = {spec["marker"]: 0 for spec in marker_specs}
    for audit in log_audits:
        counts = audit.get("match_counts_by_marker", {})
        if isinstance(counts, dict):
            for marker in totals:
                value = counts.get(marker, 0)
                if isinstance(value, int):
                    totals[marker] += value
    return totals


def _status(
    marker_specs: list[dict[str, Any]],
    raw_audits: list[dict[str, Any]],
    total_raw: dict[str, int],
) -> str:
    if not raw_audits or any(not audit.get("exists") or audit.get("read_error") for audit in raw_audits):
        return "missing_raw_logs"
    missing_markers = [
        spec["marker"]
        for spec in marker_specs
        if total_raw.get(spec["marker"], 0) < spec["expected_min_count"]
    ]
    if missing_markers:
        return "incomplete"
    return "satisfied"


def _next_actions(status: str) -> list[str]:
    if status == "satisfied":
        return [
            "record_validation_result_with_raw_log_marker_audit_ref",
            "decide_human_checkpoint_before_any_claim_trust_promotion",
        ]
    if status == "missing_raw_logs":
        return ["provide_raw_runtime_logs", "rerun_runtime_log_marker_audit"]
    return [
        "inspect_raw_runtime_logs_for_missing_markers",
        "record_inconclusive_semantic_review_if_marker_gap_remains",
    ]


def _snippet(line: str) -> str:
    text = " ".join(line.strip().split())
    if len(text) <= MAX_SNIPPET_CHARS:
        return text
    return f"{text[:MAX_SNIPPET_CHARS - 3]}..."
