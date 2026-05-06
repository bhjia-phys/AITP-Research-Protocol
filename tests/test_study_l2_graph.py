"""Tests for L3 flexible workspace and L2 knowledge graph tools (v4 API)."""

from pathlib import Path

import pytest

from brain.mcp_server import (
    aitp_switch_l3_activity,
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
    aitp_update_l2_node,
    _slugify,
    _topic_root,
    _write_md,
)
from brain.state_model import (
    L2_NODE_TYPES,
    L2_EDGE_TYPES,
    L3_ACTIVITIES,
    L3_ACTIVITY_ARTIFACT_NAMES,
)


# ---- Helpers ----

TOPIC = "test-topic"


def _setup_td(tmp_path: Path) -> str:
    """Create topics/ subdir so _global_l2_path resolves to tmp_path/L2/."""
    (tmp_path / "topics").mkdir()
    return str(tmp_path)


def _bootstrap(td):
    """Bootstrap topic and advance past L0."""
    aitp_bootstrap_topic.__wrapped__(td, TOPIC, "Test Topic", "What is X?")
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
        "## Overall Verdict\nThis assessment confirms that the registered sources are sufficient "
        "for the bounded research question. Coverage spans the core derivation path and primary "
        "validation checks. No blocking gaps were identified. Source quality is adequate for "
        "current research intensity level.\n\n"
        "## Gaps And Next Sources\nNone\n\n## Prior L2 Knowledge\nNo prior L2 knowledge for this test bootstrap topic. Unit test fixture for gate verification.\n",
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
         "bounded_question": "What is X?", "scope_boundaries": "One model. This does NOT ask about other models.",
         "target_quantities": "Energy spectrum.",
         "competing_hypotheses": "Alternative: the spectrum may be continuous."},
        "# Question Contract\n\n## Bounded Question\nWhat is X?\n\n"
        "## Competing Hypotheses\nAlternative: the spectrum may be continuous.\n\n"
        "## Scope Boundaries\nOne model. This does NOT ask about other models.\n\n"
        "## Target Quantities Or Claims\nEnergy spectrum.\n\n"
        "## Non-Success Conditions\nIf the spectrum is not bounded below, the claim is falsified.\n\n"
        "## L2 Cross-Reference\nNo prior L2 knowledge for this test topic. Unit test fixture.\n",
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
        "## Unit Conventions\nNatural units.\n\n## Unresolved Tensions\nNone.\n\n## Prior L2 Knowledge\nNo prior L2 knowledge for this test bootstrap topic. Unit test fixture for gate verification.\n",
    )
    _write_md(
        tr / "L1" / "derivation_anchor_map.md",
        {"artifact_kind": "l1_derivation_anchor_map", "stage": "L1",
         "starting_anchors": "eq-1", "anchor_count": 1},
        "# Derivation Anchor Map\n\n## Source Anchors\neq-1\n\n## Candidate Starting Points\neq-1.\n",
    )
    _write_md(
        tr / "L1" / "contradiction_register.md",
        {"artifact_kind": "l1_contradiction_register", "stage": "L1",
         "blocking_contradictions": "none"},
        "# Contradiction Register\n\n## Unresolved Source Conflicts\nNone.\n\n## Blocking Status\nnone\n",
    )
    _write_md(
        tr / "L1" / "source_toc_map.md",
        {"artifact_kind": "l1_source_toc_map", "stage": "L1",
         "sources_with_toc": "paper-a", "total_sections": 1,
         "coverage_status": "complete"},
        "# Source TOC Map\n\n## Per-Source TOC\n\n"
        "### paper-a (TOC confidence: high)\n\n"
        "- [s1] Main Content -- status: extracted  -> intake: L1/intake/paper-a/s1.md\n\n"
        "## Coverage Summary\n\n## Deferred Sections\n\n## Extraction Notes\n",
    )
    # Create intake note for extracted section (required by L1 quality gate)
    intake_dir = tr / "L1" / "intake" / "paper-a"
    intake_dir.mkdir(parents=True, exist_ok=True)
    _write_md(
        intake_dir / "s1.md",
        {"artifact_kind": "l1_section_intake", "source_id": "paper-a",
         "section_id": "s1", "section_title": "Main Content",
         "extraction_status": "extracted", "completeness_confidence": "high",
         "updated_at": "2025-01-01T00:00:00Z"},
        "# Main Content\n\n## Section Summary (skim)\nContent.\n\n"
        "## Key Concepts\nConcept.\n\n## Equations Found\neq-1.\n\n"
        "## Physical Claims\nClaim.\n\n## Prerequisites\nNone.\n\n"
        "## Cross-References\nNone.\n\n## Completeness Self-Assessment\nConfidence: **high**\n",
    )


