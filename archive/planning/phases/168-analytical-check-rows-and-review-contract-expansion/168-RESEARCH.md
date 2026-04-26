# Phase 168: Analytical Check Rows And Review Contract Expansion - Research

**Researched:** 2026-04-13
**Domain:** richer row-level analytical cross-check contract inside the
existing `analytical_review` artifact family
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- build on the existing `analytical_review` artifact family and public
  `analytical-review` CLI/service entrypoint
- keep the durable artifact at `analytical_review.json` and preserve the
  existing validation-review bundle integration path
- make each `checks[]` row self-contained with source anchors, assumption or
  regime context, and reading-depth posture
- add `source_cross_reference` to the analytical check taxonomy
- keep top-level rollups for compatibility, but make them projections from the
  richer row set
- defer new runtime/read-path analytical surfaces and the bounded proof lane to
  Phase `168.1`

### the agent's Discretion
- exact row field names for row-level context
- whether existing review-level CLI flags become defaults only or also gain
  optional row-specific overrides
- exact rollup strategy for top-level compatibility fields

### Deferred Ideas (OUT OF SCOPE)
- new runtime/read-path analytical surfaces
- a new milestone-close proof harness
- CAS, symbolic backend, or route-mutation work from analytical checks

</user_constraints>

<research_summary>
## Summary

`v1.47` already built the analytical-review path end-to-end:

- parser and dispatch in `cli_review_handler.py`
- artifact normalization and writing in `analytical_review_support.py`
- theory-packet storage and validation-mode defaults in `aitp_service.py`
- review-bundle selection in `validation_review_service.py`
- production CLI e2e and bounded acceptance coverage

That means the open gap is not artifact existence. The open gap is that the
stored `checks[]` rows are still thin while source anchors, assumptions,
regime context, and reading-depth posture live mostly at the review level.

**Primary recommendation:** keep `analytical_review.json` and the public
`checks` field, but enrich each check row so it becomes the authoritative
durable unit. Then derive top-level counts, summaries, and compatibility
fields from that richer row set. This closes `REQ-ANX-01` and `REQ-ANX-02`
without reopening the runtime/read-path work that belongs to `168.1`.

</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `research/knowledge-hub/knowledge_hub/analytical_review_support.py` | repo-local | Row normalization, blocker logic, rollups, durable artifact writing | Canonical upgrade point for the contract |
| `research/knowledge-hub/knowledge_hub/cli_review_handler.py` | repo-local | Public CLI parser and dispatch for `analytical-review` | Keeps the contract on the current entrypoint |
| `research/knowledge-hub/knowledge_hub/aitp_service.py` | repo-local | Theory-packet paths and analytical validation defaults | Holds the current analytical-mode wording and artifact routing |
| `research/knowledge-hub/knowledge_hub/validation_review_service.py` | repo-local | Primary review bundle selection | Compatibility guard for analytical mode |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `research/knowledge-hub/tests/test_aitp_service.py` | repo-local | Durable artifact and validation-bundle coverage | Lock row-level payload semantics mechanically |
| `research/knowledge-hub/tests/test_aitp_cli.py` | repo-local | CLI parser and dispatch coverage | Guard public command compatibility |
| `research/knowledge-hub/tests/test_aitp_cli_e2e.py` | repo-local | Production-CLI e2e path | Prove the public flow still works end to end |
| `research/knowledge-hub/runtime/scripts/run_analytical_judgment_surface_acceptance.py` | repo-local | Existing bounded acceptance lane | Keep as compatibility guard while new proof lane stays deferred |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| enrich existing `checks` rows | add a new `analytical_cross_check` artifact family | cleaner separation, but much wider compatibility churn |
| derive top-level rollups from rows | keep review-level context authoritative and duplicate rows later | faster patch, but leaves the row contract weak |
| preserve current CLI flags as defaults | force a brand-new row-specific CLI grammar immediately | more precise end state, but higher breakage risk for the current public flow |

