---
title: AITP Final Research Operating Memory Architecture
date: 2026-07-10
status: approved-for-roadmap
scope: AITP v5 kernel, context, lifecycle, execution, knowledge, insight, skills, and host integration
---

# AITP Final Research Operating Memory Architecture

## 1. Executive Decision

AITP will become a research operating memory system for real theoretical-physics
work. It is not a transcript logger, an autonomous physicist, a generic note
application, or a second agent runtime.

The final system has one canonical typed Research Graph Kernel and three derived
or controlled planes around it:

1. a query and context plane that retrieves bounded, coverage-declared context;
2. a research lifecycle control plane that detects durable moments and applies
   tiered write policies;
3. a procedure plane that compiles reviewed, reproducible workflows into skills.

Physics knowledge, speculative insight, execution provenance, and skill metadata
are logical subdomains of the same kernel. RAG indexes, summaries, context packs,
resume cards, dashboards, and host shims are disposable projections. They never
become a second truth source.

## 2. User Outcome

During condensed-matter computation, LibRPA development, formal theory, quantum
gravity literature work, or the adoption of new software, AITP should:

- recover the relevant topic, current focus, prior results, failed routes, open
  obligations, applicable skills, and exact expansion paths at the first useful
  research turn;
- stay quiet during ordinary work;
- automatically capture objective process facts such as source acquisition,
  code state, tool runs, scheduler snapshots, artifacts, and retrieval audits;
- generate reviewable candidates for physics concepts, formula-code mappings,
  derivation structure, interpretations, analogies, and speculative insights;
- require explicit gates for scientific promotion, cross-topic transfer,
  claim-trust changes, and skill installation;
- close a session with a resumable process record and a coalesced review batch;
- compile repeated validated workflows into versioned, project-owned skills;
- expose only the smallest useful context and the most applicable skill at the
  next turn.

The user should spend time doing physics, not maintaining AITP.

## 3. Current Baseline And Why Re-Baselining Is Required

The current v5 implementation already contains the correct building blocks:

- typed claims, evidence, artifacts, sources, code states, tool recipes and runs,
  validation records, checkpoints, promotion packets, and L2 memory;
- physics objects, object relations, proof obligations, exploratory records, and
  sensemaking reports;
- relation maps, process graphs, timelines, objective graphs, context profiles,
  recording navigation, closeout completeness audits, and a compact Codex facade;
- literature intake, source extraction candidates, source reconstruction,
  comparison drafts, knowledge connector descriptors, and a curated RAG shelf;
- domain packs and external skill discovery shims;
- HPC runs, monitor snapshots, lane policies, and real LibRPA/QSGW records.

The implementation is not yet a closed research-memory system:

- the real store already has thousands of records, but common context builders
  repeatedly scan and parse the whole Markdown store;
- the record store can overwrite an existing path and tolerant reads silently
  omit malformed records;
- registry-family knowledge is duplicated across paths, record refs, lifecycle,
  inventory, timeline, recording, process graph, and public surfaces;
- model records have no universal schema version, creation actor, revision, or
  content hash;
- the compact entry path is too slow for automatic turn integration;
- the keyword hook can inject every topic MEMORY.md and bypass focus, coverage,
  and token budgets;
- current curated RAG is a useful trust-neutral lexical fixture, not a production
  knowledge compiler;
- physics semantic fragments are still mixed into research distillation, even
  though conceptual knowledge is not a skill;
- the existing NiO harness-feedback implementation is a valuable exemplar but
  is hard-coded and too specific for final runtime use;
- architecture tests already report oversized modules and the full test suite is
  too slow for one undifferentiated CI lane.

Therefore lifecycle, multi-topic, knowledge, and skill work must be preceded by
a data, query, and architecture foundation gate.

## 4. Non-Negotiable Invariants

### 4.1 One Canonical Truth Kernel

- Canonical scientific and process state is stored as typed records under the
  AITP workspace.
