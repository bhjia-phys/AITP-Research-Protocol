# AITP M5 Autonomous Hosts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make AITP a quiet assistant inside real host sessions: recall relevant state, capture exact process events, stage semantic candidates, expose applicable Skills, and record AITP friction without taking scientific or engineering authority.

**Architecture:** Host adapters normalize native events into a small logical research-event protocol. A pure Research Moment Controller chooses one bounded action; trusted scientific changes still use existing explicit gates. Context injections and raw candidates are runtime state, canonical objective process records use M0 writers, and Harness Feedback produces one generic human-reviewable dossier record rather than an optimization plan.

**Tech Stack:** Python 3.12, dataclasses, JSON/JSONL hook payloads, Markdown/YAML process records, Codex/Claude/Kimi host adapters, M1 lifecycle/recording, M4 Skill matching, pytest host fixtures.

## Global Constraints

- M1-M4 must be green before M5 production code begins.
- Logical events are host-neutral; host hooks contain no scientific policy.
- The controller returns exactly one of six decisions: ignore, auto-capture process, stage semantic candidate, coalesce for review, require checkpoint, or block until prerequisites.
- Objective process auto-writes require exact ids/refs and are idempotent.
- Scientific content is staged/reviewed; no automatic grounded/insight promotion.
- Hooks cannot create trusted evidence, promote memory, install/patch Skills, accept baselines, rebind active claims, or update claim trust.
- Startup/injection uses bounded context plus exact refs, never all topic memories.
- Named host profiles are immutable: `startup_orientation <= 800 tokens/4000
  bytes` and `normal_research <= 1500 tokens/7500 bytes`.
- Injection audits store fingerprints/refs/budgets, not duplicate full context.
- Receipt paths and dedup fingerprints include workspace, host, host session,
  topic/focus, event, and profile; concurrent hosts/focus changes cannot collide.
- Semantic output from AITP's own recording/retrieval tools is not recursively captured.
- Harness Feedback records a problem only; research runtime never authors or applies an engineering optimization plan.
- Harness Feedback cannot emit Skill candidates, patch proposals, previews,
  install actions, or distillation requests.
- One `harness_feedback_cases` family covers friction, workflow, schema, automation, and context issues.
- NiO and other topic-specific content lives in fixtures/examples.
- Host lifecycle support is capability-declared. Prompt-submit and stop/session
  events are used only where the host exposes them; every unsupported event has
  an explicit idempotent begin-turn/closeout facade fallback.
- M0 compatibility loaders/shards receive only narrow imports/re-exports;
  focused M5 modules and installer/template owners contain behavior.

## Test Protocol

Each task runs its expected missing-contract RED and GREEN with a unique
writable external `--basetemp`, then focused M0-M4/host/security regressions.
Reports record exact host capability/version, command, failure/pass result,
receipt path, bytes/tokens, and temp root. Unavailable is never passed.

---

## Task 1: Logical Research Events And Moment Controller

**Files:**
- Create: `brain/v5/research_moments.py`
- Create: `brain/v5/research_moment_contracts.py`
- Create: `brain/v5/research_moment_policy.py`
- Create: `brain/v5/research_moment_validation.py`
- Create: `brain/v5/research_moment_application.py`
- Create: `tests/test_v5_research_moments.py`
- Modify: `brain/v5/query_index_locking.py` (one generic outer rank -1 runtime
  transaction name; canonical writer locks remain unchanged)
- Keep unchanged: `brain/v5/moment_policy.py` (existing graph-orientation
  policy) and `brain/v5/recording_navigator.py` (existing recording workflow).
  The new host-event protocol composes their public services through a focused
  facade rather than merging unrelated policy responsibilities.

**Interfaces:**
- Produces: `ResearchEvent`, `ResearchMomentDecision`
- Produces: `decide_research_moment(ws, event) -> ResearchMomentDecision`
- Produces: `apply_research_moment_decision(ws, decision, *, actor) -> MomentReceipt`

- [x] **Step 1: Write failing event/decision contract tests**

Allowed events: ResearchTurnStart, SourceAcquired, CodeStateChanged,
ToolRunCompleted, ArtifactProduced, FailureOrGapObserved, RouteChanged,
MajorConclusionPending, ExpensiveRunPending, and SessionCloseout. Every event
has event id/time/host/session/topic, exact subject refs, objective payload,
semantic payload, source event id, and recursion origin.

