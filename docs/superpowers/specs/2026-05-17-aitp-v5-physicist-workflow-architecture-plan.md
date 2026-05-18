# AITP v5 Physicist Workflow Architecture Plan

Status: planning record

Date: 2026-05-17

Scope: theoretical physics research only

Related prior record:

- `docs/superpowers/specs/2026-05-16-aitp-physicist-collaborator-kernel-design.md`

## Purpose

This document records the current v5 design direction after reviewing the old
AITP architecture and discussing what a more universal theoretical-physics
research collaborator should become.

The goal is not to discard the old AITP. The old system already proves that a
research harness can enforce source grounding, stage gates, L4 validation,
topic state, L2 memory, domain skills, and session continuity. The v5 goal is
to rebuild the foundation around the objects that real physicists reason with:
questions, ideas, claims, physical objects, object relations, evidence,
attempts, failures, tools, checks, human decisions, and reusable memory.

In short:

- old AITP is a strong protocol harness;
- v5 AITP should become a persistent physicist collaborator kernel;
- old enforcement and runtime capabilities must be preserved;
- the conceptual center should move from stage artifacts to claim-centered
  physics understanding.

## Core Position

AITP should not try to replace Codex, Claude Code, OpenCode, or any future
agent. AITP should be the theoretical-physics kernel that gives those agents:

- research state,
- trust boundaries,
- physics-oriented next-action scaffolding,
- tool contracts,
- durable process memory,
- adversarial validation gates,
- and reusable long-term memory.

The LLM performs reasoning, coding, reading, writing, and exploration. AITP
keeps the research disciplined, recoverable, evidence-backed, and auditable.

## Why Rebuild

The old architecture should not simply be patched forever because its center of
gravity is still the stage harness:

- gates often validate artifact shape before claim meaning;
- topic lanes are too coarse for mixed research;
- `aitp_get_execution_brief` can be mechanical rather than physics-shaped;
- code-method work was added later and is not yet first-class around
  formula-code translation;
- L2 contains several generations of graph and entry concepts;
- topic state is too isolated for long-horizon research contexts;
- MCP, CLI, skills, hooks, and adapters have accumulated overlap;
- next-action choice still relies too much on the model's hidden intuition.

The rebuild is justified only if it preserves old strengths while changing the
foundation. The new foundation should make weak models less likely to jump
incorrectly and let strong models spend intelligence on high-level physics
judgment instead of reconstructing missing context.

## Old Capabilities To Preserve

These old AITP capabilities are not optional. They should be migrated or
rebuilt as first-class v5 kernel services:

- legal state transitions and retreat semantics;
- stage and tool permission matrix;
- preflight checks and gate override with audit trail;
- L0 source registration and source roles;
- L1 reading/intake with source refs, convention snapshots, anchor maps, and
  contradiction registers;
- L3 flexible workbench activities and failed idea preservation;
- candidate submission with source/derivation preflight;
- adversarial L4 review with counterargument and physics checks;
- lane-aware validation requirements;
- domain skill injection, especially LibRPA/ABACUS rules;
- compute target state and background HPC job tracking;
- L4 run analysis for computational physics;
- global L2 query, entries, graph, provenance, pitfalls, questions, and bridges;
- session start/resume/stop hooks;
- offline event recording for remote or MCP-unavailable work;
- adapter surfaces for Codex, Claude Code, OpenCode, and future agents;
- notebook/report generation from durable research artifacts;
- migration tooling for existing topics.

## New Core Principles

### 1. Claim-Centered Control

The unit of scientific control is the claim, not the topic or stage.

Each serious claim should record:

- statement;
- scope;
- non-claims;
- assumptions;
- evidence profile;
- confidence state;
- supporting evidence;
- missing evidence;
- strongest failure mode;
- relation to physical objects;
- relation to prior claims and memory;
- human checkpoint triggers.

The topic remains the workbench. The claim is the unit that becomes trusted or
rejected.

### 2. Evidence Profile Per Claim

Do not force an entire topic into a rigid type. Real topics mix modes.

Each claim declares one evidence profile:

- `formal_theory`;
- `toy_numeric`;
- `code_method`;
- `literature_synthesis`;
- `mixed`.

The evidence profile determines required checks and tool recipes. A GW/LibRPA
topic can contain a formal derivation claim, a formula-code translation claim,
a benchmark claim, and a literature synthesis claim at the same time.

### 3. Model Intelligence Equalizer

AITP should reduce the amount of hidden physics judgment required for basic
progress. It should provide enough state and scaffolding that less capable
models can still choose reasonable local next steps.

It should do this by exposing:

- active uncertainty;
- active claim;
- known context;
- failed attempts;
- ranked next-action candidates;
- forbidden actions;
- required checks;
- tool recipes;
- trust status;
- human checkpoint triggers.

Stronger models still matter. Their intelligence should show up in better
questions, better analogies, better route choices, better hidden-assumption
detection, better formula-code mapping, and better failure interpretation.

### 4. Process Memory Is Not Optional

AITP must not only preserve final conclusions. It must preserve how the
research got there.

Process memory should include:

- ideas and why they were tried;
- route choices and alternatives;
- attempts and their outcomes;
- tool runs and provenance;
- failed routes and lessons;
- human steering;
- validation returns;
- reusable pitfalls;
- confidence-state transitions.

This should be enforced by kernel writes, not left to voluntary chat summaries.

### 5. Physics Sense-Making Beyond Checklist Sanity

Sanity checks are not enough. AITP must ask how physical objects relate, why a
result occurs, and why a failure happened.

A pass/fail table is insufficient if it does not record:

- which objects are involved;
- which relation supports the claim;
- which relation is most likely to break;
- what mechanism explains the result;
- what minimal diagnostic could localize the failure.

### 6. Dynamic Questions, Not Fixed Questionnaires

AITP should not make every model answer the same universal question list at
every step. Fixed questions become ritual. The kernel should instead generate
state-conditioned physics questions from the current research state.

The fixed part is the question discipline:

