# AITP Dynamic Multi-Topic Hook Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let one project-local AITP installation dynamically select the correct existing research topic/session for each relevant host turn while preserving ambiguity, bounded context, canonical write authority, and cross-topic trust isolation.

**Architecture:** Add one host-neutral, read-only route service in front of existing compact recovery and lifecycle dispatch. Candidate discovery uses one coherent indexed query snapshot and exact canonical verification; continuity is a disposable `.aitp/runtime` mapping. Host hooks remain trigger/transport adapters, dynamic installation becomes the default, and explicit fixed-session pins remain compatibility only.

**Tech Stack:** Python 3.12, frozen dataclasses, typed Markdown/YAML repository reads, deterministic JSON runtime state, SHA-256 path namespaces, FastMCP compact facade, host hook JSON/TOML/JavaScript adapters, pytest with system-Temp basetemps.

## Global Constraints

- v5 remains the only production research-write runtime.
- Typed canonical records remain the only scientific truth source.
- Route decisions, query results, context, RAG, summaries, hooks, runtime
  mappings, and Skills cannot update claim trust.
- Dynamic routing creates no canonical record family and no new compact MCP
  tool; compact remains exactly ten tools.
- `SessionBinding` remains single-topic. Supporting topics require explicit
  bridge/focus semantics and target-side revalidation.
- New project installs default to dynamic routing and contain no permanent
  session id. Pinned mode must be explicit or recognized as legacy positional
  compatibility.
- Recency or lexical similarity alone cannot select a primary session.
- Stale, malformed, truncated, partial, conflicting, or ambiguous coverage
  fails closed before session-specific context or canonical recording.
- No raw transcript, full prompt history, or unbounded tool output is persisted.
- Before route selection, hooks may enforce generic policy and append bounded
  runtime trace only.
- Existing unrelated host configuration is preserved. Legacy full-memory or
  keyword injection is a reported conflict and requires an exact reviewed
  replacement plan.
- Legacy L0-L4 remains read/audit/migration/write-guard only.
- Real canonical records are read-only unless the user gives a new exact write
  authorization. Derived index rebuild and runtime-route writes do not grant
  canonical write authority.
- All manual edits use `apply_patch`; unrelated dirty-worktree changes remain
  untouched.

## File And Responsibility Map

**New focused modules**

- `brain/v5/host_route_contracts.py`: immutable route request, candidate,
  coverage, and decision contracts with stable re-export entrypoints.
- `brain/v5/host_route_normalization.py`: shared bounded text/id/ref/JSON
  normalization helpers used by route contracts.
- `brain/v5/host_route_requests.py`: request normalization and deterministic
  input fingerprinting.
- `brain/v5/host_route_payloads.py`: decision payload encoding, decoding, and
  authority revalidation across runtime boundaries.
- `brain/v5/dynamic_host_routing.py`: pure orchestration of intent assessment,
  explicit route resolution, indexed candidate flow, and final decisions.
- `brain/v5/host_route_discovery.py`: bounded indexed discovery, evidence-tier
  scoring, and deterministic candidate plans.
- `brain/v5/host_route_coverage.py`: coherent-snapshot coverage aggregation and
  fail-closed extension across exact/scope reads.
- `brain/v5/host_route_scope.py`: selected-session scope resolution and
  supporting-only target-revalidation proposals.
- `brain/v5/host_route_cache.py`: disposable, atomically written, content-bound
  host-session route continuity below `.aitp/runtime/host_routes`.
- `brain/v5/host_lifecycle_normalization.py`: bounded host-event normalization
  with explicit dynamic/pinned mode and no raw prompt or tool-output retention.
- `brain/v5/host_lifecycle_routing.py`: route-first lifecycle gate that resolves
  fresh prompt/start events and exact-revalidates cached pre/post-tool routes.
- `brain/v5/hook_routing_mode.py`: one parser/normalizer for dynamic, pinned,
  and legacy-pinned installation/runner behavior.