- Canonical records remain Markdown plus YAML frontmatter unless a future
  contract migration explicitly changes that rule.
- Derived indexes may use optimized disposable formats behind an interface, but
  deletion of an index must never delete or change canonical records.
- No summary, RAG chunk, context pack, skill file, host hook, or dashboard is a
  source of scientific truth.

### 4.2 Trust Is Non-Transitive

- Retrieval relevance is not evidence.
- A grounded knowledge node is not claim support by itself.
- A reviewed insight is not evidence.
- A successful tool run is not physics evidence until the relevant validation
  and evidence contracts are satisfied.
- A skill is procedural guidance, not evidence.
- Cross-topic relations may transfer workflow orientation, never claim trust.

### 4.3 Human Gates Are Narrow But Strong

- Objective process capture may be automatic.
- Semantic extraction may be automatic only into candidate state.
- Canonical grounded-knowledge promotion is batch reviewed.
- Speculative-insight retention is batch reviewed.
- Claim-trust mutation and L2 promotion use existing typed preflight and human
  checkpoint paths.
- Skill creation may be drafted automatically; installation, replacement, or
  overwrite requires a typed human checkpoint bound to a content hash and diff.

### 4.4 Context Is Bounded And Auditable

- Startup context is orientation-only and small.
- Every retrieval result declares scope, checked families, excluded scope,
  truncation, stale-index state, and read errors.
- "No prior result" is forbidden when relevant families were unreadable, the
  index is stale, or the search was partial.
- Exact typed-record expansion is always available.

### 4.5 AITP Stays Out Of The Way

- Ordinary exploratory conversation is not recorded as canonical physics.
- Low-value tool calls and filesystem listings are not written as research
  records.
- Review prompts are coalesced at natural milestones instead of emitted for
  every event.
- AITP engineering and harness feedback do not dominate scientific topic state.

## 5. Architecture Planes

```text
Host agent or research runtime
          |
          v
Research Turn Orchestrator
  |                     |
  v                     v
Context Query Planner   Research Moment Controller
  |                     |
  v                     v
Context Compiler        auto capture / candidate / checkpoint / block
          \             /
           v           v
        Research Graph Kernel
  +---------------------------------------------------+
  | research state and trust                         |
  | physics knowledge and derivations                |
  | speculative insight and open questions           |
  | execution provenance and validated baselines     |
  | workflow and skill metadata                      |
  +---------------------------------------------------+
       |                 |                 |
       v                 v                 v
 derived indexes     source corpora     reviewed skill packages
```

The planes are logical boundaries. They do not require separate services.

## 6. Kernel Foundation

### 6.1 RecordEnvelope

Every canonical v5 record will expose a common envelope, directly or through a
compatibility adapter:

```yaml
record_id: <stable id>
record_family: <registered family>
schema_version: <family schema version>
created_at: <UTC timestamp>
created_by:
  actor_type: human | model | tool | migration
  actor_id: <stable local identity>
  host: codex | claude | kimi | opencode | cli | migration
session_id: <optional session>
topic_id: <optional primary topic>
program_id: <optional research program>
scope_refs: []
source_record_refs: []
content_hash: <canonical payload hash>
revision: 1
lifecycle_status: active
supersedes: []
trust_effect: none | candidate_only | trust_path_input
```

`orientation_only` is a property of a derived read surface. A persistent
closeout, candidate batch, or recall audit is a real kernel process record with
`trust_effect: none`; it is not mislabeled as an orientation-only object.

### 6.2 RecordFamilySpec

A single registry defines every record family:

```text
family name
record class and schema version
id field and exact-ref aliases
storage path
scope requirements
lifecycle policy
append and revision policy
indexable fields
auto-write policy
graph, timeline, recall, and recording participation
public read/write capabilities
```

