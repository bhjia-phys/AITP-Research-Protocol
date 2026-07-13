# AITP M3 Knowledge, Insight, And Hybrid RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compile high-quality physics sources and accumulated research into source-grounded knowledge plus separately labeled speculative insight, retrieved through auditable hybrid lanes and bounded context.

**Architecture:** Evolve existing `PhysicsObjectRecord`, `ObjectRelationRecord`, source assets, reference locations, literature extraction, and curated RAG rather than creating a second knowledge graph. Runtime candidates flow through M1 coalesced review; reviewed grounded records and insights remain separate. Deterministic fielded lexical retrieval is the baseline, optional dense/formula/graph components are disposable indexes, and fusion exposes every component score and coverage fact.

**Tech Stack:** Python 3.12, dataclasses, Markdown/YAML, source-local text/chunk manifests, deterministic BM25-style ranking, formula normalization, graph traversal, reciprocal-rank fusion, optional dense adapter, pytest evaluation fixtures.

## Global Constraints

- M1 and M2 must be green before M3 production code begins.
- Existing physics object/relation ids and schema-v1 files remain readable.
- Grounded promotion requires exact source-asset and reference-location refs.
- Insight is not evidence and cannot update claim trust or accepted baselines.
- Evidence intake resolves basis admissibility; insight, search/discovery,
  passage, summary/context, Skill, unreviewed candidate, and unresolved knowledge
  refs cannot be sole claim-support basis.
- Stable object identity is separate from source/convention-specific assertions.
- Source reconstruction cannot pass from unresolved labels or record presence;
  every asserted definition/equation resolves to a hash-pinned asset/location.
- Physics-semantic fragments never enter the Skill compiler.
- Automatic extraction creates runtime candidates only; canonical promotion requires review.
- Grounded and speculative retrieval lanes remain separate before and after fusion.
- Source identity, version/hash, extraction version, license/access note, and failures are explicit.
- Source text remains source-local; AITP stores bounded passages/anchors and never republishes full copyrighted works.
- Dense embeddings, formula indexes, graph projections, reranking, and summaries are disposable.
- Retrieval output declares index versions, checked scope, scores, truncation, errors, and exact expansion refs.
- Every retrieval component binds one effective record/source-shelf snapshot;
  incompatible generations cannot be fused as complete.
- Review decisions bind candidate/item hashes; revise, demote, invalidate, and
  supersede preserve prior reviewed versions.
- No RAG result, generated query, insight, or context slice can directly change claim trust.
- M0 compatibility loaders/shards receive only narrow imports/re-exports;
  focused M3 modules own behavior.

---

## File Structure

| File | Responsibility |
|---|---|
| `brain/v5/physics_knowledge_models.py` | Compatibility-defaulted physics object/relation v2 and insight dataclass. |
| `brain/v5/physics_assertions.py` | Source/convention-specific assertion identity, revision, contradiction, and writers. |
| `brain/v5/physics_knowledge_contracts.py` | Grounding, scope, framework, relation, and transfer validation. |
| `brain/v5/physics_knowledge_migration.py` | Read-only v1-to-v2 compatibility/migration report. |
| `brain/v5/knowledge_candidates.py` | Grounded/speculative candidate routing and diagnostics. |
| `brain/v5/knowledge_promotion.py` | Review/checkpoint-gated canonical promotion. |
| `brain/v5/insights.py` | Reviewed non-evidence insight writer and lifecycle. |
| `brain/v5/knowledge_contracts.py` | Candidate, review, promotion, and insight contracts. |
| `brain/v5/knowledge_review.py` | Hash-bound per-item review, demotion, supersession, and invalidation. |
| `brain/v5/evidence_basis_policy.py` | Evidence-basis resolution and trust-path admissibility. |
| `brain/v5/source_shelf.py` | Versioned source/chunk manifest over source assets and exact anchors. |
| `brain/v5/literature_discovery.py` | Bounded connector request/result normalization and source-candidate dedup. |
| `brain/v5/literature_discovery_contracts.py` | Read-only budget, provenance, acquisition, and non-evidence rules. |
| `brain/v5/source_acquisition.py` | Typed allow/deny/review decisions and hash-pinned receipts. |
| `brain/v5/knowledge_retrieval.py` | Fielded deterministic lexical retrieval. |
| `brain/v5/formula_retrieval.py` | Formula/symbol normalized retrieval component. |
| `brain/v5/graph_retrieval.py` | Typed dependency traversal component. |
| `brain/v5/retrieval_fusion.py` | Component-preserving fusion and optional dense adapter. |
| `brain/v5/knowledge_snapshot.py` | Shared record/shelf/component lineage and completeness contract. |
| `brain/v5/knowledge_context.py` | Bounded grounded and speculative context lanes. |
| `brain/v5/knowledge_context_contracts.py` | Token, provenance, separation, and coverage validation. |

