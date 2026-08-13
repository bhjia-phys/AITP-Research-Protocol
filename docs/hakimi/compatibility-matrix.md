# Hakimi × AITP compatibility matrix and decisions

Historical runtime audit: **2026-08-08**, against AITP HEAD
`8658f6827288f4bb61e5c193a346f0f73ebbe3b2` (working tree clean except the
deliberately untracked `ref/` and `uv.lock`). Every row was verified by
running the bundled CLI (`/home/bhjia/.local/bin/python3.12
plugins/aitp-research-protocol/scripts/aitp.py …`) and by reading the
canonical runtime. The 2026-08-10 decision changes stage authorization only;
the subsequent M1a implementation and deterministic gate are recorded in the
current amendment below, including current CLI and schema availability. If the
runtime or plugin manifests change again after this audited HEAD, rerun the
CLI/payload/zero-write checks and refresh this matrix.

## 1. Command matrix (Hakimi view)

| Command | AITP stage | Status | Hakimi may call | Blocked on | Future feature-detect |
|---|---|---|---|---|---|
| `init` | M0 | available | no — human decision, blank dir only | — | `--help` presence |
| `init --adopt` | M0.6 | available | no — touches an existing tree, human decision | — | `--help` presence |
| `enter` | M0 | available | **yes** (session start/end) | — | no `schema` key; strict shape check; M1c (shipped; gate passed): with the single-occurrence `--workstream <slug>` → `schema == "aitp/enter-0.3"` |
| `inventory <path> --name <n>` | M0.6 | available | no — operator-only, **writes** `.aitp/local/legacy/<name>-inventory.json` | — | — |
| `record prepare\|save` | M0 | available | yes (prepare → fill → save) | — | envelope shape + `status` enum; M1c (shipped; gate passed): repeatable `--workstream` seeds draft frontmatter only (repeated identical slug rejected as a duplicate), envelopes unchanged |
| `note prepare\|save` | M0 | available | yes | — | envelope shape + `status` enum; M1c (shipped; gate passed): repeatable `--workstream` seeds draft frontmatter only (repeated identical slug rejected as a duplicate), envelopes unchanged |
| `list` | M1a | **available** (read-only) | **yes** (feature-detect schema) | —; M1a deterministic gate passed | top-level `schema == "aitp/list-0.1"`; M1c (shipped; gate passed): with the single-occurrence `--workstream <slug>` → `schema == "aitp/list-0.2"` |
| `show` | M1a | **available** (read-only) | **yes** (feature-detect schema) | —; M1a deterministic gate passed | top-level `schema == "aitp/show-0.1"` |
| `check` | M1b-R1 (selected 2026-08-12) | **available** (read-only) | **yes** (feature-detect schema) | —; M1b-R1 deterministic gate passed 2026-08-12 (evidence in `docs/archive/m1b-r1-stage-notes.md`); v0.1-only, read-only, zero-write | parse `aitp/check-report-0.1` on exits 0 and 1; exit 2 is the standard error envelope |
| `lineage` | deferred candidate (Followup 2, re-deferred 2026-08-12) | **absent** | no | a new reviewed freeze revision selecting it, then its own reviewed spec | `aitp/lineage-0.1` only if actually shipped |

M0.6→M1a authorization is not a Hakimi-side decision: the approved 2026-08-10
narrowed gate review flipped the M1a roadmap row to ready, and the post-review
M1a deterministic gate passed. The 2026-08-12 reviewed freeze revision
(`docs/archive/m1b-adjudication.md`) selected M1b-R1, implemented per
`docs/archive/m1b-r1-spec.md` with its deterministic gate passed (evidence in
`docs/archive/m1b-r1-stage-notes.md`); the current read
contracts are available, `check` is shipped and gated,
`lineage` is a
deferred candidate, and the matrix reflects the closed R1 gate.
`enter` stays at `aitp/enter-0.2` in R1 — only its **text** rendering
is compact, and that text is **human-facing only**: Hakimi must not
feature-detect or parse it; machine output remains the versioned JSON.

## 2. Schema existence (current M1a amendment)

