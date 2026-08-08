# Hakimi × AITP compatibility matrix and decisions

Baseline audited **2026-08-08** against AITP HEAD
`8658f6827288f4bb61e5c193a346f0f73ebbe3b2` (working tree clean except the
deliberately untracked `ref/` and `uv.lock`). Every row was verified by
running the bundled CLI (`/home/bhjia/.local/bin/python3.12
plugins/aitp-research-protocol/scripts/aitp.py …`) and by reading the
canonical runtime. Re-verify rows when the AITP HEAD moves past this baseline.

## 1. Command matrix (Hakimi view)

| Command | AITP stage | Status | Hakimi may call | Blocked on | Future feature-detect |
|---|---|---|---|---|---|
| `init` | M0 | available | no — human decision, blank dir only | — | `--help` presence |
| `init --adopt` | M0.6 | available | no — touches an existing tree, human decision | — | `--help` presence |
| `enter` | M0 | available | **yes** (session start/end) | — | no `schema` key; strict shape check |
| `inventory <path> --name <n>` | M0.6 | available | no — operator-only, **writes** `.aitp/local/legacy/<name>-inventory.json` | — | — |
| `record prepare\|save` | M0 | available | yes (prepare → fill → save) | — | envelope shape + `status` enum |
| `note prepare\|save` | M0 | available | yes | — | envelope shape + `status` enum |
| `list` | M1a | **absent** (argparse invalid choice, exit 2) | no | M0.6 gate | top-level `schema == "aitp/list-0.1"` |
| `show` | M1a | **absent** | no | M0.6 gate | top-level `schema == "aitp/show-0.1"` |
| `check` | M1b | **absent** | no | M1a gate + cap reconciliation | exit 0/1/2 + `aitp/check-report-0.1` |

## 2. Schema existence (as of baseline)

| Schema | Kind | Status | Notes |
|---|---|---|---|
| `aitp/lite-store-0.1` | file (`STORE.toml`) | exists | `workspace.py:100` |
| `aitp/lite-topic-0.1` | file (`TOPIC.md`) | exists | `workspace.py:88` |
| `aitp/lite-entry-0.1` | file | exists; only schema `validate_entry` accepts | `records.py:86,258` |
| `aitp/lite-note-0.1` | file | exists | `notes.py:61,110` |
| `aitp/legacy-inventory-0.1` | file | exists | `workspace.py:322` |
| `aitp/enter-0.1` | **transport** | **does not exist** | `enter --json` has no top-level `schema` (`state.py:121-147`; verified live) |
| `aitp/enter-0.2`, `aitp/list-0.1`, `aitp/show-0.1` | transport | blocked (spec frozen) | `docs/m1a-spec.md` §payloads |
| `aitp/lite-entry-0.2` | file | blocked (pre-spec frozen) | `docs/m1b-spec.md:32` |
| `aitp/check-report-0.1` | transport | blocked (pre-spec frozen) | `docs/m1b-spec.md:226` |
| `aitp/run-pointer-0.1` | file | blocked (pre-spec frozen) | `docs/m1b-spec.md:288` |

The `lite-*` schemas are persistent-file schemas; they are **not** CLI
transport envelopes. Transport envelopes are unversioned until M1a.

## 3. Versioned transport envelope — decision

- **`record/note prepare|save` responses will NOT be versioned in M1a or
  M1b.** Evidence: M1a implementation map changes `records.py` by +3 lines
  (hash_mismatch message only) and `notes.py` by 0 (`docs/m1a-spec.md:453-469`);
  M1b adds only `check-report-0.1`/`run-pointer-0.1` and bumps enter/show
  (`docs/m1b-spec.md`).
- **Transition strategy:** Hakimi treats prepare/save envelopes as
  **version-0 contracts**: strict shape validation (exact key sets) and fail
  closed on unknown `status` values. Live shapes (baseline):
  - `record prepare` → `{"status":"prepared","id","path","save_command"}`;
    idempotency-key hit → `{"status":"existing","path","idempotency_key"}`;
  - `record save` / `note save` → `{"status":"saved","path"}` (or
    `{"status":"already_saved","path"}`);
  - `note prepare` → same shape as `record prepare`.
- **No AITP change required.** If hardening is ever wanted, a minimal
  optional `schema` field on success envelopes would be a documented M1a spec
  revision or M1b addendum — never a silent addition.
- **First versioned contract point for Hakimi:** `aitp/enter-0.2` at M1a
  (`docs/m1a-spec.md:253-288`). Hakimi must not pretend any schema exists
  before that gate.
- **Golden fixtures:** regenerated deliberately at M1a in
  `tests/ledger/fixtures/golden/` (`enter.json`, `enter-after-save.json`,
  new `list.json`, `show.json`); `root` normalized to `<golden-store>`;
  synthetic `nio` store only — no real research data (`docs/m1a-spec.md:518-544`).
  Hakimi may consume them as official protocol fixtures.

## 4. Hakimi integration assumptions — check results

