---
title: AITP 2.0 Repository Authority Cutover
date: 2026-07-21
revised: 2026-07-22
status: design-complete-pending-implementation
authority:
  - docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md
  - docs/superpowers/audits/2026-07-20-aitp-2-0-command-skill-protocol-architecture-audit.md
  - docs/superpowers/audits/2026-07-20-aitp-2-0-command-skill-protocol-audit-disposition.md
evidence_checkpoint: 869d8e65f19e69404405e4da976876be8fc7f9a0 (AITP-2-evidence, read-only)
live_main_baseline: eec20f6faeb089ec2fcdc982ad65adce242a21a9 (origin/main)
scope: >
  Replace v5 as repository active authority.
  Transplant only 7 design/audit/disposition documents from evidence checkpoint.
  Define archival, deactivation, rewrite, guard, CI, rollback, and landing for
  the authority cutover commit. Do not execute cutover in this phase.
---

# AITP 2.0 Repository Authority Cutover

## 1. Decision

The AITP repository changes its active authority from the installed v5/MCP/hook
system to the AITP 2.0 command-and-Skill rewrite. The cutover is executed in one
atomic commit whose scope is defined below. This design is **proposed, pending
Phase 1 self-audit and Oracle Gate 1**; the cutover commit itself occurs in a
separate implementation phase.

The evidence checkpoint (`869d8e65`) is a **read-only design source**, not an
integration branch. Only 7 documents are transplanted from that checkpoint into
the authority worktree. No v5 runtime commits, source code, or cherry-picked
history are carried over. The live origin/main baseline is
`eec20f6faeb089ec2fcdc982ad65adce242a21a9`, and the cutover branch is
`codex/aitp-2-authority-cutover`.

## 2. Transplanted Documents (Phase 1)

Only these 7 documents enter the authority worktree from the evidence
checkpoint. They are content-identical to the evidence source except for the
normalizations noted below:

| # | Path | Type | Normalizations |
|---|------|------|----------------|
| 1 | `docs/superpowers/specs/2026-07-19-aitp-2-0-rewrite-design.md` | Spec | None |
| 2 | `docs/superpowers/audits/2026-07-19-aitp-2-0-rewrite-design-architecture-audit.md` | Audit | Machine paths → symbolic placeholders; source checkpoint added to frontmatter |
| 3 | `docs/superpowers/audits/2026-07-20-aitp-2-0-rewrite-design-audit-disposition.md` | Disposition | None |
| 4 | `docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md` | Spec | None |
| 5 | `docs/superpowers/audits/2026-07-20-aitp-2-0-command-skill-protocol-architecture-audit.md` | Audit | Machine paths → symbolic placeholders; source checkpoint added to frontmatter |
| 6 | `docs/superpowers/audits/2026-07-20-aitp-2-0-command-skill-protocol-audit-disposition.md` | Disposition | None |
| 7 | `docs/superpowers/specs/2026-07-21-aitp-2-0-repository-authority-cutover-design.md` | This document | Full rewrite |

No other file from the evidence worktree may enter the authority worktree during
Phase 1. The evidence worktree itself must not be altered.

## 3. Authority Ordering After Cutover

1. `PROJECT_MEMORY.md` — sole active development and safety rules.
2. `docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md`
   — active product, data, command, and Skill contracts.
3. Reviewed implementation plans — bounded S0-S7 work.
4. `docs/legacy/aitp-v5-authority-cutover/repository/` — archived v5 operating
   material, byte-identical to pre-cutover originals.

No old document, test, plugin, entrypoint, or comment may override this ordering
merely because it still exists in the repository.

## 4. Archive — Preserve Pre-Cutover Active Material

### 4.1 Archive Root and Ledger

```
docs/legacy/aitp-v5-authority-cutover/
├── archive-manifest.json
└── repository/
    ├── PROJECT_MEMORY.md
    ├── README.md
    └── ... (source-relative paths of every deactivated entry)
```

The archive root is `docs/legacy/aitp-v5-authority-cutover/repository/`. Every
archived file keeps its original source-relative path below that root.

### 4.2 Ledger Schema (`archive-manifest.json`)

```jsonc
{
  "source_baseline": "eec20f6faeb089ec2fcdc982ad65adce242a21a9",
  "archived_at": "<ISO-8601>",
  "entries": [
    {
      "source_path": "PROJECT_MEMORY.md",
      "source_commit": "eec20f6faeb089ec2fcdc982ad65adce242a21a9",
      "original_sha256": "<hex>",
      "archive_path": "docs/legacy/aitp-v5-authority-cutover/repository/PROJECT_MEMORY.md",
      "archive_sha256": "<hex>",
      "git_mode": "100644",
      "byte_count": 12345,
      "line_count": 842,
      "byte_interval": "[0, source_size)",
      "line_interval": "1..842"
    }
  ]
}
```

Key constraints:
- `original_sha256` is the SHA-256 of the source file blob bytes as read from
  `git show <source_commit>:<source_path>`, not from the rewritten worktree.
- `archive_sha256` is the SHA-256 of the archived copy on disk after the cutover
  commit. For `PROJECT_MEMORY.md` and `README.md`, the archive is a byte-exact
  copy of the source (no wrapper, no header addition), so `original_sha256` and
  `archive_sha256` MUST be equal.
- `byte_count` and `line_count` are integers.
- `byte_interval` is always `[0, source_size)` for a complete copy.
- `line_interval` is always `1..N` where N is the source file's line count.
- `git_mode` reflects the repository mode of the source file.
- The ledger itself is committed as part of the cutover.
- The cutover commit SHA is NOT recorded in the ledger. It is obtained externally
  from Git history and acceptance records after the commit is created.

### 4.3 Files To Archive

The following live-main files constitute the complete closed inventory for
archival. They must be archived byte-identically
under `docs/legacy/aitp-v5-authority-cutover/repository/` with their source-relative
paths preserved:

1. Root authority files:
   - `PROJECT_MEMORY.md`
   - `README.md`

2. Active discovery/install manifests and packages:
   - `.agents/plugins/marketplace.json`
   - `.claude-plugin/plugin.json`
   - `.codex/INSTALL.md`
   - `plugins/marketplace.kimi.json`
   - `plugins/aitp-research-protocol/.codex-plugin/plugin.json`
   - `plugins/aitp-research-protocol/.mcp.json`
   - `plugins/aitp-research-protocol-kimi/kimi.plugin.json`
   - `plugins/aitp-research-protocol/README.md`
   - `plugins/aitp-research-protocol-kimi/README.md`
   - `research/adapters/openclaw/OPENCLAW_PLUGIN_PROFILE.manifest.json`
   - `research/adapters/openclaw/plugin/aitp-openclaw-runtime/openclaw.plugin.json`
   - `research/adapters/openclaw/plugin/aitp-openclaw-runtime/package.json`
   - `package.json`
   - `aitp-manifest.json`

