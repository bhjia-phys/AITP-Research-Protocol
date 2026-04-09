from __future__ import annotations

import unittest
from pathlib import Path


class L2GovernanceDocsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel_root = Path(__file__).resolve().parents[1]
        self.repo_root = Path(__file__).resolve().parents[3]

    def test_governance_plane_spec_exists_and_architecture_points_to_it(self) -> None:
        spec_path = (
            self.repo_root
            / "docs"
            / "superpowers"
            / "specs"
            / "2026-04-08-l2-governance-plane-consolidation-design.md"
        )
        architecture = (self.repo_root / "docs" / "AITP_UNIFIED_RESEARCH_ARCHITECTURE.md").read_text(
            encoding="utf-8"
        )

        self.assertTrue(spec_path.exists())
        spec_text = spec_path.read_text(encoding="utf-8")
        self.assertIn("L2 Governance Plane Consolidation Design", spec_text)
        self.assertIn("governance plane", architecture)
        self.assertIn("paired downstream realizations", architecture)
        self.assertIn("consultation outputs", architecture)

    def test_consultation_protocol_defines_human_and_ai_output_surfaces(self) -> None:
        consultation = (self.kernel_root / "L2_CONSULTATION_PROTOCOL.md").read_text(encoding="utf-8")

        self.assertIn("Human-facing consultation outputs", consultation)
        self.assertIn("AI-facing consultation outputs", consultation)
        self.assertIn("derived from the same promoted identity", consultation)
        self.assertIn("Consultation is not promotion", consultation)

    def test_governance_spec_locks_shared_core_and_edge_vocabulary(self) -> None:
        spec_path = (
            self.repo_root
            / "docs"
            / "superpowers"
            / "specs"
            / "2026-04-08-l2-governance-plane-consolidation-design.md"
        )
        spec_text = spec_path.read_text(encoding="utf-8")

        self.assertIn("Shared `L2` Core", spec_text)
        self.assertIn("formal_theory", spec_text)
        self.assertIn("toy_numeric", spec_text)
        self.assertIn("code_method", spec_text)
        self.assertIn("theory_synthesis", spec_text)
        self.assertIn("Canonical edge vocabulary", spec_text)
        self.assertIn("depends_on", spec_text)
        self.assertIn("applies_in_regime", spec_text)
        self.assertIn("valid_under", spec_text)
        self.assertIn("warns_about", spec_text)

    def test_paired_backend_maintenance_protocol_is_present(self) -> None:
        maintenance = self.kernel_root / "canonical" / "L2_PAIRED_BACKEND_MAINTENANCE_PROTOCOL.md"

        self.assertTrue(maintenance.exists())
        text = maintenance.read_text(encoding="utf-8")
        self.assertIn("backend debt", text)
        self.assertIn("drift audit", text)
        self.assertIn("rebuild", text)

    def test_governance_docs_lock_lean_reserve_and_v128_non_goals(self) -> None:
        architecture = (self.repo_root / "docs" / "AITP_UNIFIED_RESEARCH_ARCHITECTURE.md").read_text(
            encoding="utf-8"
        )
        canonical_readme = (self.kernel_root / "canonical" / "README.md").read_text(encoding="utf-8")

        self.assertIn("Lean", architecture)
        self.assertIn("downstream export path", architecture)
        self.assertIn("not the definition of `L2` success", architecture)
        self.assertIn("L2_PAIRED_BACKEND_MAINTENANCE_PROTOCOL.md", canonical_readme)
        self.assertIn("L2_MVP_CONTRACT.md", canonical_readme)

    def test_architecture_freeze_exposes_task_type_h_plane_and_l3_subplanes(self) -> None:
        architecture = (self.repo_root / "docs" / "AITP_UNIFIED_RESEARCH_ARCHITECTURE.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("task_type", architecture)
        self.assertIn("H-plane", architecture)
        self.assertIn("open_exploration", architecture)
        self.assertIn("conjecture_attempt", architecture)
        self.assertIn("target_driven_execution", architecture)
        self.assertIn("code_and_materials", architecture)
        self.assertIn("L3-A", architecture)
        self.assertIn("L3-R", architecture)
        self.assertIn("L3-D", architecture)
        self.assertIn("L4 -> L3-R", architecture)

    def test_layer_map_defines_layer_outputs_and_consumers(self) -> None:
        layer_map = (self.kernel_root / "LAYER_MAP.md").read_text(encoding="utf-8")

        self.assertIn("Task-type framing", layer_map)
        self.assertIn("Human interaction plane", layer_map)
        self.assertIn("Layer 3 — Research analysis / result integration / distillation", layer_map)
        self.assertIn("Primary outputs", layer_map)
        self.assertIn("Consumed by", layer_map)
        self.assertIn("L3-A", layer_map)
        self.assertIn("L3-R", layer_map)
        self.assertIn("L3-D", layer_map)
        self.assertIn("L4 outputs must return to `L3-R`", layer_map)


if __name__ == "__main__":
    unittest.main()
