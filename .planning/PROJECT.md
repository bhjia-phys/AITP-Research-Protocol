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
- `v1.65`
- `v1.66`
- `v1.67`
- `v1.68`
- `v1.69`
- `v1.70`
- `v1.71`
- `v1.72`
- `v1.73`
- `v1.74`
- `v1.75`
- `v1.76`
- `v1.77`
- `v1.78`
- `v1.79`
- `v1.80`
- `v1.81`
- `v1.82`
- `v1.83`
- `v1.84`
- `v1.85`
- `v1.86`
- `v1.87`
- `v1.88`
- `v1.89`
- `v1.90`
- `v1.91`
- `v1.92`
- `v1.93`
- `v1.94`
- `v1.95`
- `v1.96`
- `v1.97`
- `v1.98`
- `v1.99`
- `v2.0`
- `v2.1`
- `v2.2`
- `v2.3`
- `v2.4`
- `v2.5`
- `v2.6`
- `v2.7`
- `v2.8`

That closes the current bounded chain through the first three-lane real-topic
natural-language dialogue proof across formal, toy-model, and
first-principles routes plus fresh-topic `L2` hardening and first-use
reliability passes, but it still does **not** mean the broader AITP
architecture is finished.

## Current Focus

- Active milestone: `v2.9` `Promotion-Review Gate Closure`
- Latest closed milestone: `v2.8` `Selected-Candidate Route Choice Closure`
- Next boundary: materialize one explicit promotion-review gate from the chosen
  route

## Current Milestone: v2.9 Promotion-Review Gate Closure

**Goal:** make post-route continuation trustworthy enough that, once
`l2_promotion_review` becomes the selected route on a fresh topic, the loop
materializes one explicit promotion-review gate instead of stalling on the
summary placeholder.

**Target features:**
- materialize one explicit promotion-review gate from the selected staged
  candidate once `l2_promotion_review` becomes the selected route
- keep public `next`, `status`, and dashboard surfaces aligned on that gate
  instead of the summary placeholder
- close with one replayable fresh-topic proof that the same topic advances from
  promotion-review summary onto the explicit gate

**Key context:**
- `v2.8` closed selected-candidate route choice, so the same topic can already
  reach `l2_promotion_review` honestly on the bounded baseline
- a follow-up probe still showed that the loop cannot materialize the explicit
  promotion-review gate once that route becomes selected
- the next bottleneck is therefore promotion-review gate materialization, not
  earlier consultation or route-choice closure work

## Latest Closed Milestone: v2.8 Selected-Candidate Route Choice Closure

**Goal:** make post-selection continuation trustworthy enough that, once a
selected staged candidate becomes the selected route on a fresh topic, the loop
derives one bounded deeper route choice instead of stalling on the
candidate-summary placeholder.

**Delivered features:**
- the bounded loop now derives one first deeper route choice from the selected
  staged candidate
- that route choice now writes durable
  `selected_candidate_route_choice.active.json|md`
- public `next` / `status` now advance from selected-candidate summary onto
  `l2_promotion_review`
- one replayable fresh-topic proof now closes that post-selection route-choice
  baseline

**Key context:**
- `v2.7` had already closed consultation-followup execution and candidate
  selection
- `v2.8` closed the remaining route-choice gap without pretending that the
  selected promotion-review route itself was already executable

## Previous Closed Milestone: v2.7 Consultation-Followup Selection Closure

**Goal:** make post-review consultation trustworthy enough that, once
`consultation_followup` becomes the selected route on a fresh topic, the loop
can execute that consultation, write a durable selection artifact, and advance
to one selected topic-local staged candidate instead of stalling on generic
consult language.

**Delivered features:**
- the bounded loop now executes one topic-local `consult-l2` step once the
  consultation-followup route is surfaced and the operator continues again
- that consultation step now writes durable consultation and selection artifacts
- queue materialization and public `next` / `status` now advance onto one
  selected topic-local staged candidate
- one replayable fresh-topic proof now closes that consultation-followup
  selection baseline

**Key context:**
- `v2.6` had already closed the first post-review consultation surface
- `v2.7` closed the remaining consultation-followup execution and
  candidate-selection gap without pretending that route choice after selection
  was already solved

## Previous Closed Milestone: v2.6 Staged-L2 Post-Review Advancement

**Goal:** make post-review continuation trustworthy enough that, once staged-`L2`
review is already visible on a fresh topic, a later benign `continue`
advances to one bounded topic-local staged-memory consultation step instead of
stalling on the same review summary forever.

**Delivered features:**
- queue materialization now advances beyond static staged-L2 review once a
  later `continue` decision arrives
- public `next`, `status`, and dashboard surfaces now align on the bounded
  post-review consultation step
- one replayable fresh-topic proof now shows the same topic advancing beyond
  staged-L2 review into that bounded consultation route

**Key context:**
- `v2.5` had already closed staged-L2 reentry posture coherence
- `v2.6` closed the remaining post-review route-advancement gap without
  pretending that consultation-followup execution or candidate selection were
  already solved

## Previous Closed Milestone: v2.5 Staged-L2 Review Reentry Coherence

**Goal:** make staged-`L2` review reentry trustworthy enough that, after the
first fresh-topic L1->L2 follow-through lands, benign `continue` steering no
longer leaves the topic in a misleading human-control posture and public
surfaces stay focused on the review workflow itself.

**Delivered features:**
- benign `continue_recorded` steering no longer promotes the topic into false
  blocking human-control posture
