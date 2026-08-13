# M1c implementation spec — Topic workstreams (optional `workstreams` membership, single-slug scoped `enter`/`list`)

Status: **implementation specification; revised 2026-08-13; implementation in
progress; deterministic gate pending**. The natural-use feedback
[`feedback/2026-08-13-gw-librpa-workstreams-natural-use-feedback.md`](../../feedback/2026-08-13-gw-librpa-workstreams-natural-use-feedback.md)
records the observable facts behind this slice (one GW_librpa store sharing
source/build/provenance across three research lines — crpa,
magnetic-symmetry, qsgw-semiconductor — with no membership field in the
records). The deterministic gate has **not** been run and is **not claimed
passed**; gate evidence will be recorded in the stage-notes artifact
`docs/m1c-stage-notes.md`, created at gate time, not before. The spec text
below stands as the authoritative M1c contract from 2026-08-13.

## Independence boundary

M1c is a **separate stage slice, not part of the M1b A–H + Followup roster**
in `docs/m1b-spec.md` §0.1 and not a M1b Followup row: it changes no
disposition in that table, re-selects no deferred candidate (`lineage`,
structured prepare, pointer bundles, quick-run, `based_on`/`used_by`), and
grows no M1b scope. It is **not M3**: workstreams live inside a single Topic
store; the M3 cross-topic design option, its ≥ 3 real Topics and natural
cross-Topic failure gates, and the `catalog`/`link` absence are untouched.
M2/M4 dispositions are untouched. M1c's deterministic gate is its own; it
does not flip M2/M3/M4, does not reopen M1b, and does not modify any frozen
artifact (`docs/m1b-spec.md`, every existing file in `docs/archive/`,
`suite/`). The current CLI surface of M1a/M1b-R1 is unchanged where no
`--workstream` flag is used.

## Scope

One slice: an **optional `workstreams` list** on Entries and Notes, an
**explicit multi-membership** rule, a **repeatable prepare flag**, and
**single-slug scoped read projections** (`aitp/enter-0.3`, `aitp/list-0.2`)
that filter the existing global projections. Without the flag, every output
surface is byte-unchanged. No registry, no new command, no `check` change
beyond an additive field validation, no relations-scoping, no inference.

## Contract

### 1. `workstreams` field — optional, additive, v0.1 file schemas unchanged

Entries and Notes may carry an optional frontmatter list:

```yaml
workstreams:
  - crpa
  - magnetic-symmetry
```

- The persistent file schemas stay `aitp/lite-entry-0.1` and
  `aitp/lite-note-0.1`; `workstreams` is an **optional additive field**
  validated by the same `validate_entry`/`validate_note` paths. It does not
  introduce `aitp/lite-entry-0.2` (a frozen M1b candidate contract with
  different semantics) and does not touch `docs/m1b-spec.md`.
- **Unscoped legacy**: a record **without the field** is **unscoped** — it is
  valid and appears only in the unfiltered global view. A store with no
  `workstreams` anywhere behaves byte-identically to today. Unscoped records
  are **excluded from every `--workstream` scoped view**: scoped views are
  strictly exact membership, never an implicit "shared"/unscoped union. A
  cross-line common record explicitly lists all its workstreams.
- **Field presence requires a non-empty, no-duplicate list**: when the field
  is present, an empty list is **invalid** (an empty list is *not* unscoped
  legacy). Duplicate elements in a stored list are invalid.
- **Explicit multi-membership**: a record may list several workstreams; a
  record is in scope of a requested slug iff its list contains the slug.
  Membership is explicit in the record frontmatter and **never inferred** —
  not from summary text, paths, kinds, refs, or relations, and no derived
  `used_by`-style view. `shared` is an ordinary explicit slug like any other;
  there is no implicit shared status.
- **Slug grammar**: every element is a string matching the Topic slug rule
  `^[a-z0-9][a-z0-9-]{0,62}$` — the same rule as the Topic ID (`_safe_slug`),
  reused verbatim, no stricter grammar (trailing/doubled hyphens are allowed
  exactly as the Topic rule allows them; examples: `crpa`,
  `magnetic-symmetry`, `qsgw-semiconductor`).
- **Validation**: when the field is present, it must be a list of strings
  conforming to the grammar with no duplicates and at least one element. Any
  violation is the error code **`invalid_workstreams`** with message
  `invalid workstreams: <detail>` (detail: `not a list` / `empty list` /
  `empty element` / `invalid slug: <value>` / `duplicate workstream:
  <value>`), raised on the save path (exit 2, like all save validation) and
  reported by `check` as an error finding (exit 1) for the same record —
  **global, never scoped** (`check` has no scope flag; see §6).
