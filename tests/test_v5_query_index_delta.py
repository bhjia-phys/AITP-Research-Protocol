from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import hashlib
import json

from brain.v5.models import ClaimRecord, SourceAssetRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import build_query_index, load_query_manifest
from brain.v5.query_index_delta import (
    compact_query_delta,
    load_effective_query_index,
    mark_query_delta_dirty,
    project_record_delta,
    repair_query_delta,
)
from brain.v5.query_index_locking import held_ranked_lock_names
from brain.v5.record_envelope import RecordActor, canonical_record_hash
from brain.v5.record_repository import RecordRepository, WritePolicy
from brain.v5.research_retrieval import ResearchQuery, query_records
from brain.v5.store import write_record


def _claim(claim_id: str, statement: str) -> ClaimRecord:
    return ClaimRecord(
        claim_id=claim_id,
        topic_id="topic-delta",
        statement=statement,
        evidence_profile="formal_derivation",
        confidence_state="candidate",
        active_uncertainty="Independent validation remains open.",
    )


def _repository(ws: WorkspacePaths) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(actor_type="model", actor_id="delta-test", host="pytest"),
    )


def _indexed_workspace(tmp_path) -> tuple[WorkspacePaths, ClaimRecord]:
    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    seed = _claim("claim-delta-seed", "oldspectralneedle71")
    write_record(
        ws.registry_dir("claims") / f"{seed.claim_id}.md",
        seed,
        body="# Seed claim\n",
    )
    build_query_index(ws)
    return ws, seed


def test_repository_create_is_queryable_without_full_rebuild(tmp_path):
    ws, _seed = _indexed_workspace(tmp_path)
    base_generation = load_query_manifest(ws).generation
    created = _claim("claim-delta-created", "zetaquarkprojection83")

    result = _repository(ws).write("claims", created, body="# Created claim\n")
    query = query_records(
        ws,
        ResearchQuery(text="zetaquarkprojection83", families=("claims",)),
    )

    assert result.status == "created"
    assert result.index_projection.status == "projected"
    assert load_query_manifest(ws).generation == base_generation
    assert [item.record_ref for item in query.items] == [f"claim:{created.claim_id}"]
    assert query.coverage.scope_state_fresh is True
    assert query.coverage.scope_content_verified is True
    assert query.coverage.scope_fresh is True
    assert query.coverage.global_fresh is True
    assert query.coverage.dirty_families == ()


def test_repository_revision_replaces_the_effective_delta_row(tmp_path):
    ws, seed = _indexed_workspace(tmp_path)
    repository = _repository(ws)
    current = repository.read(f"claim:{seed.claim_id}")
    assert current.frontmatter is not None
    expected_hash = canonical_record_hash(current.frontmatter, current.body)
    revised = replace(seed, statement="newmodularneedle93")

    result = repository.write(
        "claims",
        revised,
        body="# Revised claim\n",
        policy=WritePolicy(mode="revision", expected_hash=expected_hash),
    )
    replacement = query_records(
        ws,
        ResearchQuery(text="newmodularneedle93", families=("claims",)),
    )
    obsolete = query_records(
        ws,
        ResearchQuery(text="oldspectralneedle71", families=("claims",)),
    )

    assert result.status == "revised"
    assert result.index_projection.status == "projected"
    assert [item.record_ref for item in replacement.items] == [f"claim:{seed.claim_id}"]
    assert obsolete.items == ()
    assert obsolete.coverage.can_claim_no_result is True


def test_out_of_band_write_invalidates_only_its_own_family(tmp_path):
    ws, _seed = _indexed_workspace(tmp_path)
    source = SourceAssetRecord(
        asset_id="source-out-of-band",
        topic_id="topic-delta",
        claim_id="claim-delta-seed",
        asset_type="paper",
        uri="arxiv:2607.00001",
        title="Out-of-band source",
        content_hash="a" * 64,
        hash_algorithm="sha256",
    )
    write_record(
        ws.registry_dir("source_assets") / f"{source.asset_id}.md",
        source,
        body="# Source\n",
    )

    claims = query_records(
        ws,
        ResearchQuery(text="absent-in-claims", families=("claims",)),
    )
    global_query = query_records(ws, ResearchQuery(text="absent-everywhere"))

    assert claims.coverage.scope_fresh is True
    assert claims.coverage.global_fresh is False
    assert claims.coverage.exhaustive is True
    assert claims.coverage.can_claim_no_result is True
    assert global_query.coverage.scope_fresh is False
    assert global_query.coverage.exhaustive is False
    assert global_query.coverage.can_claim_no_result is False


