"""Reusable theoretical-physics domain packs for AITP v5."""

from __future__ import annotations

from dataclasses import dataclass, field

from brain.v5.models import ClaimRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import write_record
from brain.v5.tool_executors import describe_tool_executors


@dataclass
class DomainPackRecord:
    pack_id: str
    domain: str
    description: str
    suggested_question_intents: list[str] = field(default_factory=list)
    risk_signals: list[str] = field(default_factory=list)
    workflow_graph: dict = field(default_factory=dict)
    failure_taxonomy: list[dict] = field(default_factory=list)
    lane_policy: dict = field(default_factory=dict)
    artifact_schema: dict = field(default_factory=dict)
    hpc_interpretation: dict = field(default_factory=dict)
    context_profile_refs: list[str] = field(default_factory=list)
    tool_recipes: list[str] = field(default_factory=list)
    tool_executor_recommendations: list[dict] = field(default_factory=list)
    skill_refs: list[dict] = field(default_factory=list)
    manifest_refs: list[dict] = field(default_factory=list)
    integration_boundary: str = (
        "Domain packs and external skills are orientation and execution guidance only; "
        "typed kernel records remain the authority for evidence, validation, memory, and trust."
    )
    trust_card_templates: list[str] = field(default_factory=list)
    truth_standard_policy: str = "global_only"
    kind: str = "domain_pack"