## Test Protocol

Each task records an expected missing-contract RED and subsequent GREEN using a
unique writable external `--basetemp`, then runs its M0-M2 regression slice.
Reports include exact command, failure reason, pass count, fixture/corpus
version, and temp root. Collection-only success is not execution evidence.

## Task 1: PhysicsObject/ObjectRelation V2 And Insight Model

**Files:**
- Create: `brain/v5/physics_knowledge_models.py`
- Create: `brain/v5/physics_knowledge_contracts.py`
- Create: `brain/v5/physics_assertions.py`
- Create: `brain/v5/physics_knowledge_migration.py`
- Create: `tests/test_v5_physics_knowledge.py`
- Create: `tests/test_v5_physics_assertions.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/record_family_registry.py`
- Modify: `brain/v5/physics_objects.py`

**Interfaces:**
- Extends: `PhysicsObjectRecord`, `ObjectRelationRecord`
- Produces: `PhysicsAssertionRecord`, `InsightRecord`
- Adds families: `physics_assertions`, `insights`
- Produces: `audit_physics_knowledge_v1_compatibility(ws) -> MigrationReport`

- [ ] **Step 1: Write failing schema compatibility tests**

Current v1 constructors and all real-store object/relation records must still
load. V2 object tests require `scope_kind`, `scope_ref`, `knowledge_role`,
`canonical_name`, aliases, review status, and lifecycle status. Legacy inline
expression/symbol/source fields remain readable but are not the new canonical
assertion shape.

Assertion tests require distinct id, object ref, predicate/field,
value/expression, framework, regime, conventions, assumptions/non-claims,
exact source-location refs, review state, contradiction refs, and
revision/supersession lineage. Two sources or conventions may assert different
definitions without duplicating or mutating object identity.

- [ ] **Step 2: Write failing relation/insight boundary tests**

V2 relations require typed subject/object refs, direction, conditions,
framework/regime, contradiction state, exact source refs, status, and
`claim_trust_transfer=forbidden`. Insight kinds are exactly interpretation,
analogy, conjecture, failed-route lesson, counterexample direction, conceptual
bridge, and open research direction.

- [ ] **Step 3: Implement compatibility-defaulted focused models**

Re-export v2 object/relation names after the model compatibility shards. Keep
legacy `subject_id`/`object_id`; derive typed refs only as compatibility
orientation until explicitly reviewed. New enveloped writes require v2 fields.

- [ ] **Step 3a: Implement assertion writers and field-level provenance**

New definitions, equations, convention-dependent properties, and source claims
write `PhysicsAssertionRecord`; they do not merge into the object identity
record. Relation assertions retain exact source locations and revision links.
Compatibility migration emits candidates from legacy inline assertions and
never auto-reviews them.

- [ ] **Step 4: Implement `InsightRecord`**

Fields: insight id/kind/statement, topic/program scope, grounding refs,
inferred-from refs, framework/regime, speculation level, counterevidence,
falsifiers/discriminating checks, open proof-obligation refs, review status,
checkpoint id, lifecycle status, source refs, created time, and fixed
`can_update_claim_trust=False`.

- [ ] **Step 5: Add migration audit without canonical rewrites**

