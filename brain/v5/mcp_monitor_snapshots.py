"""Full-surface MCP wrappers for immutable monitor snapshot history."""

from __future__ import annotations

import json

from brain.v5.mcp_base_resolution import resolve_workspace_base
from brain.v5.models import MonitorSnapshotRecord
from brain.v5.monitor_snapshots import (
    list_monitor_history,
    monitor_history_payload,
    record_monitor_snapshot_v2,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.record_envelope import RecordActor


def aitp_v5_record_monitor_snapshot_v2(base: str, *, record_json: str) -> dict:
    """Write one exact immutable monitor observation from reviewed JSON."""

    payload = json.loads(record_json)
    if not isinstance(payload, dict):
        raise ValueError("monitor snapshot JSON must decode to an object")
    record = MonitorSnapshotRecord(**payload)
    result = record_monitor_snapshot_v2(
        _workspace(base),
        record,
        actor=RecordActor(
            actor_type="tool",
            actor_id="aitp-v5-monitor-mcp",
            host="local",
        ),
    )
    response = {
        "ok": True,
        "kind": "monitor_snapshot_write_result",
        "status": result.status,
        "snapshot_id": result.record_ref.split(":", 1)[1],
        "record_ref": result.record_ref,
        "content_hash": result.content_hash,
        "revision": result.revision,
        "writes_records": True,
        "truth_source": "typed_monitor_snapshot_record",
        "orientation_only": False,
        "can_update_claim_trust": False,
    }
    return require_valid_public_surface("monitor_snapshot_write_result", response)


def aitp_v5_list_monitor_history(
    base: str,
    *,
    tool_run_ref: str,
    content_hash: str,
    revision: int,
) -> dict:
    """Read ordered monitor history for one exact tool-run version."""

    history = list_monitor_history(
        _workspace(base),
        PinnedRecordRef(
            record_ref=tool_run_ref,
            content_hash=content_hash,
            revision=revision,
        ),
    )
    return require_valid_public_surface("monitor_history", monitor_history_payload(history))


def _workspace(base: str) -> WorkspacePaths:
    return WorkspacePaths(resolve_workspace_base(base))