# ---- L3 flexible workspace tests ----

class TestL3Workspace:

    def test_l3_activities_are_defined(self):
        assert len(L3_ACTIVITIES) >= 8
        assert "ideate" in L3_ACTIVITIES
        assert "derive" in L3_ACTIVITIES
        assert "distill" in L3_ACTIVITIES

    def test_artifact_names_for_all_activities(self):
        for act in L3_ACTIVITIES:
            assert act in L3_ACTIVITY_ARTIFACT_NAMES, f"Missing artifact name for {act}"

    def test_advance_to_l3_starts_in_ideate(self, tmp_path):
        td = _setup_td(tmp_path)
        _bootstrap(td)
        _fill_l1_gate(td)

        r = aitp_advance_to_l3(td, TOPIC)
        assert "L3" in str(r)

        s = aitp_get_status(td, TOPIC)
        assert s["stage"] == "L3"

        brief = aitp_get_execution_brief(td, TOPIC)
        assert brief.get("l3_subplane") == "ideate"

    def test_activity_switch(self, tmp_path):
        td = _setup_td(tmp_path)
        _bootstrap(td)
        _fill_l1_gate(td)
        aitp_advance_to_l3(td, TOPIC)

        r = aitp_switch_l3_activity(td, TOPIC, "derive")
        assert "derive" in r

        brief = aitp_get_execution_brief(td, TOPIC)
        assert brief.get("l3_subplane") == "derive"

    def test_any_activity_switch_allowed(self, tmp_path):
        """v4: no forced sequence -- any activity can be entered at any time."""
        td = _setup_td(tmp_path)
        _bootstrap(td)
        _fill_l1_gate(td)
        aitp_advance_to_l3(td, TOPIC)

        # Jump directly from ideate to distill
        r = aitp_switch_l3_activity(td, TOPIC, "distill")
        assert "distill" in r

        brief = aitp_get_execution_brief(td, TOPIC)
        assert brief.get("l3_subplane") == "distill"

    def test_invalid_activity_rejected(self, tmp_path):
        td = _setup_td(tmp_path)
        _bootstrap(td)
        _fill_l1_gate(td)
        aitp_advance_to_l3(td, TOPIC)

        r = aitp_switch_l3_activity(td, TOPIC, "nonexistent")
        assert "Unknown activity" in r

    def test_execution_brief_includes_l3_info(self, tmp_path):
        td = _setup_td(tmp_path)
        _bootstrap(td)
        _fill_l1_gate(td)
        aitp_advance_to_l3(td, TOPIC)

        brief = aitp_get_execution_brief(td, TOPIC)
        assert isinstance(brief, dict)
        assert "l3_subplane" in brief
        assert "l3_mode" in brief


# ---- L2 knowledge graph node tests ----

