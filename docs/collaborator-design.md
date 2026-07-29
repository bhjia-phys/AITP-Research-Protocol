# M3–M4 Collaborator Design

Status: roadmap baseline  
Depends on: M0 ledger, M1 graph, M2 compilers

## Purpose

M3 makes AITP memory operational inside a research conversation. M4 uses that
grounded context to participate in a long-running scientific reasoning loop.

They are separate because remembering the right thing is easier to verify than
proposing good science. M4 may start only after M3 is reliable.

## M3: context engine

M3 is a small orchestration layer over existing records, not a database,
transcript store, daemon, or MCP server.

### Context Packet

For the current task, M3 derives an ephemeral packet with:

```text
Topic and current task
Active question and next action
Notation, conventions, assumptions, and constraints
Relevant decisions, results, failures, and unresolved contradictions
Reviewed physical knowledge
Applicable Skills and their validity limits
Candidate Insights, visibly marked unverified
Open commitments and questions
Exact source references, freshness, and omissions
```

The packet is disposable. Its sources remain the ledger, graph, compiled
artifacts, and research files.

### Conversation loop

1. **Enter** — detect the workspace and Topic; read grounded state.
2. **Orient** — interpret the user's current task and assemble a bounded packet.
3. **Verify** — open decisive sources before relying on a remembered claim.
4. **Work** — refresh context when the task, method, object, or assumptions change.
5. **Capture** — classify durable events and draft the smallest valid Entry.
6. **Close** — record unresolved questions, commitments, and the concrete next action.

M3 should extend `aitp enter` with task-aware structured output rather than add
a general `search` command:

```text
aitp enter --task "<current task>" --budget compact|standard|deep --explain
```

The Codex Skill drives this lifecycle automatically. Researchers should not
need to manage a separate session object.

### Read policy

Refresh context when:

- a session starts or the active Topic changes;
- a named object, method, convention, or prior result becomes important;
- a proposed step resembles a recorded failure;
- assumptions conflict or evidence is stale;
- the user asks why a direction was chosen.

Selection order is:

```text
current task relevance
→ active decisions and constraints
→ unresolved failures and commitments
→ reviewed knowledge and applicable Skills
→ candidate Insights
→ recent activity
```

Recency alone is never sufficient.

### Write policy

Do not save transcripts or internal chain of thought. Save only durable
observations, results, failures, decisions, sources, code changes, reproducible
runs, closeouts, and evidence-based Notes.

All writes use the M0 draft, validation, and idempotency path. Agent-authored
records are labeled as such. Human review is required to:

- accept a scientific decision on the researcher's behalf;
- promote a claim into reviewed physical knowledge;
- publish a reusable Skill;
- accept an Insight as a research direction.

Workspace policy may choose `suggest-only` or `agent-record`. Neither mode may
bypass validation or provenance.

### M3 acceptance

On a real Topic with a long ledger, an agent starting with no chat history must:

- recover the correct objective, conventions, active line, and next action;
- cite the decisive records and disclose stale or missing sources;
- avoid proposing a previously resolved failed attempt;
- retain a user correction in later sessions;
- omit irrelevant history under a fixed context budget;
- create no duplicate or conversational-noise Entries.

## M4: scientific collaborator

M4 adds a reviewed research-state model:

```text
question → competing hypotheses → predictions → tests → outcomes
     ↑              ↓                  ↓          ↓
 assumptions   contradictions       methods    conclusions
```

The model is derived from evidence and reviewed artifacts. It does not replace
the ledger or silently convert suggestions into facts.

### Collaborator behavior

For an active question, M4 should:

1. reconstruct the strongest current argument and its validity domain;
2. expose unresolved assumptions, contradictions, and alternative hypotheses;
3. propose a discriminating derivation, calculation, source check, or run;
4. state the expected observation before the test;
5. execute or help execute an approved step using applicable Skills;
6. compare outcome with prediction and update the research state;
7. preserve rejected paths and uncertainty;
8. propose knowledge or Insight promotion only when evidence warrants it.

### M4 acceptance

Evaluation must use prospective work on real projects, not only fixtures. A
successful collaborator:

- advances an active question across separate sessions;
- distinguishes a useful next test from a generic suggestion;
- records predictions before outcomes, preventing hindsight rewriting;
- changes its view when evidence or the researcher corrects it;
- keeps disagreements and uncertainty visible;
- grounds every reusable claim, Skill, and Insight in inspectable evidence.

## Deferred infrastructure

Multi-user permissions, remote synchronization, private-memory federation, and
custom merge protocols are not M4. Existing Git collaboration plus author and
reviewer provenance should be used first. Add stronger team infrastructure
only after a concrete collaboration failure cannot be solved by those tools.
