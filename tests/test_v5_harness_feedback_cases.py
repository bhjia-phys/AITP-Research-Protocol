from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "v5_harness_feedback"


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="model", actor_id="harness-feedback-test", host="pytest")


def _request(name: str = "generic"):
    from brain.v5.harness_feedback_case_contracts import HarnessFeedbackCaseRequest

    if name == "nio":
        payload = json.loads((FIXTURE_ROOT / "nio_case.json").read_text(encoding="utf-8"))
        return HarnessFeedbackCaseRequest(**payload)
    return HarnessFeedbackCaseRequest(
        topic_id="formal-qg",
        problem_type="missing_research_provenance",
        friction="A resumed derivation cannot identify which convention fixed the sign.",
        expected_behavior="Recall should expose the exact convention record before expansion.",
        actual_behavior="The compact entry reports the result without its convention source.",
        impact="The model may silently mix two incompatible curvature conventions.",
        reproduction_steps=(
            "Start a new host session for the topic.",
            "Request the compact derivation context.",
            "Inspect the returned source references.",
        ),
        host_id="codex",
        runtime_context={"surface": "compact", "event": "session_start"},
        source_refs=("derivation_chain:qg-chain-7", "source_asset:qg-note-2"),
        proposed_direction="Expose the missing convention reference in the compact entry card.",
        affected_capability="context_recall",
        affected_record_family="derivation_chains",
    )


def _read_case(ws, record_ref):
    from brain.v5.record_repository import RecordRepository

    result = RecordRepository(ws, actor=_actor()).read(record_ref)
    assert result.status == "found"
    return result.record


def test_family_registry_exposes_one_reviewed_non_authoritative_case_family():
    from brain.v5.record_family_registry import record_family_specs

    specs = record_family_specs()
    spec = specs["harness_feedback_cases"]

    assert spec.ref_kind == "harness_feedback_case"
    assert spec.schema_version == "v1"
    assert spec.lifecycle_policy == "append_revision"
    assert spec.auto_write_policy == "reviewed"
    assert spec.trust_effect == "none"
    assert spec.record_role == "review_input_record"
    assert [name for name in specs if name.startswith("harness_feedback_")] == [
        "harness_feedback_cases"
    ]


def test_generic_case_is_idempotent_and_preserves_false_authority_flags(tmp_path):
    from brain.v5.harness_feedback_cases import record_harness_feedback_case
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    now = datetime(2026, 7, 18, 8, 0, tzinfo=UTC)

    first = record_harness_feedback_case(ws, _request(), actor=_actor(), now=now)
    replay = record_harness_feedback_case(
        ws,
        _request(),
        actor=_actor(),
        now=now + timedelta(hours=1),
    )

    record = _read_case(ws, first.record_ref)
    assert first.status == "created"
    assert replay.status == "unchanged"
    assert replay.record_ref == first.record_ref
    assert record.case_id.startswith("harness-feedback-")
    assert record.source_fingerprint
    assert record.content_fingerprint
    assert record.requires_human_review is True
    assert record.orientation_only is True
    assert record.can_modify_harness is False
    assert record.produces_harness_optimization_plan is False
    assert record.produces_skill_implementation_plan is False
    assert record.can_emit_skill_artifacts is False
    assert record.can_install_skill is False
    assert record.can_install_skill_artifacts is False
    assert record.can_update_claim_trust is False

    report = RecordRepository(ws, actor=_actor()).list("harness_feedback_cases")
    assert report.loaded_count == 1
    assert report.malformed == ()


@pytest.mark.parametrize(
    "field_name",
    (
        "can_modify_harness",
        "produces_harness_optimization_plan",
        "produces_skill_implementation_plan",
        "can_emit_skill_artifacts",
        "can_install_skill",
        "can_install_skill_artifacts",
        "can_update_claim_trust",
    ),
)
def test_case_contract_rejects_every_authority_flag(field_name, tmp_path):
    from brain.v5.harness_feedback_case_contracts import require_valid_harness_feedback_case
    from brain.v5.harness_feedback_cases import record_harness_feedback_case
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    write = record_harness_feedback_case(
        ws,
        _request(),
        actor=_actor(),
        now=datetime(2026, 7, 18, 8, 0, tzinfo=UTC),
    )
    record = _read_case(ws, write.record_ref)

    with pytest.raises(ValueError, match=field_name):
        require_valid_harness_feedback_case(replace(record, **{field_name: True}))


