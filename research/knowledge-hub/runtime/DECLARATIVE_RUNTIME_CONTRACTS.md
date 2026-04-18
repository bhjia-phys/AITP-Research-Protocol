# Declarative runtime contracts

The runtime now supports multiple contract-first escape hatches so research steering
does not have to live only inside Python heuristics.

## 1. L3 action contract

Path:

- `topics/<topic_slug>/L3/runs/<run_id>/next_actions.contract.json`

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
- `append_runtime_actions=true` keeps runtime-appended system actions appended,
  including closed-loop, split-apply, follow-up reintegration, topic-completion,
  Lean-bridge, deferred-reactivation, and auto-promotion helper actions.
- `append_skill_action_if_needed=true` keeps capability-gap actions appended.

Keep the human explanation in:

- `topics/<topic_slug>/L3/runs/<run_id>/next_actions.contract.md`

## 1.1 L3-L4 iteration journal contract

Paths:

- `topics/<topic_slug>/L3/runs/<run_id>/iteration_journal.md`
- `topics/<topic_slug>/L3/runs/<run_id>/iteration_journal.json`
- `topics/<topic_slug>/L3/runs/<run_id>/iterations/<iteration_id>/plan.md`
- `topics/<topic_slug>/L3/runs/<run_id>/iterations/<iteration_id>/plan.contract.json`
- `topics/<topic_slug>/L3/runs/<run_id>/iterations/<iteration_id>/l4_return.md`
- `topics/<topic_slug>/L3/runs/<run_id>/iterations/<iteration_id>/l4_return.json`
- `topics/<topic_slug>/L3/runs/<run_id>/iterations/<iteration_id>/l3_synthesis.md`
- `topics/<topic_slug>/L3/runs/<run_id>/iterations/<iteration_id>/l3_synthesis.json`

Purpose:

- let one research `run` hold multiple `L3 -> L4 -> L3` cycles,
- give humans one Markdown-first audit trail for the whole run,
- keep machine-readable state thin enough for replay, routing, and adapter use.

Journal rules:

- `iteration_journal.md` is the primary human-facing run journal,
- `iteration_journal.json` stores only run status, current iteration pointer,
  iteration ids, and stable artifact refs,
- each iteration folder should separate:
  - `plan` for the detailed L3 intent,
  - `l4_return` for the returned execution and review summary,
  - `l3_synthesis` for the post-return interpretation and staging decision.

Preferred Markdown contents:

- `plan.md`
  - research objective,
  - detailed plan,
  - exact server / runtime / script / parameter notes when relevant,
  - pass conditions, failure signals, and bounded stop rules.
- `l4_return.md`
  - what `L4` actually returned,
  - links to `execution_task`, `validation_review_bundle`, and
    `returned_execution_result`,
  - the human-readable result summary.
- `l3_synthesis.md`
  - whether the result is accepted,
  - whether to continue another iteration,
  - whether to stage provisional outputs,
  - why that decision is honest.

Thin JSON rule:

- `plan.contract.json`, `l4_return.json`, and `l3_synthesis.json` should carry
  only machine-stable ids, statuses, artifact refs, replay inputs, and staging
  decisions.
- They should not duplicate the full narrative already present in Markdown.

Minimal `iteration_journal.json` shape:

```json
{
  "contract_version": 1,
  "run_id": "2026-04-16-demo",
  "topic_slug": "my-topic",
  "status": "iterating",
  "current_iteration_id": "iteration-002",
  "iteration_ids": ["iteration-001", "iteration-002"],
  "latest_staging_decision": "defer",
  "latest_paths": {
    "journal_note_path": "topics/my-topic/L3/runs/2026-04-16-demo/iteration_journal.md",
    "current_plan_path": "topics/my-topic/L3/runs/2026-04-16-demo/iterations/iteration-002/plan.contract.json",
    "current_return_path": "topics/my-topic/L3/runs/2026-04-16-demo/iterations/iteration-002/l4_return.json",
    "current_synthesis_path": "topics/my-topic/L3/runs/2026-04-16-demo/iterations/iteration-002/l3_synthesis.json"
  }
}
```

This journal layer supplements, and does not replace:

- `next_actions.contract.json`,
- `runtime/execution_task.json`,
- `runtime/validation_review_bundle.active.json`,
- `L4/runs/<run_id>/returned_execution_result.json`,
- canonical staging entries.

## 1.2 L3 derivation record contract

Paths:

- `topics/<topic_slug>/L3/runs/<run_id>/derivation_records.jsonl`
- `topics/<topic_slug>/L3/runs/<run_id>/derivation_records.md`

Purpose:

- keep the topic's detailed derivation body in one layer,
- allow source-derived reconstruction and original candidate derivation to share
  the same run-local home,
