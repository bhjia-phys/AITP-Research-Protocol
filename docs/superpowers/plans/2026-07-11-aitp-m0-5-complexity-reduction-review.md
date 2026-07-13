# AITP M0.5 Complexity Reduction Review Plan

> **Status:** Approved for phased implementation under the one-release soft
> deprecation policy selected by the user on 2026-07-12. CR1 may reduce compact
> exposure while full/CLI forwarding remains available; deletion still requires
> vertical acceptance and reviewed caller evidence.

**Goal:** Reduce AITP to the smallest v5 research-memory kernel justified by
real theoretical-physics work, without losing canonical refs, migration reads,
trust boundaries, or active host compatibility.

**Design:**
`docs/superpowers/specs/2026-07-11-aitp-m0-5-complexity-reduction-design.md`

**Baseline:** The accepted M0 staged candidate has 225 core capabilities, 46
families, 111 writer candidates, 485 v5 Python files, and a 16-tool compact
surface. The primary worktree also has protected, independent Harness Feedback
changes that are not part of this plan.

## Global Constraints

- Preserve the tested M0 staged candidate until the user chooses how to commit
  or integrate it.
- Do not stage or modify protected Harness Feedback files, README user hunks,
  mixed shard user hunks, or real canonical records.
- The real store may be read and `.aitp/indexes` may be rebuilt only under the
  existing authorization; no canonical cleanup or migration apply is allowed.
- V5 is the only production write runtime.
- Legacy remains read/audit/migration/schema-v1/write-guard only.
- No M1-M6 feature expansion occurs during CR0.
- No family or capability is deleted from text-mention counts alone.
- Use TDD for every behavior change after design approval.
- Run final verification from an exact staged-only system-Temp worktree.

## Task 0: Preserve The M0 Checkpoint

**Evidence:**

- 232 staged paths;
- exact staged-only `full`: 1,160 passed, 1 skipped;
- generation 7 real index: 9,772 records, malformed 0, fresh at final probe;
- protected diff hashes:
  - mixed shards: `f4651e2355ca5e394bf2f96fed8b76b209969055`;
  - Harness Feedback/README group:
    `3c0ca5a7b2ed30e0f32d43d3d1aa0e83330823a1`.

- [ ] Confirm whether M0 should be committed as its current staged checkpoint
  before any M0.5 implementation.
- Re-audit cached/unstaged path sets before every future stage operation.
- [x] Review and explicitly authorize M0.5 planning/implementation changes
  before staging them.

## Task 1: Produce Complete Classification Manifests

**Candidate files:**

- Modify: `brain/v5/capability_registry_data.py`
- Modify: `brain/v5/capability_registry.py`
- Modify: `brain/v5/record_family_registry.py`
- Modify: `brain/v5/runtime_audit.py`
- Modify: `brain/v5/runtime_audit_contracts.py`
- Modify: `brain/v5/runtime_audit_rendering.py`
- Create: `brain/v5/writer_scan.py`
- Create: `docs/superpowers/progress/2026-07-11-aitp-m0-5-classification-audit.md`
- Modify: `tests/test_v5_capability_registry.py`
- Modify: `tests/test_v5_record_family_registry.py`
- Modify: `tests/test_v5_runtime_audit.py`

### Step 1: Add failing classification completeness tests

Require every capability and family to expose exactly one of:

- `core`
- `vertical_extension`
- `maintenance`
- `migration`
- `soft_deprecated`

Require owner/evidence/removal metadata appropriate to the classification.
Reject a new capability or family without classification and a vertical or
compatibility owner.

### Step 2: Classify all current entries

Use exact operation/family review, not prefix-only heuristics. Record:

- state effect;
- default/full/CLI visibility;
- caller or compatibility consumer;
- canonical/derived/host writer role;
- vertical owner;
- removal condition.

### Step 3: Classify all writer candidates

Extend the runtime audit to report:

- canonical record/repository writer;
- derived index/projection writer;
- host/runtime installation or configuration writer;
- migration/legacy-compatibility writer;
- shared low-level storage primitive;
- unclassified writer.

