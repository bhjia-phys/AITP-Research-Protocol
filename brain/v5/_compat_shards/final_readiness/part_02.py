# Compatibility shard 2 for final_readiness.
from __future__ import annotations

def _backlog_refs(
    legacy_review: dict[str, Any],
    source_backlog: dict[str, Any],
    vnext_readiness: dict[str, Any],
) -> list[str]:
    run_id = legacy_review.get("run_id") or "missing"
    refs = [
        f"semantic_review:{run_id}:pending={legacy_review['pending_count']}",
        f"semantic_review:{run_id}:needs_revision={legacy_review['needs_revision_count']}",
        f"semantic_review:{run_id}:inconclusive={legacy_review['inconclusive_count']}",
        f"source_reconstruction:incomplete={source_backlog['incomplete_claim_count']}",
        f"source_reconstruction_review:pending={source_backlog['review_progress'].get('pending', 0)}",
        f"source_reconstruction_review:needs_revision={source_backlog['review_progress'].get('needs_revision', 0)}",
        f"source_reconstruction_review:inconclusive={source_backlog['review_progress'].get('inconclusive', 0)}",
    ]
    lane_manifest = vnext_readiness.get("lane_exemplar_manifest") or {}
    refs.append(f"vnext_lane_exemplars:missing={len(lane_manifest.get('missing_lanes') or [])}")
    refs.extend(f"vnext_workstream_backlog:{name}" for name in vnext_readiness.get("backlog_workstreams") or [])
    refs.extend(f"vnext_workstream_missing:{name}" for name in vnext_readiness.get("missing_workstreams") or [])
    refs.append("runtime_mcp_bridge_acceptance:status=expected_contract_only")
    return refs

def _unique(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