- preserve failed derivation routes instead of hiding them in chat or ad hoc
  scratch notes.

Rules:

- L1 may provide source anchors, notation tensions, and contradiction cues, but
  the detailed derivation body belongs in `L3`.
- Every derivation row should say whether it is a `source_reconstruction`,
  `cross_source_reconstruction`, `candidate_derivation`, `failed_attempt`, or
  `notation_resolution`.
- Source-derived derivations must carry explicit `source_refs`.
- The Markdown note is the primary human-readable derivation surface for the
  run; JSONL remains the thin machine-facing ledger.
- Every derivation row should carry an explicit epistemic marker showing that
  the record is AI-authored provisional reasoning rather than truth by itself.

## 1.3 L3-to-L2 comparison receipt contract

Paths:

- `topics/<topic_slug>/L3/runs/<run_id>/l2_comparison_receipts.jsonl`
- `topics/<topic_slug>/L3/runs/<run_id>/l2_comparison_receipts.md`

Purpose:

- force derivation-heavy candidates to compare themselves explicitly against
  nearby reusable L2 knowledge,
- preserve what was compared, how far the agreement goes, and what still
  blocks promotion,
- keep "compare against L2" as a durable artifact rather than an implicit chat
  claim.

Rules:

- A derivation-heavy candidate is not promotion-ready until at least one
  comparison receipt names that candidate.
- Each comparison receipt should include:
  - `candidate_ref_id`,
  - `compared_unit_ids`,
  - `comparison_summary`,
  - `comparison_scope`,
  - `outcome`,
  - `limitations`.
- The Markdown note is the primary human-readable comparison surface for the
  run; JSONL remains the thin machine-facing ledger.
- If the comparison outcome exposes a missing cited step, an unresolved
  contradiction, or an insufficient source basis, the honest route is to
  narrow the candidate or return to `L0` instead of pretending the derivation
  is already stable.

## 1.4 Theory-packet readiness gate for formal candidates

For theorem/proof/formal candidates, detailed derivation and L2 comparison are
still not enough by themselves.

Before such a candidate is promotion-ready, the corresponding theory packet
should expose at least:

- `derivation_graph.json` — the proof or derivation spine as a durable graph,
- `formal_theory_review.json` — with `overall_status: "ready"`.

These surfaces are part of the readiness contract, not optional later polish.

## 2. Runtime decision contract

Path:

- `topics/<topic_slug>/runtime/next_action_decision.contract.json`

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
    "topics/my-topic/L3/runs/2026-03-15-run/next_actions.md"
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

- `topics/<topic_slug>/runtime/next_action_decision.contract.md`

## 3. Candidate split contract

Path:

- `topics/<topic_slug>/L3/runs/<run_id>/candidate_split.contract.json`

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
- deferred fragments move into `topics/<topic_slug>/runtime/deferred_candidates.json`,
- reactivation is driven by the deferred buffer, not by prose-only notes.

Schema:

- `feedback/schemas/candidate-split-contract.schema.json`

## 4. Deferred runtime buffer

Paths:

- `topics/<topic_slug>/runtime/deferred_candidates.json`
- `topics/<topic_slug>/runtime/deferred_candidates.md`

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

- `topics/<topic_slug>/runtime/runtime_protocol.generated.json`

Public schema:

- `runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`

Purpose:

- expose `minimal_execution_brief`, `must_read_now`, and `escalation_triggers`
  as a stable machine-readable contract,
- expose explicit `runtime_mode`, `mode_envelope`, and `transition_posture`
  instead of leaving mode/transition policy implicit inside handler code,
- let queue ordering and next-action selection increasingly consume the same
  explicit contract instead of staying purely heuristic,
- let queue materialization suppress obviously mismatched runtime-appended
  actions when the explicit contract already says the topic is in a different
  routing posture,
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
  "runtime_mode": "explore",
  "active_submode": null,
  "mode_envelope": {
    "mode": "explore",
    "load_profile": "light"
  },
  "transition_posture": {
    "transition_kind": "boundary_hold"
  },
  "minimal_execution_brief": {
    "current_stage": "L3",
    "selected_action_id": "action:my-topic:02",
    "queue_source": "declared_contract",
    "open_next": "topics/my-topic/runtime/runtime_protocol.generated.md",
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
        "topics/my-topic/consultation/consultation_index.jsonl"
      ]
    }
  ],
  "recommended_protocol_slices": [
    {
      "slice": "consultation_memory",
      "trigger": "non_trivial_consultation",
      "paths": [
        "L2_CONSULTATION_PROTOCOL.md",
        "topics/my-topic/consultation/consultation_index.jsonl"
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
