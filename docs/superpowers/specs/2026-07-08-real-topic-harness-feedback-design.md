---
title: "AITP Real-Topic Harness Feedback Loop"
version: "0.1.0"
created: "2026-07-08"
status: "draft_for_review"
scope: "Repo-local Phase 1 design for trust-neutral harness feedback records, NiO seeded case material, and implementation planning."
---

# AITP Real-Topic Harness Feedback Loop Design

## Executive Summary

AITP already records scientific provenance through typed records such as
`tool_run`, `artifact`, `validation_result`, `code_state`, and claim state. The
missing layer is meta-provenance about AITP itself: when real research work shows
that recording is too heavy, monitoring is awkward, a workflow should become a
skill, or a schema does not fit the job, that friction should become structured
harness backlog input rather than chat-only memory.

Phase 1 builds the repo-local design and smallest kernel slice for that loop. It
does not write the external topics root, does not modify any scientific claim
trust, and does not treat diagnostic NiO runs as physics evidence. It defines
trust-neutral records and generated proposal surfaces that can later materialize
the meta-topic at:

```text
research/aitp-topics/_meta/aitp-harness-real-topic-feedback/
```

The first real case is `g0w0-magnetic-nio`, seeded from the user's attached
brief because the topic directory did not exist under the local
`Theoretical-Physics/research/aitp-topics` root at audit time.

## Audit Of Current AITP Role In `g0w0-magnetic-nio`

Current AITP v5 has the right scientific safety boundary:

- `tool_run` can already record HPC attempts and defaults unmarked runs to
  `lane="diagnostic"`.
- `record_tool_run` supports `scientific_run_id`, `supersedes`, and provenance
  back-links to `code_state_ids` and `artifact_ids`.
- The generalized HPC cockpit is orientation-only and reads `tool_run` plus
  lane contracts without updating claim trust.
- The compact Codex facade and closeout audit are plan/preview oriented and do
  not apply trust changes.
- `validation_result` is the first record family that may support later claim
  trust updates, subject to the existing policy and promotion gates.

The NiO case exposes a different need: AITP should observe its own workflow
friction. The current machinery can represent the scientific run provenance,
but it has no first-class place for these harness facts:

- `tool_run` payload construction is too manual for Slurm/LibRPA/FHI-aims jobs.
- Long-running job snapshots do not fit cleanly into `tool_run` or `artifact`.
- Repeated workflow lessons do not become skill drafts or patch proposals.
- Skill versions used by a run are not recorded in a consistent way.
- Failure-mode and validation checklist patterns are not reusable enough.
- User-visible AITP friction is not recorded as meta-topic backlog evidence.

## Identified Harness Friction Points

The initial friction taxonomy should use the following stable labels:

- `too_heavy`
- `repeated_manual_payload`
- `missing_record_type`
- `missing_template`
- `missing_skill_linkage`
- `missing_automation`
- `unclear_trust_gate`
- `poor_monitoring_support`
- `schema_underfit`
- `skill_not_updated`
- `validation_blocked`
- `provenance_too_verbose`
- `provenance_too_sparse`

For the NiO seed case, the most important friction classes are:

- `repeated_manual_payload`: Slurm run metadata, binary hash, input files,
  output files, interpretation boundaries, and resource accounting are manually
  assembled repeatedly.
- `missing_record_type`: live monitor snapshots need their own record.
- `missing_automation`: run directories can be inspected for many fields that
  are currently typed by hand.
- `missing_skill_linkage`: workflow lessons are not linked bidirectionally
  between topic records and skill versions.
- `unclear_trust_gate`: diagnostic runs, monitor snapshots, parsed data, and
  artifacts must not become claim evidence by default.
- `validation_blocked`: validation checklist items are implicit rather than
  encoded as a reusable template.

## Feedback Loop Architecture

The loop has eight stages:

1. Observe real topic activity from records, user feedback, repeated manual
   actions, tool calls, failure diagnoses, and monitoring snapshots.
2. Classify observations into the friction taxonomy.
3. Record them in a harness meta-topic, separate from scientific provenance.
4. Summarize friction and workflow lessons after real topic milestones.
5. Propose schema patches, skill patches, workflow templates, extractor scripts,
   monitor commands, validation checklists, and lightweight recording modes.
