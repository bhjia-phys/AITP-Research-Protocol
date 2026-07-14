# AITP M1 Lifecycle And Context Release Audit

Date: 2026-07-14

Status: M1 release acceptance complete. The named working-tree lanes,
real-store read-only probes, static audits, and an exported staged-tree
candidate are green. No real canonical migration was applied.

## Released Lifecycle

- `SessionBinding` remains single-topic. `session_focus_sets` and
  `research_programs` add reviewed sidecar scope without rebinding
  `active_claim`.
- `cross_topic_relations` require exact typed refs, target-side revalidation,
  and `claim_trust_transfer=forbidden`.
- `session_closeouts` persist process state with `trust_effect=none`; the
  resume card and generated startup boundary are derived views.
- `recall_audits` persist query coverage, errors, exclusions, truncation, and
  index lineage. Non-exhaustive retrieval cannot support exhaustive language
  or high-cost prerequisite gates.
- Raw recording staging remains runtime state. One semantic candidate is
  coalesced into at most one durable `recording_candidate_batch` per milestone
  for human review; it cannot invoke evidence, trust, memory, Skill, or install
  writers.
- Six host-neutral lifecycle operations are exposed through typed facade, MCP,
  CLI, capability, and public-surface contracts. Maintenance operations remain
  outside compact research context.
- Startup/resume shares one coherent `QuerySnapshotSession` only within that
  request. Ordinary strong queries still reload and verify their required
  families; the snapshot is not a cross-request truth cache.

## Architecture And Trust Boundary

Typed Markdown/YAML records remain canonical. Full generations, delta rows,
orientation caches, context bundles, resume cards, and generated startup files
are disposable projections. Projection failure is visible and cannot roll back
or overwrite a successful canonical write.

The M1 lifecycle can update only its typed process families. It cannot mutate
scientific evidence, validation results, active-claim binding, memory
promotion, Skill installation, or claim trust. Cross-topic records route
potentially useful material but never transfer a source-topic conclusion.

The old L0-L4 write lifecycle remains outside release acceptance. The blocking
legacy lane covers reads, schema-v1 materialization, migration accounting, and
write guards; `legacy-write-archive` was not run and is not a release gate.

## End-To-End Evidence

`tests/test_v5_gate1_lifecycle_e2e.py` contains three acceptance tests:

1. A migration audit inventories a fixture twice with byte-identical `.aitp`
   state and emits review-only focus/program candidates.
2. A primary quantum-gravity topic uses an operator-algebra topic as reviewed
   support, stages a duplicate semantic candidate idempotently, creates one
   review batch, applies one closeout, and reconnects through an identical
   resume boundary. Claim files and `active_claim` remain unchanged.
3. Two startup requests each retain global strong-family checks while one
   pointer-bound orientation load is reused; standalone strong-query reload
   behavior remains covered separately.

The fixture asserts exact `conditional` and `open_gap` boundary classes, exact
record refs, target revalidation, and `claim_trust_transfer=forbidden`.

## Real-Store Read-Only Audit

The authorized audit inspected the existing topic store without applying a
migration:

| Measure | Result |
|---|---:|
| Canonical files | 9,947 |
| Topics | 43 |
| Sessions | 88 |
| Existing M1 focus sets | 0 |
| Existing M1 research programs | 0 |
| Read errors | 0 |
| Review-only focus candidates | 83 |
| Focus blockers | 5 |
| Review-only program candidates | 1 |

The program candidate groups the two existing LibRPA/QSGW topics sharing the
`librpa-qsgw` context. These are routing hints only. They contain no
canonical-ready payload, infer no scientific boundary, and require human
review. No focus set, program, relation, closeout, batch, evidence, validation,
or trust record was written.

Canonical file-set SHA-256 before and after both the migration audit and the
startup benchmark was identical:

`b0b39b8d0c32a0ad799907c15115e5e4198c491428fba0e02ec2eefb847b3c34`

## Startup Performance

The benchmark used existing session
`v5-quantum-gravity-von-neumann-legacy-preserve` in topic
`quantum-gravity-von-neumann` without creating an M1 closeout.

