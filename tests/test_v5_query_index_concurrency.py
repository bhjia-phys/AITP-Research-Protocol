from __future__ import annotations

import multiprocessing
import os
import threading
from pathlib import Path

import pytest

from brain.v5.models import ClaimRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import (
    IndexSnapshotChangedError,
    build_query_index,
    canonical_state_token,
    load_query_index,
)
from brain.v5.query_index_delta import load_effective_query_index
from brain.v5.query_index_delta_contracts import IndexProjectionOutcome
from brain.v5.query_index_locking import (
    LockOwnershipError,
    LockOrderError,
    LockReentrancyError,
    acquire_canonical_mutation_lease,
    acquire_index_build_lease,
    acquire_ranked_lock,
    held_ranked_lock_names,
    _windows_comparison_path,
)
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.research_retrieval import ResearchQuery, query_records
from brain.v5.store import write_record


def _hold_process_lock(base: str, connection) -> None:
    ws = WorkspacePaths(Path(base))
    ws.ensure_layout()
    with acquire_ranked_lock(ws, "canonical-mutation", timeout_seconds=5):
        connection.send("acquired")
        connection.recv()


def _claim(claim_id: str, statement: str) -> ClaimRecord:
    return ClaimRecord(
        claim_id=claim_id,
        topic_id="topic-concurrency",
        statement=statement,
        evidence_profile="formal_derivation",
        confidence_state="candidate",
        active_uncertainty="Validation remains open.",
    )


def _repository(ws: WorkspacePaths) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="model",
            actor_id="query-index-concurrency-test",
            host="pytest",
        ),
    )


def test_ranked_lock_rejects_inversion(tmp_path):
    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()

    with acquire_ranked_lock(ws, "delta-manifest"):
        with pytest.raises(LockOrderError, match="lock order"):
            with acquire_ranked_lock(ws, "canonical-mutation"):
                pass


def test_ranked_lock_rejects_same_lock_reentrancy(tmp_path):
    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()

    with acquire_ranked_lock(ws, "canonical-mutation"):
        with pytest.raises(LockReentrancyError, match="reentrant"):
            with acquire_ranked_lock(ws, "canonical-mutation"):
                pass


@pytest.mark.skipif(os.name != "nt", reason="Windows extended path contract")
def test_windows_lock_containment_normalizes_extended_path_prefix():
    root = _windows_comparison_path(Path(r"C:\workspace\.aitp\runtime\locks"))
    drive_candidate = _windows_comparison_path(
        Path(r"\\?\C:\workspace\.aitp\runtime\locks\query-index\mutation.lock")
    )
    unc_root = _windows_comparison_path(Path(r"\\server\share\.aitp\runtime\locks"))
    unc_candidate = _windows_comparison_path(
        Path(r"\\?\UNC\server\share\.aitp\runtime\locks\query-index\mutation.lock")
    )

    assert drive_candidate.relative_to(root)
    assert unc_candidate.relative_to(unc_root)
    assert drive_candidate == root / "query-index" / "mutation.lock"
    assert unc_candidate == unc_root / "query-index" / "mutation.lock"


def test_kernel_releases_lock_when_owner_process_terminates(tmp_path):
    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    context = multiprocessing.get_context("spawn")
    parent_connection, child_connection = context.Pipe(duplex=True)
    process = context.Process(
        target=_hold_process_lock,
        args=(str(tmp_path), child_connection),
    )
    process.start()
    child_connection.close()
    try:
        assert parent_connection.poll(10), "child did not acquire canonical-mutation lock"
        assert parent_connection.recv() == "acquired"
        process.terminate()
        process.join(10)
        assert not process.is_alive()

        with acquire_ranked_lock(ws, "canonical-mutation", timeout_seconds=5) as lease:
            assert lease.active is True
    finally:
        parent_connection.close()
        if process.is_alive():
            process.terminate()
            process.join(10)


