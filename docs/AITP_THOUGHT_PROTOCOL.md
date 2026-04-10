# AITP Thought Protocol

Status: draft working doctrine

This document defines the design doctrine that should guide future AITP
simplification work.

It sits below the public charter and above concrete runtime structure.

Its job is not to restate every protocol file.
Its job is to answer a narrower question:

- what complexity is essential,
- what complexity is accidental,
- what outside workflow systems AITP should learn from,
- and how to simplify implementation without weakening the research protocol.

## 1. Core stance

AITP should become simpler in structure, not weaker in research discipline.

That means:

- preserve the scientific trust boundaries,
- preserve the `L0 -> L1 -> L3 -> L4 -> L2` model,
- preserve explicit promotion and audit semantics,
- but aggressively remove duplicated projections, repeated summaries, and
  implementation-side artifact sprawl.

The target is:

`strict thought protocol + light product surface + explicit control plane + reusable research memory`

See also:

- [`AITP_INTELLIGENCE_PRESERVATION_PRINCIPLES.md`](AITP_INTELLIGENCE_PRESERVATION_PRINCIPLES.md)
- [`AITP_ONTOLOGY_AND_MODE_COMPLETENESS.md`](AITP_ONTOLOGY_AND_MODE_COMPLETENESS.md)
- [`AITP_MODE_ENVELOPE_PROTOCOL.md`](AITP_MODE_ENVELOPE_PROTOCOL.md)
- [`AITP_L3_L4_ITERATIVE_VERIFY_LOOP_PROTOCOL.md`](AITP_L3_L4_ITERATIVE_VERIFY_LOOP_PROTOCOL.md)
- [`AITP_TRANSITION_AND_BACKEDGE_PROTOCOL.md`](AITP_TRANSITION_AND_BACKEDGE_PROTOCOL.md)

## 2. What must not be simplified away

The following are essential protocol complexity, not accidental complexity.

### 2.1 Evidence hierarchy

AITP must continue to distinguish:

- source-grounded statements,
- provisional understanding,
- exploratory candidates,
- validation or adjudication,
- reusable promoted memory.

These are not UI categories.
They are the core scientific honesty boundary.

### 2.2 Layer order

The default non-trivial route remains:

`L0 -> L1 -> L3 -> L4 -> L2`

`L2` stays last.
Reusable memory is earned, not assumed.

### 2.3 Human checkpoints

Human steering, pause, redirect, branch, and promotion approval remain part of
the protocol.

Human intervention is not a failure mode.
It is a legitimate part of research control.

### 2.4 Explicit contracts

If a research step matters, it should still have a durable contract or ledger
surface.

AITP should simplify the number of artifacts, not return to hidden prompt state
or chat-only memory.

## 3. What should be simplified aggressively

The current implementation has real duplication and should be reduced.

### 3.1 One truth per concern

For each concern, prefer:

- one authoritative machine-readable source,
- one primary human-facing rendering,
- optional ephemeral derived views.

Avoid a pattern where one state is persisted in many near-equivalent files.

### 3.2 Runtime should be thin

The runtime should be a control plane, not a second knowledge base.

It may expose:

- current topic state,
- current focus,
- current next action,
- current blockers,
- current promotion posture.

It should avoid accumulating many parallel summary files that restate the same
status in slightly different forms.

### 3.3 L1 should store interpretation, not source duplication

`L0` is the source substrate.

`L1` should record:

- what the source means for this topic,
- where ambiguity remains,
- what interpretation the topic is currently using.

`L1` should not mirror `L0` source metadata unless a specific intake-only
transformation is required.

### 3.4 L4 should bundle audits before splitting them

Validation dimensions may remain distinct, but the operator should not be
forced to navigate a file explosion for one bounded review.

Prefer:

- one main review bundle,
- clearly named sections inside it,
- optional specialist subfiles only where genuinely necessary.

### 3.5 Topic reuse should stay protocol-native first

Reusable topic execution should first become:

- `topic_skill_projection`

inside AITP.

Only later, if justified, should it become:

- adapter bootstrap hints,
- projection-aware routing signals,
- generated platform skills,
- or other product-facing wrappers.

AITP should not collapse mature topic memory directly into static
platform-specific `SKILL.md` files.

## 4. What AITP should learn from external systems

Three workflow systems are especially relevant.

### 4.1 GSD

Use GSD as the model for:

- explicit project state,
- explicit progress surfaces,
- explicit phase and plan structure,
- resumable execution context,
- inspectable CLI control surfaces.

The lesson is:

- natural language is not enough,
- explicit control surfaces reduce ambiguity,
- project state should be visible and recoverable.

AITP should adopt that lesson at the topic-management level.

This does **not** mean replacing the research layer model with generic software
project phases.

### 4.2 Superpowers

Use Superpowers as the model for:

- natural-language-first entry,
- automatic activation of the correct workflow,
- progressive disclosure,
- product feel that hides protocol jargon from the user.

The lesson is:

- the user should not have to learn a command language to enter the right
  research workflow,
- but the hidden routing must still materialize durable state.

AITP should borrow the front-door experience, not the ontology.

### 4.3 OpenSpec

Use OpenSpec as the model for:

- a small number of stable work artifacts,
- brownfield-friendly specification discipline,
- agreeing on the change surface before implementation,
- keeping one change centered on one explicit home.

The lesson is:

- a bounded topic or protocol change should not scatter its meaning across many
  near-equivalent files,
- AITP should prefer a few authoritative surfaces over many overlapping
  summaries,
- specification discipline should remain lightweight enough for iterative work.

AITP should borrow the compact artifact mindset, not the software-only file
names.

### 4.4 gstack

Use gstack as the model for:

- ordered workflow loops,
- explicit review pressure,
- visible delivery stages,
- operator-readable command surfaces for "where the work is now."

The lesson is:

- topic control should be explicit and inspectable,
- review is not an optional afterthought,
- "what step are we in?" should have a concrete answer at the command surface.

AITP should borrow the explicit control-plane feel while preserving its own
scientific layer ontology.

### 4.5 Compound Engineering

Use Compound as the model for:

- explicit workflow loops,
- review and reflection as first-class stages,
- codifying reusable learnings after execution,
- compounding capability instead of restarting from scratch each time.

The lesson is:

- each real topic should leave behind reusable route memory,
- the system should become better because past work was structured,
- not because the chat model "remembers" informally.

In AITP, the correct native target for this is:

- `topic_skill_projection`
- validated methods
- validated workflows
- warning notes
- bridge notes

## 5. Product formula

The intended product shape is:

`Superpowers-style entry + GSD-style explicit control + Compound-style reusable learning + AITP scientific trust model`

Broken down:

- `Superpowers-style entry`
  - natural language first
  - progressive disclosure
  - low protocol surface in user-facing dialogue

- `GSD-style explicit control`
  - inspectable topic status
  - explicit focus selection
  - explicit progress and next-step visibility
  - resumable planning artifacts for repo work

- `Compound-style reusable learning`
  - mature routes become reusable protocol objects
  - useful execution patterns are codified
  - review leads to better future execution

- `AITP scientific trust model`
  - layers stay distinct
  - promotion stays governed
  - research truth stays separate from execution convenience

## 6. Simplification rules

When deciding whether to remove or merge structure, apply these rules.

### Rule 1

If two files answer the same operator question, one should usually become
derived rather than authoritative.

### Rule 2

If a file exists only to restate another file in prose, prefer on-demand
rendering unless the prose version serves a distinct checkpoint or audit need.

### Rule 3

If a structure exists only because one adapter needed it once, do not promote it
to a core AITP invariant.

### Rule 4

If a simplification would erase:

- evidence boundaries,
- promotion semantics,
- audit semantics,
- or uncertainty tracking,

reject that simplification.

### Rule 5

If a new feature can be expressed as:

- metadata on an existing object,
- a read-path extension,
- or a derived operator surface,

prefer that over adding a new top-level artifact family.

## 7. Current strategic direction

The immediate direction should be:

1. simplify duplicated runtime and intake projections,
2. land explicit multi-topic registry and focus semantics,
3. preserve natural-language-first entry while exposing clearer topic-control
   surfaces,
4. treat projection-aware topic-family routing as the next layer after the
   registry stabilizes,
5. postpone generated platform skills and adapter auto-load until the
   protocol-native reuse model is proven stable.

## 8. One-line doctrine

AITP should be:

- strict in scientific semantics,
- simple in product entry,
- explicit in control surfaces,
- and compounding in reusable research memory.

It should not be:

- chat-only,
- artifact-sprawling,
- adapter-defined,
- or bloated by duplicate summaries.