- ask about concrete physical objects;
- ask about relations among those objects;
- ask why a result or failure occurs;
- ask which evidence supports which part of a claim;
- ask what would falsify or weaken the claim;
- ask what tool or observation would reduce the active uncertainty.

The variable part is the actual question text. It should depend on the active
claim, evidence profile, object-relation graph, failed attempts, current flow
profile, available tools, and domain pack.

### 7. Friction Proportional To Epistemic Risk

AITP should not make routine scientific work feel like paperwork. Protocol
weight should scale with uncertainty and risk.

Trusted benchmark recipes, standard workflow executions, convention lookups,
and routine source registrations should run lightly when their preconditions
are satisfied. New physical claims, surprising numerical results, convention
choices, expensive computations, literature contradictions, and L2 promotion
should trigger heavier sense-making, validation, or human checkpoint rules.

This principle prevents two failure modes at the same time:

- underthinking new science;
- overburdening established workflows.

### 8. Subagents As Auditors, Not Co-Owners

Subagents should be used as conditional disagreement mechanisms. They should
not own the research state, silently advance claims, or appear in every routine
step.

Useful auditor roles include:

- referee auditor for claim-level weaknesses;
- derivation auditor for assumptions, definitions, limits, and counterexamples;
- numerical auditor for convergence, tolerance, finite-size effects, and
  benchmark interpretation;
- formula-code auditor for index maps, normalization, conventions, and
  implementation correspondence;
- literature auditor for existing results, contradictions, and missing
  references;
- counterexample auditor for minimal failure cases.

Auditors return critique packets. The main agent remains responsible for
mapping those critiques back to claims, evidence, object relations, failure
modes, and human checkpoints.

## Full Research Workflow

The v5 workflow should be cyclic, not a one-way stage conveyor.

Canonical flow:

```text
research context
  -> intent / question / idea
  -> evidence basis
  -> understanding and translation
  -> object-relation understanding
  -> claim formation
  -> route decision
  -> attempt / tool run
  -> physics sense-making
  -> adversarial validation
  -> human checkpoint
  -> reusable memory and output
  -> new question / new idea / retreat
```

The old `L0 -> L1 -> L3 -> L4 -> L2` remains useful, but it becomes the large
trust flow rather than the complete ontology.

## Epistemic Zones

### 1. Context / Direction Zone

Purpose: define the long-horizon research direction and why a topic matters.

Stores:

- long-term direction;
- topic list;
- user preferences;
- route memory;
- related contexts;
- context-level inbox of questions and ideas;
- memory references.

This zone prevents topics from becoming isolated little universes.

### 2. Intent / Question / Idea Zone

Purpose: capture what the user and AI are trying to do before it hardens into
a claim.

This zone should exist at three levels:

- context-level inbox for pre-topic seeds;
- topic-local workbench for active execution;
- global registry for stable IDs and cross-topic search.

Context-level examples:

- a vague FQHE learning direction;
- a possible GW head-wing implementation concern;
- a broad VNA/generalized-symmetry analogy.

Topic-level files should include:

- `intent/intent.md`;
- `intent/active_focus.md`;
- `intent/question_stack.md`;
- `intent/idea_stack.md`;
- `intent/steering_log.md`;
- `intent/decision_log.md`.

The rule is:

```text
pre-topic seeds live in context inbox;
execution focus lives in topic intent;
stable identity lives in registry.
```

### 3. Evidence Basis Zone

Purpose: collect and classify evidence objects.

Evidence includes:

- papers;
- books;
- lecture notes;
- code repositories and commits;
- code worktrees, branches, local patches, and upstream bases;
- input decks;
- run outputs;
- benchmark references;
- datasets;
- local derivation notes;
- discussion notes;
- trusted tool recipes.

This is the upgraded role of old L0.

### 4. Understanding / Translation Zone

Purpose: turn sources into a usable research model.

Stores:

- definitions;
- assumptions;
- conventions;
- notation translations;
- source-to-claim map;
- source-to-object map;
- contradiction register;
- regime map;
- derivation anchors;
- formula-code map skeleton;
- data-layout map for code-method work.

This is the upgraded role of old L1.

### 5. Object-Relation Zone

Purpose: represent local physics understanding around the active claim.

Nodes may include:

- Hamiltonians;
- Green functions;
- self-energies;
- observables;
- symmetries;
- topological invariants;
- Hilbert spaces;
- operator algebras;
- code arrays;
- file outputs;
- benchmark quantities;
- literature claims.

Relations may include:

- `defines`;
- `derives_from`;
- `approximates`;
- `implements`;
- `limits_to`;
- `determines`;
- `measures`;
- `contradicts`;
- `depends_on`;
- `matches_onto`;
- `is_dual_to`;
- `has_convention`;
- `has_regime`.
- `runs_on_code_state`;
- `modifies_code_path`;
- `differs_from_upstream`;
- `reproduces`;

Every relation should carry evidence. Sanity checks should inspect relations,
not only isolated nodes.

### 6. Route / Decision Zone

Purpose: record why the next action is scientifically reasonable.

Stores:

- candidate routes;
- selected route;
- rejected alternatives;
- information gain;
- cost;
- risk;
- forbidden actions;
- user steering;
- decision provenance.

This zone is critical for model-intelligence equalization.

### 7. Attempt / Run Zone

Purpose: preserve concrete research attempts.

Attempt types:

- derivation attempt;
- literature search;
- source reading pass;
- toy numerical experiment;
- formula-code trace;
- code patch;
- upstream comparison;
- benchmark run;
- HPC validation run;
- failure diagnosis;
- synthesis attempt.

Attempts can fail. Failed attempts are first-class because they often become
pitfall memory.

### 8. Physics Sense-Making Zone

Purpose: explain results and failures.

Stores:

- involved objects;
- relevant object relations;
- dominant mechanism;
- scale argument;
- known limit;
- anomaly;
- failure hypothesis;
- minimal diagnostic;
- reusable pitfall candidate.

This zone upgrades simple "physics sanity checks" into real interpretation.

### 9. Adversarial Validation Zone

Purpose: try to falsify the claim.

Stores:

- validation contract;
- required checks;
- check evidence;
- counterargument;
- falsification condition;
- remaining uncertainty;
- confidence-state update recommendation.

This is the upgraded role of old L4.

### 10. Human Checkpoint Zone

Purpose: record decisions that should not be silently made by the AI.

Triggers:

- direction or novelty fork;
- definition or convention choice;
- benchmark or tolerance choice;
- expensive computation;
- literature contradiction;
- trusted memory conflict;
- promotion to `human_accepted`, `promotable`, or `promoted`.

### 11. Memory Governance Zone

Purpose: decide what becomes reusable long-term knowledge.

This is the upgraded role of old L2.

It should store or govern:

- promoted claims;
- systems;
- methods;
- pitfalls;
- questions;
- formula-code maps;
- benchmarks;
- route memories;
- failure modes;
- provenance and trust scope.

L2 is not abandoned. It becomes the trust-governed memory plane rather than a
catch-all folder for every long-term artifact.

### 12. Output / Communication Zone

Purpose: turn research state into human-facing outputs.

Outputs include:

- notebooks;
- reports;
- paper drafts;
- figures;
- slides;
- claim-to-text maps;
- validation summaries.

Old flow-notebook capability should be preserved and improved.

## Proposed Filesystem Architecture

The root name is intentionally neutral. It should not repeat "theoretical
physics" because AITP already means AI Theoretical Physicist.

Candidate root:

```text
.aitp/
```

Workspace-level layout:

```text
.aitp/
  workspace.md
  contexts/
  topics/
  registry/
  memory/
  tools/
  runtime/
  surfaces/
  schemas/
  migrations/
```

### Contexts

```text
contexts/
  <context_slug>/
    context.md
    dashboard.md
    topics.md
    inbox/
      questions/
      ideas/
      notes/
    route_memory/
    preferences.md
    memory_refs.md
    indexes/
```

Context is the natural home for long-term directions such as:

- FQHE/topological order;
- quantum gravity and von Neumann algebras;
- generalized symmetries;
- GW/LibRPA method development;
- Green function topology;
- long-range spin chains and quantum chaos.

### Topics

```text
topics/
  <topic_slug>/
    topic.md
    dashboard.md
    intent/
      intent.md
      active_focus.md
      question_stack.md
      idea_stack.md
      steering_log.md
      decision_log.md
    evidence/
      sources/
      benchmarks/
      code_refs/
      code_states/
      run_outputs/
      notes/
    understanding/
      definitions.md
      assumptions.md
      conventions.md
      notation_translation.md
      source_to_claim_map.md
      source_to_object_map.md
      contradiction_register.md
      regime_map.md
      derivation_anchors.md
      formula_code_map_skeleton.md
    objects/
      local_objects.md
      relation_graph.md
      formula_code_maps/
    claims/
      active_claim.md
      ledger/
    routes/
      route_options.md
      active_route.md
      decisions/
    attempts/
      derivations/
      readings/
      toy_numerics/
      code_traces/
      code_patches/
      upstream_comparisons/
      benchmarks/
      hpc_runs/
      diagnoses/
    sensemaking/
      reports/
      anomalies/
      failure_analyses/
      pitfalls/
    validation/
      contracts/
      reviews/
      evidence/
      proposals/
    checkpoints/
      active.md
      resolved/
    outputs/
      notebooks/
      reports/
      figures/
      manuscripts/
    runtime/
      event_log.md
      sessions.md
      current_state.json
      health.md
      code_workspaces.md
    indexes/
```

Topic is the workbench. It owns active execution state but should not be the
only identity authority for reusable objects.

### Registry

```text
registry/
  intents/
  questions/
  ideas/
  claims/
  physics_objects/
  object_relations/
  evidence/
  code_states/
  code_workspaces/
  routes/
  attempts/
  tool_recipes/
  tool_runs/
  checkpoints/
  outputs/
```

The registry provides stable IDs and cross-topic indexing. It is not the
primary human reading surface.

### Memory

```text
memory/
  l2/
    entries/
    graph/
    conflicts/
    indexes/
  claims/
  definitions/
  methods/
  systems/
  benchmarks/
  pitfalls/
  failure_modes/
  formula_code_maps/
  code_provenance/
  upstream_snapshots/
  route_memory/
```

The old L2 architecture is retained as the trust-governed core under
`memory/l2/`. Additional memory families make route, benchmark, and
formula-code knowledge explicit.

### Tools

```text
tools/
  recipes/
  trust_cards/
  domain_packs/
  runs/
  adapters/
```

Each trusted tool should have a trust card.

Trust card fields:

- what the tool checks;
- what it cannot check;
- required inputs;
- expected outputs;
- when it is mandatory;
- failure interpretation;
- false-positive risks;
- false-negative risks;
- promotion relevance.

### Runtime

```text
runtime/
  current_topic.md
  active_context.md
  sessions.jsonl
  event_log.jsonl
  background_jobs.jsonl
  health.md
```

Runtime is workspace-level operational state, not scientific memory.

## Core Object Types

### Intent

Represents why work is being initiated.

Required fields:

- intent id;
- origin;
- context;
- topic if assigned;
- user steering;
- desired outcome;
- current ambiguity;
- status.

### Question

Represents an uncertainty that may or may not become a claim.

Required fields:

- question id;
- statement;
- context;
- topic;
- parent intent;
- scope;
- blocking status;
- related ideas;
- related claims;
- evidence needed.

### Idea

Represents a possible route or conceptual move.

Required fields:

- idea id;
- statement;
- motivation;
- status;
- context;
- topic if assigned;
- inspired by;
- supersedes;
- possible claims;
- risks;
- lessons learned.

Statuses:

- `seed`;
- `active`;
- `parked`;
- `succeeded`;
- `failed`;
- `superseded`;
- `abandoned`.

### Claim

Represents the object that can be checked, accepted, rejected, or promoted.

Confidence states:

- `hypothesis`;
- `coherent`;
- `source_anchored`;
- `locally_checked`;
- `stress_tested`;
- `human_accepted`;
- `promotable`;
- `promoted`;
- `rejected`;
- `deferred`.

