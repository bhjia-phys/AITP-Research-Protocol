"""Filesystem path model for AITP v5 workspaces."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


_LAYOUT_DIRS = [
    "contexts",
    "topics",
    "registry/intents",
    "registry/questions",
    "registry/ideas",
    "registry/claims",
    "registry/physics_objects",
    "registry/object_relations",
    "registry/evidence",
    "registry/artifacts",
    "registry/benchmarks",
    "registry/reference_locations",
    "registry/sensemaking_reports",
    "registry/validation_contracts",
    "registry/validation_results",
    "registry/code_states",
    "registry/code_workspaces",
    "registry/routes",
    "registry/attempts",
    "registry/tool_recipes",
    "registry/tool_runs",
    "registry/checkpoints",
    "registry/promotion_packets",
    "registry/outputs",
    "memory/l2/entries",
    "memory/l2/graph",
    "memory/l2/conflicts",
    "memory/l2/indexes",
    "memory/code_provenance",
    "memory/upstream_snapshots",
    "memory/route_memory",
    "tools/recipes",
    "tools/trust_cards",
    "tools/domain_packs",
    "tools/runs",
    "tools/adapters",
    "runtime/sessions",
    "runtime/code_workspaces",
    "runtime/locks/topics",
    "runtime/locks/claims",
    "surfaces",
    "schemas",
    "migrations",
]


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

    def session_path(self, session_id: str) -> Path:
        return self.root / "runtime" / "sessions" / f"{session_id}.md"
