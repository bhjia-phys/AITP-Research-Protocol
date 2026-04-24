"""Tests for Phase 4 visualization tools."""

from pathlib import Path

import pytest

from brain.mcp_server import (
    aitp_advance_l3_subplane,
    aitp_advance_to_l1,
    aitp_advance_to_l3,
    aitp_bootstrap_topic,
    aitp_create_l2_edge,
    aitp_create_l2_node,
    aitp_create_l2_tower,
    aitp_visualize_derivation_chain,
    aitp_visualize_eft_tower,
    aitp_visualize_knowledge_graph,
    _slugify,
    _topic_root,
    _write_md,
)


TOPIC = "test-topic"


def _setup_td(tmp_path: Path) -> str:
    (tmp_path / "topics").mkdir()
    return str(tmp_path)


def _bootstrap(td):
    aitp_bootstrap_topic(td, TOPIC, "Test Topic", "What is X?", "theory")
    _fill_l0_gate(td)
    aitp_advance_to_l1(td, TOPIC)


def _fill_l0_gate(td):
    tr = _topic_root(td, TOPIC)
    _write_md(
        tr / "L0" / "source_registry.md",
        {"artifact_kind": "l0_source_registry", "stage": "L0",
         "source_count": 1, "search_status": "complete"},
        "# Source Registry\n\n## Search Methodology\narxiv\n\n"
        "## Source Inventory\npaper-a\n\n## Coverage Assessment\nAdequate\n\n"
        "## Gaps And Next Sources\nNone\n",
    )
    _write_md(
        tr / "L0" / "sources" / "paper-a.md",
        {"artifact_kind": "l0_source", "source_type": "paper",
         "slug": "paper-a", "short_title": "Paper A"},
        "# Paper A\n\nA source.\n",
    )


def _fill_l1_gate(td):
    tr = _topic_root(td, TOPIC)
    _write_md(
        tr / "L1" / "question_contract.md",
        {"artifact_kind": "l1_question_contract", "stage": "L1",
         "bounded_question": "What is X?", "scope_boundaries": "One model.",
         "target_quantities": "Energy spectrum."},
        "# Question Contract\n\n## Bounded Question\nWhat is X?\n\n"
        "## Scope Boundaries\nOne model.\n\n## Target Quantities Or Claims\nEnergy spectrum.\n",
    )
    _write_md(
        tr / "L1" / "source_basis.md",
        {"artifact_kind": "l1_source_basis", "stage": "L1",
         "core_sources": "paper-a", "peripheral_sources": "none"},
        "# Source Basis\n\n## Core Sources\npaper-a\n\n## Peripheral Sources\nnone\n\n"
        "## Why Each Source Matters\npaper-a defines X.\n",
    )
    _write_md(
        tr / "L1" / "convention_snapshot.md",
        {"artifact_kind": "l1_convention_snapshot", "stage": "L1",
         "notation_choices": "Dirac notation.", "unit_conventions": "Natural units."},
        "# Convention Snapshot\n\n## Notation Choices\nDirac notation.\n\n"
        "## Unit Conventions\nNatural units.\n\n## Unresolved Tensions\nNone.\n",
    )
    _write_md(
        tr / "L1" / "derivation_anchor_map.md",
        {"artifact_kind": "l1_derivation_anchor_map", "stage": "L1",
         "starting_anchors": "eq-1"},
        "# Derivation Anchor Map\n\n## Source Anchors\neq-1\n\n## Candidate Starting Points\neq-1.\n",
    )
    _write_md(
        tr / "L1" / "contradiction_register.md",
        {"artifact_kind": "l1_contradiction_register", "stage": "L1",
         "blocking_contradictions": "none"},
        "# Contradiction Register\n\n## Unresolved Source Conflicts\nNone.\n\n## Blocking Status\nnone\n",
    )


def _setup_full_study(td):
    _bootstrap(td)
    _fill_l1_gate(td)
    aitp_advance_to_l3(td, TOPIC, l3_mode="study")


# ---- EFT Tower Visualization ----