AI may advance early states when evidence supports it. AI must not enter
`human_accepted`, `promotable`, or `promoted` without checkpoint or gate.

### Physics Object

Represents an entity used in reasoning.

Kinds:

- equation object;
- observable;
- operator;
- Hamiltonian;
- state;
- symmetry;
- invariant;
- approximation;
- code object;
- data object;
- benchmark object;
- literature claim.

### Object Relation

Represents the connection that makes physics intelligible.

Each relation must include:

- from object;
- to object;
- relation type;
- evidence;
- confidence;
- regime;
- likely failure point.

### Route Decision

Represents why AITP chose a next move.

Fields:

- decision id;
- active uncertainty;
- candidate actions;
- selected action;
- reason;
- cost;
- risk;
- expected evidence gain;
- forbidden actions;
- human checkpoint if any.

### Attempt

Represents one concrete research try.

Fields:

- attempt id;
- type;
- goal;
- inputs;
- method;
- outputs;
- result;
- failure mode if any;
- next implication.

### Tool Run

Represents one concrete tool execution or external check.

Fields:

- tool run id;
- tool recipe;
- inputs;
- environment;
- command or API call;
- outputs;
- parsed results;
- trust card;
- claim/evidence links.
- code state id if code-dependent;
- worktree or checkout path if applicable.

### Code State

Represents the exact source-code state used for a claim, run, benchmark, or
formula-code mapping.

Fields:

- code state id;
- repository URL or local repository id;
- upstream remote;
- upstream branch;
- upstream commit;
- local branch;
- worktree path;
- dirty status;
- patch id or diff hash;
- build configuration;
- compiler and dependency versions;
- linked topic, cycle, claim, attempt, and tool run ids;
- known divergence from upstream.

Any code-dependent result without a code state should be treated as
non-reproducible evidence.

### Code Workspace

Represents an isolated workspace used to modify or test a code repository.

Fields:

- workspace id;
- topic id;
- session id;
- repository id;
- worktree path;
- branch name;
- base commit;
- upstream tracking branch;
- purpose;
- write scope;
- active claim or attempt;
- status;
- cleanup or merge plan.

### Sense-Making Report

Represents an explanation, not only a check.

Fields:

- active claim;
- involved objects;
- critical relations;
- dominant mechanism;
- scale or limiting argument;
- anomaly;
- strongest failure hypothesis;
- recommended diagnostic;
- pitfall candidate.

### Validation Contract

Represents required checks for a claim's evidence profile.

The contract is generated from:

- evidence profile;
- claim scope;
- object relations;
- domain packs;
- tool trust cards;
- human steering.

### Human Checkpoint

Represents a required human decision.

Fields:

- checkpoint id;
- trigger;
- question;
- options;
- consequences;
- selected answer;
- resolved at;
- claim or route affected.

## Dynamic Physics Question Engine

AITP should include a question bank, but the bank is not the product. The
product is a state-conditioned question engine that uses the bank as raw
material.

The engine should generate the best current physics questions from:

- active claim or idea;
- active uncertainty;
- evidence profile;
- confidence state;
- physical objects;
- object relations;
- source and literature state;
- failed attempts;
- available tool recipes;
- current flow profile;
- domain pack.

The generated questions should be specific enough to move research state. A
question that can be answered by a generic slogan, or that cannot change a
route, evidence state, claim confidence, object relation, failure hypothesis,
or human checkpoint, should be suppressed.

### Question Quality Criteria

A good generated physics question should:

- point to concrete objects or relations;
- require mechanism, not only judgment;
- ask why a result or failure happens;
- connect evidence to a bounded claim;
- expose at least one plausible failure mode;
- suggest a next observation, derivation, search, benchmark, toy model, or
  code trace;
- fit the current protocol weight.

### Question Output Contract

Generated questions should be structured artifacts, not only chat text.

```yaml
question_id: ""
scene: ""
target_claim: ""
target_objects: []
target_relations: []
target_uncertainty: ""
question: ""
why_this_question: ""
expected_answer_shape: ""
possible_next_actions: []
state_update_if_answered: []
escalation_if_unanswered: ""
```

### Universal Question Families

The following families are reusable generators. They should be triggered and
filtered by state; they should not be asked wholesale.

### Claim Clarity

- What exactly is the active claim?
- What is its scope?
- What does it not claim?
- Which assumptions are load-bearing?
- Where is the claim most likely to fail?

### Evidence

- Which evidence supports this claim?
- Which part of the claim does each evidence item support?
- Which part remains unsupported?
- Is the evidence strong enough for the current confidence state?
- Does evidence support a weaker claim rather than the stated claim?

### Physics Sense-Making

- Which physical objects are involved?
- Which relations among them support the result?
- Which relation is least secure?
- Why is this result expected physically?
- Which term, symmetry, limit, approximation, or mechanism controls the result?
- What would change if a key object or assumption changed?

### Route Choice

- What is the main uncertainty right now?
- What is the cheapest high-information check?
- Should the next move be reading, derivation, toy numerics, code tracing,
  benchmark, literature search, or human checkpoint?
- What is the risk of skipping this move?
- What should not be done yet?

### Failure and Adversarial Review

- What would falsify the claim?
- What is the strongest counterargument?
- Is there an alternative explanation?
- If a check fails, does it point to definition, convention, derivation,
  numerics, code translation, input regime, or tool failure?
- Can this failure become reusable pitfall memory?

### Human Checkpoint

- Is this a taste, direction, or definition decision?
- Is a benchmark, tolerance, or scope choice underdetermined?
- Is the next action expensive or risky?
- Is the claim approaching human acceptance or promotion?
- Does evidence conflict with trusted memory or literature?

## Next-Action Scaffold

Every execution brief should eventually include a next-action scaffold.

Example shape:

