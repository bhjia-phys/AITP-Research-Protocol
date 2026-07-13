from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import time

import pytest

from brain.v5.markdown import read_md
from brain.v5.models import ClaimRecord, SourceAssetRecord, ToolRecipeRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import (
    RecordCollisionError,
    RecordCompareAndSwapError,
    RecordIntegrityError,
    RecordLockError,
    RecordRepository,
    WritePolicy,
)
from brain.v5.record_repository_contracts import (
    validate_record_read_report,
    validate_write_result,
)


CLAIM = ClaimRecord(
    claim_id="claim-repository-1",
    topic_id="topic-repository",
    statement="The repository must preserve canonical identity.",
    evidence_profile="formal_derivation",
    confidence_state="hypothesis",
    active_uncertainty="The validation path remains open.",
)


def _repository(tmp_path):
    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    return RecordRepository(
        ws,
        actor=RecordActor(actor_type="model", actor_id="repository-test", host="pytest"),
    )


def _tool_recipe(recipe_id: str) -> ToolRecipeRecord:
    return ToolRecipeRecord(
        recipe_id=recipe_id,
        tool_family="remote_numerics",
        tool_name="fisherd",
        purpose="Run a bounded numerical audit.",
    )


def test_repository_same_content_is_idempotent(tmp_path):
    repo = _repository(tmp_path)

    first = repo.write("claims", CLAIM, body="# Claim\n")
    path = tmp_path / ".aitp" / "registry" / "claims" / f"{CLAIM.claim_id}.md"
    before = path.read_bytes()
    second = repo.write("claims", CLAIM, body="# Claim\n")
    frontmatter, _ = read_md(path)

    assert first.status == "created"
    assert second.status == "unchanged"
    assert second.content_hash == first.content_hash
    assert frontmatter["record_content_hash"] == first.content_hash
    assert path.read_bytes() == before


def test_workspace_layout_reserves_canonical_revision_archive(tmp_path):
    repo = _repository(tmp_path)

    assert (repo.ws.root / "revisions").is_dir()


def test_repository_rejects_same_id_with_different_content(tmp_path):
    repo = _repository(tmp_path)
    repo.write("claims", CLAIM, body="# Claim\n")
    changed = replace(CLAIM, statement="A different scientific statement.")

    with pytest.raises(RecordCollisionError, match="claim-repository-1"):
        repo.write("claims", changed, body="# Changed\n")


def test_repository_validates_family_schema_before_write(tmp_path):
    repo = _repository(tmp_path)
    incomplete_claim = {
        "claim_id": "claim-incomplete",
        "topic_id": "topic-repository",
        "kind": "claim",
    }

    with pytest.raises(TypeError, match="missing"):
        repo.write("claims", incomplete_claim, body="# Incomplete\n")

    assert not (
        repo.ws.registry_dir("claims") / "claim-incomplete.md"
    ).exists()


def test_repository_path_containment_rejects_traversal_before_filesystem_access(
    tmp_path,
    monkeypatch,
):
    repo = _repository(tmp_path)
    filesystem_calls = []

    def unexpected_filesystem_call(path, *_args, **_kwargs):
        filesystem_calls.append(str(path))
        raise AssertionError(f"filesystem accessed for unsafe record id: {path}")

    monkeypatch.setattr(Path, "resolve", unexpected_filesystem_call)
    monkeypatch.setattr(Path, "mkdir", unexpected_filesystem_call)

    with pytest.raises(ValueError, match="record_id"):
        repo.write("tool_recipes", _tool_recipe("../escaped-family"))

    assert filesystem_calls == []


@pytest.mark.parametrize(
    "record_id",
    [
        "../escaped-family",
        r"..\escaped-family",
        "nested/record",
        r"nested\record",
        ".",
        "..",
        " leading-space",
        "trailing-space ",
        "trailing-dot.",
        "record:alias",
        "NUL",
    ],
)
def test_repository_path_containment_rejects_unsafe_or_ambiguous_record_ids(
    tmp_path,
    record_id,
):
    repo = _repository(tmp_path)

    with pytest.raises(ValueError, match="record_id"):
        repo.write("tool_recipes", _tool_recipe(record_id))


