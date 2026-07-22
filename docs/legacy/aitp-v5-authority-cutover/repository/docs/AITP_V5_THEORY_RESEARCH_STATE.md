# AITP v5 Theory Research State Surface

This document fixes the boundary for the conservative theory-research intake
surface added for quantum-chaos, QSGW, and similar long-running physics topics.

## What It Automates

The `research-state` surface helps an agent turn real research events into typed
records:

- `register-source`: records an orientation-only `reference_location`.
- `attach-artifact`: records a by-reference `artifact` with local hash metadata
  when the file is available.
- `update-claim-status`: appends a `claim_status` maturity observation without
  mutating the original claim.
- `create-proof-obligation`: records theorem/proof/finite-audit gaps as typed
  obligations.
- `classify-event`: returns an orientation-only recommendation for source,
  artifact, evidence, failed-route, open-gap, or review handling.
- `bounded-evidence`: composes artifact + tool_run + evidence + claim_status for
  finite/run-bounded numerical results.

## What It Does Not Automate

These commands never promote L2 memory and never change claim confidence. Trust
updates still require the existing preflight, validation, promotion, and human
checkpoint surfaces.

A literature summary, chat summary, result filename, or classifier output is not
validated evidence by itself. Evidence must name a topic, claim, status, scoped
output, provenance refs, and any artifact/tool-run refs.

## CLI Examples

```powershell
aitp-v5 --base F:/AI_Workspace/Theoretical-Physics research-state register-source `
  --topic quantum-chaos-long-range-spin-chains `
  --claim claim-quantum-chaos-long-range-spin-chains-at-the-pbc-04af8f2d `
  --connector literature_search `
  --type paper `
  --uri arxiv:2604.14695 `
  --label "Close prior-art literature source" `
  --summary "Prior-art threat to level-statistics novelty; not direct proof of algebraic classification."
```

```powershell
aitp-v5 --base F:/AI_Workspace/Theoretical-Physics research-state bounded-evidence `
  --topic quantum-chaos-long-range-spin-chains `
  --claim claim-quantum-chaos-long-range-spin-chains-at-the-pbc-04af8f2d `
  --artifact-uri F:/AI_Workspace/Theoretical-Physics/research/hs-like-chaos-window/results/symmetry_resolved_ed_20260517/algebra/alpha2_h4_motif_formula_check_L10_L12_fisherd_v1.json `
  --artifact-type fisherd_result_json `
  --artifact-summary "Fisherd L=10-12 H4 motif formula result has zero mismatch groups." `
  --status supports `
  --supports-output finite_L_H4_motif_formula_check_L10_L12 `
  --scope "Finite L=10-12 Fisherd JSON audit only; not an all-L theorem." `
  --machine fisherd `
  --remote-root /home/bhj/ai-runs/quantum-chaos/20260531-spectral-commutant `
  --open-gap "prove all-L H4 motif formula from Yangian/HS algebra"
```

## Maturity Levels

- `exploratory`
- `finite-size evidence`
- `formula-identified`
- `theorem-candidate`
- `publishable`

`publishable` is a review target, not an automatic state transition. It should be
used only with explicit validation and human checkpoint records.

## Research Boundary

For quantum-chaos and HS-like long-range spin chains, bounded numerical evidence
can support scoped outputs such as `finite_L_H4_motif_formula_check_L10_L12`.
It cannot establish an all-L theorem, a Lyapunov exponent, or a final algebraic
classification unless the corresponding proof obligations and review gates are
closed.