```yaml
current_focus:
  active_claim: ""
  confidence_state: ""
  evidence_profile: ""
  main_uncertainty: ""

known_context:
  load_bearing_sources: []
  established_facts: []
  assumptions: []
  previous_failed_attempts: []

next_action_candidates:
  - action: ""
    rank: 1
    why: ""
    required_tools: []
    expected_output: ""
    expected_evidence_gain: ""
    risk_if_skipped: ""

mandatory_reflection:
  - question: ""
    answer_required: true

forbidden_now: []

human_checkpoint:
  needed: false
  reason: null
```

This is the primary mechanism for making weaker models more reliable.

## Flow Profiles And Protocol Weight

Every action should run under a flow profile. The profile controls how much
reflection, validation, tool checking, subagent auditing, and human interaction
is required.

### Autopilot Flow

Use when the workflow is known, trusted, and low uncertainty.

Examples:

- run a standard benchmark recipe inside its documented regime;
- register a source with complete metadata;
- repeat a known calculation with unchanged code and inputs;
- perform a routine convention lookup;
- execute a trusted parsing or report-generation tool.

Required behavior:

- verify recipe preconditions;
- record inputs, versions, and outputs;
- check mandatory invariants and thresholds;
- update run history or evidence state;
- avoid heavy reflection unless an anomaly appears.

Autopilot must not promote new physical claims by itself.

### Guided Flow

Use when the next step is mostly clear, but some physics judgment is still
needed.

Examples:

- choose between a small number of validation checks;
- interpret a mild benchmark deviation;
- trace a formula-code mapping that follows known patterns;
- decide whether a source is relevant enough for deep reading.

Required behavior:

- generate a small set of state-conditioned questions;
- identify the active uncertainty;
- select the cheapest high-information next action;
- record why heavier review is not yet required.

### Research Flow

Use when the work may create or materially change a claim.

Examples:

- propose a new idea;
- derive a nontrivial relation;
- explain an unexpected result;
- connect two literatures;
- introduce a new numerical diagnostic;
- change formula-code interpretation.

Required behavior:

- generate object-relation and mechanism questions;
- record assumptions and non-claims;
- preserve failed attempts;
- update claim confidence only when evidence changes;
- consider at least one falsification route.

### Adversarial Flow

Use when a claim is about to become trusted, exported, or expensive.

Examples:

- L4 validation;
- L2 promotion;
- paper-facing conclusion;
- expensive compute decision;
- literature contradiction;
- benchmark failure;
- surprising result that would change direction.

Required behavior:

- formulate the strongest counterargument;
- check profile-specific validation requirements;
- invoke suitable auditor subagents when useful;
- require human checkpoint for underdetermined taste, definition, tolerance, or
  direction choices;
- record remaining uncertainty explicitly.

### Automatic Escalation Triggers

AITP should automatically move from lighter to heavier profiles when any of the
following occurs:

- benchmark fails or drifts past tolerance;
- tool version, code path, basis, input regime, or convention changes;
- result contradicts trusted memory or literature;
- an action creates a new physical claim;
- a formula-code mapping changes;
- a run becomes expensive or hard to reproduce;
- evidence is being used outside the recipe regime;
- the user asks to trust, summarize, publish, or promote the result.

### Recipe And Trust Card Fast Path

Benchmarks and established workflows should be represented by recipes and trust
cards.

```yaml
recipe_id: ""
purpose: ""
applies_when: []
requires: []
trusted_versions: []
input_contract: {}
mandatory_invariants: []
benchmark_thresholds: []
expected_outputs: []
known_failure_modes: []
escalation_triggers: []
records_to_write: []
```

If a recipe applies and all checks pass, AITP should stay lightweight. If any
precondition or invariant fails, the same artifact should provide the escalation
path into Guided, Research, or Adversarial Flow.

## Subagent Auditor Protocol

Subagents should enter only when they increase epistemic pressure. They are
best used for disagreement, not for routine execution.

Allowed auditor packet shape:

```yaml
auditor_id: ""
role: ""
target_claim: ""
target_attempt: ""
target_tool_run: ""
critique_summary: ""
suspected_failure_modes: []
evidence_used: []
missing_evidence: []
minimal_next_checks: []
severity: ""
confidence: ""
state_updates_recommended: []
```

Rules:

- auditors cannot directly promote, reject, or rewrite claims;
- auditors cannot silently change topic state;
- the main agent must map critiques to claim, evidence, relation, route, or
  failure-mode artifacts;
- routine Autopilot Flow should not call auditors unless an escalation trigger
  fires;
- Adversarial Flow should normally include at least one independent critique
  path, which may be a subagent, tool check, literature contradiction search, or
  human review.

## Code Worktree And Upstream Provenance

Computational-physics and code-method topics often depend on source-code state.
AITP must therefore treat code provenance as part of scientific evidence, not
as developer bookkeeping.

### Core Principle

A code-dependent conclusion is incomplete unless it records:

- which repository was used;
- which upstream remote and commit it derives from;
- which branch or worktree executed the test;
- which local patches were present;
- which build options and dependencies were used;
- which input decks and run outputs belong to that exact code state;
- whether the conclusion is upstream-compatible, patch-specific, or
  version-specific.

Blind reproduction failures should be diagnosable as one of:

- wrong physics assumption;
- wrong input or benchmark regime;
- wrong code version;
- missing local patch;
- different build or dependency environment;
- changed upstream behavior;
- nondeterministic or parallel-execution issue.

### Worktree Strategy

For code repositories such as LibRPA, ABACUS, FHI-aims adapters, or local model
codes, AITP should prefer isolated workspaces for nontrivial modifications.

Recommended binding:

```text
topic/cycle/session -> code workspace -> git worktree -> branch -> code state
```

Rules:

- routine read-only inspection may use an existing clean checkout;
- any code modification for a topic should use a topic/cycle-specific worktree
  or an explicitly declared branch;
- two topics should not silently share the same dirty checkout;
- a session should record which worktree it is allowed to edit;
- a claim should link to the code state that produced its evidence;
- before comparing with others' results, AITP should compare code states, not
  only numerical outputs.

### Code Workspace Layout

The AITP workspace should track code workspaces without owning the code
repositories themselves.

