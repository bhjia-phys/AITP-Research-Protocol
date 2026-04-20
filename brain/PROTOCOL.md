---
name: aitp-protocol
version: "2.0"
description: Operating manual for the AITP brain-driven research protocol.
  Any agent reading this file can drive the protocol end-to-end.
---

# AITP Protocol — Brain-Driven Research Operating Manual

This document is the single source of truth for how to operate the AITP
(AI-assisted Theoretical Physics) protocol.  It is consumed by any
agent — Claude Code, Copilot, OpenCode, or a custom wrapper — that has
access to the AITP MCP tools.

## Core Model

The protocol is a **stage machine** with orthogonal posture and lane:

```
Stage:    L1 → L3 → L4 → L3 → L4 → ... → L2 → L5
Posture:  read | frame | derive | verify | distill | write
Lane:     formal_theory | toy_numeric | code_method
```

- **Stage** is hard state — you cannot skip or reverse.
- **Posture** is operating stance — what you *do* at the current stage.
- **Lane** is research style — orthogonal, does not affect gate logic.

Every agent action must respect the gate model.  When
`gate_status != "ready"`, you must fix missing requirements before
advancing.

## Quick Reference: Tool → When to Call

| Tool | Stage | When |
|------|-------|------|
| `aitp_bootstrap_topic` | — | First action for a new topic |
| `aitp_register_source` | L1 | Register each source (paper, book, dataset) |
| `aitp_ingest_knowledge` | L1 | Fill L1 artifacts from source content |
| `aitp_get_execution_brief` | any | **Always call this first** to check gate status |
| `aitp_advance_to_l3` | L1→L3 | After all L1 artifacts pass gate |
| `aitp_advance_l3_subplane` | L3 | Move between subplanes (respect allowed transitions) |
| `aitp_submit_candidate` | L3 | After distillation, submit a distilled claim |
| `aitp_create_validation_contract` | L4 | Define mandatory physics checks for a candidate |
| `aitp_submit_l4_review` | L4 | Submit adjudication outcome with evidence and provenance |
| `aitp_return_to_l3_from_l4` | L4→L3 | Return to L3 analysis after L4 pass (mandatory, not optional) |
| `aitp_advance_to_l5` | L4→L5 | Advance to writing phase (requires flow_notebook.tex from L3 distillation) |
| `aitp_request_promotion` | L4→L2 | Request promotion for a validated candidate |
| `aitp_resolve_promotion_gate` | L4→L2 | Approve or reject the promotion |
| `aitp_promote_candidate` | L4→L2 | Execute the promotion (writes to global L2) |
| `aitp_advance_to_l5` | L4→L5 | Enter paper writing (requires flow_notebook.tex) |
| `aitp_query_knowledge` | any | Query the knowledge base (returns authority level) |
| `aitp_lint_knowledge` | any | Check for contradictions, missing regime, broken provenance |
| `aitp_writeback_query_result` | any | Write a note back to the appropriate layer |
| `aitp_get_status` | any | Read topic state |

## End-to-End Flow

### Phase 1: Bootstrap (stage = L1, posture = read)

```
1. aitp_bootstrap_topic(topics_root, topic_slug, title, question, lane)
   → Creates directory structure, state.md, L1 artifact scaffolds

2. aitp_register_source(topics_root, topic_slug, source_id, ...)
   → One call per source. Creates L0/sources/<id>.md

3. aitp_ingest_knowledge(topics_root, topic_slug, source_id, ...)
   → Updates L1 artifacts from source content

4. aitp_get_execution_brief(topics_root, topic_slug)
   → Check gate_status. If "ready", proceed to Phase 2.
   → If "blocked_missing_field", edit the flagged artifact.
   → If "blocked_missing_artifact", create the missing file.
```

L1 requires 5 filled artifacts:
- `question_contract.md` — bounded question, scope, target quantities
- `source_basis.md` — core and peripheral sources
- `convention_snapshot.md` — notation, units, sign conventions
- `derivation_anchor_map.md` — starting points for derivation
- `contradiction_register.md` — blocking contradictions (even if "none")

### Phase 2: L3 Derivation (stage = L3, posture = derive)

```
5. aitp_advance_to_l3(topics_root, topic_slug)
   → Sets stage=L3, l3_subplane=ideation

6. Walk subplanes in order: ideation → planning → analysis
   → result_integration → distillation

   For each subplane:
   a. Edit the active artifact (e.g., L3/ideation/active_idea.md)
      Fill frontmatter fields AND body headings.
   b. aitp_advance_l3_subplane(topics_root, topic_slug, next_subplane)
      Only forward transitions are allowed (see table below).
      Back-edges exist for revision (analysis→planning, etc.)

7. aitp_submit_candidate(topics_root, topic_slug, candidate_id, claim, evidence)
   → After distillation is complete. Creates L3/candidates/<id>.md
```

Allowed L3 transitions:
```
ideation       → planning
planning       → analysis, ideation
analysis       → result_integration, ideation, planning
result_integration → distillation, analysis
distillation   → result_integration
```

### Phase 3: L4 Validation (stage = L4, posture = verify)

