# Retrospective

## Milestone: v2.0 — Three-Lane Real-Topic Natural-Language E2E

**Shipped:** 2026-04-14
**Phases:** 3 | **Plans:** 3

### What Was Built

- one real natural-language dialogue proof for the formal-theory lane
- one real natural-language dialogue proof for the toy-model lane
- one real natural-language dialogue proof for the first-principles /
  code-method lane
- one cross-lane readiness report that records the bounded success boundary and
  next widening decision for each lane

### What Worked

- reusing the bounded positive-L2 acceptance wrappers kept the dialogue proofs
  honest and mechanically replayable
- requiring fresh topic slugs and preserved `interaction_state` /
  `research_question.contract` artifacts made the hidden-seed question concrete
- phase-level receipts plus one cross-lane report closed the milestone without
  overclaiming broad scientific maturity

### What Was Inefficient

- Phase `174` originally lacked a `PLAN.md`, which confused GSD progress
  tooling at lifecycle time
- the milestone archive CLI extracted weak accomplishments from the summaries,
  so the archive surfaces still needed manual repair
- this milestone followed the newer summary-and-receipt audit convention, but
  the toolchain still assumes per-phase `VERIFICATION.md` files in some places

### Patterns Established

- "real-topic dialogue proof" now has a stable recipe: fresh dialogue request,
  runtime steering-artifact preservation, and authoritative-L2 parity check
- cross-lane closure belongs in the final phase of a milestone, not in chat
  memory
- bounded widening blockers should be written as explicit next-routing notes at
  milestone close

### Key Lessons

- always land a `PLAN.md` even for one-plan phases if the milestone will need
  GSD lifecycle tooling later
- archive automation is useful, but it still needs evidence-led manual review
  before final commit and tag
- the honest unit of progress for AITP is still the bounded lane, not the broad
  product claim

### Cost Observations

- exact token and model-mix telemetry was not captured in repo artifacts
- the final milestone closure happened in two focused implementation passes:
  first toy-model dialogue proof, then first-principles dialogue proof plus
  cross-lane report

## Cross-Milestone Trends

- acceptance-wrapper reuse remains the fastest way to widen AITP honestly
  without bypassing existing runtime surfaces
- lifecycle friction now mostly comes from planning hygiene gaps, not from the
  bounded science routes themselves