This registry generates or validates `paths.py`, record-ref lookup, workspace
inventory, lifecycle routing, process-graph loaders, timeline loaders, recording
slots, MCP/CLI catalogs, and tests. A family cannot be writable while absent
from exact-ref and inventory coverage.

### 6.3 RecordRepository

The repository layer replaces direct path writes for canonical records:

- write-once by default;
- identical payload at the same id is idempotent;
- different payload at the same id is rejected or written as an explicit
  revision/supersession;
- schema and typed-ref validation occurs before write;
- atomic writes and actual file locks or compare-and-swap protect concurrent
  host activity;
- strict canonical reads report malformed records instead of hiding them;
- tolerant readers are limited to explicitly marked legacy migration paths;
- read reports include checked, loaded, skipped, malformed, and missing counts.

### 6.4 CapabilitySpec

A single host-capability registry defines validators, state effects, MCP names,
CLI routes, compact/full visibility, bridge acceptance, and public-surface
contracts. This prevents every new capability from requiring unsynchronized
manual edits across `mcp_tools.py`, `public_surfaces.py`, runtime catalogs, bridge
targets, allowlists, and CLI dispatch.

Compatibility re-exports remain during migration. Architecture line limits are
not raised to hide oversized modules.

## 7. Scope Model And Multi-Topic Isolation

### 7.1 Scope Records

The first multi-topic slice adds:

- `ResearchProgramRecord`: a reviewed collection of related topics and its
  scientific boundary;
- `SessionFocusSetRecord`: the current primary topic plus supporting and
  excluded scopes;
- `CrossTopicRelationRecord`: a record-level bridge with source and target typed
  refs, relation kind, transfer rationale, and revalidation requirements.

`SessionBinding` remains single-topic for compatibility. Focus is a sidecar and
must support `focus_kind` plus `focus_ref`, including question, claim, route,
work package, source set, code change, or run campaign. A session is not forced
to invent an active claim for ordinary theory discussion.

### 7.2 Two-Level Physics Knowledge

- Workspace-shared grounded knowledge contains source identity, definitions,
  formulas, conventions, methods, code components, and reviewed relations.
- Topic and program overlays contain local interpretation, active questions,
  derivations, failure routes, and insights.
- Cross-scope discovery may propose a bridge, but context inclusion requires an
  explicit scope policy and target-side revalidation.

Primary-topic retrieval runs first. Program/shared retrieval runs second.
Unlinked cross-topic discovery is an optional orientation lane and is always
reported in coverage metadata.

## 8. Research Lifecycle And Tiered Autonomy

### 8.1 Logical Lifecycle Events

AITP uses host-neutral logical events rather than assuming every host has the
same hooks:

```text
ResearchTurnStart
SourceAcquired
CodeStateChanged
ToolRunCompleted
ArtifactProduced
FailureOrGapObserved
RouteChanged
MajorConclusionPending
ExpensiveRunPending
SessionCloseout
```

Host adapters map native events into these logical events. For hosts without a
real process-level session start, the first research-relevant prompt acts as
`ResearchTurnStart`.

### 8.2 Moment Decisions

The Research Moment Controller returns exactly one policy decision:

```text
ignore
auto_capture_process
stage_semantic_candidate
coalesce_for_review
require_checkpoint
block_until_prerequisites
```

The decision includes reason codes, target families, minimum refs, dedup key,
expiry policy, and verification steps.

### 8.3 Write Policy Matrix

| Content | Default action | Trust effect |
|---|---|---|
| tool result envelope, code state, source identity, artifact identity, monitor snapshot, retrieval audit | automatic typed process write when inputs are exact | none |
| unreviewed observation or evidence candidate | automatic candidate/unreviewed record | candidate only |
| definition, formula, convention, code mapping, derivation extraction | staging plus coalesced review | none until promoted |
| interpretation, analogy, conjecture, speculative bridge | speculative candidate plus coalesced review | none |
| session closeout and resume inputs | automatic process write, editable by later revision | none |
| claim trust, L2 memory, cross-topic support, accepted scientific baseline | typed preflight/checkpoint | explicit existing gate |
| skill proposal | automatic draft after readiness | none |
| skill install, overwrite, or patch apply | typed human checkpoint | none |

