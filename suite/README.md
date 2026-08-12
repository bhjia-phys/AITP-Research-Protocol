# AITP conformance suite — operator manual

**Status: DORMANT.** This suite has never been scored: FROZEN v6 is an
anchored, unexecuted preregistration. The suite is not an active gate, and no
M4 or future gate depends on it. The frozen materials below are retained as
evaluation design history; any future evaluation needs a fresh, runnable,
predeclared design.

One scored run of the M0.6 suite core. The suite is an evaluation protocol
executed by a human operator with an agent under test; it is not an automated
harness. Everything here is files: seeds, event artifacts, transcripts,
rubrics, and gold answers. No runtime code is involved.

## Layout

```text
suite/
  README.md               # this file — the operator protocol
  policy.md               # semantic research-memory policy (tool-free)
  adapters/
    cli.md                # I/O appendix: policy ↔ AITP CLI
    plain-files.md        # I/O appendix: policy ↔ plain markdown files
  scenarios/
    S1-resumption.md      # script + probes only; the seed is seeds/S1/
    S2-durable-events.md  # script + probes only; the seed is seeds/S2/
    S3-heldout.md         # script + probes only; the seed is seeds/S3/ (held out)
  rubric.md               # metrics + pre-registered thresholds (frozen)
  FROZEN.md               # pre-first-run freeze record; verified before the first scored run
  run-notes-template.md   # operator run-notes template; copied into runs/ and filled in by hand
  score-sheet-template.md # assessor score-sheet template; copied and filled in during scoring
  gold/                   # assessor-only answers; NEVER copied into seeds
  events/                 # operator-side turn-time event artifacts; NEVER in a seed or initial workspace
    S2/                   # canonical artifacts injected at S2 turns 4 and 5 (step 4)
  seeds/
    S1/                   # authoritative committed seed fixture (verified in step 1)
    S2/
    S3/
  runs/                   # raw transcripts (operator-only), end states, manifests, scores (gitignored)
```

## Binding contract

These rules are not negotiable per run:

- The suite is human-executed: zero runtime lines, no automated harness, no
  LLM judge. The operator replays scripts; the assessor scores.
- The agent under test sees ONLY its isolated seeded workspace, containing the
  seed, `RESEARCH-POLICY.md`, and `I-O-APPENDIX.md`. It never sees the repo,
  `suite/` (scenarios, gold, rubric), or the run notes.
- Treatment and control use the same model, the same system prompt bytes, the
  same agent config, the same seed copies, and the same budgets. The ONLY
  intended difference is the `I-O-APPENDIX.md` adapter content.
- Scenario event artifacts (`events/`) are operator-side, turn-time evidence:
  never in a seed, never in a workspace at session start. The operator
  injects each artifact by hand into BOTH workspaces at the same script turn,
  immediately before sending that turn, and records source/target sha256 plus
  the injection time in the run notes (step 4). This mechanism is scenario
  event evidence — not an automated harness, and not a difference between
  conditions.
- The seed window is computed on ACTIVE entries (superseded records do not
  count): at least 28 active, and at least one decisive memory-gated fact must
  sit outside `enter`'s recent window of 20.
- Every fixture Entry and Note in a seed is legal v0.1 Markdown with fixed
  IDs and `created_at`, complete `refs`/`limitations`/body, and real sha256
  pins. Filler records never carry a `next_action`.
- Gold never enters a seed.

## One scored run, step by step

### 0. Preconditions

- Two isolated machines (or two isolated user accounts): **treatment** has the
  AITP CLI runnable per the invocation contract in `adapters/cli.md`;
  **control** has no `aitp` on `PATH` and no AITP install anywhere reachable.
  Verify on the control machine before the run and record the output:
  `command -v aitp` prints nothing, and no `aitp` package is importable by the
  agent's interpreter.
- Treatment CLI/Python/PATH preflight, recorded in the run notes BEFORE the
  run: the exact invocation contract from `adapters/cli.md` holds — the one
  fixed absolute launcher + fixed interpreter (Python ≥ 3.11), resolved via
  `command -v aitp` if `aitp` is on `PATH`. The CLI has no `--version`
  flag, so identity is recorded deterministically, never from the CLI:
  record the exact command line, the launcher absolute path + sha256, the
  interpreter absolute path + `python --version` output, the installed
  plugin manifest `version` field (+ manifest file sha256), the canonical
  runtime revision/tree hash, and the Skill hashes. The same invocation is
  used for the entire run; the agent never needs a per-turn operator grant.
