# Phase 127: Doctor And Front-Door Verification Hardening - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase hardens the install-verification surface for the three front-door
runtimes that currently define adoption readiness: Codex, Claude Code, and
OpenCode.

The phase covers how `aitp doctor` and `aitp doctor --json` report readiness,
remediation, and convergence truth after install. It does **not** own the
shared quickstart walkthrough itself, the broader first-run proof wording, or
Windows-native bootstrap cleanup unless that work is strictly required to keep
the doctor surface honest.

</domain>

<decisions>
## Implementation Decisions

### Front-Door Runtime Scope
- **D-01:** Treat Codex as the baseline runtime and Claude Code plus OpenCode
  as the front-door parity targets for this phase.
- **D-02:** Keep OpenClaw visible as a specialized lane only. Do not expand
  this phase into OpenClaw parity or loop-lane productization.

### Doctor Contract Shape
- **D-03:** `aitp doctor --json` must expose one per-runtime verification /
  remediation contract instead of only raw issue codes.
- **D-04:** The doctor payload must expose one top-level convergence view so a
  user or CI job can tell whether the three front-door runtimes are aligned
  without reverse-engineering nested rows.

### Human-Readable Output
- **D-05:** Human-readable `aitp doctor` output should summarize front-door
  readiness first, rather than dumping the entire nested payload.
- **D-06:** The human output should tell the user exactly which runtime needs
  repair and what command repairs it.

### the agent's Discretion
- The exact field names may evolve as long as the same install / remediation /
  convergence semantics stay visible and are locked by tests.
- The fallback command can remain `aitp session-start "<task>"` while the
  preferred native bootstrap surface is being repaired.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Backlog And Milestone Scope
- `.planning/BACKLOG.md` — canonical milestone boundary for `999.49`, especially
  the install-verification goal and merged predecessor note.
- `.planning/REQUIREMENTS.md` — current milestone requirement mapping for
  install verification.
- `.planning/ROADMAP.md` — current phase list and ordering for `v1.65`.

### Public Adoption Surface
- `docs/INSTALL.md` — consolidated install index and doctor-facing verification
  entrypoint.
- `docs/INSTALL_CODEX.md` — Codex baseline install and verification language.
- `docs/INSTALL_CLAUDE_CODE.md` — Claude Code SessionStart install and repair
  path.
- `docs/INSTALL_OPENCODE.md` — OpenCode plugin bootstrap and verification path.
- `README.md` — top-level runtime support matrix and install/read-next surface.

### Production Code
- `research/knowledge-hub/knowledge_hub/frontdoor_support.py` — doctor payload
  assembly and install diagnostics.
- `research/knowledge-hub/knowledge_hub/runtime_support_matrix.py` — per-runtime
  readiness classification and remediation metadata.
- `research/knowledge-hub/knowledge_hub/cli_compat_handler.py` — human-readable
  rendering path for `aitp doctor`.
- `research/knowledge-hub/knowledge_hub/cli_frontdoor_handler.py` — public CLI
  registration for `doctor` and migration commands.

### Regression Coverage
- `research/knowledge-hub/tests/test_aitp_service.py` — doctor payload and
  runtime matrix contract tests.
- `research/knowledge-hub/tests/test_aitp_cli.py` — human-readable doctor CLI
  regression.
- `research/knowledge-hub/tests/test_agent_bootstrap_assets.py` — install/doc
  contract coverage for adoption-facing assets.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `build_runtime_support_matrix()` already centralizes runtime readiness
  classification; extend that instead of branching status logic inside the CLI.
- `ensure_cli_installed()` already owns top-level install diagnostics; use it as
  the source of truth for any new convergence fields.
- `emit_payload()` already has a dedicated doctor-rendering branch; keep the
  human-readable summary logic there rather than scattering formatting.

### Established Patterns
- Front-door install/report logic is already extracted out of
  `aitp_service.py`; continue using those helper modules instead of re-growing
  a service hotspot.
- Runtime rows already distinguish `ready`, `partial`, `stale`, and `missing`;
  remediation should explain those states, not replace them.

### Integration Points
- Any new JSON fields added here must stay consistent with install docs and
  migration docs.
- Asset checks for Claude / OpenCode / Codex docs live in
  `test_agent_bootstrap_assets.py`, so doc wording and machine-readable field
  names need to stay aligned.

</code_context>

<specifics>
## Specific Ideas

- The user priority is adoption consistency across OpenCode, Claude Code, and
  Codex, with OpenClaw temporarily deprioritized.
- The install-verification surface should answer both "is this runtime ready?"
  and "what exact command repairs it?".

</specifics>

<deferred>
## Deferred Ideas

- Shared first-run walkthrough content and `bootstrap -> loop -> status` proof
  belong to Phase `128`.
- Windows-native bootstrap cleanup beyond what is needed for doctor honesty
  belongs to Phase `129`.
- `pip install aitp` / PyPI publication remains outside this milestone.

</deferred>

---

*Phase: 127-doctor-and-front-door-verification-hardening*
*Context gathered: 2026-04-11*
