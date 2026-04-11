# L2 MVP Contract

## Purpose

This document freezes the minimum Layer 2 semantic contract for M1.
Its job is to define the smallest reusable node and edge families that M1 may rely on across canonical storage, runtime summaries, and retrieval-facing docs without implying a wider graph ontology than the implementation currently supports.

## MVP node families

M1 freezes the following node families as the Layer 2 MVP surface:

- `concept`
- `theorem_card`
- `method`
- `assumption_card`
- `physical_picture`
- `warning_note`

Within the current production contract sources, all six MVP families above are
active typed vocabulary represented by the canonical-unit schema, backend
targets, Layer 2 typed-family docs, and the bounded MVP graph helper path.

## Immediate next extension family

The first extension family after the M1 freeze is:

- `negative_result`

`negative_result` is also RESERVED by the M1 contract as a next-extension /
deferred family. It is NOT yet active in the current canonical-unit schema or
the current typed L2 vocabulary, and it is not activated as required populated
graph data in M1.

## MVP edge families

M1 freezes the following edge families:

- `depends_on`
- `uses_method`
- `valid_under`
- `warns_about`
- `contradicts`
- `analogy_to`
- `derived_from_source`

These edge families are the minimum reusable relation set for semantically meaningful topic summaries and later graph traversal.

## Activation rule

M1 freezes the contract.
That means the node and edge families above are the declared active Layer 2
MVP vocabulary for the current bounded implementation.

M1 still does not claim broad graph maturity, multi-backend federation, or a
rich populated knowledge network. It claims only that the MVP vocabulary is now
real production contract surface and that one bounded seeded direction may rely
on it honestly.
