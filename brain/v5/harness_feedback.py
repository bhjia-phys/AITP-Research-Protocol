"""Trust-neutral real-topic harness feedback records and generated bundles."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.models import MonitorSnapshotRecord, SkillPatchProposalRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import write_record


CASE_ID = "g0w0-magnetic-nio"
META_TOPIC_PATH = "research/aitp-topics/_meta/aitp-harness-real-topic-feedback"
CASE_REPORT_PATH = "cases/g0w0-magnetic-nio.md"
BACKLOG_PATH = "backlog.md"
SKILL_DRAFT_PATH = "skill-patch-drafts/fhi-aims-librpa-magnetic-gw-workflow.SKILL.draft.md"


def record_monitor_snapshot(ws: WorkspacePaths, **kwargs: Any) -> MonitorSnapshotRecord:
    """Write a live monitor snapshot that has no claim-trust authority."""

    record = MonitorSnapshotRecord(**kwargs)
    record.claim_trust_mutation = "none"
    record.summary_inputs_trusted = False
    record.orientation_only = True
    record.can_update_claim_trust = False
    write_record(
        ws.registry_dir("monitor_snapshots") / f"{record.snapshot_id}.md",
        record,
        body=f"# Monitor Snapshot\n\n{record.interpretation_boundary}\n",
    )
    return record


def monitor_snapshot_payload(record: MonitorSnapshotRecord) -> dict[str, Any]:
    return {"ok": True, **asdict(record)}


def record_skill_patch_proposal(ws: WorkspacePaths, **kwargs: Any) -> SkillPatchProposalRecord:
    """Write a review-gated skill patch proposal without applying it."""

    record = SkillPatchProposalRecord(**kwargs)
    record.requires_human_review = True
    record.summary_inputs_trusted = False
    record.orientation_only = True
    record.can_update_claim_trust = False
    write_record(
        ws.registry_dir("skill_patch_proposals") / f"{record.proposal_id}.md",
        record,
        body=f"# Skill Patch Proposal\n\n{record.patch_body}\n",
    )
    return record


def skill_patch_proposal_payload(record: SkillPatchProposalRecord) -> dict[str, Any]:
    return {"ok": True, **asdict(record)}


def build_nio_harness_feedback_bundle() -> dict[str, Any]:
    """Build the reviewable NiO seed bundle without writing the meta-topic."""

    backlog_items = _nio_backlog_items()
    files = {
        "README.md": _readme_markdown(),
        CASE_REPORT_PATH: _case_markdown(),
        BACKLOG_PATH: _backlog_markdown(backlog_items),
        SKILL_DRAFT_PATH: _skill_draft_markdown(),
    }
    return {
        "ok": True,
        "kind": "harness_feedback_bundle",
        "case_id": CASE_ID,
        "meta_topic_path": META_TOPIC_PATH,
        "case_report_path": CASE_REPORT_PATH,
        "backlog_path": BACKLOG_PATH,
        "skill_draft_path": SKILL_DRAFT_PATH,
        "files": files,
        "backlog_items": backlog_items,
        "record_schemas": ["monitor_snapshot", "skill_patch_proposal"],
        "writes_external_topics_root": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_claim_trust": False,
    }


def plan_run_dir_provenance_extractor(case_id: str = CASE_ID) -> dict[str, Any]:
    """Return a non-writing extractor plan for Slurm/FHI-aims/LibRPA run dirs."""

    return {
        "ok": True,
        "kind": "run_dir_provenance_extractor_plan",
        "case_id": case_id,
        "purpose": (
            "Extract reviewable payload candidates from a local or remote run directory "
            "without writing evidence, validation, memory, or claim-trust records."
        ),
        "inputs": [
            "run_dir",
            "optional job_id",
            "optional topic_id",
            "optional claim_id",
            "optional tool_run_id",
        ],
        "outputs": [
            "tool_run_candidate",
            "artifact_candidates",
            "monitor_snapshot_candidate",
            "validation_checklist_prefill",
        ],
        "extractors": [
            "slurm_job_metadata from squeue, sacct, and slurm output files",
            "librpa_input_contract from librpa.in",
            "aims_export_contract from control.in and export sidecars",
            "output_inventory from file names, sizes, mtimes, and log markers",
            "band_parse_hints from spin-resolved band files when present",
            "resource_accounting from MaxRSS, elapsed time, node count, and MPI/OMP fields",
        ],
        "review_gates": [
            "operator confirms run_dir identity before any record write",
            "diagnostic lane remains default unless a human marks the run final",
            "parsed gaps are checklist inputs, not physics evidence",
            "validation_result remains the only route toward claim-supporting evidence",
        ],
        "acceptance_test": (
            "A fixture run directory yields deterministic candidate JSON containing job id, "
            "resources, input-contract markers, output inventory, monitor snapshot fields, "
            "and explicit missing-field diagnostics while writes_records remains false."
        ),
        "writes_records": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_claim_trust": False,
    }


def _readme_markdown() -> str:
    return """# AITP Harness Real-Topic Feedback

