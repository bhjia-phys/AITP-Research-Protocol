"""Read-only final engineering readiness audit for AITP v5."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.adapter_protocols import record_gate_coverage_audit
from brain.v5.hook_smoke_coverage import runtime_hook_smoke_coverage_report
from brain.v5.legacy_semantic_review import build_legacy_semantic_review_queue
from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
from brain.v5.models import ClaimRecord, MemoryEntryRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.source_reconstruction import audit_source_reconstruction_batch
from brain.v5.source_reconstruction_review import build_source_reconstruction_review_manifest
from brain.v5.store import list_records

_PRIORITY_HOSTS = ("codex", "claude_code", "kimi_code")
_DEFERRED_HOSTS = ("opencode",)


def audit_final_engineering_readiness(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Summarize kernel readiness and remaining content backlog.

    This surface is an audit/orientation packet. It deliberately does not
    certify scientific content as complete and cannot mutate trust.
    """

    record_gates = record_gate_coverage_audit()
    host_smoke = runtime_hook_smoke_coverage_report()
    source_stack = _source_stack(ws)
    source_review = build_source_reconstruction_review_manifest(ws)
    source_backlog = _source_reconstruction_backlog(source_stack, source_review)
    legacy_review = _legacy_semantic_review(ws, migration_dir=migration_dir)
    blocking_gaps = _blocking_gaps(record_gates, host_smoke, legacy_review)
    content_backlog_status = _content_backlog_status(legacy_review, source_backlog)
    completion_status = (
        "complete"
        if not blocking_gaps and content_backlog_status == "none"
        else "kernel_ready_content_backlog"
    )
    return {
        "kind": "final_engineering_readiness_audit",
        "completion_status": completion_status,
        "kernel_capability_status": _kernel_capability_status(record_gates, host_smoke),
        "content_backlog_status": content_backlog_status,
        "kernel_capabilities": {
            "record_gate_coverage": _record_gate_payload(record_gates),
            "host_integration": _host_payload(host_smoke),
            "source_stack": source_stack,
            "knowledge_stack": _knowledge_stack(ws),
            "long_term_replay": _long_term_replay(),
            "natural_interaction": _natural_interaction(),
        },
        "content_backlog": {
            "legacy_semantic_review": legacy_review,
            "source_reconstruction": source_backlog,
        },
        "blocking_gaps": blocking_gaps,
        "residual_risks": _residual_risks(host_smoke, legacy_review),
        "evidence_refs": _evidence_refs(source_stack),
        "backlog_refs": _backlog_refs(legacy_review, source_backlog),
        "truth_source": "typed_records_and_contract_audits",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _record_gate_payload(record_gates: dict[str, Any]) -> dict[str, Any]:
    return {
        "surface": "record_gate_coverage_audit",
        "record_protocol_count": len(record_gates.get("record_protocols", [])),
        "gated_record_protocols": list(record_gates.get("gated_record_protocols", [])),
        "ungated_record_protocols": list(record_gates.get("ungated_record_protocols", [])),
        "summary_inputs_trusted": False,
    }


def _host_payload(host_smoke: dict[str, Any]) -> dict[str, Any]:
    runtimes = list(host_smoke.get("runtimes", []))
    by_runtime = {item.get("runtime"): item for item in runtimes}
    priority = {runtime: _runtime_status(by_runtime.get(runtime, {})) for runtime in _PRIORITY_HOSTS}
    deferred = {runtime: _runtime_status(by_runtime.get(runtime, {})) for runtime in _DEFERRED_HOSTS}
    return {
        "surface": "runtime_hook_smoke_coverage",
        "priority_hosts": list(_PRIORITY_HOSTS),
        "deferred_hosts": list(_DEFERRED_HOSTS),
        "priority_host_status": priority,
        "deferred_host_status": deferred,
        "production_loop_surface": "runtime_host_readiness_audit",
        "priority_host_production_loops": [_host_production_loop(runtime) for runtime in _PRIORITY_HOSTS],
        "residual_lifecycle_gap": _unique(
            gap
            for runtime in _PRIORITY_HOSTS
            for gap in priority[runtime].get("gaps", [])
        ),
        "opencode_deferred": True,
        "summary_inputs_trusted": False,
    }


def _host_production_loop(runtime: str) -> dict[str, Any]:
    cli_runtime = _cli_runtime(runtime)
    session_start_supported = runtime in {"claude_code", "kimi_code"}
    readiness_cli = f"aitp-v5 adapter host-readiness {cli_runtime}"
    if session_start_supported:
        readiness_cli = f"{readiness_cli} --run-session-start-smoke --session <session-id>"
    return {
        "runtime": runtime,
        "readiness_cli": readiness_cli,
        "lifecycle_cli": f"aitp-v5 adapter host-lifecycle {cli_runtime}",
        "session_start_smoke_supported": session_start_supported,
        "can_update_claim_trust": False,
    }


def _cli_runtime(runtime: str) -> str:
    return {"claude_code": "claude-code", "kimi_code": "kimi-code"}.get(runtime, runtime)


def _runtime_status(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": str(payload.get("status") or "missing"),
        "test_backed_check_count": len(payload.get("checks", [])),
        "gaps": [str(gap) for gap in payload.get("gaps", []) if str(gap)],
    }


def _source_stack(ws: WorkspacePaths) -> dict[str, Any]:
    claims = list_records(ws.registry_dir("claims"), ClaimRecord)
    claim_ids = [claim.claim_id for claim in claims]
    audits = audit_source_reconstruction_batch(ws, claim_ids)
    complete = [claim_id for claim_id, audit in audits.items() if audit.get("complete") is True]
    incomplete = [claim_id for claim_id, audit in audits.items() if audit.get("complete") is not True]
    return {
        "surface": "source_reconstruction_audit",
        "active_claim_count": len(claims),
        "complete_claim_count": len(complete),
        "incomplete_claim_count": len(incomplete),
        "complete_claim_ids": complete,
        "incomplete_claim_ids": incomplete,
        "missing_components_by_claim": {
            claim_id: list(audit.get("missing_components", []))
            for claim_id, audit in audits.items()
            if audit.get("complete") is not True
        },
        "summary_inputs_trusted": False,
    }


def _knowledge_stack(ws: WorkspacePaths) -> dict[str, Any]:
    entries = list_records(ws.root / "memory" / "l2" / "entries", MemoryEntryRecord)
    active_entries = [entry for entry in entries if entry.status == "active"]
    return {
        "promotion_surface": "promotion_packet_record",
        "memory_surface": "memory_entry_record",
        "l2_audit_surface": "l2_memory_audit",
        "obsidian_view_surface": "l2_obsidian_view_bundle",
        "memory_entry_count": len(entries),
        "active_memory_entry_count": len(active_entries),
        "summary_inputs_trusted": False,
    }


def _source_reconstruction_backlog(source_stack: dict[str, Any], source_review: dict[str, Any]) -> dict[str, Any]:
    incomplete_claim_ids = list(source_stack["incomplete_claim_ids"])
    return {
        "surface": "source_reconstruction_manifest",
        "review_surface": "source_reconstruction_review_manifest",
        "status": "reconstruction_backlog" if incomplete_claim_ids else "complete",
        "active_claim_count": source_stack["active_claim_count"],
        "complete_claim_count": source_stack["complete_claim_count"],
        "incomplete_claim_count": source_stack["incomplete_claim_count"],
        "next_actions": [f"source_reconstruction:{claim_id}" for claim_id in incomplete_claim_ids],
        "review_progress": dict(source_review.get("review_progress") or {}),
        "review_next_actions": list(source_review.get("next_actions") or []),
        "missing_components_by_claim": dict(source_stack["missing_components_by_claim"]),
        "top_incomplete_claims": _top_source_reconstruction_claims(source_review),
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _top_source_reconstruction_claims(source_review: dict[str, Any], *, limit: int = 5) -> list[dict[str, Any]]:
    items = [
        item
        for item in source_review.get("items", [])
        if item.get("source_reconstruction_status") == "incomplete"
    ]
    return [
        {
            "topic_id": str(item.get("topic_id") or ""),
            "claim_id": str(item.get("claim_id") or ""),
            "review_status": str(item.get("review_status") or ""),
            "missing_components": list(item.get("missing_components") or []),
            "next_actions": list(item.get("next_actions") or []),
            "review_packet_cli": str(item.get("review_packet_cli") or ""),
            "can_update_claim_trust": False,
        }
        for item in items[:limit]
    ]


def _long_term_replay() -> dict[str, Any]:
    return {
        "surface": "workspace_replay_packet",
        "workspace_refresh_surface": "workspace_refresh_bundle",
        "legacy_semantic_backlog_surface": "legacy_semantic_review_manifest",
        "legacy_human_checkpoint_view_surface": "legacy_human_checkpoint_obsidian_view_bundle",
        "migration_dir_argument": "--migration-dir",
        "purpose": "multi-session resume packet with source, evidence, and legacy semantic-review gaps",
        "host_startup_backlog_supported": True,
        "host_startup_checkpoint_view_supported": True,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _natural_interaction() -> dict[str, Any]:
    return {
        "surface": "interaction_recording_preview",
        "default_mode": "natural_conversation_with_escalation_at_trust_boundaries",
        "recording_decision_modes": [
            "lightweight_trace",
            "guarded_recording",
            "trust_boundary_checkpoint",
        ],
        "next_kernel_entrypoints": [
            "aitp_v5_record_sensemaking_report",
            "aitp_v5_request_human_checkpoint",
            "aitp_v5_preflight_trust_update",
        ],
        "summary_can_drive_trust": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "summary_inputs_trusted": False,
    }


def _legacy_semantic_review(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path | None,
) -> dict[str, Any]:
    try:
        queue = build_legacy_semantic_review_queue(ws, migration_dir=migration_dir)
        worklist = build_legacy_semantic_review_worklist(ws, migration_dir=migration_dir)
    except FileNotFoundError:
        return {
            "surface": "legacy_semantic_review_queue",
            "worklist_surface": "legacy_semantic_review_worklist",
            "status": "missing_migration_run",
            "run_id": "",
            "topic_count": 0,
            "review_item_count": 0,
            "work_item_count": 0,
            "pass_readiness_counts": {"blocked": 0, "candidate": 0},
            "pass_blocker_counts": {},
            "blocking_class_counts": {},
            "pending_count": 0,
            "passed_count": 0,
            "needs_revision_count": 0,
            "inconclusive_count": 0,
            "worklist_next_actions": [],
            "top_work_items": [],
            "semantic_lossless_proven": False,
            "summary_inputs_trusted": False,
        }
    counts = _semantic_status_counts(queue.get("items", []))
    return {
        "surface": "legacy_semantic_review_queue",
        "worklist_surface": "legacy_semantic_review_worklist",
        "status": "review_backlog" if counts["pending"] or counts["needs_revision"] else "reviewed",
        "run_id": str(queue.get("run_id") or ""),
        "topic_count": int(queue.get("topic_count") or 0),
        "review_item_count": int(queue.get("review_item_count") or 0),
        "work_item_count": int(worklist.get("work_item_count") or 0),
        "open_human_checkpoint_count": int(worklist.get("open_human_checkpoint_count") or 0),
        "open_human_checkpoints": list(worklist.get("open_human_checkpoints") or []),
        "pass_readiness_counts": dict(worklist.get("pass_readiness_counts") or {}),
        "pass_blocker_counts": dict(worklist.get("pass_blocker_counts") or {}),
        "blocking_class_counts": dict(worklist.get("blocking_class_counts") or {}),
        "priority_counts": dict(queue.get("priority_counts") or {}),
        "pending_count": counts["pending"],
        "passed_count": counts["passed"],
        "needs_revision_count": counts["needs_revision"],
        "inconclusive_count": counts["inconclusive"],
        "worklist_next_actions": list(worklist.get("next_actions") or []),
        "top_work_items": _top_legacy_work_items(worklist),
        "semantic_lossless_proven": False,
        "can_update_claim_trust": False,
        "summary_inputs_trusted": False,
    }


def _top_legacy_work_items(worklist: dict[str, Any], *, limit: int = 5) -> list[dict[str, Any]]:
    return [
        {
            "topic": str(item.get("topic") or ""),
            "review_status": str(item.get("review_status") or ""),
            "priority_score": int(item.get("priority_score") or 0),
            "review_focus": list(item.get("review_focus") or []),
            "open_human_checkpoint_refs": list(item.get("open_human_checkpoint_refs") or []),
            "source_reconstruction_review_refs": list(item.get("source_reconstruction_review_refs") or []),
            "satisfied_review_actions": list(item.get("satisfied_review_actions") or []),
            "followup_review_actions": list(item.get("followup_review_actions") or []),
            "blocking_classes": list(item.get("blocking_classes") or []),
            "review_action_commands": list(item.get("review_action_commands") or []),
            "pass_readiness": dict(item.get("pass_readiness") or {}),
            "repair_candidate_count": int(item.get("repair_candidate_count") or 0),
            "missing_source_components": list(item.get("missing_source_components") or []),
            "packet_cli": str(item.get("packet_cli") or ""),
            "can_update_claim_trust": False,
        }
        for item in list(worklist.get("items") or [])[:limit]
    ]


def _semantic_status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"pending": 0, "passed": 0, "needs_revision": 0, "inconclusive": 0}
    for item in items:
        status = item.get("semantic_review_status")
        if status == "reviewed_passed":
            counts["passed"] += 1
        elif status == "reviewed_needs_revision":
            counts["needs_revision"] += 1
        elif status == "reviewed_inconclusive":
            counts["inconclusive"] += 1
        else:
            counts["pending"] += 1
    return counts


def _kernel_capability_status(record_gates: dict[str, Any], host_smoke: dict[str, Any]) -> str:
    if record_gates.get("ungated_record_protocols"):
        return "record_gate_gaps"
    host_payload = _host_payload(host_smoke)
    missing = [
        runtime
        for runtime, status in host_payload["priority_host_status"].items()
        if status["status"] == "missing" or status["test_backed_check_count"] == 0
    ]
    if missing:
        return "priority_host_surface_gaps"
    return "ready_for_priority_hosts"


def _content_backlog_status(legacy_review: dict[str, Any], source_backlog: dict[str, Any]) -> str:
    if legacy_review["status"] == "missing_migration_run":
        return "legacy_semantic_review_backlog"
    if legacy_review["pending_count"] or legacy_review["needs_revision_count"] or legacy_review["inconclusive_count"]:
        return "legacy_semantic_review_backlog"
    if source_backlog["incomplete_claim_count"]:
        return "source_reconstruction_backlog"
    return "none"


def _blocking_gaps(
    record_gates: dict[str, Any],
    host_smoke: dict[str, Any],
    legacy_review: dict[str, Any],
) -> list[str]:
    gaps: list[str] = []
    if record_gates.get("ungated_record_protocols"):
        gaps.append("ungated_record_protocols")
    host_payload = _host_payload(host_smoke)
    for runtime, status in host_payload["priority_host_status"].items():
        if status["status"] == "missing" or status["test_backed_check_count"] == 0:
            gaps.append(f"priority_host_surface_missing:{runtime}")
    if legacy_review["status"] == "missing_migration_run":
        gaps.append("legacy_semantic_review_queue_unavailable")
    elif legacy_review["pending_count"] or legacy_review["needs_revision_count"] or legacy_review["inconclusive_count"]:
        gaps.append("legacy_semantic_review_backlog")
    return gaps


def _residual_risks(host_smoke: dict[str, Any], legacy_review: dict[str, Any]) -> list[str]:
    risks = [
        "proprietary_host_ui_lifecycle_modes_need_periodic_real_smoke",
        "opencode_host_process_smoke_deferred",
    ]
    if legacy_review.get("semantic_lossless_proven") is not True:
        risks.append("legacy_semantic_losslessness_not_proven_by_accounting")
    host_payload = _host_payload(host_smoke)
    risks.extend(f"host_gap:{gap}" for gap in host_payload["residual_lifecycle_gap"])
    return _unique(risks)


def _evidence_refs(source_stack: dict[str, Any]) -> list[str]:
    refs = [f"source_reconstruction:{claim_id}:complete" for claim_id in source_stack["complete_claim_ids"]]
    refs.extend(f"source_reconstruction:{claim_id}:incomplete" for claim_id in source_stack["incomplete_claim_ids"])
    refs.append("record_gate_coverage:ungated=0")
    refs.append("runtime_hook_smoke_coverage:codex_claude_kimi=test_backed")
    return refs


def _backlog_refs(legacy_review: dict[str, Any], source_backlog: dict[str, Any]) -> list[str]:
    run_id = legacy_review.get("run_id") or "missing"
    return [
        f"semantic_review:{run_id}:pending={legacy_review['pending_count']}",
        f"semantic_review:{run_id}:needs_revision={legacy_review['needs_revision_count']}",
        f"semantic_review:{run_id}:inconclusive={legacy_review['inconclusive_count']}",
        f"source_reconstruction:incomplete={source_backlog['incomplete_claim_count']}",
        f"source_reconstruction_review:pending={source_backlog['review_progress'].get('pending', 0)}",
        f"source_reconstruction_review:needs_revision={source_backlog['review_progress'].get('needs_revision', 0)}",
        f"source_reconstruction_review:inconclusive={source_backlog['review_progress'].get('inconclusive', 0)}",
    ]


def _unique(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
