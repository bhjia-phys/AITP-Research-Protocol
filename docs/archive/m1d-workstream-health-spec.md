# M1d implementation spec — Workstream health: single-slug scoped `check` (`aitp/check-report-0.2`)

Status: **implementation specification; frozen 2026-08-14 (adjudicated
revision absorbing the adversarial review of the first draft); implementation
in progress; deterministic gate pending**. The natural-demand evidence is the
2026-08-14 feedback chain — three ordinary real-Topic sessions, none of them
an AITP gate or a controlled experiment
([`feedback/2026-08-14-gw-librpa-natural-use.md`](../../feedback/2026-08-14-gw-librpa-natural-use.md),
[`feedback/2026-08-14-gw-librpa-qsgw-semiconductor-natural-use.md`](../../feedback/2026-08-14-gw-librpa-qsgw-semiconductor-natural-use.md),
[`feedback/2026-08-14-yangian-power-law-heisenberg-chain-natural-use.md`](../../feedback/2026-08-14-yangian-power-law-heisenberg-chain-natural-use.md)).
The deterministic gate has **not** been run and is **not claimed passed**;
gate evidence will be recorded in the stage-notes artifact
`docs/m1d-stage-notes.md`, created at gate time, not before. The spec text
below stands as the authoritative M1d contract from 2026-08-14 (adjudicated
revision).

## Natural-demand evidence

| Feedback (file, line) | Observed fact | What M1d does about it |
|---|---|---|
| `feedback/2026-08-14-gw-librpa-natural-use.md` line 4 | `aitp check --json` on 293 Entries / 3 Notes reports 201 errors / 2 warnings (203 findings); historical SHA pins against later-modified `PROJECT_MEMORY.md`/papers/scripts are reported as errors alongside truly missing files; at recovery time "historical snapshot changed" is hard to separate from "current evidence damaged" | Scoped `check --workstream` projects the health signal per research line; the `by_code` aggregate compresses the per-workstream error mix into a small per-code tally — **for stores whose records carry `workstreams`**. The GW legacy store itself has none, so its scoped view is **empty** and the 201-error wall is visible only through `counts.outside_scope` and the no-flag report; a reviewed backfill or new scoped records are the precondition for scoped health. **Not** fixed: classifying drift vs. damage (deferred; see §Claims and boundaries) |
| `feedback/2026-08-14-gw-librpa-natural-use.md` line 5 | `check` exit 1 stops common `set -e` recovery scripts before `enter`; triggered again this round; the exit code must be explicitly captured to proceed | Scoped exit 0/1 semantics stay exactly as today, but a recovery script can now gate on **the workstream's own** health signal; a workstream with no attributable findings exits 0, with `outside_scope` reporting what is left out. Scoped semantics are frozen in §7 |
| `feedback/2026-08-14-gw-librpa-natural-use.md` line 6 | `enter --recent 20` shows 246 active / 226 omitted / 30 unresolved; the latest closeout still points at work superseded by the r16/r17 fix chain; structured handoff does not follow a new conclusion chain | Not in M1d: closeout-first handoff is the selected M1a solution; stale-handoff discipline stays a Skill/human matter (roster H is dropped). No runtime change |
| `feedback/2026-08-14-gw-librpa-qsgw-semiconductor-natural-use.md` line 4 | Global `check` reports 201 errors / 2 warnings while scoped `enter --workstream qsgw-semiconductor` shows `memory_status=available`; the two projections side by side cannot say whether the **current workstream's** evidence is healthy | M1d adds the missing projection: `check --workstream <slug>` — the workstream-level health signal (`aitp/check-report-0.2`), small, deterministic, read-only, with `outside_scope` so a healthy-looking scope never hides the global remainder. On stores whose records carry `workstreams`; on the all-unscoped GW store the scoped view is empty until a reviewed backfill or new scoped records |
| `feedback/2026-08-14-gw-librpa-qsgw-semiconductor-natural-use.md` line 5 | The 201 errors mix truly missing files with SHA mismatches on later-modified mutable files; `entry-5b68…` mismatches the legitimately regenerated `generated-inputs/MANIFEST.sha256` | The scoped `by_code` tally shows the per-code, per-level mix of one workstream at a glance; distinguishing "expected drift" from "current damage" remains a human judgment (never a runtime inference) |
| `feedback/2026-08-14-yangian-power-law-heisenberg-chain-natural-use.md` line 7 | `aitp check --json` returns 147 errors, ≈ 54,469 bytes, truncated in the terminal; one real `missing_ref` is mixed into the same error count | Scoped `check` text prints **exactly four frozen lines** (workstream, totals, `by_code` compact JSON, `outside_scope`), never truncated; details stay in `--json`. A workstream run on this store is small and diffable |
| `feedback/2026-08-14-yangian-power-law-heisenberg-chain-natural-use.md` line 8 | Natural need for distinguishing "expected drift of historical pins" from "current evidence damage" and for a **baseline/delta reading** of `check` results | The baseline/delta reading is **deferred** (a report-comparison runtime is out of slice; manual `diff`/`rg` over saved deterministic JSONs already works). M1d ships only the scoped projection |

Also observed but **explicitly not** in M1d (recorded so the slice stays
minimal): remote pointer/evidence manifests and `lineage` projections
(`feedback/2026-08-14-gw-librpa-natural-use.md` line 8,
`feedback/2026-08-14-gw-librpa-qsgw-semiconductor-natural-use.md` line 8 —
roster D and Followup 2, both deferred); structured prepare and the
prepare-template `at` hint (`feedback/2026-08-14-gw-librpa-natural-use.md`
line 9 — Followup 6, deferred); handoff staleness
(`feedback/2026-08-14-gw-librpa-qsgw-semiconductor-natural-use.md` line 6 —
human closeout discipline). Nothing in M1d touches `enter`, `list`, `show`,
`record`, `note`, or the save path.

## Supersession of M1c frozen clauses (check only)

M1d is additive to the frozen M1c contract, but it **replaces the M1c
"`check` has no scope flag" rule** for the flag variant. Frozen M1c
artifacts are never edited; the clauses below record exactly what M1d
supersedes and what remains in force. Everything in M1c not listed here —
the `workstreams` field semantics (explicit multi-membership, unscoped
legacy, no inference), the repeatable prepare flags, `aitp/enter-0.3` /
`aitp/list-0.2`, no-registry, and the no-flag byte-identity of `enter` /
`list` — remains fully in force and is untouched by M1d.