- An absent field stays absent (no normalization writes `workstreams: []`).

### 2. Repeatable prepare flag

```text
aitp record prepare --kind KIND --authority LEVEL --created-by ID [--idempotency-key KEY] [--workstream SLUG]...
aitp note prepare --mode working|theory --title TITLE --created-by ID [--workstream SLUG]...
```

- `--workstream <slug>` is **repeatable** on prepare only; each occurrence
  appends to the prepared draft's `workstreams` list in flag order (a record
  may belong to several workstreams). With no flag, the draft has **no
  `workstreams` key** (byte-identical to today).
- **No silent dedup**: repeating the same slug (`--workstream crpa
  --workstream crpa`) is a **list duplicate** and raises
  `invalid_workstreams` (`duplicate workstream: crpa`, exit 2) **before any
  file is written** — no draft is created.
- An invalid slug at prepare time raises `invalid_workstreams` (exit 2)
  before any file is written.
- The prepare **success envelopes are unchanged**
  (`{"status":"prepared","id","path","save_command"}` / `{"status":
  "existing","path","idempotency_key"}`); the flag only seeds draft
  frontmatter. Save accepts, validates, and persists whatever the draft
  carries (§1).

### 3. Scoped `enter` — schema `aitp/enter-0.3`

```text
aitp enter [--recent N] [--workstream SLUG] [--cwd PATH] [--json]
```

- `--workstream` on `enter` accepts **exactly one slug** (not a repeatable
  union): a repeated `--workstream` is CLI misuse and the parser rejects it
  (exit 2, usage error). `enter_workspace(workstream=...)` likewise takes a
  single slug string.
- With `--workstream`, `enter --json` emits `"schema": "aitp/enter-0.3"`: the
  complete `aitp/enter-0.2` payload with exactly one additive top-level key
  `"workstream": "<slug>"` (singular). Without the flag, the payload is
  **byte-identical `aitp/enter-0.2`** (golden-tested).
- **Relation-before-filter**: the scan, the superseded set, and the resolved
  set are computed on the **whole store first**; membership filtering happens
  after. A cross-line resolver/superseder therefore still closes/replaces its
  target without reviving old records: an out-of-scope `resolves` removes the
  target failure from scoped `unresolved_failures`, and an entry superseded
  by an out-of-scope `supersedes` still reports `status: "superseded"` in
  scoped `list`.
- **Strictly scoped projections**: `recent_entries` (window of `--recent`
  over scoped active, same sort), `unresolved_failures` (scoped active
  failures not in the **global** resolved set), `recent_notes`,
  `latest_working_note` (latest scoped working Note; `null` when the scope
  has none), the Note age
  `counts.active_newer_than_latest_working_note` (computed over scoped
  active entries), and `next_action` (handoff) — the handoff is picked from
  the **scoped** active entries with the same closeout-first selection; a
  scope with no handoff-bearing in-scope active entry yields
  `{"status": "not_established", "source": null}`. **An out-of-scope handoff
  is never shown.**
- **Counts**: `counts.active`, `counts.superseded`, `counts.unresolved_
  failures`, `counts.omitted_active`, and `counts.active_newer_than_latest_
  working_note` are scoped; `counts.malformed` is **global** (scoping never
  masks malformed records). `memory_status` is derived from the global scan
  (malformed/valid counts) and stays global; `warnings` is **global** and
  byte-identical to the unscoped run on the same store — scope never changes
  validation warnings.
- A well-formed slug with no matching records is a valid scope (empty
  `recent_entries`, zero counts, `not_established` handoff) — never an error.

### 4. Scoped `list` — schema `aitp/list-0.2`

```text
aitp list [--kind KIND] [--since DATE] [--workstream SLUG] [--cwd PATH] [--json]
```

- `--workstream` on `list` accepts **exactly one slug** (not a repeatable
  union): a repeated `--workstream` is CLI misuse and the parser rejects it
  (exit 2, usage error). `list_workspace(workstream=...)` likewise takes a
  single slug string.
- With `--workstream`, `list --json` emits `"schema": "aitp/list-0.2"`: the
  complete `aitp/list-0.1` payload with exactly one additive top-level key
  `"workstream": "<slug>"` (singular). Without the flag, the payload is
  **byte-identical `aitp/list-0.1`** (golden-tested).
- The workstream predicate is an additional per-record filter applied in the
  existing selection loop (after kind/since checks) and is **strict exact
  membership**: only records whose list contains the slug are selected;
  unscoped records are excluded. Superseded status is computed from the
  **global** superseded set; `count` is the scoped entry count; `warnings`
  stays **global**.
