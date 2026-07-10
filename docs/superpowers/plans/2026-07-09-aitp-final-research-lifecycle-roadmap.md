# AITP Final Research Operating Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing AITP v5 protocol into a fast, trustworthy research operating memory for real theoretical-physics work, with quiet autonomous capture, reproducible execution memory, grounded knowledge and speculative insight, reviewed skill compilation, and bounded host context.

**Architecture:** Preserve one Markdown-backed typed Research Graph Kernel as the canonical store. Add a unified record/repository/query foundation, then build lifecycle, execution, knowledge, skill, and host-control planes as typed records plus disposable indexed projections. No RAG, summary, context, skill, hook, or cross-topic relation may directly mutate claim trust.

**Tech Stack:** Python 3, dataclasses, Markdown plus YAML frontmatter, PyYAML, FastMCP, pytest, PowerShell-compatible CLI and host adapters, deterministic file-backed indexes with optional derived retrieval backends.

## Global Constraints

- Canonical research and process state remains typed Markdown plus YAML frontmatter.
- Existing record ids and exact refs remain readable through compatibility adapters.
- Canonical writes are append/revision based; different content may not silently overwrite an existing id.
- RAG, summaries, context packs, resume cards, skills, hooks, and dashboards are not scientific truth sources.
- Cross-topic workflow reuse is allowed; cross-topic claim-trust transfer is forbidden.
- Automatic capture is limited to objective process state and explicitly unreviewed candidates.
- Grounded knowledge, reviewed insight, L2 promotion, claim-trust mutation, and skill installation preserve their stated review gates.
- Active claims are never rebound automatically.
- Startup context is bounded, coverage-declared, and progressively expandable.
- Existing user changes in a dirty worktree are preserved and never reverted as cleanup.
- Each Gate receives its own detailed TDD implementation plan before code changes begin.
- Each Gate ends with focused tests, architecture checks, docs, migration notes, and an independently reviewable commit series.

---

## 1. Authority And Scope

This roadmap is the authoritative successor to the earlier lifecycle-only task
ordering in this file. It implements the approved architecture in:

- `docs/superpowers/specs/2026-07-10-aitp-final-research-operating-memory-design.md`

It incorporates and re-baselines useful work from:

- `docs/superpowers/plans/2026-06-12-theory-curated-rag-general-layer.md`
- `docs/superpowers/plans/2026-07-08-real-topic-harness-feedback.md`
- `docs/superpowers/specs/2026-07-08-real-topic-harness-feedback-design.md`
- `docs/superpowers/specs/2026-06-19-record-lifecycle-design.md`
- `docs/superpowers/plans/2026-05-18-aitp-v5-full-implementation-roadmap.md`
- `docs/superpowers/plans/2026-04-24-witten-perspective-knowledge-design.md`

The previous lifecycle tasks are not discarded. They are moved behind the
foundation required to make them correct and fast on the real store.

## 2. Verified Baseline

The 2026-07-10 read-only audit established this baseline:

- the real canonical research store contains about 7,235 registry Markdown
  records, 39 observed registry families, and 87 sessions;
- focused roadmap-relevant tests produced 110 passes and two architecture
  failures;
- 39 source modules exceed the current architecture size limits;
- representative large modules include `mcp_tools.py`, `process_graph.py`,
  `codex_facade.py`, and `cli.py`;
- the full test suite collected 1,218 tests but did not finish inside ten
  minutes, so no full-suite pass claim exists;
- on the real store, relation-map construction took about 16.4 seconds,
  minimal Codex entry about 37.5 seconds, and context-pack construction about
  43.8 seconds;
- `store.write_record` can overwrite a path and tolerant list reads can silently
  omit malformed records;
- registry family maps differ across paths, inventory, record refs, lifecycle,
  process graph, timeline, and recording navigation;
- the deployed keyword router can inject all topic `MEMORY.md` content;
- current curated RAG is a trust-neutral lexical fixture;
- current skill shims are useful discovery adapters, while automatic skill
  distillation, review, installation, usage, and patching are incomplete;
- the existing NiO harness-feedback code is a useful fixture but is too
  case-specific for production runtime.

These measurements are acceptance inputs, not estimates.

## 3. User-Facing Product Contract

| Research moment | AITP behavior | User-visible result | Boundary |
|---|---|---|---|
| First relevant turn | Resolve program/topic/focus and query indexed state. | Small resume, current boundary, applicable skills, exact expansion handles. | No full topic-memory injection. |
| Normal theory or code discussion | Expand only the required process, knowledge, execution, or source lane. | Relevant prior work without AITP maintenance ceremony. | Context declares checked and unchecked scope. |
| Source, code, tool, HPC, or artifact event | Capture exact objective process state when idempotent. | Usually silent; visible through closeout or explicit audit. | Process capture has no claim-trust effect. |
| Definition, formula, mapping, derivation, interpretation, or insight appears | Stage and coalesce a semantic candidate. | One milestone review batch. | No automatic canonical scientific promotion. |
| Expensive run or major conclusion is pending | Run recall, prerequisites, and validation/trust checks. | Coverage, gaps, and valid next action. | Incomplete recall cannot support an exhaustive claim. |
| Session closeout | Persist process closeout and candidate batch; compile a resume card. | Next session starts from useful memory. | Closeout updates process state, not claim trust. |
| Workflow repeats successfully | Draft a procedural skill candidate and readiness report. | Reviewable package and applicability preview. | No automatic install or overwrite. |
| AITP friction is observed | Write one generic problem dossier. | Human-reviewable harness issue. | Research runtime does not author an optimization plan. |

## 4. Gate Dependency Graph

