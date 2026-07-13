# AITP M2 Execution And Derivation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make numerical/software/HPC work reproducible from exact typed records and represent formal physics derivations as inspectable, source-anchored DAGs.

**Architecture:** Evolve the existing code-state, tool-recipe, tool-run, and monitor records through compatibility-defaulted v2 dataclasses, then add execution environment, accepted baseline, formula-code link, and derivation records. Collectors produce trust-neutral candidates; only explicit repository writers create canonical process records, and accepted baselines require validation plus a human checkpoint.

**Tech Stack:** Python 3.12, dataclasses, Markdown/YAML, JSON manifests, SHA-256, Git/Slurm metadata, M0 repository/index/context services, pytest.

## Global Constraints

- M1 must be green before M2 production code begins.
- Existing `ToolRecipeRecord`, `ToolRunRecord`, `CodeStateRecord`,
  `ArtifactRecord`, and `MonitorSnapshotRecord` ids and schema-v1 files remain
  readable.
- Branch names are orientation; reproducibility requires an exact commit SHA.
- A dirty code state without both a diff hash and patch artifact is explicitly non-reproducible.
- Reproducibility and approval dependencies are pinned by typed ref plus record
  content hash/revision; a later current-record revision cannot change an
  accepted baseline.
- Collectors never create evidence, validation, accepted baselines, or claim trust.
- Remote scheduler state is process evidence only; completion requires output and validation checks.
- `accepted_baseline` requires passed validations and a decided acceptance checkpoint.
- New ToolRun writes record only `diagnostic`, `reproducible_candidate`, or
  `superseded`; `accepted_baseline` exists only as an
  `ExecutionMaturityProjection.effective_maturity` derived from an active
  immutable baseline.
- Baseline checkpoints bind action, exact subject/dependency refs and hashes,
  request hash, expiry, and replay policy; generic decided checkpoints fail.
- Secrets, credentials, tokens, private keys, and configured sensitive argv/env fields are redacted before persistence.
- Derivation records store inspectable scientific artifacts, not hidden model chain-of-thought.
- `structurally_closed`, `reviewed`, and `validated` derivation states are
  distinct; structural DAG closure is not scientific approval.
- Every canonical write uses `RecordRepository` and preserves collision/revision policy.
- Foreign-topic run/artifact/validation/derivation refs require an explicit Gate
  1 bridge and target-side revalidation; no execution relation transfers trust.
- M0 compatibility loaders/shards receive only narrow imports/re-exports;
  focused M2 modules own all new behavior.

---

## File Structure

| File | Responsibility |
|---|---|
| `brain/v5/execution_models.py` | Compatibility-defaulted execution v2 dataclasses. |
| `brain/v5/pinned_record_refs.py` | Hash-qualified current/archive record resolution and frozen dependency manifests. |
| `brain/v5/checkpoint_bindings.py` | Reusable action/subject/request-hash checkpoint v2 validation. |
| `brain/v5/checkpoint_transactions.py` | Bound request/decision and recoverable idempotent action application receipts. |
| `brain/v5/artifact_blobs.py` | Content-addressed local bytes and immutable external-storage receipts. |
| `brain/v5/code_patch_manifests.py` | Per-path dirty state, byte/blob hashes, exclusions, and coverage. |
| `brain/v5/effective_attempts.py` | Attempt/supersession, monitor, output, and lane-state projection shared by baseline/cockpit. |
| `brain/v5/execution_scope_policy.py` | Per-family topic/program/claim reuse and revalidation matrix. |
| `brain/v5/scope_revalidation.py` | Hash-bound target-scope decision/result for M1 bridges. |
| `brain/v5/bound_execution.py` | Registered-executor high-risk request and ToolRun/Validation receipt. |
| `brain/v5/execution_contracts.py` | Recipe/run/environment/baseline maturity and redaction contracts. |
| `brain/v5/execution_policy.py` | Baseline/checkpoint/validation admissibility and pre-tool policy extension. |
| `brain/v5/execution_environments.py` | Environment and executable identity writers. |
| `brain/v5/execution_baselines.py` | Accepted-baseline preflight and writer. |
| `brain/v5/compute_run_intake.py` | Local/remote collector candidate normalization. |
| `brain/v5/compute_run_intake_contracts.py` | Intake coverage and no-write boundary. |
| `brain/v5/monitor_snapshots.py` | Immutable ordered monitor snapshots. |
| `brain/v5/formula_code_map.py` | Structured formula-to-code relation API. |
| `brain/v5/formula_code_contracts.py` | Formula/code ref, scope, and stale-code validation. |
| `brain/v5/derivation_models.py` | Derivation chain and step dataclasses. |
| `brain/v5/derivations.py` | DAG validation and canonical writers. |
| `brain/v5/derivation_contracts.py` | Assumption/source/dependency/gap contracts. |
| `brain/v5/derivation_migration.py` | Reviewable import of legacy derivation DAGs. |
| `brain/v5/derivation_reviews.py` | Hash-bound review writer, supersession, and effective status projection. |

