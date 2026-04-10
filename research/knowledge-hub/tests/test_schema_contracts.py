from __future__ import annotations

import json
import unittest
from pathlib import Path


class SchemaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel_root = Path(__file__).resolve().parents[1]
        self.repo_root = Path(__file__).resolve().parents[3]

    def _read_json(self, relative_path: str) -> dict:
        return json.loads((self.kernel_root / relative_path).read_text(encoding="utf-8"))

    def _read_repo_json(self, relative_path: str) -> dict:
        return json.loads((self.repo_root / relative_path).read_text(encoding="utf-8"))

    def test_public_contract_schemas_expose_research_guardrail_fields(self) -> None:
        research_payload = self._read_repo_json("schemas/research-question.schema.json")
        validation_payload = self._read_repo_json("schemas/validation.schema.json")

        for field in (
            "context_intake",
            "source_basis_refs",
            "interpretation_focus",
            "open_ambiguities",
            "formalism_and_notation",
            "observables",
            "target_claims",
            "deliverables",
            "acceptance_tests",
            "forbidden_proxies",
            "uncertainty_markers",
        ):
            self.assertIn(field, research_payload["properties"])

        for field in (
            "required_checks",
            "oracle_artifacts",
            "primary_review_bundle_path",
            "review_focus",
            "open_review_questions",
            "executed_evidence",
            "confidence_cap",
            "gap_followups",
            "failure_modes",
        ):
            self.assertIn(field, validation_payload["properties"])

    def test_candidate_schema_includes_theory_granular_types_and_auto_status(self) -> None:
        payload = self._read_json("feedback/schemas/candidate.schema.json")
        candidate_types = set(payload["properties"]["candidate_type"]["enum"])
        self.assertIn("theorem_card", candidate_types)
        self.assertIn("notation_card", candidate_types)
        self.assertIn("equivalence_map", candidate_types)
        self.assertIn("topic_skill_projection", candidate_types)
        statuses = set(payload["properties"]["status"]["enum"])
        self.assertIn("auto_promoted", statuses)
        self.assertIn("split_into_children", statuses)
        self.assertIn("deferred_buffered", statuses)
        self.assertIn("reactivated", statuses)
        self.assertIn("split_child_ids", payload["properties"])
        self.assertIn("buffer_entry_ids", payload["properties"])
        self.assertIn("supporting_regression_question_ids", payload["properties"])
        self.assertIn("promotion_blockers", payload["properties"])
        self.assertIn("topic_completion_status", payload["properties"])

    def test_canonical_unit_schema_includes_l2_auto_routes_and_maturity(self) -> None:
        payload = self._read_json("canonical/canonical-unit.schema.json")
        unit_types = set(payload["properties"]["unit_type"]["enum"])
        self.assertIn("equation_card", unit_types)
        self.assertIn("proof_fragment", unit_types)
        self.assertIn("topic_skill_projection", unit_types)
        maturity_states = set(payload["properties"]["maturity"]["enum"])
        self.assertIn("auto_validated", maturity_states)
        route_states = set(payload["properties"]["promotion"]["properties"]["route"]["enum"])
        self.assertIn("L3->L4_auto->L2_auto", route_states)
        self.assertIn("L2_auto->L2", route_states)
        self.assertIn("topic_completion_status", payload["properties"])
        self.assertIn("regression_gate_status", payload["properties"]["promotion"]["properties"])
        self.assertIn("supporting_regression_question_ids", payload["properties"]["promotion"]["properties"])
        self.assertIn("supporting_oracle_ids", payload["properties"]["promotion"]["properties"])
        self.assertIn("promotion_blockers", payload["properties"]["promotion"]["properties"])
        self.assertIn("blocking_reasons", payload["properties"]["promotion"]["properties"])
        self.assertIn("cited_recovery_required", payload["properties"]["promotion"]["properties"])
        self.assertIn("followup_gap_ids", payload["properties"]["promotion"]["properties"])

    def test_backend_schema_requires_auto_promotion_policy_fields(self) -> None:
        payload = self._read_json("schemas/l2-backend.schema.json")
        required_source_policy = set(payload["properties"]["source_policy"]["required"])
        self.assertIn("allows_auto_canonical_promotion", required_source_policy)
        self.assertIn("auto_promotion_requires_coverage_audit", required_source_policy)
        self.assertIn("auto_promotion_requires_multi_agent_consensus", required_source_policy)
        self.assertIn("auto_promotion_requires_regression_gate", required_source_policy)
        self.assertIn("auto_promotion_requires_split_clearance", required_source_policy)
        self.assertIn("auto_promotion_requires_gap_honesty", required_source_policy)
        canonical_targets = set(payload["properties"]["canonical_targets"]["items"]["enum"])
        self.assertIn("theorem_card", canonical_targets)
        self.assertIn("symbol_binding", canonical_targets)
        self.assertIn("topic_skill_projection", canonical_targets)

    def test_topic_skill_projection_schema_supports_formal_theory_contract(self) -> None:
        payload = self._read_json("schemas/topic-skill-projection.schema.json")
        lane_values = set(payload["properties"]["lane"]["enum"])
        self.assertIn("formal_theory", lane_values)
        self.assertIn("status_reason", payload["required"])
        self.assertIn("required_first_reads", payload["required"])
        self.assertIn("forbidden_proxies", payload["required"])
        self.assertIn("theorem certificate", payload["description"])

    def test_topic_synopsis_schema_exposes_runtime_focus_and_truth_sources(self) -> None:
        payload = self._read_json("schemas/topic-synopsis.schema.json")
        self.assertIn("runtime_focus", payload["required"])
        self.assertIn("truth_sources", payload["required"])
        runtime_focus = payload["properties"]["runtime_focus"]["properties"]
        self.assertIn("summary", runtime_focus)
        self.assertIn("next_action_summary", runtime_focus)
        self.assertIn("dependency_status", runtime_focus)
        truth_sources = payload["properties"]["truth_sources"]["properties"]
        self.assertIn("topic_state_path", truth_sources)
        self.assertIn("next_action_surface_path", truth_sources)
        self.assertIn("promotion_readiness_path", truth_sources)

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
        followup_payload = self._read_json("runtime/schemas/followup-return-packet.schema.json")
        topic_completion_payload = self._read_json("runtime/schemas/topic-completion.schema.json")
        lean_ready_payload = self._read_json("runtime/schemas/lean-ready-packet.schema.json")
        lean_bridge_active_payload = self._read_json("runtime/schemas/lean-bridge-active.schema.json")
        self.assertEqual(split_payload["properties"]["contract_version"]["const"], 1)
        self.assertIn("splits", split_payload["required"])
        self.assertEqual(deferred_payload["properties"]["buffer_version"]["const"], 1)
        self.assertIn("entries", deferred_payload["required"])
        self.assertEqual(followup_payload["properties"]["return_packet_version"]["const"], 1)
        self.assertIn("reintegration_requirements", followup_payload["required"])
        self.assertIn("resolved_gap_update", followup_payload["properties"]["return_status"]["enum"])
        self.assertIn("accepted_return_shape", followup_payload["properties"])
        self.assertIn("return_artifact_paths", followup_payload["properties"])
        self.assertEqual(topic_completion_payload["properties"]["completion_version"]["const"], 1)
        self.assertIn("regression_manifest", topic_completion_payload["required"])
        self.assertIn("completion_gate_checks", topic_completion_payload["required"])
        self.assertEqual(lean_ready_payload["properties"]["bridge_version"]["const"], 1)
        self.assertIn("proof_obligation_count", lean_ready_payload["required"])
        self.assertIn("theory_packet_refs", lean_ready_payload["required"])
        self.assertEqual(lean_bridge_active_payload["properties"]["bridge_version"]["const"], 1)
        self.assertIn("needs_refinement_count", lean_bridge_active_payload["required"])

    def test_progressive_disclosure_runtime_schema_exposes_stable_trigger_contract(self) -> None:
        payload = self._read_json("runtime/schemas/progressive-disclosure-runtime-bundle.schema.json")
        self.assertEqual(payload["properties"]["bundle_kind"]["const"], "progressive_disclosure_runtime_bundle")
        self.assertEqual(payload["properties"]["protocol_version"]["const"], 1)
        self.assertIn("runtime_mode", payload["properties"])
        self.assertIn("active_submode", payload["properties"])
        self.assertIn("mode_envelope", payload["properties"])
        self.assertIn("transition_posture", payload["properties"])
        self.assertIn("active_research_contract", payload["properties"])
        self.assertIn("promotion_readiness", payload["properties"])
        self.assertIn("validation_review_bundle", payload["properties"])
        self.assertIn("open_gap_summary", payload["properties"])
        self.assertIn("dependency_state", payload["properties"])
        self.assertIn("topic_completion", payload["properties"])
        self.assertIn("lean_bridge", payload["properties"])
        self.assertIn("topic_skill_projection", payload["properties"])
        self.assertIn("runtime_focus", payload["properties"]["topic_synopsis"]["properties"])
        self.assertIn("truth_sources", payload["properties"]["topic_synopsis"]["properties"])
        self.assertIn("blocked_by_details", payload["properties"]["dependency_state"]["properties"])
        self.assertIn("followup_gap_writeback_count", payload["properties"]["open_gap_summary"]["properties"])
        self.assertIn("regression_manifest", payload["properties"]["topic_completion"]["properties"])
        self.assertIn("completion_gate_checks", payload["properties"]["topic_completion"]["properties"])
        self.assertIn("needs_refinement_count", payload["properties"]["lean_bridge"]["properties"])
        self.assertIn("minimum_mandatory_context", payload["properties"]["mode_envelope"]["properties"])
        self.assertIn("allowed_backedges", payload["properties"]["mode_envelope"]["properties"])
        self.assertIn("transition_kind", payload["properties"]["transition_posture"]["properties"])
        trigger_names = set(payload["$defs"]["trigger_name"]["anyOf"][0]["enum"])
        self.assertIn("non_trivial_consultation", trigger_names)
        self.assertIn("promotion_intent", trigger_names)
        self.assertIn("proof_completion_review", trigger_names)
        self.assertIn("verification_route_selection", trigger_names)
        slice_names = set(payload["$defs"]["slice_name"]["anyOf"][0]["enum"])
        self.assertIn("consultation_memory", slice_names)
        self.assertIn("proof_completion_and_coverage", slice_names)
        self.assertIn("verification_route_selection", slice_names)
        retrieval_profiles = self._read_json("canonical/retrieval_profiles.json")
        l3_types = set(retrieval_profiles["profiles"]["l3_candidate_formation"]["preferred_unit_types"])
        l4_types = set(retrieval_profiles["profiles"]["l4_adjudication"]["preferred_unit_types"])
        self.assertIn("topic_skill_projection", l3_types)
        self.assertIn("topic_skill_projection", l4_types)

    def test_closed_loop_policy_candidate_statuses_match_candidate_schema(self) -> None:
        candidate_payload = self._read_json("feedback/schemas/candidate.schema.json")
        candidate_statuses = set(candidate_payload["properties"]["status"]["enum"])
        policy_payload = self._read_json("runtime/closed_loop_policies.json")
        mapped_statuses = set((policy_payload.get("result_ingest") or {}).get("candidate_status_by_decision", {}).values())
        self.assertTrue(mapped_statuses.issubset(candidate_statuses))
        self.assertTrue((policy_payload.get("auto_promotion_policy") or {}).get("enabled"))
        self.assertTrue((policy_payload.get("topic_completion_policy") or {}).get("enabled"))
        self.assertTrue((policy_payload.get("lean_bridge_policy") or {}).get("enabled"))
        self.assertTrue((policy_payload.get("candidate_split_policy") or {}).get("enabled"))
        self.assertTrue((policy_payload.get("deferred_buffer_policy") or {}).get("auto_reactivate"))


if __name__ == "__main__":
    unittest.main()
