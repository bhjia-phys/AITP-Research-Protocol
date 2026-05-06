"""Tests for L3 subplane gates, cross-activity prerequisite checks, and
candidate submission guardrails."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from brain import mcp_server
from brain.state_model import (
    evaluate_l1_stage,
    evaluate_l3_stage,
    L3_ACTIVITIES,
    L3_ACTIVITY_TEMPLATES,
    L3_ACTIVITY_ARTIFACT_NAMES,
    topics_dir,
)
from tests.test_state_model import BootstrapL1ScaffoldTests


def _bootstrap_l1_complete(tmp: str) -> Path:
    """Bootstrap a topic with L0+L1 gates filled so it can advance to L3."""
    repo_root = Path(tmp)
    (repo_root / "topics").mkdir(exist_ok=True)
    # Use __wrapped__ to bypass @mcp.tool() signature transform
    mcp_server.aitp_bootstrap_topic.__wrapped__(
        str(repo_root), "demo-topic", "Demo Topic", "What is the bounded question?",
    )
    tr = repo_root / "topics" / "demo-topic"

    # Fill L0 gate: source_registry + register a source
    mcp_server._write_md(
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
    mcp_server._write_md(
        tr / "L0" / "sources" / "paper-a.md",
        {"artifact_kind": "l0_source", "source_type": "paper",
         "slug": "paper-a", "short_title": "Paper A"},
        "# Paper A\n\nA source.\n",
    )
    # Advance L0 -> L1
    mcp_server.aitp_advance_to_l1(str(repo_root), "demo-topic")

    filled = {
        "question_contract.md": (
            {"artifact_kind": "l1_question_contract", "stage": "L1",
             "bounded_question": "What quantity is bounded here?",
             "scope_boundaries": "One model, one regime. This does NOT ask about all-loop order or other representations.",
             "target_quantities": "Gap and symmetry sector.",
             "competing_hypotheses": "Alternative: the gap may vanish in certain limits."},
            "# Question Contract\n\n## Bounded Question\nWhat quantity is bounded here?\n\n"
            "## Competing Hypotheses\nAlternative: the gap may vanish in certain limits.\n\n"
            "## Scope Boundaries\nOne model, one regime. This does NOT ask about all-loop order.\n\n"
            "## Target Quantities Or Claims\nGap and symmetry sector.\n\n"
            "## Non-Success Conditions\nIf the gap closes at the Gamma point, the claim is falsified.\n\n"
            "## Uncertainty Markers\nFinite-size risk.\n\n## L2 Cross-Reference\nNo prior L2 knowledge for this test topic. Unit test fixture.\n",
        ),
        "source_basis.md": (
            {"artifact_kind": "l1_source_basis", "stage": "L1",
             "core_sources": "paper-a", "peripheral_sources": "note-b"},
            "# Source Basis\n\n## Core Sources\npaper-a\n\n## Peripheral Sources\nnote-b\n\n"
            "## Source Roles\npaper-a is the main derivation source.\n\n"
            "## Reading Depth\nfull_read for paper-a.\n\n"
            "## Why Each Source Matters\npaper-a defines the bounded route.\n",
        ),
        "convention_snapshot.md": (
            {"artifact_kind": "l1_convention_snapshot", "stage": "L1",
             "notation_choices": "Use source-a symbols.",
             "unit_conventions": "Natural units."},
            "# Convention Snapshot\n\n## Notation Choices\nUse source-a symbols.\n\n"
            "## Unit Conventions\nNatural units.\n\n"
            "## Sign Conventions\nHamiltonian sign fixed.\n\n"
            "## Metric Or Coordinate Conventions\nEuclidean.\n\n"
            "## Unresolved Tensions\nNone blocking.\n",
        ),
        "derivation_anchor_map.md": (
            {"artifact_kind": "l1_derivation_anchor_map", "stage": "L1",
             "starting_anchors": "eq-12"},
            "# Derivation Anchor Map\n\n## Source Anchors\neq-12\n\n"
            "## Missing Steps\nOne omitted algebra step.\n\n"
            "## Candidate Starting Points\neq-12 to eq-14.\n",
        ),
        "contradiction_register.md": (
            {"artifact_kind": "l1_contradiction_register", "stage": "L1",
             "blocking_contradictions": "none"},
            "# Contradiction Register\n\n## Unresolved Source Conflicts\nNone.\n\n"
            "## Regime Mismatches\nNone blocking.\n\n"
            "## Notation Collisions\nTracked and resolved.\n\n"
            "## Blocking Status\nnone\n",
        ),
        "source_toc_map.md": (
            {"artifact_kind": "l1_source_toc_map", "stage": "L1",
             "sources_with_toc": "paper-a", "total_sections": 1,
             "coverage_status": "complete"},
            "# Source TOC Map\n\n## Per-Source TOC\n\n"
            "### paper-a (TOC confidence: high)\n\n"
            "- [s1] Main Content  --  status: extracted  -> intake: L1/intake/paper-a/s1.md\n\n"
            "## Coverage Summary\n\n## Deferred Sections\n\n## Extraction Notes\n",
        ),
    }
    for name, (fm, body) in filled.items():
        mcp_server._write_md(tr / "L1" / name, fm, body)
    # Create intake note for extracted section (required by L1 quality gate)
    intake_dir = tr / "L1" / "intake" / "paper-a"
    intake_dir.mkdir(parents=True, exist_ok=True)
    mcp_server._write_md(
        intake_dir / "s1.md",
        {"artifact_kind": "l1_section_intake", "source_id": "paper-a",
         "section_id": "s1", "section_title": "Main Content",
         "extraction_status": "extracted", "completeness_confidence": "high",
         "updated_at": "2025-01-01T00:00:00Z"},
        "# Main Content\n\n## Section Summary (skim)\nContent.\n\n"
        "## Key Concepts\nConcept.\n\n## Equations Found\neq.\n\n"
        "## Physical Claims\nClaim.\n\n## Prerequisites\nNone.\n\n"
        "## Cross-References\nNone.\n\n## Completeness Self-Assessment\nConfidence: **high**\n",
    )
    return repo_root


def _write_filled_artifact(tr: Path, activity: str, fm: dict, body: str):
    """Write a filled L3 activity artifact."""
    from brain.state_model import L3_ACTIVITY_ARTIFACT_NAMES
    name = L3_ACTIVITY_ARTIFACT_NAMES.get(activity, f"active_{activity}.md")
    dest = tr / "L3" / activity / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    mcp_server._write_md(dest, fm, body)


# ── Activity validity tests ────────────────────────────────────────────────


class L3ActivityValidityTests(unittest.TestCase):
    """Tests for activity list and switching."""

    def test_connect_removed_from_valid_activities(self):
        """connect subplane was removed — it is no longer a valid activity."""
        self.assertNotIn("connect", L3_ACTIVITIES)
        self.assertNotIn("connect", L3_ACTIVITY_ARTIFACT_NAMES)
        self.assertNotIn("connect", L3_ACTIVITY_TEMPLATES)

    def test_new_l3_topic_starts_in_ideate(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            brief = mcp_server.aitp_get_execution_brief(tmp, "demo-topic")
            self.assertEqual(brief["stage"], "L3")
            self.assertEqual(brief["l3_subplane"], "ideate")
            self.assertIn("blocked", brief["gate_status"])

    def test_invalid_activity_name_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            result = mcp_server.aitp_switch_l3_activity(
                str(repo_root), "demo-topic", "nonexistent",
            )
            self.assertIn("Unknown activity", result)

    def test_connect_activity_rejected(self):
        """connect was removed — switching to it must be rejected."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            result = mcp_server.aitp_switch_l3_activity(
                str(repo_root), "demo-topic", "connect",
            )
            self.assertIn("Unknown activity", result)


