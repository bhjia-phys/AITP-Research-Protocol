"""Explicit bounded canonical fallback for one stale query family."""

from __future__ import annotations

from dataclasses import dataclass

from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import (
    _lexical_index,
    _project_tool_run_supersession,
    current_family_content_watermark,
)
from brain.v5.query_index_delta_contracts import EffectiveIndexSnapshot
from brain.v5.query_index_family_scan import (
    canonical_family_paths,
    scan_canonical_family,
)
from brain.v5.query_index_locking import (
    acquire_canonical_mutation_lease,
    active_canonical_mutation_lease,
)


@dataclass(frozen=True)
class FamilyFallbackResult:
    used: bool
    content_verified: bool
    snapshot: EffectiveIndexSnapshot | None = None
    malformed_count: int = 0
    checked_paths: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()


def strict_family_fallback(
    ws: WorkspacePaths,
    source: EffectiveIndexSnapshot,
    family: str,
    *,
    max_records: int,
) -> FamilyFallbackResult:
    active_lease = active_canonical_mutation_lease(ws)
    if active_lease is not None:
        active_lease.assert_active(ws)
        return _strict_family_fallback_locked(ws, source, family, max_records=max_records)
    with acquire_canonical_mutation_lease(ws):
        return _strict_family_fallback_locked(ws, source, family, max_records=max_records)


def _strict_family_fallback_locked(
    ws: WorkspacePaths,
    source: EffectiveIndexSnapshot,
    family: str,
    *,
    max_records: int,
) -> FamilyFallbackResult:
    paths = canonical_family_paths(ws, family)
    checked_paths = tuple(sorted(path.relative_to(ws.root).as_posix() for path in paths))
    if len(paths) > max_records:
        return FamilyFallbackResult(
            used=False,
            content_verified=False,
            checked_paths=checked_paths,
            diagnostics=(
                f"single-family fallback bound exceeded for {family}: "
                f"{len(paths)} > {max_records}",
            ),
        )
    before = current_family_content_watermark(ws, family)
    scan = scan_canonical_family(ws, family, paths=paths)
    after = current_family_content_watermark(ws, family)
    if not (before == scan.content_watermark == after):
        return FamilyFallbackResult(
            used=False,
            content_verified=False,
            checked_paths=scan.checked_paths,
            diagnostics=(
                f"strong canonical content changed during fallback scan: {family}",
            ),
        )
    documents = [dict(row) for row in scan.documents]
    _project_tool_run_supersession(documents)
    for doc_id, document in enumerate(documents):
        document["doc_id"] = doc_id
    lexical = _lexical_index(documents)
    snapshot = EffectiveIndexSnapshot(
        manifest=source.manifest,
        documents=tuple(documents),
        lexical_terms={term: tuple(postings) for term, postings in lexical.items()},
        record_refs=tuple(row["record_ref"] for row in documents),
        family_state_tokens={family: scan.state_token},
        family_content_watermarks={family: scan.content_watermark},
        family_content_accumulators={family: scan.content_accumulator},
        malformed_family_counts={family: scan.malformed_count},
        dirty_families=source.dirty_families,
        delta_generation=source.delta_generation,
        read_errors=scan.issues,
    )
    return FamilyFallbackResult(
        used=True,
        content_verified=True,
        snapshot=snapshot,
        malformed_count=scan.malformed_count,
        checked_paths=scan.checked_paths,
        diagnostics=scan.issues,
    )
