# AITP M1 Lifecycle And Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add multi-topic-safe session focus, canonical process closeout, auditable recall, coalesced recording candidates, and one host-neutral lifecycle facade on top of the M0 repository/query/context foundation.

**Architecture:** Keep `SessionBinding` single-topic and add reviewed sidecar scope records. Persist closeout, recall, and coalesced candidate batches as trust-neutral typed process records through `RecordRepository`; keep resume cards and startup files derived. Extend the M0 full-build index with a disposable write-through delta and per-family freshness tokens so lifecycle writes are immediately visible without rebuilding the whole store. Every startup/read path consumes the same indexed context and coverage boundary, and no lifecycle operation may rebind an active claim or update claim trust.

**Tech Stack:** Python 3.12, dataclasses, Markdown/YAML typed records, JSON runtime staging, M0 `RecordRepository`, generation-stamped retrieval, bounded context compiler, CapabilitySpec, pytest.

## Global Constraints

- M0 must be committed and its release audit green before M1 production code begins.
- `SessionBinding` remains single-topic; no M1 writer changes `active_claim`.
- Canonical process writes use `RecordRepository`; generated resume/startup files are disposable.
- A canonical write commits before its delta projection. Delta failure is visible,
  cannot roll back canonical truth, and permits only exact or bounded strict
  single-family fallback until repair.
- A failed or skipped projection makes the family durably dirty. A later
  successful write cannot advance that family back to fresh unless predecessor
  continuity is proven; only a verified family repair or full canonical rebuild
  may clear the dirty state.
- Lock acquisition order is `base-build -> canonical-mutation -> canonical-record -> delta-manifest`;
  a code path may omit locks but may never
  acquire them in a later-to-earlier order. M1 deliberately serializes the
  low-rate canonical write/repair path to make publication correctness primary;
  no canonical record lock is acquired while holding the delta lock.
- Fast state-token agreement is sufficient only for orientation freshness.
  Exhaustive/no-result language requires a strong selected-family content
  watermark check and `derived == canonical-before == canonical-after`.
- Scoped recall compares only the required family tokens. An unrelated process
  write cannot invalidate scientific coverage, and an audit write cannot certify
  the `recall_audits` family that it changes itself.
- `claim_trust_transfer` is always `forbidden` for cross-topic relations and context.
- A focus, closeout, recall, or recording batch has `trust_effect=none`.
- Raw recording staging may expire and is not canonical research state.
- One milestone produces at most one default candidate batch and one closeout id.
- Stale or failed required recall blocks exhaustive language, major conclusions, and expensive runs.
- Existing compact MCP tools remain bounded; lifecycle operations route through existing facade concepts unless a direct full-surface operation is required.
- Every new family is declared in `RecordFamilySpec`, exact refs, inventory, query index, context coverage, public contracts, CapabilitySpec, and tests.
- Preserve the independent Harness Feedback working-tree changes.

---

## File Structure

| File | Responsibility |
|---|---|
| `brain/v5/lifecycle_models.py` | M1 canonical process dataclasses. |
| `brain/v5/query_index.py` | Strong full build, v1/v2 read compatibility, and the v3 immutable root manifest. |
| `brain/v5/query_index_generation.py` | Immutable generation preparation and serialized publication. |
| `brain/v5/query_index_locking.py` | Ranked OS advisory locks, explicit leases, inversion checks, and owner-death recovery. |
| `brain/v5/query_index_accumulator.py` | Rebuildable dual-hash family accumulator with O(1) record replacement. |
| `brain/v5/query_index_documents.py` | Deterministic document, lexical, and hashing primitives. |
| `brain/v5/query_index_state.py` | Fast metadata-only family state snapshots for orientation. |
| `brain/v5/query_index_delta.py` | Write-through projection facade, dirty marking, and compaction entrypoint. |
| `brain/v5/query_index_delta_contracts.py` | Delta lineage and scoped-freshness contracts. |
| `brain/v5/query_index_delta_storage.py` | Atomic delta manifest storage and base-lineage validation. |
| `brain/v5/query_index_snapshot.py` | Coherent root/delta reads, overlay, and scoped freshness. |
| `brain/v5/query_index_delta_repair.py` | Strong full-family repair and the only dirty-state clearing path. |
| `brain/v5/query_index_family_scan.py` | Independent strong canonical family reconstruction. |
| `brain/v5/query_index_fallback.py` | Explicit bounded single-family canonical fallback. |
| `brain/v5/research_scope.py` | Program, focus-set, cross-topic-relation writes and scope resolution. |
| `brain/v5/research_scope_contracts.py` | Scope/ref/transfer-policy validation. |
| `brain/v5/session_lifecycle.py` | Closeout plan and canonical closeout write. |
| `brain/v5/session_lifecycle_contracts.py` | Closeout contract and trust boundary. |
| `brain/v5/session_resume.py` | Derived resume card from closeout, focus, and current indexed state. |
| `brain/v5/recall_audit.py` | Multi-lane persisted recall and prerequisite gates. |
| `brain/v5/recall_audit_contracts.py` | Coverage, staleness, and exhaustive-language validation. |
| `brain/v5/recording_batches.py` | Runtime staging, semantic deduplication, durable batch coalescing. |
| `brain/v5/recording_batch_contracts.py` | Candidate and batch validation. |
| `brain/v5/mcp_session_lifecycle.py` | Host-neutral M1 MCP wrappers. |
| `brain/v5/cli_session_lifecycle.py` | PowerShell-safe M1 CLI routes. |

## Task 0: Incremental Query Overlay And Family-Scoped Freshness

**Files:**
- Create: `brain/v5/query_index_generation.py`
- Create: `brain/v5/query_index_locking.py`
- Create: `brain/v5/query_index_delta.py`
- Create: `brain/v5/query_index_delta_contracts.py`
- Create: `brain/v5/query_index_accumulator.py`
- Create: `brain/v5/query_index_documents.py`
- Create: `brain/v5/query_index_state.py`
- Create: `brain/v5/query_index_delta_storage.py`
- Create: `brain/v5/query_index_snapshot.py`
- Create: `brain/v5/query_index_delta_repair.py`
- Create: `brain/v5/query_index_family_scan.py`
- Create: `brain/v5/query_index_fallback.py`
- Create: `tests/test_v5_query_index_delta.py`
- Create: `tests/test_v5_query_index_concurrency.py`
- Create: `tests/test_v5_query_index_accumulator.py`
- Modify: `brain/v5/query_index.py`
- Modify: `brain/v5/query_index_contracts.py`
- Modify: `brain/v5/research_retrieval.py`
- Modify: `brain/v5/record_repository.py`
- Modify: `brain/v5/record_repository_contracts.py`
- Modify: `tests/test_v5_query_index.py`
- Modify: `tests/test_v5_research_retrieval.py`
- Modify: `tests/test_v5_record_repository.py`
- Modify: `tests/test_v5_context_performance.py`