- public `next`, `status`, and dashboard surfaces stay aligned on staged-L2
  review under that benign reentry steering
- one replayable fresh-topic proof now shows the same topic can reenter from
  staged-L2 review under non-blocking `continue` steering

**Key context:**
- `v2.4` had already closed the first fresh-topic L1->L2 follow-through and
  advanced onto staged-L2 review
- `v2.5` closed the remaining same-topic reentry posture gap without
  pretending that later post-review advancement was already solved

## Previous Closed Milestone: v2.4 First L1 To L2 Follow-Through Coherence

**Goal:** make the first post-registration L1->L2 follow-through trustworthy
enough that a fresh topic can execute one bounded `literature_intake_stage`,
stop repeating it once it lands, and advance onto staged-`L2` review instead
of looping forever on the same action.

**Delivered features:**
- literature-intake candidate sets now persist a stable completion identity so
  the same fresh-topic stage no longer requeues forever
- post-follow-through route surfaces now advance onto staged-`L2` review and
  keep the literature-focused context envelope active
- one isolated fresh-topic proof now shows `register -> stage -> staged-L2
  review`, and `consult_l2(include_staging=True)` returns the topic-local
  staged row
- one durable replay packet now records that bounded baseline under `.planning/`

**Key context:**
- `v2.3` closed post-registration route selection, but not the first L1->L2
  follow-through after that route became available
- `v2.4` closed that first fresh-topic follow-through baseline without
  pretending that later reentry and continuation surfaces were already solved

## Previous Closed Milestone: v2.3 Post-Registration Route Coherence

**Goal:** make the first post-registration transition trustworthy enough that,
once a first source lands, runtime state and next-action surfaces move onto the
right bounded follow-up step instead of repeating the old L0 source handoff.

**Delivered features:**
- runtime `topic_state` / `layer_status` source fields now refresh after first
  registration instead of carrying stale zero-source state
- post-registration route selection now moves off the raw source-registration
  handoff text onto the next bounded research step
- one replayable fresh first-use proof package now shows that
  post-registration transition mechanically

**Key context:**
- `v2.2` closed fresh-topic entry and first-source registration reliability
- `v2.3` closed the remaining immediate post-registration planner coherence
  gap without pretending that the first L1->L2 follow-through was already
  solved

## Previous Closed Milestone: v2.2 Fresh-Topic First-Use Reliability

**Goal:** make fresh-topic public entry reliable enough that a real new topic
can be opened from natural language, register its first source on Windows
without path failure, and surface honest `L0` status immediately after
first-use actions.

**Delivered features:**
- explicit fresh-topic natural-language requests now allocate new topics
  instead of reopening stale current-topic memory
- first-source registration now uses Windows-safe short source-directory slugs
- runtime/status surfaces now refresh immediately after first-source
  registration
- one replayable first-use proof package now shows the route mechanically

**Key context:**
- `v2.1` had already closed the bounded fresh-topic `L2` hardening slice
- `v2.2` closed the remaining entry and registration reliability blockers
  without pretending that post-registration route selection or broader
  scientific widening were already solved

## Previous Closed Milestone: v2.1 L2 Real-Topic Relevance Hardening

**Goal:** make fresh real-topic `L2` staging and consultation trustworthy
enough that new literature-intake topics surface the right local knowledge
with correct provenance instead of noisy or irrelevant hits.

**Delivered features:**
- suppression of obvious staging noise such as generic notation tokens and weak
  `unspecified_method` rows
- preservation of true per-entry source provenance across fresh-topic
  multi-paper staging
- topic-local staged rows can now outrank unrelated canonical carryover on the
  primary consultation surface for the bounded fresh-topic case
- one replayable multi-paper real-topic proof package now shows the hardening
  slice mechanically

**Key context:**
- `v2.0` had already shown the three closed lanes can be entered through real
  dialogue, but a fresh measurement-induced topic exposed `L2` quality gaps on
  the literature fast path
- `v2.1` closes those bounded `L2` gaps without pretending the broader
  first-use or scientific-widening problems are already solved

## Previous Closed Milestone: v2.0 Three-Lane Real-Topic Natural-Language E2E

**Goal:** prove that the public AITP front door can steer all three closed
research directions through real natural-language dialogue without hidden seed
artifacts or authority drift.

**Delivered features:**
- one real natural-language dialogue proof for the formal-theory baseline
- one real natural-language dialogue proof for the toy-model baseline
- one real natural-language dialogue proof for the first-principles /
  code-method baseline
- one cross-lane comparative report of where the front door is truly ready and
  where bounded blockers remain

**Key context:**
- `v1.97` closed the first trustworthy formal-theory positive-L2 baseline
- `v1.98` closed the bounded HS toy-model positive-L2 baseline
- `v1.99` closed the bounded `LibRPA QSGW` first-principles / code-method
  positive-L2 baseline
- `v2.0` closes the first honest real-dialogue proof across all three
  user-requested research directions
- the next frontier is not another baseline closure; it is deciding which
  widening blocker to attack next

## Previous Closed Milestone: v1.99 LibRPA QSGW Positive L0 To L2 Closure

**Goal:** carry one bounded `LibRPA QSGW` first-principles / code-method
result from the public AITP front door into authoritative canonical `L2`, then
turn the three requested research directions into an explicit convergence
baseline.

**Target features:**
- one fresh `first_principles` topic is narrowed to one bounded positive
  `LibRPA QSGW` target with explicit codebase/workflow anchors
