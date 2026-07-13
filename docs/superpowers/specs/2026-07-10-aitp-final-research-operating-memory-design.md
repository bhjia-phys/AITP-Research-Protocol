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
the M0 data, query, and architecture foundation.

M0 is now accepted. Its audit also proved that the existing 225-capability core,
46 families, at least 111 recognized low-level writer calls, and
compatibility-shard structure are too large to treat as a mandatory
implementation baseline. The writer count is a scanner lower bound, not a
repository-wide completeness claim. M0.5 complexity
reduction is therefore required before M1-M6. Its evidence and proposed
compatibility policy are defined in
`docs/superpowers/specs/2026-07-11-aitp-m0-5-complexity-reduction-design.md`.

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
- A reusable `HumanCheckpointRecord` v2 binds action, exact subject refs,
  request/payload hash, target/effect policy, expiry, and replay policy. A
  generic approval or a checkpoint created for different bytes/refs cannot
  authorize a baseline, Skill operation, migration, or trust-changing action.
- `CheckpointApplicationReceiptRecord` is the sole canonical fact that a
  checkpoint-authorized action was applied or consumed. It is immutable and
  has this minimum payload:

```text
record_id = application_id = "checkpoint-application-" + sha256(canonical application key)
intent_ref + intent_hash + intent_revision
action + action_payload_hash
subject_refs[] = PinnedRecordRef(record_ref, record_content_hash, revision)
request_ref + request_hash + request_revision
decision_ref + decision_hash + decision_revision
result_ref + result_hash + result_revision, or null on failure
status = applied | failed
started_at + completed_at + recorded_at
errors[] = {code, message, retryable}, empty on success
```

  The canonical application key is the action, action payload hash, pinned
  intent, sorted pinned subjects, pinned request, and pinned decision. Exact
  replay therefore resolves the same id and receipt; a different action,
  subject, request, decision, or payload hash is a different application and
  cannot consume the prior authorization. Only `status=applied` proves
  consumption; `failed` preserves the attempted application and errors but does
  not consume the decision. A recovery journal and action lock may coordinate an
  in-flight transaction, but neither is a consumption fact. If the result exists
  and the receipt write was interrupted, retry verifies the deterministic result
  ref/hash and writes the missing receipt. No path patches the checkpoint or
  result after application. Retrying a failed application requires a new pinned
  intent and a policy-valid decision; it never revises the failed receipt.
- New `HumanCheckpointRecord` writes do not contain `consumed_by_ref`.
  Schema-v1 records that already contain it remain readable, and a compatibility
  read surface may expose it as a legacy/read-only projection from application
  receipts. Writers reject it as v2 input, and policy never uses it to prove
  application or consumption.

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

### 4.6 V5 Is The Production Runtime

- `brain/v5/native_mcp.py` and `aitp_v5_*` are the production research-write
  entrypoints.
- Active host installers, adapter references, and generated MCP configuration
  must point to that v5 entrypoint; deployment-surface tests reject legacy
  active wiring or stage-machine instructions.
- `brain/mcp_server.py` and the L0-L4 state machine remain read-only by default
  for audit, migration, rollback, and historical interpretation.
- The legacy write escape hatch is limited to explicit one-time
  migration/debug fixtures. Candidate submission, stage advancement, promotion,
  legacy graph writes, and their end-to-end tests are archived behavior, not
  release acceptance targets.
- Blocking release tests cover all v5 modules plus legacy read, lossless
  migration, schema-v1 materialization, and default write guards. An optional
  archive run cannot justify production legacy state-machine maintenance.

### 4.7 Complexity Must Be Earned By Real Research

- Existing classes, families, capabilities, facades, and detailed milestone
  file lists are implementation hypotheses, not permanent architecture.
- A capability or family is retained only when a real research vertical, trust
  invariant, host obligation, or required compatibility fixture owns it.
- Codex is the default host. AITP does not rebuild its generic reasoning,
  execution, tool orchestration, or conversation runtime.
- No new family or capability is added without one unique read/write path,
  exact refs and coverage, state/trust effects, and a vertical acceptance test.
- Logical responsibility size is measured across facade plus shards; splitting
  a large module into numbered files does not by itself reduce complexity.