The current 111-row inventory recognizes only four named helper calls and is an
under-approximation, not proof of repository-wide writer closure. Expand the
scanner and its fixtures to cover direct `Path.write_text`, append/write
`Path.open`, JSONL helpers, copy/rename operations, SQLite mutations, and writer
calls outside `brain/`, `hooks/`, and `deploy/hooks/`. Fail CR0 while any
reported writer remains unclassified or any supported source tree lacks a
declared scan policy. Record the 47 current canonical/repository candidates and
identify which already use `RecordRepository`.

### Step 4: Generate the human review report

The report must contain all current core capabilities, 46 families, and every row from
the current writer scanner, plus summary counts and an explicit scanner-coverage
statement. It is generated evidence, not a runtime truth source. Do not call
the 111-row baseline "all writers" until the expanded scanner closes the known
direct-file API gaps.

Current status:

- [x] Classify all 228 current core capabilities and all 46 record families.
- [x] Preserve and classify all 111 legacy named-helper rows.
- [x] Add a separate direct-mutation scanner and classify all 164 current rows.
- [x] Exclude test fixtures and reject string-replace/read-open false positives.
- [x] Keep every non-v5 `brain/` mutation in archived-legacy ownership.
- [x] Explicitly bound dynamic/aliased filesystem APIs and non-literal database
  mutation gaps. The machine-readable policy reports 573/573 declared Python
  source files parsed, zero parse errors, and
  `bounded_coverage_complete=true`, while retaining
  `coverage_complete=false` for unbounded/reflection/native-I/O claims.
- [x] Add approved lifecycle metadata to the runtime registries after Policy A
  selection. `CapabilitySpec` carries the one-release compact soft-deprecation
  window/warning/removal condition for six maintenance tools, while
  `RecordFamilySpec` retains its existing lifecycle and auto-write policies.
  The reviewed 228-way M0.5 classification remains generated audit evidence,
  not a duplicated runtime truth source.

### Verification

```powershell
python -m pytest -p no:cacheprovider `
  tests/test_v5_capability_registry.py `
  tests/test_v5_record_family_registry.py `
  tests/test_v5_runtime_audit.py -q
```

## Task 2: Approve Compatibility Policy

No behavior change proceeds until one option is selected:

1. one-release soft deprecation (recommended);
2. immediate removal;
3. classification-only freeze.

The review packet must show:

- current callers found in repo, canonical records, and research workspace;
- compact/full/CLI impact;
- proposed forwarding and warning behavior;
- rollback path;
- surfaces whose caller state remains unknown.

- [x] Record the user's explicit selection in the M0.5 design status.
- [x] Convert this plan from proposed to approved for implementation.

## Task 3: Reduce Compact Exposure

**Runs only if soft deprecation or immediate removal is approved.**

**Candidate files:**

- Modify: `brain/v5/capability_registry_data.py`
- Modify: `brain/v5/capability_registry.py`
- Modify: `brain/v5/codex_facade.py` or named facade responsibility modules
- Modify: `brain/v5/native_mcp.py`
- Modify: `tests/test_v5_capability_registry.py`
- Modify: `tests/test_v5_codex_facade.py`
- Modify: `tests/test_v5_mcp_tools.py`
- Modify: `tests/test_v5_m0_release.py`

### RED

Assert that compact contains at most ten tools and 6,000 schema bytes, and that
no maintenance/migration capability is visible. Assert compact native MCP does
not import more than 120 v5 modules or five legacy modules.

### GREEN

- remove six hook/bridge maintenance tools from compact visibility;
- preserve them on full/CLI maintenance surfaces;
- load compact functions before importing the full catalog;
- keep the eight Codex facade tools plus pre-tool and trust preflight;
- retain full-surface forwarding shims during the selected compatibility
  window.

### Verification

```powershell
python -m pytest -p no:cacheprovider `
  tests/test_v5_capability_registry.py `
  tests/test_v5_codex_facade.py `
  tests/test_v5_mcp_tools.py `
  tests/test_v5_m0_release.py -q
