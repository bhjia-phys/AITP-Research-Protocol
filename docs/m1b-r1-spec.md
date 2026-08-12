# M1b-R1 implementation spec — read-side slice (`check`, compact `enter` text)

Status: **implementation specification; implemented; deterministic gate
passed (2026-08-12)**. Frozen 2026-08-12 by the reviewed freeze
revision in [`docs/m1b-adjudication.md`](m1b-adjudication.md) and
`docs/m1b-spec.md` §0.1, separately reviewed and green-lit, implemented,
and gated; the auditable gate evidence is recorded in
[`docs/m1b-r1-stage-notes.md`](m1b-r1-stage-notes.md). The spec text below
stands as frozen. The amended gate-time re-measurement of the actual
implementation is **1,423 nonblank lines total** (`diagnostics.py` 101,
`records.py` 327 — above the author-reported prototype's 1,413/94/324),
still within the 1,425 target and the 1,450 hard cap; the pre-amendment
gate re-measurement (1,421, `diagnostics.py` 99) and the prototype figures
in §Implementation map remain historical evidence, superseded by the
amended measurement for current gate purposes.

Scope: this document is the complete implementation-level spec for the
M1b-R1 read-side slice: (1) a compact `enter` **text renderer only**
(`aitp/enter-0.2` JSON byte-unchanged) that restores the M1a safety signals
(shown/active/omitted, latest working Note and age) in two minimal frozen
lines, and (2) `aitp check` (schema `aitp/check-report-0.1`, v0.1 Entry/Note
contracts only, zero-write) with the no-crash error mappings frozen below.
The researcher's Followup-2 (`aitp lineage`, schema `aitp/lineage-0.1`) was
selected in R1 at the freeze revision but was **re-deferred at the 2026-08-12
budget reconciliation** (with lineage the measured prototype exceeds the
1,425 target and leaves only ~5 lines of the 1,450 hard cap; without it the
slice lands at 1,413 with real margin) — the deferral is recorded in
`docs/m1b-adjudication.md` §Budget reconciliation and `docs/m1b-spec.md`
§0.1 Followup roster; no lineage code is specified here. Everything else in
the M1b candidate inventory (persisted `based_on`, derived `used_by`,
schema `aitp/lite-entry-0.2`, pointer bundles, quick-run, typed open items,
Note-supersedes target rules) is **not in R1** and produces no
implementation work.

## Gate prerequisite

- The natural-use pause is complete (two ordinary sessions, see
  `docs/m1b-adjudication.md` §2).
- Fixed caps never adjust: cumulative canonical runtime ≤ 1,450 nonblank
  lines; every module < 400; current actual = 1,256 → headroom = **194**.
- R1 is read-only: no save-path behavior change beyond the explicitly
  authorized ref-validator split and the absent-git crash fix (§Save
  compatibility). Save semantics, first-failure order, and the unversioned
  success envelopes are frozen unchanged.
- This spec must be separately reviewed and green-lit before
  implementation; its own deterministic gate evidence follows at
  implementation time and is recorded in the stage-notes artifact
  `docs/m1b-r1-stage-notes.md` (created at gate time, not before). **Status:
  the review/green-light was granted, the implementation landed, and the
  gate passed on 2026-08-12 — see `docs/m1b-r1-stage-notes.md`.**

## CLI grammar and help

```text
aitp enter [--recent N] [--cwd PATH] [--json]     # text rendering only; JSON unchanged
aitp check [--cwd PATH] [--json]
```

New help string (one line; `--help` stays < 250 ms):

- `check`: "validate the whole store read-only and report findings (exit 0 clean, 1 findings, 2 cannot run)"

`--cwd` (default `.`) and `--json` behave exactly as on every existing
command. No other command or flag is added by R1.

## `aitp check` — frozen contract (v0.1 only)

### Read-only scope

`check` writes nothing: no lock file (never takes `store_lock`), no cache,
no index, no repair, no migration, no scratch, no new canonical files, no
`--fix` flag now or later. A test asserts the `.aitp` tree is byte-identical
before and after a check run.

### Exit codes

- `0` — clean: zero findings.
- `1` — findings: at least one error or warning reported.
- `2` — could not run: not a workspace, unreadable/invalid store metadata
  (`not_initialized`, `malformed_store`, `invalid_root`), or CLI misuse
  (argparse). Record-content problems are never exit 2 — they are findings
  (exit 1).

### No-crash mappings (frozen; no path may raise a traceback)

| Condition | Code | Grade | Exit |
|---|---|---|---|
| Canonical record or `TOPIC.md` unreadable or invalid UTF-8 (OSError / UnicodeDecodeError at parse) | `unreadable_record` | error finding | 1 |
| `STORE.toml` unreadable or invalid UTF-8 | `malformed_store` (message: `store metadata is unreadable: <path>: <reason>`) | could-not-run (AITPError) | 2 |
| Ref target exists but is not a file (e.g. directory), or its bytes cannot be read | `unreadable_ref` (message: `reference target is not a file: <target>` / `reference target is unreadable: <target>: <reason>`) | error finding (save and check share the code) | 1 (check) / 2 (save) |
| `git:` pin, external target (http/https/arxiv/doi) | `invalid_git_ref` | error | 1 (check) / 2 (save) |
| `git:` pin, local target, Git environment unavailable (no `git` binary, or workspace not inside a Git work tree) | `invalid_git_ref` | **warning** (cannot verify) | 1 |
| `git:` pin, local target, Git available, commit lacks the target | `invalid_git_ref` | error | 1 (check) / 2 (save) |
| Any other unexpected per-file exception | `invalid_schema` finding (belt-and-braces catch, message `{path}: {exc}`) | error finding | 1 |
| Non-string `created_at` (structural) / unparseable string `created_at` (legacy) | `invalid_timestamp` | error (structural) / warning (legacy) | 1 |

Save-path behavior for the shared codes is unchanged in code/message/order:
`validate_refs` raises the first failure in stored ref order and the save
envelopes are untouched. The R1 changes to `records.py`/`md.py`/`workspace.py`
are limited to the documented split and guards; the absent-git case
(previously an uncaught `FileNotFoundError` crash at save) is now an explicit
authorization (§Save compatibility).

### Per-file rule (entries and Notes; frozen order)

Each canonical file is processed exactly once per invocation, sorted by
canonical filename, in this order; the first failing step excludes the file
from the remaining steps:

1. **parse** — `parse_markdown`; failure ⇒ error finding with its code
   (`unreadable_record`, `malformed_record`).
2. **structure** — `validate_entry(validate_evidence=False, topic_id)` /
   `validate_note(validate_evidence=False, topic_id)`; first failure ⇒ error
   finding with its code (`missing_field`, `invalid_schema`, `invalid_id`,
   `topic_mismatch`, `invalid_timestamp` (non-string), `invalid_type`,
   `invalid_kind`, `invalid_authority`, `missing_summary`,
   `invalid_limitations`, `missing_limitations`, `missing_refs`,
   `invalid_refs`, `invalid_ref`, `invalid_relation`,
   `invalid_idempotency_key`, `unfilled_template`, `empty_section`).
3. **duplicate** — the ID already seen ⇒ error finding `duplicate_id`,
   message exactly `duplicate Entry ID: <id>` / `duplicate Note ID: <id>`;
   the file is excluded from steps 4–6. The **first structurally valid file
   in sorted canonical filename order wins** the ID; a later file with the
   same ID is the duplicate, even when the earlier file failed structure.
4. **timestamp warning** — `_stored_time(created_at)` is `None` ⇒ warning
   finding `invalid_timestamp`, message `unparseable created_at: <raw>`
   (legacy records; never crashes; never excludes the file from the counts).
5. **relations** (Entries only) — `_validate_relations` for `resolves`,
   then `supersedes`; first failure per field ⇒ error finding
   (`missing_relation`, `invalid_relation`, `invalid_supersession`).
6. **refs** — graded evidence per stored ref, in stored index order: each
   `(code, message, grade)` from `_verify_refs(root, refs)` ⇒ one finding
   (pin failures are errors exactly as on the save path; only the
   git-environment-unavailable case is a warning). For Notes, an empty
   `basis_refs` is first reported as error `missing_refs` (message `Note
   requires nonempty basis_refs`), else the graded refs.

`entry_map` for relation checks is built once from the same parse pass
(parse-only, last-wins per ID — identical semantics to `records._entry_map`),
so no file is parsed twice and relations never re-read the store.

### Counts

`counts.entries` = the number of canonical Entry files under
`.aitp/topic/entries/` matching `entry-*.md`, each file counted exactly
once — **not** reduced by structural failure or by an invalid timestamp.
`counts.notes` likewise for `note-*.md` under `.aitp/topic/notes/`.
`counts.errors`/`counts.warnings` = findings by level.

### TOPIC goal

`TOPIC.md` parse failure ⇒ error finding with its code (path
`.aitp/topic/TOPIC.md`; invalid UTF-8 ⇒ `unreadable_record` per the
mapping above). Otherwise `goal = _section_content(body, "Research Goal").strip()`;
empty or exactly `Not established yet` ⇒ **warning** finding
`empty_topic_goal`, path `.aitp/topic/TOPIC.md`, message `Research Goal is
not established`. This is the same rule the `enter` text renderer applies to
the normalized payload goal text (below): empty, missing, and literal
placeholder all report `not_established`.

### Report — schema `aitp/check-report-0.1`

```json
{
  "schema": "aitp/check-report-0.1",
  "status": "clean" | "findings",
  "root": "<absolute path>",
  "counts": {"entries": 7, "notes": 2, "errors": 0, "warnings": 1},
  "findings": [
    {"level": "warning", "code": "empty_topic_goal",
     "path": ".aitp/topic/TOPIC.md",
     "message": "Research Goal is not established"}
  ]
}
```

- Findings sort deterministically by **`(path, code, message)`** — the
  message is the tie-breaker — and the report carries no volatile fields
  (no wall-clock timestamp), so its bytes are golden-testable. Two runs on
  the same store produce byte-identical reports.
- `findings` is empty and `counts.errors`/`warnings` are 0 when
  `status` is `clean`.
- Text mode prints one line per finding to **stdout**
  (`error[<code>]: <path>: <message>` / `warning[<code>]: <path>:
  <message>`) followed by exactly one summary line:
  `check: <errors> error(s), <warnings> warning(s)`; `--json` emits the
  payload above.

### Grading principle

Reused verbatim from `docs/m1b-spec.md` §7.4, applied to v0.1 contracts
only: a pin that fails verification makes the record invalid as written and
is an **error** (`missing_ref`, `hash_mismatch`, `unreadable_ref`,
`invalid_run_ref`, `invalid_git_ref`, `invalid_ref_pin`,
`invalid_retrieved_ref`, `invalid_version_ref`, `ref_escape`);
`invalid_git_ref` is a **warning** only when the Git environment is
unavailable and a local pin therefore cannot be verified. `invalid_timestamp`
(legacy) and `empty_topic_goal` are warnings. All other failures above are
errors. Warnings never block; `check` grades without changing the save path.

## Compact `enter` text renderer (JSON unchanged)

`enter`'s text rendering is replaced by the exact format below. The
renderer is a **pure function of the existing `aitp/enter-0.2` payload**:
no extra store reads, no `state.py` change, `--json` output
byte-identical.

```text
topic: <id> — <title>
memory_status: <available|partial|not_established>
goal_status: not_established                  # or: goal: <goal text truncated to 120>
recent_entries: <shown> of <active> active (<omitted> omitted)
  <created_at> <id> <kind> <summary truncated to 110>
unresolved_failures: <count>
next_action: <text truncated to 110> [<entry_id> @ <created_at> <authority>]
next_action: not_established                  # only when no handoff is established
handoff_status: review                        # only under the condition below
recent_notes: <shown>; latest_working_note: <id @ time|(none)>; active_newer: <n|unknown>
warnings: <count> (run "aitp check" for details)   # only when warnings are non-empty
```

Frozen rules:

- **Two minimal M1a safety lines, frozen and never cut** (they restore the
  M1a projection-safety signals the earlier draft dropped):
  - `recent_entries: <shown> of <active> active (<omitted> omitted)` —
    `shown` = `len(recent_entries)`, `active` = `counts.active`,
    `omitted` = `counts.omitted_active`. One line, followed by one
    truncated summary line per shown entry.
  - `recent_notes: <shown>; latest_working_note: <id @ time|(none)>;
    active_newer: <n|unknown>` — `shown` = `len(recent_notes)`;
    `latest_working_note` from `payload.latest_working_note`
    (`<id> @ <created_at>`, or `(none)`); `active_newer` =
    `counts.active_newer_than_latest_working_note` with `unknown` when the
    payload value is `null`. One line.
- Truncation reuses `query._truncate` (collapse whitespace, strip, at most
  N chars plus `…` when longer): summaries 110, goal 120.
- **Goal rule**: the renderer tests the **normalized payload text**
  (`payload.topic.goal.text`). `state.py` already normalizes an empty or
  missing Research Goal section to the exact placeholder string
  `Not established yet`, so a single exact match against that string covers
  all three cases — empty section, missing section, and literal
  placeholder — and prints `goal_status: not_established` in place of the
  `goal:` line. Any other value prints `goal: <text>`.
- **Handoff rule**: `handoff_status: review` appears **only** when all of:
  `next_action` has a non-empty `entry_id`; `_stored_time(
  next_action.created_at)` parses; and at least one `unresolved_failures`
  item's `created_at` parses and is strictly greater than the handoff's.
  This is a factual structural prompt — it does not change `next_action`,
  does not claim semantic staleness, and is not a restored roster-H
  runtime.
- The warnings line prints only the count and the pointer to `aitp check`;
  the JSON payload keeps the complete `warnings` list. There is **no
  persistent suppression**: no config file, no cursor, no state.
- Removed from text (JSON keeps everything): `refs`/`limitations` blobs,
  per-failure detail lines, per-Note detail lines, and `schema`/`root`.
  Empty sections print their count line only.

## Save compatibility (frozen)

- **Ref-validator split**: `validate_refs` becomes a thin raise-first
  wrapper over `_verify_refs`; save validation order is the stored ref
  order (**ref index first-failure**) and codes/messages are byte-identical
  to today. The unversioned success envelopes (`{"status":"saved","path"}`,
  `{"status":"already_saved","path"}`, prepare shapes) are unchanged — R1
  adds no key to any envelope.
- **Explicitly authorized absent-git fix**: today, saving a record with a
  `git:` pin on a machine without a `git` binary propagates an uncaught
  `FileNotFoundError` (traceback). R1 explicitly authorizes fixing this:
  the split raises the same `invalid_git_ref` error with the same message
  via the normal error path (exit 2). This is the only save-path behavior
  change and it is authorized here.
- **`unreadable_ref`** is a new shared code for both paths: a `sha256:` ref
  whose target exists but is not a file, or whose bytes cannot be read, is
  rejected at save and reported as an error finding by `check`.
- `_validate_relations` gains an optional parse-only `entries` map
  parameter; the save path omits it and behaves exactly as today.

## Implementation map (files/functions; line budget)

Budget: actual M1a total is **1,256** nonblank lines (`grep -c '\S'` per
module, summed). Hard cap **1,450** (≤ 194 net); target 1,425 (≤ 169 net);
every module stays below 400.

**Author-reported prototype measurement (2026-08-12) — NOT gate evidence.**
A prototype of this spec was implemented outside the repository
(`/tmp/r1-scratch`, throwaway) to validate feasibility. The following is an
auditable record of that measurement; it is author-reported development
evidence, not a gate result, and the implementation session must reproduce
it independently:

- Prototype diff vs. the canonical baseline: 373 diff lines, SHA-256
  `ab26b7dabc00f38257cbd571d6334847b30dab45864f2f1f26d994fe9e97a461`.
  Procedure (deterministic, regenerable at gate time): concatenate the
  sorted `*.py` files of the canonical `vendor/aitp/` directory and of the
  prototype directory, `diff -u --label=baseline --label=prototype` the two
  concatenations, and SHA-256 the diff. Fixed labels are required — an
  unlabeled diff embeds volatile `/dev/fd/N` paths and wall-clock
  timestamps in its header lines and is not reproducible. `__init__.py`/
  `__main__.py` are identical on both sides and produce no hunks.
- Per-file SHA-256 of the six changed prototype modules (stable,
  reproducible): `cli.py`
  `c32cf44103d7baf0242461dff36a8523df2ab20b5a0fbb6b87e1a7ba0dad3732`;
  `core.py`
  `c9cab1f688bf645be5ee1c60232860928b556d8d3d167d64bce497b84118515e`;
  `diagnostics.py`
  `b26e0271e0ba882fb943d07196d81a0b410efc98dd95b8e2845da4aa2b30fb56`;
  `md.py`
  `8d1db880d03b7f2943f85f08fe19d62e1871f0aee91454f88931dd9b12c895e0`;
  `records.py`
  `389a7cd2b0e3eb8a632155be6b01f9dfb7a852ada3fbf3018776069c83ee6180`;
  `workspace.py`
  `fdeefce92a1d8b294e92da5df68b5a768574ec15572e1b32476d945812b51ce4`.
- Measured nonblank lines: **1,413 total (net +157)** — within the 1,425
  target and the 1,450 hard cap (37-line margin to the cap).
- Per-module: `cli.py` 189, `core.py` 28, `diagnostics.py` 94, `md.py` 63,
  `notes.py` 143, `query.py` 146, `records.py` 324, `state.py` 106,
  `workspace.py` 316 — all below 400.
- Test transcript: all **56 unchanged ledger tests passed** against the
  prototype (`pytest: 56 passed`), confirming the save-path refactor and
  the new modules do not regress the shipped contracts.
- Contract spot-checks run against the prototype (golden store and
  synthetic fixtures): `check` on the golden store reports exactly the
  `empty_topic_goal` warning with exit 1; invalid UTF-8 record ⇒
  `unreadable_record` finding, exit 1, no traceback; invalid UTF-8
  `STORE.toml` ⇒ `malformed_store`, exit 2; directory/unreadable ref target
  ⇒ `unreadable_ref` error on both paths; external git target ⇒ error,
  local git pin in a non-Git work tree ⇒ warning; `enter` text prints both
  frozen safety lines; `.aitp` byte-identity holds.
- The measurement forced one scope decision: with `aitp lineage` included,
  the same prototype measured 1,445 (5 lines of cap margin, above the
  1,425 target), so per the budget rule the slice **re-deferred lineage**
  (see `docs/m1b-adjudication.md` §Budget reconciliation) instead of
  cutting check semantics or M1a safety signals.

| File | Change | Prototype nonblank |
|---|---|---|
| `records.py` | `_git_env(root)`; `_verify_refs(root, refs) -> list[(code, message, grade)]` — the **one** verification code path; `validate_refs` raise-first wrapper; `unreadable_ref` for non-file/unreadable `sha256:` targets; `_validate_relations(..., entries=None)` optional parse-only map | 311 → **324** (+13) |
| `diagnostics.py` (new) | `_parse_all`, `_grade_records` (shared Entry/Note grading with no-traceback guards), `check_workspace`, `_finding` | **94** |
| `cli.py` | `check` subparser + help; `_emit_check`, `_emit_enter`, `_handoff_review`; dispatch, renderer map, check exit-1 mapping | 145 → **189** (+44) |
| `md.py` | `parse_markdown` read guard widened to `(OSError, UnicodeDecodeError)` ⇒ `unreadable_record` | 63 → **63** (+0) |
| `workspace.py` | `load_store` read guard: unreadable/invalid UTF-8 `STORE.toml` ⇒ `malformed_store` (explicit message) | 312 → **316** (+4) |
| `core.py` | import + `__all__` for `check_workspace` | 26 → **28** (+2) |
| `state.py`, `query.py`, `notes.py`, `__init__.py`, `__main__.py` | unchanged | 0 |

Total (prototype): **1,413** (net +157). Per-module maximum: `records.py`
324 — all modules stay below 400 nonblank lines.

Key function contracts:

- `records._git_env(root) -> bool` — true iff `git -C <root>
  rev-parse --is-inside-work-tree` exits 0; `OSError` (no `git` binary) ⇒
  false.
- `records._verify_refs(root, refs) -> list[tuple[str, str, str]]` —
  collects `(code, message, grade)` for every pin in stored ref order,
  applying exactly today's scheme rules and messages. The `git` branch:
  external target ⇒ error; local + Git environment unavailable ⇒ warning;
  local + environment available + commit lacks target ⇒ error — all with
  the same code `invalid_git_ref` and message `Git ref does not contain
  target: {target}@{value}`.
- `records.validate_refs(root, refs)` — `for code, message, _ in
  _verify_refs(root, refs): raise AITPError(code, message)` — ref-index
  first-failure, same codes/messages as today.
- `records._validate_relations(root, frontmatter, field, entry_id,
  entries=None)` — `entries` defaults to `_entry_map(root)`; save path
  unchanged; `check` passes the in-memory parse-only map.
- `md.parse_markdown` / `workspace.load_store` — read guards per the
  no-crash mapping; no other change.
- `diagnostics.check_workspace(cwd) -> dict` — per-file rule of §check
  (parse → structure → duplicate → timestamp → relations → refs);
  `_parse_all` parses each canonical file once; `_grade_records` applies the
  shared grading and the belt-and-braces `invalid_schema` catch; `entry_map`
  from the single parse pass; findings sorted by `(path, code, message)`;
  payload per `aitp/check-report-0.1`.
- `cli._emit_enter(payload, as_json)` — exact compact text of §enter text,
  including both frozen safety lines; `cli._handoff_review(payload) -> bool`
  — the §handoff condition over payload fields only.
- `cli` exit mapping — after rendering, `check` returns 1 when
  `payload["status"] == "findings"`, else 0; `AITPError` and argparse stay
  exit 2.

## Golden fixtures (deliberate regeneration)

Generated from the public API exactly as `tests/ledger/test_golden.py`
documents; `root` normalized to `<golden-store>`; no hand-edited payloads:

- `check.json` — `check_workspace` on the golden store: `status`
  `"findings"`; `counts {entries: 7, notes: 2, errors: 0, warnings: 1}`;
  the single finding is the `empty_topic_goal` warning on
  `.aitp/topic/TOPIC.md` (the golden Topic goal is exactly the
  placeholder). All golden pins are valid `sha256`, relations resolve, and
  timestamps parse — nothing else can fire.
- `enter.txt` — the compact text renderer on the golden store: topic
  `nio — Magnetic NiO`; `memory_status: available`;
  `goal_status: not_established`; `recent_entries: 6 of 6 active (0
  omitted)` (the superseded `entry-4444…` is not in the active recent
  window); `unresolved_failures: 1`; `next_action: … [entry-7777… @ …
  human]`; **no** `handoff_status` line (the unresolved failure is older
  than the handoff); `recent_notes: 2; latest_working_note: note-1111… @
  2026-07-06T12:00:00.000001Z; active_newer: 0`; no warnings line.

`test_golden.py` itself stays untouched; the new goldens land under
`tests/ledger/fixtures/golden/` with new tests that read them.

## Tests (new file `tests/ledger/test_diagnostics.py`)

CLI/exit-code contracts via the existing `run_cli` helper; API payloads
test_golden-style. Do not modify existing test files.

1. `check_golden_matches` — `check_workspace` on a golden-store copy
   equals `golden("check.json")`; CLI exit 1 (findings).
2. `check_clean_exit_zero` — a fresh `init` + filled TOPIC goal store:
   `status "clean"`, exit 0, findings `[]`.
3. `check_cannot_run` — non-store dir and a dir without STORE.toml:
   `invalid_root`/`not_initialized` exit 2; JSON error payload shape;
   `malformed_store` exit 2 for an unreadable/invalid-UTF-8 `STORE.toml`
   (exact message).
4. `check_malformed_error` — malformed YAML / missing frontmatter file ⇒
   error finding with the parse code; exit 1.
5. `check_utf8_unreadable` — a record and a `TOPIC.md` with invalid UTF-8
   bytes ⇒ `unreadable_record` findings, exit 1, no traceback on stdout or
   stderr.
6. `check_structural_error` — missing required field, bad kind, empty
   summary, unfilled template, empty section ⇒ error findings with their
   codes; exit 1.
7. `check_duplicate_error` — two files with one ID ⇒ exactly one
   `duplicate_id` error on the second (sorted canonical filename) file with
   the exact message `duplicate Entry ID: <id>`; the first structurally
   valid file wins; a duplicate Note uses `duplicate Note ID: <id>`; the
   duplicate file produces no other findings.
8. `check_counts_per_file` — a store with a structurally invalid file and
   an invalid-timestamp file: `counts.entries` counts every canonical
   Entry file exactly once (not reduced by invalidity or bad timestamp);
   `counts.notes` likewise.
9. `check_pin_matrix` — five pin schemes and their failures: `sha256`
   missing target ⇒ `missing_ref`; `sha256` directory target ⇒
   `unreadable_ref`; `sha256` unreadable file ⇒ `unreadable_ref`; `sha256`
   wrong digest ⇒ `hash_mismatch`; `git` external target ⇒
   `invalid_git_ref` error; `git` local in a non-Git work tree ⇒
   `invalid_git_ref` **warning**; `git` local in a real repo whose commit
   lacks the path ⇒ error; `run`/`version`/`retrieved` wrong shapes ⇒
   `invalid_run_ref`/`invalid_version_ref`/`invalid_retrieved_ref`;
   unknown scheme ⇒ `invalid_ref_pin`; escaping target ⇒ `ref_escape`.
10. `check_multiref_first_failure` — a record with several bad refs: all
    refs appear as findings in stored index order; the same record still
    fails save with the **first** failure's code/message (ref-index
    first-failure, exact parity).