- M0.5 classification, default-surface reduction, writer convergence, and
  legacy isolation precede implementation of M1-M6 candidate abstractions.

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
record_content_hash: <canonical record-payload hash>
revision: 1
lifecycle_status: active
supersedes: []
trust_effect: none | candidate_only | trust_path_input
```

`record_content_hash` is reserved for repository integrity. Domain records may
retain their own hashes under semantically specific fields; in particular,
`SourceAssetRecord.content_hash` continues to mean the acquired source bytes
and must remain part of the scientific payload hash.

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

Trust-relevant and reproducibility-relevant dependencies use a
`PinnedRecordRef` containing `record_ref`, `record_content_hash`, and revision.
The repository resolves current or archived content by `(record_ref,
record_content_hash)` and rejects a missing/hash-mismatched revision. A mutable
bare ref may orient retrieval, but cannot freeze an accepted baseline, reviewed
Skill package, acquisition receipt, migration plan, or checkpoint subject.
Whenever a field named `*_hash` is paired with a typed `*_ref`, that hash is the
target record's `record_content_hash`; byte hashes and request/payload hashes use
their explicit domain field names.

`ExecutionBaselineRecord` embeds a `FrozenDependencyManifest` that is the
recursive, closed dependency graph of the accepted result. The manifest stores
sorted root `PinnedRecordRef` values, sorted nodes, explicit edges
`{owner_ref, field_name, target_ref, target_hash, target_revision}`, and a
`closure_hash` over canonical JSON. `RecordFamilySpec` declares the only fields
that may contribute frozen dependency edges. Construction starts from the
baseline's pinned recipe, run, code state, environment, role-labelled artifacts,
validation results, monitor/effective-attempt inputs, lane contract, scope and
revalidation decisions, and checkpoint request/decision; it resolves each exact
current-or-archive version, follows every declared edge recursively, and rejects
missing hashes, unregistered dependency fields, hash/revision mismatches, or
unresolved terminal bytes. Traversal visits each pinned ref/hash/revision node
once while retaining explicit back-edges, so exact run/validation back-links do
not recurse forever or invalidate an otherwise closed graph.

Terminal closure requires each reproducible `ArtifactRecord` to reach its exact
`ArtifactBlobReceiptRecord` and each dirty `CodeStateRecord` to reach its exact
`CodePatchManifestRecord`; patch entries for required bytes in turn reach exact
artifact-blob receipts. Validation, scope, and checkpoint records contribute
their own declared pinned dependencies. Replay may resolve only nodes already
listed in the manifest. It may not search for a latest/current record, infer a
receipt from a path or URI, infer a patch from a worktree, discover a scope
decision by tuple, or consult ambient state. The checkpoint application receipt
is written after the baseline result and pins that result; it is not placed
inside the result's closure, which avoids a hash cycle.

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

Completion of target revalidation is an explicit
`ScopeRevalidationDecisionRecord` bound to target topic/program/claim, bridge
and imported record hashes, applicability conditions, validation/evidence/
checkpoint refs, decision, expiry, and supersession. Consumers resolve that
exact decision ref; bridge presence or a bare checkpoint never means the target
scope validated imported content.

`brain/v5/execution_scope_policy.py` owns the single execution-scope evaluator:

```python
assess_execution_scope(
    ws,
    *,
    operation: str,
    consumer_scope: ExecutionScope,
    dependency_refs: Sequence[PinnedRecordRef],
    revalidation_decision_refs: Sequence[PinnedRecordRef] = (),
) -> ExecutionScopeDecision
```

The result carries the policy version, one decision per dependency, resolved
bridge/revalidation refs and hashes, reason codes, and an aggregate disposition
of `allowed`, `orientation_only`, `requires_revalidation`, or `denied`.
Baseline preflight, context compilation, and execution CLI/MCP facades call this
evaluator directly; they do not maintain separate family/scope matrices. Context
may render an orientation-only dependency with its boundary, while baseline
acceptance requires every dependency to be `allowed` for that exact operation.

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
| claim trust, L2 memory, cross-topic support | typed preflight/checkpoint | explicit existing gate |
| accepted execution baseline | hash-bound checkpoint application transaction | none; execution maturity only |
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

Coverage stores the effective base/delta lineage, checked-family fast state
tokens, strong content watermarks, dirty-family diagnostics, and whether the
selected scope was content-verified. Resume compares those values with the
current selected scope and reports which relevant families changed. The global
watermark remains historical audit metadata; an unrelated process append does
not by itself stale the closeout.

The scientific boundary fields are structured pointer records, not free-form
authority. Every can-say, cannot-say, open-gap, and failed-route item carries a
boundary class (`proved`, `conditional`, `finite_evidence`, `open_gap`, or
`process_only`), exact source refs, scope/conditions, and an exact-expansion
requirement. A proposed can-say item without adequate exact refs is retained as
an unverified closeout note and cannot enter the rendered can-say lane. The
closeout can summarize existing trust state but cannot create support or raise
the status of any claim.

`SessionResumeCard` is a derived, orientation-only view. `topic_status.py`,
workspace startup refresh, and compact host entry must compile from the same
resume source and expose the same boundary classes and refs. Human-facing text
may be compact, but the model-facing payload must preserve per-item provenance.

### 9.2 Unified Query Layer

All context builders use one query interface over a generation-stamped index.
The first implementation provides deterministic metadata and lexical indexes;
optional dense, formula, code-symbol, and graph indexes are sidecar accelerators.

The production query index has two disposable parts: an immutable full-build
generation and a bounded write-through delta overlay. A schema-v2 root manifest
is explicitly tagged `manifest_kind="query_index_root"` and points to one
generation. Its `base_content_hash` is SHA-256 over canonical JSON containing
the schema version, canonical watermark, per-family content watermarks,
component hashes, record/family counts, and malformed/family counts; generation
id and build time are excluded. An untagged M0 manifest is loaded only as a
legacy single-generation descriptor. It remains readable, but delta projection
is `migration_required` and cannot make it fresh before a successful v2 build.

Each full build is assembled beneath an unpublished
`indexes/generations/<generation>/` directory through an `IndexBuildLease` that
holds the ranked `base-build -> canonical-mutation` locks from reservation
through publication and delta rebase. Prepare/publish helpers require the live
lease and are not independently callable. Generation reservation is therefore
unique and two builders cannot mutate one supposedly immutable directory.
Publication requires component hash verification and, for every family,
`derived content watermark == canonical before == canonical after`, including
malformed path/byte hashes. The root pointer changes through one atomic replace
only after this proof. Interrupted or rejected builds are unreferenced and have
no read authority. This three-way equality prevents an ABA mutation from
producing a mixed but apparently current generation.

A successful `RecordRepository` write holds an explicit
`CanonicalMutationLease`, commits the canonical Markdown record under its
existing record lock, and then passes the same live lease and captured
predecessor to the locked delta projector. A standalone projector acquires its
own lease and cannot infer an absent predecessor. Lock order is always
`base-build -> canonical-mutation -> canonical-record -> delta-manifest`; paths
may omit locks but never invert them. The delta manifest binds the exact base
generation and `base_content_hash`, advances a monotonic delta generation,
records per-family state/content/predecessor tokens, hashes each latest-row file
keyed by canonical `record_ref`, and carries `dirty_families`.

A family is logically dirty when it has an explicit marker or when canonical
and effective predecessor tokens disagree. A failed projection therefore
cannot be forgotten even if the dirty-marker write itself fails, and a later
successful write cannot advance that family back to fresh. Rows publish before
the manifest, so interrupted projections become ignored orphans. Missing or
hash-invalid referenced rows are dirty. Idempotent writes may restore one row
only while predecessor continuity is intact; revisions replace the latest row
for the same ref. Only a strong full-family repair or content-proven full build
may clear dirty state. Projection status and diagnostics are returned through a
typed `IndexProjectionOutcome` attached to `WriteResult`; canonical success is
never rolled back or hidden by derived-index failure.

Readers acquire a coherent derived snapshot by hashing the root pointer,
validating the referenced generation, loading and validating the bound delta
and rows, and then re-reading both manifest hashes. A changed manifest causes a
bounded retry. Corruption or retry exhaustion becomes typed scoped stale/read
diagnostics at the retrieval boundary rather than an uncaught integrity error.
Fast state-token agreement authorizes orientation use only. Exhaustive or
absolute no-result language additionally requires a strong content check for
every selected family, no dirty family, malformed/read error, or truncation.
The strong check briefly holds `canonical-mutation`, creating a linearization
point against all repository writes. Metadata-preserving out-of-band edits
therefore cannot authorize exhaustive language merely because size/mtime state
tokens still match; direct filesystem mutation remains an unsupported
concurrent writer and is guarded by canonical before/after content checks.

Family repair holds `canonical-mutation`, rebuilds every row in the family,
proves `derived == canonical before == canonical after`, and publishes through a
delta generation/base compare-and-swap. Every v2 root publication, including an
ordinary full rebuild over a nonempty delta, takes the delta lock, revalidates
the snapshot, and publishes a rebound or empty delta manifest for the new base
before returning success. Delta compaction uses this same lease primitive,
clears dirty state only for families covered by the strong proof, removes only
snapshot rows whose hashes still match, and retains later replacements when
present. A process crash before the root swap leaves the old base authoritative;
a crash after it yields either a valid rebound delta or an explicit base-lineage
mismatch, never a silently incomplete fresh index. Ranked build/mutation/delta
locks are OS advisory locks released on owner death; persistent lock files do
not imply ownership. Filesystem power-loss durability is not claimed where the
host cannot durably synchronize a directory rename. Every derived index file
may still be deleted and rebuilt from canonical records.

Freshness is reported both globally and for the exact family scope used by a
query. A selected-family query may therefore remain content-verified when an
unrelated process family changes, while an unscoped query still requires every
family to be fresh and content-verified. This distinction is required for
persisted recall audits: appending `RecallAuditRecord` must not invalidate the
scientific families that the audit just checked. An audit of the audit family
itself is not self-certifying and remains non-exhaustive until a later index
generation.

Every query returns:

```text
query and normalized intent
focus and scope filters
base generation, delta lineage, selected-family state/content tokens, dirty families, and canonical-store watermark
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