6. Aggregate proposals into an AITP harness improvement backlog.
7. Implement selected backlog items in the AITP repository through normal tests.
8. Validate in later real topics whether the change reduces friction.

The feedback records must not be used as evidence for a physics claim. Their
truth role is about the harness experience, not about NiO physics.

## Repo-Local Phase 1 Boundary

Phase 1 is intentionally narrow:

- Write design and implementation plan inside this repository.
- Add contracts for trust-neutral meta records.
- Add tests that prove those records cannot mutate claim trust.
- Generate a repo-local NiO seed bundle and draft text surfaces.
- Plan, not fully implement, the remote/local `run_dir_provenance_extractor`.

Phase 1 does not:

- Create or edit `F:/AI_Workspace/Theoretical-Physics/research/aitp-topics`.
- Install or overwrite an official skill.
- Auto-promote diagnostic run output into evidence.
- Add new trust-update shortcuts.
- Treat one failed run as a hard scientific rule.

## Meta-Topic Directory Layout

The later materialized meta-topic should use this directory shape:

```text
_meta/aitp-harness-real-topic-feedback/
  README.md
  backlog.md
  cases/
    g0w0-magnetic-nio.md
  friction-events/
  workflow-gaps/
  automation-opportunities/
  schema-gaps/
  skill-update-suggestions/
  proposals/
  skill-patch-drafts/
  implementation-milestones/
```

Phase 1 will only generate the text that should be written there later, plus a
public surface that reports the intended paths.

## Typed Record Schemas

### `friction_event`

Purpose: record a user-visible or agent-visible AITP friction event.

Required fields:

- `event_id`
- `topic_id`
- `case_id`
- `observed_at`
- `trigger`
- `friction_type`
- `description`
- `user_visible_cost`
- `linked_records`
- `severity`
- `suggested_resolution`
- `summary_inputs_trusted=false`
- `orientation_only=true`
- `can_update_claim_trust=false`

### `workflow_gap`

Purpose: record a missing workflow capability discovered through a real topic.

Required fields:

- `gap_id`
- `topic_id`
- `workflow_stage`
- `missing_capability`
- `current_workaround`
- `recurrence_count`
- `linked_tool_runs`
- `proposed_template_or_skill`
- `orientation_only=true`
- `can_update_claim_trust=false`

### `automation_opportunity`

Purpose: record a repeated manual action that has automatable inputs.

Required fields:

- `opportunity_id`
- `repeated_action`
- `manual_fields`
- `automatable_sources`
- `proposed_extractor`
- `estimated_savings`
- `acceptance_test`
- `requires_human_review=true`
- `can_update_claim_trust=false`

### `schema_gap`

Purpose: record where an existing record family is underfit.

Required fields:

- `gap_id`
- `current_record_type`
- `why_underfit`
- `proposed_record_type_or_field`
- `example_payload`
- `migration_risk`
- `orientation_only=true`
- `can_update_claim_trust=false`

### `skill_update_suggestion`

Purpose: record a possible skill/workflow update derived from topic experience.

Required fields:

- `suggestion_id`
- `skill_name`
- `suggested_change`
- `source_topic`
- `supporting_records`
- `trust_level` with values `diagnostic`, `validated`, `deprecated`, or `open`
- `patch_draft`
- `requires_human_review=true`
- `can_update_claim_trust=false`

### `harness_improvement_proposal`

Purpose: aggregate friction records into an implementable AITP backlog item.

Required fields:

- `proposal_id`
- `title`
- `motivation_from_real_case`
- `pain_point`
- `proposed_change`
- `minimal_implementation_slice`
- `acceptance_test`
- `risk`
- `linked_cases`
- `status`
- `can_update_claim_trust=false`

### `monitor_snapshot`

Purpose: record a live scheduler/run observation without turning it into
evidence. This is the first minimal record to implement.

Required fields:

- `snapshot_id`
- `topic_id`
- `claim_id`
- `tool_run_id`
- `run_dir`
- `job_id`
- `scheduler_state`
- `elapsed`
- `output_file_sizes`
- `latest_log_markers`
- `memory_status`
- `failure_markers`
- `interpretation_boundary`
- `claim_trust_mutation` fixed to `none`
- `summary_inputs_trusted=false`
- `orientation_only=true`
- `can_update_claim_trust=false`

