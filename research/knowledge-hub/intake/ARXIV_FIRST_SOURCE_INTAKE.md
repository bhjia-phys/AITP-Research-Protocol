# arXiv-first source intake

This file defines the preferred Layer 0 acquisition policy for arXiv-backed theory papers.

## Purpose

For theory-heavy research, prefer the source form that preserves equations and structure best.

The default opening order is:
1. arXiv source package (`e-print`, TeX source)
2. arXiv HTML rendering
3. arXiv PDF
4. external summaries about the paper

## Why this matters

The source package is usually the most faithful machine-usable form because it preserves:
- equations before PDF layout loss,
- macro structure,
- section and appendix boundaries,
- figure filenames and bibliography structure.

This makes later chunking, equation tracing, and note linking more reliable.

## Durable artifacts

For one arXiv paper, the full Layer 0 + Layer 1 route should usually create:
- `source.json`
- `snapshot.md`
- downloaded source bundle when available
- extracted source tree when extraction succeeds

Recommended storage:

Layer 0 source-of-truth:

`source-layer/topics/<topic_slug>/sources/<source_slug>/`

Layer 1 projection:

`intake/topics/<topic_slug>/sources/<source_slug>/`

## Helper

Use:

```bash
python3 source-layer/scripts/register_arxiv_source.py --help
```

Typical usage:

```bash
python3 source-layer/scripts/register_arxiv_source.py \
  --topic-slug <topic_slug> \
  --arxiv-id <arxiv_id> \
  --registered-by codex
```

Lightweight metadata-only usage:

```bash
python3 source-layer/scripts/register_arxiv_source.py \
  --topic-slug <topic_slug> \
  --arxiv-id <arxiv_id> \
  --registered-by codex \
  --metadata-only
```

The old path remains available as a compatibility wrapper:

```bash
python3 intake/scripts/register_arxiv_source.py --help
```

## Fallback rule

If the source package cannot be downloaded or extracted:
- keep the paper registered,
- record the failure in `snapshot.md`,
- fall back to arXiv HTML or PDF,
- do not silently pretend TeX access existed.