**Interfaces:**
- Produces: v3 `IndexManifest`, `IndexDeltaEntry`, `IndexDeltaManifest`,
  `DirtyFamilyState`, `IndexProjectionOutcome`, `EffectiveIndexSnapshot`, and
  `ScopedIndexFreshness`.
- Produces: `IndexBuildLease` and
  `acquire_index_build_lease(ws, reason)`; generation prepare/publish are lease
  methods that reject inactive, foreign-thread, or already-released leases. The
  existing `build_query_index` remains a compatibility facade over one complete
  lease transaction.
- Produces: `CanonicalMutationLease` and
  `acquire_canonical_mutation_lease(ws)` for repository/repair/projector lock
  ownership without reentrant acquisition.
- Produces: `project_record_delta(ws, record_ref)`,
  `load_effective_query_index(ws)`, `repair_query_delta(ws, families)`, and
  `compact_query_delta(ws)`.

- [x] **Step 1: Write failing write-through and scoped-freshness tests**

Use deterministic `threading.Event` barriers and named failpoints, never sleeps,
to cover create, revision, idempotent repeat, corrupt delta, deterministic
overlay ordering, deleting/rebuilding all derived files, and these required
publication failures:

- projection A fails, then projection B in the same family succeeds but cannot
  clear the continuity gap or make the family fresh;
- compaction begins with an already-dirty family and clears it only after a
  full strong canonical proof;
- a repository write started during full build waits on `canonical-mutation`,
  then projects against the newly published base without becoming lost;
- family repair races a same-ref revision and cannot overwrite the newer row;
- two full builders compete and cannot reserve or mutate one generation;
- an out-of-band ABA mutation occurs during a full scan;
- process interruption occurs after generation components, after a delta row,
  after root-manifest replacement, and before delta rebase;
- a normal full rebuild starts with a nonempty clean delta and finishes with one
  coherently rebound/empty delta rather than a successful-but-stale root;
- a reader observes each root/delta publication boundary and either retries to
  one coherent snapshot or returns scoped stale diagnostics;
- a real M0 schema-v1 root fixture loads conservatively, refuses delta
  freshness before migration, and migrates on a successful rebuild;
- lock inversion is rejected by the shared ranked-lock helper, and terminating a
  subprocess that owns `base-build` or `canonical-mutation` releases the OS lock
  so the next process can recover.

Also prove deterministic rebuilds produce byte-identical document, lexical,
and issue components, equal component/content hashes, and equal query ordering
for the same canonical snapshot; generation ids and build timestamps are the
only excluded metadata. This task guarantees process-interruption consistency,
not filesystem power-loss durability where Python/Windows cannot durably sync a
directory rename. Add this lifecycle regression first:

```python
def test_appending_recall_audit_does_not_self_invalidate_checked_claim_scope(tmp_path):
    ws = indexed_workspace_with_claim(tmp_path)
    before = query_records(ws, ResearchQuery(families=("claims",)))
    assert before.coverage.exhaustive is True
    write_recall_audit_through_repository(ws)
    after = query_records(ws, ResearchQuery(families=("claims",)))
    assert after.coverage.exhaustive is True
    assert after.coverage.scope_fresh is True
    assert after.coverage.global_fresh is True
```

Also prove an out-of-band write without a delta makes only the affected family
stale, an unscoped query becomes globally stale, and metadata-preserving edits
cannot authorize exhaustive language without a new strong content check.

- [x] **Step 2: Run RED**

Expected: missing generation/delta modules, manifest discriminators, projection
outcomes, ranked locks, coherent snapshot reads, and scoped coverage fields.

- [x] **Step 3: Add ranked locks and a discriminated v1/v2/v3 manifest loader**

Add `manifest_kind="query_index_root"` and `schema_version=3` to the root
pointer. Its immutable base descriptor defines `base_content_hash` exactly as
SHA-256 over canonical JSON containing schema version, canonical watermark,
per-family content watermarks and accumulator states, component hashes,
record/family counts, and malformed/family counts; generation id and `built_at`
are excluded. An absent discriminator is parsed only as the M0 legacy
single-generation shape. Schema-v1 and schema-v2 roots remain readable for
orientation and migration, but delta projection returns `migration_required`,
preserves canonical success, and cannot claim fresh until a successful v3
rebuild.

Implement ranked locks with the fixed order
`base-build -> canonical-mutation -> canonical-record -> delta-manifest`.
Use OS advisory locks that the kernel releases on owner death; persistent lock
files are identities, not ownership claims. `IndexBuildLease` holds
`base-build` and `canonical-mutation` across unique generation reservation,
preparation, root publication, and delta rebase. `CanonicalMutationLease` holds
the mutation lock across repository canonical commit plus projection and full
repair. Existing per-record compare-and-swap behavior remains nested inside
that lease. Internal helpers require the active lease explicitly and never
reacquire it; public projector/build facades acquire a lease only when one was
not supplied. `__exit__` releases locks and records any unpublished generation
as removable derived garbage.

- [x] **Step 4: Publish only content-proven immutable generations**

Persist state tokens and strong content watermarks per family. Write components
and an immutable generation descriptor beneath an unpublished
`indexes/generations/<generation>/` directory. Publication requires component
hash verification and, for every family,
`derived_content_watermark == canonical_before == canonical_after`; include
malformed path/byte hashes in all three values. Atomically replace only the
small root pointer after that proof. A rejected/interrupted build leaves an
unreferenced generation that readers ignore and repair may remove. All full
build and compaction callers use the lease's one publication primitive; there
is no second unsafe standalone path. Every v3 root publication also acquires the
delta lock, revalidates its snapshot, and publishes a delta manifest bound to
the new base. A content-proven base may absorb and clear pre-snapshot rows and
dirty markers; hash-changed later rows are retained. Normal return is therefore
coherent even when the old base had a nonempty delta. Interruption between root
and delta replacement remains fail-closed as an explicit lineage mismatch.

- [x] **Step 5: Implement continuity-preserving write-through projection**

