# Deferred Runtime Contracts

The deferred buffer is the durable parking surface for valuable material that is
not ready for Layer 2 yet.

It is not a garbage bin and it is not a second Layer 2.

## Paths

- `topics/<topic_slug>/runtime/deferred_candidates.json`
- `topics/<topic_slug>/runtime/deferred_candidates.md`
- optional lineage from `topics/<topic_slug>/runtime/followup_subtopics.jsonl`

## Purpose

- keep unresolved fragments visible,
- record why they were parked,
- define when they may reactivate automatically,
- prevent wide or mixed candidates from being forced into Layer 2.

## Entry states

- `buffered`
- `reactivated`
- `dismissed`

## Typical reactivation conditions

- `source_ids_any`
- `text_contains_any`
- `child_topics_any`

## Rule

If a deferred entry becomes reactivatable and it provides a
`reactivation_candidate`, the runtime may materialize a fresh Layer 3 candidate
without requiring a new ad hoc note.