def test_repository_path_containment_rejects_traversal_lock_paths(tmp_path):
    repo = _repository(tmp_path)
    family_lock_root = repo.ws.root / "runtime" / "locks" / "tool_recipes"
    escaped_lock = repo.ws.root / "runtime" / "locks" / "escaped-family.lock"

    with pytest.raises(ValueError, match="record_id"):
        with repo.lock_record("tool_recipes", "../escaped-family"):
            pass

    assert not family_lock_root.exists()
    assert not escaped_lock.exists()


def test_repository_path_containment_marks_unsafe_exact_refs_malformed_without_lookup(
    tmp_path,
    monkeypatch,
):
    repo = _repository(tmp_path)
    looked_up_paths = []

    def track_exists(path):
        looked_up_paths.append(str(path))
        return False

    monkeypatch.setattr(Path, "exists", track_exists)

    result = repo.read("tool_recipe:../escaped-family")

    assert result.status == "malformed_ref"
    assert result.path == ""
    assert looked_up_paths == []


def test_repository_path_containment_rejects_resolved_canonical_escape(
    tmp_path,
    monkeypatch,
):
    repo = _repository(tmp_path)
    record = _tool_recipe("fisherd-bounded-numerical-audit")
    canonical_path = (
        repo.ws.registry_dir("tool_recipes") / f"{record.recipe_id}.md"
    )
    escaped_path = (tmp_path / "escaped-canonical.md").resolve()
    real_resolve = Path.resolve

    def resolve_with_escape(path, *args, **kwargs):
        if path == canonical_path:
            return escaped_path
        return real_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve_with_escape)

    with pytest.raises(ValueError, match="canonical record path escaped"):
        repo.write("tool_recipes", record)


def test_repository_path_containment_rejects_resolved_lock_escape(
    tmp_path,
    monkeypatch,
):
    repo = _repository(tmp_path)
    record_id = "fisherd-bounded-numerical-audit"
    family_lock_root = repo.ws.root / "runtime" / "locks" / "tool_recipes"
    lock_path = family_lock_root / f"{record_id}.lock"
    escaped_path = (repo.ws.root / "runtime" / "locks" / "escaped.lock").resolve()
    real_resolve = Path.resolve

    def resolve_with_escape(path, *args, **kwargs):
        if path == lock_path:
            return escaped_path
        return real_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve_with_escape)

    with pytest.raises(ValueError, match="record lock path escaped"):
        with repo.lock_record("tool_recipes", record_id):
            pass

    assert not family_lock_root.exists()


def test_repository_path_containment_preserves_valid_recipe_ids_and_exact_reads(tmp_path):
    repo = _repository(tmp_path)
    record = _tool_recipe("fisherd-bounded-numerical-audit")

    written = repo.write("tool_recipes", record)
    found = repo.read(f"tool_recipe:{record.recipe_id}")

    assert Path(written.path).resolve().is_relative_to(
        repo.ws.registry_dir("tool_recipes").resolve()
    )
    assert found.status == "found"
    assert found.record == record


def test_repository_rejects_untyped_source_record_refs(tmp_path):
    repo = _repository(tmp_path)
    payload = {
        **CLAIM.__dict__,
        "source_record_refs": ["not-a-typed-ref"],
    }

    with pytest.raises(ValueError, match="source_record_refs"):
        repo.write("claims", payload, body="# Claim\n")


def test_repository_rejects_stale_declared_hash_instead_of_returning_unchanged(tmp_path):
    from brain.v5.markdown import write_md

    repo = _repository(tmp_path)
    created = repo.write("claims", CLAIM, body="# Claim\n")
    frontmatter, _body = read_md(created.path)
    write_md(created.path, frontmatter, "# Corrupted body\n")

    with pytest.raises(RecordIntegrityError, match="stored record content hash"):
        repo.write("claims", CLAIM, body="# Claim\n")


