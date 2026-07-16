"""Budgeted Markdown rendering for physics knowledge context entries."""

from __future__ import annotations

from typing import Any, Sequence

from brain.v5.context_compiler_support import estimate_context_tokens
from brain.v5.knowledge_context_contracts import (
    KnowledgeContextEntry,
    KnowledgeContextRequest,
)


def render_knowledge_entries(
    request: KnowledgeContextRequest,
    entries: Sequence[KnowledgeContextEntry],
    *,
    max_tokens: int,
    max_bytes: int,
) -> tuple[
    tuple[KnowledgeContextEntry, ...],
    str,
    dict[str, Any],
    tuple[str, ...],
]:
    header = [
        "# AITP Physics Knowledge Context",
        "",
        f"mode={request.mode}; topic={request.topic_id}; intent={request.intent}",
        "orientation_only=true; can_update_claim_trust=false",
    ]
    sections = (
        ("## Grounded knowledge", {"grounded"}),
        ("## Source passages", {"source"}),
        ("## Speculative insight", {"insight"}),
        ("## Orientation and discovery", {"orientation"}),
    )
    lines = list(header)
    shown: list[KnowledgeContextEntry] = []
    lane_tokens: dict[str, int] = {}
    omitted: list[str] = []
    for heading, lanes in sections:
        lines.extend(("", heading))
        for entry in (item for item in entries if item.knowledge_lane in lanes):
            block = _entry_lines(entry)
            proposed = "\n".join([*lines, *block, ""])
            if (
                estimate_context_tokens(proposed) > max_tokens
                or len(proposed.encode("utf-8")) > max_bytes
            ):
                omitted.append(entry.record_ref)
                continue
            lines.extend(block)
            shown.append(entry)
            lane_tokens[entry.knowledge_lane] = lane_tokens.get(
                entry.knowledge_lane, 0
            ) + estimate_context_tokens("\n".join(block))
    shown_refs = {entry.record_ref for entry in shown}
    omitted.extend(entry.record_ref for entry in entries if entry.record_ref not in shown_refs)
    markdown = "\n".join(lines).rstrip() + "\n"
    allocation = {
        "max_tokens": max_tokens,
        "used_tokens": 0,
        "remaining_tokens": max_tokens,
        "lane_tokens": lane_tokens,
        "allocation_policy": "rank_order_with_separate_knowledge_lane_sections",
    }
    return tuple(shown), markdown, allocation, tuple(dict.fromkeys(omitted))


def _entry_lines(entry: KnowledgeContextEntry) -> list[str]:
    boundary = (
        f"  scope={entry.scope_lane}; grounding={entry.grounding_state}; "
        f"framework={entry.framework_compatibility}; "
        f"regime={entry.regime_compatibility}; "
        f"convention={entry.convention_compatibility}"
    )
    handle = entry.exact_expansion
    return [
        f"- `{entry.record_ref}` {entry.summary}",
        boundary,
        f"  expand={handle.get('kind')}@{handle.get('content_hash', '')[:12]}",
    ]


__all__ = ["render_knowledge_entries"]
