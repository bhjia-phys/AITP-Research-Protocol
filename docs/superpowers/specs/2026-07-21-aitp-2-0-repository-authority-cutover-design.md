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

At minimum, the following live-main files must be archived byte-identically
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

4. Installation documents:
   - `docs/INSTALL.md`
   - `docs/INSTALL_CLAUDE_CODE.md`
   - `docs/INSTALL_CODEX.md`
   - `docs/INSTALL_KIMI_CODE.md`
   - `docs/INSTALL_OPENCLAW.md`
   - `docs/QUICKSTART.md`
   - `docs/PUBLISH_PYPI.md`
   - `docs/MIGRATE_LOCAL_INSTALL.md`
   - `docs/UNINSTALL.md`

5. Protocol/CI entry points:
   - `brain/PROTOCOL.md`
   - `docs/AUDIT_REPORT_ALIGNMENT.md` (references v5 L0-L4)
   - `.github/workflows/v5-test-lanes.yml`

### 4.4 Posts Not Archived (remain in place as historical source)

These files are historical source code and payload, not active entry points.
They remain in place but MUST NOT be referenced by any active manifest, default
documentation, or CI workflow after cutover:

- `brain/v5/**` — all v5 source code
- `hooks/**` — hook implementations
- `adapters/**` — host adapter code
- `deploy/**` — deployment configs
- `plugins/aitp-research-protocol/scripts/**` — plugin payload
- `plugins/aitp-research-protocol-kimi/scripts/**` — plugin payload
- `research/adapters/openclaw/scripts/**` — OpenClaw runtime payload
- `research/adapters/openclaw/plugin/**` — OpenClaw plugin source
- `scripts/split_*.py` — v5 split utilities
- `scripts/run_v5_test_lanes.py` — v5 test runner
- `bin/convert_legacy_to_v2.py`, `bin/migrate_legacy_topics.py`, etc. — historical utilities

## 5. Deactivation — Active Entry Points

### 5.1 Action Matrix

The cutover commit must deactivate every active entry point. The matrix
distinguishes two actions:

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
| `.codex/INSTALL.md` | REPLACE: "AITP v5 Codex installation is retired. AITP 2.0 is the active authority. See PROJECT_MEMORY.md and docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md." |
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

#### CI workflow (**MODIFY** to manual-only)

| Source Path | Action |
|-------------|--------|
| `.github/workflows/v5-test-lanes.yml` | MODIFY: remove all automatic triggers; keep `workflow_dispatch` only. Archive byte-identical copy first. |

Every retirement notice must:
- State "AITP v5 is retired."
- Point to `PROJECT_MEMORY.md` as the sole active authority.
- Point to the archival copy at `docs/legacy/aitp-v5-authority-cutover/repository/<path>`.
- Contain no install commands, no executable shell commands, no pip/npm/mcp
  directives, no hook registration steps.
- Be no longer than 8 lines.

### 5.2 Files NOT Deleted or Modified

These files remain byte-identical to the live-main baseline:

- `AGENTS.md` — thin shim; unchanged.
- `CLAUDE.md` — thin shim; unchanged.
- `brain/v5/**` — historical source; preserved in place.
- `hooks/**`, `adapters/**`, `deploy/**` — historical source; preserved in place.
- All historical research records in `research/knowledge-hub/**` — preserved.
- `contracts/**`, `schemas/**` — canonical definition files; zero-diff protected (see §8.2).

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
does not exist yet), or any v5 module. It runs on PR and push to main and checks:

1. **Forbidden active manifests**: Fail if any of these files exist and contain
   non-retirement content:
   - `.agents/plugins/marketplace.json`
   - `.claude-plugin/plugin.json`
   - `plugins/marketplace.kimi.json`
   - `plugins/aitp-research-protocol/.codex-plugin/plugin.json`
   - `plugins/aitp-research-protocol/.mcp.json`
   - `plugins/aitp-research-protocol-kimi/kimi.plugin.json`
   - `package.json`
   - `aitp-manifest.json`
   - OpenClaw manifest/plugin/package JSON files
