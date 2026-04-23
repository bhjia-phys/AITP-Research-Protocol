# Physicist-First Notebook Obligation-Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the AITP topic notebook/report stack so it reads like a serious theoretical-physics research notebook rather than a structured protocol archive, while also making missing derivations, convention bridges, source anchors, and failure analyses flow back into durable unfinished work.

**Architecture:** Treat each iteration as a bounded research round with a single `round_type` and an explicit obligation-closure state. Extend the derived runtime report surface so it materializes physicist-facing sections: physical target, regime, convention ledger, round-by-round development, main derivation spine, current best statements, excluded routes, and open obligations. Then refactor the XeLaTeX compiler so main text follows that scientific order, pushes audit-heavy material into appendices, and visually emphasizes equations and logical flow rather than dashboard boxes.

**Tech Stack:** Python runtime helpers in `research/knowledge-hub/knowledge_hub/`, JSON/Markdown runtime artifacts under `topics/<slug>/runtime/` and `topics/<slug>/L3/runs/<run_id>/`, XeLaTeX + `ctex`, `pytest`, sample topic regeneration under `output/pdf/`.

---

## Design invariants

- A round may finish without a final conclusion, but it may not finish without an honest account of what was attempted, what was learned, what is still missing, and what the next bounded step is.
- Missing derivation details are a hard blocker only for rounds that actually claim derivation support; numerical/benchmark rounds must instead carry plan, setup, observables, result interpretation, and next action.
- Convention/normalization reconciliation is not its own round type. It is a cross-round obligation block that becomes mandatory whenever a round depends on notation or normalization bridges.
- `Current Best Statements` may only cite rounds whose required obligations are closed strongly enough for claim use.
- Anything missing that matters for claim use must surface in three places simultaneously: the relevant round, the report summary, and `unfinished_work`.
- Main text should present the physics first. Protocol words such as `run`, `iteration`, `L3-L4`, `returned_result_status`, and `staging_decision` must move to secondary metadata.

## File map

### Protocol and design docs

- Create: `docs/protocols/TOPIC_NOTEBOOK_OBLIGATION_PROTOCOL.md`
- Modify: `docs/AITP_SPEC.md`
- Modify: `docs/PROJECT_INDEX.md`
- Modify: `docs/protocols/L3_execution_protocol.md`
- Modify: `research/knowledge-hub/RESEARCH_EXECUTION_GUARDRAILS.md`
- Modify: `research/knowledge-hub/runtime/DECLARATIVE_RUNTIME_CONTRACTS.md`
- Modify: `research/knowledge-hub/runtime/README.md`

### Runtime report and round materialization

- Modify: `research/knowledge-hub/knowledge_hub/research_report_support.py`
- Modify: `research/knowledge-hub/knowledge_hub/aitp_service.py`
- Modify: `research/knowledge-hub/knowledge_hub/topic_shell_support.py`
- Modify: `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`
- Modify: `research/knowledge-hub/knowledge_hub/iteration_journal_support.py`
- Modify: `research/knowledge-hub/knowledge_hub/l3_derivation_support.py`
- Modify: `research/knowledge-hub/knowledge_hub/l3_comparison_support.py`

### Notebook compiler and sample materialization

- Modify: `research/knowledge-hub/knowledge_hub/research_notebook_support.py`
- Modify: `research/knowledge-hub/runtime/scripts/run_jones_chapter4_finite_product_formal_closure_acceptance.py`

### Tests

- Modify: `research/knowledge-hub/tests/test_research_report_support.py`
- Modify: `research/knowledge-hub/tests/test_research_notebook_support.py`
- Modify: `research/knowledge-hub/tests/test_runtime_scripts.py`
- Modify: `research/knowledge-hub/tests/test_physicist_reporting_skills.py`

---

## Task 1: Define notebook obligation closure as a first-class protocol surface

