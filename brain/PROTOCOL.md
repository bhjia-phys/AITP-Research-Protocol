---
name: aitp-protocol
version: "4.0"
description: Operating manual for the AITP adversarial-collaborator protocol.
  Python stores and searches, you judge physics. Evidence before claims.
  Derivations before conclusions. Limits before generalizations.
---

# AITP Protocol — Brain-Driven Research Operating Manual

## Supreme Protocol (至高协议)

**追求真理而非沽名钓誉。Pursue truth, not fame.**

- L2 trust levels reflect physical reliability, not publication count.
- Negative results and limitations have equal value to positive results.
- Artifacts exist to serve physical correctness, not bureaucratic completeness.
- Every claim in L2 must be traceable to its source. No assertion without provenance.
- The endpoint of each topic is knowledge contributed to L2. The start of each
  topic is knowledge retrieved from L2. L2 is the memory of the protocol.

## Core Model

The protocol is a **stage machine** with orthogonal posture, lane, and L3 mode:

```
Stage:    L0 (discover) → L1 (read → frame) → L3 → L4 → L3 → L4 → ... → L2
Posture:  discover | read | frame | derive | verify | distill
Lane:     formal_theory | toy_numeric | code_method
L3 Mode:  research | study
```

- **Stage** is hard state — you cannot skip or reverse.
- **Posture** is operating stance — what you *do* at the current stage.
- **Lane** is research style — orthogonal, does not affect gate logic.
- **L3 Mode** determines the subplane flow within L3:
  - **research** (default): ideation → planning → analysis → result_integration → distillation
  - **study**: source_decompose → step_derive → gap_audit → synthesis

Every agent action must respect the gate model.  When
`gate_status != "ready"`, you must fix missing requirements before
advancing.

## Quick Reference: Tool → When to Call

### Lifecycle & State
| Tool | Stage | When |
|------|-------|------|
| `aitp_bootstrap_topic` | — | Create topic directory structure + scaffolds |
| `aitp_get_execution_brief` | any | **Always call first** — gate status, compute target, next steps |
| `aitp_get_status` | any | Read topic state |
| `aitp_session_resume` | any | Resume after session break |
| `aitp_health_check` | — | Aggregated dashboard of all topics |
| `aitp_list_topics` | — | List all topics |
| `aitp_archive_topic` | any | Archive a topic |
| `aitp_restore_topic` | archived | Restore from archive |
| `aitp_fork_topic` | any | Fork a side-discovery into a new topic |

### Stage Transitions
| Tool | Stage | When |
|------|-------|------|
| `aitp_advance_to_l1` | L0→L1 | After L0 source_registry.md passes gate |
| `aitp_advance_to_l3` | L1→L3 | After all L1 artifacts pass gate. Set l3_mode |
| `aitp_advance_l3_subplane` | L3 | Move between subplanes (respect allowed transitions) |
| `aitp_retreat_to_l0` | L1/L3 | Return to L0 |
| `aitp_retreat_to_l1` | L3 | Return to L1 |
| `aitp_switch_l3_mode` | L3 | Switch research ↔ study mode |
| `aitp_switch_lane` | any | Change lane (formal_theory / toy_numeric / code_method) |

### Sources & Candidates
| Tool | Stage | When |
|------|-------|------|
| `aitp_register_source` | L0 | Register each source |
| `aitp_list_sources` | any | List registered sources |
| `aitp_parse_source_toc` | L1 | Parse and record a source's table of contents into source_toc_map |
| `aitp_update_section_status` | L1 | Mark a section extracted/deferred in source_toc_map |
| `aitp_write_section_intake` | L1 | Write per-section intake note with concepts/equations/claims |
| `aitp_submit_candidate` | L3 | Submit a candidate claim |
| `aitp_list_candidates` | any | List all candidates |

### L4 Adversarial Review
| Tool | Stage | When |
|------|-------|------|
| `aitp_submit_l4_review` | L4 | Submit review with evidence; devil's advocate REQUIRED for pass |
| `aitp_list_inference_rules` | L3/L4 | List available derivation inference rules |
| `aitp_verify_derivation_step` | L3/L4 | Verify one derivation step via SymPy |
| `aitp_verify_derivation_chain` | L3/L4 | Verify entire derivation chain via SymPy |

### Mathematical Verification (SymPy)
| Tool | Stage | When |
|------|-------|------|
| `aitp_verify_dimensions` | L3/L4 | Check dimensional consistency of an equation |
| `aitp_verify_algebra` | L3/L4 | Verify algebraic identity |
| `aitp_verify_limit` | L3/L4 | Check limit behavior (correspondence principle) |

