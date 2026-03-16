# Formal-Theory Backend Starter

This starter pack shows the intended public route for connecting an external
formal-theory note library to `L2`.

It does not hard-wire one specific personal repository.
It demonstrates the contract shape that another clone can adapt to its own
formal-theory knowledge base.

## Included artifacts

- example backend card:
  - `canonical/backends/examples/formal-theory-note-library.example.json`
- generic backend template:
  - `canonical/backends/backend.template.json`
- runtime smoke script:
  - `runtime/scripts/run_formal_theory_backend_smoke.sh`

## Intended use

Use this starter when your external backend is primarily:

- derivation notes,
- concept notes,
- proof sketches,
- equation-focused theory notes,
- bridge notes between different formal descriptions.

The expected promotion targets are usually:

- `concept`
- `derivation_object`
- `bridge`
- `warning_note`

## How to realize the backend card in a real clone

1. Copy the example card to:
   - `canonical/backends/<backend_slug>.json`
2. Replace `root_paths` with the actual external backend root.
3. Keep `artifact_granularity` truthful.
4. Keep `l0_registration` truthful.
5. Append one compact row to:
   - `canonical/backends/backend_index.jsonl`

Recommended registry row shape:

```json
{"backend_id":"backend:formal-theory-note-library","title":"Formal Theory Note Library","backend_type":"human_note_library","status":"active","card_path":"canonical/backends/formal-theory-note-library.json","canonical_targets":["concept","derivation_object","bridge","warning_note"]}
```

## Required discipline

- backend presence is not promotion
- folder layout is not ontology
- a concrete backend note should enter `L0` before strong downstream reuse
- promotion into `L2` still needs the normal `L1 -> L2` or `L3 -> L4 -> L2` route

## Smoke test

Run:

```bash
research/knowledge-hub/runtime/scripts/run_formal_theory_backend_smoke.sh
```

The smoke script does four things:

1. creates a temporary external formal-theory backend outside the kernel tree
2. realizes the public example backend card against that temporary backend root
3. registers one formal-theory note into `L0`
4. runs one bounded `aitp loop` and leaves operator-visible runtime artifacts

This is a bounded protocol smoke test.
It is not a scientific validation claim.
