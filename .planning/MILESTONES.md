# Milestones

## v1.95 L2 Promotion Pipeline Closure (Active)

**Phases completed:** 2 / 3 phases, 2 / 3 plans

**Milestone goal:**

- close the L4→L2 promotion pipeline gap discovered during Jones E2E testing
- extend canonical schema so `negative_result` has a promotion path
- create runtime proof schemas and wire promotion bridge code
- make three targeted HCI improvements for better E2E test ergonomics

**Key accomplishments:**

- `negative_result` now has an active canonical schema path instead of stopping
  at staging-only vocabulary
- the runtime proof packet contracts now also ship in the package-local
  `research/knowledge-hub/schemas/` surface for downstream promotion code
- Layer 2 canonical index materialization now recognizes negative-result units
- promotion gates and auto-promotion now expose and validate runtime proof
  packet schema context through a dedicated bridge module

---

## v1.94 L4 Analytical Cross-Check Surface (Shipped: 2026-04-13)

**Phases completed:** 2 phases, 2 plans, milestone audit passed

**Milestone goal:**

- record bounded analytical checks as first-class rows
- carry exact source anchors and assumption or regime context with each check
- expose analytical cross-checks on runtime-facing read paths and close with a
  bounded proof lane

**Key accomplishments:**

- analytical validation now records row-first bounded check entries including
  `source_cross_reference`
- runtime-facing read paths now expose a structured analytical cross-check
  surface through the existing validation review bundle
- the milestone closes with a dedicated analytical cross-check proof lane
- the older analytical judgment runtime lane remains compatible after the
  runtime-surface expansion

---

## v1.93 L1 Contradiction Adjudication Surface (Shipped: 2026-04-13)

**Phases completed:** 2 phases, 2 plans, milestone audit passed

**Milestone goal:**

- make contradictory or mutually incompatible source claims explicit in `L1`
  intake
- carry bounded comparison context with each contradiction row so the operator
  can judge why the conflict was surfaced
- expose the contradiction surface on runtime read paths and close with one
  bounded proof lane

**Key accomplishments:**

- contradiction rows are now richer, source-backed, and pairwise
- contradiction parity now survives across runtime/read-path surfaces
- the milestone closes with a dedicated contradiction-aware proof lane

---

## v1.92 Public Front Door Source Handoff (Shipped: 2026-04-13)

**Phases completed:** 2 phases, 2 plans, milestone audit passed

**Milestone goal:**

- turn the honest post-bootstrap return to `L0` into one concrete
  source-acquisition handoff
- keep `status`, `runtime_protocol`, and `replay-topic` aligned on that
  handoff surface
- make arXiv registration contentful-by-default so following the handoff is
  useful immediately

**Key accomplishments:**

- the public front door now exposes one concrete `L0` source-acquisition lane
  instead of generic prose
- dashboard, runtime protocol, and replay now share one explicit
  `l0_source_handoff` truth surface
- arXiv registration and discovery-driven registration now attempt content
  acquisition by default with `--metadata-only` as the explicit opt-out
- one fresh-topic proof now lands
  `bootstrap -> concrete handoff -> registration`

---

## v1.91 Real Topic L0 To L2 End-To-End Validation (Shipped: 2026-04-13)

**Phases completed:** 7 phases, 3 plan files, milestone audit passed

**Key accomplishments:**

- one honest real-topic Jones route now has durable postmortem and issue-ledger
  evidence instead of chat-only conclusions
- `proof_fragment` now has a schema, a Jones bootstrap seed, and the first
  canonical proof-fragment instance
- mode-aware runtime behavior, human-readable front-door surfaces, and
  mechanical governance all landed as routed follow-up to the real-topic run
- `L0 -> L1` now includes DeepXiv-style enrichment, concept graphs,
  progressive reading, graph analysis, and Obsidian-compatible export
- the public AITP front door now has a fresh real-topic proof with an honest
  bounded return-to-`L0` outcome

---

## v1.90 Hypothesis Route Transition Authority Surface (Shipped: 2026-04-12)

**Phases completed:** 1 phase, 1 plan, 2 tasks

**Key accomplishments:**

- `route_transition_authority` now surfaces whether a committed route is still
  waiting on commitment, still pending authority, or already authoritative
  across current-topic truth surfaces
- runtime status, the runtime protocol note, and replay now expose
  post-commitment authority state without replacing transition commitment or
  helper mechanisms
- one isolated acceptance lane now proves route-transition-authority
  visibility stays declarative and does not widen into fresh runtime mutation

---

## v1.89 Hypothesis Route Transition Commitment Surface (Shipped: 2026-04-12)

**Phases completed:** 1 phase, 1 plan, 2 tasks

**Key accomplishments:**

- `route_transition_commitment` now surfaces whether a resumed route is still
  waiting on resumption, still pending commitment, or already the durable
  committed bounded lane
- runtime status, the runtime protocol note, and replay now expose
  post-resumption commitment state without replacing transition resumption or
  helper mechanisms