This meta-topic is a proposed home for trust-neutral AITP harness feedback from
real research topics. It is separate from scientific claim provenance.

Phase 1 is repo-local: this bundle describes the files that should be
materialized later and does not write the external topics root.
"""


def _case_markdown() -> str:
    return """# Case: g0w0-magnetic-nio

Seed status: generated from the user-provided real-topic brief. No existing
topic directory was found under the local topics root during the initial audit.

## Timeline

- Evaluate whether FHI-aims plus LibRPA can support magnetic G0W0/QSGW for AFM NiO.
- Generate FHI-aims `fold_C` and full-q LibRPA binary exports.
- Run spin-resolved G0W0@PBE and QSGW smoke attempts with LibRPA.
- Monitor long-running `dongfang` Slurm jobs for queue state, output growth, memory, and failure markers.
- Keep diagnostic run conclusions separate from claim trust.

## Major Run Directory Classes

- FHI-aims export directories with `control.in`, basis/export metadata, and binary exports.
- LibRPA G0W0 directories with `librpa.in`, logs, band files, and Slurm output.
- LibRPA QSGW smoke directories using `qsgw_band0 max_iter=1`.
- Monitor snapshots keyed by run directory and Slurm job id.

## AIMS Input-Contract Lessons

- Preserve `fold_C`.
- Use full-q export.
- Avoid `periodic_gw_optimize_kgrid_symmetry` unless a later validated rule says otherwise.
- Capture important `control.in` lines through the run-dir extractor.

## LibRPA Input-Contract Lessons

- Disable ABACUS/PyATB reader flags for the FHI-aims path.
- Keep spin-resolved parsing explicit.
- Separate frontier band36/37 gap checks from high-unoccupied collapse checks.
- Use `qsgw_band0 max_iter=1` for the first QSGW smoke route.

## G0W0 Diagnostic/Results Boundary

The valid status path is:

```text
submitted -> running -> completed -> parsed -> diagnostic -> validated -> physics_evidence -> human_review_checkpoint
```

Parsed bands, successful termination, monitor snapshots, and artifacts do not
update claim trust by themselves.

## QSGW Smoke Workflow

- Submit `qsgw_band0 max_iter=1` as a diagnostic `tool_run`.
- Record live status through `monitor_snapshot`.
- Record parsed outputs as artifacts or source assets by reference.
- Record validation checklist results separately.

## Repeated Manual AITP Payload Examples

- `run_dir`, Slurm `job_id`, resources, binary path/hash, source commit, `librpa.in`.
- AIMS `control.in` key lines, basis/export metadata, output files, log markers.
- Interpretation boundary and failure markers.

## Missing Monitor Snapshot Problem

Live scheduler observations currently get folded into chat or `tool_run`
payloads. They need a separate `monitor_snapshot` record with
`claim_trust_mutation: none`.

## Missing Run-Dir Extractor Problem

Given a run directory, AITP should produce reviewable payload candidates for
`tool_run`, `artifact`, `monitor_snapshot`, and validation checklist prefill.

## Missing Topic-To-Skill Problem

NiO workflow lessons should generate a draft skill or patch proposal, not
overwrite an official skill.

## Proposed Skill Outline

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
"""


def _skill_draft_markdown() -> str:
    return """---
name: fhi-aims-librpa-magnetic-gw-workflow
status: draft
source_case: g0w0-magnetic-nio
trust_level: diagnostic
requires_human_review: true
---

# FHI-aims LibRPA Magnetic GW Workflow

## Purpose

Preserve reviewable workflow knowledge for AFM NiO magnetic G0W0/QSGW runs.

## Non-goals

This draft does not validate a physics claim, update claim trust, or replace the
official LibRPA domain skill.

## Monitoring Checklist

- Record Slurm state, elapsed time, output growth, memory status, and failure markers as `monitor_snapshot`.
- Keep monitor snapshots out of claim-trust updates.

## Trust-Update Gate

