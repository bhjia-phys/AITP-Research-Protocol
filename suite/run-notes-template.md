# Paired-run notes — template (M0.6 conformance suite)

Operator fill-in form for ONE paired run (one scenario, two conditions:
treatment / control). Copy this file for every paired run and fill every
field. The completed file is the run's evidence spine: it anchors the hashes,
draws, budgets, instrumentation, end states, archive paths, and any
deviation.

- Save the completed copy at `suite/runs/<date>/<scenario>/run-notes.md`
  (`suite/runs/` is gitignored; it never enters a commit).
- This file and its completed copies are operator-only. They are NEVER placed
  in a run workspace and NEVER handed to the assessor before scoring is
  complete — the run notes contain the condition mapping.
- The run protocol is `suite/README.md`; scoring rules are `suite/rubric.md`;
  scenario scripts are `suite/scenarios/`. When this template and those files
  conflict, the README/rubric/scenario win.
- Gold answers are never copied into this file. Where a section would need a
  gold-derived value, reference the gold file instead and leave it sealed.

---

## 0. Run identity

| Field | Value |
|---|---|
| Run ID (convention: `YYYY-MM-DD-S<n>-<pair-seq>`, e.g. `2026-08-07-S1-01`) | |
| Date (local) | |
| Operator (name / machine / user account) | |
| Assessor (must NOT be the operator) | |
| Scenario (S1 / S2 / S3) | |
| Treatment machine/user | |
| Control machine/user | |
| Repo revision at run time (`git rev-parse HEAD`; `git status --porcelain suite/`) | |

## 1. Pre-run freeze (fill BEFORE the run starts)

### 1.1 Scenario, seed, and frozen artifacts

| Item | Value |
|---|---|
| Scenario file | `suite/scenarios/S<n>-*.md` |
| Scenario file sha256 (`sha256sum suite/scenarios/S<n>-*.md`) | |
| Gold file sha256 (`sha256sum suite/gold/S<n>-*-gold.md`; content stays sealed) | |
| Canonical seed path | `suite/seeds/<S>/` |
| Canonical seed hash (sha256 over the sorted `path<TAB>sha256` manifest; command in §2.3) | |
| Seed file count / inventory match (yes/no) | |
| `gold/` content absent from seed (yes/no) | |
| Rubric hash `sha256sum suite/rubric.md` (FROZEN thresholds — do not renegotiate per run) | |
| Agent config freeze date (config must not change between conditions or runs in the batch) | |
| S3 fixture freeze (only for S3 runs): the committed `suite/seeds/S3/` is frozen; canonical hash above doubles as the freeze hash | |

### 1.2 Model / provider / prompts / agent config / Skills / runtime

Fill every field BEFORE the run — this section is mandatory. Identity bytes
must be identical across both conditions of this pair; any difference is a
void condition (§7), and so is an identity field left unrecorded before the
run.

| Item | Value |
|---|---|
| Model id (exact string) | |
| Provider / endpoint | |
| Model version / release date (if known) | |
| System prompt file path + sha256 of the prompt bytes | |
| Developer prompt file path + sha256 (if the harness has a separate developer prompt) | |
| Agent config file path + sha256 (the exact config bytes used for both conditions) | |
| Config inventory (settings that can affect the run: temperature, context window, tool enablement, hooks) | |
| Agent harness / CLI client version (exact string) | |
| Skill: `aitp` (`SKILL.md` path + sha256 as delivered to the agent) | |
| Skill: `using-aitp` (`SKILL.md` path + sha256 as delivered to the agent) | |
| Skill delivery note (e.g. managed plugin copy path; reinstall after bundle changes) | |
| Skill policy decision (recorded pre-run): identical Skills in both conditions / treatment-only `aitp`+`using-aitp` as part of its adapter envelope | |
| Are Skills identical across both conditions / disabled on control as declared? | |
| Canonical runtime revision: repo `git rev-parse HEAD` (§0) + `git status --porcelain plugins/aitp-research-protocol/`; working-tree hash if uncommitted; sha256 of the runtime files as exercised | |
| CLI launcher + interpreter (exact invocation per `adapters/cli.md`): `<python3.11> <absolute-launcher>` (resolved via `command -v aitp` if on `PATH`); launcher absolute path + sha256; interpreter absolute path + `python --version` output; installed plugin manifest `version` field + manifest sha256 — the CLI has no `--version` | |
| Tool-call counting method (who counts, on what artifact: the operator, from the raw transcript / harness log, one fixed rule) | |
| Where the raw transcript / harness log is written | |

