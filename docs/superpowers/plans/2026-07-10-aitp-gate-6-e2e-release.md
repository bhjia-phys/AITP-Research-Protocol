# AITP M6 End-To-End Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the complete AITP research operating memory on realistic computational/theoretical physics journeys, migrate the real store without read loss or trust inflation, and publish one coherent operational/documentation contract.

**Architecture:** Four versioned fixture journeys exercise the same public lifecycle, execution, knowledge, Skill, host, and trust APIs used in real sessions. They are deterministic regression evidence, not substitutes for live acceptance. Each domain journey also has a read-only real-store or approved real-artifact probe; a configured remote/software smoke is required where the objective names external behavior. A generated release audit compares canonical content/trust before and after additive migration, verifies disposable indexes and performance, and records exact tests/host availability/rollback. Documentation is updated only from verified behavior.

**Tech Stack:** Python 3.12, pytest versioned fixtures, Markdown/YAML canonical stores, JSON manifests, SHA-256 audits, named CI lanes, real-store read-only probes.

## Global Constraints

- M0-M5 must be green and committed before M6 acceptance begins.
- E2E fixtures contain no secrets, private cluster credentials, copyrighted full texts, or hidden model reasoning.
- Fixture success cannot be reported as real-domain success. Each vertical report
  labels fixture, real-store, archived-real-artifact, and live-external evidence
  separately.
- Journey assertions distinguish proved, conditional, finite-evidence, diagnostic, and open-gap states.
- Real-store migration starts read-only and writes only additive approved schema/index state.
- Derived index/context/cache deletion must not remove canonical research memory.
- No migration may increase claim confidence, validation status, evidence support, baseline maturity, insight review, or Skill approval.
- Full suite and slow host/adapter lanes run to completion before release claims.
- Missing hosts/services are reported unavailable, not passed.
- Mandatory LibRPA/HPC, QFT/QG, and new-software probe status must be
  machine-readable `passed`; `skipped`, `unavailable`, stale, unhashed, or
  fixture-only evidence blocks release.
- Real-store writes require a hash-bound migration plan/checkpoint, per-record
  compare-and-swap, backup manifest, immutable apply receipt, and executable
  rollback plan/receipt.
- Performance reports include distributions, hardware/store/fixture version, cold/warm method, and context size.
- README, spec, roadmap, install docs, record lifecycle, and project memory must agree.
- Final release status comes from a contracted readiness evaluator, never from
  rendered prose or a green fixture lane alone.

## Test Protocol

Every task records expected RED/GREEN commands using unique writable external
temp roots. Fixture, archived-real-artifact, real-store, and live-external
receipts remain separate. Skips and unavailable dependencies are preserved as
blocking inputs for mandatory probes rather than converted to passing tests.

---

## Task 1: LibRPA/HPC And Code-Modification Journey

**Files:**
- Create: `tests/test_v5_e2e_librpa_research_memory.py`
- Create: `tests/fixtures/v5_e2e/librpa/manifest.json`
- Create: `tests/fixtures/v5_e2e/librpa/collector_manifest.json`
- Create: `tests/fixtures/v5_e2e/librpa/formula_code_links.json`

- [ ] **Step 1: Seed exact prior research state**

Include topic/session/focus, formula and convention objects, exact code commit and
patch, environment/executable hashes, recipe, accepted baseline, known failure,
validation, and approved applicable Skill. Every fixture file has a version and
SHA-256 in the journey manifest.

- [ ] **Step 2: Test startup recovery**

First turn retrieves focus, formula-code relation, script/commit/parameters,
failure history, baseline, and Skill name/version within budget. Full Skill body
and unrelated topics are absent; exact expansion handles are present.

- [ ] **Step 3: Capture diagnostic remote run**

Consume a Slurm collector manifest, write exact diagnostic process records and
immutable monitor snapshots, and keep queued/running/partial states separate
from completion, validation, evidence, and baseline acceptance.

- [ ] **Step 4: Validate and accept one reproducible candidate**

Require output manifest, exact code/environment/recipe, passed validation, and
acceptance checkpoint. Assert dirty code without patch remains ineligible.

- [ ] **Step 5: Generate but do not apply a Skill patch**

