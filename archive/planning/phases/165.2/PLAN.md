# Phase 165.2: 3-Mode Runtime Alignment + Literature Intake Fast Path

## Goal

Restate Phase 165.2 in canonical 3-mode terms so runtime context loading,
escalation sensitivity, and literature-intake planning all align with
`explore`, `learn`, and `implement`.

## Current State

### What exists
- `docs/protocols/mode_envelope_protocol.md` now defines the canonical 3-mode
  envelope.
- `research/knowledge-hub/knowledge_hub/mode_registry.py` is the code-level
  source of truth and already normalizes legacy names.
- Historical Phase 165.2 implementation surfaces already exist for mode-aware
  runtime bundling, escalation sensitivity, literature intake, and acceptance
  coverage.
- `L1_VAULT_PROTOCOL.md`, `L2_STAGING_PROTOCOL.md`, and
  `ARXIV_FIRST_SOURCE_INTAKE.md` already describe the source-intake and staging
  surfaces that this phase uses.

### What is missing
1. This phase plan still used legacy terminology and old profile names.
2. Escalation trigger profiles need to be rewritten against the canonical
   3-mode registry.
3. Acceptance tests need to assert validation and promotion as operations
   inside `learn` / `implement`, not as standalone modes.
4. The `literature` submode needs to remain explicitly nested under `explore`.
5. The legacy-to-canonical mapping needs to be documented for future
   maintenance.

## Plan 165.2-01: 3-Mode Runtime Bundle + Escalation Sensitivity

### Scope
- `research/knowledge-hub/knowledge_hub/mode_envelope_support.py`: canonical
  3-mode context-loading profiles and escalation trigger profiles
- `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`: mode-aware
  `must_read_now` / `may_defer_until_trigger`
- `research/knowledge-hub/knowledge_hub/kernel_markdown_renderers.py`: surface
  the current mode early in runtime markdown
- `research/knowledge-hub/runtime/scripts/run_mode_enforcement_acceptance.py`:
  3-mode acceptance coverage

### Tasks

1. **Collapse the legacy 4-profile naming into three canonical profiles in
   `mode_envelope_support.py`:**
   ```
   EXPLORE_PROFILE = {
     must_include: [topic_synopsis, research_question, control_note, relevant_l1_l3],
     must_exclude: [validation_bundles, promotion_surfaces, broad_l2_retrieval],
   }
   LEARN_PROFILE = {
     must_include: [validation_contract, selected_candidate, execution_surface, relevant_l1_l3],
     must_exclude: [unrelated_l2, unrelated_topic_history],
   }
   IMPLEMENT_PROFILE = {
     must_include: [gate_state, candidate, target_backend, supporting_artifacts],
     must_exclude: [unrelated_history, future_publication_surfaces],
   }
   ```
   - The former lightweight discovery load behavior becomes the default narrow
     `EXPLORE_PROFILE`.
   - The old standalone validation / promotion profiles disappear; surface
     selection now happens inside `LEARN_PROFILE` or `IMPLEMENT_PROFILE`.

2. **Wire `build_runtime_bundle()` in
   `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py` to use the
   selected canonical mode profile when building `must_read_now` and
   `may_defer_until_trigger`:**
   - After `_select_runtime_mode()` returns a canonical mode, use the
     corresponding profile to filter and expand the surface lists.
   - Surfaces that match `must_include` patterns go to `must_read_now`.
   - Surfaces that match `must_exclude` patterns go to
     `may_defer_until_trigger`.
   - Surfaces that do not match either stay in their current category.
   - Validation surfaces appear inside `learn` or `implement`; they are never
     represented as a fourth runtime mode.

3. **Update mode-specific escalation trigger profiles in
   `mode_envelope_support.py`:**
   ```python
   _MODE_ESCALATION_TRIGGERS = {
       "explore": {"direction_ambiguity", "scope_change", "candidate_ready"},
       "learn": {"validation_complete", "contradiction_detected", "source_gap"},
       "implement": {"gate_passed", "gate_rejected", "human_override"},
   }
   ```
   - Escalation filtering is keyed only by canonical modes.
   - Out-of-mode triggers are logged but do not escalate.
   - Promotion decisions are surfaced as operations inside `learn` /
     `implement`, not as a separate mode.

