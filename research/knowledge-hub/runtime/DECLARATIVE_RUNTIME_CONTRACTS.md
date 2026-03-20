# Declarative runtime contracts

The runtime now supports multiple contract-first escape hatches so research steering
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
      "summary": "Prepare the larger-size finite-size benchmark comparison.",
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

## 3. Candidate split contract

Path:

- `feedback/topics/<topic_slug>/runs/<run_id>/candidate_split.contract.json`

Purpose:

- split wide or mixed Layer 3 candidates into smaller reusable children,
- park unresolved fragments into the runtime deferred buffer,
- keep parent/child lineage explicit before any promotion action runs.

Minimal shape:

```json
{
  "contract_version": 1,
  "splits": [
    {
      "source_candidate_id": "candidate:wide-parent",
      "reason": "This parent mixes a definition with an unresolved caveat.",
      "child_candidates": [
        {
          "candidate_id": "candidate:narrow-definition",
          "candidate_type": "definition_card",
          "title": "Narrow Definition",
          "summary": "The reusable part extracted from the parent.",
          "origin_refs": [],
          "question": "Can the definition be promoted independently?",
          "assumptions": ["Keep the source-local scope explicit."],
          "proposed_validation_route": "bounded-smoke",
          "intended_l2_targets": ["definition:narrow-definition"]
        }
      ],
      "deferred_fragments": [
        {
          "entry_id": "deferred:wide-parent-caveat",
          "title": "Unresolved Caveat",
          "summary": "Park until a cited follow-up paper is ingested.",
          "reason": "The current source delegates the caveat externally."
        }
      ]
    }
  ]
}
```

Rules:

- the parent candidate must already exist in `candidate_ledger.jsonl`,
- child candidates are appended back into the same run ledger,
- deferred fragments move into `runtime/topics/<topic_slug>/deferred_candidates.json`,
- reactivation is driven by the deferred buffer, not by prose-only notes.

Schema:

- `feedback/schemas/candidate-split-contract.schema.json`

## 4. Deferred runtime buffer

Paths:

- `runtime/topics/<topic_slug>/deferred_candidates.json`
- `runtime/topics/<topic_slug>/deferred_candidates.md`

Purpose:

- hold unresolved but still valuable fragments outside Layer 2,
- let later source intake or spawned follow-up subtopics reactivate them,
- keep reactivation conditions durable and inspectable.

Schema:

- `runtime/schemas/deferred-candidate-buffer.schema.json`

The buffer is populated by the candidate split contract and may be reactivated by:

- new `source_id` arrivals,
- matching source text,
- or declared child-topic completion signals.

## 5. Recommended action types

When authoring `next_actions.contract.json`, prefer explicit `action_type`
values for the new runtime-capable flows:

- `apply_candidate_split_contract`
- `reactivate_deferred_candidate`
- `spawn_followup_subtopics`
- `auto_promote_candidate`

## 6. Progressive-disclosure runtime bundle contract

Path:

- `runtime/topics/<topic_slug>/runtime_protocol.generated.json`

Public schema:

- `runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`

Purpose:

- expose `minimal_execution_brief`, `must_read_now`, and `escalation_triggers`
  as a stable machine-readable contract,
- let external runtimes consume trigger semantics without scraping markdown,
- keep markdown as a human-readable projection instead of the only trigger
  definition surface.

Minimal shape:

```json
{
  "$schema": "https://aitp.local/schemas/progressive-disclosure-runtime-bundle.schema.json",
  "bundle_kind": "progressive_disclosure_runtime_bundle",
  "protocol_version": 1,
  "topic_slug": "my-topic",
  "minimal_execution_brief": {
    "current_stage": "L3",
    "selected_action_id": "action:my-topic:02",
    "queue_source": "declared_contract",
    "open_next": "runtime/topics/my-topic/runtime_protocol.generated.md",
    "immediate_allowed_work": [
      "Continue bounded L3 work after reading the required surfaces."
    ],
    "immediate_blocked_work": [
      "Do not promote material into Layer 2 without the gate artifacts."
    ]
  },
  "escalation_triggers": [
    {
      "trigger": "non_trivial_consultation",
      "active": true,
      "condition": "L2 consultation materially changes route or writeback intent.",
      "required_reads": [
        "L2_CONSULTATION_PROTOCOL.md",
        "consultation/topics/my-topic/consultation_index.jsonl"
      ]
    }
  ],
  "recommended_protocol_slices": [
    {
      "slice": "consultation_memory",
      "trigger": "non_trivial_consultation",
      "paths": [
        "L2_CONSULTATION_PROTOCOL.md",
        "consultation/topics/my-topic/consultation_index.jsonl"
      ]
    }
  ]
}
```

Rules:

- `runtime_protocol.generated.json` is the durable machine-readable source.
- `runtime_protocol.generated.md` may reorder or compress, but it must not
  invent or hide trigger state.
- Stable trigger names such as `promotion_intent`,
  `non_trivial_consultation`, `proof_completion_review`, and
  `verification_route_selection` should be consumed from JSON first.
- External executors should treat the schema as the public contract and the
  service implementation as one producer of that contract, not the contract
  itself.

## Precedence

The runtime should interpret steering in this order:

1. explicit decision contract,
2. explicit control-note directive,
3. unfinished-first heuristic.

For queue materialization:

1. explicit `next_actions.contract.json`,
2. heuristic conversion from `next_actions.md`,
3. runtime-appended system actions when enabled.
