# Validation tools

This directory stores executable helpers for Layer 4 validation runs.

Current tools:
- `hs_chaos_scan.py`
  - small-system exact-diagonalization pilot for gap ratio, OTOC, and Krylov complexity with optional translation/parity symmetry projection

Current dependency note:
- the pilot uses `numpy` and `scipy`
- in this environment they were installed in the user Python environment rather than a repo-local virtualenv because `venv` and `pip` were initially unavailable

Do not treat these tools as the final production backend.
Treat them as:
- auditable execution helpers,
- run-local evidence generators,
- reusable templates for later specialized numerical backends.
