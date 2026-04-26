# Phase 168: Analytical Check Rows And Review Contract Expansion - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution
> agents. Decisions are captured in `168-CONTEXT.md`.

**Date:** 2026-04-13
**Phase:** 168-analytical-check-rows-and-review-contract-expansion
**Mode:** auto (`gsd-discuss-phase 168 --auto`)
**Areas discussed:** review-contract boundary, check-row semantics,
verification boundary

---

## Review-contract boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Upgrade the existing `analytical_review` artifact family | Enrich the current theory-packet artifact and public CLI/service path instead of restarting the subsystem. | ✓ |
| Invent a new analytical cross-check artifact family | Cleaner split in theory, but wide compatibility churn before value lands. | |
| Defer the contract change until the runtime/read-path phase | Keeps the current flatter review payload open and blocks the milestone split. | |

**Auto choice:** upgrade the existing `analytical_review` artifact family.
**Notes:** `v1.47` already landed a working production analytical-review lane,
so the next bounded step should refine that contract rather than replace it.

---

## Check-row semantics

| Option | Description | Selected |
|--------|-------------|----------|
| Make each `checks[]` row self-contained and keep top-level compatibility rollups | Solves the contract gap while preserving current readers. | ✓ |
| Keep thin check rows and only enrich top-level review fields | Leaves the row surface too flat for later runtime parity. | |
| Redesign runtime/read-path rendering now | Useful later, but too wide for Phase `168`. | |

**Auto choice:** make each `checks[]` row self-contained and keep top-level
compatibility rollups.
**Notes:** This keeps the public field path stable while making each bounded
check durable enough for later read-path work.

---

## Verification boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Targeted CLI/service/e2e contract coverage now, proof lane later | Keeps `168` narrow and lets `168.1` close the milestone with the richer runtime surface. | ✓ |
| Force a new analytical proof lane into this phase | Overloads the phase and blurs the roadmap split. | |
| Unit-only coverage with no compatibility guard | Too weak for a contract-expansion phase. | |

**Auto choice:** targeted CLI/service/e2e contract coverage now, proof lane in
`168.1`.
**Notes:** The existing analytical judgment acceptance script should stay green
as a compatibility guard, but the new milestone-close proof lane remains a
follow-on deliverable.

---

## the agent's Discretion

- exact row field names for row-level context
- whether top-level compatibility fields are derived rollups or mirrored
  defaults
- whether existing review-level CLI flags are projected into each row only, or
  whether optional row-specific overrides are also added

## Deferred Ideas

- fresh runtime/read-path analytical cross-check presentation
- a new bounded analytical proof harness
- symbolic backend or route-mutation work driven by analytical checks
