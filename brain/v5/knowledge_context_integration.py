"""Minimal integration between research context and knowledge context."""

from __future__ import annotations

from dataclasses import asdict, replace
from typing import Any

from brain.v5.context_compiler_support import estimate_context_tokens
from brain.v5.knowledge_context_contracts import KnowledgeContextRequest
from brain.v5.paths import WorkspacePaths
from brain.v5.source_shelf_storage import hash_json


_KNOWLEDGE_PROFILES = {
    "paper_learning": "default",
    "paired_paper_learning": "comparison",
    "multi_paper_learning_route": "comparison",
    "derivation_check": "dependency",
}


def compile_requested_knowledge_context(
    ws: WorkspacePaths,
    request: KnowledgeContextRequest | None,
    *,
    topic_id: str,
    program_id: str,
    disclosure_level: str,
    max_tokens: int,
    max_bytes: int,
) -> dict[str, Any]:
    if request is None or disclosure_level not in {
        "startup_orientation",
        "normal_research",
    }:
        return {}
    if request.topic_id != topic_id:
        raise ValueError("knowledge request topic conflicts with resolved session scope")
    mode = "startup" if disclosure_level == "startup_orientation" else "normal"
    token_budget = min(request.max_tokens or 1400, max(128, max_tokens // 2))
    byte_budget = min(request.max_bytes or 8000, max(512, max_bytes // 2))
    result_limit = min(request.max_results or 12, 6 if mode == "normal" else 4)
    effective = replace(
        request,
        mode=mode,
        program_id=request.program_id or program_id,
        max_tokens=token_budget,
        max_bytes=byte_budget,
        max_results=result_limit,
    )
    from brain.v5.knowledge_context import compile_knowledge_context

    return asdict(compile_knowledge_context(ws, effective))


def profile_knowledge_request(
    ws: WorkspacePaths,
    session_id: str,
    *,
    profile_id: str,
    objective_text: str,
    user_goal: str,
    framework: str = "",
    regime: str = "",
    conventions: tuple[str, ...] = (),
    source_shelf_generation: str = "",
    source_shelf_topic_id: str = "",
) -> KnowledgeContextRequest | None:
    intent = _KNOWLEDGE_PROFILES.get(profile_id)
    query_text = " ".join(
        value.strip() for value in (objective_text, user_goal) if value.strip()
    )
    if intent is None or not query_text:
        return None
    from brain.v5.workspace import get_session_binding

    topic_id = get_session_binding(ws, session_id).topic_id
    shelf_topic = source_shelf_topic_id or (topic_id if source_shelf_generation else "")
    return KnowledgeContextRequest(
        query_text=query_text,
        topic_id=topic_id,
        framework=framework,
        regime=regime,
        conventions=conventions,
        intent=intent,
        source_shelf_generation=source_shelf_generation,
        source_shelf_topic_id=shelf_topic,
    )


def knowledge_coverage(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "knowledge_context_requested": bool(payload),
        "knowledge_context_partial": bool(payload.get("partial")) if payload else False,
        "knowledge_context_errors": list(
            (payload.get("coverage") or {}).get("errors") or []
        ),
    }


def knowledge_context_lines(payload: dict[str, Any]) -> list[str]:
    if not payload:
        return []
    markdown = str(payload.get("markdown") or "").splitlines()
    return ["", "## Physics knowledge slice", *markdown[1:]]


def knowledge_context_handles(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload:
        return {}
    return {
        "knowledge_exact_expansion_handles": list(
            payload.get("exact_expansion_handles") or []
        ),
        "knowledge_context_partial": bool(payload.get("partial")),
    }


def knowledge_context_payload_errors(
    payload: dict[str, Any],
) -> tuple[tuple[str, str], ...]:
    if not payload:
        return ()
    errors: list[tuple[str, str]] = []
    for key, expected in (
        ("orientation_only", True),
        ("summary_inputs_trusted", False),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        if payload.get(key) is not expected:
            message = (
                "knowledge context cannot update claim trust"
                if key == "can_update_claim_trust"
                else f"knowledge context {key} must be {expected}"
            )
            errors.append((key, message))
    markdown = payload.get("markdown")
    if not isinstance(markdown, str):
        errors.append(("markdown", "knowledge context markdown must be a string"))
    else:
        if payload.get("byte_count") != len(markdown.encode("utf-8")):
            errors.append(
                ("byte_count", "knowledge context byte count is inconsistent")
            )
        if payload.get("estimated_tokens") != estimate_context_tokens(markdown):
            errors.append(
                ("estimated_tokens", "knowledge context token estimate is inconsistent")
            )
    for index, entry in enumerate(payload.get("entries") or []):
        if not isinstance(entry, dict) or entry.get("can_update_claim_trust") is not False:
            errors.append(
                (
                    f"entries[{index}].can_update_claim_trust",
                    "knowledge context entry cannot update claim trust",
                )
            )
    basis = {
        key: payload.get(key)
        for key in (
            "mode", "topic_id", "query", "entries", "snapshot_lineage",
            "coverage", "token_allocation", "markdown",
        )
    }
    if payload.get("context_hash") != hash_json(basis):
        errors.append(("context_hash", "knowledge context hash is inconsistent"))
    return tuple(errors)


__all__ = [
    "compile_requested_knowledge_context",
    "knowledge_context_handles",
    "knowledge_context_lines",
    "knowledge_context_payload_errors",
    "knowledge_coverage",
    "profile_knowledge_request",
]
