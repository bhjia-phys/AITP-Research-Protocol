"""Generalized HPC research cockpit for any compute topic.

An orientation-only aggregation layer over existing typed records. For a topic
that has HPC-style tool runs (Slurm/ABACUS/LibRPA/PyATB, remote Fisherd runs)
and/or a lane contract, it summarizes: current claim, effective attempts (runs
not superseded), active jobs, failure history, lane distribution, provenance
gaps (runs missing code-state/artifact back-links), the lane contract, next
valid actions, and which conclusions are/are not allowed.

It never becomes a truth source and never updates claim trust. HPC job state
lives in ``tool_run`` records; this cockpit only reads them.
"""

from __future__ import annotations

from typing import Any

from brain.v5.lane_contracts import get_effective_lane_contract
from brain.v5.models import ClaimRecord, ToolRunRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_valid_records

# evidence_status values that mean the scheduler job is still in flight.
_ACTIVE_EVIDENCE_STATUSES = {
    "submitted_pending",
    "running",
    "submitted",
    "pending",
    "resumed",
    "queued",
}
# evidence_status values that mean the run failed before producing evidence.
_FAILURE_EVIDENCE_STATUSES = {
    "failed",
    "failed_setup",
    "failed_runtime",
    "application_failure",
    "cancelled",
    "cancelled_before_start",
    "dependency_never_satisfied",
}
_LANES = ("final", "diagnostic", "exploratory")