| Measure | Result | M1 budget |
|---|---:|---:|
| Cold startup | 0.981 s | < 3.0 s |
| Warm samples | 20 | 20 |
| Warm median | 0.261 s | informational |
| Warm p95 | 0.283 s | < 1.0 s |
| Warm maximum | 0.297 s | informational |
| Estimated tokens | 90 | < 800 |
| Payload bytes | 1,277 | bounded |

The result is an orientation-only fallback because the historical session has
no M1 closeout. It reports `can_update_claim_trust=false` and preserves the
canonical hash above.

## Classification And Static Audit

The M0.5 classification was refreshed with exact set equality, not lower
bounds:

| Inventory | Result |
|---|---:|
| Classified capabilities, excluding protected optional dossier | 234 |
| Core / vertical / maintenance / migration | 59 / 89 / 43 / 43 |
| Registered record families | 52 |
| Core / vertical / migration / soft-deprecation candidate | 25 / 19 / 4 / 4 |
| Named writers | 127 |
| Canonical / derived / host / migration / shared | 56 / 25 / 16 / 28 / 2 |
| Direct mutation candidates | 164 |
| Declared Python sources parsed | 609 / 609 |
| Parse errors | 0 |

The runtime entrypoint catalog now stores the six lifecycle rows in a literal
`part_03.py` mapping. Static runtime audit includes the authoritative lifecycle
surface rules, so dynamic registration cannot hide catalog/public drift.
Bounded writer coverage remains a declared-source lower bound and is not a
repository-wide proof against dynamic, reflected, custom, or native I/O.

## Named Test Lanes

All commands used Python 3.12.10 and isolated `--basetemp` directories under
the system Temp directory.

| Lane | Result | Pytest time |
|---|---:|---:|
| `foundation` | 186 passed, 1 skipped | 38.18 s |
| `compatibility` | 141 passed | 121.52 s |
| `v5-verticals` | 750 passed, 2 skipped | 758.74 s |
| `legacy-compat` | 200 passed | 53.80 s |
| `slow-adapter` | 88 passed | 991.51 s |

`v5-verticals` includes all three M1 end-to-end tests. The constituent release
lanes are reported separately; this audit does not claim that archived legacy
write workflows or every repository test are M1 release gates.

## Migration And Rollback

1. Existing sessions remain valid without M1 sidecars. The audit output must
   be reviewed and converted into explicit writer inputs before any migration.
2. No real-store canonical migration was applied in M1, so rollback requires
   no canonical record restoration.
3. Derived query generations, delta state, and orientation caches may be
   removed and rebuilt without changing research truth.
4. A later approved sidecar migration must use repository CAS receipts and
   retain before/after canonical hashes; it may not infer or elevate trust.
5. Reverting the M1 code leaves new typed records readable through registered
   family contracts; do not delete or overwrite them during rollback.

## Protected Work And Release Scope

The independent Harness Feedback work and its protected `README.md` hunk are
not part of this M1 commit. The release candidate excludes all 11 protected
tracked files, `.agents/skills`, `.superpowers`, `nul`, PDFs, images, `tmp`
artifacts, and every real research canonical record. The two protected diff
groups retained their pre-release hashes:

- `f4651e2355ca5e394bf2f96fed8b76b209969055`
- `3c0ca5a7b2ed30e0f32d43d3d1aa0e83330823a1`

`README.md` was intentionally not modified or staged by this release. M1
documentation is carried by the roadmap, detailed plan, classification audit,
project memory, and this release audit; README reconciliation remains owned by
the independent working-tree change.

## Exact Staged Candidate

The candidate was assembled with an exact 15-path allowlist. Cached paths
contained only M1 source, tests, roadmap/release documentation, classification
audit, and project memory. Protected tracked files and unrelated untracked
artifacts were absent.

Exported Git tree `77f8d4e47244aa9c7db767a6f177eda442af0dfe` passed the
M1 E2E, lane-contract, runtime-audit, capability-registry, and architecture
boundary set: 45 passed in 19.42 seconds. `git diff --cached --check` and AST
parsing of all changed Python sources also passed. The only later candidate
edits record these completed checks in this plan and release audit; the final
documentation-only delta is rechecked before commit.
