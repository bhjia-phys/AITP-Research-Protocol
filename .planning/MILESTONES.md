# Milestones

## v2.9 Promotion-Review Gate Closure (Active)

**Phases completed:** 0 / 3 phases, 0 / 3 plans

**Milestone goal:**

- make the selected `l2_promotion_review` route materialize one explicit
  promotion-review gate instead of leaving the topic on the summary placeholder

- keep `next`, `status`, and dashboard surfaces aligned on that explicit gate

- close with one replayable fresh-topic proof that the same topic can advance
  beyond promotion-review summary into the explicit gate

**Key accomplishments:**

- milestone scoped from the remaining operator-visible gap after `v2.8`: the
  same fresh topic can already reach `l2_promotion_review`, but the loop still
  cannot materialize the explicit promotion-review gate from that route
- Phase `183` is planned to materialize one explicit promotion-review gate
- Phase `183.1` is planned to advance public surfaces onto that gate
- Phase `183.2` is planned to close the milestone with one replayable
  sixth-continue packet

---

## v2.8 Selected-Candidate Route Choice Closure (Shipped: 2026-04-14)

**Phases completed:** 3 / 3 phases, 3 / 3 plans

**Milestone goal:**

- make the selected staged-candidate route derive one bounded deeper route
  instead of leaving the topic on the candidate-summary placeholder

- keep `next`, `status`, and dashboard surfaces aligned on that first deeper
  route choice

- close with one replayable fresh-topic proof that the same topic can advance
  beyond selected-candidate summary into the first deeper route choice

**Key accomplishments:**

- milestone scoped from the remaining operator-visible gap after `v2.7`: the
  same fresh topic can already reach one selected staged candidate, but the
  loop still could not derive the first deeper route choice from it
- Phase `182` now derives and persists one bounded route choice from the
  selected staged candidate
- Phase `182.1` now advances public surfaces onto that chosen route
- Phase `182.2` now closes the milestone with one replayable fresh-topic
  route-choice packet

---

## v2.7 Consultation-Followup Selection Closure (Shipped: 2026-04-14)

**Phases completed:** 3 / 3 phases, 3 / 3 plans

**Milestone goal:**

- make the post-review consultation route executable instead of leaving it as a
  visible-but-non-executable next action

- keep `next`, `status`, and dashboard surfaces aligned on one selected
  topic-local staged candidate after that consultation lands

- close with one replayable fresh-topic proof that the same topic can execute
  consultation-followup and advance onto candidate-specific follow-up

**Key accomplishments:**

- milestone scoped from the remaining operator-visible gap after `v2.6`: the
  route could already surface `consultation_followup`, but the loop still could
  not execute it
- Phase `181` now executes `consultation_followup` and writes durable
  consultation / selection artifacts
- Phase `181.1` now advances queue materialization and public surfaces onto the
  selected staged candidate
- Phase `181.2` now closes the milestone with one replayable fresh-topic
  consultation-followup selection packet

---

## v2.6 Staged-L2 Post-Review Advancement (Shipped: 2026-04-14)

**Phases completed:** 3 / 3 phases, 3 / 3 plans

**Milestone goal:**

- make a later benign `continue` stop leaving the same fresh topic on the
  static staged-`L2` review summary forever

- keep `next`, `status`, and dashboard surfaces aligned on one bounded
  post-review consultation step against topic-local staged `L2` memory

- close with one replayable fresh-topic proof that the same topic can advance
  beyond staged-`L2` review after that later `continue`

**Key accomplishments:**

- milestone scoped from the remaining operator-visible gap after `v2.5`: a
  later benign `continue` could still leave the topic on
  `Inspect the current L2 staging manifest before continuing.`
- Phase `180` now advances queue materialization onto one bounded
  topic-local staged-memory consultation step
- Phase `180.1` now proves public `next` and `status` advance onto the same
  post-review route
- Phase `180.2` now closes the milestone with one replayable fresh-topic
  advancement packet beyond staged-L2 review

---

## v2.5 Staged-L2 Review Reentry Coherence (Shipped: 2026-04-14)

**Phases completed:** 3 / 3 phases, 3 / 3 plans

**Milestone goal:**

- make benign `continue` steering stop surfacing as blocking human-control
  state after the first fresh-topic staged-`L2` review point is reached

- keep `next`, `status`, and dashboard reentry surfaces focused on the staged-L2
  review workflow itself while neutral `continue` steering remains durable

- close with one replayable fresh-topic proof that the same topic can continue
  from staged-`L2` review under non-blocking `continue` steering

**Key accomplishments:**

- milestone scoped from the remaining operator-visible gap after `v2.4`: even
  a benign `continue` steering request could leave
  `h_plane.overall_status = active_human_control` after staged-L2 review
- Phase `179` now treats benign `continue_recorded` steering as visible but
  non-blocking
- Phase `179.1` now proves public `next` and `status` stay aligned on
  staged-L2 review under benign `continue` steering
