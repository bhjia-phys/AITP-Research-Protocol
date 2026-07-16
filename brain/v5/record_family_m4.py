"""Focused record-family metadata owned by the M4 reviewed-Skill vertical."""

M4_REGISTRY_ROWS = (
    (
        "skill_distillation_candidates",
        "skill_distillation_candidate",
        "SkillDistillationCandidateRecord",
        "candidate_id",
    ),
    (
        "skill_readiness_reports",
        "skill_readiness_report",
        "SkillReadinessReportRecord",
        "report_id",
    ),
    (
        "skill_package_artifacts",
        "skill_package_artifact",
        "SkillPackageArtifactRecord",
        "artifact_id",
    ),
    (
        "skill_proposals",
        "skill_proposal",
        "SkillProposalRecord",
        "proposal_id",
    ),
    (
        "skill_install_plans",
        "skill_install_plan",
        "SkillInstallPlanRecord",
        "plan_id",
    ),
    (
        "skill_install_receipts",
        "skill_install_receipt",
        "SkillInstallReceiptRecord",
        "receipt_id",
    ),
)

M4_RECORD_ROLES = {
    "skill_distillation_candidates": "candidate_record",
    "skill_readiness_reports": "process_record",
    "skill_package_artifacts": "immutable_provenance_record",
    "skill_proposals": "candidate_record",
    "skill_install_plans": "review_intent_record",
    "skill_install_receipts": "authorization_receipt_record",
}
M4_SCHEMA_VERSIONS = {family: "v2" for family, *_rest in M4_REGISTRY_ROWS}
M4_CANDIDATE_ONLY_FAMILIES = frozenset({
    "skill_distillation_candidates", "skill_proposals",
})
M4_APPEND_ONLY_FAMILIES = frozenset({
    "skill_install_plans", "skill_install_receipts", "skill_package_artifacts",
    "skill_proposals", "skill_readiness_reports",
})

M4_DEPENDENCY_FIELDS = {
    "skill_distillation_candidates": (
        "recipe_refs[].record_ref",
        "execution_refs[].record_ref",
        "validation_refs[].record_ref",
        "artifact_refs[].record_ref",
        "code_state_refs[].record_ref",
        "environment_refs[].record_ref",
        "source_program_refs[].record_ref",
        "source_refs[].record_ref",
    ),
    "skill_readiness_reports": (
        "candidate_ref.record_ref",
        "expert_exception_ref.record_ref",
    ),
    "skill_package_artifacts": (
        "candidate_ref.record_ref",
        "readiness_ref.record_ref",
        "files[].blob_receipt_ref",
        "renderer_blob_ref",
        "template_refs[].record_ref",
    ),
    "skill_proposals": (
        "candidate_ref.record_ref",
        "readiness_ref.record_ref",
        "package_artifact_ref.record_ref",
        "recipe_refs[].record_ref",
        "source_program_refs[].record_ref",
        "execution_refs[].record_ref",
        "validation_refs[].record_ref",
        "artifact_refs[].record_ref",
        "code_state_refs[].record_ref",
        "environment_refs[].record_ref",
        "source_refs[].record_ref",
    ),
    "skill_install_plans": (
        "proposal_ref.record_ref",
        "package_artifact_ref.record_ref",
    ),
    "skill_install_receipts": (
        "plan_ref.record_ref",
        "proposal_ref.record_ref",
        "package_artifact_ref.record_ref",
        "checkpoint_request_ref.record_ref",
        "checkpoint_decision_ref.record_ref",
    ),
}
