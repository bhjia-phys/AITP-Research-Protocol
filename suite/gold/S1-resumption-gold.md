# Gold answers — S1 (resumption)

Assessor-only. Never copy into a seeded workspace. Score the anonymized
transcript against this file.

## M2 scope (fixed denominator)

M2's "records(this session)" counts **Entry** records saved during the
session; Notes written during the session are assessed under M1 #5 / M4 and
never enter the M2 numerator or denominator. The M2 gold typed-event list
below contains only **unconditional** events, so the denominator is fixed at 2
in every run of both conditions. The conditional correction (script turn 5)
is scored under P3 / M1 #2 and is **not** a member of the M2 list: in runs
where it never fired, no record is expected and recall must not suffer; in
runs where it fired, the required behavior is to retract the stale numbers
and cite the already-recorded supersession (e08) — no new record is expected,
because the ledger already contains the replacement. (If the agent had
written the stale numbers into a session record before the correction, a
replacing record is expected; scored under P3, still outside the M2 list.)

## Hidden facts

| # | Fact | Decisive record + locator | Expected surfaced action change |
|---|---|---|---|
| 1 | γ=7/4 is excluded | e03 `entry-0a03…` — Durable Summary ("do not support γ=7/4"); also e04 | Plan fits γ freely; the plan cites e03 with the record path and locator; a γ=7/4 plan scores 0 |
| 2 | cutoff=4 results are void | e08 `entry-0a08…` — Durable Summary ("Every result produced with cutoff=4 is void") | Working data are cutoff=6 (e09/e23); any cutoff=4 number (ν≈0.63) quoted is corrected; the validity of the data set is cited to e08 |
| 3 | old window L∈[8,32] void | e10 `entry-0a10…` — Durable Summary ("Do not use the old L∈[8,32] window") | The plan uses the recorded window L∈[16,48] (or the session's update) and does not adopt the stale window |
| 4 | next action = L=32/64 susceptibility data | e21 `entry-0a21…` — frontmatter `next_action` | The resumption continues this concrete step |
| 5 | α = order-parameter exponent | e11 `entry-0a11…` — Durable Summary | The turn-6 scaling form uses α for the order-parameter exponent and names e11 as the defining record |

Facts 1, 2, 3, and 5 sit outside `enter`'s top-20 window; the agent must
locate them via `rg` + direct file reads. The script never states any
fact's content. The `Decisive record + locator` column is the M1 binding:
credit requires citing that seeded record with its locator. A record the
agent writes this session that duplicates or restates the historical
decision is not the decisive record and cannot substitute for it.

## Typed durable events (this session) — denominator fixed at 2

| Event | Gold type | Evidence in transcript |
|---|---|---|
| Turn 3: "fix the coupling ratio at J2/J1 = 0.5 for the upcoming susceptibility runs" | `decision` | A `decision` record whose summary matches the coupling-ratio decision |
| Turn 7 closeout | `closeout` | A closeout record with a concrete, evidence-grounded next action |

No catch-all record covering several of the above counts as recall.

The closeout's next action may be the projected one (e21) or a new one; if
the session's results supersede the projected action, the closeout must state
the basis — which result or record takes the action over. A closeout with
the same substance worded differently still counts as recall; phrasing alone
never costs recall.

## Probe expectations

- P1: memory read at session start (treatment: `enter`; control: equivalent
  read) — required for M4.
- P2: plan avoids γ=7/4 and cites e03 with locator — counts toward M1 #1.
- P3: cutoff=6 data used; no cutoff=4 numbers; if turn 5 fired, the agent
  verified and retracted, citing e08 — counts toward M1 #2 (and the
  correction, outside M2).
- P4: recorded window used; stale L∈[8,32] not adopted — counts toward M1 #3.
- P5: next action L=32/64 continued — counts toward M1 #4 and M4 "next
  action".
- P6: turn-3 coupling decision recorded as `decision` — counts toward M2.
- P7: turn-4 distractor (Kitaev aside) unrecorded — counts toward M3.
- P8: turn-6 scaling form uses α for the order-parameter exponent and names
  e11 — counts toward M1 #5.
- P9: closeout with concrete next action — counts toward M2 and M4.

M4 items map to the end-state records as (each item must reference the
end-state record or file it lives in): goal — `TOPIC.md` "Research Goal";
route — e09/e21 (free-γ, cutoff=6); next action — e21 `next_action`; open
corrections — e08/e10 (the voided cutoff=4 chain and old window) and e03
(the γ=7/4 failure the records leave unresolved). Item 4 requires the
resumption session to honestly enumerate the unresolved failures and open
corrections the end-state records flag; renaming them into unrelated "open
questions" does not satisfy it.
