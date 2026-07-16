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
- `brain/v5/native_mcp.py` and `aitp_v5_*` are the only production research-write
  runtime. Legacy L0-L4 surfaces remain read-only by default for audit,
  interpretation, migration, and rollback.
- `AITP_LEGACY_ENABLE_WRITES=1` is limited to explicit one-time migration/debug
  fixtures. Legacy candidate, stage, promotion, and graph-write workflows are
  archived behavior and are never release-blocking acceptance targets.
- Existing user changes in a dirty worktree are preserved and never reverted as cleanup.
- Each milestone receives its own detailed TDD implementation plan before code changes begin.
- Each milestone ends with focused tests, architecture checks, docs, migration notes, and an independently reviewable commit series.

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

## 4. Milestone Dependency Graph

```text
M0  Data, Query, Performance, Architecture Foundation
  |
  v
M0.5  Complexity Reduction, Classification, Default-Surface Closure
  |
  v
V1-V4  LibRPA/HPC, QFT/QG, New Software, Multi-Topic Isolation
  |
  v
M1-M5  Retain Or Extract Only Capabilities Proven By The Verticals
  |
  v
M6  Final Real Research End-To-End Acceptance
```

The existing detailed-plan filenames retain `gate-*` as stable repository
locators. In architecture and acceptance language, these are milestones
`M0-M6`; the word "gate" is reserved for actual human, trust, validation, and
mutation checkpoints inside the research lifecycle.

The detailed M1-M5 plans are candidate implementation catalogs, not mandatory
checklists. M0.5 and the four verticals may merge, replace, postpone, or delete
their proposed classes, families, tools, and modules while preserving the
user-facing outcomes and trust invariants.

M3 depends on M2's pinned record/artifact/checkpoint and derivation
contracts. This removes ambiguous parallel ownership of source reconstruction
and hash-qualified refs. Independent retrieval experiments may branch, but no
M3 canonical writer lands before the shared M2 foundation is green.

## 5. Mapping From The Previous Roadmap

| Previous task | New location | Change |
|---|---|---|
| Full runtime file audit | M0.1 | Becomes generated capability/family/file inventory with CI drift checks. |
| Complexity and public-surface reduction | M0.5 | Classifies every capability/family/writer, shrinks the default surface, and freezes unowned abstractions before vertical work. |
| Multi-topic scope and focus | M1.1 | Adds polymorphic focus refs and record-level bridges. |
| Closeout, resume, context coverage | M1.2-M1.4 | Uses one indexed query/context contract and correct persistent-record flags. |
| Deep recall audit | M1.3 | Adds index generation, read errors, excluded candidates, and non-exhaustive language. |
| Pending recording queue | M1.5 | Replaced by runtime staging plus one durable coalesced candidate batch. |
| Run-dir extractor and monitor | M2.2-M2.3 | Generalized to local/remote compute intake and execution maturity. |
| Skill distillation, install, applicability | M4 | Procedural-only candidates, typed checkpoint, host-neutral package, usage refs. |
| Harness feedback registry | M5.3 | Replaced by one Markdown-backed problem-dossier family. |
| Lifecycle MCP protocol | M1.6 and M5.2 | Facade-first exposure plus generated capability registry. |
| Deferred theory knowledge boundary | M3 | Split into immediate schema/retrieval implementation and advanced discovery after acceptance. |
| End-to-end lifecycle test | M6 | Expanded to LibRPA/HPC, QFT/QG, new software, and multi-topic isolation. |

## 6. M0: Data, Query, Performance, And Architecture Foundation

**Detailed plan:** `docs/superpowers/plans/2026-07-10-aitp-gate-0-foundation.md`

**Milestone outcome:** Every canonical family is centrally registered, writes are
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

- [x] Inventory every `brain/v5`, host hook, and `test_v5_*` file.
- [x] Detect used-but-unregistered and registered-but-unused families.
- [x] Detect writers missing exact-ref, inventory, timeline, graph, lifecycle, or
  recording coverage.
- [x] Detect capabilities missing MCP/CLI/bridge/compact declarations.
- [x] Persist a reviewable report and fail CI on unexplained drift.
- [x] Verify the real-store family count and record the audit watermark used by
  that release probe; refresh it again during final index closure.

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
- [x] Limit tolerant reads to named legacy migration or recovery operations;
  ordinary runtime readers fail visibly on malformed canonical records.
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

- [x] Remove loading and injection of all topic `MEMORY.md` bodies.
- [x] Fix mojibake keyword literals and test UTF-8 input.
- [x] Require topic/focus selection through the compact facade.
- [x] Test maximum bytes/tokens and multi-topic isolation.
- [x] Keep generated startup files orientation-only and consistent with compact
  context.

### Task 0.7: Add CapabilitySpec And Restore Architecture Boundaries

**Files:**
- Create: `brain/v5/capability_registry.py`
- Create: `brain/v5/capability_registry_data.py`
- Create: `brain/v5/capability_registry_contracts.py`
- Create: `brain/v5/capability_surface_contracts.py`
- Create: `brain/v5/mcp_capabilities.py`
- Create: `tests/test_v5_capability_registry.py`
- Create: `docs/superpowers/progress/2026-07-10-aitp-capability-registry.md`
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

- [x] Register current capabilities before adding new lifecycle operations.
- [x] Split oversized modules by existing responsibility boundaries while
  preserving public imports.
- [x] Keep compact Codex exposure intentionally small.
- [x] Make missing or duplicate host exposure a registry validation failure.
- [x] Restore all architecture tests without increasing line limits.
- [x] Split CI into focused lanes and record a scheduled full-suite command.

### Task 0.8: Close V5 Release Isolation And Legacy Compatibility Boundaries

**Files:**
- Create: `scripts/run_v5_test_lanes.py`
- Create: `tests/test_v5_test_lanes.py`
- Create: `.github/workflows/v5-test-lanes.yml`
- Modify: `adapters/codex/SKILL.md`
- Modify: `adapters/claude-code/SKILL.md`
- Modify: `adapters/opencode/SKILL.md`
- Modify: `adapters/openclaw/SKILL.md`
- Modify: `adapters/README.md`
- Modify: `docs/AITP_SPEC.md`
- Modify: `docs/PROJECT_INDEX.md`
- Modify: `tests/test_aitp_pm_deploy_surfaces.py`
- Preserve unchanged: legacy L0-L4 candidate, stage, promotion, graph-write,
  and end-to-end implementation/tests

**Interfaces:**
- Produces blocking `foundation`, `compatibility`, `legacy-compat`,
  `slow-adapter`, and `full` v5 release lanes in system Temp.
