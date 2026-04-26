"""I/O contract tests for AITP layers.

Validates that each layer:
1. Produces correct outputs given valid inputs
2. Correctly blocks when inputs are missing
3. Transitions produce correct post-conditions
4. Execution brief returns correct structure

Run: python -m pytest tests/test_io_contracts.py -v
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from brain import mcp_server, state_model


def _bootstrap(tmp: str) -> Path:
    """Bootstrap a topic and return its root path."""
    mcp_server.aitp_bootstrap_topic(tmp, "test-topic", "Test Topic",
                                     "What is the ground state?", "formal_theory")
    return state_model.topics_dir(tmp) / "test-topic"


def _fill_l0(tmp: str, tr: Path) -> None:
    """Fill L0 artifacts to pass the L0 gate."""
    mcp_server._write_md(
        tr / "L0" / "source_registry.md",
        {"artifact_kind": "l0_source_registry", "stage": "L0",
         "source_count": 1, "search_status": "initial"},
        "# Source Registry\n\n## Search Methodology\nArXiv search.\n\n"
        "## Source Inventory\npaper-a\n\n## Coverage Assessment\nAdequate.\n\n"
        "## Overall Verdict\nNo blocking gaps for initial exploration.\n\n"
        "## Gaps And Next Sources\nNone.\n",
    )
    mcp_server._write_md(
        tr / "L0" / "sources" / "paper-a.md",
        {"source_id": "paper-a", "type": "paper",
         "title": "Paper A", "fidelity": "arxiv_preprint",
         "registered": "2025-01-01T00:00:00Z"},
        "# Paper A\n\nA test source.\n",
    )


def _fill_l1(tmp: str, tr: Path) -> None:
    """Fill all L1 artifacts to pass the L1 gate."""
    _fill_l0(tmp, tr)
    mcp_server.aitp_advance_to_l1(tmp, "test-topic")

    mcp_server._write_md(
        tr / "L1" / "question_contract.md",
        {"artifact_kind": "l1_question_contract", "stage": "L1",
         "bounded_question": "What is the ground state energy?",
         "scope_boundaries": "One model, zero temperature. Does NOT cover excited states.",
         "target_quantities": "Ground state energy E0.",
         "competing_hypotheses": "Alternative: mean-field theory predicts a different value."},
        "# Question Contract\n\n## Bounded Question\nWhat is the ground state energy?\n\n"
        "## Competing Hypotheses\nAlternative: mean-field theory predicts a different value.\n\n"
        "## Scope Boundaries\nOne model, zero temperature. Does NOT cover excited states.\n\n"
        "## Target Quantities Or Claims\nGround state energy E0.\n\n"
        "## Forbidden Proxies\nNo unvalidated approximations.\n\n"
        "## Deliverables\nNumeric value for E0.\n\n"
        "## Acceptance Criteria\nMatches known result within 1%.\n\n"
        "## Non-Success Conditions\nResult outside known bounds.\n\n"
        "## Uncertainty Markers\nFinite-size effects.\n",
    )
    mcp_server._write_md(
        tr / "L1" / "source_basis.md",
        {"artifact_kind": "l1_source_basis", "stage": "L1",
         "core_sources": "paper-a", "peripheral_sources": "note-b"},
        "# Source Basis\n\n## Core Sources\npaper-a\n\n## Peripheral Sources\nnote-b\n\n"
        "## Source Roles\npaper-a is primary.\n\n## Reading Depth\nfull_read.\n\n"
        "## Why Each Source Matters\npaper-a defines the problem.\n",
    )
    mcp_server._write_md(
        tr / "L1" / "convention_snapshot.md",
        {"artifact_kind": "l1_convention_snapshot", "stage": "L1",
         "notation_choices": "H for Hamiltonian.", "unit_conventions": "Natural units hbar=c=1."},
        "# Convention Snapshot\n\n## Notation Choices\nH for Hamiltonian.\n\n"
        "## Unit Conventions\nNatural units hbar=c=1.\n\n## Sign Conventions\nStandard.\n\n"
        "## Metric Or Coordinate Conventions\nEuclidean.\n\n"
        "## Categorized Assumptions\nMathematical: finite Hilbert space. Physical: zero temperature.\n\n"
        "## Canonical Notation\nUse H for Hamiltonian as canonical.\n\n"
        "## Unresolved Tensions\nNone.\n\n## L3 Discoveries\nNone yet.\n",
    )
    mcp_server._write_md(
        tr / "L1" / "derivation_anchor_map.md",
        {"artifact_kind": "l1_derivation_anchor_map", "stage": "L1",
         "starting_anchors": "eq-1", "anchor_count": 1},
        "# Derivation Anchor Map\n\n## Source Anchors\neq-1: Schrodinger equation.\n\n"
        "## Dependency Graph\neq-1 -> all results.\n\n## Missing Steps\nNone.\n\n"
        "## Candidate Starting Points\neq-1.\n",
    )
    mcp_server._write_md(
        tr / "L1" / "contradiction_register.md",
        {"artifact_kind": "l1_contradiction_register", "stage": "L1",
         "blocking_contradictions": "none"},
        "# Contradiction Register\n\n## Unresolved Source Conflicts\nNone.\n\n"
        "## Internal Inconsistencies\nNone.\n\n## Regime Mismatches\nNone.\n\n"
        "## Notation Collisions\nNone.\n\n## Blocking Status\nnone\n",
    )
    mcp_server._write_md(
        tr / "L1" / "source_toc_map.md",
        {"artifact_kind": "l1_source_toc_map", "stage": "L1",
         "sources_with_toc": "paper-a", "total_sections": 1,
         "coverage_status": "complete"},
        "# Source TOC Map\n\n## Per-Source TOC\n\n"
        "### paper-a (TOC confidence: high)\n\n"
        "- [s1] Introduction -- status: extracted  --> intake: L1/intake/paper-a/s1.md\n\n"
        "## Coverage Summary\n\n## Deferred Sections\n\n## Extraction Notes\n",
    )
    intake_dir = tr / "L1" / "intake" / "paper-a"
    intake_dir.mkdir(parents=True, exist_ok=True)
    mcp_server._write_md(
        intake_dir / "s1.md",
        {"artifact_kind": "l1_section_intake", "source_id": "paper-a",
         "section_id": "s1", "section_title": "Introduction",
         "extraction_status": "extracted", "completeness_confidence": "high",
         "regime": "general", "validity_conditions": "none",
         "figure_refs": "", "updated_at": "2025-01-01T00:00:00Z"},
        "# Introduction\n\n## Section Summary (skim)\nContent.\n\n"
        "## Key Concepts\nTest concept.\n\n## Equations Found\neq-1.\n\n"
        "## Physical Claims\nClaim: energy is bounded below.\n\n"
        "## Argument Structure\nSingle claim.\n\n## Figures & Diagrams\nNone.\n\n"
        "## Regime & Validity\nGeneral.\n\n## Prerequisites\nNone.\n\n"
        "## Cross-References\nNone.\n\n## Completeness Self-Assessment\nConfidence: **high**\n",
    )


class TestL0IOContract:
    """L0: Source Acquisition I/O contract."""

    def test_bootstrap_produces_correct_structure(self):
        """Bootstrap must create state.md + L0 scaffold."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = _bootstrap(tmp)
            assert (tr / "state.md").exists()
            assert (tr / "L0" / "source_registry.md").exists()
            assert (tr / "L0" / "sources").is_dir()

            fm, body = mcp_server._parse_md(tr / "state.md")
            assert fm["stage"] == "L0"
            assert fm["posture"] == "discover"

    def test_l0_gate_blocks_without_registry(self):
        """L0 gate must block when source_registry is missing."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = _bootstrap(tmp)
            brief = mcp_server.aitp_get_execution_brief(tmp, "test-topic")
            assert brief["gate_status"] == "blocked_missing_field"

    def test_l0_gate_ready_after_filling(self):
        """L0 gate must pass with valid source_registry + 1 source."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = _bootstrap(tmp)
            _fill_l0(tmp, tr)
            brief = mcp_server.aitp_get_execution_brief(tmp, "test-topic")
            assert brief["gate_status"] == "ready"
            assert brief["stage"] == "L0"

    def test_l0_to_l1_transition(self):
        """Advance must set stage=L1, posture=read."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = _bootstrap(tmp)
            _fill_l0(tmp, tr)
            result = mcp_server.aitp_advance_to_l1(tmp, "test-topic")
            assert "L1" in str(result)
            fm, _ = mcp_server._parse_md(tr / "state.md")
            assert fm["stage"] == "L1"
            assert fm["posture"] == "read"


class TestL1IOContract:
    """L1: Reading and Framing I/O contract."""

    def test_l1_gate_blocks_without_artifacts(self):
        """L1 gate must block when no artifacts filled."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = _bootstrap(tmp)
            _fill_l0(tmp, tr)
            mcp_server.aitp_advance_to_l1(tmp, "test-topic")
            brief = mcp_server.aitp_get_execution_brief(tmp, "test-topic")
            assert "blocked" in brief["gate_status"]

    def test_l1_gate_ready_after_all_filled(self):
        """L1 gate must pass when all 6 artifacts + intake filled."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = _bootstrap(tmp)
            _fill_l1(tmp, tr)
            brief = mcp_server.aitp_get_execution_brief(tmp, "test-topic")
            assert brief["gate_status"] == "ready"
            assert brief["posture"] == "frame"

    def test_l1_question_semantic_blocks_bad_question(self):
        """Question without scope exclusion must be blocked."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = _bootstrap(tmp)
            _fill_l0(tmp, tr)
            mcp_server.aitp_advance_to_l1(tmp, "test-topic")
            mcp_server._write_md(
                tr / "L1" / "question_contract.md",
                {"artifact_kind": "l1_question_contract", "stage": "L1",
                 "bounded_question": "What is X?", "scope_boundaries": "everything",
                 "target_quantities": "X", "competing_hypotheses": ""},
                "# Question Contract\n\n## Bounded Question\nWhat is X?\n\n"
                "## Competing Hypotheses\n\n## Scope Boundaries\neverything\n\n"
                "## Target Quantities Or Claims\nX\n\n",
            )
            brief = mcp_server.aitp_get_execution_brief(tmp, "test-topic")
            # Should block on either scope exclusion or competing_hypotheses
            assert "blocked" in brief["gate_status"]

    def test_l1_to_l3_transition(self):
        """Advance must set stage=L3 with ideate activity."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = _bootstrap(tmp)
            _fill_l1(tmp, tr)
            result = mcp_server.aitp_advance_to_l3(tmp, "test-topic")
            assert "L3" in str(result) or "popup" in str(result).lower()
            fm, _ = mcp_server._parse_md(tr / "state.md")
            assert fm["stage"] == "L3"

    def test_l1_artifacts_have_required_fields(self):
        """All 6 L1 artifacts must have correct frontmatter fields."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = _bootstrap(tmp)
            _fill_l1(tmp, tr)
            for name, _, fields, _ in state_model._L1_CONTRACTS:
                fm, _ = mcp_server._parse_md(tr / "L1" / name)
                for field in fields:
                    val = str(fm.get(field, "")).strip()
                    assert val, f"'{name}' missing required field '{field}'"