| # | Assumption | Result | Evidence |
|---|---|---|---|
| 1 | Manifest discovers `skills/` relative to plugin root | PASS | `kimi.plugin.json:5` and `.codex-plugin/plugin.json:18`: `"skills": "./skills/"`; both carry a `version` field (0.1.0 / 0.1.0+codex.20260729110858) |
| 2 | Launcher probed as `python3.13 → 3.12 → 3.11 → python3`, verified ≥ 3.11 | PASS | `skills/using-aitp/SKILL.md:8-19` (exact order); launcher hard gate `sys.version_info < (3,11)` → exit 2 (`scripts/aitp.py:11-13`). Verified live: system `python3` = 3.10.12 is rejected with `AITP requires Python 3.11 or newer.` on stderr, exit 2 |
| 3 | `--cwd` semantics | PASS (two caveats) | default `.`, relative/absolute ok (`cli.py`); `resolve_root` = nearest ancestor with `.aitp/STORE.toml` wins, else git root, else cwd (`workspace.py:42-50`). Verified live from a subdirectory. Caveat 1: ancestor-store priority ⇒ a nested second store inside a workspace cannot be opened (known design item on the M1a pre-list). Caveat 2: in a directory without a store, a parent Git root becomes the workspace root |
| 4 | Exit codes 0/2; future `check` 0/1/2 | PASS | success 0; `AITPError` → 2 (`cli.py:124-130`); argparse errors → 2; `check` contract at `docs/m1b-spec.md:193-202` |
| 5 | Error payload `{"status":"error","code","message"}` | PASS (one detail) | `cli.py:124-130`, verified live. Detail: with `--json` the JSON goes to **stdout**; in text mode the error goes to **stderr only** (stdout empty) |
| 6 | `record/note save` drafts must live under `.aitp/local/drafts` | PASS | `records.py:300-308`, `notes.py:84-92` (`invalid_draft`); verified live (absolute path outside drafts rejected, exit 2) |
| 7 | Read-only commands are zero-write | PASS | verified live: two `enter --json` runs (root + subdir `--cwd`) on a byte-copy of `suite/seeds/S1` leave the tree sha256-identical. Code: `enter` never calls `atomic_write`/`store_lock`; the lock is save-path only (`records.py:312`). **`inventory` is a write command — never treated as read-only** |

## 5. Red lines (Hakimi, now and future)

1. Never call `list`/`show`/`check` (absent until their gates; exit 2 today).
   Never emulate them with `rg` or ad-hoc Markdown parsing.
2. Never auto-run `init` / `init --adopt` / `inventory` — all need a human
   decision; `inventory` writes files.
3. Never assume `aitp/enter-0.1` or any transport schema. Contract points
   exist only after gates: `enter-0.2`/`list-0.1`/`show-0.1` (M1a),
   `check-report-0.1`/`run-pointer-0.1` (M1b).
4. Never write `.aitp/topic/entries/`, `.aitp/topic/notes/`, `TOPIC.md`,
   `STORE.toml`; never bypass `record/note prepare|save`; never copy the
   runtime/parser/validator; never keep a second ledger; no MCP/daemon/vector
   service.
5. Uninitialized workspace = graceful degradation (`not_initialized`, exit 2),
   never auto-adopt.
6. Private caches never written back; no transcript/CoT storage; context
   packets are ephemeral (`docs/collaborator-design.md:11-16`).
7. Remote evidence: `target: host:/path` is rejected today by `ref_escape`
   (`records.py:125-133`); `sha256:` verifies local files only. The remote
   evidence boundary is the M1b pointer bundle — do not route around it.
8. Python ≥ 3.11 is launcher-enforced; probe order per the Skill, never
   invented.

## 6. Next steps and blocking

AITP side (by gate):

1. Finish M0.6: two dogfood bootstrap measurements (human gold set → bootstrap
   Note → human `decision` Entry → scoring), paired scored suite runs (S1/S2
   both conditions + held-out S3), gate review.
2. After the M0.6 gate: implement M1a from the frozen spec (list/show/enter-0.2
   + golden regeneration). Same-change doc sync per `docs/m1a-spec.md` §Sync.
3. Optional (not needed for H0): a documented M1a spec revision or M1b
   addendum to version prepare/save envelopes — currently decided against.
4. M1b: cap reconciliation (1,450 − actual M1a total) → implementation spec →
   `check`/`lite-entry-0.2`.

Hakimi side (parallel):

- H0 now: adapter skeleton, launcher, strict envelope validation, capability
  detection, `enter` lifecycle, prepare→save flow, degradation, tree-hash
  tests, compatibility matrix in Hakimi's bilingual README.
- H1 after M1a gate; H2 after M1b gate; formal Hakimi contract after M4.
- Research-loop capabilities (web/PDF/reasoning/UX/private caches) are
  independent of every AITP gate.

Blocking chain: `M0.6 gate` → `M1a implementation` → `M1a gate` → `M1b` →
`M2–M4`. Hakimi H0 and the research loop have zero dependencies on it.

## 7. Audit method (baseline evidence)

- `git rev-parse HEAD` = `8658f682…`; `git status --porcelain` = `?? ref/`,
  `?? uv.lock` (both deliberately untracked).
- `uv run --python 3.12 --with pytest python -m pytest -q` → **26 passed**.
- Runtime nonblank lines = **1082** across 9 modules (all < 400).
- CLI surface captured from `--help` of every command; `list/show/check` →
  argparse `invalid choice`, exit 2.
- Live payload/exit-code/zero-write checks on a byte-copy of `suite/seeds/S1`
  under `/tmp`; S1 window counts match `suite/FROZEN.md` v6 §4 exactly
  (active 29, superseded 2, malformed 0, omitted 9, unresolved 1,
  `next_action.entry_id` = `entry-0a21…`).