A new validated failure produces a boundary/stop-rule proposal tied to exact
usage/version/failure refs. Installed Skill bytes remain unchanged without a
new hash-bound checkpoint.

- [ ] **Step 6: Run the real LibRPA/HPC acceptance probe**

Read an existing LibRPA topic/session from the canonical theory store and an
approved real collector manifest or configured cluster collector. Verify exact
script, commit/patch, parameters, environment, scheduler/job provenance,
artifacts, validation boundary, and current Skill applicability without
rewriting canonical records. A synthetic Slurm fixture alone cannot satisfy
this step. If neither live access nor an approved hash-pinned real manifest is
available, M6 remains incomplete and reports the missing evidence.
Write a `VerticalProbeReceipt(kind="librpa_hpc")` containing source/topic,
collector/artifact hashes, checked fields, timestamp, status, and blockers.

## Task 2: QFT/Quantum-Gravity Knowledge And Derivation Journey

**Files:**
- Create: `tests/test_v5_e2e_qft_qg_knowledge.py`
- Create: `tests/fixtures/v5_e2e/qft_qg/manifest.json`
- Create: `tests/fixtures/v5_e2e/qft_qg/source_a.md`
- Create: `tests/fixtures/v5_e2e/qft_qg/source_b.md`
- Create: `tests/fixtures/v5_e2e/qft_qg/relevance.json`

- [ ] **Step 1: Discover and ingest a paired source set**

Start from a persisted knowledge gap and incomplete recall audit. Issue one
budgeted connector request, preserve query/result/error coverage, and prove
search snippets cannot become source refs. Then acquire short test-owned source
excerpts with hashes and exact section/equation anchors, different conventions,
one compatible result, one caveat, and one contradiction. Build source shelf
generation and extraction candidates.

- [ ] **Step 2: Review grounded knowledge and derivation**

Promote source-backed objects/relations plus a derivation chain with assumptions,
conventions, dependency steps, local checks, and an open gap. No hidden
chain-of-thought field or free-form private reasoning is accepted.

- [ ] **Step 3: Keep interpretation and conjecture separate**

Record a reviewed cross-paper interpretation and a speculative insight with
counterevidence/falsifiers. Neither appears in grounded/evidence lanes or changes
claim trust.

- [ ] **Step 4: Test hybrid retrieval and context**

Concept, formula, and dependency queries recover correct framework/regime/
convention anchors with component scores and bounded context. Wrong-framework
contamination and stale/missing source cases fail declared thresholds.

- [ ] **Step 5: Run the real QFT/QG source-memory probe**

Use hash-pinned source assets and exact locations already present in the real
theory store (or explicitly approved local papers/notes). Recover one grounded
result, one convention boundary, one derivation dependency, and one speculative
insight separately. Test-owned excerpts prove mechanics but cannot satisfy this
real-source step.
Write a `VerticalProbeReceipt(kind="qft_qg")` with pinned source/location hashes,
retrieval/reconstruction checks, status, and blockers.

## Task 3: New Software Onboarding Journey

**Files:**
- Create: `tests/test_v5_e2e_new_software.py`
- Create: `tests/fixtures/v5_e2e/new_software/manifest.json`
- Create: `tests/fixtures/v5_e2e/new_software/docs_excerpt.md`
- Create: `tests/fixtures/v5_e2e/new_software/run_manifests.json`

- [ ] **Step 1: Start with no recipe, baseline, or Skill**

Startup reports these as gaps rather than synthesizing prior experience. Capture
source/docs identity, exact environment, diagnostic command/parameters, and
first failure.

- [ ] **Step 2: Build a reproducible recipe**

Record parameter roles, scripts, inputs/outputs, stop rules, recovery, code/
executable hashes, environment, validation fixture, and applicability boundary.

- [ ] **Step 3: Accept baseline through checkpoint**

One successful run becomes a reproducible candidate, passes validation, and is
accepted only after exact checkpoint approval.

- [ ] **Step 4: Produce a reviewable narrow Skill candidate**

One validated narrow use plus an expert-exception checkpoint may pass readiness.
Build package preview but do not install unless a separate install checkpoint is
present. Conceptual docs remain graph refs, not copied knowledge in `SKILL.md`.