```text
.aitp/
  runtime/
    code_workspaces/
      <workspace_id>.md
  registry/
    code_workspaces/
    code_states/
  memory/
    code_provenance/
    upstream_snapshots/
```

Topic-local records should reference these global records:

```text
topics/<topic_slug>/
  evidence/code_states/
  attempts/code_patches/
  attempts/upstream_comparisons/
  runtime/code_workspaces.md
```

### Code State Contract

```yaml
code_state_id: ""
repo_id: ""
repo_url: ""
upstream_remote: ""
upstream_branch: ""
upstream_commit: ""
local_branch: ""
worktree_path: ""
dirty: false
patch_id: ""
diff_hash: ""
build_config:
  compiler: ""
  flags: []
  dependencies: []
  cmake_options: []
runtime_environment:
  host: ""
  scheduler: ""
  mpi: ""
  omp_threads: ""
linked_records:
  topics: []
  cycles: []
  claims: []
  attempts: []
  tool_runs: []
known_divergence: ""
```

### Upstream Comparison Contract

When a result differs from literature, another collaborator's run, or a known
benchmark, AITP should ask whether the compared results share the same code
state.

```yaml
comparison_id: ""
target_claim: ""
reference_result: ""
reference_code_state: ""
local_code_state: ""
shared_upstream_base: ""
local_only_patches: []
upstream_delta_summary: ""
input_delta_summary: ""
build_delta_summary: ""
result_delta_summary: ""
most_likely_delta_source: ""
next_diagnostic: ""
```

### Escalation Rules

Autopilot code workflows should escalate when:

- the checkout is dirty but no patch id is recorded;
- the code state differs from a trusted recipe;
- upstream has moved since the benchmark was recorded;
- local patches touch formula-code mapped files;
- build flags or dependencies differ from the reference;
- parallel settings, MPI layout, or OMP threads differ for a sensitive run;
- a reproduction attempt lacks the reference code state.

### User-Facing Behavior

AITP should not force the user to read git metadata every time. It should
surface it only where it matters:

- before running a trusted benchmark;
- before modifying source code;
- when recording a code-dependent claim;
- when comparing against another result;
- when reproduction fails;
- before promoting code-method evidence to reusable memory.

The user-facing message should answer: "Are we testing physics, testing a patch,
or testing a different code version?"

## Evidence Profiles And Default Playbooks

### Formal Theory

Default checks:

- definition lock;
- assumption audit;
- derivation trace;
- known example;
- limiting case;
- symmetry or covariance;
- counterexample search;
- literature equivalence or contradiction;
- object-relation consistency.

### Toy Numeric

Default checks:

- model Hamiltonian statement;
- observable definition;
- exact or semi-exact limit;
- finite-size trend;
- convergence or sampling check;
- random seed and environment provenance;
- negative comparator;
- figure/table provenance.

### Code Method

Default checks:

- code state contract;
- worktree or clean-checkout binding;
- upstream commit and local patch audit;
- formula-code map;
- unit and convention audit;
- index and data-layout audit;
- parser/input-output boundary map;
- minimal reproducible case;
- smoke test;
- benchmark comparison;
- convergence/error budget;
- parallel consistency;
- source commit and runtime provenance.
- upstream comparison when reproducing external results.

### Literature Synthesis

Default checks:

- source role classification;
- claim-source map;
- notation translation;
- regime comparison;
- cross-source contradiction;
- original-source priority;
- unresolved claim register.

### Mixed

The mixed profile combines claim-local checks from multiple profiles. It must
not become an excuse to skip checks.

## L2 Role In v5

The old L2 is not abandoned.

The new interpretation:

```text
L2 = trust-governed reusable memory plane
```

L2 should not store all process history. Process history belongs in event logs,
attempts, tool runs, decisions, and validation records.

L2 should store or govern knowledge that is reusable beyond the immediate
session:

- verified or scoped claims;
- definitions;
- systems;
- methods;
- pitfalls;
- open questions;
- benchmark memories;
- route memories;
- formula-code maps;
- object relations with stable relevance;
- conflicts and contradiction resolutions.

Promotion to L2 requires:

- claim statement;
- scope and regime;
- evidence profile;
- evidence bundle;
- validation result;
- non-claims;
- known failure modes;
- provenance;
- trust status;
- human checkpoint if required.

## Relationship To Topic

Topic is a workbench, not the only place where ideas exist.

Rules:

- pre-topic ideas and questions live in context inbox;
- active research focus lives in topic intent;
- stable identities live in registry;
- trusted reusable knowledge lives in memory/L2;
- process details live in attempts, runs, and logs;
- outputs live in topic outputs and may reference promoted memory.

This keeps early ideas from cluttering topic execution while preventing global
idea pools from becoming unreadable.

## Migration From Old AITP

The v5 system must include an importer for existing topics.

Mapping:

- old `state.md` -> topic runtime state and topic metadata;
- old `L0/sources` -> evidence source objects;
- old `L0/source_registry.md` -> evidence basis summary;
- old `L1/question_contract.md` -> topic intent and question stack;
- old `L1/source_basis.md` -> evidence/source role map;
- old `L1/convention_snapshot.md` -> understanding/conventions;
- old `L1/derivation_anchor_map.md` -> understanding/derivation anchors;
- old `L1/contradiction_register.md` -> understanding/contradiction register;
- old `L1/intake` -> source intake records and source-to-object candidates;
- old `L3/ideate` and `L3/ideas` -> idea stack and registry ideas;
- old `L3/candidates` -> claim ledger;
- old `L2/graph/steps` -> derivation attempts and object relations;
- old `L4/reviews` -> validation reviews;
- old `L4/outputs` -> evidence/run outputs;
- old `runtime/log.md` -> event log;
- old global `L2/entries` -> memory/L2 entries.

The importer should preserve old file paths as provenance.

## External Pattern To Absorb: Planning With Files

Reference:

- WeChat article: <https://mp.weixin.qq.com/s/hSUuFfu8rbkfB88D18i8uQ>
- Observed title: `Planning with Files: let AI do projects steadily like a senior engineer`

The useful external pattern is simple: keep plan, findings, progress, pitfalls,
and results in local files so the agent has external working memory across a
project.

