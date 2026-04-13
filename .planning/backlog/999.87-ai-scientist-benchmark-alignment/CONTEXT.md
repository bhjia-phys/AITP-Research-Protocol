# Milestone Proposal: AI Scientist Benchmark Knowledge Extraction Alignment

**Proposed milestone name:** `v1.96 AI Scientist Benchmark Knowledge Extraction Alignment`
**Proposed milestone label:** `benchmark-knowledge-alignment`
**Source analysis:** `.sisyphus/drafts/_scratch/ai_scientist_benchmark.txt` (14-page PDF extraction)
**Backlog items:** 999.87–999.92
**Depends on:** `v1.95` (L2 Promotion Pipeline Closure) — specifically Phase 169 schema work

## Motivation

The AI Scientist Benchmark (2026) evaluates AI research competence by two axes:

1. **Paper Search** — expert-level literature relevance grading (5-tier scale: 3+/3/2/1/0)
2. **Paper Understanding** — structured extraction of conclusions, motivations, and open problems with mandatory conditions/assumptions and sentence-level evidence

AITP's knowledge extraction pipeline (`L0→L1→L3→L4→L2`) maps to the benchmark's extraction chain, but is structurally weaker at every layer in granularity and structured field requirements. The benchmark implicitly defines a minimum standard for "competent AI research knowledge extraction" — AITP should meet or exceed that standard.

## Gap Summary

| Gap | AITP Current | Benchmark Standard | Backlog |
|-----|-------------|-------------------|---------|
| Source relevance classification | acquire/pending binary | 5-tier relevance + role labels | 999.87 |
| Knowledge type discrimination | flat claims | conclusion/motivation/open_problem trichotomy | 999.88 |
| Condition tracking | no required conditions field | mandatory conditions_and_assumptions | 999.89 |
| Evidence granularity | section-level tracing | sentence-level anchoring (1–3 IDs) | 999.90 |
| L4 validation robustness | single-path | multi-reviewer cross-validation | 999.91 |
| L2 expert anchoring | AI-only summaries | human expert annotation attachment | 999.92 |

## Proposed Phase Breakdown

### Phase A: Source Intelligence (999.87)

**Axis:** A1 + A2

**Goal:** Add `relevance_tier` and `role_labels` to `source-item.schema.json`. Wire the new fields into L0 intake and the L0→L1 reading priority path.

**Depends on:** Phase 169 (canonical schema work in v1.95)

**Plans:**
1. Extend `source-item.schema.json` with `relevance_tier` enum and `role_labels` array
2. Update runtime mirror and `source_catalog_support.py` to produce/consume the new fields
3. Wire relevance tier into L0→L1 reading priority (higher tier → deeper reading)

### Phase B: Candidate Type and Condition Requirements (999.88 + 999.89)

**Axis:** A1 + A2

**Goal:** Extend `candidate-claim.schema.json` with `knowledge_type` trichotomy and make `conditions_and_assumptions` required for type `conclusion`. These two items are tightly coupled — the trichotomy defines which types require conditions, so they ship together.

**Depends on:** Phase 169 (schema evolution precedent from v1.95)

**Plans:**
1. Add `knowledge_type` enum to `candidate-claim.schema.json` with type-specific required field maps
2. Add `conditions_and_assumptions` as required for `conclusion` type
3. Update runtime mirror, candidate production helpers, and L4 validation to enforce type-specific requirements

### Phase C: Sentence-Level Evidence (999.90)

**Axis:** A1 + A3

**Goal:** Refine L1 vault intake from section-level to sentence-level evidence anchoring. Each extracted knowledge unit carries 1–3 sentence identifiers.

**Depends on:** Phase B (needs `knowledge_type` field to know what to anchor)

**Plans:**
1. Add `evidence_sentence_ids` field to the L1 intake schema
2. Update L1 vault intake helpers to extract and record sentence-level anchors
3. Update L4 validation to mechanically check claim-evidence correspondence

### Phase D: L4 Multi-Reviewer Protocol (999.91)

**Axis:** A1 + A2

**Goal:** Introduce multi-reviewer cross-validation in L4. At least two independent reviewer passes per candidate claim, with disagreement escalation.

**Depends on:** Phase B (needs `knowledge_type` for type-aware review)

**Plans:**
1. Define multi-reviewer validation contract in L4
2. Implement reviewer pass orchestration with different system prompts
3. Add disagreement detection and human escalation path

### Phase E: L2 Expert Annotation (999.92)

**Axis:** A2 + A4

**Goal:** Allow L2 promoted items to carry structured expert annotations (relevance tier, role labels, comments, key points) from the human promotion gate or external data.

**Depends on:** Phase A (needs `relevance_tier` and `role_labels` schema) + Phase D (needs validated candidates before annotation makes sense)

**Plans:**
1. Add `expert_annotations` field to L2 knowledge packet schema
2. Wire annotation capture into the human promotion gate
3. Add annotation import path for external benchmark data

## Dependency Graph

```
Phase 169 (v1.95) ──┬── Phase A (999.87)
                     │
                     ├── Phase B (999.88 + 999.89) ──┬── Phase C (999.90)
                     │                                │
                     │                                └── Phase D (999.91)
                     │
Phase A (999.87) ────────────────────────────────────── Phase E (999.92)
Phase D (999.91) ──────────────────────────────────────── Phase E (999.92)
```

**Parallelism:** Phase A and Phase B can run in parallel after v1.95 ships. Phase C and Phase D can run in parallel after Phase B. Phase E depends on both A and D.

**Critical path:** `v1.95 → B → D → E` (4 steps sequential)

## Success Criteria

- Every acquired L0 source has a `relevance_tier` and at least one `role_label`
- Every L3 candidate claim has a `knowledge_type` and claims of type `conclusion` have non-empty `conditions_and_assumptions`
- L1 intake records at least 1 sentence-level evidence anchor per extracted knowledge unit
- L4 validation produces at least 2 independent reviewer passes per candidate claim
- L2 promoted items can carry structured expert annotations
- All changes pass existing acceptance tests and new schema-specific acceptance tests

## Risk Notes

- **Sentence-level anchoring** requires L1 vault infrastructure changes that may conflict with ongoing vault work — coordinate with v1.95 HCI phases
- **Multi-reviewer L4** increases per-candidate validation cost — consider a lightweight first pass and a deep second pass rather than two full passes
- **Expert annotations** are only useful if the human actually provides them during promotion — the UI needs to be lightweight, not a form-filling exercise
