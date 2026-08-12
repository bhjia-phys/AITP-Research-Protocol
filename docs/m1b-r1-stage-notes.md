# M1b-R1 stage notes — deterministic gate closure

Status: **done; deterministic gate passed**

Evidence timestamp (UTC): `2026-08-12T12:34:22Z`

Review HEAD: `b3396e29e33885f7e07b208bbcf49ddd8cb0413d`

M1b-R1 is closed as an implementation and deterministic-regression stage under
the frozen implementation-level spec [`docs/m1b-r1-spec.md`](m1b-r1-spec.md)
and the 2026-08-12 reviewed freeze revision
([`docs/m1b-adjudication.md`](m1b-adjudication.md)). **Total M1b denotes only
that the selected R1 slice completed**: A and Followups 1/3/4/5 shipped as R1
(`aitp check` v0.1-only + compact `enter` text); B, C–E, Followup 2
(`lineage`), and Followup 6 (structured prepare) remain deferred; F → M4;
G is an independent Skill track; H is dropped. `lineage` is absent and
deferred.

**Amendment (2026-08-12, same-day precision fix):** the S3-item-1 review note
(§S3 explanations below) exposed one gate-time mismatch with the frozen
per-file rule — a record whose relations step (step 5) failed still had its
refs step (step 6) graded. Fixed: any relation failure in either
`resolves`/`supersedes` fails step 5 and skips step 6 for **that record**
(each field still reports its first failure in fixed field order). One
regression test was added (`test_check_relation_failure_skips_refs_same_record`),
so the suite is **78 tests** (56 unchanged ledger + 22 `test_diagnostics.py`)
and the runtime is **1,423 nonblank lines** (`diagnostics.py` 99 → 101,
delta from M1a +167), still within the 1,425 target and the 1,450 hard cap.
The original gate run (77 tests, 1,421 lines) is retained below as
**pre-amendment history only**; the amended **78 tests / 1,423 lines**
supersede it as the current gate evidence. The test counts, pytest re-run
(`pytest: 78 passed in 11.28s`, 2026-08-12), and runtime table below are
updated for this amendment.

This closure does not claim behavioral superiority, treatment-over-control
advantage, causal effect, bootstrap validation, or that AITP is better than
plain files. The real-store diagnostics prove only **diagnosis and zero-write**,
not research improvement: `check` reports findings about record state; it
neither repairs records nor evaluates the science, and a store with findings
is not "unhealthy" in any research-quality sense.

## Gate checklist

The gate checklist frozen in `docs/m1b-r1-spec.md` §Tests / §Version and docs
sync, all items passed:

- [x] Independent code review with no S0/S1/S2 blockers (review agent-153);
      S3 explanations recorded in §S3 explanations below.
- [x] All 22 new `test_diagnostics.py` tests plus the **unchanged** ledger
      suite (56 tests) — **78 passed** (amended for the S3-item-1 fix
      regression, see §S3 item 1); `test_plugin.py` and
      `test_distribution.py` included.
- [x] Benchmark **final PASS** (Python `3.12.13`): `--help` < 250 ms and
      1,000-Entry `enter`/`list` < 1 s; thresholds unchanged from M1a; results
      in §Benchmark.
- [x] Per-module < 400 nonblank lines and cumulative ≤ 1,450 (actual
      **1,423**, amended current; the pre-amendment gate run measured 1,421 —
      still within the target 1,425); delta from M1a (1,256) = **+167**; max
      module `records.py` = 327.
- [x] Version sync: plugin version **0.3.0** across all four surfaces
      (`kimi.plugin.json`, `.codex-plugin/plugin.json` with UTC timestamp
      suffix, `pyproject.toml`, `scripts/vendor/aitp/__init__.py`); no
      `aitp --version` flag added; `uv.lock` untouched.
- [x] Golden fixtures: `check.json` (findings; counts `{entries: 7, notes: 2,
      errors: 0, warnings: 1}`; single `empty_topic_goal` warning; exit 1) and
      the compact `enter.txt`; M1a `enter` JSON goldens unchanged by R1.
