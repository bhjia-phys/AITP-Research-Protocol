# AITP Harness Feedback Problem Capture Design

Status: approved correction slice, implementation generation v5

## Problem

Real research sessions expose AITP and harness weaknesses before the system has
enough structure to optimize itself. The feedback surface must preserve those
weaknesses as reviewable problems without pretending that the research-side
session has already designed, implemented, or approved the optimization.

Skill-related signals are especially easy to overreach. A repeated workflow may
be a good candidate for AITP-native skill distillation, but harness feedback
must not directly draft, install, or update a skill. It should record the
observed problem and mark the candidate boundary for later human-reviewed AITP
skill distillation.

## Scope

This slice covers a Markdown-first, reviewable problem dossier surface:

- Capture a concrete recording or workflow problem found during research.
- Preserve the case id and source boundary.
- State that the research side only discovers and records the problem.
- State that harness or AITP optimization happens later through review.
- Mark any reusable workflow signal as an AITP-native skill-distillation
  candidate only.
- Keep the output orientation-only and unable to update claim trust.

## Non-Goals

- Do not complete a harness optimization plan from the research session.
- Do not produce a skill implementation plan.
- Do not draft `SKILL.md`.
- Do not install a project-local skill.
- Do not update the AITP graph, kernel state, evidence, validation, or claim
  trust from this surface.
- Do not solve the broader theory-discussion insight knowledge-base layer here.

## Architecture

```text
real research observation
        |
        v
harness_feedback_problem_dossier
        |
        +--> reviewable Markdown problem file
        +--> problem_capture_boundary
        +--> skill_boundary when reusable workflow signal exists
```

The surface is a capture mechanism, not an optimizer. It can be created from a
real topic case such as the NiO magnetic G0W0/QSGW workflow, but the payload
remains trust-neutral.

## Boundary Contracts

### Problem Capture

The problem-capture boundary must declare:

- `research_side_role=discover_and_record_problem`
- `harness_side_role=review_and_optimize_later`
- `produces_harness_optimization_plan=false`
- `produces_skill_implementation_plan=false`
- `writes_project_files=false`

### Skill Distillation

The skill boundary must declare:

- `owner=aitp_native_skill_distillation`
- `harness_feedback_role=emit_distillation_candidate_only`
- `candidate_only=true`
- `produces_skill_draft=false`
- `can_install_skill=false`

This leaves room for a later AITP-native skill distillation pipeline to read
typed graph slices, check completeness, request human review, and install a
project-local skill only after approval.

## Current Implementation Slice

This slice exposes:

- `brain/v5/harness_feedback.py::build_harness_feedback_problem_dossier`
- `brain/v5/harness_feedback_contracts.py::validate_harness_feedback_problem_dossier`
- public surface `harness_feedback_problem_dossier`
- CLI command `aitp-v5 harness-feedback problem-dossier`
- MCP wrapper `aitp_v5_build_harness_feedback_problem_dossier`
- README positioning for problem capture and skill-distillation boundaries

The NiO harness feedback bundle also now emits
`skill_distillation_candidate_path` instead of `skill_draft_path`.

## Human Review

The generated Markdown dossier includes a `Human Review Notes` section. That is
where a person can decide whether the issue belongs to:

- AITP graph schema or context compiler optimization.
- Harness or MCP exposure optimization.
- AITP-native skill distillation.
- A deferred knowledge-base layer for theory discussions.

## Acceptance Criteria

- The public surface validates through `require_valid_public_surface`.
- The contract rejects completed harness optimization plans.
- The contract rejects skill implementation or install authority.
- The Markdown contains review metadata and non-goals.
- README documents `problem-dossier` rather than the removed
  `skill_graph_workflow_plan` surface.
