# Plan: 174-01 - Run one real natural-language dialogue proof for the formal-theory baseline

**Phase:** 174
**Axis:** Axis 2 (inter-layer connection) + Axis 5 (agent-facing steering)
**Requirements:** REQ-E2E-01

## Goal

Prove that the public AITP front door can steer the already-closed bounded
formal-theory baseline through one fresh natural-language dialogue, while
keeping the route tied to the authoritative Jones finite-product theorem.

## Planned Route

### Step 1: Lock the bounded formal dialogue target

**Artifacts to write during execution:**
- `.planning/phases/174-formal-theory-real-topic-natural-language-dialogue-proof/TARGET.md`
- `.planning/phases/174-formal-theory-real-topic-natural-language-dialogue-proof/RUNBOOK.md`

Pin down:

- fresh topic slug
- fresh natural-language topic / question / human request
- authoritative theorem id
- canonical mirror path
- preserved bounded non-claim against whole-book formalization

### Step 2: Add the isolated formal dialogue acceptance lane

**Files:**
- `research/knowledge-hub/runtime/scripts/run_formal_real_topic_dialogue_acceptance.py`
- `research/knowledge-hub/tests/test_runtime_scripts.py`

The route should:

- reuse the shipped bounded formal positive-L2 acceptance on a fresh work root
- pass through a fresh natural-language formal topic, question, and human
  request
- verify `interaction_state.json` and `research_question.contract.json`
  preserve the dialogue
- verify the canonical theorem mirror exists
- verify `consult-l2` still returns the bounded formal theorem

### Step 3: Leave durable evidence for phase closure

**Artifacts to write during execution:**
- `.planning/phases/174-formal-theory-real-topic-natural-language-dialogue-proof/SUMMARY.md`
- `.planning/phases/174-formal-theory-real-topic-natural-language-dialogue-proof/evidence/`

## Acceptance Criteria

- [x] one real natural-language dialogue run proves the formal-theory baseline
      can be entered through the public front door
- [x] runtime steering artifacts preserve the fresh formal-theory request
- [x] the route stays aligned with the bounded positive authoritative-L2 theorem
- [x] one dedicated acceptance lane proves the route mechanically