Context follows one fixed progressive-disclosure ladder:

1. `route_hint`: topic/focus candidates, reason, and no scientific content;
2. `startup_orientation`: bounded resume, trust boundary, open obligations,
   applicable skill names, and coverage declaration;
3. `normal_research`: one query-planned process/knowledge/execution slice with
   scored refs and explicit exclusions;
4. `exact_expansion`: paginated canonical records or anchored source passages.

Every level returns read errors, checked and unchecked scope, and handles for
the next level. A compact level may say "not shown" or "not checked"; it may
not turn either condition into "not found". MCP, CLI, hooks, topic status, and
workspace refresh expose this same ladder rather than composing independent
summaries.

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
fingerprint, source refs, base/delta lineage, selected-family state tokens and
content watermarks, dirty-family diagnostics, coverage, and token estimate. It
does not duplicate full context text and cannot support claim trust. Reinjection
keys use effective selected inputs rather than the global watermark, so an
unrelated audit/process append does not create context churn.

## 10. Physics Knowledge And Insight

### 10.1 Source Layer

Existing `SourceAssetRecord` and `ReferenceLocationRecord` remain the source
identity and exact-anchor foundation. Ingestion records reader version, source
hash, access/license note, page/section/equation anchors, and extraction errors.
Raw local source text may live under `source_blobs`; it is not frontmatter truth.

Knowledge connector bindings describe where corpora live. They do not become
retrieval results or source support by configuration alone.