- [x] Deterministic S1/S2 seed regression on fresh copies: `check` clean on
      both seeds (exit 0), `enter` text renders with both frozen safety lines,
      copies byte-identical before/after; seeds never modified.
- [x] Bundled-launcher read-only real-store acceptance: GW_librpa (537 `.aitp`
      files byte-identical) and Power-law Heisenberg (323 files byte-identical);
      `check` exit recorded as observed and consistent with the report.
- [x] Suite boundary: `suite/` has no tracked diff; FROZEN v6 and all frozen
      inputs unchanged (R1 has no suite deliverable); `uv.lock` remains
      untracked/untouched (gate hash `3f27da37…`, size 15,876).

## Independent code review (agent-153)

The independent code review of the R1 working tree reported **no S0/S1/S2
blocker**. The review verified, and this closure records as passed:

- the full test surface (77 tests at review time; 78 after the same-day
  S3-item-1 precision-fix amendment) and the CLI/exit-code contracts;
- the zero-write/read-only contract of `check` (no lock, cache, index, repair,
  migration) and the byte-identity test;
- the v0.1-only boundary (no diagnostics for unselected M1b schemas);
- version sync 0.3.0 across all four surfaces;
- the suite boundary (no tracked suite diff; `uv.lock` untouched).

The review's remaining recordable items are explained in §S3 explanations.

## S3 explanations (recorded, non-blocking)

These are the review's non-blocking (S3) items with their explanations, plus
the two gate-scope clarifications they prompted:

1. **Relations failure and refs — same-record short-circuit.** The review
   raised a relations-related failure and a refs-related independent finding.
   They are **independent findings across records**: in the frozen per-file
   rule (`docs/m1b-r1-spec.md` §Per-file rule) relations grading (step 5)
   and refs grading (step 6) are separate steps in fixed order, and the
   first failing step excludes the **same file** from the remaining steps —
   so a relation failure in either `resolves`/`supersedes` field fails
   step 5 for **that record** and its step 6 (refs) is skipped, while a
   finding on one record can never cause or mask a finding on another
   record (each record's steps run independently; a bad-ref-only record is
   still graded). The gate-time implementation graded refs even after a
   relations failure on the same record; a same-day precision fix aligns it
   with the frozen rule (each relation field still reports its first
   failure in fixed field order; any relation failure skips refs for that
   record). The fix is covered by the new regression test
   `test_check_relation_failure_skips_refs_same_record`: one Entry with
   both a relation failure and a bad ref produces **only** the relation
   finding (`missing_relation`, exact path and message), a separate
   bad-ref-only Entry still produces its ref finding (`missing_ref`), and
   two runs are byte-identical. Relation, ref, and pin-matrix cases remain
   covered by the other `test_diagnostics.py` tests and by the golden
   store, where all relations resolve and only the `empty_topic_goal`
   warning fires. Neither item is a blocker; the corrected behavior matches
   the frozen spec.
2. **Prototype is not gate evidence.** The 1,413-line prototype measurement
   recorded in `docs/m1b-r1-spec.md` §Implementation map is explicitly
   author-reported development evidence, not a gate result. The gate
   re-measures the actual implementation independently: **1,421 nonblank
   lines** (per-module table in §Runtime budget), within the 1,425 target and
   the 1,450 hard cap; `diagnostics.py` 99 and `records.py` 327 differ from
   the prototype's 94/324, so the spec's prototype figures remain historical
   development evidence and are superseded by this re-measurement for gate
   purposes. The S3-item-1 precision fix (above) added 2 nonblank lines to
   `diagnostics.py`, so the amended gate-time total is **1,423** (1,421 +
   2; per-module `diagnostics.py` 101, `records.py` 327) — still within the
   1,425 target and the 1,450 hard cap.
3. **`uv.lock` hash.** `uv.lock` is deliberately untracked and untouched by
   R1 (no new dependencies). Its gate-time SHA-256 is recorded as evidence of
   no dependency churn: `3f27da37babf76bc2723a063639010d1bbd9705416910798ec705b05e826c354`,
   size 15,876.
