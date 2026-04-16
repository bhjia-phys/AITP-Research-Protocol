# Global L2 Reuse And Capability Plane Design

## Goal

Make AITP reusable across real research topics by separating three concerns that
are currently partially present but not yet unified:

1. a global `L2` reusable knowledge layer,
2. progressive `L3` read surfaces for idea formation and plan writing,
3. a runtime capability plane that exposes what tools, scripts, servers, and
   environments are actually executable now.

The result should let `L3`:

- reuse scientific and technical knowledge without re-reading everything,
- know what execution resources exist before writing a plan,
- and hand `L4` an explicit execution contract instead of an underspecified
  prose request.

## Problem

The repository already contains important pieces:

- typed canonical `L2` families,
- `consult-l2`,
- topic skill projections,
- staging,
- compiled graph/knowledge reports,
- execution-task and returned-result contracts,
- backend bridge metadata,
- and runtime executor hints.

But they do not yet form one coherent reuse system.

Current gaps:

- `L2` is still operator-useful but not yet the default reusable read layer for
  `L3` idea and plan work.
- the repository does not yet expose one explicit progressive read surface such
  as `idea_reuse_context` or `plan_reuse_context`.
- execution resources exist in several places, but `L3` does not yet consume
  them through one stable capability plane before planning.
- human operators can describe available tools or servers in natural language,
  but the runtime lacks one stable artifact contract that turns those statements
  into machine-checkable planning inputs.

## Core design choice

Adopt a four-layer stance:

1. global authoritative `L2`
2. global compiled `L2` mirror
3. global runtime capability plane
4. topic-scoped progressive reuse contexts

Short form:

- `L2` is global reusable memory
- compiled `L2` is a human-facing mirror and navigation layer
- capability is runtime truth about what can execute now
- topics consume these layers through bounded read contexts rather than owning a
  separate topic-local `L2`

## Design decisions

### 1. `L2` is global, not topic-owned

Canonical reusable memory should remain global under `canonical/`.

Topic folders should keep:

- consultations,
- runtime state,
- run journals,
- planning artifacts,
- staging/projection references,
- and read-context projections.

They should not become a second per-topic `L2` truth store.

### 2. `L2` is not physics-only

`L2` should hold reusable knowledge of three broad kinds:

- scientific knowledge
- technical knowledge
- execution knowledge

Examples:

- `physical_picture`, `claim_card`, `theorem_card`
- `method`, `workflow`, `validation_pattern`
- `warning_note`, `negative_result`, `bridge`
- `topic_skill_projection`

This means reusable code-method knowledge, benchmark workflows, server-facing
execution patterns, and failure playbooks may live in `L2` as long as they are
durable, scoped, and honestly reusable.

### 3. Each `L2` unit must carry topic-linked evidence

Global storage must not erase where a unit came from or where it was reused.

Each reusable `L2` unit should support fields such as:

- `origin_topic_refs`
- `origin_run_refs`
- `validation_receipts`
- `reuse_receipts`
- `related_consultation_refs`
- `applicable_topics`
- `failed_topics`
- `regime_notes`

This keeps global memory reusable while preserving scientific traceability.

### 4. Compiled Markdown mirror is fixed-folder and Obsidian-friendly

Human-facing reading should not require opening raw JSON files.

Add one fixed global Markdown mirror rooted under compiled `L2`, for example:

```text
canonical/compiled/obsidian_l2/
  README.md
  index.md
  families/
    concepts/
    physical-pictures/
    claim-cards/
    theorem-cards/
    proof-fragments/
    derivation-objects/
    methods/
    workflows/
    topic-skill-projections/
    validation-patterns/
    warning-notes/
    negative-results/
    bridges/
```

This mirror is:

- stable in layout,
- regenerated from authoritative inputs,
- safe for Obsidian browsing,
- and explicitly non-authoritative.

Each unit page should expose:

- what the unit is,
- why it is reusable,
- origin topic/run links,
- validated-in topic links,
- reused-in topic links,
- failure/limit notes,
- canonical JSON path,
- authority level.

### 5. Runtime capability plane is a separate truth surface

Do not store volatile execution availability inside canonical `L2`.

Instead add a global runtime capability plane, for example:

```text
runtime/capabilities/
  registry.json
  tools/
  servers/
  environments/
  workflows/
  status/
  topic_overrides/
```

Meaning:

- `tools/`, `servers/`, `environments/`, `workflows/`
  - stable declared capability cards
- `status/`
  - volatile snapshots or probes
- `topic_overrides/`
  - optional topic-scoped allow/deny or preference overlays

The capability plane is the place where `L3` learns:

- which tools exist,
- which scripts are valid,
- which servers or schedulers are available,
- which environments are allowed,
- which workflow cards are currently usable.

### 6. Capability cards may be written by humans or via natural-language intake

AITP should support two operator entry paths:

- direct human editing of capability cards
- natural-language declarations that AITP converts into capability cards

But the runtime should never plan from raw chat text alone.

Natural-language declarations must compile into explicit artifacts before
planning can rely on them.

High-risk changes should require explicit confirmation, especially for:

- remote execution roots,
- destructive permissions,
- scheduler commands,
- target backend paths,
- credentials or auth mode assumptions.

### 7. `L3` should consume bounded progressive read contexts

Instead of opening the whole `L2`, `L3` should consume generated topic-scoped
reuse contexts:

- `topics/<topic_slug>/runtime/idea_reuse_context.json|md`
- `topics/<topic_slug>/runtime/plan_reuse_context.json|md`
- `topics/<topic_slug>/runtime/execution_resource_context.json|md`

These are derived, not authoritative.

Their role:

- `idea_reuse_context`
  - the smallest context for question refinement and novelty shaping
- `plan_reuse_context`
  - the additional reusable knowledge needed for a concrete execution plan
- `execution_resource_context`
  - the concrete tools, servers, scripts, environments, and constraints
    currently available for this topic

## Progressive read policy

Use three reading depths:

### Quick

For early `L3` idea work:

- top compiled overview
- top canonical hits
- top warnings or negative results
- topic skill projection summary when available

Avoid:

- full consultation receipts
- raw staging entries
- full backend/server cards

### Standard

For `L3` plan writing:

- top canonical hits plus one-hop neighbors
- compact topic-linked evidence summary
- relevant validation patterns, methods, workflows
- selected tool/server/environment summaries

### Deep

Only when the task genuinely needs it:

- consultation request/result/application artifacts
- staged candidate details
- full backend cards
- operation manifests
- exact environment/server status snapshots

This preserves context while still allowing honest escalation.

## Reuse surface contents

### `idea_reuse_context`

Prioritize:

- `physical_picture`
- `bridge`
- `warning_note`
- `negative_result`
- `claim_card`
- `validation_pattern`

It should answer:

- what nearby ideas already exist,
- what repeatedly fails,
- what scope or regime limits matter,
- what novelty target seems plausible.

### `plan_reuse_context`

Build on `idea_reuse_context` and add:

- `method`
- `workflow`
- `derivation_object`
- `proof_fragment`
- `example_card`
- `topic_skill_projection`

It should answer:

- what exact reusable route exists,
- what the minimum benchmark/proof step is,
- what artifacts must be produced,
- what prior routes or scripts are worth reusing.

### `execution_resource_context`

Prioritize:

- relevant `server` cards
- relevant `tool` cards
- relevant `environment` cards
- workflow cards with execution constraints
- latest status snapshots

It should answer:

- where the task may run,
- which scripts/tools may be used,
- which environment is required,
- which resources are currently unavailable,
- which execution choice is recommended and why.

## Planning rule for `L3`

`L3` may not rely on free-form memory when concrete execution resources are
needed.

When a plan names:

- a server,
- a script,
- a tool,
- an environment,
- or a backend root,

it should reference explicit ids from the capability plane.

The plan artifact should therefore carry fields such as:

- `tool_refs`
- `server_ref`
- `environment_ref`
- `workflow_ref`
- `script_ref`
- `parameter_contract`
- `expected_artifacts`
- `forbidden_shortcuts`

## Execution rule for `L4`

`L4` should execute only what the explicit task contract allows.

If the plan references a missing or unavailable capability card, `L4` should
return a bounded blocker instead of guessing.

`L4` should emit a durable receipt that records:

- what resource ids were actually used,
- what diverged from plan,
- what artifacts were produced,
- what remains unvalidated.

## File layout

Recommended additions:

```text
canonical/
  compiled/
    obsidian_l2/
      README.md
      index.md
      families/...

runtime/
  capabilities/
    registry.json
    tools/
    servers/
    environments/
    workflows/
    status/
    topic_overrides/

topics/<topic_slug>/runtime/
  idea_reuse_context.json
  idea_reuse_context.md
  plan_reuse_context.json
  plan_reuse_context.md
  execution_resource_context.json
  execution_resource_context.md
```

## Relationship to existing repository surfaces

This design should reuse, not replace:

- `canonical/index.jsonl`
- `canonical/edges.jsonl`
- typed canonical family directories
- `canonical/compiled/*`
- `canonical/staging/*`
- `consult-l2`
- `topic_skill_projection.active.*`
- runtime `execution_task.*`
- runtime `validation_review_bundle.active.*`
- run-level `iteration_journal.*`

Specifically:

- `consult-l2` remains the bounded retrieval engine
- the new reuse contexts are derived wrappers around bounded retrieval plus
  topic-linked evidence summaries
- the capability plane becomes the explicit source for execution-resource
  selection
- iteration plans consume the reuse contexts and capability plane instead of
  open-ended prose memory

## Out of scope

This design does not attempt to:

- redesign every canonical unit family in one step
- auto-discover all capabilities with no human oversight
- let compiled or mirror surfaces replace canonical truth
- make capability cards equivalent to runtime status probes
- finish full authoritative `L4 -> L2` promotion in the same phase

## Recommended implementation order

1. Freeze principle and protocol text for global `L2`, capability plane, and
   progressive contexts.
2. Add failing tests for:
   - capability card parsing and materialization,
   - progressive reuse context generation,
   - topic-linked evidence rendering,
   - explicit resource refs in `L3` planning surfaces.
3. Materialize the global Markdown mirror from canonical `L2`.
4. Materialize the runtime capability plane and natural-language intake path.
5. Materialize `idea_reuse_context` and `plan_reuse_context`.
6. Add `execution_resource_context`.
7. Wire the new surfaces into `idea_packet`, iteration planning, runtime
   bundle, and status/replay reads.

## One-line memory

`L2` is global reusable scientific-plus-technical memory; topics read it
progressively through derived reuse contexts, while concrete execution choices
come from a separate explicit runtime capability plane.
