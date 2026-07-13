"""Coherent base-plus-delta reads and strong selected-family freshness."""

from __future__ import annotations

import json
import threading
from collections import OrderedDict
from pathlib import Path
from time import monotonic
from typing import Iterable

from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import (
    IndexIntegrityError,
    IndexManifest,
    IndexSnapshotChangedError,
    load_query_index,
)
from brain.v5.query_index_delta_contracts import (
    EffectiveIndexSnapshot,
    ScopedIndexFreshness,
)
from brain.v5.query_index_delta_storage import (
    _delta_manifest_path,
    _delta_matches_base,
    _load_delta_manifest,
    _pointer_digest,
)
from brain.v5.query_index_documents import _hash_text, _lexical_index, _project_tool_run_supersession
from brain.v5.query_index_locking import (
    acquire_canonical_mutation_lease,
    active_canonical_mutation_lease,
)
from brain.v5.record_family_registry import record_family_specs
from brain.v5.record_repository import record_family_paths


_ORIENTATION_CACHE_TTL_SECONDS = 30.0
_ORIENTATION_CACHE_LIMIT = 8
_orientation_cache_guard = threading.Lock()
_orientation_cache: OrderedDict[
    tuple[str, str, str],
    tuple[float, EffectiveIndexSnapshot],
] = OrderedDict()


def load_effective_query_index(
    ws: WorkspacePaths,
    *,
    allow_cached: bool = False,
) -> EffectiveIndexSnapshot:
    """Load one coherent base-plus-delta snapshot with bounded retries."""

    root_path = ws.root / "indexes" / "manifest.json"
    delta_path = _delta_manifest_path(ws)
    last_error: Exception | None = None
    for _attempt in range(3):
        root_before = _pointer_digest(root_path)
        delta_before = _pointer_digest(delta_path)
        cache_key = (str(ws.root.resolve()), root_before, delta_before)
        if allow_cached:
            cached = _cached_orientation_snapshot(cache_key)
            if cached is not None:
                _run_failpoint("before_snapshot_recheck")
                if (
                    root_before == _pointer_digest(root_path)
                    and delta_before == _pointer_digest(delta_path)
                ):
                    return cached
        try:
            snapshot = _load_effective_query_index_once(ws)
            _run_failpoint("before_snapshot_recheck")
        except (
            IndexIntegrityError,
            IndexSnapshotChangedError,
            OSError,
            ValueError,
            TypeError,
            KeyError,
            json.JSONDecodeError,
        ) as exc:
            last_error = exc
            if (
                root_before != _pointer_digest(root_path)
                or delta_before != _pointer_digest(delta_path)
            ):
                continue
            raise
        if (
            root_before == _pointer_digest(root_path)
            and delta_before == _pointer_digest(delta_path)
        ):
            if allow_cached:
                _store_orientation_snapshot(cache_key, snapshot)
            return snapshot
        last_error = IndexSnapshotChangedError(
            "query index root or delta changed while a snapshot was read"
        )
    raise IndexSnapshotChangedError(
        "query index snapshot changed during bounded read retries"
    ) from last_error