### Promotion
| Tool | Stage | When |
|------|-------|------|
| `aitp_request_promotion` | L4→L2 | Request promotion (needs validated candidate) |
| `aitp_resolve_promotion_gate` | L2 | Human approves/rejects promotion |
| `aitp_promote_candidate` | L2 | Execute promotion → global L2 |

## L2 Knowledge Graph — The Protocol's Memory

L2 is the persistent, cross-topic knowledge graph. It is the **endpoint of every
topic** and the **starting point of every new topic**.

### Design Principles

1. **Compiled, not raw.** L2 stores distilled knowledge — concepts, theorems,
   relations, regime boundaries — not raw source text. Source provenance is
   stored for auditing but not exposed in default queries to prevent context
   bloat.
2. **Source-grounded.** Every node and edge must record its origin (source
   reference or topic candidate). No assertion without provenance.
3. **Progressive disclosure.** `aitp_query_l2_index` returns domain summaries.
   `aitp_query_l2_graph` returns matching nodes. Full details on demand.
4. **Trust evolves.** source_grounded → multi_source_confirmed → validated →
   independently_verified.

### Two Paths to L2

**Path A — Lightweight (L0→L2 directly):** For well-understood concepts where
the relationship is obvious and the source is clear. Create nodes and edges
immediately without going through L3 derivation.

**Path B — Deep (L0→L1→L3→L4→L2):** For novel or uncertain claims that
require derivation, adversarial review, and formal validation.

### Tools

| Tool | Stage | When |
|------|-------|------|
| `aitp_query_l2_index` | any | Progressive-disclosure domain taxonomy — first call for any topic |
| `aitp_query_l2_graph` | any | Query L2 graph with filters (type, tower, edges). Source fields hidden by default |
| `aitp_create_l2_node` | any | Create L2 graph node. source_ref REQUIRED |
| `aitp_update_l2_node` | any | Update node fields |
| `aitp_create_l2_edge` | any | Create typed edge. source_ref REQUIRED |
| `aitp_create_l2_tower` | any | Define EFT tower |
| `aitp_merge_subgraph_delta` | L3 study | Merge study subgraph into L2 |
| `aitp_quick_l2_concept` | any | Lightweight: create concept + theorem nodes with edges in one call |

### Source Provenance (hidden from default query output)

Every L2 node and edge records `source_ref` — a traceable reference to the
evidence. This field is stored in the node/edge frontmatter but is
**excluded from `aitp_query_l2_index` and `aitp_query_l2_graph` output**
to keep context lean. To inspect provenance, use `aitp_get_l2_provenance`.

### Domain Taxonomy

L2 nodes are organized by domain. Valid domains are enumerated (not free text):

| Domain | Scope |
|--------|-------|
| `electronic-structure` | DFT, GW, BSE, RPA, band structure methods |
| `quantum-many-body` | Green's functions, Feynman diagrams, RG, tensor networks |
| `qft` | QED, QCD, EFT, axiomatic QFT, CFT |
| `condensed-matter` | Superconductivity, topological phases, strongly correlated systems |
| `quantum-gravity` | String theory, LQG, holography, AdS/CFT |
| `generalized-symmetries` | Higher-form, non-invertible, categorical symmetries |
| `quantum-information` | Entanglement, quantum channels, error correction |
| `statistical-mechanics` | Phase transitions, critical phenomena, transport |
| `aitp-protocol` | AITP internal — protocol design, skills, workflows |

### Configuration
| Tool | Stage | When |
|------|-------|------|
| `aitp_set_compute_target` | any | Set compute target (local / fisher / lean-remote) |

### Output
| Tool | Stage | When |
|------|-------|------|
| `aitp_visualize_eft_tower` | any | ASCII EFT tower diagram |
| `aitp_visualize_derivation_chain` | any | ASCII derivation chain |
| `aitp_visualize_knowledge_graph` | any | ASCII knowledge graph |

## End-to-End Flow

### Phase 0: Bootstrap + Source Discovery (stage = L0, posture = discover)

