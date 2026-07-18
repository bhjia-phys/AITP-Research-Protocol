# AITP M5 Host Lifecycle Release Audit

Date: 2026-07-18
Scope: M5 Tasks 3-5 host lifecycle, explicit Research Moment, and generic
Harness Feedback integration.
Decision: repository code, generated-hook verticals, the combined M0-M5 release
lanes, and Kimi plugin package parity are accepted; current workspace project
hook installation is not ready, so M5 overall remains open.

## Implemented Boundary

- The repository characterizes Claude Code, Kimi Code, Codex, and OpenCode from
  their actual configuration owners instead of assuming one shared lifecycle.
- Native events normalize into one allowlisted host-neutral event contract.
- First-turn context uses the existing bounded compiler and runtime receipts.
- Pre/post-tool paths cannot invoke high-authority scientific, trust, baseline,
  session-binding, closeout-apply, or Skill writers.
- Legacy complete-Skill, complete-memory, and stage-guidance injection is
  quarantined. Replacement is exact-plan and human-review gated.
- Readiness separates command-not-found, timeout, nonzero exit, missing or
  conflicting installation, and lifecycle-not-observed states.
- The compact MCP surface remains ten tools; host installation and readiness
  stay on full MCP/CLI maintenance surfaces.
- Harness Feedback writes one generic review-only case family. It cannot author
  an optimization plan, emit Skill lifecycle artifacts, or update claim trust.
- Topic-specific NiO content is fixture-only; historical bundle/dossier
  validators remain read-only compatibility surfaces without runtime builders.
- One full-only MCP/file-backed CLI surface accepts a complete explicit
  Research Event and returns one bounded decision plus an optional receipt.
- All four generated post-tool owners use the same bridge. Raw output remains
  trace-only; only a top-level envelope with five matching identities may enter
  the controller. Nested output is ignored and malformed envelopes return an
  orientation-only diagnostic.
- Dispatch receipts report an actual canonical process write only when the
  validated controller returns new kernel record refs. Semantic staging and all
  ordinary trace/policy/context paths remain `canonical_write=False`.

## Commit Evidence

| Commit | Result |
|---|---|
| `5ff82b6c`, `c76f004d` | host capability characterization and safe fallbacks |
| `457171a5` | normalized bounded host lifecycle dispatch |
| `e387ae6a` | central host writer allowlist and high-authority sentinels |
| `63e8c8ee` | stale legacy context-injection quarantine |
| `b64ff789` | truthful process, installation, lifecycle, and fixture readiness |
| `e9ff8406` | generic typed Harness Feedback cases and fixture-only NiO example |
| `3274abc7` | case-specific runtime retirement and generic CLI/full-MCP integration |
| `292445dc` | validated Research Moments connected to four generated host owners |

## Test Evidence

- Characterization: `22 passed`; generated-owner slice: `26 passed`.
- Normalized dispatch: focused `18 passed`; isolated staged tree
  `121 passed, 1 skipped`.
- Writer boundaries: focused `20 passed`; broad lifecycle/moment slice
  `149 passed, 1 skipped`.
- Injection quarantine: isolated staged core `90 passed`; related adapter
  slice `10 passed`; real generated OpenCode runner slice `4 passed`.
- Truthful readiness: working tree `86 passed`; isolated staged tree
  `86 passed`.
- Host lifecycle/docs/deploy parity on the later Kimi-plugin HEAD:
  `95 passed` in externally authorized system Temp. The preceding managed-sandbox
  attempt was invalidated by pytest basetemp `WinError 5` and is not counted.
- Kimi plugin contract: launcher `py_compile` passed and
  `tests/test_v5_kimi_plugin_package.py` passed `5 passed`. The suite checks
  manifest/marketplace/path closure, repository and topics-root precedence,
  compact-by-default plus explicit-full launcher behavior, packaged-Skill
  compact-call parity, and duplicate project/plugin MCP registration guidance.
  The exact staged package/docs candidate then passed `51 passed`, adding MCP,
  host-readiness, deployment-surface, and architecture-boundary coverage. This
  closes package parity only; it is not project-hook lifecycle evidence.
- The complete `tests/test_v5_adapters.py` file timed out twice at 244 seconds
  during the quarantine checkpoint and is not claimed as passed by this audit.
- Generic Harness Feedback: the first exact staged tree passed `72 passed`; the
  integrated exact staged tree
  `aec978dacd02c0d9ae139e135bf22e26a4ea459d` passed `121 passed`, covering
  typed writes, idempotency/revision/related cases, repeated review, every
  false-authority flag, prohibited Skill paths, registry/capability parity,
  CLI/full MCP, deployment, and architecture budgets.
