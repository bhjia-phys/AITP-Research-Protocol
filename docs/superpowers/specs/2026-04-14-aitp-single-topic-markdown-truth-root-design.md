# AITP Single-Topic Markdown Truth-Root Design

## Goal

Move AITP from split layer roots toward a single topic-owned truth root:

- `research/knowledge-hub/topics/<topic_slug>/`

Within that root, every major layer and process surface becomes inspectable from one place, and human-facing truth surfaces are recorded as Markdown first.

## Problem

Current AITP topic state is protocol-first but physically fragmented:

- runtime state lives under `runtime/topics/<topic_slug>/`
- source intake lives under `source-layer/topics/<topic_slug>/`
- candidate work lives under `feedback/topics/<topic_slug>/runs/<run_id>/`
- validation work lives under `validation/topics/<topic_slug>/runs/<run_id>/`
- consultation work lives under `consultation/topics/<topic_slug>/`

This preserves layer semantics, but it weakens topic-level continuity for humans. It also blocks a Superpowers-like interaction surface because the topic does not yet expose one authoritative, inspectable folder that owns the research loop.

## Approved Direction

Adopt option `B`: a single topic directory becomes the unique truth root.

Target layout:

```text
research/knowledge-hub/topics/<topic_slug>/
  topic_manifest.md
  L0/
  L1/
  L2/
  L3/
  L4/
  runtime/
  consultation/
  logs/
```

The long-term rule is:

- topic-owned Markdown files are the human truth surfaces
- machine-oriented JSON may exist only as compatibility projections or generated caches
- new writes should target the single topic root rather than the legacy split roots

## Markdown Truth Contract

Markdown truth files are not free-form notes. They are constrained protocol objects.

Each truth file may contain:

1. YAML frontmatter for stable machine fields
2. fixed section headings for durable human reading
3. optional fenced blocks for structured payload excerpts
4. a freeform notes section that is explicitly non-authoritative

Canonical form:

```md
---
topic_slug: demo-topic
artifact_kind: topic_state
updated_at: 2026-04-14T12:00:00+08:00
updated_by: aitp-cli
status: active
---

# Topic State

## Summary

Human-readable current state.

## Structured Fields

```json
{"resume_stage":"L3"}
```

## Notes

Freeform commentary.
```

## Interaction Model

AITP already has structured decision semantics:

- decision points
- operator checkpoints
- route selections

The missing piece is not protocol shape. The missing piece is that adapters currently surface these only as files and JSON responses rather than as clickable host UI actions.

This design therefore separates two concerns:

1. make topic truth local, inspectable, and Markdown-first
2. keep decision/checkpoint payloads structured enough that adapters can later render them as buttons or dialogs

## Scope For This Implementation

This implementation establishes the new architecture and migrates the key shell/runtime path helpers and projections first.

In scope:

- add a single topic truth-root layout helper
- move service-owned topic roots to `topics/<topic_slug>/...`
- materialize a topic manifest and Markdown companion surfaces in the topic root
- keep runtime state under `topics/<topic_slug>/runtime/`
- move L0/L3/L4/consultation helper roots under the topic root
- add Markdown companion projections for key runtime truth surfaces
- update tests for the new path contract

Not yet in scope:

- removing every legacy path consumer in one pass
- deleting all legacy JSON projections
- rendering host-native popup UI inside every adapter

## File Layout Contract

Per-topic layout introduced in this phase:

```text
topics/<topic_slug>/
  topic_manifest.md
  L0/
    topic.md
    source_index.jsonl
  L1/
  L2/
  L3/
    runs/<run_id>/
  L4/
    runs/<run_id>/
  consultation/
  runtime/
    topic_state.json
    topic_state.md
    topic_dashboard.md
    topic_synopsis.json
    topic_synopsis.md
    pending_decisions.json
    pending_decisions.md
```

## Risks

### 1. Path migration blast radius

Many modules directly assume `runtime/topics/<slug>` or other legacy roots. The implementation must centralize new layout helpers and update the highest-leverage call sites first.

### 2. Markdown becoming prose-only

If truth Markdown is allowed to drift into free-form notes, the runtime becomes non-deterministic. Frontmatter plus fixed headings remain mandatory.

### 3. Legacy test fixtures

Many tests currently create fixtures directly under legacy roots. They must be updated or supported via compatibility resolution during migration.

## Testing Strategy

Add targeted regression coverage for:

- topic root path helpers
- runtime root relocation under `topics/<slug>/runtime`
- source/feedback/validation/consultation roots under the topic root
- Markdown companion surfaces for topic state and pending decisions
- current-topic registry reporting the new runtime root path

## Success Criteria

This design is successful when:

- one topic has one authoritative folder
- the folder exposes L0-L4 plus runtime and consultation from one place
- major runtime truth surfaces have Markdown companions
- status reporting points at `topics/<slug>/runtime/...` rather than `runtime/topics/<slug>/...`
- the next adapter phase can read decisions from one topic-owned truth root and map them to popup choice UI
