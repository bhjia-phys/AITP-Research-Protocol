# Strategy Memory Template (Run-Local JSONL)

Use this template to create:

- `feedback/topics/<topic_slug>/runs/<run_id>/strategy_memory.jsonl`

Purpose:

- capture reusable route patterns from both success and failure,
- improve future action selection without over-promoting uncertain claims.

## JSONL row format

One row per strategy event:

```json
{
  "timestamp": "2026-03-26T12:00:00Z",
  "topic_slug": "example-topic",
  "run_id": "2026-03-26-run-01",
  "lane": "formal_derivation",
  "strategy_id": "strat-check-sign-before-merge",
  "strategy_type": "verification_guardrail",
  "summary": "Checking sign conventions before combining equations prevented false agreement.",
  "input_context": {
    "observable_family": "two-point-function",
    "method_surface": "derivation"
  },
  "outcome": "helpful",
  "confidence": 0.78,
  "evidence_refs": [
    "validation/topics/example-topic/runs/2026-03-26-run-01/validation_summary.md"
  ],
  "reuse_conditions": [
    "multi-source derivation merge",
    "mixed notation sources"
  ],
  "do_not_apply_when": [
    "single-source closed derivation with fixed conventions"
  ],
  "human_note": "Keep this as a default pre-merge check."
}
```

## Field guidance

- `strategy_type`:
  - `search_route`
  - `verification_guardrail`
  - `debug_pattern`
  - `resource_plan`
  - `scope_control`
  - `proof_engineering`
  - `api_workaround`
  - `failure_pattern`
- `outcome`:
  - `helpful`
  - `neutral`
  - `harmful`
  - `inconclusive`
- `confidence`:
  - bounded estimate in `[0, 1]` based on observed evidence quality.

## Use rules

- Do not treat strategy memory as scientific truth.
- Do not promote strategy rows directly to `L2` claim objects without `L4`
  adjudication.
- Keep failure patterns. Negative strategy memory is often high-value.

