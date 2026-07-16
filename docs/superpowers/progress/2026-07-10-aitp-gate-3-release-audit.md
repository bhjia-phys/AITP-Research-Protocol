# AITP M3 Knowledge, Insight, And Hybrid RAG Release Audit

Date: 2026-07-16

Status: M3 fixture-contract acceptance complete. Real formal-theory source
memory remains a mandatory M6 acceptance input.

## Released Boundary

- Stable physics-object identity is separate from source- and
  convention-specific assertions.
- Grounded promotion requires exact source-asset and reference-location pins
  plus a hash-bound, host-attested human review decision.
- Reviewed insight remains speculative non-evidence. Candidate diagnosis,
  discovery, source shelves, retrieval, context, review, and promotion cannot
  update claim trust or write Evidence.
- Source shelves are immutable disposable generations over typed acquisition
  decisions, receipts, exact source bytes, and exact locations. Missing,
  restricted, changed, or unsupported sources produce explicit incomplete
  coverage.
- Lexical, formula, graph, and optional dense retrieval consume one lineage-
  bound snapshot. Framework, regime, convention, scope, component failures,
  lane quotas, pagination, and omitted results remain machine-readable.
- Startup knowledge context uses cheap state-token orientation checks. It is
  fast but deliberately non-exhaustive. Public knowledge query defaults to the
  same mode and supports explicit `verification_mode=strong` when a caller
  needs content-verified exhaustive semantics.

## Full And Compact Surfaces

M3 adds nine full-only MCP/CLI operations:

| Operation class | Count | State effect |
|---|---:|---|
| Candidate diagnosis, shelf read, discovery request/result, retrieval, context | 6 | `read_only` |
| Source-shelf build | 1 | `runtime_write` |
| Review decision and approved promotion | 2 | `kernel_write` |

Every operation returns one deeply validated `knowledge_operation_result`.
Kernel writes retain exact checkpoint/decision/result pins; the derived shelf
writer cannot write canonical records. All nine operations are
`compact_visibility=full`; the compact surface remains exactly ten tools.

Evidence-basis policy remains shared with evidence recording, pre-tool policy,
trust audit, and promotion. M3 does not introduce a second evidence or trust
authority. Source acquisition also remains a separate existing capability;
discovery metadata cannot create a source asset.

## Fixture End-To-End Evidence

`tests/test_v5_gate3_qft_qg_e2e.py` proves a deterministic QFT/QG-shaped
vertical:

1. A hash-pinned local note and exact source location enter a disposable source
   shelf.
2. One grounded definition and one analogy receive separate hash-bound human
   reviews and promotions.
3. Concept and formula retrieval excludes a lexically similar algebraic-QFT
   assertion from a semiclassical-gravity request.
4. Bounded context retains the grounded/source/insight split, exact expansion
   handles, regime, convention, and visible speculation.
5. Missing metadata-only sources produce incomplete shelf coverage, and
   changed source bytes make the published generation fail closed.

The fixture writes neither Evidence nor trust updates. It is not evidence that
the real QFT/QG source corpus is complete or scientifically accepted.

## Real-Store Compatibility Audit

The authorized audit rebuilt only:

`F:/AI_Workspace/Theoretical-Physics/research/aitp-topics/.aitp/indexes`

No real canonical record was written by this M3 slice.

| Measure | Result |
|---|---:|
| Canonical records checked/indexed | 9,947 / 9,947 |
| Malformed records / build issues | 0 / 0 |
| Query-index generation | 15 |
| Index schema | 3 |
| Canonical watermark | `ce44b9c34a6d39448c9a67624091dd786893eed8e24f508c2f4fad24739cdd4a` |
| Index content hash | `16b84d86c8acb29b5dbdf6ffa8f449ce9c3f3a6257b2e19b85c37f9d5001489a` |

The manifest watermark matched a fresh canonical scan after rebuild. A later
QG knowledge query/startup-context probe also retained the same before/after
watermark.

The first real-store probe found 50 legacy `code_states` with no topic,
program, or linked topic scope after payload reconstruction. M3 now excludes
them from topic-scoped knowledge snapshots and reports
`excluded_unscoped_counts={"code_states": 50}`. This makes coverage partial and
forbids an exhaustive no-result claim; it does not guess a topic or rewrite the
records. Scoped formula-code records remain available through their explicit
links.

## Startup Performance

The read-only probe used topic `quantum-gravity-von-neumann` and the generation
15 index.

| Measure | Result |
|---|---:|
| Cold orientation knowledge query | 4.135 s |
| Warm startup knowledge context | 0.565 s |
| Query/context entries | 2 / 2 |
| Startup estimated tokens | 110 |
| Canonical watermark changed | no |

The earlier strong-content probe took about 20.7 seconds because it rehashed
all selected canonical family content. M3 therefore keeps strong verification
explicit and preserves its exhaustive semantics, while startup defaults to
orientation and cannot claim complete coverage.

## Test Evidence

All listed tests used Python 3.12 and isolated system-Temp `--basetemp` roots.

| Scope | Result |
|---|---:|
| Knowledge façade and QFT/QG vertical | 9 passed |
| Context/retrieval/façade shared-query regression | 46 passed |
| Capability registry | 9 passed |
| Public surfaces, CLI, and MCP | 52 passed |
| Native MCP content-length/NDJSON/compat smokes | 3 passed |
| Lifecycle façade | 7 passed |
| M3 broad regression before final architecture-only fix | 345 passed, 1 architecture failure |
| Final M3 worktree broad regression | 346 passed |
| Staged-candidate M3 broad regression | 345 passed |
| Staged-candidate native MCP protocol smokes | 3 passed |
| Final focused architecture/retrieval/façade/E2E | 28 passed |

The sole earlier broad-suite failure was `knowledge_retrieval.py` at 502 lines
after a new coverage field. Compressing that expression restored the 500-line
budget; both the focused architecture suite and the final 346-test worktree
suite passed. The isolated candidate exported from the Git index then passed
345 M3 tests plus three native MCP protocol smokes. The one-test count
difference is the unstaged concurrent addition in `test_v5_query_index_delta.py`;
it is not part of this change set.

## Residual Work

- M6 must ingest and inspect hash-pinned real QFT/QG source assets and exact
  location receipts before accepting formal-theory source memory.
- The 50 unscoped legacy code states require explicit review/migration if they
  should become topic- or program-scoped. M3 intentionally does not infer that
  binding.
- Strong content verification is suitable for explicit audit, not automatic
  startup. Future index work may add a cryptographically safe incremental
  content-verification cache without weakening absence semantics.
- `README.md` has a concurrent protected user modification and is excluded from
  this change set. Roadmap and release-audit documentation describe the M3
  behavior without overwriting that work.
