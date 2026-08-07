# M0.6 conformance suite — first paired-run freeze (preregistration)

Version: **5** — re-frozen from the current working tree; **supersedes
version 4** (2026-08-06T19:56:51Z), which superseded version 3
(2026-08-06T19:41:43Z), which superseded version 2 (2026-08-06T18:19:57Z),
which superseded version 1 (2026-08-06T18:15:02Z). Version 5 is the
operative freeze for the first scored paired run.

Status: **FROZEN** for the first scored paired run of the M0.6 conformance
suite core. This document preregisters the exact bytes the first run is
scored against. All values below were computed from the actual bytes of the
current working tree on 2026-08-06 (UTC freeze time:
`2026-08-06T20:13:02Z`), then independently re-verified (see
[Verification](#verification)).

This file is itself **excluded from its own hash table** (section 7): it is
the record, not scored material, and it becomes the formal freeze proof of
the first scored run only when anchored by an external immutable anchor
(section 1).

## 0. What changed since version 4 (re-freeze reason)

Two frozen inputs changed after version 4 was recorded — blind-scoring
wording de-ambiguation only — so, per the freeze discipline (section 6),
this record is re-issued from the current bytes:

- `suite/rubric.md` changed (`f41014b7…` → `3fb5ee7e…`): the M4 definition
  now states that the assessor reads only the resumption session's
  condition-neutral evidence packet — the mechanically extracted verbatim
  agent evidence from that session, per the scoring procedure — never the
  raw resumption transcript or the live end state. Each of the four items
  is 1 if the packet's verbatim evidence demonstrably used the end-state
  record or file the gold answers name for that item (named or cited that
  record or file), else 0; restating content without naming the record or
  file scores 0. **The M4 definition, the four checklist items, the 1/0
  scoring semantics, and the frozen threshold (M4 = 1.0, 4/4) are
  unchanged** — this edit only pins the evidence source to the
  condition-neutral blind packet.
- `suite/README.md` changed (`0260c601…` → `f663ab46…`): step 5 point 5 is
  synchronized with the rubric — the assessor scores the four M4 checklist
  items from the session-2 condition-neutral evidence packet (the
  mechanically extracted verbatim agent evidence from the resumption
  session, per step 7), against the end-state records or files the gold
  answers name for each item; the raw session-2 transcript and the live end
  state never reach the assessor.
- Unchanged from version 4: all other 13 frozen inputs (policy, both
  adapters, all three scenarios, all three gold files, both templates, both
  `events/S2/` artifacts), all three seed trees (section 4), the runtime
  (1082 nonblank lines), and the test baseline (26 passed, section 5).
- `docs/roadmap.md` and `docs/m0.6-suite.md` carry status notes about this
  suite, but neither is part of this freeze's core table (section 3 covers
  only the 15 `suite/` files listed there); they were not read for this
  version beyond what is recorded here.

## 1. Anchor status — no git commit anchor; formal run still blocked

There is **no git commit anchor** for this freeze. Per the instructions for
this version, **no git command was run** while producing version 5; the
anchor status below is carried over from the version-2 record
(2026-08-06T18:19:57Z, itself re-verified at versions 3, 4, and 5 without
git) and must be re-verified with the run's own `git rev-parse HEAD` +
`git status --porcelain suite/` before the formal run
(`run-notes-template.md` §0):

- `git branch --show-current` → `main`; `git log --oneline -1` →
  `3a66e210 feat: aitp inventory (M0.6 gate item 2)`. That commit **does
  not contain** the suite; the suite tree is untracked.
- `git status --porcelain` showed `?? suite/` (untracked), plus uncommitted
  working-tree changes: `M .gitignore`, `M docs/m0.6-suite.md`,
  `M docs/roadmap.md`, and untracked `docs/m1-read-write-balance.md`,
  `ref/`, `uv.lock`. The clarification updates in the spec
  (`docs/m0.6-suite.md`, also `M`) and in the suite files (section 0) are
  part of these uncommitted changes; this freeze pins their current bytes,
  not a commit. `docs/m0.6-suite.md` is **not** part of this freeze's core
  table (section 3 covers only the 15 `suite/` files listed there).
- This freeze is therefore a **working-tree preregistration**: the hashes
  below pin the current bytes, not a commit.
- **The formal scored run remains BLOCKED on the anchor.** Before the
  formal paired run, the operator must obtain the user's explicit
  authorization to commit the frozen state (or pin an external immutable
  anchor), then record that anchor (commit hash or equivalent) in the run
  notes alongside the hashes below. No commit was created for this freeze,
  and no commit hash is claimed here — no anchor is fabricated. The anchor
  is what turns this record into the formal freeze proof of the scored run
  (section 7).

## 2. Frozen scope

Frozen as of the timestamp above:

- the suite core inputs: `README.md`, `policy.md`, `rubric.md` (thresholds),
  `adapters/cli.md`, `adapters/plain-files.md`, the three scenario files,
  the three gold files, the two record templates, and the two S2
  event-artifact files — 15 files, 134,276 bytes total (section 3);
  `docs/m0.6-suite.md` is deliberately **not** in the core table;
- the three seed trees `seeds/S1`, `seeds/S2`, `seeds/S3` (section 4);
- the canonical runtime `plugins/aitp-research-protocol/scripts/vendor/aitp/`
  and the test baseline (section 5);
- per `README.md` step 0, the agent configuration, model, and system prompt
  are frozen before the run and recorded in the run notes (not part of this
  file's byte pin).

Binding separations, fixed by this freeze:

- **Gold never enters a seed.** Nothing from `suite/gold/` is present in any
  seed tree (verified in section 4) and nothing from `gold/` is ever copied
  into a workspace or a record template; a violation voids the run
  (`README.md` steps 1.2/2, `rubric.md` run contract).
- **S2 event artifacts are turn-time operator injections only.** The two
  `events/S2/` files never appear in a seed (verified in section 4) and
  never exist in a workspace at deployment; the operator injects each by
  hand (`cp -a`, sha256 recorded) into BOTH workspaces immediately before
  the script turn that names it (S2 turns 4 and 5), per `README.md` step 4
  and the scenario's Event injection section. Pre-seeding, early
  visibility, or divergent digests between conditions voids the dependent
  probes (S2 P3/P4).
- **Policy bytes are identical in both conditions.** `policy.md` is the
  byte-identical `RESEARCH-POLICY.md` in both workspaces; its sha256 is
  recorded at deploy and must match across conditions (`README.md` step 2).
- **Thresholds are pre-registered, not tunable after the run.**
  `rubric.md`'s thresholds are frozen here and by the rubric's own revision
  rule: revised only between stage runs, with the diff recorded in the
  stage notes — never negotiated per run and never adjusted after a run's
  results are known.
- **S3 is held out.** Prompts, Skills, adapters, and thresholds are never
  iterated against S3; S3 is scored first and reported separately
  (`README.md` step 8, `rubric.md`, spec anti-gaming).

Templates are in the freeze as fixed documentation bytes, with fixed
operating rules (`README.md` step 0): `run-notes-template.md` is
operator-only — its filled copies (which contain the condition mapping and
the injection log) are saved at `suite/runs/<date>/<scenario>/run-notes.md`,
never placed in a run workspace, and never handed to the assessor before
scoring is complete; `score-sheet-template.md` is assessor-only — filled
copies are archived under `suite/runs/<date>/` after scoring. Neither
template contains gold content.

Explicitly **not** frozen / whitelisted to differ:

- `.aitp/local/` machine-local store state in deployed workspaces
  (`config.toml`, drafts, scratch, locks) and filesystem metadata only
  (mtime, owner, permissions) — `README.md` step 2.3;
- `suite/runs/` — the operator archive: dry-run transcripts, end states,
  manifests, run notes, score sheets, and reviews under
  `suite/runs/**/reviews/**`. All of it is gitignored result material, not
  scoring input; nothing under `suite/runs/` is frozen here (section 8).
  Its existence does not affect the frozen bytes.

## 3. Frozen inputs — full sha256 and byte counts (15 files)

| File | sha256 | Bytes |
|---|---|---|
| `suite/README.md` | `f663ab461909147fd4f06b90574fd5a9b03490423270337d0dcd76217e578a99` | 21545 |
| `suite/policy.md` | `e92b59ec88fd52d3dd896771980393ed2bb29fa72b734af56dd1c16d9d04c0d5` | 3515 |
| `suite/rubric.md` | `3fb5ee7ef4057df8f2ea6b0681e2ca19293d27bf3b2c24b7f12f9205317dc51b` | 15617 |
| `suite/adapters/cli.md` | `b1e5aa137edbbcd945509caef69e21d0d0d0b3eed300fa27bfb403b49ad84046` | 3331 |
| `suite/adapters/plain-files.md` | `3d3af41a8674f3fceb33db399f7f75c64c8380cce151a689270b5b2e57ab308f` | 3169 |
| `suite/scenarios/S1-resumption.md` | `7b1be589d9f6041b7ab89f425b7944d95e7d492fd7ffbc7d9231342e9b458ba1` | 6774 |
| `suite/scenarios/S2-durable-events.md` | `4db7486e4e655f8af43d9172ac1d7483d0357c5be1495312aa4133de2e4cd654` | 13515 |
| `suite/scenarios/S3-heldout.md` | `96a3dac29a08fdd13ea7c9db6934908e3e038bddf4969e52cfc046edede3007c` | 9521 |
| `suite/gold/S1-resumption-gold.md` | `9393d87e0ae955a6f985844a63ac6764029d77843931910e1976e40c75ab80e2` | 4856 |
| `suite/gold/S2-durable-events-gold.md` | `eb18d0b9f703cfc5ee63cb8015778b96b91038a823af8a768592a4140906ac0a` | 6081 |
| `suite/gold/S3-heldout-gold.md` | `78ecc2a5e42681bb5554bc1c369588402282f5f644fbe290ff1371170c4cb085` | 3831 |
| `suite/run-notes-template.md` | `a034ce098a9b00f2bc284f64510259a87805224d7839de0c4aa50f6dbc464feb` | 24240 |
| `suite/score-sheet-template.md` | `4825e8541eac4e8e806dd7235465236d8fb1c4d0b7bcff7a8170f5294a4bffd7` | 18239 |
| `suite/events/S2/entropy-L64.dat` | `65dc4dbbc8854e1045c6569d702799952f086b8039553c2c64062548a77cd2de` | 10 |
| `suite/events/S2/run-bond600-L64.out` | `1355a40401105ca7fa706d6864aa99bc574bbfab35e5a4569e7d5cd078f02bee` | 32 |

The two `events/S2/` files are the canonical artifacts injected at S2 turns
4 and 5 (workspace targets `calculations/dmrg/entropy-L64.dat` and
`calculations/dmrg/run-bond600-L64.out`; digests above are the ones the
scenario pins and S2 gold requires records to reproduce). Of the 15 files,
13 are unchanged from version 4; only `README.md` and `rubric.md` changed
(§0). `FROZEN.md` itself is deliberately absent from this table
(section 7).

## 4. Seed trees — canonical manifests, file counts, and window counts

Manifest construction (identical to `README.md` step 1.4): from the seed
root, `find . -type f | sort` (byte-wise sort, paths relative with `./`
prefix, dotfiles included), then per file a line `path<TAB>sha256`
(UTF-8, LF, every line including the last terminated by `\n`). The
**canonical hash** is sha256 over those exact manifest bytes.

| Seed | Files (`find . -type f`) | Total bytes | Canonical manifest sha256 |
|---|---|---|---|
| `suite/seeds/S1/` | 58 | 30563 | `2d9bfe0e8b742ace416b8f5b562106ea818657c7b54fb096c1aa126964d8f6c3` |
| `suite/seeds/S2/` | 57 | 27108 | `39952a54be0441ffcea4189656b7482fa1e64a5eba9daf46b17c82a6d596e154` |
| `suite/seeds/S3/` | 48 | 30311 | `697326340cd3a5042241c3cde1308fd4a2ed294d33316606a2b26e7ae6890530` |

All three canonical hashes, file counts, and byte totals are **unchanged
from versions 2–4**. Verified against the current seed trees:

- No file path in any seed manifest matches `entropy-L64` or
  `run-bond600-L64` — the S2 event artifacts are absent from the canonical
  seed (pre-injection invisibility, `README.md` step 1.2).
- No seed manifest line contains `gold` — no gold content in any seed.
- S2's top-level `.gitignore` (`./.gitignore`, manifest line 36; contents:
  `.aitp/local/`, `**/__pycache__/`, `**/.pytest_cache/`, `**/build/`,
  `**/.venv/`) and `.aitp/.gitignore` (manifest line 1) are part of the
  manifest as in versions 1 and 2.

Window counts, carried over from versions 2–4 (the seed bytes are identical
to those versions, where they were verified with the frozen runtime `aitp
enter --json` on byte-copies — the fixtures themselves were never executed
against and never mutated):

| Seed | `memory_status` | `warnings` | `counts.active` | `counts.omitted_active` | `counts.superseded` | `counts.malformed` | `counts.unresolved_failures` |
|---|---|---|---|---|---|---|---|
| S1 | `available` | `[]` | 29 | 9 | 2 | 0 | 1 |
| S2 | `available` | `[]` | 28 | 8 | 2 | 0 | 1 |
| S3 | `available` | `[]` | 30 | 10 | 1 | 0 | 1 |

All three satisfy the seed-window contract of `README.md` / `rubric.md`
(active ≥ 28, omitted_active ≥ 8). S3's fixture is the portable fixture
noted in `scenarios/S3-heldout.md` (one structural repair recorded there
before version 1; content repair, not iteration).

## 5. Runtime and test baseline

- **Runtime nonblank lines: 1082.** Counted per the roadmap's accounting
  rule (`grep -c '\S'` per module, summed) over all `.py` files in the
  canonical runtime `plugins/aitp-research-protocol/scripts/vendor/aitp/`
  (9 modules). Re-measured from the current tree for this version;
  unchanged from versions 1–4. The runtime was **not modified** for
  this freeze.
- **Tests: 26 passed, 0 failed** — `uv run --python 3.12 --with pytest
  python -m pytest -q` (26 collected, 1.03 s, exit 0), re-run from the
  current tree for this version. The command reuses the local `.venv`
  (Python 3.12, pytest already installed); the `.venv` was **not modified**
  for this freeze. Historical note: at version 1, the `.venv` bin-script
  shebangs pointed at a stale repo path and were repaired in place
  (environment-only; `.venv/` is gitignored; no repo content changed). No
  test or fixture file was modified.

## 6. Freeze discipline (binding)

- **S3 is held out.** Prompts, Skills, adapters, and thresholds are never
  iterated against S3 (`README.md` step 8; `rubric.md` §S3; spec
  `docs/m0.6-suite.md` anti-gaming). Within a stage batch, S3 is run and
  reported FIRST and separately; S1/S2 follow. Any structural repair to the
  S3 fixture is recorded in the stage notes as content repair, never as
  iteration.
- **Thresholds are pre-registered and never tuned after the run.** The
  `rubric.md` thresholds are frozen at the timestamps above; they are not
  negotiated per run and not adjusted in response to run results. Any
  revision happens only between stage runs, recorded as a diff in the stage
  notes, and requires a new freeze of the revised rubric bytes.
- **Freeze check before the first scored run.** Per `README.md` step 0, the
  operator verifies this file before the first scored run: every item on the
  freeze record — rubric thresholds, canonical seeds, scenario scripts,
  event artifacts (`events/`), adapters, agent config, runtime/test
  baseline, S3 hold-out — must be frozen and recorded here. An unfrozen item
  voids the run as the first scored run and must be resolved and recorded in
  the stage notes before any scoring.
- **Any change voids the first run.** Any content change to the frozen
  scope — the 15 frozen inputs, seed trees, rubric thresholds, runtime —
  after this freeze invalidates the first paired run. The run must not
  proceed on mixed bytes. Note that the threshold values in `rubric.md`
  (M1 ≥ 0.6 AND > control; M2 recall/precision ≥ 0.7; M3 = 1.0; M4 = 1.0
  (4/4); M5 reported only) are unchanged across versions 1–5: the
  clarifications (§0) operationalize scoring; they never alter a threshold.
- **Refreeze procedure.** After any such change, a new freeze must be
  recorded (new version/UTC timestamp and full re-computed hashes), and the
  change documented as a diff in the stage notes — per `rubric.md`'s
  revision rule, revisions happen only between stage runs and are recorded,
  never silent. This file is version 5 precisely because of such a
  change (section 0).
- **Event-artifact discipline.** `events/S2/` files are injected only at
  their script turns, identically in both conditions (`README.md` step 4):
  never pre-seeded in a seed (checked at freeze and at step 1.2), never
  deployed at step 2, injected by hand immediately before the naming turn,
  with source/target sha256 and injection time recorded in the run notes
  before the turn is sent. An artifact visible before its turn, or target
  digests diverging between conditions, voids the dependent probes (S2 P3,
  P4). After injection the artifact stays in the workspace as evidence — it
  rides into end states and session-2 replication unchanged.
- **Templates.** The two templates are fixed documentation bytes; filled
  copies are run artifacts under `suite/runs/` (gitignored) and never alter
  the frozen template bytes. Gold answers are never copied into either
  template (`run-notes-template.md` §0).
- **Gold separation.** Nothing from `suite/gold/` may enter a seeded
  workspace or the agent-readable run environment; a violation voids the
  run (`README.md` step 1.2, `rubric.md` run contract).
- **Condition symmetry.** The two conditions differ only in the adapter;
  identical seed bytes, model, system prompt, agent config, budgets, and
  identical `policy.md` bytes in both workspaces — any other difference
  voids the run (`README.md` step 0).
- **This file is a record, not scored material.** `FROZEN.md` is updated
  only by a new freeze or by a stage-note diff; it is not part of the
  agent-visible workspace.

## 7. FROZEN.md self-exclusion and the external anchor

- `suite/FROZEN.md` is **excluded from its own hash table** (section 3): it
  is the record of the freeze, not a scoring input, and the agent never sees
  it. No sha256 of this file is part of the frozen input set.
- Because the suite is untracked (section 1), this file alone cannot prove
  that the frozen bytes are the bytes of the first scored run: any edit to
  this file or the inputs after this timestamp would change the working tree
  undetected. The freeze becomes a **formal freeze proof** only when an
  **external immutable anchor** exists — a commit of the frozen state
  (requiring the user's explicit authorization) or an equivalent immutable
  external pin (e.g. a hash posted to an external immutable ledger) — with
  the anchor recorded in the run notes alongside the hashes in sections 3–5.
  Until such an anchor exists, this record is a working-tree
  preregistration and the **formal scored run remains blocked**: the run's
  validity as the first scored run depends on the operator's freeze check
  (section 6) against the anchored bytes, and no anchor is claimed or
  fabricated in this file.

## 8. Verification

Everything above was computed from the working tree bytes, then re-checked:

1. Frozen-input sha256 and byte counts: `sha256sum` + `wc -c` over the 15
   files (section 3) — single pass; total bytes re-confirmed with a
   concatenated `wc -c` (134,276).
2. Seed manifests: re-built from the current tree with the canonical
   `find . -type f | sort` + `path<TAB>sha256` pipeline (section 4);
   hashes, file counts (58/57/48), and byte totals (30563/27108/30311)
   match versions 2–4. Absence checks: `grep` for `entropy-L64` /
   `run-bond600-L64` in the S2 manifest (0 matches) and for `gold` in all
   three manifests (0 matches).
3. Window counts: carried over from versions 2–4, whose seeds are byte-
   identical to the current trees (manifest equality above); they were
   originally verified with `aitp enter --json` on `diff -r`-verified
   byte-copies at `/tmp/freeze-check/v2/<S>` (S1 29/9, S2 28/8, S3 30/10).
4. Runtime and tests: nonblank count (1082) and `uv run --python 3.12
   --with pytest python -m pytest -q` (26 passed, 1.03 s) re-run from the
   current tree for this version; the `.venv` was not modified (gitignored
   environment, unchanged mtimes).
5. Exclusions: no file under `suite/runs/` (including
   `suite/runs/2026-08-06-dry-run/**`, its `reviews/` subtree, transcripts,
   end states, and manifests) is frozen; nothing from `gold/` or
   `events/S2/` is inside any seed tree; `docs/m0.6-suite.md` is not in the
   core table (section 3 covers only the 15 listed `suite/` files); no
   `ref/` or `uv.lock` file was read or frozen.
6. Git anchor: no git command was run for this version; the anchor status
   in section 1 is carried from the version-2 record and must be re-verified
   at run time (`run-notes-template.md` §0). No commit is claimed; the
   formal scored run remains blocked until an anchor exists (section 7).