def test_repository_list_reports_malformed_record(tmp_path):
    repo = _repository(tmp_path)
    bad = tmp_path / ".aitp" / "registry" / "claims" / "bad.md"
    bad.write_text("---\nclaim_id: [\n---\n", encoding="utf-8")

    report = repo.list("claims")

    assert report.checked_count == 1
    assert report.loaded_count == 0
    assert report.missing is False
    assert len(report.malformed) == 1
    assert report.malformed[0].path == str(bad)
    assert report.malformed[0].family == "claims"
    assert report.malformed[0].error_type
    assert report.malformed[0].message


def test_repository_accepts_legacy_source_asset_domain_content_hash(tmp_path):
    from brain.v5.store import write_record

    repo = _repository(tmp_path)
    source = SourceAssetRecord(
        asset_id="source-1",
        topic_id="topic-repository",
        asset_type="paper",
        uri="file:///paper.pdf",
        title="Paper",
        content_hash="source-byte-hash",
        hash_algorithm="sha256",
    )
    write_record(
        repo.ws.registry_dir("source_assets") / "source-1.md",
        source,
        body="# Source\n",
    )

    report = repo.list("source_assets")

    assert report.loaded_count == 1
    assert report.malformed == ()
    assert report.records[0].content_hash == "source-byte-hash"


def test_repository_list_distinguishes_missing_directory(tmp_path):
    repo = RecordRepository(
        WorkspacePaths(tmp_path),
        actor=RecordActor(actor_type="model", actor_id="repository-test", host="pytest"),
    )

    report = repo.list("claims")

    assert report.missing is True
    assert report.checked_count == 0
    assert report.records == ()


def test_repository_revision_requires_expected_hash_and_archives_previous_version(tmp_path):
    repo = _repository(tmp_path)
    first = repo.write("claims", CLAIM, body="# Claim\n")
    changed = replace(CLAIM, statement="A reviewed replacement statement.")

    revised = repo.write(
        "claims",
        changed,
        body="# Revised claim\n",
        policy=WritePolicy(mode="revision", expected_hash=first.content_hash),
    )

    path = tmp_path / ".aitp" / "registry" / "claims" / f"{CLAIM.claim_id}.md"
    frontmatter, body = read_md(path)
    archive = (
        tmp_path
        / ".aitp"
        / "revisions"
        / "claims"
        / CLAIM.claim_id
        / f"{first.content_hash}.md"
    )
    assert revised.status == "revised"
    assert revised.previous_hash == first.content_hash
    assert revised.revision == 2
    assert revised.archive_path == str(archive)
    assert frontmatter["revision"] == 2
    assert frontmatter["supersedes"] == [f"claim:{CLAIM.claim_id}@sha256:{first.content_hash}"]
    assert "reviewed replacement" in frontmatter["statement"]
    assert body == "# Revised claim\n"
    assert archive.exists()


def test_repository_revision_rejects_stale_expected_hash(tmp_path):
    repo = _repository(tmp_path)
    repo.write("claims", CLAIM, body="# Claim\n")

    with pytest.raises(RecordCompareAndSwapError, match="expected hash"):
        repo.write(
            "claims",
            replace(CLAIM, statement="Changed."),
            body="# Changed\n",
            policy=WritePolicy(mode="revision", expected_hash="0" * 64),
        )


def test_repository_compare_and_swap_is_checked_before_idempotent_return(tmp_path):
    repo = _repository(tmp_path)
    repo.write("claims", CLAIM, body="# Claim\n")

    with pytest.raises(RecordCompareAndSwapError, match="expected hash"):
        repo.write(
            "claims",
            CLAIM,
            body="# Claim\n",
            policy=WritePolicy(expected_hash="0" * 64),
        )