- The control condition never invokes AITP: its `I-O-APPENDIX.md` is the
  plain-files adapter, the control machine has no `aitp` on `PATH` and
  nothing importable (step 2), and no control-session tool call may invoke
  any AITP CLI (a successful invocation voids the run; failed attempts are
  recorded in the run notes §9).
- The same model and the same system prompt are used in both conditions.
  Record in the run notes BEFORE the run, as mandatory identity: the model
  id, provider/endpoint, model version, the sha256 of the system prompt
  bytes (and of a separate developer prompt, if the harness has one), a hash
  of the agent configuration, the adapter file hashes, the treatment
  launcher absolute path + sha256 and interpreter path + `python --version`
  output (per `adapters/cli.md`), the installed plugin manifest version +
  manifest file sha256, the Skills as
  delivered (path + sha256) and the Skill policy decision (identical Skills
  in both conditions, or treatment-only `aitp`/`using-aitp` Skills as part of
  its adapter envelope — decided and recorded pre-run), and the canonical
  runtime revision (repo commit, or working-tree hash + `git status
  --porcelain` on the runtime path, plus the `scripts/vendor/aitp/` tree
  hash as exercised). If any of these differ between the two
  conditions, the run is void; any of these fields left unrecorded before the
  run is also a void condition.
- Assessor is not the operator; the assessor receives only the
  condition-neutral per-probe evidence packets (step 7), never transcripts;
  the condition mapping stays sealed with the operator until scoring is
  complete.
- Freeze check (first scored run): the operator verifies `FROZEN.md` — every
  item on the freeze record (rubric thresholds, canonical seeds, scenario
  scripts, event artifacts (`events/`), adapters, agent config,
  runtime/test baseline, S3 hold-out) must
  be frozen and recorded there. An unfrozen item voids the run as the first
  scored run and must be resolved and recorded in the stage notes before any
  scoring. The 2026-08-07 pre-first-scored-run static repair — the
  unexecutable `aitp --version` requirement replaced by deterministic
  treatment-identity recording (see Treatment preflight above; recorded in
  `docs/archive/m0.6-suite.md`) — supersedes the v5 freeze hashes of
  `adapters/cli.md`, `README.md`, and `run-notes-template.md`, so FROZEN.md
  must be re-issued as version 6 from the current tree before the first
  scored run.
- Templates are documentation, not tooling: the operator copies
  `run-notes-template.md` into `suite/runs/<date>/<scenario>/` and fills
  every hash/path placeholder by hand as the run proceeds; the assessor
  copies `score-sheet-template.md` before scoring (step 7) and fills it in
  by hand. No script, hook, or harness reads or generates these files.
- `suite/runs/<date>/` collects transcripts, end states, manifests, and scores
  (gitignored).

### 1. Verify the canonical seed fixture

For each scenario `S` (S1, S2, S3) the canonical seed is the authoritative
committed fixture at `suite/seeds/<S>/` — it IS the workspace: a complete
ledger store, not a record list to be reconstructed. The operator never
builds, writes, invents, or repairs any record, frontmatter, or pinned file:
every record already carries full frontmatter (fixed `id`, fixed
`created_at`, complete `refs`, `limitations`, `resolves`/`supersedes`,
`next_action`) and every `sha256:` ref pin matches the pinned file. The
scenario's Seed section only inventories the fixture; it is not a build spec.
The fixture is identical for both conditions — the plain-files condition
reads the same store layout by hand (see `adapters/plain-files.md`); nothing
is created by hand. Verification, all recorded in the run notes (the
filled `run-notes-template.md` copy from step 0):

1. Confirm the fixture is present and matches the committed repository bytes
   (no local edits under `suite/seeds/<S>/`), and that the file list matches
   the scenario's inventory.
2. Confirm nothing from `gold/` is in the seed, and confirm none of the
   scenario's event-artifact paths (step 4) exists in the seed — a
   pre-seeded artifact would leak the event before its turn.
