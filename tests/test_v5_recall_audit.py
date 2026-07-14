from __future__ import annotations

from dataclasses import replace

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="model", actor_id="recall-audit-test", host="pytest")


def _seed_workspace(tmp_path):
    from brain.v5.lifecycle_models import (
        CrossTopicRelationRecord,
        ResearchProgramRecord,
        SessionFocusSetRecord,
    )
    from brain.v5.query_index import build_query_index
    from brain.v5.research_scope import (
        record_cross_topic_relation,
        record_research_program,
        record_session_focus_set,
    )
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "target", context_id="formal-theory", title="Target replica problem")
    create_topic(ws, "source", context_id="formal-theory", title="Reviewed source method")
    create_topic(ws, "candidate", context_id="formal-theory", title="Unreviewed analogy")
    target_claim = create_claim(
        ws,
        topic_id="target",
        statement="The finite replica diagnostic is controlled in the target scope.",
        evidence_profile="formal_theory",
        confidence_state="finite_evidence",
        active_uncertainty="The continuation remains open.",
    )
    source_claim = create_claim(
        ws,
        topic_id="source",
        statement="The finite replica source method is valid under source assumptions.",
        evidence_profile="formal_theory",
        confidence_state="conditional",
        active_uncertainty="Target transfer requires revalidation.",
    )
    candidate_claim = create_claim(
        ws,
        topic_id="candidate",
        statement="A finite replica analogy is only an unreviewed discovery candidate.",
        evidence_profile="formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="The analogy has not been reviewed.",
    )
    bind_session(
        ws,
        "s1",
        topic_id="target",
        context_id="formal-theory",
        active_claim=target_claim.claim_id,
    )
    record_research_program(
        ws,
        ResearchProgramRecord(
            program_id="program-1",
            title="Replica method transfer",
            primary_topic_ids=["target"],
            supporting_topic_ids=["source"],
            scientific_boundary="Source conclusions never transfer claim trust.",
            inclusion_rules=["reviewed bridges only"],
            review_status="reviewed",
        ),
        actor=_actor(),
    )
    record_cross_topic_relation(
        ws,
        CrossTopicRelationRecord(
            relation_id="bridge-reviewed",
            source_topic_id="source",
            target_topic_id="target",
            source_ref=f"claim:{source_claim.claim_id}",
            target_ref=f"claim:{target_claim.claim_id}",
            relation_kind="method_candidate",
            transfer_rationale="The finite replica technique may be reusable.",
            applicability_boundary="Method only; no conclusion transfer.",
            revalidation_requirements=["rederive target assumptions"],
            status="reviewed",
        ),
        actor=_actor(),
    )
    record_cross_topic_relation(
        ws,
        CrossTopicRelationRecord(
            relation_id="bridge-pending",
            source_topic_id="candidate",
            target_topic_id="target",
            source_ref=f"claim:{candidate_claim.claim_id}",
            target_ref=f"claim:{target_claim.claim_id}",
            relation_kind="analogy",
            transfer_rationale="The analogy might orient a later review.",
            applicability_boundary="Discovery only until human review.",
            revalidation_requirements=["review bridge", "derive target map"],
            status="pending_review",
        ),
        actor=_actor(),
    )
    record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id="focus-1",
            session_id="s1",
            primary_topic_id="target",
            focus_kind="claim",
            focus_ref=f"claim:{target_claim.claim_id}",
            supporting_refs=[
                "cross_topic_relation:bridge-reviewed",
                "cross_topic_relation:bridge-pending",
            ],
            program_id="program-1",
        ),
        actor=_actor(),
    )
    build_query_index(ws)
    return {
        "ws": ws,
        "target_ref": f"claim:{target_claim.claim_id}",
        "source_ref": f"claim:{source_claim.claim_id}",
        "candidate_ref": f"claim:{candidate_claim.claim_id}",
    }


def _request(seed, **overrides):
    from brain.v5.recall_audit import RecallRequest

    values = {
        "session_id": "s1",
        "query_text": "finite replica",
        "normalized_intent": "recover_prior_result",
        "required_families": ("claims", "cross_topic_relations"),
        "exact_refs": (
            seed["target_ref"],
            seed["source_ref"],
            "cross_topic_relation:bridge-pending",
        ),
        "include_program_scope": True,
        "include_discovery": True,
        "top_k": 20,
    }
    values.update(overrides)
    return RecallRequest(**values)


