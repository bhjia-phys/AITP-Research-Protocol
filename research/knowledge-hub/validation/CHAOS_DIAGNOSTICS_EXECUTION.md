# Chaos diagnostics execution

This file defines the first numerical pilot for extending a spin-chain chaos study beyond spectral statistics.

## Purpose

Use this execution surface when a Layer 4 run needs small-system checks for:
- gap-ratio sanity checks,
- infinite-temperature OTOC,
- Krylov complexity from Lanczos recursion.

## Current scope

The current pilot tool supports:
- spin-1/2 long-range Heisenberg / Haldane-Shastry-type chains,
- periodic boundary conditions,
- fixed-magnetization sectors,
- optional translation-sector projection,
- optional parity-sector projection,
- small-system exact diagonalization.

It is meant for:
- architecture validation,
- quick research pilots,
- reusable execution patterns.

It is not yet the final large-scale production runner.

## Tool

Main runner:

`validation/tools/hs_chaos_scan.py`

Template config:

`validation/templates/chaos-diagnostics/hs-otoc-krylov.template.json`

## Output expectation

A successful run should emit:
- JSON summary metrics,
- CSV curves for OTOC and Krylov complexity,
- a Markdown result summary,
- paths suitable for a Layer 4 promotion decision.

Before a new physics claim is trusted, this execution surface should also emit:
- a baseline reproduction bundle for at least one public OTOC or Krylov example,
- or an explicit record of which simpler analytic/public benchmark substituted for it and why.

## Current limitation

This pilot does not yet quotient all symmetry sectors simultaneously.

It can resolve:
- a fixed total `S^z` sector,
- translation momentum sectors,
- parity sectors,

but it does not yet fully resolve:
- full non-Abelian `SU(2)` multiplet structure.

Compatibility note:
- parity may be combined with translation only in the `k = 0` or `k = pi` sectors.
- in strongly symmetry-resolved sectors, a single-site `S^z` operator may project to zero, so symmetry-compatible operators such as `bond_zz` may be required for OTOC and Krylov diagnostics.

So results should be read as:
- a reusable execution pilot,
- not the final word on the scientific claim.

## Baseline-first rule

Do not treat a new Haldane-Shastry OTOC or Krylov signal as persuasive physics
until the backend has first reproduced a public baseline.

That baseline may be:
- a published OTOC or Krylov example,
- a public reference code path,
- or a simpler analytic / public toy model using the same diagnostic pipeline.

Novel-topic scans without that baseline remain exploratory by default.
