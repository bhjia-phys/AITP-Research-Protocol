"""End-to-end test: full study mode workflow from L0 to L2 knowledge graph.

Scenario: A theoretical physicist studies the quantum harmonic oscillator from
a paper, decomposes it into atomic concepts, traces derivations, audits gaps,
synthesizes, submits candidates, validates via L4, promotes to global L2, and
builds the knowledge graph with typed nodes, edges, and correspondence checks.
"""

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
    aitp_register_source,
    aitp_merge_subgraph_delta,
    aitp_promote_candidate,
    aitp_query_l2_graph,
    aitp_request_promotion,
    aitp_resolve_promotion_gate,

    aitp_submit_candidate,
    aitp_submit_l4_review,
    aitp_switch_l3_mode,
    aitp_update_l2_node,
    _parse_md,
    _slugify,
    _topic_root,
    _write_md,
)
from brain.state_model import STUDY_L3_SUBPLANES

TOPIC = "qho-study"


# ---- Fixtures ----

def _setup_td(tmp_path: Path) -> str:
    (tmp_path / "topics").mkdir()
    return str(tmp_path)


def _bootstrap_and_fill(td):
    """Bootstrap topic, fill L0 + L1 gates, return to L1 ready state."""
    aitp_bootstrap_topic(td, TOPIC, "QHO Energy Spectrum", "What are the energy eigenvalues of the QHO?", "theory")

    tr = _topic_root(td, TOPIC)

    # Register source
    aitp_register_source(td, TOPIC, "griffiths-qm-ch2", "textbook",
                         title="Griffiths QM Chapter 2",
                         notes="The quantum harmonic oscillator: algebraic method.")

    # Fill L0 gate
    _write_md(
        tr / "L0" / "source_registry.md",
        {"artifact_kind": "l0_source_registry", "stage": "L0",
         "source_count": 1, "search_status": "complete"},
        "# Source Registry\n\n## Search Methodology\nTextbook.\n\n"
        "## Source Inventory\ngriffiths-qm-ch2\n\n## Coverage Assessment\nAdequate.\n\n"
        "## Gaps And Next Sources\nNone.\n",
    )

    # Advance to L1
    r = aitp_advance_to_l1(td, TOPIC)
    assert "L1" in r or "advanced" in r.lower()

    # Fill all L1 artifacts
    _write_md(
        tr / "L1" / "question_contract.md",
        {"artifact_kind": "l1_question_contract", "stage": "L1",
         "bounded_question": "What are the energy eigenvalues and eigenstates of the 1D QHO?",
         "scope_boundaries": "Single particle, 1D, non-relativistic.",
         "target_quantities": "Energy spectrum E_n = (n+1/2) hbar omega, eigenstates |n>."},
        "# Question Contract\n\n## Bounded Question\nQHO energy spectrum.\n\n"
        "## Scope Boundaries\n1D NRQM.\n\n## Target Quantities Or Claims\nE_n = (n+1/2) hbar omega.\n",
    )
    _write_md(
        tr / "L1" / "source_basis.md",
        {"artifact_kind": "l1_source_basis", "stage": "L1",
         "core_sources": "griffiths-qm-ch2", "peripheral_sources": "none"},
        "# Source Basis\n\n## Core Sources\ngriffiths-qm-ch2\n\n## Peripheral Sources\nnone\n\n"
        "## Why Each Source Matters\nCore derivation source.\n",
    )
    _write_md(
        tr / "L1" / "convention_snapshot.md",
        {"artifact_kind": "l1_convention_snapshot", "stage": "L1",
         "notation_choices": "Dirac bra-ket, natural units hbar=c=1.",
         "unit_conventions": "Natural units."},
        "# Convention Snapshot\n\n## Notation Choices\nDirac bra-ket.\n\n"
        "## Unit Conventions\nNatural units.\n\n## Unresolved Tensions\nNone.\n",
    )
    _write_md(
        tr / "L1" / "derivation_anchor_map.md",
        {"artifact_kind": "l1_derivation_anchor_map", "stage": "L1",
         "starting_anchors": "eq-2.44 (ladder operators)"},
        "# Derivation Anchor Map\n\n## Source Anchors\neq-2.44\n\n"
        "## Candidate Starting Points\nLadder operator algebra.\n",
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
         "sources_with_toc": "sakurai", "total_sections": 1,
         "coverage_status": "complete"},
        "# Source TOC Map\n\n## Per-Source TOC\n\n"
        "### sakurai (TOC confidence: high)\n\n"
        "- [s1] Angular Momentum — status: extracted  → intake: L1/intake/sakurai/s1.md\n\n"
        "## Coverage Summary\n\n## Deferred Sections\n\n## Extraction Notes\n",
    )
    # Create intake note for extracted section (required by L1 quality gate)
    intake_dir = tr / "L1" / "intake" / "sakurai"
    intake_dir.mkdir(parents=True, exist_ok=True)
    _write_md(
        intake_dir / "s1.md",
        {"artifact_kind": "l1_section_intake", "source_id": "sakurai",
         "section_id": "s1", "section_title": "Angular Momentum",
         "extraction_status": "extracted", "completeness_confidence": "high",
         "updated_at": "2025-01-01T00:00:00Z"},
        "# Angular Momentum\n\n## Section Summary (skim)\nAngular momentum algebra.\n\n"
        "## Key Concepts\nLadder operators.\n\n## Equations Found\n[J_i, J_j] = i hbar eps_ijk J_k.\n\n"
        "## Physical Claims\nSpectrum of J^2 and J_z.\n\n## Prerequisites\nQM basics.\n\n"
        "## Cross-References\nNone.\n\n## Completeness Self-Assessment\nConfidence: **high**\n",
    )


