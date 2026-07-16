# AITP M4 Reviewed Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compile repeated validated procedures from the research graph into complete, reviewable, versioned Skill packages, install them project-locally only after hash-bound human approval, and record exact applicability and use.

**Architecture:** Procedural distillation starts from typed M1-M3 graph slices and execution evidence, never loose chat or conceptual knowledge. Canonical candidate/readiness/proposal/install/usage records preserve provenance and review decisions; generated package files and host shims are content-addressed tool assets. Installation, overwrite, and patch application require a typed checkpoint bound to package hash, target, and diff.

**Tech Stack:** Python 3.12, dataclasses, Markdown/YAML, JSON manifests, SHA-256, project-local `.agents/skills` and host shim targets, M0 repository/capability services, pytest.

## Global Constraints

- M1-M3 must be green before M4 production code begins.
- Only executable, verifiable, transferable procedures can become Skill candidates.
- Definitions, formulas, derivations, source summaries, interpretations, and insights remain graph/knowledge records.
- A candidate may be generated automatically; package application never is.
- Install/overwrite/patch approval is bound to exact package hash, target path, diff hash, and checkpoint action.
- Every host-discoverable write, including domain-pack shims and rollback, uses
  the same project-root-constrained plan/checkpoint/receipt path.
- Generated Skills use a dedicated `aitp-generated` namespace and never overwrite external Skills implicitly.
- Canonical Skill content is host-neutral; Codex/Claude/Kimi adapters are generated shims.
- A Skill package references graph records instead of copying large research histories into `SKILL.md`.
- Skill applicability is advisory and cannot transfer scientific claim trust.
- Every actual Skill use records exact skill id/version/hash and the consuming run/baseline/session.
- Patch proposals require new validated success, failure, or applicability-boundary records and human review.
- Existing domain Skill shims remain discovery adapters.
- M4 executes built-in declarative no-network validators only. Arbitrary
  project/package commands require a separate M2 high-risk execution request
  and receipt and are never an install side effect.
- `(skill_id, semantic_version) -> package_hash` is immutable; reinstall,
  upgrade, downgrade, and rollback semantics are explicit and auditable.
- Install applies through durable intent, filesystem readback, immutable receipt,
  and compensating rollback on receipt failure.
- Harness Feedback is not a Skill input or patch signal; only M4 validated
  graph/usage records can generate Skill candidates or patches.
- M0 compatibility loaders/shards receive only narrow imports/re-exports;
  focused M4 modules own behavior.

---

## File Structure

| File | Responsibility |
|---|---|
| `brain/v5/skill_models.py` | Distillation, readiness, proposal, install, and usage records. |
| `brain/v5/skill_distillation_records.py` | Procedural candidate aggregation/writer. |
| `brain/v5/skill_distillation_contracts.py` | Procedural completeness and knowledge exclusion. |
| `brain/v5/skill_readiness.py` | Independent-use, failure-coverage, overlap, and fixture readiness. |
| `brain/v5/skill_readiness_contracts.py` | Readiness report validation. |
| `brain/v5/project_skill_packages.py` | Host-neutral content-addressed package preview and proposal rendering. |
| `brain/v5/project_skill_contracts.py` | Manifest/provenance/hash/checkpoint/target validation. |
| `brain/v5/skill_install_transactions.py` | Durable install intent, atomic apply/readback, receipt, compensation, and rollback. |
| `brain/v5/skill_validation_execution.py` | Separate M2 high-risk validation request/receipt handoff. |
| `brain/v5/skill_applicability.py` | Reviewed and derived selector matching. |
| `brain/v5/skill_usage.py` | Exact version/hash usage and patch-signal records. |

## Test Protocol

Each task runs its new tests to the expected missing-contract RED, then GREEN
with a unique writable external `--basetemp`, followed by focused M0-M3 and
security regressions. Record exact command, expected/actual failure, pass count,
target before/after hashes, and temp root. Collection-only success is not test
execution.

## Task 1: Procedural Distillation Records

**Files:**
- Create: `brain/v5/skill_models.py`
- Create: `brain/v5/skill_distillation_records.py`
- Create: `brain/v5/skill_distillation_contracts.py`
- Create: `tests/test_v5_skill_distillation_records.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/record_family_registry.py`
- Modify: `brain/v5/research_distillation.py`