def test_repository_releases_record_lock_before_projecting_under_mutation_lease(
    tmp_path,
    monkeypatch,
):
    import brain.v5.query_index_delta as query_index_delta

    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    seed = ClaimRecord(
        claim_id="claim-lock-seed",
        topic_id="topic-lock",
        statement="lock seed",
        evidence_profile="formal_derivation",
        confidence_state="candidate",
        active_uncertainty="Validation remains open.",
    )
    write_record(ws.registry_dir("claims") / "claim-lock-seed.md", seed, body="# Seed\n")
    build_query_index(ws)
    observed: list[tuple[str, ...]] = []

    def observe_projection(
        _ws,
        _record_ref,
        *,
        predecessor_content_watermark="",
        predecessor_record_content_hash="",
    ):
        observed.append(held_ranked_lock_names())
        return IndexProjectionOutcome(status="projected")

    monkeypatch.setattr(query_index_delta, "project_record_delta", observe_projection)
    record = ClaimRecord(
        claim_id="claim-lock-projection",
        topic_id="topic-lock",
        statement="projection lock boundary",
        evidence_profile="formal_derivation",
        confidence_state="candidate",
        active_uncertainty="Validation remains open.",
    )
    result = RecordRepository(
        ws,
        actor=RecordActor(actor_type="model", actor_id="lock-test", host="pytest"),
    ).write("claims", record, body="# Projection\n")

    assert result.status == "created"
    assert observed == [("canonical-mutation",)]


def test_full_rebuild_publishes_immutable_generation_components(tmp_path):
    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    first = ClaimRecord(
        claim_id="claim-generation-a",
        topic_id="topic-generation",
        statement="first generation record",
        evidence_profile="formal_derivation",
        confidence_state="candidate",
        active_uncertainty="Validation remains open.",
    )
    write_record(ws.registry_dir("claims") / "claim-generation-a.md", first, body="# A\n")
    initial = build_query_index(ws)
    initial_path = ws.root / "indexes" / initial.manifest.document_file
    initial_bytes = initial_path.read_bytes()
    second = ClaimRecord(
        claim_id="claim-generation-b",
        topic_id="topic-generation",
        statement="second generation record",
        evidence_profile="formal_derivation",
        confidence_state="candidate",
        active_uncertainty="Validation remains open.",
    )
    write_record(ws.registry_dir("claims") / "claim-generation-b.md", second, body="# B\n")

    rebuilt = build_query_index(ws)
    rebuilt_path = ws.root / "indexes" / rebuilt.manifest.document_file

    assert rebuilt.manifest.generation == initial.manifest.generation + 1
    assert rebuilt_path != initial_path
    assert initial_path.read_bytes() == initial_bytes
    assert set(load_query_index(ws).record_refs) == {
        "claim:claim-generation-a",
        "claim:claim-generation-b",
    }


def test_interrupted_generation_before_root_replace_keeps_old_root_readable(
    tmp_path,
    monkeypatch,
):
    import brain.v5.query_index as query_index

    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    first = ClaimRecord(
        claim_id="claim-interrupt-a",
        topic_id="topic-generation",
        statement="published generation",
        evidence_profile="formal_derivation",
        confidence_state="candidate",
        active_uncertainty="Validation remains open.",
    )
    write_record(ws.registry_dir("claims") / "claim-interrupt-a.md", first, body="# A\n")
    build_query_index(ws)
    root_path = ws.root / "indexes" / "manifest.json"
    root_before = root_path.read_bytes()
    refs_before = load_query_index(ws).record_refs
    second = ClaimRecord(
        claim_id="claim-interrupt-b",
        topic_id="topic-generation",
        statement="unpublished generation",
        evidence_profile="formal_derivation",
        confidence_state="candidate",
        active_uncertainty="Validation remains open.",
    )
    write_record(ws.registry_dir("claims") / "claim-interrupt-b.md", second, body="# B\n")
    original_failpoint = query_index._run_failpoint

    def interrupt_before_root(name: str) -> None:
        if name == "before_root_replace":
            raise RuntimeError("injected root publication interruption")
        original_failpoint(name)

    monkeypatch.setattr(query_index, "_run_failpoint", interrupt_before_root)
    with pytest.raises(RuntimeError, match="root publication interruption"):
        build_query_index(ws)

    assert root_path.read_bytes() == root_before
    assert load_query_index(ws).record_refs == refs_before