- one isolated acceptance lane now proves route-transition-commitment
  visibility stays declarative and does not widen into fresh runtime mutation

---

## v1.88 Hypothesis Route Transition Resumption Surface (Shipped: 2026-04-12)

**Phases completed:** 1 phase, 1 plan, 2 tasks

**Key accomplishments:**

- `route_transition_resumption` now surfaces whether ready follow-through is
  still waiting, still pending, or already durably resumed on the bounded route
- runtime status, the runtime protocol note, and replay now expose
  post-followthrough re-entry state without replacing transition follow-through
  or helper mechanisms
- one isolated acceptance lane now proves route-transition-resumption
  visibility stays declarative and does not widen into fresh runtime mutation

---

## v1.87 Hypothesis Route Transition Followthrough Surface (Shipped: 2026-04-12)

**Phases completed:** 1 phase, 1 plan, 2 tasks

**Key accomplishments:**

- `route_transition_followthrough` now surfaces whether bounded transition work
  stays held by clearance or is ready to resume from an authoritative ref
- runtime status, the runtime protocol note, and replay now expose
  post-clearance next-step state without replacing transition clearance or
  helper mechanisms
- one isolated acceptance lane now proves route-transition-followthrough
  visibility stays declarative and does not widen into fresh runtime mutation

---

## v1.86 Hypothesis Route Transition Clearance Surface (Shipped: 2026-04-12)

**Phases completed:** 1 phase, 1 plan, 2 tasks

**Key accomplishments:**

- `route_transition_clearance` now surfaces whether a bounded escalated
  transition is still waiting, blocked on a checkpoint, or already released
- runtime status, the runtime protocol note, and replay now expose
  checkpoint-mediated release state without replacing transition escalation or
  helper mechanisms
- one isolated acceptance lane now proves route-transition-clearance
  visibility stays declarative and does not widen into fresh runtime mutation

---

## v1.85 Hypothesis Route Transition Escalation Surface (Shipped: 2026-04-12)

**Phases completed:** 1 phase, 1 plan, 2 tasks

**Key accomplishments:**

- `route_transition_escalation` now surfaces whether a bounded repair stays
  local, recommends a checkpoint, or is already backed by an active checkpoint
- runtime status, the runtime protocol note, and replay now expose escalation
  state without replacing transition repair or helper mechanisms
- one isolated acceptance lane now proves route-transition-escalation
  visibility stays declarative and does not widen into fresh runtime mutation

---

## v1.82 Hypothesis Route Transition Resolution Surface (Shipped: 2026-04-12)

**Phases completed:** 1 phase, 1 plan, 2 tasks

**Key accomplishments:**

- `route_transition_resolution` now synthesizes transition intent, transition
  receipt, and active-route alignment into one resolved handoff outcome
- runtime status, the runtime protocol note, and replay now expose the resolved
  transition outcome without replacing transition receipt or helper mechanisms
- one isolated acceptance lane now proves route-transition-resolution
  visibility stays declarative and does not widen into fresh runtime mutation

---

## v1.81 Hypothesis Route Transition Receipt Surface (Shipped: 2026-04-12)

**Phases completed:** 1 phase, 1 plan, 2 tasks

**Key accomplishments:**

- `route_transition_receipt` now surfaces whether intended bounded handoff has
  been durably recorded
- runtime status, the runtime protocol note, and replay now expose the durable
  receipt location without replacing transition intent or helper mechanisms
- one isolated acceptance lane now proves route-transition-receipt visibility
  stays declarative and does not widen into fresh runtime mutation

---

## v1.80 Hypothesis Route Transition Intent Surface (Shipped: 2026-04-12)

**Phases completed:** 1 phase, 1 plan, 2 tasks

**Key accomplishments:**

- `route_transition_intent` now surfaces the declarative source route and
  target route after the bounded transition gate
- runtime status, the runtime protocol note, and replay now expose transition
  intent status without replacing the transition gate or helper mechanisms
- one isolated acceptance lane now proves route-transition-intent visibility
  stays declarative and does not mutate runtime state

---

## v1.79 Hypothesis Route Transition Gate Surface (Shipped: 2026-04-12)

**Phases completed:** 1 phase, 1 plan, 2 tasks

**Key accomplishments:**

- `route_transition_gate` now surfaces blocked versus available versus
  checkpoint-required yielding
- runtime status, the runtime protocol note, and replay now expose the gate
  artifact and transition-gate status without replacing route choice or helper
  mechanisms
- one isolated acceptance lane now proves route-transition-gate visibility
  stays declarative and does not mutate runtime state

---

## v1.78 Hypothesis Route Choice Surface (Shipped: 2026-04-12)

**Phases completed:** 1 phase, 1 plan, 2 tasks

**Key accomplishments:**

- `route_choice` now surfaces one stay-local versus yield-to-handoff summary
- runtime status, the runtime protocol note, and replay now expose route-choice
  status and both bounded options without replacing current-route-choice or
  helper mechanisms
- one isolated acceptance lane now proves route choice visibility stays
  declarative and does not mutate runtime state