3. Executable entrypoints/binaries:
   - `bin/aitp-v5.mjs`
   - `scripts/aitp`
   - `scripts/aitp.cmd`
   - `scripts/aitp-local.py`
   - `scripts/aitp-local.cmd`
   - `scripts/aitp-pm.py`

4. Installation documents and active authority prose:
   - `docs/INSTALL.md`
   - `docs/INSTALL_CLAUDE_CODE.md`
   - `docs/INSTALL_CODEX.md`
   - `docs/INSTALL_KIMI_CODE.md`
   - `docs/INSTALL_OPENCLAW.md`
   - `docs/QUICKSTART.md`
   - `docs/PUBLISH_PYPI.md`
   - `docs/MIGRATE_LOCAL_INSTALL.md`
   - `docs/UNINSTALL.md`
   - `docs/README.codex.md`
   - `docs/PROJECT_INDEX.md`
   - `docs/AITP_SPEC.md`
   - `docs/AITP_POSITIONING.md`
   - `docs/AITP_RESEARCH_BRAIN_ROADMAP.md`
   - `docs/AITP_SKILL_LINKAGE.md`
   - `docs/CODEX_APP_1_0_PLAN.md`
   - `docs/AITP_V5_THEORY_RESEARCH_STATE.md`
   - `docs/v5-quiet-research-workflow-architecture.md`
   - `docs/v5-source-asset-pdf-acquisition.md`
   - `docs/architecture.md`
   - `docs/AITP_TOPIC_FOLDER_ARCHITECTURE.md`
   - `docs/MULTI_TOPIC_RUNTIME.md`
   - `docs/AITP_GSD_WORKFLOW_CONTRACT.md`
   - `docs/MIGRATE_MULTI_TOPIC.md`
   - `docs/EXECUTION_PLAN.md`
   - `docs/SESSION_COORDINATION_10WAY.md`

5. Protocol/CI entry points:
   - `brain/PROTOCOL.md`
   - `docs/AUDIT_REPORT_ALIGNMENT.md` (references v5 L0-L4)
   - `.github/workflows/v5-test-lanes.yml`
   - `docs/protocols/TOPIC_NOTEBOOK_OBLIGATION_PROTOCOL.md`

6. Adapter entry points:
   - `adapters/README.md`
   - `adapters/claude-code/SKILL.md`
   - `adapters/codex/SKILL.md`
   - `adapters/openclaw/SKILL.md`
   - `adapters/opencode/SKILL.md`

7. Knowledge-hub and OpenClaw entry points:
   - `research/knowledge-hub/README.md`
   - `research/knowledge-hub/LAYER_MAP.md`
   - `research/knowledge-hub/runtime/TOPIC_TRUTH_ROOT_CONTRACT.md`
   - `research/adapters/openclaw/PLUGIN_PROFILE_INSTALL.md`
   - `research/adapters/openclaw/BOOTSTRAP.md`
   - `research/adapters/openclaw/AITP_AGENT_ENTRYPOINT.md`

This inventory is closed — no paths may be added during Phase 2 execution.
Adding a new archival path requires amending this design document, revising the
action matrix (§5.1) and allowlist derivation (§9.4) accordingly, and re-passing
Oracle Gate 1 (§10.1). This preserves the allowlist set equality contract in §9.4.

### 4.4 Posts Not Archived — KEEP-HISTORICAL

These files are historical source code and inert payload. They remain in place
byte-identical to the baseline and MUST NOT be modified, deleted, or replaced.
They may retain v5 content because all discovery manifests, installer documents,
and default entry-point docs that reference them have been archived and
deactivated (DELETE/REPLACE/MODIFY):

- `brain/v5/**` — all v5 source code
- `hooks/**` — hook implementations (source, not manifests)
- `deploy/**` — deployment configs/templates
- `plugins/aitp-research-protocol/scripts/**` — plugin launcher payload
- `plugins/aitp-research-protocol/skills/**` — plugin Skill payload
- `plugins/aitp-research-protocol-kimi/scripts/**` — plugin launcher payload
- `plugins/aitp-research-protocol-kimi/skills/**` — plugin Skill payload
- `research/adapters/openclaw/scripts/**` — OpenClaw runtime payload
- `research/adapters/openclaw/plugin/**` — OpenClaw plugin source (except manifest JSON and package.json files which are DELETEd)
- `scripts/split_*.py` — v5 split utilities
- `scripts/run_v5_test_lanes.py` — v5 test runner
- `tests/**` — v5 test suites
- `bin/convert_legacy_to_v2.py`, `bin/migrate_legacy_topics.py`, etc. — historical utilities
- `contracts/**` — zero-diff protected
- `schemas/**` — zero-diff protected
- `research/knowledge-hub/canonical/**` — zero-diff protected
- `research/knowledge-hub/` non-entry payload (excludes REPLACEd entry-point files and `runtime/TOPIC_TRUTH_ROOT_CONTRACT.md`) — internal historical records; local source-of-truth terminology within these files is not repo authority
- `docs/CHARTER.md` — historical; has no active/canonical status; any conflicting authority claim was in the now-retired `docs/architecture.md`
- `docs/protocols/**` except `TOPIC_NOTEBOOK_OBLIGATION_PROTOCOL.md` (which is REPLACEd) — historical subordinate material; inactive because the parent `docs/AITP_SPEC.md` is REPLACEd
- Timestamped design history (`docs/superpowers/plans/`, `docs/superpowers/progress/`) — historical

Guard MUST NOT require zero v5 tokens in KEEP-HISTORICAL files. It MUST verify
that no active manifest, default doc, or CI workflow references them as current
operational targets. The guard checks references, not historical file content.

## 5. Deactivation — Active Entry Points

### 5.1 Action Matrix

The cutover commit must deactivate every active entry point. The matrix
distinguishes three actions:

| Action | Meaning |
|--------|---------|
| **DELETE** | Remove from repository. The archival copy in `docs/legacy/aitp-v5-authority-cutover/repository/` is the canonical byte-identical record. |
| **REPLACE** | Overwrite with a retirement notice. The file still exists at the original path but contains only a message directing readers to the 2.0 authority and the archival copy. |
| **MODIFY** | Edit in place with specific changes. The file is archived byte-identically first, then modified. |

#### Discovery manifests, package files, binary entry points (**DELETE**)

| Source Path | Action |
|-------------|--------|
| `.agents/plugins/marketplace.json` | DELETE |
| `.claude-plugin/plugin.json` | DELETE |
| `plugins/marketplace.kimi.json` | DELETE |
| `plugins/aitp-research-protocol/.codex-plugin/plugin.json` | DELETE |
| `plugins/aitp-research-protocol/.mcp.json` | DELETE |
| `plugins/aitp-research-protocol-kimi/kimi.plugin.json` | DELETE |
| `research/adapters/openclaw/OPENCLAW_PLUGIN_PROFILE.manifest.json` | DELETE |
| `research/adapters/openclaw/plugin/aitp-openclaw-runtime/openclaw.plugin.json` | DELETE |
| `research/adapters/openclaw/plugin/aitp-openclaw-runtime/package.json` | DELETE |
| `package.json` | DELETE |
| `aitp-manifest.json` | DELETE |
| `bin/aitp-v5.mjs` | DELETE |
| `scripts/aitp` | DELETE |
| `scripts/aitp.cmd` | DELETE |
| `scripts/aitp-local.py` | DELETE |
| `scripts/aitp-local.cmd` | DELETE |
| `scripts/aitp-pm.py` | DELETE |