def test_full_build_rejects_metadata_preserving_canonical_edit(tmp_path, monkeypatch):
    import brain.v5.query_index as query_index

    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    path = ws.registry_dir("claims") / "claim-aba.md"
    write_record(path, _claim("claim-aba", "alpha boundary"), body="# Alpha\n")
    state_before = canonical_state_token(ws)
    original_failpoint = query_index._run_failpoint
    mutated = False

    def mutate_after_strong_before(name: str) -> None:
        nonlocal mutated
        if name == "after_canonical_before" and not mutated:
            payload = path.read_bytes()
            assert payload.count(b"alpha") == 1
            stat = path.stat()
            path.write_bytes(payload.replace(b"alpha", b"omega"))
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            mutated = True
        original_failpoint(name)

    monkeypatch.setattr(query_index, "_run_failpoint", mutate_after_strong_before)

    with pytest.raises(IndexSnapshotChangedError, match="strong canonical content"):
        build_query_index(ws)

    assert mutated is True
    assert canonical_state_token(ws) == state_before


def test_reader_retries_when_root_changes_after_base_read(tmp_path, monkeypatch):
    import brain.v5.query_index_delta as query_index_delta

    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    first = _claim("claim-reader-a", "reader base generation")
    write_record(ws.registry_dir("claims") / "claim-reader-a.md", first, body="# A\n")
    build_query_index(ws)
    second = _claim("claim-reader-b", "reader replacement generation")
    write_record(ws.registry_dir("claims") / "claim-reader-b.md", second, body="# B\n")
    original_failpoint = query_index_delta._run_failpoint
    rebuilt = False

    def rebuild_after_base(name: str) -> None:
        nonlocal rebuilt
        if name == "after_base_snapshot_read" and not rebuilt:
            rebuilt = True
            build_query_index(ws)
        original_failpoint(name)

    monkeypatch.setattr(query_index_delta, "_run_failpoint", rebuild_after_base)

    snapshot = load_effective_query_index(ws)

    assert rebuilt is True
    assert snapshot.record_refs == ("claim:claim-reader-a", "claim:claim-reader-b")
    assert snapshot.manifest.generation == 2


def test_reader_fails_closed_between_root_replace_and_delta_rebase(tmp_path, monkeypatch):
    import brain.v5.query_index as query_index

    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    write_record(
        ws.registry_dir("claims") / "claim-boundary-a.md",
        _claim("claim-boundary-a", "published base"),
        body="# A\n",
    )
    build_query_index(ws)
    write_record(
        ws.registry_dir("claims") / "claim-boundary-b.md",
        _claim("claim-boundary-b", "root without delta rebase"),
        body="# B\n",
    )
    original_failpoint = query_index._run_failpoint

    def interrupt_rebase(name: str) -> None:
        if name == "before_delta_rebase":
            raise RuntimeError("injected delta rebase interruption")
        original_failpoint(name)

    monkeypatch.setattr(query_index, "_run_failpoint", interrupt_rebase)
    with pytest.raises(RuntimeError, match="delta rebase interruption"):
        build_query_index(ws)

    result = query_records(
        ws,
        ResearchQuery(text="root without delta rebase", families=("claims",)),
    )

    assert result.index_status == "stale"
    assert result.coverage.exhaustive is False
    assert any("lineage" in error for error in result.coverage.read_errors)


