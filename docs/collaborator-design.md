# AITP Conversation Memory and Collaborator Design

Status: blocked design option, v3.7 (aligned with `docs/roadmap.md` v3.7);
Skill-only (+0 runtime lines). M1a's deterministic gate has passed, but this
collaborator design remains a blocked Skill-only design option.
Depends on: the M0 ledger and M1 memory for the alpha (Entries and Notes
only); M2 reviewed artifacts enrich it later.
Supersedes: the earlier M3 "context engine" proposal, including
`aitp enter --task`.

## Principle

Conversation memory is a **Skill-driven lifecycle over the ledger**, not an
engine. Now it uses `enter`, the M1a read-only commands `list` and `show`,
the M1b-R1 read-only diagnostic `check` (shipped; deterministic gate
passed), direct files, and `rg`. The Skill supplies semantic judgment; context packets stay
ephemeral. There is no transcript archive, chain-of-thought capture, or session
daemon.

## Known limits (read before trusting)

- **Missed events are invisible.** The ledger validates what was written; it
  cannot distinguish "nothing durable happened" from "the agent forgot to
  record". Mitigation is the external conformance suite plus researcher
  review — not hooks or runtime enforcement.
- **Attribution is a claim, not proof.** `authority: human` and `created_by`
  are attributable statements; Git makes post-hoc edits visible, but cannot
  detect a first write that was already false. See the trust model in
  `docs/roadmap.md`.
- **Record order is checkable at write time; cognitive honesty is not.** A
  resolving Entry can reference only an existing prediction; that save-time
  check is the causal proof. The shipped `aitp check` diagnoses final state,
  not rebuild history; cognitive honesty remains Skill discipline.

## Lifecycle

1. **Enter** — at the start of research work in a workspace with `.aitp`,
   run `aitp enter`. Treat the output as recorded state, not scientific
   truth.
2. **Orient** — read the latest working Note, closeout, and task; use the M1a
   read-only `list`/`show` commands now, the M1b-R1 read-only `check`
   diagnostic (shipped), direct files/`rg` for full-text
   investigation.
3. **Verify** — open the pinned evidence behind any claim before relying on
   it. Disclose stale or missing sources.
4. **Work** — refresh the selection when the task, object, method, or
   assumptions change; check unresolved failures and conventions before
   proposing a step. Before consequential compute — scientifically critical,
   expensive, or convention-ambiguous — state the setup: the exact
   Hamiltonian with sign and coupling conventions, boundary, sector, target
   observable, scale; get an explicit confirm-or-correct when anything could
   be misread, but do not pester on routine, cheap steps. When the
   researcher pushes back, genuinely reconsider: restate the prior
   reasoning, take the objection seriously, change the conclusion if
   warranted or present both readings for re-ratification — never capitulate
   by default, never defend at length. If the exchange changes course,
   record it as a `decision`.
5. **Capture** — at a durable event, draft the smallest valid Entry through
   `prepare → save`. In the future conditional collaborator loop, predictions
   are saved before the executions they constrain (order guaranteed by the
   save-time target-existence check).
   Corrections from the researcher are recorded immediately (`decision`,
   `authority: human`) and change behavior in the same session.
6. **Close** — if work is unfinished, save a closeout Entry with a concrete
   next action. The latest active closeout is authoritative; a replacement
   closeout supersedes the previous handoff. Update the working Note separately.

### Read triggers

Session start or Topic change; before relying on a remembered claim; before
proposing a step that resembles a recorded failure; when the researcher asks
why a direction was chosen; when pins are stale or assumptions conflict.

### Write triggers

Only durable events: observation, result, failure, decision, source,
code-change, run, prediction, question, closeout, and evidence-based Notes.
Never: conversational filler, scratch work, unverified speculation presented
as results, duplicate retries.

### Modes

`suggest-only` or `agent-record` is a per-workspace policy in
`.aitp/local/config.toml`, read by the Skill. In `suggest-only`, the agent
prepares drafts and asks the researcher to save. When writes go through the
CLI, neither mode bypasses validation or provenance; agent-written records
carry `created_by: agent:*`.

### Human gates (human-confirmed, attributable)

- **Current:** `aitp record prepare --kind decision` → `record save`, with
  `authority: human` for researcher confirmation and `created_by` for attribution.
- **Future conditional M2:** `compile review` (hash-bound review/withdrawal) and
  `compile export` (publication), only if M2 is selected and shipped.
- **Future conditional M3:** `link save` requires explicit human confirmation;
  only if M3 is selected and shipped, an agent may execute it with attribution.

## M4 collaborator protocol

This blocked option remains Skill-only (+0 runtime lines). F is moved to M4 and
does not force any A–E selection now; M4 adjudication must resolve dependencies.
If a reviewed freeze revision selects the pilot in M1b, its separately reviewed
selected-slice spec must resolve dependencies. If the selected collaborator
protocol requires typed `prediction`/`question` records, roster C or an explicitly
reviewed equivalent contract must first be selected and shipped. M4 otherwise
needs its own natural-demand and prospective-evidence review before its gate.

The full loop below is not executable by the current runtime. Steps that save
`prediction`/`question` Entries are future conditional on C (or an explicitly
reviewed equivalent contract) being selected and shipped.

`aitp-collaborator` is a Skill, not a subsystem. For an active question it:

1. reconstructs the strongest current argument and its validity domain from
   reviewed artifacts and Entries;
2. keeps competing hypotheses visible, with their evidence and contradictions;
3. proposes a discriminating derivation, calculation, source check, or run —
   one whose outcome distinguishes specific hypotheses;
4. saves a `prediction` Entry before the test, including what result would
   kill the favored hypothesis;
5. compares outcome with prediction afterward — matched, partly matched, or
   did not match, and why; on mismatch, opens a failure and updates
   hypotheses — never rewriting history;
6. preserves rejected paths, disagreements, and uncertainty;
7. treats verification beyond what backs the current claim as opt-in
   compute: on challenge, proposes checks along the ladder limits →
   symmetry/consistency → convergence → cross-method → literature, with
   rough costs, and runs only what is confirmed;
8. proposes artifact promotion only when evidence warrants it, and asks.

## Acceptance

All behavioral acceptance runs through the external conformance suite, with
the plain-files control group:

- A fresh session with no chat history recovers the objective, conventions,
  active line, and next action; cites decisive records; does not re-propose
  resolved failures; omits irrelevant history under a fixed budget.
- A user correction persists and shapes later sessions.
- Prediction→outcome save order is respected (guaranteed by the save-time
  target-existence check).
- Prospective evaluation on real projects (≥ 4 sessions): the collaborator
  advances an active question, its proposed tests discriminate, and every
  reusable claim is evidence-linked.
