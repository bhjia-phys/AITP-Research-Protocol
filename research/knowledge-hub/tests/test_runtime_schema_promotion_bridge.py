from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.runtime_schema_promotion_bridge import load_runtime_schema_context, translate_to_canonical_surface


class RuntimeSchemaPromotionBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_load_runtime_schema_context_validates_and_translates_supported_artifacts(self) -> None:
        statement_path = self.root / "statement_compilation.json"
        statement_path.write_text(
            json.dumps(
                {
                    "$schema": "https://aitp.local/schemas/statement-compilation-packet.schema.json",
                    "compilation_version": 1,
                    "topic_slug": "demo-topic",
                    "run_id": "run-001",
                    "candidate_id": "candidate:demo-candidate",
                    "candidate_type": "theorem_card",
                    "title": "Demo theorem packet",
                    "status": "ready",
                    "primary_statement_kind": "theorem",
                    "primary_identifier": "Demo.demo_theorem",
                    "assistant_targets": [{"assistant": "lean4", "kind": "proof_assistant", "status": "ready", "reason": "bounded export"}],
                    "declaration_count": 1,
                    "proof_hole_count": 0,
                    "dependency_ids": ["definition:demo"],
                    "notation_bindings": [{"symbol": "H", "meaning": "Hamiltonian"}],
                    "equation_labels": ["eq:1"],
                    "declarations": [
                        {
                            "declaration_id": "statement_compilation:demo:primary",
                            "statement_kind": "theorem",
                            "declaration_role": "primary_statement",
                            "identifier": "Demo.demo_theorem",
                            "signature": ": Prop",
                            "natural_language_statement": "Demo theorem statement.",
                            "dependency_ids": ["definition:demo"],
                            "source_anchor_ids": ["sec:intro"],
                            "temporary_proof_holes": [],
                        }
                    ],
                    "proof_repair_plan_path": "validation/topics/demo-topic/runs/run-001/statement-compilation/candidate-demo-candidate/proof_repair_plan.json",
                    "theory_packet_refs": {
                        "coverage_ledger": "coverage.json",
                        "structure_map": "structure.json",
                        "notation_table": "notation.json",
                        "derivation_graph": "derivation.json",
                        "regression_gate": "regression.json",
                    },
                    "updated_at": "2026-04-14T00:00:00+00:00",
                    "updated_by": "test-suite",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        repair_path = self.root / "proof_repair_plan.json"
        repair_path.write_text(
            json.dumps(
                {
                    "$schema": "https://aitp.local/schemas/proof-repair-plan.schema.json",
                    "plan_version": 1,
                    "topic_slug": "demo-topic",
                    "run_id": "run-001",
                    "candidate_id": "candidate:demo-candidate",
                    "status": "needs_repair",
                    "compilation_path": str(statement_path),
                    "repair_stages": [
                        {
                            "stage_id": "verifier_guided_repair",
                            "stage_name": "verifier_guided_repair",
                            "status": "pending",
                            "summary": "One bounded proof hole remains.",
                        }
                    ],
                    "proof_holes": [
                        {
                            "hole_id": "hole:demo",
                            "category": "missing_lemma",
                            "status": "open",
                            "claim": "Need a helper lemma.",
                            "source_anchor_ids": ["sec:intro"],
                            "required_artifacts": ["statement_compilation.json"],
                            "verifier_targets": ["lean4"],
                            "close_condition": "Prove the helper lemma.",
                        }
                    ],
                    "downstream_targets": [{"assistant": "lean4", "kind": "proof_assistant", "status": "pending", "reason": "close proof hole"}],
                    "updated_at": "2026-04-14T00:00:00+00:00",
                    "updated_by": "test-suite",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        lean_path = self.root / "lean_ready_packet.json"
        lean_path.write_text(
            json.dumps(
                {
                    "$schema": "https://aitp.local/schemas/lean-ready-packet.schema.json",
                    "bridge_version": 1,
                    "topic_slug": "demo-topic",
                    "run_id": "run-001",
                    "candidate_id": "candidate:demo-candidate",
                    "candidate_type": "theorem_card",
                    "status": "ready",
                    "namespace": "AITP.DemoTopic",
                    "declaration_kind": "theorem",
                    "declaration_name": "demo_theorem",
                    "statement_text": "Demo theorem statement.",
                    "dependency_ids": ["definition:demo"],
                    "equation_labels": ["eq:1"],
                    "regression_gate_status": "pass",
                    "notation_bindings": [{"symbol": "H", "meaning": "Hamiltonian"}],
                    "proof_obligations": [],
                    "proof_obligation_count": 0,
                    "proof_obligations_path": "proof_obligations.json",
                    "proof_state_path": "proof_state.json",
                    "statement_compilation_path": str(statement_path),
                    "proof_repair_plan_path": str(repair_path),
                    "theory_packet_refs": {
                        "coverage_ledger": "coverage.json",
                        "structure_map": "structure.json",
                        "notation_table": "notation.json",
                        "derivation_graph": "derivation.json",
                        "regression_gate": "regression.json",
                    },
                    "lean_skeleton_lines": ["theorem demo_theorem : Prop := by", "  sorry"],
                    "updated_at": "2026-04-14T00:00:00+00:00",
                    "updated_by": "test-suite",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        context = load_runtime_schema_context(
            artifact_paths={
                "statement-compilation-packet": statement_path,
                "proof-repair-plan": repair_path,
                "lean-ready-packet": lean_path,
            }
        )

        self.assertTrue(context["all_valid"])
        self.assertEqual(
            set(context["artifact_types"]),
            {"statement-compilation-packet", "proof-repair-plan", "lean-ready-packet"},
        )
        translated_types = {row["translated_unit"]["unit_type"] for row in context["artifacts"]}
        self.assertIn("theorem_card", translated_types)
        self.assertIn("negative_result", translated_types)
        self.assertIn("proof_fragment", translated_types)

    def test_translate_to_canonical_surface_rejects_unknown_artifact_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown runtime artifact type"):
            translate_to_canonical_surface("unknown-artifact", {"status": "ready"})


if __name__ == "__main__":
    unittest.main()
