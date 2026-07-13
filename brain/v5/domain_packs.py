"""Reusable theoretical-physics domain packs for AITP v5."""

from __future__ import annotations

from brain.v5.models import ClaimRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import write_record
from brain.v5.tool_executors import describe_tool_executors

from brain.v5.domain_pack_types import DomainPackRecord


def builtin_domain_packs() -> dict[str, DomainPackRecord]:
    """Return built-in theoretical-physics domain packs."""

    from brain.v5.domain_pack_catalog.formal_theory import build_domain_pack as build_formal_theory
    from brain.v5.domain_pack_catalog.qft_literature import build_domain_pack as build_qft_literature
    from brain.v5.domain_pack_catalog.quantum_gravity_literature import build_domain_pack as build_quantum_gravity_literature
    from brain.v5.domain_pack_catalog.fqhe_topological_order import build_domain_pack as build_fqhe_topological_order
    from brain.v5.domain_pack_catalog.gw_librpa import build_domain_pack as build_gw_librpa
    from brain.v5.domain_pack_catalog.toy_numerics import build_domain_pack as build_toy_numerics

    return {
        "formal_theory": build_formal_theory(),
        "qft_literature": build_qft_literature(),
        "quantum_gravity_literature": build_quantum_gravity_literature(),
        "fqhe_topological_order": build_fqhe_topological_order(),
        "gw_librpa": build_gw_librpa(),
        "toy_numerics": build_toy_numerics(),
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