- [x] **Step 2: Write a decision matrix before implementation**

Low-value reads/log noise -> ignore; exact source/code/run/artifact/monitor facts
-> auto-capture process; definition/formula/interpretation/workflow signals ->
stage candidate; milestone/closeout -> coalesce; install/trust/baseline/promotion
-> checkpoint; stale recall/missing prerequisites before high-cost action -> block.
A persisted `FailureOrGapObserved` with `gap_kind=knowledge` may request an
allowlisted read-only literature discovery action with explicit result/time
budget. It may not auto-acquire restricted content or promote a search result.

- [x] **Step 3: Implement a pure deterministic controller**

Decision contains outcome, reason codes, target families, minimum refs, dedup
key, expiry, verification steps, required checkpoint action, blocked action,
and fixed `can_update_claim_trust=False`. No filesystem write occurs here.

- [x] **Step 4: Implement bounded application adapters**

Route objective captures to exact M2 writers and semantic signals to M1
staging. Route coalescing/checkpoints/prerequisite gates to their existing APIs.
Route approved external-read requests to the M3 discovery handoff and ingest
only its normalized receipt. Reject a decision whose declared effect differs
from CapabilitySpec policy.

- [x] **Step 5: Suppress recursive and low-value capture**

Events originating from AITP retrieval/context/recording/diagnostic output carry
an origin marker and cannot create another semantic candidate. Repeated status
polls with unchanged fingerprints are idempotent/ignored.

- [x] **Step 6: Run moment/recording/execution/trust tests and commit**

Commit message: `v5: add bounded research moment controller`.

## Task 2: Context Injection Events And Shared Host Protocol

**Files:**
- Create: `brain/v5/context_injection_events.py`
- Create: `brain/v5/context_injection_contracts.py`
- Create: `brain/v5/context_injection_compilation.py`
- Create: `brain/v5/context_injection_receipt_validation.py`
- Create: `brain/v5/context_injection_storage.py`
- Create: `tests/test_v5_context_injection_events.py`
- Modify: `brain/v5/hook_protocol_contracts.py`

**Interfaces:**
- Produces: `ContextInjectionRequest`, `ContextInjectionReceipt`
- Produces: `prepare_context_injection(ws, request) -> ContextInjectionReceipt`
- Produces: `acknowledge_context_injection_delivery(...) -> ContextInjectionReceipt`
- Runtime path:
  `.aitp/runtime/context_injections/<digest-prefix>/<namespace-sha256>.json`

- [x] **Step 1: Write failing budget/fingerprint tests**

Receipt records host/event/session/topic/focus, context profile, effective
base/delta lineage, selected-family state/content tokens, dirty families,
canonical watermark, exact refs, selected record refs, checked scope, errors,
byte/token count, content SHA-256, created time, and injection status. It does
not contain full context text. Test same session/event ids across workspaces,
hosts, topics, profiles, and focus changes.

Build `namespace-sha256` from canonical JSON of workspace identity, host, host
session, topic/focus, profile, and event; store original values inside the
receipt, never as path components. Resolve under the runtime root and reject
containment/symlink escape. Test separators, `..`, absolute syntax, Unicode
normalization, Windows reserved names, long ids, and malicious host payloads.

- [x] **Step 2: Implement first-relevant-turn semantics**

If the host lacks process-level SessionStart, the first request classified as
research relevant becomes ResearchTurnStart. Setup, greetings, and unrelated
coding prompts do not trigger scientific retrieval.

- [x] **Step 3: Compile via the one lifecycle/context path**

Resolve focus, resume, recall requirements, grounded/insight lanes, execution
capsule, and applicable Skill names/versions through existing services. Enforce
the exact named `startup_orientation` and `normal_research` token and UTF-8 byte
ceilings plus exact expansion handles; hosts may request smaller limits only.

- [x] **Step 4: Persist idempotent runtime receipts**

Same workspace/host/session/event/profile/focus/effective-scope/content
fingerprint returns unchanged.
Changed focus or selected-family token produces a new receipt; an unrelated
process-family write does not. Global watermark remains audit metadata but is
not by itself a reinjection trigger. Runtime receipts have no claim-trust
authority.

