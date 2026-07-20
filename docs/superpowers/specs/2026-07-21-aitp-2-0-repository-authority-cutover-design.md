---
title: AITP 2.0 Repository Authority Cutover
date: 2026-07-21
status: approved-design-pending-implementation
authority:
  - docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md
scope: Replace v5 as the repository's active development authority while preserving it as read-only history
---

# AITP 2.0 Repository Authority Cutover

## 1. Decision

The AITP repository changes its active authority from the installed v5/MCP/hook
system to the AITP 2.0 command-and-Skill rewrite.

This cutover changes repository guidance, not local machine installation. The
existing installed plugin, MCP configuration, and host hooks are handled later
as a separate reversible operation.

## 2. Authority After Cutover

Repository authority is ordered as follows:

1. `PROJECT_MEMORY.md` defines current development and safety rules.
2. `docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md`
   defines the active product, data, command, and Skill contracts.
3. Reviewed implementation plans define bounded S0-S7 work.
4. `docs/legacy/` preserves v5 explanations and historical operating details.

An old document, test, plugin, entrypoint, or comment cannot override this
ordering merely because it still exists in the repository.

## 3. Files Changed By The Cutover

### 3.1 Preserve The Old Memory

Copy the complete pre-cutover `PROJECT_MEMORY.md` to:

```text
docs/legacy/2026-07-21-aitp-v5-project-memory.md
```

The archive receives a short historical-status header. Its original body stays
byte-identical after that header so migration and architecture archaeology do
not depend on Git history alone.

### 3.2 Replace `PROJECT_MEMORY.md`

The new project memory is concise and contains only active instructions:

- AITP 2.0 is the sole active implementation target;
- the current status is rewrite/specification work, not a released 2.0 runtime;
- normal implementation lives below `src/aitp/` and imports no legacy runtime;
- the only required host integration is `using-aitp` plus the `aitp` CLI;
- Markdown, exact refs, bounded command output, Git, and human review are the
  active storage and authority model;
- S0 fixture/provenance freeze precedes S1 implementation;
- real canonical research records are read-only unless separately authorized;
- v5, L0-L4, MCP, hooks, old plugins, context compilers, and old package
  managers are historical-only;
- old code may be read for migration semantics or reimplemented behind a 2.0
  contract, but cannot be imported into `src/aitp/` production code;
- old production, hook, plugin, and legacy-write tests are nonblocking history;
- `AGENTS.md` and `CLAUDE.md` remain thin shims to this file.

The new memory links to the active design, audit disposition, implementation
sequence, and v5 archive rather than repeating their detail.

### 3.3 Mark The README

Add a first-viewport status block stating:

- AITP 2.0 is the active rewrite target;
- AITP v5 and its MCP/hook/plugin install paths are retired and unsupported for
  new research operation;
- the repository does not yet contain a released 2.0 runtime;
- existing v5 records remain preserved and will be accessed through a future
  read-only compatibility adapter;
- contributors must read `PROJECT_MEMORY.md` and the active 2.0 design.

The remainder of the v5 README stays temporarily available below a clearly
labelled historical boundary. Rewriting installation and usage documentation is
part of S7, not this authority cutover.

### 3.4 Keep Compatibility Shims Stable

`AGENTS.md` and `CLAUDE.md` remain unchanged. They already point only to
`PROJECT_MEMORY.md`, so replacing the canonical memory switches compatible
Agents without duplicating instructions.

## 4. Legacy Boundary

After cutover, the following paths are historical reference, migration input,
or archival fixtures only:

```text
brain/
hooks/
plugins/aitp-research-protocol*/
deploy/
adapters/
contracts/
schemas/
scripts/aitp-pm.py
```

Their presence does not make them active architecture. Do not:

- run v5 MCP or hook entrypoints as the repository's default workflow;
- extend v5 record families, context surfaces, gates, writers, installers, or
  host adapters;
- make all v5 or legacy-write tests blocking for 2.0;
- import a legacy production module from `src/aitp/`;
- mutate legacy or real research records merely to create 2.0 fixtures.

Permitted uses are read-only inspection, migration-contract discovery,
sanitized fixture derivation after explicit authorization, and independent
reimplementation of a small primitive with 2.0 tests.

## 5. Active Implementation Boundary

The new implementation starts cleanly at:

```text
pyproject.toml
src/aitp/
tests/fixtures/aitp2/
```

No new 2.0 implementation is added elsewhere. The first executable milestone
is S0: freeze real-derived sanitized fixtures, command contracts, record
profiles, package resources, and simplicity checks. S1 then implements store
discovery plus `enter`, `search`, `show`, `admin init`, and `admin doctor`.

## 6. Data Safety

This cutover does not edit:

- external `.aitp` canonical records;
- real research repositories, code branches, run outputs, PDFs, or HPC state;
- local Codex/Kimi/Claude plugin installation or MCP/hook configuration;
- old production source files.

Any later real-record read, fixture extraction, local uninstall, or migration
requires its own explicit scope and verification.

## 7. Verification

The cutover is accepted only when:

1. the old project memory is preserved under `docs/legacy/`;
2. active `PROJECT_MEMORY.md` contains no instruction to run or extend v5;
3. README identifies v5 operational instructions as historical;
4. all active-memory links resolve;
5. `AGENTS.md` and `CLAUDE.md` remain unchanged thin shims;
6. no file below old production, plugin, hook, or external research paths is
   modified;
7. the Git diff contains only the archive, project memory, README status block,
   and this design/its implementation plan;
8. `git diff --check` passes.

## 8. Rollback

Rollback restores the previous `PROJECT_MEMORY.md` and removes the README
status block in a new reviewed commit. The archived v5 memory remains because it
is historical evidence, not active authority.
