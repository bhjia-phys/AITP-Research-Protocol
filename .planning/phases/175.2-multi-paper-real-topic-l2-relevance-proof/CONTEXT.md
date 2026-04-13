# Phase 175.2: Multi-Paper Real-Topic L2 Relevance Proof - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Prove the bounded `v2.1` `L2` hardening slice on one replayable multi-paper
real-topic acceptance lane, then leave durable receipts and explicit
non-claims.

</domain>

<decisions>
## Implementation Decisions

### Real-topic proof target
- Use the same measurement-induced / observer-algebra topic family that exposed
  the staging-provenance and consultation-relevance defects.
- Keep the proof bounded to `L2` quality: multi-paper provenance correctness
  plus primary-surface local relevance ordering.

### Honesty constraints
- Do not claim broad semantic reranking or full knowledge-quality closure.
- Do not widen into fresh science claims; the proof is about trustworthy `L2`
  surfaces for a fresh local topic.

### the agent's Discretion
The exact multi-paper source set and staged titles may vary, but the proof must
still demonstrate multiple distinct source provenances and one local staged
primary hit outranking unrelated canonical carryover.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase `175` already hardened fast-path staging provenance and noise
  suppression.
- Phase `175.1` already hardened topic-local primary-surface consultation
  ranking when staging is explicitly included.
- Existing runtime acceptance scripts under `research/knowledge-hub/runtime/scripts/`
  already provide the isolated-work-root pattern to reuse.

### Established Patterns
- Isolated acceptance scripts should copy canonical/schemas surfaces into a temp
  work root and verify durable artifacts, not just return in-memory payloads.
- `test_runtime_scripts.py` is the standard harness for these proof wrappers.

### Integration Points
- Phase `175.2` closes milestone `v2.1` at the phase level.
- The resulting receipts should be enough to move the milestone into lifecycle
  handling next.

</code_context>

<specifics>
## Specific Ideas

- Seed one unrelated canonical carryover unit so the local staged primary-hit
  proof is honest.
- Stage at least two entries from different source papers in the same topic.
- Materialize `workspace_staging_manifest` and `workspace_knowledge_report` as
  durable artifacts for the proof package.

</specifics>

<deferred>
## Deferred Ideas

- Full fresh-topic front-door routing repair remains outside this milestone.
- Broader AI Scientist benchmark alignment remains a later, wider milestone.

</deferred>
