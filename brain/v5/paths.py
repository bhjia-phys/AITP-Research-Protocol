"""Filesystem path model for AITP v5 workspaces."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from brain.v5.record_family_registry import registry_family_specs


_NON_REGISTRY_LAYOUT_DIRS = [
    "contexts",
    "topics",
    "source_blobs",
    "memory/l2/entries",
    "memory/l2/graph",
    "memory/l2/conflicts",
    "memory/l2/indexes",
    "memory/code_provenance",
    "memory/upstream_snapshots",
    "memory/route_memory",
    "curated_rag/indexes",
    "indexes",
    "knowledge_connectors",
    "tools/recipes",
    "tools/trust_cards",
    "tools/domain_packs",
    "tools/runs",
    "tools/adapters",
    "runtime/sessions",
    "runtime/code_workspaces",
    "runtime/locks/topics",
    "runtime/locks/claims",
    "revisions",
    "surfaces",
    "schemas",
    "migrations",
]
_LAYOUT_DIRS = [
    "contexts",
    "topics",
    *(spec.relative_dir for spec in registry_family_specs().values()),
    *[path for path in _NON_REGISTRY_LAYOUT_DIRS if path not in {"contexts", "topics"}],
]


def registry_layout_families() -> tuple[str, ...]:
    """Return the canonical registry families materialized by ``ensure_layout``."""

    return tuple(registry_family_specs())


@dataclass(frozen=True)
class WorkspacePaths:
    """Resolved paths for a v5 workspace."""

    base: Path

    @property
    def root(self) -> Path:
        return self.base / ".aitp"

    def ensure_layout(self) -> None:
        for rel in _LAYOUT_DIRS:
            (self.root / rel).mkdir(parents=True, exist_ok=True)

    def context_dir(self, context_id: str) -> Path:
        return self.root / "contexts" / context_id

    def topic_dir(self, topic_id: str) -> Path:
        return self.root / "topics" / topic_id

    def registry_dir(self, family: str) -> Path:
        return self.root / "registry" / family

    def source_blob_dir(self, topic_id: str, asset_id: str) -> Path:
        return self.root / "source_blobs" / topic_id / asset_id

    def session_path(self, session_id: str) -> Path:
        return self.root / "runtime" / "sessions" / f"{session_id}.md"