```
1. aitp_bootstrap_topic(topics_root, topic_slug, title, question, lane)
   → Creates directory structure, state.md, L0 and L1 artifact scaffolds
   → Initial stage is L0

2. aitp_register_source(topics_root, topic_slug, source_id, ...)
   → One call per source. Creates L0/sources/<id>.md
   → Source types: paper, preprint, book, dataset, code, experiment, simulation, lecture_notes, reference

3. Fill L0/source_registry.md:
   - Search Methodology — where you looked, what queries
   - Source Inventory — grouped by type
   - Coverage Assessment — what is covered, what is missing
   - Set source_count (frontmatter) to match registered sources
   - Set search_status (frontmatter) to: initial | focused | comprehensive | exhausted

4. aitp_advance_to_l1(topics_root, topic_slug)
   → Transitions from L0 to L1 (reading and framing)
   → Requires: source_registry.md filled + at least one registered source
```

### Phase 1: Reading and Framing (stage = L1, posture = read → frame)

```
5. aitp_ingest_knowledge(topics_root, topic_slug, source_id, ...)
   → Updates L1 artifacts from source content

6. aitp_get_execution_brief(topics_root, topic_slug)
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

#### L1 Source Completeness Workflow

L1 enforces mechanical source coverage via `source_toc_map.md` and per-section intake notes:

1. **Register sources** in L0 (`aitp_register_source`).
2. **Parse TOC** — for each source, call `aitp_parse_source_toc` with every
   section/subsection discovered, including `toc_confidence` (high/medium/low).
   Prefer machine-parsed TOC from `arxiv-latex-mcp` (`toc_confidence="high"`).
   Spot-check TOC against actual content to validate.
3. **Skim all sections (Phase A)** — rapid first pass. For each section call
   `aitp_write_section_intake` with `summary` (1-3 sentences) and
   `completeness_confidence=""`. Mark as `skimming` via
   `aitp_update_section_status`. This builds a complete content map.
4. **Deep-extract priority sections (Phase B)** — for relevant sections, re-read
   in detail. Call `aitp_write_section_intake` with full fields:
   `key_concepts`, `equations_found`, `physical_claims`, `prerequisites`,
   `cross_references`, and honest `completeness_confidence` (high/medium/low).
   The tool auto-marks `extracted` and links TOC entry -> intake note.
5. **Defer out-of-scope sections** — `aitp_update_section_status` with
   `new_status="deferred"` and explicit reason.
6. **Coverage + quality gate** — L1 cannot advance to L3 until:
   - `coverage_status` is `"complete"` or `"partial_with_deferrals"`
   - Every `extracted` section has an intake note
   - Intake note count >= extracted section count
   - No intake notes remain at `completeness_confidence="low"` without action

This prevents the common failure mode where L1 reading skips sections or
creates shallow extractions, leaving gaps that corrupt downstream L3 derivation.

### Phase 2: L3 Derivation (stage = L3, posture = derive)

```
8. aitp_advance_to_l3(topics_root, topic_slug, l3_mode="research"|"study")
   → Sets stage=L3, l3_subplane=entry subplane for chosen mode
   → research mode: l3_subplane=ideation
   → study mode: l3_subplane=source_decompose

9. Walk subplanes in order (mode-dependent):

   RESEARCH mode: ideation → planning → analysis → result_integration → distillation
   STUDY mode:    source_decompose → step_derive → gap_audit → synthesis

   For each subplane:
   a. Edit the active artifact (e.g., L3/ideation/active_idea.md)
      Fill frontmatter fields AND body headings.
   b. aitp_advance_l3_subplane(topics_root, topic_slug, next_subplane)
      Only valid transitions are allowed (see tables below).
      Back-edges exist for revision.

10. aitp_submit_candidate(topics_root, topic_slug, candidate_id, claim, evidence,
      candidate_type="research_claim"|"atomic_concept"|"derivation_chain"|..., regime_of_validity=...)
    → After final subplane is complete. Creates L3/candidates/<id>.md
```

Allowed L3 transitions (research mode):
```
ideation       → planning
planning       → analysis, ideation
analysis       → result_integration, ideation, planning
result_integration → distillation, analysis
distillation   → result_integration
```

Allowed L3 transitions (study mode):
```
source_decompose → step_derive
step_derive      → gap_audit, source_decompose
gap_audit        → synthesis, step_derive
synthesis        → gap_audit
```

Switching between modes mid-session:
```
aitp_switch_l3_mode(topics_root, topic_slug, new_mode="research"|"study", reason=...)
→ Resets to entry subplane of new mode
→ Current subplane state is preserved (not deleted)
→ Use when research reveals knowledge gaps (→study) or study yields new ideas (→research)
```

### Phase 3: L4 Validation (stage = L4, posture = verify)

```
11. aitp_create_validation_contract(topics_root, topic_slug, candidate_id,
      mandatory_checks=["dimensional_consistency", ...])
    → Defines what must be checked.

