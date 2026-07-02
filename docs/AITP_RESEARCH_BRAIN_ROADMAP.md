# AITP Research Brain Roadmap

This roadmap turns the current positioning into an implementation sequence.
AITP should become an AI-facing research memory layer: a typed research graph
kernel, a task-aware context compiler, domain experience packs, and a literature
knowledge substrate. The goal is not to make AITP a larger prompt. The goal is
to make prior scientific work, source grounding, method experience, failed
routes, validation state, and trust boundaries callable by agents.

## Current Diagnosis

The v5 kernel already has the correct bottom layer. Typed records cover claims,
evidence, source assets, reference locations, physics objects, object relations,
code states, tool recipes, tool runs, artifacts, validation contracts,
validation results, checkpoints, trust updates, and memory entries. This should
remain the source of truth.

The context compiler exists but is still mostly generic. `context_pack.py`
creates bounded orientation-only packs. `brief.py` already combines active
claim, risk, evidence coverage, domain packs, knowledge connectors, strategy
memory, memory entries, proof obligations, and next actions. It now needs
task-shaped compilation profiles.

Domain packs exist but started as safe tool recommendation tables. They need to
become actual experience packs: workflow graphs, failure taxonomies,
final-vs-diagnostic lane policies, artifact schemas, HPC interpretation rules,
skill refs, and validation recipes.

The literature and RAG layer has the right trust boundary. Curated RAG retrieval
is heuristic context and cannot update evidence, validation, or claim trust. The
remaining work is to make the entrypoints and domain connector model feel like a
real literature substrate for QFT, quantum gravity, LibRPA, and other domains.

## Architecture Target

```text
Domain skills and literature connectors
        |
        v
Task-aware context compiler
        |
        v
Typed research graph kernel
        |
        v
Evidence, validation, checkpoint, trust, and memory gates
```

The kernel stays conservative. Domain packs and connectors may suggest what to
load, inspect, run, or verify. They do not become evidence or trusted memory.

## Workstream A: Domain Pack v2

Objective: turn domain packs from tool suggestion lists into experience packs.

Required surfaces:

- `workflow_graph`: route stages, required records, and stage gates.
- `failure_taxonomy`: named failure modes, signals, review basis, and followup
  records.
- `lane_policy`: final-vs-diagnostic rules and forbidden promotions.
- `artifact_schema`: required/recommended artifact roles and hash expectations.
- `hpc_interpretation`: scheduler/runtime state rules for numerical work.
- `skill_refs` and `manifest_refs`: external skill bundle and domain manifest
  references.
- `context_profile_refs`: task-shaped context profiles that should be compiled
  for this domain.

First implemented target:

- `gw_librpa` becomes the reference Domain Pack v2 example.
- `domain_pack_catalog` now exposes built-in packs and claim-text suggestions
  through `aitp-v5 domain-pack catalog/suggest` and MCP wrappers.

Next implementation slices:

1. Add `formal_theory` failure taxonomy and derivation-check workflow.
2. Add QFT/QG domain packs once literature connectors and source
   reconstruction examples are in place.
3. Add project-scope external skill shim generation so hosts can discover
   domain skill bundles without copying their contents into AITP core.

## Workstream B: Literature Knowledge Substrate v1

Objective: make local PDFs, notes, and curated corpora callable without turning
retrieval into evidence.

Required surfaces:

- `source_asset` for PDF or note identity and local blob capture.
- `curated_rag` catalog, search, chunk, ingest, and promotion draft.
- `knowledge_connector_catalog` with domain-specific connector descriptors.
- Exact `reference_location` records for page, section, equation, figure, URL,
  or local-note anchors.
- Source reconstruction and comparison surfaces before claim support or memory
  promotion.

First implemented targets:

- Top-level `aitp-v5 curated-rag catalog/search/chunk/promotion-draft` aliases
  alongside the existing adapter commands.
- Built-in connector descriptors for generic IMA notes, QFT literature,
  quantum-gravity literature, and LibRPA research notes.

Next implementation slices:

1. Add file-backed connector configuration so each workspace can bind QFT/QG
   corpora to local folders.
2. Add paper-learning context profiles that request source assets and exact
   reference locations before synthesis.
3. Add source extraction helpers for concept, notation, equation, and object
   relation candidates.
4. Add paired-paper and multi-paper reading route surfaces that preserve
   conflict, dependency, and scope boundaries.

## Workstream C: Context Compiler v2

Objective: compile context by task type, not just by "current session".

Required task profiles:

- `librpa_run_continuation`
- `paper_learning`
- `derivation_check`
- `source_reconstruction`
- `group_meeting_report`
- `closeout`

Each profile must expose:

- what sections to include;
- what the agent can safely say;
- what the agent cannot say yet;
- what must be verified before trust or promotion;
- which reusable experience patterns apply;
- which read-only surfaces should be expanded.

First implemented target:

- Execution briefs now expose `known_context.context_compilation_profiles`.
- `aitp-v5 status context-pack` and `aitp_v5_get_context_pack` accept an
  explicit task profile and render profile-specific can-say/cannot-say/must
  verify boundaries.

Next implementation slices:

1. Add profile-specific closeout and report templates.
2. Add tests that verify every profile preserves orientation-only and trust
   boundaries.

## Workstream D: Lane Exemplars And Scientific Examples

Objective: clear the vNext exemplar backlog with real examples instead of
abstract policies.

Priority examples:

- `code_backed_algorithm`: LibRPA/GW or QSGW method development.
- `semi_formal_theory`: QFT/QG derivation or source reconstruction.
- `toy_numeric`: small numerical model with finite-size/negative-control
  evidence.

Each exemplar should include:

- active claim;
- domain pack or connector;
- source stack;
- artifact/tool-run/validation records;
- failure modes;
- can-say/cannot-say boundary;
- promotion status and blocked conditions.

## Implementation Discipline

- Do not add new record families unless an existing family cannot represent the
  durable state.
- Prefer richer domain/context metadata before expanding the kernel.
- Keep all RAG, connector, skill, dashboard, and summary surfaces
  orientation-only.
- Use typed records for durable outcomes.
- Treat external skills as procedural memory, not truth.
- Keep domain isolation: LibRPA, QFT, quantum gravity, and topological order
  should not contaminate each other without an explicit bridge.

## Completion Criteria

AITP starts to resemble a research brain when an agent can enter a topic and
answer:

1. What is the active claim or research focus?
2. Which sources, formulas, code states, runs, and artifacts support it?
3. Which domain experience should be loaded?
4. Which failure modes matter here?
5. Which context profile fits the current task?
6. What can be said, what cannot be said, and what must be verified?
7. What should be recorded next?
8. What is eligible for long-term memory, and what is explicitly not eligible?
