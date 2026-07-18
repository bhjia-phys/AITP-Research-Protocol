from __future__ import annotations

import json
from dataclasses import replace

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="model", actor_id="recording-batch-test", host="pytest")


def _seed_workspace(tmp_path):
    from brain.v5.query_index import build_query_index
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "target", context_id="formal-theory", title="Target theory topic")
    first = create_claim(
        ws,
        topic_id="target",
        statement="The finite diagnostic is controlled in the stated scope.",
        evidence_profile="formal_theory",
        confidence_state="finite_evidence",
        active_uncertainty="The asymptotic limit remains open.",
    )
    second = create_claim(
        ws,
        topic_id="target",
        statement="The source convention is fixed for this calculation.",
        evidence_profile="formal_theory",
        confidence_state="conditional",
        active_uncertainty="The convention must be translated for other sources.",
    )
    bind_session(
        ws,
        "session-1",
        topic_id="target",
        context_id="formal-theory",
        active_claim=first.claim_id,
    )
    build_query_index(ws)
    return ws, f"claim:{first.claim_id}", f"claim:{second.claim_id}"


def _candidate(
    source_ref: str,
    *,
    semantic_key: str = "finite replica formula",
    summary: str = "Record the finite replica formula and its applicability boundary.",
    candidate_kind: str = "formula",
    expires_at: str = "2099-07-21T00:00:00+00:00",
):
    from brain.v5.recording_batches import StagedCandidate

    return StagedCandidate(
        staging_id="",
        session_id="session-1",
        topic_id="target",
        candidate_kind=candidate_kind,
        semantic_key=semantic_key,
        summary=summary,
        payload={"equation": "Z_n", "boundary": "finite n only"},
        source_refs=(source_ref,),
        source_event_refs=("event:derivation-1",),
        missing_prerequisites=("large-n continuation",),
        dedup_key="",
        created_at="2026-07-14T00:00:00+00:00",
        expires_at=expires_at,
    )


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_staging_is_idempotent_for_normalized_semantics_and_sources(tmp_path):
    from brain.v5.recording_batches import (
        recording_staging_path,
        stage_recording_candidate,
    )

    ws, first_ref, second_ref = _seed_workspace(tmp_path)
    first = stage_recording_candidate(ws, _candidate(first_ref))
    replay = stage_recording_candidate(
        ws,
        replace(
            _candidate(f"aitp:{first_ref}"),
            semantic_key="  FINITE   REPLICA FORMULA  ",
        ),
    )
    other_source = stage_recording_candidate(ws, _candidate(second_ref))

    assert replay == first
    assert first.dedup_key != other_source.dedup_key
    assert first.semantic_key == "finite replica formula"
    assert first.source_refs == (first_ref,)
    assert recording_staging_path(ws, first).exists()
    assert recording_staging_path(ws, other_source).exists()


def test_staging_supersession_rejection_and_resume_are_explicit(tmp_path):
    from brain.v5.recording_batches import (
        recording_staging_history_dir,
        reject_recording_candidate,
        resume_recording_candidate,
        stage_recording_candidate,
    )

    ws, first_ref, _second_ref = _seed_workspace(tmp_path)
    original = stage_recording_candidate(ws, _candidate(first_ref))
    replacement = stage_recording_candidate(
        ws,
        _candidate(first_ref, summary="Use the corrected finite replica normalization."),
    )

    history_path = recording_staging_history_dir(ws, "session-1") / f"{original.staging_id}.json"
    assert replacement.staging_id != original.staging_id
    assert replacement.supersedes == (original.staging_id,)
    assert _json(history_path)["candidate"]["status"] == "superseded"

    rejected = reject_recording_candidate(
        ws,
        "session-1",
        replacement.dedup_key,
        reason="The convention is not yet checked.",
    )
    assert rejected.status == "rejected"
    assert rejected.rejection_reason == "The convention is not yet checked."

    resumed = resume_recording_candidate(
        ws,
        "session-1",
        replacement.dedup_key,
        expires_at="2099-08-01T00:00:00+00:00",
    )
    assert resumed.staging_id == replacement.staging_id
    assert resumed.status == "staged"
    assert resumed.rejection_reason == ""
    assert resumed.expires_at == "2099-08-01T00:00:00+00:00"