After a successful create or revision, project the exact canonical ref into a
latest-row file keyed by `sha256(record_ref)`, then atomically advance a delta
manifest that binds the root base generation and base-manifest content hash.
The manifest carries a monotonically increasing delta generation, per-family
state/content tokens, rebuildable family accumulator states, a predecessor chain
token, durable `dirty_families`, and the content hash of every referenced delta
row. `RecordRepository` captures both the effective family predecessor
watermark and the previous exact-record content hash before commit. A clean
family advances by removing that predecessor pair and adding the committed pair
in O(1), without rescanning canonical family content. Advance only when the
manifest's effective predecessor matches the captured predecessor. A gap,
corrupt/missing row, base mismatch, missing accumulator, or failed projection
marks that family dirty; a later successful row may be retained but cannot clear
the marker or advance exhaustive freshness.

Idempotent writes create no duplicate row and may restore a missing row only
while continuity is intact; a dirty family requires full family repair.
Revision replaces the row for the same canonical ref. Publish rows before the
manifest so interruption leaves an ignored orphan. Extend `WriteResult` with a
typed `IndexProjectionOutcome(status, dirty_families, diagnostics,
repair_required)` using statuses `projected`, `unchanged`, `dirty`,
`migration_required`, and `not_configured`; projection failure leaves canonical
success intact. Existing writers that bypass `RecordRepository` are detected by
family-token mismatch.
The repository passes its active `CanonicalMutationLease` and captured
predecessor to the locked projector helper. Standalone projection without a
lease acquires one and can only prove current continuity or mark/repair dirty,
so it cannot self-deadlock or invent a missing predecessor.

- [x] **Step 6: Add coherent reads, strong scoped freshness, and race-safe repair**

Overlay replaces base rows by `record_ref`, preserves deterministic ranking,
and reports base/delta lineage. A reader hashes the root pointer, validates the
base, reads and validates the bound delta and rows, then re-reads both manifest
hashes. It retries a bounded number of times if either changed; corruption or
retry exhaustion is converted at the public retrieval boundary into typed
scoped stale/read-error diagnostics rather than an uncaught
`IndexIntegrityError`.

Expose orientation `scope_state_fresh` separately from
`scope_content_verified`. Exhaustive/no-result language requires both, no dirty
family, no malformed/read error, and no truncation. If one requested family is
stale, allow a strict bounded scan of that family only when the caller opts in;
expose checked paths, malformed records, and `fallback_used=True`.

The strong selected-family check briefly holds `canonical-mutation` while
hashing the selected canonical paths, providing a linearization point against
all repository writes. Direct out-of-band filesystem mutation remains an
unsupported concurrent writer and is detected by before/after content checks.

Repair holds `canonical-mutation`, computes strong canonical-before, rebuilds
every row for each requested family, computes canonical-after, requires
`derived == before == after`, then takes the delta lock and uses a manifest
generation/base CAS before publication. It never publishes a previously read
row after a revision and is the only delta operation allowed to clear a dirty
family.

- [x] **Step 7: Compact without losing writes or masking gaps**

Compaction snapshots the current delta, builds and verifies an unpublished full
generation under `base-build` and the canonical snapshot lock, and rejects
publication unless the strong three-way content proof succeeds. Under the delta
lock it rechecks base/delta generations, atomically swaps the root pointer, and
removes only snapshot entries whose hashes still match. Entries written or
replaced after the snapshot are retained and rebound to the new base. A dirty
marker clears only for families included in the verified full generation. A
crash before root swap leaves the old base authoritative; a crash after it
leaves either a valid rebased delta or a base-lineage mismatch that public reads
report as stale, never a silently dropped write.

- [x] **Step 8: Run M0 retrieval/repository/context regressions**

Run the new tests plus M0 query index, retrieval, repository, context,
architecture, and performance tests. Assert normal write-through remains under
100 ms on the versioned fixture and warm scoped query remains under one second.

Acceptance evidence on 2026-07-13, using a fresh disposable 10,000-record Temp
fixture: cold compact context 0.937 s, warm compact context p95 0.095 s, warm
timeline p95 0.605 s, exact-ref p95 0.0033 s, and five repository write-through
operations p95 0.061 s. The opt-in performance test now enforces all thresholds.

- [x] **Step 9: Commit Task 0**

Commit message: `v5: add incremental query index overlay`.

## Task 1: M1 Record Models And Family Registry

**Files:**
- Create: `brain/v5/lifecycle_models.py`
- Create: `tests/test_v5_lifecycle_models.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/record_family_registry.py`
- Modify: `tests/test_v5_record_family_registry.py`

**Interfaces:**
- Produces: `ResearchProgramRecord`, `SessionFocusSetRecord`, `CrossTopicRelationRecord`
- Produces: `SessionCloseoutRecord`, `RecallAuditRecord`, `RecordingCandidateBatchRecord`
- Produces: `CloseoutBoundaryItem`
- Produces exact-ref families `research_programs`, `session_focus_sets`, `cross_topic_relations`, `session_closeouts`, `recall_audits`, and `recording_candidate_batches`.

- [x] **Step 1: Write the failing model and family tests**

```python
def test_gate1_families_are_trust_neutral_and_exact_expandable():
    specs = record_family_specs()
    for family in GATE1_FAMILIES:
        spec = specs[family]
        assert spec.record_class is not None
        assert spec.trust_effect == "none"
        assert {"exact_ref", "inventory", "query_index", "context_compiler"} <= spec.participates_in


def test_cross_topic_relation_forbids_claim_trust_transfer():
    record = CrossTopicRelationRecord(
        relation_id="bridge-1",
        source_topic_id="qg-a",
        target_topic_id="qg-b",
        source_ref="derivation_chain:d1",
        target_ref="question:q1",
        relation_kind="method_applicability",
        transfer_rationale="same convention after target-side check",
        applicability_boundary="does not transfer a proved claim",
        revalidation_requirements=["check target conventions"],
    )
    assert record.claim_trust_transfer == "forbidden"
    assert record.can_update_claim_trust is False
```

- [x] **Step 2: Run RED**

Run:

```powershell
python -m pytest tests\test_v5_lifecycle_models.py tests\test_v5_record_family_registry.py -q -p no:cacheprovider --basetemp "$env:TEMP\aitp-g1-models-red"
```

Expected: imports/family assertions fail because M1 models are absent.

- [x] **Step 3: Implement focused dataclasses**

Use these required identity and boundary fields:

```python
@dataclass
class SessionFocusSetRecord:
    focus_set_id: str
    session_id: str
    primary_topic_id: str
    focus_kind: str
    focus_ref: str
    supporting_refs: list[str] = field(default_factory=list)
    excluded_refs: list[str] = field(default_factory=list)
    objective_refs: list[str] = field(default_factory=list)
    program_id: str = ""
    scope_status: str = "active"
    source_refs: list[str] = field(default_factory=list)
    created_at: str = ""
    claim_trust_transfer: str = "forbidden"
    can_update_active_claim: bool = False
    can_update_claim_trust: bool = False
    kind: str = "session_focus_set"
```

Define the other canonical records with these exact fields:

```python
@dataclass
class ResearchProgramRecord:
    program_id: str
    title: str
    primary_topic_ids: list[str]
    supporting_topic_ids: list[str] = field(default_factory=list)
    scientific_boundary: str = ""
    inclusion_rules: list[str] = field(default_factory=list)
    exclusion_rules: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    review_status: str = "pending_review"
    checkpoint_id: str = ""
    created_at: str = ""
    claim_trust_transfer: str = "forbidden"
    can_update_claim_trust: bool = False
    kind: str = "research_program"


@dataclass
class CrossTopicRelationRecord:
    relation_id: str
    source_topic_id: str
    target_topic_id: str
    source_ref: str
    target_ref: str
    relation_kind: str
    transfer_rationale: str
    applicability_boundary: str
    revalidation_requirements: list[str]
    source_refs: list[str] = field(default_factory=list)
    status: str = "pending_review"
    checkpoint_id: str = ""
    created_at: str = ""
    claim_trust_transfer: str = "forbidden"
    can_update_claim_trust: bool = False
    kind: str = "cross_topic_relation"


@dataclass
class CloseoutBoundaryItem:
    text: str
    boundary_class: str
    source_refs: list[str]
    scope: str = ""
    conditions: list[str] = field(default_factory=list)
    requires_exact_expansion: bool = True
    can_update_claim_trust: bool = False


@dataclass
class SessionCloseoutRecord:
    closeout_id: str
    session_id: str
    topic_id: str
    milestone_id: str
    focus_set_ref: str = ""
    objective_refs: list[str] = field(default_factory=list)
    completed_work: list[str] = field(default_factory=list)
    can_say: list[CloseoutBoundaryItem] = field(default_factory=list)
    cannot_say: list[CloseoutBoundaryItem] = field(default_factory=list)
    open_gaps: list[CloseoutBoundaryItem] = field(default_factory=list)
    failed_routes: list[CloseoutBoundaryItem] = field(default_factory=list)
    unverified_notes: list[CloseoutBoundaryItem] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    source_record_refs: list[str] = field(default_factory=list)
    pending_candidate_batch_refs: list[str] = field(default_factory=list)
    reusable_workflow_candidate_refs: list[str] = field(default_factory=list)
    index_generation: int = 0
    base_index_generation: int = 0
    delta_generation: int = 0
    canonical_watermark: str = ""
    retrieval_scope_token: str = ""
    family_state_tokens: dict[str, str] = field(default_factory=dict)
    family_content_watermarks: dict[str, str] = field(default_factory=dict)
    dirty_families: list[str] = field(default_factory=list)
    checked_families: list[str] = field(default_factory=list)
    read_errors: list[str] = field(default_factory=list)
    coverage_content_verified: bool = False
    coverage_exhaustive: bool = False
    operator: str = ""
    created_at: str = ""
    can_update_claim_trust: bool = False
    kind: str = "session_closeout"


@dataclass
class RecallAuditRecord:
    audit_id: str
    session_id: str
    topic_id: str
    query_text: str
    normalized_intent: str
    scope_refs: list[str]
    lanes: list[dict] = field(default_factory=list)
    index_generation: int = 0
    base_index_generation: int = 0
    delta_generation: int = 0
    canonical_watermark: str = ""
    retrieval_scope_token: str = ""
    family_state_tokens: dict[str, str] = field(default_factory=dict)
    family_content_watermarks: dict[str, str] = field(default_factory=dict)
    dirty_families: list[str] = field(default_factory=list)
    checked_families: list[str] = field(default_factory=list)
    unchecked_families: list[str] = field(default_factory=list)
    records_read: int = 0
    top_refs: list[str] = field(default_factory=list)
    excluded_candidates: list[str] = field(default_factory=list)
    read_errors: list[str] = field(default_factory=list)
    truncated: bool = False
    stale: bool = False
    content_verified: bool = False
    exhaustive: bool = False
    can_claim_no_result: bool = False
    created_at: str = ""
    can_update_claim_trust: bool = False
    kind: str = "recall_audit"


@dataclass
class RecordingCandidateBatchRecord:
    batch_id: str
    session_id: str
    topic_id: str
    milestone_id: str
    candidates: list[dict]
    dedup_keys: list[str]
    source_event_refs: list[str] = field(default_factory=list)
    missing_prerequisites: list[str] = field(default_factory=list)
    status: str = "pending_review"
    expires_at: str = ""
    supersedes: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    created_at: str = ""
    can_update_claim_trust: bool = False
    kind: str = "recording_candidate_batch"
```

Use `default_factory` for every collection. A resume card remains a derived
dictionary and is not a canonical dataclass.

Implementation note: every persisted trust-authority field is validated at
construction and readback. `SessionCloseoutRecord` locally materializes its
nested boundary mappings as `CloseoutBoundaryItem`; the generic legacy
materializer remains unchanged.

- [x] **Step 4: Register all six families**

Add `_REGISTRY_ROWS`, aliases, ref kinds, process/orientation roles, append-only
families, bounded auto-write policy, and surfaces. Re-export the classes from
`models.py` after the compatibility shards load.

- [x] **Step 5: Run GREEN and architecture checks**

Run:

```powershell
python -m pytest tests\test_v5_lifecycle_models.py tests\test_v5_record_family_registry.py tests\test_v5_record_envelope.py tests\test_v5_query_index.py tests\test_v5_architecture_boundaries.py -q -p no:cacheprovider --basetemp "$env:TEMP\aitp-g1-models-green"
```

- [x] **Step 6: Commit Task 1**

Commit message: `v5: add M1 lifecycle record families`.

## Task 2: Programs, Focus Sets, And Cross-Topic Bridges

**Files:**
- Create: `brain/v5/research_scope.py`
- Create: `brain/v5/research_scope_contracts.py`
- Create: `tests/test_v5_research_scope.py`
- Create: `tests/test_v5_context_disclosure.py`
- Modify: `brain/v5/active_claim_focus.py`
- Modify: `brain/v5/context_compiler.py`
- Modify: `brain/v5/context_compiler_contracts.py`

