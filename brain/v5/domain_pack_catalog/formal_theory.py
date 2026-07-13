"""Built-in formal_theory domain pack."""

from brain.v5.domain_pack_types import DomainPackRecord


def build_domain_pack() -> DomainPackRecord:
    return DomainPackRecord(
            pack_id="formal_theory",
            domain="formal_theory",
            description="Definitions, assumptions, derivation trace, counterexample, and literature consistency.",
            suggested_question_intents=[
                "claim_scope_check",
                "prerequisite_check",
                "failure_mode_check",
                "limit_symmetry_dimension_check",
                "literature_conflict_check",
            ],
            risk_signals=["evidence_gap", "physics_anomaly", "claim_importance"],
            workflow_graph={
                "default_routes": [
                    {
                        "route_id": "definition_assumption_audit",
                        "stages": ["state_claim", "extract_definitions", "name_assumptions", "check_scope"],
                        "required_records": ["physics_object", "object_relation", "proof_obligation"],
                    },
                    {
                        "route_id": "derivation_trace_review",
                        "stages": ["decompose_steps", "check_each_step", "record_gaps", "compare_sources"],
                        "required_records": ["reference_location", "proof_obligation", "sensemaking_report"],
                    },
                    {
                        "route_id": "counterexample_or_limit_search",
                        "stages": ["identify_limits", "test_special_cases", "record_failure_modes"],
                        "required_records": ["proof_obligation", "evidence", "validation_result"],
                    },
                ],
                "stage_gate": "do not call a derivation proved until assumptions, source anchors, and open proof obligations are explicit",
                "orientation_only": True,
            },
            failure_taxonomy=[
                {
                    "failure_id": "implicit_definition_shift",
                    "signals": ["symbol meaning changes", "operator domain not fixed", "normalization convention absent"],
                    "review_basis": ["physics_object_records", "reference_locations", "definition audit"],
                    "required_followup_records": ["physics_object", "object_relation", "proof_obligation"],
                },
                {
                    "failure_id": "hidden_assumption_or_scope_leak",
                    "signals": ["claim omits regularity condition", "finite case treated as general", "boundary condition omitted"],
                    "review_basis": ["assumption list", "scope statement", "counterexample notes"],
                    "required_followup_records": ["proof_obligation", "sensemaking_report"],
                },
                {
                    "failure_id": "derivation_gap",
                    "signals": ["nontrivial equality unproved", "limit exchange unchecked", "operator ordering skipped"],
                    "review_basis": ["derivation trace", "source equation anchors", "validation checklist"],
                    "required_followup_records": ["proof_obligation", "validation_result"],
                },
                {
                    "failure_id": "literature_convention_mismatch",
                    "signals": ["source uses different sign convention", "different representation or gauge", "notation collision"],
                    "review_basis": ["reference locations", "object relation map", "literature comparison draft"],
                    "required_followup_records": ["reference_location", "object_relation", "evidence"],
                },
            ],
            lane_policy={
                "default_lane": "derivation_review",
                "final_evidence_requires": [
                    "explicit definitions and assumptions",
                    "closed or scoped proof obligations",
                    "source-backed reference locations when literature-dependent",
                    "human checkpoint for theorem-like promotion",
                ],
                "diagnostic_labels": ["scratch_derivation", "heuristic_argument", "analogy", "unreviewed_summary"],
                "forbidden_promotions": [
                    "heuristic derivation",
                    "summary-only literature memory",
                    "unstated assumptions",
                    "open proof obligation without scoped boundary",
                ],
                "orientation_only": True,
            },
            artifact_schema={
                "required_artifact_roles": [
                    "definition_table",
                    "assumption_list",
                    "derivation_trace",
                    "open_gap_or_closed_obligation_manifest",
                ],
                "recommended_artifact_roles": [
                    "source_backtrace",
                    "notation_map",
                    "counterexample_search_note",
                    "literature_convention_table",
                ],
                "hash_required_for": ["derivation_trace", "source_backtrace"],
                "orientation_only": True,
            },
            hpc_interpretation={
                "scheduler_states_are_process_evidence_only": True,
                "runtime_failure_not_algorithmic_evidence": True,
                "missing_expected_output_means": "formal_gap_still_open",
                "record_as": "tool_run_when_computation_is_used",
                "trust_update_allowed": False,
                "orientation_only": True,
            },
            context_profile_refs=["derivation_check", "source_reconstruction", "paper_learning", "closeout"],
            tool_recipes=["definition_audit", "derivation_trace", "counterexample_search", "literature_consistency"],
            tool_executor_recommendations=[
                {
                    "executor_id": "checklist_consistency_check",
                    "recipe_id": "recipe-formal-theory-checklist",
                    "evidence_type": "formal_theory",
                    "supports_outputs": ["evidence_or_provenance", "minimal_check"],
                    "use_when": "Record a definition, assumption, derivation-step, or counterexample-search checklist.",
                },
            ],
            trust_card_templates=["known_theorem_scope_card"],
        )