Report exact v1 records, compatibility-derived fields, missing v2 review data,
and candidate revisions. Do not auto-fill source assertions or review status.

- [ ] **Step 6: Run object/relation/registry/index tests and commit**

Commit message: `v5: evolve physics knowledge records`.

## Task 2: Knowledge And Insight Candidate Pipeline

**Files:**
- Create: `brain/v5/knowledge_candidates.py`
- Create: `brain/v5/knowledge_promotion.py`
- Create: `brain/v5/knowledge_review.py`
- Create: `brain/v5/evidence_basis_policy.py`
- Create: `brain/v5/insights.py`
- Create: `brain/v5/knowledge_contracts.py`
- Create: `tests/test_v5_knowledge_candidates.py`
- Create: `tests/test_v5_insights.py`
- Create: `tests/test_v5_evidence_basis_policy.py`
- Modify: `brain/v5/literature_source_extraction.py`
- Modify: `brain/v5/research_distillation.py`
- Modify: `brain/v5/recording_batches.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/record_family_registry.py`
- Modify: `brain/v5/record_refs.py`
- Modify: `brain/v5/lifecycle_events.py`
- Modify: `brain/v5/evidence.py`
- Modify: `brain/v5/record_contracts.py`
- Modify: `brain/v5/pretool_policy.py`
- Modify: `brain/v5/policy.py`
- Modify: `brain/v5/trust_audit.py`
- Modify: `brain/v5/scope_revalidation.py`

**Interfaces:**
- Produces: `route_knowledge_candidate(candidate) -> CandidateRoute`
- Produces: `diagnose_knowledge_candidate(ws, candidate) -> CandidateDiagnostics`
- Produces: `build_knowledge_review_batch(ws, batch_ref) -> KnowledgeReviewBatch`
- Produces: `KnowledgeReviewDecisionRecord`, embedded `EvidenceBasisAudit`
- Produces: `promote_grounded_candidate`, `promote_insight_candidate`,
  `reject_knowledge_candidate`, `revise_knowledge_record`,
  `demote_knowledge_record`, and `invalidate_knowledge_record`
- Adds family: `knowledge_review_decisions`
- Consumes: exact `scope_revalidation_decision:` refs from M2 for
  cross-topic target inclusion.

- [ ] **Step 1: Write failing routing tests**

Definitions, formulas, conventions, relations, and derivations route to grounded
knowledge. Interpretation, analogy, conjecture, failed route, counterexample,
bridge, and open direction route to insight. Procedural repeatable workflows
route to M4 Skill candidates. Mixed candidates require explicit splitting.

- [ ] **Step 2: Remove physics-semantic fragments from skill distillation**

Add a regression test that `research_distillation` cannot emit a Skill candidate
for a definition, formula, derivation, interpretation, or insight.

- [ ] **Step 3: Implement grounding/contradiction diagnostics**

Require exact source asset plus location for grounded promotion; validate scope,
framework, regime, conventions, dependencies, contradictions, duplicate ids,
and unresolved refs. An inferred statement without source assertion routes to
insight even when source refs motivated it.

- [ ] **Step 4: Implement review-gated promotion**

Promotion consumes per-item review decisions bound to candidate/batch content
hashes, exact source refs, and a matching checkpoint subject/request hash.
Rejected/demoted/invalidated/superseded records retain canonical lifecycle
history and remain excluded from active retrieval. Source-byte, anchor,
contradiction, grounding, or framework changes create invalidation candidates;
they never mutate active reviewed content silently. No promotion function calls
evidence/trust writers.

- [ ] **Step 4a: Close the evidence-admissibility boundary**

Evidence recording resolves every basis ref. Reject insight, discovery/search
receipt, derived passage, summary/context, Skill, unreviewed candidate, and
unresolved knowledge refs as sole support. A reviewed grounded assertion may be
trace context only when the evidence also cites its pinned source locations,
validated derivation, or validated run/artifact basis. Enforce the same audit in
record contracts, pre-tool policy, trust audit, and promotion preflight. Add
negative tests proving an `insight:*` cannot be wrapped in Evidence to reach a
trust path.

