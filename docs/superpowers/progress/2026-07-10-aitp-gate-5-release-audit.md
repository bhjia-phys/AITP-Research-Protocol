# AITP M5 Host Lifecycle Release Audit

Date: 2026-07-18
Scope: M5 Tasks 3-4 host lifecycle and generic Harness Feedback integration.
Decision: host and Harness Feedback implementation accepted; current workspace
host installation not ready; M5 overall remains open.

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
- Kimi plugin read-only smoke: launcher `py_compile` passed; plugin manifest and
  marketplace JSON parsed; all declared packaged Skill/launcher files existed.
  This is not a substitute for the test-backed parity work listed below.
- The complete `tests/test_v5_adapters.py` file timed out twice at 244 seconds
  during the quarantine checkpoint and is not claimed as passed by this audit.
- Generic Harness Feedback: the first exact staged tree passed `72 passed`; the
  integrated exact staged tree
  `aec978dacd02c0d9ae139e135bf22e26a4ea459d` passed `121 passed`, covering
  typed writes, idempotency/revision/related cases, repeated review, every
  false-authority flag, prohibited Skill paths, registry/capability parity,
  CLI/full MCP, deployment, and architecture budgets.

All test workspaces and runtime receipts above were isolated under system Temp.
The host dispatch tests assert unchanged canonical watermarks, and this task did
not write the real research store's canonical records or derived indexes.

## Live Host Evidence

The 2026-07-17 read-only probe launched each documented `--version` command and
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

- Run the normal-session, noise/recursion/failure, and friction-to-dossier M5
  vertical acceptances.
- Run the combined M0-M5 release lanes, architecture budgets, staged-tree audit,
  capability/family drift report, and real canonical watermark proof required
  by M5 Task 5.
- Install project hooks only when explicitly requested and then rerun
  installation plus real lifecycle smoke. A host command alone is insufficient.
- Add test-backed parity checks for the separately committed Kimi Code plugin
  package (manifest, launcher/config resolution, packaged Skills, and duplicate
  MCP/Skill registration guidance). Plugin availability must remain distinct
  from project lifecycle-hook readiness.

Until those items are closed, the roadmap must not mark M5 Acceptance or the
overall autonomous-host milestone complete.