11. `check_git_env_warning` — a `git:` pin in a store **not** inside a Git
    work tree (tmp copy) ⇒ `invalid_git_ref` warning, exit 1; the same
    record still fails save with exit 2 and the same code/message.
12. `check_invalid_timestamp_warning` — `created_at: +now+` ⇒ warning
    `invalid_timestamp`; exit 1; the file still counts in `counts.entries`;
    reads remain readable.
13. `check_empty_goal_warning` — placeholder, empty, and missing Research
    Goal ⇒ `empty_topic_goal` warning; a filled goal ⇒ no finding.
14. `check_note_rules` — malformed Note ⇒ error; Note with empty
    `basis_refs` ⇒ `missing_refs` error (exact message); Note with drifted
    `basis_refs` pin ⇒ `hash_mismatch` error; Note with `supersedes`
    targeting a nonexistent Note ID ⇒ **no finding** (v0.1 shape-only
    rule).
15. `check_deterministic_order` — a store with several mixed findings:
    two runs produce byte-identical reports; findings sorted by
    `(path, code, message)` (ties resolved by message); no volatile field
    in the payload.
16. `check_read_only_byte_identity` — before/after `.aitp` sha256 maps
    byte-identical; no lock file, no `.aitp/local` writes.
17. `enter_text_compact` — golden-store `enter` text equals
    `golden("enter.txt")`, including both frozen safety lines
    (`recent_entries: 6 of 6 active (0 omitted)`;
    `recent_notes: 2; latest_working_note: …; active_newer: 0`); a
    synthetic store with a newer unresolved failure than the handoff
    prints `handoff_status: review`; empty/missing/literal placeholder
    goals all print `goal_status: not_established`; a filled goal prints
    `goal: <text>`; `active_newer` prints `unknown` when the payload value
    is null; a store with warnings prints only the count line with the
    `aitp check` pointer; `enter --json` is byte-identical before/after
    the renderer change (same payload).
