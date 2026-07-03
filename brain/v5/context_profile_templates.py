"""Read-only report and closeout templates for task-shaped context profiles."""

from __future__ import annotations

from typing import Any

from brain.v5.context_profiles import ContextCompilationProfile, builtin_context_profiles


CATALOG_VERSION = "aitp.v5.context_profile_templates.v1"

FORBIDDEN_USES = (
    "context_profile_template_as_evidence",
    "profile_report_as_evidence",
    "profile_closeout_as_evidence",
    "source_support_result",
    "validation_result",
    "write_execution",
    "final_gate_satisfaction",
    "claim_trust_update",
    "trust_apply",
)

_PROFILE_FAMILIES = {
    "librpa_run_continuation": "code_method_continuation",
    "paper_learning": "literature_learning",
    "paired_paper_learning": "literature_learning",
    "multi_paper_learning_route": "literature_learning",
    "derivation_check": "formal_theory_check",
    "source_reconstruction": "source_reconstruction",
    "group_meeting_report": "human_report",
    "closeout": "session_handoff",
}

_SECTION_PURPOSES = {
    "active_claim": "State the active claim only from typed claim/session records.",
    "active_work_package": "Name the current work package and do not infer completion.",
    "artifacts": "List durable artifact refs and whether they are diagnostic or final.",
    "blockers": "Name typed blockers and missing records before proposing next actions.",
    "code_state": "Show code provenance required before code-derived conclusions.",
    "current_focus": "Summarize the current research focus using the stable output spine.",
    "domain_packs": "Expose domain experience packs and skill refs as routing context.",
    "evidence": "List evidence refs only; do not create support from template text.",
    "hpc_status": "Separate scheduler/runtime status from scientific validation.",
    "knowledge_connectors": "Name external note/corpus connectors as orientation sources.",
    "lane_policy": "Carry final-vs-diagnostic lane boundaries into the task context.",
    "literature_comparison_draft": "Keep source-by-source comparison separate before synthesis.",
    "missing_components": "List missing source-stack or provenance components.",
    "next_actions": "Give explicit next entrypoints rather than hidden writes.",
    "next_valid_actions": "List actions that remain valid under current trust boundaries.",
    "non_promotable_content": "Name material that must not be promoted yet.",
    "object_relations": "Show typed relations and unresolved dependency edges.",
    "open_gaps": "Preserve open theoretical, source, or validation gaps.",
    "physics_objects": "List definitions and notation objects already recorded.",
    "proof_obligations": "Expose theorem, derivation, or source proof gaps.",
    "record_completeness_audit": "Check whether the handoff has required typed slots.",
    "records": "Show durable typed refs that support the report structure.",
    "reference_locations": "Use exact source anchors instead of summary prose.",
    "source_assets": "Show canonical source identity and acquisition state.",
    "source_reconstruction_audit": "Audit source-stack coverage before claim support.",
    "source_set_comparison_matrix": "Separate agreement, convention mismatch, and gaps.",
    "tool_runs": "Show run provenance, lane, and validation links.",
    "uncertainty": "Preserve active uncertainties and failure modes.",
    "validation_gap": "Name missing validation contracts/results before trust changes.",
    "validation_results": "List typed validation results and their status only.",
    "verified_content": "Report only checks already backed by typed records.",
}