## Test Protocol

Every task first runs its named new tests to the expected missing-contract RED,
then reruns them GREEN with a unique writable external `--basetemp`, followed by
the listed M0/M1 regressions. Record the exact command, expected/actual failure
reason, pass counts, and temp root in the task report; collection-only success
does not count. Example:

```powershell
python -m pytest tests\test_v5_execution_memory.py -q -p no:cacheprovider --basetemp "$env:LOCALAPPDATA\Temp\aitp-g2-execution-<unique>"
```

## Task 1: Execution V2 Models And Compatibility

**Files:**
- Create: `brain/v5/execution_models.py`
- Create: `brain/v5/pinned_record_refs.py`
- Create: `brain/v5/checkpoint_bindings.py`
- Create: `brain/v5/checkpoint_transactions.py`
- Create: `brain/v5/artifact_blobs.py`
- Create: `brain/v5/code_patch_manifests.py`
- Create: `brain/v5/effective_attempts.py`
- Create: `brain/v5/execution_scope_policy.py`
- Create: `brain/v5/scope_revalidation.py`
- Create: `brain/v5/bound_execution.py`
- Create: `tests/test_v5_execution_models.py`
- Create: `tests/test_v5_pinned_record_refs.py`
- Create: `tests/test_v5_checkpoint_bindings.py`
- Create: `tests/test_v5_checkpoint_transactions.py`
- Create: `tests/test_v5_artifact_blobs.py`
- Create: `tests/test_v5_code_patch_manifests.py`
- Create: `tests/test_v5_effective_attempts.py`
- Create: `tests/test_v5_execution_scope_policy.py`
- Create: `tests/test_v5_scope_revalidation.py`
- Create: `tests/test_v5_bound_execution.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/record_repository.py`
- Modify: `brain/v5/record_refs.py`
- Modify: `brain/v5/checkpoints.py`
- Modify: `brain/v5/evidence.py`
- Modify: `brain/v5/research_state.py`
- Modify: `brain/v5/record_family_registry.py`

**Interfaces:**
- Extends: `ToolRecipeRecord`, `ToolRunRecord`, `CodeStateRecord`,
  `ArtifactRecord`, `MonitorSnapshotRecord`, `HumanCheckpointRecord`
- Produces: `ExecutionEnvironmentRecord`, `ExecutionBaselineRecord`
- Produces: `PinnedRecordRef`, `FrozenDependencyManifest`, and
  `CheckpointSubjectBinding`
- Produces: `ArtifactBlobReceiptRecord`, `CodePatchManifestRecord`,
  `CheckpointApplicationReceiptRecord`, `EffectiveAttemptState`,
  `ExecutionMaturityProjection`, `ExecutionScopeDecision`,
  `ScopeRevalidationDecisionRecord`, and `BoundExecutionReceipt`
- Produces: `get_record_version(ws, record_ref, content_hash)` and
  `validate_checkpoint_binding(ws, checkpoint_ref, expected)`
- Produces: `assess_execution_scope(ws, *, operation, consumer_scope,
  dependency_refs, revalidation_decision_refs=()) -> ExecutionScopeDecision`
- Produces: `request_bound_checkpoint`, `decide_bound_checkpoint`,
  `apply_bound_checkpoint_action`, `capture_artifact_bytes`,
  `resolve_artifact_bytes`, `capture_code_patch_manifest`,
  `record_scope_revalidation`, and `execute_bound_tool_request`
- Adds families: `artifact_blob_receipts`,
  `checkpoint_application_receipts`, `code_patch_manifests`,
  `scope_revalidation_decisions`,
  `execution_environments`, `execution_baselines`

`RecordFamilySpec` registration for the four dependency/transaction families
must generate their workspace directories and cover typed-ref resolution,
inventory, lifecycle, index, and strict repository reads before their writers
are enabled.

- [ ] **Step 1: Write failing schema-v1/v2 compatibility tests**

