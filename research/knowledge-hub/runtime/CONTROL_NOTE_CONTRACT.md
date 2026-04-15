# Control note contract

The `control_note` is the durable human steering surface for an active AITP
topic.

Chat may suggest a redirect, pause, or new priority.
The runtime should not act on that redirect until it is persisted into a
control note or another durable topic artifact.

## Accepted forms

The runtime currently accepts:

- Markdown notes with optional frontmatter
- JSON notes with the same fields

If a note has no explicit directive metadata, it is treated as advisory rather
than as an override.

## Recommended frontmatter

```md
---
directive: human_redirect
allow_override_unfinished: true
target_action_id: action:my-topic:02
target_action_summary: Prepare the new validation route
target_artifacts:
  - topics/my-topic/L3/runs/2026-03-15-run/next_actions.md
stop_conditions:
  - Wait until the operator confirms the observable family
summary: Redirect the topic toward the new validation route.
---
```

## Meaning of fields

- `directive`
  - `human_redirect` or `follow_control_note` means the note may override the
    default unfinished-first order.
  - `pause`, `stop`, or `no_action` means the loop should not continue
    automatically.
- `allow_override_unfinished`
  - must be `true` for a redirect to override the default unfinished-first
    policy.
- `target_action_id`
  - exact pending action to select when present.
- `target_action_summary`
  - fallback text matcher when the action id is not known yet.
- `target_artifacts`
  - artifact refs used to anchor the redirect to durable evidence.
- `stop_conditions`
  - explicit conditions that keep the loop paused.
- `summary`
  - short human-readable reason for the redirect.

If the control note changes scope, observables, deliverables, or acceptance
conditions, it should also point to the updated research-question or validation
contract rather than trying to mutate those rules implicitly.

## Practical rule

If a redirect is important enough to change the loop, it should be specific
enough to survive a new session:

- name the target action when possible,
- point to the artifacts that justify the redirect,
- say whether unfinished work is allowed to be superseded,
- update the relevant research-question or validation contract when the note
  changes what "success" means,
- record stop conditions when the loop should pause.
