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
            "l1_source_intake",
            "l1_vault",
            "interpretation_focus",
            "open_ambiguities",
            "competing_hypotheses",
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
        intake = research_payload["properties"]["l1_source_intake"]["properties"]
        self.assertIn("notation_rows", intake)
        self.assertIn("contradiction_candidates", intake)
        self.assertIn("notation_tension_candidates", intake)

    def test_candidate_schema_includes_theory_granular_types_and_auto_status(self) -> None:
        payload = self._read_json("feedback/schemas/candidate.schema.json")
        candidate_types = set(payload["properties"]["candidate_type"]["enum"])
        self.assertIn("theorem_card", candidate_types)
        self.assertIn("notation_card", candidate_types)
        self.assertIn("equivalence_map", candidate_types)
        self.assertIn("topic_skill_projection", candidate_types)
        self.assertIn("physical_picture", candidate_types)
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
        self.assertIn("physical_picture", unit_types)
        self.assertIn("negative_result", unit_types)
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
        self.assertIn("physical_picture", canonical_targets)
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
        self.assertIn("l1_source_intake", payload["required"])
        runtime_focus = payload["properties"]["runtime_focus"]["properties"]
        self.assertIn("summary", runtime_focus)
        self.assertIn("next_action_summary", runtime_focus)
        self.assertIn("dependency_status", runtime_focus)
        self.assertIn("momentum_status", runtime_focus)
        self.assertIn("stuckness_status", runtime_focus)
        self.assertIn("surprise_status", runtime_focus)
        self.assertIn("judgment_summary", runtime_focus)
        self.assertIn("l0_source_handoff", runtime_focus)
        truth_sources = payload["properties"]["truth_sources"]["properties"]
        self.assertIn("topic_state_path", truth_sources)
        self.assertIn("next_action_surface_path", truth_sources)
        self.assertIn("promotion_readiness_path", truth_sources)
        intake = payload["properties"]["l1_source_intake"]["properties"]
        self.assertIn("assumption_rows", intake)
        self.assertIn("regime_rows", intake)
        self.assertIn("reading_depth_rows", intake)
        self.assertIn("method_specificity_rows", intake)
        self.assertIn("notation_rows", intake)
        self.assertIn("contradiction_candidates", intake)
        self.assertIn("notation_tension_candidates", intake)
        self.assertIn("notation_rows", intake)
        self.assertIn("contradiction_candidates", intake)
        self.assertIn("notation_tension_candidates", intake)

    def test_consult_and_promotion_schemas_include_new_theory_surface(self) -> None:
        consult_payload = self._read_json("consultation/schemas/consult-request.schema.json")
        consult_result_payload = self._read_json("consultation/schemas/consult-result.schema.json")
        requested_unit_types = set(consult_payload["properties"]["requested_unit_types"]["items"]["enum"])
        self.assertIn("theorem_card", requested_unit_types)
        self.assertIn("equation_card", requested_unit_types)
        self.assertIn("traversal_paths", consult_result_payload["properties"])
        self.assertIn("retrieval_summary", consult_result_payload["properties"])

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
        statement_compilation_payload = self._read_json("runtime/schemas/statement-compilation-packet.schema.json")
        proof_repair_payload = self._read_json("runtime/schemas/proof-repair-plan.schema.json")
        statement_compilation_active_payload = self._read_json("runtime/schemas/statement-compilation-active.schema.json")
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
        self.assertIn("statement_compilation_path", lean_ready_payload["required"])
        self.assertIn("proof_repair_plan_path", lean_ready_payload["required"])
        self.assertEqual(lean_bridge_active_payload["properties"]["bridge_version"]["const"], 1)
        self.assertIn("needs_refinement_count", lean_bridge_active_payload["required"])
        self.assertEqual(statement_compilation_payload["properties"]["compilation_version"]["const"], 1)
        self.assertIn("assistant_targets", statement_compilation_payload["required"])
        self.assertIn("declarations", statement_compilation_payload["required"])
        self.assertEqual(proof_repair_payload["properties"]["plan_version"]["const"], 1)
        self.assertIn("proof_holes", proof_repair_payload["required"])
        self.assertEqual(statement_compilation_active_payload["properties"]["compilation_version"]["const"], 1)
        self.assertIn("needs_repair_count", statement_compilation_active_payload["required"])

    def test_package_schema_mirrors_include_runtime_proof_packets(self) -> None:
        lean_ready_payload = self._read_json("schemas/lean-ready-packet.schema.json")
        statement_compilation_payload = self._read_json("schemas/statement-compilation-packet.schema.json")
        proof_repair_payload = self._read_json("schemas/proof-repair-plan.schema.json")

        self.assertEqual(lean_ready_payload["properties"]["bridge_version"]["const"], 1)
        self.assertIn("proof_obligation_count", lean_ready_payload["required"])
        self.assertEqual(statement_compilation_payload["properties"]["compilation_version"]["const"], 1)
        self.assertIn("declarations", statement_compilation_payload["required"])
        self.assertEqual(proof_repair_payload["properties"]["plan_version"]["const"], 1)
        self.assertIn("proof_holes", proof_repair_payload["required"])

    def test_progressive_disclosure_runtime_schema_exposes_stable_trigger_contract(self) -> None:
        payload = self._read_json("runtime/schemas/progressive-disclosure-runtime-bundle.schema.json")
        self.assertEqual(payload["properties"]["bundle_kind"]["const"], "progressive_disclosure_runtime_bundle")
        self.assertEqual(payload["properties"]["protocol_version"]["const"], 1)
        self.assertIn("runtime_mode", payload["properties"])
        self.assertIn("active_submode", payload["properties"])
        self.assertIn("mode_envelope", payload["properties"])
        self.assertIn("transition_posture", payload["properties"])
        self.assertIn("human_interaction_posture", payload["properties"])
        self.assertIn("autonomy_posture", payload["properties"])
        self.assertIn("active_research_contract", payload["properties"])
        self.assertIn("promotion_readiness", payload["properties"])
        self.assertIn("validation_review_bundle", payload["properties"])
        self.assertIn("collaborator_profile", payload["properties"])
        self.assertIn("research_trajectory", payload["properties"])
        self.assertIn("mode_learning", payload["properties"])
        self.assertIn("research_judgment", payload["properties"])
        self.assertIn("research_taste", payload["properties"])
        self.assertIn("scratchpad", payload["properties"])
        self.assertIn("open_gap_summary", payload["properties"])
        self.assertIn("dependency_state", payload["properties"])
        self.assertIn("protocol_manifest", payload["properties"])
        self.assertIn("topic_completion", payload["properties"])
        self.assertIn("statement_compilation", payload["properties"])
        self.assertIn("lean_bridge", payload["properties"])
        self.assertIn("topic_skill_projection", payload["properties"])
        self.assertIn("l1_source_intake", payload["properties"]["topic_synopsis"]["properties"])
        self.assertIn("l1_source_intake", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("l1_vault", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("competing_hypotheses", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("competing_hypothesis_count", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("active_branch_hypothesis_id", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("deferred_branch_hypothesis_ids", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("followup_branch_hypothesis_ids", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("route_activation", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("route_reentry", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("route_handoff", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("route_choice", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("route_transition_gate", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("route_transition_intent", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("route_transition_receipt", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("route_transition_resolution", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("route_transition_discrepancy", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("route_transition_repair", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("route_transition_escalation", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("route_transition_clearance", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("route_transition_followthrough", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("route_transition_resumption", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("route_transition_commitment", payload["properties"]["active_research_contract"]["properties"])
        self.assertIn("route_transition_authority", payload["properties"]["active_research_contract"]["properties"])
        topic_intake = payload["$defs"]["l1_source_intake"]["properties"]
        self.assertIn("method_specificity_rows", topic_intake)
        self.assertIn("notation_rows", topic_intake)
        self.assertIn("contradiction_candidates", topic_intake)
        self.assertIn("notation_tension_candidates", topic_intake)
        self.assertIn("concept_graph", topic_intake)
        competing_hypothesis = payload["$defs"]["competing_hypothesis"]["properties"]
        self.assertIn("route_kind", competing_hypothesis)
        self.assertIn("route_target_summary", competing_hypothesis)
        self.assertIn("route_target_ref", competing_hypothesis)
        self.assertIn("evidence_ref_count", competing_hypothesis)
        self.assertIn("exclusion_notes", competing_hypothesis)
        route_activation = payload["$defs"]["route_activation"]["properties"]
        self.assertIn("active_local_action_summary", route_activation)
        self.assertIn("deferred_obligations", route_activation)
        self.assertIn("followup_obligations", route_activation)
        route_reentry = payload["$defs"]["route_reentry"]["properties"]
        self.assertIn("reentry_ready_count", route_reentry)
        self.assertIn("deferred_routes", route_reentry)
        self.assertIn("followup_routes", route_reentry)
        route_reentry_item = payload["$defs"]["route_reentry_item"]["properties"]
        self.assertIn("reentry_status", route_reentry_item)
        self.assertIn("condition_summary", route_reentry_item)
        self.assertIn("support_ref", route_reentry_item)
        route_transition_gate = payload["$defs"]["route_transition_gate"]["properties"]
        self.assertIn("transition_status", route_transition_gate)
        self.assertIn("checkpoint_status", route_transition_gate)
        self.assertIn("gate_kind", route_transition_gate)
        self.assertIn("gate_artifact_ref", route_transition_gate)
        self.assertIn("transition_target_ref", route_transition_gate)
        route_transition_intent = payload["$defs"]["route_transition_intent"]["properties"]
        self.assertIn("intent_status", route_transition_intent)
        self.assertIn("gate_status", route_transition_intent)
        self.assertIn("source_hypothesis_id", route_transition_intent)
        self.assertIn("target_hypothesis_id", route_transition_intent)
        self.assertIn("source_route_ref", route_transition_intent)
        self.assertIn("target_route_ref", route_transition_intent)
        route_transition_receipt = payload["$defs"]["route_transition_receipt"]["properties"]
        self.assertIn("receipt_status", route_transition_receipt)
        self.assertIn("intent_status", route_transition_receipt)
        self.assertIn("source_hypothesis_id", route_transition_receipt)
        self.assertIn("target_hypothesis_id", route_transition_receipt)
        self.assertIn("receipt_transition_id", route_transition_receipt)
        self.assertIn("receipt_artifact_ref", route_transition_receipt)
        route_transition_resolution = payload["$defs"]["route_transition_resolution"]["properties"]
        self.assertIn("resolution_status", route_transition_resolution)
        self.assertIn("intent_status", route_transition_resolution)
        self.assertIn("receipt_status", route_transition_resolution)
        self.assertIn("active_local_hypothesis_id", route_transition_resolution)
        self.assertIn("active_route_alignment", route_transition_resolution)
        self.assertIn("resolution_artifact_ref", route_transition_resolution)
        route_transition_discrepancy = payload["$defs"]["route_transition_discrepancy"]["properties"]
        self.assertIn("discrepancy_status", route_transition_discrepancy)
        self.assertIn("discrepancy_kind", route_transition_discrepancy)
        self.assertIn("severity", route_transition_discrepancy)
        self.assertIn("resolution_status", route_transition_discrepancy)
        self.assertIn("discrepancy_artifact_refs", route_transition_discrepancy)
        route_transition_repair = payload["$defs"]["route_transition_repair"]["properties"]
        self.assertIn("repair_status", route_transition_repair)
        self.assertIn("discrepancy_status", route_transition_repair)
        self.assertIn("discrepancy_kind", route_transition_repair)
        self.assertIn("repair_kind", route_transition_repair)
        self.assertIn("primary_repair_ref", route_transition_repair)
        self.assertIn("repair_artifact_refs", route_transition_repair)
        validation_review_bundle = payload["properties"]["validation_review_bundle"]["properties"]
        self.assertIn("analytical_cross_check_surface", validation_review_bundle)
        analytical_surface = payload["$defs"]["analytical_cross_check_surface"]["properties"]
        self.assertIn("status", analytical_surface)
        self.assertIn("candidate_id", analytical_surface)
        self.assertIn("check_rows", analytical_surface)
        analytical_row = payload["$defs"]["analytical_cross_check_row"]["properties"]
        self.assertIn("kind", analytical_row)
        self.assertIn("source_anchors", analytical_row)
        self.assertIn("assumption_refs", analytical_row)
        self.assertIn("regime_note", analytical_row)
        self.assertIn("reading_depth", analytical_row)
        self.assertIn("notes", analytical_row)
        route_transition_escalation = payload["$defs"]["route_transition_escalation"]["properties"]
        self.assertIn("escalation_status", route_transition_escalation)
        self.assertIn("repair_status", route_transition_escalation)
        self.assertIn("repair_kind", route_transition_escalation)
        self.assertIn("primary_repair_ref", route_transition_escalation)
        protocol_manifest = payload["$defs"]["protocol_manifest"]["properties"]
        self.assertIn("declared_state", protocol_manifest)
        self.assertIn("overall_status", protocol_manifest)
        self.assertIn("missing_paths", protocol_manifest)
        self.assertIn("state_catalog", protocol_manifest)
        self.assertIn("checkpoint_status", route_transition_escalation)
        self.assertIn("checkpoint_kind", route_transition_escalation)
        self.assertIn("checkpoint_ref", route_transition_escalation)
        route_transition_clearance = payload["$defs"]["route_transition_clearance"]["properties"]
        self.assertIn("clearance_status", route_transition_clearance)
        self.assertIn("clearance_kind", route_transition_clearance)
        self.assertIn("escalation_status", route_transition_clearance)
        self.assertIn("repair_status", route_transition_clearance)
        self.assertIn("checkpoint_status", route_transition_clearance)
        self.assertIn("checkpoint_kind", route_transition_clearance)
        self.assertIn("checkpoint_ref", route_transition_clearance)
        self.assertIn("followthrough_ref", route_transition_clearance)
        route_transition_followthrough = payload["$defs"]["route_transition_followthrough"]["properties"]
        self.assertIn("followthrough_status", route_transition_followthrough)
        self.assertIn("followthrough_kind", route_transition_followthrough)
        self.assertIn("clearance_status", route_transition_followthrough)
        self.assertIn("clearance_kind", route_transition_followthrough)
        self.assertIn("escalation_status", route_transition_followthrough)
        self.assertIn("repair_status", route_transition_followthrough)
        self.assertIn("checkpoint_status", route_transition_followthrough)
        self.assertIn("checkpoint_ref", route_transition_followthrough)
        self.assertIn("followthrough_ref", route_transition_followthrough)
        route_transition_resumption = payload["$defs"]["route_transition_resumption"]["properties"]
        self.assertIn("resumption_status", route_transition_resumption)
        self.assertIn("resumption_kind", route_transition_resumption)
        self.assertIn("followthrough_status", route_transition_resumption)
        self.assertIn("active_route_alignment", route_transition_resumption)
        self.assertIn("active_local_hypothesis_id", route_transition_resumption)
        self.assertIn("target_hypothesis_id", route_transition_resumption)
        self.assertIn("followthrough_ref", route_transition_resumption)
        self.assertIn("resumption_ref", route_transition_resumption)
        route_transition_commitment = payload["$defs"]["route_transition_commitment"]["properties"]
        self.assertIn("commitment_status", route_transition_commitment)
        self.assertIn("commitment_kind", route_transition_commitment)
        self.assertIn("resumption_status", route_transition_commitment)
        self.assertIn("resumption_kind", route_transition_commitment)
        self.assertIn("active_local_hypothesis_id", route_transition_commitment)
        self.assertIn("route_kind", route_transition_commitment)
        self.assertIn("route_target_ref", route_transition_commitment)
        self.assertIn("resumption_ref", route_transition_commitment)
        self.assertIn("commitment_ref", route_transition_commitment)
        route_transition_authority = payload["$defs"]["route_transition_authority"]["properties"]
        self.assertIn("authority_status", route_transition_authority)
        self.assertIn("authority_kind", route_transition_authority)
        self.assertIn("commitment_status", route_transition_authority)
        self.assertIn("commitment_kind", route_transition_authority)
        self.assertIn("active_local_hypothesis_id", route_transition_authority)
        self.assertIn("route_kind", route_transition_authority)
        self.assertIn("route_target_ref", route_transition_authority)
        self.assertIn("commitment_ref", route_transition_authority)
        self.assertIn("authority_ref", route_transition_authority)
        l1_vault = payload["$defs"]["l1_vault"]["properties"]
        self.assertIn("raw", l1_vault)
        self.assertIn("wiki", l1_vault)
        self.assertIn("output", l1_vault)
        self.assertIn("compatibility_refs", l1_vault)
        self.assertIn("runtime_focus", payload["properties"]["topic_synopsis"]["properties"])
        self.assertIn("truth_sources", payload["properties"]["topic_synopsis"]["properties"])
        runtime_focus = payload["properties"]["topic_synopsis"]["properties"]["runtime_focus"]["properties"]
        self.assertIn("momentum_status", runtime_focus)
        self.assertIn("stuckness_status", runtime_focus)
        self.assertIn("surprise_status", runtime_focus)
        self.assertIn("judgment_summary", runtime_focus)
        self.assertIn("l0_source_handoff", runtime_focus)
        decision_surface = payload["properties"]["decision_surface"]["properties"]
        self.assertIn("momentum_status", decision_surface)
        self.assertIn("stuckness_status", decision_surface)
        self.assertIn("surprise_status", decision_surface)
        self.assertIn("judgment_summary", decision_surface)
        self.assertIn("blocked_by_details", payload["properties"]["dependency_state"]["properties"])
        self.assertIn("followup_gap_writeback_count", payload["properties"]["open_gap_summary"]["properties"])
        self.assertIn("regression_manifest", payload["properties"]["topic_completion"]["properties"])
        self.assertIn("completion_gate_checks", payload["properties"]["topic_completion"]["properties"])
        statement_compilation = payload["properties"]["statement_compilation"]["properties"]
        self.assertIn("packet_count", statement_compilation)
        self.assertIn("needs_repair_count", statement_compilation)
        self.assertIn("path", statement_compilation)
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
        intake = payload["$defs"]["l1_source_intake"]["properties"]
        self.assertIn("method_specificity_rows", intake)
        self.assertIn("notation_rows", intake)
        self.assertIn("contradiction_candidates", intake)
        self.assertIn("notation_tension_candidates", intake)
        self.assertIn("concept_graph", intake)
        contradiction_candidate = payload["$defs"]["l1_contradiction_candidate"]["properties"]
        self.assertIn("comparison_basis", contradiction_candidate)
        self.assertIn("source_basis_type", contradiction_candidate)
        self.assertIn("source_basis_summary", contradiction_candidate)
        self.assertIn("source_evidence_excerpt", contradiction_candidate)
        self.assertIn("against_basis_type", contradiction_candidate)
        self.assertIn("against_basis_summary", contradiction_candidate)
        self.assertIn("against_evidence_excerpt", contradiction_candidate)
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

    def test_runtime_live_first_turn_evidence_schema_requires_posture_checks(self) -> None:
        payload = self._read_json("runtime/schemas/runtime-live-first-turn-evidence.schema.json")
        self.assertEqual(payload["properties"]["report_kind"]["const"], "runtime_live_first_turn_evidence")
        self.assertEqual(payload["properties"]["contract_version"]["const"], 1)
        self.assertIn("runtime", payload["required"])
        self.assertIn("status", payload["required"])
        self.assertIn("checks", payload["required"])
        self.assertIn("artifacts", payload["required"])
        runtimes = set(payload["properties"]["runtime"]["enum"])
        self.assertIn("claude_code", runtimes)
        self.assertIn("opencode", runtimes)
        statuses = set(payload["properties"]["status"]["enum"])
        self.assertIn("verified", statuses)
        self.assertIn("failed", statuses)
        checks = payload["properties"]["checks"]["properties"]
        self.assertIn("bootstrap_consumed_before_first_substantive_action", checks)
        self.assertIn("human_interaction_posture_visible", checks)
        self.assertIn("autonomy_posture_visible", checks)
        self.assertIn("wait_state_matches_contract", checks)
        self.assertIn("continue_state_matches_contract", checks)
        artifacts = payload["properties"]["artifacts"]["properties"]
        self.assertIn("transcript_path", artifacts)
        self.assertIn("session_start_path", artifacts)
        self.assertIn("runtime_protocol_path", artifacts)
        self.assertIn("status_payload_path", artifacts)
        self.assertIn("evidence_refs", artifacts)


if __name__ == "__main__":
    unittest.main()