3. Validate the seed and record the validator output in the run notes:

   ```text
   aitp enter --json   # from suite/seeds/<S>/
   ```

   - `memory_status` must be `available` and `warnings` must be `[]` (zero
     malformed records — the run starts only from a clean store).
   - The window check is on ACTIVE entries: `counts.active` must be ≥ 28.
     The `enter` recent window is the 20 most recent active entries, so
     `counts.omitted_active` must be ≥ 8.
   - At least one decisive hidden-fact record (from the scenario's gold
     answers) must be absent from `recent_entries` — a fact whose recovery
     requires going past passive top-of-list reading.
   - No filler record carries a non-empty `next_action`: the `next_action`
     `enter` reports must come from the scenario's intended decision or
     closeout record, never from a filler.

4. Record the canonical seed state in the run notes: the sorted file list
   (`find . -type f | sort`) with per-file sha256, plus a canonical hash
   defined as sha256 over the sorted `path<TAB>sha256` manifest. The same
   manifest is used to verify both deployed copies in step 2.

### 2. Deploy to two isolated workspaces

1. Copy the canonical seed byte-for-byte into the treatment workspace and the
   control workspace (`cp -a`), then verify each copy against the canonical
   seed with `diff -r`; record the (empty) diff output.
2. Add two files at the root of BOTH workspaces:
   - `RESEARCH-POLICY.md` — the bytes of `policy.md`. The copy is identical in
     both conditions; record its sha256. If the two copies ever differ, the
     run is void.
   - `I-O-APPENDIX.md` — the condition's adapter, verbatim: treatment gets
     `adapters/cli.md`, control gets `adapters/plain-files.md`. The delivery
     mechanism and filename are fixed and identical; only the adapter content
     differs, and that is the whole point of the comparison. Record each
     sha256.
3. Machine-local difference whitelist — the ONLY permitted differences between
   a deployed workspace and the canonical seed (plus the two files above).
   Any other difference voids the run:
   - `.aitp/local/` — machine-local store state: `config.toml` holds the
     absolute `workspace_root`, and drafts/scratch/locks are transient. When
     deployed by copy these bytes are identical anyway; if this subtree is
     regenerated locally, it is the only subtree allowed to differ.
   - filesystem metadata only (mtime, owner, permissions) — never content.
4. Pre-flight checks, all recorded in the run notes:
   - treatment workspace: `aitp enter --json` must report
     `memory_status: available` and `warnings: []`.
   - control machine: `command -v aitp` empty; no importable `aitp`.
   - `RESEARCH-POLICY.md` sha256 equal across the two workspaces.
5. The agent works with cwd inside its workspace; the repo and `suite/`
   (scenarios, gold, rubric, policy source, this file) are never visible to
   it. The workspace is its entire world.

Event artifacts are never deployed at this step: no file from `events/`
exists in either workspace at session start. Injection happens by hand, at
the event's script turn (step 4).

### 3. Paired-run order randomization

A paired run is one scenario, two conditions, same seed bytes, same
model/prompt/config, same budgets. Before the pair starts, draw the execution
order — treatment first or control first — with a recorded random draw (e.g.
`openssl rand`), and record the draw in the run notes. The assessor never
sees it. If either session of the pair must be abandoned, restart BOTH
conditions: a half pair confounds drift (time of day, API changes, operator
fatigue) with condition. The scoring order is a separate, later draw (step 7).

### 4. Session 1 — the scenario script

- Instrumentation markers, defined before the run and recorded by the
  operator at each point:
  - `TURN_START(t, n)` / `TURN_END(t, n)`: UTC wall-clock (ISO 8601) when
    script turn `n` is sent and when its reply completes. Turns are replayed
    verbatim, one at a time, waiting for the agent's reply between turns.
  - `TOOL_CALL(k)`: a counter incremented at every agent tool invocation,
    counted under one fixed rule in both conditions (every CLI command or
    file/search/editor tool call the agent makes; a treatment CLI invocation
    counts as one tool call like any other).
  - `FIRST_GROUNDED_PROPOSAL(t, k)`: the operator flags the first proposal
    that cites a recorded record and an evidence locator (rubric M5). Record
    its completion wall-clock (UTC) and the `TOOL_CALL` count at that moment.
  - M5 = (`FIRST_GROUNDED_PROPOSAL` − `TURN_START(t, 1)` in seconds, tool
    calls in between). Recorded per condition; reported, not gated.