| M1c frozen clause (location) | M1d disposition |
|---|---|
| `docs/archive/m1c-workstreams-spec.md` §6: "`check` gets **no scope flag** and `aitp/check-report-0.1` is unchanged (schema, exit 0/1/2, zero-write, deterministic `(path, code, message)` ordering)" | **Replaced for the flag variant**: with `--workstream`, `check` emits `aitp/check-report-0.2` scoped per this spec. Every no-flag part of the clause — `aitp/check-report-0.1` byte-identity, exit 0/1/2, zero-write, deterministic `(path, code, message)` ordering — remains fully in force (§8) |
| `docs/archive/m1c-workstreams-spec.md` §6: "Validation warnings remain global — `check` always scans the whole store" | **Still in force**: every run, scoped or not, scans the whole store once and computes the global report exactly as today; the scope flag restricts only the report, never the scan (§2, §3) |
| `docs/archive/m1c-workstreams-spec.md` §Scope: "no `check` change beyond an additive field validation" | **Replaced**: M1d adds the scoped flag variant on top of the M1c field validation; the M1c field validation itself is untouched |
| `docs/archive/m1c-workstreams-spec.md` §Explicit prohibitions: "No relations-scoping at save or in `check`; `check` has no scope flag and `aitp/check-report-0.1` is unchanged" | **Partly replaced**: relations are still never scoped (global `entry_map`, §4) — still in force; the "no scope flag" part is replaced for the flag variant only |
| `docs/archive/m1c-workstreams-spec.md` §Cut order "Never cut": "… global warnings/malformed/check, byte-identical old schemas without the flag, or v0.1 compatibility" | **Still in force**: the no-flag global `check` (global warnings/malformed) remains fully valid and byte-identical; the flag variant is an **additive projection** on top of the unchanged global run, never a replacement of it. M1c's `enter`/`list` global `warnings` and `counts.malformed` are untouched by M1d |
| `docs/archive/m1c-workstreams-spec.md` §Tests item 14: "`check --workstream crpa` is CLI misuse (exit 2); `check` output is identical before/after scoped runs (global, no scope flag)" | **Partly replaced**: the "CLI misuse" half is replaced (the flag is now valid; the corresponding live assertion in `tests/ledger/test_workstreams.py` is amended per §Tests); the "global check output identical before/after scoped runs" half remains in force and is asserted by §Tests test 14 and the untouched globality assertions in `test_workstreams.py` |
| `docs/m1c-stage-notes.md` §Functionality: "`warnings`, `counts.malformed`, `memory_status`, and `check` are **global** (`check` has no scope flag)" | **Historical record, unchanged**: the M1c gate evidence stands as recorded; M1d's flag variant is additive and its gate evidence goes into `docs/m1d-stage-notes.md` at gate time |
| `tests/ledger/test_workstreams.py` docstring: "`check` gains no scope flag and keeps `aitp/check-report-0.1`" and the misuse block in `test_check_workstreams_finding_and_global` | **Amended per §Tests**: the only pre-declared edit to an existing test file in M1d; every other assertion in the file is untouched |

Frozen boundaries of the supersession:

- `docs/archive/m1c-workstreams-spec.md` and `docs/m1c-stage-notes.md` are
  **not modified**; the M1c gate is not reopened. `docs/archive/
  m1c-workstreams-spec.md` remains the historical M1c record and its
  no-flag contract stays normative as frozen.
- `docs/m1b-spec.md` §0.1 dispositions are **unchanged** (B, C–E, Followup 2
  (`lineage`), Followup 6 (structured prepare) deferred; F → M4; G
  independent; H dropped). M1d selects no M1b candidate.
- **`aitp/check-report-0.2` diagnoses exactly the same v0.1 file schemas as
  `aitp/check-report-0.1`** — `aitp/lite-entry-0.1` and
  `aitp/lite-note-0.1` only. No unselected M1b schema (e.g.
  `aitp/lite-entry-0.2`) is ever validated by either report version.

## Stage authorization and independence boundary

- M1d is a **separate stage slice**, not part of the frozen M1b A–H +
  Followup roster and **not M3** (workstreams live inside one Topic store;
  the M3 design option, its ≥ 3 real Topics and natural cross-Topic failure
  gates, and the `catalog`/`link` absence are untouched). M2/M4
  dispositions are untouched. M1d does not reopen M1b or M1c and does not
  flip any disposition in any frozen roster.
- The 2026-08-14 feedback is **new natural-use evidence after the M1c gate**,
  satisfying roadmap §Simplicity rule 2: runtime work requires an explicit
  roadmap status flip and a separately reviewed implementation-level spec
  selecting the smallest coherent, evidence-backed slice. This document is
  that spec; the same change that implements it flips the M1d roadmap row to
  "implementation in progress; deterministic gate pending" (no gate claim).
- M1d's deterministic gate is its own; it does not flip M2/M3/M4, does not
  reopen M1b/M1c, and does not modify any frozen artifact (`docs/m1b-spec.md`,
  every existing file in `docs/archive/`, `suite/`). The supersession of the
  M1c "no scope flag" sentence is recorded in §Supersession above and is the
  only M1c-contract change.

## Scope

One slice: a **single-occurrence `--workstream <slug>` flag on `aitp check`**
emitting a scoped report (schema **`aitp/check-report-0.2`**) that restricts
the existing whole-store diagnostics to findings attributable to exactly one
workstream, plus a compact four-line scoped text rendering. Scoped
`counts` carry a per-code, per-level `by_code` tally and a derived
`outside_scope` level-delta total so a scoped report never masks global
findings.
Without the flag, every `check` output surface is byte-unchanged
(`aitp/check-report-0.1` JSON and text, exit 0/1/2, zero-write). No
registry, no new command, no repair, no index, no inference, no changes to
any other command.

## Contract

### 1. CLI grammar and help

```text
aitp check [--cwd PATH] [--json] [--workstream SLUG]
```

- `--workstream` on `check` accepts **exactly one slug** (not a repeatable
  union): a repeated `--workstream` is CLI misuse and the parser rejects it
  (exit 2, usage error, argparse "may only be given once"), exactly like the
  M1c `enter`/`list` flags (`_SingleValue` action). `check_workspace(cwd, *,
  workstream=None)` likewise takes a single slug string.
