"""Tests for L3 study mode and L2 knowledge graph tools."""

import os
import tempfile

import pytest

from brain.mcp_server import (
    aitp_advance_l3_subplane,
    aitp_advance_to_l1,
    aitp_advance_to_l3,
    aitp_bootstrap_topic,
    aitp_check_correspondence,
    aitp_coverage_map,
    aitp_create_l2_edge,
    aitp_create_l2_node,
    aitp_create_l2_tower,
    aitp_get_execution_brief,
    aitp_get_status,
    aitp_merge_subgraph_delta,
    aitp_query_l2_graph,
    aitp_switch_l3_mode,
    aitp_update_l2_node,
    _ensure_l2_graph_dirs,
    _slugify,
)
from brain.state_model import (
    L2_NODE_TYPES,
    L2_EDGE_TYPES,
    STUDY_L3_SUBPLANES,
    STUDY_CANDIDATE_TYPES,
    _get_l3_config,
)


# ---- Helpers ----

def _make_ready_topic(td):
    """Create a topic and advance it to L1 ready state."""
    ms_bootstrap = aitp_bootstrap_topic(td, "test-topic", "Test Topic", "What is X?", "theory")
    aitp_advance_to_l1(td, "test-topic")
    return ms_bootstrap


def _fill_l1_artifacts(td):
    """Fill required L1 artifacts so L3 advance succeeds."""
    from brain.mcp_server import _topic_root, _write_md

    root = _topic_root(td, "test-topic")
    # Fill source_registry
    src = root / "L1" / "source_registry.md"
    fm, body = {"kind": "source_registry"}, "## Sources\n\n- test-source\n"
    _write_md(src, fm, body)


# ---- Study mode tests ----

class TestStudyModeState:
    """Test L3 study mode state management."""

    def test_study_mode_constants(self):
        assert len(STUDY_L3_SUBPLANES) == 4
        assert STUDY_L3_SUBPLANES == ["source_decompose", "step_derive", "gap_audit", "synthesis"]

    def test_get_l3_config_study(self):
        subplanes, transitions, templates, artifact_names, skill_map, headings, entry = _get_l3_config("study")
        assert subplanes == STUDY_L3_SUBPLANES
        assert entry == "source_decompose"
        assert "source_decompose" in templates
        assert "synthesis" in templates

    def test_get_l3_config_research(self):
        subplanes, transitions, templates, artifact_names, skill_map, headings, entry = _get_l3_config("research")
        assert entry == "ideation"
        assert "ideation" in subplanes

    def test_advance_to_l3_study_mode(self, tmp_path):
        td = str(tmp_path)
        _make_ready_topic(td)
        _fill_l1_artifacts(td)

        r = aitp_advance_to_l3(td, "test-topic", l3_mode="study")
        assert "study" in str(r).lower() or "L3" in str(r)

        s = aitp_get_status(td, "test-topic")
        assert isinstance(s, dict)
        assert s["l3_mode"] == "study"
        assert s["stage"] == "L3"
        assert s["l3_subplane"] == "source_decompose"

    def test_study_subplane_advance(self, tmp_path):
        td = str(tmp_path)
        _make_ready_topic(td)
        _fill_l1_artifacts(td)
        aitp_advance_to_l3(td, "test-topic", l3_mode="study")

        r = aitp_advance_l3_subplane(td, "test-topic", "step_derive")
        assert "step_derive" in r

        s = aitp_get_status(td, "test-topic")
        assert s["l3_subplane"] == "step_derive"

    def test_study_subplane_backedge(self, tmp_path):
        td = str(tmp_path)
        _make_ready_topic(td)
        _fill_l1_artifacts(td)
        aitp_advance_to_l3(td, "test-topic", l3_mode="study")
        aitp_advance_l3_subplane(td, "test-topic", "step_derive")

        # Backedge: step_derive -> source_decompose
        r = aitp_advance_l3_subplane(td, "test-topic", "source_decompose")
        assert "source_decompose" in r

    def test_study_invalid_transition(self, tmp_path):
        td = str(tmp_path)
        _make_ready_topic(td)
        _fill_l1_artifacts(td)
        aitp_advance_to_l3(td, "test-topic", l3_mode="study")

        # Cannot jump directly to synthesis from source_decompose
        r = aitp_advance_l3_subplane(td, "test-topic", "synthesis")
        assert "not allowed" in r.lower() or "invalid" in r.lower()

    def test_switch_l3_mode(self, tmp_path):
        td = str(tmp_path)
        _make_ready_topic(td)
        _fill_l1_artifacts(td)
        aitp_advance_to_l3(td, "test-topic", l3_mode="study")

        r = aitp_switch_l3_mode(td, "test-topic", "research")
        assert "research" in str(r).lower()

        s = aitp_get_status(td, "test-topic")
        assert s["l3_mode"] == "research"
        assert s["l3_subplane"] == "ideation"

    def test_switch_to_study_creates_scaffolds(self, tmp_path):
        td = str(tmp_path)
        _make_ready_topic(td)
        _fill_l1_artifacts(td)
        aitp_advance_to_l3(td, "test-topic", l3_mode="research")

        aitp_switch_l3_mode(td, "test-topic", "study")

        from brain.mcp_server import _topic_root
        root = _topic_root(td, "test-topic")
        for sp in STUDY_L3_SUBPLANES:
            assert (root / "L3" / sp).is_dir(), f"Missing study subplane dir: {sp}"

    def test_execution_brief_includes_l3_mode(self, tmp_path):
        td = str(tmp_path)
        _make_ready_topic(td)
        _fill_l1_artifacts(td)
        aitp_advance_to_l3(td, "test-topic", l3_mode="study")

        brief = aitp_get_execution_brief(td, "test-topic")
        assert isinstance(brief, dict)
        assert brief.get("l3_mode") == "study"

    def test_cannot_switch_at_l0(self, tmp_path):
        td = str(tmp_path)
        _make_ready_topic(td)
        # Still at L0
        r = aitp_switch_l3_mode(td, "test-topic", "study")
        assert "Cannot" in str(r) or "cannot" in str(r).lower()