4. **`enter` JSON indirect parity.** The spec requires `aitp/enter-0.2` JSON
   byte-unchanged. Parity is verified indirectly: the renderer is text-only —
   a pure function of the existing payload with no payload-producing change —
   test `enter_text_compact` asserts `enter --json` is byte-identical
   before/after the renderer change, and the M1a JSON goldens
   (`enter.json`, `enter-after-save.json`) carry no R1-attributable diff.
5. **Benchmark environment jitter → final PASS.** Early benchmark runs on the
   recorded machine showed run-to-run environment jitter (shared machine).
   The pre-amendment gate run passed, and the same-day precision-fix amendment
   was followed by the independent amended benchmark recorded below; both are
   **PASS** on Python `3.12.13` with all thresholds met.

## Test suite

```text
pytest: 78 passed in 11.28s
```

The pre-amendment gate-run record was `pytest: 77 passed in 28.62s`
(independently re-run at closure: `77 passed`, 11.89 s on the closing
session's machine — wall time varies with the machine). Those 77-test runs
are **pre-amendment history only**: after the S3-item-1 precision fix the
suite is **78 tests** and was re-run in full on the fix session's machine:
`pytest: 78 passed in 11.28s` (2026-08-12), superseding them as the current
gate evidence. The 78 tests comprise the
**unchanged** ledger suite (56 tests: CLI, core, adopt, inventory, golden,
query, plugin, distribution) plus the 22 `test_diagnostics.py` tests
specified in `docs/m1b-r1-spec.md` §Tests (exit codes 0/1/2, JSON report
schema, read-only byte identity, error/warning grading, deterministic
ordering, pin matrix, duplicate rules, per-file counts, Note rules,
relation-failure/refs same-record short-circuit regression, compact `enter`
text, save envelope exactness, save-pin parity, CLI misuse, seed
regression).

## Benchmark

Benchmark: **final amended PASS**, Python `3.12.13` (thresholds unchanged
from M1a: `--help` < 250 ms; 1,000-Entry `enter` < 1,000 ms; `list` is
report-only). The amended run after the relation/refs precision fix recorded:

```text
module_help         45.286 ms
plugin_help         46.133 ms
module_enter20      56.312 ms
module_enter1000   462.441 ms
plugin_enter20      53.527 ms
plugin_enter1000   450.033 ms
module_list1000    469.552 ms
plugin_list1000    469.120 ms
```

All thresholds pass. The pre-amendment gate run also passed (`module_help`
228.149 ms, `plugin_help` 194.792 ms, `module_enter1000` 485.048 ms,
`plugin_enter1000` 486.239 ms; list baselines 527.944 / 555.921 ms), but the
amended run above supersedes it as the current performance evidence.

## Runtime budget

Canonical runtime (`plugins/aitp-research-protocol/scripts/vendor/aitp/`,
nonblank lines, `grep -c '\S'`): **1,423 total** (1,421 at the pre-amendment
gate run, amended +2 by the S3-item-1 fix), delta from the M1a actual (1,256)
= **+167** — within the 1,425 target and the 1,450 hard cap (27-line margin
to the cap). Every module stays below 400.

```text
__init__.py      2
__main__.py      2
cli.py         189
core.py         28
diagnostics.py 101
md.py           63
notes.py       143
query.py       146
records.py     327
state.py       106
workspace.py   316
TOTAL         1423
```

Per-module maximum: `records.py` 327 (< 400). `diagnostics.py` is the new
R1 module (101 nonblank lines, amended from 99 by the S3-item-1 fix); the
only other R1-bearing modules are the ones named in the spec's
implementation map (`cli.py`, `core.py`, `md.py`, `records.py`,
`workspace.py`).

## Goldens

Generated from the public API exactly as `tests/ledger/test_golden.py`
documents; `root` normalized to `<golden-store>`; no hand-edited payloads:

- **`check.json`** — `check_workspace` on the golden store: `status`
  `"findings"`; `counts {entries: 7, notes: 2, errors: 0, warnings: 1}`;
  the single finding is the `empty_topic_goal` warning on
  `.aitp/topic/TOPIC.md`; CLI exit **1** (findings), consistent with the
  report. All golden pins are valid `sha256`, relations resolve, and
  timestamps parse — nothing else can fire.
- **`enter.txt`** — the compact text renderer on the golden store: both
  frozen M1a safety lines present (`recent_entries: 6 of 6 active (0
  omitted)`; `recent_notes: 2; latest_working_note: note-1111… @
  2026-07-06T12:00:00.000001Z; active_newer: 0`); `goal_status:
  not_established`; `unresolved_failures: 1`; the `next_action` line with
  the handoff source; **no** `handoff_status` line (the unresolved failure
  is older than the handoff — the structural condition is false); no
  warnings line.
- **`enter.json` / `enter-after-save.json`** — the M1a `aitp/enter-0.2`
  payload goldens are **unchanged by R1** (byte-identical before/after the
  text-renderer change; see §S3 explanations item 4).

Verified at this closure on a fresh copy of the golden store: `check --json`
matches `check.json` exactly (exit 1) and `enter` text matches `enter.txt`
byte-for-byte; the store copy is byte-identical before/after the command
sequence.

## S1/S2 deterministic seed regression

Fresh `cp -a` copies of `suite/seeds/S1` and `suite/seeds/S2` (the seeds
themselves are never modified), with the bundled launcher:

| Seed | `check` result | `enter` text (both safety lines present) | Byte identity |
|---|---|---|---|
| S1 | status `clean`; counts `{entries: 31, notes: 2, errors: 0, warnings: 0}`; findings `[]`; exit **0** | `topic: mtim — Modified triangular Ising model`; `goal: …` (real goal); `recent_entries: 20 of 29 active (9 omitted)` | `.aitp` byte-identical before/after |
| S2 | status `clean`; counts `{entries: 30, notes: 2, errors: 0, warnings: 0}`; findings `[]`; exit **0** | `topic: blm — Bipartite spin ladder`; `goal: …` (real goal); `recent_entries: 20 of 28 active (8 omitted)` | `.aitp` byte-identical before/after |

Both seeds are clean under the v0.1-only rules (all pins valid, relations
resolve, goals established, timestamps parse) — deterministic, read-only,
zero-write.

## Real-store read-only acceptance (bundled launcher, in place)

Uses the **exact bundled launcher**
(`plugins/aitp-research-protocol/scripts/aitp.py` with the Skill's
interpreter probe order — not `python -m aitp`), per the frozen procedure in
`docs/m1b-r1-spec.md` §Real-store acceptance. The real store is compatibility
evidence, not a test namespace; `.aitp` maps are byte-identical before/after.
The stores are **dynamic**, so these are observed snapshots, not fixed
values, and the `check` exit is recorded as observed — the gate assertion is
that the report payload and the exit code are **mutually consistent**
(findings → exit 1, clean → exit 0), never a fixed exit for a live store.

### GW_librpa (`/home/bhjia/physics/GW_librpa`, 2026-08-12)

- `.aitp`: **537 files before and after, byte-identical**.
- `check --json`: exit **1** (findings); counts `{entries: 254, notes: 3,
  errors: 198, warnings: 2}`.
- Finding codes: `hash_mismatch` 161, `missing_ref` 37, `empty_topic_goal` 1,
  `invalid_timestamp` 1. The historical `invalid_timestamp` warning on
  `entry-97bec98c…` is preserved and reported; drifted local pins are
  reported as errors — the same grading the save path applies — and `check`
  never repairs or hides drift.
- `enter --json` (`aitp/enter-0.2`): active **210**, superseded **44**,
  unresolved **23**, malformed **0**, omitted_active **190**, warnings
  `[invalid_timestamp]`.
- `enter` text: compact renderer with both frozen safety lines;
  `goal_status: not_established` (the GW TOPIC goal is the placeholder).

### Power-law Heisenberg (independent real Topic, 2026-08-12)

- `.aitp`: **323 files before and after, byte-identical**.
- `check --json`: exit **1** (findings); counts `{entries: 43, notes: 2,
  errors: 110, warnings: 0}`; codes `hash_mismatch` 109, `missing_ref` 1.
- `enter --json`: active **33**, superseded **10**, unresolved **0**,
  malformed **0**, omitted_active **13**, `active_newer` **32**,
  warnings `[]`.
- `enter` text: compact renderer with both frozen safety lines; a **real
  goal** (`goal: <text>`, not `not_established`).

Both real stores demonstrate the R1 read-side semantics: readable under
drift, zero-write, deterministic findings, and exit codes consistent with
the reports.

## Version, manifest, and frozen-boundary checks

- **Version 0.3.0** on all four surfaces: `kimi.plugin.json` `"0.3.0"`;
  `.codex-plugin/plugin.json` `"0.3.0+codex.20260812115314"` (UTC timestamp
  suffix); `pyproject.toml` `version = "0.3.0"`;
  `scripts/vendor/aitp/__init__.py` `__version__ = "0.3.0"`. No
  `aitp --version` flag is added. `aitp/check-report-0.1` versions
  independently; `aitp/enter-0.2`, `aitp/list-0.1`, `aitp/show-0.1` are
  unchanged.
- **Manifest hashes (recorded for auditability, 2026-08-12):**
  `kimi.plugin.json`
  `20ed3fffad83af4ad6b4014dd1e89ab05a799a1f0ab7a2c60a6eb08bd450ab1c`;
  `.codex-plugin/plugin.json`
  `2511f777743e8c5d8b8f9452ab9a2de84c5a9b845b9b38378abdc3eb27321e3a`;
  `pyproject.toml`
  `0e12033e3cc296f120e0eabd21cfd0d4a9a05235b7022ae600f8896f7d39446d`;
  `__init__.py`
  `595104f0486ff7d710b9e60a7cfeac3cf8ddfa46f4cd994f4c749ee440ddd1a4`.
- **`uv.lock`**: remains untracked and untouched; SHA-256
  `3f27da37babf76bc2723a063639010d1bbd9705416910798ec705b05e826c354`, size
  15,876 — recorded as evidence of no dependency churn (R1 adds no
  dependencies).
- **Suite**: `suite/` has no tracked diff; FROZEN v6 and all frozen inputs
  remain unchanged; R1 has no suite deliverable.

## Boundaries, no claims, and `check` semantics

- **Total M1b** means only that the selected R1 slice is done. All other
  dispositions are unchanged from the 2026-08-12 reviewed freeze revision:
  B, C–E, Followup 2 (`lineage`), and Followup 6 (structured prepare)
  deferred; F → M4; G independent Skill track; H dropped. `lineage` is
  absent and must not be invoked or described as shipped; deferred rows
  produce no implementation spec and may return only through a new reviewed
  freeze revision.
- **No claims**: no behavioral superiority, treatment/control, causal, or
  treatment-advantage evidence; no bootstrap validation; no recall/
  false-import/human-time, held-out S3, paired S1/S2 scores, cold-start, or
  conformance scores (unchanged from the M0.6/M1a closures; FROZEN v6
  remains an anchored, unexecuted preregistration). R1 is an
  implementation-stage decision justified by observed pain points, not a
  scored experiment, and the real-store findings prove only diagnosis and
  zero-write — not that `check` or compact `enter` improves research
  outcomes, and not that any real store is "healthy" in a research-quality
  sense.
- **`check` semantics (frozen)**: v0.1-only, read-only, zero-write (no lock
  file — never takes `store_lock` — no cache, index, repair, migration,
  scratch, or `--fix`); exit 0 clean / 1 findings / 2 cannot run (not a
  workspace, unreadable store metadata, or CLI misuse); record-content
  problems are never exit 2 — they are findings (exit 1); findings are
  deterministic, sorted by `(path, code, message)`, with no volatile fields,
  so two runs on the same store are byte-identical. `check` grades
  contracts, not science; nothing is called "stale" or "unhealthy" by the
  runtime.
- **`enter` text**: the compact renderer restores the two frozen M1a safety
  lines; `goal_status`/`handoff_status` are structural hints, not semantic
  judgment; `aitp/enter-0.2` JSON is byte-unchanged.
- **Gate scope**: the deterministic gate passed here closes the R1 slice
  only. It does not authorize M2/M3, does not change any other M1b
  disposition, and does not turn the real-store snapshot counts into fixed
  assertions.