Instantiate every current schema-v1 shape unchanged. Instantiate v2 records and
assert exact structured argv, parameter provenance, environment ref, scheduler,
monitor refs, validation refs, skill usage refs, maturity, and non-claims are
retained.

Test current and archived hash-qualified reads, missing archive/hash mismatch,
same-ref later revision, frozen dependency round-trip, wrong checkpoint action,
wrong subject/request hash, expired checkpoint, and prohibited replay.
Use deterministic concurrency barriers and failpoints to prove two consumers of
one checkpoint yield one exact idempotent action/receipt, a different action is
rejected, and interruption before/after result write reconciles on retry. Run
maturity is derived from the immutable accepted baseline instead of a second
non-atomic ToolRun mutation.

Test recursive frozen closure, not only root pinning: every declared transitive
edge must appear as an owner-field-target ref/hash/revision edge, artifacts must
terminate in exact blob receipts, dirty code must terminate in an exact patch
manifest whose required bytes terminate in blob receipts, and replay must fail
if it would need a latest/current, path, URI, worktree, or scope-tuple lookup.

Test content-addressed local byte capture/resolve/rehash, deletion of the
original path, corrupt/missing blob, immutable external object receipt with
retention/availability verification, and rejection of reference-only mutable
paths from baseline readiness. New artifact writers either pin bytes/approved
immutable storage or label the artifact `reference_only`.

Test immutable `CodePatchManifestRecord` entries for
staged/unstaged/deleted/binary/submodule/
required-untracked paths, blob refs and hashes, excluded-required paths, and
overall coverage. Excluded required bytes force `non_reproducible`.

Test `ScopeRevalidationDecisionRecord` with target topic/program/claim, pinned
bridge and source refs, applicability conditions, validation/evidence/checkpoint
refs, decision, expiry, and supersession. Context/execution consumers resolve
the exact decision ref; bridge presence or a bare checkpoint never implies
target validation.

- [ ] **Step 2: Run RED**

Run execution-model, record-family, envelope, and real-shape compatibility
fixtures. Expected: new fields/classes/families are absent.

- [ ] **Step 3: Implement v2 dataclasses with old fields first**

`ToolRecipeRecord` adds defaulted fields: `recipe_version`,
`software_constraints`, `command_template`, `parameter_schema`, `parameter_roles`,
`units`, `defaults`, `allowed_ranges`, `physical_meanings`, `input_roles`,
`output_roles`, `script_refs`, `environment_requirements`, `failure_modes`,
`stop_rules`, `validation_contract_refs`, and `applicability_boundary`.
Existing `validation_contract_ids` remains a read-only schema-v1 compatibility
alias; new writes use typed refs.

`ToolRunRecord` adds defaulted fields: `argv`, `cwd`, `actual_parameters`,
`parameter_provenance`, `input_manifest`, `input_hashes`, `script_hashes`,
`recipe_ref`, `code_state_ref`, `environment_ref`, `executor_id`,
`executor_version`, `executor_hash`, `scheduler`, `job_id`, `submitted_at`, `started_at`,
`completed_at`, `exit_status`, `output_manifest`, `validation_result_ids`,
`monitor_snapshot_ids`, `artifact_refs`, `validation_result_refs`,
`monitor_snapshot_refs`, `skill_usage_refs`, `recorded_maturity`, and
`non_claims`. Legacy `maturity` remains a read alias. New ToolRun writes use only
`diagnostic`, `reproducible_candidate`, or `superseded`; they never persist
`accepted_baseline` on the run.
The old `*_ids` fields remain readable but cannot satisfy v2 reproducibility
without resolvable typed-ref counterparts.

`MonitorSnapshotRecord` adds `captured_at`, `sequence`, `collector_id`,
`collector_version`, `remote_uri`, `resource_usage`, and `immutable=True`.
Keep all additions defaulted so schema-v1 construction remains valid.

`ArtifactRecord` adds compatibility-defaulted `content_hash`, `hash_algorithm`,
`captured_at`, role/provenance refs, `artifact_blob_receipt_ref`, and
`artifact_blob_receipt_hash`. Every reproducibility-eligible artifact pins one
exact immutable `artifact_blob_receipt:` record; the paired receipt hash is that
record's `record_content_hash`, while the artifact `content_hash` equals the
receipt's byte hash. A reference-only artifact leaves the receipt fields null
and cannot satisfy a baseline; a URI and size alone are insufficient.