def builtin_domain_packs() -> dict[str, DomainPackRecord]:
    """Return built-in theoretical-physics domain packs."""

    return {
        "formal_theory": DomainPackRecord(
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
        ),
        "qft_literature": DomainPackRecord(
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
            context_profile_refs=["paper_learning", "derivation_check", "source_reconstruction", "closeout"],
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
        ),
        "quantum_gravity_literature": DomainPackRecord(
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
            context_profile_refs=["paper_learning", "source_reconstruction", "group_meeting_report", "closeout"],
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
        ),
        "fqhe_topological_order": DomainPackRecord(
            pack_id="fqhe_topological_order",
            domain="fqhe_topological_order",
            description="Sector, filling, counting, CFT/ED comparison, finite-size, and quasiparticle data.",
            suggested_question_intents=[
                "object_relation_check",
                "finite_size_or_cutoff_check",
                "benchmark_consistency_check",
                "literature_conflict_check",
            ],
            risk_signals=["numerical_sensitivity", "literature_conflict", "physics_anomaly"],
            tool_recipes=["ed_sector_scan", "counting_table_comparison", "negative_control"],
            tool_executor_recommendations=[
                {
                    "executor_id": "metric_table_check",
                    "recipe_id": "recipe-fqhe-counting-table",
                    "evidence_type": "toy_numeric",
                    "supports_outputs": ["evidence_or_provenance", "minimal_check"],
                    "use_when": "Compare ED/counting-table rows against expected topological-sector data.",
                },
                {
                    "executor_id": "scalar_tolerance_check",
                    "recipe_id": "recipe-fqhe-single-observable-check",
                    "evidence_type": "toy_numeric",
                    "supports_outputs": ["evidence_or_provenance"],
                    "use_when": "Check one extracted counting, gap, or overlap observable.",
                },
                {
                    "executor_id": "failure_mode_basis_check",
                    "recipe_id": "recipe-fqhe-failure-mode-review-basis",
                    "evidence_type": "toy_numeric",
                    "supports_outputs": ["failure_mode_review_basis", "minimal_check"],
                    "use_when": "Check that sector, finite-size, and convention failure modes have concrete review basis before promotion.",
                    "required_context_refs": ["validation_result_ids"],
                },
            ],
            trust_card_templates=["small_system_reproduction_card"],
        ),
        "gw_librpa": DomainPackRecord(
            pack_id="gw_librpa",
            domain="gw_librpa",
            description="Self-energy, frequency grid, basis cutoff, Coulomb singularity, commit/build/runtime, benchmark recipe.",
            suggested_question_intents=[
                "formula_code_invariant_check",
                "provenance_check",
                "benchmark_consistency_check",
                "finite_size_or_cutoff_check",
            ],
            risk_signals=["formula_to_code_risk", "reproducibility_risk", "compute_cost"],
            workflow_graph={
                "default_routes": [
                    {
                        "route_id": "abacus_librpa_molecule_gw",
                        "system_type": "molecule",
                        "stages": ["scf", "librpa_gw", "postprocess"],
                        "required_records": ["code_state", "tool_recipe", "tool_run", "artifact"],
                    },
                    {
                        "route_id": "abacus_pyatb_librpa_periodic_gw",
                        "system_type": "solid_or_2d",
                        "stages": ["scf", "pyatb", "nscf", "preprocess", "librpa_gw", "postprocess"],
                        "required_records": ["code_state", "tool_recipe", "tool_run", "artifact"],
                    },
                    {
                        "route_id": "abacus_librpa_rpa_energy",
                        "system_type": "molecule_or_solid",
                        "stages": ["scf", "librpa_rpa", "convergence_report"],
                        "required_records": ["code_state", "tool_recipe", "tool_run", "artifact"],
                    },
                ],
                "stage_gate": "each expensive stage should have an explicit preflight or validation contract before trust-relevant use",
                "orientation_only": True,
            },
            failure_taxonomy=[
                {
                    "failure_id": "basis_or_shrink_mismatch",
                    "signals": ["ABFS_ORBITAL mismatch", "use_shrink_abfs inconsistency", "basis cutoff drift"],
                    "review_basis": ["input bundle", "generated basis artifacts", "librpa.in"],
                    "required_followup_records": ["artifact", "validation_result"],
                },
                {
                    "failure_id": "formula_code_mismatch",
                    "signals": ["self-energy formula path changed", "head-wing convention changed"],
                    "review_basis": ["formula_refs", "code_state", "formula_code_invariant"],
                    "required_followup_records": ["code_state", "tool_run", "evidence"],
                },
                {
                    "failure_id": "nonfinal_or_diagnostic_data",
                    "signals": ["nonconverged", "negative gap", "noiter", "contaminated root", "assumption-only plot"],
                    "review_basis": ["lane manifest", "run report", "validation result"],
                    "required_followup_records": ["tool_run", "artifact", "validation_result"],
                },
                {
                    "failure_id": "hpc_runtime_not_science",
                    "signals": ["OOM", "TIME LIMIT", "node failure", "dependency pending", "missing final artifact"],
                    "review_basis": ["scheduler state", "stderr/stdout", "run status manifest"],
                    "required_followup_records": ["tool_run", "artifact"],
                },
            ],
            lane_policy={
                "default_lane": "diagnostic",
                "final_evidence_requires": [
                    "explicit final lane label",
                    "clean code_state",
                    "passed validation_result",
                    "artifact allowlist or final output manifest",
                ],
                "diagnostic_labels": ["smoke", "debug", "pilot", "nonconverged", "assumption_plot"],
                "forbidden_promotions": [
                    "diagnostic run",
                    "unfinished run",
                    "scheduler failure",
                    "missing final artifact",
                    "summary-only observation",
                ],
                "orientation_only": True,
            },
            artifact_schema={
                "required_artifact_roles": [
                    "input_bundle",
                    "run_report",
                    "stdout_stderr",
                    "final_or_diagnostic_output_manifest",
                ],
                "recommended_artifact_roles": [
                    "plot",
                    "benchmark_table",
                    "lane_manifest",
                    "preflight_report",
                    "archive",
                ],
                "hash_required_for": ["input_bundle", "final_or_diagnostic_output_manifest", "archive"],
                "orientation_only": True,
            },
            hpc_interpretation={
                "scheduler_states_are_process_evidence_only": True,
                "runtime_failure_not_algorithmic_evidence": True,
                "missing_expected_output_means": "not_ready",
                "record_as": "tool_run",
                "trust_update_allowed": False,
                "orientation_only": True,
            },
            context_profile_refs=[
                "librpa_run_continuation",
                "source_reconstruction",
                "group_meeting_report",
                "closeout",
            ],
            tool_recipes=["librpa_gw_benchmark_recipe", "code_state_capture", "abacus_librpa_input_audit"],
            skill_refs=[
                {
                    "skill_id": "oh-my-librpa",
                    "kind": "external_skill_bundle",
                    "repo": "https://github.com/AroundPeking/oh-my-LibRPA",
                    "entrypoint": "skills/oh-my-librpa/SKILL.md",
                    "role": "chat-first front router for ABACUS/FHI-aims + LibRPA workflows",
                    "load_when": [
                        "LibRPA GW or RPA computation is requested",
                        "ABACUS or FHI-aims source bundles, logs, or run artifacts need intake",
                        "a first-principles workflow needs route selection, preflight, execution, or debug guidance",
                    ],
                    "required_followup_records": [
                        "code_state",
                        "tool_recipe",
                        "tool_run",
                        "artifact",
                        "evidence",
                        "validation_contract",
                        "validation_result",
                    ],
                    "orientation_only": True,
                },
                {
                    "skill_id": "oh-my-librpa-abacus-librpa",
                    "kind": "external_stack_skill",
                    "repo": "https://github.com/AroundPeking/oh-my-LibRPA",
                    "entrypoint": "skills/oh-my-librpa-abacus-librpa/SKILL.md",
                    "role": "ABACUS -> LibRPA stack router",
                    "orientation_only": True,
                },
                {
                    "skill_id": "oh-my-librpa-fhi-aims-qsgw",
                    "kind": "external_stack_skill",
                    "repo": "https://github.com/AroundPeking/oh-my-LibRPA",
                    "entrypoint": "skills/oh-my-librpa-fhi-aims-qsgw/SKILL.md",
                    "role": "FHI-aims -> LibRPA QSGW/G0W0 stack router",
                    "orientation_only": True,
                },
            ],
            manifest_refs=[
                {
                    "manifest_id": "domain-manifest.abacus-librpa",
                    "repo": "https://github.com/AroundPeking/oh-my-LibRPA",
                    "path": "registry/domain-manifest.abacus-librpa.json",
                    "role": "domain operations, invariants, routing, contracts, and reproducibility metadata",
                    "orientation_only": True,
                },
                {
                    "manifest_id": "aitp-integration",
                    "repo": "https://github.com/AroundPeking/oh-my-LibRPA",
                    "path": "docs/aitp-integration.md",
                    "role": "external integration guide for AITP and oh-my-LibRPA contract boundaries",
                    "orientation_only": True,
                },
            ],
            tool_executor_recommendations=[
                {
                    "executor_id": "metric_table_check",
                    "recipe_id": "recipe-librpa-gw-benchmark-table",
                    "evidence_type": "code_method",
                    "supports_outputs": ["evidence_or_provenance", "minimal_check"],
                    "use_when": "Compare a GW benchmark table against reference values after recording code state.",
                    "required_context_refs": ["code_state_ids"],
                },
                {
                    "executor_id": "scalar_tolerance_check",
                    "recipe_id": "recipe-librpa-single-benchmark-observable",
                    "evidence_type": "code_method",
                    "supports_outputs": ["evidence_or_provenance"],
                    "use_when": "Check one GW benchmark observable such as a gap or self-energy norm.",
                    "required_context_refs": ["code_state_ids"],
                },
                {
                    "executor_id": "formula_code_invariant_check",
                    "recipe_id": "recipe-librpa-gw-formula-code-invariant",
                    "evidence_type": "code_method",
                    "supports_outputs": ["formula_code_invariant", "minimal_check"],
                    "use_when": "Check that formula references, code paths, and expected GW invariants are explicitly matched.",
                    "required_context_refs": ["code_state_ids", "formula_refs"],
                },
                {
                    "executor_id": "librpa_gw_run_metadata_check",
                    "recipe_id": "recipe-librpa-gw-run-metadata-diagnostic",
                    "evidence_type": "code_method",
                    "supports_outputs": ["librpa_gw_run_metadata", "minimal_check"],
                    "use_when": "Check frequency-grid and basis-cutoff metadata from versioned LibRPA/GW input/output artifacts.",
                    "required_context_refs": ["code_state_ids", "artifact_ids"],
                },
                {
                    "executor_id": "failure_mode_basis_check",
                    "recipe_id": "recipe-librpa-gw-failure-mode-review-basis",
                    "evidence_type": "code_method",
                    "supports_outputs": ["failure_mode_review_basis", "minimal_check"],
                    "use_when": "Check that frequency-grid, basis-cutoff, formula-code, and code-state failure modes have concrete review basis before promotion.",
                    "required_context_refs": ["code_state_ids", "validation_result_ids"],
                },
            ],
            trust_card_templates=["clean_code_state_trust_card", "trusted_benchmark_recipe_card"],
        ),
        "toy_numerics": DomainPackRecord(
            pack_id="toy_numerics",
            domain="toy_numerics",
            description="Hamiltonian definition, symmetry sector, finite-size scan, convergence, and negative control.",
            suggested_question_intents=[
                "claim_scope_check",
                "object_relation_check",
                "finite_size_or_cutoff_check",
                "limit_symmetry_dimension_check",
            ],
            risk_signals=["numerical_sensitivity", "physics_anomaly"],
            tool_recipes=["toy_hamiltonian_diagonalization", "finite_size_scan", "negative_control"],
            tool_executor_recommendations=[
                {
                    "executor_id": "metric_table_check",
                    "recipe_id": "recipe-toy-observable-table",
                    "evidence_type": "toy_numeric",
                    "supports_outputs": ["evidence_or_provenance", "minimal_check"],
                    "use_when": "Compare a table of toy-model observables across sizes or sectors.",
                },
                {
                    "executor_id": "scalar_tolerance_check",
                    "recipe_id": "recipe-toy-single-observable",
                    "evidence_type": "toy_numeric",
                    "supports_outputs": ["evidence_or_provenance"],
                    "use_when": "Check one toy-model energy, gap, norm, or symmetry observable.",
                },
            ],
            trust_card_templates=["stable_toy_numeric_recipe_card"],
        ),
    }