The selected-family state token is checked first; content is rescanned only for
a selected family whose state token changed. Full context text is delivered
through `prepared -> delivery_started -> injected`; it is never copied into the
receipt. An uncertain callback outcome is not retried until the host
acknowledges the exact delivery-attempt digest.

- [x] **Step 5: Run context/startup/facade tests and commit**

Commit message: `v5: audit bounded context injections`.

## Task 3: Claude, Kimi, Codex, And OpenCode Lifecycle Integration

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
- Modify: `brain/v5/hook_protocol_contracts.py`
- Modify: `brain/v5/hook_install_contracts.py`
- Modify: `brain/v5/hook_install_audit.py`
- Modify: `brain/v5/host_readiness.py`
- Modify: `brain/v5/hook_smoke_coverage.py`
- Modify: `brain/v5/codex_facade.py`
- Modify: `tests/test_aitp_pm_deploy_surfaces.py`
- Create: `brain/v5/host_lifecycle_facade.py`
- Create: `tests/test_v5_real_host_lifecycle.py`

- [x] **Step 1: Capture current host behavior as characterization tests**

Build a versioned host capability matrix from installer/configuration owners,
capturing OpenCode's then-existing plugin-based system transform as a legacy
injection conflict alongside its available events.
Fixture native SessionStart, prompt-submit, pre/post-tool, and stop/session-end
events only where each host actually exposes them, plus Codex compact-facade
first prompt. Record current output, trace, unsupported events, fallback,
failure, and timeout behavior before modification.

- [x] **Step 2: Map native events to logical events only**

Adapters normalize ids, refs, objective/process payload, host capability, and
origin. They call shared moment/context APIs and translate receipts back to
host-native output; they contain no family-specific scientific writer logic.
Prompt-submit maps to first-turn recall and stop/session-end maps to closeout
when supported. Otherwise the installer advertises the gap and the host calls
idempotent `begin_research_turn` / `closeout_session` facade operations. No plan
may claim automatic closeout from pre/post-tool events alone.

- [x] **Step 3: Enforce host write allowlists**

Tests monkeypatch evidence/trust/memory/skill-install/baseline/active-claim
writers to fail. Every hook path must pass. Only runtime receipts, exact process
auto-captures, and candidates produced through the validated Research Moment
Controller are allowed; a host cannot call a semantic staging writer directly.

- [x] **Step 4: Quarantine stale legacy injection paths**

Detect templates/configs that inject stage guidance or complete MEMORY bodies.
Install/doctor reports them as conflicts and replaces them only through an
explicit reviewed host-install plan.

- [x] **Step 5: Add real process smoke tests and readiness reports**

For each available host, launch the documented command, submit one fixture
event, verify trace delta/output/receipt, and distinguish unavailable host from
failing hook. Never claim an uninstalled host passed.

- [x] **Step 6: Run hook/install/readiness regressions and commit**

Commit message: `v5: connect real hosts to research lifecycle`.

Execution note: this task was delivered as reviewable commits for capability
characterization, normalized dispatch, writer boundaries, legacy-injection
quarantine, and truthful readiness. The implementation distinguishes host
command availability from hook installation. On 2026-07-17 all four commands
were available, but all four repository-local hook audits were `missing`; none
was reported production-ready. This task's completion is a code, contract, and
documentation result, not a claim that the current workspace has installed
host hooks.

## Task 4: Generic Harness Feedback Case

**Files:**
- Create: `brain/v5/harness_feedback_cases.py`
- Create: `brain/v5/harness_feedback_case_contracts.py`
- Create: `tests/test_v5_harness_feedback_cases.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/record_family_registry.py`
- Modify: `brain/v5/harness_feedback.py`
- Modify: `tests/test_v5_harness_feedback.py`

**Interfaces:**
- Produces: `HarnessFeedbackCaseRecord`
- Adds family: `harness_feedback_cases`
- Produces: `record_harness_feedback_case(ws, request, *, actor) -> WriteResult`
- Produces: `render_harness_feedback_case(record) -> str`
- Produces: `build_harness_feedback_review_view(ws) -> dict`