AITP should absorb this as a friendly workflow shell, not as a replacement for
the typed protocol kernel.

Mapping:

- `task_plan.md` -> routes, active route, next-action scaffold,
  implementation plans;
- `findings.md` -> evidence records, claim ledger, source maps,
  sense-making reports;
- `progress.md` -> attempts, tool runs, event log, session log;
- pitfalls / lessons -> failure analyses, reusable pitfalls, route memory;
- results -> validation evidence, outputs, promoted memory candidates.

Design requirements:

- AITP may expose human-facing derived files such as `task_plan.md`,
  `findings.md`, and `progress.md`.
- The truth source remains typed records: claims, evidence, object relations,
  attempts, tool runs, routes, checkpoints, code states, and memory entries.
- Summary files must be regenerable or traceable to typed records.
- Editing a summary file must not update confidence, validation, evidence, or
  promotion state.
- Planning-with-files is useful for low-risk work and session continuity, but
  must escalate on new claims, formula-to-code mapping changes, benchmark
  anomalies, code-state divergence, literature contradictions, and promotion
  decisions.

Implementation implications:

- Provide a `workspace-summary` or `session-summary` generator that writes
  compact plan/findings/progress views from kernel state.
- Each generated summary frontmatter must include
  `derived_from: kernel_state`, `truth_source: false`, and
  `orientation_only: true`.
- The first implementation surface is `brain/v5/summaries.py` plus CLI command
  `aitp-v5 summary session <session-id>` and MCP wrapper
  `aitp_v5_write_session_summary`.
- Summary orientation has its own public read surface:
  `aitp-v5 summary orientation <session-id>` and
  `aitp_v5_read_summary_orientation`, both contract-validated as
  orientation-only.
- The adapter entry surface is `brain/v5/adapters.py` plus CLI command
  `aitp-v5 adapter packet <runtime> <session-id>` and MCP wrapper
  `aitp_v5_get_adapter_packet`.
- The adapter registry surface should also be directly inspectable through
  `aitp-v5 adapter registry` and `aitp_v5_get_adapter_protocol_registry`, without
  creating workspace state.
- Direct adapter registry inspect responses should pass the same public registry
  contract validator before CLI/MCP wrappers return them.
- Execution brief and summary orientation read surfaces should also pass their
  public contract validators before CLI/MCP wrappers return them.
- Session-summary write results should pass a public bundle contract before
  CLI/MCP wrappers return them, preserving `truth_source: false` and
  `orientation_only: true`.
- Public runtime-facing surfaces should route through a shared helper, so CLI
  and MCP wrappers cannot drift by importing different individual validators.
- Adapter registry metadata should expose the public surface contract names, so
  runtimes can see which payload surfaces must pass contract validation.
- Adapter registry metadata should also expose the stable public surface
  validator reference, so runtimes know which helper enforces that contract set.
- Public surface contracts should have a direct audit payload through
  `describe_public_surfaces`, `aitp-v5 adapter public-surfaces`, and
  `aitp_v5_describe_public_surfaces`.
- Adapter packets should embed that public-surface audit payload, so runtimes
  can inspect contract coverage without a second call and the packet contract
  can reject tampered audit metadata.
- Adapter packets should also embed canonical `runtime_entrypoints`, mapping
  public surfaces and trust-changing operations to their CLI/MCP entrypoints,
  so runtimes can call the kernel without guessing command names.
- Runtime entrypoint surfaces should close over the public-surface contract set
  plus the audit payload itself, preventing adapter entrypoint drift as new
  surfaces are added.
- Runtime entrypoint declarations should also be self-validating: advertised
  MCP wrappers must exist and advertised CLI templates must parse, so adapters
  do not receive stale command names.
- Adapter packet validation should call that runtime-entrypoint validator, not
  only compare against the canonical mapping, so stale canonical entrypoint
  declarations are rejected before reaching an agent runtime.
- Add tests proving summaries do not become independent truth sources when
  they disagree with typed records.
- Codex, Claude Code, OpenCode, and future adapters may read compact views for
  orientation, but must call kernel/CLI/MCP before any trust-changing update.
- Adapter packets must expose `truth_sources = [typed_records,
  execution_brief]`, runtime rules, and an explicit list of trust-changing
  actions requiring kernel calls.
- Adapter packets are public runtime interface payloads and must pass a
  contract validator before CLI/MCP/adapters return them.
- Hook/policy enforcement must hard-block trust-changing actions sourced from
  derived summaries. This includes confidence changes, evidence/tool-run
  recording, validation, and L2 promotion when the cited basis is only
  `task_plan.md`, `findings.md`, or `progress.md`.
- Trust-changing updates should enter through a typed `TrustUpdateRequest`
  preflight surface before mutation, so adapters can cite evidence refs, code
  state ids, and source kind while keeping summary files orientation-only.
- The preflight payload is a public adapter/MCP/CLI contract and should be
  contract-validated before wrappers return it.
- Adapter packets should name `aitp_v5_preflight_trust_update` as a mandatory
  kernel entrypoint so runtimes have an explicit path for trust-changing action
  preflight.
- Confidence-state mutation should use a controlled `trust apply
  change_claim_confidence` path that reuses preflight and updates typed claim
  records, never derived summary files.
- `trust apply` responses are public CLI/MCP payloads and should be contract
  validated just like preflight responses.
- Adapter packets should name both `aitp_v5_preflight_trust_update` and
  `aitp_v5_apply_trust_update`, so runtimes see the complete trust mutation
  path.
- Adapter packets should also expose a structured `trust_mutation_entrypoints`
  map, e.g. `change_claim_confidence -> preflight/apply`, so runtimes do not
  infer mutation sequencing from a flat entrypoint list.
- Adapter packets should expose a structured `runtime_trust_update_protocol`
  that spells out `refresh brief -> preflight -> apply -> refresh brief ->
  write summary`, while marking summaries as untrusted inputs for mutation.
- Adapter packets should expose structured `runtime_record_protocols` for
  evidence and tool-run recording, naming required typed refs and accepted link
  fields so summaries cannot silently become provenance.