### 1.3 Policy and adapters

| Item | Value |
|---|---|
| `sha256sum suite/policy.md` (byte-identical in BOTH workspaces) | |
| `sha256sum suite/adapters/cli.md` (treatment `I-O-APPENDIX.md` bytes) | |
| `sha256sum suite/adapters/plain-files.md` (control `I-O-APPENDIX.md` bytes) | |

## 2. Isolation, preflight, and canonical-seed diff

### 2.1 Isolation evidence (both conditions)

- Agent's working directory is inside its isolated workspace (record `pwd`
  evidence per condition).
- The workspace contains ONLY the seed copy plus `RESEARCH-POLICY.md` and
  `I-O-APPENDIX.md` (record the file listing per condition).
- The repository, `suite/` (scenarios, gold, rubric, policy source, run
  notes), and any other suite files are NOT reachable from the agent's
  session (record how this was enforced per condition).

| Check | Treatment | Control |
|---|---|---|
| `pwd` / cwd evidence | | |
| Workspace file listing (match seed + 2 files) | | |
| Repo/suite unreachable evidence | | |

### 2.2 Control no-`aitp` preflight

Run on the control machine BEFORE the session; record the raw output.

| Command | Output (record verbatim) |
|---|---|
| `command -v aitp` (must print nothing) | |
| `python3 -c "import aitp"` (must fail) | |
| `python3 -m pip list | grep -i aitp` (must be empty) | |

Also record any other AITP install locations checked and ruled out (env,
shell rc, other interpreters).

The control session never invokes any AITP command: its `I-O-APPENDIX.md` is
the plain-files adapter and no control-session tool call may invoke the AITP
CLI. A successful AITP invocation in the control session is a void condition
(§7); a failed attempt is recorded in §9 (not void by itself).

### 2.3 Deployment and canonical-seed diff

1. Deploy: `cp -a suite/seeds/<S>/ <treatment-ws>` and
   `cp -a suite/seeds/<S>/ <control-ws>`.