- Event artifact injection — scenario event evidence. Script turns can
  announce durable events that records must pin; the physical trace of such
  an event is a turn-time artifact whose canonical bytes are committed under
  `suite/events/<S>/` and injected into the workspace by the operator at the
  event's turn (S2 turns 4 and 5; the per-scenario event inventory — files,
  pinned paths, fixed digests, exact commands — is the scenario's Event
  injection section). For each scenario-declared event turn, in BOTH
  conditions:
  1. Confirm the artifact's pinned path does NOT exist in the workspace yet
     — the agent must not have seen it.
  2. Copy the canonical artifact byte-for-byte from `suite/events/<S>/` to
     its pinned path in the workspace (`cp -a` by hand; no script, hook, or
     harness).
  3. Record in the run notes, BEFORE the turn is sent: the canonical source
     sha256, the workspace target sha256 (must equal the source — the
     scenario fixes the expected digest), and the injection wall-clock (ISO
     8601, same clock as the turn markers).
  4. Send the user turn only after the injection; its `TURN_START` is
     recorded as usual.
  The same bytes, the same turn, and the same procedure apply in both
  conditions; the recorded target sha256 must match across conditions. The
  artifact is never visible earlier: not in the seed (checked in step 1), not
  at deploy (step 2), not before the previous turn's reply completed. An
  artifact visible before its turn, or divergent target digests between the
  conditions, voids the probes that depend on it (S2 P3, P4) — record the
  deviation in the run notes. The artifact carries no information beyond the
  turn text: it is the event's physical trace, so the record can pin it and
  the assessor can verify the pin. After the turn it stays in the workspace —
  end-state snapshots and session-2 replication carry it unchanged; it is
  evidence, not transient state (unlike `.aitp/local/`).
- The scenario declares a fixed per-session budget (turns and/or tool calls);
  the tool-call budget is 40 calls in S1/S2/S3. The operator counts
  `TOOL_CALL(k)` from the authoritative transcript (below) under the one
  fixed rule, in both conditions, at reply boundaries. When a reply
  completion brings the cumulative count to the declared budget or beyond,
  the operator stops the session immediately — no further turns are sent —
  and records a budget-stop marker (UTC, turn number, cumulative count,
  overshoot); the session end status is marked `budget-exceeded` (invalid as
  script-complete). Per the frozen rubric, exceeding a budget ends the
  session and scores what exists: this is a session-end event, NOT a void
  condition; the marker is what makes the stop auditable.
- The authoritative transcript is operator-owned: the raw chat/tool log the
  agent harness captures, archived untouched — never agent-authored,
  agent-summarized, or agent-read. Per script turn it must contain, at
  minimum: the exact delivered user message, the agent's full reply output,
  UTC `TURN_START`/`TURN_END`, the cumulative tool-call count at reply end,
  and the `FIRST_GROUNDED_PROPOSAL` marker when it fires. It is the only
  source the operator draws from (budget counter, M5, packet extraction) and
  the only thing archived as the transcript (step 6); scoring draws only from
  condition-neutral packets (step 7).
- Verbatim delivery: the agent-visible user message per turn is EXACTLY the
  scripted turn text. Any operator instruction (budget, boundary, CLI path,
  framing) is delivered outside the conversation or fixed pre-run in the
  environment/adapter — never as per-turn wrapper text. A wrapped turn is
  recorded as a deviation and voids the probes whose evidence the wrapper
  could have supplied.
- M5 is unscorable without run-time instrumentation: if turn timestamps or
  tool-call counts were not recorded at run time, M5 cannot be computed and
  is never reconstructed post hoc — missing instrumentation is a void
  condition (run-notes §7).

### 5. Session 2 — end-state resumption (operationalizes M4)

Rubric M4 is scored "on a fresh session seeded from the scenario's end state";
this protocol runs that session for real.