- Adapter packets should expose structured `runtime_gate_protocols` for
  validation and L2 promotion, including required typed refs, allowed state
  sources, and human-checkpoint boundaries.
- Adapter protocol definitions should live in a shared registry/builder so
  packet generation and contract validation cannot drift apart.
- Adapter packets should include registry metadata naming the protocol source
  module and version, making runtime-facing harness assumptions auditable.
- Adapter registry metadata should list the protocol fields it governs, so
  runtimes and contract validators share the same boundary of responsibility.
- Contract validators should verify that every registry-governed protocol field
  named by the shared registry is present in the adapter packet.
- Adapter registry metadata should expose a stable fingerprint of the governed
  protocol payload, so runtimes can audit which exact harness contract they saw.
- Contract validators should recompute the adapter protocol fingerprint from
  the packet's actual protocol fields, not only compare registry metadata.
- Adapter registry metadata should name the fingerprint algorithm, so runtimes
  do not need to infer how to reproduce or audit the protocol hash.
- Adapter registry metadata should list the fingerprint input fields so runtimes
  can reproduce the hash boundary exactly.

## Implementation Plan Direction

This is not the detailed code implementation plan. It is the architecture
record that the implementation plan should follow.

### Implementation Boundary Rule

The v5 kernel must avoid recreating the old large-file failure mode. Public
facade modules may preserve stable import paths for CLI/MCP/adapters, but the
actual protocol logic should live in focused modules such as adapter contracts,
trust contracts, summary contracts, risk contracts, and migration bridges.

Add regression tests for source-module size. When a module crosses the soft
limit, split by protocol responsibility instead of adding more special cases.

Suggested phases:

### Phase 0: Compatibility Audit

Freeze the old capability inventory and write regression cases for:

- stage gates;
- candidate submission;
- L4 review;
- L2 query;
- background jobs;
- session resume;
- LibRPA domain checks.

### Phase 1: v5 Schema And Filesystem Kernel

Implement:

- root workspace layout;
- context/topic/registry/memory/runtime path helpers;
- object schemas for intent, question, idea, claim, evidence, relation, route,
  attempt, tool run, code state, code workspace, validation, and checkpoint;
- migration-safe IDs.

### Phase 2: State Observer And Next-Action Scaffold

Implement:

- state observer;
- active focus resolver;
- evidence profile resolver;
- flow profile resolver;
- dynamic physics question engine;
- next-action candidate generator;
- forbidden-action generator;
- mandatory reflection selector.

### Phase 3: Claim Ledger And Object-Relation Graph

Implement:

- claim lifecycle;
- confidence-state transitions;
- object registry;
- relation graph;
- relation evidence;
- local sense-making reports.

### Phase 4: Tool Layer And Trust Cards

Implement:

- tool recipe registry;
- trust card schema;
- recipe fast-path execution;
- escalation trigger evaluation;
- tool run records;
- code state and worktree binding records;
- upstream comparison records;
- mandatory tool selection by evidence profile;
- LibRPA/ABACUS domain pack migration.

### Phase 5: Validation And Human Checkpoints

Implement:

- validation contract builder;
- profile-specific L4 checks;
- subagent auditor packet schema;
- auditor-to-state mapping rules;
- checkpoint manager;
- promotion gate;
- L4 return payload to route/attempt/sense-making zones.

### Phase 6: Memory/L2 Governance

Implement:

- memory/L2 entries;
- old L2 importer;
- promotion packet;
- provenance query;
- cross-topic bridge search;
- pitfall and route memory surfaces.
- code provenance and upstream snapshot memory.

### Phase 7: Runtime, Adapters, And Outputs

Implement:

- session start/resume/stop;
- current topic/context;
- event log;
- background jobs;
- Codex/Claude/OpenCode adapters;
- notebook/report generation.

### Phase 8: Real Workflow Acceptance Tests

Run end-to-end tests on real-style workflows:

- FQHE from zero learning to idea to toy numerical check;
- GW/LibRPA formula-code translation and benchmark validation;
- quantum gravity/von Neumann algebra formal definition and derivation;
- Green function topology literature synthesis plus toy check;
- long-range spin-chain numerical model benchmark;
- AITP protocol design topic using AITP itself.

## Acceptance Criteria

v5 is successful when a user can ask:

- what are we doing now;
- why is this the next move;
- what claim is active;
- what evidence supports it;
- what is still uncertain;
- what physical objects and relations matter;
- why did this result occur;
- why might it be wrong;
- what has failed before;
- which code state produced this result;
- whether this reproduction uses the same upstream base and patches;
- which questions are worth asking now;
- why this step is light or heavy;
- whether this is a trusted recipe or new science;
- what tool should be used next;
- when an auditor or subagent should challenge the work;
- when do you need my judgment;
- what can be promoted to reusable memory;
- what should not be trusted yet.

The system should answer from durable state, not from chat memory.

## Non-Goals

v5 should not:

- become a general all-science framework;
- force users to choose rigid topic types;
- store every rough thought in trusted memory;
- replace human taste and judgment;
- treat tool output as automatic truth;
- hide trust boundaries behind fluent prose;
- abandon old topics;
- discard old L2;
- reduce physics reasoning to checklist completion.

## Final Design Summary

The v5 AITP architecture should be:

```text
L0-L4/L2 as the large trust flow;
context/topic as the human research organization;
registry as stable object identity;
claim as the scientific control unit;
object relations as local physics understanding;
attempts and runs as process memory;
code states and worktrees as reproducibility boundaries;
dynamic physics questions as the thinking driver;
flow profiles as the friction controller;
tool recipes and trust cards as operational physics checks;
auditors as conditional disagreement mechanisms;
human checkpoints as epistemic boundaries;
memory/L2 as trust-governed reusable knowledge.
```

The guiding principle:

```text
AITP should not merely ask whether a claim passed a check.
It should know what the claim means, what objects support it, why the result
appears, where it could break, what evidence exists, when to move lightly,
when to challenge itself, and what a useful physicist would do next.
```