**Installation:**
```bash
# No new dependencies required for Phase 168.
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Enrich the existing `checks` rows instead of replacing the artifact family
**What:** keep `analytical_review.json` and `checks[]`, but make each row
carry the context it currently borrows from top-level fields.
**Why:** the public artifact path already exists and is integrated into current
validation surfaces.

### Pattern 2: Treat top-level fields as compatibility rollups
**What:** keep review-level `overall_status`, counts, `summary`,
`source_anchors`, `assumption_refs`, `regime_note`, and `reading_depth`, but
derive them from the normalized row set.
**Why:** this preserves compatibility now while moving the durable truth into
the richer check rows.

### Pattern 3: Compatibility-first CLI contract expansion
**What:** preserve the current `analytical-review` command shape and current
review-level flags as defaults that can be projected into each row.
**Why:** existing e2e and acceptance flows already depend on that public path.

### Pattern 4: Hold runtime/read-path work for the next phase
**What:** limit Phase `168` to artifact and contract maturity.
**Why:** the roadmap already reserves runtime/read-path analytical surfaces and
the new proof lane for Phase `168.1`.

### Anti-Patterns to Avoid
- adding row fields but leaving them empty or purely decorative
- inventing a second analytical artifact family before the current one is
  mature
- breaking the current CLI/e2e flow by removing review-level compatibility
  inputs
- widening into runtime/read-path rendering changes in this phase

</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| richer analytical visibility | a new `analytical_cross_check.json` artifact family | existing `analytical_review.json` plus richer `checks[]` rows | keeps compatibility churn bounded |
| per-check context | global-only review fields | row-level `source_anchors`, `assumption_refs`, `regime_note`, and `reading_depth` on each check | satisfies the requirement where the durable unit actually lives |
| milestone proof closure | a new acceptance harness in Phase `168` | current acceptance script as compatibility guard, new proof lane in `168.1` | preserves the roadmap split |

</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: enriching rows without moving the durable truth
If row fields stay empty while top-level fields remain authoritative, the
phase still leaves a flatter aggregate payload.

### Pitfall 2: forgetting the new check taxonomy at every contract boundary
`source_cross_reference` must be accepted by normalization and reflected in
analytical validation wording, not only added in one test fixture.

### Pitfall 3: forcing a breaking CLI redesign too early
The public `analytical-review` flow is already covered by e2e and acceptance
tests. Preserve it unless a concrete row-level need proves otherwise.

### Pitfall 4: sneaking `168.1` runtime work into `168`
Phase `168` should leave the artifact richer, not redesign the read path.

</common_pitfalls>

<code_examples>
## Code Examples

### Current review-level context dominates the artifact
```python
# Source: knowledge_hub/analytical_review_support.py
{
    "reading_depth": normalized_reading_depth,
    "source_anchors": normalized_source_anchors,
    "assumption_refs": normalized_assumption_refs,
    "regime_note": normalized_regime_note,
    "checks": normalized_checks,
}
```

### Current check rows are still thin
```python
# Source: knowledge_hub/analytical_review_support.py
{
    "kind": kind,
    "label": label,
    "status": status,
    "notes": notes,
}
```

### Current public CLI grammar already supplies review-level defaults
```python
# Source: knowledge_hub/cli_review_handler.py
analytical_review.add_argument("--check", action="append", default=[], type=_parse_analytical_check)
analytical_review.add_argument("--source-anchor", action="append", default=[])
analytical_review.add_argument("--assumption", action="append", default=[])
analytical_review.add_argument("--regime-note")
analytical_review.add_argument("--reading-depth", choices=["skim", "targeted", "deep"], default="targeted")
```
</code_examples>

<sota_updates>
## State of the Art (2026 Repository State)

| Current State | Limitation | Phase 168 Target |
|---------------|------------|------------------|
| analytical review is already a production artifact family | `checks[]` rows are too thin | richer self-contained analytical check rows |
| analytical mode already promotes `analytical_review` into the primary bundle when present | bundle integration depends on a flatter artifact contract | preserve bundle behavior while enriching the artifact contract |
| analytical judgment acceptance already proves the old lane | no richer row-level contract is locked yet | strengthen the contract without reopening the proof lane |

</sota_updates>

<open_questions>
## Open Questions

1. **Do we need row-specific CLI overrides in Phase 168, or are review-level defaults enough?**
   - Recommendation: start with the current review-level flags as defaults
     copied into every row. Add row-specific overrides only if a concrete test
     proves that divergent per-check context is required now.

2. **Should top-level compatibility fields stay present after the row upgrade?**
   - Recommendation: yes. Keep them as deduped rollups from the richer row set
     so current readers remain stable until `168.1` lands the new runtime
     surfaces.

</open_questions>
