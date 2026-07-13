"""Compatibility re-exports for focused M0 MCP modules."""

from brain.v5.mcp_context import (
    aitp_v5_compile_research_context,
    aitp_v5_get_capability_registry,
    aitp_v5_get_runtime_capability_audit,
)
from brain.v5.mcp_query import (
    aitp_v5_build_query_index,
    aitp_v5_exact_expand_records,
    aitp_v5_get_query_index_status,
)

__all__ = [
    "aitp_v5_build_query_index",
    "aitp_v5_compile_research_context",
    "aitp_v5_exact_expand_records",
    "aitp_v5_get_capability_registry",
    "aitp_v5_get_query_index_status",
    "aitp_v5_get_runtime_capability_audit",
]
