# AITP v5 Record Lifecycle (rehome / supersede / audit-routing) — Design

- **Date:** 2026-06-19
- **Status:** Approved (pending implementation)
- **Owner:** bohan-jia
- **Motivating case:** Si/GW Hamiltonian dataset claims were written to the wrong topic
  (`qsgw-headwing-update-librpa`) when they belong in `si-g0w0-8atom-k999-throughput`.
  Today the only remediation is a `routing_correction` evidence record, which (a) does not
  mark the misrouted record as inactive, (b) still pollutes the source topic's
  relation-map, and (c) provides no clean way to re-attribute the record to the correct topic.

## 1. Problem

Typed records (`ClaimRecord`, `EvidenceRecord`, `ToolRunRecord`, sessions) are append-only
files with **no lifecycle field**. A record that was written to the wrong topic, superseded
by a newer record, or entered in error cannot be:

- marked inactive without losing it from audit history,
- re-attributed to the correct topic without breaking the registry/ledger invariants,
- excluded from a topic's active relation-map conclusion without also losing cross-topic
  provenance.

The legacy `routing_correction` evidence workaround is unsatisfactory because evidence
records have a fixed contract (they support/limit/refute a claim) and the relation-map
buckets them into active support — exactly the pollution we want to avoid.

## 2. Goals / Non-Goals

**Goals**

1. Mark a record `misrouted` / `voided` / `superseded` / `duplicate` / `rehomed` so the
   relation-map excludes it from the source topic's *active* conclusion.
2. Re-attribute a record to the correct topic via in-place labeling + a topic pointer,
   without copying content and without deleting anything.
3. Full provenance: every lifecycle change produces one append-only `lifecycle_event`
   record capturing operator, time, reason, from/to topic, replacement.
4. Idempotent operations; repeated applies never produce duplicate corrections.
5. Minimal, safe CLI + MCP surface following the existing plan→apply precedent.
6. Zero-risk backward compatibility: existing `.aitp` registry files keep reading.
7. Documentation stating hard-delete is not the path; rehome/supersede is.

**Non-Goals**

- Hard deletion of records. **Out of scope by explicit user decision (option 1).**
  Files are never removed. This is the safe-by-default model; no `--hard-purge` is
  provided in this version.
- Cascading lifecycle changes (e.g. auto-supersede every evidence of a voided claim).
  Out of scope; lifecycle applies to one record per explicit id.
- Migrating the real Theoretical-Physics `.aitp` data as part of implementation. The
  migration is performed by the operator after the tooling ships; implementation only
  reproduces the scenario in test fixtures.

## 3. Decisions (locked during brainstorming)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Persistence model | Lifecycle frontmatter fields on existing records **+** a new dedicated `lifecycle_event` record family |
| D2 | Rehome move semantics | **Re-attribute in place + topic pointer** (no copy, no delete) |
| D3 | MVP scope | **Full vertical**: 4 CLI commands, 4 MCP tools, relation-map 4-zone filtering, lifecycle_event family + public surface, full test matrix, docs |
| D4 | Event model | **Dedicated `lifecycle_event` family** (`registry/lifecycle_events/<id>.md`) |
| D5 | Deletion policy | **Logical deletion only** (mark `voided`/`misrouted`; files never removed) |

## 4. Data Model

### 4.1 New record family: `lifecycle_event`

Stored at `registry/lifecycle_events/<event_id>.md` (YAML frontmatter + Markdown body).
Append-only; one file per event.

```yaml
event_id:           ev-rehome-claim-...-8b58e983   # prefixed_id, deterministic hash
event_type:         rehome | supersede              # only these two, initially
subject_record_id:  claim-...-f014bb30              # the record being affected
subject_kind:       claim | evidence | tool_run | session   # derived from the subject record
from_topic:         qsgw-headwing-update-librpa     # required for rehome
to_topic:           si-g0w0-8atom-k999-throughput   # required for rehome; optional for supersede
lifecycle_status:   misrouted | voided | superseded | duplicate | rehomed
replacement_ref:    claim-...-6b58e983              # optional; points at the active replacement
reason:             "short human string"
operator:           bohan-jia
timestamp:          2026-06-19T10:00:00Z            # ISO 8601, UTC
supersedes_event:   ev-rehome-...                   # optional; chains events
```

