# Research Execution Guardrails

This file captures the strongest research-flow lessons AITP should absorb from
`get-physics-done` without replacing the `L0 -> L1 -> L3 -> L4 -> L2` ontology.

AITP should stay layer-first.
It should also stop treating "workflow discipline" as an optional style choice.

## 1. Core rule

Non-trivial research work should be governed by:

- an explicit research contract,
- bounded action packets,
- explicit verification hooks,
- forbidden proxy-success signals,
- durable gap-recovery routes.

The point is not project-management theater.
The point is to prevent silent scope drift, fake completion, and polished
research-sounding prose from being mistaken for actual progress.

## 2. Topic-level research contract

Every non-trivial topic should have an active research-question contract whose
content is rich enough to survive a new agent session.

At minimum, it should make the following explicit:

- scope,
- assumptions,
- non-goals,
- context intake,
- formalism and notation lock,
- observables,
- target claims,
- intended deliverables,
- acceptance tests,
- forbidden proxies,
- uncertainty markers.

If these are missing, the topic is easy to mutate accidentally.

## 3. Bounded action packet discipline

Every selected next action should either declare or point to:

- the immediate objective,
- the exact upstream artifacts it depends on,
- the exact deliverables it is expected to emit,
- the checks that decide whether the action succeeded,
- the blockers or escalation conditions that stop the action from over-claiming,
- the highest justified destination layer for the result.

AITP already has queue and decision surfaces.
Those surfaces should be read as bounded action packets, not as loose TODO
lists.

## 4. Micro-gates during work

AITP should not wait until the very end of a topic to detect obvious failures.

For derivation-heavy work, keep checking:

- notation consistency,
- sign and factor consistency,
- dimensional consistency,
- domain and regime assumptions,
- order-of-limits assumptions,
- cancellations and dropped terms,
- limiting cases and special cases,
- agreement with earlier declared equations.

Also keep three status distinctions explicit:

- the L3 derivation record is AI-authored provisional reasoning, not truth,
- cited dependencies and source anchors may still force a return to L0,
- comparison against known derivations or methods in L2 is part of the logic
  check, not optional polish.
- a derivation-heavy candidate is not promotion-ready until that L2
  comparison is persisted as a durable comparison receipt rather than implied
  in chat or memory.

For numerical or execution-backed work, keep checking:

- input fidelity,
- unit and convention consistency,
- convergence behavior,
- comparison against declared baselines,
- whether the executed observable is really the observable the topic asked for.

## 5. Verification evidence rule

A validated computational or execution-backed claim should not exist without at
least one executed artifact showing what actually ran and what came back.

If execution evidence is absent, confidence should be capped explicitly rather
than implied away.

For proof-heavy work, completion should also stay capped when:

- cited dependencies remain unresolved,
- proof fragments are still missing,
- notation bridges are still ambiguous,
- family equivalence is still asserted only heuristically.
- the recorded derivation body is only a summary and not a sufficiently
  detailed reasoning spine.
- the theorem/proof packet still lacks a derivation graph or a ready
  `formal_theory_review.json`.

## 6. Forbidden proxies

The following do not count as scientific success by themselves:

- polished explanatory prose,
- a plausible-looking derivation with unchecked signs or factors,
- agreement with the model's memory,
- one nice special case when the general claim is broader,
- the mere existence of a candidate note,
- the fact that a claim sounds standard or well known,
- a queue row being marked done without the declared deliverables on disk.

These should be written into the active research-question or validation
contracts when possible.

## 7. Gap recovery is first-class

When a topic hits a cited-literature dependency, a notation mismatch, a proof
gap, or a regime conflict, AITP should not smooth it over conversationally.

It should:

1. emit the gap explicitly,
2. decide whether the gap blocks current completion,
3. spawn an `L0` follow-up route when a real source recovery is needed,
4. require a return packet before reintegration.

If an L2 comparison receipt says the route only partially matches, reveals a
normalization mismatch, or exposes a missing cited step, that is a real gap
signal. The correct move is to keep the limitation visible, narrow the claim,
or return to `L0`; not to smooth the issue away in polished prose.

That is why `GAP_RECOVERY_PROTOCOL.md` and follow-up subtopics are part of the
kernel rather than a local convention.

## 8. Auto-promotion remains gated

These guardrails do not weaken AITP's promotion rules.

If anything, they make auto-promotion more honest:

- coverage is not enough,
- consensus is not enough,
- regression is not optional,
- split honesty and gap honesty remain mandatory,
- missing execution evidence should block claims that depend on execution,
- missing derivation detail, missing L2 comparison receipts, or missing
  theorem/proof theory-packet surfaces should block derivation-heavy
  promotions.

## 9. Runtime exposure rule

The runtime bundle, agent brief, and operator console should expose these
guardrails in a visible way.

Agents should not have to guess whether the active topic is allowed to:

- drift its scope,
- substitute proxy evidence for real evidence,
- declare completion while gaps are still open,
- promote notes that never satisfied their declared checks.

That visibility requirement is part of AITP's protocol surface, not a hidden
implementation preference.