**Interfaces:**
- Produces: `record_research_program(ws, record, *, actor) -> WriteResult`
- Produces: `record_session_focus_set(ws, record, *, actor) -> WriteResult`
- Produces: `record_cross_topic_relation(ws, record, *, actor) -> WriteResult`
- Produces: `resolve_session_scope(ws, session_id, *, include_discovery=False) -> ScopeResolution`
- Extends `ContextRequest.disclosure_level` with the closed set
  `route_hint|startup_orientation|normal_research|exact_expansion`.

```python
@dataclass(frozen=True)
class ScopeResolution:
    session_id: str
    primary_topic_id: str
    focus_set_ref: str
    program_id: str
    primary_refs: tuple[str, ...]
    supporting_topic_ids: tuple[str, ...]
    supporting_refs: tuple[str, ...]
    excluded_refs: tuple[str, ...]
    unresolved_refs: tuple[str, ...]
    discovery_refs: tuple[str, ...]
    requires_revalidation_refs: tuple[str, ...]
    claim_trust_transfer: str = "forbidden"
```

- [x] **Step 1: Write failing scope-isolation tests**

Cover all allowed `focus_kind` values: `question`, `claim`, `route`,
`work_package`, `source_set`, `code_change`, and `run_campaign`.

```python
def test_focus_sidecar_does_not_rebind_session_claim(tmp_path):
    ws = _workspace_with_two_topics(tmp_path)
    before = get_session_binding(ws, "s1")
    record_session_focus_set(ws, SUPPORTING_FOCUS, actor=ACTOR)
    after = get_session_binding(ws, "s1")
    assert after.active_claim == before.active_claim


def test_cross_topic_bridge_requires_typed_refs_and_revalidation(tmp_path):
    with pytest.raises(ValueError, match="revalidation"):
        record_cross_topic_relation(ws, replace(BRIDGE, revalidation_requirements=[]), actor=ACTOR)
```

Also test excluded scope, ambiguous primary scope, stale focus refs, same-topic
bridges, unknown ref kinds, and `claim_trust_transfer != forbidden`.

- [x] **Step 2: Run RED**

Run the new test module with a writable basetemp. Expected: missing module.

- [x] **Step 3: Implement validators and repository writers**

Validate typed refs through the generated record-family registry. Validate
source/target existence with exact repository reads, but allow an explicitly
`pending_target` bridge only when it remains excluded from context. Writers use
`WritePolicy(create_or_idempotent)` and never call `bind_session`.

- [x] **Step 4: Implement scope resolution**

Return primary, supporting, excluded, unresolved, and optional discovery lanes
separately. Program/shared records may orient the target topic; cross-topic
scientific support remains `requires_target_revalidation=True`.

- [x] **Step 5: Feed scope into context requests**

Extend `ContextRequest` with optional `focus_set_ref`, `program_id`, and
`include_cross_topic_discovery=False`, plus the required disclosure level.
Query the primary topic first, then the program/shared lane. Enforce the fixed
ladder: route hints contain no scientific content; startup is orientation only;
normal research returns one query-planned slice; exact expansion returns only
paginated canonical records or anchored source passages. Every level reports
checked/unchecked scope, read errors, and next-level handles. Never merge
cross-topic trust or active-claim state, and never convert `not_checked` or
`not_shown` into `not_found`.

- [x] **Step 6: Run M0 plus scope tests**

Run the scope module, context compiler, active-claim focus, retrieval, and
record-ref tests. Verify the same session binding file hash before/after.

Implementation evidence (2026-07-13):

- Initial RED produced 22 expected failures for the missing scope module and
  disclosure fields. Independent review then reproduced five valid boundary
  gaps: non-exact explicit-ref scope bypass, missing canonical exact payloads,
  inactive explicit focus selection, page-local exact coverage overclaim, and
  topicless bridge endpoints. The reported blank-`created_at` issue was not a
  defect because the repository persists the generated envelope timestamp.
  Additional RED tests reproduced omitted-support accounting (`1 failed`) and
  inactive program routing (`3 failed`).
- `ContextRequest` now has the closed disclosure ladder plus optional focus,
  program, and discovery inputs. Route hints contain handles only; startup uses
  orientation-only support handles; normal context uses one primary-topic query
  plus exact reviewed support; exact expansion returns canonical typed payloads
  with bounded truthful pagination. Scope-excluded/discovery refs remain
  distinct from `not_found`. Reviewed support omitted by the normal record
  budget is counted and exposed through bounded exact-expansion handles rather
  than silently disappearing.
- Focus lookup uses cached orientation state tokens and exact reads, with a
  bounded single-family canonical fallback only when state is stale. This keeps
  routing trust-neutral while refusing malformed or unreadable focus records.
  Explicit focus must be active, and a program enters active session scope only
  when its review status is `reviewed` or `approved`.
- Final scope/disclosure/compiler suite: 58 passed. Direct context, retrieval,
  active-focus, context-pack, public-surface, family-registry, and architecture
  regression: 117 passed. Query-index/concurrency/repository/envelope: 101
  passed. Runtime audit, architecture, multi-topic, and QFT/QG verticals: 22
  passed, 1 explicitly skipped because `AITP_RUN_REAL_VERTICAL_PROBES=1` was not
  enabled.
- Disposable 10k fixture: cold context 0.9166s, warm context p95 0.0875s,
  timeline p95 0.6436s, exact-ref p95 0.00341s, and write-through p95 0.0624s.
  The largest touched v5 modules are 448 lines, below the 500-line architecture
  limit.
- Protected user-work diff hashes remained
  `f4651e2355ca5e394bf2f96fed8b76b209969055` and
  `3c0ca5a7b2ed30e0f32d43d3d1aa0e83330823a1`.

- [x] **Step 7: Commit Task 2**

Commit message: `v5: add isolated research session scope`.

## Task 3: Canonical Closeout And Derived Resume

**Files:**
- Create: `brain/v5/session_lifecycle.py`
- Create: `brain/v5/session_lifecycle_contracts.py`
- Create: `brain/v5/session_resume.py`
- Create: `tests/test_v5_session_lifecycle.py`
- Modify: `brain/v5/quiet_checkpoint.py`
- Modify: `brain/v5/closeout_completeness.py`
- Modify: `brain/v5/topic_status_startup.py`
- Modify: `brain/v5/topic_status.py`
- Modify: `brain/v5/workspace_refresh.py`

