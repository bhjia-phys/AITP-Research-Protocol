# Migrate Runtime Surfaces

This note explains the Phase 17 runtime-surface cleanup.

The goal is not to delete every older file immediately.
The goal is to make the promoted runtime read path smaller and clearer while
keeping risky compatibility files available until downstream adapters and habits
fully converge.

## New default mental model

Read runtime surfaces in this order:

1. `runtime_protocol.generated.md`
2. `topic_dashboard.md`
3. `validation_review_bundle.active.md` when review work is active
4. the supporting slices named under `Must read now` or a declared trigger

Treat these as the primary answers:

- `topic_synopsis.json`
- `topic_dashboard.md`
- `validation_review_bundle.active.json`
- `validation_review_bundle.active.md`
- `active_topics.json`
- `active_topics.md`

## Demoted surfaces

These files still exist, but they are no longer meant to behave like equal
first-stop operator surfaces.

| Surface | New role | Why it was demoted |
|---------|----------|--------------------|
| `runtime/current_topic.json` | compatibility projection | `active_topics.json` is the authoritative multi-topic registry |
| `runtime/current_topic.md` | compatibility projection | same reason as above |
| `runtime/topics/<topic_slug>/operator_console.md` | compatibility operator view | `topic_dashboard.md` is now the primary human runtime render |
| `runtime/topics/<topic_slug>/agent_brief.md` | compatibility execution brief | `runtime_protocol.generated.md` plus primary surfaces already carry the bounded startup contract |
| `runtime/topics/<topic_slug>/promotion_readiness.md` | supporting slice | it explains one review dimension, but `validation_review_bundle.active.md` is the primary `L4` entry surface |
| `runtime/topics/<topic_slug>/gap_map.md` | supporting slice | same reason; it is a deeper blocker slice, not the main topic summary |
| `runtime/topics/<topic_slug>/session_start.generated.md` | routing/audit artifact | it records bootstrap routing, but it is not the main runtime work surface |

## What still stays stable

This cleanup does not change the protocol semantics.

It does not change:

- `L0 -> L1 -> L3 -> L4 -> L2`
- promotion gates
- topic lifecycle rules
- runtime bundle schema contract
- the existence of compatibility files where removing them would be risky

## What adapter and operator code should prefer now

Prefer:

- `topic_dashboard.md` over `operator_console.md`
- `topic_synopsis.json` over ad hoc topic-summary duplication
- `validation_review_bundle.active.md` over opening `promotion_readiness.md` or `gap_map.md` first
- `active_topics.json` over `current_topic.json` when workspace-wide truth is needed

Only fall back to the demoted surfaces when:

- an older adapter still points there
- a debugging or audit flow explicitly wants the legacy view
- a declared runtime trigger says the deeper compatibility surface is relevant
