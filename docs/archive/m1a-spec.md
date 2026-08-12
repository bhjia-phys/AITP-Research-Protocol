# M1a implementation spec — Memory that restores (`list`, `show`, `enter` v2)

Status: implementation specification; **done; deterministic gate passed**.

Scope: this document is the complete implementation-level spec for M1a,
"Memory that restores", per `docs/roadmap.md` §M1a (v3.7) and the M1
specification index `docs/m1-read-write-balance.md`. The implementation and
checklist evidence are recorded in [`docs/m1a-stage-notes.md`](m1a-stage-notes.md).
`docs/m1b-spec.md` remains a blocked M1b candidate-inventory pre-spec and is not
an implementation-level spec. The current CLI includes `list` and `show`, with
versioned read payloads for `enter`, `list`, and `show`; `check` remains absent.
The original M0.6 bootstrap Notes/decisions, recall/false-import/human-time,
held-out S3, paired S1/S2, cold-start, conformance, causal, and
treatment-advantage evidence is **not measured; deferred; not counted**. M1a
completion is deterministic implementation evidence only; it does not claim
bootstrap validation, behavioral or treatment superiority, causal effect, or
AITP advantage over plain files.

## Goal

Dense stores must be navigable and resumable, not just writable. M1a adds
exact-record retrieval (`aitp show <entry-id>`), filtered enumeration
(`aitp list [--kind KIND] [--since DATE]`), and upgrades `enter` so the
handoff is authoritative (closeout-first), Notes sort by record time, the
working-Note age signal is reported structurally, and legacy-derived material
is labeled orientation-only. All three commands are read-only deterministic
projections with versioned `--json` payloads; no index, cursor, cache, or
write is introduced.

## Gate prerequisite (binding)

`suite/FROZEN.md` v6 is an archived, anchored, unexecuted preregistration. It
records the runtime baseline as 1,082 nonblank lines in 9 modules. The v5
anchor commit `ac5209647f5f2a88a530dcd2856c13d39d31e856` still contains
identical runtime bytes, while the v6 identity-contract documents are anchored
by `145261805d5205d2150dca18c6c42d5a18a628f2`. The anchor and hashes establish
packet identity only; they are not scored evaluation evidence. M1a runtime
changes cannot be described as scores for v6. Any future external or human
scored evaluation requires a separately reviewed protocol revision and a new
freeze/refreeze before held-out execution.

The approved 2026-08-10 narrowed M0.6 gate review was the sole M1a
authorization transition. M1a has now completed its deterministic
implementation gate; the evidence is recorded in `docs/m1a-stage-notes.md`.
The original bootstrap Notes/decisions, recall/false-import/human-time,
held-out S3, paired S1/S2, cold-start, conformance, causal, and
treatment-advantage evidence is **not measured; deferred; not counted**; these
gaps are not M1a evidence.
Therefore:

- M1a implementation from this spec is complete. Deterministic S1/S2 seed
  regression, generated goldens, all tests, read-only byte-identical GW_librpa
  acceptance, performance, and line caps passed. Paired treatment-control
  evidence is optional future evidence, not a required M1a gate.
- `suite/adapters/cli.md` remains part of frozen v6 and was not changed by this
  implementation. A future suite refreeze/review may synchronize it; runtime
  changes must not be called v6 score evidence.
- The measured runtime is 1,256 nonblank lines against the 1,082 baseline,
  within the ≤ 1,300 cap (see the stage notes for the module breakdown).

### Post-gate transition

The M1a gate starts the two-session natural-use pause, not M1b; M1b remains a
candidate inventory until its separate review and selected-slice authorization.

### Read-only Note structural validator

M1a requires one minimal, reusable structural Note validator for its read projections.
It parses and checks only the Note schema/frontmatter/body structure needed for
the projection; every read invocation calls it with
`validate_evidence=False`. The read path must not acquire a store lock, call
`atomic_write`, write `.aitp/local/`, or mutate any canonical file. Save keeps
its existing validator, evidence validation, lock, and write semantics exactly
unchanged; this read-only helper is not a save-path relaxation.

## CLI grammar and help intent

Full grammar after M1a (new commands in bold):

```text
aitp init --topic <slug> --title "<title>" [--cwd PATH] [--adopt] [--dry-run] [--json]
aitp enter [--recent N] [--cwd PATH] [--json]
aitp inventory <path> --name <slug> [--cwd PATH] [--json]
aitp record prepare --kind <kind> [--authority <a>] [--created-by <id>] [--idempotency-key <k>] [--cwd PATH] [--json]
aitp record save <draft> [--cwd PATH] [--json]
aitp note prepare --mode <working|theory> --title "<title>" [--created-by <id>] [--cwd PATH] [--json]
aitp note save <draft> [--cwd PATH] [--json]
aitp list [--kind <kind>] [--since <date>] [--cwd PATH] [--json]
aitp show <entry-id> [--cwd PATH] [--json]
```

Help intent: every command, and every flag added by M1a, has a one-line
`help=` string; existing flags keep their current (no-help) behavior.
`--help` prints the grammar and defaults only (no behavioral essays);
`--help` rendering must stay below 250 ms per the gate. New help strings:

- `list`: "list canonical Entries with optional --kind and --since filters"
- `list --kind`: "only Entries of this kind (observation, result, failure,
  decision, source, code_change, run, closeout)"
