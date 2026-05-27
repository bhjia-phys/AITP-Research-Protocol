"""Legacy-aware source reconstruction review packets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.legacy_semantic_review import build_legacy_semantic_review_queue
from brain.v5.paths import WorkspacePaths
from brain.v5.source_reconstruction import build_source_reconstruction_review_packet

_RECONSTRUCTION_REF_PREFIXES = ("legacy_candidate:", "legacy_l3_process:")
_REVIEW_COMPONENTS = (
    "definitions",
    "assumptions_or_scope",
    "source_locations",
    "dependency_graph",
    "reconstruction_path",
    "failure_conditions",
)


def build_legacy_source_reconstruction_review_packet(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
    topic: str,
) -> dict[str, Any]:
    """Build a legacy-aware packet for source reconstruction component review."""

    queue = build_legacy_semantic_review_queue(ws, migration_dir=migration_dir)
    item = _queue_item(queue, topic)
    active_claim_id = str(item.get("active_claim_id") or "")
    latest_review = item.get("latest_semantic_review") if isinstance(item.get("latest_semantic_review"), dict) else {}
    source_packet = build_source_reconstruction_review_packet(ws, claim_id=active_claim_id) if active_claim_id else {}
    source_reconstruction = item.get("source_reconstruction") if isinstance(item.get("source_reconstruction"), dict) else {}
    missing_components = list(source_packet.get("missing_components") or source_reconstruction.get("missing_components") or [])
    component_reviews = list(source_packet.get("component_reviews") or [])
    reviewed_refs = _clean_refs(latest_review.get("reviewed_legacy_refs", []))
    all_source_refs = _unique([
        *reviewed_refs,
        *[str(ref) for ref in item.get("source_reconstruction", {}).get("source_refs", []) if str(ref)],
    ])
    return {
        "ok": True,
        "kind": "legacy_source_reconstruction_review_packet",
        "run_id": queue["run_id"],
        "migration_dir": queue["migration_dir"],
        "topic": item["topic"],
        "active_claim_id": active_claim_id,
        "latest_review_id": str(latest_review.get("review_id") or ""),
        "source_reconstruction_status": str(
            source_reconstruction.get("status") or ("incomplete" if missing_components else "complete")
        ),
        "missing_components": missing_components,
        "component_review_count": len(component_reviews),
        "review_result_cli": _review_result_cli(active_claim_id),
        "latest_semantic_review": latest_review,
        "source_reconstruction_review_packet": source_packet,
        "legacy_refs": {
            "reviewed_legacy_refs": reviewed_refs,
            "source_reconstruction_refs": list(item.get("source_reconstruction", {}).get("source_refs", [])),
            "refs_by_prefix": _refs_by_prefix(all_source_refs),
        },
        "legacy_component_review_guidance": [
            _legacy_component_guidance(component, active_claim_id, all_source_refs)
            for component in _REVIEW_COMPONENTS
        ],
        "recommended_actions": _unique([
            "inspect_legacy_refs_for_source_reconstruction_components",
            "record_source_reconstruction_review_result",
            *[str(action) for action in item.get("recommended_actions", []) if str(action)],
        ]),
        "semantic_lossless_proven": False,
        "truth_source": "typed_review_results_legacy_refs_and_source_reconstruction_packet",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _queue_item(queue: dict[str, Any], topic: str) -> dict[str, Any]:
    for item in queue["items"]:
        if item["topic"] == topic:
            return item
    raise ValueError(f"unknown legacy source reconstruction topic: {topic}")


def _refs_by_prefix(refs: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {
        "legacy_candidate": [],
        "legacy_l3_process": [],
        "legacy_l1": [],
        "legacy_source": [],
        "legacy_archive": [],
        "legacy_other": [],
    }
    for ref in _clean_refs(refs):
        prefix = ref.split(":", 1)[0]
        key = prefix if prefix in grouped else "legacy_other"
        grouped[key].append(ref)
    return {key: _unique(values) for key, values in grouped.items() if values}


def _legacy_component_guidance(component: str, claim_id: str, refs: list[str]) -> dict[str, Any]:
    return {
        "component": component,
        "legacy_refs_to_inspect": _legacy_refs_for_component(component, refs),
        "review_decision": "record_passed_needs_revision_or_inconclusive",
        "record_result_cli": (
            f"aitp-v5 source reconstruction-review-result --claim {claim_id} "
            f"--status <passed|needs_revision|inconclusive> --reviewed-component {component} "
            "--basis-ref <legacy-ref-or-typed-record> --summary <source reconstruction review basis>"
        ),
        "can_update_claim_trust": False,
    }


def _review_result_cli(claim_id: str) -> str:
    return (
        f"aitp-v5 source reconstruction-review-result --claim {claim_id} "
        "--status <passed|needs_revision|inconclusive> "
        "--reviewed-component <component> --basis-ref <legacy-ref-or-typed-record> "
        "--summary <source reconstruction review basis>"
    )


def _legacy_refs_for_component(component: str, refs: list[str]) -> list[str]:
    cleaned = _clean_refs(refs)
    if component == "reconstruction_path":
        reconstruction_refs = [ref for ref in cleaned if ref.startswith(_RECONSTRUCTION_REF_PREFIXES)]
        return reconstruction_refs or cleaned
    if component in {"definitions", "assumptions_or_scope", "dependency_graph", "failure_conditions"}:
        focused = [
            ref for ref in cleaned
            if ref.startswith(("legacy_l1:", "legacy_l3_process:", "legacy_candidate:", "legacy_source:"))
        ]
        return focused or cleaned
    if component == "source_locations":
        focused = [ref for ref in cleaned if ref.startswith(("legacy_source:", "legacy_archive:", "legacy_l1:"))]
        return focused or cleaned
    return cleaned


def _clean_refs(values: list[str] | None) -> list[str]:
    return [str(value).strip() for value in values or [] if str(value).strip()]


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
