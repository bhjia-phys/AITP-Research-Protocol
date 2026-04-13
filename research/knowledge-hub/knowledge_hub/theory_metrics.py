from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def _now() -> datetime:
    return datetime.now().astimezone()


def _now_iso() -> str:
    return _now().isoformat(timespec="seconds")


def _slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "aitp"


def _dedupe_strings(values: list[str] | None) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        normalized = str(value or "").strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return deduped


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def theory_metrics_paths(service: Any, *, topic_slug: str | None = None) -> dict[str, Path]:
    runtime_root = service.kernel_root / "runtime"
    global_root = runtime_root / "theory_metrics"
    if topic_slug:
        topic_root = service._runtime_root(topic_slug)
        return {
            "ledger": topic_root / "theory_operations.jsonl",
            "analysis_json": topic_root / "theory_metrics.analysis.json",
            "analysis_note": topic_root / "theory_metrics.analysis.md",
            "global_ledger": global_root / "theory_operations.jsonl",
        }
    return {
        "ledger": global_root / "theory_operations.jsonl",
        "analysis_json": global_root / "analysis.latest.json",
        "analysis_note": global_root / "analysis.latest.md",
    }


def _blocked_status(status: str) -> bool:
    return str(status or "").strip().lower() in {"blocked", "fail", "failed", "needs_revision", "not_ready", "error", "rejected"}


def _confidence_score(*, evidence_count: int, distinct_topic_count: int) -> float:
    return round(min(0.98, 0.35 + 0.12 * evidence_count + 0.08 * distinct_topic_count), 2)


def _make_event_row(
    *,
    topic_slug: str,
    run_id: str | None,
    operation_kind: str,
    status: str,
    updated_by: str,
    candidate_id: str | None = None,
    candidate_type: str | None = None,
    phase: str | None = None,
    blocker_tags: list[str] | None = None,
    source_paths: list[str] | None = None,
    summary: str | None = None,
    metric_values: dict[str, Any] | None = None,
) -> dict[str, Any]:
    recorded_at = _now_iso()
    identity = candidate_id or run_id or topic_slug
    event_id = (
        f"theory-metric:{_slugify(topic_slug)}:{_slugify(operation_kind)}:{_slugify(identity)}:"
        f"{recorded_at.replace(':', '').replace('-', '')}"
    )
    return {
        "schema_version": 1,
        "event_id": event_id,
        "topic_slug": topic_slug,
        "run_id": str(run_id or "").strip(),
        "operation_kind": operation_kind,
        "status": str(status or "").strip() or "unknown",
        "candidate_id": str(candidate_id or "").strip(),
        "candidate_type": str(candidate_type or "").strip(),
        "phase": str(phase or "").strip(),
        "summary": str(summary or "").strip(),
        "blocker_tags": _dedupe_strings(blocker_tags),
        "source_paths": _dedupe_strings(source_paths),
        "metric_values": dict(metric_values or {}),
        "recorded_at": recorded_at,
        "recorded_by": updated_by,
    }


def _maybe_build_retry_row(service: Any, *, row: dict[str, Any], topic_rows_before_append: list[dict[str, Any]]) -> dict[str, Any] | None:
    if row["operation_kind"] not in {"theory_coverage_audit", "formal_theory_audit"}:
        return None
    if not row.get("candidate_id") or not _blocked_status(str(row.get("status") or "")):
        return None
    prior_attempts = [
        event
        for event in topic_rows_before_append
        if str(event.get("candidate_id") or "") == row["candidate_id"]
        and str(event.get("operation_kind") or "") == row["operation_kind"]
    ]
    attempt_index = len(prior_attempts) + 1
    if attempt_index <= 1:
        return None
    return _make_event_row(
        topic_slug=row["topic_slug"],
        run_id=row.get("run_id"),
        operation_kind="derivation_retry",
        status="active",
        updated_by=str(row.get("recorded_by") or "aitp-cli"),
        candidate_id=row.get("candidate_id"),
        candidate_type=row.get("candidate_type"),
        blocker_tags=_dedupe_strings(list(row.get("blocker_tags") or []) + [f"retry_source:{row['operation_kind']}"]),
        source_paths=list(row.get("source_paths") or []),
        summary=f"Repeated blocked theory operation for {row['candidate_id']} via {row['operation_kind']} (attempt {attempt_index}).",
        metric_values={
            "attempt_index": attempt_index,
            "source_operation_kind": row["operation_kind"],
        },
    )


