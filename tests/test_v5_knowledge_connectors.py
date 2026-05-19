from __future__ import annotations

import json


def test_ima_connector_catalog_declares_theory_literature_protocol():
    from brain.v5.knowledge_connectors import describe_knowledge_connectors
    from brain.v5.public_surfaces import require_valid_public_surface

    catalog = describe_knowledge_connectors()
    connectors = {connector["connector_id"]: connector for connector in catalog["connectors"]}
    ima = connectors["ima"]

    assert require_valid_public_surface("knowledge_connector_catalog", catalog) == catalog
    assert catalog["kind"] == "knowledge_connector_catalog"
    assert catalog["truth_source"] == "builtin_connector_registry"
    assert catalog["summary_inputs_trusted"] is False
    assert ima["backend_role"] == "example_external_backend"
    assert ima["is_required"] is False
    assert ima["skill_ref"] == "ima-skill"
    assert "literature_learning" in ima["supported_activities"]
    assert "theory_discussion" in ima["supported_activities"]
    assert ima["truth_policy"]["retrieved_notes_are_truth_source"] is False
    assert ima["truth_policy"]["source_backed_evidence_required"] is True
    assert "retrieve_before_answering" in ima["protocol_hooks"]
    assert "capture_nontrivial_learning" in ima["protocol_hooks"]
    assert "reference_location_records" in ima["required_kernel_followup_records"]
    assert "external_note_uri" in ima["location_ref_targets"]


def test_execution_brief_exposes_ima_for_literature_learning_claim(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Learn the FQHE composite-fermion literature and compare it with my notes.",
        evidence_profile="literature_synthesis",
        confidence_state="learning",
        active_uncertainty="which conventions and benchmark results are already in my notes",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    connectors = brief["known_context"]["knowledge_connectors"]
    ima = connectors[0]
    assert ima["connector_id"] == "ima"
    assert ima["recommended_when"] == "before_theory_literature_discussion"
    assert "existing_notes" in ima["expected_retrieval_targets"]
    assert "source_refs" in ima["required_kernel_followup_records"]


def test_execution_brief_recommends_generic_connector_action_for_literature_claim(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Before judging this FQHE idea, look up prior papers and where my notes are stored.",
        evidence_profile="literature_synthesis",
        confidence_state="learning",
        active_uncertainty="paper conventions and note locations are unclear",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    action = brief["next_action_candidates"][0]
    assert action["action"] == "consult_knowledge_connector"
    assert action["connector_ids"] == ["ima"]
    assert action["backend_required"] is False
    assert "external_note_uri" in action["location_ref_targets"]
    assert "reference_location_records" in action["required_kernel_followup_records"]
    assert "orientation" in action["expected_evidence_gain"]


def test_cli_knowledge_connectors_returns_catalog(tmp_path, capsys):
    from brain.v5.cli import main

    assert main(["--base", str(tmp_path), "knowledge", "connectors"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["kind"] == "knowledge_connector_catalog"
    assert payload["connectors"][0]["connector_id"] == "ima"


def test_mcp_knowledge_connector_catalog_returns_valid_surface():
    from brain.v5.mcp_tools import aitp_v5_list_knowledge_connectors
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = aitp_v5_list_knowledge_connectors()

    assert payload["ok"] is True
    assert require_valid_public_surface("knowledge_connector_catalog", payload) == payload