def test_coalesce_reports_expired_rejected_and_corrupt_runtime_candidates(
    tmp_path, monkeypatch
):
    from brain.v5 import (
        evidence,
        harness_feedback_cases,
        skill_candidates,
        strategy_memory,
        trust_updates,
        validation,
    )
    from brain.v5.record_repository import RecordRepository
    from brain.v5.recording_batches import (
        coalesce_recording_batch,
        inspect_recording_staging,
        recording_batch_receipt_path,
        recording_staging_dir,
        recording_staging_path,
        reject_recording_candidate,
        stage_recording_candidate,
    )

    ws, first_ref, second_ref = _seed_workspace(tmp_path)
    included = stage_recording_candidate(ws, _candidate(first_ref))
    expired = stage_recording_candidate(
        ws,
        _candidate(
            second_ref,
            semantic_key="expired derivation",
            candidate_kind="derivation",
            expires_at="2000-01-01T00:00:00+00:00",
        ),
    )
    rejected = stage_recording_candidate(
        ws,
        _candidate(
            second_ref,
            semantic_key="rejected convention",
            candidate_kind="convention",
        ),
    )
    reject_recording_candidate(ws, "session-1", rejected.dedup_key, reason="not checked")
    corrupt = recording_staging_dir(ws, "session-1") / "corrupt.json"
    corrupt.write_text("{broken", encoding="utf-8")

    def forbidden(*_args, **_kwargs):
        raise AssertionError("coalescing called a forbidden downstream writer")

    for module, name in (
        (evidence, "record_evidence"),
        (validation, "record_validation_result"),
        (strategy_memory, "record_strategy_memory"),
        (harness_feedback_cases, "record_harness_feedback_case"),
        (skill_candidates, "apply_project_skill"),
        (trust_updates, "apply_trust_update"),
    ):
        monkeypatch.setattr(module, name, forbidden)

    result = coalesce_recording_batch(
        ws, "session-1", "milestone-1", actor=_actor()
    )
    batch = RecordRepository(ws, actor=_actor()).read(result.record_ref).record
    receipt = _json(recording_batch_receipt_path(ws, "session-1", "milestone-1"))
    inventory = inspect_recording_staging(ws, "session-1")

    assert result.status == "created"
    assert [item["staging_id"] for item in batch.candidates] == [included.staging_id]
    assert batch.status == "pending_review"
    assert batch.can_update_claim_trust is False
    assert receipt["included_staging_ids"] == [included.staging_id]
    assert receipt["expired_staging_ids"] == [expired.staging_id]
    assert receipt["rejected_staging_ids"] == [rejected.staging_id]
    assert receipt["corrupt_files"] == [str(corrupt)]
    assert _json(recording_staging_path(ws, included))["candidate"]["status"] == "included"
    assert _json(recording_staging_path(ws, expired))["candidate"]["status"] == "expired"
    assert inventory.corrupt[0].path == str(corrupt)


def test_coalesce_persists_at_most_one_batch_per_milestone(tmp_path):
    from brain.v5.record_repository import RecordRepository
    from brain.v5.recording_batches import (
        coalesce_recording_batch,
        recording_batch_receipt_path,
        recording_staging_path,
        stage_recording_candidate,
    )

    ws, first_ref, second_ref = _seed_workspace(tmp_path)
    first = stage_recording_candidate(ws, _candidate(first_ref))
    initial = coalesce_recording_batch(ws, "session-1", "milestone-1", actor=_actor())
    second = stage_recording_candidate(
        ws,
        _candidate(second_ref, semantic_key="source convention", candidate_kind="convention"),
    )

    replay = coalesce_recording_batch(ws, "session-1", "milestone-1", actor=_actor())
    replay_receipt = _json(
        recording_batch_receipt_path(ws, "session-1", "milestone-1")
    )
    status_after_replay = _json(recording_staging_path(ws, second))["candidate"][
        "status"
    ]
    next_batch = coalesce_recording_batch(
        ws, "session-1", "milestone-2", actor=_actor()
    )
    repository = RecordRepository(ws, actor=_actor())

    assert initial.record_ref == replay.record_ref
    assert replay.status == "unchanged"
    assert replay_receipt["deferred_staging_ids"] == [second.staging_id]
    assert status_after_replay == "staged"
    assert [
        item["staging_id"] for item in repository.read(initial.record_ref).record.candidates
    ] == [first.staging_id]
    assert [
        item["staging_id"] for item in repository.read(next_batch.record_ref).record.candidates
    ] == [second.staging_id]
    assert repository.list("recording_candidate_batches").loaded_count == 2