#### Installation/protocol documents (**REPLACE** with retirement notice)

| Source Path | Action |
|-------------|--------|
| `.codex/INSTALL.md` | REPLACE: retirement notice |
| `docs/INSTALL.md` | REPLACE: retirement notice |
| `docs/INSTALL_CLAUDE_CODE.md` | REPLACE: retirement notice |
| `docs/INSTALL_CODEX.md` | REPLACE: retirement notice |
| `docs/INSTALL_KIMI_CODE.md` | REPLACE: retirement notice |
| `docs/INSTALL_OPENCLAW.md` | REPLACE: retirement notice |
| `docs/QUICKSTART.md` | REPLACE: retirement notice |
| `docs/PUBLISH_PYPI.md` | REPLACE: retirement notice |
| `docs/MIGRATE_LOCAL_INSTALL.md` | REPLACE: retirement notice |
| `docs/UNINSTALL.md` | REPLACE: retirement notice. Must state that local v5 uninstall is a separate human-approved operation, not part of this repository cutover. Must NOT contain any uninstall commands, shell scripts, or package manager directives. |
| `plugins/aitp-research-protocol/README.md` | REPLACE: retirement notice |
| `plugins/aitp-research-protocol-kimi/README.md` | REPLACE: retirement notice |
| `brain/PROTOCOL.md` | REPLACE: retirement notice |
| `docs/AUDIT_REPORT_ALIGNMENT.md` | REPLACE: retirement notice |
| `docs/README.codex.md` | REPLACE: retirement notice |
| `docs/PROJECT_INDEX.md` | REPLACE: retirement notice |
| `docs/AITP_SPEC.md` | REPLACE: retirement notice |
| `docs/AITP_POSITIONING.md` | REPLACE: retirement notice |
| `docs/AITP_RESEARCH_BRAIN_ROADMAP.md` | REPLACE: retirement notice |
| `docs/AITP_SKILL_LINKAGE.md` | REPLACE: retirement notice |
| `docs/CODEX_APP_1_0_PLAN.md` | REPLACE: retirement notice |
| `docs/AITP_V5_THEORY_RESEARCH_STATE.md` | REPLACE: retirement notice |
| `docs/v5-quiet-research-workflow-architecture.md` | REPLACE: retirement notice |
| `docs/v5-source-asset-pdf-acquisition.md` | REPLACE: retirement notice |
| `adapters/README.md` | REPLACE: retirement notice |
| `adapters/claude-code/SKILL.md` | REPLACE: retirement notice |
| `adapters/codex/SKILL.md` | REPLACE: retirement notice |
| `adapters/openclaw/SKILL.md` | REPLACE: retirement notice |
| `adapters/opencode/SKILL.md` | REPLACE: retirement notice |
| `research/knowledge-hub/README.md` | REPLACE: retirement notice |
| `research/knowledge-hub/LAYER_MAP.md` | REPLACE: retirement notice |
| `research/adapters/openclaw/PLUGIN_PROFILE_INSTALL.md` | REPLACE: retirement notice |
| `research/adapters/openclaw/BOOTSTRAP.md` | REPLACE: retirement notice |
| `research/adapters/openclaw/AITP_AGENT_ENTRYPOINT.md` | REPLACE: retirement notice |
| `docs/architecture.md` | REPLACE: retirement notice |
| `docs/AITP_TOPIC_FOLDER_ARCHITECTURE.md` | REPLACE: retirement notice |
| `docs/MULTI_TOPIC_RUNTIME.md` | REPLACE: retirement notice |
| `docs/AITP_GSD_WORKFLOW_CONTRACT.md` | REPLACE: retirement notice |
| `docs/MIGRATE_MULTI_TOPIC.md` | REPLACE: retirement notice |
| `docs/EXECUTION_PLAN.md` | REPLACE: retirement notice |
| `docs/SESSION_COORDINATION_10WAY.md` | REPLACE: retirement notice |
| `docs/protocols/TOPIC_NOTEBOOK_OBLIGATION_PROTOCOL.md` | REPLACE: retirement notice |
| `research/knowledge-hub/runtime/TOPIC_TRUTH_ROOT_CONTRACT.md` | REPLACE: retirement notice |

#### CI workflow (**MODIFY** to manual-only)

| Source Path | Action |
|-------------|--------|
| `.github/workflows/v5-test-lanes.yml` | MODIFY: remove all automatic triggers; keep `workflow_dispatch` only. Archive byte-identical copy first. |

#### Retirement Notice Template (fail-closed)

Every REPLACE file MUST use exactly this content (parameterized by archive path):

```text
# AITP v5 entrypoint retired

AITP v5 is retired. `PROJECT_MEMORY.md` is the sole active authority.
Historical content: `docs/legacy/aitp-v5-authority-cutover/repository/<source-relative-path>`.
```

The template is exactly 4 lines (heading + blank line + body line + archive path
line). The heading MUST be `# AITP v5 entrypoint retired` (exact string). The
body line MUST be exactly `AITP v5 is retired. \`PROJECT_MEMORY.md\` is the sole active authority.`
The archive path line MUST be exactly `Historical content: \`<archive path>\`.`
where `<archive path>` is the full source-relative path under
`docs/legacy/aitp-v5-authority-cutover/repository/`. No other text, no fenced
code blocks, no URLs, no pip/npm/mcp/install commands, no shell commands.

Exception for `docs/UNINSTALL.md`: append a fifth line:
```text
Local uninstall is a separate operation and requires explicit human approval.
```
Total: exactly 5 logical lines for UNINSTALL.md, exactly 4 logical lines for all
other REPLACE files.

**Byte-level freeze**: All retirement notices MUST be encoded as UTF-8, LF-only
line endings (`\n`, no `\r\n`), no BOM. The last line MUST be followed by
exactly one `\n` (the file ends with a newline). The guard constructs the
expected bytes for each REPLACE file (exact template + archive path substitution)
and performs byte-for-byte comparison — no newline normalization, no whitespace
trimming, no encoding tolerance.

The authority guard MUST verify every REPLACE file byte-for-byte against its
expected template (exact heading, exact sentence, exact archive path, line
count, no extra content). Broad token search is insufficient.

### 5.2 Files NOT Deleted or Modified

These files remain byte-identical to the live-main baseline:

- `AGENTS.md` — thin shim; unchanged.
- `CLAUDE.md` — thin shim; unchanged.

These trees are **KEEP-HISTORICAL** — source/payload preserved in place; may
retain v5 content; not deactivated because manifests/installers/default docs
no longer reference them. They are NOT in DELETE/REPLACE/MODIFY:

- `brain/v5/**` — v5 source code
- `hooks/**` — hook implementations (source, not manifests)
- `deploy/**` — deployment configs/templates
- `plugins/aitp-research-protocol/scripts/**` — plugin launcher payload
- `plugins/aitp-research-protocol/skills/**` — plugin Skill payload
- `plugins/aitp-research-protocol-kimi/scripts/**` — plugin launcher payload
- `plugins/aitp-research-protocol-kimi/skills/**` — plugin Skill payload
- `research/adapters/openclaw/scripts/**` — OpenClaw runtime payload
- `research/adapters/openclaw/plugin/**` — OpenClaw plugin source (except DELETEd manifest JSONs)
- `scripts/run_v5_test_lanes.py` — historical test runner (not in DELETE/REPLACE)
- `tests/**` — v5 test suites
- `docs/CHARTER.md` — historical; no active status (conflicting claim was in now-retired `docs/architecture.md`)
- `docs/protocols/**` except `TOPIC_NOTEBOOK_OBLIGATION_PROTOCOL.md` (which is REPLACEd) — historical subordinate material to REPLACEd `docs/AITP_SPEC.md`
- `research/knowledge-hub/**` non-entry payload (excludes REPLACEd `README.md`, `LAYER_MAP.md`, `runtime/TOPIC_TRUTH_ROOT_CONTRACT.md`, and zero-diff `canonical/`) — internal historical; local source-of-truth terms are not repo authority
- Timestamped design history — `docs/superpowers/plans/`, `docs/superpowers/progress/`

Zero-diff protected (also KEEP-HISTORICAL but with active verification):
- `research/knowledge-hub/canonical/**`
- `contracts/**`
- `schemas/**`

Guards MUST NOT require zero v5 tokens in KEEP-HISTORICAL files. Guards check
that active manifests/installer/default docs do not reference them as current
operational targets.

## 6. Root Rewrites

### 6.1 `PROJECT_MEMORY.md` — Full Replacement

The pre-cutover `PROJECT_MEMORY.md` (842 lines, live-main SHA) is archived
byte-identically at `docs/legacy/aitp-v5-authority-cutover/repository/PROJECT_MEMORY.md`.
The root `PROJECT_MEMORY.md` is completely rewritten. The new file MUST:

1. State that AITP 2.0 is the **sole active implementation target**.
2. Summarize the 2.0 architecture:
   - One global `using-aitp` Skill (host-discovered, triggers on research
     intent, runs `aitp enter`, selects phase commands, runs `aitp checkpoint`
     and `aitp closeout`; no hooks, no MCP, no hidden inference).
   - One thin `aitp` CLI (12 command groups; deterministic operational work;
     renders command Skills; does not generate physics insight or summarize
     hidden conversation state).
   - Per-command `SKILL.md + templates + profile.yaml` (bundled package
     resources; discovered only when the command is used; NOT globally
     registered with the host).
   - Seven canonical node types + one Relation edge schema (Topic, Entity,
     Route, Statement, Episode, Assessment, Asset; Relation with deterministic
     predicates).
   - `.aitp/topics|shared|runtime` — fixed local store layout; all canonical
     records are Markdown with small YAML frontmatter; Git is the byte history.
   - Knowledge Cards (physical understanding) and Workflow Skills (repeatable
     procedure) are two parallel first-class compilation lanes. Both produce
     reviewed outputs backed by exact record provenance. Human promotion,
     publish, and install are explicit gates; nothing is auto-shared across
     topics.
3. State what AITP 2.0 does **not** require:
   - No MCP servers in the 2.0 runtime.
   - No required host hooks.
   - No graph database or vector index for correctness.
   - No general context compiler.
   - No Agent runtime or second orchestration system.
4. State the implementation boundary:
   - New code lives only in `src/aitp/`.
   - `src/aitp/` MUST NOT import any module from `brain/v5/` in production code.
   - Legacy code may be read for migration semantics or reimplemented behind a
     2.0 contract, but never imported directly.
5. State the current status:
   - **S0 has not started. No 2.0 CLI is installable.**
   - The repository currently contains specifications, audits, and this
     cutover design. No executable `aitp` command exists.
   - S0 fixture/provenance freeze precedes S1 implementation.
   - S1 implements store discovery + `enter`, `search`, `show`, `admin init`,
     `admin doctor`.
6. State the shim rule:
   - `AGENTS.md` and `CLAUDE.md` are thin shims pointing to this file. Their
     bytes remain unchanged from the live-main baseline.
7. Link to the active spec: `docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md`.

The new `PROJECT_MEMORY.md` links to the active design, audit disposition,
implementation sequence, and v5 archive rather than repeating their detail.

### 6.2 `README.md` — Full Replacement

The pre-cutover `README.md` (875 lines, live-main SHA) is archived
byte-identically at `docs/legacy/aitp-v5-authority-cutover/repository/README.md`.
The root `README.md` is completely replaced. The new file MUST:

1. **First viewport** (what a visitor sees without scrolling):
   - "**AITP 2.0** is the sole active development target for the AITP
     repository."
   - "AITP v5 and its MCP/hook/plugin installation are **retired**. Do not
     attempt to install or run v5 from this repository."
   - "**This repository does not yet contain a released 2.0 runtime.** No
     `pip install`, `npm install`, or CLI command is available."
   - "Current phase: authority cutover and S0 prerequisites (specifications,
     audits, fixture design)."
   - "Read `PROJECT_MEMORY.md` for active development rules."
   - "Read `docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md` for the product design."

2. No v5 installation instructions, production run examples, MCP registration
   commands, hook installation steps, npm/pip install commands, or plugin
   marketplace instructions.

3. No v5 operational prose of any kind. The old README exists only in the
   archive tree at `docs/legacy/aitp-v5-authority-cutover/repository/README.md`.

4. The remaining content should be minimal: a brief architecture summary
   (command-and-Skill, 7 nodes, Git-backed store) and links to key documents.

### 6.3 Shim Stability

`AGENTS.md` and `CLAUDE.md` remain **byte-identical** to their live-main
versions. They are thin shims that point to `PROJECT_MEMORY.md`. Replacing the
canonical memory switches compatible Agents without changing the shims.

Verification: after the cutover commit, `git diff eec20f6faeb089ec2fcdc982ad65adce242a21a9 -- AGENTS.md`
must produce empty output, and `git diff eec20f6faeb089ec2fcdc982ad65adce242a21a9 -- CLAUDE.md` must produce
empty output.

## 7. CI Rework

### 7.1 v5 CI — Remove Automatic Triggers

The v5 test workflow at `.github/workflows/v5-test-lanes.yml` is modified in
place (not deleted):

- **Remove** triggers: `pull_request`, `push: branches: [main]`, `schedule`.
- **Keep** only: `workflow_dispatch`.
- **Keep** all jobs as-is, but adjust:
  - `m0-fast`: change `if: github.event_name != 'schedule'` to
    `if: github.event_name == 'workflow_dispatch'`.
  - `slow-adapter`: keep `if: github.event_name == 'workflow_dispatch'`.
  - `scheduled-full-suite`: remove `if: github.event_name == 'schedule'`,
    replace with `if: github.event_name == 'workflow_dispatch'`.