Validation rule: reject any payload where `claim_trust_mutation != "none"` or
`can_update_claim_trust != false`.

### `workflow_summary`

Purpose: summarize a stabilized real-topic workflow while separating diagnostic
hints from validated rules.

Required fields:

- `summary_id`
- `topic_id`
- `scope`
- `stabilized_steps`
- `known_good_contracts`
- `known_bad_contracts`
- `failure_modes`
- `validation_gates`
- `recommended_skill`
- `linked_records`
- `validated_rules`
- `diagnostic_hints`
- `can_update_claim_trust=false`

### `workflow_template`

Purpose: represent a reusable workflow template derived from a real topic.

Required fields:

- `template_id`
- `generated_from_topic`
- `parameters`
- `command_shapes`
- `required_inputs`
- `expected_outputs`
- `validation_checklist`
- `linked_skill`
- `requires_human_review=true`
- `can_update_claim_trust=false`

### `skill_patch_proposal`

Purpose: propose a concrete skill patch without overwriting the official skill.
This is the second minimal record to implement.

Required fields:

- `proposal_id`
- `skill_name`
- `current_version`
- `proposed_version`
- `patch_summary`
- `patch_body`
- `supporting_records`
- `trust_level` with values `diagnostic`, `validated`, `deprecated`, or `open`
- `review_status` with values `draft`, `ready_for_review`, `approved`,
  `rejected`, or `applied`
- `application_status` with values `not_applied`, `applied`, or `superseded`
- `requires_human_review=true`
- `can_update_claim_trust=false`

Validation rule: reject any payload that omits human review fields or attempts
to set `application_status="applied"` while `review_status` is not `approved`.

## Topic-To-Skill Feedback Mechanism

The feedback mechanism has three links:

1. Skill provenance: a draft skill or patch proposal records source
   topic/tool_run/artifact/validation_result ids.
2. Topic recommendation: a workflow summary records the recommended skill name
   and version for a topic.
3. Run usage: `tool_run` inputs or environment can carry
   `skill_version_used` and `workflow_template_id` as optional provenance
   fields. A later schema patch can make those explicit after the first slice.

The first implementation should only validate and generate proposals. Official
skill files are updated only after human review.

## NiO Case Report Draft

Case id: `g0w0-magnetic-nio`

Source status: seeded from user-provided real-topic brief. No existing topic
directory was found in the local topics root during the initial audit.

### Timeline

- Initial goal: evaluate whether FHI-aims plus LibRPA can support magnetic
  G0W0/QSGW for AFM NiO.
- FHI-aims export route: generate `fold_C` and full-q LibRPA binary exports.
- LibRPA route: run spin-resolved G0W0@PBE and QSGW iteration attempts.
- Monitoring route: repeated `dongfang` Slurm checks for queue state, runtime,
  output growth, memory, and failure markers.
- Interpretation boundary: some runs are diagnostic and must not update claim
  trust without validation results.

### Major Run Directory Classes

- FHI-aims export directories containing control/input contracts and binary
  export products.
- LibRPA G0W0 run directories with `librpa.in`, band files, logs, and resource
  outputs.
- LibRPA QSGW smoke directories using `qsgw_band0 max_iter=1`.
- Monitoring snapshots keyed by run directory and Slurm job id.

Concrete run paths should be backfilled only from typed records or explicit
operator input.

### AIMS Input-Contract Lessons

- Preserve `fold_C`.
- Use full-q export.
- Avoid `periodic_gw_optimize_kgrid_symmetry` for this workflow unless a later
  validated rule says otherwise.
- Record the relevant `control.in` lines as provenance, ideally through the
  run-dir extractor.

### LibRPA Input-Contract Lessons

- Disable ABACUS/PyATB reader flags for this FHI-aims path.
- Keep spin-resolved parsing explicit.
- Separate frontier band36/37 gap checks from high-unoccupied collapse checks.
- Use `qsgw_band0 max_iter=1` for the first QSGW smoke route.

### G0W0 Diagnostic/Results Boundary