`lifecycle_status: rehomed` is valid **only on the event** (the action that was taken). The
subject record itself uses `misrouted` to signal "not active in this topic". This split
keeps the record's status vocabulary closed while the event log can still express "a rehome
action occurred here".

Frontmatter keys, by convention, mirror the dataclass fields. The Markdown body carries a
human-readable summary (operator, action, reason) for grep/audit readability.

### 4.2 Lazy-compatible frontmatter fields on existing records

Added to `ClaimRecord` and `EvidenceRecord` (and any record family that may later need
lifecycle). All are **optional** with defaults, so existing readers and existing files are
unaffected:

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| `lifecycle_status` | `str` | `"active"` | `active`/`misrouted`/`voided`/`superseded`/`duplicate` |
| `rehome_event_id` | `str` | `""` | back-pointer to the `lifecycle_event` that rehomed this record |
| `rehome_target_topic` | `str` | `""` | target topic id (relation-map fast filter) |
| `replaced_by` | `str` | `""` | set on superseded/voided/duplicate records; points at the replacement |

A rehomed record carries `lifecycle_status: misrouted` (it is not active in its birth
topic). The `rehomed` value appears **only** on the `lifecycle_event` (the action taken),
never on the record itself. This keeps the record status vocabulary closed.

`store.read_record`'s dataclass field-name filter already drops unknown keys, so old
readers ignore these and old files (which lack them) parse with the defaults above.

### 4.3 Cross-topic pointer (target topic ledger)

When a record is rehomed **into** topic T, a lightweight pointer entry is appended in
`topics/T/claims/ledger/` (for claims) — or the analogous evidence ledger — referencing the
original record id. This is a *reference*, not a copy: it contains the original record id,
a `pointer: true` flag, and `source_topic`. The pointer lets topic T's relation-map surface
the rehomed record as a cross-topic reference. The original file's location is unchanged.

### 4.4 Core invariants (tests enforce all of these)

1. **No hard delete.** rehome/supersede never removes or rewrites a record body. They only
   add frontmatter fields and write a new `lifecycle_event` file.
2. **One event per lifecycle change.** Each change produces exactly one
   `lifecycle_event` record under `registry/lifecycle_events/`.
3. **Idempotency.** Each event type has a deterministic identity key:
   - rehome: `(subject_record_id, "rehome", to_topic)`
   - supersede: `(subject_record_id, "supersede", lifecycle_status, replacement_ref)`

   A key may resolve to at most one event. Re-applying a plan whose event already exists
   is a no-op returning the existing event id; never a second event. Superseding the same
   record with a *different* status is allowed and chains via `supersedes_event`
   (most recent event wins for bucketing) — this is not an idempotency violation because
   the key differs.
4. **Registry ↔ ledger consistency.** A rehomed claim keeps its registry entry; a pointer
   is added in the target topic ledger; the source topic ledger entry is **not** removed.
5. **Relation-map filtering is status-driven.** Only `lifecycle_status` determines
   bucketing; the event log is read-side provenance only and never changes trust.

## 5. Rehome Semantics

A single rehome operation, given `(record_id, from_topic, to_topic, reason, operator)`:

1. Validate `record_id` exists, `from_topic` matches the record's current topic, and
   `to_topic` exists. **Any failure aborts with no state change.**
2. Set on the record: `lifecycle_status: misrouted`, `rehome_target_topic: <to_topic>`,
   `rehome_event_id: <event_id>`.
3. Append a pointer entry in the target topic ledger referencing the original record id.
4. Write a `lifecycle_event` with `event_type: rehome`, `from_topic`, `to_topic`,
   `lifecycle_status: rehomed` (note: the *event* uses `rehomed`; the *record* carries
   `misrouted` to express "this record is not active in its birth topic"), `reason`,
   `operator`, `timestamp`.
5. Source topic's relation-map now excludes this record from active buckets; target topic's
   relation-map surfaces it as a cross-topic reference.

**Idempotency:** if a `lifecycle_event` with the same `(subject_record_id, "rehome",
to_topic)` already exists, the apply is a no-op returning the existing event id.

## 6. Supersede Semantics

Given `(record_id, status, replacement_ref?, reason, operator)` where
`status ∈ {misrouted, voided, superseded, duplicate}`:

1. Validate `record_id` exists. If `replacement_ref` given, validate it exists and (when
   both are claims) is `active`. Abort on any failure.
2. Set `lifecycle_status: <status>` on the record. If `replacement_ref` given, set
   `replaced_by: <replacement_ref>`.
