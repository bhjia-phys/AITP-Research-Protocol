# Phase 179 Plan: Continue-Steering Neutrality

## Objective

Make benign `continue_recorded` steering stay visible without elevating the
overall H-plane posture into `active_human_control`.

## Plan

1. Add focused regressions for direct H-plane audit and runtime-bundle
   projection.
2. Narrow the H-plane blocking-state classifier so only genuinely blocking
   steering directives raise `active_human_control`.
3. Re-run focused regressions and capture receipts.