- one benchmark, convergence, or code-method trust contract proves that target
  is honest enough for promotion
- one authoritative positive `LibRPA QSGW` unit lands in canonical `L2`
- replay receipts and routing notes make the formal, toy-model, and
  first-principles baselines ready for broader real-topic natural-language
  tests

**Key context:**
- `v1.97` closed the first trustworthy formal-theory positive-L2 baseline
- `v1.98` closed the bounded HS toy-model positive-L2 baseline and its honest
  coexistence with the shipped HS negative-result route
- `v1.99` closed the remaining bounded `LibRPA QSGW`
  first-principles / code-method positive-L2 lane

## Previous Closed Milestone: v1.98 Toy Model Positive L0 To L2 Closure

**Goal:** carry one bounded positive `HS model` toy-model result from the
public AITP front door into authoritative canonical `L2`, then prove it can
coexist honestly with the already-shipped HS negative-result route.

**Target features:**
- one bounded positive `HS model` target is chosen honestly and kept distinct
  from the already-proven negative OTOC mismatch route
- one convergence / benchmark contract proves that target is numerically or
  theoretically trustworthy enough for promotion
- one authoritative positive toy-model unit lands in canonical `L2`
- compiled L2 and `consult-l2` expose that positive unit while keeping the
  existing HS negative-result route explicit

**Phase-level status:** all three roadmap phases are complete and the milestone
is archived.

**Key context:**
- `v1.97` closed the first trustworthy formal-theory positive-L2 baseline
- `v1.98` closed the bounded HS toy-model positive-L2 baseline and its honest
  coexistence with the shipped HS negative-result route
- `v1.99` should close the remaining `LibRPA QSGW`
  first-principles / code-method lane before broad three-lane real-topic
  natural-language testing

## Previous Closed Milestone: v1.97 First Positive L0 To L2 Closure

**Goal:** land one fresh positive authoritative unit in canonical `L2` through
the public AITP route, then make the surrounding L2 surfaces trustworthy enough
to serve as the baseline for later multi-mode closure.

**Delivered features:**
- one fresh `formal_derivation` topic now reaches authoritative canonical `L2`
  instead of stopping at `L3`
- compiled L2 and consultation surfaces expose the same promoted unit and
  authority state
- one replayable acceptance lane now proves the full positive route
  mechanically
- explicit carry-over blockers are now written for `toy_model` and
  `first_principles`

**Explicitly deferred from this milestone:**
- one positive `HS model` toy-model lane still needs a bounded positive target
  and convergence/benchmark contract before authoritative `L2` promotion
- one positive `LibRPA QSGW` first-principles lane still needs a durable
  `first_principles -> code_method` mapping and bounded positive target
- the next widening milestone should start from the now-closed formal-theory L2
  baseline instead of reopening the Jones lane

## Previous Closed Milestone: v1.96 Real Topic Promotion E2E Proof

**Goal:** prove the public front door and repaired promotion route on real
topics, including one honest negative-result lane.

**Delivered features:**
- three fresh public-front-door topics now have durable bootstrap receipts
  across `formal_derivation`, `toy_model`, and `first_principles`
- one HS-model failure now lands durably as `negative_result` staging and
  compiles as `contradiction_watch`
- all four proof lanes now have receipts, runbooks, and a cross-lane
  postmortem

**Explicitly deferred from this milestone:**
- one full positive `L0 -> L2` promotion proof
- positive promotion receipt parity across runtime/read-path surfaces
- `first_principles -> code_method` mapping on a real codebase-backed lane
- toy-model convergence or benchmark acceptance beyond bootstrap

## Previous Closed Milestone: v1.95 L2 Promotion Pipeline Closure

**Goal:** Close the L4→L2 promotion pipeline gap so E2E research runs that
already validate at `L4` can actually land their results in canonical `L2`
knowledge.

**Target features:**
- extend canonical schema so `negative_result` and runtime proof artifacts have
  a real promotion path
- wire promotion support modules to load runtime schema context and bridge
  runtime proof artifacts into canonical `L2` units
- make the next E2E run easier to operate through bounded status, hello, and
  next-action guidance improvements

**Key context:**
- two Jones E2E runs already reached `L4`; the blocker is promotion
  engineering, not scientific validation
- root causes are missing canonical enum coverage, missing formal runtime proof
  schemas, and missing bridge wiring in promotion helpers
- keep this milestone bounded to pipeline closure and minimal operator
  ergonomics rather than reopening already-shipped analytical surfaces

## Previous Closed Milestone: v1.94 L4 Analytical Cross-Check Surface

**Goal:** Close the broader post-`v1.47` analytical-validation remainder by
making bounded analytical checks explicit, durable, and visible on the runtime
read path.

**Target features:**
- analytical check rows for limiting-case, dimensional, symmetry,
  self-consistency, and source-cross-reference validation
- richer analytical review context including source anchors and regime or
  assumption basis
- analytical cross-check parity across runtime-facing read surfaces
- one bounded analytical proof lane

**Key context:**
- `v1.47` already shipped analytical review as a first-class production mode
- `v1.93` made contradiction visibility explicit, which naturally raises the bar
  for what analytical validation should surface next
- this milestone stays focused on bounded analytical cross-check visibility, not
  on symbolic algebra or automatic route mutation

## Previous Closed Milestone: v1.93 L1 Contradiction Adjudication Surface