def build_hpc_cockpit(ws: WorkspacePaths, topic_id: str) -> dict[str, Any]:
    """Build the orientation-only HPC cockpit for one compute topic."""

    all_runs = [
        run
        for run in list_valid_records(ws.registry_dir("tool_runs"), ToolRunRecord)
        if run.topic_id == topic_id
    ]
    # A run whose superseded_by is set has been replaced by a later attempt and
    # is no longer the current view of that scientific run.
    current_runs = [run for run in all_runs if not getattr(run, "superseded_by", "")]

    active_jobs = [_run_brief(run) for run in current_runs if run.evidence_status in _ACTIVE_EVIDENCE_STATUSES]
    failures = [_run_brief(run) for run in current_runs if run.evidence_status in _FAILURE_EVIDENCE_STATUSES]

    lane_counts = {lane: 0 for lane in _LANES}
    missing_code_state: list[str] = []
    missing_artifacts: list[str] = []
    for run in current_runs:
        lane_counts[run.lane] = lane_counts.get(run.lane, 0) + 1
        if not run.code_state_ids:
            missing_code_state.append(run.run_id)
        if not run.artifact_ids:
            missing_artifacts.append(run.run_id)

    effective_attempts = [
        {
            "scientific_run_id": run.scientific_run_id,
            "run_id": run.run_id,
            "evidence_status": run.evidence_status,
            "lane": run.lane,
            "run_dir": _run_dir(run),
            "scheduler_job_id": _scheduler_job_id(run),
            "supersedes": run.supersedes,
        }
        for run in current_runs
    ]

    claims = [
        claim
        for claim in list_valid_records(ws.registry_dir("claims"), ClaimRecord)
        if claim.topic_id == topic_id
    ]
    current_claim = _claim_brief(claims[0]) if claims else None

    contract = get_effective_lane_contract(ws, topic_id)
    lane_contract = _contract_brief(contract) if contract else None

    next_actions = _derive_next_actions(
        active_jobs=active_jobs,
        failures=failures,
        missing_code_state=missing_code_state,
        missing_artifacts=missing_artifacts,
        lane_counts=lane_counts,
        has_claim=bool(current_claim),
        has_runs=bool(current_runs),
    )
    allowed, not_allowed = _derive_conclusions(
        active_jobs=active_jobs,
        failures=failures,
        lane_counts=lane_counts,
        lane_contract=lane_contract,
    )

    payload = {
        "ok": True,
        "kind": "hpc_cockpit",
        "topic_id": topic_id,
        "current_claim": current_claim,
        "effective_attempts": effective_attempts,
        "active_jobs": active_jobs,
        "failure_history": failures,
        "lane_counts": lane_counts,
        "provenance_gaps": {
            "missing_code_state_run_ids": missing_code_state,
            "missing_artifact_run_ids": missing_artifacts,
        },
        "lane_contract": lane_contract,
        "next_valid_actions": next_actions,
        "conclusions_allowed": allowed,
        "conclusions_not_allowed": not_allowed,
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    payload["markdown"] = _render_markdown(payload)
    return payload


# ---------------------------------------------------------------------------


def _run_brief(run: ToolRunRecord) -> dict[str, Any]:
    return {
        "run_id": run.run_id,
        "scientific_run_id": run.scientific_run_id,
        "recipe_id": run.recipe_id,
        "tool_family": run.tool_family,
        "evidence_status": run.evidence_status,
        "lane": run.lane,
        "run_dir": _run_dir(run),
        "scheduler_job_id": _scheduler_job_id(run),
        "supersedes": run.supersedes,
        "superseded_by": run.superseded_by,
        "has_code_state": bool(run.code_state_ids),
        "has_artifacts": bool(run.artifact_ids),
    }


def _run_dir(run: ToolRunRecord) -> str:
    for key in ("remote_dir", "run_dir", "root"):
        value = run.inputs.get(key) if isinstance(run.inputs, dict) else None
        if value:
            return str(value)
    return ""


def _scheduler_job_id(run: ToolRunRecord) -> str:
    outputs = run.outputs if isinstance(run.outputs, dict) else {}
    return str(outputs.get("slurm_job_id") or outputs.get("job_id") or "")


def _claim_brief(claim: ClaimRecord) -> dict[str, Any]:
    return {
        "claim_id": claim.claim_id,
        "statement": getattr(claim, "statement", ""),
        "confidence_state": getattr(claim, "confidence_state", ""),
    }


def _contract_brief(contract) -> dict[str, Any]:
    return {
        "contract_id": contract.contract_id,
        "campaign": contract.campaign,
        "forbidden_roots": list(contract.forbidden_roots),
        "preferred_clean_roots": list(contract.preferred_clean_roots),
        "final_allowlist": list(contract.final_allowlist),
        "final_rules": list(contract.final_rules),
        "default_lane": contract.default_lane,
        "trust_update_forbidden": contract.trust_update_forbidden,
    }


def _derive_next_actions(
    *,
    active_jobs: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    missing_code_state: list[str],
    missing_artifacts: list[str],
    lane_counts: dict[str, int],
    has_claim: bool,
    has_runs: bool,
) -> list[str]:
    actions: list[str] = []
    for job in active_jobs:
        actions.append(
            f"monitor in-flight job {job['scheduler_job_id'] or job['run_id']} "
            f"({job['evidence_status']})"
        )
    for fail in failures:
        actions.append(
            f"resume or re-submit failed run {fail['scheduler_job_id'] or fail['run_id']} "
            f"({fail['evidence_status']}); record the new attempt with supersedes"
        )
    if missing_code_state:
        actions.append(
            f"back-link code_state_ids for {len(missing_code_state)} run(s) missing code provenance"
        )
    if missing_artifacts:
        actions.append(
            f"attach artifact_ids for {len(missing_artifacts)} run(s) missing product provenance"
        )
    if not actions:
        if not has_runs:
            actions.append("no HPC tool runs recorded; record a job attempt via record_tool_run")
        elif not has_claim:
            actions.append("no active claim bound; bind a claim before recording scientific evidence")
        elif lane_counts.get("final", 0) == 0:
            actions.append("no run marked lane=final; promote a converged run to final only after review")
        else:
            actions.append("all recorded runs settled; request human review before any trust update")
    return actions


def _derive_conclusions(
    *,
    active_jobs: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    lane_counts: dict[str, int],
    lane_contract,
) -> tuple[list[str], list[str]]:
    allowed: list[str] = []
    not_allowed: list[str] = []
    if active_jobs:
        not_allowed.append(
            "cannot conclude physics while scheduler jobs are still pending/running"
        )
    for fail in failures:
        not_allowed.append(
            f"run {fail['scheduler_job_id'] or fail['run_id']} failed ({fail['evidence_status']}); "
            f"this is not scientific evidence"
        )
    if lane_counts.get("diagnostic", 0) > 0 and lane_counts.get("final", 0) == 0:
        not_allowed.append(
            "only diagnostic/exploratory runs present; no final-evidence run to conclude from"
        )
    if lane_contract and lane_contract.get("trust_update_forbidden"):
        not_allowed.append(
            "lane contract forbids trust updates for this topic until cleared"
        )
    if lane_counts.get("final", 0) > 0 and not active_jobs and not failures:
        allowed.append(
            "at least one run is marked lane=final; trust still requires the existing validation/promotion surfaces"
        )
    if not allowed:
        allowed.append(
            "orientation-only status; no trust conclusion is allowed from this cockpit"
        )
    return allowed, not_allowed


def _render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = [f"# HPC Cockpit: `{payload['topic_id']}`", ""]
    claim = payload.get("current_claim")
    if claim:
        lines.append(f"**Current claim:** `{claim['claim_id']}` ({claim.get('confidence_state') or '-'})")
    else:
        lines.append("**Current claim:** none bound")
    lines.append("")

    counts = payload.get("lane_counts") or {}
    lines.append(
        "**Lane distribution:** "
        f"final={counts.get('final', 0)} diagnostic={counts.get('diagnostic', 0)} "
        f"exploratory={counts.get('exploratory', 0)}"
    )

    active = payload.get("active_jobs") or []
    lines.append(f"## Active jobs ({len(active)})")
    if active:
        for job in active:
            lines.append(
                f"- job `{job['scheduler_job_id'] or job['run_id']}`: `{job['evidence_status']}` "
                f"(run_dir `{job['run_dir'] or '-'}`, lane `{job['lane']}`)"
            )
    else:
        lines.append("- none in flight")
    lines.append("")

    failures = payload.get("failure_history") or []
    lines.append(f"## Failure history ({len(failures)})")
    if failures:
        for fail in failures:
            lines.append(
                f"- run `{fail['scheduler_job_id'] or fail['run_id']}`: `{fail['evidence_status']}` "
                f"(lane `{fail['lane']}`)"
            )
    else:
        lines.append("- none")
    lines.append("")

    gaps = payload.get("provenance_gaps") or {}
    if gaps.get("missing_code_state_run_ids") or gaps.get("missing_artifact_run_ids"):
        lines.append("## Provenance gaps")
        if gaps.get("missing_code_state_run_ids"):
            lines.append(f"- {len(gaps['missing_code_state_run_ids'])} run(s) missing code_state back-link")
        if gaps.get("missing_artifact_run_ids"):
            lines.append(f"- {len(gaps['missing_artifact_run_ids'])} run(s) missing artifact back-link")
        lines.append("")

    contract = payload.get("lane_contract")
    if contract:
        lines.append("## Lane contract")
        if contract.get("forbidden_roots"):
            lines.append("- forbidden roots: " + ", ".join(f"`{r}`" for r in contract["forbidden_roots"]))
        if contract.get("final_rules"):
            for rule in contract["final_rules"]:
                lines.append(f"- final rule: {rule}")
        lines.append("")

    lines.append("## Conclusions")
    for item in payload.get("conclusions_allowed", []):
        lines.append(f"- ✅ {item}")
    for item in payload.get("conclusions_not_allowed", []):
        lines.append(f"- ⛔ {item}")
    lines.append("")

    lines.append("## Next valid actions")
    for item in payload.get("next_valid_actions", []):
        lines.append(f"- → {item}")
    lines.append("")
    lines.append(
        "_Orientation-only. This cockpit cannot update claim trust; trust still requires "
        "the existing validation/promotion/checkpoint surfaces._"
    )
    return "\n".join(lines)
