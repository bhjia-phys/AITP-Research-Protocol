# M1d stage notes — Workstream health: single-slug scoped `check` (`aitp/check-report-0.2`) deterministic gate closure

Status: **done; deterministic gate passed** — M1d is implemented and shipped.

Evidence date: 2026-08-14. Final gate run (UTC): `2026-08-14T09:43:00Z`.

Review HEAD: `9f9e8734` (the M1c implementation commit). The frozen M1d
spec's budget references `29c75e82` as the pre-M1c committed base —
1,438 nonblank lines at that ref (verified via `git show 29c75e82`) —
and its 1,519-line M1c-gate figure was measured on the M1c working tree on
top of it. The bound **1,519** baseline is verified here against the M1c
implementation commit `9f9e8734` (via `git show 9f9e8734`); the M1d gate
measures the working-tree delta on top of that commit.

M1d (Workstream health, scoped `check`) is closed as an implementation and
deterministic regression stage under the frozen implementation spec
[`docs/archive/m1d-workstream-health-spec.md`](archive/m1d-workstream-health-spec.md)
(2026-08-14, adjudicated revision). Its natural-demand evidence is the
2026-08-14 feedback chain — three ordinary real-Topic sessions, none of
them an AITP gate or a controlled experiment
([`feedback/2026-08-14-gw-librpa-natural-use.md`](../feedback/2026-08-14-gw-librpa-natural-use.md),
[`feedback/2026-08-14-gw-librpa-qsgw-semiconductor-natural-use.md`](../feedback/2026-08-14-gw-librpa-qsgw-semiconductor-natural-use.md),
[`feedback/2026-08-14-yangian-power-law-heisenberg-chain-natural-use.md`](../feedback/2026-08-14-yangian-power-law-heisenberg-chain-natural-use.md)):
a 201-error/2-warning global wall that mixes missing files with SHA
mismatches on legitimately regenerated files, a scoped `enter` reporting
`memory_status=available` beside a failing global `check`, and a ≈ 54 KB
JSON report that truncates in the terminal. M1d is a **separate stage
slice**: additive to the frozen M1c contract (it supersedes only the M1c
"`check` has no scope flag" rule **for the flag variant**; the frozen M1c
artifacts are never edited and the M1c gate is not reopened), independent
of the frozen M1b roster (`docs/m1b-spec.md` §0.1 dispositions unchanged —
M1d selects no M1b candidate) and of M3 (workstreams live inside one Topic
store; the M3 design option and the `catalog`/`link` absence are
untouched).

This closure does **not** claim behavioral superiority, treatment-over-control
advantage, causal effect, or that scoped `check` improves research outcomes.
It proves only that the frozen M1d contract is implemented deterministically
and read-only. The real external stores were **not** part of this gate
record — no live-store acceptance is claimed here (see §Real-store
acceptance below); the in-suite deterministic evidence stands on its own.

## Functionality (frozen exact contract)

The frozen contract in `docs/archive/m1d-workstream-health-spec.md`,
implemented and gated:

- `aitp check [--cwd PATH] [--json] [--workstream SLUG]` — the flag is
  **single-occurrence** (`_SingleValue`, same action as the M1c
  `enter`/`list` flags): a repeated `--workstream` is parser-rejected
  misuse (exit 2, argparse "may only be given once"); slug validation
  reuses the M1c rule verbatim (`_validate_scope` → `_validate_workstreams`
  in `query.py`), so an invalid slug or `""` raises `invalid_workstreams`
  with the exact M1c messages under the standard JSON error envelope, and a
  non-string API scope raises `invalid workstreams: exactly one slug
  required`; the help string is frozen: `only findings on records that
  explicitly list this workstream (single slug)`;
- **strict admitted explicit membership**: a finding is in the scoped view
  iff its path is an **admitted** record (parse and structural validation
  passed **and** the ID was unique) whose frontmatter `workstreams` list
  **explicitly** contains the slug — malformed, duplicate-ID, unscoped,
  out-of-scope, and `TOPIC.md` findings are never scoped (an invalid
  `workstreams` field is itself unattributable, in any scope);