def test_changed_information_requires_explicit_revision_or_related_case(tmp_path):
    from brain.v5.harness_feedback_cases import (
        HarnessFeedbackCaseConflict,
        record_harness_feedback_case,
    )
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    now = datetime(2026, 7, 18, 8, 0, tzinfo=UTC)
    first = record_harness_feedback_case(ws, _request(), actor=_actor(), now=now)
    original_record = _read_case(ws, first.record_ref)
    changed = replace(
        _request(),
        actual_behavior="The compact entry omits both the convention and the source anchor.",
    )

    with pytest.raises(HarnessFeedbackCaseConflict, match="revision or related"):
        record_harness_feedback_case(
            ws,
            changed,
            actor=_actor(),
            now=now + timedelta(minutes=5),
        )

    revised = record_harness_feedback_case(
        ws,
        changed,
        actor=_actor(),
        now=now + timedelta(minutes=10),
        update_mode="revision",
        expected_hash=first.content_hash,
    )
    revised_record = _read_case(ws, revised.record_ref)
    assert revised.status == "revised"
    assert revised_record.case_id == original_record.case_id
    assert revised_record.created_at == original_record.created_at
    assert revised_record.updated_at != original_record.updated_at
    assert revised_record.supersedes_case_refs == (
        f"{first.record_ref}@sha256:{first.content_hash}",
    )


def test_related_cases_feed_a_read_only_repeated_problem_view(tmp_path):
    from brain.v5.harness_feedback_cases import (
        build_harness_feedback_review_view,
        record_harness_feedback_case,
    )
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    now = datetime(2026, 7, 18, 8, 0, tzinfo=UTC)
    first = record_harness_feedback_case(ws, _request(), actor=_actor(), now=now)
    related_request = replace(
        _request(),
        friction="The same missing convention also appears during explicit expansion.",
        actual_behavior="The expanded derivation omits the convention source anchor.",
    )
    related = record_harness_feedback_case(
        ws,
        related_request,
        actor=_actor(),
        now=now + timedelta(days=1),
        update_mode="related",
    )

    before = RecordRepository(ws, actor=_actor()).list("harness_feedback_cases").loaded_count
    view = build_harness_feedback_review_view(ws)
    after = RecordRepository(ws, actor=_actor()).list("harness_feedback_cases").loaded_count

    first_record = _read_case(ws, first.record_ref)
    related_record = _read_case(ws, related.record_ref)
    assert related.status == "created"
    assert related_record.case_id != first_record.case_id
    assert related_record.source_fingerprint == first_record.source_fingerprint
    assert related_record.related_case_refs == (first.record_ref,)
    assert before == after == 2
    assert view["kind"] == "harness_feedback_repeated_case_view"
    assert view["orientation_only"] is True
    assert view["can_update_claim_trust"] is False
    assert view["groups"] == [
        {
            "source_fingerprint": first_record.source_fingerprint,
            "problem_type": "missing_research_provenance",
            "affected_capability": "context_recall",
            "affected_record_family": "derivation_chains",
            "case_refs": sorted(
                [first.record_ref, related.record_ref]
            ),
            "count": 2,
            "statuses": ["pending_review"],
            "first_seen": "2026-07-18T08:00:00+00:00",
            "last_seen": "2026-07-19T08:00:00+00:00",
            "impacts": [
                "The model may silently mix two incompatible curvature conventions."
            ],
            "source_refs": [
                "derivation_chain:qg-chain-7",
                "source_asset:qg-note-2",
            ],
            "unresolved_case_refs": sorted([first.record_ref, related.record_ref]),
            "unresolved_count": 2,
        }
    ]