- Defines `full` as every `test_v5_*` module plus package-manager deployment,
  legacy read/migration, flow-notebook read rendering, and write-guard tests.
- Keeps `legacy-write-archive` explicit and opt-in; it is never invoked by
  `full`, scheduled CI, milestone acceptance, or release readiness.
- Local release evidence is taken from the exact staged candidate in an
  isolated worktree so protected unrelated working-tree edits cannot alter the
  result; CI naturally runs from a clean checkout.

- [x] Clear inherited real-store and legacy-write bindings in every blocking
  lane, preserve explicit per-test bases, and isolate `Path.home()` plus
  host-specific config roots under system Temp without hiding the launching
  Python environment. Do not set one global v5 topics root across the suite.
- [x] Add a blocking compatibility lane for legacy reads, lossless migration,
  schema-v1 materialization, old-store manifests, and default write blocking.
- [x] Select legacy write-guard tests by node id so the opt-in bootstrap
  escape-hatch test remains archive-only and cannot make old writes release
  blocking.
- [x] Exclude archived L0-L4 write workflows from `full` and CI release jobs.
- [x] Revert candidate/preflight/L3-L4/promotion/legacy-graph changes that were
  introduced only to make archived write E2E tests pass.
- [x] Remove legacy MCP/stage instructions from active-looking adapter
  references, make unsupported OpenClaw lifecycle status explicit, and cover
  all four references in the blocking deployment-surface test.
- [x] Route the specification, project index, and adapter index entrypoints to
  v5, while labeling the v4 L0-L4 protocol tree as historical semantics rather
  than a production write lifecycle.
- [x] Run targeted regressions, all blocking named lanes, and the blocking full
  v5 release suite in writable system Temp.
- [ ] Optionally record the `legacy-write-archive` result as historical drift;
  failures are not defects unless they break read, migration, or write blocking.
- [x] Rebuild only the real `.aitp/indexes` projection and prove
  `canonical_before == manifest == canonical_after`.
- [x] Stage only the reviewed allowlist; exclude protected Harness Feedback,
  README, shared mixed-hunk files, real canonical records, PDFs, images, and
  temporary artifacts.

### M0 Acceptance

- [x] All existing schema-v1 records remain readable.
- [x] Every actual registry family is registered and exact-expandable.
- [x] Canonical read errors are visible and block exhaustive recall claims.
- [x] Same-id conflicting writes are rejected.
- [x] Minimal entry warm p95 is under 1 second and cold p95 under 3 seconds on
  the 10,000-record fixture.
- [x] Normal context expansion warm p95 is under 2 seconds.
- [x] No startup hook injects full topic memories.
- [x] Architecture tests pass without relaxed limits.
- [x] All blocking v5, package-manager, legacy read/migration, and write-guard
  tests pass in system Temp with inherited legacy writes disabled. No blocking
  test enables legacy writes; the escape-hatch node is archive-only.
- [x] Archived L0-L4 write workflows are absent from release acceptance and no
  production legacy state-machine change is justified solely by their result.
- [x] Rebuilding `.aitp/indexes` leaves every canonical record hash unchanged.
- [x] M0 migration and rollback notes are documented.

## 6.5. M0.5: Complexity Reduction And Vertical Re-Baselining

**Detailed design:** `docs/superpowers/specs/2026-07-11-aitp-m0-5-complexity-reduction-design.md`

**Detailed plan:** `docs/superpowers/plans/2026-07-11-aitp-m0-5-complexity-reduction-review.md`

**Milestone outcome:** Every current capability, family, writer, compatibility
surface, and logical module has explicit ownership and evidence. Codex sees the
smallest useful default surface, legacy behavior is isolated, and subsequent
implementation follows real research verticals rather than the existing
M1-M5 file lists.

### CR0: Freeze And Complete Classification

- [x] Classify all core capabilities as `core`, `vertical_extension`,
  `maintenance`, `migration`, or `soft_deprecated` with caller and removal
  evidence.
- [x] Classify all 46 record families, including 12 zero-record families and
  five `unimplemented_layout` families.
- [x] Classify the 114 currently recognized helper-call writers (111 at the M0
  baseline) into canonical,
  derived, host/runtime, migration, or shared-primitive ownership; expand the
  scanner to direct file APIs and every declared source tree before claiming
  complete writer or canonical-bypass coverage.
- [x] Add drift tests that reject unclassified capabilities, families, or
  writers and reject new entries without a vertical owner.

### CR1: Approve Compatibility And Reduce Default Exposure

- [x] Obtain an explicit compatibility decision: one-release soft deprecation
  (recommended), immediate removal, or classification-only freeze.
- [x] If soft deprecation is approved, move six hook/bridge maintenance tools
  out of compact visibility while preserving full/CLI forwarding shims.
- [x] Keep the proposed compact surface at no more than ten tools and 6,000
  schema bytes; load no unrelated legacy or migration catalog by default.
- [x] Keep installation, release diagnostics, and migration discoverable but
  absent from normal research context.

### CR2: Close Context Selection Semantics

- [x] Preserve retrieval relevance through candidate-summary selection rather
  than re-sorting solely by family/ref.
- [x] Add status/family diversity and explicit `not_shown` accounting while
  preserving `not_found`, `not_checked`, stale, partial, and read-error states.
- [x] Treat `curated_legacy_migration` route markers as visible migration
  diagnostics, not fabricated route records and not hidden errors.
- [x] Re-run LibRPA and QFT/QG real context probes against the fresh index.

### CR3: Converge Canonical Writes By Vertical

- [x] Route the first vertical's canonical writes through `RecordRepository`
  with actor, collision, revision, exact-ref, and trust-boundary tests.
- [x] Separate derived-output and host-install writers from canonical writer
  policy.
- [x] Repeat only for writers exercised by accepted verticals; maintain a
  measured remainder until canonical bypass count reaches zero.
  LibRPA, QFT/QG fixture, new-software, and multi-topic tests prove that every
  canonical byte change in their scoped journeys equals a successful
  `RecordRepository` create/revision/archive receipt. The bounded scanner keeps
  the repository-wide dynamic/native remainder explicit rather than claiming
  zero.
- [x] Do not add a generic repository-adapter framework without two completed
  verticals demonstrating the same requirement.

### CR4: Isolate Legacy Imports And Replace Touched Shards

- [x] Keep legacy support limited to read, audit, migration, schema-v1
  materialization, and write blocking.
- [x] Prevent compact native MCP from importing unrelated legacy modules.
- [x] Replace a numbered shard with a named responsibility module only when a
  real vertical touches that responsibility; preserve the public import shim
  for the compatibility window.
- [x] Track logical facade-plus-shard size and prohibit net complexity growth.