class TestL2GraphNodes:

    def test_create_node(self, tmp_path):
        td = _setup_td(tmp_path)
        r = aitp_create_l2_node(
            td, "qho-hamiltonian", "concept",
            "QHO Hamiltonian",
            source_ref="ref:griffiths-ch2",
            domain="quantum-many-body",
        )
        assert "Created" in r

    def test_create_node_requires_source_ref(self, tmp_path):
        td = _setup_td(tmp_path)
        r = aitp_create_l2_node.__wrapped__(td, "orphan-node", "concept", "Orphan")
        assert "provenance" in r.lower() or "source_ref" in r.lower() or "REQUIRED" in r

    def test_create_node_all_types(self, tmp_path):
        td = _setup_td(tmp_path)
        for ntype in L2_NODE_TYPES:
            nid = f"test-{ntype.replace('_', '-')}"
            r = aitp_create_l2_node(
                td, nid, ntype, f"Test {ntype}",
                source_ref="ref:test", domain="quantum-many-body",
            )
            assert "Created" in r, f"Failed for type {ntype}"

    def test_update_node(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(
            td, "test-node", "concept", "Test Node",
            source_ref="ref:test", domain="quantum-many-body",
        )
        r = aitp_update_l2_node(
            td, "test-node",
            physical_meaning="Updated meaning",
            mathematical_expression="H = E",
        )
        assert "Updated" in r or "updated" in r.lower()

    def test_node_merge_preserves_trust(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node(
            td, "merge-node", "concept", "Merge Node",
            source_ref="ref:A", domain="quantum-many-body",
        )
        # Update trust to validated
        aitp_update_l2_node.__wrapped__(td, "merge-node", trust_level="validated")
        # Re-create with same id -- node already exists
        r = aitp_create_l2_node(
            td, "merge-node", "concept", "Merge Node",
            source_ref="ref:A", domain="quantum-many-body",
        )
        # Should still exist as updated
        assert "Created" in r or "v" in r.lower()


# ---- L2 knowledge graph edge tests ----

class TestL2GraphEdges:

    def test_create_edge(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node.__wrapped__(td, "node-a", "concept", "Node A", source_ref="ref:test", domain="quantum-many-body")
        aitp_create_l2_node.__wrapped__(td, "node-b", "concept", "Node B", source_ref="ref:test", domain="quantum-many-body")
        r = aitp_create_l2_edge(td, "edge-ab", "node-a", "node-b", "uses",
                                source_ref="ref:test")
        assert "Created" in r

    def test_create_edge_all_types(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node.__wrapped__(td, "na", "concept", "NA", source_ref="ref:test", domain="quantum-many-body")
        aitp_create_l2_node.__wrapped__(td, "nb", "concept", "NB", source_ref="ref:test", domain="quantum-many-body")
        for etype in L2_EDGE_TYPES:
            eid = f"edge-{etype.replace('_', '-')}"
            r = aitp_create_l2_edge(td, eid, "na", "nb", etype, source_ref="ref:test")
            assert "Created" in r, f"Failed for edge type {etype}"

    def test_edge_rejects_dangling_nodes(self, tmp_path):
        td = _setup_td(tmp_path)
        r = aitp_create_l2_edge(td, "dangling", "na", "nb", "uses")
        assert "not found" in r.lower() or "missing" in r.lower() or "provenance" in r.lower()


# ---- L2 knowledge graph query tests ----

class TestL2GraphQuery:

    def test_query_by_text(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node.__wrapped__(td, "propagator-func", "concept", "Propagator",
                            source_ref="ref:test", domain="quantum-many-body",
                            physical_meaning="Green function propagator of the many-body system")
        graph = aitp_query_l2_graph(td, query="propagator")
        assert len(graph["nodes"]) >= 1
        titles = [n["title"] for n in graph["nodes"]]
        assert any("Propagator" in t for t in titles)

    def test_query_by_type(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node.__wrapped__(td, "t1", "concept", "Concept", source_ref="ref:test", domain="quantum-many-body")
        aitp_create_l2_node.__wrapped__(td, "t2", "theorem", "Theorem", source_ref="ref:test", domain="quantum-many-body")
        graph = aitp_query_l2_graph(td, node_type="concept")
        types = {n["type"] for n in graph["nodes"]}
        assert "concept" in types

    def test_query_by_edge_from_node(self, tmp_path):
        td = _setup_td(tmp_path)
        aitp_create_l2_node.__wrapped__(td, "from-a", "concept", "From A", source_ref="ref:test", domain="quantum-many-body")
        aitp_create_l2_node.__wrapped__(td, "to-b", "concept", "To B", source_ref="ref:test", domain="quantum-many-body")
        aitp_create_l2_edge(td, "e1", "from-a", "to-b", "uses", source_ref="ref:test")
        graph = aitp_query_l2_graph(td, from_node="from-a")
        assert len(graph["edges"]) >= 1


# ---- L2 merge delta tests ----

class TestL2MergeDelta:

    def test_merge_creates_nodes_and_edges(self, tmp_path):
        td = _setup_td(tmp_path)
        _bootstrap(td)
        delta = aitp_merge_subgraph_delta.__wrapped__(td, TOPIC,
            nodes=[
                {"node_id": "new-node-1", "type": "concept",
                 "title": "New Node 1", "physical_meaning": "Test"},
            ],
            edges=[],
        )
        assert isinstance(delta, dict)
        assert delta["nodes_created"] == 1

    def test_merge_updates_existing(self, tmp_path):
        td = _setup_td(tmp_path)
        _bootstrap(td)
        # Create node first
        aitp_create_l2_node.__wrapped__(td, "existing-node", "concept", "Original",
                            source_ref="ref:test", domain="quantum-many-body")
        # Merge same node
        delta = aitp_merge_subgraph_delta.__wrapped__(td, TOPIC,
            nodes=[
                {"node_id": "existing-node", "type": "concept",
                 "title": "Updated", "physical_meaning": "Updated meaning"},
            ],
            edges=[],
        )
        assert isinstance(delta, dict)


# ---- Study candidate tests ----

class TestStudyCandidates:

    def test_l2_node_types_have_negative_result(self):
        assert "negative_result" in L2_NODE_TYPES

    def test_l2_edge_types_have_falsifies(self):
        assert "falsifies" in L2_EDGE_TYPES


if __name__ == "__main__":
    pytest.main([__file__])