**Goal:** Close the broader post-`v1.70` contradiction-adjudication remainder
by making incompatible source claims explicit inside `L1` intake and exposing
that contradiction surface on the runtime read path.

**Delivered features:**
- richer contradiction rows with bounded comparison basis and side-specific
  summaries
- contradiction parity across `status`, `runtime_protocol`, dashboard, and `L1`
  vault source-intake
- one dedicated bounded contradiction-aware proof lane

**Explicitly deferred from this milestone:**
- full scientific adjudication of which source is correct
- automatic queue-level contradiction rerouting
- broader analytical validation beyond contradiction visibility

## Previous Closed Milestone: v1.92 Public Front Door Source Handoff

**Goal:** Close the next post-`v1.91` usability gap by turning the honest
public-front-door return to `L0` into one concrete source-acquisition handoff
and making the default arXiv registration path contentful enough to be useful
immediately.

**Delivered features:**
- one concrete `L0` source-acquisition next step after a fresh public
  `bootstrap`
- matching `status`, `runtime_protocol`, and `replay-topic` source-handoff
  surfaces
- contentful-by-default arXiv registration with explicit `--metadata-only`
  opt-out
- one bounded fresh-topic proof of
  `bootstrap -> concrete source handoff -> source registration`

**Explicitly deferred from this milestone:**
- broader `L0` discovery/provider expansion beyond the shipped arXiv-first
  entry surfaces
- automatic source acquisition or any fake progress when a topic still lacks
  sources
- broader HCI, recovery, and collaboration backlog items outside this bounded
  milestone

## Previous Closed Milestone: v1.91 Real Topic L0 To L2 End-To-End Validation

**Goal:** Close the next post-`v1.90` maturity gap by proving whether the
current AITP implementation is genuinely useful on a real topic from an
initial idea through one honest bounded research outcome.

**Target features:**
- one real-topic run from an initial idea through the current public AITP
  entry surfaces
- one durable postmortem naming the actual route, friction, and bounded outcome
- one explicit issue ledger that turns discovered problems into GSD-tracked
  follow-up work

Current phase status inside `v1.91`:

- Phases `165` through `165.6` are now implemented, audited, and ready for
  archive

**Explicitly deferred from this milestone:**
- multi-user feedback collection beyond the first primary operator run
- broad cross-runtime parity closure beyond the runtime used for the first
  real-topic run
- whole-topic statement-compilation or formalization claims before the real
  run says they are needed
- more concrete `L0` source-acquisition guidance after public bootstrap
- broader proof-engineering memory distillation beyond the first Jones seed

## Previous Closed Milestone: v1.90 Hypothesis Route Transition Authority Surface

**Goal:** Close the next post-`v1.89` research-control gap by turning
transition commitment into one explicit authority surface instead of leaving
operators to infer whether a committed route has become the authoritative
bounded truth across runtime surfaces.

**Target features:**
- one explicit route transition-authority surface derived from route
  transition commitment plus current route artifacts
- one runtime/read path that shows whether a committed route has become the
  authoritative bounded truth across current-topic surfaces
- one bounded isolated acceptance lane proving route transition-authority
  visibility without fresh runtime mutation

Current phase status inside `v1.90`:

- Phase `164` is now implemented, verified, milestone-audited, and archived

**Explicitly deferred from this milestone:**
- real-topic end-to-end utility validation beyond local protocol closure
- fresh runtime mutation after authority becomes explicit
- automatic branch spawning or branch scheduling across many hypotheses

## Previous Closed Milestone: v1.77 Hypothesis Route Handoff Surface

**Goal:** Close the next post-`v1.76` research-control gap by turning ready
parked-route signals into an operator-visible route handoff surface instead of
leaving the next concrete route handoff split across activation, re-entry, and
helper artifacts.

**Target features:**
- one explicit route handoff surface derived from the current local route plus
  ready parked-route signals
- one runtime/read path that shows which ready parked route is the next
  concrete handoff candidate and which should remain parked
- one bounded isolated acceptance lane proving route handoff visibility without
  automatic route mutation

Current phase status inside `v1.77`:

- Phase `151` is now implemented, verified, milestone-audited, and archived

**Explicitly deferred from this milestone:**
- integrating the primary handoff candidate into one explicit current-route
  choice summary
- automatic branch spawning or branch scheduling across many hypotheses
- automatic candidate reactivation and parent-topic reintegration mutation

## Previous Closed Milestone: v1.76 Hypothesis Route Re-entry Surface

**Goal:** Close the next post-`v1.75` research-control gap by turning parked
route reactivation conditions and follow-up return contracts into an
operator-visible route re-entry surface instead of leaving route return
readiness split across deferred-buffer and child-topic artifacts.

**Target features:**
- one explicit route re-entry surface derived from deferred reactivation
  conditions and follow-up return metadata linked to parked hypotheses
- one runtime/read path that shows which parked routes are waiting,
  re-entry-ready, or awaiting child-topic return
- one bounded isolated acceptance lane proving route re-entry visibility
  without automatic route mutation or parent-topic patching

Current phase status inside `v1.76`:

- Phase `150` is now implemented, verified, milestone-audited, and archived

**Explicitly deferred from this milestone:**
- automatic candidate reactivation or follow-up reintegration mutation
- automatic branch spawning or branch scheduling across many hypotheses
- explicit handoff summaries beyond the bounded re-entry slice

## Previous Closed Milestone: v1.75 Hypothesis Route Activation Surface