- Phase `179.2` now closes the milestone with one replayable fresh-topic
  staged-L2 reentry packet

---

## v2.4 First L1 To L2 Follow-Through Coherence (Shipped: 2026-04-14)

**Phases completed:** 3 / 3 phases, 3 / 3 plans

**Milestone goal:**

- make the first fresh-topic `literature_intake_stage` stop repeating once the
  same candidate set has already landed in staged `L2`

- make post-follow-through `status`, `next`, and must-read surfaces advance
  onto staged-`L2` review instead of staying on the same first L1->L2 action

- close with one durable replay receipt for the bounded fresh-topic
  `register -> stage -> staging review` lane

**Key accomplishments:**

- milestone scoped from the remaining first-use gap after `v2.3`: the first
  post-registration L1->L2 follow-through executed, but the route did not yet
  recognize that completion durably
- Phase `178` now persists stable literature-stage identity and prevents the
  same fresh-topic candidate set from requeueing forever
- Phase `178` now advances the next bounded action onto staged-`L2` review and
  keeps that review inside the literature-focused context envelope
- Phase `178.1` now proves, on an isolated fresh-topic lane, that first-source
  registration can continue through one bounded `literature_intake_stage` and
  produce topic-local staged consultation hits
- Phase `178.2` now closes the milestone with one durable replay packet for
  the fresh-topic `register -> stage -> staging review` baseline

---

## v2.3 Post-Registration Route Coherence (Shipped: 2026-04-14)

**Phases completed:** 3 / 3 phases, 3 / 3 plans

**Milestone goal:**

- make post-registration runtime state and layer-status fields reflect the
  presence of the first source honestly

- make `status`, `next`, runtime protocol, and dashboard surfaces stop pointing
  back to stale L0 source-handoff text once a first source already exists

- close with a replayable first-use proof of the post-registration route
  transition

**Key accomplishments:**

- milestone scoped from the remaining accepted open gap in `v2.2`: stale
  post-registration next-action wording after the first source already landed
- Phase `177` now aligns persisted runtime state with refreshed source-aware
  status surfaces after registration
- Phase `177.1` now reroutes the first post-registration action away from the
  stale bootstrap L0 handoff
- Phase `177.2` now proves the bounded post-registration route transition on a
  replayable first-use lane

---

## v2.2 Fresh-Topic First-Use Reliability (Shipped: 2026-04-14)

**Phases completed:** 3 / 3 phases, 3 / 3 plans

**Milestone goal:**

- make explicit fresh-topic natural-language `session-start` requests allocate
  new topics instead of reopening stale current-topic memory

- make first-source registration on Windows survive long real-topic slugs and
  keep `L0` status coherent immediately after registration

- close with a replayable fresh real-topic first-use proof from session-start
  through first source registration

**Key accomplishments:**

- milestone scoped from the real measurement-induced / observer-algebra run
  that exposed front-door misrouting and first-use Windows friction after the
  `v2.1` `L2` hardening slice
- Phase `176` now makes bounded "from scratch" fresh-topic requests allocate a
  new topic instead of reopening stale current-topic memory
- Phase `176.1` now shortens first-source registration paths and refreshes
  runtime/status surfaces immediately after registration
- Phase `176.2` now proves the bounded first-use lane mechanically from fresh
  bootstrap through registration and immediate post-registration status replay

---

## v2.1 L2 Real-Topic Relevance Hardening (Shipped: 2026-04-14)

**Phases completed:** 3 / 3 phases, 3 / 3 plans

**Milestone goal:**

- harden fresh-topic `L2` staging so reusable knowledge rows carry clean
  content and correct source provenance

- improve consultation ranking so fresh real-topic local relevance can beat
  unrelated canonical carryover when the query clearly targets the new topic

- close with a replayable multi-paper acceptance proof for provenance and
  retrieval ordering

**Key accomplishments:**

- Phase `175` now suppresses obvious staging noise and preserves true per-entry
  source provenance on the literature fast path
- Phase `175.1` now lets explicit topic-local staged rows compete on the
  primary consultation surface instead of hiding only in secondary staged hits
- Phase `175.2` now proves, on a replayable multi-paper fresh-topic lane, that
  two distinct paper sources survive staging and the local staged bridge note
  outranks unrelated canonical carryover on the primary consultation surface

---

## v2.0 Three-Lane Real-Topic Natural-Language E2E (Shipped: 2026-04-14)

**Phases completed:** 3 / 3 phases, 3 / 3 plans

**Milestone goal:**

- run real natural-language dialogue tests against the closed formal-theory,
  toy-model, and first-principles baselines

- prove the public AITP front door can steer each lane honestly without hidden
  seed state

- close with a cross-lane comparative report of success boundaries, remaining
  blockers, and next widening decisions

**Key accomplishments:**

- the formal-theory baseline now has one real natural-language dialogue proof
  that preserves the Jones / von Neumann request through runtime steering
  artifacts