G0W0 outputs can be parsed and reviewed, but parsed bands or successful
termination alone do not become physics evidence. The valid path is:

```text
submitted -> running -> completed -> parsed -> diagnostic -> validated ->
physics_evidence -> claim_trust_update_candidate
```

Only the last steps can feed trust-changing surfaces, and those still require
the existing validation and human checkpoint gates.

### QSGW Smoke Workflow

- Start with a low-risk smoke run: `qsgw_band0 max_iter=1`.
- Record job submission as `tool_run` with `lane="diagnostic"`.
- Record live progress as `monitor_snapshot`.
- Record parsed outputs as artifacts or source assets by reference.
- Record validation checklist results separately.

### Repeated Manual Payload Examples

- `run_dir`
- Slurm `job_id`
- Slurm resources and MaxRSS
- binary path/hash
- source commit if available
- `librpa.in`
- AIMS `control.in` key lines
- basis and export metadata
- output file sizes and paths
- normal/failure markers
- interpretation boundary

### Missing `monitor_snapshot`

The current workaround is to fold live scheduler observations into chat,
`tool_run.outputs`, or ad hoc notes. This is too coarse and blurs current job
state with run provenance. `monitor_snapshot` should record live status and
explicitly set `claim_trust_mutation="none"`.

### Missing Run-Dir Extractor

Given a run directory, AITP should extract structured payload candidates for:

- `tool_run.inputs`
- `tool_run.outputs`
- `artifact` or `source_asset` refs
- `monitor_snapshot`
- validation checklist prefill

The extractor should output a reviewable payload, not auto-write trust-relevant
records.

### Missing Topic-To-Skill Link

The NiO workflow should generate a draft skill and future patch proposals, but
the official skill should not be overwritten automatically.

## Example Generated Skill Outline

Draft skill name:

```text
fhi-aims-librpa-magnetic-gw-workflow
```

Draft sections:

- Purpose
- When to use
- Non-goals
- Known-good FHI-aims export contract
- Known-bad FHI-aims export patterns
- LibRPA G0W0 template
- LibRPA QSGW band0 smoke template
- Slurm resource template
- Monitoring checklist
- Failure mode taxonomy
- Band parsing workflow
- Plotting workflow
- Spin-degeneracy check
- Frontier-gap check
- High-unoccupied-collapse check
- Resource accounting
- AITP recording checklist
- Trust-update gate
- Skill patch policy
- Linked AITP topics and records

The draft skill must include a provenance block listing the source case and
supporting typed records. Until those records exist, its trust level is
`diagnostic`.

## Backlog Table

| Item | Source case | Real-topic evidence | Pain point | Proposed change | Minimal slice | Acceptance test | Risk | Linked refs | Status |
|---|---|---|---|---|---|---|---|---|---|
| `run_dir_provenance_extractor` | `g0w0-magnetic-nio` | Repeated Slurm/LibRPA/FHI-aims payload assembly | Manual payload is heavy and error-prone | Add extractor that emits reviewable payload candidates | Plan extractor schema and local fixtures first | Fixture run dir produces stable JSON with no writes | Overfitting to one directory layout | seeded brief; future tool_runs | proposed |
| `monitor_snapshot` typed record | `g0w0-magnetic-nio` | Repeated live job monitoring | Live state does not fit `tool_run` or `artifact` | Add trust-neutral monitor record | Dataclass, validator, public surface, tests | Rejects any claim-trust mutation | Confusing live state with evidence | future tool_run/job ids | proposed |
| `topic_to_skill_summary` | `g0w0-magnetic-nio` | Workflow lessons from NiO route | Topic lessons do not become reusable workflow memory | Add workflow summary/proposal surface | Generate draft summary in harness bundle | Validated and diagnostic sections are separate | Prematurely canonizing hints | seeded brief | proposed |
| `skill_patch_proposal` record | `g0w0-magnetic-nio` | New failure modes and workflow lessons | Skill updates are ad hoc | Add explicit proposal record | Dataclass, validator, public surface, tests | Requires human review and valid review/application state | Auto-applying unreviewed patches | seeded brief; future records | proposed |
| `failure_mode_taxonomy` template | `g0w0-magnetic-nio` | NiO failure classes listed in brief | Failure modes are not reusable | Add workflow template section first | Include taxonomy in NiO draft and skill draft | Taxonomy labels appear in generated bundle | One-off failures become hard rules | seeded brief | proposed |
| `validation_checklist_template` | `g0w0-magnetic-nio` | Need more than normal termination | Validation is underspecified | Generate checklist template | Include checklist in bundle and future contract plan | Checklist covers required NiO checks | Checklist mistaken for passed validation | seeded brief | proposed |
| `lightweight_tool_run_recording_mode` | `g0w0-magnetic-nio` | `tool_run` payload too heavy | Agents avoid or delay records | Add extractor-assisted recording plan | Plan payload prefill, not writer | Generated plan marks missing required fields | Incomplete payloads look authoritative | tool_run contracts | proposed |
| `skill_version_used_by_run` | `g0w0-magnetic-nio` | Skill/workflow version not tracked per run | Run provenance misses workflow version | Add optional payload convention first | Include convention in design and draft skill | Example `tool_run.environment` field is documented | Schema churn before need is clear | future tool_runs | proposed |
| `AITP harness feedback meta-topic` | `g0w0-magnetic-nio` | Friction is chat-only today | No unified harness backlog | Materialize `_meta` topic later | Repo-local bundle with target paths | Bundle lists all target files | External writes without review | target meta-topic path | proposed |
| `real-topic friction event detector` | `g0w0-magnetic-nio` | User phrases like "too heavy" carry signal | Friction not captured | Add detector/proposal stage later | Define taxonomy and sample triggers | Detector emits proposal records, not trust records | False positives/noise | future user messages | proposed |