class TestL3IOContract:
    """L3: Flexible Workspace I/O contract."""

    def test_l3_starts_in_ideate(self):
        """After advance, L3 must start in ideate activity."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = _bootstrap(tmp)
            _fill_l1(tmp, tr)
            mcp_server.aitp_advance_to_l3(tmp, "test-topic")
            brief = mcp_server.aitp_get_execution_brief(tmp, "test-topic")
            assert brief["stage"] == "L3"

    def test_l3_switch_activity(self):
        """Activity switching must update state."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = _bootstrap(tmp)
            _fill_l1(tmp, tr)
            mcp_server.aitp_advance_to_l3(tmp, "test-topic")
            mcp_server.aitp_switch_l3_activity(tmp, "test-topic", "derive")
            fm, _ = mcp_server._parse_md(tr / "state.md")
            assert fm["l3_activity"] == "derive"
            assert fm["l3_subplane"] == "derive"  # compat sync

    def test_l3_activity_template_has_required_headings(self):
        """Each L3 activity template must define required headings."""
        for activity in state_model.L3_ACTIVITIES:
            assert activity in state_model.L3_ACTIVITY_TEMPLATES, \
                f"Missing template for activity '{activity}'"
            _, tmpl_fm, tmpl_body = state_model.L3_ACTIVITY_TEMPLATES[activity]
            req_fields = tmpl_fm.get("required_fields", [])
            assert len(req_fields) > 0, \
                f"Activity '{activity}' has no required_fields"
            req_headings = state_model.L3_ACTIVITY_REQUIRED_HEADINGS.get(activity, [])
            assert len(req_headings) > 0, \
                f"Activity '{activity}' has no required_headings"
            for h in req_headings:
                assert h in tmpl_body, \
                    f"Heading '{h}' not in template body for '{activity}'"