- `list --since`: "only Entries recorded at or after this ISO date/timestamp
  (inclusive)"
- `show`: "show one Entry's complete frontmatter and body"

`--cwd` (default `.`) and `--json` behave exactly as on every existing
command. `show`'s `entry-id` positional is required (argparse); `aitp show`
with no argument is an argparse usage error: usage to stderr, exit 2.

## `aitp list`

```
aitp list [--kind KIND] [--since DATE] [--cwd PATH] [--json]
```

Read-only projection over every structurally valid canonical Entry
(`.aitp/topic/entries/entry-*.md`), **including superseded Entries**. No
window, no cursor, no cache, no lock, no write of any kind.

### JSON payload (schema `aitp/list-0.1`)

```json
{
  "schema": "aitp/list-0.1",
  "root": "<absolute workspace root>",
  "count": 7,
  "entries": [
    {
      "id": "entry-77777777777777777777777777777777",
      "kind": "decision",
      "status": "active",
      "created_at": "2026-07-06T09:00:00.000001Z",
      "authority": "human",
      "summary": "Adopt the corrected cutoff for the campaign.",
      "legacy_derived": false,
      "source": ".aitp/topic/entries/entry-77777777777777777777777777777777.md"
    }
  ],
  "warnings": []
}
```

- `count` = length of `entries` after filtering.
- `entries` entry fields: `id`, `kind`, `status` (`"active"` | `"superseded"`),
  `created_at` (raw stored string; invalid values kept verbatim), `authority`,
  `summary` (**complete, untruncated**), `legacy_derived` (bool), `source`
  (store-relative path).
- `warnings`: one item per skipped/abnormal file, each `{code, path,
  message}` with the failure's `AITPError` code (`malformed_record`,
  `missing_field`, `invalid_schema`, `duplicate_id`, `invalid_timestamp`,
  …). Structural failures never crash the list.
- A file that parses but fails `validate_entry(validate_evidence=False)` is
  skipped with a warning; evidence pins are never re-validated on the read
  path, so stale local evidence cannot crash `list`.

### Text output

One row per entry on stdout:

```text
<created_at> <id> <kind> <active|superseded>[ legacy-derived] <summary-truncated>
```

`<summary-truncated>`: summary collapsed to single spaces, stripped, then
truncated to approximately 110 Unicode characters — at most 110 chars, plus
`…` when truncated (111 chars total). JSON keeps the complete summary with
its original whitespace. A legacy-derived row appends ` legacy-derived` to
the status column. Warnings print to stderr as `warning[<code>]: <path>:
<message>`. Empty result prints nothing; exit 0.

### `--kind`

- Value is normalized with `kind.replace("-", "_")` (same rule as `record
  prepare`), so `code-change` and `code_change` both match the `code_change`
  kind.
