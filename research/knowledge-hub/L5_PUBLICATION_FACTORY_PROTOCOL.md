# L5 publication factory protocol

Status: future protocol draft

This file defines the future `L5` publication/output layer for AITP.

`L5` is not a new scientific-truth layer.
It is the final communication and manuscript-production layer that turns a
completed topic into paper-grade writing outputs.

The intended ordering remains:

- `L0 -> L1 -> L3 -> L4` establishes research truth and validation state
- `L2` preserves reusable promoted knowledge
- `L5` converts that completed work into publication artifacts

## 1. Why this exists

AITP should not stop at "the topic is complete" if the practical next step is:

- write the paper,
- write the thesis chapter,
- write the technical report,
- prepare the talk,
- or generate the submission package.

Right now those outputs are only partially represented by runtime and canonical
surfaces.

`L5` exists to make the final writing step explicit, durable, and governed.

## 2. Core stance

`L5` may:

- organize,
- compress,
- narrate,
- style,
- format,
- and polish.

`L5` may not:

- invent new scientific claims,
- hide uncertainty,
- upgrade a candidate into a validated result,
- or patch missing evidence by prose alone.

If the writing pipeline discovers a missing claim boundary, missing related
work, missing derivation support, or missing validation evidence, the correct
action is to reopen topic work in `L0-L4`, not to fix the gap inside `L5`.

## 3. Scope

Use `L5` only after a topic has already reached a real completion posture.

Typical valid `L5` targets:

- paper manuscript
- thesis chapter
- technical report
- internal research memo
- talk or slide deck
- poster or extended abstract
- supplementary material
- reviewer-response package

Do not use `L5` for:

- early topic exploration
- candidate formation
- validation routing
- unresolved contradiction handling
- promotion into `L2`

## 4. Entry conditions

Before `L5` starts, the topic should already have:

- a stable `topic_synopsis.json`
- a completed or near-completed `topic_completion.json|md`
- durable `L3/L4` evidence for the claims that will be written
- explicit scope and limitation surfaces
- any required `L2` promoted memory already written when the topic depends on it

Minimum rule:

- if the topic cannot explain what claims are already supported and what
  evidence supports them, it is not ready for `L5`

## 5. Inputs

`L5` should consume the following classes of artifacts.

### 5.1 Topic state and runtime summary

- `runtime/topics/<topic_slug>/topic_synopsis.json`
- `runtime/topics/<topic_slug>/topic_dashboard.md`
- `runtime/topics/<topic_slug>/topic_completion.json`
- `runtime/topics/<topic_slug>/topic_completion.md`
- `runtime/topics/<topic_slug>/runtime_protocol.generated.json`
- `runtime/topics/<topic_slug>/runtime_protocol.generated.md`

### 5.2 Research artifacts

- `L0` source records and citation anchors
- `L1` scoped question, terminology, assumptions, and non-goals
- `L3` candidate evolution, methods, rejected routes, and strategy memory
- `L4` validation evidence, audits, adjudication, follow-up gaps, and review bundles

### 5.3 Canonical memory

- relevant promoted `L2` units such as:
  - concept
  - definition_card
  - theorem_card
  - derivation_object
  - method
  - workflow
  - validation_pattern
  - warning_note
  - topic_skill_projection

## 6. Outputs

`L5` should materialize a publication bundle rather than one giant prose note.

Suggested future layout:

```text
publication/
  topics/<topic_slug>/
    runs/<publication_run_id>/
      paper_manifest.json
      claim_evidence_map.json
      paper_outline.md
      related_work_map.md
      figure_table_plan.md
      limitations_and_scope.md
      citation_manifest.json
      manuscript.md or main.tex
      abstract_variants.md
      cover_letter.md
      response_to_reviewers.md
      supplementary.md
      writing_audit.json
      writing_audit.md
```

Not every run needs every file, but these are the intended primary surfaces.

### 6.1 Minimum mandatory outputs

