# AITP v5 Record Lifecycle: rehome / supersede / audit-routing

AITP v5 typed records are append-only history. **Records are never hard-deleted.** When a
record was written to the wrong topic, superseded by a newer record, or entered in error,
use the lifecycle operations instead of trying to delete it.

## Why not delete?

Records are referenced by other records (evidence binds to claims via `claim_id`; chains
of `replaces`/`replaced_by` link related records). Hard-deleting a record would leave
dangling references and destroy audit history. The lifecycle system marks records inactive
and filters them out of the active conclusion while preserving full provenance.

## What gets written

Every lifecycle change produces exactly one append-only `lifecycle_event` record under
`registry/lifecycle_events/<event_id>.md`. The subject record itself is **not** moved or
deleted; it gains four optional frontmatter fields:

| Field | Meaning |
|-------|---------|
| `lifecycle_status` | `active` (default) / `misrouted` / `voided` / `superseded` / `duplicate` |
| `rehome_event_id` | back-pointer to the rehome event (if any) |
| `rehome_target_topic` | the topic this record was rehomed into |
| `replaced_by` | the active record that replaces this one (if any) |

These fields are optional with defaults, so records written before this feature still load
and read as `active` — no migration required.

## Operations

### `record supersede` — mark a record inactive

Mark a claim or evidence `misrouted`, `voided`, `superseded`, or `duplicate`. Optionally
point at a replacement record.

```
aitp-v5 record supersede \
    --record-id claim-... \
    --kind claim \
    --status misrouted \
    --replacement-ref claim-...-6b58e983 \
    --reason "replaced by active claim"
```

### `record rehome` — move a misrouted record to the right topic

Re-attributes a record to the correct topic. The record file is not moved or deleted; it is
labeled `misrouted` and a cross-topic pointer is added in the target topic's ledger.

```
aitp-v5 record rehome \
    --record-id claim-... \
    --kind claim \
    --from-topic wrong-topic \
    --to-topic right-topic \
    --reason "Si G0W0 dataset misrouted"
```

### `record audit-routing` — inspect misroute history

```
aitp-v5 record audit-routing --topic wrong-topic
```

### `record lifecycle` — full history for one record

```
aitp-v5 record lifecycle --record-id claim-...
```

`--base <workspace>` may be passed before the `record` subcommand (it defaults to `.`).

## MCP tools (plan -> apply for rehome)

- `aitp_v5_build_rehome_plan` (read-only)
- `aitp_v5_apply_rehome_plan` (explicit record ids only; idempotent — re-applying returns
  the same event ids and writes nothing new)
- `aitp_v5_supersede_record`
- `aitp_v5_audit_record_routing`

`apply_rehome_plan` rejects empty lists and glob/pattern ids (`claim-*`); every id must be
explicit.

## How the relation-map treats lifecycle status

A topic's relation-map splits records into zones:

| Zone | Records |
|------|---------|
| `supported_by` / `limited_by` / `contradicted_by` / `not_tested_by` | `lifecycle_status == active` |
| `historical` | `superseded`, `duplicate` |
| `misrouted` | `misrouted`, `voided` |
| `cross_topic_references` | records rehomed *into* this topic from elsewhere |

The topic's current conclusion is computed **only** from the active zone. Misrouted records
do not pollute it.

## Idempotency

- rehome key: `(record_id, "rehome", to_topic)` — re-applying returns the same event.
- supersede key: `(record_id, "supersede", status, replacement_ref)` — same key returns the
  same event; a *different* status writes a new event chained via `supersedes_event`.

## Legacy workaround

Recording a `routing_correction` evidence note is the **legacy** workaround and is
superseded by this system. Prefer `record rehome` + `record supersede`.
