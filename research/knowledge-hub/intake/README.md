# Layer 1 — Intake / Staging

This layer stores source-bound, not-yet-canonical material.

Use it for:
- source projections from Layer 0,
- raw notes,
- provisional claims,
- extraction queues,
- early topic framing.

Layer 1 should actively consult Layer 2 while doing provisional understanding:
- compare terminology against current concepts,
- compare extracted statements against current claim cards,
- check warning notes for known scope or interpretation traps,
- reuse workflows when the source fits an existing intake routine.

When that consultation materially shapes a durable intake artifact, record it through the first-class consultation protocol under `consultation/` and treat `l2_consultation_log.jsonl` as a local projection.

Topic roots live under:

`research/knowledge-hub/intake/topics/<topic_slug>/`

For theory-paper intake from arXiv, prefer source-package acquisition before PDF:
- see `ARXIV_FIRST_SOURCE_INTAKE.md`
- primary helper: `../source-layer/scripts/register_arxiv_source.py`
- compatibility wrapper: `scripts/register_arxiv_source.py`

Nothing here should be treated as automatically canonical.
Items from this layer may later route to Layer 3 exploration, or in simpler cases directly to Layer 2.
If Layer 4 validation is needed, it should happen only after Layer 3 has produced a candidate to adjudicate.
