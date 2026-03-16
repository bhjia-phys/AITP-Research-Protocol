# Layer 4 — Validation / Adjudication Log

This layer stores explicit checks that decide whether Layer 3 candidate material is ready to enter the canonical layer.

Layer 4 has two cooperating surfaces:
- an Obsidian control plane for human-readable adjudication notes,
- an execution plane for reproducible validation artifacts and task records.

Use it for:
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

Control plane:

`/home/bhj/projects/repos/Theoretical-Physics/obsidian-markdown/11 L4 Validation/`

Runs live under:

`research/knowledge-hub/validation/topics/<topic_slug>/runs/<run_id>/`

Recommended run-local layout:
- `validation_plan.md`
- `promotion_decisions.jsonl`
- `execution-tasks/<task_id>.json`
- `results/`

Numerical and symbolic execution helpers may live under:

`research/knowledge-hub/validation/tools/`

The first domain-specific pilot now includes a small-system exact-diagonalization toolkit for:
- OTOC,
- Krylov complexity,
- gap-ratio sanity checks,

documented in:
- `CHAOS_DIAGNOSTICS_EXECUTION.md`
- `tools/README.md`

This layer is the main gate between Layer 3 exploratory material and Layer 2 canonical knowledge.
Direct `L1 -> L4 -> L2` is not allowed: Layer 4 must come after Layer 3.

See also:
- `EXECUTION_PROTOCOL.md`
- `schemas/execution-task.schema.json`
- `schemas/promotion-decision.schema.json`