An unresolved literature/knowledge gap may produce a bounded
`LiteratureDiscoveryRequest`. AITP records the normalized query, scope,
framework/regime, required source kinds, connector allowlist, result/time
budget, prior recall audit, and dedup fingerprint. The host or connector performs
the external read and returns source-identity candidates plus coverage/errors;
AITP itself does not treat search snippets or generated summaries as sources.
Metadata discovery may run automatically under an allowlisted read-only policy.
Acquisition of full text must respect access/license policy. Metadata-only
`SourceAssetRecord`/`ReferenceLocationRecord` identity may exist explicitly, but
only receipt-backed acquired bytes with a source hash and exact location qualify
for grounding, source reconstruction, or the source shelf.

Acquisition is mediated by typed `SourceAcquisitionDecisionRecord` and
`SourceAcquisitionReceiptRecord` process records. They bind discovery/request
identity, policy basis, allow/deny/review decision, access/license disposition,
storage permission, connector/collector identity, acquired byte hash, canonical
URI/identifier dedup key, errors, and expiry. Metadata-only URI records are
explicitly `metadata_only`; they cannot satisfy source reconstruction, enter a
grounded assertion, or seed the source shelf until a hash-pinned receipt exists.
Existing direct-fetch/URI-only paths become adapters to this decision boundary,
not bypasses.

### 10.2 Grounded Knowledge

Existing `PhysicsObjectRecord` and `ObjectRelationRecord` are evolved rather
than replaced by a parallel universal knowledge graph. Object identity is kept
separate from source-specific assertions: `PhysicsObjectRecord` carries stable
entity identity and aliases, while `PhysicsAssertionRecord` carries one
definition, expression, convention-dependent property, or source claim with a
distinct assertion id, field/predicate, value/expression, framework, regime,
conventions, exact source-location refs, review state, contradiction links, and
revision/supersession lineage. Legacy inline object assertions remain readable
and migrate through reviewed candidates.

Physics-object schema v2 adds:

```text
scope kind and scope ref
knowledge role
canonical name and aliases
formal expressions and symbol definitions
framework and regime of validity
assumptions, approximations, and non-claims
legacy source assertion kind
legacy exact source refs
review status and lifecycle
```

Object-relation schema v2 adds typed subject and object refs, conditions,
direction, relation status, framework/regime, contradiction state, source refs,
and transfer policy. Legacy `subject_id` and `object_id` remain readable during
migration.

Domain profiles may define narrow object and relation vocabularies. AITP does
not force every domain into one universal ontology.

Source reconstruction is complete only when every asserted definition,
equation, assumption, and reconstruction step resolves through a
`ReferenceLocationRecord` to a hash-pinned `SourceAssetRecord`. Arbitrary labels
or unresolved `paper:*` strings are orientation only. Completeness audits report
unresolved/mismatched assets and anchors and cannot pass from record presence
alone.

### 10.3 Formal Derivations

The v5 kernel adds `DerivationChainRecord` and `DerivationStepRecord`, reusing
the useful legacy derivation DAG semantics.

A chain records target statement, assumptions, conventions, framework, regime,
step refs, open gaps, checks, and status. A step records input/output expression,
justification type, dependency step refs, invoked knowledge refs, source anchors,
local checks, and unresolved conditions.

`structurally_closed` means only that the DAG is acyclic, refs resolve, and no
declared structural gap remains. `reviewed` and `validated` are separate states
bound to hash-pinned review decisions, validation/tool-run check refs, and
source-reconstruction coverage. Structural closure cannot support a claim or
be rendered as a proved derivation by itself. Imported cross-topic chains retain
their origin scope and require target-side review/revalidation.

The records contain inspectable scientific derivation artifacts. They are not a
request to persist hidden model chain-of-thought.

`DerivationReviewRecord` pins reviewed chain/step hashes, exact source anchors,
validation/tool-run check refs, reviewer/checkpoint, decision, and scope.
`supersede_derivation_review(ws, prior_review_ref, replacement, *, actor) ->
WriteResult` writes a new review plus explicit supersession; it never revises a
prior review in place. Effective reviewed/validated status is a projection from
active pinned reviews and validation results, not a mutable chain field.

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

This boundary is enforced at evidence intake, not only at insight promotion.
Every evidence write carries an `EvidenceBasisAudit` that resolves its basis
refs. Insight, search/discovery receipt, derived passage, summary/context,
Skill, unreviewed candidate, and unresolved knowledge refs are inadmissible as
sole evidence basis. A reviewed grounded assertion may appear as trace context,
but claim support must cite its pinned source locations, validated derivation,
or validated run/artifact basis. Pre-tool policy, evidence contracts, trust
audit, and promotion preflight all reject inadmissible or unresolved basis.

Evidence v2 stores `support_basis_refs` separately from `trace_context_refs` and
embeds `basis_policy_version`, `evidence_payload_hash`, per-ref role/
classification/resolution, pinned resolved refs, errors, admissibility result,
and `basis_audit_hash`. Trust paths recompute and verify this audit; a mixed
record cannot count an insight or other context-only ref as support.

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

Automatic promotion is forbidden. Review decisions are per item and bind the
candidate/batch content hash plus exact source refs. Rejected, demoted,
invalidated, and superseded records remain auditable without appearing in
active retrieval by default. Source-byte, anchor, contradiction, grounding, or
framework changes create invalidation candidates; they never silently mutate a
reviewed assertion/insight. Explicit revise/supersede/demote operations preserve
the old version and require a new hash-bound review for active status.

For autonomous literature work the preceding source event may itself originate
from a discovery loop:

```text
persisted recall/knowledge gap
  -> bounded discovery request
  -> host connector metadata search
  -> deduplicated source-identity candidates and coverage receipt
  -> reviewed/allowed acquisition with content hash
  -> ordinary source intake and extraction flow
```

The request and receipt are process memory only. Search rank, snippet text, and
model-generated query expansion are never evidence or grounded knowledge.

### 10.6 Curated RAG Role

The existing curated RAG layer becomes a versioned source-shelf and derived
retrieval lane. Its useful trust-neutral constraints remain unchanged.

Production retrieval adds fielded lexical ranking, optional dense and
formula-aware indexes, graph projection, query profiles, and evaluation sets.
It never replaces typed sources, exact anchors, evidence, or trust gates.

All knowledge components participate in one `KnowledgeSnapshotLineage` bound to
the effective record-index generation, selected-family state/content
watermarks, source-shelf generation/hash, and optional component hashes.
`KnowledgeRetrievalResult` reports every component's status, stale/dirty/errors,
checked and excluded scope, deterministic tie-break inputs, lane quotas, token
allocation, truncation, and exact pagination handles. Fusion never labels
incompatible generations complete. Missing/corrupt dense or formula sidecars
degrade visibly. A missing/corrupt graph projection uses a bounded canonical-edge
reconstruction with checked paths/errors or lexical-only partial coverage, never
a hidden unbounded scan. Dense output records adapter/model/index versions,
deterministic mode, timeout/error policy, and input/result hash; nondeterministic
output cannot alter a result labeled deterministic. Default context hard filters
incompatible framework/regime/convention results; comparison and contradiction
queries place them in an explicitly separate lane.

## 11. Reproducible Execution And New Software

### 11.1 Code And Environment Identity

Existing `CodeWorkspaceRecord` and `CodeStateRecord` remain authoritative for
repository identity. Reproducibility requires commit SHA; branch name is only
orientation. Dirty worktrees require a diff hash and patch artifact or an
explicit non-reproducible boundary.

For v2 writes, a dirty `CodeStateRecord` carries both
`patch_manifest_ref: code_patch_manifest:<id>` and `patch_manifest_hash`.
The hash resolves the exact immutable `CodePatchManifestRecord`; no search by
code-state id, commit, branch, or current worktree is permitted. The manifest
records every required path state and pins required changed/untracked byte
streams through artifact-blob receipt refs and hashes. Clean exact-commit code
states leave the patch fields null.

A dirty snapshot is reproducible only when tracked, staged, deleted, binary,
submodule, and required untracked source/script bytes are covered by pinned
patch/artifact hashes. An excluded required path keeps the run
`non_reproducible`; hashing `git status` text is not enough.

Required input/output/script/patch bytes are resolvable, not hash-only labels.
Local bytes are copied to a content-addressed workspace artifact store; approved
external immutable storage has a typed object-version/hash/retention/access/
availability receipt. Reference-only mutable paths remain useful orientation but
cannot satisfy baseline replay. Replay resolves and rehashes every required
artifact byte stream.

Every reproducibility-eligible `ArtifactRecord` carries
`artifact_blob_receipt_ref: artifact_blob_receipt:<id>` and
`artifact_blob_receipt_hash`. These resolve one exact immutable
`ArtifactBlobReceiptRecord` containing storage kind, SHA-256 byte hash, length,
and either a local blob key or external object version. External receipts also
carry retention/access policy and availability verification. Capture time and
source provenance remain on the referring artifact. `ArtifactRecord.content_hash`
must equal the receipt's byte hash. A `reference_only` artifact leaves these
fields null and is ineligible for a frozen baseline.

For local bytes, receipt identity is content-deterministic:
`artifact-blob-sha256-<byte_sha256>`. Its canonical receipt payload contains only
`storage_kind=local_sha256`, hash algorithm, byte SHA-256, byte length, and the
content-addressed blob key. Source path, capture time, and collector provenance
remain on the referring `ArtifactRecord`; they do not perturb local receipt
identity. Identical recapture is idempotent and produces the same receipt ref and
record content hash. External receipt identity is instead the hash of provider,
object id/version, byte hash, length, and retention/access policy. A Skill
package imports every file into the deterministic local form before packaging.

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

All v2 execution relationships are typed refs. Legacy bare ids remain readable,
but only hash-qualified `tool_recipe:`, `code_state:`, `tool_run:`,
`execution_environment:`, `artifact:`, `artifact_blob_receipt:`,
`code_patch_manifest:`, `validation_contract:`, `validation_result:`,
`monitor_snapshot:`, `human_checkpoint:`,
`checkpoint_application_receipt:`, `scope_revalidation_decision:`,
`lane_contract:`, `execution_baseline:`, and `skill_usage:` refs can satisfy
their corresponding reproducibility, scope, or application gate. Paths and
remote URIs identify locations; a captured content hash identifies the bytes
actually used. `RecordFamilySpec` must register
`artifact_blob_receipts`, `code_patch_manifests`,
`checkpoint_application_receipts`, and `scope_revalidation_decisions` for
storage, exact-ref resolution, inventory, lifecycle, and index coverage before
any v2 writer is enabled.

Parameter roles distinguish physical, numerical-convergence, execution-resource,
and diagnostic parameters.