def _bucket_events(rows: list[dict[str, Any]], predicate: Any) -> tuple[int, int, list[str]]:
    selected = [row for row in rows if predicate(row)]
    evidence_count = len(selected)
    distinct_topic_count = len({str(row.get("topic_slug") or "") for row in selected if str(row.get("topic_slug") or "")})
    examples = [str(row.get("event_id") or "") for row in selected[:5] if str(row.get("event_id") or "")]
    return evidence_count, distinct_topic_count, examples


def _proposal(
    *,
    proposal_kind: str,
    summary: str,
    recommended_action: str,
    evidence_count: int,
    distinct_topic_count: int,
    example_event_ids: list[str],
) -> dict[str, Any]:
    return {
        "proposal_id": f"theory-metrics-proposal:{proposal_kind}",
        "proposal_kind": proposal_kind,
        "summary": summary,
        "recommended_action": recommended_action,
        "confidence_score": _confidence_score(
            evidence_count=evidence_count,
            distinct_topic_count=distinct_topic_count,
        ),
        "evidence_count": evidence_count,
        "distinct_topic_count": distinct_topic_count,
        "example_event_ids": example_event_ids,
    }


def theory_metrics_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Theory metrics analysis",
        "",
        f"- Scope: `{payload.get('scope') or '(missing)'}`",
        f"- Topic slug: `{payload.get('topic_slug') or '(global)'}`",
        f"- Updated at: `{payload.get('updated_at') or '(missing)'}`",
        f"- Updated by: `{payload.get('updated_by') or '(missing)'}`",
        f"- Operation count: `{payload.get('operation_count') or 0}`",
        "",
        "## Operation counts",
        "",
    ]
    for key, value in sorted((payload.get("operation_counts_by_kind") or {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Status counts", ""])
    for key, value in sorted((payload.get("status_counts") or {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Proposals", ""])
    proposals = payload.get("proposals") or []
    if not proposals:
        lines.append("- `(none)`")
    for row in proposals:
        lines.extend(
            [
                f"- `{row.get('proposal_kind') or '(missing)'}` confidence=`{row.get('confidence_score')}` evidence=`{row.get('evidence_count')}`",
                f"  summary: {row.get('summary') or '(missing)'}",
                f"  action: {row.get('recommended_action') or '(missing)'}",
            ]
        )
    return "\n".join(lines) + "\n"


def candidate_metric_context(
    service: Any,
    *,
    topic_slug: str,
    run_id: str | None,
    candidate_id: str | None,
) -> tuple[str | None, str]:
    resolved_run_id = service._resolve_run_id(topic_slug, run_id) if topic_slug else None
    if not (topic_slug and resolved_run_id and str(candidate_id or "").strip()):
        return resolved_run_id, ""
    try:
        candidate = service._load_candidate(topic_slug, resolved_run_id, str(candidate_id))
    except FileNotFoundError:
        return resolved_run_id, ""
    return resolved_run_id, str(candidate.get("candidate_type") or "")


def record_conformance_metric(
    service: Any,
    *,
    topic_slug: str,
    phase: str,
    updated_by: str,
    state: dict[str, Any] | None,
    report_path: Path,
) -> None:
    preflight = (state or {}).get("mechanical_completion_preflight") or {}
    failed_checks = [
        str(check.get("code") or "").strip()
        for check in preflight.get("checks") or []
        if str(check.get("status") or "").strip() == "fail" and str(check.get("code") or "").strip()
    ]
    blocker_tags: list[str] = []
    if str((state or {}).get("overall_status") or "") != "pass":
        blocker_tags.append("conformance_not_passed")
    if str(preflight.get("status") or "") != "pass":
        blocker_tags.append("mechanical_preflight_blocked")
    blocker_tags.extend(failed_checks)
    record_theory_operation_metric(
        service,
        topic_slug=topic_slug,
        run_id=service._resolve_run_id(topic_slug, None),
        operation_kind="conformance_audit",
        status=str((state or {}).get("overall_status") or "unknown"),
        updated_by=updated_by,
        phase=phase,
        blocker_tags=blocker_tags,
        source_paths=[
            service._relativize(service._runtime_root(topic_slug) / "conformance_state.json"),
            service._relativize(report_path),
        ],
        summary=f"Conformance audit {str((state or {}).get('overall_status') or 'unknown')} for topic `{topic_slug}` during `{phase}`.",
        metric_values={
            "llm_audit_eligible": bool(preflight.get("llm_audit_eligible")),
            "failed_check_count": len(failed_checks),
        },
    )


def record_coverage_metric(
    service: Any,
    *,
    topic_slug: str,
    run_id: str | None,
    candidate_id: str,
    candidate_type: str,
    updated_by: str,
    result: dict[str, Any],
) -> None:
    coverage_ledger = (result.get("artifacts") or {}).get("coverage_ledger") or {}
    blocker_tags: list[str] = []
    if str(result.get("coverage_status") or "") != "pass":
        blocker_tags.append("coverage_not_passed")
    if int(coverage_ledger.get("missing_anchor_count") or 0) > 0:
        blocker_tags.append("missing_source_anchors")
    if int(coverage_ledger.get("skeptic_major_gap_count") or 0) > 0:
        blocker_tags.append("skeptic_major_gap_present")
    regression_gate_status = str(result.get("regression_gate_status") or "").strip()
    if regression_gate_status and regression_gate_status != "pass":
        blocker_tags.append(f"regression_gate_{regression_gate_status}")
    if str(result.get("topic_completion_status") or "") not in {"promotion-ready", "promoted"}:
        blocker_tags.append("topic_completion_not_ready")
    record_theory_operation_metric(
        service,
        topic_slug=topic_slug,
        run_id=run_id,
        operation_kind="theory_coverage_audit",
        status=str(result.get("coverage_status") or "unknown"),
        updated_by=updated_by,
        candidate_id=candidate_id or None,
        candidate_type=candidate_type or None,
        blocker_tags=blocker_tags,
        source_paths=list((result.get("paths") or {}).values()),
        summary=f"Coverage audit {result.get('coverage_status') or 'unknown'} for {candidate_id or 'candidate'}.",
        metric_values={
            "coverage_score": result.get("coverage_score"),
            "missing_anchor_count": coverage_ledger.get("missing_anchor_count"),
            "skeptic_major_gap_count": coverage_ledger.get("skeptic_major_gap_count"),
            "critical_unit_recall": coverage_ledger.get("critical_unit_recall"),
            "regression_gate_status": regression_gate_status,
        },
    )


def record_formal_theory_metric(
    service: Any,
    *,
    topic_slug: str,
    run_id: str | None,
    candidate_id: str,
    candidate_type: str,
    updated_by: str,
    result: dict[str, Any],
) -> None:
    formal_review = (result.get("artifacts") or {}).get("formal_theory_review") or {}
    blocker_tags = _dedupe_strings(list(formal_review.get("blocking_reasons") or []))
    if str(formal_review.get("prerequisite_closure_status") or "") != "closed":
        blocker_tags.append("prerequisite_closure_incomplete")
    if list(formal_review.get("formalization_blockers") or []):
        blocker_tags.append("formalization_blockers_present")
    if str(result.get("overall_status") or "") != "ready":
        blocker_tags.append("formal_theory_not_ready")
    record_theory_operation_metric(
        service,
        topic_slug=topic_slug,
        run_id=run_id,
        operation_kind="formal_theory_audit",
        status=str(result.get("overall_status") or "unknown"),
        updated_by=updated_by,
        candidate_id=candidate_id or None,
        candidate_type=candidate_type or None,
        blocker_tags=blocker_tags,
        source_paths=list((result.get("paths") or {}).values()),
        summary=f"Formal theory audit {result.get('overall_status') or 'unknown'} for {candidate_id or 'candidate'}.",
        metric_values={
            "prerequisite_closure_status": formal_review.get("prerequisite_closure_status"),
            "blocking_reason_count": len(list(formal_review.get("blocking_reasons") or [])),
            "formalization_blocker_count": len(list(formal_review.get("formalization_blockers") or [])),
        },
    )


def record_analytical_review_metric(
    service: Any,
    *,
    topic_slug: str,
    run_id: str | None,
    candidate_id: str | None,
    updated_by: str,
    result: dict[str, Any],
) -> None:
    record_theory_operation_metric(
        service,
        topic_slug=topic_slug,
        run_id=run_id,
        operation_kind="analytical_review_audit",
        status=str(result.get("overall_status") or "unknown"),
        updated_by=updated_by,
        candidate_id=str(candidate_id or "").strip() or None,
        blocker_tags=["analytical_review_not_ready"] if str(result.get("overall_status") or "") != "ready" else [],
        source_paths=list((result.get("paths") or {}).values()),
        summary=f"Analytical review {result.get('overall_status') or 'unknown'} for {str(candidate_id or '').strip() or 'candidate'}.",
    )


def record_topic_completion_metric(
    service: Any,
    *,
    topic_slug: str,
    run_id: str | None,
    updated_by: str,
    payload: dict[str, Any],
    json_path: Path,
    note_path: Path,
) -> None:
    blocked_checks = [
        str(row.get("check") or "").strip()
        for row in payload.get("completion_gate_checks") or []
        if str(row.get("status") or "").strip() != "pass" and str(row.get("check") or "").strip()
    ]
    blocker_tags: list[str] = []
    if str(payload.get("status") or "") not in {"promotion-ready", "promoted"}:
        blocker_tags.append("topic_completion_incomplete")
    blocker_tags.extend(f"completion_gate:{item}" for item in blocked_checks)
    record_theory_operation_metric(
        service,
        topic_slug=topic_slug,
        run_id=run_id,
        operation_kind="topic_completion_assessment",
        status=str(payload.get("status") or "unknown"),
        updated_by=updated_by,
        blocker_tags=blocker_tags,
        source_paths=[service._relativize(json_path), service._relativize(note_path)],
        summary=f"Topic completion assessed as {str(payload.get('status') or 'unknown')} for topic `{topic_slug}`.",
        metric_values={
            "completion_check_count": len(payload.get("completion_gate_checks") or []),
            "blocked_check_count": len(blocked_checks),
        },
    )


def record_promotion_gate_metric(
    service: Any,
    *,
    topic_slug: str,
    run_id: str | None,
    candidate_id: str,
    candidate_type: str | None,
    updated_by: str,
    operation_kind: str,
    status: str,
    blocker_tags: list[str] | None = None,
    summary: str | None = None,
    metric_values: dict[str, Any] | None = None,
) -> None:
    record_theory_operation_metric(
        service,
        topic_slug=topic_slug,
        run_id=run_id,
        operation_kind=operation_kind,
        status=status,
        updated_by=updated_by,
        candidate_id=candidate_id,
        candidate_type=candidate_type,
        blocker_tags=blocker_tags,
        source_paths=[
            service._relativize(service._promotion_gate_paths(topic_slug)["json"]),
            service._relativize(service._promotion_gate_paths(topic_slug)["note"]),
        ],
        summary=summary,
        metric_values=metric_values,
    )


def record_candidate_promotion_metric(
    service: Any,
    *,
    topic_slug: str,
    run_id: str | None,
    candidate_id: str,
    candidate_type: str | None,
    updated_by: str,
    operation_kind: str,
    status: str,
    result: dict[str, Any] | None = None,
    summary: str | None = None,
    blocker_tags: list[str] | None = None,
) -> None:
    source_paths = []
    for key, value in (result or {}).items():
        if key.endswith("_path") and isinstance(value, str):
            source_paths.append(value)
    record_theory_operation_metric(
        service,
        topic_slug=topic_slug,
        run_id=run_id,
        operation_kind=operation_kind,
        status=status,
        updated_by=updated_by,
        candidate_id=candidate_id,
        candidate_type=candidate_type,
        blocker_tags=blocker_tags,
        source_paths=source_paths,
        summary=summary,
    )


def analyze_theory_metrics(
    service: Any,
    *,
    topic_slug: str | None = None,
    updated_by: str = "aitp-cli",
) -> dict[str, Any]:
    paths = theory_metrics_paths(service, topic_slug=topic_slug)
    rows = _read_jsonl(paths["ledger"])
    operation_counts = Counter(str(row.get("operation_kind") or "unknown") for row in rows)
    status_counts = Counter(str(row.get("status") or "unknown") for row in rows)
    proposals: list[dict[str, Any]] = []

    prerequisite_count, prerequisite_topics, prerequisite_examples = _bucket_events(
        rows,
        lambda row: "prerequisite_closure_incomplete" in (row.get("blocker_tags") or []),
    )
    if prerequisite_count >= 2:
        proposals.append(
            _proposal(
                proposal_kind="strengthen_prerequisite_closure_guidance",
                summary="Prerequisite-closure debt recurs across formal-theory audits.",
                recommended_action="Surface prerequisite closure blockers earlier and keep prerequisite context pinned before theorem-facing review.",
                evidence_count=prerequisite_count,
                distinct_topic_count=prerequisite_topics,
                example_event_ids=prerequisite_examples,
            )
        )

    anchor_count, anchor_topics, anchor_examples = _bucket_events(
        rows,
        lambda row: "missing_source_anchors" in (row.get("blocker_tags") or []),
    )
    if anchor_count >= 2:
        proposals.append(
            _proposal(
                proposal_kind="recover_source_anchors_before_coverage",
                summary="Coverage audits repeatedly fail because source anchors stay unresolved.",
                recommended_action="Return to L0 source recovery before rerunning coverage audits and make anchor debt visible earlier in the route.",
                evidence_count=anchor_count,
                distinct_topic_count=anchor_topics,
                example_event_ids=anchor_examples,
            )
        )

    promotion_count, promotion_topics, promotion_examples = _bucket_events(
        rows,
        lambda row: str(row.get("operation_kind") or "") in {"promotion_reject", "candidate_promotion", "candidate_auto_promotion"}
        and _blocked_status(str(row.get("status") or "")),
    )
    if promotion_count >= 2:
        proposals.append(
            _proposal(
                proposal_kind="surface_promotion_blockers_earlier",
                summary="Promotion attempts keep ending in blocked or rejected states.",
                recommended_action="Expose promotion blockers and readiness debt earlier so promotion is not used as the first point of failure discovery.",
                evidence_count=promotion_count,
                distinct_topic_count=promotion_topics,
                example_event_ids=promotion_examples,
            )
        )

    retry_count, retry_topics, retry_examples = _bucket_events(
        rows,
        lambda row: str(row.get("operation_kind") or "") == "derivation_retry",
    )
    if retry_count >= 2:
        proposals.append(
            _proposal(
                proposal_kind="intervene_on_repeated_derivation_retries",
                summary="The same theorem-facing artifact is being retried repeatedly without route change.",
                recommended_action="Inject an explicit decomposition or strategy-change suggestion once retry counts rise instead of silently repeating the same approach.",
                evidence_count=retry_count,
                distinct_topic_count=retry_topics,
                example_event_ids=retry_examples,
            )
        )

    conformance_count, conformance_topics, conformance_examples = _bucket_events(
        rows,
        lambda row: "mechanical_preflight_blocked" in (row.get("blocker_tags") or []),
    )
    if conformance_count >= 2:
        proposals.append(
            _proposal(
                proposal_kind="surface_mechanical_preflight_debt_earlier",
                summary="Conformance checks repeatedly fail on mechanical preflight debt.",
                recommended_action="Surface baseline, gap, and pending-follow-up debt before the conformance audit is invoked.",
                evidence_count=conformance_count,
                distinct_topic_count=conformance_topics,
                example_event_ids=conformance_examples,
            )
        )

    payload = {
        "analysis_kind": "theory_metrics_analysis",
        "scope": "topic" if topic_slug else "global",
        "topic_slug": topic_slug or "",
        "updated_at": _now_iso(),
        "updated_by": updated_by,
        "operation_count": len(rows),
        "operation_counts_by_kind": dict(sorted(operation_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "proposals": proposals,
        "analysis_json_path": str(paths["analysis_json"]),
        "analysis_note_path": str(paths["analysis_note"]),
        "ledger_path": str(paths["ledger"]),
    }
    _write_json(paths["analysis_json"], payload)
    _write_text(paths["analysis_note"], theory_metrics_markdown(payload))
    return payload


def record_theory_operation_metric(
    service: Any,
    *,
    topic_slug: str,
    run_id: str | None,
    operation_kind: str,
    status: str,
    updated_by: str,
    candidate_id: str | None = None,
    candidate_type: str | None = None,
    phase: str | None = None,
    blocker_tags: list[str] | None = None,
    source_paths: list[str] | None = None,
    summary: str | None = None,
    metric_values: dict[str, Any] | None = None,
    refresh_analysis: bool = True,
) -> dict[str, Any]:
    global_paths = theory_metrics_paths(service, topic_slug=None)
    topic_paths = theory_metrics_paths(service, topic_slug=topic_slug)
    topic_rows_before_append = _read_jsonl(topic_paths["ledger"])
    row = _make_event_row(
        topic_slug=topic_slug,
        run_id=run_id,
        operation_kind=operation_kind,
        status=status,
        updated_by=updated_by,
        candidate_id=candidate_id,
        candidate_type=candidate_type,
        phase=phase,
        blocker_tags=blocker_tags,
        source_paths=source_paths,
        summary=summary,
        metric_values=metric_values,
    )
    _append_jsonl(global_paths["ledger"], row)
    _append_jsonl(topic_paths["ledger"], row)

    retry_row = _maybe_build_retry_row(service, row=row, topic_rows_before_append=topic_rows_before_append)
    if retry_row is not None:
        _append_jsonl(global_paths["ledger"], retry_row)
        _append_jsonl(topic_paths["ledger"], retry_row)

    if refresh_analysis:
        analyze_theory_metrics(service, updated_by=updated_by)
        analyze_theory_metrics(service, topic_slug=topic_slug, updated_by=updated_by)

    return {
        "event": row,
        "retry_event": retry_row,
        "global_ledger_path": str(global_paths["ledger"]),
        "topic_ledger_path": str(topic_paths["ledger"]),
    }