**Interfaces:**
- Produces: `SkillDistillationCandidateRecord`
- Adds family: `skill_distillation_candidates`
- Produces: `build_skill_distillation_candidate(ws, request) -> CandidateBuildReport`
- Produces: `record_skill_distillation_candidate(ws, report, *, actor) -> WriteResult`

- [x] **Step 1: Write failing procedural-only tests**

Accept stabilized ordered steps, parameter roles/values, prerequisites, inputs,
outputs, stop rules, known failures, recovery steps, validation refs, execution
refs, source topics, code/environment scope, applicability selectors, transfer
boundary, and package requirements. Reject conceptual-only and source-summary
inputs with explicit reason codes.

- [x] **Step 2: Run RED**

- [x] **Step 3: Define candidate record**

Fields include candidate id/title/summary, source topic/program refs, workflow
kind, ordered steps, parameter contract, inputs/outputs, prerequisites, stop
rules, failures/recoveries, validation refs, independent execution refs,
artifact/code/environment refs, applicability selectors, transfer boundary,
package requirements, status, source refs, created time, and fixed
`can_update_claim_trust=False`.

- [x] **Step 4: Aggregate independent executions without trust transfer**

Match by normalized procedural signature plus declared scope. Preserve each run,
validation, failure, code, environment, and topic separately. Cross-topic
aggregation can demonstrate workflow repetition but never claim support.

- [x] **Step 5: Remove all semantic candidate paths from distillation**

Regression tests cover definitions, formulas, derivations, literature summaries,
interpretations, and insights. Their correct route is M3.

- [x] **Step 6: Run distillation/knowledge/execution tests and commit**

Commit message: `v5: add procedural skill distillation records`.

**Task 1 implementation evidence (2026-07-16):**

- `SkillDistillationCandidateRecord` is a canonical v2 candidate-only family;
  it pins recipes, final runs, passed validations, artifacts, code states,
  environments, programs, and sources without claim-trust authority.
- The builder verifies every run-level topic and provenance binding, preserves
  all retries, and computes deterministic independent-execution groups rather
  than counting duplicate run ids as independent uses.
- Definition, formula, derivation, literature/source summary, interpretation,
  and insight inputs fail with explicit M3 routing reasons. The legacy research
  distillation wrapper now routes procedural material to the canonical
  candidate record instead of a direct Skill proposal.
- Focused Task 1, compatibility, registry, repository, execution, knowledge,
  and architecture tests passed 86 tests before the final binding hardening;
  the final binding-focused suite passed 29 tests.

## Task 2: Skill Readiness And Overlap Audit

**Files:**
- Create: `brain/v5/skill_readiness.py`
- Create: `brain/v5/skill_readiness_contracts.py`
- Create: `tests/test_v5_skill_readiness.py`
- Modify: `brain/v5/record_family_registry.py`

**Interfaces:**
- Produces: `SkillReadinessReportRecord`
- Adds family: `skill_readiness_reports`
- Produces: `assess_skill_readiness(ws, candidate_ref) -> SkillReadinessReportRecord`

- [x] **Step 1: Write failing readiness matrix tests**

Default readiness requires two independent validated uses, or one narrow
validated use plus a decided expert-exception checkpoint. Require at least one
relevant negative/failure case or an explicit justified none-known boundary,
stable applicability, complete stop rules, and an executable validation fixture.

- [x] **Step 2: Test independence**

Two retries of one scientific run, duplicated records, the same artifact, or
the same code/environment snapshot do not count as independent uses. Distinct
topics may count only for workflow validation, not trust transfer.

- [x] **Step 3: Implement installed/external overlap audit**

Compare normalized purpose, selectors, steps, command templates, files, and
declared domain against AITP-generated catalog and external/domain shims. Return
`new`, `extension_candidate`, `duplicate`, or `conflict` with exact refs.

- [x] **Step 4: Persist readiness reasons and missing requirements**

Reports contain checked refs, validation fixture refs, failures, overlap,
blockers, required actions, status, and trust-neutral boundary. Readiness does
not create a package.

- [x] **Step 5: Run readiness/domain-shim tests and commit**

Commit message: `v5: assess reviewed skill readiness`.

**Task 2 implementation evidence (2026-07-16):**

