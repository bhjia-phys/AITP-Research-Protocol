# Research Question Contract

## Purpose

Define the active research question in a way that prevents silent scope drift.

## Minimum fields

- `question_id`
- `title`
- `topic_slug`
- `status`
- `question`
- `scope`
- `assumptions`
- `non_goals`
- `target_layers`

## High-rigor fields for non-trivial topics

For theory-heavy, proof-heavy, or execution-heavy topics, the active research
question should also declare:

- `context_intake`
- `formalism_and_notation`
- `observables`
- `target_claims`
- `deliverables`
- `acceptance_tests`
- `forbidden_proxies`
- `uncertainty_markers`

## Why it matters

If the question is not explicit, the agent can silently mutate the task.
If observables, deliverables, and forbidden proxies are missing, the agent can
also confuse polished progress with real scientific progress.
