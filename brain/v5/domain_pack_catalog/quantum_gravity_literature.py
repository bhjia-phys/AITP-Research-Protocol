"""Built-in quantum_gravity_literature domain pack."""

from brain.v5.domain_pack_types import DomainPackRecord


def build_domain_pack() -> DomainPackRecord:
    return DomainPackRecord(
            pack_id="quantum_gravity_literature",
            domain="quantum_gravity_literature",
            description=(
                "Quantum gravity and holography literature learning with concept dependency maps, "
                "cross-paper comparison, speculation boundaries, and checkpointed promotion."
            ),
            suggested_question_intents=[
                "literature_learning",
                "cross_paper_comparison",
                "concept_dependency_mapping",
                "source_reconstruction",
                "scope_boundary_check",
            ],
            risk_signals=["speculation_boundary", "literature_conflict", "source_gap", "claim_importance"],
            workflow_graph={
                "default_routes": [
                    {
                        "route_id": "qg_source_grounded_learning",
                        "stages": [
                            "register_source_assets",
                            "extract_core_concepts",
                            "map_dependencies",
                            "record_scope_and_open_gaps",
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
                        "route_id": "qg_cross_paper_comparison",
                        "stages": [
                            "choose_source_set",
                            "compare_assumptions",
                            "compare_conclusions",
                            "separate_conflict_from_open_direction",
                        ],
                        "required_records": [
                            "literature_comparison_draft",
                            "reference_location",
                            "sensemaking_report",
                        ],
                    },
                    {
                        "route_id": "qg_claim_support_review",
                        "stages": [
                            "source_reconstruction_review",
                            "failure_mode_review",
                            "validation_or_proof_obligation",
                            "human_checkpoint",
                        ],
                        "required_records": [
                            "source_reconstruction_review_result",
                            "failure_mode_review_result",
                            "validation_result",
                            "human_checkpoint",
                        ],
                    },
                ],
                "stage_gate": "speculative or interpretive claims require explicit source scope and a human checkpoint before promotion",
                "orientation_only": True,
            },
            failure_taxonomy=[
                {
                    "failure_id": "speculation_promoted_as_source_result",
                    "signals": ["interpretive synthesis treated as theorem", "proposal language treated as established"],
                    "review_basis": ["source text anchors", "claim scope", "human checkpoint"],
                    "required_followup_records": ["reference_location", "proof_obligation", "human_checkpoint"],
                },
                {
                    "failure_id": "framework_mismatch",
                    "signals": ["AdS argument applied to de Sitter", "large-N assumption hidden", "semiclassical limit omitted"],
                    "review_basis": ["object relation map", "assumption table", "comparison draft"],
                    "required_followup_records": ["physics_object", "object_relation", "proof_obligation"],
                },
                {
                    "failure_id": "cross_paper_dependency_gap",
                    "signals": ["paper B assumes result from paper A without source anchor", "definition lineage unclear"],
                    "review_basis": ["dependency map", "source reconstruction review", "reference locations"],
                    "required_followup_records": ["reference_location", "object_relation", "sensemaking_report"],
                },
                {
                    "failure_id": "summary_only_understanding",
                    "signals": ["no page or section anchors", "concept map has no source refs", "memory entry has no evidence path"],
                    "review_basis": ["source asset manifest", "record ref lookup", "promotion preflight"],
                    "required_followup_records": ["source_asset", "reference_location", "evidence"],
                },
            ],
            lane_policy={
                "default_lane": "literature_orientation",
                "final_evidence_requires": [
                    "source_asset and exact reference_location records for every key source",
                    "concept dependency map with object_relation records",
                    "explicit distinction between source result, interpretation, and open direction",
                    "human checkpoint before promotion for broad QG claims",
                ],
                "diagnostic_labels": ["reading_note", "source_map_draft", "speculative_synthesis", "open_direction"],
                "forbidden_promotions": [
                    "source-free synthesis",
                    "speculation boundary omitted",
                    "framework mismatch unresolved",
                    "summary-only understanding",
                ],
                "orientation_only": True,
            },
            artifact_schema={
                "required_artifact_roles": [
                    "source_asset_manifest",
                    "reference_location_table",
                    "concept_dependency_map",
                    "cross_paper_comparison_draft",
                ],
                "recommended_artifact_roles": [
                    "scope_boundary_table",
                    "speculation_boundary_note",
                    "source_reconstruction_review",
                    "open_gap_manifest",
                ],
                "hash_required_for": ["source_asset_manifest", "concept_dependency_map"],
                "orientation_only": True,
            },
            hpc_interpretation={
                "scheduler_states_are_process_evidence_only": True,
                "runtime_failure_not_algorithmic_evidence": True,
                "missing_expected_output_means": "source_or_scope_gap_still_open",
                "record_as": "tool_run_when_symbolic_or_numeric_tools_are_used",
                "trust_update_allowed": False,
                "orientation_only": True,
            },
            context_profile_refs=[
                "paper_learning",
                "paired_paper_learning",
                "multi_paper_learning_route",
                "source_reconstruction",
                "group_meeting_report",
                "closeout",
            ],
            tool_recipes=[
                "qg_source_anchor_extraction",
                "qg_concept_dependency_map",
                "qg_cross_paper_comparison",
                "qg_speculation_boundary_review",
            ],
            skill_refs=[
                {
                    "skill_id": "quantum-gravity-literature-skill",
                    "kind": "domain_literature_skill",
                    "entrypoint": "skills/quantum-gravity-literature/SKILL.md",
                    "role": "QG/holography source reading, dependency mapping, and cross-paper comparison guidance",
                    "connector_id": "quantum_gravity_literature",
                    "required_followup_records": [
                        "source_asset",
                        "reference_location",
                        "physics_object",
                        "object_relation",
                        "proof_obligation",
                        "human_checkpoint",
                    ],
                    "orientation_only": True,
                },
            ],
            manifest_refs=[
                {
                    "manifest_id": "connector.quantum_gravity_literature",
                    "path": "brain/v5/knowledge_connectors.py:quantum_gravity_literature",
                    "role": "built-in quantum-gravity connector descriptor and binding contract",
                    "orientation_only": True,
                },
            ],
            tool_executor_recommendations=[
                {
                    "executor_id": "checklist_consistency_check",
                    "recipe_id": "recipe-qg-source-scope-checklist",
                    "evidence_type": "literature_synthesis",
                    "supports_outputs": ["evidence_or_provenance", "minimal_check"],
                    "use_when": "Check QG source anchors, framework assumptions, dependency paths, and speculation boundaries.",
                    "required_context_refs": ["source_refs", "physics_object_ids", "proof_obligation_ids"],
                },
            ],
            trust_card_templates=["source_backed_qg_scope_card", "checkpointed_speculation_boundary_card"],
        )
