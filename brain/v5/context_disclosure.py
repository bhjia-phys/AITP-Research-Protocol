"""Closed progressive-disclosure policy for AITP research context."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.record_family_registry import record_family_specs
from brain.v5.research_scope import ScopeResolution


DISCLOSURE_LEVELS = (
    "route_hint",
    "startup_orientation",
    "normal_research",
    "exact_expansion",
)

_NEXT_LEVEL = {
    "route_hint": "startup_orientation",
    "startup_orientation": "normal_research",
    "normal_research": "exact_expansion",
    "exact_expansion": "",
}

_STARTUP_SUPPORT_FAMILIES = frozenset(
    {"cross_topic_relations", "research_programs", "topics"}
)


def validate_disclosure_level(level: str) -> None:
    if level not in DISCLOSURE_LEVELS:
        raise ValueError(
            f"disclosure_level must be one of {'|'.join(DISCLOSURE_LEVELS)}"
        )


def scope_payload(scope: ScopeResolution) -> dict[str, Any]:
    payload = asdict(scope)
    for key, value in tuple(payload.items()):
        if isinstance(value, tuple):
            payload[key] = list(value)
    payload["not_shown_refs"] = list(
        dict.fromkeys([*scope.excluded_refs, *scope.discovery_refs])
    )
    return payload


def next_level_handles(scope: ScopeResolution, level: str) -> dict[str, Any]:
    return {
        "next_disclosure_level": _NEXT_LEVEL[level],
        "session_id": scope.session_id,
        "topic_id": scope.primary_topic_id,
        "focus_set_ref": scope.focus_set_ref,
        "program_id": scope.program_id,
        "exact_refs": list(dict.fromkeys([*scope.primary_refs, *scope.supporting_refs]))[:20],
        "exact_expansion_refs": [],
        "exact_expansion_ref_count": 0,
        "exact_expansion_refs_truncated": False,
        "blocked_refs_require_exact_expansion": False,
        "requires_explicit_call": bool(_NEXT_LEVEL[level]),
    }


def route_hint_refs(scope: ScopeResolution) -> tuple[str, ...]:
    allowed_families = {"sessions", "topics", "session_focus_sets", "research_programs"}
    refs: list[str] = []
    for ref in [*scope.primary_refs, *scope.supporting_refs]:
        family = family_for_ref(ref)
        if family in allowed_families:
            refs.append(ref)
    return tuple(dict.fromkeys(refs))


def startup_support_refs(scope: ScopeResolution) -> tuple[str, ...]:
    return tuple(
        ref
        for ref in scope.supporting_refs
        if family_for_ref(ref) in _STARTUP_SUPPORT_FAMILIES
    )


def family_for_ref(ref: str) -> str:
    kind = str(ref).partition(":")[0].replace("-", "_")
    for family, spec in record_family_specs().items():
        aliases = {alias.replace("-", "_") for alias in spec.exact_ref_aliases}
        if kind in aliases:
            return family
    return ""


def route_hint_markdown(scope: ScopeResolution, refs: tuple[str, ...]) -> str:
    lines = [
        "AITP route hint.",
        f"Session: {scope.session_id}",
        f"Primary topic handle: topic:{scope.primary_topic_id}",
        f"Focus handle: {scope.focus_set_ref or 'none'}",
        f"Program handle: {scope.program_id or 'none'}",
        "Next disclosure: startup_orientation",
        "Scientific content is not included at route-hint level.",
    ]
    if refs:
        lines.append("Routing refs: " + ", ".join(refs))
    return "\n".join(lines) + "\n"


def route_hint_coverage() -> dict[str, Any]:
    all_families = tuple(sorted(record_family_specs()))
    checked = ("research_programs", "session_focus_sets", "sessions", "topics")
    return {
        "exhaustive": False,
        "can_claim_no_result": False,
        "checked_families": checked,
        "unchecked_families": tuple(family for family in all_families if family not in checked),
        "malformed_count": 0,
        "reason": "route hints check routing handles only and do not inspect scientific records",
        "scope_state_fresh": True,
        "scope_content_verified": False,
        "scope_fresh": False,
        "global_fresh": False,
        "dirty_families": (),
        "checked_paths": (),
        "fallback_used": False,
        "read_errors": (),
    }
