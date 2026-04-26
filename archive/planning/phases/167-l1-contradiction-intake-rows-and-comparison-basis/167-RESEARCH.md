# Phase 167: L1 Contradiction Intake Rows And Comparison Basis - Research

**Researched:** 2026-04-13
**Domain:** richer contradiction rows inside existing `L1` source-intake contracts
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- build on the existing `l1_source_intake` contradiction path rather than
  inventing a separate contradiction subsystem
- keep contradiction rows pairwise and source-backed for this phase
- each row must carry both source refs, both reading-depth postures, and a
  bounded comparison basis rather than only a thin warning string
- keep current `contradiction_candidates` consumers working during this phase
- keep notation tensions separate from contradiction rows
- defer runtime/read-path presentation work and the milestone proof lane to
  Phase `167.1`

### the agent's Discretion
- exact richer row fields and dedup keys
- whether the richer shape remains stored under `contradiction_candidates` or is
  projected from an internal richer helper
- exact schema evolution strategy so current surfaces keep working

### Deferred Ideas (OUT OF SCOPE)
- multi-source contradiction clustering
- scientific adjudication of which source is correct
- automatic route mutation or checkpoint creation from contradiction rows

</user_constraints>

<research_summary>
## Summary

The repository already has a contradiction surface in `L1`, but it is still a
thin intermediate warning shape. The main architectural advantage is that the
whole contradiction path already exists end-to-end:

- intake derivation in `l1_source_intake_support.py`
- schema coverage in the progressive-disclosure runtime bundle
- read-path summaries in runtime and vault helpers
- one bounded acceptance lane in `run_l1_assumption_depth_acceptance.py`

That means the lowest-risk implementation is not to add a new contradiction
object family. The lowest-risk implementation is to enrich the existing row
shape so downstream surfaces have better raw material, while keeping current
field compatibility until Phase `167.1` can do the broader read-path cleanup.

**Primary recommendation:** enrich the current contradiction row payload around
three reusable ingredients already available in `L1`:

1. source identity and titles
2. reading-depth posture for both compared sources
3. extracted assumption / regime summaries that explain the comparison basis

This keeps the phase narrowly inside `L1` intake maturity and avoids broad
surface churn.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `research/knowledge-hub/knowledge_hub/l1_source_intake_support.py` | repo-local | Contradiction derivation, normalization, summary helpers | This is the canonical upgrade point |
| `research/knowledge-hub/knowledge_hub/source_distillation_support.py` | repo-local | Builds the base `L1` source-intake payload | Richer contradiction rows should ride on the existing intake build path |
| `research/knowledge-hub/runtime/schemas/progressive-disclosure-runtime-bundle.schema.json` | repo-local | Runtime schema contract | The richer row shape must stay schema-backed |
| `research/knowledge-hub/tests/test_aitp_service.py` | repo-local | Service/runtime intake contract coverage | Existing contradiction fixtures already live here |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `research/knowledge-hub/runtime/scripts/run_l1_assumption_depth_acceptance.py` | repo-local | Existing contradiction-aware acceptance lane | Use to preserve the established L1 honesty contract |
| `research/knowledge-hub/tests/test_runtime_scripts.py` | repo-local | Acceptance-script invocation coverage | Update if the bounded intake lane shape changes |
| `research/knowledge-hub/tests/test_schema_contracts.py` | repo-local | Schema contract lock | Update if richer row fields are added to schema |
| `research/knowledge-hub/knowledge_hub/source_intelligence.py` | repo-local | Contradiction detection helper | Read to understand what the detector emits today |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| enrich existing contradiction rows | add a new top-level contradiction artifact | clearer separation, but much wider compatibility and surface churn |
| pairwise contradiction rows | multi-source contradiction clusters now | richer end state, but too wide for the current phase |
| schema-backed richer rows | markdown-only contradiction notes | quicker to patch, but loses machine-readable parity and later read-path reuse |

**Installation:**
```bash
# No new dependencies required for Phase 167.
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Enrich existing row families instead of splitting the subsystem
**What:** evolve the current `contradiction_candidates` row shape inside
`l1_source_intake`.
**Why:** the repo already treats `L1` interpretation surfaces as row arrays
under one intake family, and contradiction rows already participate in that
pattern.

### Pattern 2: Derive contradiction basis from already-extracted intake facts
**What:** fill richer contradiction rows using assumption / regime /
reading-depth data that `L1` already extracts.
**Why:** this keeps contradiction explanations grounded in durable intake facts
instead of fresh synthesis.

### Pattern 3: Compatibility-first schema evolution
**What:** expand the contradiction row schema while preserving the current field
path for this phase.
**Why:** current runtime/vault helpers and tests already read
`contradiction_candidates`; Phase `167` should not force a wide rename before
Phase `167.1`.

### Anti-Patterns to Avoid
- replacing contradiction rows with free-form prose only
- adding adjudication logic that decides which source is correct
- folding notation tension into contradiction rows
- broad runtime/rendering churn before the row shape itself is stable

</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| richer contradiction visibility | a separate contradiction artifact tree | existing `l1_source_intake` row family | current code already carries contradiction rows through the intake contract |
| contradiction explanation | fresh LLM-only summaries | source-backed assumption/regime excerpts plus reading-depth posture | explanation should stay durable and auditable |
| validation | a brand-new proof harness in this phase | existing service/schema tests and the current assumption-depth acceptance lane | Phase `167` is an internal maturity slice, not the milestone proof lane |

</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: confusing contradiction visibility with contradiction resolution
This phase should make disagreement explicit, not settle scientific truth.

### Pitfall 2: widening into read-path cleanup too early
Current consumers already exist. Let Phase `167.1` own the broad rendering
cleanup once the row shape is stable.

### Pitfall 3: losing comparison basis during normalization
If normalization keeps only `detail`, the row is still too thin to guide later
read-path rendering or human judgment.

### Pitfall 4: overfitting to one fixture
The richer row shape should generalize beyond the current weak-vs-strong
coupling test pair.

</common_pitfalls>

<code_examples>
## Code Examples

### Existing thin contradiction normalization
```python
# Source: knowledge_hub/l1_source_intake_support.py
{
    "kind": ...,
    "source_id": ...,
    "against_source_id": ...,
    "detail": ...,
}
```

### Existing conflict derivation path
```python
# Source: knowledge_hub/l1_source_intake_support.py
for candidate in detect_contradiction_candidates(...):
    contradiction_candidates.append(...)
```

### Existing service fixture proving contradiction rows already flow through `L1`
```python
# Source: tests/test_aitp_service.py
self.assertEqual(len(l1_source_intake["contradiction_candidates"]), 1)
```
</code_examples>

<sota_updates>
## State of the Art (2026 Repository State)

| Current State | Limitation | Phase 167 Target |
|---------------|------------|------------------|
| contradiction candidates exist | rows are too thin to explain the comparison basis | richer source-backed contradiction rows |
| runtime/vault helpers already summarize contradiction rows | summaries can only render weak detail strings | later phases can render richer contradiction surfaces |
| assumption/depth acceptance already proves contradiction presence | it does not yet prove a strong comparison record | phase can strengthen the underlying row contract first |

</sota_updates>

<open_questions>
## Open Questions

1. **Should richer rows carry explicit claim excerpts or normalized summaries?**
   - Recommendation: prefer bounded summaries / excerpts derived from existing
     intake rows over large raw text blobs.

2. **Should deduplication key on the pair only, or the pair plus comparison basis?**
   - Recommendation: include the bounded comparison basis in dedup logic so one
     source pair can still surface multiple distinct contradiction rows when the
     compared claims differ materially.

</open_questions>
