# AITP M4 Reviewed Skill Lifecycle Release Audit

Date: 2026-07-17

Status: implementation and exact staged candidate accepted. Protected concurrent
`README.md` integration remains before M4 is declared released.

## Accepted Boundary

- Only repeatable, executable, validated procedures can enter Skill
  distillation. Physics definitions, equations, derivations, literature
  summaries, sensemaking, and speculative Insight remain M3 knowledge paths.
- A candidate pins source topics/programs, recipes, independent final runs,
  validations, failures, artifacts, code states, environments, source records,
  selectors, prerequisites, stop rules, and transfer boundaries.
- Readiness requires two independent validated uses or one narrow validated use
  plus an exact, current, host-attested expert exception. Readiness does not
  create or install a package.
- A package is a host-neutral, content-addressed, multi-file tree reconstructed
  from exact blob receipts. Draft preview and proposal records have no install
  or trust authority.
- Install, reinstall, upgrade, downgrade, rollback, and patch apply share one
  project-root plan/checkpoint/journal/readback/receipt transaction. Generated
  commands have no ambient execution authority.
- Applicability advertises only completed, byte-current project-local installs.
  Actual use pins the exact version, package hash, proposal, install receipt,
  package artifact, consuming run/baseline, validations, failures, selectors,
  and parameters.
- Skill candidates, packages, installs, applicability, usage, and patches cannot
  create scientific evidence or update claim trust.

## Public And Context Surfaces

M4 Task 6 adds ten full-only CLI/MCP operations:

| Operation | Effect |
|---|---|
| `skill_distill_candidate` | `kernel_write` |
| `skill_assess_readiness` | `kernel_write` |
| `skill_build_package_preview` | `runtime_write` |
| `skill_record_package_proposal` | `kernel_write` |
| `skill_plan_deployment` | `kernel_write` |
| `skill_apply_deployment` | `kernel_write` |
| `skill_match_applicable` | `read_only` |
| `skill_record_usage` | `kernel_write` |
| `skill_propose_patch` | `kernel_write` |
| `skill_build_validation_request` | `read_only` |

All ten return the deeply validated `skill_operation_result` surface. Only
deployment apply can materialize package bytes, and only after revalidating an
exact host-attested checkpoint, source identity, action payload, target, diff,
policy, and package hash. Compact MCP remains exactly ten tools.

Startup and normal context emit no Skill data unless the host supplies an
explicit structured applicability request. A matching response contains at
most four bounded cards with name, version, package hash, proposal/install
refs, match source, confidence, and explicit expand/use operations. Route hints
contain no cards. Skill bodies, manifests, commands, validators, patches, and
selector explanations are never inlined.

## End-To-End Evidence

`tests/test_v5_gate4_skill_e2e.py` proves a LibRPA-shaped fixture lifecycle:

1. Two independent validated runs and structured failure coverage produce a
   procedural candidate.
2. Readiness and package rendering pin the exact process and provenance graph.
3. Installation is rejected without exact approval and succeeds only inside the
   dedicated project-local AITP namespace after approval.
4. A later applicability request finds only the byte-current completed install.
5. A later run records exact Skill use without changing scientific trust.

The same acceptance rejects repeated QFT definitions, derivations, and
speculative insights before provenance expansion or canonical Skill writes.
This is a procedural fixture, not real LibRPA scientific acceptance; the real
software/HPC journey remains an M6 requirement.

## Legacy Compatibility Correction

The blocking legacy lane found that curated legacy reports with attached
artifacts were being inferred as v2 support evidence. The migration path now
preserves those artifact links through an explicit `legacy_unchecked` evidence
writer. It still uses `RecordRepository`, but creates no support pins, basis
audit, evidence authority, or trust authority. The normal v2 evidence writer
and artifact/tool-run lineage policy were not relaxed.

The lane also now proves that a supposed checkpoint-only source review is
eligible only after a real acquired source blob, acquisition receipt, source
asset, exact reference location, admissible evidence, and typed review basis
exist. A human checkpoint cannot substitute for a missing source chain.

## Real-Store Audit

Authorized target:

`F:/AI_Workspace/Theoretical-Physics/research/aitp-topics/.aitp/indexes`

The initial status had a matching content watermark but stale derived state
tokens. The authorized rebuild changed only `.aitp/indexes` and produced:

| Measure | Result |
|---|---:|
| Query-index generation | 16 |
| Index/schema version | 3 / 3 |
| Indexed/checked paths | 9,947 / 9,947 |
| Malformed/build issues | 0 / 0 |
| Runtime-audit current registry files | 7,440 |
| Runtime-audit current families | 57 |
| Actual families missing from layout | 0 |
| Index fresh after rebuild | yes |
| Canonical watermark | `ce44b9c34a6d39448c9a67624091dd786893eed8e24f508c2f4fad24739cdd4a` |
| Index content hash | `4671fac65eba20137ee25c9c8c95968fc7389e679e0be79ba79f80f2f5e1bca5` |

The canonical watermark before and after rebuild was identical and matched the
published manifest. No real canonical record was written. The real store has
no completed M4 Skill install receipts, so this audit does not advertise a
real applicable Skill.

## Architecture And Test Evidence

All tests used Python 3.12 and isolated system-Temp bases.

| Scope | Result |
|---|---:|
| Task 6 facade/context/E2E red-to-green slice | 9 passed |
| Architecture/CLI/public/context regression | 77 passed |
| Prior Skill lifecycle/security regression | 86 passed |
| M0.5 focused classification regression | 15 passed |
| Source-readiness/install regressions | 33 passed |
| Evidence/legacy trust correction regression | 47 passed |
| Final runtime-audit/architecture/lane contracts | 36 passed |
| `foundation` blocking lane | 199 passed, 1 skipped |
| `compatibility` blocking lane | 142 passed |
| `v5-verticals` blocking lane | 1,245 passed, 2 skipped |
| `slow-adapter` blocking lane | 88 passed |
| `legacy-compat` blocking lane | 200 passed |
| `full --collect-only` unique tests | 1,867 collected |
| Staged `foundation` | 199 passed, 1 skipped |
| Staged `compatibility` | 141 passed |
| Staged `v5-verticals` | 1,238 passed, 2 skipped |
| Staged `slow-adapter` | 88 passed |
| Staged `legacy-compat` | 200 passed, 2 warnings |
| Staged `full --collect-only` | 1,859 collected |

The monolithic `full` process was attempted with a 30-minute scheduler limit and
timed out without a final pytest result. This is not reported as a pass. Its
five blocking constituent lanes all pass in both the worktree and an exact Git
index export. The staged tree has eight fewer unique tests because protected
concurrent test additions were deliberately excluded. The archived
`legacy-write-archive` lane was intentionally not run and remains non-blocking.

The current static audit reports 164 helper writers, 173 direct-mutation
candidates, and 726/726 declared production Python files parsed with zero
errors. Capability/family drift is empty, compact remains ten, and all touched
production modules remain within the 500-line architecture budget.

## Remaining Release Work

- Integrate the protected concurrent `README.md` changes without overwriting
  their owner. M4 remains a release candidate rather than released until the
  README describes the same reviewed lifecycle.
- M6 must still prove real LibRPA/HPC, formal-theory source-memory, new-software,
  and multi-topic journeys. Fixture success does not satisfy those real probes.
