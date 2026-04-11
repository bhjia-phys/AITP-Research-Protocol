# Phase 68: Source Fidelity Ranking And Runtime Read Surfaces - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** Brownfield continuation after closing Phase `67`

<domain>
## Phase Boundary

Make source fidelity explicit in the existing source-intelligence runtime path:

- infer bounded fidelity tiers from source identity and provenance
- expose those tiers in `source_intelligence` payloads
- render them through runtime/status human-readable surfaces

This phase is about evidence-weight visibility.
It is not about adding a separate fidelity command surface.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Reuse the existing `source_intelligence` payload rather than inventing a new
  fidelity-only artifact family.
- Keep fidelity bounded to a small explicit tier set:
  - `peer_reviewed`
  - `preprint`
  - `local_note`
  - `web`
  - `unknown`
- Update the runtime bundle schema so the new fidelity surface remains a real
  contract rather than an accidental extra field.

### the agent's Discretion

- Exact fidelity inference rules and summary wording.
- How much fidelity detail to show in markdown versus JSON.

</decisions>

<canonical_refs>
## Canonical References

- `research/knowledge-hub/knowledge_hub/source_intelligence.py`
- `research/knowledge-hub/knowledge_hub/l1_source_intake_support.py`
- `research/knowledge-hub/knowledge_hub/runtime_read_path_support.py`
- `research/knowledge-hub/knowledge_hub/topic_shell_support.py`
- `research/knowledge-hub/runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`
- `research/knowledge-hub/tests/test_aitp_service.py`
- `research/knowledge-hub/tests/test_runtime_profiles_and_projections.py`
- `research/knowledge-hub/tests/test_aitp_cli_e2e.py`

</canonical_refs>

<code_context>
## Existing Code Insights

- Source intelligence already flowed through `topic_status`, runtime bundle
  materialization, and dashboard markdown.
- The missing step was explicit evidence-weight structure, not another command
  family.
- The runtime bundle schema had to be updated because `source_intelligence` is
  contract-validated in the regression suite.

</code_context>

<specifics>
## Specific Ideas

- Add `fidelity_rows` and `fidelity_summary` to source-intelligence payloads.
- Render a compact `## Source fidelity` section in runtime-facing markdown.
- Treat DOI and arXiv-backed identity as the first bounded fidelity anchors.

</specifics>

<deferred>
## Deferred Ideas

- richer fidelity weighting beyond bounded tier names
- promotion-side use of fidelity in later milestones

</deferred>

---

*Phase: 68-source-fidelity-ranking-and-runtime-read-surfaces*
*Context captured on 2026-04-11 after Phase 68 implementation and verification*
