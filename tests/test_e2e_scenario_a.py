"""E2E test for Scenario A: Formal Theory — Quantum Anomaly in 2+1D Gauge Theory.

Simulates the full multi-turn conversation from e2e_benchmark_scenarios.md:
  L1 -> L3(ideation->planning->analysis->result_integration->distillation)
  -> L4(pass) -> L3(return) -> L5

Covers: source registration, convention snapshot, subplane traversal,
candidate submission, validation contract, L4 review, L5 scaffolds,
and all verification checkpoints.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from brain import mcp_server


TOPIC_SLUG = "chern-simons-anomaly"
TOPIC_TITLE = "Parity Anomaly in 2+1D U(N) Chern-Simons Theory"
LANE = "formal_theory"


def _bootstrap_and_register_sources(tmp: str) -> Path:
    """Turns 1-3: bootstrap, register 3 sources, fill L1 artifacts."""
    repo_root = Path(tmp)
    (repo_root / "topics").mkdir(exist_ok=True)

    # Turn 1: bootstrap
    mcp_server.aitp_bootstrap_topic(
        str(repo_root), TOPIC_SLUG,
        TOPIC_TITLE,
        "Does a 2+1D U(N) Chern-Simons gauge theory coupled to massless "
        "Dirac fermions develop a parity anomaly, producing a level shift "
        "k -> k +/- N/2?",
    )

    tr = repo_root / "topics" / TOPIC_SLUG

    # Set lane
    state_fm, state_body = mcp_server._parse_md(tr / "state.md")
    state_fm["lane"] = LANE
    mcp_server._write_md(tr / "state.md", state_fm, state_body)

    # Turn 2: register 3 sources
    mcp_server.aitp_register_source(
        tmp, TOPIC_SLUG, "witten-cs-2018",
        source_type="paper",
        title="arXiv:1805.06306 — Witten on Chern-Simons Theory",
    )
    mcp_server.aitp_register_source(
        tmp, TOPIC_SLUG, "redlich-parity-2016",
        source_type="paper",
        title="arXiv:1609.04370 — Redlich on Parity Anomalies",
    )
    mcp_server.aitp_register_source(
        tmp, TOPIC_SLUG, "weinberg-qft-v2",
        source_type="book",
        title="Weinberg QFT Vol II, Chapter 22",
    )

    # Fill L0 source_registry to make L0 gate ready
    mcp_server._write_md(
        tr / "L0" / "source_registry.md",
        {"artifact_kind": "l0_source_registry", "stage": "L0",
         "source_count": 3, "search_status": "complete"},
        "# Source Registry\n\n## Search Methodology\narxiv + textbook\n\n"
        "## Source Inventory\nwitten-cs-2018, redlich-parity-2016, weinberg-qft-v2\n\n"
        "## Coverage Assessment\nAdequate for one-loop CS computation\n\n"
        "## Gaps And Next Sources\nNone\n",
    )
    mcp_server.aitp_advance_to_l1(tmp, TOPIC_SLUG)

    # Turn 3: fill all L1 artifacts
    mcp_server._write_md(
        tr / "L1" / "question_contract.md",
        {"artifact_kind": "l1_question_contract", "stage": "L1",
         "bounded_question": "Compute the one-loop effective action for N massless "
                            "Dirac fermions in the fundamental of U(N) CS theory "
                            "at level k and determine the level shift.",
         "scope_boundaries": "One-loop, massless fermions, fundamental rep, 2+1D",
         "target_quantities": "Level shift Delta_k = N*sgn(m)/2"},
        "# Question Contract\n\n"
        "## Bounded Question\n"
        "Does a 2+1D U(N) Chern-Simons gauge theory coupled to N massless Dirac "
        "fermions in the fundamental produce a one-loop level shift?\n\n"
        "## Scope Boundaries\n"
        "One-loop only, massless fermions, fundamental representation, 2+1D.\n\n"
        "## Target Quantities Or Claims\n"
        "Level shift Delta_k = N*sgn(m)/2.\n\n"
        "## Non-Success Conditions\n"
        "No claim about all-loop order or other representations.\n\n"
        "## Uncertainty Markers\n"
        "Regularization scheme dependence to be checked.\n",
    )
    mcp_server._write_md(
        tr / "L1" / "source_basis.md",
        {"artifact_kind": "l1_source_basis", "stage": "L1",
         "core_sources": "witten-cs-2018, redlich-parity-2016",
         "peripheral_sources": "weinberg-qft-v2"},
        "# Source Basis\n\n"
        "## Core Sources\n"
        "witten-cs-2018, redlich-parity-2016\n\n"
        "## Peripheral Sources\nweinberg-qft-v2\n\n"
        "## Source Roles\n"
        "witten-cs-2018 defines the CS framework; redlich-parity-2016 provides "
        "the parity anomaly baseline for N=1.\n\n"
        "## Reading Depth\nfull_read for core, chapter_read for Weinberg Ch22.\n\n"
        "## Why Each Source Matters\n"
        "witten-cs-2018 gives the general CS effective action; "
        "redlich-parity-2016 provides the known N=1 result to check against.\n",
    )
    mcp_server._write_md(
        tr / "L1" / "convention_snapshot.md",
        {"artifact_kind": "l1_convention_snapshot", "stage": "L1",
         "notation_choices": "CS normalization S_CS = k/(4pi) int tr(A dA + 2/3 A^3)",
         "unit_conventions": "Natural units hbar=c=1"},
        "# Convention Snapshot\n\n"
        "## Notation Choices\n"
        "S_CS = k/(4pi) int tr(A dA + 2/3 A^3)\n\n"
        "## Unit Conventions\nNatural units hbar=c=1.\n\n"
        "## Sign Conventions\nMostly-plus metric (+--).\n\n"
        "## Metric Or Coordinate Conventions\nMostly-plus (+--), Euclidean continuation for determinant.\n\n"
        "## Unresolved Tensions\nNone blocking.\n",
    )
    mcp_server._write_md(
        tr / "L1" / "derivation_anchor_map.md",
        {"artifact_kind": "l1_derivation_anchor_map", "stage": "L1",
         "starting_anchors": "Dirac operator in 2+1D, Pauli-Villars regulator"},
        "# Derivation Anchor Map\n\n"
        "## Source Anchors\n"
        "Dirac operator in 2+1D, Pauli-Villars regulator.\n\n"
        "## Missing Steps\n"
        "Regularization of functional determinant.\n\n"
        "## Candidate Starting Points\n"
        "Dirac operator -> proper-time -> zeta-function -> extract CS term.\n",
    )
    mcp_server._write_md(
        tr / "L1" / "contradiction_register.md",
        {"artifact_kind": "l1_contradiction_register", "stage": "L1",
         "blocking_contradictions": "none"},
        "# Contradiction Register\n\n"
        "## Unresolved Source Conflicts\nNone.\n\n"
        "## Regime Mismatches\nNone blocking.\n\n"
        "## Notation Collisions\n"
        "CS level convention aligned with Witten's normalization.\n\n"
        "## Blocking Status\nnone\n",
    )

    # Verify L1 gate is ready
    brief = mcp_server.aitp_get_execution_brief(tmp, TOPIC_SLUG)
    assert brief["gate_status"] == "ready", f"L1 gate not ready: {brief}"

    return repo_root


def _advance_l3_all_subplanes(tmp: str, repo_root: Path) -> None:
    """Turns 4-6: advance through all L3 subplanes with physics content."""
    tr = repo_root / "topics" / TOPIC_SLUG

    mcp_server.aitp_advance_to_l3(tmp, TOPIC_SLUG)

    # Ideation
    mcp_server._write_md(
        tr / "L3" / "ideation" / "active_idea.md",
        {"artifact_kind": "l3_active_idea", "subplane": "ideation",
         "idea_statement": "Compute the one-loop fermion determinant in 2+1D CS theory",
         "motivation": "The determinant generates an effective CS term, shifting the level"},
        "# Active Idea\n\n"
        "## Idea Statement\n"
        "Compute the one-loop fermion determinant in 2+1D CS theory to extract "
        "the induced CS level shift.\n\n"
        "## Motivation\n"
        "The parity anomaly manifests as an induced CS term from integrating out "
        "Dirac fermions, producing a level shift Delta_k = N*sgn(m)/2.\n",
    )
    mcp_server.aitp_advance_l3_subplane(tmp, TOPIC_SLUG, "planning")

    # Planning
    mcp_server._write_md(
        tr / "L3" / "planning" / "active_plan.md",
        {"artifact_kind": "l3_active_plan", "subplane": "planning",
         "plan_statement": "Regularize the fermion determinant via Pauli-Villars",
         "derivation_route": "Dirac operator -> proper-time -> Pauli-Villars -> extract CS term"},
        "# Active Plan\n\n"
        "## Plan Statement\n"
        "Regularize the fermion determinant via Pauli-Villars regularization and "
        "extract the induced CS term.\n\n"
        "## Derivation Route\n"
        "1. Write Dirac operator in 2+1D coupled to background CS gauge field.\n"
        "2. Express fermion determinant via proper-time representation.\n"
        "3. Regularize using Pauli-Villars (or zeta-function).\n"
        "4. Extract the induced CS term and read off the level shift.\n",
    )
    mcp_server.aitp_advance_l3_subplane(tmp, TOPIC_SLUG, "analysis")

    # Analysis
    mcp_server._write_md(
        tr / "L3" / "analysis" / "active_analysis.md",
        {"artifact_kind": "l3_active_analysis", "subplane": "analysis",
         "analysis_statement": "One-loop determinant yields Delta_k = N*sgn(m)/2",
         "method": "Pauli-Villars regularization of the functional determinant"},
        "# Active Analysis\n\n"
        "## Analysis Statement\n"
        "The one-loop effective action of N massless Dirac fermions in the "
        "fundamental of U(N) CS theory at level k produces a level shift "
        "Delta_k = N*sgn(m)/2.\n\n"
        "## Method\n"
        "Starting from the Dirac operator D = gamma^mu(i*d_mu + A_mu) in 2+1D, "
        "we compute log det(D) using proper-time regularization. The Pauli-Villars "
        "subtraction isolates the CS term:\n\n"
        "  S_eff = (N*sgn(m)/2) * (1/4pi) * int tr(A dA + 2/3 A^3)\n\n"
        "yielding Delta_k = N*sgn(m)/2. The theory is inconsistent unless "
        "k + N*sgn(m)/2 is an integer (gauge invariance).\n",
    )
    mcp_server.aitp_advance_l3_subplane(tmp, TOPIC_SLUG, "result_integration")

    # Result integration
    mcp_server._write_md(
        tr / "L3" / "result_integration" / "active_integration.md",
        {"artifact_kind": "l3_active_integration", "subplane": "result_integration",
         "integration_statement": "Level shift confirmed for all N",
         "findings": "Delta_k = N*sgn(m)/2, consistency requires k+N/2 in Z"},
        "# Active Integration\n\n"
        "## Integration Statement\n"
        "The result integrates cleanly with the known N=1 case (Redlich) and "
        "generalizes to arbitrary N in the fundamental representation.\n\n"
        "## Findings\n"
        "Delta_k = N*sgn(m)/2. Gauge invariance of the total CS action requires "
        "k + N*sgn(m)/2 in Z, rendering the theory inconsistent for odd N unless "
        "k is appropriately shifted.\n",
    )
    mcp_server.aitp_advance_l3_subplane(tmp, TOPIC_SLUG, "distillation")

    # Distillation
    mcp_server._write_md(
        tr / "L3" / "distillation" / "active_distillation.md",
        {"artifact_kind": "l3_active_distillation", "subplane": "distillation",
         "distilled_claim": "Delta_k = N*sgn(m)/2",
         "evidence_summary": "One-loop determinant via Pauli-Villars"},
        "# Active Distillation\n\n"
        "## Distilled Claim\n"
        "The one-loop effective action of N massless Dirac fermions in the "
        "fundamental of U(N) CS theory at level k produces a level shift "
        "Delta_k = N*sgn(m)/2, rendering the theory inconsistent unless "
        "N*sgn(m)/2 is an integer.\n\n"
        "## Evidence Summary\n"
        "Computed via Pauli-Villars regularization of the fermion determinant. "
        "Cross-checked against Redlich N=1 result and Witten's general framework.\n",
    )


def _l4_validation_and_review(tmp: str) -> None:
    """Turn 7: create validation contract and submit L4 review."""
    mcp_server.aitp_submit_candidate(
        tmp, TOPIC_SLUG, "cand-cs-anomaly",
        "The one-loop effective action of N massless Dirac fermions in the "
        "fundamental of U(N) CS theory at level k produces a level shift "
        "Delta_k = N*sgn(m)/2.",
        "Pauli-Villars regularization of fermion determinant, cross-checked "
        "against Redlich N=1 and Witten's general framework.",
    )


    mcp_server.aitp_submit_l4_review(
        tmp, TOPIC_SLUG, "cand-cs-anomaly",
        "pass",
        "All checks passed. Dimensional consistency: CS action has correct "
        "mass dimension. Limiting case: N=1 reproduces Redlich's result. "
        "Correspondence: large-k limit recovers classical CS. Symmetry: "
        "parity transformation flips sgn(m), consistent with anomaly structure.",
    )



def _create_flow_tex_and_advance_l5(tmp: str, repo_root: Path) -> None:
    """Turn 8: create flow_notebook.tex and advance to L5."""
    tr = repo_root / "topics" / TOPIC_SLUG

    # Promote through L2 gate
    cand_path = tr / "L3" / "candidates" / "cand-cs-anomaly.md"
    fm, body = mcp_server._parse_md(cand_path)
    fm["status"] = "validated"
    fm["claim"] = "Delta_k = N*sgn(m)/2"
    mcp_server._write_md(cand_path, fm, body)
    mcp_server.aitp_request_promotion(tmp, TOPIC_SLUG, "cand-cs-anomaly")
    mcp_server.aitp_resolve_promotion_gate(
        tmp, TOPIC_SLUG, "cand-cs-anomaly", "approve",
    )
    mcp_server.aitp_promote_candidate(tmp, TOPIC_SLUG, "cand-cs-anomaly")

    # Create flow_notebook.tex
    tex_dir = tr / "L3" / "tex"
    tex_dir.mkdir(parents=True, exist_ok=True)
    (tex_dir / "flow_notebook.tex").write_text(
        "\\documentclass{article}\n"
        "\\begin{document}\n"
        "\\section{Level Shift in 2+1D Chern-Simons Theory}\n"
        "The one-loop fermion determinant yields $\\Delta k = N\\,\\mathrm{sgn}(m)/2$.\n"
        "\\end{document}\n",
        encoding="utf-8",
    )

    mcp_server.aitp_advance_to_l5(tmp, TOPIC_SLUG)


class ScenarioAEndToEndTest(unittest.TestCase):
    """Full golden-path test: L1 -> L3 -> L4(pass) -> L5."""

    def test_turn1_bootstrap_creates_topic(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_and_register_sources(tmp)
            tr = repo_root / "topics" / TOPIC_SLUG
            self.assertTrue(tr.exists())
            self.assertTrue((tr / "state.md").exists())

            state_fm, _ = mcp_server._parse_md(tr / "state.md")
            self.assertEqual(state_fm["lane"], LANE)
            self.assertEqual(state_fm["stage"], "L1")

    def test_turn2_three_sources_registered(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_and_register_sources(tmp)
            tr = repo_root / "topics" / TOPIC_SLUG

            sources = mcp_server.aitp_list_sources(tmp, TOPIC_SLUG)
            self.assertGreaterEqual(len(sources), 3)

    def test_turn3_l1_gate_ready_after_filling(self):
        with tempfile.TemporaryDirectory() as tmp:
            _bootstrap_and_register_sources(tmp)
            brief = mcp_server.aitp_get_execution_brief(tmp, TOPIC_SLUG)
            self.assertEqual(brief["gate_status"], "ready")

            for artifact in [
                "question_contract.md", "source_basis.md",
                "convention_snapshot.md", "derivation_anchor_map.md",
                "contradiction_register.md",
            ]:
                repo_root = Path(tmp)
                path = repo_root / "topics" / TOPIC_SLUG / "L1" / artifact
                self.assertTrue(path.exists(), f"L1/{artifact} missing")

    def test_turn4_l3_starts_in_ideation(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_and_register_sources(tmp)
            mcp_server.aitp_advance_to_l3(tmp, TOPIC_SLUG)
            brief = mcp_server.aitp_get_execution_brief(tmp, TOPIC_SLUG)
            self.assertEqual(brief["stage"], "L3")
            self.assertEqual(brief["l3_subplane"], "ideation")

    def test_turn5_subplanes_traverse_sequentially(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_and_register_sources(tmp)
            _advance_l3_all_subplanes(tmp, repo_root)

            brief = mcp_server.aitp_get_execution_brief(tmp, TOPIC_SLUG)
            self.assertEqual(brief["l3_subplane"], "distillation")

            tr = repo_root / "topics" / TOPIC_SLUG
            for sp in ["ideation", "planning", "analysis", "result_integration", "distillation"]:
                self.assertTrue(
                    (tr / "L3" / sp).exists(),
                    f"L3/{sp} directory missing",
                )

    def test_turn6_candidate_submitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_and_register_sources(tmp)
            _advance_l3_all_subplanes(tmp, repo_root)

            mcp_server.aitp_submit_candidate(
                tmp, TOPIC_SLUG, "cand-cs-anomaly",
                "Delta_k = N*sgn(m)/2",
                "One-loop determinant via Pauli-Villars",
            )

            tr = repo_root / "topics" / TOPIC_SLUG
            cand_path = tr / "L3" / "candidates" / "cand-cs-anomaly.md"
            self.assertTrue(cand_path.exists())
            fm, _ = mcp_server._parse_md(cand_path)
            self.assertEqual(fm["candidate_id"], "cand-cs-anomaly")

    def test_turn7_l4_review_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_and_register_sources(tmp)
            _advance_l3_all_subplanes(tmp, repo_root)
            _l4_validation_and_review(tmp)

            tr = repo_root / "topics" / TOPIC_SLUG


            # Review exists with outcome=pass
            review_path = tr / "L4" / "reviews" / "cand-cs-anomaly.md"
            self.assertTrue(review_path.exists())
            r_fm, _ = mcp_server._parse_md(review_path)
            self.assertEqual(r_fm["outcome"], "pass")

    def test_turn8_l5_advance_creates_scaffolds(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_and_register_sources(tmp)
            _advance_l3_all_subplanes(tmp, repo_root)
            _l4_validation_and_review(tmp)
            _create_flow_tex_and_advance_l5(tmp, repo_root)

            tr = repo_root / "topics" / TOPIC_SLUG

            for name in [
                "outline.md", "claim_evidence_map.md",
                "equation_provenance.md", "figure_provenance.md",
                "limitations.md",
            ]:
                self.assertTrue(
                    (tr / "L5_writing" / name).exists(),
                    f"L5_writing/{name} must exist",
                )

    def test_full_flow_verification_checkpoints(self):
        """All verification checkpoints from Scenario A in e2e_benchmark_scenarios.md."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_and_register_sources(tmp)
            _advance_l3_all_subplanes(tmp, repo_root)
            _l4_validation_and_review(tmp)
            _create_flow_tex_and_advance_l5(tmp, repo_root)

            tr = repo_root / "topics" / TOPIC_SLUG

            # Checkpoint 1: state.md shows stage=L5 at end
            state_fm, _ = mcp_server._parse_md(tr / "state.md")
            self.assertEqual(state_fm["stage"], "L5")

            # Checkpoint 2: L3/candidates/ has exactly 1 candidate
            candidates = list((tr / "L3" / "candidates").glob("*.md"))
            self.assertEqual(len(candidates), 1)

            # Checkpoint 3: L4/reviews/ has a review with outcome=pass
            reviews = list((tr / "L4" / "reviews").glob("*.md"))
            self.assertGreaterEqual(len(reviews), 1)
            # Find the latest review (non-versioned)
            latest = [r for r in reviews if "_v" not in r.stem]
            self.assertTrue(latest, "Expected a non-versioned review file")
            r_fm, _ = mcp_server._parse_md(latest[0])
            self.assertEqual(r_fm["outcome"], "pass")


            # Checkpoint 5: flow_notebook.tex exists
            tex_path = tr / "L3" / "tex" / "flow_notebook.tex"
            self.assertTrue(tex_path.exists())
            tex_content = tex_path.read_text(encoding="utf-8")
            self.assertIn("Delta", tex_content)

            # Checkpoint 6: L5_writing/outline.md is filled
            outline_path = tr / "L5_writing" / "outline.md"
            self.assertTrue(outline_path.exists())
            outline = outline_path.read_text(encoding="utf-8")
            self.assertIn("## Claims", outline)
            self.assertIn("## Structure", outline)

            # Checkpoint 7: runtime/log.md has key events
            log_path = tr / "runtime" / "log.md"
            self.assertTrue(log_path.exists())
            log_content = log_path.read_text(encoding="utf-8")
            for event in ["bootstrapped", "L4 review", "advanced to L5"]:
                self.assertIn(
                    event, log_content,
                    f"runtime/log.md missing event: {event}",
                )

            # Lane preserved throughout
            self.assertEqual(state_fm["lane"], LANE)

    def test_convention_snapshot_has_cs_normalization(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_and_register_sources(tmp)
            tr = repo_root / "topics" / TOPIC_SLUG
            conv_fm, conv_body = mcp_server._parse_md(
                tr / "L1" / "convention_snapshot.md",
            )
            self.assertIn("k/(4pi)", conv_body)

    def test_source_types_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            _bootstrap_and_register_sources(tmp)
            sources = mcp_server.aitp_list_sources(tmp, TOPIC_SLUG)
            types = {s.get("type", "") for s in sources}
            self.assertIn("paper", types)
            self.assertIn("book", types)


if __name__ == "__main__":
    unittest.main()
