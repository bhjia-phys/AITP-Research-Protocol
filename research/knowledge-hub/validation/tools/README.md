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
