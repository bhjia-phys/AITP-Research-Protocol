"""Full-only MCP wrappers for M3 knowledge and insight operations."""

from __future__ import annotations

from typing import Any

from brain.v5.knowledge_facade import decode_knowledge_payload, invoke_knowledge_operation
from brain.v5.mcp_base_resolution import resolve_workspace_base
from brain.v5.paths import WorkspacePaths


def invoke_knowledge_mcp(base: str, operation: str, payload_json: str) -> dict[str, Any]:
    ws = WorkspacePaths(resolve_workspace_base(base))
    return invoke_knowledge_operation(ws, operation, decode_knowledge_payload(payload_json))


def _invoke(base: str, operation: str, payload_json: str) -> dict[str, Any]:
    return invoke_knowledge_mcp(base, operation, payload_json)


def aitp_v5_knowledge_diagnose_candidate(base: str, *, payload_json: str) -> dict[str, Any]:
    """Diagnose one exact knowledge, insight, or procedural candidate."""
    return _invoke(base, "knowledge_diagnose_candidate", payload_json)


def aitp_v5_knowledge_record_review(base: str, *, payload_json: str) -> dict[str, Any]:
    """Record a hash-bound human review decision for one knowledge candidate."""
    return _invoke(base, "knowledge_record_review", payload_json)


def aitp_v5_knowledge_promote_candidate(base: str, *, payload_json: str) -> dict[str, Any]:
    """Promote one exact approved knowledge or insight candidate."""
    return _invoke(base, "knowledge_promote_candidate", payload_json)


def aitp_v5_knowledge_build_source_shelf(base: str, *, payload_json: str) -> dict[str, Any]:
    """Build one disposable shelf from hash-pinned acquired source bytes."""
    return _invoke(base, "knowledge_build_source_shelf", payload_json)


def aitp_v5_knowledge_get_source_shelf(base: str, *, payload_json: str) -> dict[str, Any]:
    """Load and verify one exact derived source-shelf generation."""
    return _invoke(base, "knowledge_get_source_shelf", payload_json)


def aitp_v5_knowledge_build_discovery_request(base: str, *, payload_json: str) -> dict[str, Any]:
    """Build a bounded discovery request from one persisted knowledge gap."""
    return _invoke(base, "knowledge_build_discovery_request", payload_json)


def aitp_v5_knowledge_normalize_discovery_result(base: str, *, payload_json: str) -> dict[str, Any]:
    """Normalize bounded connector packets without creating source truth."""
    return _invoke(base, "knowledge_normalize_discovery_result", payload_json)


def aitp_v5_knowledge_query(base: str, *, payload_json: str) -> dict[str, Any]:
    """Run lineage-bound lexical, formula, graph, and optional dense retrieval."""
    return _invoke(base, "knowledge_query", payload_json)


def aitp_v5_knowledge_compile_context(base: str, *, payload_json: str) -> dict[str, Any]:
    """Compile one bounded trust-neutral physics-knowledge context slice."""
    return _invoke(base, "knowledge_compile_context", payload_json)