**Interfaces:**
- Produces: `SessionCloseoutRequest`, `SessionCloseoutPlan`
- Produces: `build_session_closeout_plan(ws, request: SessionCloseoutRequest) -> SessionCloseoutPlan`
- Produces: `record_session_closeout(ws, plan, *, actor) -> WriteResult`
- Produces: `build_session_resume_card(ws, session_id, *, max_tokens=800) -> dict[str, Any]`

```python
@dataclass(frozen=True)
class SessionCloseoutRequest:
    session_id: str
    milestone_id: str
    completed_work: tuple[str, ...]
    can_say: tuple[CloseoutBoundaryItem, ...]
    cannot_say: tuple[CloseoutBoundaryItem, ...]
    open_gaps: tuple[CloseoutBoundaryItem, ...]
    failed_routes: tuple[CloseoutBoundaryItem, ...]
    next_actions: tuple[str, ...]
    source_record_refs: tuple[str, ...]
    pending_candidate_batch_refs: tuple[str, ...] = ()
    reusable_workflow_candidate_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class SessionCloseoutPlan:
    record: SessionCloseoutRecord
    missing_requirements: tuple[str, ...]
    unresolved_refs: tuple[str, ...]
    allowed: bool
    can_update_claim_trust: bool = False
```

- [x] **Step 1: Write failing closeout tests**

```python
def test_one_closeout_is_idempotent_and_has_no_trust_effect(tmp_path):
    request = SessionCloseoutRequest(
        session_id="s1",
        milestone_id="m1",
        completed_work=("finite diagnostic completed",),
        can_say=(CloseoutBoundaryItem(
            text="finite diagnostic completed",
            boundary_class="finite_evidence",
            source_refs=["tool_run:run-1"],
        ),),
        cannot_say=(CloseoutBoundaryItem(
            text="no thermodynamic-limit proof",
            boundary_class="open_gap",
            source_refs=["proof_obligation:large-L"],
        ),),
        open_gaps=(CloseoutBoundaryItem(
            text="large-L proof",
            boundary_class="open_gap",
            source_refs=["proof_obligation:large-L"],
        ),),
        failed_routes=(CloseoutBoundaryItem(
            text="naive extrapolation",
            boundary_class="finite_evidence",
            source_refs=["research_route:naive-extrapolation"],
        ),),
        next_actions=("derive the finite-size bound",),
        source_record_refs=("tool_run:run-1",),
        pending_candidate_batch_refs=(),
        reusable_workflow_candidate_refs=(),
    )
    plan = build_session_closeout_plan(ws, request)
    first = record_session_closeout(ws, plan, actor=ACTOR)
    second = record_session_closeout(ws, plan, actor=ACTOR)
    assert (first.status, second.status) == ("created", "unchanged")
    assert get_claim(ws, "claim-1") == original_claim


def test_resume_card_is_derived_and_preserves_can_and_cannot_say(tmp_path):
    card = build_session_resume_card(ws, "s1")
    assert card["can_say"][0]["boundary_class"] == "finite_evidence"
    assert card["can_say"][0]["source_refs"] == ["tool_run:run-1"]
    assert card["cannot_say"][0]["boundary_class"] == "open_gap"
    assert card["orientation_only"] is True
    assert card["can_update_claim_trust"] is False
```

Test failed routes, gaps, next actions, candidate refs, reusable-workflow refs,
coverage/read errors, checked-family state/content tokens, dirty families,
content-verification status, unrelated versus relevant post-closeout writes, no
active claim, stale index, revision, and byte/token limits.

- [x] **Step 2: Run RED**

Expected: missing lifecycle/resume modules.

- [x] **Step 3: Implement closeout planning and write**

Derive deterministic `closeout_id` from session plus milestone id. Require the
current session/focus refs and a coverage snapshot. Preserve explicit can-say,
cannot-say, failed routes, gaps, next actions, source refs, candidate batch
refs, and workflow candidate refs. New can-say entries require exact refs and a
valid boundary class; unsupported items move to `unverified_notes` rather than
the model-facing can-say lane. The writer cannot call evidence,
validation, memory promotion, or trust writers.

- [x] **Step 4: Implement resume compilation**

Read the latest closeout through indexed metadata plus exact expansion, merge
only current focus and process state, and emit coverage/errors/expansion refs.
Compare the closeout's checked-family state/content tokens and dirty markers
with the current effective snapshot and report changed families. An unrelated
process append does not stale the scientific boundary; a changed or dirty
required family does. Fallback to M0 context when no closeout exists. Never
persist the card. The resume card is exactly the `startup_orientation` level;
it cannot embed a `normal_research` slice or full Skill body.

- [x] **Step 5: Make all startup surfaces consume the same resume boundary**

`topic_status`, `write_topic_status_startup_surfaces`, workspace refresh, and
`session_start.generated.md` call the same resume/context function. Delete no
existing file names. Add a characterization test proving byte-identical compact
boundary fields across all four outputs.

- [x] **Step 6: Run closeout/startup regressions**

Run session lifecycle, quiet checkpoint, closeout completeness, topic status,
workspace refresh, context pack/compiler, and Codex facade tests.

Implementation evidence (2026-07-13):

- Initial lifecycle RED produced eight expected failures for the missing
  closeout/resume modules. Closeout planning/write then passed two focused
  tests; resume selection, coverage, stale-family, index-bypass, fallback, and
  revision behavior passed seven focused tests before startup integration.
- Closeout writes use deterministic session/milestone ids and
  `RecordRepository` `create_or_idempotent`; unsupported model-facing
  boundaries are demoted to unverified notes, unresolved exact refs and
  incomplete scope block persistence, and claim bytes remain unchanged.
- One derived resume compiler now serves full topic status, lightweight startup,
  workspace refresh, and `session_start.generated.md`. All four expose the same
  canonical `resume_boundary_json`; the compatibility compact boundary remains
  orientation-only and cannot claim an exhaustive absence result.
- Self-review RED reproduced two additional fail-closed gaps: an unresolved
  focus objective omitted by the request, and orientation coverage incorrectly
  exposing `can_claim_no_result=true`. Both focused tests pass after repair.
- Final lifecycle/status/context/closeout/architecture plus M0 query-index,
  concurrency, repository, envelope, and retrieval regression: 188 passed in
  39.79 seconds. All touched v5 source modules remain below 500 lines.
- Protected user-work diff hashes remained
  `f4651e2355ca5e394bf2f96fed8b76b209969055` and
  `3c0ca5a7b2ed30e0f32d43d3d1aa0e83330823a1`.

