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
        "pack_id": pack.pack_id,
        "domain": pack.domain,
        "description": pack.description,
        "suggested_question_intents": list(pack.suggested_question_intents),
        "risk_signals": list(pack.risk_signals),
        "tool_recipes": list(pack.tool_recipes),
        "skill_refs": list(pack.skill_refs),
        "manifest_refs": list(pack.manifest_refs),
        "integration_boundary": pack.integration_boundary,
        "truth_standard_policy": pack.truth_standard_policy,
        "orientation_only": True,
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