Evidence v2 persists separate `support_basis_refs` and `trace_context_refs`.
The embedded audit binds policy version, evidence payload hash, per-ref role and
classification, resolved pinned refs/hashes, admissibility result, errors, and
audit hash. Mixed valid support plus insight is unambiguous: insight may remain
trace context but is never counted as support. Trust paths recompute/verify the
audit rather than trusting an arbitrary boolean.

- [ ] **Step 5: Integrate literature extraction and run regressions**

Literature extraction produces M1 staged candidates with equation/source
anchors. Run candidate, insight, literature, recording-batch, derivation, and
skill-boundary tests.

Add target-scope revalidation tests: a decision binds target scope, bridge and
imported content hashes, applicability, review/validation refs, expiry, and
supersession. Context resolves the exact decision ref; bridge status or a bare
checkpoint cannot move imported assertions out of the orientation-only lane.

- [ ] **Step 6: Commit Task 2**

Commit message: `v5: separate grounded knowledge and insight candidates`.

## Task 3: Versioned Source Shelf And Structured Ingestion

**Files:**
- Create: `brain/v5/source_shelf.py`
- Create: `brain/v5/literature_discovery.py`
- Create: `brain/v5/literature_discovery_contracts.py`
- Create: `brain/v5/source_acquisition.py`
- Create: `brain/v5/source_acquisition_contracts.py`
- Create: `tests/test_v5_source_shelf.py`
- Create: `tests/test_v5_literature_discovery.py`
- Create: `tests/test_v5_source_acquisition.py`
- Modify: `brain/v5/curated_rag_corpus.py`
- Modify: `brain/v5/curated_rag_contracts.py`
- Modify: `brain/v5/knowledge_connector_bindings.py`
- Modify: `brain/v5/literature_intake.py`
- Modify: `brain/v5/source_assets.py`
- Modify: `brain/v5/references.py`
- Modify: `brain/v5/source_reconstruction.py`
- Modify: `brain/v5/source_reconstruction_review.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/record_family_registry.py`
- Modify: `brain/v5/record_refs.py`
- Modify: `brain/v5/lifecycle_events.py`

**Interfaces:**
- Produces: `SourceShelfManifest`, `SourcePassage`
- Produces: `build_source_shelf(ws, request) -> SourceShelfBuildReport`
- Produces: `load_source_shelf(ws, generation) -> SourceShelf`
- Produces: `build_literature_discovery_request(ws, request) -> LiteratureDiscoveryRequest`
- Produces: `normalize_literature_discovery_result(request, connector_result) -> LiteratureDiscoveryReceipt`
- Produces: `SourceAcquisitionDecisionRecord`,
  `SourceAcquisitionReceiptRecord`, and `apply_source_acquisition_receipt`
- Adds families: `source_acquisition_decisions`, `source_acquisition_receipts`

- [ ] **Step 1: Write failing source identity/version tests**

Require source-asset ref, canonical URI, content hash, access/license note,
reader/extractor version, curation rationale, acquired time, and stale-source
diagnostics. Changed source bytes create a new derived generation.

- [ ] **Step 2: Write failing physics-aware chunk tests**

Boundaries preserve definitions, equations/labels, theorem/proposition labels,
derivation steps, figures/captions, caveats, bibliography anchors, symbols,
assumptions, nearby prose, page/section, and exact source-location refs.

- [ ] **Step 3: Implement a derived manifest, not a new truth store**

Source assets and reference locations remain canonical. Shelf manifests and
passages live under the disposable knowledge index. Store bounded passage text
and hashes; retain local source URI for reopening full content.

- [ ] **Step 4: Record failures and conservative access behavior**

Encrypted, missing, unsupported, changed, or license-restricted sources produce
explicit issues and incomplete coverage. Never silently omit a requested source.

- [ ] **Step 4a: Enforce typed acquisition and source reconstruction**