1. After session 1, build a fresh workspace with `cp -a` from the
   condition's session-1 end state — every record and file as they were at
   session-1 close, including records the agent wrote — stripped only of
   `.aitp/local/` transient state. Never repair, clean, or re-validate the
   end state before this session.
2. Both conditions run session 2, each on its own end state.
3. Pre-registration (M4): the resumption script — the exact verbatim prompt —
   its budget (turns and tool calls), and the session boundary are fixed in
   the run notes BEFORE session 1 runs and stay frozen. The session boundary:
   session 2 is a fresh agent process in a fresh conversation on a fresh
   `cp -a` copy of the session-1 end state; no transcript or artifact from
   session 1 is available to the agent; the session ends at its declared
   budget or script completion. Minimal script form: "We are continuing the
   project. Pick up where we left off." plus the scenario's open-correction
   probe, if the scenario declares one; fixed small budget declared pre-run
   (e.g. 6 turns, 15 tool calls).
4. Instrumentation is identical to session 1 (turn and tool-call markers,
   timestamps). M5 is measured on session 1 only; session 2 time and tool
   calls are recorded descriptively.
5. The assessor scores the four checklist items — current goal, active route,
   next action, open corrections — from the session-2 condition-neutral
   evidence packet (the mechanically extracted verbatim agent evidence from
   the resumption session, per step 7), against the end-state records or
   files the gold answers name for each item. The raw session-2 transcript
   and the live end state never reach the assessor.

### 6. Archive

Save under `suite/runs/<date>/<scenario>/`, per condition and session: the
raw transcripts, the end-state snapshots with a per-file sha256 manifest, the
run notes — the filled `run-notes-template.md` copy: preconditions,
model/prompt/config hashes, seed canonical hash, whitelist check output,
order draws, budgets, M5 markers, event-injection records (source/target
sha256, injection times) — and the sealed condition mapping. All of
it is gitignored. Raw transcripts are operator-archived evidence only: they
never enter the scoring package and the assessor never sees them.

### 7. Blind scoring

- Boundary: the operator assembles the scoring package and then does not
  score; the assessor scores and never sees anything outside the package.
- For scored runs, review happens ONLY through the independent
  condition-neutral blind packets: the assessor — and any stage or meta
  reviewer — receives only the scoring package; raw-transcript review is
  never part of a scored run. Before the first scored run, the operator runs
  one dry rehearsal of packet extraction so the normalization rules are
  exercised once.
- Per rubric's scoring procedure, the operator extracts per-probe evidence
  into condition-neutral packets: agent text quoted verbatim, record IDs
  referenced, cited targets and locators, timestamps, and tool-call counts,
  with tool names, command invocations, executable names, and
  condition-identifying paths (e.g. `.aitp`, CLI command names) normalized
  to neutral labels (e.g. `memory-read`, `record-write`, `<workspace>`,
  `<ledger>`). Mechanical traces never reach the assessor.
- The package contains ONLY the per-probe packets, the scenario text, the
  rubric, the gold answers, and the frozen thresholds. Raw or full
  transcripts, workspaces, run notes containing the condition mapping, and
  raw console logs never enter it — raw transcripts are archived by the
  operator only (step 6).
- Event-artifact sha256 digests are condition-neutral (the artifacts are
  byte-identical across conditions) and may be listed in the packets, so the
  assessor can verify that a record's cited pin matches the artifact present
  in the workspace at the event's turn.
- The operator randomizes packet order across conditions (a separate draw
  from the execution order) before handing the package over.
- The assessor scores per `rubric.md`, one metric at a time, recording
  per-probe evidence in the filled `score-sheet-template.md` copy, with the
  hash/path of each evidence packet it is based on.

### 8. Report

- Compute the five metrics per condition and compare against the
  pre-registered thresholds in `rubric.md`.
- S3 is frozen: prompts, Skills, and adapters are never iterated against it.
  Within each stage batch, S3 is run and reported FIRST and separately; S1/S2
  scores follow.
- Thresholds may be revised only between stage runs, with the diff recorded in
  the stage notes.
- The completed score sheets (the filled `score-sheet-template.md` copies)
  are archived under `suite/runs/<date>/` with the run notes, all gitignored.
