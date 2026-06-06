from __future__ import annotations


def test_exploratory_record_is_orientation_only_and_public(tmp_path):
    from dataclasses import asdict

    from brain.v5.contracts import validate_exploratory_record
    from brain.v5.exploration import exploratory_record_payload, record_exploratory_record
    from brain.v5.mcp_tools import aitp_v5_record_exploratory_record
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")

    record = record_exploratory_record(
        ws,
        topic_id="fqhe",
        claim_id="claim-fqhe",
        session_id="s1",
        exploration_type="question_decomposition",
        title="Break the original question into traceable subquestions",
        focal_question="Which local definitions are needed before the relation path is meaningful?",
        summary="The initial physics question is being split into local checks.",
        original_question="Does sector counting identify the edge CFT?",
        local_question="Which sector labels need reconstruction?",
        reasoning_moves=["why-question decomposition", "relation-path brainstorming"],
        backtrace_targets=["object:counting-sequence", "object:edge-cft"],
        candidate_paths=["counting sequence -> sector labels -> edge CFT"],
        relation_path_questions=["What intermediate convention links counting sectors to CFT labels?"],
        definition_boundary_questions=["Where is the sector-label convention defined?"],
        derivation_backtrace_questions=["Which step assumes finite-size sector stability?"],
        source_dependency_questions=["Which source fixes the sector-label notation?"],
        original_question_guard=["Keep sector-label reconstruction tied to edge-CFT identification."],
        unresolved_points=["finite-size aliasing"],
        next_actions=["record a source backtrace step"],
    )
    payload = exploratory_record_payload(record)

    assert validate_exploratory_record(payload).ok is True
    assert require_valid_public_surface("exploratory_record", payload) == payload
    assert asdict(record)["orientation_only"] is True
    assert asdict(record)["can_update_claim_trust"] is False
    assert payload["reasoning_moves"] == ["why-question decomposition", "relation-path brainstorming"]
    assert payload["backtrace_targets"] == ["object:counting-sequence", "object:edge-cft"]
    assert payload["relation_path_questions"] == [
        "What intermediate convention links counting sectors to CFT labels?"
    ]
    assert payload["definition_boundary_questions"] == ["Where is the sector-label convention defined?"]
    assert payload["derivation_backtrace_questions"] == ["Which step assumes finite-size sector stability?"]
    assert payload["source_dependency_questions"] == ["Which source fixes the sector-label notation?"]
    assert payload["original_question_guard"] == [
        "Keep sector-label reconstruction tied to edge-CFT identification."
    ]

    mcp_payload = aitp_v5_record_exploratory_record(
        str(tmp_path),
        topic_id="fqhe",
        claim_id="claim-fqhe",
        session_id="s1",
        exploration_type="backtrace_step",
        title="Trace sector label source",
        focal_question="Where is the sector label convention defined?",
        summary="Backtrace remains open until the source definition is found.",
        original_question="Does sector counting identify the edge CFT?",
        local_question="Find the sector label definition.",
        reasoning_moves=["source dependency backtrace", "bidirectional definition backtrace"],
        backtrace_targets=["source:edge-counting"],
        definition_boundary_questions=["Which paper defines the sector labels?"],
        source_dependency_questions=["Which cited source introduces the notation?"],
        original_question_guard=["Do not turn source lookup into a different CFT-identification question."],
        unresolved_points=["definition source not located"],
    )

    assert mcp_payload["kind"] == "exploratory_record"
    assert mcp_payload["exploration_type"] == "backtrace_step"
    assert mcp_payload["reasoning_moves"] == [
        "source dependency backtrace",
        "bidirectional definition backtrace",
    ]
    assert mcp_payload["backtrace_targets"] == ["source:edge-counting"]
    assert mcp_payload["definition_boundary_questions"] == ["Which paper defines the sector labels?"]
    assert mcp_payload["source_dependency_questions"] == ["Which cited source introduces the notation?"]
    assert mcp_payload["original_question_guard"] == [
        "Do not turn source lookup into a different CFT-identification question."
    ]
    assert mcp_payload["orientation_only"] is True
    assert mcp_payload["can_update_claim_trust"] is False


def test_exploratory_record_contract_rejects_trust_mutation():
    from brain.v5.contracts import validate_exploratory_record

    payload = {
        "ok": True,
        "kind": "exploratory_record",
        "record_id": "exploratory-bad",
        "topic_id": "fqhe",
        "claim_id": "claim-fqhe",
        "session_id": "s1",
        "exploration_type": "relation_path_brainstorm",
        "title": "Bad trust mutation",
        "focal_question": "Can this update trust?",
        "summary": "No.",
        "status": "open",
        "object_ids": [],
        "relation_ids": [],
        "source_refs": [],
        "artifact_ids": [],
        "parent_record_ids": [],
        "derived_record_ids": [],
        "reasoning_moves": [],
        "backtrace_targets": [],
        "candidate_paths": [],
        "relation_path_questions": [],
        "definition_boundary_questions": [],
        "derivation_backtrace_questions": [],
        "source_dependency_questions": [],
        "original_question_guard": [],
        "unresolved_points": [],
        "next_actions": [],
        "metadata": {},
        "orientation_only": False,
        "can_update_claim_trust": True,
    }

    result = validate_exploratory_record(payload)

    assert result.ok is False
    paths = {issue.path for issue in result.issues}
    assert "exploratory_record.orientation_only" in paths
    assert "exploratory_record.can_update_claim_trust" in paths
