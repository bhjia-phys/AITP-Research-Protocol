# AITP M0 Release Audit

Date: 2026-07-11

Status: M0 release acceptance complete. The exact staged candidate passes the
blocking v5 plus legacy read/migration/write-guard suite; the real derived index
is fresh with canonical before/manifest/after equality. M0.5 complexity
reduction review is the next required step before M1-M6 expansion.

## Released Foundation

- Typed Markdown/YAML remains the only canonical research-state source.
- `RecordFamilySpec` centrally describes 46 canonical/special record locations;
  every observed registry family is registered and exact-expandable.
- `RecordRepository` provides idempotent creation, collision rejection,
  compare-and-swap revision, atomic persistence, and explicit read diagnostics.
- Pre-envelope schema-v1 records use six explicit conservative materialization
  adapters. New enveloped records and write validation cannot use those
  adapters to bypass current schemas.
- Tolerant reads require one of 12 statically named legacy-compatibility,
  migration, recovery, or derived-orientation operations. Exhaustive canonical
  queries and absence claims remain strict and fail visibly on malformed data.
- The generation-stamped query index is disposable, freshness checked, and
  covers registry records, topics, sessions, contexts, and L2 memory entries.
- One context compiler owns byte, token, line, coverage, staleness, and exact
  expansion boundaries.
- Startup routing injects only a bounded orientation hint, never complete topic
  `MEMORY.md` bodies.
- `CapabilitySpec` joins runtime operations, MCP wrappers, public contracts,
  compact visibility, bridge targets, and state effects.

## Architecture Boundary

The RED baseline contained 39 oversized v5 modules. M0 now has 36 thin
compatibility facades backed by 94 fixed local source shards; the largest shard
is 479 lines. Large catalog data and domain packs use focused data modules.
CLI query/context operations and MCP query/context operations have dedicated
modules.

`compat_module_loader.load_module_shards` is a bounded migration mechanism, not
a second plugin system. Facades list every repository-owned shard explicitly;
the loader rejects paths outside `brain/v5`, and release tests prove every
shard is referenced exactly once. Future responsibility-oriented refactors may
replace a facade without changing its public import contract.

Current static inventory:

| Measure | Result |
|---|---:|
| Audited source/hook/script/test files | 685 |
| Canonical writer candidates | 111 |
| Registered capabilities | 226 |
| MCP wrappers | 226 |
| Public surfaces | 198 |
| Compact MCP tools | 16 |
| Bridge targets | 43 |
| Capability registry issues | 0 |
| Python parse errors | 0 |

The 226th capability is the independently developed, optional Harness Feedback
dossier extension present in this working tree. The clean core registry remains
valid without it.

## Performance Evidence

### Versioned 10,000-Record Fixture

| Measure | Result | Gate |
|---|---:|---:|
| Index build | 194.436 s | explicit/background only |
| Cold minimal context | 0.267 s | < 3.0 s |
| Warm minimal p95 | 0.203 s | < 1.0 s |
| Warm timeline p95 | 0.480 s | < 2.0 s |
| Exact ref p95 | 0.096 s | < 0.250 s |

### Real Research Store

The authorized indexes-only rebuild first produced generation 5 while
legitimate research writes were still arriving. Its pre-build watermark was
`d1210e180aa189f1fad673345a506ead6efc0ad8860e1a9ab34ca6b3f63d14df`,
while manifest and post-build were both `95ef8146...`; that attempt was
correctly rejected as M0 evidence rather than misreported as canonical
stability.

The immediate generation 6 retry obtained a quiescent window and proved:

- `before == manifest == after == 95ef8146e8e5116c813bb27d11efcd0f3c0117e91d754c8ee03041cda78140e5`;
- canonical state token before/manifest/after is
  `01565d8bc048eb0d3b4b395b75e35ec9ffcf70d3ecc7bec37f470323e5fc1152`;
- 9,764 checked and indexed records, zero malformed records;
- derived index content hash
  `5c73fe5328a4edd5d7b63d7033f644558ce0964c44ecf68ac089f700958154fb`;
- integrity reload returned all 9,764 documents;
- the build report states `can_update_kernel_state=false` and
  `can_update_claim_trust=false`.

The generation 6 status probe is fresh and orientation-only. Exact expansion
of three refs returned all three with exhaustive requested-ref coverage and no
malformed records.

| Real context probe | LibRPA/QSGW | Quantum gravity |
|---|---:|---:|
| Wall time | 0.724 s | 0.678 s |
| Context bytes | 3,889 | 3,688 |
| Estimated tokens | 460 | 358 |
| Expansion refs | 80 | 37 |
| Candidate summaries | 12 | 12 |
| Truncated | yes | no |

Both contexts are fresh, trust-neutral, and disallow absence conclusions from
their non-empty result sets. The LibRPA session also reports
`unresolved_exact_ref:research_route:curated_legacy_migration`: this is an
explicit legacy migration marker stored in three schema-v1 sessions, not a
missing route record. M0 preserves the visible read diagnostic; M0.5 must
classify or normalize the migration semantics without rewriting real records.
The old execution-brief compatibility path remains historical and is not the
session-start path.