```text
Gate 0  Data, Query, Performance, Architecture Foundation
  |
  v
Gate 1  Scope, Session Lifecycle, Recall, Context Recovery
  |
  +------------+
  v            v
Gate 2         Gate 3
Execution      Knowledge / Insight / RAG
  |            |
  +------v-----+
         Gate 4  Skill Compilation And Use
             |
             v
         Gate 5  Autonomous Host Integration And Feedback
             |
             v
         Gate 6  Real Research End-To-End Acceptance
```

Gate 2 and Gate 3 may be developed as separate branches after Gate 1, but Gate
4 consumes both and may not complete before both pass.

## 5. Mapping From The Previous Roadmap

| Previous task | New location | Change |
|---|---|---|
| Full runtime file audit | Gate 0.1 | Becomes generated capability/family/file inventory with CI drift checks. |
| Multi-topic scope and focus | Gate 1.1 | Adds polymorphic focus refs and record-level bridges. |
| Closeout, resume, context coverage | Gates 1.2-1.4 | Uses one indexed query/context contract and correct persistent-record flags. |
| Deep recall audit | Gate 1.3 | Adds index generation, read errors, excluded candidates, and non-exhaustive language. |
| Pending recording queue | Gate 1.5 | Replaced by runtime staging plus one durable coalesced candidate batch. |
| Run-dir extractor and monitor | Gates 2.2-2.3 | Generalized to local/remote compute intake and execution maturity. |
| Skill distillation, install, applicability | Gate 4 | Procedural-only candidates, typed checkpoint, host-neutral package, usage refs. |
| Harness feedback registry | Gate 5.3 | Replaced by one Markdown-backed problem-dossier family. |
| Lifecycle MCP protocol | Gates 1.6 and 5.2 | Facade-first exposure plus generated capability registry. |
| Deferred theory knowledge boundary | Gate 3 | Split into immediate schema/retrieval implementation and advanced discovery after acceptance. |
| End-to-end lifecycle test | Gate 6 | Expanded to LibRPA/HPC, QFT/QG, new software, and multi-topic isolation. |

## 6. Gate 0: Data, Query, Performance, And Architecture Foundation

**Detailed plan:** `docs/superpowers/plans/2026-07-10-aitp-gate-0-foundation.md`

**Gate outcome:** Every canonical family is centrally registered, writes are
safe and diagnosable, indexed queries replace repeated whole-store scans, compact
entry meets latency budgets, host injection is bounded, and architecture tests
are green without relaxing limits.

### Task 0.1: Generate A Complete Capability, Family, And File Audit

**Files:**
- Create: `brain/v5/runtime_audit.py`
- Create: `brain/v5/runtime_audit_contracts.py`
- Create: `tests/test_v5_runtime_audit.py`
- Create: `docs/superpowers/progress/2026-07-10-aitp-runtime-capability-audit.md`
- Modify: `brain/v5/workspace_inventory.py`

**Interfaces:**
- Produces: `build_runtime_capability_audit(repo_root: Path) -> dict[str, Any]`
- Produces: generated lists of source files, actual registry directories,
  dataclasses, writers, readers, MCP/CLI surfaces, compact visibility, and tests.

- [ ] Inventory every `brain/v5`, host hook, and `test_v5_*` file.
- [ ] Detect used-but-unregistered and registered-but-unused families.
- [ ] Detect writers missing exact-ref, inventory, timeline, graph, lifecycle, or
  recording coverage.
- [ ] Detect capabilities missing MCP/CLI/bridge/compact declarations.
- [ ] Persist a reviewable report and fail CI on unexplained drift.
- [ ] Verify the current real-store family count and record the audit watermark.

### Task 0.2: Add RecordEnvelope And RecordFamilySpec

**Files:**
- Create: `brain/v5/record_envelope.py`
- Create: `brain/v5/record_family_registry.py`
- Create: `brain/v5/record_family_contracts.py`
- Create: `tests/test_v5_record_family_registry.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/paths.py`
- Modify: `brain/v5/record_refs.py`
- Modify: `brain/v5/workspace_inventory.py`
- Modify: `brain/v5/lifecycle_events.py`

**Interfaces:**
- Produces: `RecordEnvelope`
- Produces: `RecordFamilySpec`
- Produces: `record_family_specs() -> dict[str, RecordFamilySpec]`
- Produces: `validate_record_family_registry() -> dict[str, Any]`

- [x] Add schema/version/actor/revision/hash/lifecycle/trust-effect envelope
  contracts without rewriting existing records.
- [x] Register every actual canonical family and memory-entry location.
- [x] Generate layout directories and exact-ref aliases from one registry.
- [x] Reject a writable family that lacks exact-ref and inventory support.
- [x] Preserve schema-v1 readers through compatibility adapters.
- [x] Add a migration report for envelope fields absent from existing records.
- [x] Reserve `record_content_hash` for repository integrity so domain hashes,
  especially `SourceAssetRecord.content_hash`, remain scientific payload.

### Task 0.3: Introduce RecordRepository

**Files:**
- Create: `brain/v5/record_repository.py`
- Create: `brain/v5/record_repository_contracts.py`
- Create: `tests/test_v5_record_repository.py`
- Modify: `brain/v5/store.py`
- Modify: `brain/v5/markdown.py`
- Modify: `brain/v5/paths.py`
- Modify: `brain/v5/references.py`

**Interfaces:**
- Produces: `RecordRepository.write(record, *, body: str, policy: WritePolicy) -> WriteResult`
- Produces: `RecordRepository.read(ref: str) -> ReadResult`
- Produces: `RecordRepository.list(family: str, query: RecordQuery) -> RecordReadReport`

- [x] Make identical same-id writes idempotent.
- [x] Reject different same-id content unless revision/supersession is explicit.
- [x] Validate family schema and typed-ref syntax before atomic write.
- [x] Implement actual lock or compare-and-swap protection.
- [x] Report malformed records with path and error instead of silently omitting
  them from canonical reads.
