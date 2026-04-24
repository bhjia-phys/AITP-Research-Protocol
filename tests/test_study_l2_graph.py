"""Tests for L3 study mode and L2 knowledge graph tools."""

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
    aitp_get_execution_brief,
    aitp_get_status,
    aitp_merge_subgraph_delta,
    aitp_query_l2_graph,
    aitp_switch_l3_mode,
    aitp_update_l2_node,
    _slugify,
    _topic_root,
    _write_md,
)
from brain.state_model import (
    L2_NODE_TYPES,
    L2_EDGE_TYPES,
    STUDY_L3_SUBPLANES,
    STUDY_CANDIDATE_TYPES,
    _get_l3_config,
)


# ---- Helpers ----

TOPIC = "test-topic"


def _setup_td(tmp_path: Path) -> str:
    """Create topics/ subdir so _global_l2_path resolves to tmp_path/L2/."""
    (tmp_path / "topics").mkdir()
    return str(tmp_path)


def _bootstrap(td):
    """Bootstrap topic and advance past L0."""
    aitp_bootstrap_topic(td, TOPIC, "Test Topic", "What is X?", "theory")
    _fill_l0_gate(td)
    aitp_advance_to_l1(td, TOPIC)


def _fill_l0_gate(td):
    """Fill L0 artifacts so L1 advance succeeds."""
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
    """Fill all L1 artifacts so L3 advance succeeds."""
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


# ---- Study mode state tests ----

class TestStudyModeState:

    def test_study_mode_constants(self):
        assert STUDY_L3_SUBPLANES == ["source_decompose", "step_derive", "gap_audit", "synthesis"]

    def test_get_l3_config_study(self):
        subplanes, transitions, templates, artifact_names, skill_map, headings, entry = _get_l3_config("study")
        assert subplanes == STUDY_L3_SUBPLANES
        assert entry == "source_decompose"
        assert "source_decompose" in templates
        assert "synthesis" in templates

    def test_get_l3_config_research(self):
        subplanes, _, _, _, _, _, entry = _get_l3_config("research")
        assert entry == "ideation"
        assert "ideation" in subplanes

    def test_advance_to_l3_study_mode(self, tmp_path):
        td = _setup_td(tmp_path)
        _bootstrap(td)
        _fill_l1_gate(td)

        r = aitp_advance_to_l3(td, TOPIC, l3_mode="study")
        assert "study" in str(r).lower() or "L3" in str(r)

        s = aitp_get_status(td, TOPIC)
        assert s["l3_mode"] == "study"
        assert s["stage"] == "L3"

        brief = aitp_get_execution_brief(td, TOPIC)
        assert brief.get("l3_subplane") == "source_decompose"

    def test_study_subplane_advance(self, tmp_path):
        td = _setup_td(tmp_path)
        _bootstrap(td)
        _fill_l1_gate(td)
        aitp_advance_to_l3(td, TOPIC, l3_mode="study")

        r = aitp_advance_l3_subplane(td, TOPIC, "step_derive")
        assert "step_derive" in r

        brief = aitp_get_execution_brief(td, TOPIC)
        assert brief.get("l3_subplane") == "step_derive"

    def test_study_subplane_backedge(self, tmp_path):
        td = _setup_td(tmp_path)
        _bootstrap(td)
        _fill_l1_gate(td)
        aitp_advance_to_l3(td, TOPIC, l3_mode="study")
        aitp_advance_l3_subplane(td, TOPIC, "step_derive")

        r = aitp_advance_l3_subplane(td, TOPIC, "source_decompose")
        assert "source_decompose" in r

    def test_study_invalid_transition(self, tmp_path):
        td = _setup_td(tmp_path)
        _bootstrap(td)
        _fill_l1_gate(td)
        aitp_advance_to_l3(td, TOPIC, l3_mode="study")

        # Cannot jump directly to synthesis from source_decompose
        r = aitp_advance_l3_subplane(td, TOPIC, "synthesis")
        assert "not allowed" in r.lower() or "invalid" in r.lower()

    def test_switch_l3_mode(self, tmp_path):
        td = _setup_td(tmp_path)
        _bootstrap(td)
        _fill_l1_gate(td)
        aitp_advance_to_l3(td, TOPIC, l3_mode="study")

        r = aitp_switch_l3_mode(td, TOPIC, "research")
        assert "research" in str(r).lower()

        s = aitp_get_status(td, TOPIC)
        assert s["l3_mode"] == "research"

        brief = aitp_get_execution_brief(td, TOPIC)
        assert brief.get("l3_subplane") == "ideation"

    def test_switch_to_study_creates_scaffolds(self, tmp_path):
        td = _setup_td(tmp_path)
        _bootstrap(td)
        _fill_l1_gate(td)
        aitp_advance_to_l3(td, TOPIC, l3_mode="research")

        aitp_switch_l3_mode(td, TOPIC, "study")

        root = _topic_root(td, TOPIC)
        for sp in STUDY_L3_SUBPLANES:
            assert (root / "L3" / sp).is_dir(), f"Missing study subplane dir: {sp}"

    def test_execution_brief_includes_l3_mode(self, tmp_path):
        td = _setup_td(tmp_path)
        _bootstrap(td)
        _fill_l1_gate(td)
        aitp_advance_to_l3(td, TOPIC, l3_mode="study")

        brief = aitp_get_execution_brief(td, TOPIC)
        assert isinstance(brief, dict)
        assert brief.get("l3_mode") == "study"

    def test_cannot_switch_at_l0(self, tmp_path):
        td = _setup_td(tmp_path)
        # Bootstrap but don't advance — stays at L0
        aitp_bootstrap_topic(td, TOPIC, "Test Topic", "What is X?", "theory")
        r = aitp_switch_l3_mode(td, TOPIC, "study")
        assert "cannot" in str(r).lower()


