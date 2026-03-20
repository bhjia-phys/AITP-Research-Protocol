# Gap Recovery Protocol

This file defines the public AITP contract for honest gap handling and
reactivation.

The point is not to eliminate gaps by rhetoric.
The point is to route them durably so future work can actually resolve them.

## 1. Why this exists

A proof-grade theory workflow always encounters gaps:

- missing derivations,
- cited-but-uningested prerequisites,
- notation the current topic never defined,
- contradictions between nearby sources,
- branches that are too broad to promote as one unit.

Without a recovery protocol those gaps disappear into commentary and the system
overstates what it knows.

## 2. Gap kinds

At minimum AITP should distinguish:

- missing proof,
- missing background,
- missing bridge,
- missing notation,
- source omitted or source cited only,
- contradiction unresolved,
- topic too wide or mixed for one canonical unit.

Projects may refine this list, but they should not collapse materially
different failure modes into one generic TODO bucket.

## 3. Required recovery outcomes

Every durable gap should route to one or more of:

1. local refinement
   - split a wide note into smaller proof fragments or derivation steps.
2. `L0` follow-up
   - ingest cited literature or a standard reference from source search.
3. deferred buffer
   - park the fragment honestly until future sources justify reactivation.
4. contradiction record
   - preserve the disagreement instead of fusing prematurely.
5. regression writeback
   - ensure the gap reappears in the topic regression surface.

## 4. Re-entry rule

Gap handling is only useful if re-entry is explicit.

A gap artifact should therefore record:

- what blocked continuation,
- which units or candidates are affected,
- what source type is expected for recovery,
- which objects should be revisited after recovery.

When new cited-literature evidence arrives, the correct route is:

- `L0 -> L1 -> L3 -> L4 -> L2`

not a direct silent patch to a canonical theorem card.

## 5. Wide-topic rule

If a candidate mixes several distinct claims, definitions, caveats, or cited
subproofs, do not force it into `L2`.

Instead:

- split the promotable part,
- park unresolved fragments,
- keep lineage explicit.

Wide-topic honesty is part of scientific correctness, not merely repository
tidiness.

## 6. Runtime trigger handshake

Gap recovery becomes mandatory when the runtime bundle exposes any of:

- `contradiction_detected`,
- `capability_gap_blocker`,
- `proof_completion_review`

and the active artifacts show unresolved prerequisites or cited-source
dependencies.

When that happens the next agent must open:

- `GAP_RECOVERY_PROTOCOL.md`,
- the relevant regression log,
- the active gap, deferred-buffer, or follow-up artifacts,
- the impacted proof-state or candidate ledger.

## 7. Script boundary

Scripts may:

- persist gap manifests,
- append regression writeback,
- reopen deferred entries when declared conditions match,
- scaffold follow-up source tasks.

Scripts may not decide:

- that a cited paper is unnecessary,
- that a contradiction is superficial,
- or that a wide topic is actually coherent enough for promotion.

Those decisions remain protocol-governed research work.