`CodeStateRecord` adds compatibility-defaulted `patch_manifest_ref` and
`patch_manifest_hash`. Dirty v2 code states and baselines pin an immutable
`code_patch_manifest:` record whose paired hash is the manifest record's
`record_content_hash`; an in-memory manifest or diff/status hash alone cannot
satisfy reproducibility. Manifest entries pin required changed and
untracked byte streams through artifact-blob receipt refs/hashes. Clean exact-
commit states leave the patch fields null.

`HumanCheckpointRecord` gains compatibility-defaulted `action`, typed
`subject_refs`, `request_hash`, `payload_hash`, `expires_at`, `replay_policy`,
and target/effect policy fields. New writes do not contain `consumed_by_ref`.
Schema-v1 values remain readable only as legacy/read-only compatibility
projections; v2 writers reject the field, and policy never treats it as proof of
application. Legacy checkpoints remain readable but cannot authorize new
baseline, Skill, migration, or trust-sensitive v2 actions without an exact
binding.

`ValidationContractRecord` and `ValidationResultRecord` gain
compatibility-defaulted pinned contract/run/recipe refs, executor id/version/
hash, output-manifest hash, failure-contract hash, and checked artifact hashes.
Legacy results remain readable but cannot satisfy v2 baseline readiness without
these bindings.

- [ ] **Step 4a: Implement content-addressed artifact and checkpoint action transactions**

Local artifact bytes are atomically copied to a SHA-256-addressed workspace blob
store; external-only bytes require an immutable-storage receipt with object
version, hash, retention/access policy, and verified availability. Baseline
replay resolves and rehashes bytes.

A local `ArtifactBlobReceiptRecord` has deterministic id
`artifact-blob-sha256-<byte_sha256>` and a canonical payload containing only
`storage_kind=local_sha256`, hash algorithm, byte SHA-256, byte length, and the
content-addressed blob key. Source path, capture time, and collector provenance
belong to the referring `ArtifactRecord`, not the local receipt identity. An
identical recapture is idempotent and yields the same receipt ref/content hash.
External receipts instead derive their immutable id from provider, object id,
object version, byte hash, length, and retention/access policy. Skill package
files in M4 must resolve to the deterministic local receipt form.

`CheckpointApplicationReceiptRecord` is the sole immutable canonical
application/consumption fact. Its `record_id` and `application_id` are both
`checkpoint-application-<sha256(canonical application key)>`, where the key is
the action, `action_payload_hash`, pinned intent, sorted pinned subjects, pinned
request, and pinned decision. The record contains `intent_ref/hash/revision`,
`action` plus `action_payload_hash`, `subject_refs` as `PinnedRecordRef` values,
`request_ref/hash/revision`, `decision_ref/hash/revision`, optional
`result_ref/hash/revision`, terminal `status=applied|failed`, `started_at`,
`completed_at`, `recorded_at`, and structured `errors`. A recovery-only journal
and one action lock may coordinate writes but cannot prove consumption. Only
`status=applied` proves consumption; `failed` records the attempted application
and errors without consuming the decision. Retrying a failed application
requires a new pinned intent and a policy-valid decision; it never revises the
failed receipt.
`apply_bound_checkpoint_action` writes the exact immutable result and one
receipt; it never patches `HumanCheckpointRecord` or the result. Retry verifies
an already-written deterministic result and completes the missing receipt.
Exact replay returns that receipt; different replay is rejected.

`execute_bound_tool_request` accepts only a registered M2 executor and an
exact recipe/argv/environment/write/network/timeout policy bound to a high-risk
checkpoint. It returns a `BoundExecutionReceipt` containing pinned ToolRun and
ValidationResult refs plus `checkpoint_application_receipt_ref` and
`checkpoint_application_receipt_hash`. It has no ambient shell authority and is
the only M4 handoff for arbitrary Skill validation commands.

- [ ] **Step 4: Add environment/baseline models and families**

`ExecutionEnvironmentRecord` records host/cluster, OS/architecture, compiler,
MPI, math libraries, modules, package versions, container/lock digests,
scheduler/partition constraints, executable paths/hashes, redacted env, source
refs, and creation time. `ExecutionBaselineRecord` references recipe, run, code
state, environment, role-labelled input/output artifacts with byte hashes,
validations, monitor/executor, effective attempt/lane contract, scope, known
non-claims, acceptance checkpoint, frozen dependency manifest, status, and
creation time.

