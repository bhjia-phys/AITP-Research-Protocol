"""Built-in fqhe_topological_order domain pack."""

from brain.v5.domain_pack_types import DomainPackRecord


def build_domain_pack() -> DomainPackRecord:
    return DomainPackRecord(
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
        )