def test_recall_audit_persists_ordered_isolated_lanes_and_coverage(tmp_path):
    from brain.v5.lifecycle_models import RecallAuditRecord
    from brain.v5.record_repository import RecordRepository
    from brain.v5.recall_audit import run_recall_audit

    seed = _seed_workspace(tmp_path)
    audit = run_recall_audit(seed["ws"], _request(seed), actor=_actor())
    repository = RecordRepository(seed["ws"], actor=_actor())
    persisted = repository.read(f"recall_audit:{audit.audit_id}")

    assert isinstance(audit, RecallAuditRecord)
    assert persisted.status == "found"
    assert persisted.record == audit
    assert audit.query_text == "finite replica"
    assert audit.normalized_intent == "recover_prior_result"
    assert audit.focus_set_ref == "session_focus_set:focus-1"
    assert audit.program_id == "program-1"
    assert audit.required_families == ["claims", "cross_topic_relations"]
    assert audit.required_exact_refs == [
        seed["target_ref"],
        seed["source_ref"],
        "cross_topic_relation:bridge-pending",
    ]
    assert [lane["lane"] for lane in audit.lanes] == [
        "primary",
        "program_shared",
        "discovery",
    ]
    primary, program, discovery = audit.lanes
    assert seed["target_ref"] in primary["top_refs"]
    assert seed["source_ref"] in program["top_refs"]
    assert "cross_topic_relation:bridge-pending" in discovery["top_refs"]
    assert seed["target_ref"] not in discovery["top_refs"]
    assert discovery["exact_only"] is True
    assert all("record" not in item for lane in audit.lanes for item in lane["results"])
    assert audit.index_generation >= 1
    assert audit.canonical_watermark
    assert audit.retrieval_scope_token
    assert set(audit.family_state_tokens) == set(audit.checked_families)
    assert set(audit.family_content_watermarks) == set(audit.checked_families)
    assert audit.dirty_families == []
    assert audit.unchecked_families == []
    assert audit.missing_exact_refs == []
    assert audit.records_read == sum(lane["records_read"] for lane in audit.lanes)
    assert audit.read_errors == []
    assert audit.truncated is False
    assert audit.stale is False
    assert audit.content_verified is True
    assert audit.exhaustive is True
    assert audit.can_claim_no_result is False
    assert audit.can_update_claim_trust is False


def test_discovery_lane_is_not_run_without_explicit_opt_in(tmp_path):
    from brain.v5.recall_audit import run_recall_audit

    seed = _seed_workspace(tmp_path)
    audit = run_recall_audit(
        seed["ws"],
        _request(seed, exact_refs=(), include_discovery=False),
        actor=_actor(),
    )

    assert [lane["lane"] for lane in audit.lanes] == ["primary", "program_shared"]
    assert "cross_topic_relation:bridge-pending" not in audit.top_refs
    assert "cross_topic_relation:bridge-pending" in audit.excluded_candidates


def test_discovery_can_run_without_enabling_program_lane(tmp_path):
    from brain.v5.recall_audit import run_recall_audit

    seed = _seed_workspace(tmp_path)
    audit = run_recall_audit(
        seed["ws"],
        _request(
            seed,
            exact_refs=(seed["target_ref"], "cross_topic_relation:bridge-pending"),
            include_program_scope=False,
            include_discovery=True,
        ),
        actor=_actor(),
    )

    assert [lane["lane"] for lane in audit.lanes] == ["primary", "discovery"]
    assert [lane["order"] for lane in audit.lanes] == [0, 1]
    assert "cross_topic_relation:bridge-pending" in audit.lanes[1]["top_refs"]


@pytest.mark.parametrize("action", ["major_conclusion", "expensive_run"])
def test_required_recall_failure_blocks_high_cost_action(tmp_path, action):
    from brain.v5.recall_audit import evaluate_recall_prerequisite, run_recall_audit

    seed = _seed_workspace(tmp_path)
    audit = run_recall_audit(seed["ws"], _request(seed), actor=_actor())
    stale = replace(audit, stale=True, exhaustive=False, content_verified=False)

    decision = evaluate_recall_prerequisite(stale, action)

    assert decision.allowed is False
    assert decision.reason_code == "required_recall_not_exhaustive"
    assert "run_recall_audit" in decision.required_actions
    assert decision.audit_ref == f"recall_audit:{audit.audit_id}"
    assert decision.can_update_claim_trust is False


def test_gate_prioritizes_missing_family_exact_ref_read_error_and_truncation(tmp_path):
    from brain.v5.recall_audit import evaluate_recall_prerequisite, run_recall_audit

    seed = _seed_workspace(tmp_path)
    audit = run_recall_audit(seed["ws"], _request(seed), actor=_actor())
    cases = [
        (
            replace(
                audit,
                required_families=[*audit.required_families, "tool_runs"],
                unchecked_families=["tool_runs"],
                exhaustive=False,
            ),
            "required_family_unchecked",
        ),
        (
            replace(audit, missing_exact_refs=["tool_run:missing"], exhaustive=False),
            "required_exact_ref_missing",
        ),
        (
            replace(audit, read_errors=["malformed claim"], exhaustive=False),
            "recall_read_error",
        ),
        (replace(audit, truncated=True, exhaustive=False), "recall_truncated"),
    ]

    for candidate, reason in cases:
        decision = evaluate_recall_prerequisite(candidate, "major_conclusion")
        assert decision.allowed is False
        assert decision.reason_code == reason
        assert decision.required_actions
        assert decision.can_update_claim_trust is False

    allowed = evaluate_recall_prerequisite(audit, "major_conclusion")
    assert allowed.allowed is True
    assert allowed.reason_code == "recall_prerequisite_satisfied"


