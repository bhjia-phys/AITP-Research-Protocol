# AITP Harness Feedback Problem Capture Implementation Plan

> For agentic workers: implement this plan with TDD. Keep the surface
> orientation-only and review-gated.

**Goal:** Replace the overreaching `skill_graph_workflow_plan` slice with a
problem-capture slice. Skill-related observations become AITP-native
skill-distillation candidates; harness feedback only records the problem and
the review boundary.

**Tech Stack:** Python dict contracts, v5 public surface validators, CLI/MCP
wrappers, pytest, Markdown docs.

## Constraints

- Research-side AITP feedback discovers and records problems.
- Harness/AITP optimization is reviewed and implemented later.
- Skill generation/update belongs to AITP-native skill distillation.
- This slice must not draft `SKILL.md`, install skills, or write project files.
- All outputs remain `orientation_only=true` and
  `can_update_claim_trust=false`.

## File Structure

- Modify `tests/test_v5_harness_feedback.py`.
- Modify `brain/v5/harness_feedback.py`.
- Modify `brain/v5/harness_feedback_contracts.py`.
- Modify `brain/v5/public_surfaces.py`.
- Modify `brain/v5/cli_harness_feedback.py`.
- Modify `brain/v5/mcp_tools.py`.
- Modify `README.md`.
- Add this implementation plan.
- Add
  `docs/superpowers/specs/2026-07-09-aitp-harness-feedback-problem-capture-design.md`.
- Remove the untracked `2026-07-08-aitp-skill-graph-workflow` spec/plan files.

## Task 1: Contract Tests

Add tests that assert:

```python
payload = require_valid_public_surface(
    "harness_feedback_problem_dossier",
    build_harness_feedback_problem_dossier(),
)

assert payload["problem_capture_boundary"]["research_side_role"] == "discover_and_record_problem"
assert payload["problem_capture_boundary"]["harness_side_role"] == "review_and_optimize_later"
assert payload["problem_capture_boundary"]["produces_harness_optimization_plan"] is False
assert payload["problem_capture_boundary"]["produces_skill_implementation_plan"] is False
assert payload["skill_boundary"]["owner"] == "aitp_native_skill_distillation"
assert payload["skill_boundary"]["harness_feedback_role"] == "emit_distillation_candidate_only"
```

Also add a negative contract test that mutates
`produces_harness_optimization_plan=True` and expects `ContractError`.

## Task 2: Builder And Contract

Add `build_harness_feedback_problem_dossier(case_id=CASE_ID)` with:

- `kind=harness_feedback_problem_dossier`
- `problem_dossier_path=problems/skill-related-feedback-boundary.md`
- a single reviewable Markdown file
- `problem_capture_boundary`
- `skill_boundary`
- `requires_human_review=true`
- `summary_inputs_trusted=false`
- `orientation_only=true`
- `can_update_kernel_state=false`
- `can_update_claim_trust=false`

Add `validate_harness_feedback_problem_dossier` and
`require_valid_harness_feedback_problem_dossier`.

## Task 3: Public Surface, CLI, And MCP

Register `harness_feedback_problem_dossier` in `brain/v5/public_surfaces.py`.

Expose:

```bash
aitp-v5 harness-feedback problem-dossier
```

Expose MCP wrapper:

```python
aitp_v5_build_harness_feedback_problem_dossier(...)
```

Remove the `skill_graph_workflow_plan`, `skill-graph-plan`, and
`aitp_v5_plan_skill_graph_workflow` surfaces from this slice.

## Task 4: NiO Bundle Correction

Change the NiO feedback bundle from a skill draft to a distillation candidate:

- Use `skill_distillation_candidate_path`.
- Include `skill_distillation_boundary`.
- Ensure `produces_skill_draft=false` and `can_install_skill=false`.
- Keep `record_schemas=["monitor_snapshot", "harness_feedback_problem_dossier"]`.

## Task 5: Documentation

Update README positioning and key docs so they describe:

- AITP-native skill distillation as the future owner of skill generation/update.
- Harness feedback as a problem-capture surface.
- `problem-dossier` as the current CLI/MCP exposure.
- The theory-discussion knowledge-base layer as a deferred gap.

## Verification

Run:

```powershell
python -m pytest tests\test_v5_harness_feedback.py -q -p no:cacheprovider
python -m pytest tests\test_v5_domain_packs.py -q -p no:cacheprovider
python -m compileall -q brain\v5
git diff --check -- .
```

Expected: all commands exit 0.