def suggest_domain_packs(claim: ClaimRecord) -> list[DomainPackRecord]:
    """Suggest domain packs from claim content without changing global policy."""

    packs = builtin_domain_packs()
    text = _claim_text(claim)
    if any(term in text for term in ("librpa", "gw", "self-energy", "qsgw", "abacus")):
        return [packs["gw_librpa"]]
    if any(term in text for term in ("quantum gravity", "holograph", "ads", "de sitter", "black hole", "wormhole")):
        selected = [packs["quantum_gravity_literature"]]
        if claim.evidence_profile == "formal_theory":
            selected.append(packs["formal_theory"])
        return selected
    if any(term in text for term in ("qft", "quantum field", "field theory", "renormalization", "path integral", "wilson")):
        selected = [packs["qft_literature"]]
        if claim.evidence_profile == "formal_theory":
            selected.append(packs["formal_theory"])
        return selected
    if any(term in text for term in ("fqhe", "fractional", "sector", "counting", "topological")):
        return [packs["fqhe_topological_order"]]
    if claim.evidence_profile == "toy_numeric":
        return [packs["toy_numerics"]]
    if claim.evidence_profile == "formal_theory":
        return [packs["formal_theory"]]
    return []


def domain_pack_brief_payload(pack: DomainPackRecord) -> dict:
    """Return orientation-only pack metadata for execution briefs."""

    return {
        "kind": pack.kind,
        "pack_id": pack.pack_id,
        "domain": pack.domain,
        "description": pack.description,
        "suggested_question_intents": list(pack.suggested_question_intents),
        "risk_signals": list(pack.risk_signals),
        "workflow_graph": dict(pack.workflow_graph),
        "failure_taxonomy": list(pack.failure_taxonomy),
        "lane_policy": dict(pack.lane_policy),
        "artifact_schema": dict(pack.artifact_schema),
        "hpc_interpretation": dict(pack.hpc_interpretation),
        "context_profile_refs": list(pack.context_profile_refs),
        "tool_recipes": list(pack.tool_recipes),
        "skill_refs": list(pack.skill_refs),
        "manifest_refs": list(pack.manifest_refs),
        "integration_boundary": pack.integration_boundary,
        "truth_standard_policy": pack.truth_standard_policy,
        "orientation_only": True,
    }


