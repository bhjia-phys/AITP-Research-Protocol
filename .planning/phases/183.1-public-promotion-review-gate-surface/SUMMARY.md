# Phase 183.1 Summary: Public Promotion-Review Gate Surface

Aligned the promote-mode public surface with the new explicit gate while
retaining the selected-candidate route-choice note as supporting evidence.

## What changed

- extended runtime-bundle must-read promotion support so
  `request_promotion`, `approve_promotion`, `promote_candidate`, and
  `auto_promote_candidate` keep
  `selected_candidate_route_choice.active.md` visible
- verified that promote-mode bundles foreground `promotion_gate.md` and retain
  the route-choice note instead of dropping the derivation context

## Verification

- `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "full_promote_mode_foregrounds_gate_surfaces_and_defers_history or keeps_selected_candidate_route_choice_as_supporting_evidence" -q`