- the toy-model baseline now has one real natural-language dialogue proof that
  preserves the HS-like chaos-window request while landing the same bounded
  authoritative-L2 claim

- the first-principles baseline now has one real natural-language dialogue
  proof that preserves the bounded LibRPA QSGW request while landing the same
  authoritative-L2 claim

- one honest cross-lane report now compares the three dialogue-proof lanes and
  leaves their remaining widening blockers explicit

---

## v1.99 LibRPA QSGW Positive L0 To L2 Closure (Shipped: 2026-04-14)

**Phases completed:** 3 / 3 phases, 3 / 3 plans

**Milestone goal:**

- ingest one bounded `LibRPA QSGW` first-principles / code-method lane as
  first-class AITP knowledge

- choose one honest positive QSGW workflow or algorithmic target with an
  explicit benchmark, convergence, or trust contract

- land one authoritative `LibRPA QSGW` unit in canonical `L2`
- close with replay receipts and explicit three-lane convergence notes for the
  formal, toy-model, and first-principles baselines

**Key accomplishments:**

- one bounded `LibRPA QSGW` code-method / first-principles target now has an
  explicit codebase/workflow trust contract on a fresh public-front-door topic

- that bounded `LibRPA QSGW` positive target now lands in authoritative
  canonical `L2` as
  `claim:librpa-qsgw-deterministic-reduction-consistency-core`

- the formal-theory, toy-model, and first-principles directions now each have
  a bounded positive authoritative-L2 baseline

---

## v1.98 Toy Model Positive L0 To L2 Closure (Shipped: 2026-04-14)

**Phases completed:** 3 / 3 phases, 3 / 3 plans

**Milestone goal:**

- land one bounded positive `HS model` unit in canonical `L2`
- close the positive toy-model lane with an explicit benchmark or convergence
  contract before promotion

- prove honest coexistence between the new positive `HS model` route and the
  existing HS negative-result route

- keep the deferred `LibRPA QSGW` first-principles lane explicit but out of
  scope for this bounded step

**Key accomplishments:**

- one bounded HS-like toy-model target now has an explicit benchmark-backed
  target contract on a fresh public-front-door topic shell

- that bounded HS-like positive target now lands in authoritative canonical
  `L2` as `claim:hs-like-chaos-window-finite-size-core`

- the authoritative HS positive claim and the shipped HS negative-result route
  now coexist honestly on the same compiled and consultation surfaces

- explicit carry-over notes now isolate the deferred `LibRPA QSGW`
  first-principles / code-method lane as the next bounded widening target

---

## v1.97 First Positive L0 To L2 Closure (Shipped: 2026-04-14)

**Phases completed:** 3 / 3 phases, 3 / 3 plans

**Milestone goal:**

- land one fresh positive authoritative unit in canonical `L2` through the
  public AITP route

- harden compiled L2 and consultation surfaces around real
  positive/negative coexistence

- close with replayable evidence and explicit blocker routing for the deferred
  `toy_model` and `first_principles` lanes

**Key accomplishments:**

- one fresh formal-theory topic now lands a bounded theorem in authoritative
  canonical `L2`

- repo-local compiled reports and `consult-l2` now agree on that positive
  authoritative landing

- authoritative positive rows and staged `contradiction_watch` rows now
  coexist on the same compiled and consultation surfaces without authority
  drift

- replay receipts and deferred lane routing now exist for the user-requested
  `HS model` and `LibRPA QSGW` widening work

---

## v1.96 Real Topic Promotion E2E Proof (Shipped: 2026-04-14)

**Phases completed:** 3 / 3 phases, 3 / 3 plans

**Milestone goal:**

- prove one real-topic positive promotion from the public front door into
  canonical `L2`

- prove one honest `negative_result` promotion into canonical `L2`
- close both lanes with durable replay and postmortem evidence

**Key accomplishments:**

- three fresh public-front-door topics now have durable bootstrap receipts
  across `formal_derivation`, `toy_model`, and `first_principles`

- the HS-model OTOC failure now lands durably as `negative_result` staging and
  compiles as `contradiction_watch`

- all four proof lanes now have receipts, runbooks, and a cross-lane
  postmortem

- the milestone closed honestly without pretending any positive lane had yet
  reached authoritative canonical `L2`

---

## v1.95 L2 Promotion Pipeline Closure (Shipped: 2026-04-14)

**Phases completed:** 3 / 3 phases, 3 / 3 plans

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

- the human front door now has tiered `status`, a zero-config `hello`, and a
  durable post-bootstrap next-action hint

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

- `v2.8` `Selected-Candidate Route Choice Closure` shipped

## Current Active Milestone

- `v2.9` `Promotion-Review Gate Closure`

## Current Status

- `v1.36` through `v2.8` are closed and archived or ready for archive lookup
- active work has moved into milestone `v2.9`
- next command boundary: execute Phase `183` for promotion-review gate closure
