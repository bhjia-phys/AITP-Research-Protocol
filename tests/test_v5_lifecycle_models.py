from __future__ import annotations

from dataclasses import asdict

import pytest

from brain.v5.models import (
    CloseoutBoundaryItem,
    CrossTopicRelationRecord,
    RecallAuditRecord,
    RecordingCandidateBatchRecord,
    ResearchProgramRecord,
    SessionCloseoutRecord,
    SessionFocusSetRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import build_query_index
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.research_retrieval import exact_expand


ACTOR = RecordActor(actor_type="model", actor_id="m1-model-test", host="pytest")


def test_lifecycle_model_collections_are_isolated_and_trust_neutral():
    left = SessionFocusSetRecord(
        focus_set_id="focus-left",
        session_id="session-1",
        primary_topic_id="qg-a",
        focus_kind="primary_topic",
        focus_ref="topic:qg-a",
    )
    right = SessionFocusSetRecord(
        focus_set_id="focus-right",
        session_id="session-1",
        primary_topic_id="qg-a",
        focus_kind="primary_topic",
        focus_ref="topic:qg-a",
    )

    left.supporting_refs.append("topic:qg-b")

    assert right.supporting_refs == []
    assert left.claim_trust_transfer == "forbidden"
    assert left.can_update_active_claim is False
    assert left.can_update_claim_trust is False


def test_lifecycle_models_reject_trust_authority_overrides():
    relation_fields = {
        "relation_id": "bridge-1",
        "source_topic_id": "qg-a",
        "target_topic_id": "qg-b",
        "source_ref": "derivation_chain:d1",
        "target_ref": "question:q1",
        "relation_kind": "method_applicability",
        "transfer_rationale": "The same convention may apply after target-side checks.",
        "applicability_boundary": "This bridge does not transfer a proved claim.",
        "revalidation_requirements": ["check target conventions"],
    }

    with pytest.raises(ValueError, match="claim_trust_transfer"):
        CrossTopicRelationRecord(**relation_fields, claim_trust_transfer="allowed")
    with pytest.raises(ValueError, match="can_update_claim_trust"):
        CrossTopicRelationRecord(**relation_fields, can_update_claim_trust=True)
    with pytest.raises(ValueError, match="can_update_claim_trust"):
        CloseoutBoundaryItem(
            text="Unreviewed extrapolation",
            boundary_class="cannot_say",
            source_refs=["claim:c1"],
            can_update_claim_trust=True,
        )


def test_all_lifecycle_families_round_trip_and_exact_expand(tmp_path):
    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    repository = RecordRepository(ws, actor=ACTOR)
    boundary = CloseoutBoundaryItem(
        text="The finite-n derivation is recorded.",
        boundary_class="can_say",
        source_refs=["claim:c1"],
        scope="finite_n",
    )
    records = {
        "research_programs": ResearchProgramRecord(
            program_id="program-1",
            title="Replica and operator-algebra program",
            primary_topic_ids=["qg-a"],
            supporting_topic_ids=["qg-b"],
        ),
        "session_focus_sets": SessionFocusSetRecord(
            focus_set_id="focus-1",
            session_id="session-1",
            primary_topic_id="qg-a",
            focus_kind="primary_topic",
            focus_ref="topic:qg-a",
            supporting_refs=["topic:qg-b"],
            program_id="program-1",
        ),
        "cross_topic_relations": CrossTopicRelationRecord(
            relation_id="bridge-1",
            source_topic_id="qg-a",
            target_topic_id="qg-b",
            source_ref="derivation_chain:d1",
            target_ref="question:q1",
            relation_kind="method_applicability",
            transfer_rationale="The same convention may apply after target-side checks.",
            applicability_boundary="This bridge does not transfer a proved claim.",
            revalidation_requirements=["check target conventions"],
        ),
        "session_closeouts": SessionCloseoutRecord(
            closeout_id="closeout-1",
            session_id="session-1",
            topic_id="qg-a",
            milestone_id="milestone-1",
            can_say=[boundary],
            source_record_refs=["claim:c1"],
        ),
        "recall_audits": RecallAuditRecord(
            audit_id="audit-1",
            session_id="session-1",
            topic_id="qg-a",
            query_text="recover finite-n replica work",
            normalized_intent="recover_prior_result",
            scope_refs=["topic:qg-a"],
        ),
        "recording_candidate_batches": RecordingCandidateBatchRecord(
            batch_id="batch-1",
            session_id="session-1",
            topic_id="qg-a",
            milestone_id="milestone-1",
            candidates=[{"candidate_kind": "claim", "text": "finite-n boundary"}],
            dedup_keys=["claim:finite-n-boundary"],
        ),
    }

    results = [
        repository.write(family, record, body=f"# {family}\n")
        for family, record in records.items()
    ]
    build_query_index(ws)
    refs = [result.record_ref for result in results]
    expanded = exact_expand(ws, refs, limit=10)
    closeout = repository.read("session_closeout:closeout-1")

    assert all(result.status == "created" for result in results)
    assert {item.record_ref for item in expanded.items} == set(refs)
    assert expanded.coverage.exhaustive is True
    assert isinstance(closeout.record, SessionCloseoutRecord)
    assert isinstance(closeout.record.can_say[0], CloseoutBoundaryItem)
    assert asdict(closeout.record.can_say[0]) == asdict(boundary)