12. Write validation scripts (L4/scripts/) and execute on target machine.
    Every data point must have provenance: script path, execution timestamp, method.

13. aitp_submit_l4_review(topics_root, topic_slug, candidate_id,
      outcome, notes, check_results={...}, evidence_scripts=[...],
      evidence_outputs=[...], data_provenance=[...])
    → outcome ∈ {pass, partial_pass, fail, contradiction, stuck, timeout}
    → LANE-SPECIFIC EVIDENCE REQUIREMENTS:
      - toy_numeric/code_method: evidence_scripts + evidence_outputs REQUIRED for pass
        data_provenance REQUIRED: every data point traced to a script execution
      - formal_theory: check_results is primary evidence. Required keys:
        dimensional_consistency, symmetry_compatibility, limiting_case_check,
        correspondence_check. Values describe WHAT was verified and outcome.
        evidence_scripts optional (e.g., SymPy symbolic verification).
```

**L4 pass does NOT auto-advance.** It returns to L3 for post-validation analysis.

**L4 non-pass outcomes** trigger a popup gate with options:
- `fail` → return to L3 for revision
- `contradiction` → may require retreat to L1/L0 or flag L2 conflict
- `stuck`/`timeout` → human decides: retry, switch lane, or archive

### Phase 3b: L4→L3 Return Loop (stage = L3, posture = derive)

```
14. aitp_return_to_l3_from_l4(topics_root, topic_slug, reason="post_l4_analysis")
    → Returns to L3 analysis subplane

15. Analyze L4 findings in L3/analysis/active_analysis.md
    → What passed conclusively? What had caveats? What remains open?
    → Document L4 results in L3/analysis/active_analysis.md

16. Ask the human (MANDATORY):
    - "Persist and advance" → proceed to promotion/L2
    - "Continue iterating" → new L3 cycle (plan → analyze → integrate → distill → L4)
    - "Revise scope" → narrow/adjust the claim
    - "Switch lane" → aitp_switch_lane if analytic dead-end or numeric refinement needed
```

This loop continues until the human confirms the topic is ready to persist.

Physics check fields:
`dimensional_consistency`, `symmetry_compatibility`,
`limiting_case_check`, `conservation_check`, `correspondence_check`

### Phase 4: Promotion to Global L2

```
17. Request → resolve → promote:
    aitp_request_promotion(topics_root, topic_slug, candidate_id)
    aitp_resolve_promotion_gate(topics_root, topic_slug, candidate_id, "approve")
    aitp_promote_candidate(topics_root, topic_slug, candidate_id)
    → Writes to global L2/ (cross-topic reusable knowledge)
    → Assigns 2D trust: (basis=validated, scope=bounded_reusable)
    → Conflict detection and version bumping handled automatically.

    If REJECTED:
    → Candidate status becomes "rejected_from_promotion"
    → Agent MUST call aitp_return_to_l3_from_l4 to return to L3/analysis
    → Address rejection reason, revise candidate, re-distill, re-submit
```

### Phase 5: Lifecycle Management

**Topic forking** — when a side-discovery emerges:
```
aitp_fork_topic(topics_root, parent_slug, child_slug, title, question)
→ Creates new topic with L1 copies from parent
→ Links parent/child in both runtime logs
→ Child inherits parent's lane
```

**Lane switching** — when the research approach needs to change:
```
aitp_switch_lane(topics_root, topic_slug, new_lane, reason)
→ Records old lane, new lane, reason, timestamp
→ Common: formal_theory → toy_numeric (analytical dead end)
→         toy_numeric → code_method (need production computation)
→         code_method → formal_theory (numerical results suggest clean form)
→ NOTE: L4 evidence requirements change with lane
```

**Topic archiving** — when a topic must be paused or abandoned:
```
aitp_archive_topic(topics_root, topic_slug, reason, reason_category)
→ reason_category: abandoned | paused | superseded | merged_into_another
→ All artifacts preserved
→ Stage set to "archived"

