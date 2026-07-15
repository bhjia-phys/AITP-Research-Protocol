"""Strict read projection for execution-attempt topology and eligibility."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from brain.v5.artifact_blobs import resolve_artifact_bytes
from brain.v5.lane_contracts import assess_run_lane, get_effective_lane_contract
from brain.v5.models import ArtifactRecord, MonitorSnapshotRecord, ToolRunRecord
from brain.v5.monitor_snapshots import list_monitor_history
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import (
    PinnedRecordRef,
    get_record_version,
    pin_current_record,
)
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository


_COMPLETED_STATES = {"completed", "complete", "succeeded", "success", "done"}
_FAILED_STATES = {
    "failed",
    "failure",
    "cancelled",
    "canceled",
    "timeout",
    "timed_out",
    "node_fail",
    "out_of_memory",
}
_ACTIVE_STATES = {"pending", "queued", "submitted", "running", "resumed"}
@dataclass(frozen=True)
class EffectiveAttemptState:
    requested_run_ref: PinnedRecordRef
    effective_run_ref: PinnedRecordRef | None
    attempt_chain: tuple[PinnedRecordRef, ...]
    topic_id: str
    claim_id: str
    scientific_run_id: str
    topology_status: str
    latest_monitor_ref: PinnedRecordRef | None
    latest_monitor_sequence: int
    scheduler_status: str
    output_status: str
    lane: str
    lane_status: str
    recorded_maturity: str
    attempt_eligible: bool
    blocking_reasons: tuple[str, ...]
    read_errors: tuple[str, ...] = ()
    can_update_claim_trust: bool = False
def resolve_effective_attempt_state(
    ws: WorkspacePaths,
    tool_run_ref: PinnedRecordRef | Mapping[str, Any],
) -> EffectiveAttemptState:
    """Resolve one exact run against the current append-only attempt graph."""
    requested_pin = _coerce_pin(tool_run_ref)
    requested_version = get_record_version(ws, requested_pin)
    requested = requested_version.record
    if not isinstance(requested, ToolRunRecord):
        raise ValueError("tool_run_ref must pin a tool run")

    repository = _repository(ws)
    run_report = repository.list("tool_runs")
    read_errors = [*_issues(run_report.malformed)]
    runs = {
        record.run_id: record
        for record in run_report.records
        if isinstance(record, ToolRunRecord)
    }
    if len(runs) != run_report.loaded_count:
        read_errors.append("tool_runs contains an unexpected record type")
    runs[requested.run_id] = requested

    pins: dict[str, PinnedRecordRef] = {}
    for run_id in runs:
        try:
            pins[run_id] = (
                requested_pin
                if run_id == requested.run_id
                else pin_current_record(ws, f"tool_run:{run_id}")
            )
        except Exception as exc:  # noqa: BLE001 - projection is fail closed.
            read_errors.append(f"tool_run:{run_id}: {exc}")
    if read_errors:
        return _invalid_state(requested_pin, requested, "malformed", read_errors)

    component = _connected_component(requested.run_id, runs)
    reverse_unverified, reverse_errors = _legacy_reverse_state(
        repository,
        component,
        runs,
    )
    if reverse_errors:
        return _invalid_state(requested_pin, requested, "malformed", reverse_errors)
    if reverse_unverified:
        return _state(
            requested_pin=requested_pin,
            requested=requested,
            effective_pin=None,
            chain=tuple(pins[item] for item in sorted(component)),
            topology="legacy_reverse_unverified",
            monitor_pin=None,
            monitor_sequence=0,
            scheduler_status="unknown",
            output_status="unknown",
            leaf=requested,
            eligible=False,
            reasons=["legacy reverse supersession is unverified"],
        )
    topology, leaf_id, chain_ids, topology_reasons = _resolve_topology(
        requested.run_id,
        runs,
        component,
    )
    if topology not in {"valid_leaf", "superseded"} or leaf_id is None:
        return _state(
            requested_pin=requested_pin,
            requested=requested,
            effective_pin=None,
            chain=tuple(pins[item] for item in chain_ids if item in pins),
            topology=topology,
            monitor_pin=None,
            monitor_sequence=0,
            scheduler_status="unknown",
            output_status="unknown",
            leaf=requested,
            eligible=False,
            reasons=topology_reasons,
        )

    leaf = runs[leaf_id]
    effective_pin = pins[leaf_id]
    monitor_pin, monitor, monitor_errors = _latest_monitor(ws, leaf, effective_pin)
    reasons = list(topology_reasons)
    reasons.extend(monitor_errors)
    scheduler_status = _scheduler_status(monitor)
    output_status = _output_status(ws, leaf)
    lane_assessment = assess_run_lane(
        leaf,
        get_effective_lane_contract(ws, leaf.topic_id),
    )
    lane_status = lane_assessment.status
    reasons.extend(lane_assessment.reasons)

    if topology == "superseded":
        reasons.append("requested run is superseded")
    if leaf.recorded_maturity != "reproducible_candidate":
        reasons.append("run is not a reproducible candidate")
    if lane_status != "final_eligible":
        reasons.append("lane is not final-eligible")
    if scheduler_status != "completed":
        reasons.append("latest scheduler observation is not completed")
    if output_status != "complete":
        reasons.append("outputs are not complete")
    if not _successful_exit(leaf):
        reasons.append("run exit status is not successful")

    eligible = not reasons and topology == "valid_leaf"
    return _state(
        requested_pin=requested_pin,
        requested=requested,
        effective_pin=effective_pin,
        chain=tuple(pins[item] for item in chain_ids),
        topology=topology,
        monitor_pin=monitor_pin,
        monitor_sequence=monitor.sequence if monitor else 0,
        scheduler_status=scheduler_status,
        output_status=output_status,
        leaf=leaf,
        eligible=eligible,
        reasons=reasons,
        lane_status=lane_status,
    )


def _resolve_topology(
    requested_id: str,
    runs: Mapping[str, ToolRunRecord],
    component: set[str],
) -> tuple[str, str | None, list[str], list[str]]:
    successors: dict[str, list[str]] = {run_id: [] for run_id in component}
    missing = False
    mismatch = False
    for child_id in component:
        child = runs[child_id]
        parent_id = child.supersedes_run_id
        if not parent_id:
            continue
        parent = runs.get(parent_id)
        if parent is None:
            missing = True
            continue
        successors.setdefault(parent_id, []).append(child_id)
        if not _same_attempt_scope(parent, child):
            mismatch = True
    if _has_cycle(component, runs):
        return "cycle", None, sorted(component), ["attempt chain contains a cycle"]
    if any(len(children) > 1 for children in successors.values()):
        return "branch", None, sorted(component), ["attempt chain branches"]
    if missing:
        return (
            "missing_predecessor",
            None,
            sorted(component),
            ["attempt chain has a missing predecessor"],
        )
    if mismatch:
        return (
            "scope_mismatch",
            None,
            sorted(component),
            ["attempt chain scope mismatch"],
        )

    leaf_id = requested_id
    while successors.get(leaf_id):
        leaf_id = successors[leaf_id][0]
    chain: list[str] = []
    current = leaf_id
    while current:
        chain.append(current)
        current = runs[current].supersedes_run_id
    chain.reverse()
    topology = "valid_leaf" if leaf_id == requested_id else "superseded"
    return topology, leaf_id, chain, []


def _connected_component(
    requested_id: str,
    runs: Mapping[str, ToolRunRecord],
) -> set[str]:
    neighbors: dict[str, set[str]] = {run_id: set() for run_id in runs}
    for child in runs.values():
        parent_id = child.supersedes_run_id
        if parent_id and parent_id in runs:
            neighbors[child.run_id].add(parent_id)
            neighbors[parent_id].add(child.run_id)
    found: set[str] = set()
    pending = [requested_id]
    while pending:
        current = pending.pop()
        if current in found:
            continue
        found.add(current)
        pending.extend(neighbors.get(current, ()))
    return found


def _has_cycle(component: set[str], runs: Mapping[str, ToolRunRecord]) -> bool:
    for start in component:
        seen: set[str] = set()
        current = start
        while current in component:
            if current in seen:
                return True
            seen.add(current)
            current = runs[current].supersedes_run_id
    return False


def _same_attempt_scope(parent: ToolRunRecord, child: ToolRunRecord) -> bool:
    return bool(
        parent.topic_id == child.topic_id
        and parent.claim_id == child.claim_id
        and parent.scientific_run_id
        and parent.scientific_run_id == child.scientific_run_id
    )


def _legacy_reverse_state(
    repository: RecordRepository,
    component: set[str],
    runs: Mapping[str, ToolRunRecord],
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for run_id in component:
        result = repository.read(f"tool_run:{run_id}")
        if result.status != "found" or result.frontmatter is None:
            errors.append(f"tool_run:{run_id}: current frontmatter is unreadable")
            continue
        reverse = str(result.frontmatter.get("superseded_by") or "").strip()
        if not reverse:
            continue
        child = runs.get(reverse)
        if child is None or child.supersedes_run_id != run_id:
            return True, errors
    return False, errors


def _latest_monitor(
    ws: WorkspacePaths,
    run: ToolRunRecord,
    run_pin: PinnedRecordRef,
) -> tuple[PinnedRecordRef | None, MonitorSnapshotRecord | None, list[str]]:
    history = list_monitor_history(ws, run_pin)
    if history.status == "malformed":
        return None, None, list(history.errors)
    if not history.records:
        return None, None, ["no monitor snapshot exists for the effective attempt"]
    return history.latest_snapshot_ref, history.records[-1], []


def _scheduler_status(monitor: MonitorSnapshotRecord | None) -> str:
    if monitor is None or not isinstance(monitor.scheduler_state, Mapping):
        return "unknown"
    raw = str(
        monitor.scheduler_state.get("state")
        or monitor.scheduler_state.get("status")
        or ""
    ).strip().lower()
    if raw in _COMPLETED_STATES:
        return "completed"
    if raw in _FAILED_STATES:
        return "failed"
    if raw in _ACTIVE_STATES:
        return "active"
    return "unknown"


def _output_status(ws: WorkspacePaths, run: ToolRunRecord) -> str:
    if not run.output_manifest:
        return "unknown"
    for item in run.output_manifest:
        if not isinstance(item, Mapping):
            return "partial"
        status = str(item.get("status") or "complete").strip().lower()
        if status in {"partial", "missing", "incomplete", "failed"}:
            return "partial"
        if (
            not item.get("role")
            or not item.get("artifact_ref")
            or not item.get("artifact_record_hash")
            or not item.get("artifact_revision")
            or not item.get("content_hash")
        ):
            return "partial"
        try:
            artifact_pin = PinnedRecordRef(
                record_ref=str(item["artifact_ref"]),
                content_hash=str(item["artifact_record_hash"]),
                revision=int(item["artifact_revision"]),
            )
            artifact = get_record_version(ws, artifact_pin).record
            if not isinstance(artifact, ArtifactRecord):
                return "partial"
            if artifact.topic_id != run.topic_id or artifact.claim_id != run.claim_id:
                return "partial"
            if artifact.content_hash != str(item["content_hash"]):
                return "partial"
            receipt_pin = PinnedRecordRef(
                record_ref=artifact.artifact_blob_receipt_ref,
                content_hash=artifact.artifact_blob_receipt_hash,
                revision=artifact.artifact_blob_receipt_revision,
            )
            content = resolve_artifact_bytes(ws, receipt_pin)
            if hashlib.sha256(content).hexdigest() != artifact.content_hash:
                return "partial"
        except Exception:  # noqa: BLE001 - unreadable output provenance is incomplete.
            return "partial"
    return "complete"


def _successful_exit(run: ToolRunRecord) -> bool:
    if not isinstance(run.exit_status, Mapping):
        return False
    code = run.exit_status.get("code")
    state = str(run.exit_status.get("state") or "").strip().lower()
    return code == 0 and state in _COMPLETED_STATES


def _lane_status(lane: str) -> str:
    normalized = str(lane or "").strip().lower()
    if normalized == "final":
        return "final_eligible"
    if normalized in {"diagnostic", "exploratory"}:
        return "diagnostic_only"
    return "unsupported"


def _state(
    *,
    requested_pin: PinnedRecordRef,
    requested: ToolRunRecord,
    effective_pin: PinnedRecordRef | None,
    chain: tuple[PinnedRecordRef, ...],
    topology: str,
    monitor_pin: PinnedRecordRef | None,
    monitor_sequence: int,
    scheduler_status: str,
    output_status: str,
    leaf: ToolRunRecord,
    eligible: bool,
    reasons: Sequence[str],
    read_errors: Sequence[str] = (),
    lane_status: str = "",
) -> EffectiveAttemptState:
    return EffectiveAttemptState(
        requested_run_ref=requested_pin,
        effective_run_ref=effective_pin,
        attempt_chain=chain,
        topic_id=requested.topic_id,
        claim_id=requested.claim_id,
        scientific_run_id=requested.scientific_run_id,
        topology_status=topology,
        latest_monitor_ref=monitor_pin,
        latest_monitor_sequence=monitor_sequence,
        scheduler_status=scheduler_status,
        output_status=output_status,
        lane=leaf.lane,
        lane_status=lane_status or _lane_status(leaf.lane),
        recorded_maturity=leaf.recorded_maturity,
        attempt_eligible=eligible,
        blocking_reasons=tuple(dict.fromkeys(reasons)),
        read_errors=tuple(read_errors),
    )


def _invalid_state(
    requested_pin: PinnedRecordRef,
    requested: ToolRunRecord,
    topology: str,
    errors: Sequence[str],
) -> EffectiveAttemptState:
    return _state(
        requested_pin=requested_pin,
        requested=requested,
        effective_pin=None,
        chain=(requested_pin,),
        topology=topology,
        monitor_pin=None,
        monitor_sequence=0,
        scheduler_status="unknown",
        output_status="unknown",
        leaf=requested,
        eligible=False,
        reasons=["attempt records are unreadable"],
        read_errors=errors,
    )


def _coerce_pin(value: PinnedRecordRef | Mapping[str, Any]) -> PinnedRecordRef:
    if isinstance(value, PinnedRecordRef):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("tool_run_ref must be an exact pinned ref")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=value.get("revision"),
    )


def _repository(ws: WorkspacePaths) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="system",
            actor_id="effective-attempt-projection",
            host="local",
        ),
    )


def _issues(issues: Sequence[Any]) -> list[str]:
    return [f"{item.path}: {item.error_type}: {item.message}" for item in issues]
