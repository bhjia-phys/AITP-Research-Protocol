'Thin MCP-facing wrappers around the AITP v5 kernel.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/mcp_tools/part_01.py",
    "_compat_shards/mcp_tools/part_02.py",
    "_compat_shards/mcp_tools/part_03.py",
    "_compat_shards/mcp_tools/part_04.py",
    "_compat_shards/mcp_tools/part_05.py",
    "_compat_shards/mcp_tools/part_06.py",
    ),
)
del _load_module_shards

# Keep the compact and full surfaces on one implementation during the
# one-release compatibility window. The full catalog still loads the remaining
# maintenance and migration wrappers above.
from brain.v5.compact_mcp_tools import (
    aitp_v5_codex_autoroute,
    aitp_v5_codex_closeout,
    aitp_v5_codex_enter,
    aitp_v5_codex_expand,
    aitp_v5_codex_literature_step,
    aitp_v5_codex_record_apply,
    aitp_v5_codex_recording_step,
    aitp_v5_codex_tool_catalog,
    aitp_v5_evaluate_pre_tool_policy,
    aitp_v5_preflight_trust_update,
)
from brain.v5.mcp_session_lifecycle import (
    aitp_v5_apply_session_closeout,
    aitp_v5_coalesce_recording_batch,
    aitp_v5_plan_session_closeout,
    aitp_v5_run_recall_audit,
    aitp_v5_session_start,
    aitp_v5_stage_recording_candidate,
)
from brain.v5.mcp_monitor_snapshots import (
    aitp_v5_list_monitor_history,
    aitp_v5_record_monitor_snapshot_v2,
)
from brain.v5.mcp_harness_feedback import (
    aitp_v5_build_harness_feedback_review_view,
    aitp_v5_record_harness_feedback_case,
)
from brain.v5.mcp_research_moments import aitp_v5_process_research_moment
from brain.v5.mcp_execution import (
    aitp_v5_execution_apply_bound_action,
    aitp_v5_execution_assess_baseline_readiness,
    aitp_v5_execution_assess_scope,
    aitp_v5_execution_build_compute_intake,
    aitp_v5_execution_build_formula_code_capsule,
    aitp_v5_execution_decide_bound_checkpoint,
    aitp_v5_execution_get_record_version,
    aitp_v5_execution_project_derivation_status,
    aitp_v5_execution_project_maturity,
    aitp_v5_execution_resolve_effective_attempt,
    aitp_v5_execution_request_bound_checkpoint,
)
from brain.v5.mcp_promotion import aitp_v5_request_promotion_checkpoint
from brain.v5.mcp_knowledge import (
    aitp_v5_knowledge_build_discovery_request,
    aitp_v5_knowledge_build_source_shelf,
    aitp_v5_knowledge_compile_context,
    aitp_v5_knowledge_diagnose_candidate,
    aitp_v5_knowledge_get_source_shelf,
    aitp_v5_knowledge_normalize_discovery_result,
    aitp_v5_knowledge_promote_candidate,
    aitp_v5_knowledge_query,
    aitp_v5_knowledge_record_review,
)
from brain.v5.mcp_skills import (
    aitp_v5_skill_apply_deployment,
    aitp_v5_skill_assess_readiness,
    aitp_v5_skill_build_package_preview,
    aitp_v5_skill_build_validation_request,
    aitp_v5_skill_distill_candidate,
    aitp_v5_skill_match_applicable,
    aitp_v5_skill_plan_deployment,
    aitp_v5_skill_propose_patch,
    aitp_v5_skill_record_package_proposal,
    aitp_v5_skill_record_usage,
)


def aitp_v5_propose_detected_procedural_skill(
    base: str,
    *,
    topic_id: str,
    candidate_id: str,
    skill_name: str,
    current_version: str = "0.0.0",
    proposed_version: str = "0.1.0",
) -> dict:
    """Materialize one eligible detected workflow as a review-gated proposal."""

    from dataclasses import asdict

    from brain.v5.mcp_base_resolution import resolve_workspace_base
    from brain.v5.paths import WorkspacePaths
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.skill_distillation import propose_detected_procedural_skill

    record = propose_detected_procedural_skill(
        WorkspacePaths(resolve_workspace_base(base)),
        topic_id=topic_id,
        candidate_id=candidate_id,
        skill_name=skill_name,
        current_version=current_version,
        proposed_version=proposed_version,
    )
    return require_valid_public_surface(
        "skill_patch_proposal_record",
        {"ok": True, **asdict(record)},
    )


def aitp_v5_request_skill_install_review(
    base: str,
    *,
    proposal_id: str,
    topic_id: str,
    claim_id: str,
    requested_by: str,
) -> dict:
    """Request a hash-bound human checkpoint for project skill installation."""

    from dataclasses import asdict

    from brain.v5.mcp_base_resolution import resolve_workspace_base
    from brain.v5.paths import WorkspacePaths
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.skill_candidates import request_skill_install_review

    checkpoint = request_skill_install_review(
        WorkspacePaths(resolve_workspace_base(base)),
        proposal_id=proposal_id,
        topic_id=topic_id,
        claim_id=claim_id,
        requested_by=requested_by,
    )
    return require_valid_public_surface(
        "human_checkpoint_record",
        {"ok": True, **asdict(checkpoint)},
    )


def aitp_v5_apply_project_skill(
    base: str,
    *,
    proposal_id: str,
    checkpoint_id: str,
) -> dict:
    """Install an exact host-approved proposal into the AITP project workspace."""

    from dataclasses import asdict

    from brain.v5.mcp_base_resolution import resolve_workspace_base
    from brain.v5.paths import WorkspacePaths
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_candidates import apply_project_skill

    ws = WorkspacePaths(resolve_workspace_base(base))
    installation = apply_project_skill(
        ws,
        proposal_id=proposal_id,
        checkpoint_id=checkpoint_id,
    )
    proposal = RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="mcp_skill_read", host="aitp-v5"),
    ).read(f"skill_patch_proposal:{proposal_id}").record
    return require_valid_public_surface(
        "skill_patch_proposal_record",
        {"ok": True, **asdict(proposal), "skill_path": installation["skill_path"]},
    )
