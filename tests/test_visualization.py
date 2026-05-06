"""Tests for Phase 4 visualization tools."""

from pathlib import Path

import pytest

from brain.mcp_server import (
    aitp_create_l2_edge,
    aitp_create_l2_node,
    aitp_create_l2_tower,
    aitp_visualize_derivation_chain,
    aitp_visualize_eft_tower,
    aitp_visualize_knowledge_graph,
    aitp_update_l2_node,
    _ensure_l2_graph_dirs,
    _parse_md,
    _write_md,
)


TOPIC = "test-topic"


def _setup_td(tmp_path: Path) -> str:
    (tmp_path / "topics").mkdir()
    return str(tmp_path)


# ---- EFT Tower Visualization ----

class TestVisualizeEFTTower:

    def test_basic_tower(self, tmp_path):
        td = _setup_td(tmp_path)
        layers = [
            {"id": "classical", "energy_scale": "< eV", "theories": "newtonian-mech"},
            {"id": "quantum", "energy_scale": "eV - keV", "theories": "qm"},
            {"id": "qed", "energy_scale": "keV - GeV", "theories": "qed"},
        ]
        aitp_create_l2_tower.__wrapped__(td, "physics", "Physics Tower", "eV - TeV", layers=layers)

        r = aitp_visualize_eft_tower(td, "physics")
        assert isinstance(r, dict)
        assert "ascii" in r
        assert "metadata" in r
        assert r["metadata"]["layer_count"] == 3
        assert "qed" in r["ascii"]
        assert "keV - GeV" in r["ascii"]

    def test_tower_with_correspondence(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node.__wrapped__(td, "qed", "concept", "QED", energy_scale="keV-GeV",
                            source_ref="ref:test")
        aitp_create_l2_node.__wrapped__(td, "classical-em", "concept", "Classical EM",
                            energy_scale="< eV", source_ref="ref:test")
        aitp_create_l2_edge(td, "qed-limits-classical", "qed", "classical-em",
                            "limits_to", regime_condition="alpha -> 0",
                            source_ref="ref:test")
        layers = [
            {"id": "classical", "energy_scale": "< eV", "theories": "classical-em"},
            {"id": "qed", "energy_scale": "keV - GeV", "theories": "qed"},
        ]
        aitp_create_l2_tower.__wrapped__(td, "em", "EM Tower", "eV - GeV", layers=layers)

        r = aitp_visualize_eft_tower(td, "em")
        assert "limits_to" in r["ascii"] or "-->" in r["ascii"]
        assert r["metadata"]["correspondence_count"] >= 1

    def test_tower_not_found(self, tmp_path):
        td = _setup_td(tmp_path)
        r = aitp_visualize_eft_tower(td, "nonexistent")
        assert "error" in r or "not found" in str(r).lower()

    def test_empty_tower(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_tower.__wrapped__(td, "empty", "Empty Tower", "N/A")
        r = aitp_visualize_eft_tower(td, "empty")
        assert "no layers" in r["ascii"].lower() or r["metadata"]["layer_count"] == 0

    def test_tower_node_title_lookup(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node.__wrapped__(td, "newton", "concept", "Newtonian Mechanics",
                            energy_scale="< eV", source_ref="ref:test")
        layers = [
            {"id": "classical", "energy_scale": "< eV", "theories": "newton"},
        ]
        aitp_create_l2_tower.__wrapped__(td, "mech", "Mech Tower", "< eV", layers=layers)

        r = aitp_visualize_eft_tower(td, "mech")
        assert "Newtonian Mechanics" in r["ascii"]


# ---- Derivation Chain Visualization ----

class TestVisualizeDerivationChain:

    def test_basic_chain(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node.__wrapped__(td, "e2e-derivation", "derivation_chain",
                            "E2E Derivation",
                            source_ref="ref:test",
                            regime_of_validity="non-relativistic",
                            domain="quantum-many-body")
        r = aitp_visualize_derivation_chain(td, "e2e-derivation")
        assert isinstance(r, dict)
        assert "ascii" in r
        assert "E2E Derivation" in r["ascii"]
        assert r["metadata"]["node_id"] == "e2e-derivation"

    def test_chain_with_steps_in_body(self, tmp_path):
        td = _setup_td(tmp_path)
        global_l2 = _ensure_l2_graph_dirs(td)
        node_path = global_l2 / "graph" / "nodes" / "chain-with-steps.md"
        _write_md(
            node_path,
            {"node_id": "chain-with-steps", "type": "derivation_chain",
             "title": "Test Chain", "trust_basis": "validated",
             "regime_of_validity": "1D", "source_ref": "ref:test"},
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
        aitp_create_l2_node.__wrapped__(td, "chain-a", "derivation_chain", "Chain A",
                            source_ref="ref:test")
        aitp_create_l2_node.__wrapped__(td, "result-b", "result", "Result B",
                            source_ref="ref:test")
        aitp_create_l2_edge(td, "chain-to-result", "chain-a", "result-b",
                            "derives_from", source_ref="ref:test")
        r = aitp_visualize_derivation_chain(td, "chain-a")
        assert "Result B" in r["ascii"]
        assert r["metadata"]["outgoing_edges"] >= 1

    def test_non_derivation_node(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node.__wrapped__(td, "concept-x", "concept", "Concept X",
                            source_ref="ref:test")
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
        aitp_create_l2_node.__wrapped__(td, "qho", "concept", "Quantum HO",
                            source_ref="ref:test",
                            physical_meaning="Quantum harmonic oscillator")
        aitp_create_l2_node.__wrapped__(td, "gs-energy", "result", "Ground State Energy",
                            source_ref="ref:test")
        r = aitp_visualize_knowledge_graph(td)
        assert r["metadata"]["node_count"] == 2
        assert "qho" in r["ascii"]
        assert "gs-energy" in r["ascii"]

    def test_graph_with_edges(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node.__wrapped__(td, "a", "concept", "A", source_ref="ref:test")
        aitp_create_l2_node.__wrapped__(td, "b", "result", "B", source_ref="ref:test")
        aitp_create_l2_edge(td, "a-to-b", "a", "b", "derives_from",
                            source_ref="ref:test")
        r = aitp_visualize_knowledge_graph(td)
        assert "derives_from" in r["ascii"]
        assert r["metadata"]["edge_count"] >= 1

    def test_graph_type_filter(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node.__wrapped__(td, "c1", "concept", "C1", source_ref="ref:test")
        aitp_create_l2_node.__wrapped__(td, "r1", "result", "R1", source_ref="ref:test")
        r = aitp_visualize_knowledge_graph(td, node_type="result")
        assert r["metadata"]["node_count"] == 1
        assert "r1" in r["ascii"]

    def test_graph_center_node(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node.__wrapped__(td, "center", "concept", "Center",
                            source_ref="ref:test")
        aitp_create_l2_node.__wrapped__(td, "neighbor", "concept", "Neighbor",
                            source_ref="ref:test")
        aitp_create_l2_node.__wrapped__(td, "far", "concept", "Far Away",
                            source_ref="ref:test")
        aitp_create_l2_edge(td, "c-n", "center", "neighbor", "uses",
                            source_ref="ref:test")
        r = aitp_visualize_knowledge_graph(td, center_node="center", max_depth=1)
        assert "center" in r["ascii"]
        assert "neighbor" in r["ascii"]
        assert "far" not in r["ascii"]

    def test_missing_correspondence_detection(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node.__wrapped__(td, "res-a", "result", "Result A",
                            source_ref="ref:test", regime_of_validity="1D")
        r = aitp_visualize_knowledge_graph(td)
        assert "Missing Correspondence" in r["ascii"] or r["metadata"]["missing_correspondence"] >= 1

    def test_no_missing_when_limits_exists(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node.__wrapped__(td, "res-b", "result", "Result B",
                            source_ref="ref:test", regime_of_validity="1D")
        aitp_create_l2_node.__wrapped__(td, "classical", "concept", "Classical Limit",
                            source_ref="ref:test")
        aitp_create_l2_edge(td, "res-b-limits", "res-b", "classical", "limits_to",
                            regime_condition="hbar -> 0", source_ref="ref:test")
        r = aitp_visualize_knowledge_graph(td)
        assert r["metadata"]["missing_correspondence"] == 0

    def test_type_icons_in_output(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node.__wrapped__(td, "c", "concept", "C", source_ref="ref:test")
        aitp_create_l2_node.__wrapped__(td, "r", "result", "R", source_ref="ref:test")
        aitp_create_l2_node.__wrapped__(td, "q", "open_question", "Q", source_ref="ref:test")
        r = aitp_visualize_knowledge_graph(td)
        assert "[C]" in r["ascii"]
        assert "[R]" in r["ascii"]
        assert "[?]" in r["ascii"]

    def test_trust_markers(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node.__wrapped__(td, "t-node", "concept", "T Node",
                            source_ref="ref:test")
        aitp_update_l2_node.__wrapped__(td, "t-node", trust_level="validated")
        r = aitp_visualize_knowledge_graph(td)
        assert "*" in r["ascii"]


if __name__ == "__main__":
    pytest.main([__file__])
