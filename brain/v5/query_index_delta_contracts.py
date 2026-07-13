"""Typed contracts for the disposable query-index delta overlay."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DirtyFamilyState:
    family: str
    reason: str
    predecessor_content_watermark: str = ""
    observed_content_watermark: str = ""
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class IndexDeltaEntry:
    record_ref: str
    family: str
    row_file: str
    row_hash: str
    record_content_hash: str
    predecessor_content_hash: str = ""


@dataclass(frozen=True)
class IndexDeltaManifest:
    base_generation: int
    base_content_hash: str
    generation: int
    entries: dict[str, IndexDeltaEntry] = field(default_factory=dict)
    repaired_families: dict[str, str] = field(default_factory=dict)
    family_state_tokens: dict[str, str] = field(default_factory=dict)
    family_content_watermarks: dict[str, str] = field(default_factory=dict)
    family_content_accumulators: dict[str, dict[str, Any]] = field(default_factory=dict)
    family_malformed_counts: dict[str, int] = field(default_factory=dict)
    dirty_families: dict[str, DirtyFamilyState] = field(default_factory=dict)
    predecessor_chain_token: str = ""
    content_hash: str = ""
    manifest_kind: str = "query_index_delta"
    schema_version: int = 1


@dataclass(frozen=True)
class IndexProjectionOutcome:
    status: str = "not_configured"
    dirty_families: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()
    repair_required: bool = False


@dataclass(frozen=True)
class EffectiveIndexSnapshot:
    manifest: Any
    documents: tuple[dict[str, Any], ...]
    lexical_terms: dict[str, tuple[int, ...]]
    record_refs: tuple[str, ...]
    family_state_tokens: dict[str, str]
    family_content_watermarks: dict[str, str]
    family_content_accumulators: dict[str, dict[str, Any]] = field(default_factory=dict)
    malformed_family_counts: dict[str, int] = field(default_factory=dict)
    dirty_families: tuple[str, ...] = ()
    delta_generation: int = 0
    read_errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScopedIndexFreshness:
    checked_families: tuple[str, ...]
    scope_state_fresh: bool
    scope_content_verified: bool
    scope_fresh: bool
    global_fresh: bool
    dirty_families: tuple[str, ...] = ()
    checked_paths: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()


_PROJECTION_STATUSES = {
    "projected",
    "unchanged",
    "dirty",
    "migration_required",
    "not_configured",
}


def validate_projection_outcome(outcome: IndexProjectionOutcome) -> tuple[str, ...]:
    errors: list[str] = []
    if outcome.status not in _PROJECTION_STATUSES:
        errors.append("projection status is unsupported")
    if outcome.status == "dirty" and not outcome.dirty_families:
        errors.append("dirty projection requires dirty_families")
    if outcome.repair_required != bool(outcome.dirty_families):
        errors.append("repair_required must match dirty_families")
    return tuple(errors)
