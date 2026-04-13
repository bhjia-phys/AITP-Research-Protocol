# Phase 175: Staging Provenance And Noise Suppression - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Harden the literature-intake fast path before consultation ranking by removing
obviously noisy staged rows and preserving the true per-entry source
provenance.

</domain>

<decisions>
## Implementation Decisions

### Noise suppression
- Suppress generic notation bindings such as `classes`, `studied`, and
  `considered` before they become reusable staging rows.
- Treat weak `unspecified_method` rows as non-reusable unless stronger
  evidence exists; do not let them populate the bounded `L2` fast path by
  default.

### Provenance preservation
- Preserve source provenance per staged entry, not per batch.
- Carry the true `source_id` / `source_slug` through staging tags and
  provenance so multi-paper topic intake does not collapse onto one paper.

### the agent's Discretion
Keep the fix bounded to staging hygiene and provenance. Consultation ranking is
deferred to Phase `175.1`.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `literature_intake_support.py` already owns candidate derivation and
  literature fast-path staging.
- `l2_graph.py` already owns staging-entry writeback and staging-aware
  consultation.
- `l2_staging.py` rebuilds `workspace_staging_manifest` and `staging_index`.

### Established Patterns
- Staging content is explicitly provisional and must stay schema-backed.
- Tests already exist around literature fast-path derivation and staging
  manifests, so the safest route is TDD on those files first.

### Integration Points
- Phase `175` feeds Phase `175.1` by ensuring the staged rows entering
  consultation are clean and correctly attributed.

</code_context>

<specifics>
## Specific Ideas

- Add explicit per-entry source provenance payload on literature fast-path
  units.
- Make staging-manifest rebuild preserve richer staging-index fields instead of
  dropping them on rewrite.
- Capture the observed real-topic failure mode with tests instead of fixing only
  the current staging artifacts by hand.

</specifics>

<deferred>
## Deferred Ideas

- Consultation ranking and topic-local primary-hit ordering are deferred to
  Phase `175.1`.
- Front-door `session-start` misrouting and Windows source-path/status issues
  stay out of scope for this phase.

</deferred>