def test_repository_cleans_stale_lock_only_when_policy_allows(tmp_path):
    repo = _repository(tmp_path)
    lock = (
        tmp_path
        / ".aitp"
        / "runtime"
        / "locks"
        / "claims"
        / f"{CLAIM.claim_id}.lock"
    )
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text("stale\n", encoding="utf-8")
    old = time.time() - 60
    os.utime(lock, (old, old))

    result = repo.write(
        "claims",
        CLAIM,
        body="# Claim\n",
        policy=WritePolicy(stale_lock_after_seconds=1),
    )

    assert result.status == "created"
    assert not lock.exists()

    lock.write_text("fresh\n", encoding="utf-8")
    with pytest.raises(RecordLockError, match="already held"):
        repo.write(
            "claims",
            CLAIM,
            policy=WritePolicy(lock_timeout_seconds=0.01, stale_lock_after_seconds=60),
        )
    assert lock.exists()
    lock.unlink()


def test_repository_concurrent_same_content_creation_is_idempotent(tmp_path):
    repo = _repository(tmp_path)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(repo.write, "claims", CLAIM, body="# Claim\n")
            for _ in range(2)
        ]
    statuses = sorted(future.result().status for future in futures)

    assert statuses == ["created", "unchanged"]


def test_repository_reads_one_exact_record_and_reports_missing(tmp_path):
    repo = _repository(tmp_path)
    repo.write("claims", CLAIM, body="# Claim\n")

    found = repo.read(f"claim:{CLAIM.claim_id}")
    missing = repo.read("claim:missing-claim")

    assert found.status == "found"
    assert found.record == CLAIM
    assert found.issue is None
    assert missing.status == "not_found"
    assert missing.record is None


def test_repository_lists_and_reads_documented_special_record_paths(tmp_path):
    from brain.v5.workspace import bind_session, create_context, create_topic

    repo = _repository(tmp_path)
    create_context(repo.ws, "physics", title="Physics")
    create_topic(repo.ws, "qg", context_id="physics", title="Quantum Gravity")
    bind_session(repo.ws, "s1", topic_id="qg", context_id="physics")

    assert repo.list("contexts").loaded_count == 1
    assert repo.list("topics").loaded_count == 1
    assert repo.list("sessions").loaded_count == 1
    assert repo.read("context:physics").status == "found"
    assert repo.read("topic:qg").status == "found"
    assert repo.read("session:s1").status == "found"


def test_repository_results_satisfy_trust_neutral_contracts(tmp_path):
    repo = _repository(tmp_path)
    write_result = repo.write("claims", CLAIM, body="# Claim\n")
    read_report = repo.list("claims")

    assert validate_write_result(write_result) == ()
    assert validate_record_read_report(read_report) == ()


def test_record_lock_closes_its_descriptor_once(tmp_path, monkeypatch):
    import brain.v5.record_repository as repository_module

    closed_descriptors = []

    class TrackingOS:
        O_CREAT = os.O_CREAT
        O_EXCL = os.O_EXCL
        O_WRONLY = os.O_WRONLY
        open = staticmethod(os.open)
        write = staticmethod(os.write)
        getpid = staticmethod(os.getpid)

        @staticmethod
        def close(descriptor):
            closed_descriptors.append(descriptor)
            os.close(descriptor)

    monkeypatch.setattr(repository_module, "os", TrackingOS)
    repo = _repository(tmp_path)

    with repo.lock_record("claims", "claim-lock-close-once"):
        pass

    assert len(closed_descriptors) == 1


def test_atomic_text_writer_removes_temp_file_when_replace_fails(tmp_path, monkeypatch):
    import brain.v5.markdown as markdown_module

    def fail_replace(_source, _target):
        raise OSError("replace failed")

    monkeypatch.setattr(markdown_module.os, "replace", fail_replace)
    target = tmp_path / "record.md"

    with pytest.raises(OSError, match="replace failed"):
        markdown_module.write_text_atomic(target, "content")

    assert list(tmp_path.iterdir()) == []