def test_new_source_fingerprint_requires_an_explicit_related_case_ref(tmp_path):
    from brain.v5.harness_feedback_cases import (
        HarnessFeedbackCaseConflict,
        record_harness_feedback_case,
    )
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    now = datetime(2026, 7, 18, 8, 0, tzinfo=UTC)
    first = record_harness_feedback_case(ws, _request(), actor=_actor(), now=now)
    new_source = replace(
        _request(),
        source_refs=("derivation_chain:qg-chain-8",),
        actual_behavior="A second derivation chain reproduces the missing source anchor.",
    )

    with pytest.raises(HarnessFeedbackCaseConflict, match="explicit related_case_refs"):
        record_harness_feedback_case(
            ws,
            new_source,
            actor=_actor(),
            now=now + timedelta(days=1),
            update_mode="related",
        )

    linked = record_harness_feedback_case(
        ws,
        replace(new_source, related_case_refs=(first.record_ref,)),
        actor=_actor(),
        now=now + timedelta(days=1),
        update_mode="related",
    )
    linked_record = _read_case(ws, linked.record_ref)
    assert linked.status == "created"
    assert linked.record_ref != first.record_ref
    assert linked_record.related_case_refs == (first.record_ref,)


def test_renderer_is_generic_and_fixture_driven(tmp_path):
    from brain.v5.harness_feedback_cases import (
        record_harness_feedback_case,
        render_harness_feedback_case,
    )
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    result = record_harness_feedback_case(
        ws,
        _request("nio"),
        actor=_actor(),
        now=datetime(2026, 7, 18, 8, 0, tzinfo=UTC),
    )
    record = _read_case(ws, result.record_ref)
    rendered = render_harness_feedback_case(record)
    expected = (FIXTURE_ROOT / "nio_case_expected.md").read_text(encoding="utf-8")
    expected = expected.replace("<CASE_ID>", record.case_id).replace(
        "<SOURCE_FINGERPRINT>", record.source_fingerprint
    )

    assert rendered == expected
    generic_write = record_harness_feedback_case(
        ws,
        _request(),
        actor=_actor(),
        now=datetime(2026, 7, 18, 9, 0, tzinfo=UTC),
    )
    generic_render = render_harness_feedback_case(_read_case(ws, generic_write.record_ref))
    assert "NiO" not in generic_render
    assert "FHI-aims" not in generic_render
    assert "LibRPA" not in generic_render
    for forbidden in (
        "Skill Distillation",
        "Skill Package",
        "Skill Install",
        "Implementation Roadmap",
        "Code Patch",
        "Trust Decision",
    ):
        assert forbidden not in rendered


def test_recording_case_cannot_invoke_any_skill_write_or_install_path(tmp_path, monkeypatch):
    from brain.v5 import (
        skill_candidates,
        skill_distillation,
        skill_distillation_records,
        skill_facade,
        skill_install_planning,
        skill_install_transactions,
        skill_package_artifacts,
        skill_patch_install_planning,
        skill_usage,
    )
    from brain.v5.harness_feedback_cases import record_harness_feedback_case
    from brain.v5.workspace import init_workspace

    def forbidden(*args, **kwargs):
        raise AssertionError("Harness Feedback crossed into the Skill lifecycle")

    for module, names in (
        (
            skill_distillation,
            ("build_procedural_skill_candidates", "propose_detected_procedural_skill"),
        ),
        (skill_distillation_records, ("record_skill_distillation_candidate",)),
        (skill_facade, ("invoke_skill_operation",)),
        (
            skill_candidates,
            (
                "propose_procedural_skill",
                "request_skill_install_review",
                "apply_project_skill",
            ),
        ),
        (skill_package_artifacts, ("record_skill_package_artifact", "rebuild_skill_package_preview")),
        (skill_install_planning, ("build_skill_install_plan",)),
        (skill_patch_install_planning, ("build_skill_patch_install_plan",)),
        (skill_install_transactions, ("apply_skill_install_plan",)),
        (skill_usage, ("build_skill_patch_proposal",)),
    ):
        for name in names:
            monkeypatch.setattr(module, name, forbidden)

    ws = init_workspace(tmp_path)
    result = record_harness_feedback_case(
        ws,
        _request(),
        actor=_actor(),
        now=datetime(2026, 7, 18, 8, 0, tzinfo=UTC),
    )
    assert result.status == "created"