Diagnostic runs, parsed outputs, monitor snapshots, and artifacts are not
physics evidence until an explicit validation result and human review support
the claim-trust path.
"""


def _backlog_markdown(backlog_items: list[dict[str, str]]) -> str:
    lines = ["# AITP Harness Feedback Backlog", ""]
    for item in backlog_items:
        lines.extend(
            [
                f"## {item['title']}",
                "",
                f"- Source case: `{item['source_case']}`",
                f"- Real-topic evidence: {item['real_topic_evidence']}",
                f"- Pain point: {item['pain_point']}",
                f"- Proposed change: {item['proposed_change']}",
                f"- Minimal implementation slice: {item['minimal_implementation_slice']}",
                f"- Acceptance test: {item['acceptance_test']}",
                f"- Risk: {item['risk']}",
                f"- Linked topic/records/artifacts: {item['linked_topic_records_artifacts']}",
                f"- Status: `{item['status']}`",
                "",
            ]
        )
    return "\n".join(lines)


def _nio_backlog_items() -> list[dict[str, str]]:
    return [
        _backlog_item(
            "run_dir_provenance_extractor",
            "Repeated Slurm/LibRPA/FHI-aims payload assembly.",
            "Manual payload assembly is heavy and error-prone.",
            "Add a non-writing extractor that emits reviewable payload candidates.",
            "Plan extractor schema and local fixtures first.",
            "Fixture run dir produces stable candidate JSON with no writes.",
            "Overfitting to one directory layout.",
        ),
        _backlog_item(
            "monitor_snapshot typed record",
            "Repeated live job monitoring.",
            "Live state does not fit `tool_run` or `artifact`.",
            "Add a trust-neutral monitor snapshot record.",
            "Dataclass, validator, public surface, and tests.",
            "Rejects any claim-trust mutation.",
            "Confusing live scheduler state with evidence.",
        ),
        _backlog_item(
            "topic_to_skill_summary",
            "Workflow lessons from the NiO route.",
            "Topic lessons do not become reusable workflow memory.",
            "Generate a workflow summary with validated and diagnostic layers.",
            "Generate draft summary in the harness bundle.",
            "Validated rules and diagnostic hints are separate.",
            "Prematurely canonizing hints.",
        ),
        _backlog_item(
            "skill_patch_proposal record",
            "New failure modes and workflow lessons.",
            "Skill updates are ad hoc.",
            "Add explicit review-gated skill patch proposals.",
            "Dataclass, validator, public surface, and tests.",
            "Requires human review and valid review/application state.",
            "Applying unreviewed patches.",
        ),
        _backlog_item(
            "failure_mode_taxonomy template",
            "NiO failure classes listed in the case brief.",
            "Failure modes are not reusable.",
            "Add reusable taxonomy in workflow and skill drafts.",
            "Include taxonomy labels in the generated bundle.",
            "Taxonomy labels appear in case and skill draft files.",
            "One-off failures become hard rules.",
        ),
        _backlog_item(
            "validation_checklist_template",
            "Need more than normal termination.",
            "Validation is underspecified.",
            "Generate a reusable validation checklist template.",
            "Include checklist in the bundle and future contract plan.",
            "Checklist covers required NiO checks.",
            "Checklist mistaken for passed validation.",
        ),
        _backlog_item(
            "lightweight_tool_run_recording_mode",
            "`tool_run` payloads are too heavy.",
            "Agents delay or avoid records when payloads are manual.",
            "Add extractor-assisted payload prefill.",
            "Plan payload candidates rather than writing records.",
            "Generated plan marks missing required fields.",
            "Incomplete payloads look authoritative.",
        ),
        _backlog_item(
            "skill_version_used_by_run",
            "Skill/workflow version is not tracked per run.",
            "Run provenance misses workflow version.",
            "Add an optional payload convention first.",
            "Document `tool_run.environment.skill_version_used` convention.",
            "Example convention appears in the draft skill.",
            "Schema churn before multiple cases justify it.",
        ),
        _backlog_item(
            "AITP harness feedback meta-topic",
            "Friction is chat-only today.",
            "No unified harness backlog exists.",
            "Materialize the `_meta` topic after explicit approval.",
            "Repo-local bundle with target paths.",
            "Bundle lists all target files and writes_external_topics_root is false.",
            "External writes without review.",
        ),
        _backlog_item(
            "real-topic friction event detector",
            "User phrases such as too heavy and not smooth carry signal.",
            "Friction is not captured.",
            "Add detector/proposal stage that emits feedback records.",
            "Define taxonomy and sample triggers.",
            "Detector emits proposal records, not trust records.",
            "False positives create backlog noise.",
        ),
    ]


def _backlog_item(
    title: str,
    real_topic_evidence: str,
    pain_point: str,
    proposed_change: str,
    minimal_implementation_slice: str,
    acceptance_test: str,
    risk: str,
) -> dict[str, str]:
    return {
        "title": title,
        "source_case": CASE_ID,
        "real_topic_evidence": real_topic_evidence,
        "pain_point": pain_point,
        "proposed_change": proposed_change,
        "minimal_implementation_slice": minimal_implementation_slice,
        "acceptance_test": acceptance_test,
        "risk": risk,
        "linked_topic_records_artifacts": "seeded brief; future typed records",
        "status": "proposed",
    }
