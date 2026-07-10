"""Focused MCP wrappers for registry, index, retrieval, and context capabilities."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from brain.v5.capability_registry import audit_capability_registry
from brain.v5.context_compiler import (
    ContextRequest,
    compile_research_context,
    context_bundle_payload,
)
from brain.v5.mcp_base_resolution import resolve_workspace_base
from brain.v5.paths import WorkspacePaths
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.query_index import (
    build_query_index,
    canonical_state_token,
    load_query_manifest,
)
from brain.v5.research_retrieval import exact_expand
from brain.v5.runtime_audit import build_runtime_capability_audit


def aitp_v5_get_capability_registry() -> dict:
    return require_valid_public_surface(
        "capability_registry_audit",
        audit_capability_registry(),
    )


def aitp_v5_get_runtime_capability_audit(
    base: str = "",
    *,
    repo_root: str = "",
) -> dict:
    root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parents[2]
    workspace_base = resolve_workspace_base(base) if base else None
    payload = {
        "ok": True,
        **build_runtime_capability_audit(root, workspace_base=workspace_base),
    }
    return require_valid_public_surface("runtime_capability_audit", payload)


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
            "record_count": 0,
            "malformed_count": 0,
            "canonical_watermark": "",
            "reason": "derived query index has not been built",
            **_trust_neutral_boundary(),
        }
    else:
        manifest = load_query_manifest(ws)
        fresh = canonical_state_token(ws) == manifest.canonical_state_token
        payload = {
            "ok": True,
            "kind": "query_index_status",
            "exists": True,
            "fresh": fresh,
            "generation": manifest.generation,
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


def aitp_v5_compile_research_context(
    base: str,
    *,
    session_id: str,
    objective_text: str = "",
    user_goal: str = "",
    topic_id: str = "",
    exact_refs: list[str] | None = None,
    max_tokens: int = 1200,
    max_bytes: int = 6000,
    record_limit: int = 80,
    candidate_limit: int = 12,
) -> dict:
    ws = _workspace(base)
    if not (ws.root / "indexes" / "manifest.json").exists():
        raise FileNotFoundError(
            "derived query index is missing; call aitp_v5_build_query_index first"
        )
    bundle = compile_research_context(
        ws,
        ContextRequest(
            session_id=session_id,
            objective_text=objective_text,
            user_goal=user_goal,
            topic_id=topic_id,
            exact_refs=tuple(exact_refs or ()),
            max_tokens=max_tokens,
            max_bytes=max_bytes,
            record_limit=record_limit,
            candidate_limit=candidate_limit,
        ),
    )
    payload = {
        "ok": True,
        "kind": "research_context_bundle",
        **context_bundle_payload(bundle),
    }
    return require_valid_public_surface("research_context_bundle", payload)


def _workspace(base: str) -> WorkspacePaths:
    return WorkspacePaths(resolve_workspace_base(base))


def _trust_neutral_boundary() -> dict[str, bool]:
    return {
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