# ── Activity switching (flexible workspace) ────────────────────────────────


class L3ActivitySwitchTests(unittest.TestCase):
    """Activity switching is allowed at any time (flexible workspace),
    but the gate reports blocked_incomplete when prerequisites are missing."""

    def test_switch_to_derive_is_allowed(self):
        """Entry to any activity is always allowed."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            result = mcp_server.aitp_switch_l3_activity(
                str(repo_root), "demo-topic", "derive",
            )
            self.assertIn("derive", result.lower())

    def test_sequence_with_filled_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            tr = repo_root / "topics" / "demo-topic"
            # Fill ideate artifact
            _write_filled_artifact(
                tr, "ideate",
                {"artifact_kind": "l3_active_idea", "activity": "ideate",
                 "idea_statement": "Test idea", "motivation": "Why this matters"},
                "# Active Idea\n\n## Idea Statement\nTest idea\n\n## Motivation\nWhy this matters\n",
            )
            result = mcp_server.aitp_switch_l3_activity(
                str(repo_root), "demo-topic", "plan",
            )
            self.assertIn("plan", result.lower())
            brief = mcp_server.aitp_get_execution_brief(tmp, "demo-topic")
            self.assertEqual(brief["l3_subplane"], "plan")

    def test_backedge_from_derive_to_ideate_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            tr = repo_root / "topics" / "demo-topic"
            _write_filled_artifact(
                tr, "ideate",
                {"artifact_kind": "l3_active_idea", "activity": "ideate",
                 "idea_statement": "Idea", "motivation": "Motivation"},
                "# Active Idea\n\n## Idea Statement\nIdea\n\n## Motivation\nMotivation\n",
            )
            mcp_server.aitp_switch_l3_activity(str(repo_root), "demo-topic", "plan")
            _write_filled_artifact(
                tr, "plan",
                {"artifact_kind": "l3_active_plan", "activity": "plan",
                 "plan_statement": "Plan", "derivation_route": "Route"},
                "# Active Plan\n\n## Plan Statement\nPlan\n\n## Derivation Route\nRoute\n",
            )
            mcp_server.aitp_switch_l3_activity(str(repo_root), "demo-topic", "derive")
            # Backedge to ideate is always allowed
            result = mcp_server.aitp_switch_l3_activity(
                str(repo_root), "demo-topic", "ideate",
            )
            self.assertIn("ideate", result.lower())


# ── Cross-activity prerequisite gate tests ─────────────────────────────────


class L3CrossActivityPrerequisiteTests(unittest.TestCase):
    """The gate reports blocked_incomplete when upstream artifacts lack
    real content. Entry to any activity is still allowed, but the gate
    reflects the incomplete state."""

    def _parse_md(self, path):
        import yaml
        if not path.exists():
            return {}, ""
        text = path.read_text(encoding="utf-8")
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                try:
                    return yaml.safe_load(parts[1]) or {}, parts[2] if len(parts) > 2 else ""
                except Exception:
                    return {}, parts[2] if len(parts) > 2 else ""
        return {}, text

    def test_distill_without_integrate_is_blocked_incomplete(self):
        """When in distill but integrate Findings is empty, gate reports blocked_incomplete."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            tr = repo_root / "topics" / "demo-topic"
            # Switch directly to distill without filling integrate
            mcp_server.aitp_switch_l3_activity(str(repo_root), "demo-topic", "distill")
            # Write minimal distill artifact to pass template check
            _write_filled_artifact(
                tr, "distill",
                {"artifact_kind": "l3_active_distillation", "activity": "distill",
                 "distilled_claim": "Claim", "evidence_summary": "Evidence"},
                "# Active Distillation\n\n## Distilled Claim\nClaim\n\n"
                "## Evidence Summary\nEvidence\n",
            )
            snapshot = evaluate_l3_stage(self._parse_md, tr)
            self.assertEqual(snapshot.gate_status, "blocked_incomplete")
            self.assertTrue(
                any("Findings" in issue for issue in snapshot.missing_requirements),
                f"Expected 'Findings' mention in: {snapshot.missing_requirements}",
            )

    def test_distill_without_gap_audit_is_blocked_incomplete(self):
        """When in distill but gap-audit Correspondence Check is empty."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            tr = repo_root / "topics" / "demo-topic"
            # Fill integrate with real Findings content
            _write_filled_artifact(
                tr, "integrate",
                {"artifact_kind": "l3_active_integration", "activity": "integrate",
                 "integration_statement": "Integrated", "findings": "F1, F2"},
                "# Active Integration\n\n## Integration Statement\nIntegrated\n\n"
                "## Findings\nHere are detailed findings from the integration phase. "
                "The derivation produces consistent results across all tested limits. "
                "No unresolved contradictions remain.\n",
            )
            mcp_server.aitp_switch_l3_activity(str(repo_root), "demo-topic", "distill")
            _write_filled_artifact(
                tr, "distill",
                {"artifact_kind": "l3_active_distillation", "activity": "distill",
                 "distilled_claim": "Claim", "evidence_summary": "Evidence"},
                "# Active Distillation\n\n## Distilled Claim\nClaim\n\n"
                "## Evidence Summary\nEvidence\n",
            )
            snapshot = evaluate_l3_stage(self._parse_md, tr)
            self.assertEqual(snapshot.gate_status, "blocked_incomplete")
            self.assertTrue(
                any("Correspondence Check" in issue for issue in snapshot.missing_requirements),
                f"Expected 'Correspondence Check' mention in: {snapshot.missing_requirements}",
            )

    def test_integrate_without_gap_audit_is_blocked_incomplete(self):
        """When in integrate but gap-audit Correspondence Check is empty."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            tr = repo_root / "topics" / "demo-topic"
            # Fill derive with real content
            _write_filled_artifact(
                tr, "derive",
                {"artifact_kind": "l3_active_derivation", "activity": "derive",
                 "derivation_count": 3, "all_steps_justified": "yes"},
                "# Active Derivation\n\n## Derivation Chains\n"
                "D1: From Hamiltonian to response. Step 1: express chi_0. "
                "Step 2: Fourier transform. Step 3: Matsubara sum. "
                "All steps closed.\n"
                "## Step-by-Step Trace\nTraced.\n",
            )
            mcp_server.aitp_switch_l3_activity(str(repo_root), "demo-topic", "integrate")
            _write_filled_artifact(
                tr, "integrate",
                {"artifact_kind": "l3_active_integration", "activity": "integrate",
                 "integration_statement": "Integrated", "findings": "F1"},
                "# Active Integration\n\n## Integration Statement\nIntegrated\n\n"
                "## Findings\nFindings here.\n",
            )
            snapshot = evaluate_l3_stage(self._parse_md, tr)
            self.assertEqual(snapshot.gate_status, "blocked_incomplete")
            self.assertTrue(
                any("Correspondence Check" in issue for issue in snapshot.missing_requirements),
                f"Expected 'Correspondence Check' mention in: {snapshot.missing_requirements}",
            )

    def test_derive_without_plan_is_blocked_incomplete(self):
        """When in derive but plan Derivation Route is empty."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            tr = repo_root / "topics" / "demo-topic"
            mcp_server.aitp_switch_l3_activity(str(repo_root), "demo-topic", "derive")
            _write_filled_artifact(
                tr, "derive",
                {"artifact_kind": "l3_active_derivation", "activity": "derive",
                 "derivation_count": 1, "all_steps_justified": "no"},
                "# Active Derivation\n\n## Derivation Chains\nD1 start.\n"
                "## Step-by-Step Trace\nStep 1.\n",
            )
            snapshot = evaluate_l3_stage(self._parse_md, tr)
            self.assertEqual(snapshot.gate_status, "blocked_incomplete")
            self.assertTrue(
                any("Derivation Route" in issue for issue in snapshot.missing_requirements),
                f"Expected 'Derivation Route' mention in: {snapshot.missing_requirements}",
            )

    def test_blocked_incomplete_when_derive_done_but_no_candidates(self):
        """When in integrate/distill with real derivation but zero candidates."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            tr = repo_root / "topics" / "demo-topic"
            # Fill derive with substantial real content
            _write_filled_artifact(
                tr, "derive",
                {"artifact_kind": "l3_active_derivation", "activity": "derive",
                 "derivation_count": 5, "all_steps_justified": "yes"},
                "# Active Derivation\n\n## Derivation Chains\n"
                "D1: Full derivation from Hamiltonian to observable. "
                "Step 1: Define the partition function in the path-integral "
                "representation with source terms. Step 2: Perform the Hubbard-"
                "Stratonovich transformation to decouple the interaction. "
                "Step 3: Integrate out fermions to obtain an effective action. "
                "Step 4: Apply the saddle-point approximation. "
                "Step 5: Compute the Gaussian fluctuations.\n"
                "## Step-by-Step Trace\nDetailed trace follows.\n",
            )
            # Fill gap-audit with real correspondence check
            _write_filled_artifact(
                tr, "gap-audit",
                {"artifact_kind": "l3_active_gaps", "activity": "gap-audit",
                 "gap_count": 1, "blocking_gaps": "none"},
                "# Active Gap Audit\n\n## Unstated Assumptions\n"
                "Assumption: translational invariance is maintained.\n\n"
                "## Correspondence Check\n"
                "Limit 1: q→0 recovers RPA dielectric function. "
                "Limit 2: T→0 matches zero-temperature Lindhard. "
                "Both limits verified analytically.\n"
                "## Prerequisite Gaps\nNone.\n",
            )
            mcp_server.aitp_switch_l3_activity(str(repo_root), "demo-topic", "integrate")
            _write_filled_artifact(
                tr, "integrate",
                {"artifact_kind": "l3_active_integration", "activity": "integrate",
                 "integration_statement": "Integrated results", "findings": "F1, F2, F3"},
                "# Active Integration\n\n## Integration Statement\nResults integrated.\n\n"
                "## Findings\nFinding 1: derivation is self-consistent. "
                "Finding 2: all correspondence limits pass. "
                "Finding 3: result reduces to known RPA in static limit.\n",
            )
            # No candidates submitted — but work is done
            snapshot = evaluate_l3_stage(self._parse_md, tr)
            self.assertEqual(snapshot.gate_status, "blocked_incomplete")
            self.assertTrue(
                any("no candidates" in issue.lower() for issue in snapshot.missing_requirements),
                f"Expected 'no candidates' mention in: {snapshot.missing_requirements}",
            )

    def test_all_prerequisites_satisfied_is_ready(self):
        """When all cross-activity prerequisites are met, gate is ready."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            tr = repo_root / "topics" / "demo-topic"
            # Fill plan → derive → gap-audit → integrate → distill
            _write_filled_artifact(
                tr, "plan",
                {"artifact_kind": "l3_active_plan", "activity": "plan",
                 "plan_statement": "Plan", "derivation_route": "Route: D1→D2→D3"},
                "# Active Plan\n\n## Plan Statement\nPlan\n\n"
                "## Derivation Route\nRoute: Step 1 builds the Hamiltonian. "
                "Step 2 diagonalizes in momentum space. "
                "Step 3 computes the response.\n",
            )
            _write_filled_artifact(
                tr, "derive",
                {"artifact_kind": "l3_active_derivation", "activity": "derive",
                 "derivation_count": 3, "all_steps_justified": "yes"},
                "# Active Derivation\n\n## Derivation Chains\n"
                "D1: Hamiltonian → diagonalization → response. "
                "Full derivation with all steps justified. "
                "Derivation is complete and self-consistent.\n"
                "## Step-by-Step Trace\nTraced.\n",
            )
            _write_filled_artifact(
                tr, "gap-audit",
                {"artifact_kind": "l3_active_gaps", "activity": "gap-audit",
                 "gap_count": 0, "blocking_gaps": ""},
                "# Active Gap Audit\n\n## Unstated Assumptions\nNone hidden.\n\n"
                "## Correspondence Check\nLimit q→0 recovers the known RPA dielectric function. "
                "Limit ω→0 matches the static Lindhard formula. Both verified.\n"
                "## Prerequisite Gaps\nNone.\n",
            )
            _write_filled_artifact(
                tr, "integrate",
                {"artifact_kind": "l3_active_integration", "activity": "integrate",
                 "integration_statement": "Done", "findings": "F1, F2"},
                "# Active Integration\n\n## Integration Statement\nIntegrated.\n\n"
                "## Findings\nAll results consistent. Correspondences pass. "
                "No open obligations blocking submission.\n",
            )
            # Create a candidate
            cand_dir = tr / "L3" / "candidates"
            cand_dir.mkdir(parents=True, exist_ok=True)
            mcp_server._write_md(
                cand_dir / "test-candidate.md",
                {"candidate_id": "test-candidate", "status": "submitted",
                 "derivation_chain_id": "D1", "source_refs": ["paper-a"],
                 "claim_statement": "The response function is correct."},
                "# Candidate\n\n## Claim\nVerified.\n",
            )
            # Switch to distill (which has real content and prerequisites met)
            mcp_server.aitp_switch_l3_activity(str(repo_root), "demo-topic", "distill")
            _write_filled_artifact(
                tr, "distill",
                {"artifact_kind": "l3_active_distillation", "activity": "distill",
                 "distilled_claim": "Final claim", "evidence_summary": "Evidence done"},
                "# Active Distillation\n\n## Distilled Claim\nFinal claim.\n\n"
                "## Evidence Summary\nAll evidence supports the claim.\n",
            )
            snapshot = evaluate_l3_stage(self._parse_md, tr)
            self.assertEqual(snapshot.gate_status, "ready")

    def test_ideate_never_blocked_by_prerequisites(self):
        """ideate is the entry point — it has no upstream prerequisites."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            tr = repo_root / "topics" / "demo-topic"
            _write_filled_artifact(
                tr, "ideate",
                {"artifact_kind": "l3_active_idea", "activity": "ideate",
                 "idea_statement": "Idea", "motivation": "Motivation"},
                "# Active Idea\n\n## Idea Statement\nIdea\n\n## Motivation\nMotivation\n",
            )
            snapshot = evaluate_l3_stage(self._parse_md, tr)
            # ideate has no prerequisites — should be ready once its own
            # artifact is filled
            self.assertEqual(snapshot.gate_status, "ready")


