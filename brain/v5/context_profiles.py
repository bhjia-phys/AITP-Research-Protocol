"""Task-shaped context compilation profiles for AITP v5."""

from __future__ import annotations

from dataclasses import dataclass, field

from brain.v5.models import ClaimRecord


@dataclass(frozen=True)
class ContextCompilationProfile:
    profile_id: str
    task_type: str
    purpose: str
    include_sections: tuple[str, ...] = ()
    can_say: tuple[str, ...] = ()
    cannot_say: tuple[str, ...] = ()
    must_verify: tuple[str, ...] = ()
    reusable_experience: tuple[str, ...] = ()
    recommended_surfaces: tuple[str, ...] = ()
    truth_policy: dict = field(default_factory=dict)
    kind: str = "context_compilation_profile"


def builtin_context_profiles() -> dict[str, ContextCompilationProfile]:
    """Return context profiles used by the execution brief."""

    no_trust_policy = {
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "requires_typed_followup_for_claim_support": True,
    }
    return {
        "librpa_run_continuation": ContextCompilationProfile(
            profile_id="librpa_run_continuation",
            task_type="code_method_continuation",
            purpose="Resume a LibRPA/GW or first-principles run without confusing diagnostic process state with final evidence.",
            include_sections=(
                "active_claim",
                "domain_packs",
                "lane_policy",
                "tool_runs",
                "artifacts",
                "validation_results",
                "hpc_status",
                "next_valid_actions",
            ),
            can_say=(
                "which run, lane, code state, and artifacts are currently linked",
                "whether expected final outputs are present or still missing",
            ),
            cannot_say=(
                "that a diagnostic or unfinished run supports the claim",
                "that scheduler success proves scientific correctness",
            ),
            must_verify=(
                "code_state is recorded",
                "final lane is explicit before evidence use",
                "tool-derived evidence cites passed validation results",
            ),
            reusable_experience=("final_vs_diagnostic_lane_policy", "hpc_runtime_not_science"),
            recommended_surfaces=("execution_brief", "hpc_cockpit", "claim_trust_audit"),
            truth_policy=dict(no_trust_policy),
        ),
        "paper_learning": ContextCompilationProfile(
            profile_id="paper_learning",
            task_type="literature_learning",
            purpose="Read papers or notes as source-backed orientation before turning any statement into claim support.",
            include_sections=(
                "source_assets",
                "reference_locations",
                "knowledge_connectors",
                "curated_rag_search",
                "object_relations",
                "proof_obligations",
            ),
            can_say=(
                "which source, page, section, equation, or note location is relevant",
                "which concepts and notations need extraction",
            ),
            cannot_say=(
                "that retrieved text is evidence by itself",
                "that a paper summary resolves a claim without source-linked records",
            ),
            must_verify=(
                "source_asset exists or acquisition status is explicit",
                "reference_location points to exact source anchors",
                "evidence is created only for a specific claim",
            ),
            reusable_experience=("source_backtrace", "notation_dependency_map"),
            recommended_surfaces=("knowledge_connector_catalog", "curated_rag_search_result", "source_reconstruction_audit"),
            truth_policy=dict(no_trust_policy),
        ),
        "derivation_check": ContextCompilationProfile(
            profile_id="derivation_check",
            task_type="formal_theory_check",
            purpose="Check a derivation, definition, or theoretical claim while preserving assumptions and open proof gaps.",
            include_sections=(
                "active_claim",
                "physics_objects",
                "object_relations",
                "proof_obligations",
                "reference_locations",
                "claim_relation_map",
            ),
            can_say=("which assumptions, definitions, and relations are recorded",),
            cannot_say=("that a derivation is proved unless proof obligations and validation are closed",),
            must_verify=("definitions are explicit", "failure modes are named", "source reconstruction is complete"),
            reusable_experience=("proved_conditional_finite_evidence_open_gap_boundary",),
            recommended_surfaces=("execution_brief", "claim_relation_map", "source_reconstruction_audit"),
            truth_policy=dict(no_trust_policy),
        ),
        "source_reconstruction": ContextCompilationProfile(
            profile_id="source_reconstruction",
            task_type="source_reconstruction",
            purpose="Rebuild the typed source stack behind a claim before using or promoting it.",
            include_sections=(
                "source_assets",
                "reference_locations",
                "object_relations",
                "evidence",
                "validation_results",
                "missing_components",
            ),
            can_say=("what source stack is reconstructable from typed records",),
            cannot_say=("that legacy or summary material is semantically lossless without review",),
            must_verify=("source locations cover definitions and scope", "claim support cites evidence records"),
            reusable_experience=("source_stack_manifest",),
            recommended_surfaces=("source_reconstruction_audit", "source_reconstruction_manifest"),
            truth_policy=dict(no_trust_policy),
        ),
        "group_meeting_report": ContextCompilationProfile(
            profile_id="group_meeting_report",
            task_type="research_report",
            purpose="Compile a human-facing progress view without upgrading provisional results into final claims.",
            include_sections=(
                "current_focus",
                "verified_content",
                "uncertainty",
                "records",
                "next_actions",
                "non_promotable_content",
            ),
            can_say=("what was checked, what failed, and what remains open",),
            cannot_say=("that unvalidated plots or summaries are final results",),
            must_verify=("final output profile is active", "diagnostic outputs are labeled"),
            reusable_experience=("stable_output_spine", "final_vs_diagnostic_report_policy"),
            recommended_surfaces=("topic_status", "qsgw_cockpit", "execution_brief"),
            truth_policy=dict(no_trust_policy),
        ),
        "closeout": ContextCompilationProfile(
            profile_id="closeout",
            task_type="session_handoff",
            purpose="Close a session with enough typed pointers for the next agent to resume safely.",
            include_sections=(
                "active_claim",
                "artifacts",
                "code_state",
                "tool_runs",
                "validation_gap",
                "next_valid_actions",
                "record_completeness_audit",
            ),
            can_say=("which durable records were created or are still missing",),
            cannot_say=("that a quiet checkpoint is a complete research package by itself",),
            must_verify=("record completeness audit is inspected", "missing recommended slots are named"),
            reusable_experience=("quiet_checkpoint_boundary",),
            recommended_surfaces=("recording_navigation_state", "quiet_checkpoint_preview", "execution_brief"),
            truth_policy=dict(no_trust_policy),
        ),
    }


