# AITP Mode Envelope Protocol

Status: draft working doctrine

## Decision

AITP modes should define operating envelopes, not replace the layer ontology.

Each mode must specify:

- local task,
- foreground layers,
- minimum mandatory context,
- deferred context,
- allowed backedges,
- writeback obligations,
- human-checkpoint policy.

Short form:

- mode controls posture
- layer controls epistemic meaning

## Why This Document Exists

AITP already has:

- lanes,
- layers,
- runtime bundles,
- progressive-disclosure ideas.

But until the mode envelope is explicit, the runtime will keep drifting toward
two bad extremes:

- too much mandatory context,
- or too little research discipline.

Mode envelopes are how AITP avoids both.

## 1. Core Rule

At any moment, AITP should load only the minimum context required for the
current mode and the current boundary crossing.

Nothing else should become mandatory just because the artifact exists.

Modes therefore define:

- what is mandatory now,
- what is callable on trigger,
- what must stay deferred,
- and what kind of result is legitimate for this step.

## 2. Required Fields For Every Mode

Each mode definition should explicitly state:

1. `local_task`
2. `foreground_layers`
3. `minimum_mandatory_context`
4. `deferred_context`
5. `allowed_backedges`
6. `required_writeback`
7. `forbidden_shortcuts`
8. `human_checkpoint_policy`
9. `entry_conditions`
10. `exit_conditions`

## 3. Primary Modes

### 3.1 Discussion Mode

#### Local task

- shape the question,
- compare framings,
- clarify direction,
- preserve an exploration window before heavy crystallization.

#### Foreground layers

- `L0`
- `L1`
- early `L3`

#### Minimum mandatory context

- active topic identity
- current human request
- current steering if it already exists
- minimal source subset if already registered

#### Deferred context

- full validation bundle
- promotion surfaces
- topic completion surfaces
- broad `L2` retrieval
- heavy follow-up or execution artifacts

#### Allowed backedges

- `L1 -> L0`
- narrow `L1/L3 -> L2`

#### Required writeback

- clarified question fragment
- direction note if steering changed
- unresolved ambiguity note if the question is still open

#### Forbidden shortcuts

- do not pretend discussion already equals validation
- do not preload heavy `L4` or promotion context
- do not force a full contract closure before the idea has a real shape

#### Human checkpoint policy

- ask only when the ambiguity materially changes route choice

### 3.2 Explore Mode

#### Local task

- form bounded candidates,
- generate routes,
- build derivation or benchmark scaffolds,
- turn vague direction into testable work.

#### Foreground layers

- `L1`
- `L3`

#### Minimum mandatory context

- current research question
- active idea packet if it exists
- selected bounded action
- the minimal source or prior-work subset needed for the current candidate

#### Deferred context

- full promotion package
- unrelated historical logs
- unrelated prior candidates
- broad `L2` memory loads

#### Allowed backedges

- `L3 -> L0`
- `L3 -> L2`

#### Required writeback

- candidate packets
- explicit blocker notes
- route choice notes
- source recovery notes when needed

#### Forbidden shortcuts

- do not treat a candidate as validated
- do not treat local plausibility as promotion readiness

#### Human checkpoint policy

- ask only at real route changes, cost changes, or novelty-definition changes

### 3.3 Verify Mode

#### Local task

- test a candidate,
- choose or execute a validation route,
- resolve a contradiction,
- inspect proof obligations,
- or adjudicate whether a claim survives.

#### Foreground layers

- `L4`

#### Minimum mandatory context

- current validation contract
- the selected candidate or selected action
- the specific execution or proof surface required for the current check
- current blockers

#### Deferred context

- unrelated `L2` bodies
- unrelated topic families
- broad topic history not relevant to the current check

#### Allowed backedges

- `L4 -> L0`
- `L4 -> L2`

#### Required writeback

- validation result artifacts
- contradiction or mismatch artifacts
- explicit blocker classification
- updated decision or route record

#### Forbidden shortcuts

- do not let style confidence count as validation
- do not keep iterating when the real problem is missing `L0` or `L2` support

#### Human checkpoint policy

- ask when the execution lane, resource commitment, or adjudication route is
  still materially open

### 3.4 Promote Mode

#### Local task

- inspect promotion gates,
- decide whether writeback is allowed,
- choose the target backend,
- and execute canonical writeback only when justified.

#### Foreground layers

- `L4 -> L2` boundary

#### Minimum mandatory context

- current gate state
- current candidate
- target backend information
- the exact supporting artifacts required by the gate

#### Deferred context

- unrelated topic history
- unrelated `L2` areas
- future publication surfaces

#### Allowed backedges

- `promote -> L4`
- `promote -> L0`
- narrow consult into `L2`

#### Required writeback

- promotion gate artifact
- promotion decision
- backend receipt
- updated reusable-memory registration

#### Forbidden shortcuts

- do not treat consultation as promotion
- do not treat "looks mature" as gate satisfaction

#### Human checkpoint policy

- human checkpoints remain legitimate for writeback and expensive trust moves

## 4. Conditional Submode: Iterative Verify

AITP may enter `iterative_verify` inside `explore` or `verify` when:

- the objective is bounded,
- the loop has a concrete completion test,
- each failed iteration can produce explicit feedback,
- and the task is small enough to fit repeated short passes safely.

This submode is defined in:

- [`AITP_L3_L4_ITERATIVE_VERIFY_LOOP_PROTOCOL.md`](AITP_L3_L4_ITERATIVE_VERIFY_LOOP_PROTOCOL.md)

## 5. Backedge Rule

Modes must explicitly allow legitimate returns to `L0` and `L2`.

If the current failure is really:

- missing source,
- missing citation chain,
- missing definition,
- missing prior-work comparison,
- missing reusable method memory,

AITP should leave the current local loop and create a real backedge rather than
pretending more local iteration will solve it.

That movement law is formalized in:

- [`AITP_TRANSITION_AND_BACKEDGE_PROTOCOL.md`](AITP_TRANSITION_AND_BACKEDGE_PROTOCOL.md)

## 6. Context Loading Rule

The mode envelope should govern the runtime's top disclosure tier.

In practice this means:

- `must_read_now` should be mode-bounded,
- deeper surfaces should be trigger-bounded,
- and unrelated later-layer artifacts should remain deferred.

Progressive disclosure is therefore not optional product polish.
It is a mode-enforcement rule.

## 7. Implementation Rule

Current implementation details such as:

- `load_profile`
- runtime bundle generation
- shell-surface generation
- support modules

should increasingly become implementations of mode envelopes rather than a
parallel hidden policy system.

This also means continued reduction of giant hotspot files still matters:

- not because code size is the only problem,
- but because hidden coupling makes mode boundaries harder to trust.

## 8. Current Consequence

AITP should now move toward:

- explicit top-level modes,
- explicit minimum mandatory context per mode,
- explicit allowed backedges per mode,
- explicit human-checkpoint policy per mode,
- and runtime bundles that reflect those policies honestly.

That is the intended envelope model.