def build_context_profile_template_catalog(
    *,
    profile_ids: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Return static task-profile report/closeout templates without side effects."""

    profiles = builtin_context_profiles()
    requested = [str(item).strip() for item in (profile_ids or []) if str(item).strip()]
    selected_ids = requested or list(profiles)
    known_ids = [profile_id for profile_id in selected_ids if profile_id in profiles]
    unknown_ids = [profile_id for profile_id in selected_ids if profile_id not in profiles]
    templates = [_template_payload(profiles[profile_id]) for profile_id in known_ids]

    return {
        "ok": True,
        "kind": "context_profile_template_catalog",
        "catalog_version": CATALOG_VERSION,
        "requested_profile_ids": requested,
        "unknown_profile_ids": unknown_ids,
        "profile_ids": known_ids,
        "profile_count": len(known_ids),
        "template_count": len(templates),
        "templates": templates,
        "report_template_profiles": [
            template["profile_id"]
            for template in templates
            if template["output_shape"] in {"report_template", "continuation_report_template"}
        ],
        "closeout_template_profiles": [template["profile_id"] for template in templates],
        "template_policy": _template_policy(),
        "read_surface_effect": "context_profile_template_catalog_only",
        "truth_source": "static_context_profile_catalog",
        "read_only": True,
        "requires_explicit_next_action": True,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "records_validation_result": False,
        "source_support_result": False,
        "evidence_created": False,
        "validation_created": False,
        "write_executed": False,
        "trust_update_forbidden": True,
        "claim_trust_mutation": "none",
    }


def _template_payload(profile: ContextCompilationProfile) -> dict[str, Any]:
    output_shape = _output_shape(profile.profile_id)
    section_prompts = [_section_prompt(section_id) for section_id in profile.include_sections]
    reusable_patterns = list(profile.reusable_experience)
    read_surfaces = list(profile.recommended_surfaces)
    recommended_next = _recommended_next_entrypoints(profile, read_surfaces)
    return {
        "kind": "context_profile_template",
        "template_id": f"context-profile-template-{profile.profile_id}",
        "profile_id": profile.profile_id,
        "task_type": profile.task_type,
        "template_family": _PROFILE_FAMILIES.get(profile.profile_id, profile.task_type),
        "template_role": "task_aware_context_compiler_template",
        "output_shape": output_shape,
        "purpose": profile.purpose,
        "required_sections": section_prompts,
        "section_count": len(section_prompts),
        "can_say": list(profile.can_say),
        "cannot_say_yet": list(profile.cannot_say),
        "must_verify_before_trust_or_promotion": list(profile.must_verify),
        "reusable_experience_patterns": reusable_patterns,
        "read_only_surfaces_to_expand": read_surfaces,
        "recommended_next_entrypoints": recommended_next,
        "report_template": _report_template(profile, section_prompts),
        "closeout_template": _closeout_template(profile),
        "template_policy": _template_policy(),
        "forbidden_uses": list(FORBIDDEN_USES),
        "trust_boundary": {
            "summary_inputs_trusted": False,
            "claim_trust_mutation": "none",
            "requires_typed_followup_for_claim_support": True,
            "requires_passed_validation_for_tool_derived_support": True,
            "requires_exact_source_anchors_for_literature_support": profile.profile_id in {
                "paper_learning",
                "paired_paper_learning",
                "multi_paper_learning_route",
                "source_reconstruction",
            },
        },
        "truth_source": "static_context_profile_catalog",
        "read_only": True,
        "requires_explicit_next_action": True,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "records_validation_result": False,
        "source_support_result": False,
        "evidence_created": False,
        "validation_created": False,
        "write_executed": False,
        "trust_update_forbidden": True,
        "claim_trust_mutation": "none",
    }


def _section_prompt(section_id: str) -> dict[str, Any]:
    return {
        "section_id": section_id,
        "heading": section_id.replace("_", " ").title(),
        "purpose": _SECTION_PURPOSES.get(section_id, "Compile this section from typed records or read-only surfaces."),
        "required": True,
        "source_policy": "typed_records_or_read_only_public_surfaces",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "source_support_result": False,
        "claim_trust_mutation": "none",
    }


def _report_template(profile: ContextCompilationProfile, section_prompts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "template_kind": "profile_report_template",
        "title_template": f"AITP {profile.profile_id} report",
        "section_order": [section["section_id"] for section in section_prompts],
        "section_prompts": section_prompts,
        "boundary_line": (
            "This report is orientation-only; promote nothing until typed source, evidence, "
            "validation, and trust-preflight records satisfy the relevant gates."
        ),
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "claim_trust_mutation": "none",
    }


def _closeout_template(profile: ContextCompilationProfile) -> dict[str, Any]:
    return {
        "template_kind": "profile_closeout_template",
        "title_template": f"AITP {profile.profile_id} closeout",
        "section_order": [
            "durable_records_created",
            "missing_typed_records",
            "must_verify_next",
            "safe_resume_entrypoints",
            "non_promotable_content",
        ],
        "section_prompts": [
            {
                "section_id": "durable_records_created",
                "purpose": "List typed records, source assets, artifacts, or tool runs created during the work.",
            },
            {
                "section_id": "missing_typed_records",
                "purpose": "Name the records still required before evidence, validation, memory, or trust use.",
            },
            {
                "section_id": "must_verify_next",
                "purpose": "Carry forward the profile-specific must-verify checks.",
            },
            {
                "section_id": "safe_resume_entrypoints",
                "purpose": "Provide explicit read/write/preflight entrypoints for the next agent.",
            },
            {
                "section_id": "non_promotable_content",
                "purpose": "State which summaries, diagnostics, or drafts cannot be treated as support.",
            },
        ],
        "requires_record_completeness_audit": profile.profile_id == "closeout",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "claim_trust_mutation": "none",
    }


def _template_policy() -> dict[str, Any]:
    return {
        "host_may_use_for": [
            "task_context_compilation",
            "report_drafting_scaffold",
            "closeout_scaffold",
            "safe_resume_planning",
            "skill_or_domain_pack_invocation_planning",
        ],
        "requires_runtime_context_pack_before_final_answer": True,
        "requires_explicit_next_entrypoint": True,
        "forbidden_uses": list(FORBIDDEN_USES),
        "records_validation_result": False,
        "source_support_result": False,
        "claim_trust_mutation": "none",
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _recommended_next_entrypoints(profile: ContextCompilationProfile, read_surfaces: list[str]) -> list[str]:
    next_entrypoints = [f"aitp-v5 status context-pack <session-id> --task-profile {profile.profile_id}"]
    next_entrypoints.extend(f"expand:{surface}" for surface in read_surfaces)
    return next_entrypoints


def _output_shape(profile_id: str) -> str:
    if profile_id == "closeout":
        return "closeout_template"
    if profile_id == "librpa_run_continuation":
        return "continuation_report_template"
    return "report_template"
