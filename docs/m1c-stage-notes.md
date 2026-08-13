# M1c stage notes — Topic workstreams deterministic gate closure

Status: **done; deterministic gate passed** — M1c is implemented and shipped.

Evidence date: 2026-08-13. Final gate run (UTC): `2026-08-13T15:49:34Z`.

Review HEAD: `29c75e82` (the pre-M1c implementation commit the frozen spec
measured; the gate measures the working-tree delta on top of it).

M1c (Topic workstreams) is closed as an implementation and deterministic
regression stage under the frozen implementation spec
[`docs/archive/m1c-workstreams-spec.md`](archive/m1c-workstreams-spec.md)
(2026-08-13). Its natural-demand evidence is the 2026-08-13 workstreams
natural-use feedback
([`feedback/2026-08-13-gw-librpa-workstreams-natural-use-feedback.md`](../feedback/2026-08-13-gw-librpa-workstreams-natural-use-feedback.md)):
one GW_librpa store sharing source/build/provenance across three research
lines (crpa, magnetic-symmetry, qsgw-semiconductor) with no membership field
in the records and global handoff/failure/Note recovery costs. M1c is a
**separate stage slice**: independent of the frozen M1b roster
(`docs/m1b-spec.md` §0.1 dispositions unchanged) and of M3 (workstreams live
inside one Topic store; the M3 design option, its gates, and the
`catalog`/`link` absence are untouched).

This closure does **not** claim behavioral superiority, treatment-over-control
advantage, causal effect, or that manually assigning workstreams improves
research outcomes. It proves only that the frozen M1c contract is implemented
deterministically and read-only. The real store was **not migrated** and has
**no workstreams written** to any record, so practical use starts with new
records carrying `workstreams`, or with a reviewed manual backfill.

## Functionality (frozen exact contract)

The frozen contract in `docs/archive/m1c-workstreams-spec.md`, implemented
and gated:

- optional non-empty, no-duplicate `workstreams` list on Entries/Notes
  (file schemas unchanged); absence = **unscoped legacy**, valid and
  visible only in the unfiltered global view;
- membership **explicit and multi-valued**, never inferred — a cross-line
  record lists all its workstreams;
- `record prepare`/`note prepare`: **repeatable** `--workstream <slug>` flag
  seeding the draft's list in flag order; a repeated identical slug is
  rejected as a duplicate (no silent dedup); envelopes unchanged;
- `enter`/`list`: **single-occurrence** `--workstream <slug>` (a repeated
  flag is parser-rejected misuse) emitting `aitp/enter-0.3`/`aitp/list-0.2`
  — old payload plus one additive top-level **singular `workstream`** key;
- **relations run on the whole store first** (global superseded/resolved
  sets), then the projections including the `next_action` handoff are
  **strictly scoped** — an out-of-scope handoff is never shown;
- `warnings`, `counts.malformed`, `memory_status`, and `check` are
  **global** (`check` has no scope flag);
- **no registry** — no new file or command, no index, no migration;
  `show`/`check` contracts unchanged;
- **no flag ⇒ byte-identical old contracts** (`aitp/enter-0.2`,
  `aitp/list-0.1`).

## Gate checklist

All items frozen in `docs/archive/m1c-workstreams-spec.md` §Tests /
§Real-store acceptance / §Version and docs sync passed:

- [x] Independent review — three read-only review passes, final result **no
      S0 blocker**; the findings raised were all resolved **before** the gate
      run (see §Independent review below).
- [x] Full ledger suite: **107 passed** (85 unchanged tests + 22 new
      `tests/ledger/test_workstreams.py` tests, including the regression
      coverage added for the review findings); `test_plugin.py`,
      `test_distribution.py`, `test_release_sync.py`, and `test_golden.py`
      included.
- [x] Benchmark **final PASS** (Python `3.12.13`, linux x86_64): module and
      plugin `--help` medians < 250 ms; module/plugin 1,000-Entry
      `enter`/`list` medians < 1,000 ms. The benchmark pass condition now
      includes `list` (`tests/ledger/benchmark.py` thresholds unchanged from
      M1a; pass = all six medians under their thresholds).
- [x] Per-module < 400 nonblank lines; cumulative **1,519** — within the
      target ≤ 1,550 and the hard cap ≤ 1,600 (81-line margin to the cap).
- [x] Version sync **0.4.0** on all four surfaces (see §Version and frozen
      boundaries).
- [x] Real-store acceptance on `/home/bhjia/physics/GW_librpa`: 578 `.aitp`
      files hashed, **byte-identical before/after**; old-runtime vs
      current-runtime parity and scoped read compatibility verified (see
      §Real-store acceptance).
- [x] `git diff --check` clean; goldens, S1/S2 deterministic regression, and
      release sync are covered by the 107-test suite. Frozen spec and every
      existing `docs/archive/` file are unchanged; `suite/` has no tracked
      diff; `uv.lock` untouched.

## Independent review

Three independent read-only reviews of the M1c working tree were run before
the gate. Final result: **no S0 blocker**. This closure does not claim "no
S1/S2 findings" — findings were raised and **all were fixed before the gate
run**:

- **One S1 (code review):** the unscoped (no-flag) `enter` output ordering
  for `invalid_timestamp` warnings on Notes with invalid timestamps had
  diverged from the old runtime. Fixed before the gate; new regression
  coverage in `tests/ledger/test_workstreams.py` checks the legacy descending
  order and confirms scoped warnings remain identical to the global warning
  list. The live-store old-runtime parity check independently verifies the
  final no-flag payload is byte-identical.
- **S2 gaps (API/document/benchmark):** API-surface gaps, documentation
  status text, and benchmark pass-condition items raised by the reviews were
  all corrected before the gate run.