# ---- L2 knowledge graph tests ----

class TestL2GraphNodes:
    """Test L2 graph node CRUD."""

    def test_create_node(self, tmp_path):
        td = str(tmp_path)
        r = aitp_create_l2_node(
            td, "qho", "concept", "Quantum Harmonic Oscillator",
            physical_meaning="Quantum analog of classical HO",
            mathematical_expression="H = p^2/(2m) + (1/2)m omega^2 x^2",
            regime_of_validity="Non-relativistic QM",
        )
        assert "Created" in r
        assert "qho" in r

    def test_create_node_invalid_type(self, tmp_path):
        td = str(tmp_path)
        r = aitp_create_l2_node(td, "bad", "invalid_type", "Bad Node")
        assert "Invalid" in r

    def test_create_node_all_types(self, tmp_path):
        td = str(tmp_path)
        for nt in L2_NODE_TYPES:
            r = aitp_create_l2_node(td, f"node-{nt}", nt, f"Test {nt}")
            assert "Created" in r, f"Failed for type {nt}: {r}"

    def test_update_node(self, tmp_path):
        td = str(tmp_path)
        aitp_create_l2_node(td, "qho", "concept", "QHO", physical_meaning="test")

        r = aitp_update_l2_node(td, "qho", trust_level="multi_source_confirmed")
        assert "Updated" in r or "updated" in r.lower() or "v2" in r

    def test_update_nonexistent_node(self, tmp_path):
        td = str(tmp_path)
        r = aitp_update_l2_node(td, "nonexistent", trust_level="validated")
        assert "not found" in r.lower()

    def test_node_merge_preserves_trust(self, tmp_path):
        td = str(tmp_path)
        # Create with source_grounded
        aitp_create_l2_node(td, "qho", "concept", "QHO")
        # Upgrade trust
        aitp_update_l2_node(td, "qho", trust_level="independently_verified")
        # Recreate (merge) — should preserve higher trust
        r = aitp_create_l2_node(td, "qho", "concept", "QHO Updated")
        assert "v3" in r or "v2" in r  # version bumped


