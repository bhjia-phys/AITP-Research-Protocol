# Phase 141: Adopt LLM-Wiki-Skill Three-Layer Vault And Flowback Into L1 Knowledge Compilation - Context

**Gathered:** 2026-04-12
**Status:** Ready for execution

<domain>
## Phase Boundary

This phase owns the first real `L1` wiki-style vault surface inside AITP.

The phase should materialize one topic-scoped three-layer vault:

- raw: immutable source-input anchors that point back to `source-layer`
- wiki: Obsidian-compatible compiled notes that agents may maintain
- output: derived query products plus an explicit flowback ledger

The phase should extend the existing topic-shell path rather than opening a
parallel CLI lane.

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Build on `ensure_topic_shell_surfaces()` and the existing
  `research_question.contract` / `l1_source_intake` path rather than inventing
  another L1 compiler entrypoint.
- **D-02:** Keep raw inputs anchored to `source-layer` instead of copying source
  artifacts into a second mutable directory.
- **D-03:** Make flowback explicit and inspectable through one output digest plus
  one flowback ledger.
- **D-04:** Keep `control_note.md`, `operator_console.md`, and
  `research_question.contract.{json,md}` visible as compatibility/runtime
  surfaces linked from the new vault, not displaced by it.
- **D-05:** Treat the vault as non-authoritative compiled L1 structure; it does
  not bypass `L0` truth or later `L2` promotion gates.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `research/knowledge-hub/intake/README.md`
- `research/knowledge-hub/knowledge_hub/topic_shell_support.py`
- `research/knowledge-hub/knowledge_hub/source_distillation_support.py`
- `research/knowledge-hub/knowledge_hub/l1_source_intake_support.py`
- `research/knowledge-hub/runtime/README.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- L0 search/discovery integration
- multi-topic wiki federation across topic vaults
- L2 statement-compilation / verifier-repair work for Phase `142`

</deferred>

---

*Phase: 141-l1-three-layer-vault-and-flowback*
*Context gathered: 2026-04-12*