**Goal:** Close the next post-`v1.74` research-control gap by turning explicit
hypothesis route metadata into an operator-visible route-activation surface
instead of inferring concrete local-route versus parked-route next steps from
separate runtime artifacts.

**Target features:**
- one explicit route-activation surface derived from the declared route of each
  competing hypothesis
- one runtime/read path that shows the concrete next-step activation of the
  active local route versus parked routes
- one bounded isolated acceptance lane proving route activation without
  automatic branch spawning or scheduling

Current phase status inside `v1.75`:

- Phase `149` is now implemented, verified, milestone-audited, and archived

**Explicitly deferred from this milestone:**
- automatic branch spawning or branch scheduling across many hypotheses
- automatic route adjudication heuristics beyond explicit activation summaries
- explicit parked-route re-entry summaries beyond the bounded activation slice

## Previous Closed Milestone: v1.74 Hypothesis Branch Routing Surface

**Goal:** Close the next post-`v1.73` research-control gap by making branch
intent explicit per competing hypothesis instead of reconstructing it from
separate deferred/follow-up runtime artifacts.

**Target features:**
- one explicit branch-routing surface on each active competing hypothesis
- one runtime/replay path that shows which hypothesis stays on the current
  topic, which routes to deferred parking, and which routes to a follow-up
  branch
- one bounded isolated acceptance lane proving hypothesis routing without
  hidden branch-execution heuristics

Current phase status inside `v1.74`:

- Phase `148` is now implemented, verified, and archived

**Explicitly deferred from this milestone:**
- automatic branch spawning or branch scheduling across many hypotheses
- hypothesis auto-adjudication heuristics beyond explicit declared routing
- reopening already-closed `v1.73` visibility work except for regressions

## Previous Closed Milestone: v1.73 Competing Hypotheses First-Class Surface

**Goal:** Close the research-question modeling gap so AITP can keep multiple
plausible bounded answers visible as first-class hypotheses instead of
flattening them into one main direction or burying them only in deferred
execution surfaces.

**Target features:**
- one explicit `competing_hypotheses` surface on the research-question
  contract
- one runtime/read path that keeps multiple live hypotheses visible without
  forcing them into separate hidden subtopics immediately
- one bounded isolated acceptance lane proving the multi-hypothesis surface on
  a temp kernel root

Current phase status inside `v1.73`:

- Phase `147` is now implemented, verified, milestone-audited, and archived

**Explicitly deferred from this milestone:**
- broader branch-management automation beyond the explicit question-level
  hypothesis surface
- hypothesis auto-discovery or adjudication heuristics that are not yet durable
- reopening already-closed transition-history or approval-record work

## Previous Closed Milestone: v1.72 Promotion Gate Human Modification Record

**Goal:** Close the next promotion-gate honesty gap by recording what the human
changed when approving an `L2` promotion, instead of only storing who approved
it.

**Closed features:**

- one explicit `human_modifications` record on approval
- one promotion-gate / replay surface that distinguishes modified from
  unchanged approvals
- one bounded isolated acceptance lane for modified approval
- one direct evaluator-divergence signal without widening into full evaluator
  analytics

**Explicitly deferred from this milestone:**

- full competing-hypothesis modeling
- broader evaluator-divergence analytics beyond the approval-time modification
  record
- generalized human rewrite tracking outside the L2 approval gate

## Previous Closed Milestone: v1.71 Runtime Transition And Demotion History

**Goal:** Close the runtime-history gap so AITP can show how a topic moved
across layers, including bounded backtracks and demotions, instead of only
showing the latest `resume_stage` plus `last_materialized_stage`.

**Closed features:**

- one structured runtime transition log with reasons and evidence refs
- one explicit demotion-history surface for backward layer moves
- one replay/read path that explains what got sent backward and why
- one bounded isolated acceptance lane for the new history surface

**Explicitly deferred from this milestone:**

- human modification capture inside the L2 approval gate
- full competing-hypothesis modeling
- broader evaluator-divergence analytics beyond the transition/demotion record

## Previous Closed Milestone: v1.70 L1 Source Assumptions And Reading Depth Closure

**Goal:** Close the still-open `999.27` intake-honesty remainder so AITP keeps
source-backed assumptions, reading-depth limits, and shallow/conflicting
evidence visible on the real `L1` operator path.

**Closed features:**

- one explicit assumption-and-reading-depth surface through the existing
  `l1_source_intake` path
- one honest view of skim-only, weak, or conflicting source evidence
- one bounded acceptance lane for the assumption/depth honesty slice
- one stronger isolated method-specificity acceptance path

**Explicitly deferred from this milestone:**

- broader contradiction adjudication workflow
- runtime transition/demotion history
- larger `L1` redesign beyond the immediate honesty slice

## Previous Closed Milestone: v1.69 L0 Source Discovery Via DeepXiv MCP Integration

**Goal:** Close the pre-registration discovery gap in `L0` so AITP can move
from idea or topic query to search, evaluate candidates, and then register
sources through one bounded discovery path.

**Closed features:**

- one search-first discovery surface before `register_arxiv_source.py`
- one explicit candidate-evaluation receipt before registration
- one bounded discovery acceptance lane on an isolated temp kernel root
- one fallback-aware bridge that keeps search external to `L0` core protocol

**Explicitly deferred from this milestone:**

- broader literature triage and larger provider expansion
- `L1` follow-on work around source-backed assumptions and reading depth
- embedding search into the `L0` core protocol as if it were no longer an
  external dependency

## Previous Closed Milestone: v1.68 Persistent Wiki-Style Knowledge Compilation

