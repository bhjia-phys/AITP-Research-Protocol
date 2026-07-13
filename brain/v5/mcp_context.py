"""MCP wrappers for capability audits and bounded research context."""

from __future__ import annotations

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