def test_two_builders_publish_distinct_serial_generations(tmp_path, monkeypatch):
    import brain.v5.query_index as query_index

    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    write_record(
        ws.registry_dir("claims") / "claim-builders.md",
        _claim("claim-builders", "serialized builders"),
        body="# Builders\n",
    )
    first_prepared = threading.Event()
    release_first = threading.Event()
    second_started = threading.Event()
    second_finished = threading.Event()
    call_guard = threading.Lock()
    call_count = 0
    reports = []
    errors: list[BaseException] = []
    original_write = query_index.write_immutable_generation

    def block_first_generation(*args, **kwargs):
        nonlocal call_count
        with call_guard:
            call_count += 1
            current = call_count
        if current == 1:
            first_prepared.set()
            assert release_first.wait(5), "first builder was not released"
        return original_write(*args, **kwargs)

    def run_builder(*, second: bool = False) -> None:
        if second:
            second_started.set()
        try:
            reports.append(build_query_index(ws))
        except BaseException as exc:  # noqa: BLE001 - thread failures must reach pytest.
            errors.append(exc)
        finally:
            if second:
                second_finished.set()

    monkeypatch.setattr(query_index, "write_immutable_generation", block_first_generation)
    first_thread = threading.Thread(target=run_builder)
    second_thread = threading.Thread(target=run_builder, kwargs={"second": True})
    first_thread.start()
    assert first_prepared.wait(5), "first builder did not reach generation preparation"
    second_thread.start()
    assert second_started.wait(5), "second builder did not start"
    assert not second_finished.wait(0.2), "second builder bypassed the base-build lease"
    release_first.set()
    first_thread.join(10)
    second_thread.join(10)

    assert not first_thread.is_alive()
    assert not second_thread.is_alive()
    assert errors == []
    assert sorted(report.manifest.generation for report in reports) == [1, 2]
    assert load_query_index(ws).manifest.generation == 2


def test_write_waits_for_build_then_projects_against_published_base(tmp_path, monkeypatch):
    import brain.v5.query_index as query_index

    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    write_record(
        ws.registry_dir("claims") / "claim-build-seed.md",
        _claim("claim-build-seed", "build seed"),
        body="# Seed\n",
    )
    build_query_index(ws)
    build_prepared = threading.Event()
    release_build = threading.Event()
    writer_started = threading.Event()
    writer_finished = threading.Event()
    build_reports = []
    write_results = []
    errors: list[BaseException] = []
    original_write = query_index.write_immutable_generation

    def block_build(*args, **kwargs):
        build_prepared.set()
        assert release_build.wait(5), "blocked build was not released"
        return original_write(*args, **kwargs)

    def run_build() -> None:
        try:
            build_reports.append(build_query_index(ws))
        except BaseException as exc:  # noqa: BLE001 - thread failures must reach pytest.
            errors.append(exc)

    def run_write() -> None:
        writer_started.set()
        try:
            write_results.append(
                _repository(ws).write(
                    "claims",
                    _claim("claim-after-build", "write after published base"),
                    body="# After build\n",
                )
            )
        except BaseException as exc:  # noqa: BLE001 - thread failures must reach pytest.
            errors.append(exc)
        finally:
            writer_finished.set()

    monkeypatch.setattr(query_index, "write_immutable_generation", block_build)
    build_thread = threading.Thread(target=run_build)
    writer_thread = threading.Thread(target=run_write)
    build_thread.start()
    assert build_prepared.wait(5), "build did not acquire its publication lease"
    writer_thread.start()
    assert writer_started.wait(5), "writer did not start"
    assert not writer_finished.wait(0.2), "writer bypassed canonical-mutation"
    assert not (ws.registry_dir("claims") / "claim-after-build.md").exists()
    release_build.set()
    build_thread.join(10)
    writer_thread.join(10)

    assert not build_thread.is_alive()
    assert not writer_thread.is_alive()
    assert errors == []
    assert build_reports[0].manifest.generation == 2
    assert write_results[0].index_projection.status == "projected"
    snapshot = load_effective_query_index(ws)
    assert "claim:claim-after-build" in snapshot.record_refs
    assert snapshot.manifest.generation == 2


@pytest.mark.parametrize("lease_kind", ["mutation", "build"])
def test_lease_rejects_foreign_thread_assertion(tmp_path, lease_kind):
    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    lease_factory = (
        (lambda: acquire_canonical_mutation_lease(ws))
        if lease_kind == "mutation"
        else (lambda: acquire_index_build_lease(ws, reason="foreign-thread-test"))
    )
    errors: list[BaseException] = []

    with lease_factory() as lease:
        def assert_from_foreign_thread() -> None:
            try:
                lease.assert_active(ws)
            except BaseException as exc:  # noqa: BLE001 - thread failure is the assertion.
                errors.append(exc)

        thread = threading.Thread(target=assert_from_foreign_thread)
        thread.start()
        thread.join(5)
        assert not thread.is_alive()

    assert len(errors) == 1
    assert isinstance(errors[0], LockOwnershipError)
    assert "foreign" in str(errors[0])


