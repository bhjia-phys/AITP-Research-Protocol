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
- `formal_theory` now carries a derivation-focused workflow graph, failure
  taxonomy, lane policy, artifact schema, and context profile refs.
- `qft_literature` and `quantum_gravity_literature` now carry source-grounded
  reading workflows, convention/scope failure taxonomies, literature lane
  policies, extraction artifact schemas, connector/skill refs, and context
  profile refs.
- `domain_pack_catalog` now exposes built-in packs and claim-text suggestions
  through `aitp-v5 domain-pack catalog/suggest` and MCP wrappers.
- `domain_skill_shim_manifest` now previews or explicitly writes
  project-local external skill `SKILL.md` shims through
  `aitp-v5 domain-pack skill-shims` and
  `aitp_v5_build_domain_skill_shim_manifest`. These shims copy no external
  skill content and remain orientation-only.

Next implementation slices:

1. Add a domain-pack authoring path for user-defined skills and connector
   bindings once the project-scope shim is stable.
2. Add recording-navigation recipes that map common skill outputs into typed
   AITP write surfaces.

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
- Workspace-local connector bindings now let a project attach QFT/QG/LibRPA
  corpora or note roots through `aitp-v5 knowledge bind/bindings` and MCP
  wrappers without reading content or creating evidence.
- `literature_source_extraction_candidates` now exposes a read-only
  concept/notation/equation-anchor/object-relation/proof-gap extraction
  planning surface through `aitp-v5 literature source-extraction`, MCP, public
  surface contracts, and the runtime bridge manifest.
- `literature_reading_route` now compiles single-paper, paired-paper, and
  multi-paper reading routes through CLI, MCP, public surface contracts, and
  the runtime bridge manifest. It requires source assets, exact reference
  locations, per-source extraction reports, reconstruction review, and
  comparison boundaries before synthesis, evidence, validation, or trust work.
- `literature_source_set_readiness` now audits source sets before synthesis,
  showing which papers still lack canonical source identity, exact anchors,
  typed extraction traces, or source reconstruction review through CLI, MCP,
  public surface contracts, and the runtime bridge manifest.
- `literature_extraction_report` now summarizes existing typed extraction
  records by profile (`paper_learning`, `paired_paper_learning`,
  `multi_paper_learning_route`, QFT/QG/LibRPA literature profiles) through CLI,
  MCP, public surface contracts, and the runtime bridge manifest. It only reads
  typed records and cannot promote extraction reports into evidence,
  validation, final gates, or trust updates.
- `literature_corpus_extraction_artifact` now drafts corpus-backed extraction
  artifacts by aligning curated RAG chunks to typed exact reference locations.
  The artifact draft is read-only, creates no artifact/evidence/validation
  records, and keeps retrieval as heuristic context until ordinary source,
  evidence, validation, and trust-preflight records exist.

Next implementation slices:

1. Use Workstream C task-profile templates to render concrete context packs,
   group-meeting drafts, and closeout drafts from live typed records.
2. Start Workstream D lane exemplars with a LibRPA/GW code-backed algorithm
   example and a QFT/QG source-reconstruction example.

## Workstream C: Context Compiler v2

Objective: compile context by task type, not just by "current session".

Required task profiles:

- `librpa_run_continuation`
- `paper_learning`
- `paired_paper_learning`
- `multi_paper_learning_route`
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
- `context_profile_template_catalog` now exposes profile-specific report and
  closeout templates for all required task profiles through CLI, MCP, public
  surface contracts, and the runtime bridge manifest.
- `aitp_context_pack` now includes compact `profile_template_hint` metadata
  when a task profile is selected, so turn-input context carries output shape,
  section ids, must-verify checks, read-only expansion surfaces, and forbidden
  uses without embedding the full template or creating evidence.
- Tests verify that every context profile template remains read-only,
  orientation-only, cannot create evidence/validation/source-support results,
  and cannot update claim trust.

Next implementation slices:

1. Add read-only materializers for group-meeting and closeout drafts that fill
   those templates from typed records without turning drafts into evidence.
2. Add a LibRPA/GW code-backed algorithm exemplar that uses the context
   compiler, domain pack, lane contract, tool-run, and validation surfaces
   together.

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