- **Update** workflow `name` to: "AITP v5 test lanes (historical — manual trigger only)".

After this change, no v5 job can run automatically on any PR, push, or cron
schedule. All v5 jobs are manual `workflow_dispatch` only.

### 7.2 New Authority Guard CI

Create `.github/workflows/authority-guard.yml`:

```yaml
name: Repository Authority Guard
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  guard:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Run authority guard
        run: python scripts/check_repository_authority.py
```

The guard script (`scripts/check_repository_authority.py`) is a standalone
standard-library Python script. It MUST NOT import `brain/`, `src/aitp/` (which
does not exist yet), or any v5 module. It runs on PR and push to main.

The guard anchors to the repository root via `git rev-parse --show-toplevel`.
All changed-path checks use `git diff --name-only eec20f6faeb089ec2fcdc982ad65adce242a21a9 HEAD -- <repo-relative pathspec>`.
The guard does NOT rely on unstaged `git diff` for PR/push contexts.

Checks:

1. **DELETE paths — fail on existence**: For every path in the DELETE list in
   §5.1, fail if the file exists at the original path. Content is irrelevant;
   mere existence at the source path after cutover is a violation.

2. **REPLACE paths — exact template match**: For every path in the REPLACE list
   in §5.1, verify the file content byte-for-byte matches the expected template.
   The expected content is the parametrized retirement notice template defined in
   §5.1 with the correct archive path substituted. Verification: exact heading
   `# AITP v5 entrypoint retired`, exact body sentence, exact archive path line,
   total line count exactly 4 (exactly 5 for `docs/UNINSTALL.md`), no fenced code blocks, no
   URLs, no pip/npm/mcp/shell command patterns. The 43 REPLACE paths are:

   `.codex/INSTALL.md`, `docs/INSTALL.md`, `docs/INSTALL_CLAUDE_CODE.md`,
   `docs/INSTALL_CODEX.md`, `docs/INSTALL_KIMI_CODE.md`,
   `docs/INSTALL_OPENCLAW.md`, `docs/QUICKSTART.md`, `docs/PUBLISH_PYPI.md`,
   `docs/MIGRATE_LOCAL_INSTALL.md`, `docs/UNINSTALL.md`,
   `docs/README.codex.md`, `docs/PROJECT_INDEX.md`, `docs/AITP_SPEC.md`,
   `docs/AITP_POSITIONING.md`, `docs/AITP_RESEARCH_BRAIN_ROADMAP.md`,
   `docs/AITP_SKILL_LINKAGE.md`, `docs/CODEX_APP_1_0_PLAN.md`,
   `docs/AITP_V5_THEORY_RESEARCH_STATE.md`,
   `docs/v5-quiet-research-workflow-architecture.md`,
   `docs/v5-source-asset-pdf-acquisition.md`, `docs/AUDIT_REPORT_ALIGNMENT.md`,
   `plugins/aitp-research-protocol/README.md`,
   `plugins/aitp-research-protocol-kimi/README.md`,
   `brain/PROTOCOL.md`, `adapters/README.md`,
   `adapters/claude-code/SKILL.md`, `adapters/codex/SKILL.md`,
   `adapters/openclaw/SKILL.md`, `adapters/opencode/SKILL.md`,
   `research/knowledge-hub/README.md`,
   `research/knowledge-hub/LAYER_MAP.md`,
   `research/adapters/openclaw/PLUGIN_PROFILE_INSTALL.md`,
   `research/adapters/openclaw/BOOTSTRAP.md`,
   `research/adapters/openclaw/AITP_AGENT_ENTRYPOINT.md`,
   `docs/architecture.md`,
   `docs/AITP_TOPIC_FOLDER_ARCHITECTURE.md`,
   `docs/MULTI_TOPIC_RUNTIME.md`,
   `docs/AITP_GSD_WORKFLOW_CONTRACT.md`,
   `docs/MIGRATE_MULTI_TOPIC.md`, `docs/EXECUTION_PLAN.md`,
   `docs/SESSION_COORDINATION_10WAY.md`,
   `docs/protocols/TOPIC_NOTEBOOK_OBLIGATION_PROTOCOL.md`,
   `research/knowledge-hub/runtime/TOPIC_TRUTH_ROOT_CONTRACT.md`.

3. **MODIFY path — v5 CI trigger contract**: `.github/workflows/v5-test-lanes.yml`
   must ONLY have `workflow_dispatch` trigger. The guard parses the file
   line-by-line with standard-library Python (no PyYAML). It locates the
   column-0 `on:` key, then collects all exactly-two-space-indented event keys
   until the next column-0 key. The resulting event-key set MUST be exactly
   `{workflow_dispatch}`. Whole-file grep for `schedule` is forbidden — it
   would falsely match the `scheduled-full-suite` job name. Additionally,
   verify every job-level `if:` condition references
   `github.event_name == 'workflow_dispatch'` (no `schedule`, no bare push/PR
   conditions). Job names and job body may remain as-is.

4. **Root authority**: Fail if:
   - `PROJECT_MEMORY.md` references v5 as active or contains v5 install/run
     instructions.
   - `README.md` first 40 lines contain v5 operational content.

5. **Shim no-drift**: Fail if `AGENTS.md` or `CLAUDE.md` differ from their
   baseline bytes at `eec20f6faeb089ec2fcdc982ad65adce242a21a9`.

6. **Legacy imports**: Fail if any `.py` file under `src/aitp/` imports from
   `brain/`, `brain.v5`, or `brain/` subpackages.

7. **Archive ledger — unconditional**: The file
   `docs/legacy/aitp-v5-authority-cutover/archive-manifest.json` MUST exist
   (missing ledger is FAIL). Verify every `original_sha256` by computing SHA-256
   on `git show <source_commit>:<source_path>` (NOT the worktree file). Verify
   every `archive_sha256` matches the archived file on disk. For
   `PROJECT_MEMORY.md` and `README.md` entries, verify
   `original_sha256 == archive_sha256`. Verify the ledger's `source_path` set
   is set-equal to the closed archive inventory in §4.3. Verify every archive
   path exists on disk. Verify `git_mode`, `byte_count`, `line_count`,
   `byte_interval`, and `line_interval` match the actual file. Verify every
   retirement notice's archive path mapping is consistent with the ledger.
   Missing any archivable entry, extra entry, or hash/boundary mismatch is FAIL.