def test_family_repair_serializes_same_ref_revision_and_cannot_publish_old_row(
    tmp_path,
    monkeypatch,
):
    import brain.v5.query_index_delta as query_index_delta

    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    seed = _claim("claim-repair-race", "repairraceoldtoken151")
    write_record(
        ws.registry_dir("claims") / f"{seed.claim_id}.md",
        seed,
        body="# Repair race\n",
    )
    build_query_index(ws)
    query_index_delta.mark_query_delta_dirty(
        ws,
        "claims",
        reason="injected repair race gap",
    )
    repository = _repository(ws)
    current = repository.read(f"claim:{seed.claim_id}")
    assert current.frontmatter is not None
    from brain.v5.record_envelope import canonical_record_hash
    from brain.v5.record_repository import WritePolicy

    expected_hash = canonical_record_hash(current.frontmatter, current.body)
    repair_ready = threading.Event()
    release_repair = threading.Event()
    writer_started = threading.Event()
    writer_finished = threading.Event()
    outcomes = []
    errors: list[BaseException] = []
    original_failpoint = query_index_delta._run_failpoint

    def block_repair_publication(name: str) -> None:
        if name == "before_repair_manifest_replace":
            repair_ready.set()
            assert release_repair.wait(5), "repair publication was not released"
        original_failpoint(name)

    def run_repair() -> None:
        try:
            outcomes.append(query_index_delta.repair_query_delta(ws, ("claims",)))
        except BaseException as exc:  # noqa: BLE001 - thread failures must reach pytest.
            errors.append(exc)

    def run_revision() -> None:
        writer_started.set()
        try:
            outcomes.append(
                repository.write(
                    "claims",
                    _claim("claim-repair-race", "repairracenewtoken152"),
                    body="# Newer\n",
                    policy=WritePolicy(mode="revision", expected_hash=expected_hash),
                )
            )
        except BaseException as exc:  # noqa: BLE001 - thread failures must reach pytest.
            errors.append(exc)
        finally:
            writer_finished.set()

    monkeypatch.setattr(query_index_delta, "_run_failpoint", block_repair_publication)
    repair_thread = threading.Thread(target=run_repair)
    writer_thread = threading.Thread(target=run_revision)
    repair_thread.start()
    assert repair_ready.wait(5), "repair did not reach manifest publication"
    writer_thread.start()
    assert writer_started.wait(5), "revision writer did not start"
    assert not writer_finished.wait(0.2), "revision bypassed repair mutation lease"
    release_repair.set()
    repair_thread.join(10)
    writer_thread.join(10)

    assert not repair_thread.is_alive()
    assert not writer_thread.is_alive()
    assert errors == []
    result = query_records(
        ws,
        ResearchQuery(text="repairracenewtoken152", families=("claims",)),
    )
    obsolete = query_records(
        ws,
        ResearchQuery(text="repairraceoldtoken151", families=("claims",)),
    )
    assert [item.record_ref for item in result.items] == [f"claim:{seed.claim_id}"]
    assert obsolete.items == ()
    assert result.coverage.scope_fresh is True