**Goal:** Move beyond retrieval-only `L2` helper views by compiling repeated
reading, discussion, and route-comparison outcomes into one durable linked
research-brain surface, while keeping authoritative `L2` writeback behind
existing `L4` promotion gates.

**Closed features:**

- one explicit compiled-knowledge contract and production report surface
- one bounded compiled-knowledge regression / acceptance lane
- one `L1` raw/wiki/output vault with explicit flowback on the topic-shell path
- one bounded statement-compilation pilot that separates declaration skeleton
  generation from proof repair

**Explicitly deferred from this milestone:**

- Layer 0 source discovery before registration
- broader graph-growth or multi-user validation
- whole-topic automated formalization claims

## Previous Closed Milestone: v1.67 Cross-Runtime Deep Execution Parity

**Goal:** Move Claude Code and OpenCode from install/front-door parity targets
to honest deep-execution parity probes against the Codex baseline, while
keeping OpenClaw deferred as a specialized lane.

**Target features:**
- one explicit artifact-level parity contract that distinguishes install
  readiness from deep-execution readiness
- one bounded real-topic acceptance route for Claude Code against the Codex
  baseline
- one bounded real-topic acceptance route for OpenCode against the Codex
  baseline
- one honest closure report that says where parity is reached and where a
  runtime still falls short

Current phase status inside `v1.67`:
- shared parity contract and Codex baseline harness landed in Phase `134`
- Claude Code bounded parity probe landed in Phase `135`
- OpenCode bounded parity probe landed in Phase `136`
- closure and cross-runtime audit landed in Phase `137`
- `v1.67` is now archived and milestone completion is finished

**Closed outcome:**

- one explicit artifact-level parity contract now distinguishes install
  readiness from deep-execution readiness
- one bounded Codex baseline plus bounded Claude/OpenCode probes now exist
- one shared closure report now names equivalent surfaces, degraded surfaces,
  and still-open gaps

**Known remaining gaps:**

- live Claude Code first-turn bootstrap consumption is still not directly
  proven
- live OpenCode first-turn bootstrap consumption is still not directly proven

**Explicitly deferred from this milestone:**
- reopening install/adoption work closed in `v1.65` and `v1.66`
- OpenClaw deep-parity expansion
- multi-user research-utility validation beyond runtime parity evidence

## Previous Closed Milestone: v1.66 PyPI Publishable Package

**Goal:** Replace repo-clone plus editable-install onboarding with a versioned
public `pip install aitp-kernel` path without regressing the already-shipped adoption
surface.

**Target features:**
- a public distribution contract that publishes under an actually available
  PyPI name instead of a repo-local editable-first surface
- a single semver and packaged runtime-asset contract that survives outside a
  git checkout
- newcomer docs and release workflow that make PyPI the default path while
  keeping editable install available for contributors
- one clean-install smoke path that proves the installed wheel can run outside
  the repository

**Closed features:**
- `aitp-kernel` as the real publishable package name while keeping `aitp` as
  the CLI
- one bounded distribution verification contract for wheel + sdist metadata and
  packaged runtime assets
- one isolated public-install smoke acceptance path for the installed runtime

**Explicitly deferred from this milestone:**
- reopening install/adoption hardening work already closed in `v1.65`
- OpenClaw parity or broader cross-runtime deep execution parity
- any repo split that is not directly required for shipping the public package

## Previous Closed Milestone: v1.65 Installation And Adoption Readiness

**Goal:** Make installation verification, first-run quickstart, and
Windows-native bootstrap behavior converge into one honest adoption surface for
Codex, Claude Code, and OpenCode.

**Closed features:**
- a machine-readable `aitp doctor` / remediation contract for the three
  front-door runtimes plus top-level convergence truth
- a shared `bootstrap -> loop -> status` quickstart with isolated acceptance
  coverage on a bounded real topic
- Windows-native bootstrap paths that do not assume bash or POSIX symlink
  habits for the default front-door experience

**Explicitly deferred from this milestone:**
- `999.48` PyPI publishable package
- OpenClaw deep parity beyond specialized-lane visibility

## Previous Closed Milestone: v1.64 L1 Method Specificity Surface

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
  Code, OpenClaw are still "parity targets" until the active milestone closes).
  `v1.67` closed the bounded parity-audit milestone, but the live app-turn
  parity gap remains intentionally visible.
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
- `.planning/milestones/v1.65-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.66-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.67-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.68-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.69-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.70-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.71-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.72-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.73-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.74-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.75-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.76-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.77-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.78-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.79-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.80-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.81-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.82-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.83-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.84-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.85-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.86-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.87-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.88-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.89-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.90-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.91-MILESTONE-AUDIT.md`

## Latest Integrated Regression Evidence

