# AITP agent conformance protocol

This file defines the strongest practical answer to the question:

How do we keep an AI agent operating inside AITP rather than drifting into an
ad hoc workflow?

The answer is not blind trust.
The answer is a required entrypoint plus an auditable artifact contract.

## Hard truth

AITP cannot force an arbitrary external model to think in a particular way.

What it can do is:

1. force work to begin from the AITP entrypoint,
2. force durable artifacts to exist in the right places,
3. fail conformance when those artifacts are missing or inconsistent,
4. make non-compliance visible to both humans and later agents.

This is the correct operational notion of conformance.

## Required entry rule

A valid AITP run should start from:

```bash
python3 research/adapters/openclaw/scripts/aitp_loop.py ...
```

or the equivalent installed `aitp loop ...` surface when available.

The loop entrypoint must materialize the runtime surfaces before deeper work begins, even though it delegates internally to `research/knowledge-hub/runtime/scripts/orchestrate_topic.py`.

## Required runtime artifacts

Every active topic must expose:

- `runtime/topics/<topic_slug>/topic_state.json`
- `runtime/topics/<topic_slug>/resume.md`
- `runtime/topics/<topic_slug>/action_queue.jsonl`
- `runtime/topics/<topic_slug>/unfinished_work.json`
- `runtime/topics/<topic_slug>/unfinished_work.md`
- `runtime/topics/<topic_slug>/next_action_decision.json`
- `runtime/topics/<topic_slug>/next_action_decision.md`
- `runtime/topics/<topic_slug>/action_queue_contract.generated.json`
- `runtime/topics/<topic_slug>/action_queue_contract.generated.md`
- `runtime/topics/<topic_slug>/agent_brief.md`
- `runtime/topics/<topic_slug>/interaction_state.json`
- `runtime/topics/<topic_slug>/operator_console.md`
- `runtime/topics/<topic_slug>/conformance_state.json`
- `runtime/topics/<topic_slug>/conformance_report.md`

If these are missing, the run is not considered AITP-conformant.

## Entry gate

At session entry, the conformance audit should verify:

1. the runtime state exists,
2. the operator-visible surfaces exist,
3. the layer pointers are present,
4. the unfinished-work and next-action decision surfaces are present,
5. the generated queue-contract snapshot is present,
6. the delivery contract is explicit,
7. the capability-adaptation protocol is declared.

## Exit gate

At session exit, the conformance audit should be refreshed again.

The goal is to verify that the session still leaves:

1. a resumable topic state,
2. a visible unfinished-work index,
3. an explicit next-action decision,
4. exact file pointers for the next operator,
5. a truthful operator-facing summary.

## Audit command

Use:

```bash
python3 research/knowledge-hub/runtime/scripts/audit_topic_conformance.py \
  --topic-slug <topic_slug> \
  --phase entry
```

or:

```bash
python3 research/knowledge-hub/runtime/scripts/audit_topic_conformance.py \
  --topic-slug <topic_slug> \
  --phase exit
```

## Interpretation

A passed conformance audit means:

- the agent operated through the AITP artifact contract,
- the run is inspectable and resumable,
- later agents do not need to reconstruct state from chat.

It does not mean:

- the science is correct,
- the reasoning is complete,
- the validation is finished.

Scientific correctness still depends on `L3/L4`.

## Relationship to Layer 4

Conformance is not validation.

Conformance answers:
- did the agent use the AITP operating model correctly?

Layer 4 answers:
- did the scientific candidate survive explicit checks?