18. `save_envelope_exact` — after the split, `record save`/`note save`
    success envelopes are exactly `{"status":"saved","path"}` /
    `{"status":"already_saved","path"}` and the prepare envelopes are
    unchanged (exact key sets); no new key anywhere.
19. `save_pin_parity` — for each shared pin failure (`missing_ref`,
    `hash_mismatch`, `unreadable_ref`, `ref_escape`, `invalid_ref_pin`,
    `invalid_git_ref`), save raises the same code/message as the
    corresponding check finding (exit 2).
20. `cli_misuse` — bare `aitp check --bogus` and other argparse misuse:
    usage to stderr, exit 2; `--json` errors keep the stdout envelope.
21. `seed_regression_s1_s2` — on `cp -a` copies of `suite/seeds/S1` and
    `S2`: `check` runs deterministically (counts and status recorded as
    observed in `docs/m1b-r1-stage-notes.md`), `enter` text renders with
    both safety lines, the copies are byte-identical (`diff -r`)
    before/after; the seeds are never modified.

Gate checklist (recorded in `docs/m1b-r1-stage-notes.md`): the 21 tests
above plus the **unchanged** ledger suite (all 56), the existing benchmark
(`--help` < 250 ms; 1,000-Entry `enter`/`list` < 1 s; thresholds unchanged,
results recorded), plugin tests (`test_plugin.py`), distribution tests
(`test_distribution.py`), per-module < 400 and cumulative ≤ 1,450 line
counts, version sync (0.3.0 across all four version surfaces), and the
bundled-launcher acceptance below.

