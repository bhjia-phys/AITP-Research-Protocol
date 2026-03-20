# Proof Obligation Protocol

This file defines the public AITP contract for proof-heavy and derivation-heavy
work.

It is not a promise that every source already contains a complete proof.
It is the rule for how AITP must represent that situation honestly and
durably.

## 1. Why this exists

Theoretical-physics writeback fails when a theorem card says "proved" but the
actual derivation still lives only in agent memory.

This protocol exists so AITP can make four things explicit:

- what is being proved,
- which logical moves are already grounded,
- which steps are still missing or externally cited,
- what evidence is sufficient for promotion or reuse.

## 2. When it is mandatory

Use this protocol whenever a topic contains one or more of the following:

- a theorem-like or equivalence-like candidate that claims proof-level reuse,
- a derivation that spans multiple nontrivial intermediate formulas,
- a regression oracle that requires exact proof reconstruction,
- a coverage or consensus review for a theory-formal `L2_auto` route.

Do not collapse these situations into a summary-only note.

## 3. Core objects

AITP proof-grade work should expose, or be mappable to, the following durable
objects:

1. `proof_obligation`
   - one bounded claim or subclaim that must be discharged,
   - explicit prerequisites,
   - exact source anchors and formulas,
   - clear success and failure conditions.
2. `proof_state`
   - the current ledger for a whole theorem or derivation family,
   - which obligations are complete, partial, blocked, or deferred.
3. `equation_context`
   - the local role of an equation label or displayed formula,
   - notation bindings, regime, and why the equation matters in the proof.
4. `dependency_graph_snapshot`
   - the ordered prerequisite graph for the active theorem family,
   - enough structure to recover the derivation spine without hidden memory.

These objects may live in an external `L2` backend, but their semantics are
governed here.

## 4. Minimal proof obligation content

Every proof obligation should state:

- the bounded claim being discharged,
- the prerequisite units or obligations,
- the equations or definitions that must be opened,
- the required logical move,
- the expected output statement,
- the honest status:
  - complete,
  - partial,
  - blocked,
  - source-cited-only,
  - deferred.

If a source skips the proof and cites another paper, the correct status is not
"complete."
It is `source-cited-only` until the cited route is recovered or the limitation
is kept explicit.

## 5. Promotion rule

No theorem-like object should be treated as proof-grade reusable knowledge only
because:

- the source is famous,
- the result is standard,
- or an agent can restate the conclusion fluently.

Promotion-grade proof work requires:

- explicit obligation coverage,
- explicit dependency structure,
- equation-level grounding when the source provides equations,
- honest unresolved obligations or cited-source gaps when the source does not.

## 6. Runtime trigger handshake

The runtime progressive-disclosure bundle names this surface through:

- `proof_completion_review`

When that trigger fires, the next agent must open:

- `PROOF_OBLIGATION_PROTOCOL.md`,
- the active theory-packet coverage artifacts,
- the dependency graph or structure map for the candidate under review,
- any local proof-obligation objects emitted by the target backend.

This trigger is about proof completeness and proof honesty.
It does not itself authorize promotion.

## 7. Script boundary

Scripts may:

- materialize obligation ledgers,
- render dependency snapshots,
- validate required fields,
- expose status summaries.

Scripts may not decide:

- whether a missing intermediate derivation is harmless,
- whether an externally cited proof can be treated as locally known,
- whether a theorem family is truly reusable for downstream derivation.

Those are research judgments governed by this contract plus the relevant
coverage, consultation, validation, and regression surfaces.
