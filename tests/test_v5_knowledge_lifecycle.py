from __future__ import annotations


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="knowledge-lifecycle-test", host="pytest")


def _assertion(ws, assertion_id):
    from brain.v5.models import PhysicsAssertionRecord
    from brain.v5.record_repository import RecordRepository

    result = RecordRepository(ws, actor=_actor()).write(
        "physics_assertions",
        PhysicsAssertionRecord(
            assertion_id=assertion_id,
            object_ref="physics_object:local-algebra",
            topic_id="qg",
            predicate="definition",
            value=f"Definition {assertion_id}.",
            review_status="reviewed",
        ),
    )
    return result


def _setup(tmp_path):
    from brain.v5.models import PhysicsObjectRecord
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum gravity")
    RecordRepository(ws, actor=_actor()).write(
        "physics_objects",
        PhysicsObjectRecord(
            object_id="local-algebra",
            topic_id="qg",
            object_type="operator_algebra",
            name="Local algebra",
            definition="Stable object identity.",
        ),
    )
    return ws


def test_demote_is_append_only_and_projects_without_rewriting_subject(tmp_path):
    from brain.v5.knowledge_lifecycle import (
        project_knowledge_lifecycle,
        record_knowledge_lifecycle_event,
    )
    from brain.v5.pinned_record_refs import PinnedRecordRef

    ws = _setup(tmp_path)
    result = _assertion(ws, "assertion-v1")
    subject_pin = PinnedRecordRef(result.record_ref, result.content_hash, result.revision)
    before = (ws.registry_dir("physics_assertions") / "assertion-v1.md").read_bytes()

    event_result = record_knowledge_lifecycle_event(
        ws,
        subject_ref=subject_pin,
        action="demote",
        reason="The review boundary was later judged incomplete.",
        operator="reviewer",
        timestamp="2026-07-15T10:00:00Z",
        actor=_actor(),
    )
    after = (ws.registry_dir("physics_assertions") / "assertion-v1.md").read_bytes()
    projection = project_knowledge_lifecycle(ws, subject_pin)

    assert before == after
    assert event_result.record_ref.startswith("lifecycle_event:")
    assert projection.effective_status == "demoted"
    assert projection.active is False
    assert projection.can_update_claim_trust is False


def test_supersede_requires_exact_same_scope_replacement_and_projects_it(tmp_path):
    from brain.v5.knowledge_lifecycle import (
        project_knowledge_lifecycle,
        record_knowledge_lifecycle_event,
    )
    from brain.v5.pinned_record_refs import PinnedRecordRef

    ws = _setup(tmp_path)
    old = _assertion(ws, "assertion-v1")
    new = _assertion(ws, "assertion-v2")
    old_pin = PinnedRecordRef(old.record_ref, old.content_hash, old.revision)
    new_pin = PinnedRecordRef(new.record_ref, new.content_hash, new.revision)

    record_knowledge_lifecycle_event(
        ws,
        subject_ref=old_pin,
        action="supersede",
        reason="A narrower reviewed assertion replaces this one.",
        operator="reviewer",
        timestamp="2026-07-15T11:00:00Z",
        replacement_ref=new_pin,
        actor=_actor(),
    )
    projection = project_knowledge_lifecycle(ws, old_pin)

    assert projection.effective_status == "superseded"
    assert projection.replacement_ref == new_pin.record_ref
    assert projection.replacement_content_hash == new_pin.content_hash


def test_invalidate_event_is_trust_neutral_and_exactly_pinned(tmp_path):
    from brain.v5.knowledge_lifecycle import record_knowledge_lifecycle_event
    from brain.v5.models import LifecycleEventRecord
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.record_repository import RecordRepository

    ws = _setup(tmp_path)
    result = _assertion(ws, "assertion-invalid")
    subject_pin = PinnedRecordRef(result.record_ref, result.content_hash, result.revision)

    event_result = record_knowledge_lifecycle_event(
        ws,
        subject_ref=subject_pin,
        action="invalidate",
        reason="The exact source interpretation was invalid.",
        operator="reviewer",
        timestamp="2026-07-15T12:00:00Z",
        actor=_actor(),
    )
    event = RecordRepository(ws, actor=_actor()).read(event_result.record_ref).record

    assert isinstance(event, LifecycleEventRecord)
    assert event.subject_ref == vars(subject_pin)
    assert event.lifecycle_action == "invalidate"
    assert event.can_update_claim_trust is False
