---
name: aitp-action-classifier
description: Classify the action type for a topic loop step using semantic reasoning instead of keyword matching. Load when the action queue is being materialized.
---

# AITP Action Classifier

## Environment gate

- This skill runs inside an AITP session after research mode has been classified and recorded.
- Load this skill when `aitp_run_topic_loop` or `aitp_resume_topic` is about to materialize the next action.

## Classification task

Determine which action type best describes the current step from these categories:

| Action type | When to choose |
|-------------|---------------|
| `baseline_reproduction` | Reproducing a known result from a reference to establish a computational baseline. |
| `atomic_understanding` | Deep reading or analysis of a single concept, paper section, theorem, or method to build understanding. |
| `conformance_audit` | Checking whether existing artifacts (derivations, code, data) conform to their stated specifications. |
| `derivation_step` | Advancing a formal derivation by one step: applying a theorem, expanding, simplifying, or closing a proof obligation. |
| `numerical_experiment` | Running a computation or simulation to produce numerical evidence. |
| `literature_intake` | Reading, parsing, and ingesting source material (papers, textbooks, notes) into the topic workspace. |
| `validation_round` | Running a verification or validation pass against target claims or benchmarks. |
| `scope_refinement` | Narrowing or adjusting the research question, assumptions, or target claims. |
| `promotion_attempt` | Preparing and submitting a candidate for promotion to L2 canonical knowledge. |
| `gap_analysis` | Identifying missing pieces, unproven lemmas, insufficient data, or other gaps blocking closure. |
| `synthesis` | Combining results from multiple threads or layers into a coherent summary or report. |
| `debugging` | Diagnosing why a prior step failed or produced unexpected results. |
| `trust_audit` | Auditing the trust level, provenance, or coverage of a claim or candidate. |
| `report_writing` | Producing narrative output: topic report, derivation narrative, or human-facing summary. |
| `consultation` | Asking a question or seeking guidance from the human operator or an external resource. |
| `reactivate_deferred` | Picking up a previously deferred action that is now unblocked. |

## Reasoning priority

1. **Explicit queue state**: If the topic state or operator console names the next action explicitly, use that.
2. **Human request semantics**: What did the user just ask for? Match the intent to the action type.
3. **Protocol state signals**: Look at the current phase, pending obligations, and validation status. A topic in the validation phase likely needs `validation_round` or `gap_analysis`.
4. **Default**: If uncertain, choose `atomic_understanding` (safe default that builds knowledge without side effects).

## Special mechanical actions

These do not need semantic reasoning and should be handled by the infrastructure directly:
- **Split contract**: When the contract has multiple independent target claims, split into subtopics.
- **Reactivate deferred**: When a deferred action is now unblocked, reactivate it.

For these, pass through the infrastructure classification without invoking this skill.

## Recording the classification

After reasoning, call the MCP tool:

```
aitp_record_classification(
    topic_slug=<current topic>,
    classification_type="action_type",
    value=<action type string>,
    rationale=<1-2 sentence explanation>,
    signals_used=<list of signals>,
    source="ai_reasoning"
)
```

## Hard rules

- Do not use keyword matching. Reason from context and intent.
- Record every classification. The action type must be durable before the loop step executes.
- A single loop iteration may reclassify if the context shifts mid-step.
