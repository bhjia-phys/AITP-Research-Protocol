from __future__ import annotations

import json


def test_ima_connector_catalog_declares_theory_literature_protocol():
    from brain.v5.knowledge_connectors import describe_knowledge_connectors
    from brain.v5.public_surfaces import require_valid_public_surface

    catalog = describe_knowledge_connectors()
    connectors = {connector["connector_id"]: connector for connector in catalog["connectors"]}
    ima = connectors["ima"]
    qft = connectors["qft_literature"]
    qg = connectors["quantum_gravity_literature"]
    librpa = connectors["librpa_research_notes"]

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
    assert qft["backend_role"] == "domain_literature_connector"
    assert "equation_anchors" in qft["expected_retrieval_targets"]
    assert "proof_obligation_records" in qft["required_kernel_followup_records"]
    assert qg["recommended_when"] == "for_quantum_gravity_or_holography_literature_learning"
    assert "paper_pair_reading_notes" in qg["expected_retrieval_targets"]
    assert librpa["skill_ref"] == "oh-my-librpa"
    assert "lane_manifests" in librpa["expected_retrieval_targets"]
    assert librpa["truth_policy"]["source_backed_evidence_required"] is True


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


def test_execution_brief_recommends_domain_specific_literature_connectors(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "quantum-gravity", context_id="qg-literature", title="Quantum Gravity")
    claim = create_claim(
        ws,
        topic_id="quantum-gravity",
        statement="Compare the quantum gravity wormhole literature with local notes before making a claim.",
        evidence_profile="literature_synthesis",
        confidence_state="learning",
        active_uncertainty="source scope and speculative boundaries are unclear",
    )
    bind_session(ws, "s1", topic_id="quantum-gravity", context_id="qg-literature", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    connectors = brief["known_context"]["knowledge_connectors"]
    connector_ids = [connector["connector_id"] for connector in connectors]
    assert connector_ids == ["quantum_gravity_literature"]
    assert connectors[0]["truth_policy"]["retrieved_notes_are_truth_source"] is False
    assert connectors[0]["binding_status"] == "unconfigured"
    assert connectors[0]["configured_binding_count"] == 0
    assert brief["known_context"]["context_compilation_profiles"][0]["orientation_only"] is True


def test_workspace_connector_binding_is_file_backed_configuration_surface(tmp_path):
    from brain.v5.knowledge_connector_bindings import bind_knowledge_connector, list_knowledge_connector_bindings
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)

    empty = require_valid_public_surface(
        "knowledge_connector_binding_registry",
        list_knowledge_connector_bindings(ws),
    )
    bound = require_valid_public_surface(
        "knowledge_connector_binding_registry",
        bind_knowledge_connector(
            ws,
            connector_id="qft_literature",
            root_uri="file:///D:/theory/qft",
            corpus_id="qft-local",
            label="Local QFT notes",
            file_globs=["**/*.pdf", "**/*.md"],
            domain_hints=["qft"],
            topic_hints=["renormalization"],
        ),
    )
    listed = require_valid_public_surface(
        "knowledge_connector_binding_registry",
        list_knowledge_connector_bindings(ws, connector_id="qft_literature", include_connector_catalog=True),
    )

    assert empty["binding_count"] == 0
    assert bound["state_effect"] == "knowledge_connector_binding_config_write"
    assert bound["binding_count"] == 1
    assert bound["bindings"][0]["connector_id"] == "qft_literature"
    assert bound["bindings"][0]["root_uri"] == "file:///D:/theory/qft"
    assert bound["bindings"][0]["orientation_only"] is True
    assert bound["can_create_evidence"] is False
    assert listed["bindings"][0]["file_globs"] == ["**/*.pdf", "**/*.md"]
    connector_counts = {connector["connector_id"]: connector["configured_binding_count"] for connector in listed["connectors"]}
    assert connector_counts["qft_literature"] == 1
    assert (tmp_path / ".aitp" / "knowledge_connectors" / "bindings.json").exists()