- [ ] Limit tolerant reads to named legacy migration operations.
- [x] Migrate one low-risk writer family first and prove compatibility.

### Task 0.4: Build Generation-Stamped Index And Unified Query Layer

**Files:**
- Create: `brain/v5/query_index.py`
- Create: `brain/v5/query_index_contracts.py`
- Create: `brain/v5/research_retrieval.py`
- Create: `brain/v5/retrieval_audit.py`
- Create: `tests/test_v5_query_index.py`
- Create: `tests/test_v5_research_retrieval.py`
- Modify: `brain/v5/paths.py`
- Modify: `brain/v5/workspace.py`

**Interfaces:**
- Produces: `build_query_index(ws: WorkspacePaths) -> IndexBuildReport`
- Produces: `query_records(ws, query: ResearchQuery) -> RetrievalResult`
- Produces: `exact_expand(ws, refs: list[str], *, limit: int) -> RetrievalResult`

- [x] Index record envelope fields, ids, scopes, source refs, selected text,
  lifecycle, and family-specific fields.
- [x] Store canonical watermark, manifest and component hashes, generation, build time, counts,
  and malformed-record diagnostics.
- [x] Implement exact, metadata-filtered, and deterministic lexical retrieval.
- [x] Return checked families, read errors, truncation, and excluded candidates.
- [x] Mark indexes stale after canonical file-state changes.
- [x] Prohibit exhaustive "none found" claims from stale or partial results.
- [x] Benchmark index build and representative queries on the real store.

### Task 0.5: Move Context Builders Onto The Query Layer

**Files:**
- Create: `brain/v5/context_compiler.py`
- Create: `brain/v5/context_compiler_contracts.py`
- Create: `tests/test_v5_context_compiler.py`
- Modify: `brain/v5/context_pack.py`
- Modify: `brain/v5/objective_graph.py`
- Modify: `brain/v5/research_distillation.py`
- Modify: `brain/v5/claim_relation_map.py`
- Modify: `brain/v5/research_timeline.py`
- Modify: `brain/v5/codex_facade.py`

**Interfaces:**
- Produces: `compile_research_context(ws, request: ContextRequest) -> ContextBundle`
- Produces compact coverage header and exact expansion handles.

- [x] Stop recursive context builders from independently scanning the store.
- [x] Add byte/token budgets in addition to line budgets.
- [x] Add paginated `record_refs` expansion to the compact facade.
- [x] Preserve active-claim trust scope while allowing orientation-only focus
  and related-topic cards.
- [x] Add read-error and stale-index behavior to context contracts.
- [x] Meet warm/cold latency budgets on a versioned 10,000-record fixture.

### Task 0.6: Replace Unbounded Keyword Injection

**Files:**
- Modify: `deploy/hooks/aitp-keyword-router.py`
- Modify: `tests/test_aitp_pm_deploy_surfaces.py`
- Modify: `brain/v5/topic_status.py`
- Modify: `brain/v5/workspace_refresh.py`
- Create: `tests/test_v5_context_injection_budget.py`

**Interfaces:**
- Produces a bounded route hint containing topic ids/titles and facade entrypoint,
  not full topic memories.

- [ ] Remove loading and injection of all topic `MEMORY.md` bodies.
- [ ] Fix mojibake keyword literals and test UTF-8 input.
- [ ] Require topic/focus selection through the compact facade.
- [ ] Test maximum bytes/tokens and multi-topic isolation.
- [ ] Keep generated startup files orientation-only and consistent with compact
  context.

### Task 0.7: Add CapabilitySpec And Restore Architecture Boundaries

**Files:**
- Create: `brain/v5/capability_registry.py`
- Create: `brain/v5/capability_registry_contracts.py`
- Create: `tests/test_v5_capability_registry.py`
- Modify: `brain/v5/mcp_tools.py`
- Modify: `brain/v5/public_surfaces.py`
- Modify: `brain/v5/runtime_entrypoint_catalog.py`
- Modify: `brain/v5/runtime_bridge_targets.py`
- Modify: `brain/v5/codex_facade.py`
- Modify: `brain/v5/cli.py`
- Modify: `tests/test_v5_architecture_boundaries.py`

**Interfaces:**
- Produces: `CapabilitySpec`
- Produces: `capability_specs() -> dict[str, CapabilitySpec]`
- Produces generated MCP/CLI/public/bridge/compact validation catalogs.

- [ ] Register current capabilities before adding new lifecycle operations.
- [ ] Split oversized modules by existing responsibility boundaries while
  preserving public imports.
- [ ] Keep compact Codex exposure intentionally small.
- [ ] Make missing or duplicate host exposure a registry validation failure.
- [ ] Restore all architecture tests without increasing line limits.
- [ ] Split CI into focused lanes and record a scheduled full-suite command.

### Gate 0 Acceptance

- [ ] All existing schema-v1 records remain readable.
- [ ] Every actual registry family is registered and exact-expandable.
- [ ] Canonical read errors are visible and block exhaustive recall claims.
- [ ] Same-id conflicting writes are rejected.
- [ ] Minimal entry warm p95 is under 1 second and cold p95 under 3 seconds on
  the 10,000-record fixture.
- [ ] Normal context expansion warm p95 is under 2 seconds.
- [ ] No startup hook injects full topic memories.
- [ ] Architecture tests pass without relaxed limits.
- [ ] Gate 0 migration and rollback notes are documented.

## 7. Gate 1: Scope, Lifecycle, Recall, And Context Recovery

**Detailed plan:** `docs/superpowers/plans/2026-07-10-aitp-gate-1-lifecycle-context.md`