```
8.  aitp_create_validation_contract(topics_root, topic_slug, candidate_id,
      mandatory_checks=["dimensional_consistency", ...])
    → Defines what must be checked.

9.  Write validation scripts (L4/scripts/) and execute on target machine.
    Every data point must have provenance: script path, execution timestamp, method.

10. aitp_submit_l4_review(topics_root, topic_slug, candidate_id,
      outcome, notes, evidence_scripts=[...], evidence_outputs=[...],
      data_provenance=[...])
    → outcome ∈ {pass, partial_pass, fail, contradiction, stuck, timeout}
    → evidence_scripts/outputs REQUIRED for toy_numeric and code_method lanes
    → data_provenance REQUIRED: every data point traced to a specific script execution
```

**L4 pass does NOT advance to L5.** It returns to L3 for post-validation analysis.

### Phase 3b: L4→L3 Return Loop (stage = L3, posture = derive)

```
11. aitp_return_to_l3_from_l4(topics_root, topic_slug, reason="post_l4_analysis")
    → Returns to L3 analysis subplane

12. Analyze L4 findings in L3/analysis/active_analysis.md
    → What passed conclusively? What had caveats? What remains open?
    → Update flow_notebook.tex with L4 results

13. Ask the human (MANDATORY):
    - "Persist and advance" → proceed to promotion/L5
    - "Continue iterating" → new L3 cycle (plan → analyze → integrate → distill → L4)
    - "Revise scope" → narrow/adjust the claim
```

This loop continues until the human confirms the topic is ready to persist.
Each L3 cycle does incremental flow_notebook.tex updates at every subplane.

Physics check fields:
`dimensional_consistency`, `symmetry_compatibility`,
`limiting_case_check`, `conservation_check`, `correspondence_check`

### Phase 4: Promotion to Global L2

```
14. Agent generates L3/tex/flow_notebook.tex during L3 distillation
    (Markdown→LaTeX conversion and PDF compilation per skill-l3-distill)

15. Request → resolve → promote:
    aitp_request_promotion(topics_root, topic_slug, candidate_id)
    aitp_resolve_promotion_gate(topics_root, topic_slug, candidate_id, "approve")
    aitp_promote_candidate(topics_root, topic_slug, candidate_id)
    → Writes to global L2/ (cross-topic reusable knowledge)
    → Assigns 2D trust: (basis=validated, scope=bounded_reusable)
    → Conflict detection and version bumping handled automatically.
```

### Phase 5: L5 Writing (stage = L5, posture = write)

```
16. aitp_advance_to_l5(topics_root, topic_slug)
    → BLOCKED if flow_notebook.tex does not exist.
    → Creates L5_writing/ provenance scaffolds:
      - outline.md
      - claim_evidence_map.md
      - equation_provenance.md
      - figure_provenance.md
      - limitations.md
```

Fill these provenance files before drafting paper content.

## Gate Model Summary

Every tool that changes state checks gates.  The pattern is:

1. Call `aitp_get_execution_brief` to see current state.
2. If `gate_status == "ready"` and `next_allowed_transition` matches your
   intended action → proceed.
3. If `gate_status == "blocked_*"` → fix the flagged artifact first.
4. Never skip stages. Never call a tool for a later stage while blocked.

## Agent Decision Loop

For any agent driving this protocol, the loop is:

```
while topic is not complete:
    brief = aitp_get_execution_brief(topics_root, topic_slug)

    if brief.gate_status == "blocked_missing_artifact":
        Create the missing artifact file.
        continue

    if brief.gate_status == "blocked_missing_field":
        Edit the flagged artifact. Fill the missing fields/headings.
        continue

    if brief.gate_status == "ready":
        Match on brief.stage:
            "L1" → Fill remaining L1 artifacts or advance to L3
            "L3" → Work on active subplane artifact, then advance
            "L4" → Validate candidate with code, submit review,
                    then return to L3 via aitp_return_to_l3_from_l4
            "L5" → Fill provenance files, then draft paper
        continue
```

## Knowledge Authority Model

Every query returns `basis_layer` and `authority_warning`.  Respect this:

- **L1** answer = source-grounded, no derivation yet
- **L3** answer = derivation in progress, not validated
- **L4** answer = validated claim, can be reused
- **L2** answer = promoted reusable knowledge, highest trust

Never treat a lower-layer answer as having higher-layer authority.

## Directory Layout

```
topics_root/
├── L2/                              # Global reusable knowledge
│   ├── index.md                     # Cross-topic index
│   ├── log.md                       # Promotion history
│   ├── <candidate>.md               # Promoted units (2D trust)
│   └── conflicts/<candidate>.md     # Conflict records
│
└── topics/<slug>/
    ├── state.md                     # Core state machine
    ├── L0/sources/*.md              # Registered sources
    ├── L1/                          # Framing artifacts (5 files)
    ├── L3/
    │   ├── <subplane>/active_*.md   # Subplane artifacts
    │   ├── candidates/*.md          # Submitted candidates
    │   └── tex/flow_notebook.tex    # Flow-end archive
    ├── L4/
    │   ├── validation_contract.md
    │   ├── scripts/*.py               # Validation scripts (mandatory for numeric lanes)
    │   ├── outputs/                   # Execution logs, plots, data tables
    │   └── reviews/*.md
    ├── L5_writing/                  # Paper provenance
    │   ├── outline.md
    │   ├── claim_evidence_map.md
    │   ├── equation_provenance.md
    │   ├── figure_provenance.md
    │   └── limitations.md
    └── runtime/
        ├── index.md                 # Topic index
        └── log.md                   # Event log
```