def test_scoped_freshness_linearization_blocks_repository_writer(tmp_path, monkeypatch):
    import brain.v5.query_index_delta as query_index_delta

    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    write_record(
        ws.registry_dir("claims") / "claim-freshness-seed.md",
        _claim("claim-freshness-seed", "freshness seed"),
        body="# Seed\n",
    )
    build_query_index(ws)
    hash_started = threading.Event()
    release_hash = threading.Event()
    writer_started = threading.Event()
    writer_finished = threading.Event()
    query_results = []
    write_results = []
    errors: list[BaseException] = []
    original_watermark = query_index_delta.current_family_content_watermark
    blocked = False

    def block_claim_hash(_ws, family: str):
        nonlocal blocked
        value = original_watermark(_ws, family)
        if family == "claims" and not blocked:
            blocked = True
            hash_started.set()
            assert release_hash.wait(5), "freshness hash was not released"
        return value

    def run_query() -> None:
        try:
            query_results.append(
                query_records(
                    ws,
                    ResearchQuery(text="absent", families=("claims",)),
                )
            )
        except BaseException as exc:  # noqa: BLE001 - thread failures must reach pytest.
            errors.append(exc)

    def run_write() -> None:
        writer_started.set()
        try:
            write_results.append(
                _repository(ws).write(
                    "claims",
                    _claim("claim-after-freshness", "after freshness lock"),
                    body="# After\n",
                )
            )
        except BaseException as exc:  # noqa: BLE001 - thread failures must reach pytest.
            errors.append(exc)
        finally:
            writer_finished.set()

    monkeypatch.setattr(
        query_index_delta,
        "current_family_content_watermark",
        block_claim_hash,
    )
    query_thread = threading.Thread(target=run_query)
    writer_thread = threading.Thread(target=run_write)
    query_thread.start()
    assert hash_started.wait(5), "query did not reach selected-family strong hash"
    writer_thread.start()
    assert writer_started.wait(5), "writer did not start"
    assert not writer_finished.wait(0.2), "writer bypassed freshness linearization"
    release_hash.set()
    query_thread.join(10)
    writer_thread.join(10)

    assert not query_thread.is_alive()
    assert not writer_thread.is_alive()
    assert errors == []
    assert query_results[0].coverage.scope_fresh is True
    assert write_results[0].index_projection.status == "projected"


def test_scoped_freshness_detects_metadata_preserving_edit_between_strong_hashes(
    tmp_path,
    monkeypatch,
):
    import brain.v5.query_index_delta as query_index_delta

    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    path = ws.registry_dir("claims") / "claim-freshness-aba.md"
    write_record(
        path,
        _claim("claim-freshness-aba", "alpha freshness boundary"),
        body="# ABA\n",
    )
    build_query_index(ws)
    state_before = canonical_state_token(ws)
    original_watermark = query_index_delta.current_family_content_watermark
    mutated = False

    def mutate_after_first_hash(_ws, family: str):
        nonlocal mutated
        value = original_watermark(_ws, family)
        if family == "claims" and not mutated:
            payload = path.read_bytes()
            assert payload.count(b"alpha") == 1
            stat = path.stat()
            path.write_bytes(payload.replace(b"alpha", b"omega"))
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            mutated = True
        return value

    monkeypatch.setattr(
        query_index_delta,
        "current_family_content_watermark",
        mutate_after_first_hash,
    )

    result = query_records(
        ws,
        ResearchQuery(text="absent", families=("claims",)),
    )

    assert mutated is True
    assert canonical_state_token(ws) == state_before
    assert result.coverage.scope_state_fresh is True
    assert result.coverage.scope_content_verified is False
    assert result.coverage.scope_fresh is False
    assert result.coverage.exhaustive is False


def test_orientation_reuses_pointer_bound_snapshot_but_strong_query_reloads(
    tmp_path,
    monkeypatch,
):
    import brain.v5.query_index_snapshot as query_index_snapshot

    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    write_record(
        ws.registry_dir("claims") / "claim-cache.md",
        _claim("claim-cache", "orientation cache fixture"),
        body="# Cache\n",
    )
    build_query_index(ws)
    load_count = 0
    original_load = query_index_snapshot.load_query_index

    def counting_load(_ws):
        nonlocal load_count
        load_count += 1
        return original_load(_ws)

    monkeypatch.setattr(query_index_snapshot, "load_query_index", counting_load)
    orientation = ResearchQuery(
        text="orientation cache fixture",
        families=("claims",),
        verification_mode="orientation",
    )

    first = query_records(ws, orientation)
    second = query_records(ws, orientation)
    strong = query_records(
        ws,
        ResearchQuery(text="orientation cache fixture", families=("claims",)),
    )

    assert first.items == second.items
    assert first.coverage.exhaustive is False
    assert strong.coverage.exhaustive is True
    assert load_count == 2
