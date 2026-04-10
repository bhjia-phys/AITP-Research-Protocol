# Theoretical Physics Backend Pairing

This note defines the supported paired-backend configuration for formal-theory
knowledge downstream of AITP.

For the stronger role and alignment contract, also read:

- `THEORETICAL_PHYSICS_PAIRED_BACKEND_CONTRACT.md`

## Backend pair

- `backend:theoretical-physics-brain`
  - root example: `obsidian-markdown/01 Theoretical Physics`
  - role: operator-facing, human-readable implementation
- `backend:theoretical-physics-knowledge-network`
  - root example: standalone `theoretical-physics-knowledge-network` clone
  - role: typed and structured companion implementation

## Intended semantics

These two backends are treated as paired downstream implementations of the same
theoretical-physics knowledge network.

This means:

- neither backend is automatically more authoritative because of path, file
  format, or local tooling;
- both are governed by the same AITP promotion gates;
- both are post-promotion storage targets, not scratch-space substitutes;
- drift between the pair is backend debt that must be surfaced explicitly.
- the human-readable backend is operator-primary;
- the typed backend is machine-primary;
- authority remains with the shared promotion and alignment contract rather
  than with one serialization format.

## Alignment requirements

When a promotion packet lands in one or both backends, preserve alignment for:

- semantic identity of the promoted object;
- source anchors and citation scope;
- assumptions and regime limits;
- reusable versus unresolved boundaries;
- theorem/proof-gap versus warning/caveat status.

If one backend currently cannot express the full structure of the other, record
that reduction honestly rather than silently broadening or weakening the claim.

## Relation to `L2` trust surfaces

The paired backend split is not the same thing as:

- canonical `L2`
- compiled `L2`
- staging `L2`

Those three names describe AITP trust posture inside the `L2` governance
plane.

The paired backends instead describe downstream knowledge realizations:

- one human-readable realization
- one typed realization

So:

- the human-readable backend is not merely a compiled markdown helper;
- the typed backend is not globally authoritative just because it is typed;
- compiled helper surfaces may summarize promoted knowledge, but they do not
  replace either paired realization.

## What the pair is not

The pair is not:

- a license to bypass `L1 -> L2`, `L3 -> L4 -> L2`, or `L3 -> L4_auto -> L2_auto` gates;
- a justification for treating folder layout as ontology;
- a reason to dump runtime notes, chat transcripts, or unresolved research debt
  into long-term memory.

## Practical consequence

In a clone that uses this pair, `01 Theoretical Physics` can be the real
human-maintained knowledge surface while TPKN provides stronger typed retrieval,
graph checks, and projection rebuilding.

AITP should treat that as one downstream L2 network with two governed storage
realizations.
