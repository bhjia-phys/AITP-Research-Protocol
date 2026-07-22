# AITP 2.0

**AITP 2.0** is the sole active development target for the AITP repository.
AITP v5 and its MCP/hook/plugin installation are **retired**. Do not attempt
to install or run v5 from this repository.

**This repository does not yet contain a released or installable 2.0 runtime.** No 2.0 command distribution is available.

Current phase: authority cutover and S0 prerequisites (specifications,
audits, fixture design).

Read [`PROJECT_MEMORY.md`](PROJECT_MEMORY.md) for active development rules.
Read [`docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md`](docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md) for the product design.

## Architecture

AITP 2.0 is a local research-memory protocol operated through commands and
Markdown guides. One global `using-aitp` Skill, one thin `aitp` CLI (12 command
groups), per-command `SKILL.md + templates + profile.yaml`. Seven canonical
node types + one Relation edge. `.aitp/topics|shared|runtime` fixed store.
Markdown + YAML frontmatter; Git as byte history. Knowledge Cards and Workflow
Skills are parallel first-class compilation lanes with human-gated promotion.

## Key Documents

- [PROJECT_MEMORY.md](PROJECT_MEMORY.md) — active development rules
- [docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md](docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md) — product design
- [docs/superpowers/specs/2026-07-21-aitp-2-0-repository-authority-cutover-design.md](docs/superpowers/specs/2026-07-21-aitp-2-0-repository-authority-cutover-design.md) — cutover design
- [docs/legacy/aitp-v5-authority-cutover/](docs/legacy/aitp-v5-authority-cutover/) — v5 archive