# ── Session start skill mention ─────────────────────────────────────────────


class L3SubplaneSkillTests(unittest.TestCase):
    REPO_ROOT = Path(__file__).resolve().parents[1]

    def test_session_start_mentions_l3_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            completed = subprocess.run(
                [sys.executable, str(self.REPO_ROOT / "hooks" / "session_start.py")],
                cwd=repo_root, text=True, capture_output=True,
            )
            self.assertIn("stage: L3", completed.stdout)
            self.assertIn("ideate", completed.stdout)
            self.assertIn("skill-l3-ideate", completed.stdout)


# ── L3-L4 interface tests ───────────────────────────────────────────────────


class L3L4InterfaceTests(unittest.TestCase):
    """Tests for the L3-L4 interface: direct submit activities, advance gate,
    and background job → review lifecycle."""

    def _parse_md(self, path):
        import yaml
        if not path.exists():
            return {}, ""
        text = path.read_text(encoding="utf-8")
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                try:
                    return yaml.safe_load(parts[1]) or {}, parts[2] if len(parts) > 2 else ""
                except Exception:
                    return {}, parts[2] if len(parts) > 2 else ""
        return {}, text

    def test_direct_submit_excludes_derive(self):
        """derive cannot be in _DIRECT_SUBMIT_ACTIVITIES — content checks
        require integrate/gap-audit artifacts that don't exist yet."""
        from brain.contracts import _DIRECT_SUBMIT_ACTIVITIES
        self.assertNotIn("derive", _DIRECT_SUBMIT_ACTIVITIES)
        self.assertEqual(_DIRECT_SUBMIT_ACTIVITIES, {"distill", "integrate"})

    def test_l4_check_results_sets_review_needed_flag(self):
        """aitp_l4_check_results must set l4_review_needed=True in state.md."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            tr = repo_root / "topics" / "demo-topic"
            # Set up as L3 with background job submitted
            state_path = tr / "state.md"
            fm, body = self._parse_md(state_path)
            fm["l4_background_status"] = "submitted"
            fm["l4_job_id"] = "12345"
            fm["l4_job_host"] = "fisher"
            fm["stage"] = "L3"  # check_results requires being at L3 from bg job
            from brain.cli.commands.l3_workflow import _write_md
            _write_md(state_path, fm, body)

            result = mcp_server.aitp_l4_check_results(
                str(repo_root), "demo-topic",
                job_status="success", output_summary="All tests passed.",
            )
            self.assertTrue(result.get("l4_review_needed"))
            # Verify state.md has the flag
            fm2, _ = self._parse_md(state_path)
            self.assertTrue(fm2.get("l4_review_needed"))

    def test_submit_l4_review_clears_review_needed_flag(self):
        """aitp_submit_l4_review must clear l4_review_needed from state.md."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            tr = repo_root / "topics" / "demo-topic"
            # Set up: create candidate, set stage to L4, set review_needed flag
            cand_dir = tr / "L3" / "candidates"
            cand_dir.mkdir(parents=True, exist_ok=True)
            mcp_server._write_md(
                cand_dir / "test-candidate.md",
                {"candidate_id": "test-candidate", "status": "submitted",
                 "claim_statement": "A claim that needs validation.",
                 "source_refs": ["paper-a"]},
                "# Candidate\n\n## Claim\nA claim.\n",
            )
            state_path = tr / "state.md"
            fm, body = self._parse_md(state_path)
            fm["stage"] = "L4"
            fm["posture"] = "verify"
            fm["l4_review_needed"] = True
            from brain.cli.commands.l3_workflow import _write_md
            _write_md(state_path, fm, body)

            # Submit a pass review
            mcp_server.aitp_submit_l4_review.__wrapped__(
                str(repo_root), "demo-topic", "test-candidate",
                outcome="pass",
                notes="Verification passed.",
                devils_advocate="Assumes exact diagonalization is converged.",
                check_results={
                    "dimensional_consistency": "pass",
                    "correspondence_check": "pass: matches known limit",
                },
            )
            # Verify flag is cleared
            fm2, _ = self._parse_md(state_path)
            self.assertNotIn("l4_review_needed", fm2)


if __name__ == "__main__":
    unittest.main()