## Real-store acceptance (GW_librpa, operator, in place, read-only)

The real store is compatibility evidence, not a test namespace. Uses the
**exact bundled launcher** (`plugins/aitp-research-protocol/scripts/aitp.py`
with the Skill's interpreter probe order — not `python -m aitp`):

```text
find .aitp -type f -print0 | sort -z | xargs -0 sha256sum > /tmp/r1-before.txt
<bundled-aitp> check --json      # exit is recorded as observed, NOT fixed to 1:
                                 # the report payload and the exit code must be
                                 # mutually consistent (findings -> exit 1,
                                 # clean -> exit 0) and are recorded verbatim
                                 # in docs/m1b-r1-stage-notes.md
<bundled-aitp> check             # text: one line per finding + summary line
<bundled-aitp> enter             # compact text renders; both safety lines present
<bundled-aitp> enter --json      # payload unchanged (schema aitp/enter-0.2)
find .aitp -type f -print0 | sort -z | xargs -0 sha256sum > /tmp/r1-after.txt
diff /tmp/r1-before.txt /tmp/r1-after.txt   # must be empty
```

The historical `invalid_timestamp` warning on `entry-97bec98c…` is expected
to appear as a warning finding; drifted local pins as error findings —
but the store is dynamic, so the acceptance records the **observed** exit
and payload and asserts consistency, not a fixed exit code. `list`/`show`/
`enter` remain readable; `check` never repairs or hides drift.

## Version and docs sync

- **Version**: when R1 ships, the plugin version becomes **0.3.0** in
  `kimi.plugin.json`, `.codex-plugin/plugin.json` (with its UTC timestamp
  suffix), `pyproject.toml`, and `scripts/vendor/aitp/__init__.py`
  (`aitp.__version__`). `aitp/check-report-0.1` versions independently;
  `aitp/enter-0.2`, `aitp/list-0.1`, `aitp/show-0.1` are unchanged. Do not
  modify the untracked `uv.lock`. No `aitp --version` flag is added.
- **Docs**: the same change updates all status surfaces:
  `docs/roadmap.md` (stage table + current state), `README.md`,
  `AGENTS.md`, `docs/design.md` §Commands, `docs/m1-read-write-balance.md`
  (index), `docs/m1b-spec.md` §0.1, `docs/m1b-adjudication.md` §8,
  `docs/m1a-stage-notes.md` pause section, the `docs/hakimi/` handoff
  (compatibility matrix rows + red lines), the `using-aitp` Skill (teach
  only shipped commands), and the new stage-notes artifact
  `docs/m1b-r1-stage-notes.md` (gate evidence: tests, benchmark, line
  counts, prototype re-measurement, real-store observed payload/exit).
- **Skill**: `using-aitp` teaches only shipped commands: `check` for
  store health before resuming a dense store (read-only; exit 0/1/2; parse
  the report on exits 0 and 1) and the compact `enter` text semantics
  (goal/handoff hints are structural, not semantic). The Skill must not
  teach deferred candidates (`lineage` included).
- **Hakimi**: the compact `enter` text is human-facing only — Hakimi must
  not feature-detect or parse it; machine output is the versioned JSON.
  `check` returns `aitp/check-report-0.1` on exits 0 and 1 and the standard
  error envelope on exit 2. `aitp/lineage-0.1` remains a deferred
  candidate (not shipped).
- **Suite**: `suite/` stays frozen and unchanged; R1 has no suite
  deliverable.

## Cut order if over budget

The cap is 1,450 cumulative nonblank lines (hard) with target 1,425. The
author-reported prototype measured **1,413** (net +157, 37-line margin to
the cap). Followup-2 (`lineage`) was already re-deferred at budget
reconciliation rather than cutting signals. If the implementation session's
draft still exceeds 1,450, cut in this order — before any implementation is
accepted:

1. **Compact `enter` display lines (residual cosmetic)** — in this order:
   (a) the `unresolved_failures:` count line; (b) the `topic:`/
   `memory_status:` lines. Never cut: the two frozen safety lines
   (`recent_entries: … of … active (… omitted)` and `recent_notes: …;
   latest_working_note: …; active_newer: …`), `goal_status`/`goal`,
   `next_action`, `handoff_status`, or the warnings summary. JSON
   untouched.
2. Never cut: `check`'s validator semantics (structural/evidence grading,
   the no-crash mappings, exit 0/1/2, zero-write, deterministic
   `(path, code, message)` ordering, `check-report-0.1`), the two text-only
   hints, the warning summary, any JSON contract, v0.1 compatibility, or
   the no-index rule. Do not expand scope to absorb slack.

