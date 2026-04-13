# Phase 167: L1 Contradiction Intake Rows And Comparison Basis - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase upgrades the current `L1` contradiction intake shape from thin
`contradiction_candidates` into richer, source-backed contradiction rows with a
bounded comparison basis. It covers derivation, normalization, schema shape,
and durable intake payloads inside `l1_source_intake`. It does not yet widen
into runtime/read-path wording or the milestone proof lane; those belong to
Phase `167.1`.

</domain>

<decisions>
## Implementation Decisions

### Data-model and derivation boundary
- **D-01:** Build on the existing `l1_source_intake` contradiction path instead
  of inventing a new top-level contradiction subsystem. The current
  `contradiction_candidates` chain in `l1_source_intake_support.py`,
  `source_distillation_support.py`, and the runtime schema is the starting
  surface for this phase.
- **D-02:** Contradiction rows in this phase must stay explicitly source-backed
  and pairwise. No multi-source clustering, score-based adjudication, or
  cross-topic contradiction graph belongs in Phase `167`.
- **D-03:** Each contradiction row must carry enough bounded comparison context
  to explain why the conflict was surfaced. At minimum that means both source
  refs, both reading-depth postures, the contradiction kind, and explicit
  compared claim/regime/assumption summaries rather than only a vague `detail`
  string.

### Compatibility and scope safety
- **D-04:** Keep existing `contradiction_candidates` consumers working during
  this phase. The agent may enrich the row schema and internal helpers, but
  Phase `167` must not force a broad breaking rename across all runtime/read
  paths before Phase `167.1`.
- **D-05:** Keep `notation_tension_candidates` separate. This phase is about
  contradiction rows for incompatible claims/assumptions/regimes, not about
  merging all intake tensions into one mixed family.
- **D-06:** Runtime/read-path rendering improvements are intentionally deferred
  to Phase `167.1`. If minimal schema or helper updates are needed to keep
  current surfaces functioning, that is allowed, but new operator-facing
  contradiction presentation is not the main deliverable here.

### Verification boundary
- **D-07:** Phase `167` should land targeted unit/service/schema coverage for
  the richer contradiction row shape and comparison-basis derivation.
- **D-08:** The bounded contradiction-aware acceptance lane remains Phase
  `167.1`; this phase should reuse the existing assumption/depth fixtures and
  helper surfaces without claiming the milestone proof is already closed.

### the agent's Discretion
- exact field names for richer contradiction row payloads, as long as they stay
  source-backed and readable
- whether compatibility is implemented as an enriched
  `contradiction_candidates` row shape or as an internal richer row with a
  compatibility projection
- exact deduplication keys for contradiction rows when multiple source facts
  collapse to the same bounded contradiction

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone scope and requirement routing
- `.planning/ROADMAP.md` — Phase `167` goal, scope boundary, and dependency on
  `v1.92`
- `.planning/REQUIREMENTS.md` — `REQ-L1CON-01` and `REQ-L1CON-02`
- `.planning/BACKLOG.md` — item `999.27` defines the broader intake-maturity
  remainder this phase now promotes

### Prior shipped surfaces that constrain this work
- `.planning/milestones/v1.70-ROADMAP.md` — previous assumption/depth closure
  and its explicitly deferred contradiction-adjudication remainder
- `research/knowledge-hub/runtime/scripts/run_l1_assumption_depth_acceptance.py`
  — existing acceptance lane that already expects contradiction candidates
- `research/knowledge-hub/tests/test_aitp_service.py` — current runtime/service
  fixtures showing the thin contradiction candidate shape

### Core implementation surfaces
- `research/knowledge-hub/knowledge_hub/l1_source_intake_support.py` — current
  contradiction derivation, normalization, and summary helpers
- `research/knowledge-hub/knowledge_hub/source_distillation_support.py` —
  current `L1` source-intake construction path
- `research/knowledge-hub/knowledge_hub/source_intelligence.py` — current
  contradiction detection helper
- `research/knowledge-hub/runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`
  — current `l1_source_intake` and `l1_contradiction_candidate` schema shape

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `l1_source_intake_support.py` already has:
  - `_normalize_contradiction_candidates(...)`
  - `derive_l1_conflict_intake(...)`
  - `l1_contradiction_summary_lines(...)`
- `source_distillation_support.py` already builds the broader
  `l1_source_intake` payload from source-backed rows.
- `run_l1_assumption_depth_acceptance.py` already proves the current system can
  surface contradiction candidates on the read path, so this phase can refine
  an existing lane rather than creating a new one from scratch.

### Established Patterns
- `L1` intake families use row arrays (`assumption_rows`, `reading_depth_rows`,
  `method_specificity_rows`) plus normalization helpers and schema-level row
  contracts.
- Existing contradiction rows are thin but already pairwise and source-backed,
  which makes them a safe upgrade target for richer comparison payloads.
- Runtime/read-path helpers already summarize contradiction rows, so keeping
  compatibility matters if Phase `167` is to stay narrowly scoped.

### Integration Points
- `research/knowledge-hub/knowledge_hub/l1_source_intake_support.py`
- `research/knowledge-hub/knowledge_hub/source_distillation_support.py`
- `research/knowledge-hub/runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`
- `research/knowledge-hub/tests/test_aitp_service.py`
- `research/knowledge-hub/runtime/scripts/run_l1_assumption_depth_acceptance.py`

</code_context>

<specifics>
## Specific Ideas

- Preferred phase outcome: after this phase, a contradiction row should read
  more like a bounded comparison record than a loose warning candidate.
- The compared content should come from already-extracted intake facts when
  possible, not from fresh free-form synthesis.
- If a contradiction is only weakly supported because one source is
  `abstract_only` or `skim`, that weakness should stay visible in the row
  rather than being hidden behind a stronger-sounding contradiction label.

</specifics>

<deferred>
## Deferred Ideas

- renaming all runtime/read-path surfaces from `contradiction_candidates` to a
  new public term in this phase
- contradiction clustering or adjudication workflows across many sources
- automatic route mutation or checkpoint creation when contradiction rows appear

</deferred>

---

*Phase: 167-l1-contradiction-intake-rows-and-comparison-basis*
*Context gathered: 2026-04-13*