High-risk external commands run only through a registered M2 executor. A
bound request fixes recipe/argv/environment, executor, network/write/timeout
policy, and checkpoint application. Its `BoundExecutionReceipt` pins the
resulting ToolRun and ValidationResult records and carries
`checkpoint_application_receipt_ref` plus
`checkpoint_application_receipt_hash`. The receipt is a derived validated
surface, not a second record family. Later gates may request this path but cannot
execute arbitrary package/project code directly.

### 11.3 ToolRun V2

`ToolRunRecord` is extended with structured argv, cwd, actual parameter values
and provenance, input/script hashes, code states, environment ref, first-class
executor id/version/hash, scheduler and job identity, timestamps, exit status,
output manifest, validation refs, monitor refs, and skill/version usage refs.

New `ToolRunRecord` writes set `recorded_maturity` to exactly one of:

```text
diagnostic
reproducible_candidate
superseded
```

They never persist `accepted_baseline`; legacy `maturity` is a read-only
compatibility alias and cannot authorize baseline use.

`ExecutionMaturityProjection` contains the pinned run ref/hash,
`recorded_maturity`, `effective_maturity`, and optional active baseline ref/hash.
Without an active baseline, effective maturity equals recorded maturity. An
active immutable `ExecutionBaselineRecord` makes
`effective_maturity=accepted_baseline`; the run itself is not revised in a
second transaction. Context, cockpit, facade, and Skill matching consume the
projection rather than raw compatibility fields.

`accepted_baseline` requires passed validation, complete reproducibility refs,
and a typed acceptance checkpoint bound to the exact baseline request/dependency
hash. An immutable `ExecutionBaselineRecord` contains a role-labelled frozen
dependency manifest: pinned recipe, run, code state, environment, input/output
artifacts and byte hashes, validation results, monitor snapshot, executor,
effective attempt/lane contract, scope, and known non-claims. Passed validation
must bind the exact run, recipe version/hash, executor version/hash, outputs,
and failure-mode contract. Later current-record revisions cannot change what an
accepted baseline means.

The baseline stores the recursive `FrozenDependencyManifest` defined in section
6.3. Root-only manifests are invalid: every declared transitive record edge and
terminal blob/patch receipt must be present by ref and hash, and replay performs
no implicit lookup. `BaselineAcceptanceResult` returns the baseline ref/hash and
the immutable checkpoint-application receipt ref/hash that proves application;
the receipt remains outside the baseline hash closure.

Validation contract/result v2 records persist pinned contract/run/recipe refs,
executor id/version/hash, output-manifest hash, failure-contract hash, and
checked artifact hashes. Legacy validation ids remain readable but cannot
satisfy baseline or trust-sensitive v2 gates without these bindings.

### 11.4 Remote HPC Intake

The current run-directory plan becomes a generic compute-run intake supporting
local and remote URIs, cluster/host, scheduler, job id, collector version,
captured-at time, executable and code hash, input/output manifests, resource
accounting, lane, and missing fields.

The public collector contract is
`build_compute_run_intake(request: ComputeRunIntakeRequest) ->
ComputeRunIntakeReport`; the report contains typed prefill candidates, checked
and missing fields, and explicit no-write/trust-neutral flags.

Collector output is a candidate/prefill surface. Separate typed writes create
or update tool-run, artifact, monitor, and validation records.

`MonitorSnapshotRecord` gains capture time, sequence, collector identity, remote
URI, and immutable snapshot id. Scheduler state remains process evidence only.
The HPC cockpit resolves effective attempt/supersession chains and latest
immutable monitor snapshots. Baseline preflight rejects active/partial/failed
attempts, unresolved partial outputs, and runs excluded by the effective
final/diagnostic lane contract.

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
It pins an immutable package artifact containing the exact reviewed bytes plus
renderer/template version; included-file hashes alone are insufficient. If the
artifact is missing and deterministic reconstruction does not reproduce the
approved package hash, installation is blocked.

`SkillPackageArtifactRecord` is a sorted canonical POSIX-path tree manifest.
Each full regular-file row pins path, allowlisted mode, length, SHA-256, and a
deterministic local M2 artifact-blob receipt ref/content hash; symlinks and
special files are rejected. Paths are Unicode-NFC normalized relative POSIX
paths with no empty, `.`, `..`, drive, or absolute segment. Mode is exactly the
string `0644` or `0755`. The tree identity projects every row to exactly
`{path, mode, length, sha256, blob_receipt_content_hash}`, sorts rows by UTF-8
path bytes, serializes the list as UTF-8 JSON with sorted object keys, separators
`,` and `:`, no insignificant whitespace, and no trailing newline, then hashes
it with SHA-256. Renderer code-state, generator version, template blobs, and
other provenance are pinned outside the byte-tree identity. Deterministic local
receipt identity makes recapture of identical bytes preserve the package hash.

The canonical reviewed package is project-owned and host-neutral. Host adapters
materialize discovery shims or installations for `.agents`, `.codex`, `.claude`,
and `.kimi`. AITP-generated ids use a dedicated namespace and cannot collide
with domain-pack shims.

Installation and overwrite require a `HumanCheckpointRecord` bound to proposal
hash, target paths, namespace, overwrite policy, and diff. Free-form confirmation
strings are not authorization.

All host-discoverable Skill writes use this path, including generated packages,
domain-pack discovery shims, updates, patches, and rollback. Legacy `apply=True`
shim helpers become preview-only compatibility facades unless supplied a valid
install plan/checkpoint. Every target is project-root constrained.