- `tests/test_v5_dynamic_host_routing.py`: deterministic unit and service tests.
- `tests/test_v5_dynamic_multi_topic_host_e2e.py`: one-project/two-topic
  acceptance with canonical before/after byte snapshots.

**Existing composition points**

- `brain/v5/compact_mcp_tools.py` and `brain/v5/codex_facade.py`: use the real
  workspace and compose route decisions into the existing ten-tool entry
  surface.
- `brain/v5/host_lifecycle_contracts.py`,
  `brain/v5/host_lifecycle_dispatch.py`, and
  `hooks/aitp_v5_adapter_event_runner.py`: allow unresolved dynamic events to
  remain policy/trace-only and resolve cached selections before bounded context
  or validated Research Moments.
- `brain/v5/cli_adapters.py`, host installer/template modules, bridge/fixture
  builders, and hook scripts: emit and consume explicit routing mode rather
  than requiring a positional session for every installation.
- `brain/v5/hook_install_audit.py`, installation contracts, readiness, and
  smoke coverage: report dynamic/pinned/legacy-pinned state truthfully.

## Verification Lanes

Use the system interpreter:

```powershell
& 'C:\Users\samur\AppData\Local\Programs\Python\Python312\python.exe' -m pytest <tests> -q --basetemp '<unique-system-temp-path>'
```

Keep these lanes separate:

1. Deterministic route/cache/compact tests: short RED/GREEN loop.
2. Installer, bridge, runner, and contract tests: subprocess fixture lane.
3. Existing `tests/test_v5_adapters.py`: slow adapter lane with its own budget.
4. `test_v5_real_host_lifecycle.py` and `test_v5_host_readiness.py`: real-host
   probe lane; timeout means unverified, never passed.
5. Blocking release lanes from `scripts/run_v5_test_lanes.py` after all focused
   work is green.
6. Real multi-topic project install/observation only after exact configuration
   diff approval.

The pre-change release candidate already has recorded evidence for 1,997 passed
and four skipped tests across five blocking lanes. Three attempted combined
baseline commands in this isolated worktree reached their 5-10 minute budgets
without a failure summary; they are unverified timeouts, not new pass or failure
claims. New deterministic coverage must therefore carry the implementation
loop, while slow lanes remain separately observable.

---

### Task 1: Lock Route Contracts And Authority

**Files:**
- Create: `brain/v5/host_route_contracts.py`
- Create: `brain/v5/host_route_normalization.py`
- Create: `brain/v5/host_route_requests.py`
- Create: `brain/v5/host_route_payloads.py`
- Create: `tests/test_v5_dynamic_host_routing.py`
- Modify: `brain/v5/public_surfaces.py` only if an existing surface validator
  cannot express the nested route payload; do not register a new MCP operation.

**Interfaces:**
- Produces: `HOST_ROUTE_REQUEST_SCHEMA_VERSION = "aitp.host_route_request.v1"`.
- Produces: `HOST_ROUTE_DECISION_SCHEMA_VERSION = "aitp.host_route_decision.v1"`.
- Produces: `HostRouteRequest` with bounded request summary, host identity,
  project/repository/path signals, explicit topic/session/ref inputs, optional
  pin, routing mode, and semantic assessment.
- Produces: `HostRouteCandidate` with exact topic/session ids, bounded score
  components, evidence tier, reason codes, exact refs, and supporting-only flag.
- Produces: `HostRouteCoverage` with checked/not-shown/not-checked families,
  malformed/read-error/truncation state, index generation, watermark, and
  strong-selection eligibility.
- Produces: `HostRouteDecision` with one allowed status, at most three
  candidates, selected refs only for `selected`, input fingerprint, next
  operation, and fixed false trust/write authority.
- Produces: `normalize_host_route_request(...)` and `route_decision_payload(...)`.

- [x] **Step 1: Write failing contract tests**

Test all six statuses, candidate limit, normalized/sorted exact inputs, maximum
summary/path counts and lengths, rejection of raw transcript/tool-output fields,
and deterministic serialization/fingerprints.

- [x] **Step 2: Prove authority invariants in RED**

