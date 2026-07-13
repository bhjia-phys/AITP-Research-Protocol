"""Write-through overlay facade for canonical records newer than the full index."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from brain.v5.markdown import write_text_atomic
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import (
    IndexIntegrityError,
    IndexManifest,
    _document_row,
    _hash_json,
    _hash_text,
    current_family_content_watermark,
    current_family_state_snapshot,
    current_family_state_token,
    load_query_manifest,
)
from brain.v5.query_index_accumulator import (
    content_accumulator_watermark,
    replace_content_accumulator_pair,
)
from brain.v5.query_index_delta_contracts import (
    DirtyFamilyState,
    IndexDeltaEntry,
    IndexProjectionOutcome,
)
from brain.v5.query_index_delta_storage import (
    _delta_manifest_path,
    _delta_matches_base,
    _load_delta_manifest,
    _new_delta_for_base,
    _pointer_digest,
    _publish_delta_manifest,
)
from brain.v5.query_index_locking import (
    acquire_canonical_mutation_lease,
    acquire_ranked_lock,
    active_canonical_mutation_lease,
)
from brain.v5.query_index_snapshot import (
    global_index_state_is_fresh,
    load_effective_query_index,
    scoped_index_orientation,
    scoped_index_freshness,
)
from brain.v5.record_envelope import RecordActor, read_envelope_compat
from brain.v5.record_family_registry import record_family_specs
from brain.v5.record_repository import RecordRepository


def reset_query_delta_for_base(
    ws: WorkspacePaths,
    manifest: IndexManifest,
    *,
    lock_held: bool = False,
) -> None:
    """Bind an empty disposable delta to a newly published full base."""

    if manifest.manifest_kind != "query_index_root" or manifest.schema_version < 3:
        return
    delta = _new_delta_for_base(manifest)
    if lock_held:
        _publish_delta_manifest(ws, delta)
        return
    with acquire_ranked_lock(ws, "delta-manifest"):
        _publish_delta_manifest(ws, delta)


def project_record_delta(
    ws: WorkspacePaths,
    record_ref: str,
    *,
    predecessor_content_watermark: str = "",
    predecessor_record_content_hash: str = "",
) -> IndexProjectionOutcome:
    """Project one committed canonical record without rebuilding the full index."""

    active_lease = active_canonical_mutation_lease(ws)
    if active_lease is not None:
        active_lease.assert_active(ws)
        return _project_record_delta_locked(
            ws,
            record_ref,
            predecessor_content_watermark=predecessor_content_watermark,
            predecessor_record_content_hash=predecessor_record_content_hash,
        )
    with acquire_canonical_mutation_lease(ws):
        return _project_record_delta_locked(
            ws,
            record_ref,
            predecessor_content_watermark=predecessor_content_watermark,
            predecessor_record_content_hash=predecessor_record_content_hash,
        )


def repair_query_delta(
    ws: WorkspacePaths,
    families: tuple[str, ...] | list[str],
) -> IndexProjectionOutcome:
    """Rebuild selected-family overlay rows under a strong canonical proof."""

    from brain.v5.query_index_delta_repair import repair_query_delta as repair

    return repair(ws, families)


def compact_query_delta(ws: WorkspacePaths):
    """Absorb the current delta through the full strong rebuild transaction."""

    from brain.v5.query_index import build_query_index

    return build_query_index(ws)


def _project_record_delta_locked(
    ws: WorkspacePaths,
    record_ref: str,
    *,
    predecessor_content_watermark: str = "",
    predecessor_record_content_hash: str = "",
) -> IndexProjectionOutcome:
    root_path = ws.root / "indexes" / "manifest.json"
    if not root_path.exists():
        return IndexProjectionOutcome(status="not_configured")
    base_at_start = load_query_manifest(ws)
    if base_at_start.manifest_kind != "query_index_root" or base_at_start.schema_version < 3:
        return IndexProjectionOutcome(
            status="migration_required",
            diagnostics=("query index root requires a v3 rebuild before delta projection",),
        )
    family = _family_for_ref(record_ref)
    if not family:
        return IndexProjectionOutcome(
            status="dirty",
            dirty_families=("unknown",),
            diagnostics=(f"unsupported record ref for projection: {record_ref}",),
            repair_required=True,
        )
    _run_failpoint("before_delta_row")
    row = _canonical_document_row(ws, family, record_ref)
    row_text = json.dumps(row, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    row_hash = _hash_text(row_text)
    ref_hash = hashlib.sha256(record_ref.encode("utf-8")).hexdigest()
    row_file = f"delta/rows/{ref_hash}.{row_hash}.json"
    row_path = ws.root / "indexes" / Path(row_file)
    if row_path.exists():
        if _hash_text(row_path.read_text(encoding="utf-8")) != row_hash:
            raise IndexIntegrityError(f"content-addressed delta row is corrupt: {record_ref}")
    else:
        write_text_atomic(row_path, row_text)
    _run_failpoint("after_delta_row")
    with acquire_ranked_lock(ws, "delta-manifest"):
        base = load_query_manifest(ws)
        if base.manifest_kind != "query_index_root" or base.schema_version < 3:
            return IndexProjectionOutcome(
                status="migration_required",
                diagnostics=("query index root changed to an unsupported schema",),
            )
        delta = _load_delta_manifest(ws)
        if delta is None or not _delta_matches_base(delta, base):
            delta = _new_delta_for_base(base)
        current_state = current_family_state_token(ws, family)
        expected_predecessor = delta.family_content_watermarks.get(
            family,
            base.family_content_watermarks.get(family, ""),
        )
        dirty = dict(delta.dirty_families)
        diagnostics: list[str] = []
        predecessor_mismatch = bool(
            predecessor_content_watermark
            and predecessor_content_watermark != expected_predecessor
        )
        unproven_standalone = not predecessor_content_watermark
        if (predecessor_mismatch or unproven_standalone) and family not in dirty:
            reason = (
                "canonical predecessor does not match the effective delta lineage"
                if predecessor_mismatch
                else "standalone projection cannot prove canonical predecessor continuity"
            )
            diagnostics.append(reason)
            dirty[family] = DirtyFamilyState(
                family=family,
                reason=reason,
                predecessor_content_watermark=expected_predecessor,
                observed_content_watermark=predecessor_content_watermark,
                diagnostics=(reason,),
            )
        entries = dict(delta.entries)
        existing = entries.get(record_ref)
        record_content_hash = str(row.get("record_content_hash") or "")
        if (
            existing is not None
            and existing.row_hash == row_hash
            and existing.record_content_hash == record_content_hash
        ):
            entry = existing
        else:
            entry = IndexDeltaEntry(
                record_ref=record_ref,
                family=family,
                row_file=row_file,
                row_hash=row_hash,
                record_content_hash=record_content_hash,
                predecessor_content_hash=predecessor_record_content_hash,
            )
        entries[record_ref] = entry
        state_tokens = dict(delta.family_state_tokens)
        state_tokens[family] = current_state
        content_watermarks = dict(delta.family_content_watermarks)
        content_accumulators = dict(delta.family_content_accumulators)
        if family not in dirty:
            prior_accumulator = content_accumulators.get(
                family,
                base.family_content_accumulators.get(family),
            )
            if prior_accumulator is None:
                reason = "effective delta lineage has no family content accumulator"
                diagnostics.append(reason)
                dirty[family] = DirtyFamilyState(
                    family=family,
                    reason=reason,
                    predecessor_content_watermark=expected_predecessor,
                    observed_content_watermark=predecessor_content_watermark,
                    diagnostics=(reason,),
                )
            else:
                updated_accumulator = replace_content_accumulator_pair(
                    prior_accumulator,
                    key=record_ref,
                    previous_value=predecessor_record_content_hash,
                    current_value=record_content_hash,
                )
                content_accumulators[family] = updated_accumulator
                content_watermarks[family] = content_accumulator_watermark(
                    updated_accumulator
                )
        changed = (
            existing != entry
            or state_tokens != delta.family_state_tokens
            or content_watermarks != delta.family_content_watermarks
            or content_accumulators != delta.family_content_accumulators
            or dirty != delta.dirty_families
        )
        generation = delta.generation + (1 if changed else 0)
        if changed:
            successor = replace(
                delta,
                generation=generation,
                entries=entries,
                family_state_tokens=state_tokens,
                family_content_watermarks=content_watermarks,
                family_content_accumulators=content_accumulators,
                dirty_families=dirty,
                predecessor_chain_token=_hash_json(
                    [
                        delta.predecessor_chain_token,
                        generation,
                        record_ref,
                        row_hash,
                        content_watermarks.get(family, expected_predecessor),
                    ]
                ),
                content_hash="",
            )
            _run_failpoint("before_delta_manifest_replace")
            _publish_delta_manifest(ws, successor)
    _run_failpoint("after_delta_manifest")
    dirty_names = tuple(sorted(dirty))
    if dirty_names:
        return IndexProjectionOutcome(
            status="dirty",
            dirty_families=dirty_names,
            diagnostics=tuple(diagnostics)
            or tuple(state.reason for _, state in sorted(dirty.items())),
            repair_required=True,
        )
    return IndexProjectionOutcome(status="projected" if changed else "unchanged")


def mark_query_delta_dirty(
    ws: WorkspacePaths,
    family: str,
    *,
    reason: str,
    predecessor_content_watermark: str = "",
) -> IndexProjectionOutcome:
    """Persist a projection gap without changing canonical truth."""

    active_lease = active_canonical_mutation_lease(ws)
    if active_lease is not None:
        active_lease.assert_active(ws)
        return _mark_query_delta_dirty_locked(
            ws,
            family,
            reason=reason,
            predecessor_content_watermark=predecessor_content_watermark,
        )
    with acquire_canonical_mutation_lease(ws):
        return _mark_query_delta_dirty_locked(
            ws,
            family,
            reason=reason,
            predecessor_content_watermark=predecessor_content_watermark,
        )


def _mark_query_delta_dirty_locked(
    ws: WorkspacePaths,
    family: str,
    *,
    reason: str,
    predecessor_content_watermark: str = "",
) -> IndexProjectionOutcome:
    root_path = ws.root / "indexes" / "manifest.json"
    if not root_path.exists():
        return IndexProjectionOutcome(status="not_configured", diagnostics=(reason,))
    with acquire_ranked_lock(ws, "delta-manifest"):
        base = load_query_manifest(ws)
        if base.manifest_kind != "query_index_root" or base.schema_version < 3:
            return IndexProjectionOutcome(
                status="migration_required",
                diagnostics=(reason, "query index root requires migration"),
            )
        delta = _load_delta_manifest(ws)
        if delta is None or not _delta_matches_base(delta, base):
            delta = _new_delta_for_base(base)
        dirty = dict(delta.dirty_families)
        existing = dirty.get(family)
        diagnostics = tuple(dict.fromkeys([*(existing.diagnostics if existing else ()), reason]))
        observed = ""
        try:
            observed = current_family_content_watermark(ws, family)
        except (KeyError, OSError, ValueError):
            pass
        dirty[family] = DirtyFamilyState(
            family=family,
            reason=existing.reason if existing else reason,
            predecessor_content_watermark=(
                existing.predecessor_content_watermark
                if existing
                else predecessor_content_watermark
            ),
            observed_content_watermark=observed,
            diagnostics=diagnostics,
        )
        successor = replace(
            delta,
            generation=delta.generation + 1,
            dirty_families=dirty,
            predecessor_chain_token=_hash_json(
                [delta.predecessor_chain_token, delta.generation + 1, family, "dirty", reason]
            ),
            content_hash="",
        )
        _publish_delta_manifest(ws, successor)
    return IndexProjectionOutcome(
        status="dirty",
        dirty_families=tuple(sorted(dirty)),
        diagnostics=diagnostics,
        repair_required=True,
    )


def _canonical_document_row(
    ws: WorkspacePaths,
    family: str,
    record_ref: str,
) -> dict[str, Any]:
    repository = RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="migration",
            actor_id="query-index-projector",
            host="query-index",
        ),
    )
    result = repository.read(record_ref)
    if result.frontmatter is None or not result.path:
        detail = result.issue.message if result.issue else result.status
        raise ValueError(f"cannot project canonical record {record_ref}: {detail}")
    spec = record_family_specs()[family]
    path = Path(result.path)
    envelope = read_envelope_compat(result.frontmatter, spec, path, body=result.body)
    return _document_row(ws, spec, result.frontmatter, result.body, envelope, path)


def _family_for_ref(record_ref: str) -> str:
    kind = record_ref.partition(":")[0].replace("-", "_")
    for family, spec in record_family_specs().items():
        if kind in {alias.replace("-", "_") for alias in spec.exact_ref_aliases}:
            return family
    return ""


def _run_failpoint(_name: str) -> None:
    """Named no-op seam used by deterministic interruption tests."""
