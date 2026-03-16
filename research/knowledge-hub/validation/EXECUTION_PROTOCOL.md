# Layer 4 execution protocol

This file defines how the Layer 4 execution plane consumes a validation note and produces auditable evidence.

## Architectural split

Layer 4 is not only a note surface.

It is split into:
- `L4-control`: the validation note in Obsidian,
- `L4-execution`: reproducible task and result artifacts under `research/knowledge-hub/validation/`.

## Control-plane input

The execution plane should start only after the validation note has defined:
- candidate id,
- candidate type,
- validation question,
- check matrix,
- pass conditions,
- failure signals,
- expected writeback route.

If these are missing, execution is not ready.

## Execution-plane responsibilities

The execution plane is responsible for:
- task records,
- runtime selection,
- output artifact capture,
- result summaries,
- baseline reproduction when method trust is not yet established,
- atomic-understanding support artifacts when a derivation-heavy method is being reused,
- promotion-decision records.

It is not responsible for inventing the validation target after the fact.

## Task record model

Each execution task should be stored as one JSON artifact, typically at:

`topics/<topic_slug>/runs/<run_id>/execution-tasks/<task_id>.json`

Each task should record:
- which validation note it came from,
- which surface it uses,
- what inputs it requires,
- what outputs it promises,
- pass conditions,
- failure signals,
- current status,
- resulting artifact paths.

## Execution surfaces

Supported surfaces include:
- `numerical`
- `symbolic`
- `formal`
- `coding`
- `human_review`

Use the narrowest surface that matches the real task.

Tool-specific execution guides may refine this further.
Current example:
- `CHAOS_DIAGNOSTICS_EXECUTION.md`

## Result loop

1. Read the validation note.
2. Determine whether baseline reproduction or atomic-understanding gates are required.
3. Create one or more execution-task records.
4. Run the required execution work.
5. Write result artifacts and update task status.
6. Return findings to the validation note.
7. Issue one promotion decision artifact.

See:
- `validation/BASELINE_REPRODUCTION_AND_UNDERSTANDING_GATES.md`

## Promotion decision artifact

Every completed validation run should emit a decision artifact that records:
- candidate id,
- route,
- verdict,
- promoted Layer 2 ids if any,
- fallback Layer 3 targets if any,
- evidence references,
- decider identity,
- decision timestamp.

## Constraint

Execution may support the verdict, but execution does not replace the verdict.

The final adjudication still belongs to the Layer 4 validation note and its recorded decision artifact.