```

Current status:

- [x] RED proved the 16-tool, 7,331-byte, full-catalog baseline.
- [x] Compact now exposes exactly ten tools and 5,945 schema bytes.
- [x] Cold compact import loads 108 v5 modules, three allowed legacy-read
  modules, and no `brain.v5.mcp_tools` full catalog.
- [x] Six maintenance tools remain on full MCP and their existing CLI routes,
  with one-release metadata and structured compact-call migration errors.
- [x] Missing surface configuration preserves the full default; blank and
  unknown values fail closed to compact.
- [x] Focused CR1 tests, foundation, compatibility, and the nine directly
  affected maintenance MCP/CLI tests pass. The complete 88-test slow-adapter
  lane exceeded its six-minute outer timeout and remains part of final full
  verification rather than being reported as passed.

## Task 4: Preserve Retrieval Rank And Add `not_shown`

**Candidate files:**

- Modify: `brain/v5/research_retrieval.py`
- Modify: `brain/v5/context_compiler.py`
- Modify: `brain/v5/context_compiler_contracts.py`
- Modify: `brain/v5/context_pack_contracts.py`
- Modify: `tests/test_v5_research_retrieval.py`
- Modify: `tests/test_v5_context_compiler.py`
- Modify: `tests/test_v5_context_pack.py`

### RED

Add tests where the most relevant code/tool/validation item would be displaced
by family/ref sorting. Require:

- retrieval order preserved within explicit failure/claim/process priorities;
- family/status diversity;
- `not_shown_count` and `not_shown_reason`;
- stale, partial, not-found, not-checked, read-error, and truncation semantics
  remain distinct;
- no trust or evidence effect.

### GREEN

Remove the final record-ref sort as the dominant tie-break. Carry retrieval
rank into summary selection and apply a small deterministic diversity policy.
Do not introduce model summarization, embeddings, or another context service.

### Real probes

Re-run:

- `qsgw-headwing-update-librpa`;
- `quantum-gravity-von-neumann`.

The LibRPA legacy route marker remains an explicit migration diagnostic unless
a reviewed compatibility rule normalizes it.

Current status:

- [x] Candidate summaries retain retrieval rank plus exact/lexical/total score;
  failure/claim/process representatives and bounded family/status diversity no
  longer use record-ref ordering as the dominant selector.
- [x] Compiler and final context pack expose additive `not_shown_count` and a
  deterministic list of `not_shown_reason` codes.
- [x] `stale`, `partial`, `not_found_refs`, `not_checked_families`,
  `read_errors`, `retrieval_truncated`, and `render_truncated` remain distinct.
- [x] Final pack candidates preserve family, status, rank, and score without
  changing evidence or trust authority.
- [x] A concurrent real-store write exposed an index snapshot race; the builder
  now refuses publication if the canonical state changes during its scan and
  leaves the previous derived files intact.
- [x] Focused query/context tests pass (38), broader context/Codex tests pass
  (44), and the compatibility lane passes (140).
- [x] Fresh generation-11/schema-v2 probes completed after more than 87 minutes
  of canonical quiescence. LibRPA compiled in 0.835 seconds with 1,229
  candidates, 12 shown, 1,215 explicitly `not_shown`, no read errors, and the missing
  `research_route:curated_legacy_migration` reported rather than fabricated.
  QFT/QG compiled in 0.687 seconds with 46 candidates, 12 shown, 32 explicitly
  `not_shown`, no read errors, and both hash-pinned paired source assets shown.
  IDF-weighted retrieval plus bounded execution/source family quotas preserve
  LibRPA code/tool/artifact provenance and QFT/QG paired-paper context. Both
  probes used the fresh index and remained orientation-only.

## Task 5: Converge The First Vertical's Canonical Writers

**First vertical:** LibRPA/HPC and code modification.

### RED

Build one end-to-end test covering:

- session/topic/claim recovery;
- source and source-asset refs;
- code state with repo/branch/commit/dirty state;
- tool recipe and tool run with environment/command/input/output;
- artifact and validation result;
- failure mode and closeout;
- collision and revision behavior;
- no trust promotion from process capture.

The test must fail if any exercised canonical write bypasses
`RecordRepository`.

### GREEN

Migrate only the underlying writers exercised by this vertical. Separate
derived cockpit/status files from canonical records. Do not rewrite unrelated
families or add a generic adapter layer.

### Verification

Run the focused writer/repository tests and the LibRPA vertical. Re-run the
runtime audit and record the remaining canonical bypass count.

Independent review must pass before this task is marked complete. In
particular, the acceptance test must prove persisted tool-run supersession
semantics, authenticated human-decision provenance, artifact compatibility,
successful repository writes rather than attempted calls, and canonical-path
mutation coverage. Repository-backed semantic writers must remain visible in
the writer inventory instead of disappearing when their low-level helper call
is removed.

Current status:

- [x] `tests/test_v5_librpa_hpc_vertical.py` snapshots every canonical root and
  equates every changed canonical path with successful repository write or
  revision-archive results.
- [x] Source/reference, code state, recipe/run, artifact, validation,
  checkpoint, and closeout writers exercised by the vertical use
  `RecordRepository`; derived cockpit/status views remain outside canonical
  trust.
- [x] Tool-run identity is deterministic under delimiter ambiguity and
  concurrency; supersession is one immutable forward edge, scoped to the same
  topic/claim/scientific run, with reverse state derived at read time.
- [x] Promotion recovery commits authorization before materializing active
  memory, and authenticated checkpoint metadata is required by every trust
  consumer.
- [x] Repository path containment, collision, CAS revision, artifact race, and
  Windows lock-descriptor lifecycle tests pass.
- [x] The post-split affected slice passes: 195 tests.

## Task 6: Isolate Legacy Imports

**Candidate files:**

- Modify: `brain/v5/native_mcp.py`
- Modify: `brain/v5/mcp_tools.py` or named tool catalogs
- Modify: `brain/v5/cli_legacy.py`
- Modify: `tests/test_v5_m0_release.py`
- Modify: `tests/test_v5_legacy_bridge.py`
- Modify: `tests/test_v5_test_lanes.py`

### RED

Assert compact import budgets and verify migration/read/write-guard tools remain
available only through explicit full/CLI migration routes.

### GREEN

Split tool loading by responsibility. Keep schema-v1 materialization available
to core reads, but avoid importing unrelated semantic-review, L2 view, graph,
or archived-write modules on compact startup.

Do not modify legacy candidate, stage, promotion, or graph-write business
logic.

Current status:

- [x] Compact startup lazily loads its ten research tools and does not import
  full Codex facade, graph/timeline, workspace migration, legacy audit, or the
  old MCP server; schema-v1 record materialization remains available.
- [x] Legacy write behavior is excluded from blocking lanes. Read, migration,
  materialization, and write-guard coverage remain blocking.
- [x] `legacy-write-archive` is explicit, opt-in, and absent from CI and release
  acceptance.

## Task 7: Replace Only Touched Compatibility Shards

When Tasks 3-6 touch a logical module above 1,000 lines:

1. identify one named responsibility;
2. create one explicit responsibility module;
3. retain the old public import facade;
4. remove only the corresponding numbered shard code;
5. prove logical line count does not increase.

Priority order:

1. compact/full MCP loading;
2. Codex facade;
3. canonical writer owners;
4. context selection;
5. report-only modules only when a vertical requires them.

Current status:

- [x] Compact loading moved to `compact_mcp_tools.py` with lazy facade imports.
- [x] Context selection moved to `context_selection.py` behind existing public
  facades.
- [x] Tool-run transition logic moved to `tool_run_transitions.py`; record path
  containment moved to `record_path_safety.py`; public imports remain stable.
- [x] Touched production modules remain below the 500-line complexity budget:
  `tools.py` 360, `tool_run_transitions.py` 316,
  `record_repository.py` 456, and `record_path_safety.py` 119 lines.

## Task 8: Run Vertical Retention Review

After the first vertical, run the remaining three minimal journeys:

- QFT/QG literature and derivation;
- new software from no recipe;
- multi-topic isolation and reviewed reuse.

Current status:

- [x] LibRPA/HPC synthetic canonical-writer vertical and a real hash-pinned
  read-only probe pass. The real receipt validates 31 final rows across Si,
  MgO, and BN plus collector/final/status file hashes and context provenance.
- [x] QFT/QG typed fixture passes with paired sources, grounded objects and
  relations, an open proof obligation, and a separate speculative insight.
- [ ] Real QFT/QG acceptance remains open. The paired PDFs and context probe
  pass, but the real canonical topic still lacks a proof-obligation/derivation
  chain.
  The hash-pinned blocked receipt is
  `docs/superpowers/progress/2026-07-13-qft-qg-real-vertical-probe.json`;
  recording the missing canonical chain requires separate authorization.
- [x] New-software onboarding executes a real disposable local utility, records
  source/code/run/artifact/validation, automatically detects an eligible
  procedural workflow, and installs only after a hash-bound human checkpoint.
- [x] Multi-topic reuse shares one recipe and grounded source through an
  explicit target-side bridge while requiring target validation and preventing
  source insight, run supersession, or claim-trust transfer.
- [x] All four vertical fixtures take canonical before/after byte snapshots and
  require the changed path set to equal successful `RecordRepository`
  create/revision/archive receipts. This closes scoped vertical writer
  convergence while leaving unbounded dynamic/native I/O as a measured
  repository-wide remainder.
- [x] Retention review records one class-level disposition over the exact
  itemized inventory: 53 core, 43 maintenance, 43 migration, and 77 owned
  vertical contracts are retained; 12 unowned vertical extensions are frozen
  without expansion; no public capability is deleted during Policy A's
  one-release compatibility window.

For every capability/family proposed by M1-M5, record one of:

- retained by a passing vertical;
- merged into an existing contract;
- postponed with an explicit missing vertical;
- soft-deprecated for the compatibility window;
- deleted after the compatibility window.

## Task 9: M0.5 Acceptance

Run:

```powershell
python scripts/run_v5_test_lanes.py full --basetemp <SYSTEM_TEMP_PATH>
```

Then verify:

- all classifications complete;
- compact and import budgets pass;
- real context probes pass with `not_shown`;
- first vertical canonical bypass count is zero;
- total canonical bypass count is measured and non-increasing;
- logical facade-plus-shard size is non-increasing;
- legacy write archive remains excluded;
- exact staged candidate excludes protected user changes;
- real canonical watermark is unchanged unless separate writes were explicitly
  authorized.

Do not begin broad M1-M5 implementation until this acceptance and the selected
compatibility policy are both recorded.

Current acceptance evidence:

- Policy A is recorded and compact/full/CLI behavior is tested.
- Blocking v5 files are partitioned into foundation, compatibility,
  `v5-verticals`, slow-adapter, and legacy-compat lanes. Every `test_v5_*.py`
  file is owned by a blocking lane; archived legacy writes remain separate.
- Foundation: 182 passed, 1 skipped. Compatibility: 141 passed.
  `v5-verticals`: 639 passed, 2 skipped. Slow-adapter: 88 passed.
  Legacy-compat: 200 passed. The independently green partitions contain some
  intentional overlap. The current working tree collects 1,243 tests, including
  four protected Harness Feedback tests that are intentionally not staged. The
  exact staged candidate collects 1,239 tests and passes with 1,236 passed,
  three skipped, and two pre-existing `flow_notebook` escape-sequence warnings.
  Two skips are the explicitly gated real-machine probes, which pass when run
  separately under the authorized read-only environment. The remaining skip is
  the opt-in context performance probe. The original monolithic run exceeded
  20 minutes, so lane coverage plus the independently green exact staged run is
  the current executable evidence.
- Real derived index generation 11/schema v2 is fresh with 9,850 records, zero malformed
  records, and canonical watermark
  `cd83cdad3f14cab0a822ae4f42066299bd789cc6b7be1535e59757bcba812452`.
  The complete 9,850-file canonical snapshot is byte-identical before and
  after rebuild (snapshot SHA-256
  `247912fcebb9f8b331cce07ad688898664e57979416de92fbc66e019121acf59`).
- The bounded writer-scan coverage decision is reviewed and machine-checked:
  573 declared production Python files parse without error, all 114 helper
  rows and 164 direct-mutation rows are classified, and unbounded coverage
  remains explicitly false.
- M0.5 is not complete until Task 8 closes the real QFT/QG derivation vertical.