### V5 Release-Test Boundary Closure

The first archived legacy-write diagnostic exposed MCP-to-CLI path fallback: source
registration resolved through the installed real topics root. The test created
10 untracked legacy files under `qho-study` and `chern-simons-anomaly` at
03:49-03:50 on 2026-07-11. They are outside the typed `.aitp` store and do not
participate in the typed watermark, but they are still real-workspace files.
The user has forbidden canonical-record modification, so they remain untouched
and explicitly excluded from staging and index rebuild.
A later read-only recheck still found exactly those 10 files with their original
03:49-03:50 local write times; hashes were recorded during the audit and no
cleanup, rewrite, move, or staging action was performed.

Quarantine manifest, relative to `research/aitp-topics/`:

| Path | SHA-256 |
|---|---|
| `qho-study/research.md` | `22758f61ec9e20ee29c44b5bcdc327698c440e2998f1daaeab467077c763f826` |
| `qho-study/L0/sources/griffiths-qm-ch2/notes.md` | `cbadebd052f1e7a8590b952ceee77b20dcd6f48a9c8f3dcea15da6d4ee59b52e` |
| `qho-study/L0/sources/griffiths-qm-ch2/source.md` | `6d68003fb65e2bd144135a7215743422ec1347a338f4e613ba13f009602a467d` |
| `chern-simons-anomaly/research.md` | `b833aab8924330015361233b8129ed6e71451dd7ba7e3929ac3a6553edc1293e` |
| `chern-simons-anomaly/L0/sources/redlich-parity-2016/notes.md` | `9936233ca3acaaa4ca80b5d097a1f08b345dc007adf893de8a35e1953a8f77b9` |
| `chern-simons-anomaly/L0/sources/redlich-parity-2016/source.md` | `17fe10d3b9e45d4ea9c7bcfcf0e61586b8432b8a85541c7b07adf4fbbd5d3c29` |
| `chern-simons-anomaly/L0/sources/weinberg-qft-v2/notes.md` | `5a8904eb4ff02958b28afeeafc6b54a067848fcc8fde59654619b48f16b38753` |
| `chern-simons-anomaly/L0/sources/weinberg-qft-v2/source.md` | `42c4539866949b17976ec413e415f7303b1b05136a977eb4b36a543bea02c30b` |
| `chern-simons-anomaly/L0/sources/witten-cs-2018/notes.md` | `ef4da56e0ff08f4eeda2776484bde79fa1a2b40e730a78a8a9881470900839a6` |
| `chern-simons-anomaly/L0/sources/witten-cs-2018/source.md` | `7fe572d5142da1150ea3081cc3c913a23354fb85a8d72f4a41923f06b0e05e7c` |

The initial closure strategy then made the archived write workflow
release-blocking and began repairing candidate submission, L3/L4 gates,
promotion, and legacy graph writes. That was an architecture regression even
though the production MCP entrypoint remained v5. Those production and test
changes were removed.

The corrected runner clears inherited real-store and legacy-write bindings,
preserves explicit per-test workspace bases, and isolates `Path.home()` plus
host-specific config roots under system Temp. It preserves `APPDATA` and
`LOCALAPPDATA` so the child interpreter retains the launching Python package
environment. It does not set one global v5 topics root across a blocking suite.
No blocking test enables legacy writes: the runner selects four exact
legacy nodes for default blocking, native-MCP rejection, old-record reads, and
side-effecting-query blocking. The one opt-in bootstrap escape-hatch node is
archive-only. Blocking `full` collects every `test_v5_*` module plus
package-manager deployment, flow-notebook read rendering, and those exact
legacy read/write-guard nodes.
`legacy-compat` names the read, migration, schema-v1 materialization, old-store,
and write-blocking subset. `legacy-write-archive` remains available only for
explicit historical diagnostics and is not called by `full`, CI release jobs,
or M0 acceptance. Final local `full` evidence must run from the exact staged
candidate in an isolated worktree so protected working-tree edits are excluded.
The initial runner contract had 6 passing pytest tests; documentation-boundary
and M1-M6 ownership assertions also passed when invoked directly.

The first exact staged-candidate `full` run on 2026-07-11 collected 1,159 tests
and ran for 1,714.1 seconds, but it is not release evidence. The runner had set
one global `AITP_TOPICS_ROOT`; after an MCP test created that root,
`resolve_workspace_base` redirected later explicit `tmp_path` workspaces into
the shared root. The first failure appeared in the HPC cockpit MCP surface and
was followed by cross-test state and missing-parent cascades. The runner now
clears the global topics-root binding and isolates only host home/config roots
without hiding Python's package environment. A first targeted launch exposed
that overriding Windows `APPDATA` hid the launching interpreter's user-site
`pygments`; the runner now preserves `APPDATA`/`LOCALAPPDATA` while isolating
`Path.home()` and host-specific config roots.

