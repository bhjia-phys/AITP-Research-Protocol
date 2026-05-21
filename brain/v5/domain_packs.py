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
    tool_recipes: list[str] = field(default_factory=list)
    tool_executor_recommendations: list[dict] = field(default_factory=list)
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
            tool_recipes=["librpa_gw_benchmark_recipe", "code_state_capture", "abacus_librpa_input_audit"],
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
    if any(term in text for term in ("fqhe", "fractional", "sector", "counting", "topological")):
        return [packs["fqhe_topological_order"]]
    if claim.evidence_profile == "toy_numeric":
        return [packs["toy_numerics"]]
    if claim.evidence_profile == "formal_theory":
        return [packs["formal_theory"]]
    return []


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