Require `orientation_only=True`, `summary_inputs_trusted=False`,
`canonical_write_allowed=False`, `can_update_kernel_state=False`, and
`can_update_claim_trust=False`. Reject a `selected` decision without one exact
topic/session pair or with blocked coverage.

- [x] **Step 3: Implement minimal frozen contracts**

Use immutable tuples/mappings and existing timestamp/id/path normalization where
appropriate. Do not import repository writers or lifecycle application code.

- [x] **Step 4: Run focused GREEN and review field flow**

```powershell
python -m pytest tests/test_v5_dynamic_host_routing.py -q -k contract
```

Review every request field for an actual producer and every decision field for
an actual consumer. Delete speculative fields before commit.

- [x] **Step 5: Commit**

Commit message: `v5: define trust-neutral host route contracts`.

Execution note: nine focused route-contract tests cover deterministic request
normalization/fingerprints, bounded candidate decisions, strong-coverage
selection, ambiguity, target revalidation, fixed false authority, and JSON
round-trip tamper rejection. The initial all-in-one contract module exceeded
the 500-line architecture budget, so request normalization and payload codecs
were split into focused modules without changing the public API. The combined
route, public-surface, generic-contract, and architecture lane passed 77 tests
in 226.51 seconds using an explicit system-Temp basetemp.

### Task 2: Implement Coherent Read-Only Route Resolution

**Files:**
- Create: `brain/v5/dynamic_host_routing.py`
- Create: `brain/v5/host_route_discovery.py`
- Create: `brain/v5/host_route_coverage.py`
- Create: `brain/v5/host_route_scope.py`
- Modify: `tests/test_v5_dynamic_host_routing.py`
- Read/reuse: `brain/v5/research_retrieval.py`
- Read/reuse: `brain/v5/research_scope.py`
- Read/reuse: `brain/v5/repository.py`
- Read/reuse: `brain/v5/codex_facade.py`

**Interfaces:**
- Produces: `resolve_host_research_route(ws, request, *, query_session=None) -> HostRouteDecision`.
- Consumes: `ResearchQuery`, `QuerySnapshotSession`, `query_records`, exact
  repository reads, current `codex_autoroute` intent assessment, and
  `resolve_session_scope` after exact session selection.

- [x] **Step 1: Write failing explicit-ref and outside-AITP tests**

An exact valid session/topic ref selects deterministically. Conflicting explicit
refs return `conflict`. A generic non-research prompt returns `outside_aitp`
without querying every family or creating runtime state.

- [x] **Step 2: Write failing indexed-discovery tests**

Build two-topic fixtures with overlapping terms. Query a bounded family set
covering topic/session/route/closeout/claim/code/artifact/source anchors through
one `QuerySnapshotSession`; aggregate to topic/session candidates and exact-read
all selected anchors.

- [x] **Step 3: Implement evidence tiers and deterministic scoring**

Use this order: explicit refs/pin, exact repository/path/code/artifact anchors,
valid runtime continuity, objective/route/closeout/claim/topic text, then
recency tie-break only. Store component scores and reason codes; never hide the
runner-up from an ambiguous decision.

- [x] **Step 4: Implement fail-closed coverage and ambiguity**

Any stale scope, failed exact read, malformed in-scope family, truncation, or
unresolved top-candidate tie returns `coverage_blocked` or `ambiguous`.
`workspace_recovery` means AITP is relevant but no safe session exists; it does
not create one.

- [x] **Step 5: Implement supporting-scope proposal**

Only after a clear primary selection, return bounded supporting candidates from
program/bridge discovery with `requires_target_revalidation=True`. Do not write
a focus set or treat supporting claims as evidence.

- [x] **Step 6: Run focused GREEN and query-count assertions**

Assert one coherent snapshot, bounded result limit, exact reads for selected
anchors, deterministic ordering, and zero repository writer calls.

- [x] **Step 7: Commit**

Commit message: `v5: resolve dynamic research routes read only`.

