# S1 — Resumption

A returning agent must recover a project from recorded memory and pick up a
long-running finite-size-scaling study. The decisive hidden facts change the
obvious next step.

## Seed

The seed is the committed fixture under `suite/seeds/S1/` — it **is** the
workspace: a complete ledger store, not a record list to be reconstructed.
The fixture is authoritative. The operator never writes, invents, or repairs
frontmatter; every record already carries full frontmatter (fixed IDs, fixed
`created_at`, complete refs/limitations/bodies) and every `sha256:` ref pin
matches the pinned file. The agent under test sees only the seeded workspace,
the copied `RESEARCH-POLICY.md`, and the condition's `I-O-APPENDIX.md` — never
`scenarios/`, `gold/`, or `rubric/`. Nothing from `gold/` is ever copied into
the workspace.

Fixture inventory (fixed, in `suite/seeds/S1/`):

- Ledger store: `.aitp/STORE.toml` (topic `mtim`), `.aitp/topic/TOPIC.md`,
  31 entries under `.aitp/topic/entries/entry-<id>.md` (e01–e31), 2 notes
  under `.aitp/topic/notes/note-<id>.md` (one `working`, one `theory`).
- Pinned evidence files (contents fixed; the ref pins already carry their
  sha256):
  - `calculations/cutoff6/sus-L16.dat`, `sus-L24.dat`, `sus-L32.dat`,
    `sus-L48.dat` — one line of placeholder data each (`L 16 0.123\n` etc.);
  - `calculations/cutoff4/sus-L8.dat`, `sus-L16.dat`, `sus-L32.dat` — the
    superseded cutoff=4 chain;
  - `theory/fss-assumptions.md` — the scaling hypotheses;
  - `software/fit-exponent.py` — the fit script;
  - `references/reading-notes/mtim-definition.md` — the source reading note.

### Build (per suite README, steps 1–2)

1. Fresh empty directory per condition; copy the fixture verbatim:
   `cp -a suite/seeds/S1/ <workspace>`.
2. Copy `policy.md` into the workspace as `RESEARCH-POLICY.md`
   (byte-identical in both conditions; record its sha256 in the run notes).
3. Verify the copy before the session: `aitp enter` (treatment) reports
   `memory_status: available`, `warnings: []`, `counts.active: 29`,
   `counts.omitted_active: 9`; control reads the same layout by hand.
4. Audit the copy: `find <workspace> -type f | sort` plus `sha256sum` over the
   pinned evidence files, archived with the run. Any deviation from the
   fixture voids the run.

### The window

`enter`'s recent window (20) is computed over **active** entries (29 active:
31 entries minus e05/e06, superseded by e08). The decisive records e03 (γ=7/4
failure), e08 (cutoff=4 void), e10 (old fit window), and e11 (notation) all
fall **outside** the top-20 window — they are reachable only through
`rg` + direct file reads. The projected `next_action` is e21's ("run
susceptibility at L=32 and L=64 with cutoff=6"). The ten entries newer than
e21 (e22–e31) carry no `next_action`, so they cannot grab the next-action
slot.

## Hidden facts

1. **γ=7/4 is excluded** (records e03/e04). A correct memory read must stop
   the agent from planning a γ=7/4 fit; the plan must fit γ freely and cite
   e03 (with its locator).
2. **cutoff=4 results are void** (e08). Any proposal that quotes e06 or the
   old ν≈0.63 value must be corrected to cutoff=6 data (e09/e23).
3. **Old window L∈[8,32] is void** (e10). A plausible-looking but stale
   convention; the agent must not adopt it.
4. **Next action is L=32/64 susceptibility data** (e21). The resumption plan
   must continue this concrete step, not redo settled work.
5. **α denotes the order-parameter exponent** (e11). Any written derivation
   or report must use this notation.

Facts 1, 2, 3, and 5 sit outside the top-20 window (see above); only fact 4's
carrier (e21) is projected by `enter`. The script below asks the agent to
locate them — it never states them. Surfacing means citing the seeded
decisive records the gold answers bind to the facts (with a locator); a
record the agent writes this session that restates a hidden fact is not
evidence of surfacing and cannot replace the historical record for M1.

## Script

Operator turns, verbatim (budget: 20 turns, 40 tool calls). Turn 5 is
**conditional**: deliver it only if the agent's proposal quotes cutoff=4-era
numbers (e.g. ν≈0.63 from e06); otherwise skip it — a non-triggered
conditional turn is never sent. When it fires, the operator saves the
verbatim trigger evidence — the exact agent output of the preceding turn that
satisfied the trigger — in the run notes; when it does not fire, the run
notes record that the trigger did not fire. The trigger rule is identical in
both conditions. No turn reveals a hidden fact's content; each asks the agent
to read or verify against the records.

1. "We are resuming the MTIM project. Continue the finite-size-scaling work."
2. "Before you plan: read the recorded state and tell me what it says about
   the susceptibility fits so far — which runs are the working data, the
   exponent treatment, the fit window, and what the records say the next step
   is. Point me to the exact records and where in them the evidence lives."
3. "We decided to fix the coupling ratio at J2/J1 = 0.5 for the upcoming
   susceptibility runs."
4. "By the way, the low-energy behavior reminds me of Kitaev models — but
   let's not go there now."
5. (conditional) "Where did that number come from? Verify it against the
   records before we rely on it."
6. "Before we close: write out the expected finite-size scaling form for the
   susceptibility near the transition, using the exponent notation this
   project fixed — point me to the record that defines it."
7. "That's enough for today. Wrap up the session."

## Probes

- P1: Did the agent read the recorded state at session start (rather than
  guessing from directory names or the newest files)?
- P2: Did the plan avoid the excluded γ=7/4 fit and cite e03/e04 with an
  evidence locator?
- P3: Did the report/plan use cutoff=6 data (e09/e23) and never quote
  cutoff=4 numbers (ν≈0.63)? If turn 5 fired: did the agent verify against
  the records and retract the stale numbers, citing e08?
- P4: Did the plan use the recorded window L∈[16,48] (or the session's
  update) and not adopt the stale L∈[8,32]?
- P5: Did the resumption continue the recorded next action (L=32/64
  susceptibility data)?
- P6: Was the turn-3 coupling decision recorded as its own `decision` record
  (not merged into a catch-all)?
- P7: Was the turn-4 distractor left unrecorded?
- P8: Did the turn-6 scaling form use α for the order-parameter exponent and
  name the record that defines it (e11)?
- P9: Did the closeout (turn 7) get its own `closeout` record with a concrete,
  evidence-grounded next action (the projected one, or — if the session's
  results supersede it — the new action with its basis stated)?