## Test suite

```text
$ .venv/bin/python -m pytest tests/ledger -q
107 passed in 16.91s
```

The 107 tests comprise the **unchanged** ledger suite (85 tests: CLI, core,
adopt, inventory, golden, query, plugin, distribution, release sync,
diagnostics) plus the **22** new `tests/ledger/test_workstreams.py` tests
specified in `docs/archive/m1c-workstreams-spec.md` §Tests (prepare flag
seeding and duplicate/invalid-slug rejection, save-path validation, unscoped
legacy validity and no-flag schema byte-parity, scoped `enter`-0.3/`list`-0.2
schema and post-filter, global malformed/memory/warnings, scoped handoff,
list composition with kind/since filters, global superseded/resolved sets,
single-occurrence flag enforcement, scoped text line, `check` finding and
globality, CLI misuse, read-only byte identity and determinism) plus the
regression coverage added for the review findings.

## Benchmark

Benchmark: **final PASS**, Python `3.12.13` linux x86_64. Thresholds:
`--help` < 250 ms; 1,000-Entry `enter` < 1,000 ms; 1,000-Entry `list` <
1,000 ms (the pass condition was revised to include `list` in
`tests/ledger/benchmark.py`; the frozen threshold values are unchanged from
M1a).

```text
module_help           58.809 ms
plugin_help           63.192 ms
module_enter1000     543.430 ms
plugin_enter1000     514.352 ms
module_list1000      572.582 ms
plugin_list1000      550.866 ms
```

All six medians pass their thresholds.

## Runtime budget

Canonical runtime (`plugins/aitp-research-protocol/scripts/vendor/aitp/`,
nonblank lines, `grep -c '\S'` per module, summed): **1,519 total** — within
the target ≤ 1,550 and the hard cap ≤ 1,600 (81-line margin to the cap);
delta from the M1b-R1 actual (1,423) = **+96**. Every module stays below 400;
per-module maximum `records.py` = 348.

```text
__init__.py      2
__main__.py      2
cli.py         221
core.py         28
diagnostics.py  78
md.py           63
notes.py       156
query.py       179
records.py     348
state.py       107
workspace.py   335
TOTAL         1519
```

## Version and frozen boundaries

- **Version 0.4.0** on all four surfaces: `kimi.plugin.json` `"0.4.0"`;
  `.codex-plugin/plugin.json` `"0.4.0+codex.20260813145756"` (the UTC
  timestamp suffix currently actually read by the Codex plugin load);
  `pyproject.toml` `version = "0.4.0"`;
  `scripts/vendor/aitp/__init__.py` `__version__ = "0.4.0"`. No
  `aitp --version` flag is added. `aitp/enter-0.3`/`aitp/list-0.2` version
  independently; `aitp/enter-0.2`, `aitp/list-0.1`, `aitp/show-0.1`,
  `aitp/check-report-0.1`, and the `lite-*` file schemas are unchanged.
- **Frozen boundaries**: `docs/m1b-spec.md` and every existing file in
  `docs/archive/` are unchanged; `suite/` has no tracked diff (M1c has no
  suite deliverable); FROZEN v6 and all frozen inputs remain untouched; the
  untracked `uv.lock` is untouched. `git diff --check` is clean.

## Real-store acceptance (GW_librpa, operator, in place, read-only)

`/home/bhjia/physics/GW_librpa`, 2026-08-13, with the exact bundled launcher
(Skill interpreter probe order):

- **Tree zero-write**: 578 `.aitp` files hashed before and after; diff
  **empty** — byte-identical.
- **Old-runtime vs current-runtime parity (unscoped)**: the pre-M1c runtime
  (`git archive HEAD`) and the current runtime were run on the **same real
  store**: unscoped `enter --json` and `list --json` both exit 0, and
  stdout/stderr are **byte-identical** between the two runtimes. Current
  stdout sizes: `enter` 82,861 bytes; `list` 169,260 bytes. No flag ⇒ old
  contracts unchanged, proven against the old runtime itself on the live
  store.
- **Scoped runs** with `--workstream crpa`,
  `--workstream magnetic-symmetry`, and `--workstream qsgw-semiconductor`:
  `enter`/`list` all exit 0, schemas `aitp/enter-0.3`/`aitp/list-0.2`,
  additive singular `workstream` correct per scope. Because all 274 entries
  and 3 notes in the store are legacy **unscoped** records, every scope's
  `active`/`superseded`/`unresolved`/`recent`/`list` counts are **0** and
  `warnings` is **1** per scope — this proves the **empty scoped-view
  compatibility**, not that records are already classified or migrated.
- **`check --json`**: exit **1** (findings — the successful-findings
  exit), schema `aitp/check-report-0.1`, counts `{entries: 274, notes: 3,
  errors: 200, warnings: 2, findings: 202}`, stderr empty, and the `.aitp`
  tree is still byte-identical after the run. No scientific state is
  interpreted here and no claim is made that the errors are caused by M1c —
  `check` grades contracts, not the science.

## Boundaries and no claims

- **Done/shipped means the deterministic gate passed for the frozen M1c
  slice only.** M2, M3, and M4 remain blocked design options; passing the
  M1c gate flips no M1b disposition and reopens nothing.
- **No claims**: no behavioral superiority, treatment/control, causal, or
  treatment-advantage evidence; no proof that manual workstream assignment
  improves outcomes; no bootstrap validation; FROZEN v6 remains an anchored,
  unexecuted preregistration. M1c is an implementation-stage decision
  justified by observed pain points, not a scored experiment.
- **Real store untouched by M1c**: no record was written, migrated, or
  classified; users start using workstreams with new records that carry the
  field, or with a reviewed manual backfill.
