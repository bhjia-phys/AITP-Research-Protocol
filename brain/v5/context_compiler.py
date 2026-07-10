"""Bounded research context compiled from one indexed retrieval plan."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Callable, Mapping

from brain.v5.indexed_topic_snapshot import (
    IndexedRecord,
    IndexedTopicSnapshot,
    load_indexed_topic_snapshot,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import build_query_index
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.research_retrieval import ResearchQuery, RetrievalResult, query_records


_DEFAULT_CONTEXT_FAMILIES = (
    "artifacts",
    "checkpoints",
    "claim_statuses",
    "claims",
    "code_states",
    "evidence",
    "object_relations",
    "physics_objects",
    "proof_obligations",
    "quiet_checkpoints",
    "reference_locations",
    "research_run_events",
    "research_runs",
    "routes",
    "sensemaking_reports",
    "source_assets",
    "tool_recipes",
    "tool_runs",
    "validation_contracts",
    "validation_results",
)
_PROCESS_FAMILIES = frozenset(
    {
        "artifacts",
        "checkpoints",
        "code_states",
        "evidence",
        "quiet_checkpoints",
        "research_run_events",
        "research_runs",
        "routes",
        "tool_runs",
        "validation_results",
    }
)
_TOKEN_RE = re.compile(
    r"[A-Za-z0-9_]+(?:[.+-][A-Za-z0-9_]+)*|[\u3400-\u4dbf\u4e00-\u9fff]|[^\s]"
)


class ContextCompilationError(RuntimeError):
    """Raised when the requested session cannot anchor a bounded context."""


@dataclass(frozen=True)
class ContextRequest:
    session_id: str
    objective_text: str = ""
    user_goal: str = ""
    topic_id: str = ""
    exact_refs: tuple[str, ...] = ()
    families: tuple[str, ...] = _DEFAULT_CONTEXT_FAMILIES
    max_tokens: int = 1200
    max_bytes: int = 6000
    record_limit: int = 80
    candidate_limit: int = 12

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError("session_id must be non-empty")
        if self.max_tokens < 64:
            raise ValueError("max_tokens must be at least 64")
        if self.max_bytes < 384:
            raise ValueError("max_bytes must be at least 384")
        if not 1 <= self.record_limit <= 200:
            raise ValueError("record_limit must be between 1 and 200")
        if not 1 <= self.candidate_limit <= 40:
            raise ValueError("candidate_limit must be between 1 and 40")


@dataclass(frozen=True)
class ContextBundle:
    session_id: str
    topic_id: str
    current_objective: dict[str, Any]
    current_boundary: dict[str, Any]
    recent_process_refs: tuple[str, ...]
    candidate_summaries: tuple[dict[str, Any], ...]
    record_refs: tuple[str, ...]
    expansion: dict[str, Any]
    coverage: dict[str, Any]
    read_errors: tuple[str, ...]
    index_status: str
    source_index_generation: int
    total_candidates: int
    truncated: bool
    can_claim_no_prior_result: bool
    requires_exact_expansion_before_trust_conclusions: bool
    markdown: str
    byte_count: int
    estimated_tokens: int
    max_bytes: int
    max_tokens: int
    orientation_only: bool = True
    summary_inputs_trusted: bool = False
    can_update_kernel_state: bool = False
    can_update_claim_trust: bool = False


QueryFunction = Callable[[WorkspacePaths, ResearchQuery], RetrievalResult]


def compile_research_context(
    ws: WorkspacePaths,
    request: ContextRequest,
    *,
    query_fn: QueryFunction = query_records,
    repository: RecordRepository | None = None,
) -> ContextBundle:
    """Compile one trust-neutral context from one exact read and one query plan."""

    repo = repository or RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="migration",
            actor_id="context-compiler-read",
            host="context-compiler",
        ),
    )
    session_result = repo.read(f"session:{request.session_id}")
    if session_result.status != "found" or session_result.record is None:
        detail = session_result.issue.message if session_result.issue else session_result.status
        raise ContextCompilationError(
            f"cannot compile context for session {request.session_id!r}: {detail}"
        )
    session = _record_mapping(session_result.record)
    topic_id = request.topic_id.strip() or str(session.get("topic_id") or "")
    if not topic_id:
        raise ContextCompilationError("session does not identify a topic")

    exact_refs = _unique_refs(
        (
            f"session:{request.session_id}",
            f"topic:{topic_id}",
            _typed_ref("claim", session.get("active_claim")),
            _typed_ref("research_route", session.get("active_route")),
            *request.exact_refs,
        )
    )
    query_text = " ".join(
        part.strip() for part in (request.objective_text, request.user_goal) if part.strip()
    )
    if not (ws.root / "indexes" / "manifest.json").exists():
        build_query_index(ws)
    result = query_fn(
        ws,
        ResearchQuery(
            text=query_text,
            exact_refs=exact_refs,
            topic_ids=(topic_id,),
            families=tuple(dict.fromkeys(request.families)),
            limit=request.record_limit,
        ),
    )

    item_by_ref = {item.record_ref: item for item in result.items}
    topic_item = item_by_ref.get(f"topic:{topic_id}")
    active_claim_ref = _typed_ref("claim", session.get("active_claim"))
    claim_item = item_by_ref.get(active_claim_ref) if active_claim_ref else None
    current_objective = _objective(topic_id, topic_item, request)
    current_boundary = _boundary(claim_item)
    record_refs = tuple(item.record_ref for item in result.items)
    process_refs = tuple(
        item.record_ref for item in result.items if item.family in _PROCESS_FAMILIES
    )[:12]
    all_candidate_summaries = [
        _candidate_summary(item.record_ref, item.family, item.record)
        for item in result.items
        if item.record_ref not in {f"session:{request.session_id}", f"topic:{topic_id}"}
    ]
    all_candidate_summaries.sort(key=_candidate_priority)
    candidate_summaries = tuple(all_candidate_summaries[: request.candidate_limit])
    read_errors = _read_errors(result)
    coverage = asdict(result.coverage)
    expansion = {
        "surface": "record_refs",
        "refs": list(record_refs),
        "page_size": min(20, max(1, len(record_refs))),
        "next_offset": result.next_offset,
        "requires_explicit_call": True,
        "full_record_bodies_in_default_context": False,
    }
    lines = _context_lines(
        request=request,
        topic_id=topic_id,
        current_objective=current_objective,
        current_boundary=current_boundary,
        candidate_summaries=candidate_summaries,
        coverage=coverage,
        index_status=result.index_status,
        read_errors=read_errors,
        record_refs=record_refs,
    )
    markdown, budget_truncated = _bounded_markdown(
        lines,
        max_bytes=request.max_bytes,
        max_tokens=request.max_tokens,
    )
    truncated = bool(result.truncated or budget_truncated)
    can_claim_no_prior_result = bool(
        result.total_count == 0
        and result.coverage.can_claim_no_result
        and not truncated
        and not read_errors
    )
    return ContextBundle(
        session_id=request.session_id,
        topic_id=topic_id,
        current_objective=current_objective,
        current_boundary=current_boundary,
        recent_process_refs=process_refs,
        candidate_summaries=candidate_summaries,
        record_refs=record_refs,
        expansion=expansion,
        coverage=coverage,
        read_errors=read_errors,
        index_status=result.index_status,
        source_index_generation=_index_generation(result),
        total_candidates=result.total_count,
        truncated=truncated,
        can_claim_no_prior_result=can_claim_no_prior_result,
        requires_exact_expansion_before_trust_conclusions=True,
        markdown=markdown,
        byte_count=len(markdown.encode("utf-8")),
        estimated_tokens=estimate_context_tokens(markdown),
        max_bytes=request.max_bytes,
        max_tokens=request.max_tokens,
    )


def context_bundle_payload(bundle: ContextBundle) -> dict[str, Any]:
    """Return the stable JSON-compatible representation used by host surfaces."""

    return asdict(bundle)


def estimate_context_tokens(text: str) -> int:
    """Return a deterministic conservative token estimate for mixed physics text."""

    return len(_TOKEN_RE.findall(str(text or "")))


def _record_mapping(record: Any) -> dict[str, Any]:
    if is_dataclass(record):
        return asdict(record)
    if isinstance(record, Mapping):
        return dict(record)
    raise ContextCompilationError(f"unsupported exact record type: {type(record).__name__}")


def _typed_ref(kind: str, record_id: Any) -> str:
    text = str(record_id or "").strip()
    return f"{kind}:{text}" if text else ""


def _unique_refs(refs: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(ref for ref in refs if ref and ":" in ref))


def _objective(
    topic_id: str,
    topic_item: Any,
    request: ContextRequest,
) -> dict[str, Any]:
    record = topic_item.record if topic_item is not None else {}
    title = str(record.get("title") or topic_id)
    return {
        "objective_id": f"objective-{topic_id}",
        "title": title,
        "requested_focus": request.objective_text or request.user_goal,
        "source_ref": f"topic:{topic_id}",
        "orientation_only": True,
    }


def _boundary(claim_item: Any) -> dict[str, Any]:
    if claim_item is None:
        return {
            "claim_id": "",
            "statement": "",
            "confidence_state": "unknown",
            "active_uncertainty": "active claim is not available in the current result page",
            "source_ref": "",
            "requires_exact_expansion": True,
        }
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


def _candidate_summary(record_ref: str, family: str, record: Mapping[str, Any]) -> dict[str, Any]:
    summary_fields = record.get("summary_fields")
    selected = dict(summary_fields) if isinstance(summary_fields, Mapping) else {}
    status = str(
        record.get("status")
        or record.get("lifecycle_status")
        or selected.get("evidence_status")
        or selected.get("claim_status")
        or selected.get("validation_status")
        or ""
    )
    return {
        "record_ref": record_ref,
        "family": family,
        "claim_id": str(record.get("claim_id") or ""),
        "title": str(record.get("title") or record.get("statement") or ""),
        "status": status,
        "summary_fields": selected,
        "typed_materialization_status": str(record.get("typed_materialization_status") or ""),
        "requires_exact_expansion": True,
        "orientation_only": True,
    }


def _candidate_priority(candidate: Mapping[str, Any]) -> tuple[int, str]:
    selected = candidate.get("summary_fields")
    fields = selected if isinstance(selected, Mapping) else {}
    status = str(candidate.get("status") or fields.get("evidence_status") or "").lower()
    text = json.dumps(fields, ensure_ascii=False, sort_keys=True).lower()
    failed = bool(
        status in {"failed", "fail", "negative", "invalid", "contradicted", "superseded"}
        or fields.get("superseded_by")
        or any(marker in text for marker in ("does not test", "runtime failure", "wrong route"))
    )
    if failed:
        rank = 0
    elif candidate.get("family") == "claims":
        rank = 1
    elif candidate.get("family") in _PROCESS_FAMILIES:
        rank = 2
    else:
        rank = 3
    return rank, str(candidate.get("record_ref") or "")


def _read_errors(result: RetrievalResult) -> tuple[str, ...]:
    errors = [f"unresolved_exact_ref:{ref}" for ref in result.excluded_candidates]
    if result.coverage.malformed_count:
        errors.append(f"malformed_records_in_scope:{result.coverage.malformed_count}")
    return tuple(errors)


def _context_lines(
    *,
    request: ContextRequest,
    topic_id: str,
    current_objective: Mapping[str, Any],
    current_boundary: Mapping[str, Any],
    candidate_summaries: tuple[dict[str, Any], ...],
    coverage: Mapping[str, Any],
    index_status: str,
    read_errors: tuple[str, ...],
    record_refs: tuple[str, ...],
) -> list[str]:
    lines = [
        "AITP bounded research context.",
        f"Session: {request.session_id} | Topic: {topic_id}",
        (
            "Coverage: "
            f"index={index_status}; exhaustive={str(bool(coverage.get('exhaustive'))).lower()}; "
            f"can_claim_no_result={str(bool(coverage.get('can_claim_no_result'))).lower()}."
        ),
        "Boundary: orientation-only; exact expansion is required before evidence, validation, or trust conclusions.",
        f"Objective: {_excerpt(current_objective.get('title'), 180)}",
    ]
    requested = request.objective_text or request.user_goal
    if requested:
        lines.append(f"Requested focus: {_excerpt(requested, 220)}")
    if current_boundary.get("claim_id"):
        lines.extend(
            [
                f"Active claim: {current_boundary.get('claim_id')} - {_excerpt(current_boundary.get('statement'), 240)}",
                f"Current uncertainty: {_excerpt(current_boundary.get('active_uncertainty'), 220)}",
            ]
        )
    else:
        lines.append("Active claim: unavailable in bounded result; expand the session and claim refs.")
    if read_errors:
        lines.append(f"Read diagnostics: {'; '.join(read_errors)}")
    if candidate_summaries:
        lines.append("Candidate records:")
        for candidate in candidate_summaries:
            label = candidate.get("title") or candidate.get("status") or candidate.get("family")
            lines.append(f"- {candidate['record_ref']}: {_excerpt(label, 180)}")
    if record_refs:
        lines.append("Expansion refs: " + ", ".join(record_refs[:12]))
    lines.append("Default context contains summaries and handles only, never full record bodies.")
    return lines


def _bounded_markdown(lines: list[str], *, max_bytes: int, max_tokens: int) -> tuple[str, bool]:
    accepted: list[str] = []
    truncated = False
    for line in lines:
        candidate = "\n".join([*accepted, line]) + "\n"
        if len(candidate.encode("utf-8")) > max_bytes or estimate_context_tokens(candidate) > max_tokens:
            truncated = True
            break
        accepted.append(line)
    if not accepted:
        raise ContextCompilationError("context budget cannot hold the mandatory coverage header")
    return "\n".join(accepted) + "\n", truncated


def _excerpt(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _index_generation(result: RetrievalResult) -> int:
    return int(result.index_generation)
