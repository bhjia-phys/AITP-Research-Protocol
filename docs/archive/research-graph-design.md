# AITP Research Graph — superseded

Status: **superseded** (kept for history; do not implement from this file).

The design that lived here — catalog, sync, JSONL projection, `graph
enter`/`graph query`, and a Python `distill` pipeline — was re-evaluated
against first principles and the real workspace, and cut:

- **Sync / projection / graph query removed.** At the real scale (a handful
  of Topics, each with tens to hundreds of Markdown records), cross-topic
  lookup is served by `rg` plus per-topic `enter`. The projection machinery
  existed to solve a performance problem that does not occur, at the cost of
  freshness/staleness/snapshot bookkeeping.
- **Graph database rejected.** Canonical data must stay in readable
  repositories; a database would absorb it and invite low-quality edges.
- **`distill` moved and corrected.** Distillation is single-Topic work, not
  graph work. In M2 (`docs/roadmap.md`) Python validates compiled artifacts
  and gates their review; it never generates their content.
- **What survives** — the Topic catalog and explicit, human-saved links —
  is now `docs/cross-topic-links.md` (M3). The `topics.toml` file convention
  arrives earlier, in M0.6, as part of the multi-topic workspace layout.

See `docs/roadmap.md` for the current staging.