def test_execution_brief_exposes_configured_connector_binding(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.knowledge_connector_bindings import bind_knowledge_connector
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    bind_knowledge_connector(
        ws,
        connector_id="quantum_gravity_literature",
        root_uri="file:///D:/theory/quantum-gravity",
        corpus_id="qg-local",
        file_globs=["**/*.pdf"],
    )
    create_topic(ws, "quantum-gravity", context_id="qg-literature", title="Quantum Gravity")
    claim = create_claim(
        ws,
        topic_id="quantum-gravity",
        statement="Compare holography papers with my quantum gravity notes before making a claim.",
        evidence_profile="literature_synthesis",
        confidence_state="learning",
        active_uncertainty="source scope and speculative boundaries are unclear",
    )
    bind_session(ws, "s1", topic_id="quantum-gravity", context_id="qg-literature", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    connector = brief["known_context"]["knowledge_connectors"][0]
    action = brief["next_action_candidates"][0]
    assert connector["connector_id"] == "quantum_gravity_literature"
    assert connector["binding_status"] == "configured"
    assert connector["configured_binding_count"] == 1
    assert connector["configured_bindings"][0]["root_uri"] == "file:///D:/theory/quantum-gravity"
    assert action["action"] == "consult_knowledge_connector"
    assert action["binding_status"] == "configured"
    assert action["configured_binding_count"] == 1


def test_execution_brief_recommends_librpa_notes_connector_for_method_claim(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="Continue the LibRPA QSGW benchmark and inspect prior run reports.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="prior failure route and lane policy need review",
    )
    bind_session(ws, "s1", topic_id="librpa-gw", context_id="gw-methods", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    connector_ids = [connector["connector_id"] for connector in brief["known_context"]["knowledge_connectors"]]
    assert connector_ids == ["librpa_research_notes"]
    assert "artifact" in brief["known_context"]["knowledge_connectors"][0]["required_kernel_followup_records"]


def test_cli_knowledge_connectors_returns_catalog(tmp_path, capsys):
    from brain.v5.cli import main

    assert main(["--base", str(tmp_path), "knowledge", "connectors"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["kind"] == "knowledge_connector_catalog"
    assert payload["connectors"][0]["connector_id"] == "ima"
    assert {connector["connector_id"] for connector in payload["connectors"]} >= {
        "qft_literature",
        "quantum_gravity_literature",
        "librpa_research_notes",
    }


def test_cli_knowledge_connector_bindings_bind_and_list(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.public_surfaces import require_valid_public_surface

    assert main(
        [
            "--base",
            str(tmp_path),
            "knowledge",
            "bind",
            "--connector",
            "qft_literature",
            "--root",
            "file:///D:/theory/qft",
            "--corpus-id",
            "qft-local",
            "--glob",
            "**/*.pdf",
        ]
    ) == 0
    bound = json.loads(capsys.readouterr().out)
    assert main(["--base", str(tmp_path), "knowledge", "bindings", "--connector", "qft_literature"]) == 0
    listed = json.loads(capsys.readouterr().out)

    assert require_valid_public_surface("knowledge_connector_binding_registry", bound) == bound
    assert require_valid_public_surface("knowledge_connector_binding_registry", listed) == listed
    assert listed["binding_count"] == 1
    assert listed["bindings"][0]["corpus_id"] == "qft-local"


def test_mcp_knowledge_connector_catalog_returns_valid_surface():
    from brain.v5.mcp_tools import aitp_v5_list_knowledge_connectors
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = aitp_v5_list_knowledge_connectors()

    assert payload["ok"] is True
    assert require_valid_public_surface("knowledge_connector_catalog", payload) == payload


def test_mcp_knowledge_connector_binding_returns_valid_surface(tmp_path):
    from brain.v5.mcp_knowledge_bindings import (
        aitp_v5_bind_knowledge_connector,
        aitp_v5_list_knowledge_connector_bindings,
    )
    from brain.v5.public_surfaces import require_valid_public_surface

    bound = aitp_v5_bind_knowledge_connector(
        str(tmp_path),
        connector_id="quantum_gravity_literature",
        root_uri="file:///D:/theory/qg",
        corpus_id="qg-local",
        file_globs=["**/*.pdf"],
    )
    listed = aitp_v5_list_knowledge_connector_bindings(str(tmp_path), connector_id="quantum_gravity_literature")

    assert require_valid_public_surface("knowledge_connector_binding_registry", bound) == bound
    assert require_valid_public_surface("knowledge_connector_binding_registry", listed) == listed
    assert listed["bindings"][0]["connector_id"] == "quantum_gravity_literature"
