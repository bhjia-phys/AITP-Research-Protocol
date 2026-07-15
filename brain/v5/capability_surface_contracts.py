"""Focused public-surface contracts introduced by the capability registry."""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Any, Callable

from brain.v5.contracts import ContractError, ContractResult


@dataclass(frozen=True)
class SurfaceRule:
    purpose: str
    required: tuple[str, ...]
    kind: str = ""


_RULES = {
    "public_surface_contracts": SurfaceRule(
        "self-describing registry of contracted public payload surfaces",
        ("surface_names", "surfaces", "validator"),
        "public_surface_contracts",
    ),
    "risk_assessment": SurfaceRule(
        "read-only risk assessment over a claim and linked code state",
        ("ok", "claim_id", "risk_assessment"),
    ),
    "record_routing_audit": SurfaceRule(
        "read-only lifecycle routing audit for one topic",
        ("ok", "topic_id", "events"),
    ),
    "session_binding_record": SurfaceRule(
        "canonical session-to-topic binding returned by an explicit write",
        ("ok", "session_id", "topic_id"),
    ),
    "record_rehome_plan": SurfaceRule(
        "read-only explicit-record rehome plan",
        ("ok", "plan", "record_count"),
    ),
    "codex_mcp_surface_catalog": SurfaceRule(
        "compact Codex facade catalog and progressive-disclosure policy",
        ("ok", "profiles", "codex_surface_tools"),
        "codex_mcp_surface_catalog",
    ),
    "codex_auto_route_decision": SurfaceRule(
        "read-only decision to enter or skip AITP for a research request",
        ("ok", "aitp_required_before_answer", "recommended_next_tool"),
        "codex_auto_route_decision",
    ),
    "codex_entry_context": SurfaceRule(
        "bounded topic and session entry context",
        ("ok", "recommended_next_tool"),
        "codex_entry_context",
    ),
    "codex_context_expansion": SurfaceRule(
        "explicit progressive context expansion",
        ("ok", "expansion"),
        "codex_context_expansion",
    ),
    "codex_recording_step": SurfaceRule(
        "read-only recording classification and slot guidance",
        ("ok", "classification"),
        "codex_recording_step",
    ),
    "codex_record_apply": SurfaceRule(
        "explicit constrained typed-record apply result",
        ("ok", "slot"),
        "codex_record_apply",
    ),
    "codex_literature_step": SurfaceRule(
        "layered literature registration and reading workflow result",
        ("ok", "action"),
        "codex_literature_step",
    ),
    "codex_closeout": SurfaceRule(
        "quiet checkpoint preview or explicitly applied closeout",
        ("ok", "mode", "write_executed"),
        "codex_closeout",
    ),
    "claim_record": SurfaceRule(
        "canonical claim returned by an explicit create operation",
        ("ok", "claim_id", "topic_id"),
    ),
    "topic_record": SurfaceRule(
        "canonical topic returned by an explicit create operation",
        ("ok", "topic_id", "context_id"),
    ),
    "workspace_initialization": SurfaceRule(
        "explicit workspace initialization result",
        ("ok", "workspace_root"),
    ),
    "curated_legacy_topic_catalog": SurfaceRule(
        "read-only catalog of curated legacy topic fixtures",
        ("ok", "topics"),
        "curated_legacy_topic_catalog",
    ),
    "capability_registry_audit": SurfaceRule(
        "read-only cross-surface capability parity audit",
        ("ok", "capability_count", "issues"),
        "capability_registry_audit",
    ),
    "runtime_capability_audit": SurfaceRule(
        "read-only source, file, family, writer, and runtime capability audit",
        ("capabilities", "files", "writers"),
        "runtime_capability_audit",
    ),
    "query_index_build_report": SurfaceRule(
        "derived query-index build result with malformed-record coverage",
        ("ok", "manifest", "checked_count", "indexed_count", "issues"),
        "query_index_build_report",
    ),
    "query_index_status": SurfaceRule(
        "read-only query-index generation, freshness, and coverage status",
        ("ok", "exists", "fresh"),
        "query_index_status",
    ),
    "research_retrieval_result": SurfaceRule(
        "read-only exact record expansion with explicit retrieval coverage",
        ("ok", "items", "coverage", "index_status"),
        "research_retrieval_result",
    ),
    "research_context_bundle": SurfaceRule(
        "bounded trust-neutral context compiled from indexed typed records",
        ("ok", "session_id", "topic_id", "coverage", "markdown"),
        "research_context_bundle",
    ),
    "monitor_snapshot_write_result": SurfaceRule(
        "canonical immutable monitor snapshot write result",
        (
            "ok",
            "snapshot_id",
            "record_ref",
            "content_hash",
            "revision",
            "writes_records",
            "can_update_claim_trust",
        ),
        "monitor_snapshot_write_result",
    ),
    "monitor_history": SurfaceRule(
        "read-only ordered process observations for one exact tool run",
        (
            "ok",
            "status",
            "tool_run_ref",
            "snapshot_refs",
            "snapshots",
            "errors",
            "can_update_kernel_state",
            "can_update_claim_trust",
        ),
        "monitor_history",
    ),
}


def capability_surface_names() -> tuple[str, ...]:
    return tuple(_RULES)


def capability_surface_purposes() -> dict[str, str]:
    return {name: rule.purpose for name, rule in _RULES.items()}


def capability_surface_validators() -> dict[str, Callable[[dict[str, Any]], dict[str, Any]]]:
    return {
        name: partial(require_valid_capability_surface, name)
        for name in capability_surface_names()
    }


def validate_capability_surface(
    surface_name: str,
    payload: dict[str, Any],
    *,
    path: str = "capability_surface",
) -> ContractResult:
    result = ContractResult()
    rule = _RULES.get(surface_name)
    if rule is None:
        result.add(path, f"unknown capability surface {surface_name!r}")
        return result
    candidate: Any = payload
    if surface_name == "public_surface_contracts" and "public_surfaces" in payload:
        candidate = payload["public_surfaces"]
    if not isinstance(candidate, dict):
        result.add(path, "must be a mapping")
        return result
    if rule.kind and candidate.get("kind") != rule.kind:
        result.add(f"{path}.kind", f"must be {rule.kind!r}")
    for field in rule.required:
        if field not in candidate:
            result.add(f"{path}.{field}", "is required")
    if surface_name in {"monitor_snapshot_write_result", "monitor_history"}:
        if candidate.get("can_update_claim_trust") is not False:
            result.add(
                f"{path}.can_update_claim_trust",
                "must be false for process-only monitor surfaces",
            )
    if surface_name == "monitor_snapshot_write_result":
        if candidate.get("writes_records") is not True:
            result.add(f"{path}.writes_records", "must be true for the write result")
    if surface_name == "monitor_history":
        if candidate.get("can_update_kernel_state") is not False:
            result.add(f"{path}.can_update_kernel_state", "must be false for read history")
    return result


def require_valid_capability_surface(
    surface_name: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    result = validate_capability_surface(surface_name, payload, path=surface_name)
    if not result.ok:
        raise ContractError(result)
    return payload
