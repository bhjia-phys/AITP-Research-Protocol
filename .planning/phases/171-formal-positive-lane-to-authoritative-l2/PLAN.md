# Plan: 171-01 — Run one fresh formal positive lane from public bootstrap to authoritative canonical L2

**Phase:** 171
**Axis:** Axis 2 (inter-layer connection) + Axis 4 (human evidence and read-path trust)
**Requirements:** REQ-L2POS-01, REQ-L2POS-02

## Goal

Take the most mature positive real-topic lane in the repository —
von-Neumann-algebra / Jones-style formal derivation — and prove that a **fresh
public-front-door topic** can travel all the way into one authoritative
canonical `L2` unit, with the same landing visible on runtime surfaces and on
`consult-l2`.

This phase is the first real positive closure target after `v1.96`, which only
proved three-mode bootstrap and one honest negative-result route.

## Context

The current repository already contains two strong bounded formal-closure
acceptance assets:

1. `research/knowledge-hub/runtime/scripts/run_jones_chapter4_finite_product_formal_closure_acceptance.py`
2. `research/knowledge-hub/runtime/scripts/run_witten_topological_phases_formal_closure_acceptance.py`

Those scripts prove that promotion machinery, theory packets, and backend
writeback can work for formal topics. What they do **not** yet prove for the
current milestone is:

- a fresh public-front-door bootstrap on a new topic slug
- a bounded positive route that begins from operator-facing natural language
  instead of an already-prepared topic family
- runtime/read-path parity including `consult-l2` after the authoritative writeback

The best bounded route is therefore:

- reuse the existing Jones formal-closure mechanics as the backend baseline
- start from a fresh public-front-door topic in the same topic family
- promote one bounded reusable unit, not a whole-book closure
- finish by checking runtime/read-path and `consult-l2` parity

## Planned Route

### Step 1: Lock the fresh formal topic and promoted unit target

**Artifacts to write during execution:**
- `.planning/phases/171-formal-positive-lane-to-authoritative-l2/RUNBOOK.md`
- `.planning/phases/171-formal-positive-lane-to-authoritative-l2/TARGET.md`

Choose one fresh public-front-door topic slug in the Jones / von Neumann family
that is close enough to the existing formal acceptance scripts to avoid fake
novelty, but still honest as a fresh route.

Preferred target:
- topic family: finite-dimensional von Neumann algebras / Type I factor closure
- promoted unit family: `theorem`, `proof_fragment`, or another already-valid
  canonical formal unit family supported by the current TPKN bridge

The target document must pin down:
- fresh topic slug
- exact public front-door question
- exact bounded positive claim
- candidate id and expected target unit id
- expected backend root and receipt locations

### Step 2: Add one failing positive-L2 acceptance lane for a fresh formal topic

**Files:**
- `research/knowledge-hub/runtime/scripts/run_formal_positive_l2_acceptance.py`
- `research/knowledge-hub/tests/test_runtime_scripts.py`
- `research/knowledge-hub/tests/test_l2_backend_contracts.py`

Add a dedicated acceptance script that:

- bootstraps a fresh formal topic through `AITPService().new_topic()`
- registers the bounded source material needed for the Jones-style route
- creates or reuses the bounded candidate packet honestly
- runs the promotion path into a TPKN-style backend
- verifies the authoritative canonical `L2` unit exists
- verifies runtime/read-path parity after that landing

This step must start with a **failing** targeted test entry in
`test_runtime_scripts.py` or another existing targeted test surface so the new
acceptance script is proven necessary before implementation.

### Step 3: Reuse the Jones formal-closure machinery instead of inventing a new route

**Files likely touched:**
- `research/knowledge-hub/runtime/scripts/run_formal_positive_l2_acceptance.py`
- `research/knowledge-hub/runtime/scripts/run_jones_chapter4_finite_product_formal_closure_acceptance.py`
- related helper modules only if a real gap appears

Prefer composition over rewrite:

- extract only the reusable setup or promotion helpers that the fresh-topic
  acceptance lane needs
- keep the existing Jones acceptance script passing
- avoid widening schema or backend policy unless the fresh public-front-door
  route reveals a real missing contract

The phase succeeds faster if it proves:
- fresh topic bootstrap
- bounded source registration
- bounded candidate shaping
- authoritative promotion

It should **not** reopen broader formal-theory automation or Lean workflow
design unless a concrete blocker forces that.

### Step 4: Prove read-path and consultation parity after promotion

**Files likely touched:**
- `research/knowledge-hub/knowledge_hub/aitp_service.py`
- `research/knowledge-hub/knowledge_hub/l2_consultation_support.py`
- `research/knowledge-hub/knowledge_hub/l2_compiler.py`
- related tests

After the positive unit lands, verify the same authoritative outcome is visible in:

- promotion gate state
- promotion decision receipt
- compiled workspace knowledge report
- compiled workspace memory map or graph report
- `consult-l2` using a natural-language query about the promoted result

If parity is missing, patch the smallest read surface necessary. Do not widen
into a general retrieval redesign in this phase.

### Step 5: Leave durable evidence for phase closure

**Artifacts to write during execution:**
- `.planning/phases/171-formal-positive-lane-to-authoritative-l2/SUMMARY.md`
- `.planning/phases/171-formal-positive-lane-to-authoritative-l2/evidence/`

Execution evidence must record:

- exact front-door command or API call
- source registration and candidate paths
- promotion gate and decision paths
- target unit id and target unit path
- `consult-l2` query text and retrieved authoritative row
- what remained manual, if anything
- whether this route is strong enough to serve as the baseline positive-L2 proof

## Must Do

- start from a **fresh public-front-door topic**, not the old `jones-von-neumann-algebras` topic
- land one **authoritative** positive unit in canonical `L2`
- include one natural-language `consult-l2` proof after promotion
- keep the route bounded to one honest reusable result
- preserve the already-proven negative-result `contradiction_watch` path

## Must Not Do

- do not claim whole-topic completion when only one bounded positive unit landed
- do not silently depend on hidden pre-seeded runtime state
- do not rewrite the entire formal-closure stack when the existing Jones route
  already proves most backend mechanics
- do not reopen the three-mode widening work in this phase; that belongs after
  the first trustworthy positive L2 landing

## Evidence

- [ ] one fresh `formal_derivation` topic enters through the public front door
- [ ] one bounded positive candidate lands as an authoritative canonical `L2` unit
- [ ] backend writeback receipt is durable and replayable
- [ ] promotion gate, compiled L2, and `consult-l2` agree on the same promoted unit
- [ ] one dedicated acceptance lane proves the route mechanically