The corrected exact staged candidate then passed 28 targeted runner, HPC, and
deployment regressions. The uncapped blocking `full` run collected 1,161 tests
and completed with 1,160 passed, 1 skipped, and 2 pre-existing flow-notebook
escape-sequence warnings in 1,314.86 seconds. It ran from system Temp with no
real AITP root binding; `legacy-write-archive` was not invoked.

The active-looking top-level Codex, Claude Code, OpenCode, and OpenClaw adapter
references no longer teach legacy MCP writes or the L0-L4 stage lifecycle.
Codex and Claude point to their canonical v5 assets, OpenCode points to the v5
native MCP, and OpenClaw explicitly reports that no dedicated lifecycle
installer is release-supported. The blocking deployment-surface test covers
all four references.

The remaining top-level documentation entrypoints were also inconsistent:
`docs/AITP_SPEC.md` still declared v4 globally authoritative,
`docs/PROJECT_INDEX.md` routed runtime readers into the legacy Brain protocol,
and `adapters/README.md` assumed one generic `aitp` executable. They now route
production work to `brain/v5/native_mcp.py` and the v5 design, while preserving
the L0-L4 protocol tree only as historical semantics, audit, and migration
material. A release-boundary test prevents those entrypoints from reverting.

## Migration And Rollback

1. Canonical schema-v1 files are not rewritten by M0. Rollback therefore
   begins by removing `.aitp/indexes`; no research records need restoration.
2. Rebuild derived state with `aitp-v5 query index-build`. Check freshness with
   `aitp-v5 query index-status` before allowing exhaustive absence language.
3. If a new repository writer must be rolled back, retain its revision archive
   and restore through an explicit compared revision. Do not copy an old file
   over the canonical id.
4. Compatibility facades preserve existing imports. Reverting one extraction
   restores the prior monolith without changing canonical data or host names.
5. The keyword router can be rolled back independently, but a deployment is
   invalid if it resumes injecting complete topic memory bodies.
6. Optional retrieval backends, cached context, and generated startup files are
   disposable projections and never participate in claim trust.

## Staged Release Scope

The local M0 candidate is assembled with explicit path allowlists. Never use
`git add -A`, `git add .`, or a broad re-add of mixed files.

Always exclude these protected working-tree files:

- `README.md`;
- `brain/v5/cli_harness_feedback.py`;
- `brain/v5/harness_feedback.py`;
- `brain/v5/harness_feedback_contracts.py`;
- `tests/test_v5_harness_feedback.py`;
- the independent Harness Feedback plan/spec and generated skill/problem files;
- `.agents/skills`, `.superpowers`, `nul`, PDFs, images, and `tmp` artifacts;
- every real research canonical record.

The four mixed shard files already contain reviewed M0 core hunks in the index
and protected user hunks only in the working tree. Do not re-add them:

- `brain/v5/_compat_shards/mcp_tools/part_01.py`;
- `brain/v5/_compat_shards/mcp_tools/part_05.py`;
- `brain/v5/_compat_shards/public_surfaces/part_01.py`;
- `brain/v5/_compat_shards/public_surfaces/part_02.py`.

After staging, audit both directions: cached paths must equal the reviewed M0
allowlist, while unstaged tracked paths must contain only the protected files
and the four mixed user-hunk files. Run blocking `full` from an isolated
worktree constructed from that exact cached patch, not from the dirty primary
worktree.

The reviewed candidate contains 232 staged paths. Forbidden/protected cached
paths and legacy business paths are both zero. The unstaged tracked set is
exactly the 11 protected files listed above, and both protected diff hashes are
unchanged from the pre-staging audit.

## Verification Matrix

Completed in the current release slice:

- architecture, recursive line-boundary, compatibility-manifest/traversal,
  runtime-audit, strict/tolerant-read policy, schema-v1 compatibility, and test
  lane contracts: 27 focused passes;
- real-store generation 6 index: 9,764 checked and loaded, zero issues, strong
  canonical watermark and state-token equality;
- generation 6 real-store LibRPA and quantum-gravity contexts: fresh and within
  byte/token and latency budgets;
- static capability parity: 226 registered and 226 wrapped, zero registry
  issues.

Current named-lane execution evidence:

| Lane | Result | Wall time |
|---|---:|---:|
| foundation | 144 passed, 1 skipped | 19.93 s |
| compatibility | 134 passed | 97.51 s |
| legacy-compat | 200 passed | 46.25 s |
| slow-adapter | 88 passed | 846.89 s |
| corrected staged-only targeted set | 28 passed | 5.11 s |
| blocking staged-only `full` | 1,160 passed, 1 skipped | 1,314.86 s |

The historical all-tests tree includes archived L0-L4 write workflows and is
not a release contract. The weekly GitHub Actions full job enables the
versioned performance fixture. `legacy-write-archive` remains an optional
historical diagnostic; not running it is intentional and does not weaken M0.

## Trust Boundary

Every audit, index, context, compatibility adapter, and performance result in
this report is structural or orientation evidence. None can update scientific
evidence, validation status, active-claim binding, L2 promotion, or claim trust.
