"""MCP wrappers for workspace-local knowledge connector bindings."""

from __future__ import annotations

from brain.v5.knowledge_connector_bindings import bind_knowledge_connector, list_knowledge_connector_bindings
from brain.v5.mcp_base_resolution import resolve_workspace_base
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def _ws(base: str):
    return init_workspace(resolve_workspace_base(base))


def aitp_v5_list_knowledge_connector_bindings(
    base: str,
    *,
    connector_id: str = "",
    include_connector_catalog: bool = False,
) -> dict:
    """Return configured connector bindings without reading corpus content."""

    return require_valid_public_surface(
        "knowledge_connector_binding_registry",
        list_knowledge_connector_bindings(
            _ws(base),
            connector_id=connector_id,
            include_connector_catalog=include_connector_catalog,
        ),
    )


def aitp_v5_bind_knowledge_connector(
    base: str,
    *,
    connector_id: str,
    root_uri: str,
    corpus_id: str = "",
    label: str = "",
    file_globs: list[str] | None = None,
    domain_hints: list[str] | None = None,
    topic_hints: list[str] | None = None,
    priority: str = "medium",
    status: str = "active",
    notes: str = "",
) -> dict:
    """Persist one workspace-local connector binding as configuration metadata."""

    return require_valid_public_surface(
        "knowledge_connector_binding_registry",
        bind_knowledge_connector(
            _ws(base),
            connector_id=connector_id,
            root_uri=root_uri,
            corpus_id=corpus_id,
            label=label,
            file_globs=file_globs,
            domain_hints=domain_hints,
            topic_hints=topic_hints,
            priority=priority,
            status=status,
            notes=notes,
        ),
    )