- Unknown value → `AITPError("invalid_kind", ...)` with a message naming the
  allowed kinds: `unsupported Entry kind: <value> (allowed: observation,
  result, failure, decision, source, code_change, run, closeout)`. Exit 2
  (same code as `record prepare`'s invalid kind; messages may differ).
- Filtering applies to the status-aware scan: superseded Entries are
  included when their kind matches.

### `--since` and time handling

- Accepts an ISO date (`2026-08-06`) or ISO timestamp (`2026-08-06T09:00:00Z`,
  any ISO-8601 offset). Parsing rule: `datetime.fromisoformat(value.replace(
  "Z", "+00:00"))`; a naive result is assumed UTC (date-only means
  `00:00:00+00:00`). Unparseable value → `AITPError("invalid_since", ...)`,
  exit 2 — a fatal flag error, never a warning.
- Inclusive: an Entry is kept iff its parsed `created_at` ≥ the parsed
  `--since` (both normalized to aware UTC).
- A stored `created_at` that does not parse: when `--since` is present it
  cannot be compared, so the Entry is **omitted with a warning**
  (`code: "invalid_timestamp"`, message `unparseable created_at: <raw>`),
  never guessed. When `--since` is absent the Entry is **kept** (raw value
  shown), sorted after all valid timestamps, also with the warning.

### Ordering

- Valid timestamps sort newest first; tie-breaker is Entry ID descending
  (string comparison — IDs are `entry-<32hex>`, string order equals hex
  order).
- Invalid timestamps sort after all valid ones; among themselves by raw
  `created_at` string then ID, descending. The rule is one shared sort key
  (see `query._sort_key`), used by `list`, `show`-adjacent scans, and
  `enter`.

## `aitp show`

```
aitp show <entry-id> [--cwd PATH] [--json]
```

Read-only exact-record read: the complete frontmatter and body, the canonical
source path, and the active/superseded status. No derived relations are
invented (`used_by` is M1b). Evidence pins are not re-validated (reads must
survive drifted local evidence).

### JSON payload (schema `aitp/show-0.1`)

```json
{
  "schema": "aitp/show-0.1",
  "root": "<absolute workspace root>",
  "id": "entry-44444444444444444444444444444444",
  "status": "superseded",
  "source": ".aitp/topic/entries/entry-44444444444444444444444444444444.md",
  "legacy_derived": false,
  "frontmatter": {
    "schema": "aitp/lite-entry-0.1",
    "id": "entry-44444444444444444444444444444444",
    "topic": "nio",
    "created_at": "2026-07-03T09:00:00.000001Z",
    "created_by": "agent:codex",
    "kind": "result",
    "authority": "agent",
    "summary": "The update removes the discontinuity under the old cutoff.",
    "refs": [{"target": "theory/check.md", "at": "sha256:cdbdf8597befbea0b88f4d552a127719f52ad69ed1f6174140a60292590f1f65", "locator": "whole file"}],
    "limitations": ["Only three momentum points were checked."],
    "resolves": [],
    "supersedes": [],
    "next_action": ""
  },
  "body": "<complete body text, verbatim>"
}
```

- `frontmatter` is the full parsed frontmatter map, verbatim (all v0.1 keys,
  plus any optional ones such as `idempotency_key`); stored order preserved.
  Nesting under `frontmatter` avoids the `schema` collision with the payload
  version.
- Derived fields at top level: `status`, `source`, `legacy_derived`, plus
  `id` for convenience.
- `status`: `"active"` unless the Entry's ID appears in some structurally
  valid Entry's `supersedes` list (same active computation as `enter`).

### Text output

```text
id: <id>
status: <active|superseded>
source: <store-relative path>
legacy_derived: <true|false>
<every frontmatter key in stored order: key: <scalar> — lists/dicts as JSON>
<blank line>
<body verbatim>
```

### Errors

- `entry-id` not matching `^entry-[0-9a-f]{32}$` →
  `AITPError("invalid_id", "invalid Entry ID")`, exit 2 (same code as
  `validate_entry`).
- ID valid but no canonical file →
  `AITPError("entry_not_found", f"no Entry with id {entry_id}")`, exit 2.
- File exists but fails parse/validation → the failure's code
  (`malformed_record`, …), exit 2; stale pins cannot trigger this
  (evidence not re-validated).

## `enter` v2 (schema `aitp/enter-0.2`)

`enter` remains a compact orientation view — not a search command. Its
structural sections (topic/goal, recent active Entries, unresolved failures,
next action, recent Notes, counts, warnings) are unchanged; the payload gains
a version marker and the M1a fields. Deterministic structural sections and
no semantic ranking: unchanged.

### Payload delta from the M0 payload

```json
{
  "schema": "aitp/enter-0.2",
  "memory_status": "available",
  "root": "<golden-store>",
  "topic": {"id": "nio", "title": "…", "goal": {"text": "…", "source": "…"}},
  "recent_entries": [
    {"id": "…", "kind": "…", "summary": "…", "limitations": ["…"],
     "authority": "…", "created_at": "…",
     "refs": [{"target": "…", "at": "sha256:…", "locator": "…"}],
     "source": "…", "legacy_derived": false}
  ],
  "unresolved_failures": [ …same shape… ],
  "next_action": {"text": "…", "entry_id": "…", "authority": "…",
                  "created_at": "…", "source": "…"},
  "latest_working_note": {"id": "note-…", "created_at": "…", "source": "…"},
  "recent_notes": [
    {"id": "…", "title": "…", "mode": "…", "review_state": "…",
     "created_at": "…", "summary": "…", "source": "…", "legacy_derived": false}
  ],
  "counts": {"active": 6, "superseded": 1, "unresolved_failures": 1,
             "malformed": 0, "omitted_active": 0,
             "active_newer_than_latest_working_note": 0},
  "warnings": []
}
```

Additive changes only — every existing key keeps its meaning and shape:

1. Top-level `"schema": "aitp/enter-0.2"` (the M0 payload had none).
2. `recent_entries` and `unresolved_failures` entries gain `legacy_derived`
   (both use the same `output_entry` projection, so it lands in both for
   free).
3. `recent_notes` entries gain `created_at` (recorded time) and
   `legacy_derived`.
4. New top-level `latest_working_note` (object `{id, created_at, source}` or
   `null`).
5. New `counts` key `active_newer_than_latest_working_note` (`int` or
   `null`).
6. `next_action` selection is closeout-first (below); its shape is
   unchanged, including the `{"status": "not_established", "source": null}`
   fallback.

### Closeout-first handoff

The next action must come from the explicit current handoff, not from a
newest-timestamp scan (dense-ledger dogfood finding). Selection, in order:

1. Scan the active Entries, newest first (valid timestamps first, per the
   shared sort key). Return the first whose `kind == "closeout"` and whose
   `next_action` is a non-empty string.
2. Only if no active closeout establishes a handoff, scan again over all
   active Entries, newest first, and return the first with a non-empty
   `next_action`.
3. Neither → `{"status": "not_established", "source": null}`.

The returned object retains the exact source Entry ID, `created_at`,
`authority`, and file path — unchanged fields, new selection rule.

### Notes ordering

`recent_notes` sorts by the shared sort key over the recorded `created_at`
and ID, descending — not by UUID filename. In the golden store both rules
coincide (`note-2222…`, 2026-07-07, sorts before `note-1111…`, 2026-07-06,
under either sort), so the golden order does not change; the rule change is
observable only where UUID filename order disagrees with recorded-time order,
which test 12 covers synthetically.

### Latest working Note and the null age count

- **Full note scan**: every canonical Note (`.aitp/topic/notes/note-*.md`)
  is parsed in full on every read — the scan covers the whole Notes
  directory, not just the `recent` window. A malformed Note (parse or
  validation failure) is excluded from `recent_notes` and
  `latest_working_note`, increments `counts.malformed`, and appends a
  warning — the same per-file rule as Entries, applied to Notes.
- `latest_working_note`: `null`, or an object with exactly three fields —
  `id`, `created_at` (raw stored string), `source` (store-relative path);
  no other fields. Among structurally valid canonical Notes with
  `mode == "working"`, the newest by the shared sort key; else `null`.
  Supersession is **not** consulted — this is a structural age signal, not a
  semantic claim (the design doc's wording: the count is "a structural age
  signal, not a claim that those Entries are semantically uncovered").
- `counts.active_newer_than_latest_working_note`: `null` when
  `latest_working_note` is `null` **or** when the working Note's `created_at`
  does not parse; otherwise the number of **active** Entries whose parsed
  `created_at` is strictly greater than the Note's. Entries whose
  `created_at` does not parse are not counted (and remain visible through
  `list`). A count of 0 is a valid non-null value.
- The count reports active Entries only, and only the count — no entry list.

### Legacy-derived labeling (exact marker)

- **Exact marker**: an Entry or Note is legacy-derived iff its body's first
  line is exactly the marker line frozen by `docs/m0.6-bootstrap.md` for
  bootstrap working Notes:

  ```text
  > legacy-derived: recovery orientation only — not re-validated
  ```

  No substring matching: the body's first line must equal the marker
  byte-for-byte (case-sensitive, including the `> ` prefix and the em dash),
  with no other characters before or after. A `legacy-derived:` substring
  anywhere else in the body, a marker on any line other than the first, or
  any character variation (`legacy-derived:` alone, `LEGACY-DERIVED:`,
  missing `> ` prefix, wrong dash) does **not** label. Individually confirmed
  legacy-derived drafts per the M0.6 conventions carry the same first line.
  Body only, no frontmatter.
- Surfacing: `legacy_derived: true` in `list` entries, `show` (top level),
  `recent_entries`, `unresolved_failures`, and `recent_notes`; `list` text
  rows append ` legacy-derived` to the status column.
- The label is orientation-only: it changes no validation, no credibility
  weighting, no ordering. The Skill (see Sync) interprets it.

## Errors and exit codes (compatibility contract)

Unchanged handler, new commands included: every `AITPError` produces
`{"status": "error", "code": "<code>", "message": "<message>"}` on stdout
when `--json` (exit 2), else `error[<code>]: <message>` on stderr (exit 2).
argparse-level errors (unknown flag, missing required positional) keep their
current behavior: usage to stderr, exit 2.

| Code | Where | Exit |
|---|---|---|
| `invalid_kind` | `list --kind` (unknown kind; same code as `record prepare`) | 2 |
| `invalid_since` | `list --since` (unparseable date/timestamp) | 2 |
| `invalid_id` | `show` (ID not `entry-<32hex>`; same code as `validate_entry`) | 2 |
| `entry_not_found` | `show` (valid ID, no canonical file) | 2 |
| `invalid_timestamp` | **warning only** (stored `created_at` unparseable) | 0 |

All existing codes (`invalid_root`, `not_initialized`, `malformed_store`,
`malformed_record`, …) keep their meaning; `list`/`show` may surface them as
per-file `warnings` with exit 0.

## Diagnostics: actionable pin errors

M1a scope item: error messages for stale or invalid pins provide actionable
remediation without accepting the changed evidence. Single change in
`records.py` `validate_refs` (sha256 branch): the message gains both digests:

```python
raise AITPError(
    "hash_mismatch",
    f"sha256 mismatch: {target}: expected {value}, actual {digest}",
)
```

(was `sha256 mismatch: {target}`). The missing-target message
(`reference target does not exist: <target>`) already names the exact target
and stays unchanged. No pin scheme, validation rule, or exit code changes.

## Performance: defaults, and the parser prohibition

Gate item: 1,000-Entry `enter` < 1 s with a wider margin than the M0.5
baseline (≈ 0.94 s, ~6% under; fails under load); per-record YAML frontmatter
parsing is ≈ 80% of the cost. The M1a defaults below are the only performance
work in scope, applied in this order:

1. **Shared single-pass scan.** All read projections consume the same
   `query._scan_entries` scan per canonical directory (`entries/`, `notes/`),
   so each file is loaded and parsed exactly once per command invocation;
   `list`, `show`, and `enter` never re-read or re-parse a file another
   projection has already scanned. Status (the supersedes set), filters, and
   the `enter` sections are computations over the already-parsed items, not
   new reads.
2. **No duplicate load/parse.** The entry view is one scan over
   `.aitp/topic/entries/`, the note view one scan over
   `.aitp/topic/notes/`; nothing loads a file twice, and no projection
   re-parses a file to derive a field it can take from the shared items
   (timestamps, summaries, frontmatter maps).
3. **Provable micro-optimizations only.** A micro-optimization (reuse of
   already-validated items, single truncation pass, no redundant string
   rebuilds) is allowed only when its effect is demonstrated: measured on the
   recorded machine and recorded in the stage notes. Speculative tuning is
   rejected.

No persistent index, no new dependency, no output-semantics change — under
any mechanism.

A custom fast frontmatter parser is **prohibited in M1a by default**: the
implementation session must not add any fast-path or strict-subset frontmatter
parser (with or without `yaml.safe_load` fallback), regardless of measured
margin. If, after the defaults above are measured, the 1,000-Entry `enter`
margin is still insufficient, the follow-up is a separate spec revision — not
an implementation decision. The revision must state the parser contract in
full and introduce a parity corpus (every canonical record in the golden
store and `cp -a` copies of `seeds/S1` + `seeds/S2`, plus hand-written edge
cases), with a parity test the parser must pass before any code lands.

## Implementation map (files/functions; line budget)

Budget: M1a runtime additions target **149–176 nonblank lines** against the
1,082-line baseline (`grep -c '\S'` per module, summed); hard cap: cumulative
total ≤ 1,300. If the gate review measures a different baseline, additions
shrink to fit the cap. Each module stays below 400 nonblank lines.

| File | Change | Estimate |
|---|---|---|
| `query.py` (new) | `list_workspace`, `show_entry`, shared single-pass `_scan_entries`, `_parse_since`, `_stored_time`, `_sort_key`, `_truncate`, `_is_legacy_derived`, `_projection` | +90–105 |
| `state.py` | `enter_workspace` v2: schema field, closeout-first `_pick_next_action`, shared sort key, full note scan + `created_at` sort + malformed counting, `latest_working_note` + age count, `legacy_derived` in `output_entry` and notes | +30–38 |
| `records.py` | `hash_mismatch` message with expected + actual digests | +3 |
| `cli.py` | `list`/`show` subparsers, help strings, routing in `main` | +22–26 |
| `core.py` | import + `__all__` for `list_workspace`, `show_entry` | +4 |

`md.py` is unchanged in M1a: all performance work sits in `query.py` /
`state.py` (shared scan, no duplicate load/parse, measured micro-
optimizations). A custom frontmatter parser in `md.py` is prohibited by
default (see Performance).

Target sum ≈ 149–176 (well inside the ≤ 1,300 cumulative cap). Private
cross-module imports are established practice
in this package (`state.py` already imports `records._canonical_entries`):
`state.py` imports `_sort_key` and `_is_legacy_derived` from `query.py`;
`query.py` imports `_canonical_entries`, `validate_entry` from `records.py`
and `parse_markdown` from `md.py`. No import cycle (`query.py` never imports
`state.py`).

Key function contracts:

- `query._parse_since(value) -> datetime` — raises `invalid_since` (message
  `invalid --since value: <value>`); naive → UTC.
- `query._stored_time(raw) -> datetime | None` — `fromisoformat(raw.replace(
  "Z", "+00:00"))`, naive → UTC; `None` on any failure.
- `query._sort_key(raw, entry_id) -> tuple[int, Any, str]` — `(0, parsed,
  id)` for valid timestamps, `(1, raw, id)` otherwise; consumers sort with
  `reverse=True`, which yields valid-newest-first and invalid-last.
- `query._truncate(text, limit=110) -> str` — collapse whitespace, strip,
  first 110 chars + `…` when longer.
- `query._is_legacy_derived(body) -> bool` — `body.splitlines()[0] ==
  "> legacy-derived: recovery orientation only — not re-validated"`; the
  marker must be the body's exact first line (byte-exact, including the em
  dash); no substring search.
- `query._scan_entries(root) -> (items, warnings)` — the one shared single-
  pass scan over a canonical directory: parse + `validate_entry(
  validate_evidence=False)` per canonical file, duplicate ID → warning +
  skip, structural failures → warning + skip; `items` carry frontmatter,
  body, and path. Each file is loaded and parsed exactly once per command
  invocation; `list`, `show`, and `enter` reuse the same items.
- `list_workspace(cwd, *, kind=None, since=None) -> dict` — scan, filter,
  sort, project; computes `status` from the superseded set over valid items.
- `show_entry(cwd, entry_id) -> dict` — ID regex check (`invalid_id`),
  canonical file existence (`entry_not_found`), parse + validate
  (evidence off), status, payload.
- `state._pick_next_action(ordered)` — two-pass closeout-first selection.
- `state` note scan — one scan over **all** canonical Notes (malformed →
  `counts.malformed` + warning, excluded from the view), sort by `_sort_key`,
  take the `recent` window; `latest_working_note` = max over
  `mode == "working"`, payload `{id, created_at, source}` or `null`.

All projections share the single scan (see Performance): per-projection
computations differ (`unresolved_failures`, closeout-first selection, the
note window) but run over the already-parsed shared items — no second read,
no re-parse, no duplicated scan plumbing.

## Golden fixtures (deliberate regeneration)

Per the roadmap, M1a regenerates goldens deliberately — no hand-editing of
payloads:

- Regenerate `tests/ledger/fixtures/golden/enter.json` and
  `enter-after-save.json` against the v0.2 payload (build the store via the
  public API exactly as `tests/ledger/test_golden.py` documents, freeze IDs
  and timestamps by hand, normalize `root` → `<golden-store>`). Expected
  deltas in the golden store (`nio`, 7 Entries, working Note
  `note-1111…`): `schema: "aitp/enter-0.2"`; `recent_notes` keeps the order
  [theory 2222, working 1111] (identical under the old filename sort and the
  new created_at sort) and each note gains `created_at` + `legacy_derived`;
  `latest_working_note` = `note-1111…`;
  `counts.active_newer_than_latest_working_note` = 0 in `enter.json` before
  save and 1 in `enter-after-save.json` after the dated `entry-8888…` result
  is appended; `next_action` = `entry-7777…` ("Archive the old sweep logs."
  — the golden store has **no closeouts**, so v2 exercises the fallback
  branch); `legacy_derived` false everywhere; all other values byte-identical
  to today's goldens.
- Add `list.json` — `list_workspace` on the golden store: 7 entries, sorted
  `7777… 6666… 5555… 4444… 3333… 2222… 1111…`, `4444…` superseded, rest
  active, `count` 7, warnings `[]`.
- Add `show.json` — `show_entry` of `entry-4444…` (superseded): exercises
  the `status` field in a golden.
- `test_golden.py` itself stays untouched; the regenerated goldens keep it
  green.

## Tests (new file `tests/ledger/test_query.py`)

Fixture style: `test_cli.py`-style subprocess runs (via the existing
`run_cli` helper) for CLI/exit-code contracts, `test_golden.py`-style
API calls for payloads. Do not modify existing test files (benchmark.py
excepted — see Benchmark).

1. `list_unfiltered_matches_golden` — `list_workspace` on a golden-store
   copy equals `golden("list.json")`.
2. `list_json_field_shape` — schema, count, entry field names, no
   truncation in JSON summaries.
3. `list_kind_filter` — `--kind result` → the 2 golden results;
   `--kind code-change` and `--kind code_change` both accepted;
   `--kind bogus` → exit 2, `code == "invalid_kind"`, message lists allowed
   kinds.
4. `list_since_inclusive` — boundary semantics: `--since 2026-07-03`
   (midnight UTC) includes `4444…` (2026-07-03T09:00); `--since
   2026-07-03T09:00:00Z` includes it (inclusive at the exact timestamp);
   `--since 2026-07-03T09:00:01Z` and `--since 2026-07-04` exclude it;
   `--since bogus` → exit 2, `code == "invalid_since"`.
5. `list_invalid_timestamp_no_since` — hand-written Entry with
   `created_at: "not-a-date"`: kept, sorted after valid ones, raw value in
   payload, warning `invalid_timestamp`, exit 0.
6. `list_invalid_timestamp_with_since` — same store: Entry omitted, warning
   present, exit 0.
7. `list_text_truncation` — Entry with a > 110-char summary: text row ends
   `…` at 110 chars; JSON summary complete.
8. `show_json_matches_golden` — `show_entry` of `entry-4444…` equals
   `golden("show.json")`; `status == "superseded"`.
9. `show_errors` — `show entry-nope` → exit 2 `invalid_id`; valid ID not in
   store → exit 2 `entry_not_found`; JSON error payload shape
   `{status, code, message}` on stdout; text mode prints
   `error[<code>]: <message>` on stderr.
10. `enter_v2_closeout_first` — synthetic store: closeout (older) with
    `next_action` X + newer non-closeout with `next_action` Y → `enter`
    reports X with the closeout's ID; superseded closeout with `next_action`
    does not win.
11. `enter_v2_closeout_fallback` — no active closeout with `next_action` →
    newest active carrier wins (golden store case, covered by the regenerated
    golden).
12. `enter_v2_note_order` — Notes sorted by `created_at`/ID desc, not
    filename.
13. `enter_v2_working_note_age_count` — working Note present: count =
    active Entries strictly newer; no working Note: `latest_working_note`
    null and count null; working Note with unparseable `created_at`: note
    reported, count null; count 0 is non-null.
14. `enter_v2_legacy_marker` — bootstrap-shaped working Note whose body's
    first line is exactly `> legacy-derived: recovery orientation only — not
    re-validated` → `legacy_derived: true` in `enter`, `list`, `show`; the
    marker on any other line, a substring elsewhere in the body, or any
    character variation (`legacy-derived:` alone, `LEGACY-DERIVED:`, missing
    `> ` prefix, wrong dash) is not labeled.
15. `enter_v2_note_read_only_validator` — a structurally malformed canonical
    Note is omitted from `recent_notes` and `latest_working_note`, emits a
    structural warning, and increments `counts.malformed`; a structurally valid
    Note with missing or drifted `basis_refs` remains readable because the read
    path calls `validate_evidence=False`; before/after `.aitp` hashes are
    byte-identical and the read path takes no lock, calls no `atomic_write`, and
    writes no `.aitp/local` state; save-path evidence validation remains
    unchanged.
16. `seed_regression_s1_s2` — on `cp -a` copies of `suite/seeds/S1` and
    `suite/seeds/S2`: `list` counts 31 / 30, `--kind result` 7 / 8,
    `--kind failure` 3 / 3; `enter` S1: active 29, superseded 2, malformed 0,
    unresolved 1, omitted_active 9, `active_newer_than_latest_working_note`
    10, `next_action.entry_id == "entry-0a21…"`,
    `latest_working_note.id == "note-0a01…"`; S2: active 28, omitted 8, age
    11, `next_action.entry_id == "entry-0b20…"`; `show` of the S1 γ=7/4
    failure (`entry-0a03…`) is kind `failure`, status `active`; the copies
    are byte-identical (`diff -r`) before/after all reads; the seeds
    themselves are never modified.
17. `error_payload_compat` — new commands reuse the shared error contract
    (stdout JSON + exit 2 with `--json`; stderr line + exit 2 in text mode).
18. `hash_mismatch_message` — save an Entry whose `sha256:` pin is wrong:
    message contains `expected` and `actual` digests.

## Benchmark (extension of `tests/ledger/benchmark.py`)

Documented extension, report-only: add `module_list_1000` and
`plugin_list_1000` measurements (1,000-Entry `list --json`, both runners)
to the JSON report — the roadmap requires the baseline to be *reported*, not
gated. Keep the existing thresholds (`--help` < 250 ms, 1,000-Entry `enter`
< 1 s) and the PASS/FAIL logic unchanged; the stage notes record the new
1,000-Entry `enter` median and its margin against the ≈ 0.94 s M0.5 reference
on the recorded machine, after the default mechanisms (shared single-pass
scan, no duplicate load/parse, measured micro-optimizations). If the margin
is still insufficient, the follow-up is the separate spec revision with a
parity corpus described under Performance — never an ad-hoc parser.

## Acceptance

### Unit/integration

```text
uv run --python 3.12 --with pytest python -m pytest -q        # all green (26 existing + new)
uv run --python 3.12 python tests/ledger/benchmark.py          # PASS + list baselines reported
for f in plugins/aitp-research-protocol/scripts/vendor/aitp/*.py; do grep -c '\S' "$f"; done
# per-module < 400; sum ≤ 1,300; M1a additions within 149–176
```

### Deterministic S1/S2 seed regression

- The seed-regression test (test 16) is the in-repo proof that M1a retrieval
  surfaces the S1/S2 decisive records (γ=7/4 exclusion, cutoff=4 void, next
  action) that sit outside `enter`'s top-20 window, with byte-identical
  workspaces before/after. It is deterministic fixture evidence, not a
  treatment-control score and not evidence from FROZEN v6 execution.
- On `cp -a` copies of `suite/seeds/S1` and `suite/seeds/S2`, the regression
  must preserve the declared counts, generated payloads, and source-tree byte
  identity before/after all reads. No participant, assessor, or gold-scoring
  run is required for this deterministic gate.

### Optional future treatment-control evidence

A paired treatment-control resumption evaluation may be run as optional future
evidence. It is not a required M1a gate and cannot retroactively satisfy the
original M0.6 evidence gaps or turn runtime changes into FROZEN v6 scores. If
pursued, it requires its own reviewed protocol, freeze/refreeze, and explicit
status synchronization.

### GW_librpa read acceptance (operator, in place, read-only)

```text
find .aitp -type f -print0 | sort -z | xargs -0 sha256sum > /tmp/m1a-before.txt
aitp list --json            # historical compatibility snapshot (2026-08-06): 60 Entries, warnings []
aitp list --kind result --json   # historical compatibility snapshot: 26
aitp enter --json           # historical compatibility snapshot: 41 active, 19 superseded, 1 unresolved active failure
aitp show <a superseded entry id>   # status: superseded; runs despite drifted local pins
find .aitp -type f -print0 | sort -z | xargs -0 sha256sum > /tmp/m1a-after.txt
diff /tmp/m1a-before.txt /tmp/m1a-after.txt   # must be empty
```

- The 60/41/19/26/1 values above are the historical compatibility snapshot
  dated 2026-08-06, not fixed current-count assertions. Current acceptance
  records dynamic counts as observed, retains the `invalid_timestamp` warning,
  checks read-only projections, and requires byte-identical `.aitp` maps before
  and after reads. The current 194-record snapshot is recorded in
  [`docs/m1a-stage-notes.md`](m1a-stage-notes.md); 194 is not a fixed baseline
  and is not treatment/advantage evidence. Historical deltas caused by
  recorded M0.6 bootstrap records (a `source` Entry per legacy corpus, a human
  `decision` Entry per bootstrap Note) are enumerated in the stage notes —
  never repaired, never hidden.
- The real store is compatibility evidence: no Entry, Note, or file under
  `.aitp` is written, moved, or touched by any M1a command; reads must
  survive stale local evidence (37 missing / 78 mismatched pins in the dated
  snapshot) without crashing and without weakening save-time pin discipline.
- A new Entry is written to the real project only for a genuine research
  event with the researcher's approval — never to satisfy acceptance.

### Gate evidence (roadmap §M1a gate, deterministic checklist)

- [x] The approved 2026-08-10 narrowed M0.6 review is recorded; M1a is now
      **done; deterministic gate passed**, with this spec as its pointer. The
      original M0.6 empirical gaps are not counted here.
- [x] Deterministic S1/S2 seed regression passes on fresh copies, including
      declared counts, generated payloads, and byte-identical source trees
      before/after all read commands.
- [x] Generated goldens are produced from this spec and match the public API
      contracts; no hand-edited payload is accepted.
- [x] Read-only Note validator acceptance passes: a malformed structural Note
      is omitted from `recent_notes`/`latest_working_note`, emits a warning, and
      increments `counts.malformed`; a structurally valid Note with missing or
      drifted `basis_refs` remains readable because the read path uses
      `validate_evidence=False`; before/after `.aitp` hashes are byte-identical
      with no lock, `atomic_write`, or `.aitp/local` state write, and save-path
      evidence validation is unchanged.
- [x] All 56 ledger and M1a tests pass.
- [x] GW_librpa read acceptance is read-only and its `.aitp` before/after file
      hash maps are byte-identical; stale local pins do not crash reads. The
      dynamic snapshot counts and the single historical invalid-timestamp
      warning are recorded in `docs/m1a-stage-notes.md`.
- [x] `--help` < 250 ms; 1,000-Entry `enter` and `list` < 1 s; cumulative
      runtime is 1,256 nonblank lines and every module is below 400.
- [ ] Optional paired treatment-control evidence is not required. If pursued,
      it is separately reviewed and frozen/refrozen and cannot be represented
      as FROZEN v6 evidence.

## Sync (Skill / docs / adapter / version)

- **Skill** (`plugins/aitp-research-protocol/skills/using-aitp/SKILL.md`,
  zero runtime lines, lands with the runtime): (1) dense-store retrieval —
  replace the rg-only retrieval guidance with: enumerate via
  `aitp list [--kind KIND] [--since DATE]`, open the exact record via
  `aitp show <entry-id>`, keep `rg` for full-text over `.aitp/topic/`;
  "there is no `aitp search`" stays true; (2) closeout discipline — one
  closeout per unfinished session, and a new closeout `supersedes` the
  previous closeout when replacing its handoff (append-only, old state stays
  visible); (3) Note trigger, verbatim from the design doc: "When four or
  more related durable Entries form a conclusion chain that a returning
  session would otherwise have to reconstruct, consider a working Note" —
  Skill judgment, never a runtime rule; (4) `legacy_derived` (body's first
  line exactly `> legacy-derived: recovery orientation only — not
  re-validated`) means orientation-only: recovery orientation, not
  re-validated science; (5) `latest_working_note` and
  `active_newer_than_latest_working_note` are structural signals, not
  semantic coverage. The `aitp` entrypoint Skill is unchanged.
- **Docs**: `docs/roadmap.md` records M1a as **done; deterministic gate passed**
  and points to `docs/m1a-stage-notes.md`; the implementer never edits stage
  status without the evidence record. `docs/design.md` §Commands documents
  `list` and `show`; `check` stays an absent, blocked M1b candidate.
  `docs/m1-read-write-balance.md` and the `using-aitp` Skill keep the post-M1a
  pause and selected-slice checklist.
- **Adapter**: `suite/adapters/cli.md` remains frozen v6 and is not changed by
  M1a implementation. A future reviewed protocol revision/refreeze may sync
  its "Read memory" appendix with `aitp list` / `aitp show` and the `enter` v2
  fields (`latest_working_note`, `active_newer_than_latest_working_note`,
  `legacy_derived`); `plain-files.md` remains unchanged until that same
  future refreeze.
- **Version**: the completed M1a implementation is synchronized at plugin
  version **0.2.0** in `kimi.plugin.json`, `.codex-plugin/plugin.json` (with its
  UTC timestamp suffix), `pyproject.toml`, and
  `scripts/vendor/aitp/__init__.py` (`aitp.__version__`). Schema identifiers
  (`aitp/enter-0.2`, `aitp/list-0.1`, `aitp/show-0.1`) version independently
  of the plugin version. No `aitp --version` flag is added. Do not modify the
  untracked `uv.lock` as part of version sync.

## Explicit prohibitions

- No changes to any existing v0.1 Entry or Note — golden store, seeds, or
  real corpora. Reads only.
- `list`, `show`, and `enter` v2 never write any file: no `atomic_write`,
  no store lock, no `.aitp/local` writes, no cursor (no
  `.aitp/local/last-enter`), no cache, no index. `enter` stays free of local
  cursor writes (no implicit last-enter cursor — rejected feature).
- No `record complete` command; no `enter --since` (rejected in this spec;
  incremental reads are explicit `list --since`).
- No new dependencies; no vector service, MCP server, hook, or daemon.
- No semantic ranking, summarization, or content judgment in Python;
  truncation is display-only and deterministic.
- No guessing for invalid stored timestamps (omit with a warning under
  `--since`; never coerce).
- No weakening of evidence validation, relation validation, template checks,
  or v0.1 compatibility. The read-only Note structural validator calls
  `validate_evidence=False`, takes no lock, and writes nothing; save semantics
  remain unchanged. The existing validator change is only the actionable
  `hash_mismatch` message.
- No M1b scope: no `based_on`, no `used_by`, no `resolution` closures, no
  `aitp check`, no schema `aitp/lite-entry-0.2`.
- Frozen suite inputs (seeds, scenarios, gold, adapters, `events/`, rubric,
  `FROZEN.md`) remain untouched by M1a implementation. `suite/adapters/cli.md`
  stays frozen; any future synchronization requires a separately reviewed
  protocol revision and refreeze, with the change recorded.
- No edits to existing test files except the documented `benchmark.py`
  extension and the deliberate golden regeneration; new tests land in
  `tests/ledger/test_query.py`.
- No custom frontmatter parser in M1a: no fast-path or strict-subset parser
  added by the implementation session, with or without `yaml.safe_load`
  fallback. A parser may land only through a separate spec revision that
  states its contract in full and adds a parity corpus (see Performance).
- Runtime changes live only in the canonical package
  (`plugins/aitp-research-protocol/scripts/vendor/aitp/`); no copied runtime
  is hand-maintained.

## Cut order if over budget

M1a ends at 1,300 nonblank lines; additions target 149–176. If the budget
does not fit, cut in this order:

1. cosmetic output features (text-row ellipsis styling, warning line
   formatting);
2. `--since` conveniences (date-only shorthand — require full ISO
   timestamps);
3. the `legacy-derived` tag in `list` text rows (JSON field stays).

Never cut: v0.1 compatibility, error-payload compatibility and exit codes,
closeout-first selection, Note ordering, `latest_working_note` and the null
age count, `legacy_derived` in JSON, deterministic ordering and truncation
bounds, the shared single-pass scan (the gate's performance item), read-only
projections, or the no-index rule. Do not expand scope to absorb slack
below 150.
