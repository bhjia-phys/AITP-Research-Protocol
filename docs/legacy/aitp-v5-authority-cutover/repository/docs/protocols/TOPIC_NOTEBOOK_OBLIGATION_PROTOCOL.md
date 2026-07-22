# Topic Notebook Obligation Protocol

Domain: Point (L3) + runtime-derived reporting surface
Authority: subordinate to AITP SPEC S3 and the L3 execution protocol
Status: active

---

## 1. Purpose

AITP's topic notebook should read like a serious theoretical-physics research
notebook rather than a protocol dashboard or a flattened event archive.

This protocol defines:

- how each bounded research round declares its scientific role,
- which obligation blocks must be present before a round can support a current
  statement,
- how missing obligations flow back into unfinished work,
- how the derived report and XeLaTeX notebook order material for human
  learning and audit.

The core rule is:

> A round may end without a final conclusion, but it may not end without an
> honest statement of what was attempted, what was learned, what is still
> missing, and what the next bounded step is.

---

## 2. Round types

Each notebook-facing round must declare exactly one `round_type`.

Allowed round types:

- `derivation_round`
- `source_restoration_round`
- `numerical_or_benchmark_round`
- `synthesis_round`

The `round_type` does not erase cross-round obligations such as notation
bridges or source anchoring. It only declares the main scientific job of that
round.

### 2.1 `derivation_round`

Purpose:

- advance a derivation,
- close a proof or identity chain,
- expose what remains unclosed in an analytical route.

Minimum required blocks:

- `round_question`
- `derivation_spine`
- `assumptions_and_regime`
- `open_obligation_list`
- `next_plan`

Hard-blocking gaps:

- no stepwise derivation spine,
- dependence on literature without source anchors,
- dependence on notation/normalization translation without a convention ledger,
- summary prose that skips the logical chain required for claim use.

### 2.2 `source_restoration_round`

Purpose:

- recover a source-local derivation, definition, or bridge from literature in a
  way that later rounds can audit and learn from.

Minimum required blocks:

- `round_question`
- `target_source_location`
- `source_anchor_table`
- `source_omissions`
- `l3_restoration`
- `open_obligation_list`
- `next_plan`

Hard-blocking gaps:

- claiming a restoration without page / section / equation anchors,
- failing to distinguish what the source explicitly states from what L3
  reconstructed,
- failing to describe which intermediate steps remain unrecovered.

### 2.3 `numerical_or_benchmark_round`

Purpose:

- run or review a bounded numerical, execution-backed, or benchmark-facing
  test.

Minimum required blocks:

- `round_question`
- `test_plan`
- `setup_and_regime`
- `observable_definition`
- `pass_conditions`
- `result_summary`
- `anomaly_or_failure_analysis`
- `next_plan`

Hard-blocking gaps:

- reported result without setup or observable definition,
- reported success/failure without declared pass conditions,
- anomaly or mismatch without analysis and bounded next action.

This round type does **not** require a derivation spine unless the round
explicitly claims derivation support.

### 2.4 `synthesis_round`

Purpose:

- consolidate what a phase has taught the topic,
- identify which routes are strong enough to quote,
- mark which routes remain exploratory or blocked.

Minimum required blocks:

- `phase_question`
- `what_was_learned`
- `current_best_statement_candidates`
- `excluded_routes_summary`
- `open_obligation_list`
- `next_plan`

Hard-blocking gaps:

- summary-only prose that does not name the supporting rounds,
- promoting a statement while hiding excluded routes or unresolved obligations,
- collapsing still-open routes into current results.

---

## 3. Cross-round obligation blocks

These are not independent round types. They become mandatory when the content
of a round requires them.

### 3.1 `convention_ledger`

Use when:

- notation changes across sources,
- normalization/units affect comparison,
- a benchmark or observable depends on symbol translation.

Expected fields:

- symbol,
- meaning,
- normalization / units,
- source basis,
- bridge status,
- notes on remaining ambiguity.

### 3.2 `source_anchor_table`

Use when:

- a derivation or restoration depends on cited literature,
- a round claims that a step comes from a paper, note, lecture, or theorem
  packet.

Expected fields:

- local step reference,
- source file or citation,
- page / section / equation anchor,
- formula-level anchor when the restoration depends on a specific displayed
  formula,