- Slug validation on the flag: a slug not matching the grammar raises
  `invalid_workstreams` (exit 2, CLI misuse). A well-formed slug with no
  matching records is a valid scope (empty `entries`, `count` 0) — never an
  error.

### 5. Text renderer (human-facing only)

Scoped `enter` text runs (`--workstream` present) print exactly one
additional first line `workstream: <slug>`, then the existing compact
renderer over the scoped payload — the two frozen M1a safety lines and the
goal/handoff/warnings lines are never cut and render from the payload as
today (the `workstream:` line is **not printed** when unscoped, so the frozen
`enter.txt` golden stays valid). The text is human-facing only; Hakimi must
never parse it (machine output is the versioned JSON).

### 6. `check` — unchanged contract, additive field validation

`check` gets **no scope flag** and `aitp/check-report-0.1` is unchanged
(schema, exit 0/1/2, zero-write, deterministic `(path, code, message)`
ordering). The per-file structural step gains the §1 `workstreams` check:
an invalid field (including an empty list) is an error finding
`invalid_workstreams` with the same message as the save path. Validation
warnings remain global — `check` always scans the whole store.

### 7. `show` — unchanged

`aitp show` and `aitp/show-0.1` are unchanged (no scope flag); the exact
record's frontmatter (including `workstreams` when present) is already
returned in `frontmatter`.

### 8. No registry

There is no workstream registry: no new file, no `workstreams.toml`, no
workspace-level catalog, no `aitp workstream` command, no enumeration
command. Membership lives only in record frontmatter; enumerating distinct
slugs is `rg` (`rg '^  - ' .aitp/topic/` / reading frontmatter), never a
runtime feature.

## Budget and implementation map

Measured on HEAD `29c75e82` (2026-08-13): the canonical runtime is
**1,438 nonblank lines** (`grep -c '\S'` per module, summed; every module
< 400; `records.py` 322, `workspace.py` 335). M1c caps: **target ≤ 1,550**
(net ≤ +112), **hard cap ≤ 1,600** (net ≤ +162); every module stays below
400. Caps are ceilings, not targets; the implementation session reports its
own measurement at gate time.

Expected touch points (implementation economy is the implementer's choice,
subject to the caps):

| File | Change |
|---|---|
| `records.py` | `WORKSTREAM_RE` (Topic slug rule); `_validate_workstreams(frontmatter)` (shared Entry/Note rule, code `invalid_workstreams`, empty list invalid); call from `validate_entry`/`validate_note`; `prepare_entry`/`prepare_note` accept repeatable slugs, validate the raw list (duplicates rejected, no dedup), and seed `workstreams` |
| `query.py` | `_in_scope(frontmatter, workstream)` (strict exact membership; unscoped ⇒ False when scoped); `_validate_scope` (single slug); `list_workspace(..., workstream=None)` — scope predicate in the selection loop, `schema`/additive singular `workstream` key, global warnings/superseded |
| `state.py` | `enter_workspace(..., workstream=None)` — global scan/relations as today; strictly scoped projections including `next_action` (never an out-of-scope handoff); `schema`/additive singular `workstream` key |
| `cli.py` | repeatable `--workstream` on `record prepare`/`note prepare`; single-occurrence `--workstream` on `enter`/`list` (parser rejects repetition); slug validation (exit 2); renderer dispatch to enter-0.3/list-0.2; scoped `workstream:` text line |
| `diagnostics.py` | the per-file structural step also runs `_validate_workstreams`; finding code `invalid_workstreams`; no other change |
| `core.py` | export additions only |

No module may exceed 400 nonblank lines; if a touch point would overflow,
split the helper into the smallest natural module (e.g. the slug regex and
`_in_scope` in `query.py`), never by duplicating logic.

## Tests (new file `tests/ledger/test_workstreams.py`)

New tests only; existing test files are not modified. Use the existing
`run_cli` helper and golden fixtures; unscoped golden parity is asserted
against the existing `enter.json`/`list.json` goldens where applicable.
The implemented suite (16 tests):

1. `test_prepare_flag_seeds_draft` — `record prepare`/`note prepare` with
   repeated distinct `--workstream crpa --workstream magnetic-symmetry`
   produce drafts whose frontmatter `workstreams` is exactly `["crpa",
   "magnetic-symmetry"]` (flag order); without the flag the draft has no
   `workstreams` key; envelope keys unchanged.
2. `test_prepare_duplicate_slug_rejected_no_draft` — `--workstream crpa
   --workstream crpa` ⇒ `invalid_workstreams: duplicate workstream: crpa`,
   exit 2, **no draft written** (no silent dedup).