def test_stale_index_and_missing_exact_ref_are_persisted_fail_closed(tmp_path):
    from brain.v5.models import ToolRunRecord
    from brain.v5.recall_audit import evaluate_recall_prerequisite, run_recall_audit
    from brain.v5.store import write_record

    seed = _seed_workspace(tmp_path)
    write_record(
        seed["ws"].registry_dir("tool_runs") / "unindexed-run.md",
        ToolRunRecord(
            run_id="unindexed-run",
            recipe_id="deep-recall",
            tool_family="python",
            tool_name="recall-probe",
            topic_id="target",
            claim_id=seed["target_ref"].split(":", 1)[1],
            outputs={"summary": "finite replica result bypassed the index"},
        ),
    )
    stale = run_recall_audit(
        seed["ws"],
        _request(
            seed,
            required_families=("tool_runs",),
            exact_refs=("tool_run:unindexed-run",),
            include_program_scope=False,
            include_discovery=False,
        ),
        actor=_actor(),
    )
    missing = run_recall_audit(
        seed["ws"],
        _request(
            seed,
            required_families=("tool_runs",),
            exact_refs=("tool_run:missing",),
            include_program_scope=False,
            include_discovery=False,
        ),
        actor=_actor(),
    )

    assert stale.stale is True
    assert stale.content_verified is False
    assert stale.exhaustive is False
    assert evaluate_recall_prerequisite(stale, "expensive_run").allowed is False
    assert missing.missing_exact_refs == ["tool_run:missing"]
    assert missing.exhaustive is False
    assert (
        evaluate_recall_prerequisite(missing, "major_conclusion").reason_code
        == "required_exact_ref_missing"
    )


def test_recall_audit_cannot_self_certify_its_own_family(tmp_path):
    from brain.v5.recall_audit import evaluate_recall_prerequisite, run_recall_audit

    seed = _seed_workspace(tmp_path)
    audit = run_recall_audit(
        seed["ws"],
        _request(
            seed,
            query_text="prior recall audit",
            required_families=("recall_audits",),
            exact_refs=(),
            include_program_scope=False,
            include_discovery=False,
        ),
        actor=_actor(),
    )

    assert audit.content_verified is True
    assert audit.exhaustive is False
    assert audit.can_claim_no_result is False
    assert audit.lanes[0]["self_certification_blocked"] is True
    decision = evaluate_recall_prerequisite(audit, "major_conclusion")
    assert decision.allowed is False
    assert decision.reason_code == "required_recall_not_exhaustive"


def test_context_no_prior_result_language_requires_persisted_exhaustive_audit(tmp_path):
    from brain.v5.context_compiler import ContextRequest, compile_research_context
    from brain.v5.context_pack import build_aitp_context_pack
    from brain.v5.recall_audit import run_recall_audit

    seed = _seed_workspace(tmp_path)
    audit = run_recall_audit(
        seed["ws"],
        _request(
            seed,
            query_text="absent tool workflow result",
            normalized_intent="recover_prior_workflow",
            required_families=("tool_runs",),
            exact_refs=(),
            include_program_scope=False,
            include_discovery=False,
        ),
        actor=_actor(),
    )
    audit_ref = f"recall_audit:{audit.audit_id}"
    without_audit = compile_research_context(
        seed["ws"],
        ContextRequest(session_id="s1", families=("tool_runs",)),
    )
    with_audit = compile_research_context(
        seed["ws"],
        ContextRequest(
            session_id="s1",
            families=("tool_runs",),
            recall_audit_ref=audit_ref,
        ),
    )
    pack = build_aitp_context_pack(
        seed["ws"],
        "s1",
        recall_audit_ref=audit_ref,
    )

    assert audit.top_refs == []
    assert audit.can_claim_no_result is True
    assert without_audit.can_claim_no_prior_result is False
    assert with_audit.can_claim_no_prior_result is True
    assert with_audit.coverage["recall_audit_ref"] == audit_ref
    assert with_audit.coverage["recall_query_text"] == "absent tool workflow result"
    assert with_audit.coverage["recall_normalized_intent"] == "recover_prior_workflow"
    assert with_audit.coverage["recall_exhaustive"] is True
    assert audit_ref in with_audit.record_refs
    assert audit_ref in with_audit.next_level_handles["exact_expansion_refs"]
    assert audit_ref in with_audit.markdown
    assert "recover_prior_workflow" in with_audit.markdown
    assert "absent tool workflow result" in with_audit.markdown
    assert pack["recall_audit_ref"] == audit_ref
    assert pack["retrieval_coverage"]["recall_can_claim_no_result"] is True
