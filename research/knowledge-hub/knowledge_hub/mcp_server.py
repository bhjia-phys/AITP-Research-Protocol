from __future__ import annotations

import json
import traceback

from mcp.server.fastmcp import FastMCP

try:
    from .hub import KnowledgeHub
except ImportError:  # pragma: no cover
    from hub import KnowledgeHub


mcp = FastMCP(
    "knowledge-hub",
    instructions=(
        "Knowledge middleware between Zotero/OpenCode/Obsidian. "
        "Provides ingest, query, provenance lookup, Obsidian export, and index status tools."
    ),
)

hub = KnowledgeHub()


def _ok(**payload: object) -> str:
    return json.dumps({"status": "success", **payload}, ensure_ascii=False, indent=2)


def _err(message: str) -> str:
    return json.dumps(
        {
            "status": "error",
            "error": message,
            "traceback": traceback.format_exc(),
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def hub_ingest_sources(sources: list[str], source_kind: str = "auto") -> str:
    """Ingest file/url/inline sources into the local hub store."""
    try:
        result = hub.ingest_sources(sources=sources, source_kind=source_kind)
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@mcp.tool()
def hub_query(
    question: str,
    top_k: int = 6,
    include_zotero: bool = True,
    max_claims: int = 3,
    min_local_score: float = 0.0,
) -> str:
    """Query the hub and return answer with citations and query_id."""
    try:
        result = hub.query(
            question=question,
            top_k=top_k,
            include_zotero=include_zotero,
            max_claims=max_claims,
            min_local_score=min_local_score,
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@mcp.tool()
def hub_get_provenance(query_id: str) -> str:
    """Fetch stored query record for a query_id."""
    try:
        record = hub.get_provenance(query_id=query_id)
        return _ok(record=record)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@mcp.tool()
def hub_export_obsidian(
    query_id: str,
    note_title: str,
    vault_path: str | None = None,
    output_subdir: str = "07 Knowledge Hub",
) -> str:
    """Export a query record to an Obsidian markdown note."""
    try:
        result = hub.export_obsidian(
            query_id=query_id,
            note_title=note_title,
            vault_path=vault_path,
            output_subdir=output_subdir,
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@mcp.tool()
def hub_refresh_index(force_rebuild: bool = False) -> str:
    """Read Zotero semantic DB status and rebuild guidance."""
    try:
        result = hub.refresh_index(force_rebuild=force_rebuild)
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