def test_projection_gap_stays_dirty_after_a_later_successful_family_write(
    tmp_path,
    monkeypatch,
):
    import brain.v5.query_index_delta as query_index_delta

    ws, _seed = _indexed_workspace(tmp_path)
    repository = _repository(ws)
    original_failpoint = query_index_delta._run_failpoint

    def fail_before_delta_row(name: str) -> None:
        if name == "before_delta_row":
            raise RuntimeError("injected projection failure")
        original_failpoint(name)

    monkeypatch.setattr(query_index_delta, "_run_failpoint", fail_before_delta_row)
    failed = repository.write(
        "claims",
        _claim("claim-delta-gap", "canonical write with projection gap"),
        body="# Gap claim\n",
    )
    monkeypatch.setattr(query_index_delta, "_run_failpoint", original_failpoint)
    later = repository.write(
        "claims",
        _claim("claim-delta-after-gap", "later projected row"),
        body="# Later claim\n",
    )
    query = query_records(
        ws,
        ResearchQuery(text="later projected row", families=("claims",)),
    )

    assert failed.status == "created"
    assert failed.index_projection.status == "dirty"
    assert failed.index_projection.repair_required is True
    assert failed.index_projection.dirty_families == ("claims",)
    assert later.index_projection.status == "dirty"
    assert later.index_projection.repair_required is True
    assert query.coverage.scope_fresh is False
    assert query.coverage.dirty_families == ("claims",)
    assert query.coverage.exhaustive is False


def test_interruption_after_delta_row_keeps_the_published_snapshot_readable(
    tmp_path,
    monkeypatch,
):
    import brain.v5.query_index_delta as query_index_delta

    ws, _seed = _indexed_workspace(tmp_path)
    repository = _repository(ws)
    original = _claim("claim-interrupted-row", "publishedrowbeforefailure41")
    created = repository.write("claims", original, body="# Original\n")
    before = load_effective_query_index(ws)
    original_failpoint = query_index_delta._run_failpoint

    def fail_after_row(name: str) -> None:
        if name == "after_delta_row":
            raise RuntimeError("injected interruption after row publication")
        original_failpoint(name)

    monkeypatch.setattr(query_index_delta, "_run_failpoint", fail_after_row)
    revised = repository.write(
        "claims",
        replace(original, statement="canonicalrevisionafterfailure42"),
        body="# Revised\n",
        policy=WritePolicy(mode="revision", expected_hash=created.content_hash),
    )
    monkeypatch.setattr(query_index_delta, "_run_failpoint", original_failpoint)

    after = load_effective_query_index(ws)
    effective = {
        row["record_ref"]: row for row in after.documents
    }[f"claim:{original.claim_id}"]
    canonical = repository.read(f"claim:{original.claim_id}")

    assert revised.status == "revised"
    assert revised.index_projection.status == "dirty"
    assert after.dirty_families == ("claims",)
    assert effective["record_content_hash"] == {
        row["record_ref"]: row for row in before.documents
    }[f"claim:{original.claim_id}"]["record_content_hash"]
    assert canonical.record.statement == "canonicalrevisionafterfailure42"


def test_concurrent_standalone_projectors_serialize_and_preserve_both_entries(tmp_path):
    ws, _seed = _indexed_workspace(tmp_path)
    records = (
        _claim("claim-concurrent-a", "concurrentprojectionalpha51"),
        _claim("claim-concurrent-b", "concurrentprojectionbeta52"),
    )
    for record in records:
        write_record(
            ws.registry_dir("claims") / f"{record.claim_id}.md",
            record,
            body="# Out-of-band concurrent claim\n",
        )
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(project_record_delta, ws, f"claim:{record.claim_id}")
            for record in records
        ]
    results = [future.result() for future in futures]
    snapshot = load_effective_query_index(ws)

    assert [result.status for result in results] == ["dirty", "dirty"]
    assert snapshot.dirty_families == ("claims",)
    assert {f"claim:{record.claim_id}" for record in records}.issubset(snapshot.record_refs)