8. **Strong authority-marker guard**: Repo-root-anchored scan of all tracked
   Markdown files. Exclude: `archive/`, `docs/archive/`, `docs/legacy/`,
   `docs/superpowers/`, `docs/session_reports/`, `.planning/`, `tests/`,
   `output/`, `tmp/`, `build/`, `generated/`, `.git/`, and all KEEP-HISTORICAL paths in
   §4.4/§5.2.
   Among the remaining non-retirement Markdown surfaces, FAIL if any file
   contains an old authority marker pattern:
   - `Status:` or `status:` followed by `active` or `canonical`
   - `highest public authority`
   - `active local workflow rule`
   - `active runtime contract`
   - `single source of truth` (with or without hyphens)
   - `authoritative active-topic`
   This check does NOT require zero v5 tokens in KEEP-HISTORICAL files. It does
   NOT scan external `.aitp`.

9. **Canonical zero-diff and changed-path protection**: Fail if
   `git diff --name-only eec20f6faeb089ec2fcdc982ad65adce242a21a9 HEAD -- research/knowledge-hub/canonical/ contracts/ schemas/`
   produces any output.

10. **`.aitp/` boundary**: Only check repo-root `.aitp/` (the directory
   `<repo-root>/.aitp/`). Fail if the current diff modifies any file under repo-root
   `.aitp/`. Do NOT `rglob('.aitp')`, traverse parent directories, or scan
   outside the repository root. External `<topics-root>/.aitp` directories are
   never read, written, or scanned.

These three trees — `research/knowledge-hub/canonical/`, `contracts/`,
`schemas/` — are v5 historical and canonical-contract surfaces. Under 2.0
authority they are frozen; the guard uses `git diff` against the baseline
`eec20f6faeb089ec2fcdc982ad65adce242a21a9` to verify no modification.

The CI checkout requires `fetch-depth: 0` because the source baseline
`eec20f6faeb089ec2fcdc982ad65adce242a21a9` must be reachable for `git show` and
`git diff` operations. Shallow clones that do not contain this commit will cause
guard failures.

The guard script reports each violation as a single line:
`FAIL <check-name>: <path> — <reason>`. Exit code 0 on all-clear, 1 on any
violation.

## 8. Data Safety and External Boundaries

### 8.1 External `.aitp`

The cutover design and guard:
- Only consider repo-root `.aitp/` (the directory at `<repo-root>/.aitp/`).
- Do NOT `rglob('.aitp')`, traverse parent directories, or scan outside the
  repository root.
- Do NOT read, write, or validate any external `<topics-root>/.aitp`.
- Do NOT use `repo diff` to assert anything about external `.aitp` stores.
- Explicitly state that external `.aitp` directories are outside the
  repository's scope and are handled by the 2.0 CLI store discovery at
  runtime, not during authority cutover.

### 8.2 Zero-Diff Canonical Protection

The following directory trees receive explicit zero-diff protection in the guard
and in the cutover verification:

- `research/knowledge-hub/canonical/`
- `contracts/`
- `schemas/`

The cutover commit MUST NOT modify any file under these trees. The authority
guard CI MUST fail if any future commit modifies them.

### 8.3 Local Plugin/MCP/Hook Uninstall

**This is a separate human-approved operation, not part of the repository
cutover commit.** The cutover only changes repository contents. Local machine
state (installed Codex/Kimi/Claude plugins, MCP configuration, host hooks)
remains as-is until the machine owner explicitly approves and executes an
uninstall procedure. The cutover design does not define that procedure; it is
out of scope for repository authority and will be documented separately.

The local uninstall operation must:
- Be explicitly requested and approved by the machine owner.
- Be reversible (re-install from a historical repo tag if the v5 plugin source
  is preserved).
- Be verified by the owner, not by automated repository CI.

This separation is deliberate: repository authority and local machine
installation are independent concerns.

## 9. Cutover Commit Structure

### 9.1 Single Atomic Commit

All archive, deactivation, rewrite, guard, and CI modifications land in a
**single atomic commit** on the `codex/aitp-2-authority-cutover` branch. The
commit message must follow this template:

```
docs: cut over repository authority from AITP v5 to 2.0

- Archive pre-cutover PROJECT_MEMORY.md, README.md, and all active entry
  points under docs/legacy/aitp-v5-authority-cutover/repository/
- Add archive-manifest.json with exact SHA-256, byte/line intervals
- Deactivate v5 discovery manifests, bin/scripts, install docs
- Replace PROJECT_MEMORY.md and README.md with 2.0 authority content
- Keep AGENTS.md/CLAUDE.md byte-identical (shims)
- Restrict v5 CI to workflow_dispatch only
- Add authority-guard CI workflow and check script
- Zero-diff protect canonical/, contracts/, schemas/
- Commit touches exactly the Phase 2 allowlist (see §9.4)

Authority: docs/superpowers/specs/2026-07-21-aitp-2-0-repository-authority-cutover-design.md
Evidence checkpoint: 869d8e65f19e69404405e4da976876be8fc7f9a0
Live-main baseline: eec20f6faeb089ec2fcdc982ad65adce242a21a9
```

### 9.2 Commit Ordering

1. **Phase 1 (this design)** — commit the 7 transplanted documents (including
   this design) to the cutover branch. This is the specification commit.
2. **Phase 2 (implementation)** — commit the archive, deactivation, rewrites,
   guard, and CI changes. This is the cutover execution commit. The commit
   must touch exactly the allowlist derived in §9.4 — no more, no fewer paths.
3. **Phase 3 (S0 implementation plan)** — write and commit an S0 implementation
   plan. The plan must describe: desensitized source-derived fixture structures,
   the 12 command contracts, record profiles, the command Skill package
   contract, and the simplicity CI design. The S0 plan does NOT create any
   fixtures, directory scaffolding, package `__init__.py`, or implementation
   code. S1 CLI implementation must not begin until the S0 plan passes review.

### 9.3 Rollback

Rollback is the exact `git revert <phase2-sha>` of the Phase 2 cutover commit,
applied on the development branch or after merge to main. The `<phase2-sha>` is
the full 40-character SHA recorded in the acceptance record (not in the ledger).
Because this is a
single atomic revert, the new archive tree (`docs/legacy/`) and ledger created
by the cutover commit will also be removed from the current working tree. This
is expected: `git revert` exactly inverts the commit's diff.

The archival evidence is preserved in the reverted commit's Git history and can
be recovered at any time via `git show <phase2-sha>:<path>`. If a user needs
the archive to remain in the working tree after rollback, that requires extra
non-atomic operations (e.g., cherry-picking only part of the revert, or
restoring the archive from the reverted commit after revert). These non-atomic
alternatives are not part of this design.

The revert must:

1. Restore `PROJECT_MEMORY.md`, `README.md`, and all deactivated/deleted entry
   points to their pre-cutover state.
2. Remove the authority guard workflow and script.
3. Restore the v5 CI triggers.
4. NOT touch external `.aitp` or any local machine configuration.

