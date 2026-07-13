"""Race-safe full-family repair for the disposable query-index delta."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import brain.v5.query_index_delta as delta_store
from brain.v5.markdown import write_text_atomic
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import (
    IndexIntegrityError,
    IndexSnapshotChangedError,
    _hash_json,
    _hash_text,
    current_family_content_watermark,
    load_query_manifest,
)
from brain.v5.query_index_delta_contracts import (
    DirtyFamilyState,
    IndexDeltaEntry,
    IndexProjectionOutcome,
)
from brain.v5.query_index_family_scan import CanonicalFamilyScan, scan_canonical_family
from brain.v5.query_index_locking import (
    acquire_canonical_mutation_lease,
    acquire_ranked_lock,
    active_canonical_mutation_lease,
)
from brain.v5.record_family_registry import record_family_specs


def repair_query_delta(
    ws: WorkspacePaths,
    families: tuple[str, ...] | list[str],
) -> IndexProjectionOutcome:
    """Replace selected-family overlay rows after a strong canonical proof."""

    requested = tuple(sorted({str(family).strip() for family in families if str(family).strip()}))
    unknown = tuple(family for family in requested if family not in record_family_specs())
    if not requested:
        raise ValueError("repair requires at least one canonical family")
    if unknown:
        raise ValueError("unknown canonical families: " + ", ".join(unknown))
    active_lease = active_canonical_mutation_lease(ws)
    if active_lease is not None:
        active_lease.assert_active(ws)
        return _repair_query_delta_locked(ws, requested)
    with acquire_canonical_mutation_lease(ws):
        return _repair_query_delta_locked(ws, requested)


def _repair_query_delta_locked(
    ws: WorkspacePaths,
    requested: tuple[str, ...],
) -> IndexProjectionOutcome:
    root_path = ws.root / "indexes" / "manifest.json"
    if not root_path.exists():
        return IndexProjectionOutcome(status="not_configured")
    with acquire_ranked_lock(ws, "delta-manifest"):
        base_at_start = load_query_manifest(ws)
        if base_at_start.manifest_kind != "query_index_root" or base_at_start.schema_version < 3:
            return IndexProjectionOutcome(
                status="migration_required",
                diagnostics=("query index root requires a v3 rebuild before family repair",),
            )
        delta_at_start = delta_store._load_delta_manifest(ws)
        delta_existed = delta_at_start is not None
        if delta_at_start is None:
            delta_at_start = delta_store._new_delta_for_base(base_at_start)
        elif not delta_store._delta_matches_base(delta_at_start, base_at_start):
            return IndexProjectionOutcome(
                status="dirty",
                dirty_families=requested,
                diagnostics=("delta base lineage mismatch requires a full rebuild",),
                repair_required=True,
            )

    canonical_before = {
        family: current_family_content_watermark(ws, family) for family in requested
    }
    delta_store._run_failpoint("after_repair_canonical_before")
    scans = {family: scan_canonical_family(ws, family) for family in requested}
    canonical_after = {
        family: current_family_content_watermark(ws, family) for family in requested
    }
    changed = tuple(
        family
        for family in requested
        if not (
            canonical_before[family]
            == scans[family].content_watermark
            == canonical_after[family]
        )
    )
    if changed:
        for family in changed:
            delta_store.mark_query_delta_dirty(
                ws,
                family,
                reason="strong canonical content changed during family repair",
                predecessor_content_watermark=canonical_before[family],
            )
        return IndexProjectionOutcome(
            status="dirty",
            dirty_families=changed,
            diagnostics=(
                "strong canonical content changed during family repair: "
                + ", ".join(changed),
            ),
            repair_required=True,
        )

    repaired_entries: dict[str, IndexDeltaEntry] = {}
    for family, scan in scans.items():
        repaired_entries.update(_write_repair_rows(ws, scan))

    with acquire_ranked_lock(ws, "delta-manifest"):
        base = load_query_manifest(ws)
        current = delta_store._load_delta_manifest(ws)
        if not _repair_cas_matches(
            base_at_start,
            delta_at_start,
            delta_existed=delta_existed,
            current_base=base,
            current_delta=current,
        ):
            raise IndexSnapshotChangedError(
                "query delta changed before family repair publication"
            )
        if current is None:
            current = delta_store._new_delta_for_base(base)
        entries = {
            record_ref: entry
            for record_ref, entry in current.entries.items()
            if entry.family not in requested
        }
        entries.update(repaired_entries)
        repaired_families = dict(current.repaired_families)
        state_tokens = dict(current.family_state_tokens)
        content_watermarks = dict(current.family_content_watermarks)
        content_accumulators = dict(current.family_content_accumulators)
        malformed_counts = dict(current.family_malformed_counts)
        dirty = dict(current.dirty_families)
        for family, scan in scans.items():
            repaired_families[family] = scan.content_watermark
            state_tokens[family] = scan.state_token
            content_watermarks[family] = scan.content_watermark
            content_accumulators[family] = scan.content_accumulator
            malformed_counts[family] = scan.malformed_count
            dirty.pop(family, None)
        generation = current.generation + 1
        successor = replace(
            current,
            generation=generation,
            entries=entries,
            repaired_families=repaired_families,
            family_state_tokens=state_tokens,
            family_content_watermarks=content_watermarks,
            family_content_accumulators=content_accumulators,
            family_malformed_counts=malformed_counts,
            dirty_families=dirty,
            predecessor_chain_token=_hash_json(
                [
                    current.predecessor_chain_token,
                    generation,
                    "repair",
                    [[family, scans[family].content_watermark] for family in requested],
                ]
            ),
            content_hash="",
        )
        delta_store._run_failpoint("before_repair_manifest_replace")
        delta_store._publish_delta_manifest(ws, successor)
    remaining_dirty = tuple(sorted(dirty))
    if remaining_dirty:
        return IndexProjectionOutcome(
            status="dirty",
            dirty_families=remaining_dirty,
            diagnostics=("selected families repaired; other dirty families remain",),
            repair_required=True,
        )
    return IndexProjectionOutcome(status="projected")


def _write_repair_rows(
    ws: WorkspacePaths,
    scan: CanonicalFamilyScan,
) -> dict[str, IndexDeltaEntry]:
    entries: dict[str, IndexDeltaEntry] = {}
    for row in scan.documents:
        record_ref = str(row["record_ref"])
        row_text = json.dumps(row, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        row_hash = _hash_text(row_text)
        ref_hash = hashlib.sha256(record_ref.encode("utf-8")).hexdigest()
        row_file = f"delta/rows/{ref_hash}.{row_hash}.json"
        row_path = ws.root / "indexes" / Path(row_file)
        if row_path.exists():
            if _hash_text(row_path.read_text(encoding="utf-8")) != row_hash:
                raise IndexIntegrityError(
                    f"content-addressed repair row is corrupt: {record_ref}"
                )
        else:
            write_text_atomic(row_path, row_text)
        entries[record_ref] = IndexDeltaEntry(
            record_ref=record_ref,
            family=scan.family,
            row_file=row_file,
            row_hash=row_hash,
            record_content_hash=str(row.get("record_content_hash") or ""),
        )
    return entries


def _repair_cas_matches(
    base_at_start,
    delta_at_start,
    *,
    delta_existed: bool,
    current_base,
    current_delta,
) -> bool:
    if (
        current_base.generation != base_at_start.generation
        or (current_base.base_content_hash or current_base.content_hash)
        != (base_at_start.base_content_hash or base_at_start.content_hash)
    ):
        return False
    if not delta_existed:
        return current_delta is None
    if current_delta is None:
        return False
    return (
        current_delta.generation == delta_at_start.generation
        and current_delta.content_hash == delta_at_start.content_hash
    )