### 8.4 Coalesced Candidate Batches

Raw extraction and event staging lives under runtime state and may expire.
A durable `RecordingCandidateBatchRecord` preserves one reviewable batch per
session or milestone. It deduplicates candidates, links source events, records
missing prerequisites, and cannot write evidence, trust, or skills by itself.

This replaces a noisy one-file-per-event pending queue.

## 9. Session Memory, Recall, And Context

### 9.1 Closeout And Resume

`SessionCloseoutRecord` is a canonical process record containing:

- focus set and objective refs;
- completed work;
- can-say and cannot-say boundaries;
- open gaps and failed routes;
- next actions;
- source record refs;
- pending candidate batch refs;
- reusable workflow candidate refs;
- context/index coverage at closeout.

`SessionResumeCard` is a derived, orientation-only view. `topic_status.py`,
workspace startup refresh, and compact host entry must compile from the same
resume source and expose the same boundary.

### 9.2 Unified Query Layer

All context builders use one query interface over a generation-stamped index.
The first implementation provides deterministic metadata and lexical indexes;
optional dense, formula, code-symbol, and graph indexes are sidecar accelerators.

Every query returns:

```text
query and normalized intent
focus and scope filters
index generation and canonical-store watermark
families checked
records read and read errors
ranking components
top-k and truncation
excluded high-score candidates
stale-index diagnostics
exact expansion handles
```

### 9.3 Retrieval Lanes

The query planner selects independent lanes:

- exact typed refs;
- current research state and recent process history;
- grounded physics knowledge;
- speculative insight, clearly separated;
- source passages and equation anchors;
- derivation dependencies;
- code symbols and formula-code mappings;
- recipes, known failures, accepted baselines, and skill applicability;
- optional cross-topic discovery.

Lexical/BM25 retrieval is the deterministic baseline. Dense retrieval improves
concept recall. Formula-aware retrieval normalizes TeX/symbol structure and
keeps equation-local prose. Graph retrieval follows typed dependency paths.
Late-interaction reranking and generated query expansion are optional; generated
query text is never evidence.

### 9.4 Context Compiler

The default startup context contains:

1. current objective and focus;
2. can-say/cannot-say and open gaps;
3. latest process state;
4. a small grounded-knowledge slice;
5. speculative insight only when explicitly relevant and visibly labeled;
6. applicable skill names and versions, not every full skill body;
7. an execution capsule when the task concerns software or HPC;
8. coverage, errors, and exact expansion handles.

Budgets are measured in tokens/bytes as well as lines:

- startup target: at most 800 estimated tokens;
- one normal expansion target: at most 1,500 estimated tokens;
- exact-record expansion is bounded and paginated;
- full skill content is loaded only after selection;
- large source passages require an explicit source expansion.

The compact keyword router is replaced by a bounded autoroute hint. It must not
read and inject all topic `MEMORY.md` files.

### 9.5 Context Injection Audit

Each real host injection records a compact process event containing host, turn,
fingerprint, source refs, index generation, coverage, and token estimate. It
does not duplicate full context text and cannot support claim trust.

## 10. Physics Knowledge And Insight

### 10.1 Source Layer

Existing `SourceAssetRecord` and `ReferenceLocationRecord` remain the source
identity and exact-anchor foundation. Ingestion records reader version, source
hash, access/license note, page/section/equation anchors, and extraction errors.
Raw local source text may live under `source_blobs`; it is not frontmatter truth.

Knowledge connector bindings describe where corpora live. They do not become
retrieval results or source support by configuration alone.

### 10.2 Grounded Knowledge

Existing `PhysicsObjectRecord` and `ObjectRelationRecord` are evolved rather
than replaced by a parallel universal knowledge graph.