**Files:**
- Create: `docs/protocols/TOPIC_NOTEBOOK_OBLIGATION_PROTOCOL.md`
- Modify: `docs/AITP_SPEC.md`
- Modify: `docs/protocols/L3_execution_protocol.md`
- Modify: `research/knowledge-hub/runtime/DECLARATIVE_RUNTIME_CONTRACTS.md`
- Modify: `research/knowledge-hub/runtime/README.md`
- Modify: `research/knowledge-hub/RESEARCH_EXECUTION_GUARDRAILS.md`
- Modify: `docs/PROJECT_INDEX.md`

- [ ] **Step 1: Define the four round types and their minimum obligations**

Document these round types:

- `derivation_round`
- `source_restoration_round`
- `numerical_or_benchmark_round`
- `synthesis_round`

For each type, state:

- required blocks
- hard-blocking gaps
- qualified gaps
- claim-eligibility effect
- unfinished-work backflow rule

- [ ] **Step 2: Define cross-round obligation blocks**

Write protocol language for these blocks:

- `convention_ledger`
- `source_anchor_table`
- `failure_route_note`
- `open_obligation_list`
- `next_plan`

State explicitly that these blocks are triggered by round content and are not independent round types.

- [ ] **Step 3: Define the claim-readiness ladder**

Document the three readiness states:

- `blocked`
- `qualified`
- `stable`

Specify which readiness states may appear in:

- `Current Best Statements`
- `Active But Not Yet Claim-Worthy Routes`
- appendix-only archival material

- [ ] **Step 4: Define the physicist-facing main-text ordering rule**

Add one canonical ordering rule:

1. research problem and physical target
2. setup, regime, and convention ledger
3. round-by-round research development
4. main derivation spine
5. current best statements
6. excluded routes and lessons
7. open obligations and next direction
8. appendices for provenance, catalogs, and chronology

- [ ] **Step 5: Verify protocol coverage**

Run:

```powershell
rg -n "round_type|convention_ledger|Current Best Statements|obligation" docs research/knowledge-hub/runtime
```

Expected:

- the new protocol doc and updated runtime docs all reference the obligation-closure model

---

## Task 2: Extend the report surface from a summary artifact into a physicist-facing research state

**Files:**
- Modify: `research/knowledge-hub/knowledge_hub/research_report_support.py`
- Modify: `research/knowledge-hub/knowledge_hub/aitp_service.py`
- Modify: `research/knowledge-hub/knowledge_hub/topic_shell_support.py`
- Modify: `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`
- Test: `research/knowledge-hub/tests/test_research_report_support.py`

- [ ] **Step 1: Add report sections that match the physicist reading order**

Extend `research_report.active.json` to materialize or derive:

- `physical_target`
- `observables_or_decision_targets`
- `core_equations_or_targets`
- `current_dispute_or_bottleneck`
- `convention_ledger`
- `round_development`
- `main_derivation_spine`
- `current_best_statements`
- `active_routes_not_yet_claim_worthy`
- `excluded_routes`
- `open_obligations`

- [ ] **Step 2: Add per-round obligation closure fields**

Every round row in the report should carry:

- `round_type`
- `required_blocks`
- `present_blocks`
- `missing_blocks`
- `hard_blocking_gaps`
- `qualified_gaps`
- `claim_readiness`
- `eligible_for_current_claims`
- `must_feed_unfinished_work`

- [ ] **Step 3: Derive cross-round blocks from current artifacts**

Teach the report builder to derive:

- `convention_ledger` from research-question notation locks, L1 notation tensions, round-level bridge notes, and report-facing route data
- `source_anchor_table` from derivation/source-restoration records
- `failure_route_note` from failed derivation attempts and rejected comparison outcomes
- `open_obligation_list` from missing blocks and unresolved caveats

- [ ] **Step 4: Replace current-claims card logic with statement logic**

Refactor current claim derivation so the report stores statement-grade entries:

- `statement`
- `validity_regime`
- `depends_on`
- `breaks_if`
- `still_unclosed`
- `claim_readiness`

