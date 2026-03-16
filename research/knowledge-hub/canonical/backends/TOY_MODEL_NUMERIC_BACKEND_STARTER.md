# Toy-Model Numeric Backend Starter

This starter pack shows the intended public route for connecting an external
toy-model numeric workspace to `L2`.

It does not assume one personal topic or one private codebase.
It demonstrates the contract shape for small-system, finite-size, or
toy-model calculations that should remain reproducible and operator-visible.

## Included artifacts

- example backend card:
  - `canonical/backends/examples/toy-model-numeric-workspace.example.json`
- generic backend template:
  - `canonical/backends/backend.template.json`
- public validation helper:
  - `validation/tools/tfim_exact_diagonalization.py`
- runtime smoke script:
  - `runtime/scripts/run_toy_model_numeric_backend_smoke.sh`

## Intended use

Use this starter when your external backend is primarily:

- small-system exact diagonalization,
- finite-size toy-model scans,
- symmetry-sector benchmark notes,
- reduced-model validation notebooks,
- public numeric sanity checks before heavier infrastructure.

The expected promotion targets are usually:

- `method`
- `workflow`
- `validation_pattern`
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
{"backend_id":"backend:toy-model-numeric-workspace","title":"Toy-Model Numeric Workspace","backend_type":"mixed_local_library","status":"active","card_path":"canonical/backends/toy-model-numeric-workspace.json","canonical_targets":["method","workflow","validation_pattern","warning_note"]}
```

## Required discipline

- backend presence is not promotion
- finite-size numerics are not automatically transferable to the full theory
- exact model definition, boundary conditions, and parameter choices must stay explicit
- one concrete run note should enter `L0` before strong downstream reuse
- promotion into `L2` still needs the normal `L1 -> L2` or `L3 -> L4 -> L2` route

## Smoke test

Run:

```bash
research/knowledge-hub/runtime/scripts/run_toy_model_numeric_backend_smoke.sh
```

The smoke script does five things:

1. creates a temporary external toy-model numeric backend outside the kernel tree
2. runs a tiny public TFIM exact-diagonalization helper on a fixed config
3. realizes the public example backend card against that temporary backend root
4. registers one generated run note into `L0`
5. runs one bounded `aitp loop` and leaves operator-visible runtime artifacts

This is a bounded protocol smoke test.
It is not a scientific validation claim.