- **global scan and global relations first**: every run, scoped or not,
  computes the complete global report exactly as today (relations validated
  against the global `entry_map`, so an in-scope resolver/superseder whose
  target exists anywhere in the store validates cleanly), and the scoped
  report is exactly the global report **restricted** to attributable
  in-scope paths — same findings, levels, codes, messages, `(path, code,
  message)` order; nothing is re-sorted, re-graded, or re-worded (the
  frozen subset invariant, asserted exactly by test 19);
- scoped `--json` emits **`aitp/check-report-0.2`**: the complete
  `aitp/check-report-0.1` payload plus exactly three additive changes —
  one top-level **singular** `workstream: "<slug>"` key (appended last; no
  `workstreams` key anywhere), `counts.by_code` (code →
  `{"errors": n, "warnings": m}`, per-level buckets over the scoped
  findings, keys sorted lexicographically, always present, `{}` when
  clean), and `counts.outside_scope` (`{"errors": n, "warnings": m}`, the
  derived **global − scoped** level totals — a pure level delta: no paths,
  no codes, never a finding, never affects `status`/exit; no `malformed`
  key). Frozen key order: top level `schema, status, root, counts,
  findings, workstream`; inside `counts`: `entries, notes, errors,
  warnings, by_code, outside_scope`;
- scoped `counts.entries`/`counts.notes` are the **admitted in-scope**
  canonical files (deliberately different from the global count-every-file
  rule, because malformed files cannot be attributed to any scope);
  `counts.errors`/`counts.warnings` are the scoped findings by level;
  `status` is `"findings"` iff the scoped `findings` list is non-empty;
- scoped text prints **exactly four human-only stdout lines, always —
  including a clean scope** (workstream / check totals / `by_code` compact
  JSON / `outside_scope` with the literal `(run "aitp check" for the whole
  store)` suffix), stderr empty on exits 0/1, no per-finding lines (the
  fixed answer to the 54,469-byte terminal-truncation observation);
- **empty scope is legal**: a well-formed slug with no admitted in-scope
  records yields counts 0, `findings` `[]`, `by_code` `{}`,
  `outside_scope` = the global totals, status `clean`, exit 0 — on a
  legacy store whose records carry no `workstreams`, every scoped view is
  empty, so a scoped `clean` may mean **nothing is attributable, not
  health** (the no-flag run remains the whole-store instrument);
- exit codes, evaluated on the scoped report, are unchanged in mapping:
  `0` clean (zero scoped findings), `1` findings, `2` could not run
  (`not_initialized`, `malformed_store`, `invalid_root`) or CLI misuse;
  payload and exit are mutually consistent (the R1 rule);
- **no flag ⇒ `aitp/check-report-0.1` byte-compatible**: `check_workspace(
  cwd, *, workstream=None)` with `None` short-circuits before any scoped
  computation (the only added no-flag cost is a `_validate_scope(None)`
  no-op), so JSON, text, exit 0/1/2, and zero-write are byte-unchanged —
  golden-tested;
- **zero-write in both modes**: no lock (never takes `store_lock`), no
  cache, no index, no repair, no migration, no scratch, no `--fix` flag.

## Spec selection, freeze, and independent review

- **Selection**: the 2026-08-14 feedback chain is new natural-use evidence
  after the M1c gate, satisfying roadmap §Simplicity rule 2 — runtime work
  requires an explicit roadmap status flip and a separately reviewed
  implementation-level spec selecting the smallest coherent,
  evidence-backed slice. The frozen spec is that document; the same change
  flips the M1d roadmap row (now "done; deterministic gate passed").
- **Freeze after independent review**: the first-draft contract underwent
  an **independent adversarial review**; the adjudicated revision absorbing
  it was frozen 2026-08-14 (spec header and §11). The five adjudicated
  resolutions are recorded in spec §11: duplicate-ID files are never
  attributable (admission requires structure passed **and** ID unique);
  scoped `counts.entries`/`notes` are admitted in-scope counts (the
  deliberate, versioned difference from the global rule); `by_code` uses
  per-level buckets (`code → {"errors": n, "warnings": m}`), resolving the
  level-split ambiguity for codes that grade as both error and warning
  (e.g. `invalid_git_ref`); `outside_scope` is a derived level delta that
  never masks global findings and never labels any workstream's findings
  as "debt" or "damage"; scoped `clean`/exit 0 while the store has global
  findings is intended — the scope's contract is "no attributable findings
  for this workstream".
