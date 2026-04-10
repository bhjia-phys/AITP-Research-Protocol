# L2 compiler protocol

Status: draft

This file defines how AITP may build compiled `L2` helper surfaces without
turning those helper surfaces into a second source of truth.

## 1. Why this exists

`L2` should become easier to consult, audit, and reuse.

But that does not mean:

- flattening canonical units into one giant wiki page,
- letting scratch notes masquerade as trusted knowledge,
- or hardcoding high-level knowledge semantics into another oversized Python
  service file.

This protocol exists to keep those boundaries explicit before implementation
spreads.

## 2. Core stance

AITP should distinguish three classes of `L2` surface:

1. canonical `L2`
   - authoritative promoted units and their lightweight relation/index layers
2. compiled `L2`
   - derived helper surfaces built from canonical `L2`
3. staging `L2`
   - provisional or scratch material that is not yet trusted canonical memory

Short form:

- canonical is authoritative
- compiled is derived
- staging is provisional

## 3. Authoritative canonical `L2`

Canonical `L2` remains the source of truth for reusable promoted knowledge.

Primary canonical surfaces include:

- `canonical/index.jsonl`
- `canonical/edges.jsonl`
- typed canonical unit files under the family directories
- backend bridge metadata
- promotion and provenance records that justify why a unit is in `L2`

Compiled views may summarize these surfaces.
They may not outrank them.

## 4. Compiled `L2`

Compiled `L2` is allowed when it improves:

- consultation,
- cross-topic navigation,
- hygiene review,
- and operator-readable reuse.

Compiled surfaces must be:

- fully derived from canonical inputs,
- reproducible,
- inspectable from disk,
- and safe to regenerate.

They should live under:

- `research/knowledge-hub/canonical/compiled/`

Typical shape:

- `*.json` for machine-readable compiled output
- `*.md` for human-readable compiled render

Compiled surfaces may contain:

- grouped entry points,
- relation summaries,
- warning clusters,
- bridge clusters,
- consultation-oriented maps,
- hygiene summaries.

They may not:

- invent new canonical units,
- silently rewrite unit meaning,
- bypass promotion rules,
- or replace explicit unit-level provenance.

## 5. Staging `L2`

Staging is the explicit quarantine zone for provisional or scratch material
that might later inform `L2` but is not yet trusted `L2`.

Staging should live under:

- `research/knowledge-hub/canonical/staging/`

Staging content is:

- non-authoritative,
- not eligible to masquerade as canonical memory,
- and not a valid substitute for promoted units during final writeback.

## 6. First bounded compiler target

The first bounded compiler target should be a workspace-scoped consultation and
reuse map:

- `research/knowledge-hub/canonical/compiled/workspace_memory_map.json`
- `research/knowledge-hub/canonical/compiled/workspace_memory_map.md`

Its job is modest:

- show the major reusable entry points in canonical `L2`
- cluster units by family and relation
- surface bridges, warnings, workflows, and validation patterns in one
  inspectable derived map
- give consultation a bounded read aid without pretending to replace unit refs

Inputs for this first compiler target should come only from canonical sources
such as:

- `canonical/index.jsonl`
- `canonical/edges.jsonl`
- canonical unit files
- `canonical/retrieval_profiles.json`

The first target should not try to compile all runtime state or all raw notes
into one mega-view.

## 7. Consultation rule

`L2` consultation may reference compiled surfaces as supporting derived reads
when they genuinely improve explainability.

But consultation must still keep these distinctions explicit:

- what canonical units were returned,
- what compiled helper surface was shown,
- what was actually applied.

Compiled surfaces help the human or agent navigate.
They do not replace canonical unit refs as the durable memory object.

## 8. Promotion rule

Compiled surfaces are downstream of promotion.

They may summarize promoted material.
They may not manufacture canonical status.

If a useful structure only exists inside a compiled surface, then the system
still has more work to do before that structure counts as canonical reusable
knowledge.

## 9. Python boundary

Python remains allowed and necessary for:

- loading canonical artifacts,
- validating inputs and outputs,
- materializing compiled surfaces,
- indexing,
- audit and hygiene passes,
- and deterministic regeneration.

Python should not keep absorbing:

- high-level research reasoning,
- mutable knowledge semantics,
- large policy tables that belong in JSON or protocol docs,
- or render-heavy output semantics that belong in templates or declarative
  config.

Short form:

- Python should stay in the kernel role
- compiler semantics should prefer docs, schemas, JSON policy, and templates
  over new giant branching service code

## 10. Anti-patterns

Do not:

- treat compiled markdown as canonical truth,
- mix staging content into compiled surfaces without marking it clearly,
- use compiled surfaces to bypass `L4 -> L2` promotion,
- turn the compiler into a hidden research-reasoning engine,
- or centralize all future compiler logic inside one giant service hotspot.

## 11. One-line doctrine

`L2` compiler outputs should make trusted knowledge easier to use without
changing what trusted knowledge is.
