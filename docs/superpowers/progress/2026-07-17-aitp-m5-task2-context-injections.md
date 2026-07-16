# AITP M5 Task 2 Context Injection Audit

## Scope

This slice implements the host-neutral bounded context injection boundary. It
does not connect real Claude, Kimi, Codex, or OpenCode lifecycle events yet,
does not expose another compact MCP tool, and does not modify canonical
research records.

## Implemented Boundary

- `ContextInjectionRequest` and trust-neutral `ContextInjectionReceipt`.
- First-relevant-turn fallback to `ResearchTurnStart` only for hosts without a
  process-level SessionStart event. Setup, greeting, and unrelated requests do
  not consume the first research turn.
- Exact `startup_orientation` 800-token/4000-byte and `normal_research`
  1500-token/7500-byte ceilings. Hosts may request smaller limits only.
- One existing `compile_research_context` path for scope, recall, knowledge,
  insight, execution, applicable Skill, coverage, and expansion handles.
- Two-phase callback delivery of full context. A `delivery_started` receipt is
  durable before the Host callback; success becomes `injected`, while an
  uncertain outcome requires acknowledgement of the exact attempt digest before
  retry. Receipts contain only hashes, refs, scope, budgets, errors, and lineage.
- SHA-256 receipt namespaces over workspace, host, host session, research
  session, topic/focus, profile, and event. Raw host values never become path
  components.
- NFC, length, reserved-name, traversal, absolute-path, containment, and
  symlink-escape checks for runtime identity and storage.
- Idempotent same-event replay, including concurrent replay, with monotonic
  receipt revisions and immutable history even for A-to-B-to-A content cycles.
- Strict receipt field-set, path, budget, lineage, fingerprint-chain, instance
  identity, and full-payload SHA-256 validation. Interrupted receipt/event/
  session writes are reconciled on replay.
- Selected-family state/content tokens trigger reinjection. An unselected
  process-family write and the resulting global canonical watermark change do
  not trigger it.
- Explicit base index and delta lineage. Runtime receipts cannot update kernel
  state or claim trust.

## Locking And Complexity

The runtime transaction lock is the outermost ranked lock so an initially
missing query index can be built inside one serialized host event. The public
entrypoint remains small while contracts, compilation, runtime storage, and
strict receipt validation have separate modules. Production physical line
counts remain below 500: contracts 290, compilation 287, events 210, storage
308, and receipt validation 279.

## Verification Evidence

- RED: 26 expected failures because the context injection module did not exist.
- Focused context injection plus moment/lock regression: 69 passed, 1 skipped.
- Expanded context, disclosure, performance, knowledge, lifecycle, Hook,
  architecture, moment, and lock regression: 166 passed, 2 skipped.
- Concurrent same-event delivery and global-watermark non-trigger checks: 2
  passed.
- Independent review regressions for integrity tampering, cyclic history,
  uncertain delivery, and interrupted lifecycle state: 9 passed; complete
  context-injection suite: 35 passed, 1 skipped.
- Second-review regressions for ignored-event cyclic history and malformed host
  payload validation: 5 passed; complete context-injection suite: 40 passed, 1
  skipped.
- Pre-third-review expanded regression after the validation-module split: 197
  passed, 2 skipped; the exact staged-index export passed 196 with 2 skipped.
- Third-review exception-totality regressions reproduced 6 expected failures
  for array/object enum fields, mixed-type unknown keys, and uncaught validator
  faults. The corrected regression slice passed 15 tests; focused context plus
  architecture passed 52 with 1 skipped; the expanded suite passed 203 with 2
  skipped in 69.20 seconds.
- The corrected exact staged-index export passed 202 tests with 2 skipped in
  62.24 seconds. The working tree has one additional passing concurrent
  lifecycle test that is intentionally outside this staged slice.
- Python compilation: passed with bytecode redirected to system Temp.
- `git diff --check`: passed for the task files.
- All write tests used isolated system-Temp workspaces. No real topic-store
  canonical records were modified.

## Deferred Host Integration

Real host adapters, installer templates, readiness/smoke reports, compact Codex
facade integration, and quarantine of stale legacy injection paths remain M5
Task 3. `brain/v5/codex_facade.py` had concurrent user changes and was not
modified by this slice.
