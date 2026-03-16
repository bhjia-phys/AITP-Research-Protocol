# Candidate

`candidate` is the formal Layer 3 object used for `L3 -> L4` handoff.

Its purpose is to turn exploratory work into an explicit adjudication target.

## Required fields

Every candidate should provide:
- `candidate_id`
- `candidate_type`
- `title`
- `summary`
- `topic_slug`
- `run_id`
- `origin_refs`
- `question`
- `assumptions`
- `proposed_validation_route`
- `intended_l2_targets`
- `status`

## Semantic rules

### 1. Explicit adjudication target

The candidate must name what kind of Layer 2 object is expected if the candidate succeeds.

### 2. Origin trace

The candidate must link back to:
- source-bound intake material,
- the relevant research run,
- and any already-used canonical units.

### 3. Validation is proposed, not assumed

The candidate may suggest the validation route, but it is not yet a decision artifact.

### 4. Candidate is smaller than a run summary

Do not use the entire research log as the candidate.
The candidate should be the smallest adjudicable unit or unit bundle.

## Typical candidate types

- `concept`
- `claim_card`
- `derivation_object`
- `method`
- `workflow`
- `bridge`
- `validation_pattern`
- `warning_note`

## Storage

Recommended storage:
- `feedback/topics/<topic_slug>/runs/<run_id>/candidate_ledger.jsonl`

Machine-readable schema:
- `feedback/schemas/candidate.schema.json`
