# Layer 2 object families

This file defines the typed families that sit on top of `CanonicalUnit`.

The target is not to freeze the ontology forever.
The target is to make reusable identity explicit from day one, especially for
theory-formal material that should not collapse into one broad `concept` or
`claim_card`.

## Transitional and generic families

### 1. `atomic_note`

Use for:
- sharply scoped reusable distinctions,
- small mechanisms that are too small to justify a richer type yet,
- temporary canonicalization when the content is settled but the narrower type is still unclear.

`payload` should usually include:
- `statement`
- `context`

Do not use for:
- unresolved reminders,
- vague scratch thoughts,
- theory-formal items that clearly belong in one of the dedicated families below.

This is a fallback, not the preferred target for formal theory intake.

### 2. `concept`

Use for:
- broad conceptual maps,
- stable explanatory frames,
- distinctions between nearby ideas that are not best captured as a definition, theorem, or equivalence.

`payload` should usually include:
- `definition`
- `key_distinctions`
- `canonical_examples`

Do not use for:
- source-local claims,
- equation-level formal content,
- theorem statements or proof fragments that should remain decomposed.

### 3. `claim_card`

Use for:
- stable claims worth reusing,
- statements whose scope and assumptions matter,
- distilled claims promoted from papers, runs, or checks when they are not best represented as theorems.

`payload` should usually include:
- `claim`
- `confidence_note`
- `supporting_evidence`
- `counterpoints_or_limits`

Do not use for:
- broad concept explanations,
- active conjectures,
- theorems, lemmas, or proof obligations that should stay explicitly formal.

## Theory-formal families

### 4. `definition_card`

Use for:
- explicit formal definitions,
- source-anchored meaning of technical objects,
- reusable definitions that should be cited independently of longer concept notes.

`payload` should usually include:
- `definition`
- `defined_object`
- `equivalent_forms`
- `non_examples`

Do not use for:
- informal background explanations,
- notation-only disambiguation,
- assumption or regime statements.

### 5. `notation_card`

Use for:
- stable notation conventions,
- overloaded symbol disambiguation,
- notation that recurs across papers or sections.

`payload` should usually include:
- `symbol`
- `meaning`
- `binding_context`
- `notation_variants`

Do not use for:
- equations with semantic content,
- definitions that introduce mathematical objects,
- local scratch aliases.

### 6. `equation_card`

Use for:
- named equations,
- canonical identities,
- source-anchored equations whose exact form is reusable independently of the surrounding derivation.

`payload` should usually include:
- `equation`
- `variables`
- `assumption_refs`
- `regime_refs`

Do not use for:
- long multi-step derivations,
- symbolic manipulations that are only meaningful as a step inside a proof.

### 7. `assumption_card`

Use for:
- explicit hypotheses,
- approximation statements,
- domain assumptions that recur across definitions, equations, and theorems.

`payload` should usually include:
- `assumption`
- `scope_of_use`
- `failure_modes`
- `dependent_units`

Do not use for:
- regime descriptions that package several assumptions plus scale/boundary information,
- caveats whose value is mostly warning rather than hypothesis declaration.

### 8. `regime_card`

Use for:
- validity regimes,
- asymptotic windows,
- parameter-domain restrictions that should be referenced by other units.

`payload` should usually include:
- `regime_statement`
- `parameter_window`
- `boundary_conditions`
- `known_breakdowns`

Do not use for:
- individual assumptions without a regime story,
- warnings that are mostly operational rather than formal.

### 9. `theorem_card`

Use for:
- theorem, lemma, proposition, or corollary statements,
- formally scoped statements whose dependencies and hypotheses must remain explicit.

`payload` should usually include:
- `statement`
- `hypotheses`
- `conclusion`
- `proof_status`

Do not use for:
- informal claims without a theorem-style dependency structure,
- derivation steps that do not stand as a reusable theorem.

### 10. `proof_fragment`

Use for:
- reusable proof ideas,
- local proof subroutines,
- theorem-supporting arguments that should not be flattened into one monolithic derivation object.

`payload` should usually include:
- `goal`
- `inputs`
- `argument`
- `gap_markers`

Do not use for:
- whole theorem statements,
- complete derivations that are better represented as `derivation_object`.

### 11. `derivation_step`

Use for:
- one atomic symbolic or logical step,
- intermediate equalities or substitutions,
- fine-grained proof or derivation units meant to compose into larger objects.

