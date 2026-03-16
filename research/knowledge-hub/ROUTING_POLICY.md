# Routing policy

This file defines how new material is analyzed and routed across `L0/L1/L2/L3/L4`.

The purpose is to make routing operational rather than intuitive.

## 1. Core principle

The default route for non-trivial research material is:

`L0 -> L1 -> L3 -> L4 -> L2`

The low-risk exception route is:

`L0 -> L1 -> L2`

Direct `L1 -> L4 -> L2` is not allowed.

## 2. Stage roles

### Layer 0

Role:
- source acquisition,
- source identity,
- source reopening,
- search and retrieval substrate.

Current note:
- Layer 0 is not yet split into its own dedicated top-level persistent directory,
- at the moment its operational trace is embedded in intake registration and snapshots.

### Layer 1

Role:
- source-bound understanding,
- snapshotting,
- chunking,
- provisional claims,
- first-pass interpretation.

### Layer 2

Role:
- active research memory,
- canonical reusable objects,
- comparison surface for later stages,
- final writeback target for promoted units.

Important constraint:
- Layer 2 is not only the end of the route,
- it must also be consulted during `L1`, `L3`, and `L4`.

### Layer 3

Role:
- candidate formation,
- research planning,
- derivation scaffolding,
- blocker organization,
- bridge and method exploration.

### Layer 4

Role:
- adjudication,
- execution-bound checking,
- contradiction testing,
- promotion / reject / defer decisions.

## 3. Input classes

The routing policy should handle at least:
- paper
- PDF
- URL / web page
- video
- transcript
- human conversation
- local note or notebook fragment

Every input first needs:
- `topic_slug`
- `source_id`
- source type
- source provenance

## 4. Routing by stage

### Step A. Register the source in Layer 0 / Layer 1

Create or update:
- `intake/topics/<topic_slug>/source_index.jsonl`
- `intake/topics/<topic_slug>/sources/<source_id>/`

Expected artifacts:
- source identity
- source snapshot or durable pointer
- raw notes if needed

At this point the system knows **what the source is**, not yet what should be kept.

### Step B. Produce Layer 1 understanding artifacts

Create or update:
- provisional notes
- chunk-level observations if needed
- `provisional_claims.jsonl`
- `promotion_candidates.jsonl` if a low-risk reusable unit is already visible

Mandatory Layer 2 consultation during Layer 1:
- compare extracted terminology against existing `concept` objects,
- compare source-local claims against existing `claim_card` objects,
- check `warning_note` objects for known traps or scope creep,
- check `workflow` objects if the source should be processed through an existing research routine.

For non-trivial cases that materially shape a durable Layer 1 artifact, this consultation must emit protocol artifacts under:
- `consultation/`

The stage-local `l2_consultation_log.jsonl` file remains a projection, not the consultation source-of-truth.

Layer 1 outputs split into two cases:

#### Case 1. Low-risk reusable material

If the item is already:
- reusable,
- explicit in scope,
- explicit in assumptions,
- source-anchored,
- low-risk enough to avoid deeper adjudication,

then it may route:

`L0 -> L1 -> L2`

Typical examples:
- a narrow concept definition,
- a small warning note about a documented limitation,
- a tightly scoped source-anchored claim card.

#### Case 2. Active research material

If the item triggers:
- ambiguity,
- derivation work,
- comparison work,
- bridge-building,
- planning,
- or execution-heavy checking,

then route to Layer 3.

### Step C. Form Layer 3 candidates

Create or update:
- research log entries,
- derivation scaffolds,
- idea ledgers,
- blockers,
- candidate objects,
- next actions.

Mandatory Layer 2 consultation during Layer 3:
- retrieve `method` objects before inventing a procedure from scratch,
- retrieve `derivation_object` objects before building a new derivation route,
- retrieve `bridge` objects when trying to connect frameworks,
- retrieve `workflow` objects for known research procedures,
- retrieve `warning_note` objects before committing to a risky interpretation.

