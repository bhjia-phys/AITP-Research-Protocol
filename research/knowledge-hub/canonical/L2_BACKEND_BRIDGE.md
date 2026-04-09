# L2 internal backend bridge

This file defines a thin internal bridge inside `L2`.

It is not a new epistemic layer.
It is the registration and adapter surface that lets `L2` consult durable external knowledge backends without pretending that those backends are already canonical truth.

## 1. Why this exists

AITP needs a way to reuse:
- human-maintained note libraries,
- software repositories,
- numerical workflow docs,
- local result stores,

without collapsing all of them directly into `canonical/`.

The bridge exists so that:
- human knowledge bases can feed `L2`,
- software knowledge bases can feed `L2`,
- `L2` stays schema-first and auditable,
- later software integrations do not require redesigning the whole layer model.

## 2. Current role

The bridge sits between:
- external backend stores,
- concrete `L0` source registrations,
- `L2` canonical objects.

A backend card says:
- what the backend is,
- where it lives,
- what kind of knowledge it contains,
- which canonical object families it is expected to seed,
- what registration and promotion rules apply.
- and, when a paired downstream backend exists, which maintenance contract
  governs drift audit, backend debt, and rebuild.

## 3. Hard rules

1. Backend presence is not canonical acceptance.
2. A backend root must not be treated as a live `L2` store by path alone.
3. Concrete artifacts from a backend should usually be registered into `L0` before strong downstream reuse.
4. Promotion into `L2` still follows normal `L1 -> L2` or `L3 -> L4 -> L2` rules.
5. `L2` objects may cite backend cards through `provenance.backend_refs`, but backend refs do not replace concrete source ids, `L3` runs, or `L4` checks.

## 4. Intended backend families

- human note library
  - example: a local Markdown theory vault
- software repo
  - example: a numerical or formal code repository
- local docs repo
- local result store

## 5. Public-kernel stance

This public repository ships the backend protocol and registry surface, not a
claim that any machine-specific backend is already integrated.

A concrete clone may later register:

- a human-note backend for pure formal theory or derivation reservoirs
- a software backend for methods, workflows, validation patterns, and execution contracts

## 6. Recommended lifecycle

1. Register the backend in `canonical/backends/`.
2. Pick one concrete backend artifact.
3. Register that artifact into `L0` when strong reuse or promotion is expected.
4. Let `L1`, `L3`, or `L4` consult and apply the result explicitly.
5. Promote only the reusable distilled object, not the whole backend artifact tree.
6. If the backend belongs to a paired downstream realization, maintain that pair
   through `L2_PAIRED_BACKEND_MAINTENANCE_PROTOCOL.md` instead of silently
   treating one side as authoritative.

## 7. Why this helps

This gives AITP a stable bridge between:
- AI-side canonical memory,
- human-side note systems,
- software-side method and benchmark systems.

That bridge is what lets the same kernel support:
- pure formal theory libraries,
- numerical code ecosystems,
- and future mixed workflows without turning `L2` into a black box.

When the downstream realization is paired, the bridge remains only half the
story.
Explicit drift audit and rebuild rules are the other half, and they live in:

- `L2_PAIRED_BACKEND_MAINTENANCE_PROTOCOL.md`