def describe_domain_packs(*, claim: ClaimRecord | None = None, selection_scope: str = "all") -> dict:
    """Describe or suggest domain packs as a read-only research-experience catalog."""

    all_packs = builtin_domain_packs()
    if claim is None:
        packs = list(all_packs.values())
        scope = selection_scope or "all"
        claim_context: dict = {}
    else:
        packs = suggest_domain_packs(claim)
        scope = selection_scope or "suggested_for_claim"
        claim_context = {
            "claim_id": claim.claim_id,
            "topic_id": claim.topic_id,
            "evidence_profile": claim.evidence_profile,
            "confidence_state": claim.confidence_state,
            "scope": claim.scope,
        }
    return {
        "ok": True,
        "kind": "domain_pack_catalog",
        "truth_source": "builtin_domain_pack_registry",
        "selection_scope": scope,
        "known_pack_count": len(all_packs),
        "pack_count": len(packs),
        "claim_context": claim_context,
        "packs": [domain_pack_brief_payload(pack) for pack in packs],
        "required_followup_for_use": [
            "create or locate typed source/reference records before claim support",
            "record tool_recipe, tool_run, artifact, evidence, and validation_result before trust promotion",
            "treat external skills and domain manifests as orientation unless backed by typed records",
        ],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "can_materialize_skills": False,
    }


def suggest_tool_executors_for_claim(claim: ClaimRecord) -> list[dict]:
    """Return domain-conditioned safe executor recommendations for a claim."""

    catalog = {executor["executor_id"]: executor for executor in describe_tool_executors()["executors"]}
    recommendations: list[dict] = []
    for pack in suggest_domain_packs(claim):
        for recommendation in pack.tool_executor_recommendations:
            executor = catalog.get(recommendation.get("executor_id", ""))
            if executor is None:
                continue
            if recommendation.get("evidence_type") not in {claim.evidence_profile, "mixed"}:
                continue
            recommendations.append(
                {
                    "pack_id": pack.pack_id,
                    "domain": pack.domain,
                    **recommendation,
                    "executor": executor,
                }
            )
    return recommendations


def register_domain_pack(ws: WorkspacePaths, pack: DomainPackRecord) -> DomainPackRecord:
    """Persist a domain pack into the v5 workspace."""

    write_record(
        ws.root / "tools" / "domain_packs" / f"{pack.pack_id}.md",
        pack,
        body=f"# Domain Pack: {pack.pack_id}\n\n{pack.description}\n",
    )
    return pack


def _claim_text(claim: ClaimRecord) -> str:
    return " ".join(
        [
            claim.topic_id,
            claim.statement,
            claim.evidence_profile,
            claim.active_uncertainty,
            claim.scope,
            claim.strongest_failure_mode,
        ]
    ).lower()
