"""Pure summary and rendering helpers for the bounded context compiler."""

from __future__ import annotations

import re
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

from brain.v5.research_retrieval import RetrievalResult


DEFAULT_CONTEXT_FAMILIES = (
    "artifacts",
    "artifact_blob_receipts",
    "checkpoint_application_receipts",
    "checkpoints",
    "claim_statuses",
    "claims",
    "code_states",
    "code_patch_manifests",
    "derivation_chains",
    "derivation_reviews",
    "derivation_steps",
    "evidence",
    "execution_baselines",
    "execution_environments",
    "exploratory_records",
    "object_relations",
    "monitor_snapshots",
    "physics_objects",
    "proof_obligations",
    "quiet_checkpoints",
    "reference_locations",
    "research_run_events",
    "research_runs",
    "routes",
    "sensemaking_reports",
    "scope_revalidation_decisions",
    "source_assets",
    "tool_recipes",
    "tool_runs",
    "validation_contracts",
    "validation_results",
)


_TOKEN_RE = re.compile(
    r"[A-Za-z0-9_]+(?:[.+-][A-Za-z0-9_]+)*|[\u3400-\u4dbf\u4e00-\u9fff]|[^\s]"
)


def estimate_context_tokens(text: str) -> int:
    """Return a deterministic conservative token estimate for mixed physics text."""

    return len(_TOKEN_RE.findall(str(text or "")))


def record_mapping(record: Any) -> dict[str, Any]:
    if is_dataclass(record):
        return asdict(record)
    if isinstance(record, Mapping):
        return dict(record)
    raise TypeError(f"unsupported exact record type: {type(record).__name__}")


def typed_ref(kind: str, record_id: Any) -> str:
    text = str(record_id or "").strip()
    return f"{kind}:{text}" if text else ""


def unique_refs(refs: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(ref for ref in refs if ref and ":" in ref))


def objective(topic_id: str, topic_item: Any, request: Any) -> dict[str, Any]:
    record = topic_item.record if topic_item is not None else {}
    title = str(record.get("title") or topic_id)
    return {
        "objective_id": f"objective-{topic_id}",
        "title": title,
        "requested_focus": request.objective_text or request.user_goal,
        "source_ref": f"topic:{topic_id}",
        "orientation_only": True,
    }


def boundary(claim_item: Any) -> dict[str, Any]:
    if claim_item is None:
        return empty_boundary()
    record = claim_item.record
    return {
        "claim_id": str(record.get("claim_id") or record.get("record_id") or ""),
        "statement": str(record.get("statement") or record.get("title") or ""),
        "confidence_state": str(record.get("confidence_state") or "unknown"),
        "active_uncertainty": str(record.get("active_uncertainty") or ""),
        "scope": str(record.get("scope") or ""),
        "source_ref": claim_item.record_ref,
        "requires_exact_expansion": True,
    }


def empty_boundary() -> dict[str, Any]:
    return {
        "claim_id": "",
        "statement": "",
        "confidence_state": "unknown",
        "active_uncertainty": "active claim is not available in the current result page",
        "source_ref": "",
        "requires_exact_expansion": True,
    }


def candidate_summary(
    item: Any,
    *,
    retrieval_rank: int,
    scope_lane: str = "primary",
    requires_target_revalidation: bool = False,
) -> dict[str, Any]:
    record = item.record
    summary_fields = record.get("summary_fields")
    selected = dict(summary_fields) if isinstance(summary_fields, Mapping) else {}
    if item.family == "claims":
        status_value = (
            record.get("confidence_state")
            or selected.get("confidence_state")
            or selected.get("claim_status")
            or record.get("status")
            or record.get("lifecycle_status")
        )
    else:
        status_value = (
            record.get("status")
            or record.get("lifecycle_status")
            or selected.get("evidence_status")
            or selected.get("claim_status")
            or selected.get("validation_status")
        )
    return {
        "record_ref": item.record_ref,
        "family": item.family,
        "claim_id": str(record.get("claim_id") or ""),
        "title": str(record.get("title") or record.get("statement") or ""),
        "status": str(status_value or "unknown"),
        "summary_fields": selected,
        "typed_materialization_status": str(record.get("typed_materialization_status") or ""),
        "retrieval_rank": retrieval_rank,
        "retrieval_score": item.total_score,
        "exact_score": item.exact_score,
        "lexical_score": item.lexical_score,
        "process_family": item.family
        in {
            "artifacts",
            "artifact_blob_receipts",
            "checkpoint_application_receipts",
            "checkpoints",
            "code_patch_manifests",
            "code_states",
            "derivation_chains",
            "derivation_reviews",
            "derivation_steps",
            "evidence",
            "execution_baselines",
            "execution_environments",
            "monitor_snapshots",
            "quiet_checkpoints",
            "research_run_events",
            "research_runs",
            "routes",
            "scope_revalidation_decisions",
            "tool_runs",
            "validation_results",
        },
        "scope_lane": scope_lane,
        "requires_target_revalidation": requires_target_revalidation,
        "requires_exact_expansion": True,
        "orientation_only": True,
    }


