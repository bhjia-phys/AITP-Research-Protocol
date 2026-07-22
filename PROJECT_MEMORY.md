# AITP 2.0 — Active Project Memory

AITP 2.0 is the **sole active implementation target** for this repository.
All AITP v5 repository entrypoints (MCP servers, hooks, plugins, installers,
CLI launchers) are **retired**. Historical v5 source code remains in place
for audit and rollback reference only — it is not an active authority.

## Current Status

**S0 has not started. No installable 2.0 runtime or CLI exists.**
This repository is in the authority-cutover and S0-planning phase.
No 2.0 command distribution is available.

## Architecture

- One global `using-aitp` Skill — host-discovered; triggers on research intent;
  runs `aitp enter`; selects phase commands; no hooks, no MCP, no hidden inference.
- One thin `aitp` CLI — 12 command groups; deterministic operational work;
  renders per-command `SKILL.md + templates + profile.yaml`; does not generate
  physics insight or summarize hidden conversation state.
- Seven canonical node types + one Relation edge schema: Topic, Entity, Route,
  Statement, Episode, Assessment, Asset; Relation with deterministic predicates.
- `.aitp/topics`, `.aitp/shared`, `.aitp/runtime` — fixed local store layout;
  all canonical records are Markdown with small YAML frontmatter; Git is the
  byte history.
- Knowledge Cards (physical understanding) and Workflow Skills (repeatable
  procedure) are two parallel first-class compilation lanes. Both produce
  reviewed outputs backed by exact record provenance. Human gates control
  scientific promotion, Knowledge publish, and Skill install.

## What AITP 2.0 Does Not Require

- No MCP servers in the 2.0 runtime.
- No required host hooks.
- No graph database or vector index for correctness.
- No general context compiler.
- No Agent runtime or second orchestration system.

## Implementation Boundary

- New code lives only in `src/aitp/`.
- `src/aitp/` MUST NOT import any module from `brain/v5/` in production code.
- Legacy code may be read for migration reference, never imported directly.

## Shims

`AGENTS.md` and `CLAUDE.md` are thin shims that point to this file. Their
bytes remain unchanged from the pre-cutover baseline. Do not edit them directly.

## External `.aitp`

External `<topics-root>/.aitp` directories are outside the scope of this
repository cutover. They are handled by the 2.0 CLI store discovery at runtime.

## Local v5 Uninstall

Uninstalling locally installed v5 plugins, MCP configurations, and host hooks
is a separate human-approved operation. It is not part of this repository cutover.

## Key Documents

- Active spec: [docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md](docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md)
- Audit disposition: [docs/superpowers/audits/2026-07-20-aitp-2-0-command-skill-protocol-audit-disposition.md](docs/superpowers/audits/2026-07-20-aitp-2-0-command-skill-protocol-audit-disposition.md)
- Cutover design: [docs/superpowers/specs/2026-07-21-aitp-2-0-repository-authority-cutover-design.md](docs/superpowers/specs/2026-07-21-aitp-2-0-repository-authority-cutover-design.md)
- v5 archive manifest: [docs/legacy/aitp-v5-authority-cutover/archive-manifest.json](docs/legacy/aitp-v5-authority-cutover/archive-manifest.json)