- `367 tests passed` on 2026-04-11
- `v1.77` route-handoff closure slices on 2026-04-12:
  - `python -m compileall research/knowledge-hub/knowledge_hub/runtime_read_path_support.py research/knowledge-hub/knowledge_hub/runtime_bundle_support.py research/knowledge-hub/knowledge_hub/topic_replay.py research/knowledge-hub/knowledge_hub/kernel_markdown_renderers.py research/knowledge-hub/runtime/scripts/run_hypothesis_route_handoff_acceptance.py research/knowledge-hub/tests/test_hypothesis_route_handoff_contracts.py research/knowledge-hub/tests/test_runtime_scripts.py research/knowledge-hub/tests/test_topic_replay.py research/knowledge-hub/tests/test_schema_contracts.py`
  - result: `compiled successfully`
  - `python research/knowledge-hub/runtime/scripts/run_hypothesis_route_handoff_acceptance.py --json`
  - result: `success`
  - `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "hypothesis_route_handoff_acceptance or hypothesis_route_reentry_acceptance" -q`
  - result: `2 passed`
  - `python -m pytest research/knowledge-hub/tests/test_hypothesis_route_handoff_contracts.py research/knowledge-hub/tests/test_hypothesis_route_reentry_contracts.py research/knowledge-hub/tests/test_hypothesis_route_activation_contracts.py research/knowledge-hub/tests/test_hypothesis_branch_routing_contracts.py research/knowledge-hub/tests/test_topic_replay.py research/knowledge-hub/tests/test_schema_contracts.py -q`
  - result: `17 passed`
  - `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "runtime_protocol_bundle_matches_public_schema or topic_status_and_prepare_verification_surface_new_shell_fields" -q`
  - result: `1 passed`
  - `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "projection_helpers_write_valid_outputs" -q`
  - result: `1 passed`
- `v1.76` route-reentry closure slices on 2026-04-12:
  - `python -m compileall research/knowledge-hub/knowledge_hub/runtime_read_path_support.py research/knowledge-hub/knowledge_hub/runtime_bundle_support.py research/knowledge-hub/knowledge_hub/topic_replay.py research/knowledge-hub/knowledge_hub/kernel_markdown_renderers.py research/knowledge-hub/runtime/scripts/run_hypothesis_route_reentry_acceptance.py research/knowledge-hub/tests/test_hypothesis_route_reentry_contracts.py research/knowledge-hub/tests/test_hypothesis_route_activation_contracts.py research/knowledge-hub/tests/test_hypothesis_branch_routing_contracts.py research/knowledge-hub/tests/test_runtime_scripts.py research/knowledge-hub/tests/test_topic_replay.py research/knowledge-hub/tests/test_schema_contracts.py`
  - result: `compiled successfully`
  - `python -m pytest research/knowledge-hub/tests/test_hypothesis_route_reentry_contracts.py research/knowledge-hub/tests/test_hypothesis_route_activation_contracts.py research/knowledge-hub/tests/test_hypothesis_branch_routing_contracts.py research/knowledge-hub/tests/test_topic_replay.py research/knowledge-hub/tests/test_schema_contracts.py -q`
  - result: `16 passed`
  - `python research/knowledge-hub/runtime/scripts/run_hypothesis_route_reentry_acceptance.py --json`
  - result: `success`
  - `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "hypothesis_route_reentry_acceptance or hypothesis_route_activation_acceptance" -q`
  - result: `2 passed`
  - `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "runtime_protocol_bundle_matches_public_schema or topic_status_and_prepare_verification_surface_new_shell_fields" -q`
  - result: `1 passed`
  - `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "projection_helpers_write_valid_outputs" -q`
  - result: `1 passed`
- `v1.75` route-activation closure slices on 2026-04-12:
  - `python -m compileall research/knowledge-hub/knowledge_hub/runtime_read_path_support.py research/knowledge-hub/knowledge_hub/topic_replay.py research/knowledge-hub/runtime/scripts/run_hypothesis_route_activation_acceptance.py research/knowledge-hub/tests/test_runtime_scripts.py research/knowledge-hub/tests/test_topic_replay.py research/knowledge-hub/tests/test_hypothesis_route_activation_contracts.py`
  - result: `compiled successfully`
  - `python research/knowledge-hub/runtime/scripts/run_hypothesis_route_activation_acceptance.py --json`
  - result: `success`
  - `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "hypothesis_route_activation_acceptance" -q`
  - result: `1 passed`
  - `python -m pytest research/knowledge-hub/tests/test_topic_replay.py research/knowledge-hub/tests/test_hypothesis_route_activation_contracts.py research/knowledge-hub/tests/test_hypothesis_branch_routing_contracts.py research/knowledge-hub/tests/test_schema_contracts.py -q`
  - result: `15 passed`
  - `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "runtime_protocol_bundle_matches_public_schema or topic_status_and_prepare_verification_surface_new_shell_fields" -q`
  - result: `1 passed`
  - `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "projection_helpers_write_valid_outputs" -q`
  - result: `1 passed`
- `v1.74` hypothesis-branch-routing closure slices on 2026-04-12:
  - `python -m pytest research/knowledge-hub/tests/test_hypothesis_branch_routing_contracts.py -q`
  - result: `2 passed`
  - `python -m pytest research/knowledge-hub/tests/test_schema_contracts.py -q`
  - result: `10 passed`
  - `python -m pytest research/knowledge-hub/tests/test_topic_replay.py -q`
  - result: `2 passed`
  - `python research/knowledge-hub/runtime/scripts/run_hypothesis_branch_routing_acceptance.py --json`
  - result: `success`
  - `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "hypothesis_branch_routing_acceptance" -q`
  - result: `1 passed`
  - `python -m pytest research/knowledge-hub/tests/test_competing_hypotheses_contracts.py -q`
  - result: `2 passed`
  - `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "runtime_protocol_bundle_matches_public_schema or topic_status_and_prepare_verification_surface_new_shell_fields" -q`
  - result: `1 passed`
  - `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "projection_helpers_write_valid_outputs" -q`
  - result: `1 passed`
