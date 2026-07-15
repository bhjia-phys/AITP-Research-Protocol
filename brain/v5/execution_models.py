"""Compatibility-defaulted execution records for reproducible research work."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CodeStateRecord:
    code_state_id: str
    repo_id: str
    upstream_remote: str
    upstream_branch: str
    upstream_commit: str
    local_branch: str
    worktree_path: str
    dirty: bool
    patch_id: str = ""
    diff_hash: str = ""
    build_config: dict = field(default_factory=dict)
    runtime_environment: dict = field(default_factory=dict)
    linked_records: dict = field(default_factory=dict)
    known_divergence: str = ""
    patch_manifest_ref: str = ""
    patch_manifest_hash: str = ""
    kind: str = "code_state"


@dataclass
class ToolRecipeRecord:
    recipe_id: str
    tool_family: str
    tool_name: str
    purpose: str
    required_inputs: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    validation_contract_ids: list[str] = field(default_factory=list)
    recipe_version: str = "v1-compat"
    software_constraints: dict = field(default_factory=dict)
    command_template: list[str] = field(default_factory=list)
    parameter_schema: dict = field(default_factory=dict)
    parameter_roles: dict = field(default_factory=dict)
    units: dict = field(default_factory=dict)
    defaults: dict = field(default_factory=dict)
    allowed_ranges: dict = field(default_factory=dict)
    physical_meanings: dict = field(default_factory=dict)
    input_roles: dict = field(default_factory=dict)
    output_roles: dict = field(default_factory=dict)
    script_refs: list[str] = field(default_factory=list)
    environment_requirements: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)
    stop_rules: list[str] = field(default_factory=list)
    validation_contract_refs: list[str] = field(default_factory=list)
    applicability_boundary: str = ""
    kind: str = "tool_recipe"


@dataclass
class ToolRunRecord:
    run_id: str
    recipe_id: str
    tool_family: str
    tool_name: str
    topic_id: str
    claim_id: str
    inputs: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    environment: dict = field(default_factory=dict)
    evidence_status: str = "unreviewed"
    code_state_ids: list[str] = field(default_factory=list)
    artifact_ids: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    scientific_run_id: str = ""
    supersedes_run_id: str = ""
    lane: str = "diagnostic"
    argv: list[str] = field(default_factory=list)
    cwd: str = ""
    actual_parameters: dict = field(default_factory=dict)
    parameter_provenance: dict = field(default_factory=dict)
    input_manifest: list[dict] = field(default_factory=list)
    input_hashes: dict = field(default_factory=dict)
    script_hashes: dict = field(default_factory=dict)
    recipe_ref: str = ""
    code_state_ref: str = ""
    environment_ref: str = ""
    executor_id: str = ""
    executor_version: str = ""
    executor_hash: str = ""
    scheduler: dict = field(default_factory=dict)
    job_id: str = ""
    submitted_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    exit_status: dict = field(default_factory=dict)
    output_manifest: list[dict] = field(default_factory=list)
    validation_result_ids: list[str] = field(default_factory=list)
    monitor_snapshot_ids: list[str] = field(default_factory=list)
    artifact_refs: list[str] = field(default_factory=list)
    validation_result_refs: list[str] = field(default_factory=list)
    monitor_snapshot_refs: list[str] = field(default_factory=list)
    skill_usage_refs: list[str] = field(default_factory=list)
    recorded_maturity: str = "diagnostic"
    non_claims: list[str] = field(default_factory=list)
    kind: str = "tool_run"

    @property
    def supersedes(self) -> str:
        return self.supersedes_run_id

    @property
    def superseded_by(self) -> str:
        return ""

    @property
    def maturity(self) -> str:
        return self.recorded_maturity


@dataclass
class MonitorSnapshotRecord:
    snapshot_id: str
    topic_id: str
    claim_id: str
    tool_run_id: str
    run_dir: str
    job_id: str
    scheduler_state: dict = field(default_factory=dict)
    elapsed: str = ""
    output_file_sizes: dict = field(default_factory=dict)
    latest_log_markers: list[str] = field(default_factory=list)
    memory_status: dict = field(default_factory=dict)
    failure_markers: list[str] = field(default_factory=list)
    interpretation_boundary: str = ""
    claim_trust_mutation: str = "none"
    summary_inputs_trusted: bool = False
    orientation_only: bool = True
    can_update_claim_trust: bool = False
    captured_at: str = ""
    sequence: int = 0
    collector_id: str = ""
    collector_version: str = ""
    remote_uri: str = ""
    resource_usage: dict = field(default_factory=dict)
    immutable: bool = True
    previous_snapshot_ref: str = ""
    tool_run_ref: str = ""
    tool_run_hash: str = ""
    tool_run_revision: int = 0
    kind: str = "monitor_snapshot"


@dataclass
class ArtifactRecord:
    artifact_id: str
    topic_id: str
    claim_id: str
    artifact_type: str
    uri: str
    summary: str
    size_bytes: int = 0
    metadata: dict = field(default_factory=dict)
    content_hash: str = ""
    hash_algorithm: str = ""
    captured_at: str = ""
    role: str = ""
    provenance_refs: list[str] = field(default_factory=list)
    storage_mode: str = "reference_only"
    artifact_blob_receipt_ref: str = ""
    artifact_blob_receipt_hash: str = ""
    artifact_blob_receipt_revision: int = 0
    kind: str = "artifact"


@dataclass
class ValidationContractRecord:
    contract_id: str
    topic_id: str
    claim_id: str
    required_checks: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)
    required_evidence_outputs: list[str] = field(default_factory=list)
    tool_recipe_ids: list[str] = field(default_factory=list)
    executor_ids: list[str] = field(default_factory=list)
    validator_role: str = "adversarial_reviewer"
    status: str = "open"
    tool_recipe_refs: list[str] = field(default_factory=list)
    failure_contract_hash: str = ""
    kind: str = "validation_contract"


@dataclass
class ValidationResultRecord:
    result_id: str
    topic_id: str
    claim_id: str
    contract_id: str
    tool_run_id: str
    status: str
    checked_outputs: list[str] = field(default_factory=list)
    missing_outputs: list[str] = field(default_factory=list)
    covered_failure_modes: list[str] = field(default_factory=list)
    failure_modes_observed: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    artifact_ids: list[str] = field(default_factory=list)
    summary: str = ""
    contract_ref: str = ""
    contract_hash: str = ""
    contract_revision: int = 0
    tool_run_ref: str = ""
    tool_run_hash: str = ""
    tool_run_revision: int = 0
    recipe_ref: str = ""
    recipe_hash: str = ""
    recipe_revision: int = 0
    executor_id: str = ""
    executor_version: str = ""
    executor_hash: str = ""
    output_manifest_hash: str = ""
    failure_contract_hash: str = ""
    checked_artifact_hashes: dict = field(default_factory=dict)
    kind: str = "validation_result"


@dataclass
class HumanCheckpointRecord:
    checkpoint_id: str
    topic_id: str
    claim_id: str
    reason: str
    requested_by: str
    options: list[str] = field(default_factory=list)
    status: str = "open"
    decision: str = ""
    rationale: str = ""
    decided_by: str = ""
    decision_verified: bool = False
    decision_verification: str = ""
    decision_receipt_hash: str = ""
    decision_receipt_nonce: str = ""
    can_authorize_trust: bool = False
    intent_ref: str = ""
    intent_hash: str = ""
    intent_revision: int = 0
    action: str = ""
    subject_refs: list[dict] = field(default_factory=list)
    request_hash: str = ""
    payload_hash: str = ""
    expires_at: str = ""
    replay_policy: str = ""
    target_scope_refs: list[str] = field(default_factory=list)
    effect_policy: str = ""
    kind: str = "human_checkpoint"


@dataclass
class ArtifactBlobReceiptRecord:
    receipt_id: str
    storage_kind: str
    hash_algorithm: str
    byte_sha256: str
    byte_length: int
    blob_key: str
    provider: str = ""
    object_id: str = ""
    object_version: str = ""
    retention_policy: str = ""
    access_policy: str = ""
    availability_verified: bool = True
    availability_verification_ref: str = ""
    availability_verification_hash: str = ""
    availability_verification_revision: int = 0
    can_update_claim_trust: bool = False
    kind: str = "artifact_blob_receipt"


@dataclass
class CodePatchManifestRecord:
    manifest_id: str
    repo_id: str
    base_commit: str
    status_hash: str
    entries: list[dict] = field(default_factory=list)
    excluded_required_paths: list[str] = field(default_factory=list)
    coverage_complete: bool = False
    source_refs: list[dict] = field(default_factory=list)
    created_from: str = "explicit_patch_entry_request"
    coverage_basis: str = "declared_entries_only"
    observed_status_hash: str = ""
    observed_paths: list[str] = field(default_factory=list)
    can_update_claim_trust: bool = False
    kind: str = "code_patch_manifest"


@dataclass
class CheckpointApplicationReceiptRecord:
    application_id: str
    intent_ref: str
    intent_hash: str
    intent_revision: int
    decision_ref: str
    decision_hash: str
    decision_revision: int
    action: str
    action_payload_hash: str
    subject_refs: list[dict] = field(default_factory=list)
    request_ref: str = ""
    request_hash: str = ""
    request_revision: int = 0
    result_ref: str = ""
    result_hash: str = ""
    result_revision: int = 0
    status: str = "applied"
    started_at: str = ""
    completed_at: str = ""
    recorded_at: str = ""
    errors: list[dict] = field(default_factory=list)
    can_update_claim_trust: bool = False
    kind: str = "checkpoint_application_receipt"


@dataclass
class ScopeRevalidationDecisionRecord:
    decision_id: str
    bridge_ref: str
    bridge_hash: str
    bridge_revision: int
    decision: str
    topic_id: str = ""
    claim_id: str = ""
    program_id: str = ""
    source_scope_refs: list[str] = field(default_factory=list)
    target_scope_refs: list[str] = field(default_factory=list)
    allowed_operations: list[str] = field(default_factory=list)
    source_refs: list[dict] = field(default_factory=list)
    applicability_conditions: list[str] = field(default_factory=list)
    validation_refs: list[dict] = field(default_factory=list)
    evidence_refs: list[dict] = field(default_factory=list)
    checkpoint_refs: list[dict] = field(default_factory=list)
    expires_at: str = ""
    supersedes_decision_ref: str = ""
    supersedes_decision_hash: str = ""
    supersedes_decision_revision: int = 0
    can_update_claim_trust: bool = False
    kind: str = "scope_revalidation_decision"


@dataclass
class ExecutionEnvironmentRecord:
    environment_id: str
    host: str
    operating_system: str
    architecture: str
    compiler: dict = field(default_factory=dict)
    mpi: dict = field(default_factory=dict)
    math_libraries: list[dict] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)
    package_versions: dict = field(default_factory=dict)
    container_digests: list[str] = field(default_factory=list)
    lock_digests: list[str] = field(default_factory=list)
    scheduler: dict = field(default_factory=dict)
    executable_paths: dict = field(default_factory=dict)
    executable_hashes: dict = field(default_factory=dict)
    redacted_environment: dict = field(default_factory=dict)
    source_refs: list[dict] = field(default_factory=list)
    created_at: str = ""
    kind: str = "execution_environment"


@dataclass
class ExecutionBaselineRecord:
    baseline_id: str
    topic_id: str
    claim_id: str
    run_ref: str
    frozen_dependencies: dict
    recipe_ref: str = ""
    code_state_ref: str = ""
    environment_ref: str = ""
    input_artifact_refs: list[str] = field(default_factory=list)
    output_artifact_refs: list[str] = field(default_factory=list)
    validation_refs: list[str] = field(default_factory=list)
    monitor_refs: list[str] = field(default_factory=list)
    non_claims: list[str] = field(default_factory=list)
    acceptance_checkpoint_ref: str = ""
    checkpoint_application_receipt_ref: str = ""
    status: str = "active"
    kind: str = "execution_baseline"
