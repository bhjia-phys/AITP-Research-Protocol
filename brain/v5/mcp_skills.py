"""Full-only MCP wrappers for the reviewed M4 Skill lifecycle."""

from __future__ import annotations

from typing import Any

from brain.v5.mcp_base_resolution import resolve_workspace_base
from brain.v5.paths import WorkspacePaths
from brain.v5.skill_facade import decode_skill_payload, invoke_skill_operation


def invoke_skill_mcp(base: str, operation: str, payload_json: str) -> dict[str, Any]:
    ws = WorkspacePaths(resolve_workspace_base(base))
    return invoke_skill_operation(ws, operation, decode_skill_payload(payload_json))


def _invoke(base: str, operation: str, payload_json: str) -> dict[str, Any]:
    return invoke_skill_mcp(base, operation, payload_json)


def aitp_v5_skill_distill_candidate(base: str, *, payload_json: str) -> dict[str, Any]:
    """Record one complete procedural candidate, never conceptual knowledge."""
    return _invoke(base, "skill_distill_candidate", payload_json)


def aitp_v5_skill_assess_readiness(base: str, *, payload_json: str) -> dict[str, Any]:
    """Assess and record exact independence, fixture, failure, and overlap readiness."""
    return _invoke(base, "skill_assess_readiness", payload_json)


def aitp_v5_skill_build_package_preview(base: str, *, payload_json: str) -> dict[str, Any]:
    """Render a derived host-neutral package preview without install authority."""
    return _invoke(base, "skill_build_package_preview", payload_json)


def aitp_v5_skill_record_package_proposal(base: str, *, payload_json: str) -> dict[str, Any]:
    """Record an immutable package artifact and draft proposal for review."""
    return _invoke(base, "skill_record_package_proposal", payload_json)


def aitp_v5_skill_plan_deployment(base: str, *, payload_json: str) -> dict[str, Any]:
    """Plan an install, rollback, or patch without changing the project Skill tree."""
    return _invoke(base, "skill_plan_deployment", payload_json)


def aitp_v5_skill_apply_deployment(base: str, *, payload_json: str) -> dict[str, Any]:
    """Apply one exact deployment plan after host-attested human approval."""
    return _invoke(base, "skill_apply_deployment", payload_json)


def aitp_v5_skill_match_applicable(base: str, *, payload_json: str) -> dict[str, Any]:
    """Match current reviewed project Skills without loading their bodies."""
    return _invoke(base, "skill_match_applicable", payload_json)


def aitp_v5_skill_record_usage(base: str, *, payload_json: str) -> dict[str, Any]:
    """Record one exact installed-package use and trust-neutral consumer backlinks."""
    return _invoke(base, "skill_record_usage", payload_json)


def aitp_v5_skill_propose_patch(base: str, *, payload_json: str) -> dict[str, Any]:
    """Draft an exact package patch from Skill-use records without applying it."""
    return _invoke(base, "skill_propose_patch", payload_json)


def aitp_v5_skill_build_validation_request(base: str, *, payload_json: str) -> dict[str, Any]:
    """Classify declared validators without executing arbitrary commands."""
    return _invoke(base, "skill_build_validation_request", payload_json)