**Gate outcome:** A real session resumes quickly with explicit focus and coverage,
records durable moments through one review batch, and closes without trust
leakage or forced claim rebinding.

### Task 1.1: Research Programs, Focus Sets, And Record-Level Bridges

**Files:**
- Create: `brain/v5/research_scope.py`
- Create: `brain/v5/research_scope_contracts.py`
- Create: `tests/test_v5_research_scope.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/active_claim_focus.py`

**Interfaces:**
- Produces: `ResearchProgramRecord`
- Produces: `SessionFocusSetRecord`
- Produces: `CrossTopicRelationRecord`

- [ ] Keep `SessionBinding` single-topic and add sidecar focus.
- [ ] Support question, claim, route, work package, source set, code change, and
  run campaign focus refs.
- [ ] Require source/target typed refs and explicit revalidation boundary for
  cross-topic relations.
- [ ] Enforce `claim_trust_transfer=forbidden` in writers and consumers.
- [ ] Test related, excluded, ambiguous, and stale focus scopes.

### Task 1.2: Canonical Closeout And Derived Resume

**Files:**
- Create: `brain/v5/session_lifecycle.py`
- Create: `brain/v5/session_lifecycle_contracts.py`
- Create: `brain/v5/session_resume.py`
- Create: `tests/test_v5_session_lifecycle.py`
- Modify: `brain/v5/quiet_checkpoint.py`
- Modify: `brain/v5/closeout_completeness.py`
- Modify: `brain/v5/topic_status.py`
- Modify: `brain/v5/workspace_refresh.py`

**Interfaces:**
- Produces: `SessionCloseoutRecord`
- Produces: `record_session_closeout(...) -> SessionCloseoutRecord`
- Produces: `build_session_resume_card(...) -> dict[str, Any]`

- [ ] Record closeout as persistent process state with `trust_effect=none`.
- [ ] Compile resume from closeout, focus, current typed records, and coverage.
- [ ] Persist the same compact boundary to `session_start.generated.md`.
- [ ] Preserve can-say/cannot-say, failed routes, gaps, next actions, and pending
  candidate refs.
- [ ] Test no claim-trust mutation and no summary-as-evidence behavior.

### Task 1.3: Deep Recall And Coverage Certificates

**Files:**
- Create: `brain/v5/recall_audit.py`
- Create: `brain/v5/recall_audit_contracts.py`
- Create: `tests/test_v5_recall_audit.py`
- Modify: `brain/v5/context_compiler.py`
- Modify: `brain/v5/context_pack.py`

**Interfaces:**
- Produces: `RecallAuditRecord`
- Produces: `run_recall_audit(ws, request: RecallRequest) -> RecallAuditRecord`

- [ ] Persist query, scope, families, index generation, counts, errors, top-k,
  truncation, and excluded candidates.
- [ ] Add primary-topic, program/shared, and optional discovery lanes.
- [ ] Compile compact coverage headers from persisted audit facts.
- [ ] Block major-conclusion and expensive-run gates on stale/failed required
  recall.
- [ ] Test non-exhaustive wording and cross-topic trust isolation.

### Task 1.4: Coalesced Recording Candidate Batches

**Files:**
- Create: `brain/v5/recording_batches.py`
- Create: `brain/v5/recording_batch_contracts.py`
- Create: `tests/test_v5_recording_batches.py`
- Modify: `brain/v5/recording_navigator.py`
- Modify: `brain/v5/moment_policy.py`
- Modify: `brain/v5/closeout_completeness.py`

**Interfaces:**
- Produces: `RecordingCandidateBatchRecord`
- Produces: `stage_recording_candidate(...) -> StagedCandidate`
- Produces: `coalesce_recording_batch(...) -> RecordingCandidateBatchRecord`

- [ ] Store raw staging separately from durable batch records.
- [ ] Deduplicate by semantic key and source refs.
- [ ] Coalesce review at milestone/closeout.
- [ ] Prevent batches from invoking evidence, trust, skill, or install writers.
- [ ] Test expiry, supersession, rejection, and resume behavior.

### Task 1.5: Lifecycle Facade And Host-Neutral Entry Contract

**Files:**
- Create: `brain/v5/mcp_session_lifecycle.py`
- Create: `brain/v5/cli_session_lifecycle.py`
- Modify: `brain/v5/codex_facade.py`
- Modify: `brain/v5/capability_registry.py`
- Modify: `brain/v5/topic_status.py`
- Create: `tests/test_v5_lifecycle_facade.py`

**Interfaces:**
- Produces compact operations for session start, exact expand, recording batch,
  closeout plan, and closeout apply.

- [ ] Expose facade operations through CapabilitySpec.
- [ ] Keep maintenance writers on the full surface.
- [ ] Test Codex compact discovery and bridge acceptance.
- [ ] Ensure host startup and explicit facade entry compile the same context.

### Gate 1 Acceptance

- [ ] Multi-topic focus never auto-rebinds the active claim.
- [ ] Startup, topic-status, workspace-refresh, and compact-entry boundaries match.
- [ ] Recall coverage is persisted and blocks unsupported exhaustive claims.
- [ ] One closeout creates one resumable process record and at most one review
  batch by default.
- [ ] No lifecycle surface changes claim trust.

## 8. Gate 2: Reproducible Execution, HPC, And Formal Derivations

**Detailed plan:** `docs/superpowers/plans/2026-07-10-aitp-gate-2-execution-derivation.md`

**Gate outcome:** Important computations and software use can be reproduced from
exact code, scripts, parameters, environment, outputs, and validation; formal
derivations have inspectable DAG records.

### Task 2.1: ToolRecipe V2, ToolRun V2, And Execution Environment

**Files:**
- Create: `brain/v5/execution_environments.py`
- Create: `brain/v5/execution_contracts.py`
- Create: `brain/v5/execution_baselines.py`
- Create: `tests/test_v5_execution_memory.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/tools.py`
- Modify: `brain/v5/code.py`