## Explicit prohibitions

- This work package is **documentation only**: no runtime, tests, suite,
  or plugin-manifest change ships with the adjudication/spec; the code
  described here lands only after the spec is green-lit and gated.
- No persisted `based_on`/`used_by`; no schema `aitp/lite-entry-0.2`; no
  `prediction`/`question` kinds; no typed closures; no `contradicts`; no
  Note-supersedes target rules; no pointer bundles; no quick-run; no
  structured prepare input; **no `aitp lineage`** (re-deferred at budget
  reconciliation) — deferred candidates produce no code.
- `check` never validates unselected M1b schemas and never diagnoses
  capabilities that are not shipped.
- `check`/`enter` text never write: no `atomic_write`, no `store_lock`, no
  `.aitp/local` writes, no cursor, no cache, no index, no repair, no
  migration, no `--fix`.
- No semantic judgment in Python: the hints are structural; `check` grades
  contracts, not science; nothing is called "stale" by the runtime.
- `enter-0.2` JSON is byte-unchanged; `list-0.1`/`show-0.1` untouched;
  save-path validation unchanged except the documented, explicitly
  authorized ref-validator split and absent-git fix (same codes, messages,
  first-failure order; envelopes exact).
- No new dependencies; no MCP/daemon/hook/vector service; no persistent
  warning suppression of any kind.
- Frozen suite inputs (`suite/FROZEN.md` and everything under `suite/`)
  remain untouched.