3. `test_prepare_flag_invalid_slug` — `--workstream "Bad Slug"` / `"a__b"` /
   `"UPPER"` / `""` / `"-lead"` ⇒ `invalid_workstreams`, exit 2, no draft
   written.
4. `test_save_valid_workstreams` — saving a draft with a valid `workstreams`
   list succeeds; the canonical file keeps the field; a Topic-rule-allowed
   shape (`a-`) saves unchanged.
5. `test_save_invalid_workstreams` — not-a-list, **empty list**, empty
   element, invalid slug, duplicate element ⇒ `invalid_workstreams` with the
   exact message, exit 2, on both Entry and Note save paths.
6. `test_unscoped_legacy_valid_and_no_flag_schema_unchanged` — records
   without `workstreams` save and read exactly as today; a store with no
   workstreams anywhere: `enter --json` byte-identical to the golden,
   `list --json` byte-identical to the golden, `enter` text byte-identical
   to the golden `enter.txt` (no flag ⇒ old schemas unchanged).
7. `test_scoped_enter_schema_and_post_filter` — `enter --workstream crpa
   --json` ⇒ `schema "aitp/enter-0.3"`, additive top-level singular
   `"workstream": "crpa"` (no `workstreams` key); unscoped run on the same
   store ⇒ `schema "aitp/enter-0.2"` and no `workstream` key; scoped
   `recent_entries`/`unresolved_failures`/`recent_notes` contain only
   in-scope records — **unscoped records never appear in a scoped view**; a
   multi-slug record appears in each of its scopes; a scope with no records
   is empty but valid.
8. `test_scoped_enter_counts_global_malformed_and_memory` — scoped
   `counts.active`/`superseded`/`unresolved_failures`/`omitted_active`/
   `active_newer_than_latest_working_note`; global `counts.malformed`,
   `memory_status`, and `warnings` identical to the unscoped run.
9. `test_scoped_enter_handoff_scoped` — `next_action` is picked from the
   scoped active entries (closeout-first, same object shape); an out-of-scope
   handoff is **never** shown; a scope with no handoff-bearing in-scope
   active entry ⇒ `{"status": "not_established", "source": null}`.
10. `test_scoped_list_schema_filter_and_composition` — `list --workstream
    qsgw-semiconductor --json` ⇒ `aitp/list-0.2`, additive singular
    `workstream`, strictly scoped `entries` and `count` (unscoped excluded),
    global `warnings`; kind/since filters compose with the scope.
11. `test_scoped_superseded_global` — an out-of-scope resolver removes the
    target from scoped `unresolved_failures`; an entry superseded by an
    out-of-scope entry still reports `status: "superseded"` in scoped
    `list` (relation-before-filter).