Bind allow/deny/review decision, policy basis, access/license disposition,
storage permission, connector/collector, canonical URI/identifier dedup key,
acquired byte hash, errors, and expiry. URI-only legacy intake is
`metadata_only` and cannot enter the shelf, grounded assertions, or source
reconstruction. Existing direct PDF acquisition routes through this decision
and receipt path.

Harden reconstruction so every definition/equation/assumption/step anchor
resolves through `ReferenceLocationRecord` to a hash-pinned `SourceAssetRecord`.
Unresolved labels and arbitrary `paper:*` strings remain orientation only and
cannot satisfy completeness. Replace the old false-complete fixture with
positive hash-pinned and negative unresolved/hash-mismatch cases.

- [ ] **Step 5: Preserve curated RAG compatibility**

Existing curated corpus/search/chunk APIs become adapters over the source shelf
where available and remain trust-neutral.

- [ ] **Step 6: Add bounded autonomous discovery handoff**

Build a request only from a persisted recall/knowledge gap. Bind normalized
query, topic/program/focus, framework/regime, required source types, prior audit
ref, connector allowlist, max results, timeout, dedup fingerprint, and expiry.
Normalize host-returned DOI/arXiv/URI/title/author/year candidates plus connector
coverage and errors. Search snippets and generated query expansions remain
process-only; only an acquired source with access decision, exact bytes/hash,
and location may enter source intake/shelf. Test repeated requests, wrong
framework, duplicate identifiers, partial connector failure, license denial,
and result-budget enforcement.

- [ ] **Step 7: Run shelf/discovery/intake regressions and commit**

Run source shelf, literature discovery/intake, connector, extraction, candidate,
registry, delta-index, and trust-boundary tests. Commit message:
`v5: add versioned physics source shelf and discovery`.

## Task 4: Hybrid Retrieval Components And Fusion

**Files:**
- Create: `brain/v5/knowledge_retrieval.py`
- Create: `brain/v5/formula_retrieval.py`
- Create: `brain/v5/graph_retrieval.py`
- Create: `brain/v5/retrieval_fusion.py`
- Create: `brain/v5/knowledge_snapshot.py`
- Create: `tests/test_v5_knowledge_retrieval.py`
- Create: `tests/fixtures/v5_retrieval/manifest.json`
- Create: `tests/fixtures/v5_retrieval/qft_qg_queries.json`

**Interfaces:**
- Produces: `KnowledgeQuery`, `KnowledgeSnapshotLineage`,
  `KnowledgeRetrievalCoverage`, `KnowledgeRetrievalResult`
- Produces: `search_fielded_lexical`, `search_formula`, `search_graph`, `search_dense_optional`
- Produces: `fuse_knowledge_rankings(results, policy) -> KnowledgeRetrievalResult`

- [ ] **Step 1: Build versioned evaluation fixtures before ranking code**

Include definitions, convention collisions, equivalent formula notation,
nearby but wrong frameworks, source caveats, derivation dependencies,
contradictory relations, grounded records, and speculative insights. Expected
relevance judgments are exact refs with grades.

- [ ] **Step 2: Implement deterministic fielded BM25-style baseline**

Index canonical names/aliases, formulas/symbols, framework/regime, assumptions,
non-claims, source anchors, relation statements, and passage text as separate
fields. Persist corpus statistics and expose field-level score contributions.

- [ ] **Step 3: Implement formula normalization**

Normalize TeX whitespace, harmless delimiters, indexed dummy symbols, and
commutative products only where declared safe. Preserve sign, normalization,
operator order, indices, and convention fields. Return both normalized and
original anchors.

- [ ] **Step 4: Implement typed graph traversal**

Traverse object/relation, derivation dependency, source, proof-obligation, and
formula-code edges with bounded depth and explicit path scores. Do not traverse
cross-topic support unless the consumer resolves a valid, unexpired,
unsuperseded exact `scope_revalidation_decision:` ref for the target scope.

- [ ] **Step 5: Define optional dense interface and reciprocal-rank fusion**

Dense retrieval is absent-by-default and disposable. Fusion preserves component
ranks/scores, grounded/speculative lane, scope filters, exclusions, and exact
refs. Generated query expansions have their own non-evidence provenance.