---

## v1.77 Hypothesis Route Handoff Surface (Shipped: 2026-04-12)

**Phases completed:** 1 phase, 1 plan, 2 tasks

**Key accomplishments:**

- `route_handoff` now surfaces one primary parked-route handoff candidate plus
  explicit keep-parked decisions
- runtime status, the runtime protocol note, and replay now expose the handoff
  candidate count and handoff candidate id without replacing re-entry or helper
  mechanisms
- one isolated acceptance lane now proves handoff visibility stays declarative
  and does not mutate runtime state

---

## v1.76 Hypothesis Route Re-entry Surface (Shipped: 2026-04-12)

**Phases completed:** 1 phase, 1 plan, 2 tasks

**Key accomplishments:**

- `route_reentry` now surfaces deferred waiting conditions plus follow-up
  return readiness directly on parked hypotheses
- runtime status, the runtime protocol note, and replay now expose the
  re-entry-ready count and parked-route condition summaries without replacing
  deferred or follow-up helper mechanisms
- one isolated acceptance lane now proves re-entry visibility stays
  declarative and does not auto-reactivate the deferred route or write a
  reintegration receipt

---

## v1.75 Hypothesis Route Activation Surface (Shipped: 2026-04-12)

**Phases completed:** 1 phase, 1 plan, 2 tasks

**Key accomplishments:**

- `route_activation` now surfaces the active local hypothesis, its bounded next
  action, and the parked-route obligation lanes directly
- runtime status, the runtime protocol note, and replay now expose parked-route
  counts and obligations without replacing the queue, deferred buffer, or
  follow-up subtopics
- one isolated acceptance lane now proves route activation stays declarative
  and does not auto-spawn a follow-up topic directory

---

## v1.74 Hypothesis Branch Routing Surface (Shipped: 2026-04-12)

**Phases completed:** 1 phase, 1 plan, 2 tasks

**Key accomplishments:**

- each competing hypothesis now carries explicit branch-routing metadata
- `status --json`, the runtime protocol note, and replay now expose the active
  branch hypothesis plus parked-route ids and counts
- one isolated acceptance lane now proves routing coexists with steering,
  deferred parking, and follow-up subtopics

---

## v1.73 Competing Hypotheses First-Class Surface (Shipped: 2026-04-12)

**Phases completed:** 1 phase, 1 plan, 2 tasks

**Key accomplishments:**

- `research_question.contract.json|md` now keeps explicit competing
  hypotheses with status, evidence refs, and exclusion notes

- `status --json`, the runtime protocol note, and replay now expose the
  leading hypothesis plus count/exclusion summary

- one isolated acceptance lane now proves the question-level hypothesis
  surface coexists with deferred candidates and follow-up subtopics

---

## Status

Completed milestone chain:

- `v1.28` implemented
- `v1.29` implemented
- `v1.30` implemented
- `v1.31` implemented
- `v1.32` first slice implemented
- `v1.33` first slice implemented
- `v1.34` implemented
- `v1.35` implemented
- `v1.36` implemented
- `v1.37` implemented
- `v1.38` implemented
- `v1.39` implemented
- `v1.40` implemented
- `v1.41` implemented
- `v1.42` implemented
- `v1.43` implemented
- `v1.44` implemented
- `v1.45` implemented
- `v1.46` implemented
- `v1.47` implemented
- `v1.48` implemented
- `v1.49` implemented
- `v1.50` implemented
- `v1.51` implemented
- `v1.52` implemented
- `v1.53` implemented
- `v1.54` implemented
- `v1.55` implemented
- `v1.56` implemented
- `v1.57` implemented
- `v1.58` implemented
- `v1.59` implemented
- `v1.60` implemented
- `v1.61` implemented
- `v1.62` implemented
- `v1.63` implemented
- `v1.64` implemented
- `v1.65` implemented
- `v1.66` implemented
- `v1.67` implemented
- `v1.68` implemented
- `v1.69` implemented
- `v1.70` implemented
- `v1.71` implemented
- `v1.72` implemented
- `v1.73` implemented
- `v1.74` implemented
- `v1.75` implemented
- `v1.76` implemented
- `v1.77` implemented
- `v1.78` implemented
- `v1.79` implemented
- `v1.80` implemented
- `v1.81` implemented
- `v1.82` implemented
- `v1.83` implemented
- `v1.84` implemented
- `v1.85` implemented
- `v1.86` implemented
- `v1.87` implemented
- `v1.88` implemented
- `v1.89` implemented
- `v1.90` implemented
- `v1.91` implemented

## Latest Closed Milestone

- `v1.94` `L4 Analytical Cross-Check Surface` implemented

## Current Active Milestone

- `v1.95` `L2 Promotion Pipeline Closure` — 3 phases, 2 completed

## Current Status

- `v1.36` through `v1.94` are closed and archived or ready for archive lookup
- `v1.95` is active with 3 phases (169, 169.1, 169.2)
- next command boundary: `$gsd-execute-phase 169.2`