Physics-object schema v2 adds:

```text
scope kind and scope ref
knowledge role
canonical name and aliases
formal expressions and symbol definitions
framework and regime of validity
assumptions, approximations, and non-claims
source assertion kind
exact source refs
review status and lifecycle
```

Object-relation schema v2 adds typed subject and object refs, conditions,
direction, relation status, framework/regime, contradiction state, source refs,
and transfer policy. Legacy `subject_id` and `object_id` remain readable during
migration.

Domain profiles may define narrow object and relation vocabularies. AITP does
not force every domain into one universal ontology.

### 10.3 Formal Derivations

The v5 kernel adds `DerivationChainRecord` and `DerivationStepRecord`, reusing
the useful legacy derivation DAG semantics.

A chain records target statement, assumptions, conventions, framework, regime,
step refs, open gaps, checks, and status. A step records input/output expression,
justification type, dependency step refs, invoked knowledge refs, source anchors,
local checks, and unresolved conditions.

The records contain inspectable scientific derivation artifacts. They are not a
request to persist hidden model chain-of-thought.

### 10.4 Speculative Insight

`InsightRecord` is distinct from evidence, sensemaking prose, and skills:

```text
insight kind
statement
topic/program scope
grounding and inferred-from refs
framework and regime
speculation level
known counterevidence
falsifiers or discriminating checks
open proof obligations
review status
lifecycle status
```

Allowed kinds include interpretation, analogy, conjecture, failed-route lesson,
counterexample direction, conceptual bridge, and open research direction.

An insight may motivate a question, route, proof obligation, source search, or
validation contract. It cannot be attached as evidence without a separate
source/derivation/validation path.

### 10.5 Knowledge Candidate And Promotion Flow

```text
source/research event
  -> extraction candidate in runtime staging
  -> dependency/provenance/contradiction diagnostics
  -> coalesced candidate batch
  -> human review
  -> physics object/relation/derivation or reviewed insight
  -> lifecycle and index update
```

Automatic promotion is forbidden. Rejected and superseded candidates remain
auditable without appearing in active retrieval by default.

### 10.6 Curated RAG Role

The existing curated RAG layer becomes a versioned source-shelf and derived
retrieval lane. Its useful trust-neutral constraints remain unchanged.

Production retrieval adds fielded lexical ranking, optional dense and
formula-aware indexes, graph projection, query profiles, and evaluation sets.
It never replaces typed sources, exact anchors, evidence, or trust gates.

## 11. Reproducible Execution And New Software

### 11.1 Code And Environment Identity

Existing `CodeWorkspaceRecord` and `CodeStateRecord` remain authoritative for
repository identity. Reproducibility requires commit SHA; branch name is only
orientation. Dirty worktrees require a diff hash and patch artifact or an
explicit non-reproducible boundary.

An `ExecutionEnvironmentRecord` captures reusable environment identity:

```text
host/cluster
operating system and architecture
compiler, MPI, math libraries, modules, and package versions
container or environment-lock digest
scheduler and partition constraints
executable paths and hashes
redacted environment variables
```

Secrets and credentials are never recorded. Structured argv is redacted by
policy before persistence.

### 11.2 ToolRecipe V2

`ToolRecipeRecord` is extended with recipe version, software constraints,
structured command template, parameter schema, units, defaults, allowed ranges,
physical meaning, input/output roles, script refs, environment requirements,
failure modes, stop rules, validation contracts, and applicability boundary.

Parameter roles distinguish physical, numerical-convergence, execution-resource,
and diagnostic parameters.

### 11.3 ToolRun V2

`ToolRunRecord` is extended with structured argv, cwd, actual parameter values
and provenance, input/script hashes, code states, environment ref, scheduler and
job identity, timestamps, exit status, output manifest, validation refs,
monitor refs, and skill/version usage refs.

Execution maturity is explicit:

```text
diagnostic
reproducible_candidate
accepted_baseline
superseded
```

`accepted_baseline` requires passed validation, complete reproducibility refs,
and a typed acceptance checkpoint. An immutable `ExecutionBaselineRecord`
references the accepted recipe, run, code state, environment, artifacts,
validation results, scope, and known non-claims.

### 11.4 Remote HPC Intake

The current run-directory plan becomes a generic compute-run intake supporting
local and remote URIs, cluster/host, scheduler, job id, collector version,
captured-at time, executable and code hash, input/output manifests, resource
accounting, lane, and missing fields.

Collector output is a candidate/prefill surface. Separate typed writes create
or update tool-run, artifact, monitor, and validation records.

`MonitorSnapshotRecord` gains capture time, sequence, collector identity, remote
URI, and immutable snapshot id. Scheduler state remains process evidence only.

### 11.5 Formula-Code Map

Physics-object and relation records support code-aware relation types:

```text
implemented_by
controlled_by_parameter
approximated_by
discretized_by
normalizes_as
produces_observable
validated_by
```

A LibRPA code-edit context can therefore recover the relevant formula, symbol
convention, module/function, input parameters, tests, known failures, accepted
baseline, and applicable skill without embedding this information in one
monolithic skill.

## 12. Skill Compilation And Use

### 12.1 Procedural Boundary

Only stable procedural workflows are skill candidates. Definitions, physical
relations, derivations, interpretations, and insights remain knowledge records.

`research_distillation` must route `physics_semantic_fragment_candidate` away
from the skill pipeline and into the knowledge-candidate path.

### 12.2 Candidate And Readiness

`SkillDistillationCandidateRecord` includes stabilized steps, parameter schema,
inputs/outputs, stop rules, failure modes, validation requirements, source
records, topic/program scope, and transfer boundary.

Default readiness requires:

- at least two independent successful validated executions; or
- one narrow validated execution plus an explicit expert exception;
- at least one relevant negative/failure case when failure is plausible;
- stable parameter and regime boundaries;
- executable tests or validation fixtures;
- duplicate and overlap checks against installed skills.

### 12.3 Proposal, Package, And Installation

A project skill proposal contains a complete package preview, content hash,
manifest, provenance, test/eval results, target namespace, and filesystem diff.

The canonical reviewed package is project-owned and host-neutral. Host adapters
materialize discovery shims or installations for `.agents`, `.codex`, `.claude`,
and `.kimi`. AITP-generated ids use a dedicated namespace and cannot collide
with domain-pack shims.

Installation and overwrite require a `HumanCheckpointRecord` bound to proposal
hash, target paths, namespace, overwrite policy, and diff. Free-form confirmation
strings are not authorization.

### 12.4 Applicability, Usage, And Patching

Skill manifests declare selectors for domain, task kind, software, repository,
code path, physics object, focus kind, and required records. Applicability cards
are derived. Canonical applicability records are reserved for reviewed overrides
and exceptions to avoid a stale topic-by-skill matrix.

Every run may record skill id and version usage. New validated success, failure,
or boundary evidence may generate a `SkillPatchProposalRecord`; patch application
uses the same review gate as installation.

## 13. Harness Feedback

Real research may detect AITP friction, but it does not design or implement its
own harness changes.

Use one generic Markdown-backed `HarnessFeedbackCaseRecord` family. One file is
one reviewable problem dossier containing problem type, observed friction,
source topic/program and record refs, expected/actual behavior, user-visible
cost, proposed direction, status, reviewer, and explicit statements that it has
no optimization-plan or skill-install authority.

The current NiO case becomes an example and test fixture. Do not create separate
canonical families for friction events, workflow gaps, automation opportunities,
schema gaps, and improvement proposals. Those may be sections or tags in the
single dossier. Reviewed engineering work moves into the repository roadmap or
issue tracker outside the scientific kernel.

## 14. Host Integration

### 14.1 Compact Default Surface