Post-rollback verification:
- All deleted entry points are restored (compare with source paths in the
  cutover commit's `archive-manifest.json` via `git show`).
- `AGENTS.md` and `CLAUDE.md` are byte-identical to live-main baseline.
- `research/knowledge-hub/canonical/`, `contracts/`, `schemas/` have zero diff
  against live-main baseline.
- `git diff --check` passes.

### 9.4 Phase 2 Exact Allowlist Contract

The Phase 2 commit must touch exactly the following paths — no more, no fewer.
The staged set and final commit tree diff against baseline must be set-equal to
this list.

**Derivation rules:**

1. **Archive tree paths**: For every path in the DELETE, REPLACE, and MODIFY
   lists, derive one archive path:
   `docs/legacy/aitp-v5-authority-cutover/repository/<source-path>`. Plus root
   entries for `PROJECT_MEMORY.md` and `README.md`. Plus the ledger itself:
   `docs/legacy/aitp-v5-authority-cutover/archive-manifest.json`.

2. **Active changed paths**:
   - `PROJECT_MEMORY.md` (rewritten)
   - `README.md` (rewritten)
   - Every DELETE path (removed from worktree)
   - Every REPLACE path (overwritten with retirement template)
   - `.github/workflows/v5-test-lanes.yml` (MODIFY)
   - `.github/workflows/authority-guard.yml` (new)
   - `scripts/check_repository_authority.py` (new)

3. **Explicitly excluded from changed set**:
   - `AGENTS.md` and `CLAUDE.md` — byte-identical shims
   - `research/knowledge-hub/canonical/`, `contracts/`, `schemas/` — zero-diff frozen
   - All KEEP-HISTORICAL paths listed in §4.4 and §5.2

The exact allowlist (all paths, machine-comparable) is generated from this
design matrix before Phase 2 implementation. The staged paths and commit diff
names must be set-equal to the generated allowlist.

## 10. Default Branch Landing Conditions

### 10.1 Phase 1 / Gate 1 Start Checklist

Before Phase 2 implementation can begin, the following items must be verified.
These are the only items that can be checked with only Phase 1 artifacts (no
archive tree, no ledger, no rewrites, no guard script exists yet):

| # | Check | Acceptance |
|---|-------|------------|
| G1-1 | Seven Phase 1 documents committed | Exact 7 paths committed to cutover branch; no extra files |
| G1-2 | Worktree clean | `git status --short` shows only Phase 1 untracked paths or nothing (after commit) |
| G1-3 | Frontmatter and review links resolve | All `authority:`, `scope:`, `evidence_checkpoint:`, `live_main_baseline:` in frontmatter point to existing files/commits |
| G1-4 | Machine paths normalized | Zero absolute machine paths in the 7 documents (Unix user-home absolute paths, Windows drive-qualified paths, or any other machine-specific absolute paths) |
| G1-5 | Live `origin/main` equals baseline | `git fetch origin && git rev-parse origin/main` strictly equals `eec20f6faeb089ec2fcdc982ad65adce242a21a9`. If not: STOP; do not rebase/continue. Re-inventory, update baseline/archive hashes/action matrix/design, and re-pass Gate 1. |
| G1-6 | Cutover design self-review complete | All reviewer findings addressed; no unresolved P0 |
| G1-7 | Oracle Gate 1 pass | Independent Oracle review (Gate 1) confirms no blocking findings |

Only after G1-1 through G1-7 all pass may Phase 2 implementation begin. The
Phase 2 completion checklist (§11) runs only after Phase 2 artifacts are
produced — it must NOT appear as a Phase 2 start prerequisite.

### 10.2 Baseline Freshness and Merge Identity

Before Phase 2 begins AND before landing/merge:

1. Run `git fetch origin`.
2. Verify `git rev-parse origin/main` strictly equals
   `eec20f6faeb089ec2fcdc982ad65adce242a21a9`.
3. If different: STOP immediately. Do NOT rebase onto or merge a different
   `origin/main`. The cutover design, archive hashes, action matrix, and
   checklist are anchored to this exact baseline. Changing the baseline requires
   a full re-inventory, updated design, and re-pass of Oracle Gate 1.

### 10.3 Landing Requirements

The cutover must NOT be pushed directly to `main`. Landing requires:

1. **P0 review**: At least two independent reviewers confirm:
   - All archive entries conform to the ledger schema (§4.2).
   - No DELETE path exists at its original location.
   - Every REPLACE file matches the exact retirement template.
   - `PROJECT_MEMORY.md` and `README.md` meet §6 requirements.
   - `AGENTS.md` and `CLAUDE.md` are byte-identical to baseline.
   - v5 CI has only `workflow_dispatch` triggers.
   - Authority guard script uses only standard-library Python and checks all
     categories in §7.2.
   - `canonical/`, `contracts/`, `schemas/` have zero diff against baseline.
2. **Oracle Gate 2**: Cutover commit passes independent Oracle review (Gate 2,
   post-cutover).
3. **Authority guard CI green**: The guard workflow passes on the PR branch.
4. **Remote SHA match**: The remote cutover branch HEAD equals the local commit
   proposed for merge.
5. **Human approval**: A merge of the PR must be explicitly approved by the
   repository owner or a designated maintainer.
6. **Clean tree**: `git status --short` on the PR branch is empty.
7. **`git diff --check`** passes on the entire branch diff against `origin/main`.

### 10.4 Merge Constraints

- Allowed merge methods: **fast-forward** or **merge commit** (preserves the
  Phase 2 commit object).
- **Forbidden**: squash merge, rebase-and-merge. These destroy the Phase 2
  commit SHA, breaking rollback identity and acceptance records.
- Post-merge verification: confirm `git merge-base --is-ancestor <phase2-sha> origin/main`
  exits 0 after merge.
- The actual Phase 2 full SHA must be recorded in the acceptance record (not in
  the ledger). Rollback is `git revert <phase2-sha>` — this requires the exact
  SHA to be preserved.
- No `push --force` or direct-to-main commit is permitted.

### 10.5 Post-merge Acceptance Verification

After the cutover PR is merged to `origin/main`, the following must be verified
before the cutover is considered complete. These checks can only run post-merge
because they require the merged state on `origin/main`.

1. **Ancestor check**: Run `git fetch origin`, then:
   ```
   git merge-base --is-ancestor <phase2-sha> origin/main
   ```
   Must exit 0. This confirms the Phase 2 commit object was preserved (not
   squashed or rebased away) and is reachable from main.

2. **Record landed main SHA**: Record the full 40-character SHA of
   `origin/main` after the merge. This is the **landed main SHA** and must be
   recorded alongside the `<phase2-sha>` in the acceptance record. The pair
   `(phase2-sha, landed-main-sha)` is the canonical identity of the cutover
   landing.

3. **Rollback dry-run**: From a clean checkout at the landed main SHA, run
   `git diff <phase2-sha>^ <phase2-sha> | git apply --reverse --check`. It must
   report no conflict and must not modify the worktree. An actual
   `git revert <phase2-sha>` remains a separate human-approved operation.

## 11. Phase 2 Completion Checklist

These checks can ONLY run after Phase 2 artifacts exist (archive tree, ledger,
rewrites, guard script, retirement notices). They are NOT prerequisites for
Phase 2 start.

### P0 (Blocking — must all pass before merge)

| # | Check | Acceptance | Command / Evidence |
|---|-------|------------|--------------------|
| P0-1 | Commit scope exact and tree clean | Before commit: staged paths exactly equal the Phase 2 allowlist derived per §9.4; no extra unstaged/untracked files diverge from baseline. After commit: `git status --short` empty. | `git diff --cached --name-only` list equals allowlist; commit; `git status --short` shows nothing |
| P0-2 | Changed paths exact allowlist | Only files in the Phase 2 allowlist appear | Compare `git diff --cached --name-only` against allowlist derived from §9.4 |
| P0-3 | `PROJECT_MEMORY.md` archive SHA equals original | `original_sha256` in ledger equals `sha256sum(git show eec20f6faeb089ec2fcdc982ad65adce242a21a9:PROJECT_MEMORY.md)`. `archive_sha256` equals `sha256sum docs/legacy/aitp-v5-authority-cutover/repository/PROJECT_MEMORY.md`. Both equal. | `git show <baseline>:PROJECT_MEMORY.md \| sha256sum` vs `sha256sum archive-path` |
| P0-4 | `README.md` archive SHA equals original | Ditto for README.md | Same as P0-3 for README.md |
| P0-5 | New `README.md` first viewport | First 40 lines contain no v5 install/run content | Manual read + `grep -i 'pip install\|npm install\|mcp install\|hook install' README.md` returns nothing |
| P0-6 | DELETE paths do not exist | Every path in §5.1 DELETE list absent from worktree | `ls <path>` fails for each DELETE entry |
| P0-7 | REPLACE paths match template | Every REPLACE file content equals parametrized template | Byte-for-byte comparison against expected template for all 43 REPLACE paths |
| P0-8 | v5 CI trigger restricted | Only `workflow_dispatch` in v5-test-lanes.yml `on:` block; all job `if:` use manual dispatch | Guard check 3 (line-by-line column-0 `on:` parse, not whole-file grep) |
| P0-9 | Shim no-drift | `AGENTS.md` and `CLAUDE.md` unchanged | `git diff eec20f6faeb089ec2fcdc982ad65adce242a21a9 -- AGENTS.md CLAUDE.md` exits 0 |
| P0-10 | `src/aitp/` no legacy imports | No `import brain` or `from brain` in `src/aitp/` | `grep -r 'import brain\|from brain' src/aitp/` returns nothing |
| P0-11 | Canonical zero diff | `canonical/`, `contracts/`, `schemas/` unchanged | `git diff --name-only eec20f6faeb089ec2fcdc982ad65adce242a21a9 HEAD -- research/knowledge-hub/canonical/ contracts/ schemas/` produces no output |
| P0-12 | `git diff --check` passes | No whitespace warnings | `git diff --check` on tracked changes passes |
| P0-13 | Remote branch SHA match | `git rev-parse codex/aitp-2-authority-cutover` equals local HEAD | `git rev-parse HEAD` vs `git ls-remote origin refs/heads/codex/aitp-2-authority-cutover` |
| P0-14 | Authority guard passes | Guard script exits 0 | `python scripts/check_repository_authority.py; echo $?` |
| P0-15 | Baseline freshness | `origin/main` still equals `eec20f6faeb089ec2fcdc982ad65adce242a21a9` | `git fetch origin && git rev-parse origin/main` |

### P1 (Must pass before merge)

| # | Check | Acceptance |
|---|-------|------------|
| P1-1 | Archive ledger exists and complete | `archive-manifest.json` must exist (missing=FAIL); `source_path` set is set-equal to closed archive inventory in §4.3 (all DELETE + REPLACE + MODIFY + root files); every archive path exists on disk |
| P1-2 | Ledger hashes and boundaries validate | Every `original_sha256` equals `sha256sum(git show <source_commit>:<source_path>)`. Every `archive_sha256` equals `sha256sum <archive-file-on-disk>`. `git_mode`, `byte_count`, `line_count`, `byte_interval`, `line_interval` match actual file. |
| P1-3 | All retirement notices exact match (bytes) | Every REPLACE file byte-for-byte matches template (UTF-8, LF-only, no BOM, trailing `\n`; exactly 4 logical lines, exactly 5 for UNINSTALL.md). Retirement notice archive mapping consistent with ledger. |
| P1-4 | New `PROJECT_MEMORY.md` links resolve | All markdown links in the new PM point to existing files |
| P1-5 | Authority guard script is standard-library only | `grep -E '^import \|^from ' scripts/check_repository_authority.py` shows only stdlib modules |
| P1-6 | KEEP-HISTORICAL files not in changed set | No file from §4.4/§5.2 KEEP-HISTORICAL list appears in `git diff --name-only` against baseline |
| P1-7 | Strong authority-marker scan clean | Guard strong-marker check (§7.2 item 8) finds zero old authority markers in non-retirement, non-historical Markdown surfaces |
| P1-8 | v5 CI trigger verified by guard check 3 | Guard parses `on:` block line-by-line (no whole-file grep); event-key set exactly `{workflow_dispatch}`; all job `if:` use manual dispatch |

## 12. What This Design Does Not Do

1. Does NOT create archive copies, edit root files, or write the guard script.
   That is Phase 2 (implementation).
2. Does NOT delete or modify files outside the 7 transplanted paths in Phase 1.
3. Does NOT read or write external `.aitp` stores.
4. Does NOT define the local uninstall procedure for v5 plugins/MCP/hooks.
5. Does NOT add any code to `src/aitp/` — S0 begins after cutover.
6. Does NOT change the default branch or merge strategy.
7. Does NOT delete `brain/v5`, `hooks/**`, `deploy/**`, plugin payload, test
   suites, or any KEEP-HISTORICAL file. These remain byte-identical.
8. Does NOT require zero v5 tokens in KEEP-HISTORICAL files.
9. Does NOT install, upgrade, or remove any pip/npm/MCP package on the user's
   machine.
10. Does NOT add `plugins/*/scripts/**`, `plugins/*/skills/**`, adapter payload
    (non-entry-point), deploy templates, or `scripts/run_v5_test_lanes.py`
    to DELETE/REPLACE lists. These are inert historical payload — deactivated
    because manifests/installer/default docs no longer reference them.

## A. Appendix — Machine Path Normalization (Phase 1)

In the two architecture audits (#2 and #5), all machine-local absolute research
paths in the original audits have been replaced with stable symbolic
placeholders. Only the following abstract source categories are referenced in
the normalized audits:

| Abstract source category | Symbolic placeholder used |
|--------------------------|---------------------------|
| Quantum-chaos research source | `<private-research-source>/quantum-chaos` |
| Materials-workflow research source | `<private-research-source>/materials-workflow` |
| Legacy topics store | `<private-legacy-topics-root>/.aitp` |

The source checkpoint (`869d8e65`) and the fact that only machine paths were
normalized are recorded transparently in the audit frontmatter. No scientific or
audit conclusions were altered. The original audit evidence with the literal
machine-local paths remains available in the evidence worktree at the preserved
checkpoint.
