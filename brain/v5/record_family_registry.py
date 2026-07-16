"""Canonical metadata registry for AITP v5 record families."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from brain.v5 import models
from brain.v5 import record_family_m3 as _m3, record_family_m4 as _m4


@dataclass(frozen=True)
class RecordFamilySpec:
    """Stable path, identity, lifecycle, and exposure metadata for one family."""

    family: str
    record_kind: str
    record_class: type[Any] | None
    id_field: str
    ref_kind: str
    relative_dir: str
    schema_version: str = "v1"
    trust_effect: str = "none"
    legacy_id_fields: tuple[str, ...] = ()
    exact_ref_aliases: tuple[str, ...] = ()
    lifecycle_policy: str = "append_revision"
    index_fields: tuple[str, ...] = ()
    auto_write_policy: str = "reviewed"
    participates_in: frozenset[str] = frozenset({"exact_ref", "inventory"})
    storage_scope: str = "registry"
    record_role: str = "typed_record"
    surface: str = ""
    dependency_fields: tuple[str, ...] = ()

    @property
    def is_registry_family(self) -> bool:
        return self.storage_scope == "registry"


_REGISTRY_ROWS: tuple[tuple[str, str, str | None, str], ...] = (
    ("active_claim_rebind_audits", "active_claim_rebind_audit", "ActiveClaimRebindAuditRecord", "audit_id"),
    ("artifact_blob_receipts", "artifact_blob_receipt", "ArtifactBlobReceiptRecord", "receipt_id"),
    ("artifacts", "artifact", "ArtifactRecord", "artifact_id"),
    ("attempts", "attempt", None, "attempt_id"),
    ("authorities", "authority", "AuthorityRecord", "authority_id"),
    ("benchmarks", "benchmark", "BenchmarkRecord", "benchmark_id"),
    ("checkpoint_application_receipts", "checkpoint_application_receipt", "CheckpointApplicationReceiptRecord", "application_id"),
    ("checkpoints", "human_checkpoint", "HumanCheckpointRecord", "checkpoint_id"),
    ("claim_statuses", "claim_status", "ClaimStatusRecord", "status_id"),
    ("claims", "claim", "ClaimRecord", "claim_id"),
    ("code_patch_manifests", "code_patch_manifest", "CodePatchManifestRecord", "manifest_id"),
    ("code_states", "code_state", "CodeStateRecord", "code_state_id"),
    ("code_workspaces", "code_workspace", "CodeWorkspaceRecord", "workspace_id"),
    ("cross_topic_relations", "cross_topic_relation", "CrossTopicRelationRecord", "relation_id"),
    ("derivation_chains", "derivation_chain", "DerivationChainRecord", "chain_id"),
    ("derivation_reviews", "derivation_review", "DerivationReviewRecord", "review_id"),
    ("derivation_steps", "derivation_step", "DerivationStepRecord", "step_id"),
    ("evidence", "evidence", "EvidenceRecord", "evidence_id"),
    ("execution_environments", "execution_environment", "ExecutionEnvironmentRecord", "environment_id"),
    ("execution_baselines", "execution_baseline", "ExecutionBaselineRecord", "baseline_id"),
    ("exploratory_records", "exploratory_record", "ExploratoryRecord", "record_id"),
    ("failure_mode_reviews", "failure_mode_review_result", "FailureModeReviewResultRecord", "result_id"),
    ("ideas", "idea", None, "idea_id"),
    ("intents", "research_intent", None, "intent_id"),
    ("lane_contracts", "lane_contract", "LaneContractRecord", "contract_id"),
    ("legacy_l2_seed_group_reviews", "legacy_l2_seed_group_review_result", "LegacyL2SeedGroupReviewResultRecord", "review_id"),
    ("legacy_semantic_repairs", "legacy_semantic_repair", "LegacySemanticRepairRecord", "repair_id"),
    ("legacy_semantic_reviews", "legacy_semantic_review_result", "LegacySemanticReviewResultRecord", "review_id"),
    ("legacy_source_reconstruction_repairs", "legacy_source_reconstruction_repair", None, "repair_id"),
    ("lifecycle_events", "lifecycle_event", "LifecycleEventRecord", "event_id"),
    ("monitor_snapshots", "monitor_snapshot", "MonitorSnapshotRecord", "snapshot_id"),
    ("object_relations", "object_relation", "ObjectRelationRecord", "relation_id"),
    ("outputs", "output", None, "output_id"),
    ("physics_objects", "physics_object", "PhysicsObjectRecord", "object_id"),
    ("promotion_packets", "promotion_packet", "PromotionPacketRecord", "packet_id"),
    ("proof_obligations", "proof_obligation", "ProofObligationRecord", "obligation_id"),
    ("questions", "dynamic_question", "QuestionRecord", "question_id"),
    ("quiet_checkpoints", "quiet_checkpoint_batch", "QuietCheckpointBatchRecord", "checkpoint_id"),
    ("recall_audits", "recall_audit", "RecallAuditRecord", "audit_id"),
    ("recording_candidate_batches", "recording_candidate_batch", "RecordingCandidateBatchRecord", "batch_id"),
    ("reference_locations", "reference_location", "ReferenceLocationRecord", "location_id"),
    ("research_run_events", "research_run_event", "ResearchRunEventRecord", "event_id"),
    ("research_programs", "research_program", "ResearchProgramRecord", "program_id"),
    ("research_runs", "research_run", "ResearchRunRecord", "run_id"),
    ("routes", "research_route", "ResearchRouteRecord", "route_id"),
    ("scope_revalidation_decisions", "scope_revalidation_decision", "ScopeRevalidationDecisionRecord", "decision_id"),
    ("sensemaking_reports", "sensemaking_report", "SensemakingReportRecord", "report_id"),
    ("session_closeouts", "session_closeout", "SessionCloseoutRecord", "closeout_id"),
    ("session_focus_sets", "session_focus_set", "SessionFocusSetRecord", "focus_set_id"),
    ("skill_patch_proposals", "skill_patch_proposal", "SkillPatchProposalRecord", "proposal_id"),
    ("source_assets", "source_asset", "SourceAssetRecord", "asset_id"),
    ("source_reconstruction_reviews", "source_reconstruction_review_result", "SourceReconstructionReviewResultRecord", "result_id"),
    ("tool_recipes", "tool_recipe", "ToolRecipeRecord", "recipe_id"),
    ("tool_runs", "tool_run", "ToolRunRecord", "run_id"),
    ("trust_updates", "trust_update", "TrustUpdateRecord", "update_id"),
    ("validation_contracts", "validation_contract", "ValidationContractRecord", "contract_id"),
    ("validation_results", "validation_result", "ValidationResultRecord", "result_id"),
) + _m3.M3_REGISTRY_ROWS + _m4.M4_REGISTRY_ROWS

_SPECIAL_ROWS: tuple[tuple[str, str, str, str, str, str], ...] = (
    ("contexts", "context", "ContextRecord", "context_id", "contexts/<context_id>/context.md", "context"),
    ("topics", "topic", "TopicRecord", "topic_id", "topics/<topic_id>/topic.md", "topic"),
    ("sessions", "session_binding", "SessionBinding", "session_id", "runtime/sessions", "runtime"),
    ("memory_entries", "memory_entry", "MemoryEntryRecord", "entry_id", "memory/l2/entries", "memory"),
)

_ALIASES: dict[str, tuple[str, ...]] = {
    "artifacts": ("artifact_record",),
    "authorities": ("authority_record", "sector_authority"),
    "checkpoints": ("checkpoint", "human_checkpoint_record"),
    "claims": ("claim_record",),
    "code_states": ("code-state", "code_state_record"),
    "evidence": ("evidence_record",),
    "memory_entries": ("memory", "memory-entry", "memory_entry_record"),
    "physics_objects": ("object", "physics-object", "physics_object_record"),
    "proof_obligations": ("proof-obligation", "proof_obligation_record"),
    "quiet_checkpoints": ("quiet-checkpoint", "quiet_checkpoint"),
    "reference_locations": ("reference-location", "ref_location", "reference_location_record"),
    "routes": ("route", "research-route", "research_route_record"),
    "sensemaking_reports": ("sensemaking", "sensemaking-report", "sensemaking_report_record"),
    "source_assets": ("asset", "source-asset", "source_asset_record"),
    "source_reconstruction_reviews": (
        "source-reconstruction-review",
        "source_reconstruction_review_result",
        "source-reconstruction-review-result",
        "source_reconstruction_review_result_record",
    ),
    "tool_runs": ("tool-run", "tool_run_record"),
    "topics": ("topic_record",),
    "validation_contracts": ("validation-contract", "validation_contract_record"),
    "validation_results": ("validation-result", "validation_result_record"),
}

_REF_KINDS = {
    "checkpoints": "human_checkpoint",
    "quiet_checkpoints": "quiet_checkpoint",
    "questions": "question",
    "sessions": "session",
    "source_reconstruction_reviews": "source_reconstruction_review",
}
_RECORD_ROLES = {
    "artifact_blob_receipts": "immutable_blob_receipt",
    "authorities": "orientation_only_record",
    "checkpoint_application_receipts": "authorization_receipt_record",
    "code_patch_manifests": "immutable_provenance_record",
    "cross_topic_relations": "orientation_only_record",
    "derivation_reviews": "review_record",
    "quiet_checkpoints": "process_record",
    "recall_audits": "process_record",
    "recording_candidate_batches": "process_record",
    "reference_locations": "orientation_only_record",
    "research_programs": "orientation_only_record",
    "research_run_events": "process_event_record",
    "research_runs": "process_record",
    "routes": "orientation_only_record",
    "scope_revalidation_decisions": "review_record",
    "sensemaking_reports": "orientation_only_record",
    "session_closeouts": "process_record",
    "session_focus_sets": "process_record",
    "sessions": "runtime_binding",
    "source_assets": "orientation_only_record",
}
_RECORD_ROLES.update(_m3.M3_RECORD_ROLES)
_RECORD_ROLES.update(_m4.M4_RECORD_ROLES)
_SURFACES = {
    "quiet_checkpoints": "quiet_checkpoint_batch",
    "sessions": "session_binding",
    "source_reconstruction_reviews": "source_reconstruction_review_result_record",
}
_LEGACY_ID_FIELDS = {
    "reference_locations": ("reference_location_id",),
    "validation_results": ("validation_result_id",),
}
_SCHEMA_VERSIONS = {
    "artifact_blob_receipts": "v2",
    "artifacts": "v2",
    "checkpoints": "v2",
    "checkpoint_application_receipts": "v2",
    "code_patch_manifests": "v2",
    "code_states": "v2",
    "derivation_chains": "v2",
    "derivation_reviews": "v2",
    "derivation_steps": "v2",
    "evidence": "v2",
    "execution_environments": "v2",
    "execution_baselines": "v2",
    "monitor_snapshots": "v2",
    "scope_revalidation_decisions": "v2",
    "tool_recipes": "v2",
    "tool_runs": "v2",
    "validation_contracts": "v2",
    "validation_results": "v2",
}
_SCHEMA_VERSIONS.update(_m3.M3_SCHEMA_VERSIONS)
_SCHEMA_VERSIONS.update(_m4.M4_SCHEMA_VERSIONS)

_DEPENDENCY_FIELDS = {
    "artifact_blob_receipts": (
        "availability_verification_ref",
    ),
    "artifacts": (
        "artifact_blob_receipt_ref",
        "provenance_refs",
    ),
    "checkpoint_application_receipts": (
        "intent_ref",
        "request_ref",
        "decision_ref",
        "result_ref",
        "subject_refs[].record_ref",
    ),
    "code_patch_manifests": (
        "entries[].blob_receipt_ref",
        "entries[].index_blob_receipt_ref",
        "source_refs[].record_ref",
    ),
    "code_states": (
        "patch_manifest_ref",
    ),
    "derivation_chains": (
        "check_refs[].record_ref",
        "imported_chain_bindings[].bridge_ref.record_ref",
        "imported_chain_bindings[].chain_ref.record_ref",
        "imported_chain_bindings[].revalidation_decision_ref.record_ref",
        "ordered_step_refs[].record_ref",
        "source_refs[].record_ref",
    ),
    "derivation_reviews": (
        "chain_ref.record_ref",
        "checkpoint_ref.record_ref",
        "source_anchor_refs[].record_ref",
        "step_refs[].record_ref",
        "supersedes_review_ref.record_ref",
        "tool_run_check_refs[].record_ref",
        "validation_check_refs[].record_ref",
    ),
    "derivation_steps": (
        "dependency_step_refs[].record_ref",
        "invoked_knowledge_refs[].record_ref",
        "local_check_refs[].record_ref",
        "source_anchor_refs[].record_ref",
    ),
    "evidence": ("support_basis_refs", "trace_context_refs"),
    "execution_environments": (
        "source_refs[].record_ref",
    ),
    "execution_baselines": (
        "acceptance_checkpoint_ref",
        "code_state_ref",
        "environment_ref",
        "monitor_refs[].record_ref",
        "recipe_ref",
        "run_ref",
        "validation_refs[].record_ref",
    ),
    "scope_revalidation_decisions": (
        "bridge_ref",
        "checkpoint_refs[].record_ref",
        "evidence_refs[].record_ref",
        "source_refs[].record_ref",
        "validation_refs[].record_ref",
    ),
    "tool_runs": (
        "artifact_refs",
        "code_state_ref",
        "environment_ref",
        "input_manifest[].artifact_ref",
        "monitor_snapshot_refs",
        "output_manifest[].artifact_ref",
        "recipe_ref",
        "skill_usage_refs",
        "validation_result_refs",
    ),
    "tool_recipes": (
        "script_refs",
        "validation_contract_refs",
    ),
    "validation_results": (
        "contract_ref",
        "recipe_ref",
        "tool_run_ref",
    ),
}
_DEPENDENCY_FIELDS.update(_m3.M3_DEPENDENCY_FIELDS)
_DEPENDENCY_FIELDS.update(_m4.M4_DEPENDENCY_FIELDS)

_LIFECYCLE_FAMILIES = {"claims", "evidence"}
_APPEND_ONLY_FAMILIES = {
    "active_claim_rebind_audits",
    "artifact_blob_receipts",
    "claim_statuses",
    "checkpoint_application_receipts",
    "code_patch_manifests",
    "execution_environments",
    "execution_baselines",
    "failure_mode_reviews",
    "lifecycle_events",
    "monitor_snapshots",
    "recall_audits",
    "recording_candidate_batches",
    "research_programs",
    "scope_revalidation_decisions",
    "research_run_events",
    "session_closeouts",
    "session_focus_sets",
    "source_reconstruction_reviews",
    "trust_updates",
    "cross_topic_relations",
    "derivation_reviews",
} | _m3.M3_APPEND_ONLY_FAMILIES | _m4.M4_APPEND_ONLY_FAMILIES
_BOUNDED_AUTO_WRITE_FAMILIES = {
    "monitor_snapshots",
    "recall_audits",
    "recording_candidate_batches",
    "research_run_events",
    "session_closeouts",
}
_TRUST_PATH_FAMILIES = {
    "artifacts",
    "authorities",
    "benchmarks",
    "claims",
    "code_states",
    "evidence",
    "failure_mode_reviews",
    "memory_entries",
    "promotion_packets",
    "proof_obligations",
    "source_reconstruction_reviews",
    "tool_runs",
    "validation_contracts",
    "validation_results",
}
_CANDIDATE_ONLY_FAMILIES = {
    "attempts",
    "claim_statuses",
    "exploratory_records",
    "ideas",
    "intents",
    "outputs",
    "questions",
    "sensemaking_reports",
} | _m4.M4_CANDIDATE_ONLY_FAMILIES


def record_family_specs() -> dict[str, RecordFamilySpec]:
    """Return all normal registry and documented special-path specifications."""

    specs = {
        family: _registry_spec(family, kind, class_name, id_field)
        for family, kind, class_name, id_field in _REGISTRY_ROWS
    }
    specs.update(
        {
            family: _special_spec(family, kind, class_name, id_field, relative_dir, scope)
            for family, kind, class_name, id_field, relative_dir, scope in _SPECIAL_ROWS
        }
    )
    return dict(sorted(specs.items()))


def validate_record_family_registry() -> dict[str, Any]:
    """Return a read-only integrity audit for the canonical family registry."""

    from brain.v5.record_family_contracts import validate_record_family_registry as _validate

    return _validate(record_family_specs())


def registry_family_specs() -> dict[str, RecordFamilySpec]:
    """Return only normal ``registry/<family>`` specifications."""

    return {key: spec for key, spec in record_family_specs().items() if spec.is_registry_family}


def special_record_specs() -> dict[str, RecordFamilySpec]:
    """Return context, topic, runtime-session, and memory special-path specs."""

    return {key: spec for key, spec in record_family_specs().items() if not spec.is_registry_family}


def spec_for_family(family: str) -> RecordFamilySpec:
    """Return one registered family or raise a precise error."""

    try:
        return record_family_specs()[family]
    except KeyError as exc:
        raise KeyError(f"unknown AITP record family: {family}") from exc


def _registry_spec(
    family: str,
    kind: str,
    class_name: str | None,
    id_field: str,
) -> RecordFamilySpec:
    participates = {"exact_ref", "inventory", "query_index", "context_compiler"}
    if family in _LIFECYCLE_FAMILIES:
        participates.add("lifecycle")
    ref_kind = _REF_KINDS.get(family, kind)
    return RecordFamilySpec(
        family=family,
        record_kind=kind,
        record_class=getattr(models, class_name) if class_name else None,
        id_field=id_field,
        ref_kind=ref_kind,
        relative_dir=f"registry/{family}",
        schema_version=_SCHEMA_VERSIONS.get(family, "v1"),
        trust_effect=_trust_effect(family),
        legacy_id_fields=_legacy_id_fields(family),
        exact_ref_aliases=_aliases(family, kind, ref_kind),
        lifecycle_policy="append_only" if family in _APPEND_ONLY_FAMILIES else "append_revision",
        index_fields=(id_field, "topic_id", "claim_id", "kind", "status"),
        auto_write_policy=(
            "unimplemented_layout"
            if class_name is None
            else "bounded_observation"
            if family in _BOUNDED_AUTO_WRITE_FAMILIES
            else "reviewed"
        ),
        participates_in=frozenset(participates),
        record_role=_RECORD_ROLES.get(family, "typed_record"),
        surface=_SURFACES.get(family, f"{kind}_record"),
        dependency_fields=_DEPENDENCY_FIELDS.get(family, ()),
    )


def _special_spec(
    family: str,
    kind: str,
    class_name: str,
    id_field: str,
    relative_dir: str,
    scope: str,
) -> RecordFamilySpec:
    ref_kind = _REF_KINDS.get(family, kind)
    return RecordFamilySpec(
        family=family,
        record_kind=kind,
        record_class=getattr(models, class_name),
        id_field=id_field,
        ref_kind=ref_kind,
        relative_dir=relative_dir,
        schema_version=_SCHEMA_VERSIONS.get(family, "v1"),
        trust_effect=_trust_effect(family),
        legacy_id_fields=_legacy_id_fields(family),
        exact_ref_aliases=_aliases(family, kind, ref_kind),
        lifecycle_policy=(
            "runtime_binding"
            if scope == "runtime"
            else "append_only"
            if scope == "memory"
            else "replace_idempotent"
        ),
        index_fields=(id_field, "topic_id", "context_id", "kind", "status"),
        auto_write_policy="promotion_only" if scope == "memory" else "reviewed",
        participates_in=frozenset({"exact_ref", "inventory", "query_index", "context_compiler"}),
        storage_scope=scope,
        record_role=_RECORD_ROLES.get(family, "typed_record"),
        surface=_SURFACES.get(family, f"{kind}_record"),
        dependency_fields=_DEPENDENCY_FIELDS.get(family, ()),
    )


def _aliases(family: str, kind: str, ref_kind: str) -> tuple[str, ...]:
    singular = _singular_family(family)
    generated = {
        kind,
        kind.replace("_", "-"),
        ref_kind,
        ref_kind.replace("_", "-"),
        singular,
        singular.replace("_", "-"),
    }
    generated.update(_ALIASES.get(family, ()))
    return tuple(sorted(alias for alias in generated if alias))


def _singular_family(family: str) -> str:
    if family.endswith("ies"):
        return f"{family[:-3]}y"
    if family.endswith("statuses"):
        return family[:-2]
    if family.endswith("s"):
        return family[:-1]
    return family


def _trust_effect(family: str) -> str:
    if family in _TRUST_PATH_FAMILIES:
        return "trust_path_input"
    if family in _CANDIDATE_ONLY_FAMILIES:
        return "candidate_only"
    return "none"


def _legacy_id_fields(family: str) -> tuple[str, ...]:
    return ("id", *_LEGACY_ID_FIELDS.get(family, ()))