The embedded `FrozenDependencyManifest` contains sorted root pinned refs, sorted
resolved nodes, explicit `{owner_ref, field_name, target_ref, target_hash,
target_revision}` edges, and a canonical `closure_hash`. Construction follows
only dependency fields declared by `RecordFamilySpec`, recursively resolves
exact current/archive versions, and rejects undeclared edges, missing hashes, or
unresolved terminal bytes. It visits each pinned node once while retaining
explicit back-edges, so exact run/validation back-links terminate without being
discarded. The checkpoint-application receipt is
written after the baseline result and pins that result, so it remains outside
the result's closure and no hash cycle is introduced.

- [ ] **Step 5: Re-export v2 classes after model compatibility shards**

Do not edit generated model shards. `models.py` imports the focused v2 classes
after loading compatibility shards so existing imports retain the same names.

- [ ] **Step 6: Run GREEN, architecture, and index tests; commit**

Commit message: `v5: add execution memory v2 models`.

## Task 2: Environment, Recipe, Run, And Baseline Writers

**Files:**
- Create: `brain/v5/execution_contracts.py`
- Create: `brain/v5/execution_policy.py`
- Create: `brain/v5/execution_environments.py`
- Create: `brain/v5/execution_baselines.py`
- Create: `tests/test_v5_execution_memory.py`
- Modify: `brain/v5/tools.py`
- Modify: `brain/v5/code.py`
- Modify: `brain/v5/validation.py`
- Modify: `brain/v5/policy.py`
- Modify: `brain/v5/pretool_policy.py`
- Modify: `brain/v5/adapter_protocols.py`

**Interfaces:**
- Produces: `redact_execution_payload(payload, policy) -> RedactionResult`
- Produces: `record_execution_environment(ws, record, *, actor) -> WriteResult`
- Produces: `record_tool_recipe_v2(ws, record, *, actor) -> WriteResult`
- Produces: `record_tool_run_v2(ws, record, *, actor) -> WriteResult`
- Consumes: `assess_execution_scope(...) -> ExecutionScopeDecision`
- Produces: `assess_baseline_readiness(ws, run_ref) -> BaselineReadiness`
- Produces: `project_execution_maturity(ws, run_ref) -> ExecutionMaturityProjection`
- Produces: `accept_execution_baseline(ws, request, *, actor) -> BaselineAcceptanceResult`

- [ ] **Step 1: Write failing redaction and maturity tests**

Test environment keys matching token/password/key/credential patterns,
configured sensitive argv positions, URI credentials, and an explicit
allowlist. Assert redacted values never enter canonical Markdown.

- [ ] **Step 2: Write failing reproducibility tests**

Cover clean exact commit, dirty worktree with patch, dirty worktree without
patch, missing executable hash, missing environment, failed output manifest,
stale code-state refs, bare ids without typed refs, and a path/URI whose captured
content hash no longer matches.

Dirty coverage includes staged, unstaged, deleted, binary, submodule, and
required untracked source/script bytes. If any required bytes are excluded from
the pinned patch/artifact manifest, retain `non_reproducible` even when status or
diff text has a hash.

Apply `assess_execution_scope(...)` to recipe, environment, run, artifact,
validation, checkpoint, and baseline refs. Shared recipes/environments may be
reused when their scope permits; claim-local runs/results require a reviewed
bridge plus an explicitly supplied pinned target-revalidation decision. Add
foreign topic/program/claim negatives for every baseline dependency. Baseline,
context, and facade code must import this evaluator and may not duplicate its
family/scope matrix.

- [ ] **Step 3: Implement repository writers and compatibility wrappers**

Keep `register_tool_recipe`, `record_tool_run`, and `record_code_state` public
signatures working; route their canonical persistence through the v2 repository
writers. Explicit revisions replace current backfill-overwrite behavior.

- [ ] **Step 4: Implement baseline preflight**

Require `recorded_maturity=reproducible_candidate`, exact recipe/run/environment/code
version refs and frozen dependency hashes, role-labelled artifact byte hashes,
complete outputs, latest immutable monitor state, effective attempt/lane
eligibility, passed validation results, no unresolved reproducibility errors,
and a decided human checkpoint whose action/subjects/request hash exactly bind
the proposed baseline. Every validation result must bind the exact run, recipe
version/hash, executor version/hash, output manifest, and failure-mode contract.

- [ ] **Step 4a: Gate every new canonical writer through policy**

Add baseline/environment/recipe/run writes to pre-tool policy, adapter
protocols, bridge schemas, and negative replay/mismatch tests. Task 4 separately
adds monitor actions and Task 6 adds derivation actions when those writers exist.
CapabilitySpec state effects remain descriptive metadata, not the enforcement
mechanism.

- [ ] **Step 5: Prove trust isolation**