- [x] **Step 7: Commit Task 3**

Commit message: `v5: persist session closeout and compile resume`.

## Task 4: Recall Audits And Prerequisite Gates

**Files:**
- Create: `brain/v5/recall_audit.py`
- Create: `brain/v5/recall_audit_contracts.py`
- Create: `tests/test_v5_recall_audit.py`
- Modify: `brain/v5/context_compiler.py`
- Modify: `brain/v5/context_pack.py`
- Modify: `brain/v5/query_index.py`
- Modify: `brain/v5/research_retrieval.py`

**Interfaces:**
- Produces: `RecallRequest`, `run_recall_audit(ws, request, *, actor) -> RecallAuditRecord`
- Produces: `evaluate_recall_prerequisite(audit, action) -> RecallGateDecision`

```python
@dataclass(frozen=True)
class RecallRequest:
    session_id: str
    query_text: str
    normalized_intent: str
    required_families: tuple[str, ...]
    exact_refs: tuple[str, ...] = ()
    focus_set_ref: str = ""
    include_program_scope: bool = True
    include_discovery: bool = False
    top_k: int = 20


@dataclass(frozen=True)
class RecallGateDecision:
    action: str
    allowed: bool
    reason_code: str
    required_actions: tuple[str, ...]
    audit_ref: str
    can_update_claim_trust: bool = False
```

- [x] **Step 1: Write failing audit tests**

Cover primary topic, program/shared, and optional discovery lanes independently.
Assert query text, normalized intent, focus refs, index generation, canonical
watermark, retrieval-scope token, per-family state/content tokens, dirty
families, content-verification status, families, counts, read errors, top refs,
excluded candidates, truncation, and staleness are persisted.

```python
@pytest.mark.parametrize("action", ["major_conclusion", "expensive_run"])
def test_required_recall_failure_blocks_high_cost_action(action):
    decision = evaluate_recall_prerequisite(STALE_AUDIT, action)
    assert decision.allowed is False
    assert decision.reason_code == "required_recall_not_exhaustive"
```

- [x] **Step 2: Run RED**

- [x] **Step 3: Implement ordered lane retrieval and persistence**

Run exact/current primary scope first, program/shared second, and discovery only
when requested. Preserve lane-local scores and coverage before fusion. Persist
the audit through `RecordRepository`; do not persist retrieved summaries as
evidence. Validate the completed audit against its checked-family state/content
tokens and dirty markers after the audit write; do not compare only the
now-changed global watermark. If `recall_audits` is itself requested, mark that
lane non-exhaustive until a later generation rather than allowing
self-certification.

- [x] **Step 4: Implement prerequisite gates**

Block when a required family is unchecked, index stale, read errors exist,
results truncated beyond the declared policy, or a required exact ref is
missing. Return required repair actions, never a trust update.

- [x] **Step 5: Compile coverage headers from audit facts**

Context may cite `recall_audit:<id>` and exact expansion handles. It may say
"no prior result found" only when the relevant persisted audit has
`can_claim_no_result=True`.

- [x] **Step 6: Run retrieval/context/recall tests and commit**

Implementation evidence (2026-07-13):

- Initial RED produced eight expected failures for the missing recall module.
  The completed suite has nine tests covering ordered primary,
  program/shared, and opt-in discovery lanes; discovery without program scope;
  stale/index-bypass and missing exact refs; self-certification refusal;
  prerequisite reason priority; and audit-bound no-result language.
- Canonical recall persists query/intent, focus/program scope, required families
  and exact refs, lane-local scores and coverage, selected-family state/content
  tokens, dirty/read-error facts, excluded refs, and bounded top refs. It stores
  no retrieved record content and cannot update claim trust.
- Recall retrieval and audit persistence share one canonical-mutation lease.
  Post-write validation compares only checked-family state/content facts and
  deliberately excludes the newly changed `recall_audits` family; global
  watermark change is not misclassified as scientific staleness.
- Context exposes the exact audit ref plus query/normalized-intent boundary and
  exact-expansion handles. Generic no-result language is disabled without a
  persisted, empty, exhaustive, content-verified, non-stale audit.
- Recall/context/retrieval/model/architecture regression: 70 passed. Final
  lifecycle/startup/context plus M0 index/concurrency/repository/envelope
  regression: 214 passed in 47.56 seconds. Family registry, public-surface, and
  runtime-audit regression: 53 passed in 34.10 seconds.
- All touched v5 source modules remain below 500 lines. Protected user-work
  hashes remained `f4651e2355ca5e394bf2f96fed8b76b209969055` and
  `3c0ca5a7b2ed30e0f32d43d3d1aa0e83330823a1`.

Commit message: `v5: add persisted deep recall coverage`.

## Task 5: Runtime Staging And Coalesced Recording Batches

**Files:**
- Create: `brain/v5/recording_batches.py`
- Create: `brain/v5/recording_batch_contracts.py`
- Create: `tests/test_v5_recording_batches.py`
- Modify: `brain/v5/recording_navigator.py`
- Modify: `brain/v5/moment_policy.py`
- Modify: `brain/v5/closeout_completeness.py`

**Interfaces:**
- Produces: `StagedCandidate`
- Produces: `stage_recording_candidate(ws, candidate) -> StagedCandidate`
- Produces: `coalesce_recording_batch(ws, session_id, milestone_id, *, actor) -> WriteResult`
- Runtime path: `.aitp/runtime/recording_staging/<session_id>/<dedup-key>.json`

```python
@dataclass(frozen=True)
class StagedCandidate:
    staging_id: str
    session_id: str
    topic_id: str
    candidate_kind: str
    semantic_key: str
    summary: str
    payload: dict[str, Any]
    source_refs: tuple[str, ...]
    source_event_refs: tuple[str, ...]
    missing_prerequisites: tuple[str, ...]
    dedup_key: str
    created_at: str
    expires_at: str
    status: str = "staged"
    trust_effect: str = "none"
    can_update_claim_trust: bool = False
```

- [ ] **Step 1: Write failing staging/dedup tests**

Test same semantic key/source refs idempotency, different sources, expiry,
supersession, rejection, resume, corrupt staging diagnostics, and one batch per
milestone.

- [ ] **Step 2: Run RED**

- [ ] **Step 3: Implement normalized runtime staging**

Accepted candidate classes are `definition`, `formula`, `convention`,
`relation`, `derivation`, `interpretation`, `analogy`, `conjecture`,
`failed_route`, `counterexample`, `bridge`, `open_direction`, and
`workflow_candidate`. Each candidate declares source refs, missing
prerequisites, dedup key, expiry, and `trust_effect=none`.