def _load_effective_query_index_once(ws: WorkspacePaths) -> EffectiveIndexSnapshot:
    base = load_query_index(ws)
    _run_failpoint("after_base_snapshot_read")
    family_state_tokens = dict(base.manifest.family_state_tokens)
    family_content_watermarks = dict(base.manifest.family_content_watermarks)
    family_content_accumulators = dict(base.manifest.family_content_accumulators)
    malformed_family_counts = dict(base.manifest.malformed_family_counts)
    if base.manifest.manifest_kind != "query_index_root" or base.manifest.schema_version < 2:
        return EffectiveIndexSnapshot(
            manifest=base.manifest,
            documents=base.documents,
            lexical_terms=base.lexical_terms,
            record_refs=base.record_refs,
            family_state_tokens=family_state_tokens,
            family_content_watermarks=family_content_watermarks,
            family_content_accumulators=family_content_accumulators,
            malformed_family_counts=malformed_family_counts,
        )
    delta = _load_delta_manifest(ws)
    if delta is None:
        return EffectiveIndexSnapshot(
            manifest=base.manifest,
            documents=base.documents,
            lexical_terms=base.lexical_terms,
            record_refs=base.record_refs,
            family_state_tokens=family_state_tokens,
            family_content_watermarks=family_content_watermarks,
            family_content_accumulators=family_content_accumulators,
            malformed_family_counts=malformed_family_counts,
        )
    if not _delta_matches_base(delta, base.manifest):
        raise IndexIntegrityError("delta base lineage does not match query index root")
    repaired_families = set(delta.repaired_families)
    documents_by_ref = {
        row["record_ref"]: dict(row)
        for row in base.documents
        if row.get("family") not in repaired_families
    }
    for record_ref, entry in sorted(delta.entries.items()):
        row_path = ws.root / "indexes" / Path(entry.row_file)
        row_text = row_path.read_text(encoding="utf-8")
        if _hash_text(row_text) != entry.row_hash:
            raise IndexIntegrityError(f"delta row hash mismatch: {record_ref}")
        row = json.loads(row_text)
        if row.get("record_ref") != record_ref:
            raise IndexIntegrityError(f"delta row ref mismatch: {record_ref}")
        documents_by_ref[record_ref] = row
    documents = [dict(row) for _, row in sorted(documents_by_ref.items())]
    _project_tool_run_supersession(documents)
    for doc_id, document in enumerate(documents):
        document["doc_id"] = doc_id
    lexical = _lexical_index(documents)
    family_state_tokens.update(delta.family_state_tokens)
    family_content_watermarks.update(delta.family_content_watermarks)
    family_content_accumulators.update(delta.family_content_accumulators)
    malformed_family_counts.update(delta.family_malformed_counts)
    return EffectiveIndexSnapshot(
        manifest=base.manifest,
        documents=tuple(documents),
        lexical_terms={term: tuple(postings) for term, postings in lexical.items()},
        record_refs=tuple(row["record_ref"] for row in documents),
        family_state_tokens=family_state_tokens,
        family_content_watermarks=family_content_watermarks,
        family_content_accumulators=family_content_accumulators,
        malformed_family_counts=malformed_family_counts,
        dirty_families=tuple(sorted(delta.dirty_families)),
        delta_generation=delta.generation,
    )


def scoped_index_freshness(
    ws: WorkspacePaths,
    snapshot: EffectiveIndexSnapshot,
    families: Iterable[str],
) -> ScopedIndexFreshness:
    active_lease = active_canonical_mutation_lease(ws)
    if active_lease is not None:
        active_lease.assert_active(ws)
        return _scoped_index_freshness_locked(ws, snapshot, families)
    with acquire_canonical_mutation_lease(ws):
        return _scoped_index_freshness_locked(ws, snapshot, families)


def scoped_index_orientation(
    ws: WorkspacePaths,
    snapshot: EffectiveIndexSnapshot,
    families: Iterable[str],
) -> ScopedIndexFreshness:
    """Check cheap selected-family state without authorizing exhaustive claims."""

    active_lease = active_canonical_mutation_lease(ws)
    if active_lease is not None:
        active_lease.assert_active(ws)
        return _scoped_index_orientation_locked(ws, snapshot, families)
    with acquire_canonical_mutation_lease(ws):
        return _scoped_index_orientation_locked(ws, snapshot, families)


def _scoped_index_orientation_locked(
    ws: WorkspacePaths,
    snapshot: EffectiveIndexSnapshot,
    families: Iterable[str],
) -> ScopedIndexFreshness:
    specs = record_family_specs()
    requested = tuple(sorted({family for family in families if family in specs}))
    checked = requested or tuple(sorted(specs))
    dirty = set(snapshot.dirty_families)
    diagnostics = list(snapshot.read_errors)
    checked_paths: list[str] = []
    state_results: list[bool] = []
    for family in checked:
        state_snapshot = _current_family_state_snapshot(ws, family)
        checked_paths.extend(state_snapshot.checked_paths)
        expected = snapshot.family_state_tokens.get(family, "")
        state_results.append(bool(expected) and state_snapshot.token == expected)
    scope_state_fresh = all(state_results)
    dirty_in_scope = dirty.intersection(checked)
    scope_fresh = scope_state_fresh and not dirty_in_scope and not snapshot.read_errors
    if not scope_state_fresh:
        diagnostics.append("selected family state token mismatch")
    if dirty_in_scope:
        diagnostics.append("dirty families require repair: " + ", ".join(sorted(dirty_in_scope)))
    return ScopedIndexFreshness(
        checked_families=checked,
        scope_state_fresh=scope_state_fresh,
        scope_content_verified=False,
        scope_fresh=scope_fresh,
        global_fresh=scope_fresh and len(checked) == len(specs),
        dirty_families=tuple(sorted(dirty)),
        checked_paths=tuple(sorted(checked_paths)),
        diagnostics=tuple(dict.fromkeys(diagnostics)),
    )