Baseline acceptance updates execution maturity only. Monkeypatch claim/evidence
trust writers to fail if called; baseline tests must pass.

`ExecutionBaselineRecord` is authoritative for
`effective_maturity=accepted_baseline`; ToolRun recorded maturity is unchanged.
`BaselineAcceptanceResult` returns baseline ref/hash and checkpoint-application
receipt ref/hash. Context, cockpit, facade, and Skill applicability consume
`project_execution_maturity`, never a raw run field.

- [ ] **Step 6: Run tool/code/checkpoint/repository regressions; commit**

Commit message: `v5: enforce reproducible execution baselines`.

## Task 3: Generic Local And Remote Compute Intake

**Files:**
- Create: `brain/v5/compute_run_intake.py`
- Create: `brain/v5/compute_run_intake_contracts.py`
- Create: `tests/test_v5_compute_run_intake.py`
- Create: `tests/fixtures/v5_compute_run_intake/nio_manifest.json`

**Interfaces:**
- Produces: `ComputeRunIntakeRequest`, `ComputeRunIntakeReport`
- Produces: `build_compute_run_intake(request: ComputeRunIntakeRequest) ->
  ComputeRunIntakeReport`

- [ ] **Step 1: Write failing deterministic fixture tests**

Fixtures cover a local completed run, Slurm remote manifest, partial running
job, missing executable hash, failed job, and inaccessible URI. Assert stable
candidate JSON and explicit missing fields.

- [ ] **Step 2: Run RED**

- [ ] **Step 3: Implement collector-manifest ingestion**

Inputs include URI, host/cluster, scheduler/job id, collector id/version,
captured time, code/executable hashes, input/output manifests, resource
accounting, lane, and optional topic/claim/run refs. Direct SSH/scheduler access
is adapter responsibility; the kernel consumes an exact collector manifest.

- [ ] **Step 4: Build typed prefill candidates only**

Return tool-run, artifact, monitor, environment, and validation-checklist
candidates plus checked/missing fields. Set `writes_records=False`,
`orientation_only=True`, and `can_update_claim_trust=False`.

- [ ] **Step 5: Preserve NiO only as compute-intake fixture data**

Keep the existing NiO collector material as test/example data for the generic
intake builder; no production constant chooses NiO or a fixed path. Do not add
compute intake, monitor, baseline, or Skill behavior to Harness Feedback. M5
removes its legacy case-specific runtime and retains only a problem dossier.

- [ ] **Step 6: Run intake/harness tests and commit**

Commit message: `v5: generalize compute run intake`.

## Task 4: Immutable Monitor Snapshots

**Files:**
- Create: `brain/v5/monitor_snapshots.py`
- Modify: `brain/v5/effective_attempts.py`
- Create: `tests/test_v5_monitor_snapshots.py`
- Modify: `brain/v5/hpc_cockpit.py`
- Modify: `brain/v5/lane_contracts.py`
- Modify: `tests/test_v5_hpc_cockpit.py`
- Create: `tests/test_v5_lane_contracts.py`

**Interfaces:**
- Produces: `record_monitor_snapshot_v2(ws, record, *, actor) -> WriteResult`
- Produces: `list_monitor_history(ws, tool_run_ref) -> MonitorHistory`
- Projects via `effective_attempts.py`:
  `resolve_effective_attempt_state(ws, tool_run_ref) -> EffectiveAttemptState`

- [ ] **Step 1: Write failing immutability/order tests**

Same snapshot id plus identical content is idempotent; conflicting content is
rejected. Sequence must increase per run. Earlier scheduler observations remain
readable after later snapshots.

- [ ] **Step 2: Implement repository writer and history projection**

Snapshot id is deterministic from tool run, collector, captured time, and
sequence. Never revise a snapshot in place. A later observation links the
previous snapshot but does not supersede its factual observation.

- [ ] **Step 3: Test remote partial-state boundary**

`COMPLETED` scheduler state without required outputs/validation remains process
completion only and cannot mark a run accepted or scientific evidence.

Test attempt/supersession chains, latest immutable monitor state, failed and
partial outputs, diagnostic/final lane allowlists, and an older successful
attempt superseded by a newer failure. The HPC cockpit and baseline preflight
consume the same `EffectiveAttemptState`; mutable `evidence_status` alone cannot
decide active/completed/accepted state.

Register monitor-snapshot write/read capabilities and pre-tool/bridge policy in
this task, with public-surface and scope-mismatch tests.

- [ ] **Step 4: Run monitor/HPC regressions and commit**

Commit message: `v5: persist immutable monitor history`.

