# Layer 4 — Planning / Execution / Validation / Adjudication Log

This layer stores explicit `L4` artifacts that decide whether Layer 3 candidate
material is ready to enter the canonical layer.
That includes bounded planning, executable handoff tasks, returned results,
validation records, and promotion / reject / defer decisions.

The standalone public kernel treats this repository-local validation surface as
the source-of-truth. Teams may optionally mirror human-readable adjudication
notes elsewhere, but that external note surface is supplemental rather than
normative.

The public layer role is broader than the directory name alone:

- the directory stays `validation/` for continuity,
- but the `L4` contract is the general plan / execute / validate / adjudicate surface.

Use it for:
- bounded execution plans,
- execution handoff contracts,
- validation plans,
- cross-checks against existing workflows and concepts,
- contradiction checks,
- reproduction attempts,
- numerical or formal test records,
- promotion / reject / defer decisions.

Layer 4 should actively consult Layer 2 while adjudicating:
- retrieve validation patterns to choose the right checks,
- retrieve claim cards for contradiction comparison,
- retrieve warning notes for known failure modes,
- retrieve concept and derivation objects to test scope and regime consistency.

When that consultation materially shapes a durable validation artifact or promotion decision, record it through the first-class consultation protocol under `consultation/` and treat `l2_consultation_log.jsonl` as a local projection.

Runs live under:

`research/knowledge-hub/validation/topics/<topic_slug>/runs/<run_id>/`

Recommended run-local layout:
- `validation_plan.md`
- `promotion_decisions.jsonl`
- `execution-tasks/<task_id>.json`
- `results/`

Numerical and symbolic execution helpers may live under:

`research/knowledge-hub/validation/tools/`

This public repository deliberately does not ship a personal topic-specific
numerical pilot as part of the default kernel.
Teams should add their own auditable `L4` executors, templates, and baseline
gates when they need domain-specific numerics or formal tooling.

This layer is the main gate between Layer 3 exploratory material and Layer 2 canonical knowledge.
Direct `L1 -> L4 -> L2` is not allowed: Layer 4 must come after Layer 3.

See also:
- `EXECUTION_PROTOCOL.md`
- `schemas/execution-task.schema.json`
- `schemas/promotion-decision.schema.json`