- Readiness defaults to two deterministic independent-use groups. One narrow
  use is accepted only with a current v2 bound checkpoint whose exact candidate
  pin, action, payload hash, scope, effect policy, and host receipt all verify.
- Failure coverage accepts either typed failure/recovery rows or an explicit
  none-known boundary. Stop rules, stable selectors, and a declared validation
  fixture remain mandatory.
- Project-local `aitp-generated` manifests and external domain-pack Skill refs
  are classified as `new`, `extension_candidate`, `duplicate`, or `conflict`.
  Duplicate/conflict and malformed catalog state block package readiness;
  extension overlap remains visible for review.
- The canonical readiness writer recomputes the current report before writing,
  so a shape-valid forged `ready` result or post-assessment catalog drift cannot
  enter the graph. No readiness path installs files or updates claim trust.
- Task 2 broad checkpoint/domain/registry/query/architecture regression passed
  108 tests; the final forged-report and focused suite passed 34 tests.

## Task 3: Host-Neutral Package Preview

**Files:**
- Create: `brain/v5/project_skill_packages.py`
- Create: `brain/v5/project_skill_contracts.py`
- Create: `brain/v5/skill_package_artifacts.py`
- Create: `tests/test_v5_project_skill_packages.py`
- Create: `tests/test_v5_skill_package_artifacts.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/record_family_registry.py`

**Interfaces:**
- Produces: `SkillPackageArtifactRecord`, `SkillProposalRecord`
- Adds families: `skill_package_artifacts`, `skill_proposals`
- Produces: `record_skill_package_artifact(ws, preview, *, actor) -> WriteResult`
- Produces: `build_skill_package_preview(ws, readiness_ref) -> SkillPackagePreview`
- Produces: `record_skill_proposal(ws, preview, *, actor) -> WriteResult`

- [x] **Step 1: Write failing completeness tests**

A package preview contains `SKILL.md`, `manifest.json`, provenance refs,
applicability/transfer boundary, version, content hash, validation commands,
test fixtures, and required scripts/templates/references. Omit optional folders
when unused; reject referenced but missing files. Classify every validation as
an AITP built-in declarative validator or an explicit project command with
executor/network/write/timeout requirements.

The proposal pins every source record by ref/content hash and an immutable
package artifact containing the exact reviewed bytes plus renderer/template
version. Deleting preview files is safe only when deterministic reconstruction
reproduces the package hash; otherwise installation is blocked.

The package artifact is a canonical sorted POSIX-path tree manifest whose full
rows bind path, allowlisted file mode, length, SHA-256, and deterministic local
M2 artifact-blob receipt ref/content hash. Symlinks and special files are
rejected. Each path is a Unicode-NFC normalized relative POSIX path with no
empty, `.`, `..`, drive, or absolute segment; mode is exactly the string `0644`
or `0755`. The `tree_hash` input projects each row to exactly
`{path, mode, length, sha256, blob_receipt_content_hash}`, sorts rows by UTF-8
path bytes, serializes the list as UTF-8 JSON with sorted object keys, separators
`,` and `:`, no insignificant whitespace, and no trailing newline, then applies
SHA-256. M2 makes local receipt identity deterministic from byte content, so
recapturing identical bytes preserves both the row and tree hash. Renderer
code-state ref/hash, generator version, template refs, and other provenance stay
outside this byte-tree identity while remaining pinned on the package artifact.
External-only receipts must first be materialized into deterministic local blob
receipts. Exact file blobs make later reconstruction independent of mutable
renderer code.

- [x] **Step 2: Define host-neutral manifest**

Required keys: skill id, namespace, name, semantic version, package hash,
candidate/readiness refs, source topic/program refs, run/validation/failure refs,
selectors, entrypoint, included file hashes, validation commands, external
dependencies, license/access notes, renderer/template version, pinned package
artifact identity, and generated time. Reject same `(skill_id, version)` with a
different package hash. The manifest carries the deterministic artifact typed
ref but not that artifact record's content hash: embedding the latter would
create an impossible self-reference because the artifact tree contains the
manifest bytes. The canonical proposal supplies the exact artifact
ref/content-hash/revision pin.

- [x] **Step 3: Render a compact `SKILL.md`**