4. **Promote the mode section in `runtime_protocol.generated.md`:**
   - Move the `## Mode envelope` and `## Transition posture` sections to appear
     immediately after the topic header, before any detailed action queues.
   - Add a one-line summary: `Operating in {mode} mode. {local_task}`.
   - Explicitly state that validation and promotion are operations within
     `learn` or `implement`, not standalone runtime modes.

5. **Acceptance test: `run_mode_enforcement_acceptance.py` (part 1):**
   - Bootstrap a topic, force `explore`, and verify a discovery-biased
     `must_read_now`.
   - Force `learn`, and verify L4-foreground loading and validation-route
     surfaces.
   - Force `implement`, and verify execution / gate-state loading.
   - Verify escalation triggers fire only for the active mode's trigger set.
   - Verify no runtime surface renders standalone legacy validation or
     promotion modes.

6. **Front-door visible H-plane + autonomy contract:**
   - `session_start.generated.md` and `runtime_protocol.generated.md` must
     publish a plain-language human-control summary.
   - The summary must tell the agent whether AITP is waiting on the human now,
     or whether bounded work should continue autonomously.
   - Codex / Claude Code / OpenCode skill text must explicitly tell the agent
     to surface that posture before deeper work.

7. **Validation-heavy `learn` continuation budget:**
   - `run_topic_loop()` must expand bounded auto-step budget for repeated
     validation work inside `learn` when no active checkpoint or clarification
     gate is present.
   - If historical artifacts still carry legacy validation-loop labels,
     normalize the surfaced language to `learn` + validation operation before
     it reaches agents.
   - Do not expand when the human explicitly disabled auto steps or when a real
     checkpoint / approval / clarification gate is active.
   - Treat this as a foreground agent-loop contract, not as a hidden daemon.

### Out of scope
- Literature-intake fast path (Plan 165.2-02).
- New CLI commands.
- Changes to the layer model or promotion policy.

### Verification
- `run_mode_enforcement_acceptance.py --json` passes on isolated temp kernel
  root.
- Existing acceptance tests still pass.
- `aitp doctor --json` reports the mode-envelope surface as present.
- Session-start / runtime markdown and Codex prompt tests assert the same
  3-mode autonomy contract.

---

## Plan 165.2-02: Literature-Intake Fast Path Under `explore`

### Scope
- Keep `literature` as an `explore` submode in
  `research/knowledge-hub/knowledge_hub/mode_envelope_support.py` and related
  renderers.
- L1 vault -> L2 staging bridge in
  `research/knowledge-hub/knowledge_hub/literature_intake_support.py` (or an
  equivalent staging-support extension).
- Acceptance test for the fast path.

### Tasks

1. **Keep `literature` as an `explore` submode in
   `mode_envelope_support.py`:**
   ```python
   "literature": {
       "parent_mode": "explore",
       "local_task": "Read a source, extract reusable knowledge units, and stage them into L2 without full formal-theory audit.",
       "entry_conditions": [
           "Action involves source intake, reading, or note extraction.",
           "No active benchmark or proof obligation.",
           "Topic lane is formal_theory or mixed.",
       ],
       "exit_conditions": [
           "All extractable units from the current source are staged.",
           "Human redirects to a different task.",
       ],
       "allowed_unit_types": [
           "concept", "physical_picture", "method", "warning_note",
           "claim_card", "workflow",
       ],
       "forbidden_unit_types": [
           "theorem_card", "proof_fragment", "derivation_object",
       ],
       "required_writeback": [
           "L2 staging entries with literature_intake_fast_path provenance tag.",
           "L1 vault wiki pages for the source.",
       ],
   }
   ```
   - Entry: detected automatically when `explore`-mode actions involve
     source-intake keywords, or manually via a literature-intake route.
   - Exit: when all extractable units are staged or the human redirects.
   - This submode does not create a fourth mode; it refines `explore`
     behavior only.