Execution note: the resolver now normalizes explicit session/topic refs, skips
the index for clearly outside-AITP requests, discovers candidates through one
coherent bounded snapshot, exact-reads every selected anchor, preserves ties,
and blocks stale, malformed, truncated, missing, or conflicting coverage.
Reviewed program/focus/bridge scope is resolved only after primary selection;
supporting sessions are marked supporting-only and require target-side
revalidation. The resolver invokes no repository writer and leaves the
canonical watermark unchanged. Focused routing tests passed 29 tests in 5.98
seconds; retrieval/scope/public-surface/contract regressions passed 93 tests in
226.68 seconds; architecture boundaries passed 6 tests in 0.42 seconds. Pure
discovery, coverage, and scope finalization were split from orchestration to
keep every new production module below the 500-line budget.

### Task 3: Add Disposable Host-Session Route Continuity

**Files:**
- Create: `brain/v5/host_route_cache.py`
- Modify: `tests/test_v5_dynamic_host_routing.py`

**Interfaces:**
- Produces: `write_host_route_mapping(ws, request, decision) -> HostRouteMapping`.
- Produces: `read_host_route_mapping(ws, request) -> HostRouteMapping | None`.
- Produces: `clear_host_route_mapping(ws, request) -> bool`.
- Stores: `.aitp/runtime/host_routes/<sha256>.json` using existing atomic text
  helpers and no raw host-session/path component in filenames.

- [x] **Step 1: Write failing namespace and traversal tests**

Cover Windows reserved names, Unicode normalization, long ids, symlink escape,
different workspaces/hosts/host sessions, and deterministic SHA-256 paths.

- [x] **Step 2: Write failing integrity and invalidation tests**

Bind workspace identity, host/session identity, route-input continuity fields,
selected exact refs, index generation, watermark, creation/verification time,
and integrity hash. Tampering, changed explicit refs/repository identity, expiry,
or missing canonical anchors invalidates the mapping.

- [x] **Step 3: Implement atomic runtime-only persistence**

Use the existing atomic write helper. Exact-read selected session/topic before
reuse; a mapping is a continuity hint, never a selection truth source.

- [x] **Step 4: Prove canonical neutrality**

Snapshot all canonical registry bytes and the canonical watermark before and
after write/read/clear. Assert exact equality while runtime files change.

- [x] **Step 5: Commit**

Commit message: `v5: cache exact host routes outside canonical memory`.

Execution note: host-session continuity is stored only below the hash-namespaced
`.aitp/runtime/host_routes` tree with NFC-normalized identity, a sealed payload,
a 24-hour TTL, request-continuity fingerprint, exact selected refs, and the
verified index generation/watermark. Reads fail closed on tampering, expiry,
repository or explicit-route drift, generation changes, stale coverage, or
missing canonical anchors. Request summaries and current paths are not
persisted. Write/read/clear preserved byte-identical canonical records and the
canonical watermark. The full resolver/cache file passed 39 tests with one
Windows symlink-creation skip in 18.33 seconds; query-index, repository, and
runtime-path regressions passed 91 tests with one existing environment skip in
17.17 seconds; architecture boundaries passed 6 tests in 0.43 seconds.

### Task 4: Compose Dynamic Routing Into The Ten-Tool Compact Entry

**Files:**
- Modify: `brain/v5/compact_mcp_tools.py`
- Modify: `brain/v5/codex_facade.py`
- Modify: `tests/test_v5_dynamic_host_routing.py`
- Modify or extend: compact public-surface/catalog tests without changing tool
  count.

**Interfaces:**
- Extends: `aitp_v5_codex_autoroute(base, *, request_summary, ...)` with one
  bounded `route_context` object carrying optional `host`, `host_session_id`,
  `project_root`, `current_path`, `repo_id`, `branch`, exact-ref, pin, and mode
  inputs. The internal facade keeps typed keyword arguments while the compact
  MCP schema stays within its global byte budget.
- Preserves: existing call shapes with no host identity and existing route-hint
  response keys where compatible.
- Fixes: compact autoroute must use `_ws(base)` instead of discarding `base`.