- what the source says,
- whether L3 completed omitted steps,
- whether the step remains fully auditable or still has missing fields.

### 3.3 `failure_route_note`

Use when:

- a route was plausible enough to teach future sessions something,
- a direct identification, shortcut, or reduction failed,
- a benchmark route was rejected for a concrete scientific reason.

Expected fields:

- route,
- why it looked plausible,
- exact failure point,
- lesson,
- revive conditions if any.

### 3.4 `open_obligation_list`

Use for every round.

Expected fields:

- missing block,
- why it matters,
- whether it blocks claim use,
- recommended next round type.

### 3.5 `next_plan`

Use for every round.

Expected fields:

- next bounded objective,
- why this is the most justified next step,
- the main artifacts or signals the next step depends on.

---

## 4. Claim readiness

Notebook/report-facing statements must declare one of:

- `blocked`
- `qualified`
- `stable`

### 4.1 `blocked`

Use when any supporting round has a hard-blocking gap.

Consequences:

- may not appear in `Current Best Statements`,
- must appear in `Active But Not Yet Claim-Worthy Routes` or appendix,
- missing obligations must flow into `unfinished_work`.

### 4.2 `qualified`

Use when the supporting route is materially informative but still carries
explicit caveats such as unresolved factors, normalization bridges, or source
gaps.

Consequences:

- may appear in `Current Best Statements` only as a bounded working statement,
- must include:
  - `validity_regime`
  - `depends_on`
  - `breaks_if`
  - `still_unclosed`

### 4.3 `stable`

Use when the statement's supporting rounds have no hard-blocking gaps and no
unexplained contradiction that would make the current wording scientifically
misleading.

Consequences:

- may appear in `Current Best Statements`,
- may be summarized in conclusion-facing notebook sections.

---

## 5. Unfinished-work backflow

Any missing notebook obligation that matters for claim use must flow into the
topic's unfinished-work surface.

Each unfinished-work row should preserve:

- source round id,
- linked candidate / derivation id when relevant,
- missing block type,
- whether it blocks claim use,
- recommended next round type,
- concise repair instruction.

This turns "we still need to do something" into a durable scientific repair
task rather than a conversational reminder.

---

## 6. Main-text ordering rule

The notebook main text should present physics before protocol machinery.

Preferred order:

1. `Research Problem, Physical Target, And Motivation`
2. `Setup, Regime, And Convention Ledger`
3. `Round-by-Round Research Development`
4. `Main Derivation Spine`
5. `Current Best Statements`
6. `Excluded Routes And Lessons`
7. `Open Obligations And Next Research Direction`

Appendices should hold:

- full source provenance,
- full candidate catalog,
- full strategy/failure memory,
- complete chronological event log,
- low-priority archival detail.

Protocol metadata such as run ids, iteration ids, L3/L4 staging status, and
execution-control receipts should be visible but visually demoted relative to
the physical narrative.

---

## 7. Rendering rule for derivation-heavy topics

When structured derivation steps exist, the notebook should prefer direct text
and equation flow over card-heavy rendering.

Each derivation step should make clear:

- what mathematical transformation occurred,
- why it is justified,
- whether the step is source-given or L3-completed,
- which assumptions it depends on,
- which formula-level anchor supports it when the route is source-based,
- whether the step still has missing audit fields,
- which gaps remain open.

Warnings, assumptions, caveats, and failure notes may use framed environments;
the main derivation itself should remain easy to read as a mathematical
argument.

For long topics, the notebook may keep:

- a main narrative spine that preserves the opening and most recent rounds,
- supplementary appendix sections for intermediate round archives,
- supplementary derivation files and excluded-route archives grouped by route
  or derivation kind.

---

## 8. Relationship to other protocols

This protocol supplements, and does not replace:

- `docs/protocols/L3_execution_protocol.md`
- `research/knowledge-hub/runtime/DECLARATIVE_RUNTIME_CONTRACTS.md`
- `research/knowledge-hub/RESEARCH_EXECUTION_GUARDRAILS.md`
- `research/knowledge-hub/runtime/README.md`

If there is a conflict, the stronger truthfulness rule wins:

- missing scientific obligations may not be hidden by polished prose,
- a route that is still blocked may not be rendered as a stable statement,
- auditability must remain visible even when the notebook becomes more
  human-readable.
