# Validation tools

This directory stores executable helpers for Layer 4 validation runs.

The public kernel does not ship a personal topic-specific numerical tool by
default.
It does ship one tiny public toy-model starter:

- `tfim_exact_diagonalization.py`

This directory is reserved for auditable clone-local or contributed `L4`
executors.

If you add a tool here, pair it with:

- one execution note under `validation/`,
- one explicit input/output contract or template,
- one baseline or understanding gate when trust is required.

Do not treat these tools as the final source of scientific judgment.
Treat them as auditable execution helpers and evidence generators.

## Starter pack categories

Validation tools are organized into three pack categories matching the AITP
research lane taxonomy:

### Formal-theory pack

For topics in the `formal_derivation` lane (template_mode=formal_theory).

Validation focuses on:
- proof closure (goal-state checks, axiom audit),
- Lean bridge compilation where applicable,
- manual derivation cross-check against source.

See `validation/templates/formal-theory-pack.md` for bounded starter guidance.

Example tool: Lean bridge verification via `lean-lsp-mcp` integration.

### Toy-model numeric pack

For topics in the `toy_model` lane.

Validation focuses on:
- exact diagonalization benchmarks against known spectra,
- lattice-model ground-state convergence checks,
- analytic limiting-case comparison.

See `validation/templates/toy-model-numeric/` for bounded starter guidance
and the existing `tfim_exact_diagonalization.py` as a concrete pack member.

### Code-method pack

For topics in the `first_principles` lane (DFT/GW/QSGW workflows).

Validation focuses on:
- basis-set convergence tracking,
- self-consistency cycle convergence criteria,
- comparison against published benchmark values.

See `validation/templates/toy-model-numeric/` for the template format that
code-method packs should mirror.
