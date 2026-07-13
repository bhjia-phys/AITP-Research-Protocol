"""Built-in toy_numerics domain pack."""

from brain.v5.domain_pack_types import DomainPackRecord


def build_domain_pack() -> DomainPackRecord:
    return DomainPackRecord(
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
        )