- [ ] **Step 4: Implement durable batch coalescing**

Sort/deduplicate candidates by semantic key and normalized source refs. Use a
deterministic batch id from session/milestone. Persist only the coalesced batch;
write a runtime receipt for included/rejected/expired staging ids.

- [ ] **Step 5: Enforce forbidden downstream writes**

Tests monkeypatch evidence, trust, memory, skill proposal, and install writers
to fail if called. `coalesce_recording_batch` must still pass.

- [ ] **Step 6: Integrate moment and closeout policy**

Moment decisions stage candidates silently; milestone/closeout produces at
most one review batch by default. Recording navigator returns the batch ref,
not one prompt per candidate.

- [ ] **Step 7: Run recording regressions and commit**

Commit message: `v5: coalesce recording candidates for review`.

## Task 6: Lifecycle MCP, CLI, Capability, And Compact Entry

**Files:**
- Create: `brain/v5/mcp_session_lifecycle.py`
- Create: `brain/v5/cli_session_lifecycle.py`
- Create: `tests/test_v5_lifecycle_facade.py`
- Modify: `brain/v5/mcp_tools.py`
- Modify: `brain/v5/cli.py`
- Modify: `brain/v5/capability_registry_data.py`
- Modify: `brain/v5/codex_facade.py`
- Modify: `brain/v5/public_surfaces.py`
- Modify: `brain/v5/runtime_entrypoint_catalog.py`

**Interfaces:**
- Produces full-surface operations: `session_start`, `recall_audit`,
  `recording_stage`, `recording_batch`, `session_closeout_plan`, and
  `session_closeout_apply`.
- Existing compact concepts remain: enter, expand, recording step/apply, and
  closeout.
- Maps compact enter to `startup_orientation`, bounded expand to
  `normal_research`, and exact ref/source expansion to `exact_expansion`.
- Host autoroute emits only `route_hint`; it cannot call a deeper level without
  an explicit facade/tool transition recorded in the context receipt.

- [ ] **Step 1: Write failing capability/facade tests**

Assert every direct wrapper has one `CapabilitySpec`, state effect, public
surface, CLI route, and MCP wrapper. Assert compact allowlist count does not
grow unless the final design explicitly requires it.

- [ ] **Step 2: Run RED**

- [ ] **Step 3: Implement wrappers and `session` CLI group**

Use file-backed JSON options for nested candidate/closeout payloads. Read-only
start/plan operations do not initialize or write a workspace. Runtime staging
is `runtime_write`; closeout/audit/batch are trust-neutral `kernel_write`.

- [ ] **Step 4: Route existing compact facade operations**

`codex_enter` returns the same session-start resume/context boundary.
`codex_recording_step` stages/coalesces according to policy. `codex_closeout`
plans first and applies only the explicit supplied plan id.

- [ ] **Step 5: Run capability and bridge matrices**

Run capability registry, public surfaces, runtime entrypoints, bridge runtime,
MCP bridge acceptance, CLI, Codex facade, and adapters.

- [ ] **Step 6: Commit Task 6**

Commit message: `v5: expose host-neutral session lifecycle`.

## Task 7: M1 Migration And End-To-End Acceptance

**Files:**
- Create: `tests/test_v5_gate1_lifecycle_e2e.py`
- Create: `docs/superpowers/progress/2026-07-10-aitp-gate-1-release-audit.md`
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-07-09-aitp-final-research-lifecycle-roadmap.md`
- Modify: `docs/superpowers/plans/2026-07-10-aitp-gate-1-lifecycle-context.md`

- [ ] **Step 1: Add a two-topic end-to-end fixture**

Start one primary QFT/QG topic with a supporting method topic, retrieve primary
then program scope, stage duplicate semantic candidates, coalesce one batch,
persist one closeout, and resume a new session. Assert no active claim rebind,
no cross-topic trust transfer, and identical startup boundaries.

- [ ] **Step 2: Add migration dry-run**

Inventory existing sessions/topics and report possible program/focus candidates
without writing them. Existing sessions remain valid with no focus sidecar.

- [ ] **Step 3: Run M1 focused lanes**

Run all new tests plus M0 foundation/compatibility lanes. Run the slow
adapter lane separately. Record exact commands, counts, and durations.

- [ ] **Step 4: Run real-store read-only start/resume benchmark**

Use an existing session without writing canonical M1 records. Confirm
fallback resume remains under 800 estimated tokens and warm p95 under one
second. Hash canonical state before/after.

- [ ] **Step 5: Update README and roadmap**

Document sidecar focus, recall coverage, one coalesced review batch, closeout vs
resume, exact expansion, and trust isolation. Mark only verified checklist
items complete.

- [ ] **Step 6: Write release audit and verify staged tree**

Run `git diff --check`, AST parse all source files, named test lanes, and a
staged-tree capability audit. Preserve independent user hunks.

- [ ] **Step 7: Commit M1**

Commit message: `v5: complete M1 research lifecycle`.

## M1 Completion Checklist

- [ ] Session focus supports all required ref kinds without changing `SessionBinding.active_claim`.
- [ ] Cross-topic relations always forbid claim-trust transfer and require target revalidation.
- [ ] One closeout is idempotent, canonical process state with no trust effect.
- [ ] Every model-facing closeout boundary item preserves proved/conditional/
  finite-evidence/open-gap classification and exact refs; summary text alone
  never enters the can-say lane.
- [ ] Resume, topic status, workspace refresh, compact entry, and generated startup files share one boundary.
- [ ] MCP, CLI, hooks, topic status, and workspace refresh expose the same
  four-level disclosure ladder; every level preserves coverage/errors/handles
  and `not_checked|not_shown` never becomes `not_found`.
- [ ] Recall coverage is persisted and blocks unsupported exhaustive/high-cost actions.
- [ ] Full-base plus delta retrieval makes lifecycle writes immediately visible;
  scoped content verification survives unrelated process writes without hiding
  dirty, stale, malformed, or continuity-broken required families.
- [ ] One milestone creates at most one coalesced recording batch by default.
- [ ] Raw staging cannot write evidence, trust, memory, or skills.
- [ ] Capability, MCP, CLI, public, bridge, and compact declarations have zero drift.
- [ ] M0 tests remain green and architecture limits are unchanged.
- [ ] Real-store fallback startup meets token/latency budgets without canonical rewrites.