2. **Forbidden active bins/commands**: Fail if any executable entrypoint from the
   DELETE list in §5.1 exists at its original path — `bin/aitp-v5.mjs`,
   `scripts/aitp`, `scripts/aitp.cmd`, `scripts/aitp-local.py`,
   `scripts/aitp-local.cmd`, or `scripts/aitp-pm.py`.
3. **Forbidden install docs and retired entry points**: Fail if any file from the
   REPLACE list in §5.1 contains non-retirement content (pip install, npm
   install, MCP registration, hook commands, or v5 operational prose):
   `.codex/INSTALL.md`, all `docs/INSTALL*.md`, `docs/QUICKSTART.md`,
   `docs/PUBLISH_PYPI.md`, `docs/MIGRATE_LOCAL_INSTALL.md`,
   `docs/UNINSTALL.md`, `plugins/aitp-research-protocol/README.md`,
   `plugins/aitp-research-protocol-kimi/README.md`, `brain/PROTOCOL.md`,
   `docs/AUDIT_REPORT_ALIGNMENT.md`.
4. **Root authority**: Fail if:
   - `PROJECT_MEMORY.md` references v5 as active or contains v5 install/run
     instructions.
   - `README.md` first 40 lines contain v5 operational content.
5. **v5 workflow trigger**: Fail if `.github/workflows/v5-test-lanes.yml`
   contains `pull_request`, `push`, or `schedule` triggers outside
   `workflow_dispatch`.
6. **Shim no-drift**: Fail if `AGENTS.md` or `CLAUDE.md` differ from their
   live-main baseline bytes.
7. **Legacy imports**: Fail if any `.py` file under `src/aitp/` imports from
   `brain/`, `brain.v5`, or `brain/` subpackages.
8. **Archive ledger hashes**: If `docs/legacy/aitp-v5-authority-cutover/archive-manifest.json`
   exists, verify every `original_sha256` by computing SHA-256 on the output of
   `git show <source_commit>:<source_path>` (NOT the worktree file). Verify
   every `archive_sha256` matches the archived file on disk. For
   `PROJECT_MEMORY.md` and `README.md` entries, verify
   `original_sha256 == archive_sha256`.
9. **Canonical zero-diff**: Fail if any file under
   `research/knowledge-hub/canonical/` differs from its live-main baseline
   (`eec20f6faeb089ec2fcdc982ad65adce242a21a9`). Similarly fail for
   `contracts/` and `schemas/`.
10. **Changed-path protection**: Fail if the current diff modifies any file
    under `research/knowledge-hub/canonical/`, `contracts/`, `schemas/`, or
    `.aitp/` (if it exists in-repo).

These three trees — `research/knowledge-hub/canonical/`, `contracts/`,
`schemas/` — are v5 historical and canonical-contract surfaces. Under 2.0
authority they are frozen; the guard uses `git show` and `git diff` against the
baseline `eec20f6faeb089ec2fcdc982ad65adce242a21a9` to verify no modification.
External `.aitp` directories are still never read or written by the guard.

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
- Replace PROJECT_MEMORY.md with 2.0 sole-active-authority content
- Replace README.md with concise 2.0 status block
- Keep AGENTS.md/CLAUDE.md byte-identical (shims)
- Restrict v5 CI to workflow_dispatch only
- Add authority-guard CI workflow and check script
- Zero-diff protect canonical/, contracts/, schemas/

