from __future__ import annotations

import json
import unittest
from pathlib import Path


class SchemaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel_root = Path(__file__).resolve().parents[1]

    def _read_json(self, relative_path: str) -> dict:
        return json.loads((self.kernel_root / relative_path).read_text(encoding="utf-8"))

    def test_candidate_schema_includes_theory_granular_types_and_auto_status(self) -> None:
        payload = self._read_json("feedback/schemas/candidate.schema.json")
        candidate_types = set(payload["properties"]["candidate_type"]["enum"])
        self.assertIn("theorem_card", candidate_types)
        self.assertIn("notation_card", candidate_types)
        self.assertIn("equivalence_map", candidate_types)
        statuses = set(payload["properties"]["status"]["enum"])
        self.assertIn("auto_promoted", statuses)
        self.assertIn("split_into_children", statuses)
        self.assertIn("deferred_buffered", statuses)
        self.assertIn("reactivated", statuses)
        self.assertIn("split_child_ids", payload["properties"])
        self.assertIn("buffer_entry_ids", payload["properties"])

    def test_canonical_unit_schema_includes_l2_auto_routes_and_maturity(self) -> None:
        payload = self._read_json("canonical/canonical-unit.schema.json")
        unit_types = set(payload["properties"]["unit_type"]["enum"])
        self.assertIn("equation_card", unit_types)
        self.assertIn("proof_fragment", unit_types)
        maturity_states = set(payload["properties"]["maturity"]["enum"])
        self.assertIn("auto_validated", maturity_states)
        route_states = set(payload["properties"]["promotion"]["properties"]["route"]["enum"])
        self.assertIn("L3->L4_auto->L2_auto", route_states)
        self.assertIn("L2_auto->L2", route_states)

    def test_backend_schema_requires_auto_promotion_policy_fields(self) -> None:
        payload = self._read_json("schemas/l2-backend.schema.json")
        required_source_policy = set(payload["properties"]["source_policy"]["required"])
        self.assertIn("allows_auto_canonical_promotion", required_source_policy)
        self.assertIn("auto_promotion_requires_coverage_audit", required_source_policy)
        self.assertIn("auto_promotion_requires_multi_agent_consensus", required_source_policy)
        canonical_targets = set(payload["properties"]["canonical_targets"]["items"]["enum"])
        self.assertIn("theorem_card", canonical_targets)
        self.assertIn("symbol_binding", canonical_targets)

    def test_consult_and_promotion_schemas_include_new_theory_surface(self) -> None:
        consult_payload = self._read_json("consultation/schemas/consult-request.schema.json")
        requested_unit_types = set(consult_payload["properties"]["requested_unit_types"]["items"]["enum"])
        self.assertIn("theorem_card", requested_unit_types)
        self.assertIn("equation_card", requested_unit_types)

        promotion_payload = self._read_json("validation/schemas/promotion-decision.schema.json")
        routes = set(promotion_payload["properties"]["route"]["enum"])
        self.assertIn("L3->L4_auto->L2_auto", routes)
        self.assertIn("L1->L2_auto", routes)
        self.assertIn("review_mode", promotion_payload["properties"])
        self.assertIn("merge_outcome", promotion_payload["properties"])

    def test_split_and_deferred_contract_schemas_exist(self) -> None:
        split_payload = self._read_json("feedback/schemas/candidate-split-contract.schema.json")
        deferred_payload = self._read_json("runtime/schemas/deferred-candidate-buffer.schema.json")
        self.assertEqual(split_payload["properties"]["contract_version"]["const"], 1)
        self.assertIn("splits", split_payload["required"])
        self.assertEqual(deferred_payload["properties"]["buffer_version"]["const"], 1)
        self.assertIn("entries", deferred_payload["required"])

    def test_progressive_disclosure_runtime_schema_exposes_stable_trigger_contract(self) -> None:
        payload = self._read_json("runtime/schemas/progressive-disclosure-runtime-bundle.schema.json")
        self.assertEqual(payload["properties"]["bundle_kind"]["const"], "progressive_disclosure_runtime_bundle")
        self.assertEqual(payload["properties"]["protocol_version"]["const"], 1)
        trigger_names = set(payload["$defs"]["trigger_name"]["anyOf"][0]["enum"])
        self.assertIn("non_trivial_consultation", trigger_names)
        self.assertIn("promotion_intent", trigger_names)
        self.assertIn("proof_completion_review", trigger_names)
        self.assertIn("verification_route_selection", trigger_names)
        slice_names = set(payload["$defs"]["slice_name"]["anyOf"][0]["enum"])
        self.assertIn("consultation_memory", slice_names)
        self.assertIn("proof_completion_and_coverage", slice_names)
        self.assertIn("verification_route_selection", slice_names)

    def test_closed_loop_policy_candidate_statuses_match_candidate_schema(self) -> None:
        candidate_payload = self._read_json("feedback/schemas/candidate.schema.json")
        candidate_statuses = set(candidate_payload["properties"]["status"]["enum"])
        policy_payload = self._read_json("runtime/closed_loop_policies.json")
        mapped_statuses = set((policy_payload.get("result_ingest") or {}).get("candidate_status_by_decision", {}).values())
        self.assertTrue(mapped_statuses.issubset(candidate_statuses))
        self.assertTrue((policy_payload.get("auto_promotion_policy") or {}).get("enabled"))
        self.assertTrue((policy_payload.get("candidate_split_policy") or {}).get("enabled"))
        self.assertTrue((policy_payload.get("deferred_buffer_policy") or {}).get("auto_reactivate"))


if __name__ == "__main__":
    unittest.main()