aitp_restore_topic(topics_root, topic_slug)
→ Restores archived topic to previous stage
```

**Session resumption** — when continuing after a break:
```
aitp_session_resume(topics_root, topic_slug)
→ Returns current state, recent log entries, execution brief
→ Agent reads the indicated skill and continues from last checkpoint
```

**Global L2 queries** — cross-topic knowledge search:
```
aitp_query_l2(topics_root, query)
→ Searches all promoted claims in global L2
→ Returns claims with trust basis, scope, version, conflicts
→ Use when starting a new topic to avoid duplicating work
```

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
            "L0" → Register sources, fill source_registry.md, advance to L1
            "L1" → Fill remaining L1 artifacts or advance to L3
            "L3" → Check brief.l3_mode:
                     "research" → Work on active subplane artifact (ideation...distillation)
                     "study" → Work on active subplane artifact (source_decompose...synthesis)
                   Then advance subplane or submit candidate
            "L4" → Validate candidate with code/analysis, submit review,
                    then return to L3 via aitp_return_to_l3_from_l4
            "L2" → Request promotion from validated L4 candidate
        continue

    # Lifecycle overrides (can happen at any stage):
    if human requests lane change:
        aitp_switch_lane(topics_root, topic_slug, new_lane, reason)
    if human requests L3 mode switch (research <-> study):
        aitp_switch_l3_mode(topics_root, topic_slug, new_mode, reason)
    if human requests fork:
        aitp_fork_topic(topics_root, topic_slug, child_slug, ...)
    if human requests archive:
        aitp_archive_topic(topics_root, topic_slug, reason, category)
    if human requests retreat to L1 (from L3 only):
        aitp_retreat_to_l1(topics_root, topic_slug, reason)
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
    ├── L0/
    │   ├── source_registry.md       # Source discovery inventory and coverage
    │   └── sources/*.md             # Registered sources (papers, datasets, code, etc.)
    ├── L1/                          # Framing artifacts (5 files)
    ├── L3/
    │   ├── <subplane>/active_*.md   # Subplane artifacts
    │   │   # Research mode: ideation/ planning/ analysis/ result_integration/ distillation/
    │   │   # Study mode: source_decompose/ step_derive/ gap_audit/ synthesis/
    │   ├── candidates/*.md          # Submitted candidates
    ├── L4/
    │   ├── validation_contract.md
    │   ├── scripts/*.py               # Validation scripts (mandatory for numeric lanes)
    │   ├── outputs/                   # Execution logs, plots, data tables
    │   └── reviews/*.md
    └── runtime/
        ├── index.md                 # Topic index
        └── log.md                   # Event log
```

## Tool Integration Architecture

External tools (MCP servers, skills) integrate into AITP via three patterns:

### Pattern A — Catalog-only (load on demand)

Tool is listed in the progressive-disclosure catalog for the current stage.
The agent discovers it from the session-start menu and loads full content
via `Skill` or `ToolSearch` when needed.

**When to use**: Tool is optional reference; missing it doesn't break results.
**Examples**: `arxiv-latex-mcp`, `paper-search-mcp`, `ssh-mcp`, `mcp-server-chart`

### Pattern B — Skill reference (invoke at checkpoint)

Tool is listed in the catalog AND the AITP skill file explicitly tells the
agent to invoke it at a specific checkpoint. The session-start hook prints
a `PATTERN-B` instruction so the agent knows to load it proactively.

**When to use**: Tool has a workflow that should be followed at specific subplane points.
**Examples**: `scientific-brainstorming` at L3/ideation

**How to add a Pattern B tool**:
1. Add entry to `TOOL_CATALOG` with pattern `"B"`
2. Add entry to `PATTERN_B_INSTRUCTIONS` with invoke instruction
3. Add a reference in the AITP skill file (e.g., `skill-l3-ideate.md`)

### Pattern C — Workflow absorbed (embedded in AITP skill)

Tool's workflow is already part of the AITP skill's mandatory steps.
The catalog entry is informational only — the agent already follows the
workflow by reading the AITP skill.

**When to use**: Tool is critical for correctness; missing it would produce wrong results.
**Examples**: `jupyter-mcp-server` in L4 validation, `knowledge-hub` in L1/L2

### Decision matrix

| Question | A | B | C |
|----------|---|---|---|
| Missing this tool breaks results? | No | Might | Yes |
| Tool has independent use outside AITP? | Yes | Yes | No |
| Must be used every time? | No | At specific points | Every time |

### Adding new tools

To add a new tool to AITP:

1. **Install** the MCP server or skill
2. **Classify** using the decision matrix above
3. **Register** in `TOOL_CATALOG` (in `brain/state_model.py`) with the pattern tag
4. If Pattern B: also add to `PATTERN_B_INSTRUCTIONS` and update the AITP skill file
5. If Pattern C: embed the workflow into the AITP skill's mandatory steps
6. **Test** by starting a new session and verifying the catalog prints correctly
