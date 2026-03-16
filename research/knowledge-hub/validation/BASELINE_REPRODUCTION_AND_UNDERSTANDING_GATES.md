# Baseline reproduction and understanding gates

This file defines two hard gates that must be satisfied before AITP treats a
new result as trustworthy enough for serious scientific interpretation or Layer
2 writeback.

## Core rule

No novel scientific conclusion should outrun method trust.

Before using a method or backend to support a new claim, AITP must first show
that the method itself is understood well enough.

This gate has two branches.

## Gate A: numerical baseline reproduction

Use this gate when the relevant evidence depends on a numerical backend,
simulation pipeline, or external code path.

Required rule:

- reproduce at least one public baseline before treating new-topic numerical
  output as scientifically persuasive.

Acceptable baseline types:

1. a published example from the literature,
2. a public reference implementation or repository,
3. a known analytic limit that the code should reproduce exactly,
4. a simpler public toy model that exercises the same diagnostic pipeline.

Required artifacts:

- `baseline_plan.md`
- `baseline_results.jsonl`
- `baseline_summary.md`

Minimum recorded fields:

- what was reproduced,
- why it is an appropriate baseline,
- which code or workflow was used,
- what agreement criterion was applied,
- whether the baseline passed, failed, or remained inconclusive.

If no acceptable public baseline exists, AITP must record that explicitly
before proceeding and explain which weaker substitute was used.

## Gate B: theoretical atomic-understanding gate

Use this gate when the result depends on a non-trivial derivation, formal
technique, or conceptual method that AITP claims to understand and reuse.

Required rule:

- decompose the method into atomic concepts and dependency links before
  declaring the method understood.

Required artifacts:

- `atomic_concept_map.json`
- `derivation_dependency_graph.json`
- `understanding_summary.md`

Minimum recorded contents:

- the atomic concepts involved,
- the assumptions and regime for each concept,
- the dependency order between concepts or derivation steps,
- the unresolved links or missing justifications,
- the final judgment: understood, partially understood, or not yet understood.

If the dependency graph is not stable enough to write, the method is still
Layer 3 material.

## Promotion implication

These gates apply before:

- trusting a new numerical signal as physics,
- promoting a numerical method into `L2`,
- promoting a derivation-heavy method or claim into `L2`,
- treating a theory technique as already mastered.

## Current practical reading

- new-topic numerical novelty requires a reproduced baseline first,
- new-topic theoretical reuse requires atomic decomposition first,
- otherwise the honest status is still exploratory or deferred.