- Explicit Research Moment and M5 vertical: exact code staged tree
  `ee847d918f1f4eb5834a419377b3bbca463de1f8` passed 186 focused tests in split
  system-Temp runs: core/MCP/architecture `137 passed`, new normal/noise/friction
  vertical `15 passed`, existing real-host lifecycle `21 passed`, and existing
  adapter runners `13 passed`. The adapter file passed in 346.52 seconds after
  earlier combined runs exceeded their 3/5-minute command limits. Compact MCP
  was read back as exactly ten tools.
- Post-truthfulness staged candidate
  `0586993e67a0920ccab885d5f51da14d3d2037ba` passed `70 passed`, covering the
  exact objective host write, deep decision/receipt effect parity, four-host
  semantics, public surfaces, and architecture limits.
- Combined release candidate
  `4a8377b835dcc804506b93737fdb6c2c2b60f429` passed every blocking lane:
  foundation `199 passed, 1 skipped`, compatibility `141 passed`, v5 verticals
  `1369 passed, 3 skipped`, slow adapter `88 passed`, and legacy compatibility
  `200 passed`. This is `1997 passed, 4 skipped` across the lane executions;
  ten legacy-materialization tests intentionally occur in both foundation and
  legacy compatibility. The slow-adapter lane took 645.63 seconds and remains a
  test-infrastructure performance concern, not a bypassed lane.
- The four skips were audited explicitly: one Windows directory-symlink
  condition, one opt-in context performance probe, and the LibRPA plus QFT/QG
  real-machine probes guarded by `AITP_RUN_REAL_VERTICAL_PROBES=1`. The latter
  two remain M6 evidence gaps and are not counted as real-journey acceptance.
- The final candidate exposes 268 classified capabilities, 74 record families,
  and exactly ten compact MCP tools. Runtime registry, static layout, literal
  use, and actual-store drift checks are empty after the audit fix.

All test workspaces and runtime receipts above were isolated under system Temp.
The host dispatch tests assert unchanged canonical watermarks. The only real
store write in this closeout was the separately authorized rebuild of
`.aitp/indexes`; no canonical record was written.

## Real-Store Index And Drift Evidence

Authorized target:

`F:/AI_Workspace/Theoretical-Physics/research/aitp-topics/.aitp/indexes`

Candidate `abc497791fb36c23c3bdc91cf1d2cb3969b65425` performed the authorized
derived-index rebuild. Candidate `4a8377b835dcc804506b93737fdb6c2c2b60f429`
then performed the final read-only registry/layout and freshness audit.

| Measure | Result |
|---|---:|
| Query-index generation | 16 stale -> 17 fresh |
| Index/schema version | 3 / 3 |
| Indexed/checked paths | 9,947 / 9,947 |
| Malformed/build issues | 0 / 0 |
| Runtime-audit registry records | 7,440 |
| Actual populated/storage families | 69 |
| Runtime registry/static layout families | 74 / 74 |
| Registry/layout/literal/actual drift | empty |
| Canonical watermark | `ce44b9c34a6d39448c9a67624091dd786893eed8e24f508c2f4fad24739cdd4a` |
| Canonical file snapshot hash | `a0d365ac6a54a540d10893cb99c7ec0b9803980fd436ef69a6781a4c1fbe413b` |
| Index content hash | `7e1284f857f83c5345b4fc64136e24edf54f926cdfac7cf8c23d873a94ef55ac` |

The before/after canonical path list, every canonical file digest, aggregate
snapshot hash, and canonical watermark were identical. The published manifest
matches the live watermark and reports zero malformed records.

## Live Host Evidence

The 2026-07-18 read-only probe launched each documented `--version` command and
audited its repository-local preferred hook path:

| Host | Process | Project hook audit | Readiness status |
|---|---|---|---|
| Codex | found, exit 0 | `.codex/hooks.json`: missing | `process_ready_installation_incomplete` |
| Claude Code | found, exit 0 | `.claude/settings.local.json`: missing | `process_ready_installation_incomplete` |
| Kimi Code | found, exit 0 | `.kimi/config.toml`: missing | `process_ready_installation_incomplete` |
| OpenCode | found, exit 0 | `.opencode/plugins/aitp-v5.js`: missing | `process_ready_installation_incomplete` |

No live host lifecycle event was claimed. The fixture lifecycle path is covered
by isolated executable tests, but the current workspace must install and audit
its project hooks before a real interactive event can pass.

## Remaining M5 Work

- Install project hooks only when explicitly requested and then rerun
  installation plus real lifecycle smoke. A host command alone is insufficient.

Until this item is closed, the roadmap must not mark M5 Acceptance or the
overall autonomous-host milestone complete.