- `v1.73` competing-hypotheses closure slices on 2026-04-12:
  - `python -m pytest research/knowledge-hub/tests/test_competing_hypotheses_contracts.py -q`
  - result: `2 passed`
  - `python -m pytest research/knowledge-hub/tests/test_schema_contracts.py -q`
  - result: `10 passed`
  - `python -m pytest research/knowledge-hub/tests/test_topic_replay.py -q`
  - result: `2 passed`
  - `python research/knowledge-hub/runtime/scripts/run_competing_hypotheses_acceptance.py --json`
  - result: `success`
  - `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "competing_hypotheses_acceptance" -q`
  - result: `1 passed`
  - `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "projection_helpers_write_valid_outputs" -q`
  - result: `1 passed`
  - `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "runtime_protocol_bundle_matches_public_schema or topic_status_and_prepare_verification_surface_new_shell_fields" -q`
  - result: `1 passed`
- `v1.71` transition-history closure slices on 2026-04-12:
  - `python -m pytest research/knowledge-hub/tests/test_transition_history_contracts.py -q`
  - result: `2 passed`
  - `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "projection_helpers_write_valid_outputs" -q`
  - result: `1 passed`
  - `python -m pytest research/knowledge-hub/tests/test_topic_replay.py -q`
  - result: `2 passed`
  - `python research/knowledge-hub/runtime/scripts/run_transition_history_acceptance.py --json`
  - result: `success`
  - `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "transition_history_acceptance" -q`
  - result: `1 passed`
- `v1.70` assumption/depth closure slices on 2026-04-12:
  - `python -m pytest research/knowledge-hub/tests/test_l1_assumption_depth_contracts.py -q`
  - result: `2 passed`
  - `python research/knowledge-hub/runtime/scripts/run_l1_assumption_depth_acceptance.py --json`
  - result: `success`
  - `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "l1_assumption_depth_acceptance" -q`
  - result: `1 passed, 29 deselected`
  - `python -m pytest research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_source_backed_l1_intake -q`
  - result: `1 passed`
  - `python research/knowledge-hub/runtime/scripts/run_l1_method_specificity_acceptance.py --json`
  - result: `success`
- `v1.69` discovery-bridge closure slices on 2026-04-12:
  - `python -m pytest research/knowledge-hub/tests/test_source_discovery_contracts.py -q`
  - result: `3 passed`
  - `python research/knowledge-hub/runtime/scripts/run_l0_source_discovery_acceptance.py --json`
  - result: `success`
  - `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "l0_source_discovery_acceptance" -q`
  - result: `1 passed, 28 deselected`
- `v1.68` compiled-knowledge / vault / statement-compilation closure slices on
  2026-04-12:
  - `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -q -k "source_backed_l1_intake or l1_vault"`
  - result: `2 passed`
  - `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -q -k "l1_vault_acceptance or statement_compilation_acceptance"`
  - result: `2 passed`
  - `python -m pytest research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_l1_vault_contracts.py research/knowledge-hub/tests/test_statement_compilation_contracts.py -q`
  - result: `13 tests passed`
  - `python research/knowledge-hub/runtime/scripts/run_l1_vault_acceptance.py --json`
  - result: `success`
  - `python research/knowledge-hub/runtime/scripts/run_statement_compilation_acceptance.py --json`
  - result: `success`
- public-package closure slice:
  - `python -m unittest discover -s research/knowledge-hub/tests -p "test_agent_bootstrap_assets.py"`
  - `python -m unittest discover -s research/knowledge-hub/tests -p "test_documentation_entrypoints.py"`
  - `python -m unittest discover -s research/knowledge-hub/tests -p "test_dependency_contracts.py"`
  - `python -m unittest discover -s research/knowledge-hub/tests -p "test_quickstart_contracts.py"`
  - `python -m unittest discover -s research/knowledge-hub/tests -p "test_public_install_contracts.py"`
  - result: `24 tests passed`
- distribution metadata acceptance:
  - `python research/knowledge-hub/runtime/scripts/run_dependency_contract_acceptance.py --json`
  - result: `success`
- public install smoke acceptance:
  - `python research/knowledge-hub/runtime/scripts/run_public_install_smoke.py --json`
  - result: `success`
- install/adoption regression slice:
  - `python -m unittest research/knowledge-hub/tests/test_agent_bootstrap_assets.py research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_quickstart_contracts.py research/knowledge-hub/tests/test_aitp_cli_e2e.py`
  - result: `159 tests passed`
- first-run acceptance:
  - `python research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py --json`
  - result: `success`
- Windows-native Claude hook probe:
  - `python hooks/session-start.py`
  - result: `JSON SessionStart payload emitted successfully`
- full knowledge-hub suite:
  - `python -m unittest discover -s research/knowledge-hub/tests -v`
  - result: `367 tests passed`

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. move newly validated scope into milestone history
2. record fresh decisions or constraints that change later planning
3. surface any new deferred scope explicitly instead of hiding it in chat

**After each milestone:**
1. promote the next bounded milestone into `Current Milestone`
2. refresh active focus and latest-closed context
3. keep the maturity ladder and honesty boundary aligned with real shipped state

## Immediate Reality Check

This does **not** mean AITP is finished.

It means `v1.97` is archived on a stronger positive-L2 baseline and the next
bounded milestone can widen honestly to the deferred `HS model` and `LibRPA
QSGW` lanes instead of re-litigating whether AITP already has a trustworthy
positive canonical-L2 path.

---
*Last updated: 2026-04-14 after starting milestone v2.9*