The host-visible path remains small:

```text
autoroute
enter minimal context
expand exact surface
recording step
record apply
closeout
```

New lifecycle, knowledge, execution, and skill operations are exposed through
these facade operations unless a direct compact tool is demonstrably necessary.
The full kernel surface remains available for maintenance and advanced review.

### 14.2 Startup Behavior

- Codex: first research-relevant prompt triggers autoroute and minimal entry.
- Hosts with SessionStart: refresh handles and caches only; select scientific
  context after request/focus disambiguation.
- No host injects every topic memory.
- `topic_status.py`, workspace refresh, compact entry, and generated startup
  files compile from the same resume/context contract.

### 14.3 Hook Safety

Hooks write process traces and objective capture candidates only. They cannot
write trusted evidence, promote memory, install skills, or mutate claim trust.
Legacy host entrypoints that violate the v5 compact contract are quarantined and
eventually removed after compatibility tests.

## 15. Workspace Layout

New layout entries are narrow and generated from `RecordFamilySpec`:

```text
.aitp/
  registry/
    research_programs/
    session_focus_sets/
    cross_topic_relations/
    session_closeouts/
    recall_audits/
    recording_candidate_batches/
    derivation_chains/
    derivation_steps/
    insights/
    execution_environments/
    execution_baselines/
    skill_distillation_candidates/
    skill_readiness_reports/
    skill_proposals/
    skill_install_records/
    harness_feedback_cases/
  runtime/
    sessions/
    knowledge_staging/
    recording_staging/
    context_injections/
    hook_trace_events.jsonl
  indexes/
    manifest.json
    metadata/
    lexical/
    optional_dense/
    optional_formula/
    optional_graph/
  surfaces/
    context/
    resume/
    recall/
  tools/
    skills/
      catalog/
      installed_manifests/
```

Existing registry families remain in place. Migration is additive and preserves
exact refs.

## 16. Code Architecture

Implementation proceeds through focused modules with compatibility re-exports,
not one repository-wide package move:

```text
record_envelope.py
record_family_registry.py
record_repository.py
capability_registry.py
query_index.py
research_retrieval.py
retrieval_audit.py
context_compiler.py
research_moments.py
recording_batches.py
session_lifecycle.py
knowledge_candidates.py
knowledge_promotion.py
knowledge_retrieval.py
derivations.py
insights.py
execution_environments.py
execution_baselines.py
skill_distillation_records.py
project_skill_packages.py
```

Large existing files are split along these boundaries while their public imports
remain stable. Architecture tests enforce focused size limits and dependency
direction.

## 17. Migration And Compatibility

1. Generate a complete capability and file audit from the current checkout.
2. Build a record-family manifest for every actual registry directory, including
   families currently missing from `_LAYOUT_DIRS`.
3. Add envelope compatibility adapters without rewriting existing records.
4. Build the first index from the canonical store and report every malformed or
   unsupported record.
5. Migrate readers to `RecordRepository` and the unified query layer.
6. Add schema-v2 writers; keep schema-v1 readers.
7. Generate migration proposals for physics objects/relations and legacy
   derivation steps; do not hand-edit canonical topic state.
8. Switch context builders and host entrypoints to indexed queries.
9. Enable autonomous objective capture only after idempotency and coverage tests
   pass.
10. Remove compatibility paths only after real-store read audits and rollback
    instructions are recorded.

No migration may reinterpret an old record as more trusted than before.

## 18. Failure Handling

- Stale index: return diagnostics, use exact canonical lookup when possible, and
  refuse exhaustive claims.
- Malformed record: expose the path and family in read errors; do not silently
  treat it as absent.
- Duplicate id with different content: reject and require revision/supersession.
- Ambiguous topic or focus: ask before rebinding; never auto-rebind an active
  claim.
- Missing remote run state: record partial intake and missing fields; do not
  infer completion.