# ---- L2 knowledge graph node tests ----

class TestL2GraphNodes:

    def test_create_node(self, tmp_path):
        td = _setup_td(tmp_path)
        r = aitp_create_l2_node(
            td, "qho", "concept", "Quantum Harmonic Oscillator",
            physical_meaning="Quantum analog of classical HO",
            mathematical_expression="H = p^2/(2m) + (1/2)m omega^2 x^2",
            regime_of_validity="Non-relativistic QM",
        )
        assert "Created" in r
        assert "qho" in r

    def test_create_node_invalid_type(self, tmp_path):
        td = _setup_td(tmp_path)
        r = aitp_create_l2_node(td, "bad", "invalid_type", "Bad Node")
        assert "Invalid" in r

    def test_create_node_all_types(self, tmp_path):
        td = _setup_td(tmp_path)
        for nt in L2_NODE_TYPES:
            r = aitp_create_l2_node(td, f"node-{nt}", nt, f"Test {nt}")
            assert "Created" in r, f"Failed for type {nt}: {r}"

    def test_update_node(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "qho", "concept", "QHO", physical_meaning="test")
        r = aitp_update_l2_node(td, "qho", trust_level="multi_source_confirmed")
        assert "Updated" in r or "updated" in r.lower() or "v2" in r

    def test_update_nonexistent_node(self, tmp_path):
        td = _setup_td(tmp_path)
        r = aitp_update_l2_node(td, "nonexistent", trust_level="validated")
        assert "not found" in r.lower()

    def test_node_merge_preserves_trust(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "qho", "concept", "QHO")
        aitp_update_l2_node(td, "qho", trust_level="independently_verified")
        # Recreate (merge) — should preserve higher trust, bump version
        r = aitp_create_l2_node(td, "qho", "concept", "QHO Updated")
        assert "v2" in r or "v3" in r


# ---- L2 graph edge tests ----

class TestL2GraphEdges:
    # aitp_create_l2_edge(topics_root, edge_id, from_node, to_node, edge_type, ...)

    def test_create_edge(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "qho", "concept", "QHO")
        aitp_create_l2_node(td, "ground-state", "result", "Ground State Energy")
        r = aitp_create_l2_edge(td, "gs-to-qho", "ground-state", "qho", "derives_from",
                                regime_condition="1D QHO")
        assert "Created" in r or "created" in r.lower()

    def test_create_edge_invalid_type(self, tmp_path):
        td = _setup_td(tmp_path)
        r = aitp_create_l2_edge(td, "bad-edge", "a", "b", "invalid_edge_type")
        assert "Invalid" in r

    def test_create_edge_all_types(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "a", "concept", "A")
        aitp_create_l2_node(td, "b", "concept", "B")
        for i, et in enumerate(L2_EDGE_TYPES):
            r = aitp_create_l2_edge(td, f"edge-{i}", "a", "b", et)
            assert "Created" in r or "created" in r.lower(), f"Failed for {et}: {r}"


# ---- L2 graph query tests ----