## Task 5: Formula-Code Relations And Edit Capsules

**Files:**
- Create: `brain/v5/formula_code_map.py`
- Create: `brain/v5/formula_code_contracts.py`
- Create: `tests/test_v5_formula_code_map.py`
- Modify: `brain/v5/physics_objects.py`
- Modify: `brain/v5/context_compiler.py`

**Interfaces:**
- Produces: `record_formula_code_relation(ws, relation, *, actor) -> WriteResult`
- Produces: `build_code_edit_execution_capsule(ws, request) -> dict[str, Any]`

- [ ] **Step 1: Write failing LibRPA mapping tests**

Cover `implemented_by`, `controlled_by_parameter`, `approximated_by`,
`discretized_by`, `normalizes_as`, `produces_observable`, and `validated_by`.
Require formula/object ref, exact code-state ref, module/function or parameter,
scope, assumptions, source refs, tests, and applicability boundary. Formula,
code-state, tests, and accepted baseline refs are hash-pinned. Reject a current
ref whose content has changed since relation review.

- [ ] **Step 2: Use current object relations with a structured metadata contract**

Do not add a parallel knowledge graph. Persist formula-code links as
`ObjectRelationRecord` with the allowed relation type and structured metadata
keys: `formula_ref`, `code_state_ref`, `module`, `function`, `parameter`,
`output`, `normalization`, `test_refs`, and `known_failures`.

- [ ] **Step 3: Implement bounded edit capsule**

Retrieve formula/symbol, code location, exact commit/patch, parameter role,
tests, known failures, accepted baseline, and exact expansion refs. A stale code
state makes the capsule non-reproducible and blocks baseline claims.

Add foreign-topic/claim negative tests. A reviewed M1 bridge may expose the
relation as orientation, but target-side code/baseline revalidation is required
before use and claim-trust transfer remains forbidden.

- [ ] **Step 4: Run physics-object/context/code tests and commit**

Commit message: `v5: connect formulas to exact code states`.

## Task 6: Formal Derivation DAG And Legacy Migration

**Files:**
- Create: `brain/v5/derivation_models.py`
- Create: `brain/v5/derivations.py`
- Create: `brain/v5/derivation_contracts.py`
- Create: `brain/v5/derivation_migration.py`
- Create: `brain/v5/derivation_reviews.py`
- Create: `tests/test_v5_derivations.py`
- Create: `tests/test_v5_derivation_migration.py`
- Create: `tests/test_v5_derivation_reviews.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/record_family_registry.py`
- Modify: `brain/v5/source_reconstruction.py`
- Modify: `brain/v5/source_reconstruction_review.py`

**Interfaces:**
- Produces: `DerivationChainRecord`, `DerivationStepRecord`,
  `DerivationReviewRecord`
- Produces: `record_derivation_chain`, `record_derivation_step`,
  `record_derivation_review`
- Produces: `supersede_derivation_review(ws, prior_review_ref, replacement, *,
  actor) -> WriteResult`
- Produces: `validate_derivation_dag`, `migrate_legacy_derivation_candidates`
- Produces: `project_derivation_status(ws, chain_ref) -> DerivationStatusProjection`
- Adds family: `derivation_reviews`

- [ ] **Step 1: Write failing model/DAG tests**

A chain records target, assumptions, conventions, framework, regime, ordered
step refs, open gaps, checks, source refs, and status. A step records input and
output expressions, justification type, dependencies, invoked knowledge refs,
source anchors, local checks, unresolved conditions, and status.

- [ ] **Step 2: Test cycles, missing refs, unresolved conditions, and scope**

Reject cycles and cross-chain dependencies without an explicit imported-chain
ref. A derivation with open gaps cannot have status `structurally_closed`.
Reject foreign topic/program/claim dependencies unless the imported-chain ref
binds origin hashes and a M1 bridge; target review remains required.

- [ ] **Step 3: Implement additive families and repository writers**

Add `derivation_chains` and `derivation_steps` with `trust_effect=none` until a
separate validation/evidence path uses them. Writers validate the complete DAG
against pinned refs before accepting `structurally_closed`. `reviewed` and
`validated` are not chain writer statuses.

- [ ] **Step 3a: Add hash-bound derivation review and reconstruction coverage**

Review records bind chain/step content hashes, exact source anchors,
validation/tool-run check refs, reviewer/checkpoint, decision, and scope.
Source-reconstruction audit consumes derivation chains/steps/reviews and reports
structural closure, source completeness, review, and validation separately. A
structurally closed chain without review cannot be rendered as proved or used as
evidence basis.