3. Write a `lifecycle_event` with `event_type: supersede`, `lifecycle_status: <status>`,
   `replacement_ref`, `reason`, `operator`, `timestamp`.
4. Relation-map moves the record out of active buckets; if `replaced_by` is set, the
   replacement surfaces as the active support instead.

**Idempotency:** re-superseding the same record with the same `(status, replacement_ref)`
returns the existing event id; superseding with a *different* status writes a new event and
chains it via `supersedes_event` (the most recent event wins for bucketing).

## 7. CLI Surface (4 commands)

All under a new top-level `record` subcommand (does not collide with the existing
`code state record` / `evidence record` subcommands):

```
aitp-v5 record rehome \
    --record-id claim-...-f014bb30 \
    --from-topic qsgw-headwing-update-librpa \
    --to-topic   si-g0w0-8atom-k999-throughput \
    --reason "Si G0W0 dataset misrouted; belongs in throughput topic"

aitp-v5 record supersede \
    --record-id claim-...-f014bb30 \
    --status misrouted \
    --replacement-ref claim-si-g0w0-...-6b58e983 \
    --reason "replaced by active claim in si-g0w0-8atom-k999-throughput"

aitp-v5 record audit-routing --topic qsgw-headwing-update-librpa
    # lists every misrouted/rehomed/superseded record that touched this topic

aitp-v5 record lifecycle --record-id claim-...-f014bb30
    # prints the full lifecycle event history for a single record
```

**Safety:** every command requires an explicit `--record-id` (or `--topic` for audit). No
glob, no fuzzy match, no batch-by-pattern.

## 8. MCP Surface (4 tools, plan→apply)

Registered in `brain/v5/mcp_tools.py`, mirroring the `legacy_semantic_repair`
plan/apply precedent:

| Tool | Behavior |
|------|----------|
| `aitp_v5_build_rehome_plan` | **Read-only.** Takes `record_ids[]`, `from_topic`, `to_topic`, `reason`. Returns a plan describing every change (record fields to set, pointer to add, event to write) without touching state. |
| `aitp_v5_apply_rehome_plan` | Takes the **explicit** plan (must contain explicit record ids). Validates idempotency, applies, returns created event ids. Refuses empty / pattern-matched record ids. |
| `aitp_v5_supersede_record` | Single-record supersede. Validates, applies, returns event id. |
| `aitp_v5_audit_record_routing` | Read-only. Returns misrouted/rehomed/superseded history for a topic or record. |

Plan-then-apply is enforced for rehome (the riskier operation); supersede and audit are
direct calls.

## 9. Relation-Map Behavior

`claim_relation_map._bucket_for_status` gains a lifecycle filter. A topic's relation-map
now exposes four zones:

| Zone | Contents |
|------|----------|
| `active_support` (existing buckets: supported_by / limited_by / contradicted_by / not_tested_by) | records with `lifecycle_status == active` |
| `historical` | records with `lifecycle_status ∈ {superseded, duplicate}` — kept for audit, excluded from the active conclusion |
| `misrouted` | records with `lifecycle_status ∈ {misrouted, voided}` that originated in this topic |
| `cross_topic_references` | rehomed records pointed into this topic from elsewhere |

The `current_conclusion` of a topic is computed **only** from `active_support`. The source
topic's conclusion is therefore not polluted by its misrouted records. The new zones are
additive; existing relation-map consumers that ignore them keep working.

## 10. Testing Matrix (fixtures, not real data)

All tests build throwaway workspaces under `tmp_path` reproducing the Si scenario. The
real `.aitp` is never touched.

| # | Test | Asserts |
|---|------|---------|
| T1 | claim rehome | registry entry unchanged in location; pointer added in target ledger; lifecycle fields set; one event written |
| T2 | evidence marked misrouted | relation-map for the source topic no longer treats it as support/limit/contradict |
| T3 | replacement claim in new topic | relation-map of target topic surfaces it as active (or cross-topic reference) |
| T4 | audit-routing | lists all misrouted/rehomed history for a topic |
| T5 | idempotent apply | re-applying the same rehome plan does not produce a second event; returns same event id |
| T6 | invalid topic / record id | operation fails and **no** state changes (no fields set, no event written) |
| T7 | backward compat | a registry file written in the old format (no lifecycle fields) parses with defaults `lifecycle_status: active` |
| T8 | supersede with replacement | relation-map shows replacement as active, old record in `historical` |
| T9 | lifecycle CLI | `record lifecycle` prints the chained event history for a record |
| T10 | MCP build/apply | `build_rehome_plan` is read-only (no state change); `apply_rehome_plan` requires explicit ids and applies them |