- [x] **Step 1: Write failing workspace-aware compact tests**

Prove the same prompt routes differently in two fixture workspaces and that the
wrapper passes the requested base into the resolver.

- [x] **Step 2: Add route decision composition**

Keep the existing intent heuristic as an initial signal. When AITP is relevant
and a workspace is available, attach the bounded route decision and recommend
`aitp_v5_codex_enter` only for `selected`; recommend bounded recovery/choice for
all other relevant statuses.

- [x] **Step 3: Persist continuity only after safe selection**

Write runtime mapping only when host and host-session ids are present and the
decision is `selected`. Route-time canonical authority remains false.

- [x] **Step 4: Prove compact count and payload budget**

Assert exact ten-tool registration, no Skill body/full memory/transcript in the
route response, at most three cards, and existing route-hint byte/token budget.

- [x] **Step 5: Commit**

Commit message: `v5: route compact entry across research topics`.

Execution note: compact autoroute now passes the resolved workspace instead of
discarding `base`, composes a trust-neutral typed host-route decision only for
the host-aware call shape, rewrites entry arguments to the exact selected
session, preserves ambiguity without an enter recommendation, and stores
runtime continuity only after strong selection. Legacy calls without host
routing context retain the prior heuristic behavior. Unknown `route_context`
fields are rejected. The compact registry remains exactly ten tools; the
native schema is 5,944 bytes against the 6,000-byte budget and the tested route
hint remains below 24 KB without transcript, context pack, full memory, or
Skill body content. Compact/capability/MCP/lifecycle regressions passed 81 tests
with one environment skip in 60.14 seconds; public surfaces passed 24 tests in
0.71 seconds; architecture boundaries passed 6 tests in 0.57 seconds; generic
contracts passed 38 tests in 327.33 seconds. A prior combined contracts command
timed out at 304 seconds without a summary and was superseded by these split
lanes.

### Task 5: Make Lifecycle Dispatch Safe Before And After Selection

**Files:**
- Modify: `brain/v5/host_lifecycle_contracts.py`
- Modify: `brain/v5/host_lifecycle_dispatch.py`
- Modify: `hooks/aitp_v5_adapter_event_runner.py`
- Modify: `brain/v5/hook_research_moment_bridge.py`
- Modify: `tests/test_v5_adapter_event_runner.py`
- Modify: `tests/test_v5_real_host_lifecycle.py`
- Modify: `tests/test_v5_dynamic_host_routing.py`

**Interfaces:**
- Extends: normalized events with explicit `routing_mode` and route status while
  retaining a concrete `session_id` only after selection/pin validation.
- Produces: a bounded `route_required`, `route_ambiguous`, or
  `route_coverage_blocked` dispatch with both write flags false.
- Preserves: existing bounded context and validated Research Moment operations
  after exact binding succeeds.

- [x] **Step 1: Write failing unresolved-event tests**

Dynamic pre/post-tool events with no selected route must not call
`get_session_binding`, context injection, Research Moment application, or any
canonical writer. Generic pre-tool policy and bounded trace remain available.

- [x] **Step 2: Add runner routing-mode parsing**

`--routing-mode dynamic` accepts no session id and derives host-session identity
from allowlisted stdin fields. `--routing-mode pinned --session-id X` validates
the pin. Never read a full raw prompt or nested output for routing.

- [x] **Step 3: Resolve exact cached route before bound operations**

On prompt/start events, route from bounded objective data when supported. On
pre/post-tool events, reuse only an exact-valid runtime mapping. A missing or
invalid mapping returns policy/trace-only status.

Prompt-only exact refs select and anchor the cached route but are not required
on every later tool event. The runtime mapping still exact-revalidates the
selected session, topic, candidate anchors, index generation, and canonical
watermark before reuse.

- [x] **Step 4: Preserve validated Research Moment identity pins**

The explicit top-level event envelope must still match host, host-session,
selected session, topic, and source event. Dynamic routing cannot weaken the
five-pin check or turn raw tool output into semantic input.

- [x] **Step 5: Run writer-sentinel and recursion tests**

