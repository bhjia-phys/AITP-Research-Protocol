"""Generalized HPC research cockpit for any compute topic.

An orientation-only aggregation layer over existing typed records. For a topic
that has HPC-style tool runs (Slurm/ABACUS/LibRPA/PyATB, remote Fisherd runs)
and/or a lane contract, it summarizes: current claim, effective attempts (runs
not superseded), active jobs, failure history, lane distribution, provenance
gaps (runs missing code-state/artifact back-links), the lane contract, next
valid actions, and which conclusions are/are not allowed.

It never becomes a truth source and never updates claim trust. Scheduler state
comes from immutable monitor snapshots; mutable run status is display-only.
"""

from __future__ import annotations

from typing import Any

from brain.v5.effective_attempts import EffectiveAttemptState, resolve_effective_attempt_state
from brain.v5.lane_contracts import get_effective_lane_contract
from brain.v5.monitor_snapshots import list_monitor_history
from brain.v5.models import ClaimRecord, ToolRunRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import pin_current_record
from brain.v5.store import list_records

_LANES = ("final", "diagnostic", "exploratory")


def build_hpc_cockpit(ws: WorkspacePaths, topic_id: str) -> dict[str, Any]:
    """Build the orientation-only HPC cockpit for one compute topic."""

    all_runs = [
        run
        for run in list_records(ws.registry_dir("tool_runs"), ToolRunRecord)
        if run.topic_id == topic_id
    ]
    superseded_ids = {
        run.supersedes_run_id
        for run in all_runs
        if getattr(run, "supersedes_run_id", "")
    }
    successor_by_prior = {
        run.supersedes_run_id: run.run_id
        for run in all_runs
        if getattr(run, "supersedes_run_id", "")
    }
    # New records carry only the immutable forward edge. Reverse status is a
    # derived read model; legacy ``superseded_by`` values remain read-only.
    current_runs = [
        run
        for run in all_runs
        if run.run_id not in superseded_ids and not getattr(run, "superseded_by", "")
    ]

    state_errors: list[str] = []
    states = {
        run.run_id: _effective_state(ws, run, state_errors)
        for run in current_runs
    }
    active_jobs = [
        _run_brief(run, successor_by_prior.get(run.run_id, ""), states[run.run_id])
        for run in current_runs
        if states[run.run_id] is not None
        and states[run.run_id].scheduler_status == "active"
    ]
    current_failures = [
        _run_brief(run, successor_by_prior.get(run.run_id, ""), states[run.run_id])
        for run in current_runs
        if states[run.run_id] is not None
        and states[run.run_id].scheduler_status == "failed"
    ]
    failures = _failure_history(ws, all_runs, successor_by_prior, states)

    lane_counts = {lane: 0 for lane in _LANES}
    missing_code_state: list[str] = []
    missing_artifacts: list[str] = []
    missing_monitor: list[str] = []
    for run in current_runs:
        lane_counts[run.lane] = lane_counts.get(run.lane, 0) + 1
        if not run.code_state_ids:
            missing_code_state.append(run.run_id)
        if not run.artifact_ids:
            missing_artifacts.append(run.run_id)
        state = states[run.run_id]
        if state is None or state.latest_monitor_ref is None:
            missing_monitor.append(run.run_id)

    effective_attempts = [
        {
            "scientific_run_id": run.scientific_run_id,
            "run_id": run.run_id,
            "evidence_status": run.evidence_status,
            "lane": run.lane,
            "run_dir": _run_dir(run),
            "scheduler_job_id": _scheduler_job_id(run),
            "supersedes": run.supersedes,
            "scheduler_status": states[run.run_id].scheduler_status if states[run.run_id] else "unknown",
            "output_status": states[run.run_id].output_status if states[run.run_id] else "unknown",
            "lane_status": states[run.run_id].lane_status if states[run.run_id] else "unsupported",
            "attempt_eligible": states[run.run_id].attempt_eligible if states[run.run_id] else False,
            "blocking_reasons": list(states[run.run_id].blocking_reasons) if states[run.run_id] else ["effective attempt state is unreadable"],
        }
        for run in current_runs
    ]

    claims = [
        claim
        for claim in list_records(ws.registry_dir("claims"), ClaimRecord)
        if claim.topic_id == topic_id
    ]
    current_claim = _claim_brief(claims[0]) if claims else None

    contract = get_effective_lane_contract(ws, topic_id)
    lane_contract = _contract_brief(contract) if contract else None

    next_actions = _derive_next_actions(
        active_jobs=active_jobs,
        failures=current_failures,
        missing_code_state=missing_code_state,
        missing_artifacts=missing_artifacts,
        missing_monitor=missing_monitor,
        lane_counts=lane_counts,
        has_claim=bool(current_claim),
        has_runs=bool(current_runs),
    )
    allowed, not_allowed = _derive_conclusions(
        active_jobs=active_jobs,
        failures=current_failures,
        lane_counts=lane_counts,
        lane_contract=lane_contract,
        eligible_attempts=sum(
            1 for state in states.values() if state is not None and state.attempt_eligible
        ),
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
            "missing_monitor_run_ids": missing_monitor,
        },
        "state_errors": state_errors,
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