`payload` should usually include:
- `step_statement`
- `input_refs`
- `output_refs`
- `justification`

Do not use for:
- multi-step argument packages,
- standalone equations with no stepwise role.

### 12. `example_card`

Use for:
- canonical worked examples,
- toy cases that instantiate a definition, theorem, or method,
- examples that materially clarify scope.

`payload` should usually include:
- `setup`
- `worked_result`
- `illustrated_units`
- `limitations`

Do not use for:
- raw notebook calculations,
- benchmark logs that belong in validation artifacts.

### 13. `caveat_card`

Use for:
- formal scope limitations,
- subtle exceptions,
- portability warnings that are part of the content contract rather than a runtime checklist.

`payload` should usually include:
- `caveat`
- `trigger_conditions`
- `affected_units`
- `mitigation_or_rephrasing`

Do not use for:
- operational troubleshooting notes with no formal content,
- unresolved blockers.

### 14. `equivalence_map`

Use for:
- equivalence between definitions, formulations, or representations,
- mappings across formal languages that should be reusable as a first-class object.

`payload` should usually include:
- `left_formulation`
- `right_formulation`
- `translation_rules`
- `equivalence_conditions`

Do not use for:
- vague topic relations,
- loose analogies without explicit mapping rules.

### 15. `symbol_binding`

Use for:
- precise variable or symbol bindings,
- local but reusable declarations needed to interpret equations or proof steps,
- disambiguation between symbol instances across contexts.

`payload` should usually include:
- `symbol`
- `bound_object`
- `binding_scope`
- `collision_notes`

Do not use for:
- whole notation systems,
- equations that already carry the real reusable content.

## Process and validation families

### 16. `derivation_object`

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
- cases where the derivation should stay decomposed into `proof_fragment` and `derivation_step`.

### 17. `method`

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

### 18. `workflow`

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

### 19. `topic_skill_projection`

Use for:
- validated reusable execution projections compiled from a mature topic,
- lane-specific startup/read-order contracts,
- benchmark-first or trust-gated execution capsules,
- topic-derived agent-facing route memory that is stable enough for reuse,
- bounded formal-theory execution capsules whose theorem-facing trust artifacts are already explicit and ready.

`payload` should usually include:
- `source_topic_slug`
- `lane`
- `entry_signals`
- `required_first_reads`
- `required_first_routes`
- `benchmark_first_rules`
- `operator_checkpoint_rules`
- `operation_trust_requirements`
- `strategy_guidance`
- `forbidden_proxies`
- `derived_from_artifacts`

Do not use for:
- raw runtime state for the current active topic,
- unvalidated prompt fragments,
- ad hoc operator notes that have not yet stabilized across runs,
- theorem certificates, proof-complete packets, or any object whose main identity is mathematical truth rather than reusable execution guidance.

For `formal_theory`:
- require an active run plus explicit theorem-facing trust artifacts before treating the projection as reusable,
- treat the projection as a read-order and route-memory capsule, not as a promoted theorem statement,
- keep promotion human-reviewed even when neighboring theory packets can enter `L2_auto`.

### 20. `bridge`

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
- vague "related to" links with no real structure,
- unresolved bridge ideas that still belong in the backlog.

### 21. `validation_pattern`

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

### 22. `warning_note`

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

### 23. `physical_picture`

Use for:
- stable physics intuition that is worth reusing,
- heuristic pictures that clarify why a route or object matters,
- bounded informal models that are more than a broad concept note but less
  than a theorem or derivation object.

`payload` should usually include:
- `picture`
- `intuition_scope`
- `supports_units`
- `known_limits`

Do not use for:
- vague inspiration notes with no bounded scope,
- theorem statements or proof fragments,
- runtime steering or collaborator preference notes.

## Family-selection rule

Prefer the narrowest type that matches the object's real reusable role.

For theory-formal material:
- prefer `definition_card`, `notation_card`, `equation_card`, `assumption_card`, `regime_card`, `theorem_card`, `proof_fragment`, `derivation_step`, `example_card`, `caveat_card`, `equivalence_map`, or `symbol_binding` before falling back to `concept` or `claim_card`,
- promote a bundle of small units rather than one report-shaped canonical note,
- merge with an existing concept only when the identity and scope already match.

If an item can only be described as:
- "interesting,"
- "maybe important,"
- "needs follow-up,"
- or "I should remember this later,"

then it is probably still a Layer 3 object, not a Layer 2 one.
