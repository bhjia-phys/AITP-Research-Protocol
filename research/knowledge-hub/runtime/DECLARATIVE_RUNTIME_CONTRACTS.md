# Declarative runtime contracts

The runtime now supports two contract-first escape hatches so research steering
does not have to live only inside Python heuristics.

## 1. L3 action contract

Path:

- `feedback/topics/<topic_slug>/runs/<run_id>/next_actions.contract.json`

Purpose:

- declare the intended research-action queue explicitly,
- let humans or agents pin action types, stages, and handlers,
- reduce the amount of queue synthesis hidden in `orchestrate_topic.py`.

Minimal shape:

```json
{
  "contract_version": 1,
  "policy_note": "Why this declared queue is the right one.",
  "append_runtime_actions": true,
  "append_skill_action_if_needed": true,
  "actions": [
    {
      "action_id": "action:my-topic:01",
      "summary": "Prepare the larger-size OTOC comparison.",
      "action_type": "manual_followup",
      "resume_stage": "L3",
      "auto_runnable": false
    }
  ]
}
```

Rules:

- `actions[*].summary` is required.
- `action_type` may be omitted; runtime will fill it heuristically.
- `append_runtime_actions=true` keeps closed-loop/system actions appended.
- `append_skill_action_if_needed=true` keeps capability-gap actions appended.

Keep the human explanation in:

- `feedback/topics/<topic_slug>/runs/<run_id>/next_actions.contract.md`

## 2. Runtime decision contract

Path:

- `runtime/topics/<topic_slug>/next_action_decision.contract.json`

Purpose:

- select the exact next action explicitly,
- stop or pause the loop without relying on implicit control-note matching,
- let Python act as validator/executor instead of sole decision maker.

Minimal shape:

```json
{
  "contract_version": 1,
  "decision_mode": "human_redirect",
  "selected_action_id": "action:my-topic:02",
  "reason": "This redirected action must run before the old queue head.",
  "requires_human_intervention": true,
  "auto_dispatch_allowed": false,
  "evidence_refs": [
    "feedback/topics/my-topic/runs/2026-03-15-run/next_actions.md"
  ]
}
```

Stop/pause variant:

```json
{
  "contract_version": 1,
  "decision_mode": "pause",
  "reason": "Wait for the operator to revise the observable family."
}
```

Keep the human explanation in:

- `runtime/topics/<topic_slug>/next_action_decision.contract.md`

## Precedence

The runtime should interpret steering in this order:

1. explicit decision contract,
2. explicit control-note directive,
3. unfinished-first heuristic.

For queue materialization:

1. explicit `next_actions.contract.json`,
2. heuristic conversion from `next_actions.md`,
3. runtime-appended system actions when enabled.
