# Research-memory policy

This policy governs how a research agent uses the project's recorded memory.
It states WHAT to do. The mechanics of each action are described in the
condition-specific adapter, never here. This file is byte-identical in every
condition of every scored run.

## When to read memory

- At the start of every research session or resumption, before proposing any
  plan, read the recorded project state.
- Before making a claim, citing a result, or choosing a next step that the
  memory could constrain, open the underlying records and read the original
  evidence, not just a summary line.
- When the recorded state reports missing or damaged memory, say so explicitly
  and proceed cautiously; never invent what the memory should have contained.
- Do not infer research state from file names, directory layout, timestamps,
  or the most recently modified file. Memory is what the records say.

## What is a durable event

Record only what must survive the current conversation:

- a completed result, with its evidence boundary and limitations;
- a failure that occurred, and whether it is resolved or still open;
- a human decision, including corrections and convention changes;
- a source assessment (what a source is, where its claims end);
- a reproducible run and its outputs;
- a consequential code change;
- a session closeout: what was accomplished, what is unresolved, and the
  concrete next action.

Do not record:

- conversational filler and chit-chat;
- speculative ideas not yet developed — they belong in the conversation, not
  the memory;
- scratch work, transient states, or duplicate retries of the same logical
  event.

## Classification discipline

- Choose one record type per event. A single catch-all "we did things"
  record covering heterogeneous events is a type error, not a recall.
- A result is a recorded project outcome with its evidence boundary, not a
  claim of universal truth. Distinguish what was observed from what is
  interpreted.
- When one record replaces an older one, the newer record names the older one
  as replaced. Never rewrite or delete the older record; history stays
  append-only and visible.

## Correction and contradiction

- When the researcher corrects you, take the correction seriously: restate
  the prior reasoning, weigh the objection, and change the conclusion if it
  is warranted. If the course changes, record it.
- A correction that supersedes an earlier statement must leave both visible:
  the earlier record stays, the correcting record points at it.
- Do not label competing hypotheses or claims in different regimes as
  contradictions. A contradiction requires both sides to be expected to hold
  at the same time and to be logically incompatible, with evidence for each.

## Closeout discipline

- Before a session ends, verify that durable events of the session are
  recorded, unresolved failures are honestly open, evidence is reachable, and
  the next action is concrete.
- Record the closeout as its own typed event. The next session must be able
  to resume from it: current goal, active route, next action, and any open
  corrections.

## Honesty

- Treat recorded memory as an auditable record, not as truth. Cite the exact
  record and evidence location when you rely on it.
- If you cannot verify a pinned reference, disclose that it is stale or
  missing instead of assuming it.
- If your proposal rests on a memory read, say which record it rests on and
  where in that record the evidence lives.