- **One pre-declared amendment**: the only edit to an existing test file is
  the spec's §Tests amendment of the M1c-era `check --workstream` misuse
  assertion in `tests/ledger/test_workstreams.py` (docstring sentence +
  misuse block, replaced by a scoped-valid assertion: exit 0,
  `aitp/check-report-0.2`, empty scoped view, `outside_scope` carrying the
  global `invalid_workstreams` error). No other assertion in the file
  changes, and the file's test count is unchanged.

## Gate checklist

All items frozen in `docs/archive/m1d-workstream-health-spec.md` §Tests /
§Version and docs sync that this gate record could measure passed; the one
item that could **not** be measured in this environment is recorded below
as not measured, not claimed:

- [x] Independent adversarial review of the first-draft contract; the
      adjudicated revision was frozen before implementation (§Spec
      selection, freeze, and independent review).
- [x] Full ledger suite: **126 passed** — 107 unchanged baseline (including
      the one pre-declared amendment, which replaces assertions without
      changing the test count) + 19 new `tests/ledger/test_check_workstream.py`
      tests, exactly the 126 the frozen spec's §Tests checklist enumerates.
      The bundle/template/Skill distribution assertions (bundled
      natural-use template byte-identity, Skill M1d contract and claim
      boundary teaching, pinned-reference exact-shape survival) are merged
      into these 19 tests; `test_distribution.py` is byte-restored to its
      pre-M1d state in the final tree.
- [x] Benchmark **final PASS** (Python `3.12.13`, linux x86_64): module and
      plugin `--help` medians < 250 ms; module/plugin 1,000-Entry
      `enter`/`list` medians < 1,000 ms (thresholds unchanged; see
      §Benchmark for the measured medians).
- [x] Per-module < 400 nonblank lines; cumulative **1,543** — within the
      binding target ≤ 1,550 (7-line margin) and the hard cap ≤ 1,600
      (57-line margin); delta from the M1c actual (1,519, verified against
      HEAD `9f9e8734`) = **+24** (see §Runtime budget).
- [x] Version sync **0.5.0** on all four surfaces (see §Version and frozen
      boundaries), asserted by `test_release_sync.py`
      `test_published_versions_agree`.
- [x] No-flag byte parity, scoped determinism, zero-write, scoped golden,
      empty-scope validity, and invalid-flag misuse — all asserted in-suite
      (see §In-suite evidence).
- [x] `git diff --check` clean; goldens, the pre-declared amendment, and
      release sync are covered by the 126-test suite. Frozen spec and every
      existing `docs/archive/` file are unchanged; `suite/` has no tracked
      diff; the untracked `feedback/2026-08-14-*.md`, `ref/`, and `uv.lock`
      are untouched.
- [ ] **Real-store acceptance per spec §Real-store acceptance: not
      executed in this gate record** — the live stores sit outside this
      repository and no live-store run (hashing, old-runtime parity, scoped
      payload recording) is claimed here; the feedback files are
      natural-demand evidence, not live acceptance of this runtime (see
      §Real-store acceptance below).

## Test suite

```text
$ .venv/bin/python -m pytest -q tests/ledger
126 passed in 20.63s
```

Two independent runs on the final working tree both pass with the same
count — `126 passed in 24.88s` and `126 passed in 20.63s` — the count is
the invariant, timing varies with load. The measured 126 matches the
frozen spec's §Tests enumeration exactly (107 + 19).

The 126 tests break down as:

- **107 unchanged baseline** — the full pre-M1d ledger suite (CLI, core,
  adopt, inventory, golden, query, plugin, distribution, release sync,
  diagnostics, and the 22 `test_workstreams.py` tests **including the one
  pre-declared amendment**, whose assertions were replaced but whose count
  is unchanged);