- The `--workstream` help string is frozen: `only findings on records that
  explicitly list this workstream (single slug)`. The `check` command help
  line stays `validate the whole store read-only and report findings (exit 0
  clean, 1 findings, 2 cannot run)`.
- Slug validation reuses the M1c rule verbatim (`_validate_scope` in
  `query.py` → `_validate_workstreams([slug])`): an invalid slug raises
  `invalid_workstreams` with the exact M1c messages (`invalid workstreams:
  invalid slug: '…'`, `invalid workstreams: empty element` for `""`), exit 2
  with the standard JSON error envelope under `--json`; a non-string API
  scope raises `invalid workstreams: exactly one slug required`. Same order
  as M1c read commands: `resolve_root` → `load_store` → scope validation.
- `--help` stays < 250 ms.

### 2. Attribution rule (frozen)

The whole-store diagnostics run **exactly as today** — same parse pass, same
per-file rule (parse → structure → duplicate → timestamp warning → relations
→ refs), same global `entry_map`, same global `(path, code, message)` sort —
and the scoped report is that report **restricted** to attributable
in-scope findings, with additive keys. A finding on path P is in the scoped
view iff **both**:

1. **Admitted**: P's record was admitted into the scanned record set —
   parse and structural validation passed **and** the ID was unique (i.e.,
   the record is in the `entries`/`notes` item lists, not in the warning
   list). A file that fails parse or structure, or is rejected as a
   duplicate ID, is **not admitted** and none of its findings is ever
   scoped.
2. **In scope**: the admitted record's frontmatter `workstreams` list
   explicitly contains the requested slug (strict exact membership,
   `_in_scope`, never inferred; unscoped records are out of every scope).

Frozen consequences:

- Unscoped records (no `workstreams` field) → their findings (timestamp
  warnings, relations, refs) are **excluded** from every scoped view.
- Out-of-scope records → excluded.
- Malformed records — parse failure (`unreadable_record`,
  `malformed_record`), structural failure (including `invalid_workstreams`,
  structural `invalid_timestamp`, `missing_field`, `invalid_schema`,
  `invalid_id`, `topic_mismatch`, `invalid_type`, `invalid_kind`,
  `invalid_authority`, `missing_summary`, `invalid_limitations`,
  `missing_limitations`, `missing_refs` (Entry-side, raised by
  `validate_entry` for evidence-required kinds), `invalid_refs`,
  `invalid_ref`, `invalid_relation`, `invalid_idempotency_key`,
  `unfilled_template`, `empty_section`) — are **not attributable** and
  their findings are **excluded** from every scoped view (a record whose
  `workstreams` field is itself invalid is therefore never scoped, in any
  scope).
- Duplicate-ID files: the later file passes structure but is rejected at
  the duplicate step; it is **not admitted**, so its `duplicate_id` finding
  is **excluded** from every scoped view. The first structurally valid file
  wins the ID exactly as today (global semantics unchanged).
- Admitted records' step-4–6 findings — legacy `invalid_timestamp` warning
  (`unparseable created_at: …`), relations findings, graded ref findings,
  and the Note-side `missing_refs` finding (`Note requires nonempty
  basis_refs`, reported by the ref step because Note structure validation
  runs with `validate_evidence=False`; the Note is admitted) — are
  **included** when the record is in scope. The same code is a structural
  failure for Entries and an attributed step-6 finding for Notes; the
  attribution rule follows the per-file step where the finding actually
  fires.
- **TOPIC.md findings** (`empty_topic_goal`, TOPIC parse failures) are not
  record findings and are **excluded** from every scoped view; they remain
  in the no-flag global report and in `counts.outside_scope` (§5). A scoped
  `clean` (exit 0) therefore means "no attributable findings for this
  workstream", **not** "the whole store is clean" — the no-flag run remains
  the whole-store health instrument (frozen; see §7).
- `malformed_store`, `not_initialized`, `invalid_root` (exit 2) are
  pre-scope conditions; unchanged.

### 3. Scoped-subset invariant (frozen)

The scoped report is a **strict subset projection of the global report**:

- The complete global pass — scan, structure, duplicate, timestamp,
  relations, refs, with relations validated against the **global**
  `entry_map` — executes first and produces the global report exactly as a
  no-flag run would.
- The scoped projection then keeps exactly the findings whose path is an
  **admitted** record path (structure passed and ID unique, §2) whose
  frontmatter explicitly contains the slug.
- **Invariant (testable, asserted in §Tests test 19)**: the scoped
  `findings` list is element-wise equal to the global `findings` restricted
  to the scoped paths — same findings, same levels, same codes, same
  messages, same `(path, code, message)` order. Scoped order is the global
  order restricted; no finding is re-sorted, re-graded, or re-worded.
- Every finding not on a scoped path — out-of-scope, unscoped, malformed,
  duplicate, and TOPIC.md findings — is **unattributable to any scope** and
  appears in the scoped report only through the derived `outside_scope`
  level totals (§5), never as a finding.
- The scope flag performs **no validation beyond the global run**; it only
  restricts and annotates.

### 4. Relations: global first, then scope

Relations are validated on the **whole store** before any scoping — the
`entry_map` is built once from the single global parse pass (identical
semantics to today), and an in-scope resolver/superseder is checked against
that global map. Consequences (frozen):

- An in-scope Entry whose `resolves`/`supersedes` target is an **out-of-scope
  or unscoped** existing record validates cleanly — `missing_relation` never
  fires because the target exists globally (a cross-workstream resolver still
  closes its target, mirroring the M1c relation-before-filter rule).
- `missing_relation`/`invalid_relation` fire only when the target is
  absent from the whole store, or targets itself — and the finding then
  appears in the scoped view iff the resolving record is in scope.
- A scoped run performs **no validation beyond the global run**: the flag
  only restricts and annotates. The scoped report is exactly the global
  report restricted to attributable in-scope findings, plus the §5 keys.

### 5. Report — schema `aitp/check-report-0.2` (flag present only)

With `--workstream`, `check --json` emits `"schema": "aitp/check-report-0.2"`:
the complete `aitp/check-report-0.1` payload with exactly three additive
changes:

- one additive top-level **singular `workstream: "<slug>"`** key (mirroring
  `aitp/enter-0.3`/`aitp/list-0.2`; there is no `workstreams` key anywhere
  in the payload);