def _run_brief(
    run: ToolRunRecord,
    derived_successor_id: str = "",
    state: EffectiveAttemptState | None = None,
) -> dict[str, Any]:
    payload = {
        "run_id": run.run_id,
        "scientific_run_id": run.scientific_run_id,
        "recipe_id": run.recipe_id,
        "tool_family": run.tool_family,
        "evidence_status": run.evidence_status,
        "lane": run.lane,
        "run_dir": _run_dir(run),
        "scheduler_job_id": _scheduler_job_id(run),
        "supersedes": run.supersedes,
        "superseded_by": derived_successor_id or getattr(run, "superseded_by", ""),
        "has_code_state": bool(run.code_state_ids),
        "has_artifacts": bool(run.artifact_ids),
    }
    if state is not None:
        payload.update(
            scheduler_status=state.scheduler_status,
            output_status=state.output_status,
            lane_status=state.lane_status,
            attempt_eligible=state.attempt_eligible,
            blocking_reasons=list(state.blocking_reasons),
            latest_monitor_ref=(
                state.latest_monitor_ref.record_ref if state.latest_monitor_ref else ""
            ),
        )
    return payload


def _effective_state(
    ws: WorkspacePaths,
    run: ToolRunRecord,
    errors: list[str],
) -> EffectiveAttemptState | None:
    try:
        return resolve_effective_attempt_state(
            ws,
            pin_current_record(ws, f"tool_run:{run.run_id}"),
        )
    except Exception as exc:  # noqa: BLE001 - cockpit remains a fail-closed read model.
        errors.append(f"tool_run:{run.run_id}: {exc}")
        return None


def _observed_scheduler_status(ws: WorkspacePaths, run: ToolRunRecord) -> str:
    try:
        run_ref = pin_current_record(ws, f"tool_run:{run.run_id}")
        history = list_monitor_history(ws, run_ref)
    except Exception:  # noqa: BLE001
        return "unknown"
    if history.status == "malformed" or not history.records:
        return "unknown"
    raw = str(
        history.records[-1].scheduler_state.get("state")
        or history.records[-1].scheduler_state.get("status")
        or ""
    ).strip().lower()
    if raw in {"failed", "failure", "cancelled", "canceled", "timeout", "timed_out", "node_fail", "out_of_memory"}:
        return "failed"
    if raw in {"pending", "queued", "submitted", "running", "resumed"}:
        return "active"
    if raw in {"completed", "complete", "succeeded", "success", "done"}:
        return "completed"
    return "unknown"


def _failure_history(
    ws: WorkspacePaths,
    runs: list[ToolRunRecord],
    successor_by_prior: dict[str, str],
    states: dict[str, EffectiveAttemptState | None],
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for run in runs:
        observed = _observed_scheduler_status(ws, run)
        if observed != "failed":
            continue
        brief = _run_brief(
            run,
            successor_by_prior.get(run.run_id, ""),
            states.get(run.run_id),
        )
        brief["scheduler_status"] = observed
        failures.append(brief)
    return failures


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
    missing_monitor: list[str],
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
    if missing_monitor:
        actions.append(
            f"record immutable monitor snapshots for {len(missing_monitor)} run(s) missing scheduler observations"
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
    eligible_attempts: int,
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
    if eligible_attempts > 0 and not active_jobs and not failures:
        allowed.append(
            "at least one effective attempt is execution-eligible; scientific trust still requires validation and checkpoint surfaces"
        )
    elif lane_counts.get("final", 0) > 0:
        not_allowed.append(
            "a final label alone is insufficient; no effective attempt satisfies immutable monitor, output, and lane checks"
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
