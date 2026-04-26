# Phase 141 Summary

Status: implemented on `main`

## Goal

Adopt the three-layer `L1` raw/wiki/output vault pattern on top of the
existing topic-shell path, keep flowback explicit, and preserve the runtime
compatibility surfaces instead of replacing them.

## What Landed

- a new support module:
  `research/knowledge-hub/knowledge_hub/l1_vault_support.py`
- topic-shell materialization now writes one topic-scoped vault under:
  - `intake/topics/<topic_slug>/vault/raw/`
  - `intake/topics/<topic_slug>/vault/wiki/`
  - `intake/topics/<topic_slug>/vault/output/`
- the raw layer now anchors immutable `source-layer` inputs through one source
  manifest instead of duplicating writable source copies
- the wiki layer now writes Obsidian-compatible pages with frontmatter,
  lowercase filenames, wikilinks, and a local schema page
- the output layer now writes one derived query digest plus one explicit
  `flowback.jsonl` ledger recording applied wiki syncs
- `research_question.contract.md` and `runtime_protocol.generated.md` now both
  surface the new `L1 vault` section
- a new isolated acceptance script and schema/doc tests now protect this lane

## Outcome

Phase `141` is complete.
`v1.68` now has a real persistent `L1` wiki-style vault surface, and the next
remaining phase is `142`.