For non-trivial cases that materially shape a durable Layer 3 artifact, record this via the `L2 consultation` protocol surface first and only then project a compact local summary if needed.

Layer 3 should produce a **candidate** when:
- the target object type is known,
- the research question is explicit,
- the expected evidence is explicit,
- the need for adjudication is explicit.

Then route:

`L3 -> L4`

### Step D. Adjudicate in Layer 4

Create or update:
- validation notes,
- execution tasks,
- contradiction checks,
- benchmark or reproduction records,
- baseline-reproduction records when the backend or diagnostic is not yet trusted,
- atomic-understanding records when a derivation-heavy method is being reused,
- promotion decisions.

Mandatory Layer 2 consultation during Layer 4:
- retrieve `validation_pattern` objects to define the right checks,
- retrieve `claim_card` objects for contradiction comparison,
- retrieve `warning_note` objects for known failure modes,
- retrieve relevant `concept` and `derivation_object` objects to test scope and regime consistency.

For non-trivial adjudication that materially shapes a durable Layer 4 artifact or decision, the consultation protocol artifacts must be treated as the source-of-truth for what `L4` asked, what `L2` returned, and what was actually applied.

Layer 4 must answer:
- what candidate is being judged,
- what checks were required,
- which checks passed or failed,
- whether the result is now reusable enough for Layer 2.

Before trusting a new method-dependent result, Layer 4 should also answer:
- was a public or analytic baseline reproduced first for the numerical backend,
- was the relevant theory method decomposed into atomic concepts and dependencies first,
- if not, why the result still remains only exploratory or deferred.

Then either:
- route `L4 -> L2` if accepted,
- or route `L4 -> L3` if deferred, rejected, or still unresolved.

### Step E. Write back to Layer 2

Write back only:
- reusable typed units,
- with explicit provenance,
- with explicit assumptions and regime,
- with explicit promotion metadata.

Do not write back:
- run-local TODOs,
- vague summaries,
- unresolved coordination debt,
- backlog artifacts that still belong in Layer 3.

## 5. Allowed and disallowed edges

### Allowed

- `L0 -> L1`
- `L0 -> L1 -> L2` in low-risk cases
- `L0 -> L1 -> L3 -> L4 -> L2`
- `L2 -> L1` as consultation
- `L2 -> L3` as consultation and seeding
- `L2 -> L4` as consultation for validation patterns and contradiction checks
- `L4 -> L3` when adjudication fails or produces new research work

### Disallowed

- `L1 -> L4 -> L2`
- `L3 -> L2` without Layer 4 adjudication for non-trivial cases
- treating an external note vault as the live formal Layer 2 store
- treating a handoff note surface as the live formal Layer 4 store

## 6. Worked route: paper input

Example route:

1. Register the paper as `source_id = paper:foo-2026`.
2. Store source registration and snapshot trace under intake.
3. Extract provisional claims in Layer 1.
4. Compare terminology against Layer 2 concepts and claim cards.
5. Discover that one claim needs derivation and scope checking.
6. Create a Layer 3 candidate for a `claim_card` plus supporting `derivation_object`.
7. Pull relevant methods, warnings, and derivation objects from Layer 2.
8. Create a Layer 4 validation case and execution tasks.
9. Compare against Layer 2 validation patterns and existing claim cards.
10. If adjudication succeeds, promote one or more Layer 2 units.

## 7. Worked route: video or URL input

Example route:

1. Register the video or URL source.
2. Store transcript or snapshot trace under intake.
3. Extract source-bound statements and provisional claims.
4. Consult Layer 2 concepts and warning notes to normalize terminology.
5. If the content is mainly explanatory and low-risk, promote a small concept or warning note directly.
6. If the content raises a real research question, form a Layer 3 candidate and continue through Layer 4.

## 8. Current limitation

Layer 0 is not yet independently formalized.

So the routing policy should be read as:
- conceptually starting in `L0`,
- but operationally registering the durable trace inside intake until the dedicated Layer 0 contract exists.