def test_standalone_projector_acquires_canonical_mutation_lease(tmp_path, monkeypatch):
    import brain.v5.query_index_delta as query_index_delta

    ws, _seed = _indexed_workspace(tmp_path)
    record = _claim("claim-standalone-lock", "standaloneprojectorlock61")
    write_record(
        ws.registry_dir("claims") / f"{record.claim_id}.md",
        record,
        body="# Standalone\n",
    )
    observed: list[tuple[str, ...]] = []
    original_failpoint = query_index_delta._run_failpoint

    def observe_before_row(name: str) -> None:
        if name == "before_delta_row":
            observed.append(held_ranked_lock_names())
        original_failpoint(name)

    monkeypatch.setattr(query_index_delta, "_run_failpoint", observe_before_row)
    outcome = project_record_delta(ws, f"claim:{record.claim_id}")

    assert outcome.status == "dirty"
    assert observed == [("canonical-mutation",)]


def test_corrupt_delta_returns_scoped_stale_diagnostics_instead_of_raising(tmp_path):
    ws, _seed = _indexed_workspace(tmp_path)
    record = _claim("claim-corrupt-delta", "corruptdeltaneedle71")
    created = _repository(ws).write("claims", record, body="# Corrupt target\n")
    manifest_path = ws.root / "indexes" / "delta" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row_path = ws.root / "indexes" / manifest["entries"][created.record_ref]["row_file"]
    row_path.write_text('{"tampered": true}\n', encoding="utf-8")

    result = query_records(
        ws,
        ResearchQuery(text="corruptdeltaneedle71", families=("claims",)),
    )

    assert result.items == ()
    assert result.index_status == "stale"
    assert result.coverage.scope_fresh is False
    assert result.coverage.exhaustive is False
    assert result.coverage.can_claim_no_result is False
    assert any("delta row hash mismatch" in error for error in result.coverage.read_errors)