- [ ] **Step 5: Run one real, disposable software onboarding smoke**

Select a small locally available research utility or explicitly approved test
binary, capture its actual version/executable hash/environment/docs, run a
bounded diagnostic command, validate its real output, and reconstruct the run
from records in a clean temporary workspace. A mocked executable cannot satisfy
this step; unavailable software leaves the Gate incomplete rather than passed.
Write a `VerticalProbeReceipt(kind="new_software")` with executable/docs/output
hashes, clean-replay result, status, and blockers.

## Task 4: Multi-Topic Isolation And Discovery Journey

**Files:**
- Create: `tests/test_v5_e2e_multi_topic_isolation.py`
- Create: `tests/fixtures/v5_e2e/multi_topic/manifest.json`

- [ ] **Step 1: Seed related and unrelated topics**

Use one research program, two related topics, and one lexically similar unrelated
topic. Add reviewed shared grounded knowledge, topic-local interpretations, one
workflow Skill, and one pending cross-topic bridge.

- [ ] **Step 2: Test ordered retrieval lanes**

Primary topic runs first, program/shared second, optional discovery last.
Excluded/unrelated candidates remain visible in coverage but absent from
injected context.

- [ ] **Step 3: Test reuse versus trust transfer**

The reviewed workflow and shared definition may orient the target topic. A
topic-local claim, insight, derivation conclusion, or baseline cannot support
the target without explicit bridge and target-side revalidation.

- [ ] **Step 4: Prove session/claim isolation**

Focus sidecars never rebind active claims. Closeout/resume for each topic retains
its own can/cannot-say, gaps, candidates, and execution state. Every rendered
boundary item retains its proved/conditional/finite-evidence/open-gap class and
exact refs; a bare summary string is rejected from the can-say lane.

## Task 5: Generated Release Audit And Real-Store Migration

**Files:**
- Create: `brain/v5/release_audit.py`
- Create: `brain/v5/release_audit_contracts.py`
- Create: `brain/v5/release_readiness.py`
- Create: `brain/v5/mcp_release.py`
- Create: `brain/v5/cli_release.py`
- Create: `brain/v5/release_surface_contracts.py`
- Create: `brain/v5/migration_transactions.py`
- Create: `brain/v5/migration_transaction_contracts.py`
- Create: `tests/test_v5_release_audit.py`
- Create: `tests/test_v5_release_readiness.py`
- Create: `tests/test_v5_migration_transactions.py`
- Modify: `brain/v5/capability_registry_data.py`
- Modify: `brain/v5/capability_surface_contracts.py`
- Modify: `brain/v5/public_surfaces.py`
- Modify: `brain/v5/pretool_policy.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/record_family_registry.py`
- Modify: `brain/v5/record_refs.py`
- Modify: `brain/v5/lifecycle_events.py`
- Create: `docs/superpowers/progress/aitp-final-release-audit.md`

**Interfaces:**
- Produces: `capture_release_baseline(repo_root, topics_root) -> ReleaseBaseline`
- Produces: `compare_release_state(before, after) -> ReleaseAudit`
- Produces: `render_release_audit(audit) -> str`
- Produces: `VerticalProbeReceipt`, `ReleaseReadinessDecision`, and
  `evaluate_release_readiness(audit, probe_receipts, test_receipts)`
- Produces: `MigrationPlanRecord`, `MigrationApplyReceiptRecord`,
  `MigrationRollbackPlan`, and `MigrationRollbackReceiptRecord`
- Adds families: `migration_plans`, `migration_apply_receipts`,
  `migration_rollback_receipts`
- Generated release artifact paths:
  `.aitp/release/receipts/<kind>/<receipt-hash>.json` and
  `.aitp/release/decisions/<decision-hash>.json`

- [ ] **Step 1: Write failing synthetic migration audit tests**

Detect missing/unreadable refs, changed canonical payload hashes, family/count
drift, trust-field changes, lifecycle changes, accepted baseline/Skill approval
changes, stale indexes, context budget failures, and unexplained new writes.