**Interfaces:**
- Produces: `ExecutionEnvironmentRecord`
- Produces: `ExecutionBaselineRecord`
- Extends: `ToolRecipeRecord`, `ToolRunRecord`, `CodeStateRecord`

- [ ] Add recipe versions, parameter roles/schema, scripts, environment,
  failures, stop rules, validation, and applicability.
- [ ] Add structured argv, cwd, actual parameters, hashes, timestamps, outputs,
  validation refs, monitors, and skill usage to runs.
- [ ] Add diagnostic, reproducible-candidate, accepted-baseline, and superseded
  maturity states.
- [ ] Require passed validation and checkpoint for accepted baseline.
- [ ] Redact secrets before environment/argv persistence.

### Task 2.2: Generic Local And Remote Compute Intake

**Files:**
- Create: `brain/v5/compute_run_intake.py`
- Create: `brain/v5/compute_run_intake_contracts.py`
- Create: `tests/test_v5_compute_run_intake.py`
- Modify: `brain/v5/harness_feedback.py`

**Interfaces:**
- Produces: `build_compute_run_intake(...) -> dict[str, Any]`
- Consumes local paths or remote URIs, scheduler/job metadata, and collector
  manifests.

- [ ] Generalize the NiO run-dir extractor plan.
- [ ] Capture collector version, captured time, code/executable hashes, input and
  output manifests, resources, lane, and missing fields.
- [ ] Return typed prefill candidates without creating scientific evidence.
- [ ] Test local, Slurm remote, partial, missing, and failed intake.

### Task 2.3: Immutable Monitor Snapshots