Include trigger/when-to-use, prerequisites, procedure, parameters, stop rules,
failure recovery, validation, applicability/non-applicability, and exact AITP
expansion refs. Do not embed source papers, long graph slices, or claim summaries.

- [x] **Step 4: Store proposal, not install**

The canonical proposal records full file hashes and package hash. Preview files
live under `.aitp/tools/skills/catalog/<skill-id>/<version>/preview`; they are
derived and disposable until approved.

- [x] **Step 5: Run package/hash/rebuild tests and commit**

Commit message: `v5: build host-neutral skill package previews`.

**Task 3 implementation evidence (2026-07-16):**

- A ready report renders a compact multi-file preview under the derived
  `aitp-generated` catalog only. `SKILL.md` contains when-to-use,
  non-applicability, prerequisites, procedure, parameters, stop rules, failure
  recovery, validation, and exact graph expansion refs without copying long
  physics summaries.
- Manifest and proposal preserve exact recipe, run, validation, artifact, code
  state, environment, program, and source pins. Proposals remain immutable
  `draft/not_applied` candidates and have no install, evidence, or claim-trust
  authority.
- Identity is deliberately two-layered. Manifest `package_hash` hashes the
  canonical manifest projection before its own hash is inserted and binds all
  non-manifest file hashes. Artifact `tree_hash` binds the complete sorted tree,
  including the final manifest and each local blob-receipt content hash. The
  proposal then pins the artifact record by exact ref/content hash/revision.
- Artifact reads re-resolve every M2 blob, verify row length/hash/order,
  recompute both hashes, and cross-check manifest/artifact identity before
  proposal or derived reconstruction. Same-id/version hash conflicts, unsafe
  paths, links/junctions, stale preview files, malformed pins, and nested
  authority flags are rejected.
- Task 3 package/artifact/registry tests passed 30 tests; the combined M4
  Task 1-3, blob, repository, query-index, and architecture regression passed
  110 tests in system Temp. No project Skill was installed and no real research
  canonical record was written.

## Task 4: Review-Gated Project-Local Installation

**Files:**
- Modify: `brain/v5/project_skill_packages.py`
- Modify: `brain/v5/project_skill_contracts.py`
- Modify: `brain/v5/domain_skill_shims.py`
- Modify: `brain/v5/skill_models.py`
- Modify: `brain/v5/record_family_registry.py`
- Create: `brain/v5/skill_install_transactions.py`
- Create: `brain/v5/skill_validation_execution.py`
- Create: `tests/test_v5_project_skill_install.py`
- Create: `tests/test_v5_project_skill_rollback.py`
- Create: `tests/test_v5_skill_validation_execution.py`

**Interfaces:**
- Produces: `SkillInstallPlanRecord`, `SkillInstallIntentRecord`,
  `SkillInstallReceiptRecord`, `SkillRollbackPlanRecord`,
  `SkillRollbackReceiptRecord`,
  `SkillValidationExecutionRequest`
- Adds families: `skill_install_plans`, `skill_install_intents`,
  `skill_install_receipts`, `skill_rollback_plans`, `skill_rollback_receipts`
- Produces: `build_skill_install_plan(ws, proposal_ref, target_root, hosts) -> SkillInstallPlanRecord`
- Produces: `apply_skill_install_plan(ws, plan_ref, checkpoint_ref, *, actor) -> SkillInstallReceiptRecord`
- Produces: `build_skill_rollback_plan` and `apply_skill_rollback_plan`
- Produces: `resume_skill_install_intent` and `recover_skill_install_intent`

- [ ] **Step 1: Write failing no-checkpoint/no-install tests**

Missing, pending, rejected, wrong-action, wrong-target, wrong-package-hash,
wrong-diff-hash, wrong subject/request hash, expired, or replayed checkpoints
must leave every target byte unchanged.

- [ ] **Step 2: Constrain install targets**

Install only below an explicit project root in dedicated paths such as
`.agents/skills/aitp-generated/<skill-name>`. Resolve every target and reject
traversal, symlink escape, external-skill overwrite, and user-global targets
unless separately approved by an explicit future policy.

All domain-skill shim writes use this path. Legacy `apply=True` is preview-only
or returns `checkpoint_required`; arbitrary absolute `output_root`, overwrite
flags, or direct host-shim writes cannot bypass target and approval validation.

