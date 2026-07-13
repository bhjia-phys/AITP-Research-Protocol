"""Canonical metadata registry for AITP v5 record families."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from brain.v5 import models


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

    @property
    def is_registry_family(self) -> bool:
        return self.storage_scope == "registry"


_REGISTRY_ROWS: tuple[tuple[str, str, str | None, str], ...] = (
    ("active_claim_rebind_audits", "active_claim_rebind_audit", "ActiveClaimRebindAuditRecord", "audit_id"),
    ("artifacts", "artifact", "ArtifactRecord", "artifact_id"),
    ("attempts", "attempt", None, "attempt_id"),
    ("authorities", "authority", "AuthorityRecord", "authority_id"),
    ("benchmarks", "benchmark", "BenchmarkRecord", "benchmark_id"),
    ("checkpoints", "human_checkpoint", "HumanCheckpointRecord", "checkpoint_id"),
    ("claim_statuses", "claim_status", "ClaimStatusRecord", "status_id"),
    ("claims", "claim", "ClaimRecord", "claim_id"),
    ("code_states", "code_state", "CodeStateRecord", "code_state_id"),
    ("code_workspaces", "code_workspace", "CodeWorkspaceRecord", "workspace_id"),
    ("evidence", "evidence", "EvidenceRecord", "evidence_id"),
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
    ("reference_locations", "reference_location", "ReferenceLocationRecord", "location_id"),
    ("research_run_events", "research_run_event", "ResearchRunEventRecord", "event_id"),
    ("research_runs", "research_run", "ResearchRunRecord", "run_id"),
    ("routes", "research_route", "ResearchRouteRecord", "route_id"),
    ("sensemaking_reports", "sensemaking_report", "SensemakingReportRecord", "report_id"),
    ("skill_patch_proposals", "skill_patch_proposal", "SkillPatchProposalRecord", "proposal_id"),
    ("source_assets", "source_asset", "SourceAssetRecord", "asset_id"),
    ("source_reconstruction_reviews", "source_reconstruction_review_result", "SourceReconstructionReviewResultRecord", "result_id"),
    ("tool_recipes", "tool_recipe", "ToolRecipeRecord", "recipe_id"),
    ("tool_runs", "tool_run", "ToolRunRecord", "run_id"),
    ("trust_updates", "trust_update", "TrustUpdateRecord", "update_id"),
    ("validation_contracts", "validation_contract", "ValidationContractRecord", "contract_id"),
    ("validation_results", "validation_result", "ValidationResultRecord", "result_id"),
)

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
    "authorities": "orientation_only_record",
    "quiet_checkpoints": "process_record",
    "reference_locations": "orientation_only_record",
    "research_run_events": "process_event_record",
    "research_runs": "process_record",
    "routes": "orientation_only_record",
    "sensemaking_reports": "orientation_only_record",
    "sessions": "runtime_binding",
    "source_assets": "orientation_only_record",
}
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
    "checkpoints": "v2",
}

_LIFECYCLE_FAMILIES = {"claims", "evidence"}
_APPEND_ONLY_FAMILIES = {
    "active_claim_rebind_audits",
    "claim_statuses",
    "failure_mode_reviews",
    "lifecycle_events",
    "monitor_snapshots",
    "research_run_events",
    "source_reconstruction_reviews",
    "trust_updates",
}
_BOUNDED_AUTO_WRITE_FAMILIES = {"monitor_snapshots", "research_run_events"}
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
}


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
