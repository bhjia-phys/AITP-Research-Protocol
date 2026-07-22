# Multi-Topic Runtime

Status: active

This document explains the v1.3 multi-topic runtime model.

## 1. Why this exists

AITP originally treated `runtime/current_topic.json` as the main durable topic
memory.

That was enough for one active topic at a time, but it breaks down once one
workspace needs to hold multiple real topics in parallel.

The v1.3 model fixes that by separating:

- the authoritative active-topic registry,
- the focused-topic compatibility projection,
- the scheduler that chooses a topic when the operator does not name one,
- and the operator surfaces used to inspect or change that state.

## 2. The runtime model

### Authoritative registry

The source of truth is now:

- `research/knowledge-hub/runtime/active_topics.json`

This is the authoritative registry for multi-topic runtime state.

Each topic row may carry:

- `topic_slug`
- `status`
- `operator_status`
- `priority`
- `last_activity`
- `runtime_root`
- `lane`
- `resume_stage`
- `run_id`
- `projection_status`
- `blocked_by`
- `blocked_by_details`
- `focus_state`

### Focused-topic compatibility projection

The following file still exists:

- `research/knowledge-hub/runtime/current_topic.json`

But it is no longer the authoritative multi-topic state.

It is now the focused-topic compatibility projection so older current-topic
flows keep working.

## 3. Topic selection

### Explicit operator choice wins

If the operator names a topic explicitly, that topic wins.

Examples:

- `aitp loop --topic-slug alpha-topic`
- `aitp focus-topic --topic-slug alpha-topic`
- natural-language requests that clearly name a known topic

### Scheduler fallback

If no explicit topic is supplied, `aitp loop` may select a topic through the
registry-backed scheduler.

The scheduler is:

- deterministic
- explainable
- single-focus only

It is not a concurrent executor.

Current ordering considers:

1. priority
2. focused-topic bonus
3. last-activity recency
4. stable slug fallback

### Hard skips

The scheduler skips topics that are:

- paused
- dependency-blocked
- missing durable runtime state

## 4. Topic-management surfaces

### Natural-language management

Session-start routing can recognize management requests such as:

- `现在有哪些课题？`
- `暂停 alpha-topic`
- `恢复 alpha-topic`
- `切换到 alpha-topic`

These requests return topic-management payloads directly instead of opening a
research loop by mistake.

### Explicit CLI

The runtime also exposes explicit operator controls:

```bash
aitp topics
aitp focus-topic --topic-slug <topic_slug>
aitp pause-topic --topic-slug <topic_slug>
aitp resume-topic --topic-slug <topic_slug>
aitp block-topic --topic-slug <topic_slug> --blocked-by <other_topic_slug> --reason "<reason>"
aitp unblock-topic --topic-slug <topic_slug> --blocked-by <other_topic_slug>
aitp clear-topic-dependencies --topic-slug <topic_slug>
```

Natural-language-first entry remains the default UX.
These explicit commands exist so topic control stays inspectable and recoverable.

## 5. Dependencies

Dependencies live in the active-topic registry.

The compatibility field is:

- `blocked_by`

The richer field is:

- `blocked_by_details`

Each dependency detail row should carry at least:

- `topic_slug`
- `reason`

This lets AITP keep simple scheduler logic while still giving the operator a
human-readable reason for the blockage.

## 6. Visibility

Dependency and focus state should be visible through:

- `aitp topics`
- `aitp current-topic`
- `aitp status --topic-slug <topic_slug>`
- `topics/<topic_slug>/runtime/topic_dashboard.md`

The operator should not need to infer dependency blockage only from the fact
that a topic was skipped.

## 7. What v1.3 does not do

The v1.3 multi-topic runtime does **not**:

- run multiple topics concurrently in the background
- auto-generate platform `SKILL.md` files from mature topics
- auto-load topic-family projections into adapters
- replace the `L0 -> L1 -> L3 -> L4 -> L2` research model

Those are later concerns.

The purpose of v1.3 is narrower:

- durable multi-topic state
- deterministic topic selection
- inspectable management surfaces

## 8. Relationship to `topic_skill_projection`

`topic_skill_projection` remains a reusable route capsule for a mature topic.

It is related to the multi-topic runtime because future topic-family routing may
consult those projections.

But v1.3 does not yet turn projections into adapter auto-load or generated
platform skills.

The order stays:

1. make multi-topic runtime state durable
2. make scheduling and management explicit
3. only then consider projection-aware routing or skill generation

## 8.1 Projection-aware routing seed

The first projection-aware routing seed is intentionally narrow.

AITP may now consult mature `topic_skill_projection` metadata from the active
topic registry when:

- the request does not explicitly name a topic
- durable current-topic focus is absent or ambiguous
- a mature projection clearly matches the requested route shape

But projection hints do **not** outrank:

- an explicit topic slug or explicit topic title
- an explicit current-topic request
- durable current-topic memory
- the focused topic in the active registry

This means projection-aware routing is guidance, not silent reassignment.

The runtime should also explain when projection metadata was:

- used to select a topic
- used only to reinforce the current topic choice
- ignored because current-topic or explicit-topic signals outranked it

## 8.2 Protocol-native topic-family reuse

AITP now also materializes a workspace-level reuse surface:

- `research/knowledge-hub/runtime/topic_family_reuse.json`
- `research/knowledge-hub/runtime/topic_family_reuse.md`

This surface groups mature reusable route capsules by family or lane.

It is meant to answer:

- what reusable route families currently exist
- which mature topics currently provide those route capsules
- what family-level rules or anti-proxy constraints still apply

This is still not adapter-specific skill generation.
It is a protocol-native reuse catalog that stays subordinate to:

- explicit topic choice
- current-topic focus
- current trust gates
- human-reviewed promotion boundaries