- [ ] **Step 3: Bind approval to exact plan**

Checkpoint action is `install_aitp_skill` or `overwrite_aitp_skill`; metadata
contains package hash, diff hash, target root/path, hosts, and existing version.
It also binds the exact validation-command digest, executor policy, network
policy, writable roots, timeout, and environment allowlist. Any changed byte or
execution policy invalidates approval.

- [ ] **Step 4: Materialize atomically and verify readback**

Persist a hash-bound install intent before filesystem mutation. Write package to
a sibling temporary directory, verify file hashes and policy, atomically replace
only after checks, read back every hash, then persist an immutable receipt. If
receipt persistence fails, restore the before-image and leave a
`compensated` intent when restore/readback succeeds; only compensation failure
leaves `recovery_required`. Intent id is deterministic from plan/checkpoint/
target and transitions exactly `prepared -> materialized -> completed` or
`prepared|materialized -> compensated|recovery_required`. Resume/recover
revalidates target and before/after hashes, completes a missing receipt or
compensates deterministically, and never reuses approval for changed bytes.
Built-in declarative no-network validators may run
in restricted staging. M4 never executes arbitrary project/package code;
such commands become a separate M2 high-risk request and must return a typed
`BoundExecutionReceipt` with pinned ToolRun and ValidationResult refs before a
policy requiring them can pass. Reject traversal,
junction/symlink escape, undeclared writes, network/secret access, timeout, and
post-approval mutation. Receipt records paths/hosts/hash/version/checkpoint and
before/rollback hashes. Host shims point to the same canonical package bytes.

- [ ] **Step 5: Preserve external domain shims**

Existing external Skills remain discovery adapters. An overlap result may
propose an extension/patch but cannot overwrite the external package.

- [ ] **Step 5a: Enforce version and rollback semantics**

`(skill_id, semantic_version)` maps to one immutable package hash. Same hash and
target reinstall is idempotent; same version/different hash fails; upgrades are
monotonic; downgrade and rollback require action-specific hash-bound checkpoints.
Rollback installs a previously pinned package through the same intent/readback/
receipt transaction and never deletes prior history. Rollback itself is a
canonical `SkillRollbackPlanRecord` with expected current/target package hashes,
before-image, target, diff, and checkpoint binding.

- [ ] **Step 6: Run install/security/rollback tests and commit**

Include malicious package fixtures for command substitution, traversal,
symlink/junction escape, undeclared executable, environment-secret access,
network attempt, timeout, post-approval command mutation, and validation code
that tries to alter the staged package, direct domain-shim apply, receipt-write
failure, same-version collision, and rollback drift. Every fixture must leave
target bytes unchanged; arbitrary commands are not executed in this Gate even
when present in a package.

Commit message: `v5: require reviewed project skill installs`.

## Task 5: Applicability, Usage, And Patch Loop

**Files:**
- Create: `brain/v5/skill_applicability.py`
- Create: `brain/v5/skill_usage.py`
- Create: `tests/test_v5_skill_applicability.py`
- Create: `tests/test_v5_skill_usage.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/record_family_registry.py`
- Modify: `brain/v5/execution_models.py`

**Interfaces:**
- Produces: `SkillUsageRecord`, `SkillPatchProposalRecord`
- Adds families: `skill_usage_records`, `skill_patch_proposals`
- Produces: `match_applicable_skills(ws, request) -> SkillApplicabilityResult`
- Produces: `record_skill_usage(ws, record, *, actor) -> WriteResult`
- Produces: `build_skill_patch_proposal(ws, usage_refs) -> SkillPatchProposalRecord`

- [ ] **Step 1: Write failing selector tests**

Match domain, task, software, repository, code path/symbol, physics object,
formula, parameter, environment/cluster, focus ref, topic/program, required
inputs, and exclusions. Return selector-level reasons and confidence; never use
claim trust as an applicability shortcut.

- [ ] **Step 2: Separate derived matching from reviewed overrides**

Default matches are derived and orientation-only. A canonical override requires
a reviewed relation/checkpoint with scope, reason, expiry, and source refs.

- [ ] **Step 3: Record exact use**

