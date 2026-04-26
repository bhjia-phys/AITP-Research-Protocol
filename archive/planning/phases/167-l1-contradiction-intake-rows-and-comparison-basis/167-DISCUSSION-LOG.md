# Phase 167: L1 Contradiction Intake Rows And Comparison Basis - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution
> agents. Decisions are captured in `167-CONTEXT.md`.

**Date:** 2026-04-13
**Phase:** 167-l1-contradiction-intake-rows-and-comparison-basis
**Mode:** auto (`gsd-discuss-phase 167 --auto`)
**Areas discussed:** data-model boundary, compatibility and scope safety,
verification boundary

---

## Data-model boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Upgrade the existing contradiction intake path | Enrich the current `contradiction_candidates` chain into richer source-backed contradiction rows. | ✓ |
| Invent a new top-level contradiction subsystem | Clean slate, but wide compatibility churn before value lands. | |
| Delay contradiction work until full adjudication exists | Keeps the gap open and blocks the next bounded intake improvement. | |

**Auto choice:** upgrade the existing contradiction intake path.
**Notes:** The codebase already has contradiction derivation, schema, and
acceptance surfaces; this phase should refine them rather than restart from
zero.

---

## Compatibility and scope safety

| Option | Description | Selected |
|--------|-------------|----------|
| Keep current consumers working, defer broad read-path rename | Preserve compatibility now; let Phase `167.1` handle user-facing wording changes. | ✓ |
| Break consumers now and rename everything immediately | Cleaner end state, but too wide for this phase. | |
| Keep the current thin shape unchanged | Too weak to solve the actual milestone goal. | |

**Auto choice:** keep current consumers working and defer broad rename/read-path
polish to Phase `167.1`.

---

## Verification boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Targeted unit/service/schema coverage now, bounded proof lane later | Keep `167` narrow and let `167.1` close the milestone proof. | ✓ |
| Force the full contradiction-aware proof into this phase | Overloads the phase and blurs the roadmap split. | |
| Unit-only with no service/schema coverage | Too weak for a row-shape upgrade. | |

**Auto choice:** targeted unit/service/schema coverage in `167`, proof lane in
`167.1`.

---

## the agent's Discretion

- exact richer row fields and dedup keys
- exact compatibility projection strategy
- whether to keep the internal field name unchanged throughout the phase

## Deferred Ideas

- contradiction clustering across many sources
- scientific adjudication of which source is correct
- automatic route mutation from contradiction rows