- [x] **Step 1: Write failing generic-schema tests**

Record fields: case id, problem type, observed friction, expected behavior,
actual behavior, research impact, reproducibility steps, host/runtime, source
record refs, log/artifact refs, proposed direction, affected capability/family,
status, reviewer, duplicate/supersession refs, created/updated time,
`produces_harness_optimization_plan=False`, `can_install_skill=False`, and
`can_update_claim_trust=False`.

- [x] **Step 2: Implement one Markdown-backed family**

Do not create friction/workflow/schema/automation/proposal sub-families. Same
problem/source fingerprint is idempotent; new information creates an explicit
revision or related case.

- [x] **Step 3: Preserve research-side boundary**

The renderer may include observed facts and a proposed direction, but not an
implementation roadmap, code patch, Skill package, install action, or trust
decision. Human engineering review owns downstream optimization.

Delete the legacy runtime Skill-distillation candidate file/field/renderer and
remove that requirement from Harness Feedback contracts. Compatibility readers
may recognize old dossier bundles, but new or revised cases cannot create Skill
candidates, patch proposals, package previews, install actions, or distillation
requests. Add monkeypatch/negative tests for every prohibited Skill path.

- [x] **Step 4: Move NiO constants/content to fixtures**

Current NiO dossier becomes `tests/fixtures/v5_harness_feedback/nio_case.json`
plus expected Markdown. Production runtime contains no fixed case id/topic/path.

- [x] **Step 5: Build a derived repeated-case review view**

Group by problem type/capability/fingerprint and show counts, recency, impact,
source refs, status, and unresolved cases. The view writes no optimization plan.

- [x] **Step 6: Run Harness Feedback and registry tests; commit**

Commit message: `v5: record generic harness feedback cases`.

Implementation status: complete in `e9ff8406` and `3274abc7`. The runtime now
stores one `harness_feedback_cases` typed family with deterministic source and
content fingerprints, idempotent replay, compare-and-swap revision, explicit
related-case links, a Markdown renderer, and a read-only repeated-case view.
CLI and full MCP expose only generic case recording and review; compact MCP
remains ten tools. NiO content exists only under test fixtures. Historical
bundle/dossier validators remain read-only compatibility surfaces, while their
runtime builders, run-directory optimization plan, Skill candidate, patch,
preview, install, and distillation paths are absent. The exact staged tree
`aec978dacd02c0d9ae139e135bf22e26a4ea459d` passed 121 Harness Feedback,
registry, public-surface, CLI, MCP, deployment, and architecture tests in
system Temp.

## Task 5: Host/Moment Facade And M5 Acceptance

**Files:**
- Create: `brain/v5/mcp_research_moments.py`
- Create: `brain/v5/cli_research_moments.py`
- Create: `brain/v5/research_moment_facade.py`
- Create: `brain/v5/research_moment_surface_contracts.py`
- Create: `brain/v5/hook_research_moment_bridge.py`
- Create: `tests/test_v5_research_moment_facade.py`
- Create: `tests/test_v5_gate5_host_e2e.py`
- Create: `docs/superpowers/progress/2026-07-10-aitp-gate-5-release-audit.md`
- Modify: `brain/v5/capability_registry_data.py`
- Modify: `brain/v5/capability_surface_contracts.py`
- Modify: `brain/v5/public_surfaces.py`
- Modify: `brain/v5/mcp_tools.py`
- Modify: `brain/v5/cli.py`
- Modify: `brain/v5/host_lifecycle_dispatch.py`
- Modify: `brain/v5/host_lifecycle_facade.py`
- Modify: `hooks/aitp_v5_adapter_event_runner.py`
- Modify: `hooks/aitp_v5_claude_hook.py`
- Modify: `hooks/aitp_v5_kimi_hook.py`
- Modify: `README.md`
- Modify: `PROJECT_MEMORY.md`
- Modify: `docs/superpowers/plans/2026-07-09-aitp-final-research-lifecycle-roadmap.md`

- [x] **Step 1: Register event/decision/apply/injection/feedback capabilities**

Pure decisions/read views are read-only; runtime staging/injection receipts are
runtime writes; objective process records and feedback cases are trust-neutral
kernel writes. Compact surface remains enter/expand/record/closeout concepts.
Register deep validators, host capability/fallback contracts, CLI/MCP parity,
pre-tool policies, and compact visibility for every operation. Loader files
receive only focused-module imports.