## 11. Backward Compatibility

- No change to the on-disk layout of existing record families. New frontmatter fields are
  optional with defaults.
- `store.read_record` already filters by dataclass field name, so unknown keys are dropped;
  this needs no migration.
- No reader needs to change to keep working. Lifecycle awareness is opt-in via the new
  fields and the new `lifecycle_events` family.
- No migration script is required for the first release. If a future need arises, a
  one-shot migration can backfill `lifecycle_status: active` but it is not required for
  correctness (default semantics already equal `active`).

## 12. Documentation

Add `docs/.../record-lifecycle.md` (or extend the existing v5 CLI/MCP doc) covering:

- Hard delete is not supported and not recommended; records are immutable history.
- `rehome` / `supersede` are the preferred remediation.
- `routing_correction` evidence is the **legacy** workaround and is superseded by this
  system.
- How the relation-map treats `active` / `historical` / `misrouted` / `cross_topic_reference`
  records.
- Worked example using the Si scenario.

CLI `--help` text and MCP tool docstrings restate the above at the call site.

## 13. Files Changed (estimated)

**New:**
- `brain/v5/lifecycle_events.py` — `lifecycle_event` family: dataclass, create/read/list,
  idempotency lookup.
- `brain/v5/cli_record_lifecycle.py` — 4 CLI command implementations.
- `brain/v5/mcp_lifecycle.py` — 4 MCP tool implementations (build_rehome_plan,
  apply_rehome_plan, supersede_record, audit_record_routing).
- `tests/test_v5_lifecycle.py` — T1–T10.
- `docs/.../record-lifecycle.md` — user-facing doc.

**Modified:**
- `brain/v5/models.py` — add the four optional lifecycle fields to `ClaimRecord` and
  `EvidenceRecord`; add `LifecycleEventRecord` dataclass.
- `brain/v5/record_contracts.py` — register a validator for `lifecycle_event`; extend
  base-record validation to allow the new optional fields.
- `brain/v5/public_surfaces.py` — register `lifecycle_event` and any new public surfaces.
- `brain/v5/claim_relation_map.py` — `_bucket_for_status` lifecycle filter + the four zones.
- `brain/v5/cli.py` — mount the `record` subcommand and its sub-subcommands.
- `brain/v5/mcp_tools.py` — register the four MCP tools.
- `brain/v5/store.py` — `read_record` path for the new family (if needed beyond the
  generic registry reader).

## 14. Si Misrouting Migration Plan (operator-run, not part of implementation)

After the tooling ships, the operator runs the following **explicitly, one record at a
time**, per the no-batch / explicit-id safety rule. Implementation does not execute this.

Misrouted records (in `qsgw-headwing-update-librpa`):
- `claim-qsgw-headwing-update-librpa-the-correct-si-g0w0-f014bb30`
- `claim-qsgw-headwing-update-librpa-si8-perturbation-hig-706cc7ba`
- `claim-qsgw-headwing-update-librpa-the-correct-si-workf-1530c357`

Correct topic: `si-g0w0-8atom-k999-throughput`.
Correct active claim: `claim-si-g0w0-8atom-k999-throughput-for-the-machine-le-6b58e983`.

Per misrouted claim:

```
aitp-v5 record rehome \
    --record-id claim-qsgw-headwing-update-librpa-the-correct-si-g0w0-f014bb30 \
    --from-topic qsgw-headwing-update-librpa \
    --to-topic   si-g0w0-8atom-k999-throughput \
    --reason "Si G0W0 dataset misrouted; belongs in throughput topic"

aitp-v5 record supersede \
    --record-id claim-qsgw-headwing-update-librpa-the-correct-si-g0w0-f014bb30 \
    --status misrouted \
    --replacement-ref claim-si-g0w0-8atom-k999-throughput-for-the-machine-le-6b58e983 \
    --reason "replaced by active claim in si-g0w0-8atom-k999-throughput"
```

Repeat for the other two record ids. Then verify with:

```
aitp-v5 record audit-routing --topic qsgw-headwing-update-librpa
```

which should list the three rehomed/superseded records, and the topic's relation-map
current conclusion should no longer reference them as active support.