class TestL2GraphQuery:

    def test_query_by_text(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "qho", "concept", "Quantum Harmonic Oscillator",
                            physical_meaning="The quantum analog of the classical harmonic oscillator")
        r = aitp_query_l2_graph(td, query="oscillator")
        assert isinstance(r, dict)
        assert len(r["nodes"]) >= 1

    def test_query_by_type(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "qho", "concept", "QHO")
        aitp_create_l2_node(td, "gs", "result", "Ground State")
        r = aitp_query_l2_graph(td, node_type="result")
        assert len(r["nodes"]) == 1
        assert r["nodes"][0]["type"] == "result"

    def test_query_by_edge_from_node(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(td, "a", "concept", "A")
        aitp_create_l2_node(td, "b", "concept", "B")
        aitp_create_l2_edge(td, "a-to-b", "a", "b", "derives_from")
        r = aitp_query_l2_graph(td, from_node="a")
        assert len(r["edges"]) >= 1

    def test_query_empty_graph(self, tmp_path):
        td = _setup_td(tmp_path)
        r = aitp_query_l2_graph(td)
        assert r["nodes"] == []
        assert r["edges"] == []


# ---- EFT tower tests ----

class TestL2Tower:

    def test_create_tower(self, tmp_path):
        td = _setup_td(tmp_path)
        layers = [
            {"id": "phonon", "energy_scale": "meV", "theories": "phonon-theory"},
            {"id": "bcs", "energy_scale": "0.1-1 meV", "theories": "bcs-theory, cooper-pairs"},
        ]
        r = aitp_create_l2_tower(td, "condensed-matter", "Condensed Matter EFT Tower",
                                 "meV - eV", layers=layers)
        assert "Created" in r or "created" in r.lower()

    def test_create_tower_no_layers(self, tmp_path):
        td = _setup_td(tmp_path)
        r = aitp_create_l2_tower(td, "qft", "QFT Tower", "GeV - TeV")
        assert "Created" in r or "created" in r.lower()


# ---- Merge delta tests ----

class TestL2MergeDelta:
    # aitp_merge_subgraph_delta(topics_root, topic_slug, nodes=[], edges=[], ...)

    def test_merge_creates_nodes_and_edges(self, tmp_path):
        td = _setup_td(tmp_path)
        _bootstrap(td)
        _fill_l1_gate(td)
        aitp_advance_to_l3(td, TOPIC, l3_mode="study")
        aitp_create_l2_node(td, "qho", "concept", "QHO")

        r = aitp_merge_subgraph_delta(
            td, TOPIC,
            nodes=[
                {"node_id": "new-concept", "type": "concept", "title": "New Concept",
                 "action": "create"},
            ],
            edges=[
                {"from_node": "new-concept", "to_node": "qho", "type": "uses"},
            ],
        )
        assert isinstance(r, dict)
        assert r["nodes_created"] == 1
        assert r["edges_created"] == 1

    def test_merge_updates_existing(self, tmp_path):
        td = _setup_td(tmp_path)
        _bootstrap(td)
        _fill_l1_gate(td)
        aitp_advance_to_l3(td, TOPIC, l3_mode="study")
        aitp_create_l2_node(td, "existing", "concept", "Existing Concept")

        r = aitp_merge_subgraph_delta(
            td, TOPIC,
            nodes=[
                {"node_id": "existing", "type": "concept", "title": "Existing Concept",
                 "action": "update"},
            ],
            edges=[],
        )
        assert isinstance(r, dict)
        assert r["nodes_updated"] == 1


# ---- Constants and helpers ----

class TestStudyCandidates:

    def test_study_candidate_types(self):
        assert "atomic_concept" in STUDY_CANDIDATE_TYPES
        assert "derivation_chain" in STUDY_CANDIDATE_TYPES

    def test_l2_node_types(self):
        expected = {"concept", "theorem", "technique", "derivation_chain",
                    "result", "approximation", "open_question", "regime_boundary"}
        assert set(L2_NODE_TYPES) == expected

    def test_l2_edge_types(self):
        assert "limits_to" in L2_EDGE_TYPES
        assert "derives_from" in L2_EDGE_TYPES
        assert "emerges_from" in L2_EDGE_TYPES
        assert "decouples_at" in L2_EDGE_TYPES
        assert len(L2_EDGE_TYPES) == 16


class TestSlugify:

    def test_basic(self):
        assert _slugify("Quantum Harmonic Oscillator") == "quantum-harmonic-oscillator"

    def test_special_chars(self):
        assert _slugify("E = mc^2") == "e-mc-2"

    def test_idempotent(self):
        s = "Berry Phase and Topology"
        assert _slugify(_slugify(s)) == _slugify(s)