Monkeypatch trust, evidence, baseline, Skill, active-claim, focus-set, and
canonical family writers. All unresolved/ambiguous paths must pass with zero
calls.

- [x] **Step 6: Commit**

Commit message: `v5: gate host lifecycle on exact dynamic routes`.

**Evidence:** The route/lifecycle RED cases first failed on the absent public
`routing_mode` and runner interfaces, and the exact-ref continuity case failed
with `route_required` after a successful exact-ref prompt selection. After the
implementation and module split, the dynamic-routing plus architecture lane
passed `59 passed, 1 skipped`; the complete adapter-runner lane passed
`17 passed`; host lifecycle plus Gate 5 passed `37 passed`; and Research Moment
recursion plus architecture passed `35 passed`. The skip is the existing
Windows symlink-creation limitation. All pytest runs used unique system-Temp
basetemps with cache disabled and no real canonical records.

### Task 6: Make Dynamic Installation The Default

**Files:**
- Create: `brain/v5/hook_routing_mode.py`
- Modify: `brain/v5/cli_adapters.py`
- Modify: `brain/v5/hook_codex_install.py`
- Modify: `brain/v5/hook_install_templates.py`
- Modify: `brain/v5/hook_fixture_templates.py`
- Modify: `brain/v5/hook_runner_payloads.py`
- Modify: `brain/v5/hook_kimi_install.py`
- Modify: `brain/v5/hook_opencode_install.py`
- Modify: `hooks/aitp_v5_claude_hook.py`
- Modify: `hooks/aitp_v5_kimi_hook.py`
- Modify: `brain/v5/hook_install_contracts.py`
- Modify: `brain/v5/hook_protocol_contracts.py`
- Modify: `tests/test_v5_adapters.py`
- Modify: `tests/test_v5_hooks.py`

**Interfaces:**
- Produces: `normalize_hook_routing_mode(routing_mode, session_id, *, legacy_positional=False)`.
- New CLI: `adapter install-hooks <runtime> --routing-mode dynamic ...`.
- Pinned CLI: `adapter install-hooks <runtime> --routing-mode pinned --session-id <id> ...`.
- Compatibility CLI: old positional session with no explicit mode becomes
  `pinned_compat` and emits a deprecation/migration field.

- [x] **Step 1: Write CLI RED for all mode combinations**

Default no-session install is dynamic. Pinned without a session fails. Explicit
dynamic plus any pin fails. Legacy positional session remains readable and is
never mislabeled dynamic.

- [x] **Step 2: Centralize generated runner argv**

All Codex/Claude/Kimi/OpenCode fixture and native installers emit explicit
`--routing-mode`. Dynamic argv contains no `--session-id`; pinned argv contains
one exact session. Bridge payloads declare mode and roots.

- [x] **Step 3: Preserve unrelated configuration and idempotence**

Run merge tests for JSON, TOML, and JavaScript targets. Reinstall is byte-stable,
does not duplicate hooks, and cannot overwrite unrelated or conflicted legacy
injection without the existing reviewed replacement-plan boundary.

- [x] **Step 4: Update contracts without loosening authority**

Validate routing mode, optional pin, project root, topics root, runtime-only
status, false trust authority, and required runner tokens. Preserve existing
installation kinds unless a versioned compatibility adapter is required.

- [x] **Step 5: Run installer/runner fixture lane**

Run host-specific files separately from the slow all-adapters file; record
exact counts and duration.

Evidence (isolated system-Temp basetemps, cache disabled, no real canonical
records):

- Routing mode/default/negative-contract slice: `17 passed, 88 deselected in
  1.95s`.
- Adapter Hook lane: `42 passed, 63 deselected in 169.73s`.
- Adapter event runner: `17 passed in 30.04s`.
- Native Hook scripts: `28 passed in 14.16s`.
- Runtime/public Hook surfaces: `14 passed, 14 deselected in 16.04s`.
- Architecture and M0 boundaries: `12 passed in 3.13s`.

- [x] **Step 6: Commit**

