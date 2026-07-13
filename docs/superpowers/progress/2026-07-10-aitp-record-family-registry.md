# AITP Record-Family Registry Migration

## Boundary

This checkpoint centralizes record-family metadata without rewriting the canonical
topic store. It is structural migration evidence only: it cannot update kernel
state, evidence status, validation status, memory promotion, or claim trust.

## Result

- Canonical specs: `46`
- Normal `registry/<family>` specs: `42`
- Special-path specs: `4` (`contexts`, `topics`, `sessions`, `memory_entries`)
- Real registry records inspected: `7,235`
- Code-used families absent from layout before migration: `8`
- Actual families absent from layout before migration: `5`
- Code-used families absent from layout after migration: `0`
- Actual families absent from layout after migration: `0`
- Layout-only families with no current writer: `6`

The six layout-only families are `attempts`, `benchmarks`, `ideas`, `intents`,
`outputs`, and `questions`. Their specs use
`auto_write_policy=unimplemented_layout`; this preserves old paths and exact-ref
readability without claiming that AITP has a supported writer for them.

## Canonical Projections

The following consumers now derive from `RecordFamilySpec`:

- `WorkspacePaths.ensure_layout()` normal registry directories
- exact record-ref kinds, aliases, paths, record classes, roles, and surfaces
- workspace inventory family accounting
- lifecycle-enabled subject kind/family/class maps
- runtime audit fallback for a dynamically projected `_LAYOUT_DIRS`

Context, topic, session, and promoted-memory records remain explicit special
paths. They are not counted as ordinary registry families.

## Verification

- Family/layout/lifecycle/recording slice: `54 passed`
- Exact-ref compatibility slice: `2 passed`
- Runtime-audit module: `9 passed`
- Architecture boundary: `4 passed, 2 failed`

The two architecture failures are the pre-existing baseline: 39 source modules
remain above the 500-line limit, and `brain/v5/cli.py` remains 1,509 lines. This
task added no oversized module and did not raise either limit.

## Next M0 Work

The registry is metadata convergence, not yet safe storage. The next tasks add a
compatibility `RecordEnvelope`, then a strict atomic `RecordRepository` with
idempotency, malformed-record diagnostics, and revision/supersession controls.