- **19 new** `tests/ledger/test_check_workstream.py` tests exactly as
  enumerated in spec §Tests: no-flag byte parity against the `check.json`
  golden, scoped schema and additive keys with frozen key order, strict
  attribution filter, scoped counts and `by_code` sums, relations
  global-then-scope, duplicate-ID exclusion, invalid-`workstreams`
  unattributability, legacy timestamp warning scoping, TOPIC.md exclusion,
  scoped exit codes (incl. repeated-flag misuse and invalid/empty slug
  envelopes), exact four-line text, empty-scope validity, zero-write
  (`hash_tree` before/after), determinism, scoped golden
  (`check-workstream.json`), unscoped legacy empty scope, per-level
  same-code buckets, derived `outside_scope`, and the scoped-subset
  invariant.

The **bundle/template/Skill distribution assertions** of the spec's
§Version and docs sync are merged into these 19 tests — they do not live
in `test_distribution.py`, which is byte-restored to its pre-M1d state in
the final tree. Concretely: `test_no_flag_byte_parity` asserts the bundled
natural-use template link resolves to a file inside the bundle and that
the bundled copy stays byte-identical to the authoritative repo-root
template (`feedback/natural-use-session-template.md`);
`test_unscoped_legacy_store_empty_scope` asserts the Skill teaches the
surface it exercises and its claim boundary (unscoped legacy records are
in no scope; a scoped `clean`/exit 0 may mean nothing is attributable,
not health; scoped health requires records explicitly carrying the slug
or a reviewed manual backfill — the runtime never backfills);
`test_by_code_per_level_same_code` asserts the Skill documents the frozen
ref shape (`target` + `at` + locator) and the mutable-pin discipline for
"evidence that may change".

## Benchmark

Benchmark: **final PASS**, Python `3.12.13` linux x86_64. Thresholds
unchanged: `--help` < 250 ms; 1,000-Entry `enter` < 1,000 ms; 1,000-Entry
`list` < 1,000 ms. Gate-run medians (implementation session):

```text
module_help          48.923 ms
plugin_help          47.199 ms
module_enter1000    475.025 ms
plugin_enter1000    456.881 ms
module_list1000     481.142 ms
plugin_list1000     492.543 ms
```

An independent re-run on the same working tree also passed
(`"result": "PASS"`), medians: `module_help` 47.439 ms, `plugin_help`
47.319 ms, `module_enter1000` 488.516 ms, `plugin_enter1000` 481.419 ms,
`module_list1000` 523.088 ms, `plugin_list1000` 505.155 ms. All six medians
pass their thresholds in both runs; `--help` stays well under 250 ms with
the added flag.

## Runtime budget

Canonical runtime (`plugins/aitp-research-protocol/scripts/vendor/aitp/`,
nonblank lines, `grep -c '\S'` per module, summed): **1,543 total** — within
the binding target ≤ 1,550 (7-line margin) and the hard cap ≤ 1,600
(57-line margin to the cap); delta from the M1c actual (1,519, re-verified
against HEAD `9f9e8734` via `git show`) = **+24**. Every module stays below
400; per-module maximum `records.py` = 348.

```text
__init__.py      2
__main__.py      2
cli.py         229
core.py         28
diagnostics.py  94
md.py           63
notes.py       156
query.py       179
records.py     348
state.py       107
workspace.py   335
TOTAL         1543
```

The +24 lands within the spec's re-estimated touch-point budget
(`cli.py` +8 net: `--workstream` `_SingleValue` flag, `check_workspace(
..., workstream=...)` call, `_emit_check` four-line scoped branch;
`diagnostics.py` +16 net: `workstream=None` keyword with `_validate_scope`,
the attributable `{relative_path: frontmatter}` map from the admitted
`entries`/`notes` item lists, one restriction pass over the globally sorted
findings, per-level sorted `by_code` buckets, derived `outside_scope`,
`aitp/check-report-0.2` payload with `workstream` appended last; `query.py`,
`records.py`, `state.py`, `notes.py`, `workspace.py`, `md.py` unchanged).

## Version and frozen boundaries

- **Version 0.5.0** on all four surfaces: `kimi.plugin.json` `"0.5.0"`;
  `.codex-plugin/plugin.json` `"0.5.0+codex.20260814090722"` (the UTC
  timestamp suffix actually read by the Codex plugin load);
  `pyproject.toml` `version = "0.5.0"`; `scripts/vendor/aitp/__init__.py`
  `__version__ = "0.5.0"` — all four asserted equal by
  `test_release_sync.py`. No `aitp --version` flag is added.
  `aitp/check-report-0.2` versions independently; `aitp/check-report-0.1`
  is unchanged and still emitted whenever the flag is absent;
  `aitp/enter-0.2`/`-0.3`, `aitp/list-0.1`/`-0.2`, `aitp/show-0.1`, and
  the `lite-*` file schemas are unchanged (the diagnosed file schemas
  remain the shipped v0.1 ones in both report transports).