Add deep public-surface, CLI/MCP, capability, and pre-tool tests for baseline
capture, probe receipt validation, readiness evaluation, migration plan/apply/
rollback, and recovery. Migration writes are full-surface only and require exact
checkpoint/policy approval; rendered audit/readiness views are read-only.

- [ ] **Step 2: Implement canonical/trust baseline capture**

Record repo commit, schema/registry/capability versions, all canonical relative
paths and hashes, envelope/read status, family counts, exact refs, sessions/
topics, trust-sensitive fields, index generations, and host availability. Raw
scientific bodies remain local and are not copied into the report.

- [ ] **Step 3: Implement transactional migration plan/dry-run/apply/rollback**

Plan binds before-watermark, every target ref/path and expected content hash,
proposed additive bytes/revisions/index writes, tool/schema version, backup/
archive before-images, dry-run diff hash, and required checkpoint action. Apply
requires an exact matching checkpoint, uses per-record compare-and-swap, is
restartable/idempotent, and writes an immutable receipt. Drift stops before the
affected write. Rollback plan restores only archived before-images from this
apply, rejects records changed afterward, writes a receipt, and never relies on
documentation prose. Compare before/after and fail on read loss, unexplained
hash change, or trust inflation.

- [ ] **Step 4: Build/rebuild all disposable indexes**

Delete/rebuild metadata, lexical, knowledge, formula, graph, and optional dense
indexes; verify canonical hashes unchanged and exact results preserved. Exercise
the base-plus-delta lifecycle explicitly: write one closeout and prove immediate
resume visibility, delete/corrupt the delta and observe explicit scoped stale
diagnostics with exact canonical recovery, repair/rebuild it, and prove the same
record and coverage return. Persisting a recall audit must not invalidate the
unchanged scientific families it checked.

- [ ] **Step 5: Measure performance distributions**

Record cold and at least 20 warm samples for startup, normal context, exact
expand, knowledge query, Skill match, and closeout/resume. Report p50/p95/max,
bytes/tokens, store count, fixture version, machine/runtime, and pass/fail gates.

- [ ] **Step 6: Run real store read-only first, then approved migration**

The canonical theory-topic store is audited without writes. Any malformed or
unmigratable record blocks release until classified and reviewed. Never convert
an unreadable record into absence.

- [ ] **Step 7: Evaluate fail-closed release readiness**

Normalize fixture/test/host/migration/performance receipts and hash-pinned real
probe receipts. Require `passed` for mandatory `librpa_hpc`, `qft_qg`, and
`new_software` probes plus all required lanes and migration checks. A skip,
unavailable system, stale source, missing hash, fixture-only result, failed
rollback drill, or prose-only report returns `ready=False` with exact blockers.
Persist receipts and decisions as content-addressed generated release artifacts
at the declared paths; they are audit inputs, not research truth. Validate file
hash and input fingerprint before use. Freshness is input-based: LibRPA/HPC
binds topic/collector/artifact hashes (plus an explicit age limit only for live
scheduler state), QFT/QG binds source/location and relevant family/shelf hashes,
and new software binds executable/environment/docs/output hashes and clean
replay. Any changed input makes the receipt stale regardless of timestamp.
Render Markdown only from the validated decision.

## Task 6: Full Test And Host Release Matrix

**Files:**
- Modify: `scripts/run_v5_test_lanes.py`
- Modify: `.github/workflows/v5-test-lanes.yml`
- Create: `tests/test_v5_release_matrix.py`

- [ ] **Step 1: Add M1-M6 named lanes**

Keep foundation/compatibility/slow-adapter; add lifecycle, execution,
knowledge, skills, `security-install`, hosts, migration, performance-smoke, and
e2e lanes. Every declared test path exists and full suite remains rooted at
`tests/`.

- [ ] **Step 2: Run every focused lane**

Record command, commit, environment, count, failures, skips, and duration.
Resolve all product failures; classify unavailable external hosts explicitly.

- [ ] **Step 3: Run slow adapter and full suite to completion**

No timeout-based success claim. Scheduled full suite includes versioned
performance acceptance. Local permission/infrastructure failures are reported
separately and rerun in a writable environment.

- [ ] **Step 4: Run real host smoke matrix**