- `counts` gains **`by_code`**: a map `code → {"errors": n, "warnings": m}`
  over the **scoped findings**, keys sorted lexicographically by code,
  **always present** (`{}` when there are no scoped findings). The buckets
  are per-level, so a code that grades as an error on one finding and a
  warning on another (e.g. `invalid_git_ref`) is tallied separately:
  `sum(b["errors"] for b in by_code.values()) == counts.errors`,
  `sum(b["warnings"] for b in by_code.values()) == counts.warnings`, and
  `sum(b["errors"] + b["warnings"] for b in by_code.values()) ==
  counts.errors + counts.warnings == len(findings)`;
- `counts` gains **`outside_scope`: `{"errors": n, "warnings": m}`** — the
  derived level totals of all global findings **not** in the scoped view
  (out-of-scope, unscoped, malformed, duplicate, and TOPIC.md findings):
  exactly global totals minus scoped totals, per level, always present in
  `aitp/check-report-0.2`, `{"errors": 0, "warnings": 0}` when the scoped
  view already contains every finding. `outside_scope` is **not a scoped
  finding**: it carries no paths, no codes, no `by_code` contribution, never
  appears in `findings`, and never affects `status` or the exit code (§7) —
  it exists so a scoped report can never silently mask global findings. It
  is a **pure level delta**: it names no path, no code, and no workstream,
  and it does **not** label any other workstream's (or unscoped, malformed,
  duplicate, TOPIC) findings as "debt" or "damage" — those remain ordinary
  global findings graded exactly as the global report grades them; the only
  claim is the arithmetic difference. **No `malformed` key is added to
  `counts`.**

```json
{
  "schema": "aitp/check-report-0.2",
  "status": "clean" | "findings",
  "root": "<absolute path>",
  "counts": {"entries": 3, "notes": 0, "errors": 2, "warnings": 1,
             "by_code": {"hash_mismatch": {"errors": 2, "warnings": 0},
                         "invalid_timestamp": {"errors": 0, "warnings": 1}},
             "outside_scope": {"errors": 5, "warnings": 1}},
  "findings": [
    {"level": "error", "code": "hash_mismatch", "path": ".aitp/topic/entries/entry-….md", "message": "sha256 mismatch: …"}
  ],
  "workstream": "<slug>"
}
```

Frozen semantics:

- **Scoped `counts.entries`** = the number of **admitted in-scope** canonical
  Entry files (parse + structure passed, ID unique, `workstreams` contains
  the slug); **scoped `counts.notes`** likewise for Notes. This deliberately
  differs from the global rule ("count every canonical file exactly once,
  not reduced by structural failure") because malformed files cannot be
  attributed to any scope — the asymmetry is intentional and frozen.
  `TOPIC.md` never counts.
- **`counts.errors`/`counts.warnings`** = scoped findings by level;
  `status` = `"findings"` iff the scoped findings list is non-empty, else
  `"clean"`; `findings` is the global sorted list restricted to
  attributable in-scope findings (same `(path, code, message)` order, §3).
- **Key order is frozen** (golden-testable): top level
  `schema, status, root, counts, findings, workstream` (the `workstream`
  key appended last, mirroring the M1c implementation pattern); inside
  `counts`: `entries, notes, errors, warnings, by_code, outside_scope`.
- A scoped report with findings always satisfies
  `counts.entries + counts.notes >= 1` (every scoped finding sits on an
  admitted in-scope record), `counts.errors + counts.warnings ==
  len(findings)`, `outside_scope` ≥ 0 per level, and
  `outside_scope.errors + counts.errors == <global errors>` (likewise
  warnings) — the payload/exit consistency rule of §7.

### 6. Scoped text renderer (frozen, four lines)

Scoped `check` text runs (`--workstream` present) print **exactly these four
lines, always — including a clean scope**:

```text
workstream: <slug>
check: <e> error(s), <w> warning(s)
by_code: <compact JSON>
outside_scope: <e> error(s), <w> warning(s) (run "aitp check" for the whole store)
```

- `check:` and `outside_scope:` use the **scoped** and derived totals of
  §5; `by_code:` is the compact JSON serialization of
  `counts["by_code"]` — `json.dumps(by_code, ensure_ascii=False)` with
  default separators (no indent), e.g.
  `by_code: {"hash_mismatch": {"errors": 2, "warnings": 0}}` — and prints
  `by_code: {}` on a clean scope.
- **No per-finding lines** are printed in scoped text — details live in
  `check --json` only. This is the fixed answer to the 54,469-byte
  terminal-truncation observation.
- **All four lines go to stdout; stderr is empty** on a successful scoped
  run (exit 0 or 1). Exit-2 misuse keeps the standard usage/error behavior.
- The text is human-facing only; Hakimi must never parse it (machine output
  is the versioned JSON). The unscoped text path is byte-unchanged
  (one line per finding + the summary line, exactly as today).

### 7. Exit codes, status, and empty scope (frozen)

Unchanged mapping, evaluated on the scoped report:

- `0` — clean: **zero scoped findings** (the store may still have global
  findings, reported as `counts.outside_scope`; frozen: a scoped `clean`
  claims nothing about other workstreams or the whole store — §2, §3).
- `1` — findings: at least one attributable in-scope error or warning.
- `2` — could not run: not a workspace, unreadable/invalid store metadata
  (`not_initialized`, `malformed_store`, `invalid_root`), or CLI misuse
  (argparse, repeated `--workstream`, invalid slug `invalid_workstreams`).

Frozen rules:

- The report payload and the exit code must be mutually consistent
  (scoped `findings` non-empty ⇒ exit 1; empty ⇒ exit 0) — the R1
  acceptance rule, unchanged.
- **`outside_scope` never affects `status` or the exit code** — it is a
  derived level-delta indicator only. A scope with zero attributable findings
  exits 0 even when `outside_scope` is large; the four-line text keeps that
  remainder visible and points at the whole-store run.
- **Warnings semantics differ between the two scoped surfaces (frozen)**:
  M1c's scoped `enter --workstream` keeps `warnings` and `counts.malformed`
  **global**; M1d's scoped `check --workstream` `counts.warnings` is
  **scoped** (scoped findings by level), with `outside_scope` carrying the
  global−scoped remainder. The Skill (§Version and docs sync) teaches both,
  so the difference is never read as an inconsistency.
- A well-formed slug with no admitted in-scope records is a **valid empty
  scope** (counts 0, `findings` `[]`, `by_code` `{}`, `outside_scope` =
  the global totals, status `clean`, exit 0) — never an error, mirroring
  M1c empty-scope semantics.

### 8. No-flag compatibility (binding)

Without `--workstream`:

- `check --json` is **byte-identical `aitp/check-report-0.1`** (schema,
  counts, findings, ordering, key order, no `workstream` key, no `by_code`,
  no `outside_scope`);
- `check` text is **byte-identical** (one line per finding + exactly one
  summary line);
- exit 0/1/2 and zero-write are unchanged.

No-flag byte-parity is golden-tested (existing `check.json` golden plus the
unchanged suite), asserted at the real-store acceptance against the
pre-change recorded output and, where feasible, the old runtime
(old-runtime vs. current-runtime parity, as in the M1c gate). The API
default is `check_workspace(cwd, *, workstream=None)`; `None` short-circuits
before any scoped computation so the no-flag code path is literally the
today code path.

### 9. Zero-write

Unchanged: `check` writes nothing in either mode — no lock file (never takes
`store_lock`), no cache, no index, no repair, no migration, no scratch, no
new canonical files, no `--fix` flag now or later. A test asserts the `.aitp`
tree is byte-identical before and after both scoped and unscoped runs.

### 10. Determinism and ordering

Two runs on the same store produce byte-identical reports in both modes:
findings sorted globally by `(path, code, message)` and the scoped
restriction applied to the sorted list (the §3 subset invariant, so scoped
order is the global order restricted); `by_code` keys sorted
lexicographically with per-level buckets; `outside_scope` derived by
subtraction of deterministic totals; the four text lines in the frozen
order with the compact `by_code` JSON; no volatile fields (no wall-clock
timestamp).

### 11. Adjudicated resolutions and frozen interpretations

The first-draft contract was sound; the adversarial review adjudicated two
refinements and confirmed the rest. The five points below are the frozen
interpretations; **no further change to the contract was required**:

1. **Duplicate-ID files** — "passes structural validation" is ambiguous for
   a file rejected at the duplicate step. Frozen: only **admitted** records
   (structure passed **and** ID unique) are attributable; `duplicate_id`
   findings are never scoped (§2). Rationale: the per-file rule already
   excludes the duplicate from steps 4–6; the scoped projection must not
   attribute a finding to a record that is not part of the record set.
2. **Scoped `counts.entries`/`counts.notes`** — frozen: admitted in-scope
   records, deliberately different from the global "count every canonical
   file" rule (§5). Rationale: malformed files cannot be attributed; the
   difference is explicit, versioned (`aitp/check-report-0.2`), and
   documented.
3. **`by_code` per-level buckets** — adjudicated change: the flat
   `code → count` shape was replaced by `code → {"errors": n, "warnings":
   m}` (§5). This resolves the level-split ambiguity exactly: a code that
   grades as both error and warning (e.g. `invalid_git_ref`,
   `invalid_timestamp`) is tallied per level, and the buckets sum to
   `counts.errors`/`counts.warnings`.
4. **`outside_scope`** — adjudicated addition: scoped `counts` carry
   `{"errors": n, "warnings": m}` equal to the global totals minus the
   scoped totals (§5), so a scoped report can never silently mask global
   findings. It is a derived indicator, not a finding: no paths, no codes,
   no effect on `status`/exit; deliberately **no `malformed` key** and no
   per-finding details (the no-flag report is the whole-store instrument).
   It is a **pure level delta** — it never labels any other workstream's
   findings as "debt" or "damage"; those are ordinary global findings
   (§5).
5. **Scoped `clean`/exit 0 while the store has global findings** — intended,
   not a flaw: the scope's contract is "no attributable findings for this
   workstream". Frozen with the explicit caveat (§2, §7) and the help text
   ("only findings on records that explicitly list this workstream"); the
   no-flag run remains the whole-store instrument.

## Budget and implementation map

Measured on the M1c gate HEAD `29c75e82` (2026-08-13): the canonical runtime
is **1,519 nonblank lines** (`grep -c '\S'` per module, summed; every module
< 400; `records.py` 348, `workspace.py` 335). M1d caps: **target ≤ 1,550**
(net ≤ +31), **hard cap ≤ 1,600** (net ≤ +81); every module stays below 400.

**The target is the budget, not a soft ceiling**: the implementation must
land at or below **1,550** nonblank lines; a draft above the target stops
per the §Over-budget rule (contract-preserving economy first, then
fail-stop — never a contract cut). The **1,600 hard cap is the absolute
ceiling** and must never be exceeded. The implementation session reports
its own measurement at gate time.

Re-estimated touch points for the adjudicated contract (per-level `by_code`
buckets, `outside_scope`, four-line text; implementation economy is the
implementer's choice, subject to the caps). Expected net **≈ +26–32**
(cumulative ≈ 1,545–1,551); the small risk of brushing the target is
handled by the §Over-budget rule (economy first, then stop), never by cap
growth:

| File | Change |
|---|---|
| `diagnostics.py` (78) | import `_in_scope`, `_validate_scope` from `query.py`; `check_workspace(cwd, *, workstream=None)` — validate scope; keep the global report computation byte-identical; build the attributable `{relative_path: frontmatter}` map from the `entries`/`notes` item lists; restrict the globally sorted findings to attributable in-scope ones (one filter pass); compute scoped `counts.entries/notes/errors/warnings`, the per-level `by_code` buckets with keys **rebuilt in lexicographic order** (`dict(sorted(by_code.items()))`; always present), and `outside_scope` (global totals − scoped totals, per level); amend the payload (`schema` `aitp/check-report-0.2`, top-level `workstream` appended last, `counts.by_code` then `counts.outside_scope` appended last inside `counts`); `None` short-circuits to the today code path |
| `cli.py` (221) | `--workstream` on the `check` subparser with the frozen help string (`_SingleValue`, single-occurrence); `check_workspace(args.cwd, workstream=args.workstream)`; `_emit_check` scoped branch — exactly the four frozen lines (§6), `by_code` via `json.dumps(..., ensure_ascii=False)`, early return so the unscoped text path is untouched |
| `core.py` (28) | no change (`check_workspace` already exported; signature is backward compatible) |
| `query.py`, `records.py`, `state.py`, `notes.py`, `workspace.py`, `md.py` | unchanged |

No module may exceed 400 nonblank lines; if a touch point would overflow,
split the helper into the smallest natural module (e.g. a `_scoped_counts`
helper in `diagnostics.py`), never by duplicating logic.

## Tests (new file `tests/ledger/test_check_workstream.py` + one pre-declared amendment)

New test file, plus **exactly one pre-declared amendment to an existing
test file** (the M1c-era `check --workstream` misuse assertion and its
docstring sentence in `tests/ledger/test_workstreams.py` — superseding the
M1c "no scope flag" rule per §Supersession). No other existing test file is
modified. Use the existing conventions (`run_cli`, `copy_store`, `golden`,
`normalized`, `make_entry`, `make_note`, `hash_tree` as in
`tests/ledger/test_workstreams.py`). The implemented suite (19 tests):

1. `test_no_flag_byte_parity` — golden-store copy: `check_workspace(root)`
   equals `golden("check.json")` (with `root` normalized to
   `<golden-store>`); `check --json` stdout parses to that payload; `check`
   text is exactly
   `warning[empty_topic_goal]: .aitp/topic/TOPIC.md: Research Goal is not established\ncheck: 0 error(s), 1 warning(s)\n`; exit 1; no `workstream`/`by_code`/`outside_scope` anywhere.
2. `test_scoped_schema_and_additive_keys` — mixed store: `check_workspace(
   root, workstream="crpa")["schema"] == "aitp/check-report-0.2"`, additive
   top-level singular `"workstream": "crpa"` (no `workstreams` key),
   `counts` keys exactly `entries, notes, errors, warnings, by_code,
   outside_scope` (no `malformed` key), frozen key order
   (`schema, status, root, counts, findings, workstream`).
3. `test_scope_attribution_filter` — a store whose findings span an
   in-scope admitted record, an out-of-scope record, an unscoped record, a
   malformed record, a duplicate-ID file, and `TOPIC.md`: the scoped
   `findings` contain exactly the attributable in-scope ones; the global
   report contains all of them.
4. `test_scoped_counts_and_by_code` — scoped `counts.entries`/`notes` equal
   the admitted in-scope record counts; `counts.errors`/`warnings` from the
   scoped findings; `by_code` keys sorted; per-level bucket sums equal
   `counts.errors`/`counts.warnings` exactly
   (`sum(b["errors"]) == errors`, `sum(b["warnings"]) == warnings`);
   `counts.entries + counts.notes >= 1` whenever findings are non-empty.
5. `test_relations_global_then_scope` — an in-scope Entry whose `resolves`
   target exists out-of-scope (or unscoped) produces **no** finding in the
   scope; the same record with a store-absent target produces
   `missing_relation` in the scope; an out-of-scope resolver's own findings
   stay out.
6. `test_duplicate_id_excluded_from_scope` — two files with one ID: the
   `duplicate_id` error appears in the global report, is **absent** from
   every scoped view (even when the duplicate file's own `workstreams`
   contains the slug); the first structurally valid file wins, as today.
7. `test_invalid_workstreams_unattributable` — an admitted-looking record
   with a duplicate-slug `workstreams` field: `invalid_workstreams` error in
   the global report, absent from every scoped view (including the
   intended slug); the record still fails save with the same code/message.
8. `test_legacy_timestamp_warning_scoped` — an admitted in-scope record
   with `created_at: banana` ⇒ warning `invalid_timestamp` in the scope; a
   non-string `created_at` (structural) ⇒ finding excluded from the scope.
9. `test_topic_global_excluded` — `empty_topic_goal` warning in the global
   report, absent from every scoped view but present in
   `counts.outside_scope`.
10. `test_exit_codes_scoped` — scoped clean (findings exist only on
    out-of-scope/unscoped/malformed records) ⇒ exit 0 via CLI, status
    `clean`, with non-zero `outside_scope`; scoped findings ⇒ exit 1;
    payload/exit consistency in both; not-a-store and unreadable
    `STORE.toml` ⇒ exit 2 unchanged; repeated `--workstream` ⇒ exit 2, "may
    only be given once"; `--workstream "Bad"` / `""` ⇒
    `invalid_workstreams`, exit 2, JSON error envelope; API non-string
    scope ⇒ `invalid workstreams: exactly one slug required`.
11. `test_scoped_text_exact_four_lines` — scoped text is **exactly** the
    four frozen lines of §6 (workstream / check / by_code compact JSON /
    outside_scope with the literal `(run "aitp check" for the whole
    store)` suffix), in order, with sorted `by_code` keys; a clean scope
    still prints all four lines with `by_code: {}`; no per-finding lines;
    unscoped text has no `workstream:` line and matches the golden-era
    format.
12. `test_empty_scope_valid` — `workstream="lone"` (no records):
    `aitp/check-report-0.2`, `counts` `{entries: 0, notes: 0, errors: 0,
    warnings: 0, by_code: {}, outside_scope: {errors: <global errors>,
    warnings: <global warnings>}}`, `findings` `[]`, `status` `clean`,
    exit 0.
13. `test_zero_write` — `.aitp` tree sha256-identical before/after scoped
    and unscoped runs (no lock, no cache, no index, no registry file).
14. `test_determinism` — two scoped runs byte-identical (JSON and the
    four-line text); two unscoped runs byte-identical; an unscoped run
    between two scoped runs changes nothing.
15. `test_scoped_golden` — a workstream-tagged fixture store (deliberate
    regeneration, `root` normalized to `<golden-store>`): scoped
    `check_workspace(root, workstream=…)` equals the new golden
    `check-workstream.json` (0.2 shape incl. `by_code` buckets and
    `outside_scope`); CLI exit consistent.
16. `test_unscoped_legacy_store_empty_scope` — the golden store (all
    records unscoped): any slug yields an empty scoped view (counts 0,
    `by_code` `{}`, `outside_scope` `{errors: 0, warnings: 1}`, exit 0)
    while the global report still carries `empty_topic_goal` — the
    real-store reality, not a classification.
17. `test_by_code_per_level_same_code` — one in-scope record with a `git:`
    external pin (error) and one in-scope record with a local `git:` pin in
    a non-Git work tree (warning): `by_code == {"invalid_git_ref":
    {"errors": 1, "warnings": 1}}` while `counts.errors == 1` and
    `counts.warnings == 1`, and both findings appear in the scoped
    `findings` with their own levels — freezing the per-level bucket
    semantics.
18. `test_outside_scope_derived` — a store with in-scope findings **and**
    global-only findings (out-of-scope, unscoped, malformed, duplicate,
    TOPIC): `counts.outside_scope` equals the global totals minus the
    scoped totals **exactly**, per level; `outside_scope` never appears in
    `findings` or `by_code`; a clean scope with global-only findings still
    exits 0 with non-zero `outside_scope`; a scope containing every finding
    of the store reports `outside_scope` `{errors: 0, warnings: 0}`.
19. `test_scoped_subset_invariant` — the §3 invariant, asserted exactly:
    `scoped["findings"] == [f for f in global_run["findings"] if f["path"]
    in {p for admitted in-scope records}]`, element-wise equal (same
    levels/codes/messages, global order preserved); the global run used for
    the comparison is a separate `check_workspace(root)` call on the same
    store, byte-identical to the no-flag output.

**Pre-declared amendment** (the only edit to an existing test file; per
§Supersession): in `tests/ledger/test_workstreams.py` —
`test_check_workstreams_finding_and_global`, replace the block

```python
misuse = run_cli(root, "check", "--workstream", "crpa", "--json")
assert misuse.returncode == 2
assert "usage:" in misuse.stderr
```

with a scoped-valid assertion: the same command exits **0** with schema
`aitp/check-report-0.2`, an empty scoped view (the test store's only record
has an invalid `workstreams` field and is unattributable), and
`counts.outside_scope` carrying the global `invalid_workstreams` error
(`{"errors": 1, "warnings": 0}`); and amend the file docstring sentence
"`check` gains no scope flag and keeps `aitp/check-report-0.1`" to
"`check` gains the M1d single-slug `--workstream` flag variant
(`aitp/check-report-0.2`; without the flag `aitp/check-report-0.1` is
byte-unchanged)". No other assertion in the file changes.

Gate checklist (recorded in `docs/m1d-stage-notes.md` at gate time): the
full ledger suite — **107 tests, including the one pre-declared amendment
to `test_workstreams.py`** — plus the **19 new tests** in
`test_check_workstream.py` (**126 total**), the existing benchmark
thresholds unchanged (`--help` < 250 ms; 1,000-Entry `enter`/`list` < 1 s),
per-module < 400 and cumulative **≤ 1,550 (binding target; an over-target
draft stops per §Over-budget rule) / ≤ 1,600 (hard cap — absolute
ceiling)** line counts, version sync 0.5.0 across all four version
surfaces, and the real-store acceptance below.

## Real-store acceptance (GW_librpa and yangian, operator, in place, read-only)

The real stores are compatibility evidence, not test namespaces. Uses the
exact bundled launcher with the Skill's interpreter probe order. On the live
store:

1. **No-flag parity**: `check --json` and `check` (text) are byte-identical
   before and after the change set (payloads against the pre-change recorded
   outputs; old-runtime vs. current-runtime parity as in the M1c gate).
2. **Scoped runs** on `/home/bhjia/physics/GW_librpa` with
   `--workstream crpa`, `--workstream magnetic-symmetry`, and
   `--workstream qsgw-semiconductor`: observed exits and payloads recorded
   verbatim in the stage notes; because the store's records are legacy
   **unscoped**, every scope is expected to be an **empty scoped view**
   (counts 0, `by_code` `{}`, exit 0) with `outside_scope` equal to the
   observed global totals — this proves empty-scope compatibility and the
   derived `outside_scope` indicator, not classification. On the
   `yangian-power-law-heisenberg-chain` store used in the 2026-08-14 session
   (the same live store whose global report is ≈ 54 KB; it carries scoped
   records, e.g. `--workstream algebra-flow`), the observed exit, the
   `by_code` buckets, the `outside_scope` totals, and the small scoped
   text/JSON sizes are recorded verbatim — including that the scoped text
   stays exactly four lines on a store whose global report is tens of
   kilobytes.
3. **Zero-write**: `find .aitp -type f -print0 | sort -z | xargs -0
   sha256sum` before/after diff is **empty** on every store touched. No
   record is written; exits and payloads are mutually consistent per §7.

## Version and docs sync (same change)

- **Version**: the plugin version becomes **0.5.0** in
  `kimi.plugin.json`, `.codex-plugin/plugin.json` (with its current UTC
  timestamp suffix `+codex.<YYYYMMDDHHMMSS>`), `pyproject.toml`, and
  `scripts/vendor/aitp/__init__.py` (`aitp.__version__`).
  `aitp/check-report-0.2` versions independently; `aitp/check-report-0.1`
  stays unchanged and is still emitted whenever the flag is absent;
  `aitp/enter-0.2`/`-0.3`, `aitp/list-0.1`/`-0.2`, `aitp/show-0.1`, and the
  `lite-*` file schemas are unchanged. Do not modify the untracked
  `uv.lock`.
- **Docs**: the same change updates all status surfaces with **M1d
  implementation in progress; deterministic gate pending** (no gate claim):
  `AGENTS.md` (current CLI surface: `check` gains the single-occurrence
  `--workstream` flag and `aitp/check-report-0.2`; the "check has no scope
  flag" wording is additively revised per §Supersession), `README.md`
  (stage table + current checkpoint + current state + CLI surface),
  `docs/design.md` (commands + schema list), `docs/roadmap.md` (stage table
  M1d row + M1d section + current state; the M1c row/closure wording is
  amended only to record that M1d additively supersedes the "no scope flag"
  sentence for the scoped projection; **§Trust model and §Python boundary
  sweep**: the outdated "M1b-R1 `aitp check` (v0.1-only, …)" and "…
  whole-store diagnostic (v0.1-only, schema `aitp/check-report-0.1`)"
  phrasings are updated to "two read-only transports —
  `aitp/check-report-0.1` no-flag / `aitp/check-report-0.2` scoped — while
  the **diagnosed file schemas remain the shipped v0.1 ones**
  (`aitp/lite-entry-0.1`/`aitp/lite-note-0.1`)"), the `docs/hakimi/`
  handoff (README amendment + phased plan + compatibility-matrix rows and
  red lines: the `check` row gains the scoped `aitp/check-report-0.2`
  contract incl. `by_code`/`outside_scope` semantics, **§5 red line 9's**
  "`check` has no scope flag" wording is replaced by the M1d rule, the
  schema table gains `aitp/check-report-0.2`, and the matrix records that
  scoped `counts.entries`/`counts.notes` are **admitted in-scope** counts
  that are **not directly comparable across schemas** —
  `aitp/check-report-0.1` vs `aitp/check-report-0.2` differ by definition;
  compare only within one schema version), the `using-aitp` Skill (teach
  only the M1d surface with the in-progress status; §Claims and boundaries
  language, plus: unscoped legacy records are in **no scope**, so an empty
  scope / exit 0 may simply mean **nothing is attributable**, not health;
  scoped health is meaningful only once records explicitly carry
  `workstreams` — new scoped records or a **reviewed manual backfill**
  (M1d never backfills); scoped `enter` warnings stay **global** while
  scoped `check-0.2` `counts.warnings` is **scoped**, with `outside_scope`
  carrying the difference), and the new stage-notes artifact
  `docs/m1d-stage-notes.md` (gate evidence, **created at gate time, not
  before**).
- **Tests**: the same change includes the pre-declared amendment to
  `tests/ledger/test_workstreams.py` (§Tests) and the new
  `tests/ledger/test_check_workstream.py`.
- **Frozen**: `docs/m1b-spec.md` and every existing file in `docs/archive/`
  are not modified (this spec is the only new archive file); `suite/` stays
  frozen and unchanged; M1d has no suite deliverable; the untracked
  `feedback/2026-08-14-*.md`, `ref/`, and `uv.lock` are not modified.

## Over-budget rule (fail-stop; no contract cuts)

The frozen contract — including the **exactly-four-lines** scoped text (§6)
— is not cuttable: no text line, no JSON key, no invariant may be dropped
to save lines. The target is **1,550** cumulative nonblank lines (binding)
and the cap is **1,600** (hard, absolute); both are ceilings, never
budgets.

If the implementation session's draft exceeds the binding target, proceed
in this order — before any acceptance:

1. **Contract-preserving implementation economy**: reclaim nonblank lines
   without changing any frozen surface — one shared `_scoped_counts`
   helper, one filter pass, no duplicated loops, no repeated inline
   expressions, reusing `_in_scope`/`_validate_scope` verbatim.
2. **If the draft still exceeds 1,550: stop.** Do not implement, do not
   mark the stage done, do not claim the gate; do not modify any frozen
   surface (schema, the four text lines, invariants, test contracts) and do
   not expand the cap. The over-budget draft is reported and returns to
   adjudication.

There is no cut list: the four text lines, `aitp/check-report-0.2`
(additive top-level `workstream`, `counts.by_code`, `counts.outside_scope`,
frozen key order), the attribution rule (§2), the scoped-subset invariant
(§3), relations-global-then-scope (§4), scoped counts semantics, exit 0/1/2
and payload-exit consistency, zero-write, no-flag byte-identity of
`aitp/check-report-0.1` JSON and text, empty-scope validity, and v0.1
compatibility are all **never cut**. Do not expand scope to absorb slack.

## Claims and boundaries (Skill/claim language)

M1d's gate claims only deterministic implementation and read-only
compatibility. The scoped projection **solves or alleviates** the observed
frictions it names in §Natural-demand evidence — a per-workstream health
signal **on stores whose records carry `workstreams`** (a legacy unscoped
store yields an empty scoped view — the empty scope is the signal, not a
health certificate), a small non-truncating scoped text, and an explicit
`outside_scope` level-delta indicator. It does **not** claim any of the
following, and the `using-aitp` Skill (updated in the same change) must not
teach them:

- **`by_code` is not a drift-vs-damage classification.** It is a
  deterministic per-code, per-level tally of scoped findings. Whether a
  `hash_mismatch` is "expected historical pin drift" or "current evidence
  damage" is a human judgment informed by the tally — the runtime never
  makes that call (§Explicit prohibitions).
- **A scoped `clean`/exit 0 is not a whole-store health certificate.** It
  claims only "no attributable findings for this workstream"; global
  findings outside the scope are surfaced (not classified) by
  `outside_scope`, and the no-flag run remains the whole-store instrument.
- **M1d does not fix handoff staleness** (closeout-first handoff is
  unchanged; roster H remains dropped) **and does not change exit-1
  semantics** — exit codes are byte-identical; the flag gives recovery
  scripts a per-workstream signal, nothing more.
- **M1d does not reduce write friction**: prepare/refs/pin-collection
  friction (Followup 6, roster D) is untouched and deferred.
- **No behavioral, treatment/control, causal, or treatment-advantage
  evidence** is claimed; no claim that scoped `check` improves research
  outcomes; FROZEN v6 remains an anchored, unexecuted preregistration.

## Explicit prohibitions

- No registry, catalog, enumeration, or new `aitp workstream` command; no
  new canonical or local file; no new schema besides the additive
  `aitp/check-report-0.2` transport.
- No repair: no `--fix`, no migration, no reclassification, no rewriting of
  records or pins; `check` stays zero-write in both modes.
- **No semantic inference of any kind**: the scoped projection is a
  deterministic per-record predicate. M1d does **not** classify findings as
  "historical pin drift" vs. "current evidence damage", does not compare
  reports across runs (no baseline/delta runtime — manual `diff`/`rg` over
  saved deterministic JSONs is the query path), and does not rank, judge,
  or suggest fixes. `by_code` is a tally, never a diagnosis.
- No lineage projection, no remote pointer/evidence manifest (roster D), no
  structured prepare input or prepare-template `at` hint (Followup 6), no
  handoff/next-action changes, no `enter`/`list`/`show`/`record`/`note`
  changes — deferred candidates produce no code and no schema.
- No repeatable `--workstream` on `check` (single slug only; a repeated
  flag is parser-rejected misuse); no union or implicit "shared" scope;
  unscoped records never appear in any scoped view.
- No flag ⇒ byte-identical `aitp/check-report-0.1` JSON and text; the
  scoped code paths never run and never alter the no-flag output.
- No `malformed` key in `counts`; `outside_scope` carries level totals only
  — no paths, no codes, no effect on `findings`/`status`/exit.
- No new dependencies; no MCP/daemon/hook/vector service; no index, cache,
  lock, or persistent state.
- Frozen inputs untouched: `docs/m1b-spec.md`, every existing
  `docs/archive/` file (including `docs/archive/m1c-workstreams-spec.md`),
  `suite/` (`FROZEN.md` and everything under `suite/`), the untracked
  `feedback/2026-08-14-*.md`, `ref/`, and `uv.lock`.