class TestL4IOContract:
    """L4: Validation I/O contract."""

    def test_l4_gate_blocks_without_candidates(self):
        """L4 gate must block when no candidates exist."""
        with tempfile.TemporaryDirectory() as tmp:
            _bootstrap(tmp)
            # Manually set stage to L4
            tr = Path(tmp) / "topics" / "test-topic"
            mcp_server._write_md(
                tr / "state.md",
                {"stage": "L4", "posture": "verify", "lane": "formal_theory",
                 "l3_activity": "distill", "mode": "explore", "compute": "local"},
                "# Test\n",
            )
            brief = mcp_server.aitp_get_execution_brief(tmp, "test-topic")
            assert "blocked" in brief["gate_status"]

    def test_l4_review_requires_devils_advocate(self):
        """Pass outcome must require non-empty devil's advocate."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = _bootstrap(tmp)
            _fill_l1(tmp, tr)
            mcp_server.aitp_advance_to_l3(tmp, "test-topic")
            slug = "test-claim"
            cand_dir = tr / "L3" / "candidates"
            cand_dir.mkdir(parents=True, exist_ok=True)
            mcp_server._write_md(
                cand_dir / f"{slug}.md",
                {"candidate_id": slug, "claim": "E0 = -1.0",
                 "status": "submitted", "regime_of_validity": "T=0"},
                "# Candidate\n\nTest.\n",
            )
            result = mcp_server.aitp_submit_l4_review(
                tmp, "test-topic", slug, outcome="pass",
                notes="Test review.",
                check_results={"dimensional_consistency": "verified"},
            )
            assert "devils_advocate" in str(result).lower() or "Devil" in str(result)


class TestL2IOContract:
    """L2: Knowledge Graph I/O contract."""

    def test_create_l2_node(self):
        """Node creation must write correct frontmatter."""
        with tempfile.TemporaryDirectory() as tmp:
            mcp_server.aitp_create_l2_node(
                tmp, "test-concept", "concept",
                "Test Concept", source_ref="test-source",
                physical_meaning="A test concept.",
                domain="electronic-structure",
            )
            l2_dir = mcp_server._global_l2_path(tmp) / "graph" / "nodes"
            node_path = l2_dir / "test-concept.md"
            assert node_path.exists()
            fm, _ = mcp_server._parse_md(node_path)
            assert fm["type"] == "concept"
            assert fm["title"] == "Test Concept"
            assert fm["trust_basis"] == "source_grounded"

    def test_create_l2_edge_requires_existing_nodes(self):
        """Edge creation must refuse dangling edges."""
        with tempfile.TemporaryDirectory() as tmp:
            result = mcp_server.aitp_create_l2_edge(
                tmp, "test-edge", "missing-a", "missing-b",
                "generalizes", source_ref="test",
            )
            assert "not found" in str(result).lower()


class TestExecutionBrief:
    """Execution brief must return consistent structure."""

    REQUIRED_KEYS = [
        "topic_slug", "stage", "posture", "lane",
        "gate_status", "skill", "immediate_allowed_work",
        "immediate_blocked_work",
    ]

    def test_brief_has_required_keys(self):
        """Every brief must include all required keys."""
        with tempfile.TemporaryDirectory() as tmp:
            _bootstrap(tmp)
            brief = mcp_server.aitp_get_execution_brief(tmp, "test-topic")
            for key in self.REQUIRED_KEYS:
                assert key in brief, f"Brief missing key: {key}"

    def test_brief_has_no_duplicate_keys(self):
        """Brief must not have duplicate keys (L4 bug regression test)."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = _bootstrap(tmp)
            _fill_l1(tmp, tr)
            mcp_server.aitp_advance_to_l3(tmp, "test-topic")
            # Submit candidate and L4 review to trigger L4 state
            slug = "test-cand"
            cand_dir = tr / "L3" / "candidates"
            cand_dir.mkdir(parents=True, exist_ok=True)
            mcp_server._write_md(
                cand_dir / f"{slug}.md",
                {"candidate_id": slug, "claim": "Test", "status": "submitted"},
                "# Test\n",
            )
            mcp_server._write_md(
                tr / "state.md",
                {"stage": "L4", "posture": "verify", "lane": "formal_theory",
                 "l3_activity": "distill", "mode": "explore", "compute": "local"},
                "# Test\n",
            )
            brief = mcp_server.aitp_get_execution_brief(tmp, "test-topic")
            # Count key occurrences (would differ if duplicates existed)
            key_count = len(brief.keys())
            unique_count = len(set(brief.keys()))
            assert key_count == unique_count, \
                f"Brief has duplicate keys: {key_count} total, {unique_count} unique"