Authority: docs/superpowers/specs/2026-07-21-aitp-2-0-repository-authority-cutover-design.md
Evidence checkpoint: 869d8e65f19e69404405e4da976876be8fc7f9a0
Live-main baseline: eec20f6faeb089ec2fcdc982ad65adce242a21a9
```

### 9.2 Commit Ordering

1. **Phase 1 (this design)** — commit the 7 transplanted documents (including
   this design) to the cutover branch. This is the specification commit.
2. **Phase 2 (implementation)** — commit the archive, deactivation, rewrites,
   guard, and CI changes. This is the cutover execution commit.
3. **Phase 3 (S0 implementation plan)** — write and commit an S0 implementation
   plan. The plan must describe: desensitized source-derived fixture structures,
   the 12 command contracts, record profiles, the command Skill package
   contract, and the simplicity CI design. The S0 plan does NOT create any
   fixtures, directory scaffolding, package `__init__.py`, or implementation
   code. S1 CLI implementation must not begin until the S0 plan passes review.

### 9.3 Rollback

Rollback is the exact `git revert` of the cutover execution commit (Phase 2),
applied on the development branch or after merge to main. Because this is a
single atomic revert, the new archive tree (`docs/legacy/`) and ledger created
by the cutover commit will also be removed from the current working tree. This
is expected: `git revert` exactly inverts the commit's diff.

The archival evidence is preserved in the reverted commit's Git history and can
be recovered at any time via `git show <cutover-commit>:<path>`. If a user needs
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

## 10. Default Branch Landing Conditions

### 10.1 Prerequisites Before Cutover Implementation

The cutover implementation (Phase 2) must NOT begin until:

1. **Phase 1 design committed**: This design, plus all other Phase 1 documents,
   are committed to the cutover branch.
2. **P0/P1 self-review complete**: All items in the §11 checklist below are
   verified and documented. All P0 items must pass; all P1 items must pass
   before S0.
3. **Oracle Gate 1 unblocked**: The Phase 1 design and self-review pass
   independent Oracle review (Gate 1, the CTL gate defined in the project's
   governance model) with no blocking findings.

### 10.2 Landing Requirements

The cutover must NOT be pushed directly to `main`. Landing requires:

1. **P0 review**: At least two independent reviewers confirm:
   - All architectural archive entries conform to the ledger schema.
   - No active manifest, bin, or install doc retains v5 operational content.
   - Root `PROJECT_MEMORY.md` and `README.md` meet the exact requirements in §6.
   - `AGENTS.md` and `CLAUDE.md` are byte-identical to baseline.
   - v5 CI has only `workflow_dispatch` triggers.
   - Authority guard script uses only standard-library Python and checks all
     10 categories in §7.2.
   - `canonical/`, `contracts/`, `schemas/` have zero diff.
2. **Oracle Gate 2**: Cutover commit passes independent Oracle review (Gate 2,
   post-cutover).
3. **Authority guard CI green**: The guard workflow passes on the PR branch.
4. **Remote SHA match**: The remote cutover branch HEAD equals the local commit
   proposed for merge.
5. **Human approval**: A merge of the PR must be explicitly approved by the
   repository owner or a designated maintainer.
6. **Clean tree**: `git status --short` on the PR branch shows only intended
   changes.
7. **`git diff --check`** passes on the entire branch diff against
   `origin/main`.

No `push --force` or direct-to-main commit is permitted.

## 11. P0/P1 Self-Audit Checklist

Before the cutover commit is proposed for merge, the implementer must run the
following checks and record the output as evidence:

### P0 (Blocking — must all pass)

| # | Check | Acceptance | Command / Evidence |
|---|-------|------------|--------------------|
| P0-1 | Commit scope exact and tree clean | Before commit: staged paths exactly equal the cutover allowlist; no extra unstaged/untracked files diverge from baseline. After commit: `git status --short` is empty. | `git diff --cached --name-only` lists only allowed paths; `git status --short` shows only expected untracked scope; commit; `git status --short` shows nothing |
| P0-2 | Changed paths exact allowlist | Only files in the cutover scope appear | `git diff --cached --name-only` or `git diff --name-only origin/main...HEAD` |
| P0-3 | `PROJECT_MEMORY.md` archive SHA equals original | `original_sha256` in ledger equals `sha256sum(git show eec20f6faeb089ec2fcdc982ad65adce242a21a9:PROJECT_MEMORY.md)`. `archive_sha256` equals `sha256sum docs/legacy/aitp-v5-authority-cutover/repository/PROJECT_MEMORY.md`. Both hashes must be equal. | `git show eec20f6faeb089ec2fcdc982ad65adce242a21a9:PROJECT_MEMORY.md \| sha256sum` vs `sha256sum docs/legacy/aitp-v5-authority-cutover/repository/PROJECT_MEMORY.md` |
| P0-4 | `README.md` archive SHA equals original | Ditto for README.md | `git show eec20f6faeb089ec2fcdc982ad65adce242a21a9:README.md \| sha256sum` vs `sha256sum docs/legacy/aitp-v5-authority-cutover/repository/README.md` |
| P0-5 | New `README.md` first viewport | First 40 lines contain no v5 install/run content | Manual read + `grep -i 'pip install\|npm install\|mcp install\|hook install' README.md` returns nothing |
| P0-6 | No active manifest exposes v5 | All deleted/replaced manifests verified | `find . -name '*.json' -path '*plugin*' -o -name 'marketplace*' -o -name 'aitp-manifest*' -o -name 'package.json'` and verify each is either deleted or retirement |
| P0-7 | v5 CI trigger restricted | Only `workflow_dispatch` triggers exist in `v5-test-lanes.yml` | `grep -E 'pull_request|push:|schedule' .github/workflows/v5-test-lanes.yml` returns nothing |
| P0-8 | Shim no-drift | `AGENTS.md` and `CLAUDE.md` unchanged | `git diff eec20f6faeb089ec2fcdc982ad65adce242a21a9 -- AGENTS.md CLAUDE.md` exits 0 with no output |
| P0-9 | `src/aitp/` no legacy imports | No `import brain` or `from brain` in `src/aitp/` | `grep -r 'import brain\|from brain' src/aitp/` returns nothing (or dir doesn't exist yet) |
| P0-10 | Canonical zero diff | `canonical/`, `contracts/`, `schemas/` unchanged | `git diff eec20f6faeb089ec2fcdc982ad65adce242a21a9 -- research/knowledge-hub/canonical/ contracts/ schemas/` exits 0 with no output |
| P0-11 | `git diff --check` passes | No whitespace warnings on the complete cutover diff. Phase 1 untracked files are checked via `git diff --no-index --check /dev/null <file>` or staged via `git add --intent-to-add` before `git diff --cached --check`. Phase 2 tracked changes use `git diff origin/main...HEAD --check`. | `git diff --check` for tracked changes; `git diff --no-index --check /dev/null <untracked-file>` for each Phase 1 file (accepts diff exit 1 but must produce zero whitespace-error output) |
| P0-12 | Remote branch SHA match | `git rev-parse codex/aitp-2-authority-cutover` equals local HEAD | `git rev-parse HEAD` and `git ls-remote origin refs/heads/codex/aitp-2-authority-cutover` |
| P0-13 | Authority guard passes | Guard script exits 0 | `python scripts/check_repository_authority.py; echo $?` |

### P1 (Must pass before S0 implementation)

| # | Check | Acceptance |
|---|-------|------------|
| P1-1 | Archive ledger complete | `archive-manifest.json` has an entry for every file listed in §4.3 |
| P1-2 | Ledger hashes validate | Every `original_sha256` in the ledger equals `sha256sum` of `git show <source_commit>:<source_path>` output. Every `archive_sha256` equals `sha256sum` of the archived file on disk. |
| P1-3 | All retirement notices ≤ 8 lines | `wc -l` on every REPLACE target |
| P1-4 | No retirement notice contains shell commands | `grep -E 'pip|npm|mcp|aitp install|aitp run|python -m'` on all REPLACE targets returns nothing |
| P1-5 | New `PROJECT_MEMORY.md` links resolve | All markdown links in the new PM point to existing files |
| P1-6 | Authority guard script is standard-library only | `grep -E '^import |^from ' scripts/check_repository_authority.py` shows only stdlib modules |

## 12. What This Design Does Not Do

1. Does NOT create archive copies, edit root files, or write the guard script.
   That is Phase 2 (implementation).
2. Does NOT delete or modify files outside the 7 transplanted paths in Phase 1.
3. Does NOT read or write external `.aitp` stores.
4. Does NOT define the local uninstall procedure for v5 plugins/MCP/hooks.
5. Does NOT add any code to `src/aitp/` — S0 begins after cutover.
6. Does NOT change the default branch or merge strategy.
7. Does NOT require deleting `brain/v5` or any historical source code.
8. Does NOT install, upgrade, or remove any pip/npm/MCP package on the user's
   machine.

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
