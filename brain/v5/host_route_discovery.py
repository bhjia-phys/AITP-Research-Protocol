"""Bounded lexical candidate discovery helpers for host routing."""

from __future__ import annotations

from brain.v5.host_route_contracts import HostRouteCandidate, HostRouteRequest
from brain.v5.query_index import lexical_terms
from brain.v5.research_retrieval import RetrievalResult


DISCOVERY_FAMILIES = (
    "artifacts",
    "claims",
    "code_states",
    "questions",
    "research_programs",
    "routes",
    "session_closeouts",
    "sessions",
    "source_assets",
    "topics",
)
DISCOVERY_LIMIT = 48
SESSION_LIMIT = 12

_FAMILY_WEIGHTS = {
    "topics": 30_000,
    "routes": 28_000,
    "session_closeouts": 26_000,
    "claims": 24_000,
    "questions": 22_000,
    "code_states": 20_000,
    "artifacts": 18_000,
    "source_assets": 16_000,
    "sessions": 14_000,
    "research_programs": 12_000,
}
_ROUTE_STOP_TERMS = frozenset(
    {
        "a",
        "an",
        "and",
        "continue",
        "for",
        "in",
        "of",
        "on",
        "research",
        "the",
        "this",
        "to",
        "work",
    }
)


def discovery_text(request: HostRouteRequest) -> str:
    parts = (
        request.request_summary,
        request.repo_id,
        request.branch,
        request.current_path,
        *request.visible_files,
    )
    return " ".join(part for part in parts if part)


def rank_topic_matches(
    request: HostRouteRequest,
    retrieval: RetrievalResult,
) -> list[tuple[str, int, dict[str, int], tuple[str, ...]]]:
    meaningful = set(lexical_terms(discovery_text(request))) - _ROUTE_STOP_TERMS
    matches: dict[str, dict[str, object]] = {}
    for item in retrieval.items:
        topic_id = str(item.topic_id or item.record.get("topic_id") or "").strip()
        search_terms = set(lexical_terms(str(item.record.get("search_text") or "")))
        explicit_topic = topic_id in request.explicit_topic_ids
        exact_anchor = item.exact_score > 0
        if not topic_id or (
            not explicit_topic
            and not exact_anchor
            and not meaningful.intersection(search_terms)
        ):
            continue
        match = matches.setdefault(topic_id, {"components": {}, "refs": []})
        components = match["components"]
        component = (
            "explicit_topic"
            if explicit_topic
            else "exact_record_anchor"
            if exact_anchor
            else f"indexed_{item.family}"
        )
        value = (
            750_000
            if explicit_topic
            else 500_000
            if exact_anchor
            else _FAMILY_WEIGHTS.get(item.family, 10_000) + item.total_score * 100
        )
        components[component] = max(int(components.get(component, 0)), value)
        match["refs"].append(item.record_ref)

    ranked = []
    for topic_id, match in matches.items():
        components = dict(match["components"])
        refs = tuple(sorted(set(match["refs"])))[:8]
        score = min(sum(components.values()), 900_000)
        ranked.append((topic_id, score, components, refs))
    return sorted(ranked, key=lambda item: (-item[1], item[0]))


def candidate_plans(topic_matches, sessions: RetrievalResult) -> list[tuple]:
    plans = []
    for item in sessions.items:
        topic_id = str(item.topic_id or item.record.get("topic_id") or "").strip()
        if topic_id not in topic_matches:
            continue
        session_id = str(item.record.get("record_id") or "").strip()
        if not session_id and item.record_ref.startswith("session:"):
            session_id = item.record_ref.partition(":")[2]
        if not session_id:
            continue
        _, score, components, refs = topic_matches[topic_id]
        exact_refs = (f"session:{session_id}", f"topic:{topic_id}", *refs)
        plans.append(
            (
                topic_id,
                session_id,
                score,
                {**components, "exact_anchor_verification": 100},
                tuple(dict.fromkeys(exact_refs)),
            )
        )
    return sorted(plans, key=lambda item: (-item[2], item[0], item[1]))


def candidate_from_plan(plan: tuple) -> HostRouteCandidate:
    topic_id, session_id, score, components, exact_refs = plan
    explicit_topic = "explicit_topic" in components
    exact_anchor = "exact_record_anchor" in components
    return HostRouteCandidate(
        topic_id=topic_id,
        session_id=session_id,
        score=score,
        evidence_tier=(
            "explicit" if explicit_topic else "exact_anchor" if exact_anchor else "indexed_text"
        ),
        component_scores=components,
        reason_codes=(
            "explicit_topic"
            if explicit_topic
            else "exact_record_anchor"
            if exact_anchor
            else "indexed_text_match",
            "exact_session_topic_verified",
        ),
        exact_refs=exact_refs,
    )
