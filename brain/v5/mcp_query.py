"""MCP wrappers for derived query indexes and exact typed-record retrieval."""

from __future__ import annotations

from dataclasses import asdict

from brain.v5.mcp_base_resolution import resolve_workspace_base
from brain.v5.paths import WorkspacePaths
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.query_index import (
    INDEX_SCHEMA_VERSION,
    build_query_index,
    load_query_manifest,
    query_index_is_fresh,
)
from brain.v5.research_retrieval import exact_expand


def aitp_v5_build_query_index(base: str) -> dict:
    report = build_query_index(_workspace(base))
    payload = {
        "ok": True,
        "kind": "query_index_build_report",
        **asdict(report),
    }
    return require_valid_public_surface("query_index_build_report", payload)


def aitp_v5_get_query_index_status(base: str) -> dict:
    ws = _workspace(base)
    manifest_path = ws.root / "indexes" / "manifest.json"
    if not manifest_path.exists():
        payload = {
            "ok": True,
            "kind": "query_index_status",
            "exists": False,
            "fresh": False,
            "generation": 0,
            "index_schema_version": 0,
            "required_index_schema_version": INDEX_SCHEMA_VERSION,
            "record_count": 0,
            "malformed_count": 0,
            "canonical_watermark": "",
            "reason": "derived query index has not been built",
            **_trust_neutral_boundary(),
        }
    else:
        manifest = load_query_manifest(ws)
        fresh = query_index_is_fresh(ws, manifest)
        payload = {
            "ok": True,
            "kind": "query_index_status",
            "exists": True,
            "fresh": fresh,
            "generation": manifest.generation,
            "index_schema_version": manifest.index_schema_version,
            "required_index_schema_version": INDEX_SCHEMA_VERSION,
            "record_count": manifest.record_count,
            "malformed_count": manifest.malformed_count,
            "canonical_watermark": manifest.canonical_watermark,
            "reason": (
                "derived index matches canonical state"
                if fresh
                else "derived index is stale and must not support absolute no-result claims"
            ),
            **_trust_neutral_boundary(),
        }
    return require_valid_public_surface("query_index_status", payload)


def aitp_v5_exact_expand_records(
    base: str,
    *,
    refs: list[str],
    limit: int = 50,
) -> dict:
    result = exact_expand(_workspace(base), refs, limit=limit)
    payload = {
        "ok": True,
        "kind": "research_retrieval_result",
        **asdict(result),
    }
    return require_valid_public_surface("research_retrieval_result", payload)


def _workspace(base: str) -> WorkspacePaths:
    return WorkspacePaths(resolve_workspace_base(base))


def _trust_neutral_boundary() -> dict[str, bool]:
    return {
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