**Files:**
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/harness_feedback.py`
- Create: `brain/v5/monitor_snapshots.py`
- Create: `tests/test_v5_monitor_snapshots.py`

- [ ] Extend existing `MonitorSnapshotRecord`; do not duplicate it.
- [ ] Add capture time, sequence, collector id, remote URI, and immutable id.
- [ ] Preserve scheduler state as process evidence only.
- [ ] Link snapshots to tool runs without overwriting earlier observations.

### Task 2.4: Formula-Code Relations

**Files:**
- Create: `brain/v5/formula_code_map.py`
- Create: `brain/v5/formula_code_contracts.py`
- Create: `tests/test_v5_formula_code_map.py`
- Modify: `brain/v5/physics_objects.py`

**Interfaces:**
- Produces typed relations for implementation, parameters, approximations,
  normalization, observables, and validation.

- [ ] Require code-state or exact source refs for code mappings.
- [ ] Record formula/symbol, module/function, parameter, output, and scope.
- [ ] Compile a bounded code-edit execution capsule.
- [ ] Test LibRPA Hamiltonian/sigcmat-style mappings and stale code states.

### Task 2.5: Formal Derivation Records And Legacy Migration

**Files:**
- Create: `brain/v5/derivations.py`
- Create: `brain/v5/derivation_contracts.py`
- Create: `brain/v5/derivation_migration.py`
- Create: `tests/test_v5_derivations.py`
- Create: `tests/test_v5_derivation_migration.py`

**Interfaces:**
- Produces: `DerivationChainRecord`
- Produces: `DerivationStepRecord`
- Produces: `migrate_legacy_derivation_candidates(...) -> MigrationReport`

- [ ] Represent target, assumptions, conventions, regime, dependencies, source
  anchors, checks, gaps, and status.
- [ ] Preserve inspectable derivation artifacts without storing hidden
  chain-of-thought.
- [ ] Import legacy derivation DAGs through reviewable migration reports.
- [ ] Test cycles, missing dependencies, unresolved steps, and source-local
  reconstruction.

### Gate 2 Acceptance

- [ ] A validated run can be reproduced from exact structured records.
- [ ] Dirty code without a patch is visibly non-reproducible.
- [ ] Remote partial state is not reported as completion.
- [ ] Formula-code context resolves theory, source, code, parameter, and tests.
- [ ] Derivation chains preserve assumptions and open gaps.

## 9. Gate 3: Grounded Knowledge, Speculative Insight, And Hybrid RAG

**Detailed plan:** `docs/superpowers/plans/2026-07-10-aitp-gate-3-knowledge-insight-rag.md`

**Gate outcome:** High-quality sources and accumulated research compile into
source-grounded physics knowledge plus separately labeled insights, retrieved
through auditable hybrid lanes and exposed through bounded context.

### Task 3.1: PhysicsObject And ObjectRelation Schema V2

**Files:**
- Create: `brain/v5/physics_knowledge_contracts.py`
- Create: `brain/v5/physics_knowledge_migration.py`
- Create: `tests/test_v5_physics_knowledge.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/physics_objects.py`

- [ ] Add scope, role, canonical name, aliases, expressions, symbols, framework,
  regime, assumptions, non-claims, source assertion, and review fields.
- [ ] Add typed subject/object refs, conditions, contradiction, source, status,
  and transfer policy to relations.
- [ ] Preserve legacy ids and fields through schema-v1 readers.
- [ ] Allow domain-specific vocabularies without a mandatory universal ontology.

### Task 3.2: Knowledge And Insight Candidate Pipeline

**Files:**
- Create: `brain/v5/knowledge_candidates.py`
- Create: `brain/v5/knowledge_promotion.py`
- Create: `brain/v5/insights.py`
- Create: `brain/v5/knowledge_contracts.py`
- Create: `tests/test_v5_knowledge_candidates.py`
- Create: `tests/test_v5_insights.py`
- Modify: `brain/v5/literature_source_extraction.py`
- Modify: `brain/v5/research_distillation.py`

**Interfaces:**
- Produces: `InsightRecord`
- Produces candidate extraction, diagnostics, batch review, rejection, and
  promotion operations.

- [ ] Route definitions, formulas, conventions, relations, and derivations to
  knowledge candidates.
- [ ] Route interpretation, analogy, conjecture, failed route, counterexample,
  bridge, and open direction to speculative candidates.
- [ ] Remove physics-semantic fragments from the skill path.
- [ ] Require exact grounding refs for grounded promotion.
- [ ] Keep reviewed insight non-evidence and able only to motivate research
  questions, routes, obligations, and checks.

### Task 3.3: Versioned Source Shelf And Structured Ingestion

**Files:**
- Modify: `brain/v5/curated_rag_corpus.py`
- Modify: `brain/v5/curated_rag_contracts.py`
- Modify: `brain/v5/knowledge_connector_bindings.py`
- Create: `brain/v5/source_shelf.py`
- Create: `tests/test_v5_source_shelf.py`

- [ ] Preserve source identity, URI, hash, access/license note, reader version,
  curation rationale, and local source-asset refs.
- [ ] Chunk around definitions, equations, theorem/proposition labels,
  derivation steps, figures, caveats, and bibliography anchors.
- [ ] Store equation labels, symbols, assumptions, and nearby prose as fields.
- [ ] Keep copyrighted-source handling conservative and source-local.
- [ ] Record extraction failures and stale source versions.

### Task 3.4: Hybrid Retrieval And Evaluation

**Files:**
- Create: `brain/v5/knowledge_retrieval.py`
- Create: `brain/v5/formula_retrieval.py`
- Create: `brain/v5/graph_retrieval.py`
- Create: `brain/v5/retrieval_fusion.py`
- Create: `tests/test_v5_knowledge_retrieval.py`
- Create: `tests/fixtures/v5_retrieval/`

- [ ] Implement fielded lexical/BM25-style ranking as the deterministic
  baseline.
- [ ] Add optional dense retrieval behind a disposable index interface.
- [ ] Add formula-normalized and graph-dependency retrieval.
- [ ] Fuse independent rankings and expose component scores.
- [ ] Keep grounded and speculative result lanes separate.
- [ ] Measure recall, contamination, exact-anchor recovery, convention mismatch,
  and reasoning-intensive retrieval on versioned fixtures.

### Task 3.5: Knowledge Context Slice

**Files:**
- Create: `brain/v5/knowledge_context.py`
- Create: `brain/v5/knowledge_context_contracts.py`
- Create: `tests/test_v5_knowledge_context.py`
- Modify: `brain/v5/context_compiler.py`
- Modify: `brain/v5/context_pack.py`
- Modify: `brain/v5/context_profiles.py`

- [ ] Add grounded knowledge, source anchors, derivation dependencies, and
  visibly separated insight to context profiles.
- [ ] Add QFT/QG framework, regime, convention, and speculation boundaries.
- [ ] Add exact expansion for source, equation, derivation, object, relation,
  and insight refs.
- [ ] Enforce context token budgets and retrieval coverage.

### Gate 3 Acceptance

- [ ] Grounded nodes have exact source or derivation grounding.
- [ ] Insights never appear as evidence or claim support.
- [ ] QFT/QG fixtures distinguish source results, interpretations, and
  conjectures.
- [ ] Hybrid retrieval improves target recall without hiding component scores or
  coverage.
- [ ] Deleting all derived indexes leaves canonical knowledge intact.

## 10. Gate 4: Reviewed Skill Compilation, Installation, And Use

**Detailed plan:** `docs/superpowers/plans/2026-07-10-aitp-gate-4-skills.md`

**Gate outcome:** Stable validated procedures become complete, reviewable,
host-neutral skill packages linked to their source research and actual usage.

### Task 4.1: Procedural Skill Distillation Records

**Files:**
- Create: `brain/v5/skill_distillation_records.py`
- Create: `brain/v5/skill_distillation_contracts.py`
- Create: `tests/test_v5_skill_distillation_records.py`
- Modify: `brain/v5/research_distillation.py`

- [ ] Persist procedural candidates only.
- [ ] Capture stabilized steps, parameters, inputs, outputs, stop rules,
  failures, validation, source records, scope, and transfer boundary.
- [ ] Reject conceptual-only and source-summary candidates.
- [ ] Aggregate independent executions without transferring claim trust.

### Task 4.2: Skill Readiness

**Files:**
- Create: `brain/v5/skill_readiness.py`
- Create: `brain/v5/skill_readiness_contracts.py`
- Create: `tests/test_v5_skill_readiness.py`

- [ ] Require two independent validated uses or one validated narrow use plus a
  typed expert exception.
- [ ] Require relevant failure/negative coverage, stable boundary, and executable
  validation fixture.
- [ ] Detect overlap and duplication with installed/external skills.
- [ ] Persist readiness reasons and missing requirements.

### Task 4.3: Host-Neutral Skill Package And Review-Gated Install

**Files:**
- Create: `brain/v5/project_skill_packages.py`
- Create: `brain/v5/project_skill_contracts.py`
- Create: `tests/test_v5_project_skill_packages.py`
- Modify: `brain/v5/domain_skill_shims.py`

- [ ] Build complete package previews with manifest, provenance, references,
  scripts/templates when required, tests, version, and content hash.
- [ ] Use a dedicated AITP-generated namespace.
- [ ] Bind install/overwrite approval to a typed human checkpoint, hash, target,
  and diff.
- [ ] Preserve external domain shims as discovery adapters.
- [ ] Materialize host-specific shims without changing canonical skill content.

### Task 4.4: Applicability, Usage, And Patch Loop

**Files:**
- Create: `brain/v5/skill_applicability.py`
- Create: `brain/v5/skill_usage.py`
- Create: `tests/test_v5_skill_applicability.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/harness_feedback.py`

- [ ] Derive applicability from domain/task/software/repository/code-path/
  physics-object/focus selectors.
- [ ] Store canonical applicability only for reviewed overrides.
- [ ] Record skill id/version usage on tool runs and execution baselines.
- [ ] Generate patch proposals from new validated success, failure, or boundary
  evidence.
- [ ] Require review before patch application.

### Gate 4 Acceptance

- [ ] No conceptual knowledge enters a skill package as a substitute for graph
  refs.
- [ ] A skill can be traced to source topics, runs, artifacts, validations, and
  checkpoints.
- [ ] An applicable skill is discoverable at session start without loading every
  full skill body.
- [ ] Skill installation and overwrite cannot occur without a typed approval.
- [ ] Actual use records the exact skill version.

## 11. Gate 5: Autonomous Research Moments, Hosts, And Feedback

**Detailed plan:** `docs/superpowers/plans/2026-07-10-aitp-gate-5-autonomous-hosts.md`

**Gate outcome:** AITP behaves as a quiet assistant inside real host sessions,
captures objective process state, stages semantic candidates, exposes relevant
skills/context, and records its own friction without taking engineering authority.

### Task 5.1: Research Moment Controller

**Files:**
- Create: `brain/v5/research_moments.py`
- Create: `brain/v5/research_moment_contracts.py`
- Create: `tests/test_v5_research_moments.py`
- Modify: `brain/v5/moment_policy.py`
- Modify: `brain/v5/recording_navigator.py`

- [ ] Map logical research events to ignore, auto-capture, candidate, review,
  checkpoint, or block decisions.
- [ ] Include reason codes, minimum refs, dedup key, expiry, and verification.
- [ ] Skip low-value tool noise and recursive semantic-tool capture.
- [ ] Test objective auto-writes separately from scientific promotion.

### Task 5.2: Real Host Lifecycle Integration

**Files:**
- Modify: `hooks/aitp_v5_claude_hook.py`
- Modify: `hooks/aitp_v5_kimi_hook.py`
- Modify: `brain/v5/hook_codex_install.py`
- Modify: `brain/v5/hook_protocol_contracts.py`
- Modify: `brain/v5/host_readiness.py`
- Modify: `brain/v5/hook_smoke_coverage.py`
- Modify: `brain/v5/codex_facade.py`
- Create: `brain/v5/context_injection_events.py`
- Create: `tests/test_v5_real_host_lifecycle.py`

- [ ] Map native hooks to host-neutral research events.
- [ ] Use first relevant prompt as ResearchTurnStart when SessionStart is absent.
- [ ] Inject only bounded context fingerprints/refs and selected content.
- [ ] Persist injection audits without full context duplication.
- [ ] Prove hooks cannot write trusted evidence, promote memory, install skills,
  or mutate claim trust.
- [ ] Quarantine legacy paths that inject stale stage guidance or full memories.

### Task 5.3: One Generic Harness Feedback Dossier

**Files:**
- Create: `brain/v5/harness_feedback_cases.py`
- Create: `brain/v5/harness_feedback_case_contracts.py`
- Create: `tests/test_v5_harness_feedback_cases.py`
- Modify: `brain/v5/harness_feedback.py`
- Modify: `tests/test_v5_harness_feedback.py`

**Interfaces:**
- Produces: `HarnessFeedbackCaseRecord`
- Produces one formatted Markdown file per problem.

- [ ] Store problem type, observed friction, expected/actual behavior, impact,
  source refs, proposed direction, status, and reviewer.
- [ ] Keep `produces_harness_optimization_plan=false` and
  `can_install_skill=false`.
- [ ] Move NiO-specific content into fixtures/examples.
- [ ] Do not create separate friction/workflow/schema/automation/proposal
  registry families.
- [ ] Aggregate repeated cases in a derived review view.

### Gate 5 Acceptance

- [ ] A normal research session can start, retrieve, work, capture, review, and
  close without manual AITP file editing.
- [ ] Objective capture is idempotent and low-noise.
- [ ] Semantic candidates remain review gated.
- [ ] Host context stays within budget and is traceable to exact refs.
- [ ] Harness feedback produces only a reviewable problem dossier.

## 12. Gate 6: Real Research End-To-End Acceptance

**Detailed plan:** `docs/superpowers/plans/2026-07-10-aitp-gate-6-e2e-release.md`

**Gate outcome:** The full architecture is proven on realistic research journeys,
migrates the existing store without trust inflation, and is documented for real
users and maintainers.

### Task 6.1: LibRPA/HPC And Code-Modification Journey

**Files:**
- Create: `tests/test_v5_e2e_librpa_research_memory.py`
- Create: `tests/fixtures/v5_e2e/librpa/`

- [ ] Recover focus, formula-code map, accepted recipe/baseline, failure history,
  exact script/commit/parameters, and applicable skill.
- [ ] Capture a diagnostic remote run and monitor snapshots.
- [ ] Validate a reproducible candidate and accept a baseline through checkpoint.
- [ ] Generate a skill patch candidate after a new failure without applying it.

### Task 6.2: QFT/Quantum-Gravity Literature And Derivation Journey

**Files:**
- Create: `tests/test_v5_e2e_qft_qg_knowledge.py`
- Create: `tests/fixtures/v5_e2e/qft_qg/`

- [ ] Ingest a paired source set with exact anchors and conventions.
- [ ] Build grounded objects, relations, and a derivation chain.
- [ ] Record a cross-paper interpretation and speculative insight separately.
- [ ] Retrieve compact context with framework/regime/speculation boundaries.
- [ ] Prove no retrieval or insight path changes claim trust.

### Task 6.3: New Software Onboarding Journey

**Files:**
- Create: `tests/test_v5_e2e_new_software.py`
- Create: `tests/fixtures/v5_e2e/new_software/`

- [ ] Start without an existing recipe or skill.
- [ ] Capture source/docs, environment, diagnostic run, parameters, and failure.
- [ ] Produce a validated reproducible recipe and accepted baseline.
- [ ] Produce a reviewable procedural skill candidate.

### Task 6.4: Multi-Topic Isolation And Discovery Journey

**Files:**
- Create: `tests/test_v5_e2e_multi_topic_isolation.py`

- [ ] Reuse a workflow and shared grounded knowledge across related topics.
- [ ] Keep topic-local interpretations and insights scoped.
- [ ] Require explicit bridge and target revalidation.
- [ ] Prove claim trust never transfers.

### Task 6.5: Real-Store Migration And Performance Acceptance

**Files:**
- Create: `brain/v5/release_audit.py`
- Create: `tests/test_v5_release_audit.py`
- Create: `docs/superpowers/progress/aitp-final-release-audit.md`

- [ ] Run a read-only pre-migration audit of the real store.
- [ ] Build indexes and report malformed records without rewriting them.
- [ ] Run compatibility, focused, architecture, host, and E2E suites.
- [ ] Record cold/warm performance distributions and context budgets.
- [ ] Verify no record became more trusted through migration.
- [ ] Record rollback and index-rebuild procedures.

### Task 6.6: Documentation And Installation Contract

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_MEMORY.md`
- Modify: `docs/AITP_RESEARCH_BRAIN_ROADMAP.md`
- Modify: `docs/AITP_SPEC.md`
- Modify: `docs/record-lifecycle.md`
- Modify: `docs/INSTALL_CODEX.md`

