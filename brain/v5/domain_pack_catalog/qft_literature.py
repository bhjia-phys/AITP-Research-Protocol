"""Built-in qft_literature domain pack."""

from brain.v5.domain_pack_types import DomainPackRecord


def build_domain_pack() -> DomainPackRecord:
    return DomainPackRecord(
            pack_id="qft_literature",
            domain="qft_literature",
            description=(
                "Quantum field theory literature learning with source anchors, notation maps, "
                "renormalization conventions, derivation checks, and scoped evidence boundaries."
            ),
            suggested_question_intents=[
                "literature_learning",
                "notation_lookup",
                "derivation_check",
                "source_reconstruction",
                "literature_conflict_check",
            ],
            risk_signals=["literature_conflict", "convention_mismatch", "evidence_gap", "claim_importance"],
            workflow_graph={
                "default_routes": [
                    {
                        "route_id": "qft_source_grounded_reading",
                        "stages": [
                            "register_source_asset",
                            "record_reference_locations",
                            "extract_physics_objects",
                            "extract_object_relations",
                            "record_open_proof_obligations",
                        ],
                        "required_records": [
                            "source_asset",
                            "reference_location",
                            "physics_object",
                            "object_relation",
                            "proof_obligation",
                        ],
                    },
                    {
                        "route_id": "qft_derivation_convention_audit",
                        "stages": [
                            "name_conventions",
                            "align_notation",
                            "trace_derivation_steps",
                            "record_gap_or_scope_limit",
                        ],
                        "required_records": [
                            "physics_object",
                            "object_relation",
                            "reference_location",
                            "proof_obligation",
                        ],
                    },
                    {
                        "route_id": "qft_literature_to_evidence_review",
                        "stages": [
                            "compare_sources",
                            "separate_background_from_claim_support",
                            "create_validation_contract",
                            "preflight_trust_update",
                        ],
                        "required_records": [
                            "literature_comparison_draft",
                            "evidence",
                            "validation_contract",
                            "validation_result",
                        ],
                    },
                ],
                "stage_gate": "source-backed locations and convention maps are required before literature summaries can support a claim",
                "orientation_only": True,
            },
            failure_taxonomy=[
                {
                    "failure_id": "notation_or_normalization_collision",
                    "signals": ["field normalization differs", "metric signature differs", "operator symbol reused"],
                    "review_basis": ["notation map", "reference locations", "physics object records"],
                    "required_followup_records": ["physics_object", "object_relation", "reference_location"],
                },
                {
                    "failure_id": "renormalization_scheme_mismatch",
                    "signals": ["scheme not named", "scale dependence hidden", "regularization convention omitted"],
                    "review_basis": ["source equations", "scheme statement", "derivation trace"],
                    "required_followup_records": ["physics_object", "proof_obligation", "validation_result"],
                },
                {
                    "failure_id": "heuristic_summary_promoted_as_evidence",
                    "signals": ["paper summary has no page or equation anchor", "claim support inferred from memory"],
                    "review_basis": ["source asset", "reference location", "source reconstruction review"],
                    "required_followup_records": ["source_asset", "reference_location", "evidence"],
                },
                {
                    "failure_id": "scope_or_regime_leak",
                    "signals": ["perturbative result used nonperturbatively", "Euclidean result applied in Lorentzian setting"],
                    "review_basis": ["claim scope", "assumption list", "comparison draft"],
                    "required_followup_records": ["proof_obligation", "object_relation", "sensemaking_report"],
                },
            ],
            lane_policy={
                "default_lane": "literature_orientation",
                "final_evidence_requires": [
                    "source_asset and exact reference_location records",
                    "explicit convention and notation map",
                    "claim-scoped evidence record only after source review",
                    "validation_result or proof obligation closure for derivation-sensitive claims",
                ],
                "diagnostic_labels": [
                    "reading_note",
                    "unanchored_summary",
                    "convention_hypothesis",
                    "derivation_sketch",
                ],
                "forbidden_promotions": [
                    "retrieved chunk",
                    "summary-only memory",
                    "unreviewed derivation",
                    "unstated renormalization convention",
                ],
                "orientation_only": True,
            },
            artifact_schema={
                "required_artifact_roles": [
                    "source_asset_manifest",
                    "reference_location_table",
                    "notation_map",
                    "extracted_object_relation_candidates",
                ],
                "recommended_artifact_roles": [
                    "derivation_trace",
                    "scheme_convention_table",
                    "literature_comparison_table",
                    "source_reconstruction_review",
                ],
                "hash_required_for": ["source_asset_manifest", "derivation_trace"],
                "orientation_only": True,
            },
            hpc_interpretation={
                "scheduler_states_are_process_evidence_only": True,
                "runtime_failure_not_algorithmic_evidence": True,
                "missing_expected_output_means": "source_or_derivation_gap_still_open",
                "record_as": "tool_run_when_symbolic_or_numeric_tools_are_used",
                "trust_update_allowed": False,
                "orientation_only": True,
            },
            context_profile_refs=[
                "paper_learning",
                "paired_paper_learning",
                "derivation_check",
                "source_reconstruction",
                "closeout",
            ],
            tool_recipes=[
                "qft_source_anchor_extraction",
                "qft_notation_map",
                "qft_derivation_convention_audit",
                "qft_literature_comparison",
            ],
            skill_refs=[
                {
                    "skill_id": "qft-literature-skill",
                    "kind": "domain_literature_skill",
                    "entrypoint": "skills/qft-literature/SKILL.md",
                    "role": "QFT source reading, notation extraction, and derivation-audit guidance",
                    "connector_id": "qft_literature",
                    "required_followup_records": [
                        "source_asset",
                        "reference_location",
                        "physics_object",
                        "object_relation",
                        "proof_obligation",
                        "evidence",
                    ],
                    "orientation_only": True,
                },
            ],
            manifest_refs=[
                {
                    "manifest_id": "connector.qft_literature",
                    "path": "brain/v5/knowledge_connectors.py:qft_literature",
                    "role": "built-in QFT connector descriptor and binding contract",
                    "orientation_only": True,
                },
            ],
            tool_executor_recommendations=[
                {
                    "executor_id": "checklist_consistency_check",
                    "recipe_id": "recipe-qft-source-convention-checklist",
                    "evidence_type": "literature_synthesis",
                    "supports_outputs": ["evidence_or_provenance", "minimal_check"],
                    "use_when": "Check that QFT source anchors, notation, assumptions, and open gaps are explicit before evidence.",
                    "required_context_refs": ["source_refs", "physics_object_ids"],
                },
            ],
            trust_card_templates=["source_backed_qft_scope_card"],
        )