def read_errors(result: RetrievalResult) -> tuple[str, ...]:
    errors: list[str] = list(result.coverage.read_errors)
    if result.coverage.malformed_count:
        errors.append(f"malformed_records_in_scope:{result.coverage.malformed_count}")
    return tuple(dict.fromkeys(errors))


def context_lines(
    *,
    request: Any,
    topic_id: str,
    current_objective: Mapping[str, Any],
    current_boundary: Mapping[str, Any],
    candidate_summaries: tuple[dict[str, Any], ...],
    coverage: Mapping[str, Any],
    index_status: str,
    read_errors: tuple[str, ...],
    not_found_refs: tuple[str, ...],
    not_checked_families: tuple[str, ...],
    not_shown_count: int,
    not_shown_reason: tuple[str, ...],
    record_refs: tuple[str, ...],
    scope: Mapping[str, Any] | None = None,
) -> list[str]:
    lines = [
        "AITP bounded research context.",
        f"Disclosure: {request.disclosure_level}",
        f"Session: {request.session_id} | Topic: {topic_id}",
        (
            "Coverage: "
            f"index={index_status}; exhaustive={str(bool(coverage.get('exhaustive'))).lower()}; "
            f"can_claim_no_result={str(bool(coverage.get('can_claim_no_result'))).lower()}."
        ),
        "Boundary: orientation-only; exact expansion is required before evidence, validation, or trust conclusions.",
        f"Objective: {excerpt(current_objective.get('title'), 180)}",
    ]
    requested = request.objective_text or request.user_goal
    if requested:
        lines.append(f"Requested focus: {excerpt(requested, 220)}")
    if current_boundary.get("claim_id"):
        lines.extend(
            [
                f"Active claim: {current_boundary.get('claim_id')} - {excerpt(current_boundary.get('statement'), 240)}",
                f"Current uncertainty: {excerpt(current_boundary.get('active_uncertainty'), 220)}",
            ]
        )
    else:
        lines.append("Active claim: unavailable in bounded result; expand the session and claim refs.")
    if scope:
        lines.append(
            "Scope: "
            f"primary={len(scope.get('primary_refs') or [])}; "
            f"supporting={len(scope.get('supporting_refs') or [])}; "
            f"excluded={len(scope.get('excluded_refs') or [])}; "
            f"unresolved={len(scope.get('unresolved_refs') or [])}."
        )
    if read_errors:
        lines.append(f"Read diagnostics: {'; '.join(read_errors)}")
    if not_found_refs:
        lines.append(f"Not-found exact refs: {', '.join(not_found_refs)}")
    if not_checked_families:
        lines.append(f"Not-checked families: {', '.join(not_checked_families)}")
    lines.append(
        "Candidate selection: "
        f"shown={len(candidate_summaries)}; not_shown={not_shown_count}; "
        f"reason={'+'.join(not_shown_reason) or 'none'}."
    )
    if candidate_summaries:
        lines.append("Candidate records:")
        for candidate in candidate_summaries:
            label = candidate.get("title") or candidate.get("status") or candidate.get("family")
            lines.append(f"- {candidate['record_ref']}: {excerpt(label, 180)}")
    if record_refs:
        lines.append("Expansion refs: " + ", ".join(record_refs[:12]))
    lines.append("Default context contains summaries and handles only, never full record bodies.")
    return lines


def bounded_markdown(lines: list[str], *, max_bytes: int, max_tokens: int) -> tuple[str, bool]:
    accepted: list[str] = []
    truncated = False
    for line in lines:
        candidate = "\n".join([*accepted, line]) + "\n"
        if len(candidate.encode("utf-8")) > max_bytes or estimate_context_tokens(candidate) > max_tokens:
            truncated = True
            break
        accepted.append(line)
    if not accepted:
        raise ValueError("context budget cannot hold the mandatory coverage header")
    return "\n".join(accepted) + "\n", truncated


def excerpt(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def index_generation(result: RetrievalResult) -> int:
    return int(result.index_generation)