### CR5: Execute Vertical-First Retention Review

- [x] Close the minimal LibRPA/HPC and code-modification journey.
- [x] Close the minimal QFT/quantum-gravity source and open-derivation journey.
  The real paired-source probe now verifies both pinned PDF byte hashes, two
  exact equation-range anchors, one source-grounded object per paper, one
  explicitly hypothetical cross-paper relation, and one human-gated open proof
  obligation with an ordered strategy. This is the smallest honest derivation
  trace for the real topic, not a completed physics derivation or trust update.
  See `docs/superpowers/progress/2026-07-13-qft-qg-real-vertical-probe.json`.
- [x] Close new-software onboarding from no existing recipe or skill.
- [x] Prove multi-topic knowledge/workflow reuse without claim/insight/trust
  propagation.
- [x] Retain, merge, postpone, or remove M1-M5 candidate capabilities from the
  evidence of those journeys. The classification audit retains core,
  maintenance, migration, and 77 owned vertical contracts; 12 unowned vertical
  extensions are frozen without expansion during the compatibility window.

### M0.5 Acceptance

- [x] Every capability, family, and writer reported by the bounded scan policy
  has exactly one reviewed classification and owner; the policy covers direct
  file APIs rather than only named helper calls. Unbounded dynamic/native I/O
  coverage remains explicitly false and cannot support a repository-wide
  no-bypass claim.
- [x] Compact visibility meets the ten-tool, 6,000-byte, and import budgets.
- [x] No maintenance/migration tool appears in normal Codex context.
- [x] Context exposes `not_shown` and retains relevance, diversity, coverage,
  and explicit migration/read diagnostics.
- [x] The first accepted vertical has no canonical repository bypass.
- [x] Legacy writes remain blocked and archived write E2E remains non-release.
- [x] Logical module complexity is non-increasing.
- [x] The selected compatibility policy is approved and documented.

## 7. M1: Scope, Lifecycle, Recall, And Context Recovery

**Detailed plan:** `docs/superpowers/plans/2026-07-10-aitp-gate-1-lifecycle-context.md`

**Milestone outcome:** A real session resumes quickly with explicit focus and coverage,
records durable moments through one review batch, and closes without trust
leakage or forced claim rebinding.

**Status (2026-07-14): complete.** The reviewed implementation and acceptance
evidence are recorded in
`docs/superpowers/progress/2026-07-10-aitp-gate-1-release-audit.md`. The real
store migration remained read-only: it produced review candidates but wrote no
focus set, research program, closeout, recording batch, or claim-trust state.

### Task 1.0: Incremental Query Overlay And Scoped Freshness

**Files:**
- Create: `brain/v5/query_index_generation.py`
- Create: `brain/v5/query_index_locking.py`
- Create: `brain/v5/query_index_delta.py`
- Create: `brain/v5/query_index_delta_contracts.py`
- Create: `tests/test_v5_query_index_delta.py`
- Create: `tests/test_v5_query_index_concurrency.py`
- Modify: `brain/v5/query_index.py`
- Modify: `brain/v5/research_retrieval.py`
- Modify: `brain/v5/record_repository.py`

**Interfaces:**
- Produces a disposable write-through delta over the full index generation.
- Produces global and selected-family freshness/coverage tokens.
- Produces a typed projection outcome on every repository write.
- Produces explicit build/mutation leases whose OS advisory locks survive
  exceptions and release on owner death.

- [x] Publish immutable full generations through one atomic root-manifest
  pointer only after component hashes and three-way derived/canonical family
  content watermarks agree; retain conservative M0/schema-v1 reads.
- [x] Project successful repository creates/revisions into a base-bound,
  hash-verified atomic delta with fixed lock ordering, predecessor continuity,
  and durable dirty-family semantics; canonical writes remain authoritative if
  projection fails.
- [x] Overlay delta rows deterministically and compact them into a later full
  generation without rewriting canonical records or dropping writes concurrent
  with build/publication.
- [x] Require every successful v2 root publication, including ordinary rebuild,
  to publish a delta rebound/empty state bound to the new base in the same
  lease transaction.
- [x] Read root/base/delta as one retryable coherent snapshot and convert
  integrity disagreement into typed stale diagnostics.
- [x] Allow scoped exhaustive coverage only when every requested family has a
  strong content verification, not merely a fast state-token match; unscoped
  queries still require global verification.
- [x] Provide a bounded strict single-family fallback with visible diagnostics,
  never a hidden whole-store scan.
- [x] Prove a newly written closeout is immediately resumable and a newly
  persisted recall audit does not invalidate the families it just checked.

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

- [x] Keep `SessionBinding` single-topic and add sidecar focus.
- [x] Support question, claim, route, work package, source set, code change, and
  run campaign focus refs.
- [x] Require source/target typed refs and explicit revalidation boundary for
  cross-topic relations.
- [x] Enforce `claim_trust_transfer=forbidden` in writers and consumers.
- [x] Test related, excluded, ambiguous, and stale focus scopes.

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

- [x] Record closeout as persistent process state with `trust_effect=none`.
- [x] Compile resume from closeout, focus, current typed records, and coverage.
- [x] Persist the same compact boundary to `session_start.generated.md`.
- [x] Preserve can-say/cannot-say, failed routes, gaps, next actions, and pending
  candidate refs as structured items with boundary class, scope, and exact
  provenance rather than authority-bearing summary strings.
- [x] Test no claim-trust mutation and no summary-as-evidence behavior.

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

- [x] Persist query, scope, families, index generation, counts, errors, top-k,
  truncation, and excluded candidates.
- [x] Add primary-topic, program/shared, and optional discovery lanes.
- [x] Compile compact coverage headers from persisted audit facts.
- [x] Block major-conclusion and expensive-run gates on stale/failed required
  recall.
- [x] Test non-exhaustive wording and cross-topic trust isolation.

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

- [x] Store raw staging separately from durable batch records.
- [x] Deduplicate by semantic key and source refs.
- [x] Coalesce review at milestone/closeout.
- [x] Prevent batches from invoking evidence, trust, skill, or install writers.
- [x] Test expiry, supersession, rejection, and resume behavior.

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

- [x] Expose facade operations through CapabilitySpec.
- [x] Keep maintenance writers on the full surface.
- [x] Test Codex compact discovery and bridge acceptance.
- [x] Ensure host startup and explicit facade entry compile the same context.

### M1 Acceptance

- [x] Multi-topic focus never auto-rebinds the active claim.
- [x] Startup, topic-status, workspace-refresh, and compact-entry boundaries match.
- [x] Recall coverage is persisted and blocks unsupported exhaustive claims.
- [x] Lifecycle writes are immediately queryable through the delta overlay and
  unrelated process writes do not invalidate scoped scientific recall.