12. `test_read_flag_not_repeatable` — a second `--workstream` on
    `enter`/`list` is rejected by the parser (exit 2, usage error, "may
    only be given once"); the API rejects a non-string (old-style list)
    scope with `invalid_workstreams: exactly one slug required`.
13. `test_scoped_text_line` — scoped `enter` text prints exactly one leading
    `workstream: <slug>` line and the two frozen safety lines; unscoped text
    has no `workstream:` line and matches the golden `enter.txt`.
14. `test_check_workstreams_finding_and_global` — a store with an invalid
    `workstreams` field: `check` reports exactly one `invalid_workstreams`
    error finding, exit 1, `aitp/check-report-0.1` schema unchanged; the
    same record still fails save with the same code/message; `check
    --workstream crpa` is CLI misuse (exit 2); `check` output is identical
    before/after scoped runs (global, no scope flag).
15. `test_cli_misuse_bad_slug` — `enter --workstream "Bad"` / `list
    --workstream "Bad"` ⇒ `invalid_workstreams`, exit 2, JSON error
    envelope.
16. `test_scoped_read_only_byte_identity_and_determinism` — scoped
    `enter`/`list` runs leave the `.aitp` tree sha256-identical (no lock,
    no cache, no index, no registry file); scoped payloads are deterministic
    (two runs byte-identical); `show` returns `workstreams` in frontmatter.

Gate checklist (recorded in `docs/m1c-stage-notes.md` at gate time): the
tests above plus the **unchanged** ledger suite (all existing tests), the
existing benchmark thresholds unchanged (`--help` < 250 ms; 1,000-Entry
`enter`/`list` < 1 s), plugin tests, distribution tests, per-module < 400 and
cumulative ≤ 1,550 (target) / ≤ 1,600 (cap) line counts, version sync 0.4.0
across all four version surfaces, and the real-store acceptance below.

## Real-store acceptance (GW_librpa, operator, in place, read-only)

The real store is compatibility evidence, not a test namespace. Uses the
exact bundled launcher with the Skill's interpreter probe order. On the live
store: (a) unscoped `enter --json`/`list --json` are byte-identical before
and after the change set (payloads against the pre-change recorded outputs);
(b) scoped runs with `--workstream crpa`, `--workstream magnetic-symmetry`,
and `--workstream qsgw-semiconductor` render `aitp/enter-0.3`/`aitp/list-0.2`
with internally consistent counts and lists; (c) `find .aitp -type f -print0
| sort -z | xargs -0 sha256sum` before/after diff is **empty**. No record is
written; observed exits and payloads are recorded verbatim in the stage
notes.

## Version and docs sync (same change)

- **Version**: the plugin version is **0.4.0** in `kimi.plugin.json`,
  `.codex-plugin/plugin.json` (with its current UTC timestamp suffix
  `+codex.<YYYYMMDDHHMMSS>`), `pyproject.toml`, and
  `scripts/vendor/aitp/__init__.py` (`aitp.__version__`).
  `aitp/enter-0.3` and `aitp/list-0.2` version independently of the plugin;
  `aitp/enter-0.2`, `aitp/list-0.1`, `aitp/show-0.1`,
  `aitp/check-report-0.1`, and the `lite-*` file schemas are unchanged. Do
  not modify the untracked `uv.lock`.
- **Docs**: the same change updates all status surfaces with **M1c
  implementation in progress; deterministic gate pending** (no gate claim):
  `AGENTS.md`, `README.md` (stage table + current checkpoint + current
  state + CLI surface), `docs/design.md` (commands + schema list), `docs/roadmap.md`
  (stage table + M1c section + current state), the `docs/hakimi/` handoff
  (README amendment + phased plan + compatibility-matrix rows and red
  lines), the `using-aitp` Skill (teach only the M1c surface with the
  in-progress status), and the new stage-notes artifact
  `docs/m1c-stage-notes.md` (gate evidence, **created at gate time, not
  before**).
- **Frozen**: `docs/m1b-spec.md` and every existing file in `docs/archive/`
  are not modified; `suite/` stays frozen and unchanged; M1c has no suite
  deliverable.

## Cut order if over budget

The cap is 1,600 cumulative nonblank lines (hard) with target 1,550. If the
implementation session's draft still exceeds the cap, cut in this order —
before any implementation is accepted:

1. The scoped `enter` text `workstream:` line (residual cosmetic; JSON
   untouched).
2. `--workstream` on `enter` (drop `aitp/enter-0.3`; `aitp/list-0.2` and the
   prepare flags remain).
3. `--workstream` on `list` (drop `aitp/list-0.2`; prepare flags remain).

Never cut: the `workstreams` field contract (§1), unscoped-legacy semantics,
explicit multi-membership, the repeatable prepare flags, relation-before-
filter (global superseded/resolved sets), strictly scoped projections
(including `next_action`), global warnings/malformed/check, no-registry,
byte-identical old schemas without the flag, or v0.1 compatibility. Do not
expand scope to absorb slack.

## Explicit prohibitions

- No registry, catalog, enumeration, or new `aitp workstream` command; no
  new canonical or local file.
- No inference of membership (text, path, kind, refs, relations); no
  derived views; no implicit "shared" scope — scoped views are strict exact
  membership and unscoped records never appear in them.
- No relations-scoping at save or in `check`; `check` has no scope flag and
  `aitp/check-report-0.1` is unchanged. The superseded/resolved sets are
  always computed on the whole store before membership filtering.
- No repeatable `--workstream` on `enter`/`list` (single slug only; a
  repeated flag is parser-rejected CLI misuse); no out-of-scope handoff.
- `show`, `record save`/`note save` envelopes, and all unversioned
  envelopes are unchanged; the prepare flag seeds drafts only; repeated
  identical prepare slugs are rejected, never silently deduped.
- No flag ⇒ byte-identical old schemas (`aitp/enter-0.2`, `aitp/list-0.1`);
  `enter-0.3`/`list-0.2` appear only when the flag is present.
- No new dependencies; no MCP/daemon/hook/vector service; no index, cache,
  or persistent state.
- No semantic judgment in Python: scoping is a deterministic per-record
  predicate; nothing is inferred, ranked, or interpreted.
- Frozen inputs untouched: `docs/m1b-spec.md`, all existing `docs/archive/`
  files, `suite/` (`FROZEN.md` and everything under `suite/`), and the
  untracked `feedback/2026-08-13-gw-librpa-m1b-r1-natural-use-feedback.md`,
  `ref/`, and `uv.lock`.