def test_legacy_root_is_readable_but_requires_rebuild_before_projection(tmp_path):
    ws, _seed = _indexed_workspace(tmp_path)
    root_path = ws.root / "indexes" / "manifest.json"
    payload = json.loads(root_path.read_text(encoding="utf-8"))
    index_dir = root_path.parent
    legacy_components = {
        "document_file": "record_documents.json",
        "lexical_file": "lexical_index.json",
        "issues_file": "issues.json",
    }
    for field_name, legacy_name in legacy_components.items():
        source = index_dir / payload[field_name]
        (index_dir / legacy_name).write_bytes(source.read_bytes())
        payload[field_name] = legacy_name
    for key in (
        "manifest_kind",
        "schema_version",
        "base_content_hash",
        "family_state_tokens",
        "family_content_watermarks",
        "family_content_accumulators",
        "issues_file",
        "generation_manifest_file",
    ):
        payload.pop(key, None)
    legacy_basis = {
        "canonical_watermark": payload["canonical_watermark"],
        "document_hash": payload["document_hash"],
        "lexical_hash": payload["lexical_hash"],
        "issues_hash": payload["issues_hash"],
        "index_schema_version": payload["index_schema_version"],
    }
    raw = json.dumps(
        legacy_basis,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    payload["content_hash"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    root_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    record = _claim("claim-legacy-root", "legacyrootprojection81")

    created = _repository(ws).write("claims", record, body="# Legacy root write\n")

    assert created.status == "created"
    assert created.index_projection.status == "migration_required"
    assert load_effective_query_index(ws).manifest.manifest_kind == ""

    rebuilt = build_query_index(ws)
    result = query_records(
        ws,
        ResearchQuery(text="legacyrootprojection81", families=("claims",)),
    )
    assert rebuilt.manifest.manifest_kind == "query_index_root"
    assert result.coverage.scope_fresh is True
    assert [item.record_ref for item in result.items] == [created.record_ref]


def test_full_rebuild_absorbs_clean_delta_without_duplicate_rows(tmp_path):
    ws, _seed = _indexed_workspace(tmp_path)
    record = _claim("claim-rebuild-delta", "rebuildabsorbsdelta91")
    created = _repository(ws).write("claims", record, body="# Delta before rebuild\n")
    before = load_effective_query_index(ws)

    report = build_query_index(ws)
    after = load_effective_query_index(ws)
    delta_manifest = json.loads(
        (ws.root / "indexes" / "delta" / "manifest.json").read_text(encoding="utf-8")
    )

    assert created.record_ref in before.record_refs
    assert after.record_refs.count(created.record_ref) == 1
    assert delta_manifest["base_generation"] == report.manifest.generation
    assert delta_manifest["entries"] == {}
    assert delta_manifest["dirty_families"] == {}


def test_idempotent_repository_write_does_not_advance_or_duplicate_delta(tmp_path):
    ws, _seed = _indexed_workspace(tmp_path)
    record = _claim("claim-idempotent-delta", "idempotentdeltarow101")
    repository = _repository(ws)
    first = repository.write("claims", record, body="# Idempotent\n")
    manifest_path = ws.root / "indexes" / "delta" / "manifest.json"
    before = json.loads(manifest_path.read_text(encoding="utf-8"))

    second = repository.write("claims", record, body="# Idempotent\n")
    after = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert first.index_projection.status == "projected"
    assert second.status == "unchanged"
    assert second.index_projection.status == "unchanged"
    assert after["generation"] == before["generation"]
    assert list(after["entries"]) == [first.record_ref]


def test_repository_projection_updates_content_watermark_without_family_rescan(
    tmp_path,
    monkeypatch,
):
    import brain.v5.query_index as query_index
    import brain.v5.query_index_delta as query_index_delta

    ws, _seed = _indexed_workspace(tmp_path)
    original_query_scan = query_index.current_family_content_watermark
    original_delta_scan = query_index_delta.current_family_content_watermark

    def reject_family_scan(*_args, **_kwargs):
        raise AssertionError("normal repository projection scanned canonical family content")

    monkeypatch.setattr(query_index, "current_family_content_watermark", reject_family_scan)
    monkeypatch.setattr(
        query_index_delta,
        "current_family_content_watermark",
        reject_family_scan,
    )
    created = _repository(ws).write(
        "claims",
        _claim("claim-no-rescan", "incrementalcontentaccumulator161"),
        body="# Incremental accumulator\n",
    )
    monkeypatch.setattr(
        query_index,
        "current_family_content_watermark",
        original_query_scan,
    )
    monkeypatch.setattr(
        query_index_delta,
        "current_family_content_watermark",
        original_delta_scan,
    )
    snapshot = load_effective_query_index(ws)

    assert created.index_projection.status == "projected"
    assert snapshot.family_content_watermarks["claims"] == original_query_scan(ws, "claims")


def test_family_repair_rebuilds_complete_view_and_clears_only_verified_dirty_state(
    tmp_path,
):
    ws, _seed = _indexed_workspace(tmp_path)
    gap = _claim("claim-repair-gap", "repairrecoversthiscanonicalrow111")
    write_record(
        ws.registry_dir("claims") / f"{gap.claim_id}.md",
        gap,
        body="# Repair gap\n",
    )
    dirty = mark_query_delta_dirty(
        ws,
        "claims",
        reason="injected missing projection",
    )

    repaired = repair_query_delta(ws, ("claims",))
    snapshot = load_effective_query_index(ws)
    result = query_records(
        ws,
        ResearchQuery(text="repairrecoversthiscanonicalrow111", families=("claims",)),
    )
    delta = json.loads(
        (ws.root / "indexes" / "delta" / "manifest.json").read_text(encoding="utf-8")
    )

    assert dirty.status == "dirty"
    assert repaired.status == "projected"
    assert repaired.repair_required is False
    assert snapshot.dirty_families == ()
    assert [item.record_ref for item in result.items] == [f"claim:{gap.claim_id}"]
    assert result.coverage.scope_fresh is True
    assert result.coverage.exhaustive is True
    assert delta["repaired_families"]["claims"] == snapshot.family_content_watermarks["claims"]
    assert all(
        entry["predecessor_content_hash"] == ""
        for entry in delta["entries"].values()
        if entry["family"] == "claims"
    )


def test_family_repair_complete_view_removes_deleted_base_rows(tmp_path):
    ws, seed = _indexed_workspace(tmp_path)
    (ws.registry_dir("claims") / f"{seed.claim_id}.md").unlink()
    mark_query_delta_dirty(ws, "claims", reason="out-of-band canonical deletion")

    repaired = repair_query_delta(ws, ("claims",))
    snapshot = load_effective_query_index(ws)

    assert repaired.status == "projected"
    assert f"claim:{seed.claim_id}" not in snapshot.record_refs
    assert snapshot.dirty_families == ()


def test_compaction_clears_dirty_state_only_through_strong_full_rebuild(tmp_path):
    ws, _seed = _indexed_workspace(tmp_path)
    gap = _claim("claim-compact-gap", "compactionrecoverscanonicalrow121")
    write_record(
        ws.registry_dir("claims") / f"{gap.claim_id}.md",
        gap,
        body="# Compact gap\n",
    )
    mark_query_delta_dirty(ws, "claims", reason="injected compaction gap")
    generation_before = load_query_manifest(ws).generation

    report = compact_query_delta(ws)
    snapshot = load_effective_query_index(ws)
    delta = json.loads(
        (ws.root / "indexes" / "delta" / "manifest.json").read_text(encoding="utf-8")
    )

    assert report.manifest.generation == generation_before + 1
    assert snapshot.dirty_families == ()
    assert f"claim:{gap.claim_id}" in snapshot.record_refs
    assert delta["entries"] == {}
    assert delta["dirty_families"] == {}


def test_single_family_fallback_is_explicit_bounded_and_canonical(tmp_path):
    ws, _seed = _indexed_workspace(tmp_path)
    gap = _claim("claim-fallback-gap", "strictfamilyfallbackneedle131")
    write_record(
        ws.registry_dir("claims") / f"{gap.claim_id}.md",
        gap,
        body="# Fallback gap\n",
    )
    mark_query_delta_dirty(ws, "claims", reason="injected fallback gap")

    default = query_records(
        ws,
        ResearchQuery(text="strictfamilyfallbackneedle131", families=("claims",)),
    )
    fallback = query_records(
        ws,
        ResearchQuery(
            text="strictfamilyfallbackneedle131",
            families=("claims",),
            allow_family_fallback=True,
            fallback_max_records=10,
        ),
    )

    assert default.items == ()
    assert default.coverage.fallback_used is False
    assert default.coverage.scope_fresh is False
    assert [item.record_ref for item in fallback.items] == [f"claim:{gap.claim_id}"]
    assert fallback.index_status == "fresh"
    assert fallback.coverage.fallback_used is True
    assert fallback.coverage.scope_state_fresh is True
    assert fallback.coverage.scope_content_verified is True
    assert fallback.coverage.scope_fresh is True
    assert fallback.coverage.exhaustive is True
    assert fallback.coverage.global_fresh is False
    assert fallback.coverage.dirty_families == ("claims",)


def test_family_fallback_refuses_unscoped_or_over_bound_scans(tmp_path):
    ws, _seed = _indexed_workspace(tmp_path)
    gap = _claim("claim-fallback-bound", "fallbackboundneedle141")
    write_record(
        ws.registry_dir("claims") / f"{gap.claim_id}.md",
        gap,
        body="# Bound\n",
    )
    mark_query_delta_dirty(ws, "claims", reason="injected fallback bound gap")

    over_bound = query_records(
        ws,
        ResearchQuery(
            text="fallbackboundneedle141",
            families=("claims",),
            allow_family_fallback=True,
            fallback_max_records=1,
        ),
    )
    unscoped = query_records(
        ws,
        ResearchQuery(
            text="fallbackboundneedle141",
            allow_family_fallback=True,
            fallback_max_records=10,
        ),
    )

    assert over_bound.items == ()
    assert over_bound.coverage.fallback_used is False
    assert over_bound.coverage.scope_fresh is False
    assert any("bound" in error for error in over_bound.coverage.read_errors)
    assert unscoped.items == ()
    assert unscoped.coverage.fallback_used is False
    assert unscoped.coverage.scope_fresh is False