- **Docs sync (same change)**: `AGENTS.md` (CLI surface: `check` gains the
  single-occurrence `--workstream` flag and `aitp/check-report-0.2`, with
  the "no scope flag" wording additively revised per §Supersession),
  `README.md` (stage table, current checkpoint/state, CLI surface),
  `docs/design.md` (commands + schema list), `docs/roadmap.md` (stage table
  M1d row + M1d section + current state; the M1c wording amended only to
  record that M1d additively supersedes the "no scope flag" sentence for
  the flag variant; §Trust model / §Python boundary updated to the
  two-transport wording), `docs/hakimi/` (README + phased plan +
  compatibility-matrix: `check` row gains the scoped
  `aitp/check-report-0.2` contract incl. `by_code`/`outside_scope`
  semantics and the red-line replacement; the matrix records that scoped
  `counts.entries`/`counts.notes` are admitted in-scope counts **not
  directly comparable across schemas** — compare only within one schema
  version), the `using-aitp` Skill (M1d surface, `by_code`-is-a-tally /
  scoped-`clean`-is-not-a-health-certificate claim language, unscoped
  legacy in no scope / empty scope may mean nothing is attributable,
  reviewed-manual-backfill precondition — "the runtime never backfills" —
  the frozen `enter`-global-vs-`check`-scoped warnings asymmetry, the
  `memory_status`-vs-evidence-health working-Note guidance, pinned
  references exact YAML `target`/`at`/locator and "evidence that may
  change" discipline, and the `set -e` exit-code capture guidance with
  fail-closed on exit 2), and this stage-notes artifact. The Skill also
  bundles the natural-use feedback template
  (`plugins/aitp-research-protocol/skills/using-aitp/
  natural-use-session-template.md`), byte-identical to the authoritative
  `feedback/natural-use-session-template.md` — asserted within the M1d
  suite (the bundle/template/Skill assertions are merged into the 19
  `test_check_workstream.py` tests; see §Test suite). In the final tree
  the Skill's M1d section is updated to "shipped; deterministic gate
  passed" with Status "done; deterministic gate passed" — no in-progress
  wording remains.
- **Frozen boundaries**: `docs/m1b-spec.md` and every pre-existing file in
  `docs/archive/` are unchanged (this spec is the only new archive file);
  `docs/m1c-workstreams-spec.md` and `docs/m1c-stage-notes.md` are not
  modified and the M1c gate is not reopened; `suite/` has no tracked diff
  (M1d has no suite deliverable); the untracked `feedback/2026-08-14-*.md`,
  `ref/`, and `uv.lock` are untouched. `git diff --check` is clean.

## In-suite evidence: parity, determinism, zero-write, golden, misuse

- **No-flag byte parity** (test 1): on a golden-store copy,
  `check_workspace(root)` equals the `check.json` golden (0.1 shape, with
  `root` normalized); `check --json` stdout parses to that payload; `check`
  text is exactly `warning[empty_topic_goal]: .aitp/topic/TOPIC.md:
  Research Goal is not established\ncheck: 0 error(s), 1 warning(s)\n`;
  exit 1; no `workstream`/`by_code`/`outside_scope` key anywhere. The
  committed `check.json` golden and the golden store fixture are unchanged
  in this change. The same test carries the merged bundle/template
  assertion: the Skill's natural-use template link resolves to a file
  inside the bundle and the bundled copy stays byte-identical to the
  authoritative repo-root template.
- **Scoped golden** (test 15): the new `tests/ledger/fixtures/golden/
  check-workstream.json` (deliberate regeneration, `root` normalized)
  freezes the 0.2 shape — `schema`, `status: findings`, additive top-level
  `workstream: "crpa"`, `counts` keys `entries, notes, errors, warnings,
  by_code, outside_scope`, per-level `by_code` buckets (`hash_mismatch`
  1 error, `invalid_timestamp` 1 warning), derived `outside_scope`
  `{errors: 3, warnings: 1}`, and the `(path, code, message)`-sorted
  findings.
