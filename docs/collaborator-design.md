# AITP Conversation Memory and Collaborator Design

Status: active design, v3.1 (aligned with `docs/roadmap.md` v3.1).
Depends on: the M0 ledger and M1 memory for the alpha (Entries and Notes
only); M2 reviewed artifacts enrich it later.
Supersedes: the earlier M3 "context engine" proposal, including
`aitp enter --task`.

## Principle

Conversation memory is a **Skill-driven lifecycle over the ledger**, not an
engine. Python provides deterministic structural access (`enter`, `show`,
`list`, `check`); the Skill provides all semantic judgment — what is
relevant, what is worth recording, when to stop and ask. Context packets are
ephemeral: assembled inside the conversation, never stored. There is no
transcript archive, no chain-of-thought capture, no session daemon.

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
  resolving Entry can only reference a prediction that already exists when
  it is saved; the save-time existence check is the causal proof. `aitp
  check` re-validates final-state consistency — it does not rebuild history.
  Whether the agent had already seen the outcome is Skill discipline,
  measured by the conformance suite.

## Lifecycle

1. **Enter** — at the start of research work in a workspace with `.aitp`,
   run `aitp enter`. Treat the output as recorded state, not scientific
   truth.
2. **Orient** — read the latest working Note, the latest closeout, and the
   researcher's current task. Use `list`/`show`/`rg` to fetch records
   relevant to the task.
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
   `prepare → save`. Predictions are saved before the executions they
   constrain (order guaranteed by the save-time target-existence check).
   Corrections from the researcher are recorded immediately (`decision`,
   `authority: human`) and change behavior in the same session.
6. **Close** — if work is unfinished, save a closeout Entry with a concrete
   next action and supersede the working Note with an updated one.

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

- `compile review` transitions (`agent_draft` → `human_reviewed`/`withdrawn`),
  each bound to the artifact's content hash;
- `compile export` (publication);
- `decision` Entries with `authority: human` (the researcher speaks or
  confirms; `created_by` still attributes the drafter);
- cross-topic `link save` (explicit human confirmation; an agent may execute
  the save with `created_by` attribution).

## M4 collaborator protocol

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