`project_derivation_status` derives rather than mutates structural/reviewed/
validated state from active pinned records and validation results. Review
revision uses explicit supersession. Register chain/step/review writers and
status projection in capability/public-surface/pre-tool/bridge contracts in this
task, including foreign-scope and stale-hash negatives.

- [ ] **Step 4: Implement reviewable legacy migration**

Read legacy DAG artifacts, preserve exact source path/hash and original text,
emit candidate records plus unresolved mappings, and write nothing unless an
explicit reviewed apply request is supplied.

- [ ] **Step 5: Run derivation, registry, index, and context tests; commit**

Commit message: `v5: add inspectable formal derivations`.

## Task 7: Execution Facade And M2 Acceptance

**Files:**
- Create: `brain/v5/mcp_execution.py`
- Create: `brain/v5/cli_execution.py`
- Create: `brain/v5/execution_surface_contracts.py`
- Create: `tests/test_v5_execution_facade.py`
- Create: `tests/test_v5_gate2_execution_e2e.py`
- Create: `docs/superpowers/progress/2026-07-10-aitp-gate-2-release-audit.md`
- Modify: `brain/v5/capability_registry_data.py`
- Modify: `brain/v5/capability_surface_contracts.py`
- Modify: `brain/v5/public_surfaces.py`
- Modify: `brain/v5/mcp_tools.py`
- Modify: `brain/v5/cli.py`
- Modify: `brain/v5/context_compiler.py`
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-07-09-aitp-final-research-lifecycle-roadmap.md`

- [ ] **Step 1: Register full-surface execution capabilities**

Expose pinned version read, bound checkpoint request/decide/apply, artifact
capture/resolve, code-patch capture, scope revalidation, registered bound tool
execution, environment/recipe/run, effective attempt/maturity, intake, monitor,
baseline readiness/acceptance, formula-code capsule, derivation/review/status,
and migration dry-run. Give every operation exact CapabilitySpec effects, deep
public validators, pre-tool/bridge policy where stateful, and CLI/MCP parity.
`BoundExecutionReceipt` is a derived validated surface backed by pinned
ToolRun, ValidationResult, and `CheckpointApplicationReceiptRecord` canonical
records, including the checkpoint-application receipt ref/hash, not a parallel
record family. Context compilation and execution facades use
`assess_execution_scope(...)` rather than a local scope matrix. Do not enlarge
compact visibility by default. Loader files receive only narrow focused-module
imports.

- [ ] **Step 2: Add LibRPA/HPC vertical acceptance**

Record exact commit/patch, script, structured parameters, environment, remote
job, immutable monitor history, artifacts, validation, and accepted baseline.
Assert a dirty unpatched run and partial scheduler state remain ineligible.
This is deterministic contract/fixture acceptance. It must not be labeled real
LibRPA/HPC operational acceptance; M6 requires a hash-pinned real collector
manifest/read-only topic probe.

- [ ] **Step 3: Add formal-derivation vertical acceptance**

Build a source-anchored QFT/QG derivation chain with conventions, a failed
step, open gap, and later repaired step. Assert no hidden reasoning text or
claim-trust mutation is stored.

- [ ] **Step 4: Run M0-M2 lanes and real-store compatibility audit**

All objects in the recorded pre-Gate-2 audit remain readable.
Capability/family/public-surface/policy drift is zero,
architecture limits are unchanged, and canonical hashes change only for
explicit test fixtures or approved new records.

- [ ] **Step 5: Update docs, write release audit, verify staged tree, and commit**

Commit message: `v5: complete M2 reproducible execution`.

## M2 Completion Checklist

- [ ] A validated accepted run is reproducible from exact structured records.
- [ ] Every accepted baseline resolves every frozen dependency by ref and hash.
- [ ] Dirty code without a patch is visibly non-reproducible.
- [ ] Secrets are redacted before persistence.
- [ ] Remote partial state is never reported as scientific completion.
- [ ] Monitor observations are immutable and ordered.
- [ ] Formula-code context resolves formula, code, parameters, tests, and baseline.
- [ ] Derivation DAGs preserve assumptions, conventions, checks, and open gaps.
- [ ] Structural closure is distinct from reviewed/validated derivation status.
- [ ] Existing execution ids and schema-v1 records remain readable.
- [ ] No execution/context/derivation surface updates claim trust directly.
- [ ] M2 is labeled fixture-contract complete only; real LibRPA/HPC
  acceptance remains a mandatory M6 decision input.