def test_coalesce_refuses_to_create_an_empty_canonical_batch(tmp_path):
    from brain.v5.record_repository import RecordRepository
    from brain.v5.recording_batches import (
        RecordingBatchError,
        coalesce_recording_batch,
        recording_batch_receipt_path,
        stage_recording_candidate,
    )

    ws, first_ref, _second_ref = _seed_workspace(tmp_path)
    expired = stage_recording_candidate(
        ws,
        _candidate(first_ref, expires_at="2000-01-01T00:00:00+00:00"),
    )

    with pytest.raises(RecordingBatchError, match="no eligible"):
        coalesce_recording_batch(ws, "session-1", "milestone-empty", actor=_actor())

    receipt = _json(
        recording_batch_receipt_path(ws, "session-1", "milestone-empty")
    )
    assert receipt["expired_staging_ids"] == [expired.staging_id]
    assert RecordRepository(ws, actor=_actor()).list(
        "recording_candidate_batches"
    ).loaded_count == 0


def test_existing_batch_reconciles_runtime_state_after_interrupted_marking(
    tmp_path, monkeypatch
):
    from brain.v5 import recording_batches
    from brain.v5.record_repository import RecordRepository
    from brain.v5.recording_batches import (
        RecordingBatchError,
        coalesce_recording_batch,
        recording_staging_path,
        stage_recording_candidate,
    )

    ws, first_ref, _second_ref = _seed_workspace(tmp_path)
    staged = stage_recording_candidate(ws, _candidate(first_ref))

    def interrupted(*_args, **_kwargs):
        raise RuntimeError("simulated interruption after canonical write")

    with monkeypatch.context() as patch:
        patch.setattr(recording_batches, "_mark_included", interrupted)
        with pytest.raises(RuntimeError, match="simulated interruption"):
            coalesce_recording_batch(
                ws, "session-1", "milestone-interrupted", actor=_actor()
            )

    assert _json(recording_staging_path(ws, staged))["candidate"]["status"] == "staged"
    replay = coalesce_recording_batch(
        ws, "session-1", "milestone-interrupted", actor=_actor()
    )

    assert replay.status == "unchanged"
    assert _json(recording_staging_path(ws, staged))["candidate"]["status"] == "included"
    with pytest.raises(RecordingBatchError, match="no eligible"):
        coalesce_recording_batch(
            ws, "session-1", "milestone-after-interruption", actor=_actor()
        )
    assert RecordRepository(ws, actor=_actor()).list(
        "recording_candidate_batches"
    ).loaded_count == 1


def test_moment_closeout_and_navigator_expose_one_quiet_batch_handoff(tmp_path):
    from brain.v5.closeout_completeness import coalesce_closeout_recording_batch
    from brain.v5.moment_policy import stage_moment_recording_candidate
    from brain.v5.recording_navigator import recording_batch_handoff

    ws, first_ref, second_ref = _seed_workspace(tmp_path)
    staged = stage_moment_recording_candidate(
        ws,
        decision={"decision_type": "recording", "action_kind": "record_formula"},
        candidate=_candidate(first_ref),
    )
    skipped = stage_moment_recording_candidate(
        ws,
        decision={"decision_type": "brainstorming", "action_kind": "explore"},
        candidate=_candidate(second_ref, semantic_key="uncommitted analogy"),
    )
    result = coalesce_closeout_recording_batch(
        ws, "session-1", "closeout-1", actor=_actor()
    )
    handoff = recording_batch_handoff(result)

    assert staged == {
        "kind": "recording_candidate_staging",
        "status": "staged",
        "staging_id": staged["staging_id"],
        "dedup_key": staged["dedup_key"],
        "trust_effect": "none",
        "can_update_claim_trust": False,
    }
    assert skipped["status"] == "skipped"
    assert handoff == {
        "kind": "recording_batch_handoff",
        "status": result.status,
        "batch_ref": result.record_ref,
        "review_status": "pending_review",
        "human_review_required": True,
        "can_update_claim_trust": False,
    }
    assert "prompt" not in staged
    assert "prompt" not in skipped
    assert "prompt" not in handoff
