# Layer 0 source layer

This file defines Layer 0 as the callable source substrate of the kernel.

Layer 0 is not only the front door for new material.
It is the layer later stages can call back into when they need more source evidence, cleaner source traces, or new acquisition.

## 1. Purpose

Use Layer 0 for:
- source acquisition,
- source identity,
- source registration,
- source reopening,
- source retrieval,
- source search expansion.

Layer 0 answers:
- what the source is,
- where it came from,
- how it can be reopened,
- how later stages can ask for more related source material.

## 2. Source classes

The system should at least support:
- paper
- PDF
- URL
- web page
- video
- transcript
- conversation
- local note
- dataset or table later if needed

## 3. Current operational status

Layer 0 now has a dedicated persistent top-level storage surface at:
- `source-layer/topics/<topic_slug>/source_index.jsonl`
- `source-layer/topics/<topic_slug>/sources/<source_slug>/`
- `source-layer/global_index.jsonl`

Layer 1 intake may still keep topic-local projections under:
- `intake/topics/<topic_slug>/source_index.jsonl`
- `intake/topics/<topic_slug>/sources/<source_slug>/`

Those intake-side artifacts are now projections for topic-local readability.
They are no longer the canonical Layer 0 source-of-truth.

## 4. Minimal source object

Every registered source should have:
- `source_id`
- `source_type`
- `title`
- `topic_slug`
- `provenance`
- `locator`
- `acquired_at`
- `registered_by`
- `summary`

See:
- `schemas/source-item.schema.json`

## 5. Downstream call-back rule

Later layers may call back into Layer 0 when:
- Layer 3 discovers a missing prerequisite source,
- Layer 4 needs a stronger source trace,
- Layer 4 needs a missing citation or transcript,
- Layer 1 needs a better snapshot or acquisition format,
- a bridge or warning note reveals missing evidence.

This call-back should produce:
- either a new `source_item`,
- or an updated source registration / snapshot.

## 5a. arXiv-first policy for theory papers

For arXiv-backed theory papers, the default source-opening priority is:
- arXiv source package (`e-print`, TeX source) when available,
- arXiv HTML rendering,
- arXiv PDF,
- only then downstream summaries or local notes about the paper.

The reason is architectural, not cosmetic:
- TeX source exposes equations, macros, and section structure more faithfully,
- HTML is usually easier to chunk than PDF when source is unavailable,
- PDF remains the fallback rather than the preferred first opening.

The current helper for this policy lives at:
- `source-layer/scripts/register_arxiv_source.py`
- `intake/scripts/register_arxiv_source.py` as a compatibility wrapper
- `intake/ARXIV_FIRST_SOURCE_INTAKE.md`

## 6. What Layer 0 should not do

Layer 0 should not:
- decide canonical promotion,
- store provisional reasoning as if it were source identity,
- replace Layer 1 interpretation,
- replace Layer 3 candidate formation,
- replace Layer 4 adjudication.

## 7. Current next step

The next maturity steps for Layer 0 are:
- add more source-class-specific helpers beyond arXiv papers,
- add stronger cross-topic deduplication and alias handling,
- let later-layer callbacks create typed source-query requests rather than only direct registrations.