Usage contains skill id/version/package hash, session/topic/focus, consuming
tool run/baseline, selected selectors, parameters, outcome, validations,
failure refs, created time, and `can_update_claim_trust=False`. ToolRun and
ExecutionBaseline store the usage ref. Skill package, run, baseline, validation,
and failure dependencies are pinned by ref/content hash.

- [ ] **Step 4: Build evidence-backed patch proposals**

New validated success may clarify steps; validated failure may add a stop rule
or boundary; changed software/code may update selectors. Proposal records exact
old/new versions, diff, source uses, validations/failures, package hash, and
review status. No patch applies from this function.
Harness Feedback cases are inadmissible patch evidence and cannot call this
builder.

- [ ] **Step 5: Reuse the same install checkpoint path for patch application**

Patch approval action is `apply_aitp_skill_patch` and binds old/new package
hashes, diff, and target. Readback/rollback rules match installation.

- [ ] **Step 6: Run applicability/usage/patch/execution tests and commit**

Commit message: `v5: track skill applicability and exact use`.

## Task 6: Skill Facade And M4 Acceptance

**Files:**
- Create: `brain/v5/mcp_skills.py`
- Create: `brain/v5/cli_skills.py`
- Create: `brain/v5/skill_surface_contracts.py`
- Create: `tests/test_v5_skill_facade.py`
- Create: `tests/test_v5_gate4_skill_e2e.py`
- Create: `docs/superpowers/progress/2026-07-10-aitp-gate-4-release-audit.md`
- Modify: `brain/v5/capability_registry_data.py`
- Modify: `brain/v5/capability_surface_contracts.py`
- Modify: `brain/v5/public_surfaces.py`
- Modify: `brain/v5/mcp_tools.py`
- Modify: `brain/v5/cli.py`
- Modify: `brain/v5/context_compiler.py`
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-07-09-aitp-final-research-lifecycle-roadmap.md`

- [ ] **Step 1: Register distill/readiness/preview/plan/apply/match/use/patch capabilities**

Distill/readiness/preview/match are read or candidate operations; proposal,
install, usage, and patch records have precise runtime/kernel effects. Compact
startup exposes applicable names/versions/refs only, never all Skill bodies.
Register deep public validators, pre-tool/checkpoint policies, CLI/MCP parity,
and compact visibility for install, rollback, validation-request, match, use,
and patch operations. Loader files receive only focused-module imports.

- [ ] **Step 2: Add LibRPA procedural vertical acceptance**

Use two independent validated LibRPA runs plus a failure case to produce a
candidate/readiness report/package preview. Reject install without approval,
approve exact hash/diff/target, install project-locally, invoke it on a later
run, and record exact usage.

- [ ] **Step 3: Add conceptual-exclusion acceptance**

A QFT definition, derivation, and speculative insight remain knowledge records
and cannot produce a package even when repeated in many sessions.

- [ ] **Step 4: Run M0-M4, security, staged-tree, and real-store audits**

Capability/family drift is zero, architecture limits unchanged, old records
readable, install tests cannot escape the project, and no package operation
changes scientific trust.

- [ ] **Step 5: Update docs, release audit, and commit**

Commit message: `v5: complete M4 reviewed skill lifecycle`.

## M4 Completion Checklist

- [ ] Only procedural validated workflows enter Skill distillation.
- [ ] Every candidate traces to topics, runs, artifacts, validations, failures, and boundaries.
- [ ] Readiness requires independent uses or a typed expert exception.
- [ ] Package preview is complete, host-neutral, versioned, and content-addressed.
- [ ] Approved package bytes are pinned as an immutable artifact and
  deterministically reconstruct to the same hash.
- [ ] Install/overwrite/patch cannot occur without exact hash/diff/target approval.
- [ ] Domain shims, rollback, downgrade, and reinstall use the same transaction
  and cannot bypass project-root/checkpoint policy.
- [ ] Generated validation code has no ambient execution authority; command and
  executor policy are separately hash/checkpoint bound.
- [ ] Generated Skills remain inside a dedicated project-local namespace.
- [ ] Applicable skill names/versions are discoverable without loading full bodies.
- [ ] Actual use records exact version/hash and consuming run/baseline.
- [ ] Same id/version cannot map to different bytes; rollback is explicit and
  history preserving.
- [ ] External Skills remain independent discovery adapters.
- [ ] No Skill operation transfers or updates claim trust.