Bind every component to the effective record-index generation, selected-family
state/content watermarks, source-shelf generation/hash, and its component hash.
The result reports component status, stale/dirty/errors, checked/excluded scope,
fixed tie-break inputs, lane quotas, token allocation, truncation, and exact
pagination. Incompatible generations cannot be labeled complete. A corrupt or
missing formula sidecar degrades visibly to lexical/graph results. A missing or
corrupt graph projection either reconstructs a bounded graph from canonical
typed edges with checked paths/errors or degrades visibly to lexical-only;
neither path performs a hidden unbounded scan.

Dense results declare adapter/model/index versions, deterministic-mode flag,
timeout/error policy, input/result hash, and tie handling. A nondeterministic
adapter cannot alter a result labeled deterministic; deterministic evaluation
disables it or consumes only a captured hash-pinned result. Test deletion,
corruption, timeout, partial component failure, and repeatability for every
optional sidecar.

Default retrieval hard-filters incompatible framework/regime/convention hits.
Comparison/contradiction intent may return them only in a separate named lane.
Fix RRF constants, weights, tie rules, lane quotas, and fixture thresholds in
the versioned manifest before implementation.

- [ ] **Step 6: Measure quality and contamination**

Report recall@k, MRR/nDCG, exact-anchor recovery, convention mismatch rate,
wrong-framework contamination, grounded/insight cross-contamination, and
reasoning-intensive dependency recovery. Set fixture-versioned acceptance
thresholds before enabling a component in default context.

Add primary-topic, program/shared, and discovery lane tests; local insight is
isolated, every cross-topic assertion remains orientation until target review,
and all claim-trust-transfer paths are rejected.

- [ ] **Step 7: Run deterministic/repeatability tests and commit**

Commit message: `v5: add auditable hybrid knowledge retrieval`.

## Task 5: Knowledge Context Slice

**Files:**
- Create: `brain/v5/knowledge_context.py`
- Create: `brain/v5/knowledge_context_contracts.py`
- Create: `tests/test_v5_knowledge_context.py`
- Modify: `brain/v5/context_compiler.py`
- Modify: `brain/v5/context_pack.py`
- Modify: `brain/v5/context_profiles.py`

**Interfaces:**
- Produces: `KnowledgeContextRequest`, `KnowledgeContextSlice`
- Produces: `compile_knowledge_context(ws, request) -> KnowledgeContextSlice`

- [ ] **Step 1: Write failing separation/budget tests**

Grounded knowledge, exact source anchors, derivation dependencies, and
speculative insight have distinct headings and machine fields. Startup remains
under 800 estimated tokens; a normal knowledge expansion remains under 1,500.
Assert shared `KnowledgeSnapshotLineage`, selected-family content verification,
component failures, lane quotas, exact pagination, bytes, and token allocation.

- [ ] **Step 2: Add framework/regime/convention boundary**

For QFT/QG, every result declares framework, regime, convention compatibility,
grounding state, speculation level, checked scope, and exact expansion handles.

- [ ] **Step 3: Add exact expansion kinds**

Support source asset/location, passage/equation anchor, physics object,
relation, derivation chain/step, insight, and formula-code refs. Derived passage
refs resolve through a generation plus canonical source-location ref.

- [ ] **Step 4: Integrate into the unified context compiler**

The main compiler requests a knowledge slice only when objective/focus requires
it. It never loads all source passages or all insight. Retrieval errors and
excluded high-score candidates remain visible in coverage.

Compile current-topic results first, reviewed program/shared knowledge second,
and optional discovery last. Local insights never cross topic by default;
reviewed bridges carry exact target-side `scope_revalidation_decision:` refs and
cannot transfer claim trust. Imported content leaves the orientation-only lane
only after the compiler resolves a valid, unexpired, unsuperseded exact
revalidation decision ref.

- [ ] **Step 5: Run context/retrieval/trust tests and commit**

Commit message: `v5: compile bounded physics knowledge context`.

## Task 6: Facade, Evaluation, And M3 Acceptance

