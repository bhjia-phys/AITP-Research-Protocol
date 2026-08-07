# Gold answers — S2 (durable events)

Assessor-only. Never copy into a seeded workspace.

## Hidden facts

| # | Fact | Decisive record + locator | Expected surfaced action change |
|---|---|---|---|
| 1 | bond=200 data is void | b05 `entry-0b05…` (supersedes b03); b07 `entry-0b07…` (supersedes b02) | The rung expectation quoted is 0.61(1) (bond=400), never 0.62(2) |
| 2 | bond=400 is the working bond | b04 `entry-0b04…` — Durable Summary; b05 | No plan reruns at bond=200; bond=400 is the default |
| 3 | density-matrix cutoff fixed at 1e-8 | b08 `entry-0b08…` — Durable Summary | Runs keep 1e-8; the turn-6 restatement produces no new record |
| 4 | next action = bond=400-vs-600 check at L=64 | b20 `entry-0b20…` — frontmatter `next_action` | The session continues this check |

Window note: the decisive records b04 (position 27), b05 (26), b07 (24),
and b08 (23) all sit OUTSIDE the `enter` top-20 window (28 active entries,
8 omitted). Recovery requires `rg` + direct file reads over the store, and
M1 requires a citation to the record plus an evidence locator. b20 sits at
position 11 and is additionally surfaced by `enter`'s `next_action`
projection (fillers b21–b30 carry none) — P10 checks the handoff was
actually used. The `Decisive record + locator` column is the M1 binding:
credit requires citing that seeded record with its locator. A record the
agent writes this session that duplicates or restates the historical
decision is not the decisive record and cannot substitute for it.

## Typed durable events (this session)

The fixed typed-event denominator is exactly the three events below. The
turn-3 correction is conditional — a replacing record is expected only if
the agent first misquoted 0.62(2) — and never enters this denominator. Turn
6 restates the already-recorded b08 convention and must produce no record.

| Event | Gold type | Evidence in transcript |
|---|---|---|
| Turn 4: L=64 entanglement entropy 1.96(1) | `result` | A result record with that value pinning `calculations/dmrg/entropy-L64.dat` |
| Turn 5: bond=600 memory blowup at L=64 | `failure` | A failure record (unresolved) pinning `calculations/dmrg/run-bond600-L64.out` |
| Turn 9: closeout | `closeout` | A closeout record with a concrete, evidence-grounded next action |

The turn-4 and turn-5 records must pin the operator-injected event artifacts,
byte-identical to the committed fixtures in `suite/events/S2/`: the ref
target is the workspace path above and the `sha256:` digest must equal the
canonical digest of the fixture —
`sha256:65dc4dbbc8854e1045c6569d702799952f086b8039553c2c64062548a77cd2de`
(`entropy-L64.dat`) and
`sha256:1355a40401105ca7fa706d6864aa99bc574bbfab35e5a4569e7d5cd078f02bee`
(`run-bond600-L64.out`). Both files are absent from the canonical seed and
exist in each workspace only from the operator's injection moment (recorded
in the run notes, just before the turn that names each file); a record that
pins a different path, a different digest, or a file that was already present
at session start fails this check. A record with no file pin at all (summary
only) is incomplete evidence, not recall.

Turn 3 (correction): the agent must use 0.61(1) and cite b07 replacing b02;
a replacing record is expected ONLY if the agent first misquoted 0.62(2) —
without a prior misquote a correction record is a false positive.
Turn 6 (cutoff restatement) must NOT produce a duplicate record — a new
record for an already-recorded convention costs precision.

Distractors (must be unrecorded): turn 7 (weather), turn 8 (undeveloped
dual-transformation idea).

A single catch-all closeout covering the result + failure counts as a type
error for both, not as recall.

The closeout's next action may be the projected handoff (b20) or a new one;
if the session's new results supersede it (e.g. the turn-5 bond=600
failure), the closeout must state the basis — which result or record takes
the action over. A closeout with the same substance worded differently still
counts as recall; phrasing alone never costs recall.

## Probe expectations

- P1: memory read at session start — required for M4. The read must go past
  the top-20 window to the decisive records (b04/b05/b07/b08) via
  `rg` + direct file reads; passive top-of-list reading does not surface
  them.
- P2: after turn 3, bond=400 value used with b07 citation — counts toward M1
  #1 and M2 correction handling; conditional, never in the fixed denominator.
- P3: turn-4 value recorded as `result` — counts toward M2. Must pin
  `calculations/dmrg/entropy-L64.dat` with the canonical digest
  (`sha256:65dc4dbb…`).
- P4: turn-5 event recorded as `failure` — counts toward M2. Must pin
  `calculations/dmrg/run-bond600-L64.out` with the canonical digest
  (`sha256:1355a404…`).
- P5: turn 6 restates the recorded b08 convention — expected: NO new record;
  a duplicate 1e-8 decision is a false positive (M2 precision), not recall.
- P6: turns 7 and 8 unrecorded — counts toward M3.
- P7: closeout recorded as `closeout` — counts toward M2.
- P8: no single catch-all covering heterogeneous events — type-error check
  for M2.
- P9: no duplicate record for the already-recorded cutoff convention —
  precision check.
- P10: session continues the b20 handoff (bond=400-vs-600 check at L=64)
  with a citation to b20 — counts toward M1 #4 and the closeout next-action
  check.

M4 items map to the end-state records as (each item must reference the
end-state record or file it lives in): goal — `TOPIC.md`; route — b05/b07
(the bond=400 working chain, still in force); next action — b20
`next_action` (the bond=400-vs-600 check at L=64); open corrections —
b05/b07 (the bond=200-era supersessions, still in force) and the unresolved
failures the end-state records flag (b11, and the session's turn-5 bond=600
failure, written unresolved). Item 4 requires the resumption session to
honestly enumerate the unresolved failures and open corrections the
end-state records flag; renaming them into unrelated "open questions" does
not satisfy it.
