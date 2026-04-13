# Plan: 170-01 — Run one fresh public-front-door positive promotion proof into canonical L2

**Phase:** 170
**Axis:** Axis 2 (inter-layer connection) + Axis 4 (human evidence and read-path trust)
**Requirements:** REQ-E2E-01, REQ-E2E-02

## Goal

Prove that the repaired promotion pipeline can carry one real bounded topic
from the public AITP front door through bounded validation into canonical `L2`,
with durable runtime/read-path receipts showing that the promoted unit actually
landed.

## Context

`v1.95` closed the engineering gaps that blocked promotion:

1. `negative_result` and runtime proof packet schemas now have canonical and
   package-level contract surfaces
2. promotion gates and auto-promotion now expose runtime schema context
3. the front door now has bounded `status`, zero-config `hello`, and
   post-bootstrap `next_action_hint`

What is still unproven is the end-to-end route on a fresh real topic. The
earlier Jones public-entry closure run in `165.6` proved honest public entry
and an explicit return-to-`L0`, but it did **not** prove a promoted `L2`
receipt. This phase should turn the repaired path into evidence, not another
latent capability layer.

## Steps

### Step 1: Define the proof topic and exact positive target

**Artifacts:**
- `.planning/phases/170-positive-promotion-proof-lane/RUNBOOK.md`
- `.planning/phases/170-positive-promotion-proof-lane/TARGET.md`

Select one fresh real topic slug and one bounded positive target that is
realistic with the current shipped stack.

Preferred rule:
- keep using the Jones finite-dimensional backbone family because it already
  has known front-door evidence and bounded source-intake history
- choose a target that can honestly reach canonical `L2` with the current
  stack, for example a bounded source-backed `concept`, `workflow`, or
  `physical_picture`, rather than forcing a whole-topic theorem closure if that
  is not yet mechanically stable

The runbook must record:
- topic title
- fresh topic slug
- public front-door command
- bounded loop request
- promotion command sequence
- expected canonical unit family and receipt locations

### Step 2: Add one dedicated positive-promotion acceptance lane

**Files:**
- `research/knowledge-hub/runtime/scripts/run_positive_promotion_acceptance.py`
- `research/knowledge-hub/tests/test_runtime_scripts.py`
- `research/knowledge-hub/tests/test_aitp_cli_e2e.py`

Create one acceptance lane that performs the positive proof on an isolated
temporary kernel or run fixture:
- bootstrap from the public CLI/front door
- advance through the bounded route needed to produce one promotable candidate
- execute promotion into a backend root with a durable receipt
- verify the canonical unit exists and the route surfaces expose the same
  promotion receipt

The test does not need to prove broad scientific completion. It must prove that
one real bounded route can now cross the repaired `L4 -> L2` boundary.

### Step 3: Surface the receipt on runtime/read paths

**Files:**
- `research/knowledge-hub/knowledge_hub/aitp_service.py`
- `research/knowledge-hub/knowledge_hub/topic_shell_support.py`
- `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`
- related tests

If the positive lane reveals missing read-path parity, patch the read surfaces
so the operator can see the same receipt in:
- `status`
- runtime protocol note
- topic dashboard
- replay or other current read-path surfaces

This step is only for receipt visibility and parity. Do not widen into new
promotion policy or unrelated UX redesign.

### Step 4: Leave durable evidence for milestone closure

**Artifacts:**
- `.planning/phases/170-positive-promotion-proof-lane/SUMMARY.md`
- `.planning/phases/170-positive-promotion-proof-lane/evidence/...`

Record:
- exact commands run
- receipt paths
- promoted unit id and family
- what remained manual, if anything
- whether the route is strong enough to serve as the baseline positive proof
  for `v1.96`

## Must Do

- use a **fresh** public-front-door topic slug
- keep the proof bounded; prove one real promoted unit, not whole-topic
  closure
- verify the canonical backend receipt and runtime/read-path receipt parity
- keep all evidence durable in files, not only in chat

## Must Not Do

- do not bypass the public front door with hidden seed state
- do not redefine what counts as canonical `L2` promotion
- do not force a theorem-grade proof lane if a smaller real bounded positive
  unit is the honest first closure target
- do not mix the negative-result proof into this phase

## Evidence

- [ ] one fresh topic slug enters through the public front door
- [ ] one bounded candidate promotes into canonical `L2`
- [ ] the backend receipt path is durable and replayable
- [ ] `status` and runtime/read-path surfaces expose the same promotion result
- [ ] one dedicated acceptance lane proves the route mechanically