def _scoped_index_freshness_locked(
    ws: WorkspacePaths,
    snapshot: EffectiveIndexSnapshot,
    families: Iterable[str],
) -> ScopedIndexFreshness:
    specs = record_family_specs()
    requested = tuple(sorted({family for family in families if family in specs}))
    checked = requested or tuple(sorted(specs))
    dirty = set(snapshot.dirty_families)
    diagnostics = list(snapshot.read_errors)
    checked_paths: list[str] = []
    state_results: dict[str, bool] = {}
    for family in sorted(specs):
        current = _current_family_state_token(ws, family)
        expected = snapshot.family_state_tokens.get(family, "")
        state_results[family] = bool(expected) and current == expected
    scope_state_fresh = all(state_results.get(family, False) for family in checked)
    global_fresh = all(state_results.values()) and not dirty
    content_results: list[bool] = []
    for family in checked:
        spec = specs[family]
        paths, _storage_exists = record_family_paths(ws, spec)
        checked_paths.extend(path.relative_to(ws.root).as_posix() for path in paths)
        canonical_before = _current_family_content_watermark(ws, family)
        canonical_after = _current_family_content_watermark(ws, family)
        expected = snapshot.family_content_watermarks.get(family, "")
        matches = bool(expected) and expected == canonical_before == canonical_after
        content_results.append(matches)
        if not matches:
            diagnostics.append(f"family content watermark mismatch: {family}")
    scope_content_verified = all(content_results)
    dirty_in_scope = dirty.intersection(checked)
    scope_fresh = scope_state_fresh and scope_content_verified and not dirty_in_scope
    if not scope_state_fresh:
        diagnostics.append("selected family state token mismatch")
    if dirty_in_scope:
        diagnostics.append("dirty families require repair: " + ", ".join(sorted(dirty_in_scope)))
    return ScopedIndexFreshness(
        checked_families=checked,
        scope_state_fresh=scope_state_fresh,
        scope_content_verified=scope_content_verified,
        scope_fresh=scope_fresh,
        global_fresh=global_fresh,
        dirty_families=tuple(sorted(dirty)),
        checked_paths=tuple(sorted(checked_paths)),
        diagnostics=tuple(dict.fromkeys(diagnostics)),
    )


def global_index_state_is_fresh(ws: WorkspacePaths, manifest: IndexManifest) -> bool:
    try:
        snapshot = load_effective_query_index(ws)
    except (OSError, ValueError, json.JSONDecodeError, IndexIntegrityError):
        return False
    if snapshot.manifest.generation != manifest.generation or snapshot.dirty_families:
        return False
    return all(
        _current_family_state_token(ws, family) == snapshot.family_state_tokens.get(family, "")
        for family in record_family_specs()
    )


def _run_failpoint(name: str) -> None:
    import brain.v5.query_index_delta as facade

    facade._run_failpoint(name)


def _current_family_state_token(ws: WorkspacePaths, family: str) -> str:
    import brain.v5.query_index_delta as facade

    return facade.current_family_state_token(ws, family)


def _current_family_content_watermark(ws: WorkspacePaths, family: str) -> str:
    import brain.v5.query_index_delta as facade

    return facade.current_family_content_watermark(ws, family)


def _current_family_state_snapshot(ws: WorkspacePaths, family: str):
    import brain.v5.query_index_delta as facade

    return facade.current_family_state_snapshot(ws, family)


def _cached_orientation_snapshot(
    key: tuple[str, str, str],
) -> EffectiveIndexSnapshot | None:
    now = monotonic()
    with _orientation_cache_guard:
        entry = _orientation_cache.get(key)
        if entry is None:
            return None
        expires_at, snapshot = entry
        if expires_at <= now:
            _orientation_cache.pop(key, None)
            return None
        _orientation_cache.move_to_end(key)
        return snapshot


def _store_orientation_snapshot(
    key: tuple[str, str, str],
    snapshot: EffectiveIndexSnapshot,
) -> None:
    with _orientation_cache_guard:
        _orientation_cache[key] = (
            monotonic() + _ORIENTATION_CACHE_TTL_SECONDS,
            snapshot,
        )
        _orientation_cache.move_to_end(key)
        while len(_orientation_cache) > _ORIENTATION_CACHE_LIMIT:
            _orientation_cache.popitem(last=False)