Commit message: `v5: install dynamic multi-topic hooks by default`.

### Task 7: Audit Routing Mode And Production Readiness Truthfully

**Files:**
- Modify: `brain/v5/hook_install_audit.py`
- Modify: `brain/v5/hook_install_contracts.py`
- Modify: `brain/v5/hook_install_paths.py`
- Modify: `brain/v5/host_readiness.py`
- Modify: `brain/v5/hook_smoke_coverage.py`
- Modify: `tests/test_v5_host_readiness.py`
- Modify: `tests/test_v5_real_host_lifecycle.py`
- Modify: `tests/test_v5_hooks.py`

**Interfaces:**
- Audit output adds: `routing_mode`, `pinned_session_id`, `project_root`,
  `topics_root`, `legacy_pinned`, and `migration_required`.
- Production readiness requires a dynamic install for a multi-topic project;
  pinned compatibility can be installed but cannot satisfy that status.

- [ ] **Step 1: Write audit classification RED**

Classify dynamic, pinned, legacy-pinned, partial, missing, and legacy-injection
conflict from actual generated/configured command tokens. Never infer dynamic
from absence of a parseable pin alone.

- [ ] **Step 2: Implement structured audit parsing**

Use JSON/TOML/known generated JavaScript structures where practical; keep text
token fallback bounded and report uncertainty. Return exact migration action,
not an automatic edit.

- [ ] **Step 3: Update paths/readiness/smoke reports**

Show dynamic install commands by default, explicit pinned examples separately,
and capability gaps for hosts without prompt-submit. A command being installed
or a fixture passing is not real interactive lifecycle evidence.

- [ ] **Step 4: Run deterministic audit tests and separate real-host probes**

Use a long external budget for real-host probes. Preserve timeout/unavailable/
conflict as distinct non-passing outcomes.

- [ ] **Step 5: Commit**

Commit message: `v5: audit dynamic host routing readiness`.

### Task 8: Prove One-Project Two-Topic Behavior End To End

**Files:**
- Create: `tests/test_v5_dynamic_multi_topic_host_e2e.py`
- Modify: `tests/test_v5_gate5_host_e2e.py` only for shared acceptance labels,
  not to duplicate route mechanics.

**Interfaces:**
- Consumes only public compact, installer, runner, lifecycle, repository, and
  audit surfaces.

- [ ] **Step 1: Build one realistic multi-topic fixture**

Create topic/session A for LibRPA/HPC with code/run/artifact anchors and
topic/session B for QFT/QG with source/formula/derivation anchors. Include
overlapping generic terms so exact anchors matter.

- [ ] **Step 2: Route two independent host sessions**

Through one dynamic install, prompt A selects A and prompt B selects B. Enter
bounded context and confirm exact refs, topic isolation, and runtime mappings.

- [ ] **Step 3: Exercise ambiguous and cross-topic turns**

An equal mixed request is `ambiguous` with no selection. A clear primary plus
supporting request preserves one primary and marks supporting material for
target revalidation. No topic-local trust transfers.

- [ ] **Step 4: Exercise all fail-closed cases**

Cover stale index, malformed in-scope record, truncated results, missing exact
ref, changed repo/path identity, tampered cache, and pin conflict. Assert no
session-specific context or canonical write.

- [ ] **Step 5: Prove byte-level canonical closure**

Compare complete canonical registry bytes and watermark before/after routing,
cache, install fixture, generic policy, and ambiguous lifecycle operations.
Separately exercise one explicitly validated durable Research Moment and prove
only its expected repository receipt changes canonical state.

- [ ] **Step 6: Run compact-count, architecture, and security regressions**

Check ten compact tools, import direction, module-size budget, path traversal,
raw-payload absence, and all forbidden writer sentinels.

- [ ] **Step 7: Commit**

Commit message: `test: prove dynamic multi-topic host entry`.