| Schema | Kind | Status | Notes |
|---|---|---|---|
| `aitp/lite-store-0.1` | file (`STORE.toml`) | exists | `workspace.py` store metadata contract |
| `aitp/lite-topic-0.1` | file (`TOPIC.md`) | exists | `workspace.py` Topic metadata contract |
| `aitp/lite-entry-0.1` | file | exists; only schema `validate_entry` accepts | `records.py` schema validation contract |
| `aitp/lite-note-0.1` | file | exists | `notes.py` Note schema validation contract |
| `aitp/legacy-inventory-0.1` | file | exists | `workspace.py` legacy inventory contract |
| `aitp/enter-0.1` | **transport** | **does not exist** | `enter --json` has no top-level `schema` (`state.py` enter projection; verified live) |
| `aitp/enter-0.2`, `aitp/list-0.1`, `aitp/show-0.1` | transport | **exists and available** | `docs/archive/m1a-spec.md` headings `aitp list` → `JSON payload (schema aitp/list-0.1)`, `aitp show` → `JSON payload (schema aitp/show-0.1)`, and `enter v2 (schema aitp/enter-0.2)`; Hakimi feature-detects these read-only contracts. Additive 2026-08-12 stability revision to `show-0.1`: when the target file exists but fails validation, `show` returns exit 0 with `status: "malformed"`, `frontmatter: null`, raw file text in `body`, and a `warning` carrying the finding — consumers must tolerate the `malformed` status value and null `frontmatter` (`docs/design.md` §`aitp show`) |
| `aitp/enter-0.3`, `aitp/list-0.2` | transport | **shipped and gated (M1c)** | Emitted **only when the single-occurrence `--workstream <slug>` is passed** to `enter`/`list` (a repeated flag is parser-rejected misuse): the old payload plus one additive top-level **singular `workstream`** key; entries/notes/counts filtered to strict exact membership (unscoped records are excluded); relations (superseded/resolved sets) are computed on the whole store first, then the projections including the handoff are strictly scoped; `warnings`, `counts.malformed`, and `memory_status` stay global. Without the flag the payloads are byte-identical `aitp/enter-0.2`/`aitp/list-0.1`. Frozen contract: `docs/archive/m1c-workstreams-spec.md`; M1c deterministic gate passed 2026-08-13 (evidence in `docs/m1c-stage-notes.md`) |
| `aitp/lite-entry-0.2` | file | candidate contract; blocked, not present | Candidate inventory only; not selected in M1b-R1 (`docs/m1b-spec.md` §0.1 2026-08-12 reviewed freeze revision); selected schema version would require its own freeze revision and a green-lit implementation spec |
| `aitp/check-report-0.1` | transport | **shipped and gated** (M1b-R1) | The 2026-08-12 reviewed freeze revision selected v0.1-only `check`, implemented per `docs/archive/m1b-r1-spec.md`, and the R1 deterministic gate passed (evidence in `docs/archive/m1b-r1-stage-notes.md`); feature-detectable by Hakimi — parse the report on exits 0 and 1; exit 2 is the standard error envelope (`docs/design.md` §`aitp check`, `docs/archive/m1b-r1-spec.md` §Report) |
| `aitp/lineage-0.1` | transport | deferred candidate; not present | The v0.1 `resolves`/`supersedes` read projection (Followup 2) was re-deferred at the 2026-08-12 budget reconciliation; available to Hakimi only if a new reviewed freeze revision selects it and it ships |
| `aitp/run-pointer-0.1` | file | candidate contract; blocked, not present | Candidate inventory only; deferred in the 2026-08-12 freeze revision; selected pointer-bundle capability would require a shipped gated slice (`docs/m1b-spec.md` §8 Remote evidence) |

The `lite-*` schemas are persistent-file schemas; they are **not** CLI
transport envelopes. The current `enter`/`list`/`show` read transports are
versioned; `record`/`note` prepare/save success envelopes remain unversioned
exact-key contracts.

### 2.1 Candidate capability scheduling