class TestVisualizeEFTTower:

    def test_basic_tower(self, tmp_path):
        td = _setup_td(tmp_path)
        layers = [
            {"id": "classical", "energy_scale": "< eV", "theories": "newtonian-mech"},
            {"id": "quantum", "energy_scale": "eV - keV", "theories": "qm"},
            {"id": "qed", "energy_scale": "keV - GeV", "theories": "qed"},
        ]
        aitp_create_l2_tower(td, "physics", "Physics Tower", "eV - TeV", layers=layers)

        r = aitp_visualize_eft_tower(td, "physics")
        assert isinstance(r, dict)
        assert "ascii" in r
        assert "metadata" in r
        assert r["metadata"]["layer_count"] == 3
        assert "qed" in r["ascii"]
        assert "keV - GeV" in r["ascii"]

    def test_tower_with_correspondence(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "qed", "concept", "QED", energy_scale="keV-GeV")
        aitp_create_l2_node(td, "classical-em", "concept", "Classical EM", energy_scale="< eV")
        aitp_create_l2_edge(td, "qed-limits-classical", "qed", "classical-em",
                            "limits_to", regime_condition="alpha -> 0")
        layers = [
            {"id": "classical", "energy_scale": "< eV", "theories": "classical-em"},
            {"id": "qed", "energy_scale": "keV - GeV", "theories": "qed"},
        ]
        aitp_create_l2_tower(td, "em", "EM Tower", "eV - GeV", layers=layers)

        r = aitp_visualize_eft_tower(td, "em")
        assert "limits_to" in r["ascii"] or "-->" in r["ascii"]
        assert r["metadata"]["correspondence_count"] >= 1

    def test_tower_not_found(self, tmp_path):
        td = _setup_td(tmp_path)
        r = aitp_visualize_eft_tower(td, "nonexistent")
        assert "error" in r or "not found" in str(r).lower()

    def test_empty_tower(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_tower(td, "empty", "Empty Tower", "N/A")
        r = aitp_visualize_eft_tower(td, "empty")
        assert "no layers" in r["ascii"].lower() or r["metadata"]["layer_count"] == 0

    def test_tower_node_title_lookup(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "newton", "concept", "Newtonian Mechanics",
                            energy_scale="< eV")
        layers = [
            {"id": "classical", "energy_scale": "< eV", "theories": "newton"},
        ]
        aitp_create_l2_tower(td, "mech", "Mech Tower", "< eV", layers=layers)

        r = aitp_visualize_eft_tower(td, "mech")
        assert "Newtonian Mechanics" in r["ascii"]


# ---- Derivation Chain Visualization ----

class TestVisualizeDerivationChain:

    def test_basic_chain(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "e2e-derivation", "derivation_chain",
                            "E2E Derivation",
                            regime_of_validity="non-relativistic")
        r = aitp_visualize_derivation_chain(td, "e2e-derivation")
        assert isinstance(r, dict)
        assert "ascii" in r
        assert "E2E Derivation" in r["ascii"]
        assert r["metadata"]["node_id"] == "e2e-derivation"

    def test_chain_with_steps_in_body(self, tmp_path):
        td = _setup_td(tmp_path)
        from brain.mcp_server import _ensure_l2_graph_dirs, _parse_md
        global_l2 = _ensure_l2_graph_dirs(td)
        node_path = global_l2 / "graph" / "nodes" / "chain-with-steps.md"
        _write_md(
            node_path,
            {"node_id": "chain-with-steps", "type": "derivation_chain",
             "title": "Test Chain", "trust_basis": "validated",
             "regime_of_validity": "1D"},
            "# Test Chain\n\n## Steps\n\n"
            "- Start from Lagrangian L = T - V\n"
            "- Apply Euler-Lagrange equation\n"
            "- Obtain equation of motion\n\n",
        )
        r = aitp_visualize_derivation_chain(td, "chain-with-steps")
        assert "S1" in r["ascii"]
        assert "S2" in r["ascii"]
        assert r["metadata"]["step_count"] == 3

    def test_chain_with_edges(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "chain-a", "derivation_chain", "Chain A")
        aitp_create_l2_node(td, "result-b", "result", "Result B")
        aitp_create_l2_edge(td, "chain-to-result", "chain-a", "result-b", "derives_from")
        r = aitp_visualize_derivation_chain(td, "chain-a")
        assert "Result B" in r["ascii"]
        assert r["metadata"]["outgoing_edges"] >= 1

    def test_non_derivation_node(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "concept-x", "concept", "Concept X")
        r = aitp_visualize_derivation_chain(td, "concept-x")
        assert "error" in r or "not 'derivation_chain'" in str(r).lower()

    def test_nonexistent_node(self, tmp_path):
        td = _setup_td(tmp_path)
        r = aitp_visualize_derivation_chain(td, "nope")
        assert "error" in r or "not found" in str(r).lower()


# ---- Knowledge Graph Visualization ----

class TestVisualizeKnowledgeGraph:

    def test_empty_graph(self, tmp_path):
        td = _setup_td(tmp_path)
        r = aitp_visualize_knowledge_graph(td)
        assert "empty" in r["ascii"].lower()
        assert r["metadata"]["node_count"] == 0

    def test_graph_with_nodes(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "qho", "concept", "Quantum HO",
                            physical_meaning="Quantum harmonic oscillator")
        aitp_create_l2_node(td, "gs-energy", "result", "Ground State Energy")
        r = aitp_visualize_knowledge_graph(td)
        assert r["metadata"]["node_count"] == 2
        assert "qho" in r["ascii"]
        assert "gs-energy" in r["ascii"]

    def test_graph_with_edges(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "a", "concept", "A")
        aitp_create_l2_node(td, "b", "result", "B")
        aitp_create_l2_edge(td, "a-to-b", "a", "b", "derives_from")
        r = aitp_visualize_knowledge_graph(td)
        assert "derives_from" in r["ascii"]
        assert r["metadata"]["edge_count"] >= 1

    def test_graph_type_filter(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "c1", "concept", "C1")
        aitp_create_l2_node(td, "r1", "result", "R1")
        r = aitp_visualize_knowledge_graph(td, node_type="result")
        assert r["metadata"]["node_count"] == 1
        assert "r1" in r["ascii"]

    def test_graph_center_node(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "center", "concept", "Center")
        aitp_create_l2_node(td, "neighbor", "concept", "Neighbor")
        aitp_create_l2_node(td, "far", "concept", "Far Away")
        aitp_create_l2_edge(td, "c-n", "center", "neighbor", "uses")
        # 'far' is disconnected
        r = aitp_visualize_knowledge_graph(td, center_node="center", max_depth=1)
        assert "center" in r["ascii"]
        assert "neighbor" in r["ascii"]
        assert "far" not in r["ascii"]

    def test_missing_correspondence_detection(self, tmp_path):
        td = _setup_td(tmp_path)
        # Create result nodes without limits_to edges
        aitp_create_l2_node(td, "res-a", "result", "Result A", regime_of_validity="1D")
        r = aitp_visualize_knowledge_graph(td)
        assert "Missing Correspondence" in r["ascii"] or r["metadata"]["missing_correspondence"] >= 1

    def test_no_missing_when_limits_exists(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "res-b", "result", "Result B", regime_of_validity="1D")
        aitp_create_l2_node(td, "classical", "concept", "Classical Limit")
        aitp_create_l2_edge(td, "res-b-limits", "res-b", "classical", "limits_to",
                            regime_condition="hbar -> 0")
        r = aitp_visualize_knowledge_graph(td)
        assert r["metadata"]["missing_correspondence"] == 0

    def test_type_icons_in_output(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "c", "concept", "C")
        aitp_create_l2_node(td, "r", "result", "R")
        aitp_create_l2_node(td, "q", "open_question", "Q")
        r = aitp_visualize_knowledge_graph(td)
        assert "[C]" in r["ascii"]
        assert "[R]" in r["ascii"]
        assert "[?]" in r["ascii"]

    def test_trust_markers(self, tmp_path):
        td = _setup_td(tmp_path)
        from brain.mcp_server import aitp_update_l2_node
        aitp_create_l2_node(td, "t-node", "concept", "T Node")
        aitp_update_l2_node(td, "t-node", trust_level="validated")
        r = aitp_visualize_knowledge_graph(td)
        assert "*" in r["ascii"]