- **Scoped determinism** (test 14): two scoped runs byte-identical (JSON
  and the four-line text), an unscoped run in between changes nothing, and
  the `.aitp` tree stays byte-identical.
- **Zero-write** (test 13): the `.aitp` tree sha256-identical before/after
  scoped and unscoped runs; no `write.lock` is ever created.
- **Empty scope / legacy-store reality** (tests 12 and 16): a well-formed
  slug with no admitted in-scope records is valid (counts 0, `by_code`
  `{}`, `outside_scope` = global totals, status `clean`, exit 0); on the
  all-unscoped golden store, every slug yields the empty scoped view while
  the global report still carries `empty_topic_goal` — the legacy-store
  reality, not a classification.
- **Invalid flag misuse** (test 10): repeated `--workstream` ⇒ exit 2,
  "usage:" + "may only be given once"; `--workstream "Bad"` and `""` ⇒
  exit 2 with the standard JSON error envelope
  (`invalid_workstreams`, `invalid slug: 'Bad'` / `empty element`); the
  API-level non-string scope is rejected with `invalid workstreams: exactly
  one slug required`; `not_initialized`/`malformed_store` stay exit 2.
- **Subset invariant** (test 19): `scoped["findings"]` is element-wise
  equal to the global `findings` restricted to the admitted in-scope
  paths, in global order, with the global run itself byte-identical to the
  no-flag CLI output.

## Real-store acceptance — not measured; not claimed

The frozen spec's §Real-store acceptance prescribes live runs on
`/home/bhjia/physics/GW_librpa` and the yangian store used in the
2026-08-14 session: tree hashing before/after, no-flag old-runtime vs.
current-runtime parity, scoped payload recording, and zero-write diffs on
every store touched. **Those runs are not part of this gate record**: the
live stores sit outside this repository and were not accessible to the
environment in which this evidence was collected, so no live-store hash,
parity, or payload claim is made here. The 2026-08-14 feedback files are
**natural-demand evidence** — they record observed frictions in ordinary
research sessions — and are not treated as live acceptance of this runtime.
The deterministic no-flag parity, empty-scope, and zero-write properties
are carried by the in-suite evidence above (golden byte parity; test 16
mirrors the all-unscoped legacy-store reality; test 13 tree hashing), which
is what this gate claims.

## Boundaries and no claims

- **Done/shipped means the deterministic gate passed for the frozen M1d
  slice only.** M2, M3, and M4 remain blocked design options; the M1d gate
  flips no M1b disposition (B, C–E, Followup 2 (`lineage`), Followup 6
  (structured prepare) remain deferred; F → M4; G independent; H dropped)
  and does not reopen M1b or M1c.
- **No claims**: no behavioral, treatment/control, causal, or
  treatment-advantage evidence; no claim that scoped `check` improves
  research outcomes; no bootstrap validation; FROZEN v6 remains an
  anchored, unexecuted preregistration. `by_code` is a deterministic
  tally, never a drift-vs-damage classification — whether a
  `hash_mismatch` is "expected historical pin drift" or "current evidence
  damage" is a human judgment, never a runtime call. A scoped
  `clean`/exit 0 claims only "no attributable findings for this
  workstream", never whole-store health; `outside_scope` surfaces (does
  not classify) the remainder, and the no-flag run remains the
  whole-store instrument.
- **Not in M1d (deferred, untouched)**: the baseline/delta report
  comparison (manual `diff`/`rg` over saved deterministic JSONs is the
  query path), handoff staleness (closeout-first handoff unchanged; roster
  H stays dropped), exit-1 semantics (unchanged; the flag gives recovery
  scripts a per-workstream signal), write friction (structured prepare is
  Followup 6), remote pointer/evidence manifests and `lineage` (roster D),
  and any `enter`/`list`/`show`/`record`/`note` change.
- **Real stores untouched by M1d**: no record was written, migrated, or
  classified; scoped health is meaningful only once records explicitly
  carry `workstreams` — new scoped records or a **reviewed manual
  backfill** (the runtime never backfills).
