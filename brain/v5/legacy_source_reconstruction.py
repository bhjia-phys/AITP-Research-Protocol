"""Guarded source-reconstruction repairs derived from legacy semantic reviews."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from brain.v5.evidence import record_evidence
from brain.v5.ids import prefixed_id
from brain.v5.legacy_semantic_review import build_legacy_semantic_review_queue
from brain.v5.legacy_source_reconstruction_models import LegacySourceReconstructionRepairRecord
from brain.v5.legacy_source_reconstruction_review import build_legacy_source_reconstruction_review_packet
from brain.v5.models import EvidenceRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_records, write_record

_RECONSTRUCTION_REF_PREFIXES = ("legacy_candidate:", "legacy_l3_process:")
_REPAIR_TYPE = "reconstruction_path_evidence_backfill"
_REVIEW_COMPONENTS = (
    "definitions",
    "assumptions_or_scope",
    "source_locations",
    "dependency_graph",
    "reconstruction_path",
    "failure_conditions",
)


def build_legacy_source_reconstruction_plan(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
    topic: str,
) -> dict[str, Any]:
    """Plan reconstruction-path evidence backfills without mutating state."""

    queue = build_legacy_semantic_review_queue(ws, migration_dir=migration_dir)
    item = _queue_item(queue, topic)
    latest_review = item.get("latest_semantic_review") if isinstance(item.get("latest_semantic_review"), dict) else {}
    proposed_repairs = _proposed_repairs(item, latest_review)
    return {
        "kind": "legacy_source_reconstruction_plan",
        "run_id": queue["run_id"],
        "migration_dir": queue["migration_dir"],
        "topic": item["topic"],
        "active_claim_id": item["active_claim_id"],
        "repair_status": _repair_status(latest_review, proposed_repairs),
        "latest_semantic_review": latest_review,
        "proposed_repairs": proposed_repairs,
        "can_apply": False,
        "semantic_lossless_proven": False,
        "truth_source": "typed_review_results_and_legacy_refs",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def build_legacy_source_reconstruction_manifest(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
) -> dict[str, Any]:
    """Batch source-reconstruction repair/review triage for a legacy migration."""

    queue = build_legacy_semantic_review_queue(ws, migration_dir=migration_dir)
    items = [
        _manifest_item(ws, queue, item)
        for item in queue["items"]
        if _source_reconstruction_incomplete(item)
    ]
    items.sort(key=lambda item: (_repair_sort_rank(item["repair_status"]), item["topic"], item["active_claim_id"]))
    repair_status_counts = Counter(item["repair_status"] for item in items)
    required_actions = Counter(action for item in items for action in item["required_actions"])
    return {
        "kind": "legacy_source_reconstruction_manifest",
        "run_id": queue["run_id"],
        "migration_dir": queue["migration_dir"],
        "work_item_count": len(items),
        "repair_status_counts": {
            "awaiting_needs_revision_review": repair_status_counts.get("awaiting_needs_revision_review", 0),
            "no_repair_candidates": repair_status_counts.get("no_repair_candidates", 0),
            "proposed_repairs": repair_status_counts.get("proposed_repairs", 0),
        },
        "proposed_repair_count": sum(item["proposed_repair_count"] for item in items),
        "missing_component_counts": _missing_component_counts(items),
        "required_action_counts": dict(sorted(required_actions.items())),
        "items": items,
        "next_actions": [f"legacy_source_reconstruction:{item['topic']}" for item in items],
        "semantic_lossless_proven": False,
        "semantic_review_required": True,
        "truth_source": "typed_review_results_legacy_refs_and_source_reconstruction_audit",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def apply_legacy_source_reconstruction_repair(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
    topic: str,
    repair_type: str,
    review_id: str,
) -> dict[str, Any]:
    """Apply a single guarded reconstruction-path evidence backfill."""

    plan = build_legacy_source_reconstruction_plan(ws, migration_dir=migration_dir, topic=topic)
    latest_review = plan["latest_semantic_review"]
    repair = _matching_repair(plan, repair_type=repair_type)
    if review_id != latest_review.get("review_id"):
        return _apply_payload(
            plan,
            repair_type=repair_type,
            review_id=review_id,
            evidence_id="",
            applied=False,
            required_actions=["match_latest_needs_revision_review_id"],
            basis_refs=_review_basis_refs(latest_review),
            ws=ws,
        )
    if repair is None:
        existing = _existing_reconstruction_path_evidence(ws, plan, latest_review)
        if (
            repair_type == _REPAIR_TYPE
            and existing is not None
            and _latest_review_requests_source_reconstruction(latest_review)
        ):
            return _apply_payload(
                plan,
                repair_type=repair_type,
                review_id=review_id,
                evidence_id=existing.evidence_id,
                applied=True,
                required_actions=[],
                basis_refs=_review_basis_refs(latest_review),
                ws=ws,
            )
        return _apply_payload(
            plan,
            repair_type=repair_type,
            review_id=review_id,
            evidence_id="",
            applied=False,
            required_actions=["select_available_repair"],
            basis_refs=[],
            ws=ws,
        )
    summary = f"Reviewed legacy reconstruction path for {plan['topic']} from {len(repair['source_refs'])} L3/candidate refs."
    evidence = record_evidence(
        ws,
        topic_id=plan["topic"],
        claim_id=plan["active_claim_id"],
        evidence_type=repair["proposed_evidence_type"],
        status=repair["proposed_status"],
        summary=summary,
        supports_outputs=repair["proposed_supports_outputs"],
        source_refs=repair["source_refs"],
        body=_evidence_body(plan, repair, summary),
    )
    return _apply_payload(
        plan,
        repair_type=repair_type,
        review_id=review_id,
        evidence_id=evidence.evidence_id,
        applied=True,
        required_actions=[],
        basis_refs=repair["basis_refs"],
        ws=ws,
    )


def _queue_item(queue: dict[str, Any], topic: str) -> dict[str, Any]:
    for item in queue["items"]:
        if item["topic"] == topic:
            return item
    raise ValueError(f"unknown legacy source reconstruction topic: {topic}")


def _proposed_repairs(item: dict[str, Any], latest_review: dict[str, Any]) -> list[dict[str, Any]]:
    if latest_review.get("status") != "needs_revision":
        return []
    if not _latest_review_requests_source_reconstruction(latest_review):
        return []
    missing_components = set(item.get("source_reconstruction", {}).get("missing_components", []))
    if "reconstruction_path" not in missing_components:
        return []
    source_refs = _reviewed_reconstruction_refs(latest_review)
    if not source_refs:
        return []
    basis_refs = _review_basis_refs(latest_review)
    return [
        {
            "repair_type": _REPAIR_TYPE,
            "target_ref": str(item.get("active_claim_id") or ""),
            "current_missing_component": "reconstruction_path",
            "proposed_evidence_type": "source_reconstruction",
            "proposed_status": "supports",
            "proposed_supports_outputs": ["reconstruction_path"],
            "source_refs": source_refs,
            "basis_refs": basis_refs,
            "mutation_authority": "typed_review_and_apply_separately",
        }
    ]


def _repair_status(latest_review: dict[str, Any], proposed_repairs: list[dict[str, Any]]) -> str:
    if proposed_repairs:
        return "proposed_repairs"
    if latest_review.get("status") != "needs_revision":
        return "awaiting_needs_revision_review"
    return "no_repair_candidates"


def _source_reconstruction_incomplete(item: dict[str, Any]) -> bool:
    source_reconstruction = item.get("source_reconstruction") if isinstance(item.get("source_reconstruction"), dict) else {}
    missing = source_reconstruction.get("missing_components") or []
    return source_reconstruction.get("status") == "incomplete" or bool(missing)


def _manifest_item(ws: WorkspacePaths, queue: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    latest_review = item.get("latest_semantic_review") if isinstance(item.get("latest_semantic_review"), dict) else {}
    source_reconstruction = item.get("source_reconstruction") if isinstance(item.get("source_reconstruction"), dict) else {}
    proposed_repairs = _proposed_repairs(item, latest_review)
    repair_status = _repair_status(latest_review, proposed_repairs)
    proposed_repair_types = _unique([repair["repair_type"] for repair in proposed_repairs])
    return {
        "topic": str(item.get("topic") or ""),
        "active_claim_id": str(item.get("active_claim_id") or ""),
        "latest_review_id": str(latest_review.get("review_id") or ""),
        "latest_review_status": str(latest_review.get("status") or "pending"),
        "source_reconstruction_status": str(source_reconstruction.get("status") or "incomplete"),
        "missing_components": list(source_reconstruction.get("missing_components") or []),
        "source_reconstruction_recommended_actions": list(source_reconstruction.get("recommended_actions") or []),
        "source_refs": list(source_reconstruction.get("source_refs") or []),
        "repair_status": repair_status,
        "proposed_repair_count": len(proposed_repairs),
        "proposed_repair_types": proposed_repair_types,
        "required_actions": _manifest_required_actions(repair_status, proposed_repairs),
        "plan_cli": (
            f"aitp-v5 --base {ws.base} legacy source-reconstruction-plan "
            f"--migration-dir {queue['migration_dir']} --topic {item.get('topic')}"
        ),
        "plan_mcp": "aitp_v5_build_legacy_source_reconstruction_plan",
        "plan_surface": "legacy_source_reconstruction_plan",
        "review_packet_cli": (
            f"aitp-v5 --base {ws.base} legacy source-reconstruction-review "
            f"--migration-dir {queue['migration_dir']} --topic {item.get('topic')}"
        ),
        "review_packet_mcp": "aitp_v5_build_legacy_source_reconstruction_review_packet",
        "review_packet_surface": "legacy_source_reconstruction_review_packet",
        "apply_cli": _apply_cli(ws, queue, item, latest_review, proposed_repair_types),
        "apply_mcp": "aitp_v5_apply_legacy_source_reconstruction_repair",
        "apply_surface": "legacy_source_reconstruction_apply",
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _manifest_required_actions(repair_status: str, proposed_repairs: list[dict[str, Any]]) -> list[str]:
    actions = [
        "inspect_legacy_refs_for_source_reconstruction_components",
        "record_source_reconstruction_review_result",
    ]
    if proposed_repairs:
        actions.extend([
            "review_proposed_source_reconstruction_repair_before_apply",
            "apply_selected_source_reconstruction_repair_with_latest_review_id",
        ])
    elif repair_status == "awaiting_needs_revision_review":
        actions.append("record_needs_revision_review_with_specific_source_reconstruction_basis")
    else:
        actions.append("record_review_basis_or_keep_source_reconstruction_inconclusive")
    return _unique(actions)


def _apply_cli(
    ws: WorkspacePaths,
    queue: dict[str, Any],
    item: dict[str, Any],
    latest_review: dict[str, Any],
    repair_types: list[str],
) -> str:
    if not repair_types:
        return ""
    return (
        f"aitp-v5 --base {ws.base} legacy source-reconstruction-apply "
        f"--migration-dir {queue['migration_dir']} --topic {item.get('topic')} "
        f"--repair-type {repair_types[0]} --review-id {latest_review.get('review_id')}"
    )


def _missing_component_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {component: 0 for component in _REVIEW_COMPONENTS}
    for item in items:
        for component in item["missing_components"]:
            if component in counts:
                counts[component] += 1
    return counts


def _repair_sort_rank(status: str) -> int:
    return {"proposed_repairs": 0, "no_repair_candidates": 1, "awaiting_needs_revision_review": 2}.get(status, 3)


def _source_reconstruction_action_tokens(raw_actions: list[str] | None) -> set[str]:
    tokens: set[str] = set()
    for action in raw_actions or []:
        text = str(action).strip()
        if not text:
            continue
        tokens.add(text)
        normalized = " ".join(text.lower().replace("_", " ").split())
        if "source reconstruction" in normalized or "reconstruction path" in normalized:
            tokens.add("complete_source_reconstruction")
    return tokens


def _latest_review_requests_source_reconstruction(latest_review: dict[str, Any]) -> bool:
    return (
        latest_review.get("status") == "needs_revision"
        and "complete_source_reconstruction"
        in _source_reconstruction_action_tokens(latest_review.get("remaining_actions", []))
    )


def _reviewed_reconstruction_refs(latest_review: dict[str, Any]) -> list[str]:
    return [
        ref
        for ref in _clean_refs(latest_review.get("reviewed_legacy_refs", []))
        if ref.startswith(_RECONSTRUCTION_REF_PREFIXES)
    ]


def _review_basis_refs(latest_review: dict[str, Any]) -> list[str]:
    return _unique([*_reviewed_reconstruction_refs(latest_review), str(latest_review.get("review_id") or "")])


def _existing_reconstruction_path_evidence(
    ws: WorkspacePaths,
    plan: dict[str, Any],
    latest_review: dict[str, Any],
) -> EvidenceRecord | None:
    reviewed_refs = set(_reviewed_reconstruction_refs(latest_review))
    for record in list_records(ws.registry_dir("evidence"), EvidenceRecord):
        if record.claim_id != plan["active_claim_id"]:
            continue
        if record.evidence_type != "source_reconstruction":
            continue
        if record.status in {"failed", "refutes", "invalid"}:
            continue
        if "reconstruction_path" not in set(record.supports_outputs):
            continue
        if reviewed_refs and not reviewed_refs.intersection(set(record.source_refs)):
            continue
        return record
    return None


def _matching_repair(plan: dict[str, Any], *, repair_type: str) -> dict[str, Any] | None:
    for repair in plan["proposed_repairs"]:
        if repair["repair_type"] == repair_type:
            return repair
    return None


def _apply_payload(
    plan: dict[str, Any],
    *,
    repair_type: str,
    review_id: str,
    evidence_id: str,
    applied: bool,
    required_actions: list[str],
    basis_refs: list[str],
    ws: WorkspacePaths,
) -> dict[str, Any]:
    repair_id = prefixed_id(
        "legacy-source-repair",
        f"{plan['run_id']}:{plan['topic']}:{plan['active_claim_id']}:{repair_type}:{review_id}:{evidence_id}:{applied}",
        max_slug=40,
    )
    record = LegacySourceReconstructionRepairRecord(
        repair_id=repair_id,
        migration_run_id=plan["run_id"],
        migration_dir=plan["migration_dir"],
        topic=plan["topic"],
        active_claim_id=plan["active_claim_id"],
        review_id=review_id,
        repair_type=repair_type,
        evidence_id=evidence_id,
        basis_refs=list(basis_refs),
        applied=applied,
        required_actions=list(required_actions),
    )
    write_record(
        ws.registry_dir("legacy_source_reconstruction_repairs") / f"{repair_id}.md",
        record,
        body=(
            f"# Legacy Source Reconstruction Repair: {plan['topic']}\n\n"
            f"**Applied:** {applied}\n\n{repair_type}\n"
        ),
    )
    return {
        "kind": "legacy_source_reconstruction_apply",
        "repair_id": repair_id,
        "run_id": plan["run_id"],
        "migration_dir": plan["migration_dir"],
        "topic": plan["topic"],
        "active_claim_id": plan["active_claim_id"],
        "review_id": review_id,
        "repair_type": repair_type,
        "evidence_id": evidence_id,
        "basis_refs": list(basis_refs),
        "applied": applied,
        "required_actions": list(required_actions),
        "semantic_lossless_proven": False,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": applied,
        "can_update_claim_trust": False,
    }


def _evidence_body(plan: dict[str, Any], repair: dict[str, Any], summary: str) -> str:
    lines = [
        "# Legacy Source Reconstruction Evidence",
        "",
        summary,
        "",
        "## Reviewed Legacy Reconstruction Refs",
        "",
    ]
    lines.extend(f"- `{ref}`" for ref in repair["source_refs"])
    lines.extend([
        "",
        "## Review Basis",
        "",
    ])
    lines.extend(f"- `{ref}`" for ref in repair["basis_refs"])
    lines.extend([
        "",
        "## Trust Boundary",
        "",
        "This evidence records a reconstruction-path pointer only; it does not prove semantic losslessness or update claim trust.",
    ])
    return "\n".join(lines) + "\n"


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
