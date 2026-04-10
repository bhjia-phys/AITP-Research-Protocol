from __future__ import annotations

import json
import unittest
from pathlib import Path

import sys

from jsonschema import Draft202012Validator


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()


class L2BackendContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel_root = Path(__file__).resolve().parents[1]
        self.schema = json.loads(
            (self.kernel_root / "schemas" / "l2-backend.schema.json").read_text(encoding="utf-8")
        )
        self.validator = Draft202012Validator(self.schema)

    def test_backend_template_conforms_to_schema(self) -> None:
        payload = json.loads(
            (self.kernel_root / "canonical" / "backends" / "backend.template.json").read_text(encoding="utf-8")
        )
        self.validator.validate(payload)

    def test_formal_theory_example_card_conforms_to_schema(self) -> None:
        payload = json.loads(
            (
                self.kernel_root
                / "canonical"
                / "backends"
                / "examples"
                / "formal-theory-note-library.example.json"
            ).read_text(encoding="utf-8")
        )
        self.validator.validate(payload)
        self.assertEqual(payload["backend_type"], "human_note_library")
        self.assertEqual(payload["source_policy"]["default_source_type"], "local_note")
        self.assertIn("derivation_object", payload["canonical_targets"])
        self.assertEqual(
            payload["l0_registration"]["script"],
            "source-layer/scripts/register_local_note_source.py",
        )

    def test_formal_theory_starter_references_smoke_script(self) -> None:
        starter = (
            self.kernel_root / "canonical" / "backends" / "FORMAL_THEORY_BACKEND_STARTER.md"
        ).read_text(encoding="utf-8")
        smoke_script = self.kernel_root / "runtime" / "scripts" / "run_formal_theory_backend_smoke.sh"
        self.assertTrue(smoke_script.exists())
        self.assertIn("run_formal_theory_backend_smoke.sh", starter)
        self.assertIn("SEMI_FORMAL_THEORY_PROTOCOL.md", starter)

    def test_tpkn_backend_card_and_smoke_script_exist(self) -> None:
        payload = json.loads(
            (
                self.kernel_root
                / "canonical"
                / "backends"
                / "theoretical-physics-knowledge-network.json"
            ).read_text(encoding="utf-8")
        )
        smoke_script = self.kernel_root / "runtime" / "scripts" / "run_tpkn_formal_promotion_smoke.sh"
        auto_smoke_script = (
            self.kernel_root / "runtime" / "scripts" / "run_tpkn_formal_auto_promotion_smoke.sh"
        )
        self.validator.validate(payload)
        self.assertEqual(payload["backend_type"], "mixed_local_library")
        self.assertIn("derivation_object", payload["canonical_targets"])
        self.assertIn("equation_card", payload["canonical_targets"])
        self.assertTrue(payload["source_policy"]["allows_auto_canonical_promotion"])
        self.assertTrue(smoke_script.exists())
        self.assertTrue(auto_smoke_script.exists())

    def test_real_topic_acceptance_script_is_present_and_documented(self) -> None:
        acceptance_script = (
            self.kernel_root / "runtime" / "scripts" / "run_witten_topological_phases_formal_closure_acceptance.py"
        )
        jones_acceptance_script = (
            self.kernel_root / "runtime" / "scripts" / "run_jones_chapter4_finite_product_formal_closure_acceptance.py"
        )
        scrpa_acceptance_script = (
            self.kernel_root / "runtime" / "scripts" / "run_scrpa_thesis_topic_acceptance.py"
        )
        code_method_acceptance_script = (
            self.kernel_root / "runtime" / "scripts" / "run_tfim_benchmark_code_method_acceptance.py"
        )
        readme = (self.kernel_root / "README.md").read_text(encoding="utf-8")
        runbook = (self.kernel_root / "runtime" / "AITP_TEST_RUNBOOK.md").read_text(encoding="utf-8")
        self.assertTrue(acceptance_script.exists())
        self.assertTrue(jones_acceptance_script.exists())
        self.assertTrue(scrpa_acceptance_script.exists())
        self.assertTrue(code_method_acceptance_script.exists())
        self.assertIn("run_witten_topological_phases_formal_closure_acceptance.py", readme)
        self.assertIn("run_jones_chapter4_finite_product_formal_closure_acceptance.py", readme)
        self.assertIn("run_scrpa_thesis_topic_acceptance.py", readme)
        self.assertIn("run_tfim_benchmark_code_method_acceptance.py", readme)
        self.assertIn("run_jones_chapter4_finite_product_formal_closure_acceptance.py", runbook)
        self.assertIn("run_scrpa_thesis_topic_acceptance.py", runbook)
        self.assertIn("run_tfim_benchmark_code_method_acceptance.py", runbook)

    def test_jones_acceptance_docs_reference_formal_theory_projection_outputs(self) -> None:
        readme = (self.kernel_root / "README.md").read_text(encoding="utf-8")
        runtime_readme = (self.kernel_root / "runtime" / "README.md").read_text(encoding="utf-8")
        runbook = (self.kernel_root / "runtime" / "AITP_TEST_RUNBOOK.md").read_text(encoding="utf-8")

        self.assertIn("human-promotes", readme)
        self.assertIn("units/topic-skill-projections/", readme)
        self.assertIn("human-promotes", runtime_readme)
        self.assertIn("units/topic-skill-projections/", runtime_readme)
        self.assertIn("topic_skill_projection.active.json|md", runbook)
        self.assertIn("units/topic-skill-projections/", runbook)

    def test_l2_compiler_protocol_is_present_and_referenced(self) -> None:
        protocol_path = self.kernel_root / "canonical" / "L2_COMPILER_PROTOCOL.md"
        canonical_readme = (self.kernel_root / "canonical" / "README.md").read_text(encoding="utf-8")
        consultation_protocol = (self.kernel_root / "L2_CONSULTATION_PROTOCOL.md").read_text(encoding="utf-8")
        communication_contract = (self.kernel_root / "COMMUNICATION_CONTRACT.md").read_text(encoding="utf-8")
        architecture_doc = (self.kernel_root.parents[1] / "docs" / "architecture.md").read_text(encoding="utf-8")

        self.assertTrue(protocol_path.exists())
        protocol = protocol_path.read_text(encoding="utf-8")
        self.assertIn("L2_COMPILER_PROTOCOL.md", canonical_readme)
        self.assertIn("canonical/compiled/workspace_memory_map.json", protocol)
        self.assertIn("canonical/staging/", protocol)
        self.assertIn("Python should stay in the kernel role", protocol)
        self.assertIn("Compiled `L2` helper surfaces", consultation_protocol)
        self.assertIn("compiled `L2` helper views", communication_contract)
        self.assertIn("Derived compiled `L2` helper surfaces", architecture_doc)

    def test_l2_staging_protocol_and_public_readme_reference_final_v15_surfaces(self) -> None:
        staging_protocol_path = self.kernel_root / "canonical" / "L2_STAGING_PROTOCOL.md"
        kernel_readme = (self.kernel_root / "README.md").read_text(encoding="utf-8")
        canonical_readme = (self.kernel_root / "canonical" / "README.md").read_text(encoding="utf-8")
        consultation_protocol = (self.kernel_root / "L2_CONSULTATION_PROTOCOL.md").read_text(encoding="utf-8")
        communication_contract = (self.kernel_root / "COMMUNICATION_CONTRACT.md").read_text(encoding="utf-8")

        self.assertTrue(staging_protocol_path.exists())
        self.assertIn("workspace_memory_map.json|md", kernel_readme)
        self.assertIn("workspace_hygiene_report.json|md", kernel_readme)
        self.assertIn("workspace_staging_manifest.json|md", kernel_readme)
        self.assertIn("topic_replay_bundle.json|md", kernel_readme)
        self.assertIn("stage-l2-provisional", kernel_readme)
        self.assertIn("L2_STAGING_PROTOCOL.md", canonical_readme)
        self.assertIn("hygiene/", canonical_readme)
        self.assertIn("Rule 7. Staged entries are not canonical consultation refs", consultation_protocol)
        self.assertIn("staged provisional entries", communication_contract)

    def test_semi_formal_theory_protocol_is_present_and_documented(self) -> None:
        protocol = self.kernel_root / "SEMI_FORMAL_THEORY_PROTOCOL.md"
        readme = (self.kernel_root / "README.md").read_text(encoding="utf-8")
        runtime_readme = (self.kernel_root / "runtime" / "README.md").read_text(encoding="utf-8")
        self.assertTrue(protocol.exists())
        self.assertIn("SEMI_FORMAL_THEORY_PROTOCOL.md", readme)
        self.assertIn("SEMI_FORMAL_THEORY_PROTOCOL.md", runtime_readme)

    def test_toy_model_numeric_example_card_conforms_to_schema(self) -> None:
        payload = json.loads(
            (
                self.kernel_root
                / "canonical"
                / "backends"
                / "examples"
                / "toy-model-numeric-workspace.example.json"
            ).read_text(encoding="utf-8")
        )
        self.validator.validate(payload)
        self.assertEqual(payload["backend_type"], "mixed_local_library")
        self.assertIn("validation_pattern", payload["canonical_targets"])
        self.assertEqual(
            payload["l0_registration"]["script"],
            "source-layer/scripts/register_local_note_source.py",
        )

    def test_toy_model_numeric_starter_references_public_tool_and_smoke_script(self) -> None:
        starter = (
            self.kernel_root / "canonical" / "backends" / "TOY_MODEL_NUMERIC_BACKEND_STARTER.md"
        ).read_text(encoding="utf-8")
        smoke_script = self.kernel_root / "runtime" / "scripts" / "run_toy_model_numeric_backend_smoke.sh"
        tool_path = self.kernel_root / "validation" / "tools" / "tfim_exact_diagonalization.py"
        self.assertTrue(smoke_script.exists())
        self.assertTrue(tool_path.exists())
        self.assertIn("run_toy_model_numeric_backend_smoke.sh", starter)
        self.assertIn("tfim_exact_diagonalization.py", starter)


if __name__ == "__main__":
    unittest.main()