### Task 9: Run Release Lanes And Align Documentation

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_MEMORY.md`
- Modify: `docs/protocols/adapter_interface.md`
- Modify: `docs/superpowers/progress/2026-07-10-aitp-gate-5-release-audit.md`
- Modify: `docs/superpowers/plans/2026-07-09-aitp-final-research-lifecycle-roadmap.md`
- Modify: `docs/superpowers/plans/2026-07-10-aitp-gate-5-autonomous-hosts.md`

- [ ] **Step 1: Run all focused deterministic tests from a clean staged candidate**

Record exact commit/tree id, commands, counts, skipped tests, durations, and
system-Temp roots.

- [ ] **Step 2: Run slow adapter and real-host lanes separately**

Do not combine lanes under one timeout. A slow-lane timeout remains an open
verification item and cannot be hidden by fast-suite passes.

- [ ] **Step 3: Run all blocking v5 release lanes**

```powershell
python scripts/run_v5_test_lanes.py full
```

Verify legacy write E2E remains non-blocking and no old L0-L4 business logic was
revived to satisfy archived tests.

- [ ] **Step 4: Rebuild only authorized derived indexes if needed**

Before and after, compute the canonical file snapshot/watermark. Any canonical
change is a release blocker unless covered by a separate exact authorization.

- [ ] **Step 5: Update user and maintainer docs**

Explain dynamic default, optional pinned mode, one-project multi-topic behavior,
ambiguity handling, compact fallback for hosts without prompt-submit, runtime
cache location, migration preview, and the distinction between installation,
process availability, and observed lifecycle readiness.

- [ ] **Step 6: Commit**

Commit message: `docs: align AITP host entry with dynamic routing`.

### Task 10: Install And Observe One Real Multi-Topic Project Hook

**Files outside this repository:**
- A user-approved project-local host config, expected initially under
  `F:\AI_Workspace\Theoretical-Physics`.
- Runtime-only route/audit files below that workspace's `.aitp/runtime`.

**Authorization boundary:** Do not execute this task from the implementation
approval alone. Present the exact target paths, before/after config diff,
commands, legacy-router conflict handling, and rollback before requesting a new
write authorization.

- [ ] **Step 1: Run read-only install audit and prepare exact migration diff**
- [ ] **Step 2: Obtain explicit approval for the listed config writes**
- [ ] **Step 3: Install dynamic mode without a permanent session id**
- [ ] **Step 4: Observe prompt/session A, prompt/session B, and one ambiguity**
- [ ] **Step 5: Verify bounded context, exact refs, runtime-only route state,
  compact count ten, no trust/Skill/baseline effects, and unchanged canonical
  watermark**
- [ ] **Step 6: Update M5 release evidence and commit repository docs only**

## Final Plan Review Checkpoints

- [ ] **Spec coverage review:** map every design verification item 1-12 to at
  least one test and every real M5 acceptance bullet to Task 10 evidence.
- [ ] **Trust review:** trace every potential write from compact entry, cache,
  runner, dispatch, and installer; confirm only runtime writes occur before a
  separately validated Research Moment.
- [ ] **Multi-topic review:** confirm a single-topic binding remains canonical,
  supporting scope never transfers trust, and ambiguity is never collapsed by
  recency.
- [ ] **Compatibility review:** prove old pinned files remain auditable/readable,
  dynamic is the new default, and legacy L0-L4 receives no new write behavior.
- [ ] **Context review:** inspect payload bytes and ensure no full memories,
  transcripts, Skill bodies, or unbounded records are injected.
- [ ] **Operational review:** distinguish generated fixture, installed config,
  available host process, observed lifecycle event, and successful dynamic
  multi-topic research entry in every readiness claim.
- [ ] **Complexity review:** keep new behavior in focused modules, avoid another
  facade/shard layer, and run architecture-size/import tests before finalizing.

## Definition Of Done

This plan is complete only when all deterministic implementation tasks are
green, blocking release lanes pass, one real approved multi-topic installation
routes two topics and preserves one ambiguity, canonical watermark neutrality is
proven for route/cache/install operations, compact remains ten tools, docs match
runtime behavior, and no path transfers trust or writes scientific memory before
the existing validated Research Moment/checkpoint boundaries.