2. **Implement the L1 vault -> L2 staging bridge:**
   - Use `stage_literature_units()` in
     `research/knowledge-hub/knowledge_hub/literature_intake_support.py`
     (or an equivalent staging-support extension).
   - Input: topic slug, source slug, list of candidate knowledge units
     extracted from L1 vault wiki pages.
   - For each unit:
     - validate it is in `allowed_unit_types`,
     - create canonical-format JSON with
       `provenance.literature_intake_fast_path: true`,
     - write to `canonical/staging/entries/` following
       `L2_STAGING_PROTOCOL.md`,
     - update `staging_index.jsonl` and `workspace_staging_manifest.json`.
   - Staged items are immediately searchable via `aitp consult-l2` but are not
     in canonical L2 until a later full audit promotes them.

3. **Wire the fast path into the topic loop:**
   - When `_select_runtime_mode()` returns `explore` and the action summary
     contains source-intake keywords, set `active_submode = "literature"`.
   - The runtime bundle for the `literature` submode should include:
     - the L1 vault wiki pages for the current source,
     - the L2 staging manifest (to check for duplicates),
     - the canonical index (to check for existing units).
   - The runtime bundle should NOT include:
     - validation bundles,
     - promotion gates,
     - full coverage-audit surfaces.

4. **Acceptance test: `run_mode_enforcement_acceptance.py` (part 2):**
   - Register an arXiv source using the existing source-registration flow.
   - Run a literature-intake loop on the topic.
   - Verify that:
     - the runtime bundle is in `explore` mode with `literature` submode,
     - extracted concept / physical_picture / method units appear in L2 staging,
     - staged units carry `literature_intake_fast_path: true` provenance,
     - staged units are NOT in canonical L2 (no premature promotion),
     - `aitp consult-l2` returns the staged units with a staging indicator.
   - Run all checks on isolated temp kernel root.

### Out of scope
- Automatic promotion from staging to canonical (requires later full audit).
- New `aitp intake-literature` CLI command (convenience wrapper; defer to a
  later phase if needed).
- Changes to existing promotion or validation surfaces.

### Verification
- `run_mode_enforcement_acceptance.py --json` passes both parts on isolated
  temp kernel root.
- Staged literature units are visible via `aitp consult-l2 --retrieval-profile
  l1_provisional_understanding` but not in `index.jsonl`.
- Existing acceptance tests still pass.

---

## Migration Note

Canonical mode mapping for this phase plan:
- `discussion` -> `explore`
- `verify` -> `learn`
- `promote` -> `implement` for legacy runtime compatibility only

Operational rules after migration:
- Validation is a `learn` / `implement` operation, not a standalone mode.
- Promotion is a `learn` / `implement` operation, not a standalone mode.
- The `literature` submode stays under `explore`.
- Future acceptance tests and runtime markdown must render only `explore`,
  `learn`, and `implement` as modes.

## Dependencies

- Plan `165.2-01` must complete before Plan `165.2-02` (the literature submode
  builds on the canonical 3-mode runtime bundle).
- The historical Phase `165` real-topic proof remains useful context, but the
  3-mode terminology refresh is self-contained and can proceed independently as
  a documentation and refactoring alignment task.

## Key Files

| File | Change |
|---|---|
| `research/knowledge-hub/knowledge_hub/mode_registry.py` | Canonical mode constants and legacy mapping |
| `research/knowledge-hub/knowledge_hub/mode_envelope_support.py` | Canonical profiles, escalation triggers, literature submode |
| `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py` | Mode-aware context loading |
| `research/knowledge-hub/knowledge_hub/literature_intake_support.py` | L1 -> L2 staging bridge |
| `research/knowledge-hub/runtime/scripts/run_mode_enforcement_acceptance.py` | 3-mode acceptance coverage |
| `research/knowledge-hub/knowledge_hub/kernel_markdown_renderers.py` | Promote mode section in runtime protocol markdown |

## Risk Notes

- The literature fast path deliberately bypasses full formal coverage / theory
  audit. The `literature_intake_fast_path: true` provenance tag is what keeps
  those units visibly distinct from canonical L2 knowledge.
- Staged literature units should be treated as "probably correct but not yet
  fully audited" by agents consulting L2.
- Mode-specific escalation trigger profiles may need iteration once tested
  against real topics. Start conservative and expand only with evidence.
- The highest migration risk is leaving stray legacy 4-mode names in runtime
  markdown or acceptance tests after profile renaming; those surfaces must be
  audited together.