- [x] One closeout creates one resumable process record and at most one review
  batch by default.
- [x] No lifecycle surface changes claim trust.

## 8. M2: Reproducible Execution, HPC, And Formal Derivations

**Detailed plan:** `docs/superpowers/plans/2026-07-10-aitp-gate-2-execution-derivation.md`

**Status (2026-07-15): fixture-contract complete.** The reviewed implementation
and acceptance evidence are recorded in
`docs/superpowers/progress/2026-07-10-aitp-gate-2-release-audit.md`. Real
LibRPA/HPC operational acceptance remains a mandatory M6 probe.

**Milestone outcome:** Important computations and software use can be reproduced from
exact code, scripts, parameters, environment, outputs, and validation; formal
derivations have inspectable DAG records.

### Task 2.1: ToolRecipe V2, ToolRun V2, And Execution Environment

**Files:**
- Create: `brain/v5/execution_environments.py`
- Create: `brain/v5/execution_contracts.py`
- Create: `brain/v5/execution_baselines.py`
- Create: `brain/v5/pinned_record_refs.py`
- Create: `brain/v5/checkpoint_bindings.py`
- Create: `brain/v5/checkpoint_transactions.py`
- Create: `brain/v5/artifact_blobs.py`
- Create: `brain/v5/code_patch_manifests.py`
- Create: `brain/v5/effective_attempts.py`
- Create: `brain/v5/execution_scope_policy.py`
- Create: `brain/v5/bound_execution.py`
- Create: `brain/v5/scope_revalidation.py`
- Create: `tests/test_v5_execution_memory.py`
- Create: `tests/test_v5_execution_scope_policy.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/tools.py`
- Modify: `brain/v5/code.py`

**Interfaces:**
- Produces: `ExecutionEnvironmentRecord`
- Produces: `ExecutionBaselineRecord`
- Produces: `ArtifactBlobReceiptRecord`, `CodePatchManifestRecord`,
  `CheckpointApplicationReceiptRecord`, `ScopeRevalidationDecisionRecord`
- Produces: `ExecutionMaturityProjection`, `ExecutionScopeDecision`, and
  `BoundExecutionReceipt`
- Produces: `assess_execution_scope(ws, *, operation, consumer_scope,
  dependency_refs, revalidation_decision_refs=()) -> ExecutionScopeDecision`
- Extends: `ToolRecipeRecord`, `ToolRunRecord`, `CodeStateRecord`,
  `ArtifactRecord`, and `HumanCheckpointRecord`

- [x] Add recipe versions, parameter roles/schema, scripts, environment,
  failures, stop rules, validation, and applicability.
- [x] Add structured argv, cwd, actual parameters, hashes, timestamps, outputs,
  validation refs, monitors, and skill usage to runs.
- [x] Keep legacy bare ids readable but require typed recipe/code/environment/
  artifact/validation/monitor/skill refs for v2 reproducibility gates.
- [x] Restrict new `ToolRunRecord.recorded_maturity` writes to `diagnostic`,
  `reproducible_candidate`, or `superseded`; never write `accepted_baseline`
  into a ToolRun or its legacy `maturity` compatibility alias.
- [x] Derive `ExecutionMaturityProjection.effective_maturity`; only an active
  immutable `ExecutionBaselineRecord` may project `accepted_baseline`, with the
  ToolRun left unchanged.
- [x] Freeze a recursive `FrozenDependencyManifest` by typed
  ref/content-hash/revision, including every declared transitive edge and
  terminal blob/patch receipt; support exact archived reads and prohibit latest,
  path, URI, worktree, or tuple-based implicit lookup during replay.
- [x] Require every reproducibility-eligible `ArtifactRecord` to pin one
  `ArtifactBlobReceiptRecord` by `artifact_blob_receipt_ref` and
  `artifact_blob_receipt_hash`; require every dirty `CodeStateRecord` to pin one
  `CodePatchManifestRecord` by `patch_manifest_ref` and `patch_manifest_hash`.
  Each paired hash is the target record's `record_content_hash`, distinct from
  artifact byte hashes and patch-entry byte hashes.
- [x] Pin/resolve/rehash required local bytes or approved immutable external
  storage receipts; reference-only mutable paths cannot satisfy replay.
- [x] Make immutable `CheckpointApplicationReceiptRecord` the sole application/
  consumption fact. Its deterministic id includes action payload hash and pinned
  intent, subjects, request, and decision; its immutable payload pins those
  refs/hashes plus result, terminal status, timestamps, and errors. Only
  `status=applied` proves consumption. New checkpoint writes omit
  `consumed_by_ref`; legacy values are read-only projections, and no application
  path mutates a checkpoint again.
- [x] Require exact run/recipe/executor/output/failure-contract validation and a
  subject/request-hash-bound checkpoint for accepted baseline.
- [x] Cover staged/unstaged/deleted/binary/submodule/required-untracked bytes in
  dirty snapshots or retain `non_reproducible`.
- [x] Persist exact validation contract/run/recipe/executor/output/failure-mode
  bindings and enforce the per-family topic/program/claim scope matrix.
- [x] Implement the matrix once in `assess_execution_scope(...)`; baseline,
  context, and facade consumers call it directly and pass explicit pinned
  `ScopeRevalidationDecisionRecord` refs rather than rediscovering decisions.
- [x] Provide a registered-executor high-risk `BoundExecutionReceipt` that pins
  ToolRun, ValidationResult, and checkpoint-application receipt refs/hashes for
  later Skill validation, plus explicit target-scope revalidation records.
- [x] Register `artifact_blob_receipts`, `code_patch_manifests`,
  `checkpoint_application_receipts`, and `scope_revalidation_decisions` in
  `RecordFamilySpec`, typed-ref resolution, inventory, lifecycle/index coverage,
  and generated workspace layout before enabling their writers.
- [x] Redact secrets before environment/argv persistence.

### Task 2.2: Generic Local And Remote Compute Intake

**Files:**
- Create: `brain/v5/compute_run_intake.py`
- Create: `brain/v5/compute_run_intake_contracts.py`
- Create: `tests/test_v5_compute_run_intake.py`

**Interfaces:**
- Produces: `ComputeRunIntakeRequest`, `ComputeRunIntakeReport`
- Produces: `build_compute_run_intake(request: ComputeRunIntakeRequest) ->
  ComputeRunIntakeReport`
- Consumes local paths or remote URIs, scheduler/job metadata, and collector
  manifests.

- [x] Generalize compute intake independently; NiO is fixture data and Harness
  Feedback owns no execution/monitor behavior.