def suggest_context_profiles_for_claim(claim: ClaimRecord, *, domain_pack_refs: list[str] | None = None) -> list[dict]:
    """Suggest task-shaped context profiles without changing trust state."""

    profiles = builtin_context_profiles()
    text = _claim_text(claim)
    suggested: list[ContextCompilationProfile] = []
    domain_pack_refs = domain_pack_refs or []

    if "gw_librpa" in domain_pack_refs or any(term in text for term in ("librpa", "qsgw", "abacus", "self-energy")):
        suggested.append(profiles["librpa_run_continuation"])
        suggested.append(profiles["source_reconstruction"])
    if claim.evidence_profile == "literature_synthesis" or any(
        term in text for term in ("paper", "literature", "arxiv", "reading", "qft", "quantum field", "quantum gravity")
    ):
        suggested.append(profiles["paper_learning"])
    if claim.evidence_profile == "formal_theory":
        suggested.append(profiles["derivation_check"])
    suggested.append(profiles["closeout"])
    return [_profile_payload(profile) for profile in _dedupe_profiles(suggested)]


def _profile_payload(profile: ContextCompilationProfile) -> dict:
    return {
        "kind": profile.kind,
        "profile_id": profile.profile_id,
        "task_type": profile.task_type,
        "purpose": profile.purpose,
        "include_sections": list(profile.include_sections),
        "can_say": list(profile.can_say),
        "cannot_say": list(profile.cannot_say),
        "must_verify": list(profile.must_verify),
        "reusable_experience": list(profile.reusable_experience),
        "recommended_surfaces": list(profile.recommended_surfaces),
        "truth_policy": dict(profile.truth_policy),
        "orientation_only": True,
    }


def _dedupe_profiles(profiles: list[ContextCompilationProfile]) -> list[ContextCompilationProfile]:
    seen = set()
    result = []
    for profile in profiles:
        if profile.profile_id in seen:
            continue
        seen.add(profile.profile_id)
        result.append(profile)
    return result


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