- [ ] Document the final product model and real research rhythm.
- [ ] Document canonical versus derived state.
- [ ] Document automatic capture and human-gate matrix.
- [ ] Document knowledge/insight, execution maturity, and skill boundaries.
- [ ] Document host startup, exact expansion, recovery, and troubleshooting.
- [ ] Keep AGENTS.md and CLAUDE.md as thin project-memory shims.

### Gate 6 Acceptance

- [ ] All four real journeys pass.
- [ ] Performance budgets pass on the versioned large fixture.
- [ ] Real-store migration audit has no unexplained read loss or trust inflation.
- [ ] Targeted CI lanes and scheduled full-suite instructions are green.
- [ ] README, spec, roadmap, install docs, and project memory agree.

## 13. Cross-Gate Testing Commands

Use the bundled workspace Python when the system Python lacks project
dependencies. Use a writable explicit `--basetemp` on this Windows workspace.

Focused commands grow by Gate:

```powershell
python -m pytest tests\test_v5_record_family_registry.py tests\test_v5_record_repository.py tests\test_v5_query_index.py -q -p no:cacheprovider
python -m pytest tests\test_v5_context_compiler.py tests\test_v5_architecture_boundaries.py -q -p no:cacheprovider
python -m pytest tests\test_v5_research_scope.py tests\test_v5_session_lifecycle.py tests\test_v5_recall_audit.py -q -p no:cacheprovider
python -m pytest tests\test_v5_execution_memory.py tests\test_v5_compute_run_intake.py tests\test_v5_derivations.py -q -p no:cacheprovider
python -m pytest tests\test_v5_physics_knowledge.py tests\test_v5_knowledge_retrieval.py tests\test_v5_knowledge_context.py -q -p no:cacheprovider
python -m pytest tests\test_v5_skill_readiness.py tests\test_v5_project_skill_packages.py tests\test_v5_skill_applicability.py -q -p no:cacheprovider
python -m pytest tests\test_v5_research_moments.py tests\test_v5_real_host_lifecycle.py tests\test_v5_harness_feedback_cases.py -q -p no:cacheprovider
python -m pytest tests\test_v5_e2e_librpa_research_memory.py tests\test_v5_e2e_qft_qg_knowledge.py tests\test_v5_e2e_new_software.py tests\test_v5_e2e_multi_topic_isolation.py -q -p no:cacheprovider
```

