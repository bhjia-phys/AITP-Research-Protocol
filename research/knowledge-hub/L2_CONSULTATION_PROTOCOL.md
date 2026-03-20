# L2 consultation protocol

This file defines `L2 consultation` as a first-class protocol surface.

It is not a new layer.
It is the explicit mechanism by which `L1`, `L3`, and `L4` query and apply `L2` as active memory during their own work.

## 1. Why this exists

Without an explicit consultation protocol, `L2` risks degrading into passive storage:
- knowledge is written back,
- but later stages do not consult it in a stable, auditable way.

This protocol exists to make three things explicit:
- what a stage asked `L2`,
- what `L2` returned,
- what the stage actually applied.

## 2. Scope and policy

Use this protocol for non-trivial, artifact-shaping `L2` consultation during:
- `L1` provisional understanding,
- `L3` candidate formation,
- `L4` adjudication.

For policy purposes:
- if the consultation materially changes terminology, candidate shape, validation route, contradiction handling, warning attachment, or writeback intent, emitting this protocol is mandatory,
- if the lookup is purely ephemeral and leaves no durable artifact or decision changed, it may stay local and unrecorded.

Do not use it for:
- final promotion into `L2`,
- raw source registration,
- ad hoc chat-only memory references with no durable artifact.

## 2.1 Runtime trigger handshake

The runtime progressive-disclosure bundle names this path explicitly as:

- `non_trivial_consultation`

When that trigger is active in `runtime_protocol.generated.json` or
`runtime_protocol.generated.md`, the next agent must open:

- `L2_CONSULTATION_PROTOCOL.md`,
- `consultation/topics/<topic_slug>/consultation_index.jsonl`,
- the relevant consultation `request.json`, `result.json`, and `application.json`
  artifacts.

This runtime trigger expands consultation semantics only.
It does not grant promotion or writeback authority.
If the consultation outcome later supports canonical writeback, that is a
second trigger path: `promotion_intent`, plus its own promotion-gate artifacts.

## 3. Core lifecycle

One complete consultation should produce three protocol artifacts:

1. `consult_request`
   - what the stage needs from `L2`
   - why it is asking
   - which artifact context triggered the request

2. `consult_result`
   - what `L2` returned
   - which retrieval profile was used
   - which refs were considered relevant enough to surface

3. `consult_application`
   - which returned refs were actually applied
   - what effect the consultation had on the work
   - which stage-local projections were updated

This keeps retrieval separate from application.
The system should not pretend that every retrieved ref was actually used.

## 4. Source-of-truth layout

The protocol surface lives under:

`research/knowledge-hub/consultation/`

Current layout:

```text
consultation/
  README.md
  schemas/
    consult-request.schema.json
    consult-result.schema.json
    consult-application.schema.json
    consultation-index-entry.schema.json
  topics/<topic_slug>/
    consultation_index.jsonl
    calls/<consultation_slug>/
      request.json
      result.json
      application.json
```

## 5. Stage-local projections

The existing stage-local files remain valid:
- `intake/topics/<topic_slug>/l2_consultation_log.jsonl`
- `feedback/topics/<topic_slug>/runs/<run_id>/l2_consultation_log.jsonl`
- `validation/topics/<topic_slug>/runs/<run_id>/l2_consultation_log.jsonl`

But they should now be read as:
- local projection logs,
- compact per-stage summaries,
- not the primary source-of-truth for consultation semantics.

The new protocol surface is the authoritative record.

## 6. Minimal rules

### Rule 0. Non-trivial consultation must be durable and explicit

If a consultation materially shapes a durable `L1`, `L3`, or `L4` artifact, it must produce protocol artifacts under `consultation/`.
Only ephemeral no-effect lookups may skip this.

### Rule 1. Every non-trivial consultation needs a `context_ref`

The request must say what local artifact triggered the need for memory lookup.

### Rule 2. Retrieval and application stay separate

`consult_result` records what was returned.
`consult_application` records what was actually used.

### Rule 3. Consultation is not promotion

Looking up `L2` does not itself justify writing new objects into `L2`.
The runtime trigger `non_trivial_consultation` is therefore distinct from
`promotion_intent`, and both may be active in the same topic without collapsing
into one decision surface.

### Rule 4. Empty or weak results are allowed

A consultation may legitimately return:
- no strong refs,
- only warning refs,
- or only partial support.

That outcome is still useful and should remain visible.

### Rule 5. Stage-local logs are projections, not replacements

The local `l2_consultation_log.jsonl` files can stay small.
If detail is needed, the protocol surface should hold it.

## 7. Stage expectations

### `L1`

Consult `L2` to:
- normalize terminology,
- compare extracted claims,
- catch known scope traps,
- reuse existing workflows.

### `L3`

Consult `L2` to:
- reuse methods,
- reuse derivation routes,
- reuse workflows,
- surface bridges and warnings before candidate formation hardens.

### `L4`

Consult `L2` to:
- choose validation patterns,
- compare against prior accepted claims,
- surface contradiction risks,
- keep regime and scope checks explicit.

## 8. Current example

The first complete consultation chain now exists under:

`consultation/topics/holographic-entanglement-saddles/`

It records:
- one `L1` consultation,
- one `L3` consultation,
- one `L4` consultation,

all tied to the existing RT example route.