At least these should exist for a non-trivial `L5` run:

- `paper_manifest.json`
- `claim_evidence_map.json`
- `paper_outline.md`
- `limitations_and_scope.md`
- manuscript draft
- `writing_audit.json`

## 7. Core lifecycle

One complete `L5` pass should follow this order.

### Step 1. Freeze a topic snapshot

Before drafting begins, freeze the topic state that the manuscript is allowed to
use.

This prevents the writing layer from drifting while the research layer is still
changing underneath it.

### Step 2. Select publication target

Declare:

- target artifact type
- audience
- venue or style target
- desired length and section structure

### Step 3. Extract paper-worthy claims

Only claims already supported by topic artifacts may enter the writing set.

This step should explicitly separate:

- supported claims
- speculative but interesting ideas
- known limitations
- open future work

### Step 4. Build claim-to-evidence map

Every manuscript-grade claim should point to durable support.

The purpose is not just traceability.
It is also to block overclaiming before prose polish starts.

### Step 5. Organize narrative

The publication layer should then decide:

- motivation
- problem statement
- prior work positioning
- method story
- validation/results story
- limitations
- outlook

This is where writing skill matters.
But writing skill must remain downstream of the claim/evidence map.

### Step 6. Generate manuscript draft

Once claim and structure are stable, `L5` may generate:

- full prose draft
- section variants
- title and abstract variants
- figure/table references
- venue-shaped formatting outputs

### Step 7. Run writing audit

The final step is an `L5` writing audit that checks:

- unsupported statements
- claim/evidence mismatches
- missing citations
- scope drift
- overclaiming
- omitted limitations

If the audit fails, the output is not publication-ready.

## 8. Mandatory rules

### Rule 0. `L5` is downstream only

`L5` may consume completed research state.
It may not replace research-state validation.

### Rule 1. Evidence before rhetoric

No polished paragraph outranks the underlying claim/evidence map.

### Rule 2. Limitations stay visible

If a topic has unresolved scope limits, those limits must remain visible in the
publication bundle.

### Rule 3. Related work is not decoration

If the manuscript meaning depends on prior work comparison, `L5` must surface
that comparison explicitly.
If the comparison is missing, reopen `L0-L4`.

### Rule 4. Null or negative results are valid outputs

`L5` should be able to write an honest negative-result or bounded-failure
manuscript package.

### Rule 5. `L5` is not `L2`

A beautiful manuscript draft does not itself create canonical knowledge.
`L2` promotion and `L5` publication are separate paths.

## 9. Writing audit contract

The writing audit should classify each draft into one of:

- `ready`
- `ready_with_limits`
- `needs_topic_reopen`
- `blocked`

### `ready`

Claims are supported, citations are adequate, and limitations are correctly
stated.

### `ready_with_limits`

The manuscript is acceptable only if stated limits remain explicit.

### `needs_topic_reopen`

The writing step found missing evidence, unresolved claim boundaries, or missing
comparisons that must be fixed upstream.

### `blocked`

The topic was not actually mature enough for `L5`.

## 10. Relationship to `topic_skill_projection`

`topic_skill_projection` tells a future agent how to safely re-enter a topic
family.

`L5` tells a publication pipeline how to safely write a completed topic.

They are related but not equivalent:

- `topic_skill_projection` is reusable execution memory
- `L5` is reusable writing/communication packaging

## 11. Future runtime handshake

This protocol is not yet implemented as a runtime trigger.

When the runtime eventually exposes `L5`, the intended trigger name should be:

- `publication_intent`

When that trigger is active, the next agent should open:

- `L5_PUBLICATION_FACTORY_PROTOCOL.md`
- the completed topic snapshot
- the claim/evidence map
- the current manuscript bundle
- the latest writing audit

This trigger should not activate before topic completion and evidence closure
are already materially true.

## 12. One-line doctrine

`L5` should turn completed research into publication-ready writing without
altering what the research actually proved.