2. Add the two root files to BOTH workspaces: `RESEARCH-POLICY.md` (bytes of
   `policy.md`) and `I-O-APPENDIX.md` (condition's adapter, verbatim).
3. Verify each copy against the canonical seed: `diff -r suite/seeds/<S>/
   <workspace>` — record the (must be empty) output.
4. Whitelist — the ONLY permitted differences between a deployed workspace
   and the canonical seed are:
   - `.aitp/local/` machine-local state (allowed to be absent or regenerated);
   - filesystem metadata only (mtime, owner, permissions) — never content.

Manifest command (same on the seed and on each deployed workspace):

```bash
cd <workspace-or-seed>
find . -type f | sort | while read -r f; do
  printf '%s\t' "$f"; sha256sum "$f" | awk '{print $1}'
done > manifest.txt
sha256sum manifest.txt        # canonical hash = sha256 of the manifest bytes
```

| Item | Record |
|---|---|
| Canonical seed manifest path + hash | |
| Treatment manifest hash (must equal canonical) | |
| Control manifest hash (must equal canonical) | |
| `diff -r` output treatment (empty) | |
| `diff -r` output control (empty) | |
| `RESEARCH-POLICY.md` sha256 — treatment | |
| `RESEARCH-POLICY.md` sha256 — control (must equal treatment) | |
| `I-O-APPENDIX.md` sha256 — treatment | |
| `I-O-APPENDIX.md` sha256 — control | |
| Treatment preflight: `aitp enter --json` (record `memory_status`, `warnings`, `counts` verbatim; must be `available` / `[]` / `active ≥ 28`, `omitted_active ≥ 8`) | |
| Seed validity note (validator output archived where?) | |

## 3. Condition order and randomization

Draw the EXECUTION order (treatment first or control first) with a recorded
random source; the assessor never sees this mapping until scoring is
complete.

| Item | Record |
|---|---|
| Draw command (e.g. `openssl rand -hex 16`) | |
| Raw draw value (hex) | |
| Mapping: first condition / second condition | |
| Where the sealed mapping is kept (operator-only) | |
| Pair-restart rule check: if either session of the pair is abandoned, BOTH conditions restart (README §3) — confirm applied when relevant | |

## 4. Budget accounting convention

Fixed counting rules, applied identically in both conditions:

- **Turns**: script turns are replayed verbatim, one at a time; the agent's
  reply must complete before the next turn is sent.
- **Tool calls (`TOOL_CALL(k)`)**: a counter incremented at EVERY agent tool
  invocation — every CLI command or file/search/editor tool call; a treatment
  CLI invocation counts as one tool call like any other. Same rule in both
  conditions. The operator counts from the authoritative raw transcript (the
  harness log) at reply boundaries — the transcript is operator-owned and
  never agent-authored or agent-read.
- **Wall clock**: `TURN_START(t, n)` = UTC wall-clock (ISO 8601) when script
  turn `n` is sent; `TURN_END(t, n)` = when its reply completes. All times
  are recorded in UTC, ISO 8601.
- **Exceeding a budget** ends the session and scores what exists — this is a
  session-end event, NOT a void condition. The operator stops the session at
  the first reply completion at-or-after the declared budget (no further
  turns are sent) and records a budget-stop marker (UTC, turn number,
  cumulative tool-call count, overshoot); the session end status is marked
  `budget-exceeded` (invalid as script-complete) — per the frozen rubric it
  still scores what exists.

Session-1 budget (from the scenario; fill per scenario):

| Condition | Turns | Tool calls | Wall clock (if any) |
|---|---|---|---|
| Treatment | | | |
| Control | | | |

Session-2 (resumption) budget — fixed small budget declared HERE before the
pair runs:

| Condition | Turns | Tool calls | Wall clock (if any) |
|---|---|---|---|
| Treatment | | | |
| Control | | | |

Budget-stop marker — recorded at run time whenever a session stops at-or-after
its declared budget (also records the session end status):

| Session | Budget-stop marker (UTC, turn, cum. calls) | End status (script-complete / budget-exceeded) |
|---|---|---|
| Session 1 — treatment | | |
| Session 1 — control | | |
| Session 2 — treatment | | |
| Session 2 — control | | |

### 4.1 Pre-declared resumption script (session 2) — fill BEFORE session 1

The session-2 script is fixed in the run notes before the run. Minimal form:
"We are continuing the project. Pick up where we left off." plus the
scenario's open-correction probe if the scenario declares one.

```text
<quote the exact session-2 turns, verbatim>
```

Also declare the session boundary here, before session 1 runs: session 2 is a
fresh agent process in a fresh conversation on a fresh `cp -a` copy of the
session-1 end state (stripped only of `.aitp/local/`); no transcript or
out-of-workspace artifact of session 1 is available to the agent. The script,
the §4 budget, and this boundary are pre-registered and stay frozen for the
pair.

## 5. Session 1 — instrumented log

Record one table per condition. The authoritative transcript is the
operator-owned raw chat/tool log (harness log), archived untouched; this
table is the per-turn instrumentation drawn from it. The agent never authors,
summarizes, or reads the transcript. Mark scenario-declared conditional turns
(e.g. S1 turn 5) in the "Cond." column; record whether each fired, and quote
the trigger basis in "Trigger basis" when it did. Turn-time event injections
(per scenario; S2 declares turns 4 and 5) are logged in §5.3; cross-reference
each injection's copy time in the corresponding turn row's Notes.
"Delivered verbatim (Y/N)" attests the agent-visible message was exactly the
scripted turn text, with no operator wrapper.

| Turn | Cond. (fired? Y/N/–) | TURN_START (UTC) | TURN_END (UTC) | Wall s | Cum. tool calls at reply end | Delivered verbatim (Y/N) | Trigger basis (quote) | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | |
| 2 | | | | | | | | |
| … | | | | | | | | |
| last | | | | | | | | |

### 5.1 FIRST_GROUNDED_PROPOSAL (M5)

Definition: the first agent turn containing a proposal (plan, answer, or
written text) that cites recorded evidence with a locator. Determined post
hoc from this log and the raw transcript — never self-reported by the agent.
M5 = (seconds from `TURN_START(t, 1)` to the marker, tool calls in between).
Recorded per condition; reported, not gated. If none occurs within the
budget, report "none within budget" with the budget values.

M5 is unscorable without run-time instrumentation: if the turn timestamps or
tool-call counts were not recorded at run time, M5 cannot be computed and is
never reconstructed post hoc — missing instrumentation is a void condition
(§7).

| Item | Treatment | Control |
|---|---|---|
| Marker turn # | | |
| Marker wall-clock | | |
| Seconds from TURN_START(t,1) | | |
| Cum. tool calls at marker | | |
| Tool calls in between | | |
| M5 outcome (pair) or "none within budget" | | |

### 5.2 Session-1 end state

Taken at session-1 close, before any cleanup: every record and file as the
agent left them. Never repair, clean, or re-validate before hashing.

| Item | Treatment | Control |
|---|---|---|
| End-state path | | |
| End-state manifest + canonical hash (same command as §2.3) | | |
| Entries/notes added this session (count only) | | |
| Budget state at close (turns / tool calls used) | | |
| Session ended by: script complete / budget / other (specify) | | |

### 5.3 Turn-time event injection log

Scenario-declared events that arrive mid-session with a physical artifact
(S2 declares two: turns 4 and 5; other scenarios add rows as declared) are
injected into BOTH workspaces by hand at the turn that speaks them. This log
pins each injected artifact: a real, frozen, byte-identical file that exists
in the workspace only from the injection moment onward. The artifact is
NEVER pre-placed in the seed or at deployment — pre-placing would leak the
event (and its turn) before it happens, so the canonical seed and the §2.3
deploy manifests never contain it. Event contents and canonical digests are
not hardcoded in this template; the scenario and the committed fixture
(`suite/events/S2/` for S2) are authoritative, and the operator records
observed values at run time. Event ID convention: `S<n>-E<turn>` (e.g.
`S2-E4` = S2 turn 4).

This section is operator-only: Target and per-condition hashes are part of
the condition mapping (§3) and never enter a scoring package (§8.2).

Procedure — human-executed; no harness performs or records injections:

1. BEFORE the run (freeze time): for each scenario-declared turn-time event,
   record its fixture path and derive the source frozen hash
   (`sha256sum suite/events/S2/<artifact>`). It must equal the digest the
   scenario pins; if not, the fixture changed — stop before starting the
   run. Declare the event row here (Event ID, user turn, target).
2. AT RUN TIME, immediately before sending the turn that names the artifact
   — strictly after the previous turn's reply completes and at-or-before
   `TURN_START` of the naming turn — copy the fixture into that condition's
   workspace (`cp -a suite/events/S2/<artifact>
   <workspace>/<target-path>`), then `sha256sum` the deployed copy and `cmp`
   it against the fixture. Record copy UTC (ISO 8601, same clock as §4) and
   the deployed hash.
3. Pre-injection invisibility proof: the artifact did not exist in the
   workspace before the copy. Record `grep -F '<target-path>' <canonical
   seed manifest>` (must print nothing); the §2.3 deploy manifests (canonical
   seed == treatment == control, pre-session) extend that absence through
   session start.
4. The injected file stays in place as the session's real evidence artifact:
   it rides into the session-1 end-state manifest (§5.2) and the session-2
   replication (§6) unchanged, and its hash there must still equal the
   source frozen hash. Injected artifacts are the ONLY permitted
   post-deployment workspace additions; any other difference remains void
   (§7).
5. Every deviation (early or late copy, hash mismatch, path difference,
   missed `cmp`/`grep`, any §7 near-miss) goes in the Deviation column AND
   in §9. An artifact found in a workspace with no logged row, or with
   deployed bytes differing from the source frozen hash, voids the run.

| Event ID | Source frozen hash | Target (treatment / control) | Copy UTC (T / C) | Deployed sha256 (T / C) | User turn | Pre-injection invisibility proof | Deviation |
|---|---|---|---|---|---|---|---|
| S2-E4 | | treatment + control | T: / C: | T: / C: | 4 | | |
| S2-E5 | | treatment + control | T: / C: | T: / C: | 5 | | |

One row per event; the T / C sub-fields record each condition's copy. Both
deployed hashes must equal the source frozen hash — byte-identical across
conditions (`cmp` the two deployed copies as well).

## 6. Session 2 (M4 resumption) — fresh-session replication

1. Build the fresh workspace with `cp -a` from the condition's session-1 end
   state, stripped ONLY of `.aitp/local/` transient state. Nothing else is
   repaired, cleaned, or re-validated.
2. `RESEARCH-POLICY.md` and `I-O-APPENDIX.md` ride along in the copy; verify
   their sha256 still match §2.3.
3. Verify the replicated workspace manifest equals the session-1 end-state
   hash; record the (empty) `diff -r` output.
4. Run the pre-declared script (§4.1) under the pre-declared budget (§4),
   with identical instrumentation. The script, budget, and session boundary
   (§4.1) are pre-registered before session 1 and stay frozen for the pair.
   M5 is measured on session 1 only; session-2 time and tool calls are
   recorded descriptively.

| Item | Treatment | Control |
|---|---|---|
| End-state hash of replication source (= §5.2) | | |
| Replicated workspace manifest hash (must match) | | |
| `diff -r` output (empty) | | |
| Policy/adapter sha256 in replicated workspace | | |

Session-2 log (same columns as §5):

| Turn | TURN_START | TURN_END | Wall s | Cum. tool calls | Notes |
|---|---|---|---|---|---|
| 1 | | | | | |
| … | | | | | |

## 7. Void conditions (checklist)

If ANY of the following is true, the run (or the affected session) is VOID;
record the finding in §9 and do not score the affected material:

- [ ] Model, system prompt bytes, or agent config differ between the two
      conditions of the pair.
- [ ] `RESEARCH-POLICY.md` bytes differ between the two workspaces.
- [ ] A deployed workspace differs from the canonical seed beyond the
      whitelist (§2.3): content differences outside `.aitp/local/`, or
      `diff -r` non-empty.
- [ ] Any content from `gold/` is present in a seeded workspace.
- [ ] The agent saw the repository, `suite/` (scenarios, gold, rubric,
      policy source, run notes), or any file outside its isolated workspace;
      or a response demonstrably drew on those files.
- [ ] Control machine has `aitp` on `PATH` or importable (§2.2).
- [ ] Control session successfully invoked an AITP CLI command (failed
      attempts are recorded in §9, not void by themselves).
- [ ] Seed validity gate failed: `memory_status` ≠ `available`, non-empty
      `warnings`, `counts.active` < 28, or `counts.omitted_active` < 8.
- [ ] Assessor is the operator, or the assessor received raw transcripts or
      the condition mapping before scoring was complete.
- [ ] Instrumentation missing: turn timestamps or tool-call counts not
      recorded at run time (M5 and budget checks become unreadable).
- [ ] Identity fields (§1.2) not fully recorded before the run.
- [ ] A user turn was delivered with operator wrapper text beyond the
      scripted turn text, or a conditional turn fired without a recorded
      trigger basis (voids the probes the wrapper could have leaked).
- [ ] The transcript is not the operator-owned raw log (agent-authored,
      agent-summarized, or agent-read) — instrumentation and M5 are
      unreadable.
- [ ] One session of the pair was abandoned and BOTH conditions were not
      restarted (half-pair drift confound).
- [ ] Condition order draw not recorded, or the draw was performed after the
      first session of the pair.
- [ ] Turn-time event injection (§5.3): an event artifact present in a
      workspace with no logged row, deployed bytes differing from the source
      frozen hash, or present before its declared turn (pre-seeded leak).

NOT void by themselves (record, don't discard): budget exceeded (scores what
exists); conditional turn never fired; a scenario-declared N/A metric.

## 8. Archive and evidence paths

### 8.1 Raw transcripts (operator-only)

Full verbatim raw transcripts — the operator-owned harness logs, archived
untouched, never agent-authored, agent-summarized, or agent-read — per
condition and session, archived by the operator only. They never enter the
scoring package and the assessor never sees them.

```text
suite/runs/<date>/<scenario>/<condition>/session-1/transcript.<ext>
suite/runs/<date>/<scenario>/<condition>/session-1/end-state/   + manifest.txt
suite/runs/<date>/<scenario>/<condition>/session-2/transcript.<ext>
suite/runs/<date>/<scenario>/<condition>/session-2/end-state/   + manifest.txt
suite/runs/<date>/<scenario>/run-notes.md                       # this file
suite/runs/<date>/<scenario>/condition-mapping.sealed           # operator-kept
```

| Item | Path recorded |
|---|---|
| Treatment session-1 transcript | |
| Control session-1 transcript | |
| Treatment session-2 transcript | |
| Control session-2 transcript | |
| Sealed condition mapping location | |

### 8.2 Condition-neutral packets (scoring package)

The operator extracts per-probe evidence into condition-neutral packets:
agent text quoted verbatim, record IDs referenced, cited targets and
locators, timestamps, and tool-call counts, with tool names, command
invocations, executable names, and condition-identifying paths (e.g.
`.aitp`, CLI command names) normalized to neutral labels (`memory-read`,
`record-write`, `search`, `<workspace>`, `<ledger>`). Mechanical traces never
reach the assessor.

```text
suite/runs/<date>/<scenario>/scoring-package/
  packets/            # one condition-neutral packet per probe
  scenario.md         # the scenario text
  rubric.md           # the rubric
  gold/               # the gold answers (assessor-only)
  thresholds.md       # frozen thresholds
  order-draw.sealed   # packet-order randomization draw
```

| Item | Value |
|---|---|
| Packet-order randomization draw (separate from §3; command + raw value) | |
| Package path | |
| Confirm: no raw transcript, workspace, or run notes inside the package | |

### 8.3 S3 hold-out and reporting order (declaration)

For every S3 run — and stated once here per batch — the operator confirms:

- S3 is held out: prompts, Skills, and adapters are NEVER iterated against
  S3 once the agent config is frozen; S3 is not referenced by S1/S2.
- Any structural repair to the S3 fixture before the first scored run is
  recorded in the stage notes as content repair, with what changed and why —
  never as iteration.
- Within this stage batch, S3 is run and reported FIRST and separately;
  S1/S2 scores follow. S3 numbers never enter the S1 + S2 pooled gates.
- Thresholds are revised only between stage runs, recorded as a diff in the
  stage notes; the frozen rubric hash is recorded in §1.1.

Signed (operator): ____________________  Date: ____________

## 9. Exceptions and deviations

Record every deviation from the protocol as it happens — missed marker,
interrupted session, clock drift, misdelivered turn, tool-call counting
ambiguity, any §7 near-miss. For each: describe, judge void vs non-void with
the reasoning, and get a second opinion if the run's validity is at stake.

| # | Time (UTC) | Deviation | Protocol step | Action taken | Void? (Y/N + rationale) |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |

## 10. Sign-off and unseal

| Item | Signature / date |
|---|---|
| Operator: run executed per protocol, deviations recorded | |
| Assessor: scored blind from the package only | |
| Condition mapping unsealed after scoring complete | |
| Score sheet archived at | |