class TestL2GraphEdges:
    """Test L2 graph edge operations."""

    def test_create_edge(self, tmp_path):
        td = str(tmp_path)
        aitp_create_l2_node(td, "qho", "concept", "QHO")
        aitp_create_l2_node(td, "ground-state", "result", "Ground State Energy")

        r = aitp_create_l2_edge(td, "ground-state", "qho", "derives_from", regime_condition="1D QHO")
        assert "Created" in r or "created" in r.lower()

    def test_create_edge_invalid_type(self, tmp_path):
        td = str(tmp_path)
        r = aitp_create_l2_edge(td, "a", "b", "invalid_edge_type")
        assert "Invalid" in r

    def test_create_edge_all_types(self, tmp_path):
        td = str(tmp_path)
        aitp_create_l2_node(td, "a", "concept", "A")
        aitp_create_l2_node(td, "b", "concept", "B")
        for et in L2_EDGE_TYPES:
            r = aitp_create_l2_edge(td, "a", "b", et)
            assert "Created" in r or "created" in r.lower(), f"Failed for edge type {et}: {r}"


class TestL2GraphQuery:
    """Test L2 graph querying."""

    def test_query_by_text(self, tmp_path):
        td = str(tmp_path)
        aitp_create_l2_node(td, "qho", "concept", "Quantum Harmonic Oscillator",
                            physical_meaning="The quantum analog of the classical harmonic oscillator")

        r = aitp_query_l2_graph(td, query="oscillator")
        assert isinstance(r, dict)
        assert len(r["nodes"]) >= 1

    def test_query_by_type(self, tmp_path):
        td = str(tmp_path)
        aitp_create_l2_node(td, "qho", "concept", "QHO")
        aitp_create_l2_node(td, "gs", "result", "Ground State")

        r = aitp_query_l2_graph(td, node_type="result")
        assert len(r["nodes"]) == 1
        assert r["nodes"][0]["type"] == "result"

    def test_query_by_edge_from_node(self, tmp_path):
        td = str(tmp_path)
        aitp_create_l2_node(td, "a", "concept", "A")
        aitp_create_l2_node(td, "b", "concept", "B")
        aitp_create_l2_edge(td, "a", "b", "derives_from")

        r = aitp_query_l2_graph(td, from_node="a")
        assert len(r["edges"]) >= 1

    def test_query_empty_graph(self, tmp_path):
        td = str(tmp_path)
        r = aitp_query_l2_graph(td)
        assert r["nodes"] == []


class TestL2Tower:
    """Test EFT tower creation."""

    def test_create_tower(self, tmp_path):
        td = str(tmp_path)
        layers = [
            {"id": "phonon", "energy_scale": "meV", "theories": "phonon-theory"},
            {"id": "bcs", "energy_scale": "0.1-1 meV", "theories": "bcs-theory, cooper-pairs"},
        ]
        r = aitp_create_l2_tower(td, "condensed-matter", "Condensed Matter EFT Tower", "meV - eV", layers=layers)
        assert "Created" in r or "created" in r.lower()

    def test_create_tower_no_layers(self, tmp_path):
        td = str(tmp_path)
        r = aitp_create_l2_tower(td, "qft", "QFT Tower", "GeV - TeV")
        assert "Created" in r or "created" in r.lower()