Generated package code has no ambient execution authority. M4 installation
runs only allowlisted built-in declarative, no-network validators in a restricted
staging directory. Project/package commands are recorded as separate
`SkillValidationExecutionRequest` objects and may run only through the M2
executor/policy path with a high-risk checkpoint and resulting typed receipt;
they are never an implicit install/readback side effect. The checkpoint binds
the exact command digest, file hashes, executor/network/write/timeout policy,
and environment allowlist. Static hash/path/symlink verification always runs
independently of package code.

Installation is a recoverable transaction: persist a hash-bound install intent,
atomically materialize/read back bytes, then persist an immutable receipt. If
receipt persistence fails, restore and read back the before-image; a verified
restoration leaves a `compensated` intent, while failed or uncertain restoration
leaves `recovery_required`. `(skill_id, semantic_version) -> package_hash` is
immutable; same-version hash collisions fail, identical reinstall is idempotent,
upgrades are monotonic, and downgrade requires a separately bound checkpoint.
Rollback has explicit plan/apply/receipt interfaces, installs a previously
pinned package through the same checks, and never deletes prior install history.

Install intent status is exactly `prepared`, `materialized`, `completed`,
`compensated`, or `recovery_required`. Successful compensation records
`compensated`; only failed/uncertain compensation is `recovery_required`.
Deterministic resume/recover validates before/after hashes, completes a missing
receipt or compensates, and cannot reuse approval for changed bytes. Rollback is
itself a canonical hash-bound plan, not an in-memory helper.

### 12.4 Applicability, Usage, And Patching

Skill manifests declare selectors for domain, task kind, software, repository,
code path, physics object, focus kind, and required records. Applicability cards
are derived. Canonical applicability records are reserved for reviewed overrides
and exceptions to avoid a stale topic-by-skill matrix.

Every run may record skill id and version usage. New validated success, failure,
or boundary evidence may generate a `SkillPatchProposalRecord`; patch application
uses the same review gate as installation.

### 12.5 M0.5 Vertical-Minimal Implementation

The accepted new-software vertical deliberately implements a smaller first
slice than the package architecture above:

- `build_procedural_skill_candidates` is a read-only derived report over
  `tool_recipe`, final `tool_run`, code/source provenance, artifact links, and
  passed `validation_result` records. It does not add a canonical candidate
  family.
- Physics objects, object relations, exploratory/Insight records, and
  sensemaking reports are explicitly excluded from procedural eligibility.
- One bounded validated workflow is labeled `single_validated_workflow`; two or
  more are labeled `repeated_validated_workflow`. Both still require human
  review. Missing final run, validation, artifact, provenance, or invariants is
  returned as a recording gap and blocks proposal creation.
- An eligible result may materialize the existing
  `SkillPatchProposalRecord`, enriched with topic ids, applicability,
  preconditions, execution/validation/source refs, artifacts, target, and review
  checkpoint metadata.
- The current installer supports one collision-checked project-local
  `.agents/skills/<name>/SKILL.md`. A host-verified `approve_install` checkpoint
  is bound to the exact proposal content hash. Installation writes the project
  file, then CAS-revises the proposal to `approved/applied`; it never changes
  claim trust.
- The read-only candidate report is included in the existing research
  distillation surface. Proposal, review-request, and apply operations are full
  MCP capabilities; none is added to the ten-tool compact surface.

Multi-file immutable package artifacts, install intents/receipts, rollback,
cross-host materialization, usage records, and overwrite migrations remain
future candidates. They must not be treated as implemented or release-ready
until a real vertical requires them and supplies transaction and recovery
tests.

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

Harness Feedback cannot emit a Skill distillation candidate, patch proposal,
package preview, install action, or automatic optimization plan. Reusable
procedures are discovered independently by the M4 graph-to-Skill pipeline
from validated research records; a dossier may only cite the relevant refs as
problem context.

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
- Hosts exposing prompt-submit and stop/session-end events map them to the shared
  first-turn and closeout facade. Hosts without those events advertise the gap
  and use explicit idempotent `begin-research-turn` / `closeout-session`
  facade calls; availability is tested, never assumed from prose.
- No host injects every topic memory.
- `topic_status.py`, workspace refresh, compact entry, and generated startup
  files compile from the same resume/context contract.

Named immutable context profiles are `startup_orientation` (at most 800
estimated tokens and 4,000 UTF-8 bytes) and `normal_research` (at most 1,500
estimated tokens and 7,500 UTF-8 bytes). Hosts may request a smaller budget but
cannot silently expand these ceilings.

### 14.3 Hook Safety

Hooks write process traces and objective capture candidates only. They cannot
write trusted evidence, promote memory, install skills, or mutate claim trust.
Legacy host entrypoints that violate the v5 compact contract are quarantined and
eventually removed after compatibility tests.