**Files:**
- Create: `brain/v5/mcp_knowledge.py`
- Create: `brain/v5/cli_knowledge.py`
- Create: `brain/v5/knowledge_surface_contracts.py`
- Create: `tests/test_v5_knowledge_facade.py`
- Create: `tests/test_v5_gate3_qft_qg_e2e.py`
- Create: `docs/superpowers/progress/2026-07-10-aitp-gate-3-release-audit.md`
- Modify: `brain/v5/capability_registry_data.py`
- Modify: `brain/v5/capability_surface_contracts.py`
- Modify: `brain/v5/public_surfaces.py`
- Modify: `brain/v5/mcp_tools.py`
- Modify: `brain/v5/cli.py`
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-07-09-aitp-final-research-lifecycle-roadmap.md`

- [ ] **Step 1: Register discovery/candidate/review/shelf/retrieval/context capabilities**

Assign read/runtime/kernel state effects precisely. Keep maintenance writes off
the compact surface; compact entry receives only bounded names/refs/context.
Discovery request/result normalization is read/runtime state only; source
acquisition and promotion remain separate capabilities.
Register deep validators, evidence-basis and pre-tool policy coverage, CLI/MCP
parity, and explicit compact visibility for every operation. Loader files receive
only focused-module imports.

- [ ] **Step 2: Add QFT/quantum-gravity vertical acceptance**

Ingest source-local notes and papers with conflicting conventions, extract
objects/relations/derivation candidates, review one grounded record and one
insight, retrieve by concept and formula, and compile context. Assert exact
anchors, correct regime, visible speculation, and no trust mutation.
This proves deterministic fixture-contract readiness only. It is not the real
QFT/QG acceptance claim; M6 must consume hash-pinned real source assets and
exact location receipts.

- [ ] **Step 3: Add contamination and missing-source failure cases**

Wrong-framework but lexically similar passages are excluded from default context
and appear only in an explicit comparison/contradiction lane. Missing or stale
sources make coverage incomplete and forbid source-exhaustive language.

- [ ] **Step 4: Run M0-M3 test lanes and real-store compatibility audit**

All pre-Gate-3 records remain readable. Retrieval fixtures meet versioned
thresholds, capability/family drift is zero, and architecture limits are
unchanged.

- [ ] **Step 5: Update docs, release audit, staged verification, and commit**

Commit message: `v5: complete M3 physics knowledge and insight`.

## M3 Completion Checklist

- [ ] Physics object/relation v1 records remain readable under v2.
- [ ] Grounded knowledge requires exact source identity and location.
- [ ] Source reconstruction cannot pass on unresolved labels or record presence.
- [ ] Physics object identity and source/convention assertions are separate.
- [ ] Insight is visibly speculative and never evidence.
- [ ] Evidence intake rejects insight/search/summary/Skill and unresolved
  knowledge as sole claim-support basis.
- [ ] Evidence v2 separates support basis from trace context and persists a
  policy-versioned, payload-hash-bound per-ref audit.
- [ ] Hash-bound review, revise, demote, invalidate, supersede, and target-scope
  revalidation preserve old versions and exact lifecycle refs.
- [ ] Physics semantic content cannot enter the Skill path.
- [ ] Source shelf versions identity, hash, extraction, access, and failures.
- [ ] Lexical, formula, graph, and optional dense components expose scores and coverage.
- [ ] Grounded and speculative lanes remain separate through fusion/context.
- [ ] QFT/QG context preserves framework, regime, conventions, and source anchors.
- [ ] A persisted knowledge gap can trigger bounded literature discovery, but
  search snippets/results cannot bypass source acquisition or review.
- [ ] Retrieval quality and contamination are measured on versioned fixtures.
- [ ] Formula/graph/dense sidecar deletion, corruption, timeout, and
  nondeterminism degrade visibly without hidden scans or false deterministic
  labels.
- [ ] M3 is fixture-contract complete only; real formal-theory acceptance is
  a mandatory M6 decision input.
- [ ] No knowledge/RAG/context operation updates claim trust directly.
