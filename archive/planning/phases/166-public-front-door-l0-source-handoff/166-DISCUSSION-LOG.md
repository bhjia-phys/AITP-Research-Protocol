# Phase 166: Public Front Door L0 Source Handoff - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution
> agents. Decisions are captured in `166-CONTEXT.md`.

**Date:** 2026-04-13
**Phase:** 166-public-front-door-l0-source-handoff
**Mode:** auto (`gsd-discuss-phase 166 --auto`)
**Areas discussed:** Primary handoff lane, Surface parity, Honesty boundary,
Verification boundary

---

## Primary handoff lane

| Option | Description | Selected |
|--------|-------------|----------|
| Discovery-first primary lane | Use `discover_and_register.py` as the default "start here" path when the user only has a topic/query; list direct registration and doc surfaces as alternates. | ✓ |
| Registration-first primary lane | Default to `register_arxiv_source.py` and treat discovery as a secondary tool. | |
| Doc-first handoff | Point only to `ARXIV_FIRST_SOURCE_INTAKE.md` and let the operator infer commands from the doc. | |

**User's choice:** Auto-selected recommended default: discovery-first primary
lane.
**Notes:** This keeps one concrete starting point while still exposing the
already shipped direct-registration and runbook surfaces for operators who
already know an arXiv id.

---

## Surface parity

| Option | Description | Selected |
|--------|-------------|----------|
| Shared payload across surfaces | Add one shared handoff payload or source-of-truth block consumed by dashboard, runtime protocol, and replay. | ✓ |
| Per-surface prose patches | Update each surface independently with hand-written copy. | |
| Dashboard-only | Improve only `topic_dashboard.md` first and defer protocol/replay parity. | |

**User's choice:** Auto-selected recommended default: shared payload across
surfaces.
**Notes:** The requirement is cross-surface parity, and the existing runtime
bundle architecture already centralizes next-action truth.

---

## Honesty boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Advisory handoff only when blocked on L0 | Show the handoff only for real `l0_source_expansion` / `return_to_L0` cases; do not auto-run discovery or registration. | ✓ |
| Auto-run discovery | Trigger `discover_and_register.py` automatically when a query is available. | |
| Always-visible helper block | Show the same handoff even when the topic is not currently blocked on missing sources. | |

**User's choice:** Auto-selected recommended default: advisory handoff only
when blocked on `L0`.
**Notes:** This phase is about making the honest gap actionable, not about
faking progress or widening into automatic execution.

---

## Verification boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Regression-first in Phase 166 | Add bounded tests for concrete handoff wording and cross-surface parity; keep the fresh-topic registration proof for Phase `166.1`. | ✓ |
| Full handoff-plus-registration proof now | Force the end-to-end registration lane into Phase `166`. | |
| Minimal no-test doc change | Land the handoff copy without adding targeted regression coverage. | |

**User's choice:** Auto-selected recommended default: regression-first in Phase
`166`.
**Notes:** The roadmap already reserves the actual registration proof for Phase
`166.1`, so this phase should stay narrow and keep the milestone sequencing
honest.

---

## the agent's Discretion

- final helper-object shape for the shared handoff payload
- exact markdown layout of the handoff block on each surface
- whether command examples are inline or path-only, as long as the same facts
  stay visible everywhere

## Deferred Ideas

- contentful-by-default arXiv registration in Phase `166.1`
- non-arXiv provider expansion
- automatic discovery/registration from the runtime queue