## Minimal Implementation Plan

The implementation plan should be separate from this spec and should include
test-first tasks. The expected task split is:

1. Add record dataclasses and validators for `monitor_snapshot` and
   `skill_patch_proposal`.
2. Register both public surfaces and add contract tests.
3. Add a `harness_feedback` module that builds a repo-local NiO seed bundle.
4. Add tests for the bundle's required sections, backlog fields, and
   trust-neutral flags.
5. Add CLI/MCP wrappers only if the kernel tests are stable.
6. Add a run-dir extractor plan surface with explicit non-writing behavior.

## Acceptance Tests

Required Phase 1 tests:

- A valid `monitor_snapshot` passes public-surface validation.
- A `monitor_snapshot` with `claim_trust_mutation="candidate"` fails.
- A `monitor_snapshot` with `can_update_claim_trust=true` fails.
- A valid `skill_patch_proposal` passes public-surface validation.
- A `skill_patch_proposal` without `requires_human_review=true` fails.
- A `skill_patch_proposal` with `application_status="applied"` and
  `review_status!="approved"` fails.
- The NiO seed bundle contains the required case report headings.
- Every backlog item contains title, source case, real-topic evidence, pain
  point, proposed change, minimal slice, acceptance test, risk, linked refs, and
  status.
- Generated bundle payload sets `orientation_only=true`,
  `summary_inputs_trusted=false`, and `can_update_claim_trust=false`.
- No test creates `evidence`, `memory_entry`, `promotion_packet`, or
  `trust_update` records.

## Open Design Questions

1. Should `monitor_snapshot` live under `registry/monitor_snapshots`, or under a
   broader `registry/harness_feedback` tree with record-kind subdirectories?
   Recommendation: use `registry/monitor_snapshots` because it is a real record
   family that may be linked by `tool_run_id`.
2. Should `skill_patch_proposal` be a first-class typed record or a specialized
   `harness_improvement_proposal`? Recommendation: first-class record, because
   review/application lifecycle is specific to skill updates.
3. Should `skill_version_used_by_run` become a `ToolRunRecord` field now?
   Recommendation: not in Phase 1. Use `tool_run.environment` convention until
   multiple real cases justify a schema migration.
4. Should the run-dir extractor write records directly? Recommendation: no. It
   should emit reviewable payload candidates first.
5. Should the meta-topic materializer create files automatically? Recommendation:
   only under explicit user approval because the target path is outside this
   repository's current writable root.

## Review Status

This spec is ready for review as the repo-local Phase 1 design. It deliberately
keeps the first implementation slice small: typed contracts and generated
proposal surfaces, not a large end-to-end automation rewrite.