Implemented as one full-only `process_research_moment` capability with a shared
deep surface contract and file-backed CLI. Existing context injection and
Harness Feedback capabilities remain separate. Compact stays exactly ten tools;
the controller is reached through the existing compact recording workflow or an
explicit full-surface event rather than another compact tool.

- [x] **Step 2: Run a normal-session vertical acceptance**

First relevant turn recalls bounded context and applicable Skills; source/code/
run/artifact events capture exact process state; semantic events stage; milestone
coalesces one batch; closeout persists one record; next session resumes. No
manual `.aitp` file edit occurs. Include one knowledge-gap event that issues a
bounded discovery handoff and preserves connector coverage. Connector execution,
allowed hashed-source acquisition, and grounded promotion remain M3/M6 work;
M5 must not duplicate that authority. Search snippets and unacquired results
remain process-only.

`tests/test_v5_gate5_host_e2e.py` proves bounded first-turn recall, explicit
semantic staging, one closeout review batch, plan-only host closeout, and next-
session resume. Exact objective process writers and the bounded knowledge-gap
handoff remain covered by `tests/test_v5_research_moments.py`.

- [x] **Step 3: Run noise/recursion/failure acceptance**

Repeated polls, unchanged files, AITP tool output, malformed host payload,
missing session, stale index, unavailable host, and hook timeout produce bounded
diagnostics without recursive writes or scientific promotion.

Raw post-tool output stays trace-only. Only a complete top-level event envelope
may enter the controller; five identity pins are checked before application.
Nested tool output is ignored and malformed envelopes return a bounded,
orientation-only diagnostic without exposing their content.

- [x] **Step 4: Run a friction-to-dossier acceptance**

A real research-side recording/context failure produces one generic case and a
review view. Assert no optimization plan, code patch, Skill candidate/patch/
preview/install/distillation action, or claim-trust change exists.

The vertical writes one generic case and reads the recurring-case view. A single
incident is counted but correctly does not fabricate a recurring group.

- [x] **Step 5: Run M0-M5, host smokes, architecture, and staged-tree audits**

Record exact available/unavailable host status, test counts, budgets, canonical
hash effects, and capability/family drift.

- [x] **Step 6: Update docs, release audit, and commit**

The repository-level vertical is commit `292445dc` (`v5: connect validated
research moments to host lifecycle`). The release audit drift fix is a separate
closeout commit so it cannot rewrite that implementation evidence.
Do not call M5 complete until at least one installed project-hook lifecycle
event is observed. The separately packaged Kimi Code parity checks now pass,
but plugin packaging is not project-hook installation evidence.

## M5 Completion Checklist

- [x] Every host event maps to one host-neutral logical event.
- [x] Every moment returns exactly one bounded decision.
- [x] Objective capture is exact, idempotent, and low-noise.
- [x] Knowledge gaps may trigger budgeted read-only literature discovery; full
  source acquisition and semantic promotion retain their separate gates.
- [x] Semantic candidates remain review gated and coalesced.
- [x] Context injections are bounded, fingerprinted, and ref-traceable.
- [x] Hooks cannot write trust, evidence promotion, baselines, or Skill installs.
- [x] Hosts without SessionStart use first relevant prompt safely.
- [x] Prompt-submit/stop events are wired only where supported; every missing
  event has an audited begin-turn/closeout facade fallback.
- [x] One generic Harness Feedback family replaces case-specific runtime logic.
- [x] Feedback creates a problem dossier, never an optimization plan.
- [x] Feedback cannot emit any Skill candidate, patch, preview, install, or
  distillation action.
- [x] A normal research lifecycle requires no manual AITP file editing in the
  generated-hook and fixture vertical.
- [ ] At least one repository-local project hook is installed and a real
  interactive lifecycle event is observed. Process availability or generated
  command smoke alone does not satisfy this item.
- [x] The separately packaged Kimi Code plugin has test-backed manifest,
  launcher/config resolution, packaged-Skill, and duplicate-registration parity.
  Plugin availability does not satisfy project lifecycle-hook readiness.
