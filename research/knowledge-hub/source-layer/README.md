# Layer 0 source substrate

This directory is the dedicated persistent home of Layer 0.

Layer 0 is the callable source substrate of AITP:
- source acquisition,
- source identity,
- source reopening,
- source expansion,
- durable source snapshots before later interpretation layers begin.

## Layout

- `topics/<topic_slug>/topic.json`
- `topics/<topic_slug>/source_index.jsonl`
- `topics/<topic_slug>/sources/<source_slug>/`
- `global_index.jsonl`
- `compiled/source_catalog.json|md`
- `compiled/citation_traversals/`
- `compiled/source_families/`
- `compiled/bibtex_exports/`
- `compiled/bibtex_imports/`
- `scripts/register_arxiv_source.py`
- `scripts/backfill_topic_sources.py`

## Source-of-truth rule

Layer 0 is now the source-of-truth for registered sources.

Layer 1 intake may still keep topic-local projections under:

`intake/topics/<topic_slug>/source_index.jsonl`

and

`intake/topics/<topic_slug>/sources/<source_slug>/`

but those should be treated as stage-local projections that point back to Layer 0, not as the canonical source store.

## Why this split exists

The split matters because:
- the same source may later support multiple later-stage routes,
- Layer 3 and Layer 4 may need to call back into sources without pretending the source belongs to intake only,
- the source substrate should remain durable even when intake artifacts are revised, filtered, or promoted.

## Current helper workflow

Register a new arXiv-backed source into Layer 0 and create the Layer 1 projection:

```bash
python3 source-layer/scripts/register_arxiv_source.py \
  --topic-slug <topic_slug> \
  --arxiv-id <arxiv_id> \
  --download-source
```

Backfill an existing topic that still stores sources only inside intake:

```bash
python3 source-layer/scripts/backfill_topic_sources.py \
  --topic-slug <topic_slug>
```

## Current limitation

This is a persistence split, not yet a global deduplication engine.

The same paper may still appear under multiple topic slugs.
That is acceptable for now as long as:
- each registration remains explicit,
- provenance stays intact,
- later deduplication can be added without losing source identity.

The current bounded compiled surfaces now make that reuse easier to inspect:
- `compiled/source_catalog.json|md`
- `compiled/citation_traversals/`
- `compiled/source_families/`
- `compiled/bibtex_exports/`
- `compiled/bibtex_imports/`