- Dirty code state without patch: mark non-reproducible.
- Retrieval-only physics relation: keep as candidate.
- Rejected insight or skill: retain review outcome, exclude from active default
  retrieval/install.
- Host hook unavailable: fall back to explicit facade entry; scientific kernel
  behavior remains correct.

## 19. Verification Strategy

### 19.1 Unit And Contract Tests

- envelope and family registration;
- repository idempotency, collision, locking, revision, and malformed reads;
- exact refs and lifecycle across every registered family;
- index freshness, invalidation, and coverage;
- moment-policy classification and deduplication;
- candidate/promotion boundaries;
- skill readiness and install checkpoint binding;
- context token/byte limits and trust-neutral flags.

### 19.2 Retrieval Evaluation

Versioned fixtures measure lexical, dense, formula, code-symbol, and graph lanes
separately and after fusion. Tests cover relevant-record recall, cross-topic
contamination, exact-anchor recovery, convention mismatches, stale indexes,
and reasoning-intensive queries.

Retrieval quality never substitutes for scientific validation.

### 19.3 Real Research Vertical Tests

1. LibRPA/HPC and code modification:
   recover formula-code links, exact script/commit/parameters, remote run state,
   failed routes, accepted baseline, validation, and applicable skill.
2. QFT/quantum gravity literature and derivation:
   preserve source-local definitions, conventions, framework, derivation DAG,
   grounded comparison, speculative insight, and no trust leakage.
3. New software onboarding:
   progress from diagnostic use to recipe, reproducible candidate, accepted
   baseline, and reviewable skill proposal.
4. Multi-topic isolation:
   reuse workflow knowledge while preventing claim-trust transfer.

### 19.4 Performance Gates

On a versioned fixture with at least 10,000 records:

- minimal entry warm p95 is below 1 second;
- minimal entry cold p95 is below 3 seconds;
- normal context expansion warm p95 is below 2 seconds;
- exact ref lookup p95 is below 250 milliseconds;
- startup context stays within its token/byte budget;
- index rebuild reports throughput and malformed records;
- no query silently scans the whole store after the indexed path is enabled.

### 19.5 CI Structure

Tests are split into kernel, query/context, lifecycle, knowledge, execution,
skills, hosts, migration, performance-smoke, and real-journey lanes. A full
scheduled suite remains available, but normal development uses targeted slices.

## 20. Release Gates

The implementation roadmap follows these gates:

1. Gate 0: data, query, performance, and architecture foundation;
2. Gate 1: scope, lifecycle, recall, and context recovery;
3. Gate 2: reproducible execution, remote HPC, and formal derivations;
4. Gate 3: grounded knowledge, speculative insight, and hybrid RAG;
5. Gate 4: reviewed skill compilation, installation, applicability, and usage;
6. Gate 5: autonomous research-moment integration and generic harness feedback;
7. Gate 6: end-to-end validation and advanced cross-topic discovery.

No later gate may relax an earlier trust, provenance, compactness, performance,
or human-review invariant.

## 21. Decisions Explicitly Rejected

- A second canonical vector or graph database;
- automatic promotion of retrieved or model-generated knowledge;
- automatic claim rebinding;
- full-topic memory injection at every prompt;
- using skills as physics knowledge containers;
- treating branch names without commit/hash state as reproducibility;
- using six harness-feedback record families for one reviewable problem;
- universal ontology work before real vertical cases require it;
- implementing autonomous research loops before deterministic recovery and
  recording are fast and correct.

## 22. Definition Of Done

AITP reaches this architecture when a researcher can begin a relevant physics
conversation and receive fast, bounded, accurate recovery; work normally while
objective process state is captured quietly; review a coalesced set of semantic
candidates at a natural milestone; reproduce important software/HPC results from
exact code, scripts, parameters, environment, and validation; retrieve formal
physics knowledge and visibly separated insights from high-quality sources; and
reuse or improve a reviewed skill without any path that silently changes
scientific trust.