Do not materialize a statement into `current_best_statements` if any supporting round has a hard-blocking gap.

- [ ] **Step 5: Backflow missing obligations into unfinished work**

When a report round has missing blocks, write or update unfinished-work items that include:

- source round id
- linked candidate/derivation id when available
- missing block type
- whether it blocks claim use
- recommended next round type

- [ ] **Step 6: Write failing tests for report obligations**

Add tests that cover:

- derivation round without stepwise derivation -> `claim_readiness == blocked`
- numerical round without observable definition -> `claim_readiness == blocked`
- convention-sensitive route without convention ledger -> missing block recorded and unfinished work updated
- qualified route appears in `active_routes_not_yet_claim_worthy`, not `current_best_statements`

- [ ] **Step 7: Run report tests**

Run:

```powershell
python -m pytest research/knowledge-hub/tests/test_research_report_support.py -q
```

Expected:

- all new obligation-closure tests fail first, then pass after implementation

---

## Task 3: Strengthen round source data so the report can materialize real derivation and restoration structure

**Files:**
- Modify: `research/knowledge-hub/knowledge_hub/l3_derivation_support.py`
- Modify: `research/knowledge-hub/knowledge_hub/l3_comparison_support.py`
- Modify: `research/knowledge-hub/knowledge_hub/iteration_journal_support.py`
- Modify: `research/knowledge-hub/knowledge_hub/aitp_service.py`
- Test: `research/knowledge-hub/tests/test_runtime_scripts.py`

- [ ] **Step 1: Extend derivation records with stepwise support**

Support optional structured derivation fields such as:

- `derivation_steps`
- `step_dependencies`
- `step_kind`
- `source_anchor`
- `is_l3_completion`
- `assumption_dependencies`
- `justification_note`
- `open_gap_note`

Fallback behavior should still work for legacy body-only derivation records, but the new compiler/report should prefer structured steps when present.

- [ ] **Step 2: Add source-restoration specific fields**

Allow restoration rows or derivation records to store:

- `source_statement`
- `source_omissions`
- `l3_restoration_notes`
- `restoration_assumptions`

- [ ] **Step 3: Add round-level convention bridge hooks**

Allow iteration plan/synthesis or report-facing rows to persist:

- `notation_bindings`
- `normalization_bridge_status`
- `bridge_open_questions`

- [ ] **Step 4: Add failure-route specific fields**

Support durable failure-route material such as:

- `why_plausible`
- `exact_failure_point`
- `lesson`
- `revive_conditions`

- [ ] **Step 5: Update acceptance-path sample generation**

Modify the real acceptance/sample script so it emits at least:

- one structured derivation round
- one convention ledger
- one failed route note
- one qualified current statement
- one blocked route that stays out of current statements

- [ ] **Step 6: Run targeted acceptance tests**

Run:

```powershell
python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -q -k "jones or research_report or notebook"
```

Expected:

- updated sample/acceptance flows still pass with richer round payloads

---

## Task 4: Rebuild the notebook compiler around a physicist-first main text

**Files:**
- Modify: `research/knowledge-hub/knowledge_hub/research_notebook_support.py`
- Test: `research/knowledge-hub/tests/test_research_notebook_support.py`

- [ ] **Step 1: Replace protocol-heavy section naming with physics-first titles**

Main-text sections should become:

- `Research Problem, Physical Target, And Motivation`
- `Setup, Regime, And Convention Ledger`
- `Round-by-Round Research Development`
- `Main Derivation Spine`
- `Current Best Statements`
- `Excluded Routes And Lessons`
- `Open Obligations And Next Research Direction`

Protocol labels such as run id and iteration id should move to metadata lines or marginal context, not headline positions.

- [ ] **Step 2: Render the convention ledger as a first-class front-matter table**

Build one explicit notation/convention table with columns or fields for:

- symbol
- meaning
- normalization / units
- source
- bridge status
- notes

- [ ] **Step 3: Render round development in physicist order**

Within each round, render in this order:

- question
- route/plan
- main derivation action or benchmark action
- result
- unresolved obligations
- next plan

Do not lead with protocol tags.

- [ ] **Step 4: Render main derivation spine as prose + equations, not summary boxes**

When structured derivation steps exist, render them as a stepwise mathematical narrative:

- step label
- equation or transformation
- justification
- source-vs-L3 note
- assumption dependency note
- open gap marker when needed

Use boxes only for assumptions, warnings, and caveats.

- [ ] **Step 5: Split main-text and appendix responsibilities**

Ensure:

- main text contains only one learnable derivation spine and the most instructive excluded routes
- appendices contain full source provenance, candidate catalog, strategy memory, and chronological log
- repeated derivation bodies do not appear in both main text and appendices at equal prominence

- [ ] **Step 6: Add notebook tests for the new reading order**

Write failing tests that assert:

- convention ledger is front-loaded before round development
- `Current Best Statements` replaces claim-card language
- a blocked route does not appear in current statements
- failed route summaries appear in the main text when marked pedagogically relevant
- chronology remains in appendix only

- [ ] **Step 7: Run notebook tests**

Run:

```powershell
python -m pytest research/knowledge-hub/tests/test_research_notebook_support.py -q
```

Expected:

- tests fail against the old protocol-heavy structure, then pass after refactor

---

## Task 5: Make the LaTeX style read like a research manuscript instead of a dashboard

**Files:**
- Modify: `research/knowledge-hub/knowledge_hub/research_notebook_support.py`
- Test via notebook PDF generation under `output/pdf/`

- [ ] **Step 1: Reduce box density in the main text**

Keep `tcolorbox` for:

- assumptions
- warnings/caveats
- proposition-style statements
- failure-route summaries
- metadata strips

Render derivation prose and equations directly in the text body where possible.

- [ ] **Step 2: Introduce manuscript-style semantic environments**

Define lightweight environments or macros for:

- `Physical Target`
- `Working Proposition`
- `Caveat`
- `Failure Note`
- `Source Restoration Note`

These should read like theorem/remark structures, not dashboard cards.

- [ ] **Step 3: Demote protocol metadata visually**

Render run ids, iteration ids, statuses, and staging details as small metadata lines beneath headers rather than as title-bearing labels.

- [ ] **Step 4: Improve equation readability**

When a derivation contains multiple steps:

- allow `align`-style or enumerated step layouts
- keep math blocks visually separated from warning/caveat boxes
- preserve Chinese support and XeLaTeX compatibility

- [ ] **Step 5: Verify PDF aesthetics manually**

Regenerate the sample notebook and inspect:

- title and front matter
- convention ledger page
- one round page
- one derivation-spine page
- one excluded-route page

Expected:

- the notebook reads like a physics manuscript with archival appendices, not like a monitoring dashboard

---

## Task 6: Preserve failed routes as scientific exclusions, not just event history

**Files:**
- Modify: `research/knowledge-hub/knowledge_hub/research_report_support.py`
- Modify: `research/knowledge-hub/knowledge_hub/research_notebook_support.py`
- Modify: `research/knowledge-hub/tests/test_research_report_support.py`
- Modify: `research/knowledge-hub/tests/test_research_notebook_support.py`

- [ ] **Step 1: Add excluded-route report rows**

Materialize a dedicated report section for excluded routes with:

- route
- why plausible
- exact failure point
- lesson
- revive conditions
- archival reference

- [ ] **Step 2: Select which failures belong in the main text**

Add a rule:

- pedagogically important failures appear in `Excluded Routes And Lessons`
- operational noise remains appendix-only

- [ ] **Step 3: Add tests for failure-route pedagogy**

Write tests that assert:

- a failed direct-identification route appears in excluded-route main text
- its lesson and failure point are rendered
- full raw event history stays in chronology

- [ ] **Step 4: Run focused tests**

Run:

```powershell
python -m pytest research/knowledge-hub/tests/test_research_report_support.py research/knowledge-hub/tests/test_research_notebook_support.py -q
```

Expected:

- excluded routes are visible as scientific lessons rather than only archived attempts

---

## Task 7: Regenerate the public sample and verify end-to-end behavior

**Files:**
- Modify: `research/knowledge-hub/runtime/scripts/run_jones_chapter4_finite_product_formal_closure_acceptance.py`
- Output: `output/pdf/aitp-topic-archive-sample-v4/knowledge-hub/topics/chern-response-demo-topic/L3/research_notebook.pdf`

- [ ] **Step 1: Update the sample scenario**

Ensure the sample includes:

- one convention ledger with an unresolved bridge
- one structured source-restoration round
- one structured derivation round
- one numerical or benchmark round if available
- one qualified current best statement
- one blocked route
- one excluded route with lesson

- [ ] **Step 2: Rebuild the sample report and notebook**

Run the relevant acceptance/sample materialization flow, then compile the notebook twice with XeLaTeX to avoid stale TOC/PDF artifacts.

- [ ] **Step 3: Render preview pages**

Generate PNG previews for:

- table of contents
- convention ledger page
- round-development page
- derivation-spine page
- excluded-route page

- [ ] **Step 4: Verify the sample against the design goals**

Check manually that:

- protocol words no longer dominate the main narrative
- derivation steps are inspectable rather than summary-only
- notation/convention issues are front-loaded
- current statements read like bounded physical propositions
- repeated archival content has moved out of the main spine

---

## Task 8: Full verification pass

**Files:**
- No additional files; verification only

- [ ] **Step 1: Run the report and notebook test suite**

Run:

```powershell
python -m pytest research/knowledge-hub/tests/test_research_report_support.py research/knowledge-hub/tests/test_research_notebook_support.py -q
```

Expected:

- all report/notebook tests pass

- [ ] **Step 2: Run the broader regression suite**

Run:

```powershell
python -m pytest research/knowledge-hub/tests/test_physicist_reporting_skills.py research/knowledge-hub/tests/test_runtime_scripts.py -q
```

Expected:

- broader reporting/runtime regressions pass

- [ ] **Step 3: Compile the sample notebook manually**

Run a clean two-pass XeLaTeX compile in the sample L3 directory.

Expected:

- `research_notebook.pdf` is regenerated from the new TeX without stale TOC residue

- [ ] **Step 4: Capture final evidence**

Record:

- passing test commands
- sample PDF path
- preview image paths
- any residual risks, especially if some legacy round producers still emit only summary-style derivation data

---

## Execution ordering recommendation

Implement in this order:

1. Task 1
2. Task 2
3. Task 3
4. Task 4
5. Task 6
6. Task 5
7. Task 7
8. Task 8

Reason:

- protocol and report semantics must exist before the notebook compiler can render them cleanly
- failure-route and claim-readiness logic should be stable before final visual tuning
- visual tuning should happen against near-final content, not draft-only sections

---

## Main risks

- Legacy derivation records may not yet contain stepwise data, so the compiler must support graceful fallback while still surfacing missing obligations honestly.
- If unfinished-work backflow is too aggressive, the topic may accumulate noisy obligations; the implementation should deduplicate by round id and missing-block type.
- If the notebook compiler keeps too many boxes in the derivation spine, the report will still feel dashboard-like even after semantic refactor.
- If sample PDF regeneration is done without a clean rebuild, stale TOC/PDF state can make it look as if old section names survived the refactor.

---

## Completion criteria

This plan is complete when:

- obligation-closure semantics exist in protocol docs and derived runtime surfaces
- claim readiness is computed from round obligations rather than only from candidate/comparison presence
- missing obligations feed `unfinished_work`
- main text follows a physicist-readable order
- convention ledger is first-class and front-loaded
- derivation rendering is stepwise when data exists and honest about gaps when it does not
- excluded routes read like scientific lessons
- sample PDF visually reads like a research manuscript with archival appendices