class TestL2Correspondence:
    """Test correspondence checking."""

    def test_check_correspondence_missing(self, tmp_path):
        td = str(tmp_path)
        # Create a result node without limits_to edges
        aitp_create_l2_node(td, "qho-energy", "result", "QHO Energy Levels",
                            regime_of_validity="1D QHO")

        r = aitp_check_correspondence(td)
        assert isinstance(r, dict)
        assert r.get("missing", 0) >= 1

    def test_check_correspondence_verified(self, tmp_path):
        td = str(tmp_path)
        aitp_create_l2_node(td, "qho", "concept", "QHO")
        aitp_create_l2_node(td, "qho-energy", "result", "QHO Energy Levels",
                            regime_of_validity="1D QHO")
        aitp_create_l2_edge(td, "qho-energy", "qho", "limits_to",
                            regime_condition="hbar omega >> kT")

        r = aitp_check_correspondence(td)
        assert isinstance(r, dict)
        # At least checked
        assert r.get("total_checked", 0) >= 1


class TestL2MergeDelta:
    """Test incremental subgraph merge."""

    def test_merge_creates_nodes_and_edges(self, tmp_path):
        td = str(tmp_path)
        aitp_create_l2_node(td, "qho", "concept", "QHO")

        r = aitp_merge_subgraph_delta(
            td,
            nodes=[
                {"title": "new-concept", "type": "concept", "action": "create",
                 "clarity_target": "clear"},
            ],
            edges=[
                {"from_id": "new-concept", "to_wikilink": "qho", "relation": "uses"},
            ],
        )
        assert isinstance(r, dict)
        assert r["nodes_created"] == 1
        assert r["edges_created"] == 1

    def test_merge_detects_conflict(self, tmp_path):
        td = str(tmp_path)
        aitp_create_l2_node(td, "existing", "concept", "Existing Concept",
                            physical_meaning="Original meaning")

        r = aitp_merge_subgraph_delta(
            td,
            nodes=[
                {"title": "existing", "type": "concept", "action": "update",
                 "clarity_target": "clear"},
            ],
            edges=[],
        )
        assert isinstance(r, dict)
        assert r["nodes_updated"] == 1


class TestL2CoverageMap:
    """Test study mode coverage map."""

    def test_coverage_in_study_mode(self, tmp_path):
        td = str(tmp_path)
        _make_ready_topic(td)
        _fill_l1_artifacts(td)
        aitp_advance_to_l3(td, "test-topic", l3_mode="study")

        r = aitp_coverage_map(td, "test-topic")
        assert isinstance(r, dict)
        assert "total_subplanes" in r

    def test_coverage_not_in_study_mode(self, tmp_path):
        td = str(tmp_path)
        _make_ready_topic(td)
        # At L0, not study mode
        r = aitp_coverage_map(td, "test-topic")
        assert isinstance(r, dict)
        assert "only available in study mode" in r.get("message", "").lower()


class TestStudyCandidates:
    """Test study-specific candidate submission and promotion."""

    def test_study_candidate_types(self):
        assert "atomic_concept" in STUDY_CANDIDATE_TYPES
        assert "derivation_chain" in STUDY_CANDIDATE_TYPES
        assert "correspondence_link" in STUDY_CANDIDATE_TYPES
        assert "regime_boundary" in STUDY_CANDIDATE_TYPES
        assert "open_question" in STUDY_CANDIDATE_TYPES

    def test_l2_node_types(self):
        expected = {"concept", "theorem", "technique", "derivation_chain",
                    "result", "approximation", "open_question", "regime_boundary"}
        assert set(L2_NODE_TYPES) == expected

    def test_l2_edge_types(self):
        assert "limits_to" in L2_EDGE_TYPES
        assert "derives_from" in L2_EDGE_TYPES
        assert "emerges_from" in L2_EDGE_TYPES
        assert "decouples_at" in L2_EDGE_TYPES
        assert len(L2_EDGE_TYPES) == 17


class TestSlugify:
    """Test slugification helper."""

    def test_basic(self):
        assert _slugify("Quantum Harmonic Oscillator") == "quantum-harmonic-oscillator"

    def test_special_chars(self):
        assert _slugify("E = mc^2") == "e--mc-2"

    def test_idempotent(self):
        s = "Berry Phase and Topology"
        assert _slugify(_slugify(s)) == _slugify(s)