def _fill_subplane_artifact(td, subplane, artifact_name, frontmatter, body_text):
    """Fill a study subplane's active artifact with content."""
    tr = _topic_root(td, TOPIC)
    path = tr / "L3" / subplane / artifact_name
    _write_md(path, frontmatter, body_text)


# ---- E2E: Full study workflow ----

class TestE2EStudyWorkflow:
    """Complete study mode lifecycle: L0 -> L1 -> L3 study -> L4 -> promote -> L2 graph."""

    def test_full_study_lifecycle(self, tmp_path):
        td = _setup_td(tmp_path)
        _bootstrap_and_fill(td)

        # ================================================================
        # STEP 1: Verify L1 is ready, advance to L3 study mode
        # ================================================================
        brief = aitp_get_execution_brief(td, TOPIC)
        assert brief["stage"] == "L1"
        assert brief["gate_status"] == "ready"

        r = aitp_advance_to_l3(td, TOPIC, l3_mode="study")
        assert "study" in str(r).lower()

        s = aitp_get_status(td, TOPIC)
        assert s["l3_mode"] == "study"
        assert s["stage"] == "L3"

        # ================================================================
        # STEP 2: source_decompose — decompose the QHO source
        # ================================================================
        brief = aitp_get_execution_brief(td, TOPIC)
        assert brief.get("l3_subplane") == "source_decompose"

        _fill_subplane_artifact(td, "source_decompose", "active_decomposition.md", {
            "artifact_kind": "l3_study_source_decompose",
            "stage": "L3",
            "required_fields": ["claim_count", "decomposition_type", "source_id"],
            "claim_count": 3,
            "decomposition_type": "algebraic",
            "source_id": "griffiths-qm-ch2",
            "key_entities": "ladder operators, number operator, ground state, Hamiltonian",
            "new_to_l2": "ladder-operator-method, zero-point-energy",
        }, (
            "# Source Decomposition: Griffiths QM Ch2\n\n"
            "## Key Entities\n- Ladder operators a, a-dagger\n- Number operator N = a-dagger a\n"
            "- Ground state |0>\n- Hamiltonian H = hbar omega (N + 1/2)\n\n"
            "## Claims Extracted\n"
            "1. [a, a-dagger] = 1 (commutation relation)\n"
            "2. H|n> = (n+1/2) hbar omega |n> (energy eigenvalues)\n"
            "3. Ground state energy E_0 = hbar omega / 2 (zero-point energy)\n\n"
            "## Prerequisites\n- Linear algebra (Hermitian operators)\n- Commutator algebra\n\n"
            "## Notation\n- a: lowering operator\n- a-dagger: raising operator\n- N: number operator\n"
        ))

        # Verify artifact was written
        tr = _topic_root(td, TOPIC)
        dec_path = tr / "L3" / "source_decompose" / "active_decomposition.md"
        assert dec_path.exists()
        fm, body = _parse_md(dec_path)
        assert fm["claim_count"] == 3
        assert "ladder" in body.lower()

        # ================================================================
        # STEP 3: Advance to step_derive — trace derivations
        # ================================================================
        r = aitp_advance_l3_subplane(td, TOPIC, "step_derive")
        assert "step_derive" in r

        _fill_subplane_artifact(td, "step_derive", "active_derivation.md", {
            "artifact_kind": "l3_study_step_derive",
            "stage": "L3",
            "required_fields": ["step_count", "feynman_self_check"],
            "step_count": 4,
            "feynman_self_check": "passed",
        }, (
            "# Step-by-Step Derivation: QHO Energy Spectrum\n\n"
            "## Step 1: Define ladder operators\n"
            "a = sqrt(m omega / (2 hbar)) (x + ip/(m omega))\n"
            "a-dagger = sqrt(m omega / (2 hbar)) (x - ip/(m omega))\n"
            "Justification: algebraic identity, definition\n\n"
            "## Step 2: Compute [a, a-dagger] = 1\n"
            "Justification: algebraic identity, canonical commutation [x,p]=i hbar\n\n"
            "## Step 3: Show H = hbar omega (N + 1/2)\n"
            "Justification: algebraic identity\n\n"
            "## Step 4: Derive energy spectrum\n"
            "H|n> = hbar omega (n + 1/2) |n>\n"
            "Justification: theorem (number operator eigenvalue equation)\n\n"
            "## Feynman Self-Check\n"
            "Can I explain this to a first-year grad student? Yes. "
            "The ladder operator method is constructive: define a, a-dagger, "
            "show H = hbar omega (N + 1/2), then N|n> = n|n> gives the spectrum.\n"
        ))

        # ================================================================
        # STEP 4: Advance to gap_audit — find hidden assumptions
        # ================================================================
        r = aitp_advance_l3_subplane(td, TOPIC, "gap_audit")
        assert "gap_audit" in r

        _fill_subplane_artifact(td, "gap_audit", "active_gaps.md", {
            "artifact_kind": "l3_study_gap_audit",
            "stage": "L3",
            "required_fields": ["gap_count", "blocking_gaps"],
            "gap_count": 2,
            "blocking_gaps": "none",
        }, (
            "# Gap Audit: QHO\n\n"
            "## Unstated Assumptions\n"
            "1. [minor] Author assumes canonical commutation [x,p]=i hbar without deriving from Poisson brackets.\n"
            "2. [minor] Implicit assumption: potential V(x) = (1/2)m omega^2 x^2 is unbounded.\n\n"
            "## Approximation Regimes\n"
            "1. Non-relativistic: valid when E << mc^2, i.e. hbar omega << mc^2.\n"
            "2. No spin-orbit coupling: valid for spinless particle.\n\n"
            "## Correspondence Check\n"
            "1. E_n -> <n+1/2> hbar omega: in classical limit n -> inf, "
            "<E> = (n+1/2) hbar omega matches classical E = n hbar omega (equipartition).\n\n"
            "## Prerequisite Gaps\n"
            "1. [future_work] Sturm-Liouville theory needed for completeness proof of eigenstates.\n\n"
            "## Severity Assessment\n"
            "| Gap | Severity | Status |\n"
            "|-----|----------|--------|\n"
            "| Canonical commutation | minor | deferred |\n"
            "| Unbounded potential | minor | deferred |\n"
            "| Sturm-Liouville theory | future_work | deferred |\n"
        ))

        # ================================================================
        # STEP 5: Advance to synthesis — reconstruct contribution
        # ================================================================
        r = aitp_advance_l3_subplane(td, TOPIC, "synthesis")
        assert "synthesis" in r

        _fill_subplane_artifact(td, "synthesis", "active_synthesis.md", {
            "artifact_kind": "l3_study_synthesis",
            "stage": "L3",
            "required_fields": ["synthesis_statement", "l2_update_summary"],
            "synthesis_statement": "The algebraic (ladder operator) method gives the QHO energy spectrum E_n = (n+1/2) hbar omega without solving the Schrodinger equation directly.",
            "l2_update_summary": "3 nodes (ladder-operator, qho-hamiltonian, zero-point-energy), 2 edges (derives_from, limits_to)",
        }, (
            "# Synthesis: QHO via Ladder Operators\n\n"
            "## Reconstructed Contribution\n"
            "The algebraic method constructs ladder operators a, a-dagger from x and p. "
            "The number operator N = a-dagger a commutes with H, so H = hbar omega (N + 1/2). "
            "This gives E_n = (n+1/2) hbar omega, where n = 0, 1, 2, ...\n\n"
            "## L2 Node Proposals\n"
            "1. ladder-operator-method (technique): algebraic method for QHO spectrum\n"
            "2. qho-hamiltonian (concept): H = hbar omega (N + 1/2)\n"
            "3. zero-point-energy (result): E_0 = hbar omega/2\n\n"
            "## L2 Edge Proposals\n"
            "1. zero-point-energy --[derives_from]-> qho-hamiltonian (regime: 1D QHO)\n"
            "2. qho-hamiltonian --[limits_to]-> classical-harmonic-oscillator (regime: n -> inf)\n\n"
            "## Open Questions\n"
            "1. How does this generalize to coupled oscillators?\n"
            "2. What happens at the relativistic regime boundary?\n"
        ))

        # ================================================================
        # STEP 6: Submit study candidates
        # ================================================================
        # Candidate 1: atomic concept
        r1 = aitp_submit_candidate(
            td, TOPIC, "ladder-operator-method",
            title="Ladder Operator Method for QHO",
            claim="The algebraic method using ladder operators a and a-dagger yields "
                  "the QHO energy spectrum E_n = (n+1/2) hbar omega without solving "
                  "the Schrodinger equation.",
            evidence="Step-by-step derivation traced in step_derive. "
                     "Commutes with H verified algebraically.",
            assumptions="Canonical commutation [x,p] = i hbar. "
                        "Non-relativistic regime.",
            candidate_type="atomic_concept",
            regime_of_validity="Non-relativistic QM, 1D, spinless particle",
        )
        assert "Submitted" in str(r1)

        # Candidate 2: result
        r2 = aitp_submit_candidate(
            td, TOPIC, "zero-point-energy",
            title="Zero-Point Energy of QHO",
            claim="The ground state energy of the 1D QHO is E_0 = hbar omega / 2, "
                  "a non-zero minimum energy arising from the uncertainty principle.",
            evidence="Derived from H = hbar omega (N + 1/2) with N|0> = 0.",
            candidate_type="result",
            regime_of_validity="1D QHO, non-relativistic",
        )
        assert "Submitted" in str(r2)

        # Candidate 3: correspondence link
        r3 = aitp_submit_candidate(
            td, TOPIC, "qho-classical-correspondence",
            title="QHO to Classical HO Correspondence",
            claim="In the limit n -> infinity, the QHO energy E_n = (n+1/2) hbar omega "
                  "reproduces the classical harmonic oscillator energy with the correspondence "
                  "<E_quantum> -> E_classical.",
            evidence="Gap audit correspondence check. "
                     "Equipartition in classical limit.",
            candidate_type="correspondence_link",
            regime_of_validity="Large quantum number limit, n >> 1",
        )
        assert "Submitted" in str(r3)

        # Verify candidates were created
        tr = _topic_root(td, TOPIC)
        cand_dir = tr / "L3" / "candidates"
        assert (cand_dir / "ladder-operator-method.md").exists()
        assert (cand_dir / "zero-point-energy.md").exists()
        assert (cand_dir / "qho-classical-correspondence.md").exists()

        # Verify candidate metadata
        fm1, _ = _parse_md(cand_dir / "ladder-operator-method.md")
        assert fm1["candidate_type"] == "atomic_concept"
        assert fm1["regime_of_validity"] == "Non-relativistic QM, 1D, spinless particle"

        fm2, _ = _parse_md(cand_dir / "zero-point-energy.md")
        assert fm2["candidate_type"] == "result"

        # ================================================================
        # STEP 7: L4 validation
        # ================================================================
        # Submit L4 pass review (formal_theory lane — check_results suffice)
        r = aitp_submit_l4_review(
            td, TOPIC, "ladder-operator-method",
            outcome="pass",
            notes="All checks pass. Dimensional analysis: [H] = energy, [hbar omega] = energy. "
                  "Symmetry: H commutes with parity operator. "
                  "Limiting case: reduces to classical HO for n >> 1.",
            check_results={
                "dimensional_consistency": "pass: [H] = [hbar omega] = energy",
                "symmetry_compatibility": "pass: H commutes with parity P",
                "limiting_case_check": "pass: classical limit recovered",
                "correspondence_check": "pass: E_n -> <n+1/2> hbar omega matches classical",
            },
            devils_advocate="Assumes harmonic potential; anharmonic corrections unverified.",
            verification_evidence={"tool": "aitp_verify_dimensions", "result": {"pass": True}},
        )
        assert "pass" in str(r).lower()

        # Verify candidate status updated to validated
        fm1, _ = _parse_md(cand_dir / "ladder-operator-method.md")
        assert fm1["status"] == "validated"

        # ================================================================
        # STEP 8: Promotion pipeline
        # ================================================================
        # Request promotion
        r = aitp_request_promotion(td, TOPIC, "ladder-operator-method")
        assert "pending_approval" in str(r).lower()

        # Approve
        r = aitp_resolve_promotion_gate(td, TOPIC, "ladder-operator-method", "approve",
                                        reason="Clean derivation, all checks pass.")
        assert "approve" in r.lower()

        # Promote to global L2
        r = aitp_promote_candidate(td, TOPIC, "ladder-operator-method")
        assert "Promoted" in r

        # Repeat for the other candidates (abbreviated)
        for cand_id in ["zero-point-energy", "qho-classical-correspondence"]:
            aitp_submit_l4_review(td, TOPIC, cand_id, outcome="pass",
                                  notes="Validated.", check_results={"all": "pass"},
                                  devils_advocate="Rapid promotion check; detailed adversarial review deferred.")
            aitp_request_promotion(td, TOPIC, cand_id)
            aitp_resolve_promotion_gate(td, TOPIC, cand_id, "approve")
            r = aitp_promote_candidate(td, TOPIC, cand_id)
            assert "Promoted" in r

        # ================================================================
        # STEP 9: Verify global L2 knowledge graph
        # ================================================================
        # Query promoted nodes
        graph = aitp_query_l2_graph(td, query="ladder")
        assert len(graph["nodes"]) >= 1
        ladder_node = next(n for n in graph["nodes"] if "ladder" in n["title"].lower())
        assert ladder_node["type"] == "concept"  # atomic_concept maps to concept in L2 graph
        assert ladder_node["trust_basis"] == "validated"

        # Create additional L2 nodes for the knowledge graph
        r = aitp_create_l2_node(td, "qho-hamiltonian", "concept",
                                "QHO Hamiltonian via Ladder Operators",
                                physical_meaning="H = hbar omega (N + 1/2), where N = a-dagger a is the number operator.",
                                mathematical_expression="H = hbar omega (a-dagger a + 1/2)",
                                regime_of_validity="1D QHO, non-relativistic, spinless")
        assert "Created" in r

        r = aitp_create_l2_node(td, "classical-harmonic-oscillator", "concept",
                                "Classical Harmonic Oscillator",
                                physical_meaning="A point mass on a spring: E = (1/2) m omega^2 A^2.",
                                mathematical_expression="E = (1/2) m omega^2 A^2",
                                regime_of_validity="Classical mechanics")
        assert "Created" in r

        # Create typed edges
        r = aitp_create_l2_edge(td, "zpe-from-hamiltonian", "zero-point-energy",
                                "qho-hamiltonian", "derives_from",
                                regime_condition="1D QHO, N|0>=0")
        assert "Created" in r

        r = aitp_create_l2_edge(td, "qho-classical-limit", "qho-hamiltonian",
                                "classical-harmonic-oscillator", "limits_to",
                                regime_condition="n -> infinity, hbar -> 0",
                                correspondence_verified=True)
        assert "Created" in r

        r = aitp_create_l2_edge(td, "ladder-uses-hamiltonian", "ladder-operator-method",
                                "qho-hamiltonian", "uses",
                                regime_condition="1D QHO")
        assert "Created" in r

        # ================================================================
        # STEP 10: Create EFT tower
        # ================================================================
        r = aitp_create_l2_tower(td, "quantum-oscillators",
                                 "Quantum Oscillator EFT Tower",
                                 "meV - eV",
                                 layers=[
                                     {"id": "qho", "energy_scale": "meV - eV",
                                      "theories": "qho-hamiltonian, ladder-operator-method"},
                                     {"id": "phonons", "energy_scale": "meV",
                                      "theories": "phonon-theory, lattice-dynamics"},
                                     {"id": "coupled-qho", "energy_scale": "meV - eV",
                                      "theories": "coupled-oscillator, normal-modes"},
                                 ])
        assert "Created" in r

        # ================================================================
        # STEP 11: Update node trust level
        # ================================================================
        r = aitp_update_l2_node(td, "qho-hamiltonian",
                                trust_level="multi_source_confirmed",
                                physical_meaning="The QHO Hamiltonian expressed in terms of "
                                                 "ladder operators. This decomposition reveals "
                                                 "the equally-spaced energy spectrum.")
        assert "Updated" in r or "updated" in r.lower()

        # ================================================================
        # STEP 12: Merge subgraph delta (simulating another study session)
        # ================================================================
        delta = aitp_merge_subgraph_delta(td, TOPIC,
            nodes=[
                {"node_id": "coherent-states", "type": "concept",
                 "title": "Coherent States of QHO",
                 "regime_of_validity": "1D QHO",
                 "physical_meaning": "Minimum uncertainty states that are eigenstates of a."},
            ],
            edges=[
                {"from_node": "coherent-states", "to_node": "qho-hamiltonian",
                 "type": "uses"},
            ],
            missing_prerequisites=["displacement-operator"],
        )
        assert isinstance(delta, dict)
        assert delta["nodes_created"] == 1
        assert delta["edges_created"] == 1
        assert len(delta["missing"]) >= 1  # displacement-operator flagged

        # ================================================================
        # STEP 13: Final graph query — verify full structure
        # ================================================================
        full_graph = aitp_query_l2_graph(td)
        node_count = len(full_graph["nodes"])
        edge_count = len(full_graph["edges"])

        # At minimum: 5 nodes (ladder-operator-method, zero-point-energy,
        # qho-classical-correspondence, qho-hamiltonian, classical-harmonic-oscillator)
        # + 1 from delta (coherent-states) = 6
        # Also promoted candidates create graph nodes automatically
        assert node_count >= 5, f"Expected >=5 nodes, got {node_count}"

        # At minimum: 3 edges (derives_from, limits_to, uses) + 1 from delta
        assert edge_count >= 4, f"Expected >=4 edges, got {edge_count}"

        # ================================================================
        # STEP 14: Switch to research mode to verify roundtrip
        # ================================================================
        r = aitp_switch_l3_mode(td, TOPIC, "research")
        assert "research" in str(r).lower()

        s = aitp_get_status(td, TOPIC)
        assert s["l3_mode"] == "research"

        # Verify study subplanes still exist (not deleted)
        for sp in STUDY_L3_SUBPLANES:
            assert (tr / "L3" / sp).is_dir(), f"Study subplane {sp} should persist after mode switch"

        # ================================================================
        # DONE — full lifecycle verified
        # ================================================================

    def test_study_to_research_to_study_roundtrip(self, tmp_path):
        """Verify mode switching preserves artifacts and allows round-trip."""
        td = _setup_td(tmp_path)
        _bootstrap_and_fill(td)
        aitp_advance_to_l3(td, TOPIC, l3_mode="study")

        # Fill a study artifact
        _fill_subplane_artifact(td, "source_decompose", "active_decomposition.md", {
            "artifact_kind": "l3_study_source_decompose", "stage": "L3",
            "required_fields": ["claim_count", "decomposition_type", "source_id"],
            "claim_count": 1, "decomposition_type": "test", "source_id": "test-src",
        }, "# Test decomposition\n")

        # Switch to research
        aitp_switch_l3_mode(td, TOPIC, "research")
        s = aitp_get_status(td, TOPIC)
        assert s["l3_mode"] == "research"

        # Switch back to study
        r = aitp_switch_l3_mode(td, TOPIC, "study")
        assert "study" in str(r).lower()

        s = aitp_get_status(td, TOPIC)
        assert s["l3_mode"] == "study"

        # Artifact should still be there
        tr = _topic_root(td, TOPIC)
        assert (tr / "L3" / "source_decompose" / "active_decomposition.md").exists()

    def test_conflict_detection_on_promotion(self, tmp_path):
        """Verify conflict detection when promoting conflicting claims."""
        td = _setup_td(tmp_path)
        _bootstrap_and_fill(td)
        aitp_advance_to_l3(td, TOPIC, l3_mode="study")

        # Submit, validate, promote first candidate
        aitp_submit_candidate(td, TOPIC, "energy-formula",
                              title="Energy Formula",
                              claim="E_n = (n+1/2) hbar omega",
                              candidate_type="result",
                              regime_of_validity="1D QHO")
        aitp_submit_l4_review(td, TOPIC, "energy-formula", outcome="pass",
                              devils_advocate="Test review for conflict detection.")
        aitp_request_promotion(td, TOPIC, "energy-formula")
        aitp_resolve_promotion_gate(td, TOPIC, "energy-formula", "approve")
        r = aitp_promote_candidate(td, TOPIC, "energy-formula")
        assert "Promoted" in r

        # Submit a CONFLICTING claim with the same ID
        aitp_submit_candidate(td, TOPIC, "energy-formula",
                              title="Energy Formula v2",
                              claim="E_n = n hbar omega (WRONG!)",
                              candidate_type="result",
                              regime_of_validity="1D QHO")
        # Manually set status to approved_for_promotion to test conflict detection
        tr = _topic_root(td, TOPIC)
        cand_path = tr / "L3" / "candidates" / "energy-formula.md"
        fm, body = _parse_md(cand_path)
        fm["status"] = "approved_for_promotion"
        _write_md(cand_path, fm, body)

        r = aitp_promote_candidate(td, TOPIC, "energy-formula")
        assert "Conflict" in r or "conflict" in r.lower()

    def test_trust_evolution(self, tmp_path):
        """Verify trust level progression through the evolution ladder."""
        td = _setup_td(tmp_path)

        # Create node with source_grounded (default)
        aitp_create_l2_node(td, "test-concept", "concept", "Test Concept",
                            physical_meaning="A test concept for trust evolution")
        graph = aitp_query_l2_graph(td, query="test concept")
        node = graph["nodes"][0]
        assert node["trust_basis"] == "source_grounded"

        # Upgrade to multi_source_confirmed
        aitp_update_l2_node(td, "test-concept", trust_level="multi_source_confirmed")
        graph = aitp_query_l2_graph(td, query="test concept")
        node = graph["nodes"][0]
        assert node["trust_basis"] == "multi_source_confirmed"

        # Upgrade to validated
        aitp_update_l2_node(td, "test-concept", trust_level="validated")
        graph = aitp_query_l2_graph(td, query="test concept")
        node = graph["nodes"][0]
        assert node["trust_basis"] == "validated"

        # Upgrade to independently_verified
        aitp_update_l2_node(td, "test-concept", trust_level="independently_verified")
        graph = aitp_query_l2_graph(td, query="test concept")
        node = graph["nodes"][0]
        assert node["trust_basis"] == "independently_verified"