- [x] Capture collector version, captured time, code/executable hashes, input and
  output manifests, resources, lane, and missing fields.
- [x] Return typed prefill candidates without creating scientific evidence.
- [x] Test local, Slurm remote, partial, missing, and failed intake.

### Task 2.3: Immutable Monitor Snapshots

**Files:**
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/hpc_cockpit.py`
- Modify: `brain/v5/lane_contracts.py`
- Create: `brain/v5/monitor_snapshots.py`
- Create: `tests/test_v5_monitor_snapshots.py`

- [x] Extend existing `MonitorSnapshotRecord`; do not duplicate it.
- [x] Add capture time, sequence, collector id, remote URI, and immutable id.
- [x] Preserve scheduler state as process evidence only.
- [x] Link snapshots to tool runs without overwriting earlier observations.
- [x] Resolve effective attempt/supersession, latest monitor state, partial
  outputs, and final/diagnostic lane eligibility in both cockpit and baseline.

### Task 2.4: Formula-Code Relations

**Files:**
- Create: `brain/v5/formula_code_map.py`
- Create: `brain/v5/formula_code_contracts.py`
- Create: `tests/test_v5_formula_code_map.py`
- Modify: `brain/v5/physics_objects.py`

**Interfaces:**
- Produces typed relations for implementation, parameters, approximations,
  normalization, observables, and validation.

- [x] Require code-state or exact source refs for code mappings.
- [x] Record formula/symbol, module/function, parameter, output, and scope.
- [x] Compile a bounded code-edit execution capsule.
- [x] Test LibRPA Hamiltonian/sigcmat-style mappings and stale code states.

### Task 2.5: Formal Derivation Records And Legacy Migration

**Files:**
- Create: `brain/v5/derivation_models.py`
- Create: `brain/v5/derivations.py`
- Create: `brain/v5/derivation_contracts.py`
- Create: `brain/v5/derivation_migration.py`
- Create: `brain/v5/derivation_reviews.py`
- Create: `tests/test_v5_derivations.py`
- Create: `tests/test_v5_derivation_migration.py`
- Create: `tests/test_v5_derivation_reviews.py`

**Interfaces:**
- Produces: `DerivationChainRecord`
- Produces: `DerivationStepRecord`
- Produces: `DerivationReviewRecord`
- Produces: `record_derivation_review(...)`
- Produces: `supersede_derivation_review(ws, prior_review_ref, replacement, *,
  actor) -> WriteResult`
- Produces: `project_derivation_status(...) -> DerivationStatusProjection`
- Produces: `migrate_legacy_derivation_candidates(...) -> MigrationReport`

- [x] Represent target, assumptions, conventions, regime, dependencies, source
  anchors, checks, gaps, and status.
- [x] Preserve inspectable derivation artifacts without storing hidden
  chain-of-thought.
- [x] Import legacy derivation DAGs through reviewable migration reports.
- [x] Test cycles, missing dependencies, unresolved steps, and source-local
  reconstruction.
- [x] Separate `structurally_closed` from hash-bound reviewed/validated status
  and integrate derivations into source-reconstruction review.
- [x] Reject foreign-topic dependencies without explicit bridge and target-side
  revalidation.

### M2 Acceptance

- [x] A validated run can be reproduced from exact structured records.
- [x] Current-record revisions cannot change an accepted baseline's frozen
  meaning, and generic/replayed checkpoints cannot approve it.
- [x] Bare legacy ids or unhashed paths cannot satisfy reproducibility.
- [x] Dirty code without a patch is visibly non-reproducible.
- [x] Remote partial state is not reported as completion.
- [x] Formula-code context resolves theory, source, code, parameter, and tests.
- [x] Derivation chains preserve assumptions and open gaps.
- [x] M2 proves deterministic contract readiness; real LibRPA/HPC acceptance
  remains a mandatory M6 probe.

## 9. M3: Grounded Knowledge, Speculative Insight, And Hybrid RAG

**Detailed plan:** `docs/superpowers/plans/2026-07-10-aitp-gate-3-knowledge-insight-rag.md`

**Status (2026-07-16): fixture-contract complete.** The full-only knowledge
façade, QFT/QG fixture vertical, real-store index compatibility audit, and
performance evidence are recorded in
`docs/superpowers/progress/2026-07-10-aitp-gate-3-release-audit.md`. Real
formal-theory source-memory acceptance remains a mandatory M6 probe.

**Milestone outcome:** High-quality sources and accumulated research compile into
source-grounded physics knowledge plus separately labeled insights, retrieved
through auditable hybrid lanes and exposed through bounded context.

### Task 3.1: PhysicsObject And ObjectRelation Schema V2

**Files:**
- Create: `brain/v5/physics_knowledge_contracts.py`
- Create: `brain/v5/physics_assertions.py`
- Create: `brain/v5/physics_knowledge_migration.py`
- Create: `tests/test_v5_physics_knowledge.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/physics_objects.py`

- [x] Keep stable object identity separate from source/convention-specific
  `PhysicsAssertionRecord` definitions, equations, properties, and revisions.
- [x] Add typed subject/object refs, conditions, contradiction, source, status,
  and transfer policy to relations.
- [x] Preserve legacy ids and fields through schema-v1 readers.
- [x] Allow domain-specific vocabularies without a mandatory universal ontology.

### Task 3.2: Knowledge And Insight Candidate Pipeline

**Files:**
- Create: `brain/v5/knowledge_candidates.py`
- Create: `brain/v5/knowledge_promotion.py`
- Create: `brain/v5/knowledge_review.py`
- Create: `brain/v5/evidence_basis_policy.py`
- Create: `brain/v5/insights.py`
- Create: `brain/v5/knowledge_contracts.py`
- Create: `tests/test_v5_knowledge_candidates.py`
- Create: `tests/test_v5_insights.py`
- Modify: `brain/v5/literature_source_extraction.py`
- Modify: `brain/v5/research_distillation.py`
- Modify: `brain/v5/evidence.py`
- Modify: `brain/v5/pretool_policy.py`
- Modify: `brain/v5/trust_audit.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/record_family_registry.py`
- Modify: `brain/v5/record_refs.py`
- Modify: `brain/v5/lifecycle_events.py`

**Interfaces:**
- Produces: `InsightRecord`
- Produces candidate extraction, diagnostics, batch review, rejection, and
  promotion operations.

- [x] Route definitions, formulas, conventions, relations, and derivations to
  knowledge candidates.
- [x] Route interpretation, analogy, conjecture, failed route, counterexample,
  bridge, and open direction to speculative candidates.
- [x] Remove physics-semantic fragments from the skill path.
- [x] Require exact grounding refs for grounded promotion.
- [x] Keep reviewed insight non-evidence and able only to motivate research
  questions, routes, obligations, and checks.
- [x] Enforce evidence-basis admissibility in evidence write, pre-tool policy,
  trust audit, and promotion so insight/search/summary/Skill cannot be wrapped
  into claim support.
- [x] Bind per-item review to content hash and preserve revise/demote/invalidate/
  supersede history.

### Task 3.3: Versioned Source Shelf And Structured Ingestion

**Files:**
- Modify: `brain/v5/curated_rag_corpus.py`
- Modify: `brain/v5/curated_rag_contracts.py`
- Modify: `brain/v5/knowledge_connector_bindings.py`
- Create: `brain/v5/source_shelf.py`
- Create: `brain/v5/source_acquisition.py`
- Modify: `brain/v5/source_reconstruction.py`
- Modify: `brain/v5/source_reconstruction_review.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/record_family_registry.py`
- Modify: `brain/v5/record_refs.py`
- Modify: `brain/v5/lifecycle_events.py`
- Create: `tests/test_v5_source_shelf.py`

- [x] Preserve source identity, URI, hash, access/license note, reader version,
  curation rationale, and local source-asset refs.
- [x] Chunk around definitions, equations, theorem/proposition labels,
  derivation steps, figures, caveats, and bibliography anchors.
- [x] Store equation labels, symbols, assumptions, and nearby prose as fields.
- [x] Keep copyrighted-source handling conservative and source-local.
- [x] Record extraction failures and stale source versions.
- [x] Require typed acquisition allow/deny/review receipts with access/license,
  storage permission, acquired byte hash, and dedup identity; URI-only metadata
  cannot satisfy grounding.
- [x] Make source reconstruction resolve every asserted anchor to a hash-pinned
  asset/location; record presence or arbitrary labels cannot pass.
- [x] Turn persisted knowledge gaps into budgeted host/connector discovery
  requests; keep snippets and unacquired results process-only.

### Task 3.4: Hybrid Retrieval And Evaluation

**Files:**
- Create: `brain/v5/knowledge_retrieval.py`
- Create: `brain/v5/formula_retrieval.py`
- Create: `brain/v5/graph_retrieval.py`
- Create: `brain/v5/retrieval_fusion.py`
- Create: `brain/v5/knowledge_snapshot.py`
- Create: `tests/test_v5_knowledge_retrieval.py`
- Create: `tests/fixtures/v5_retrieval/`

- [x] Implement fielded lexical/BM25-style ranking as the deterministic
  baseline.
- [x] Add optional dense retrieval behind a disposable index interface.
- [x] Add formula-normalized and graph-dependency retrieval.
- [x] Fuse independent rankings and expose component scores.
- [x] Keep grounded and speculative result lanes separate.
- [x] Bind all components to one record/shelf snapshot and expose stale/dirty/
  errors, fixed tie rules, lane quotas, token allocation, and pagination.
- [x] Hard-filter incompatible framework/regime/conventions from default context;
  comparison intent uses a separate lane.
- [x] Measure recall, contamination, exact-anchor recovery, convention mismatch,
  and reasoning-intensive retrieval on versioned fixtures.

### Task 3.5: Knowledge Context Slice

**Files:**
- Create: `brain/v5/knowledge_context.py`
- Create: `brain/v5/knowledge_context_contracts.py`
- Create: `tests/test_v5_knowledge_context.py`
- Modify: `brain/v5/context_compiler.py`
- Modify: `brain/v5/context_pack.py`
- Modify: `brain/v5/context_profiles.py`

- [x] Add grounded knowledge, source anchors, derivation dependencies, and
  visibly separated insight to context profiles.
- [x] Add QFT/QG framework, regime, convention, and speculation boundaries.
- [x] Add exact expansion for source, equation, derivation, object, relation,
  and insight refs.
- [x] Enforce context token budgets and retrieval coverage.

### M3 Acceptance

- [x] Grounded nodes have exact source or derivation grounding.
- [x] Insights never appear as evidence or claim support.
- [x] Object identity/assertion lineage, acquisition policy, source
  reconstruction, and evidence admissibility are enforced end to end.
- [x] Evidence separates support basis from trace context and persists a
  payload-hash-bound policy audit.
- [x] Review revise/demote/invalidate/supersede and target-scope revalidation
  have exact records, hashes, and lifecycle behavior.
- [x] QFT/QG fixtures distinguish source results, interpretations, and
  conjectures.
- [x] Hybrid retrieval improves target recall without hiding component scores or
  coverage.
- [x] Deleting all derived indexes leaves canonical knowledge intact.
- [x] Formula/graph/dense sidecar failures degrade visibly without false
  deterministic or exhaustive claims.
- [x] M3 proves fixture-contract readiness only; real QFT/QG source-memory
  acceptance remains mandatory in M6.

## 10. M4: Reviewed Skill Compilation, Installation, And Use

**Detailed plan:** `docs/superpowers/plans/2026-07-10-aitp-gate-4-skills.md`

**Status (2026-07-16): in progress.** Tasks 4.1-4.3 are implemented, including
host-neutral package artifacts and review-gated project-local deployment,
rollback, compensation, and recovery. Applicability, exact usage, patch
feedback, facade exposure, and M4 end-to-end acceptance remain open.

**Milestone outcome:** Stable validated procedures become complete, reviewable,
host-neutral skill packages linked to their source research and actual usage.

### Task 4.1: Procedural Skill Distillation Records

**Files:**
- Create: `brain/v5/skill_distillation_records.py`
- Create: `brain/v5/skill_distillation_contracts.py`
- Create: `tests/test_v5_skill_distillation_records.py`
- Modify: `brain/v5/research_distillation.py`

- [x] Persist procedural candidates only.
- [x] Capture stabilized steps, parameters, inputs, outputs, stop rules,
  failures, validation, source records, scope, and transfer boundary.
- [x] Reject conceptual-only and source-summary candidates.
- [x] Aggregate independent executions without transferring claim trust.

### Task 4.2: Skill Readiness

**Files:**
- Create: `brain/v5/skill_readiness.py`
- Create: `brain/v5/skill_readiness_contracts.py`
- Create: `tests/test_v5_skill_readiness.py`

- [x] Require two independent validated uses or one validated narrow use plus a
  typed expert exception.
- [x] Require relevant failure/negative coverage, stable boundary, and executable
  validation fixture.
- [x] Detect overlap and duplication with installed/external skills.
- [x] Persist readiness reasons and missing requirements.

### Task 4.3: Host-Neutral Skill Package And Review-Gated Install

**Files:**
- Create: `brain/v5/project_skill_packages.py`
- Create: `brain/v5/project_skill_contracts.py`
- Create: `brain/v5/skill_install_transactions.py`
- Create: `brain/v5/skill_install_planning.py`
- Create: `brain/v5/skill_install_materialization.py`
- Create: `brain/v5/skill_install_plan_derivations.py`
- Create: `brain/v5/skill_install_plan_validation.py`
- Create: `brain/v5/skill_install_host_safety.py`
- Create: `brain/v5/skill_validation_execution.py`
- Create: `brain/v5/skill_package_artifacts.py`
- Create: `tests/test_v5_project_skill_packages.py`
- Create: `tests/test_v5_project_skill_install.py`
- Create: `tests/test_v5_project_skill_install_security.py`
- Create: `tests/test_v5_project_skill_rollback.py`
- Modify: `brain/v5/domain_skill_shims.py`

- [x] Build complete package previews with manifest, provenance, references,
  scripts/templates when required, tests, version, and content hash.
- [x] Pin exact package bytes as an immutable artifact plus renderer/template
  version; hashes alone cannot stand in for missing unreconstructable bytes.
- [x] Store a canonical sorted package-tree manifest whose files resolve through
  M2 content-addressed blob receipts; reject symlinks/special files.
- [x] Use a dedicated AITP-generated namespace.
- [x] Bind install/overwrite approval to a typed human checkpoint, hash, target,
  and diff.
- [x] Run built-in declarative validators only; arbitrary commands use a
  separate M2 high-risk execution request/receipt.
- [x] Disable external domain-shim writes until represented by the same
  project-root plan/checkpoint/receipt gate; legacy direct apply cannot bypass it.
- [x] Enforce immutable id/version/hash, idempotent reinstall, monotonic upgrade,
  separately approved downgrade, and explicit history-preserving rollback.
- [x] Persist install intent before mutation, read back exact bytes, persist an
  immutable receipt, and compensate on receipt failure.
- [x] Re-derive plan/source/target/action/policy identity on load, revalidate
  target and staging immediately before rename, and preserve the after-image
  when a damaged backup makes automatic compensation unsafe.
- [x] Model prepared/materialized/completed/compensated/recovery-required intent
  transitions and deterministic resume/recovery; rollback is an operation of the
  same canonical plan/receipt model.
- [x] Keep one host-neutral project-local installed tree; host declarations are
  receipt metadata and may not create divergent Skill copies.

### Task 4.4: Applicability, Usage, And Patch Loop

**Files:**
- Create: `brain/v5/skill_applicability.py`
- Create: `brain/v5/skill_usage.py`
- Create: `tests/test_v5_skill_applicability.py`
- Modify: `brain/v5/models.py`

- [x] Derive applicability from domain/task/software/repository/code-path/
  physics-object/focus selectors.
- [x] Store canonical applicability only for reviewed overrides.
- [x] Record skill id/version usage on tool runs and execution baselines.
- [x] Generate patch proposals from new validated success, failure, or boundary
  evidence.
- [x] Reject Harness Feedback as Skill candidate/patch evidence.
- [x] Require review before patch application.

Task 4.4 now matches only completed, byte-current project-local installs and
returns selector-level orientation reasons without loading Skill bodies. Exact
usage pins the installed receipt, proposal, package artifact, consuming run and
optional baseline, validations, failures, selectors, and parameters; run and
baseline revisions carry a trust-neutral usage backlink. Reviewed applicability
exceptions reuse expiring `ScopeRevalidationDecisionRecord` plus a verified
scope-revalidation checkpoint instead of creating a stale topic-by-Skill
matrix. Patch proposals re-prove exact historical usage and old/new package
identities, reject the Harness Feedback compatibility lane, and produce no
write outside canonical candidate storage. Applying a patch requires the same
recoverable Task 4.3 transaction with action `apply_aitp_skill_patch`, binding
the patch ref, old/new hashes, package bytes, target, diff, validators, and
receipt. Historical usage remains verifiable after upgrade while applicability
advertises only the one currently materialized version.

### M4 Acceptance

- [ ] No conceptual knowledge enters a skill package as a substitute for graph
  refs.
- [ ] A skill can be traced to source topics, runs, artifacts, validations, and
  checkpoints.
- [ ] An applicable skill is discoverable at session start without loading every
  full skill body.
- [x] Skill installation and overwrite cannot occur without a typed approval.
- [x] Domain shims, rollback, downgrade, and reinstall cannot bypass the same
  transaction and checkpoint path.
- [x] Install readback cannot implicitly execute arbitrary generated scripts.
- [ ] Actual use records the exact skill version.
- [x] Same id/version cannot map to different bytes and rollback preserves
  immutable install history.

## 11. M5: Autonomous Research Moments, Hosts, And Feedback

**Detailed plan:** `docs/superpowers/plans/2026-07-10-aitp-gate-5-autonomous-hosts.md`

**Milestone outcome:** AITP behaves as a quiet assistant inside real host sessions,
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
- [ ] Allow a persisted knowledge gap to request budgeted read-only literature
  discovery while keeping acquisition and semantic promotion separately gated.
- [ ] Skip low-value tool noise and recursive semantic-tool capture.
- [ ] Test objective auto-writes separately from scientific promotion.

### Task 5.2: Real Host Lifecycle Integration

**Files:**
- Modify: `hooks/aitp_v5_claude_hook.py`
- Modify: `hooks/aitp_v5_kimi_hook.py`
- Modify: `deploy/templates/opencode/aitp-plugin.js`
- Modify: `adapters/codex/SKILL.md`
- Modify: `adapters/claude-code/SKILL.md`
- Modify: `adapters/opencode/SKILL.md`
- Modify: `adapters/openclaw/SKILL.md`
- Modify: `docs/protocols/adapter_interface.md`
- Modify: `brain/v5/hook_codex_install.py`
- Modify: `brain/v5/hook_install_templates.py`
- Modify: `brain/v5/hook_kimi_install.py`
- Modify: `brain/v5/hook_install_audit.py`
- Modify: `brain/v5/hook_protocol_contracts.py`
- Modify: `brain/v5/host_readiness.py`
- Modify: `brain/v5/hook_smoke_coverage.py`
- Modify: `brain/v5/codex_facade.py`
- Modify: `tests/test_aitp_pm_deploy_surfaces.py`
- Create: `brain/v5/context_injection_events.py`
- Create: `tests/test_v5_real_host_lifecycle.py`

- [ ] Map native hooks to host-neutral research events.
- [ ] Use first relevant prompt as ResearchTurnStart when SessionStart is absent.
- [ ] Wire prompt-submit and stop/session-end only where supported; advertise and
  test idempotent begin-turn/closeout facade fallbacks elsewhere.
- [ ] Inject only bounded context fingerprints/refs and selected content.
- [ ] Persist injection audits without full context duplication.
- [ ] Namespace receipt/dedup identity by workspace/host/session/topic-focus/
  event/profile and enforce named 800/4000 and 1500/7500 token/byte profiles.
- [ ] Encode context receipt paths from canonical namespace SHA-256 rather than
  raw host ids; reject traversal, reserved-name, and symlink escapes.
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
- [ ] Remove legacy Skill-candidate/patch/preview/install/distillation emission
  from Harness Feedback and test every prohibited path.
- [ ] Move NiO-specific content into fixtures/examples.
- [ ] Do not create separate friction/workflow/schema/automation/proposal
  registry families.
- [ ] Aggregate repeated cases in a derived review view.

### M5 Acceptance

- [ ] A normal research session can start, retrieve, work, capture, review, and
  close without manual AITP file editing.
- [ ] Objective capture is idempotent and low-noise.
- [ ] Semantic candidates remain review gated.
- [ ] Search snippets and unacquired literature results remain process-only.
- [ ] Host context stays within budget and is traceable to exact refs.
- [ ] Harness feedback produces only a reviewable problem dossier.
- [ ] Harness feedback cannot create any Skill or automatic optimization action.

## 12. M6: Real Research End-To-End Acceptance

**Detailed plan:** `docs/superpowers/plans/2026-07-10-aitp-gate-6-e2e-release.md`

**Milestone outcome:** The full architecture is proven on realistic research journeys,
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
- [x] Repeat the journey read-only against a real LibRPA topic plus an approved
  hash-pinned real HPC collector manifest or configured collector.

### Task 6.2: QFT/Quantum-Gravity Literature And Derivation Journey

**Files:**
- Create: `tests/test_v5_e2e_qft_qg_knowledge.py`
- Create: `tests/fixtures/v5_e2e/qft_qg/`

- [x] Start from a knowledge gap, run bounded discovery, and ingest an allowed
  paired source set with exact anchors and conventions.
- [x] Build grounded objects and relations plus a minimal open derivation trace:
  exact anchors and an ordered `ProofObligationRecord.proof_strategy`. Do not
  describe this as a completed derivation or invent a full derivation ontology
  until another real vertical demonstrates that the current trace is
  insufficient.
- [x] Record the cross-paper hypothesis and speculative insight separately from
  source-grounded objects; neither is evidence.
- [x] Retrieve compact context with framework/regime/speculation boundaries.
- [x] Prove no retrieval or insight path changes claim trust.
- [x] Repeat against hash-pinned real QFT/QG source assets and exact locations;
  fixture excerpts alone are insufficient. The real probe passes with two
  source anchors, two grounded objects, one cross-source hypothesis, and one
  open proof obligation, while remaining orientation-only and trust-neutral.

### Task 6.3: New Software Onboarding Journey

**Files:**
- Create: `tests/test_v5_e2e_new_software.py`
- Create: `tests/fixtures/v5_e2e/new_software/`

- [x] Start without an existing recipe or skill.
- [x] Capture source/docs, environment, diagnostic run, parameters, and failure.
- [ ] Produce a validated reproducible recipe and accepted baseline. The recipe
  is validated; a distinct scientific-baseline acceptance checkpoint remains
  open and is not implied by Skill installation approval.
- [x] Produce a reviewable procedural skill candidate.
- [x] Onboard one real disposable local research utility and reconstruct its
  actual run; a mocked executable alone is insufficient.

### Task 6.4: Multi-Topic Isolation And Discovery Journey

**Files:**
- Create: `tests/test_v5_e2e_multi_topic_isolation.py`

- [x] Reuse a workflow and shared grounded knowledge across related topics.
- [x] Keep topic-local interpretations and insights scoped.
- [x] Require explicit bridge and target revalidation.
- [x] Prove claim trust never transfers.

### Task 6.5: Real-Store Migration And Performance Acceptance

**Files:**
- Create: `brain/v5/release_audit.py`
- Create: `brain/v5/release_readiness.py`
- Create: `brain/v5/migration_transactions.py`
- Create: `brain/v5/mcp_release.py`
- Create: `brain/v5/cli_release.py`
- Create: `tests/test_v5_release_audit.py`
- Create: `docs/superpowers/progress/aitp-final-release-audit.md`

- [ ] Run a read-only pre-migration audit of the real store.
- [ ] Build a hash-bound migration plan/checkpoint with per-record CAS, backup
  before-images, immutable apply receipt, executable rollback plan, and immutable
  rollback receipt.
- [ ] Build indexes and report malformed records without rewriting them.
- [ ] Prove full-base/delta write visibility, explicit delta-failure degradation,
  exact canonical recovery, and deterministic repair/compaction.
- [ ] Run compatibility, focused, architecture, host, and E2E suites.
- [ ] Record cold/warm performance distributions and context budgets.
- [ ] Verify no record became more trusted through migration.
- [ ] Execute rollback drill on a disposable clone; documentation alone does not
  satisfy rollback.
- [ ] Evaluate a machine-readable release decision that requires `passed` real
  LibRPA/HPC, QFT/QG, and new-software receipts; skipped/unavailable/fixture-only
  evidence blocks release.
- [ ] Store probe/readiness receipts as hash-pinned generated release artifacts
  with per-vertical input-fingerprint freshness; expose full-surface validated
  release/migration routes.

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

### M6 Acceptance

- [ ] All four real journeys pass.
- [ ] Every objective-mandated real vertical has a hash-pinned machine-validated
  `passed` receipt; unavailable leaves M6 incomplete.
- [ ] Performance budgets pass on the versioned large fixture.
- [ ] Real-store migration audit has no unexplained read loss or trust inflation.
- [ ] Delta deletion/corruption never hides canonical lifecycle records and is
  recoverable without trust or content changes.
- [ ] Targeted CI lanes and scheduled full-suite instructions are green.
- [ ] A dedicated security-install lane and transactional migration/rollback
  tests are green; migration and performance-smoke are named lanes.
- [ ] README, spec, roadmap, install docs, and project memory agree.

## 13. Cross-Milestone Testing Commands

Use the bundled workspace Python when the system Python lacks project
dependencies. Use a writable explicit `--basetemp` on this Windows workspace.

Focused commands grow by milestone:

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

Each detailed milestone plan records the exact temporary directory, expected failing
test, expected passing test, and commit boundary for every task.

## 14. Commit And Review Policy

- One independently testable task per commit series.
- Documentation and migration notes ship with the task they describe.
- Do not mix unrelated cleanup into a milestone commit.
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