Each detailed Gate plan records the exact temporary directory, expected failing
test, expected passing test, and commit boundary for every task.

## 14. Commit And Review Policy

- One independently testable task per commit series.
- Documentation and migration notes ship with the task they describe.
- Do not mix unrelated cleanup into a Gate commit.
- Review kernel/trust boundaries before performance or UX review.
- Review data migration before enabling automatic capture.
- Review skill package diffs before installation tests.
- Do not mark a Gate complete while required sessions or test commands remain
  running.

## 15. Stop Conditions

Stop the current Gate and fix the foundation when any of these occurs:

- a canonical record becomes unreachable by exact ref;
- a query hides malformed records or claims exhaustive coverage from partial
  state;
- a migration changes trust semantics;
- automatic capture writes scientific promotion rather than a candidate;
- cross-topic context transfers claim trust;
- a context path exceeds budget or falls back to unbounded whole-store scans;
- a skill installs or overwrites without a hash-bound checkpoint;
- a host hook becomes a truth source;
- architecture tests are made green by weakening their limits;
- real-store compatibility cannot be demonstrated read-only.

## 16. Final Definition Of Done

The goal is complete only when AITP can enter a real theoretical-physics
conversation quickly; recover precise prior state without flooding context;
quietly capture objective research events; present one reviewable batch of
semantic candidates at natural milestones; preserve source, formula, code,
parameter, environment, HPC, artifact, validation, and failure provenance;
separate grounded knowledge from speculative insight; compile repeated validated
procedures into reviewed versioned skills; expose the correct context and skill
to a later session; and pass the LibRPA/HPC, QFT/QG, new-software, and multi-topic
end-to-end journeys without any path that silently changes scientific trust.
