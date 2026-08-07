# S2 — Durable events

A mid-study session in which several durable events arise implicitly in the
conversation, alongside distractors that must not be recorded. Scoring
focuses on typed recall/precision and non-durable rejection.

## Seed

Topic: `blm` — "Bipartite spin ladder".

The canonical seed is the committed portable fixture at `suite/seeds/S2/`
(the workspace root). The fixture is authoritative: ids, `created_at`,
`refs`/`limitations`, bodies, Notes, and the pinned `sha256:` digests all
live there and must not be hand-retyped. Build the workspace by copying the
fixture byte-for-byte into an empty directory (`.aitp/local/` is
machine-local and whitelisted to differ or be absent; it is not part of the
fixture; the two event files of the next subsection are the ONLY other
workspace additions, and they enter at the turns the Script declares — never
at deployment), then verify:

```text
aitp enter --json          # run from the workspace root
```

Expected: `memory_status: available`, `warnings: []` (zero malformed
records), `counts: {active: 28, superseded: 2, unresolved_failures: 1,
malformed: 0, omitted_active: 8}`, and `next_action` sourced from
`entry-0b200000000000000000000000000000` ("check bond=400 vs bond=600 at
L=64").

Pinned evidence files (fixed contents; the fixture holds the actual
`sha256:` digests):

- `calculations/dmrg/rung-L32.dat` — `rung 0.62`
- `calculations/dmrg/entropy-L32.dat` — `S 1.83`
- `calculations/dmrg/run-bond200-L32.out` — `bond=200: no convergence; discarded-weight tail open`
- `calculations/dmrg/run-bond400-L32.out` — `bond=400: converged; rung 0.61(1)`
- `calculations/dmrg/run-bond400-L48.out` — `bond=400: converged; rung 0.58(2)`
- `calculations/dmrg/run-bond600-L48.out` — `bond=600: out of memory`
- `calculations/dmrg/run-bond400-L64.out` — `bond=400: converged; rung 0.59(2)`
- `calculations/dmrg/gap-fit-L3248.dat` — `Delta 0.34`
- `calculations/dmrg/gap-fit-L64.dat` — `Delta 0.30`
- `software/dmrg/truncation.py` — truncation driver (no numeric constants)
- `theory/CONVENTIONS.md` — ladder model and parameter convention

Run-time injected event files — NOT part of the seed; see Script for when
they enter the workspace. Both live in the committed fixture
`suite/events/S2/` with fixed contents and fixed digests:

- `entropy-L64.dat` → injected at `calculations/dmrg/entropy-L64.dat` —
  `S 1.96(1)`
- `run-bond600-L64.out` → injected at `calculations/dmrg/run-bond600-L64.out`
  — `bond=600: out of memory at L=64`

Canonical digests (sha256 of the committed `suite/events/S2/` bytes; the
operator re-derives them at injection and the run's records must pin the same
values):

- `suite/events/S2/entropy-L64.dat` → `sha256:65dc4dbbc8854e1045c6569d702799952f086b8039553c2c64062548a77cd2de`
- `suite/events/S2/run-bond600-L64.out` → `sha256:1355a40401105ca7fa706d6864aa99bc574bbfab35e5a4569e7d5cd078f02bee`

Pre-placing either file in a seeded workspace would leak the turn-4 and
turn-5 events before the turns that speak them, so they are never part of the
canonical seed: the operator injects each byte-for-byte (`cp -a`, sha256
recorded in the run notes) into BOTH workspaces immediately before the turn
that names it, and never earlier. From injection on, the file stays in place
as the session's real evidence artifact.

Records (32 total: 30 entries + 2 notes). The `enter` recent window is the
20 most recent ACTIVE entries; with 28 active entries the window omits the
8 oldest (b01, b04–b10). The `window` column shows where each record sits
(`top-20` / `omitted` / `superseded`):

| # | id | kind | created_at | summary | relations | window |
|---|---|---|---|---|---|---|
| 1 | b01 | source | 2026-04-01T09:00:00.000001Z | ladder model definition and parameter convention | refs: CONVENTIONS.md | omitted |
| 2 | b02 | result | 2026-04-03T09:00:00.000001Z | rung-operator expectation 0.62(2) at L=32 | refs: rung-L32.dat | superseded |
| 3 | b03 | run | 2026-04-04T09:00:00.000001Z | DMRG run, bond=200, L=32 | refs: run-bond200-L32.out | superseded |
| 4 | b04 | failure | 2026-04-05T09:00:00.000001Z | bond=200 does not converge (entropy too high) | refs: entropy-L32.dat | omitted |
| 5 | b05 | decision | 2026-04-05T10:00:00.000001Z | bond=400 for the ladder; bond=200 data void | resolves: b04; supersedes: b03 | omitted |
| 6 | b06 | run | 2026-04-06T09:00:00.000001Z | DMRG run, bond=400, L=32 | refs: run-bond400-L32.out | omitted |
| 7 | b07 | result | 2026-04-07T09:00:00.000001Z | bond=400 converges; rung expectation 0.61(1) | supersedes: b02; refs: run-bond400-L32.out | omitted |
| 8 | b08 | decision | 2026-04-08T09:00:00.000001Z | density-matrix cutoff fixed at 1e-8 | — | omitted |
| 9 | b09 | run | 2026-04-09T09:00:00.000001Z | L=48 run, bond=400, cutoff 1e-8 | refs: run-bond400-L48.out | omitted |
| 10 | b10 | result | 2026-04-10T09:00:00.000001Z | entanglement entropy S≈1.83(1) at L=32 | refs: entropy-L32.dat | omitted |
| 11 | b11 | failure | 2026-04-12T09:00:00.000001Z | L=48 run memory blowup at bond=600 | refs: run-bond600-L48.out | top-20 |
| 12 | b12 | closeout | 2026-04-13T09:00:00.000001Z | session done; next: L=64 rung expectation | — | top-20 |
| 13 | b13 | code_change | 2026-04-15T09:00:00.000001Z | DMRG script: truncation parameter cleanup | refs: truncation.py | top-20 |
| 14 | b14 | result | 2026-04-16T09:00:00.000001Z | L=48 rung expectation 0.58(2) | refs: run-bond400-L48.out | top-20 |
| 15 | b15 | observation | 2026-04-17T09:00:00.000001Z | cluster queue was down; runs delayed | — | top-20 |
| 16 | b16 | run | 2026-04-18T09:00:00.000001Z | L=64 run, bond=400, cutoff 1e-8 | refs: run-bond400-L64.out | top-20 |
| 17 | b17 | failure | 2026-04-19T09:00:00.000001Z | L=64 rung expectation drifts vs L=48 | refs: run-bond400-L64.out | top-20 |
| 18 | b18 | decision | 2026-04-20T09:00:00.000001Z | treat rung drift as finite-size; continue | resolves: b17 | top-20 |
| 19 | b19 | result | 2026-04-21T09:00:00.000001Z | gap estimate Δ≈0.34(3) from L=32/48 | refs: gap-fit-L3248.dat | top-20 |
| 20 | b20 | closeout | 2026-04-22T09:00:00.000001Z | next: check bond=400 vs bond=600 at L=64 | — | top-20 |
| 21 | b21 | run | 2026-04-23T09:00:00.000001Z | L=64 run, bond=400, cutoff 1e-8 (overnight) | refs: run-bond400-L64.out | top-20 |
| 22 | b22 | result | 2026-04-24T09:00:00.000001Z | L=64 rung expectation 0.59(2) at bond=400 | refs: run-bond400-L64.out | top-20 |
| 23 | b23 | observation | 2026-04-25T09:00:00.000001Z | cluster queue backlog; morning slots only | — | top-20 |
| 24 | b24 | run | 2026-04-26T09:00:00.000001Z | L=64 rerun, bond=400, initial-state sweep | refs: run-bond400-L64.out | top-20 |
| 25 | b25 | result | 2026-04-27T09:00:00.000001Z | L=64 rung stable 0.59(2) across initial states | refs: run-bond400-L64.out | top-20 |
| 26 | b26 | observation | 2026-04-28T09:00:00.000001Z | wall-time cap raised to 24 h on cluster | — | top-20 |
| 27 | b27 | decision | 2026-04-29T09:00:00.000001Z | use spin-adapted basis for L=64 production runs | — | top-20 |
| 28 | b28 | code_change | 2026-05-01T09:00:00.000001Z | DMRG script: spin-adapted basis flag | refs: truncation.py | top-20 |
| 29 | b29 | run | 2026-05-02T09:00:00.000001Z | L=64 production run, bond=400, spin-adapted | refs: run-bond400-L64.out | top-20 |
| 30 | b30 | result | 2026-05-03T09:00:00.000001Z | L=64 gap estimate Δ≈0.30(3) | refs: gap-fit-L64.dat | top-20 |
| 31 | n01 | note | 2026-04-21T12:00:00.000001Z | working: ladder status and open checks | basis: b07,b10 | — |
| 32 | n02 | note | 2026-04-15T12:00:00.000001Z | theory: single-triplet approximation | basis: b02 | — |

Every fixture record is legal v0.1 Markdown with fixed `id` and
`created_at`, complete `refs`/`limitations`/body and real `sha256:` pins
(digests computed from the pinned files; every `resolves`/`supersedes`
target exists, and `supersedes` targets are older). `b02`/`b03` are
superseded (inactive, absent from `recent_entries`); fillers `b21`–`b30`
carry no `next_action`, so the `next_action` projection is owned by b20 —
the newest record with a non-empty `next_action` (b04's historical
`next_action: "raise bond to 400"` stays in that record but never wins the
projection).

## Hidden facts

1. **bond=200 data is void** (b05 supersedes b03; b07 supersedes b02). Any
   proposal quoting the old rung expectation 0.62(2) must use the bond=400
   value 0.61(1) instead — this changes a concrete action.
2. **bond=400 is the working bond** (b04/b05). A plan that reruns at bond=200
   repeats a known failure.
3. **density-matrix cutoff is fixed at 1e-8** (b08). Runs must keep it;
   changing it per run violates the convention. Turn 6 only restates it —
   it must not produce a new record.
4. **Next action is the bond=400-vs-600 check at L=64** (b20). The session
   should continue it rather than redoing L=32.

Window note: the decisive records b04 (position 27), b05 (26), b07 (24), and
b08 (23) all sit OUTSIDE the `enter` top-20 window (28 active entries);
recovering them requires `rg` + direct file reads over the store, not passive
top-of-list reading. b20 (position 11) stays in the window, and its handoff
is additionally reported by `enter`'s `next_action` projection because no
newer record carries one. Surfacing means citing the seeded decisive records
the gold answers bind to the facts (with a locator); a record the agent
writes this session that restates a hidden fact is not evidence of surfacing
and cannot replace the historical record for M1.

## Script

Event injection (operator-only — the agent never sees this section). Both
conditions receive the same injections at the same script points; record each
sha256 in the run notes:

- Before sending turn 4 (after turn 3's reply completes), in that condition's
  workspace: `cp -a suite/events/S2/entropy-L64.dat
  <workspace>/calculations/dmrg/entropy-L64.dat`, then `sha256sum` the
  injected copy (must equal
  `65dc4dbbc8854e1045c6569d702799952f086b8039553c2c64062548a77cd2de`) and
  `cmp` it against the fixture. The file must not exist in the workspace
  before this moment.
- Before sending turn 5 (after turn 4's reply completes): `cp -a
  suite/events/S2/run-bond600-L64.out
  <workspace>/calculations/dmrg/run-bond600-L64.out`, sha256 must equal
  `1355a40401105ca7fa706d6864aa99bc574bbfab35e5a4569e7d5cd078f02bee`; record
  and `cmp` as above; same absence rule.

Never pre-place either file at deployment — injection is the earliest moment
the artifact exists. The turn text names the file's path so the agent can
open and pin the real artifact; the injected files stay in the workspace as
the session's evidence.

Operator turns, verbatim (budget: 18 turns, 40 tool calls):

1. "We are back on the ladder project. Let's look at the L=64 results."
2. "The rung expectation we quoted last time — where did 0.62 come from?"
   (This must be answered by retrieval before any disclosure: b02 is
   superseded — absent from `recent_entries` — and its evidence file
   `rung-L32.dat` is the 0.62 source; the voiding is disclosed only in
   turn 3.)
3. "That was the bond=200 run, which is void. Use the bond=400 value."
4. "While that settles: today the L=64 entanglement entropy converged to
   1.96(1) — the output file is `calculations/dmrg/entropy-L64.dat`."
5. "We also tried bond=600 for L=64 and it blew up memory again — the run
   log is at `calculations/dmrg/run-bond600-L64.out`."
6. "So keep the truncation exactly at 1e-8; we are not tuning it per run."
7. "Nice weather today, by the way."
8. "One more idea, half-baked: maybe a dual-transformation shortcut would
   skip DMRG — but I have not thought it through, so ignore it for now."
9. "Let's stop here and close out the session."

## Probes

- P1: Did the agent read the recorded state at session start?
- P2: After turn 3's correction, did the agent switch to the bond=400 value
  (0.61(1)) with a citation to b07? The correction is conditional: if the
  agent first quoted 0.62(2), it must record a replacing record naming b02;
  if it never misquoted, no correction record is expected. Either way the
  correction is not part of the fixed typed-event denominator.
- P3: Was turn 4's entropy value recorded as a `result` (not merged into a
  catch-all), pinning `calculations/dmrg/entropy-L64.dat` with a sha256
  digest equal to the committed `suite/events/S2/entropy-L64.dat` fixture?
- P4: Was turn 5's failure recorded as a `failure`, pinning
  `calculations/dmrg/run-bond600-L64.out` with a sha256 digest equal to the
  committed `suite/events/S2/run-bond600-L64.out` fixture?
- P5: Turn 6 restates the already-recorded 1e-8 convention (b08). Expected:
  NO new record — a duplicate `decision` for it is a false positive (M2
  precision), not recall.
- P6: Were turns 7 and 8 (chit-chat, undeveloped idea) left unrecorded?
- P7: Did the closeout (turn 9) get its own `closeout` record with a concrete,
  evidence-grounded next action (the bond=400-vs-600 check at L=64, or — if
  the session's new results supersede it — the new action with its basis
  stated)?
- P8: Count the records written this session; any single catch-all covering
  several of the typed events scores as a type error, not as recall.
- P9: Was no duplicate record written for the already-recorded cutoff
  convention (precision check)?
- P10: Did the session continue the recorded handoff (bond=400-vs-600 check
  at L=64, from b20) rather than redoing settled L=32 work?
