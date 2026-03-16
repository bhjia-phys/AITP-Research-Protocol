# Layer 2 object families

This file defines the first-pass typed families that sit on top of `CanonicalUnit`.

The target is not to freeze the final ontology forever.
The target is to make typed identity explicit from day one.

## 1. `atomic_note`

Use for:
- sharply scoped reusable distinctions,
- small definitions,
- local mechanisms that are too small to justify a richer type yet.

`payload` should usually include:
- `statement`
- `context`

Do not use for:
- unresolved reminders,
- vague scratch thoughts,
- content that should really be a concept, claim card, or warning note.

This is a transitional fallback, not the ideal default target.

## 2. `concept`

Use for:
- definitions,
- conceptual maps,
- distinctions between nearby ideas,
- stable explanatory frames.

`payload` should usually include:
- `definition`
- `key_distinctions`
- `canonical_examples`

Do not use for:
- source-local claims,
- procedure descriptions,
- long derivation traces.

## 3. `claim_card`

Use for:
- stable claims worth reusing,
- statements whose scope and assumptions matter,
- distilled claims promoted from papers, runs, or checks.

`payload` should usually include:
- `claim`
- `confidence_note`
- `supporting_evidence`
- `counterpoints_or_limits`

Do not use for:
- broad concept explanations,
- active conjectures,
- claims whose provenance is still too weak to audit.

## 4. `derivation_object`

Use for:
- semi-formal natural-language derivations,
- structured proof sketches,
- reusable derivational routes,
- ordered reasoning that should be callable later.

`payload` should usually include:
- `goal`
- `inputs`
- `ordered_steps`
- `gap_markers`
- `rigor_status`
- `reusable_intermediate_results`
- `fragility_points`

Do not use for:
- raw scratch calculations,
- unresolved long derivation backlogs,
- one-off notebook fragments that still belong in Layer 3.

## 5. `method`

Use for:
- calculational procedures,
- symbolic or numerical techniques,
- formal manipulations with repeated reuse value.

`payload` should usually include:
- `procedure`
- `inputs`
- `outputs`
- `preconditions`
- `failure_modes`

Do not use for:
- full research workflows with decision points,
- one-shot benchmark logs.

## 6. `workflow`

Use for:
- repeatable multi-step research procedures,
- playbooks for intake, checking, validation, or synthesis,
- agent-usable protocols.

`payload` should usually include:
- `goal`
- `prerequisites`
- `steps`
- `handoff_points`
- `expected_outputs`

Do not use for:
- a single theorem-style derivation,
- content whose main value is conceptual explanation rather than process.

## 7. `bridge`

Use for:
- structural links across topics,
- mappings between frameworks,
- technique transfers,
- cross-domain translations.

`payload` should usually include:
- `left_side`
- `right_side`
- `bridge_statement`
- `mapping_constraints`

Do not use for:
- vague “related to” links with no real structure,
- unresolved bridge ideas that still belong in the backlog.

## 8. `validation_pattern`

Use for:
- reusable check templates,
- contradiction tests,
- benchmark patterns,
- formal or numerical adjudication routes.

`payload` should usually include:
- `target_object_types`
- `validation_question`
- `required_inputs`
- `check_steps`
- `pass_conditions`
- `failure_signals`

Do not use for:
- records of a single run outcome,
- broad method notes without a check goal.

## 9. `warning_note`

Use for:
- portable traps,
- failure modes,
- regime caveats,
- repeated mistakes that should not be relearned.

`payload` should usually include:
- `warning`
- `trigger_conditions`
- `symptoms`
- `mitigation`

Do not use for:
- run-local TODOs,
- unresolved blockers that still need investigation.

## Family-selection rule

Prefer the narrowest type that matches the object's real reusable role.

If an item can only be described as:
- “interesting,”
- “maybe important,”
- “needs follow-up,”
- or “I should remember this later,”

then it is probably still a Layer 3 object, not a Layer 2 one.
