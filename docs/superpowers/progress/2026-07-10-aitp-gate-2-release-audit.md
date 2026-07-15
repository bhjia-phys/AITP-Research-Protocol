# AITP M2 Reproducible Execution And Derivation Release Audit

Date: 2026-07-15

Status: M2 fixture-contract acceptance complete. The implementation proves the
typed execution, HPC intake, formula-code, and formal-derivation contracts on
deterministic fixtures. It does not claim a real LibRPA/HPC operational run;
that remains a mandatory M6 probe.

## Released Boundary

- Typed Markdown/YAML records remain canonical. Intake reports, maturity
  projections, edit capsules, context bundles, and execution operation results
  are derived and cannot update scientific trust.
- Tool runs retain recorded maturity. Only an immutable accepted-baseline
  record can project `effective_maturity=accepted_baseline`.
- Accepted baselines freeze typed refs, record hashes, revisions, artifact
  bytes, dirty-code patch manifests, validation inputs, failure contracts, and
  a subject-bound human checkpoint application receipt.
- Monitor snapshots are immutable observations. Scheduler state and partial
  output are process evidence, never scientific completion.
- Formal derivations persist assumptions, conventions, source anchors,
  inspectable steps, checks, gaps, and review state without hidden reasoning.
- Cross-topic/program execution dependencies require explicit scope policy and
  target-side revalidation. Context exact reads preserve canonical envelope
  scope and hash metadata.

## Full And Compact Surfaces

The M2 facade deliberately exposes 11 full/CLI operations:

- Eight read-only operations: exact record version, scope assessment, detached
  compute intake, effective attempt, baseline readiness, maturity projection,
  formula-code capsule, and derivation status.
- Three kernel writes: request a bound checkpoint, decide it with host
  attestation, and apply the bound action through an immutable receipt.

Direct environment, recipe, run, baseline, artifact, patch, monitor,
derivation, migration, and review writers are not public facade operations.
They remain internal repository services because exposing them without the
host pre-tool binding would weaken provenance. The compact MCP surface remains
exactly 10 tools; every M2 operation has `compact_visibility=full`.

## Fixture End-To-End Evidence

`tests/test_v5_gate2_execution_e2e.py` proves two verticals:

1. A LibRPA-shaped HPC fixture records a redacted environment, exact code and
   patch state, recipe, structured run, immutable monitor history, validation,
   bound human approval, checkpoint application receipt, and accepted
   baseline. Normal context recovers the run, baseline, monitor, and
   environment; exact expansion verifies the pinned environment hash and
   revision. Partial output and dirty unpatched code remain ineligible.
2. A source-anchored formal derivation retains assumptions and conventions,
   exposes a repaired structural chain, keeps review/validation distinct, and
   stores no hidden-reasoning fields.

Both flows compare the canonical claim before and after. Claim content hash,
revision, confidence, and active binding remain unchanged.

## Real-Store Compatibility Audit

The authorized audit rebuilt only
`F:/AI_Workspace/Theoretical-Physics/research/aitp-topics/.aitp/indexes`.
No canonical topic record was modified.

| Measure | Result |
|---|---:|
| Canonical records checked/indexed | 9,947 / 9,947 |
| Registered families | 61 |
| Malformed records | 0 |
| Index generation | 14 |
| Canonical watermark before/manifest/after | `ce44b9c34a6d39448c9a67624091dd786893eed8e24f508c2f4fad24739cdd4a` |

The quantum-gravity session context compiled fresh with zero errors in 4.131 s
(499 estimated tokens, 4,730 bytes). The LibRPA/QSGW session context compiled
fresh with zero errors in 2.834 s (432 estimated tokens, 4,281 bytes). Both
reported no trust write. The LibRPA result recovered code, artifact, evidence,
tool recipe/run, validation, and relation families through progressive
disclosure.

## Classification And Static Audit

The refreshed M0.5 audit uses exact set equality:

| Inventory | Result |
|---|---:|
| Classified capabilities, excluding protected optional dossier | 247 |
| Registered record families | 61 |
| Named helper writers classified | 146 / 146 |
| Direct mutation candidates classified | 168 / 168 |
| Declared production Python files parsed | 642 / 642 |

The external-tree parser now derives the execution capability rows from the
literal `_READ` and `_GATED` operation maps. The live-repository path uses the
canonical runtime registries. This prevents dynamic execution registration
from disappearing from static drift audits.

## Test Evidence

All listed commands used Python 3.12 and isolated `--basetemp` directories in
the system Temp directory.

| Scope | Result | Pytest time |
|---|---:|---:|
| Final focused context/audit/lock set | 55 passed | 14.65 s |
| Broad M2 regression, 29 files | 293 passed | 59.40 s |
| Blocking foundation lane | 190 passed, 1 skipped | 36.30 s |
| Final facade/runtime/lane/architecture candidate | 41 passed | 11.29 s |

An earlier blocking-full attempt exceeded 904 seconds without a pytest
summary. It was terminated and is not reported as passed. Archived legacy
L0-L4 write E2Es were not run and are not release gates; only legacy reads,
migration compatibility, schema-v1 materialization, and write guards remain
blocking compatibility obligations.

## Review Findings Closed

Independent review identified and the final patch closed these issues:

- Exact operational refs could cross a research-program boundary because typed
  dataclass materialization discarded envelope-only scope metadata.
- Exact environment recovery did not expose the canonical content hash and
  verified request pin.
- Static external-tree audit omitted dynamically registered execution rows.
- Windows extended drive/UNC lock aliases could acquire different in-process
  lock keys.
- Classification prose retained stale vertical counts.

Regression tests now cover each boundary. Exact reads merge canonical
frontmatter with normalized typed fields; they do not trust the disposable
index for scope or hash facts.

## Release Scope And Residual Work

The implementation spans commits `9844aab1` through `086622f9`. Protected
Harness Feedback files and their README/compatibility-shard work, unrelated
untracked artifacts, and all real canonical topic records were excluded from
the final fixture/context closeout commit. README reconciliation remains owned
by the protected concurrent documentation change.

M2 establishes deterministic contract readiness only. M6 must still ingest a
hash-pinned real LibRPA/HPC collector manifest, resolve actual code/branch/job/
script/output provenance, and decide whether the operational workflow is
reproducible. M3 may now depend on M2 pinned refs, artifact receipts,
checkpoint receipts, derivation records, and exact-expansion semantics.
