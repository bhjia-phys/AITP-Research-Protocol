# AITP Indexed Context Compiler Report

Date: 2026-07-10

## Delivered Contract

- `ContextRequest` and `ContextBundle` compile one session/topic context from one
  indexed query plan plus exact canonical reads.
- The injected Markdown is bounded by UTF-8 bytes, deterministic mixed-language
  token estimation, and line count.
- Default context contains summaries and typed `record_refs`; complete records
  require explicit, paginated `record_refs` expansion.
- Stale indexes, malformed scoped records, unresolved refs, and truncation are
  visible and prohibit absolute prior-result absence claims.
- Stale topic snapshots enumerate selected-family paths and parse only canonical
  paths absent from the index, so newly written records remain visible without a
  synchronous full rebuild.
- Context, retrieval, timeline, focus, and distillation projections are
  orientation-only and cannot update evidence, validation, kernel state, claim
  trust, L2 memory, or Skills.

## Migrated Read Paths

- `context_pack` no longer invokes compact brief, execution brief, relation map,
  and distillation recursively.
- Objective graph, relation map, active-claim focus, research timeline, and
  distillation share topic-scoped `IndexedTopicSnapshot` projections.
- Timeline reuses frontmatter already parsed and integrity-checked by
  `RecordRepository`; it does not parse exact records twice.
- High-volume `reference_locations` remain exact-expandable but are excluded
  from active-claim drift scoring because orientation-only location count is not
  a sufficient rebind signal.
- Exact ref expansion reads canonical paths directly and loads only the small
  index manifest for freshness/coverage, not the full 44 MB derived index.

## Performance Acceptance

### Versioned Synthetic Fixture

Fixture: `tests/fixtures/v5_context_10000_fixture.json` (`v1`), generated only
when `AITP_RUN_PERFORMANCE=1`.

| Measure | Result | Gate |
|---|---:|---:|
| Record count | 10,000 | exactly 10,000 |
| Index build | 194.436 s | explicit/background only |
| Cold minimal context | 0.267 s | < 3.0 s |
| Warm minimal p95 | 0.203 s | < 1.0 s |
| Warm timeline p95 | 0.480 s | < 2.0 s |
| Exact ref p95 | 0.096 s | < 0.250 s |
| Context size | 2,701 bytes | within request budget |
| Context estimate | 431 tokens | within request budget |

### Real Research Store

The real fixture contains 9,741 indexed objects: 7,235 registry records plus
topics, sessions, contexts, and L2 memory entries.

| Measure | Result |
|---|---:|
| First minimal context | 0.465 s |
| Warm minimal p95 | 0.513 s |
| Warm timeline p95 | 0.802 s |
| Exact ref p95 | 0.120 s |
| Context size | 3,747 bytes |
| Context estimate | 520 tokens |

The representative real-store session was
`v5-qsgw-headwing-update-librpa`. No canonical research record was written by
the benchmark.

## Verification

- 84 focused context, objective graph, relation map, timeline, distillation,
  active-focus, Codex facade, retrieval, index, and repository tests passed.
- The explicit 10,000-record performance test passed in 213.36 seconds.
- New modules are below the 500-line architecture limit:
  `context_compiler.py` 440, `indexed_topic_snapshot.py` 224,
  `context_pack.py` 425, `context_pack_projection.py` 249,
  `objective_graph.py` 491, and `research_timeline.py` 458.
- Repository-wide architecture debt remains an M0 Task 9 blocker and was not
  hidden by relaxing limits.