Codex, Claude, and Kimi smokes execute only when installed. Verify process,
trace delta, bounded injection receipt, objective capture, semantic staging, and
forbidden-writer guards.

Host availability may be optional, but the three objective-mandated vertical
probe receipts are not. Their unavailable/skipped status remains a release
blocker in `ReleaseReadinessDecision` even if pytest marks an environment-specific
smoke skipped.

## Task 7: Documentation And Installation Contract

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_MEMORY.md`
- Modify: `docs/AITP_RESEARCH_BRAIN_ROADMAP.md`
- Modify: `docs/AITP_SPEC.md`
- Modify: `docs/record-lifecycle.md`
- Modify: `docs/INSTALL_CODEX.md`
- Modify: `docs/superpowers/plans/2026-07-09-aitp-final-research-lifecycle-roadmap.md`

- [ ] **Step 1: Document final product and research rhythm**

Cover first-turn recall, sidecar focus, progressive expansion, objective capture,
semantic review batches, closeout/resume, knowledge/insight, execution maturity,
reviewed Skills, host behavior, Harness Feedback, and exact trust boundaries.

- [ ] **Step 2: Document canonical/derived/runtime layout**

List every family/path, writer authority, lifecycle/revision rule, index rebuild,
backup/rollback, malformed-read behavior, and migration procedure.

- [ ] **Step 3: Document install and troubleshooting**

Cover project-local topics root, MCP/Skill/hook install, restart, status/doctor,
index status/rebuild, context coverage, host readiness, missing sessions,
malformed records, stale code/source, checkpoint failures, and uninstall.

- [ ] **Step 4: Reconcile all authoritative docs**

`README`, final spec/roadmap, AITP spec, lifecycle doc, install doc, project
memory, and release audit must use the same names, gates, commands, and current
implementation status. Keep AGENTS.md/CLAUDE.md thin shims.

- [ ] **Step 5: Verify links/examples/commands and commit**

Run Markdown link/path checks, CLI `--help`, capability parity, install dry-run,
and doc command smokes. Commit message: `docs: publish final AITP operating memory`.

## Task 8: Final Review And Release Commit

- [ ] Re-read every Gate checklist against implementation and tests.
- [ ] Verify working/staged trees preserve unrelated user changes.
- [ ] Run `git diff --check`, AST/compile checks, all named lanes, slow adapter,
  full suite, E2E journeys, host smokes, and real-store release audit.
- [ ] Confirm no running sessions remain and every generated report is current.
- [ ] Review trust, migration, security/install, performance, and user workflow
  separately before release approval.
- [ ] Require `ReleaseReadinessDecision.ready=True`; no human prose override may
  convert unavailable/skipped mandatory evidence into pass.
- [ ] Commit final release audit with message `v5: complete AITP research operating memory`.

## M6 Completion Checklist

- [ ] LibRPA/HPC/code journey passes with exact reproducibility and Skill use.
- [ ] QFT/QG journey passes with grounded/insight/derivation separation.
- [ ] New-software journey passes from no prior memory to reviewed candidate.
- [ ] Each named vertical has both deterministic fixture evidence and the
  required real-store/real-artifact/live smoke evidence; neither is conflated.
- [ ] Multi-topic journey permits reuse but forbids claim-trust transfer.
- [ ] Real-store audit has zero unexplained read loss or trust inflation.
- [ ] All disposable indexes rebuild without canonical changes.
- [ ] Delta loss/corruption degrades visibly, preserves exact canonical access,
  and repairs without losing the just-written lifecycle record.
- [ ] Closeout/resume preserves per-item boundary class and exact provenance;
  summary prose never becomes scientific support.
- [ ] Performance/context budgets pass with recorded distributions.
- [ ] Every focused lane, slow adapter, and full suite is green.
- [ ] Installed hosts pass real smokes; unavailable hosts are explicit.
- [ ] Mandatory real vertical receipts are all machine-validated `passed`; an
  unavailable mandatory probe leaves M6 incomplete.
- [ ] README/spec/roadmap/lifecycle/install/project memory agree.
- [ ] Rollback, backup, index rebuild, and troubleshooting are documented/tested.
- [ ] Migration plan/apply/rollback CAS and receipts pass on a disposable clone
  before any real-store apply.
