---
name: using-aitp
description: "Executes structured theoretical physics research using the AITP (AI Theoretical Physicist) protocol. Performs physics derivations, analyzes research papers, validates physical models, manages layered research state (L0-L4), and enforces evidence boundaries. Use when the user asks about quantum field theory, Lagrangian mechanics, physics derivation, research paper analysis, continue a physics topic, formalization, validation planning, or any theoretical-physics research question."
---

# Using AITP

Manages structured theoretical-physics research inside the AITP protocol. Routes user requests through environment check, clarification, and layered execution (L0 source tracing, L1 provisional analysis, L3 candidate outputs, L4 validation) before promoting trusted results to L2 long-term memory.

## Workflow

### 1. Environment gate (always first)

Check for an AITP-enabled workspace. If native bootstrap is active, proceed. Otherwise:

```bash
aitp session-start "<research task description>"
```

If the environment check fails, tell the user to run `aitp session-start` or install AITP first.

### 2. Clarify the research question

Before executing, tighten the research contract if scope, assumptions, or target claims are unclear.

- Ask at most 3 rounds of 1-3 questions each, prioritizing the biggest ambiguity first (scope, assumptions, target claims, validation route).
- If the user says "just go", "skip clarification", or equivalent, proceed and mark missing fields as deferred.
- If the user references an existing topic ("continue this topic", "current topic", "继续这个topic"), resolve it from durable topic memory or ask for the topic slug.

### 3. Route the request

| Situation | Action |
|-----------|--------|
| Existing topic continuation | Load `topic_state.json`, resume from last checkpoint |
| New research question | Extract title, materialize topic shell, create `research_question.contract.json` with scope + assumptions + target claims |
| Direction or scope change | Update `innovation_direction.md` and `control_note.md` before continuing |
| Paper review or source work | Enter L0 source acquisition, produce source maps and traceable references |
| Derivation or formalization | Enter L1 provisional analysis, produce derivation sketches with explicit assumption lists |
| Validation or trust audit | Enter L4, run baseline checks and produce audit artifacts |

### 4. Execute through layers

Research flows: **L0** (source traces) -> **L1** (provisional analysis) -> **L3** (candidate outputs) -> **L4** (validation) -> **L2** (promoted memory, requires human approval).

Each layer produces durable artifacts. Never skip L4 validation to promote directly to L2.

**Key artifacts to preserve across sessions:**
- `topic_state.json` -- current topic checkpoint and layer progress
- `research_question.contract.json` -- scope, assumptions, target claims
- `control_note.md` -- human steering decisions
- `operator_console.md` -- session audit trail

### 5. Error recovery

- If topic state is missing or corrupted, reconstruct from the most recent `control_note.md` and `operator_console.md`.
- If a derivation fails validation at L4, document the failure visibly (do not hide it), then return to L1 with updated assumptions.
- If the user changes direction mid-execution, pause, update steering artifacts, then re-route.

## Conversation style

- Never expose protocol jargon (e.g., "decision_point", "L2 consultation", "load profile"). Speak as a research collaborator.
- Ask one question at a time unless a single answer would still leave the route ambiguous.
- If the user already gave enough direction, skip clarification and execute.
- When presenting options, explain routes and tradeoffs in plain language.

## Exception

If the task is AITP repo maintenance (not research execution), work directly on the codebase while preserving the layer model and promotion gates.