Context receipts and dedup keys are namespaced by workspace identity, host,
host session, topic/focus, logical event id, and context profile. Concurrent
hosts or a focus change cannot collide merely because they reuse a session or
event id. Filesystem names use SHA-256 of canonical namespace JSON, never raw
host ids; containment/symlink checks and adversarial Windows/path tests are
mandatory. Installer templates, host capability declarations, hook audits, and
fallback facades are the configuration owners for this lifecycle contract.

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
    derivation_reviews/
    physics_assertions/
    insights/
    source_acquisition_decisions/
    source_acquisition_receipts/
    knowledge_review_decisions/
    artifact_blob_receipts/
    code_patch_manifests/
    checkpoint_application_receipts/
    scope_revalidation_decisions/
    execution_environments/
    execution_baselines/
    skill_distillation_candidates/
    skill_readiness_reports/
    skill_proposals/
    skill_package_artifacts/
    skill_install_plans/
    skill_install_intents/
    skill_install_receipts/
    skill_rollback_plans/
    skill_rollback_receipts/
    skill_usage_records/
    skill_patch_proposals/
    harness_feedback_cases/
    migration_plans/
    migration_apply_receipts/
    migration_rollback_receipts/
  runtime/
    sessions/
    knowledge_staging/
    literature_discovery/
    recording_staging/
    context_injections/
    hook_trace_events.jsonl
  artifacts/
    blobs/
      sha256/
  indexes/
    manifest.json
    generations/
      <generation>/
        generation_manifest.json
        record_documents.json
        lexical_index.json
        issues.json
    delta/
      manifest.json
      records/
    knowledge/
      source_shelf/
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
  release/
    receipts/
    decisions/
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
query_index_delta.py
research_retrieval.py
retrieval_audit.py
context_compiler.py
research_moments.py
recording_batches.py
session_lifecycle.py
pinned_record_refs.py
checkpoint_bindings.py
checkpoint_transactions.py
artifact_blobs.py
code_patch_manifests.py
effective_attempts.py
execution_scope_policy.py
scope_revalidation.py
bound_execution.py
knowledge_candidates.py
knowledge_promotion.py
knowledge_review.py
evidence_basis_policy.py
knowledge_retrieval.py
knowledge_snapshot.py
literature_discovery.py
source_acquisition.py
source_shelf.py
derivation_models.py
derivations.py
derivation_reviews.py
physics_assertions.py
insights.py
execution_environments.py
execution_baselines.py
skill_distillation_records.py
project_skill_packages.py
skill_install_transactions.py
release_readiness.py
migration_transactions.py
```

Large existing files are split along these boundaries while their public imports
remain stable. Architecture tests enforce focused size limits and dependency
direction.

M0 compatibility loaders and generated shards are not implementation
owners. Later milestones add focused owner modules and only narrow facade
imports/re-exports in `models.py`, `cli.py`, `mcp_tools.py`,
`research_distillation.py`, `moment_policy.py`, or similar loaders. Plans and
reviews must name the focused owner, deep public-surface validator, CapabilitySpec
entry, CLI/MCP route, compact visibility, and parity tests for every operation.

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

Real-store mutation uses a typed `MigrationPlanRecord` bound to before-watermark,
per-record expected hashes, proposed writes, backup/archive manifest, tool
version, and dry-run diff. Apply requires a matching human checkpoint, writes an
immutable `MigrationApplyReceiptRecord`, is restartable/idempotent, and stops on
compare-and-swap drift. `MigrationRollbackPlan` and rollback receipt restore
only the plan's archived before-images and never touch records changed after
apply. A documentation-only rollback instruction is not an executable rollback
contract.

## 18. Failure Handling

- Stale index: return diagnostics, use exact canonical lookup when possible, and
  refuse exhaustive claims for every stale required family. A missing or
  corrupt delta may use a bounded strict scan of only the requested family, with
  explicit coverage, but never a hidden whole-store scan.
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
skills, `security-install`, hosts, migration, performance-smoke, and
real-journey lanes. A full scheduled suite remains available, but normal
development uses targeted slices.

## 20. Implementation Milestones

The implementation roadmap follows these evidence-gated milestones:

1. M0: data, query, performance, and architecture foundation;
2. M0.5: classify and reduce capabilities, families, writers, imports, default
   surface, legacy dependencies, and logical module complexity;
3. V1-V4: close minimal LibRPA/HPC, QFT/QG, new-software, and multi-topic
   verticals;
4. M1-M5: retain or extract only lifecycle, execution, knowledge, skill, and
   host capabilities proven necessary by those verticals;
5. M6: final end-to-end validation and advanced cross-topic discovery.

The existing M1-M5 detailed plans are candidate catalogs. M0.5 and vertical
evidence may merge, replace, postpone, or delete their proposed implementation
objects without weakening the required user outcomes or trust invariants.

No later milestone may relax an earlier trust, provenance, compactness, performance,
or human-review invariant.

M6 produces a machine-validated `ReleaseReadinessDecision` from hash-pinned
test, migration, performance, host, and real-probe receipts. LibRPA/HPC,
QFT/quantum-gravity source memory, and disposable new-software onboarding are
mandatory verticals and each must be `passed`. `skipped`, `unavailable`, stale,
unhashed, fixture-only, or archived evidence not allowed by that probe's policy
is blocking. A rendered audit cannot override the contracted decision.

Probe receipts and readiness decisions are content-addressed generated release
artifacts under `.aitp/release/receipts` and `.aitp/release/decisions`; they are
not scientific truth. Their freshness is defined by bound input fingerprints,
not timestamp alone: topic/collector/artifact inputs for LibRPA/HPC,
source/location/family/shelf inputs for QFT/QG, and executable/environment/docs/
output/clean-replay inputs for new software. M6 exposes deep validated
CLI/MCP/full-surface routes for receipt/readiness review and checkpoint-gated
migration plan/apply/rollback/recovery; every route participates in
CapabilitySpec, public-surface, and pre-tool parity.

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