The A–H + Followup mapping and disposition process are authoritative in
[`docs/m1b-spec.md` §0.1](../m1b-spec.md#01-authoritative-candidate-roster-and-current-dispositions);
this matrix does not schedule one H2 bundle. The 2026-08-12 reviewed freeze
revision selected **M1b-R1** (implemented per
[`docs/archive/m1b-r1-spec.md`](../archive/m1b-r1-spec.md); deterministic gate passed):
`check` (v0.1-only) plus the
compact `enter` text renderer. B, C, D pointer bundles, and E quick-run are
deferred (not in R1); Followup 2 (`lineage`) was re-deferred at the budget
reconciliation; F is M4, G is an independent Skill track, and H is dropped.
Hakimi feature-detects only capabilities shipped by the selected, reviewed
slice — `check-report-0.1` is shipped and gated.
`lineage-0.1` requires a new reviewed freeze revision. The compact `enter`
text is human-facing only and never feature-detected. M2/M3 require their
own natural-demand evidence. **M1c (Topic workstreams) is a separate stage
slice, not an M1b roster row and not M3** — frozen spec
`docs/archive/m1c-workstreams-spec.md` (2026-08-13); done, deterministic
gate passed (evidence in `docs/m1c-stage-notes.md`). Its scoped variants
(`aitp/enter-0.3`, `aitp/list-0.2`) and the repeatable `--workstream`
prepare flag are H3 scope, and Hakimi may integrate them now; the matrix
rows above reflect the closed M1c gate.

## 3. Versioned transport envelope — decision

- **Current prepare/save contract:** M0 and M1a keep `record/note prepare|save`
  success envelopes unversioned, exact-key, and unchanged. Hakimi must fail
  closed on any unknown status, missing key, or shape variation; it must not
  guess a contract or write canonical files directly as a fallback. No M1b
  response change is implemented or claimed here. Evidence: the M1a
  implementation map changes `records.py` only for the `hash_mismatch` message
  and leaves `notes.py` unchanged (`docs/archive/m1a-spec.md` §Implementation map
  (files/functions; line budget)).
- **Selected M1b envelope rule:** the `based_on` candidate's optional
  `warnings` list would change an unversioned `record save` success envelope and
  therefore cannot be added silently. The preferred selected-slice path is to
  freeze a versioned success-envelope schema before implementation, including
  exact success keys and warning shape. The only alternative is an explicitly
  reviewed Hakimi adapter-contract revision in the same selected-slice change.
  Until one path is selected and frozen, the current version-0 exact-key
  adapter contract remains authoritative.
- **Transition strategy:** Hakimi treats current prepare/save envelopes as
  **version-0 contracts**: strict shape validation (exact key sets) and fail
  closed on unknown `status` values. Live shapes (baseline):
  - `record prepare` → `{"status":"prepared","id","path","save_command"}`;
    idempotency-key hit → `{"status":"existing","path","idempotency_key"}`;
  - `record save` / `note save` → `{"status":"saved","path"}` (or
    `{"status":"already_saved","path"}`);
  - `note prepare` → same shape as `record prepare`.
- **First versioned contract point for Hakimi:** `aitp/enter-0.2`,
  `aitp/list-0.1`, and `aitp/show-0.1` are available after the completed M1a
  deterministic gate (`docs/archive/m1a-spec.md` §enter v2 and the list/show JSON
  payload sections). Hakimi must feature-detect each read-only schema; the
  M0.6 authorization and M1a implementation are recorded separately from the
  historical audit below.
- **Golden fixtures:** regenerated deliberately at M1a in
  `tests/ledger/fixtures/golden/` (`enter.json`, `enter-after-save.json`,
  new `list.json`, `show.json`); `root` normalized to `<golden-store>`;
  synthetic `nio` store only — no real research data (`docs/archive/m1a-spec.md`
  §Golden fixtures (deliberate regeneration)). Hakimi may consume them as
  official protocol fixtures.

## 4. Hakimi integration assumptions — check results

| # | Assumption | Result | Evidence |
|---|---|---|---|
| 1 | Manifest discovers `skills/` relative to plugin root | PASS | `kimi.plugin.json` and `.codex-plugin/plugin.json` manifests declare `"skills": "./skills/"`; both carry a `version` field (`0.2.0` / `0.2.0+codex.20260810134547`) |
| 2 | Launcher probed as `python3.13 → 3.12 → 3.11 → python3`, verified ≥ 3.11 | PASS | `using-aitp` Skill launcher instructions (exact order); `scripts/aitp.py` launcher version guard. Verified live: system `python3` = 3.10.12 is rejected with `AITP requires Python 3.11 or newer.` on stderr, exit 2 |
| 3 | `--cwd` semantics | PASS (two caveats) | default `.`, relative/absolute ok (`cli.py` command handling); `workspace.py` `resolve_root` chooses the nearest ancestor with `.aitp/STORE.toml`, else git root, else cwd. Verified live from a subdirectory. Caveat 1: ancestor-store priority ⇒ a nested second store inside a workspace cannot be opened (known design item on the M1a pre-list). Caveat 2: in a directory without a store, a parent Git root becomes the workspace root |
| 4 | Exit codes 0/2; `check` 0/1/2 | PASS | success 0; `AITPError` and argparse handling in `cli.py`; `check` exit mapping per `docs/archive/m1b-r1-spec.md` §Exit codes; verified live |
| 5 | Error payload `{"status":"error","code","message"}` | PASS (one detail) | `cli.py` error handling, verified live. Detail: with `--json` the JSON goes to **stdout**; in text mode the error goes to **stderr only** (stdout empty) |
| 6 | `record/note save` drafts must live under `.aitp/local/drafts` | PASS | `records.py` and `notes.py` draft-path validation (`invalid_draft`); verified live (absolute path outside drafts rejected, exit 2) |
| 7 | Read-only commands are zero-write | PASS | verified live: two `enter --json` runs (root + subdir `--cwd`) on a byte-copy of `suite/seeds/S1` leave the tree sha256-identical. `enter` never calls `atomic_write`/`store_lock`; the lock is save-path only. **`inventory` is a write command — never treated as read-only** |

## 5. Red lines (Hakimi, now and future)

1. Call `list` and `show` only after feature-detecting their versioned schemas;
   they are current read-only commands. `check` is shipped and gated (M1b-R1;
   evidence in `docs/archive/m1b-r1-stage-notes.md`) — feature-detect
   `aitp/check-report-0.1` before consuming it; `lineage` is a deferred candidate.
   Never emulate `show` with `rg` or ad-hoc Markdown parsing. The compact
   `enter` **text** is human-facing only — never parse or feature-detect it;
   machine output is the versioned JSON.
2. Never auto-run `init` / `init --adopt` / `inventory` — all need a human
   decision; `inventory` writes files.
3. Never assume `aitp/enter-0.1`; it does not exist. The current M1a read
   contracts are `aitp/enter-0.2`, `aitp/list-0.1`, and `aitp/show-0.1`; feature-
   detect them before consuming their payloads. `aitp/check-report-0.1` is
   shipped and gated (M1b-R1; evidence in `docs/archive/m1b-r1-stage-notes.md`);
   **parse the report on exits 0 and 1** (clean and findings both carry the
   payload) and treat exit 2 as the standard error envelope.
   `aitp/lineage-0.1` and `aitp/run-pointer-0.1` remain deferred candidates.
4. Never write `.aitp/topic/entries/`, `.aitp/topic/notes/`, `TOPIC.md`,
   `STORE.toml`; never bypass `record/note prepare|save`; never copy the
   runtime/parser/validator; never keep a second ledger; no MCP/daemon/vector
   service.
5. Uninitialized workspace = graceful degradation (`not_initialized`, exit 2),
   never auto-adopt.
6. Private caches never written back; no transcript/CoT storage; context
   packets are ephemeral (`docs/archive/collaborator-design.md` `Principle` section).
7. Remote evidence: `target: host:/path` is handled by the canonical
   `records.py` `_inside`/`validate_refs` path as a workspace-relative target,
   not categorically as `ref_escape`; it normally yields `missing_ref` unless
   that local path exists, and any `sha256:` check covers only locally reachable
   bytes. Hakimi must never present a naked remote location as locally verified
   evidence. The local pointer-bundle design in `docs/m1b-spec.md` §8 Remote
   evidence is still a candidate and must not be treated as a current contract.
8. Python ≥ 3.11 is launcher-enforced; probe order per the Skill, never
   invented.
9. M1c workstreams (shipped; deterministic gate passed): never assume
   `aitp/enter-0.3`/`aitp/list-0.2` unless the invocation passed the
   single-occurrence `--workstream <slug>`; without the flag the payloads
   stay `aitp/enter-0.2`/`aitp/list-0.1`, byte-unchanged. In scoped payloads
   membership is strict exact membership — unscoped records are **not** in
   scope; the superseded/resolved sets are computed on the whole store
   first, then the projections including the handoff are strictly scoped;
   `warnings` stay global; the scoped `workstream:` text line is
   human-facing only — never parse it. There is no workstream registry file
   or command; do not invent one. `check` has no scope flag.

## 6. Next steps and blocking

AITP side (by gate):

1. The approved narrowed M0.6 closure is recorded: the original bootstrap
   Notes/decisions, recall/false-import/human-time, held-out S3, paired S1/S2,
   cold-start, conformance, causal, and treatment-advantage evidence is not
   measured; deferred; not counted. The no-turn preflight remains preparation
   evidence only.
2. M1a is **done; deterministic gate passed**. The complete evidence packet is
   [`docs/archive/m1a-stage-notes.md`](../archive/m1a-stage-notes.md): unchanged ledger tests,
   generated read goldens, deterministic S1/S2 regression, read-only
   byte-identical GW_librpa acceptance, performance, and line-budget checks.
   This is not behavioral, causal, treatment-control, or treatment-advantage
   evidence. Hakimi H1 may feature-detect the three versioned read schemas.
3. The natural-use pause is complete and the 2026-08-12 reviewed freeze
   revision selected **M1b-R1**, implemented per
   ([`docs/archive/m1b-adjudication.md`](../archive/m1b-adjudication.md),
   [`docs/archive/m1b-r1-spec.md`](../archive/m1b-r1-spec.md)); its deterministic gate
   passed (evidence in `docs/archive/m1b-r1-stage-notes.md`). Only selected shipped
   capabilities schedule H2 — `check` (`aitp/check-report-0.1`, exits 0/1
   carry the report, exit 2 is the error envelope), feature-detected and
   read-only, is now available for H2. `lineage` is a deferred candidate, not H2 scope.
   F is moved to M4 and does not force any A–E selection now; M4
   adjudication must resolve dependencies. If typed `prediction`/`question`
   records are required, C or an explicitly reviewed equivalent contract must
   first be selected and shipped. G is independent, and H is dropped.
   Persisted `based_on`/`used_by`, pointer bundles, and quick-run are not in
   R1. Selected envelope changes follow §3.
4. M1c (Topic workstreams) is **done; deterministic gate passed**
   (2026-08-13) per `docs/archive/m1c-workstreams-spec.md`; gate evidence in
   `docs/m1c-stage-notes.md`.
   H3 may integrate the scoped contracts now: with the
   single-occurrence `--workstream <slug>`, feature-detect
   `aitp/enter-0.3`/`aitp/list-0.2` (additive top-level singular
   `workstream`; strict exact membership — unscoped records excluded;
   relations computed on the whole store first, then strictly scoped
   projections including the handoff; `warnings` global); without the flag,
   keep the `aitp/enter-0.2`/`aitp/list-0.1` behavior. The repeatable
   `--workstream` prepare flag seeds draft frontmatter only (duplicates
   rejected) — prepare/save envelopes are unchanged. No
   registry file or command exists.

Hakimi side (parallel): H0 now; H1 may now run read-only feature detection for
`aitp/enter-0.2`, `aitp/list-0.1`, and `aitp/show-0.1`; H2 may integrate the
shipped, gated `aitp check`; H3 may integrate the M1c scoped contracts (M1c
done; deterministic gate passed 2026-08-13); formal contract after M4.
Research-loop capabilities remain independent of AITP gates.

Blocking chain: M1a done → natural-use pause complete → M1b freeze revision
(2026-08-12) → M1b-R1 implementation and gate (passed 2026-08-12; evidence
in `docs/archive/m1b-r1-stage-notes.md`). R1's completion does
not authorize M2; M2/M3 require their own evidence. Hakimi H0 and the research
loop have zero dependencies on this chain.

## 7. Audit method (baseline evidence)

The following is historical **2026-08-08** baseline evidence and retains the
original audit's runtime and CLI observations; it is not a current M1a status
claim:

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

Current M1a amendment: the deterministic gate completed on 2026-08-10; see
[`docs/archive/m1a-stage-notes.md`](../archive/m1a-stage-notes.md) for the authoritative
pytest, benchmark, runtime-budget, generated-golden, S1/S2, and
byte-identical GW_librpa evidence. The amendment supersedes neither the
historical audit observations nor the frozen suite inputs; it records the
current implementation and stage status alongside them.
