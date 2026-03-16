# Layer 3 — Research Feedback / Exploratory Log

This layer stores active research output that is still uncertain or too local to canonicalize.

Use it for:
- conjectures,
- derivation fragments,
- failed attempts,
- anomalies,
- negative results,
- run-specific observations,
- open technical questions,
- pre-validation reasoning.

Layer 3 should actively consult Layer 2 while forming candidates:
- retrieve methods before inventing new procedures unnecessarily,
- retrieve derivation objects before rebuilding known argument routes,
- retrieve bridges and workflows to structure the research path,
- retrieve warning notes before committing to risky interpretations.

When that consultation materially shapes a durable Layer 3 artifact, record it through the first-class consultation protocol under `consultation/` and treat `l2_consultation_log.jsonl` as a local projection.

Key structured handoff object:
- `candidate`
- schema: `feedback/schemas/candidate.schema.json`
- notes: `feedback/CANDIDATE.md`

Runs live under:

`research/knowledge-hub/feedback/topics/<topic_slug>/runs/<run_id>/`

Material here can later move into Layer 4 for explicit checking, and only then be promoted into the canonical layer if it becomes reusable and stable.
