# AITP Runtime And Knowledge Foundations

## Current Position

The previously scoped GSD mainline is implemented through:

- `v1.28`
- `v1.29`
- `v1.30`
- `v1.31`
- first `v1.32` slice
- first `v1.33` slice
- `v1.34`
- `v1.35`
- `v1.36`
- `v1.37`
- `v1.38`
- `v1.39`
- `v1.40`
- `v1.41`
- `v1.42`
- `v1.43`
- `v1.44`
- `v1.45`
- `v1.46`
- `v1.47`
- `v1.48`
- `v1.49`
- `v1.50`
- `v1.51`
- `v1.52`
- `v1.53`
- `v1.54`
- `v1.55`
- `v1.56`
- `v1.57`
- `v1.58`
- `v1.59`
- `v1.60`
- `v1.61`
- `v1.62`
- `v1.63`
- `v1.64`

That closes the current bounded chain through the L1 method-specificity surface,
but
it still does **not** mean the broader AITP architecture is finished.

## Current Focus

- Active milestone: `v1.65` `Installation And Adoption Readiness`
- Latest closed milestone: `v1.64` `L1 Method Specificity Surface`
- Next boundary: discuss and plan Phase `127`

## Current Milestone: v1.65 Installation And Adoption Readiness

**Goal:** Make installation verification, first-run quickstart, and
Windows-native bootstrap behavior converge into one honest adoption surface for
Codex, Claude Code, and OpenCode.

**Target features:**
- a machine-readable `aitp doctor` / remediation contract for the three
  front-door runtimes
- a shared `bootstrap -> loop -> status` quickstart with isolated acceptance
  coverage
- Windows-native bootstrap paths that do not assume bash or POSIX symlink
  habits for the default experience

**Explicitly deferred from this milestone:**
- `999.48` PyPI publishable package
- OpenClaw deep parity beyond specialized-lane visibility

## Latest Closed Milestone: v1.64 L1 Method Specificity Surface

**Goal:** Close the first still-missing production slice of backlog `999.27`
by giving AITP a real source-backed method-specificity surface inside
`l1_source_intake`.

**Closed features:**
- `method_specificity_rows` with method family, specificity tier, and evidence
  excerpt
- topic-shell, runtime-bundle, and `status --json` exposure for that surface
- one isolated non-mocked acceptance path through real runtime status

## Previous Closed Milestone: v1.63 Source Citation BibTeX Surface

**Goal:** Close backlog `999.26` by adding real Layer 0 BibTeX import/export
capabilities on top of the already-implemented citation traversal and source
catalog surfaces.

**Closed features:**
- a new extracted helper module:
  `research/knowledge-hub/knowledge_hub/source_bibtex_support.py`
- new production CLI/service entrypoints:
  `export-source-bibtex` and `import-bibtex-sources`
- durable `.bib`, `.json`, and `.md` import/export artifacts plus updated
  source-catalog acceptance coverage

## Previous Closed Milestone: v1.62 Scratchpad And Negative Result Runtime Surface

**Goal:** Close the first production slice of backlog `999.28` by giving AITP
a durable topic-scoped scratchpad surface for route comparison, open questions,
failed attempts, and negative-result retention.

## Maturity Ladder

Completing all backlog items does **not** mean AITP is mature. It means
every L0-L5 surface has a real production path. The backlog answers "does this
feature exist?" but not "is this feature actually useful for research?"

```
engineering skeleton complete
        │
        ▼
all backlog closed
  → protocol surface complete (every L0-L5 layer has a real path)
        │
        ▼
real topic E2E
  → research utility verified (1-2 real physics topics run full L0→L2)
        │
        ▼
multi-user feedback
  → protocol design validated (multiple people used it and found it useful)
        │
        ▼
benchmark evidence
  → value quantified (AITP measurably improved research efficiency vs.
    unassisted workflow)
        │
        ▼
  mature
```

Dimensions the backlog does **not** cover:

- Real topic end-to-end validation with genuine physics research questions.
- Cross-runtime deep execution parity (Codex is baseline; OpenCode, Claude
  Code, OpenClaw are still "parity targets").
- Multi-user feedback on whether the bounded-step protocol helps or creates
  friction compared to how physicists actually work.
- Knowledge-graph content quality beyond a thin seeded baseline.
- At least one real semi-formal theory result exported through the Lean
  bridge.

Use this ladder when deciding what to promote next and when to claim a
milestone represents genuine progress rather than surface coverage.

## Important Honesty Boundary

Closing a milestone or finishing a backlog slice does **not** mean:

- that AITP now has full `L0-L5` maturity,
- that the current milestone is the last remaining engineering gap,
- or that AITP is finished.

It means the current milestone is archived on a verified baseline and the next
step is choosing the next bounded milestone rather than casually reopening
already-shipped surfaces.

## Closure History

- `.planning/V1.30_CLOSURE_AUDIT.md`
- `.planning/V1.31_CLOSURE_AUDIT.md`
- `.planning/V1.32_SLICE1_AUDIT.md`
- `.planning/V1.33_SLICE1_AUDIT.md`
- `.planning/V1.34_CLOSURE_AUDIT.md`
- `.planning/V1.35_CLOSURE_AUDIT.md`
- `.planning/milestones/v1.36-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.37-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.38-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.39-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.40-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.41-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.42-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.43-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.44-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.45-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.46-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.47-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.48-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.49-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.50-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.51-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.52-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.53-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.54-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.55-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.56-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.57-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.58-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.59-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.60-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.61-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.62-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.63-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.64-MILESTONE-AUDIT.md`

## Latest Integrated Regression Evidence

- `368 passed, 10 subtests passed` on 2026-04-11
- method-specificity slice:
  - `python -m pytest research/knowledge-hub/tests/test_topic_start_regressions.py research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_runtime_profiles_and_projections.py research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_aitp_cli_e2e.py research/knowledge-hub/tests/test_l1_method_specificity_contracts.py -q`
  - result: `175 passed`
- method-specificity acceptance:
  - `python research/knowledge-hub/runtime/scripts/run_l1_method_specificity_acceptance.py --json`
  - result: `success`
- maintainability-budget gate:
  - `python -m pytest research/knowledge-hub/tests/test_maintainability_budgets.py -q`
  - result: `2 passed`
- full knowledge-hub suite:
  - `python -m pytest research/knowledge-hub/tests -q`
  - result: `368 passed, 10 subtests passed`

## Immediate Reality Check

This does **not** mean AITP is finished.

It means `v1.65` is now the active install/adoption milestone and the next step
is discussing and planning Phase `127`.

---
*Last updated: 2026-04-11 after opening v1.65 Installation And Adoption Readiness*