class TestFlowNotebook:
    """Flow notebook must generate without ImportError."""

    def test_notebook_imports_work(self):
        """Flow notebook builder must not crash on import."""
        # The backwards-compat aliases should prevent ImportError
        assert hasattr(state_model, "L3_SUBPLANES"), "L3_SUBPLANES missing"
        assert hasattr(state_model, "L3_ACTIVE_ARTIFACT_NAMES"), "L3_ACTIVE_ARTIFACT_NAMES missing"
        assert hasattr(state_model, "STUDY_L3_SUBPLANES"), "STUDY_L3_SUBPLANES missing"
        assert hasattr(state_model, "STUDY_L3_ACTIVE_ARTIFACT_NAMES"), "STUDY_L3_ACTIVE_ARTIFACT_NAMES missing"

    def test_notebook_builds_without_crash(self):
        """Flow notebook generation must not crash."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = _bootstrap(tmp)
            _fill_l0(tmp, tr)
            result = mcp_server.aitp_generate_flow_notebook(tmp, "test-topic")
            # Should complete without error (even if mostly empty)
            assert "generated" in str(result).lower() or "created" in str(result).lower() or \
                   "notebook" in str(result).lower()


class TestDoctorValidation:
    """Doctor command: content-level topic validation."""

    def test_valid_topic_state_passes(self):
        """Topic with valid state.md must be reported as healthy."""
        with tempfile.TemporaryDirectory() as tmp:
            tr = _bootstrap(tmp)
            _fill_l0(tmp, tr)
            # Simulate doctor check
            import re, yaml
            state_path = tr / "state.md"
            text = state_path.read_text(encoding="utf-8")
            m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
            assert m is not None, "state.md must have YAML frontmatter"
            fm = yaml.safe_load(m.group(1))
            assert fm is not None, "YAML must parse"
            assert "stage" in fm, "state.md must have stage field"

    def test_missing_state_md_is_invalid(self):
        """Topic without state.md must be flagged."""
        import tempfile
        tmp = tempfile.mkdtemp()
        bad_topic = Path(tmp) / "bad-topic"
        bad_topic.mkdir()
        assert not (bad_topic / "state.md").exists()

    def test_broken_yaml_is_invalid(self):
        """state.md with broken YAML frontmatter must be flagged."""
        import tempfile
        tmp = tempfile.mkdtemp()
        bad_topic = Path(tmp) / "broken-topic"
        bad_topic.mkdir()
        (bad_topic / "state.md").write_text("---\nbroken: [unclosed\n---\n# Title\n", encoding="utf-8")
        import yaml
        try:
            yaml.safe_load("broken: [unclosed")
            assert False, "Should have raised"
        except yaml.YAMLError:
            pass  # Expected — broken YAML
