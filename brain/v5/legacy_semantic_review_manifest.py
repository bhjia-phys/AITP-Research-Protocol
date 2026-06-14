"""Batch manifest for legacy semantic review packets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.legacy_bridge import scan_legacy_topic
from brain.v5.legacy_file_review_scope import (
    build_workspace_file_review_scope_index,
    file_review_scope_for_topic,
)
from brain.v5.legacy_recovery_focus import (
    build_legacy_recovery_focus_index,
    compact_legacy_recovery_focus,
)
from brain.v5.legacy_semantic_review import build_legacy_semantic_review_queue
from brain.v5.legacy_semantic_repair_candidates import (
    failed_validation_result_ids,
    manifest_repair_candidate,
    validation_results_by_id,
)
from brain.v5.markdown import read_md
from brain.v5.models import ClaimRecord, SourceReconstructionReviewResultRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_records


def build_legacy_semantic_review_manifest(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
) -> dict[str, Any]:
    """Build a read-only manifest of per-topic semantic review work."""

    queue = build_legacy_semantic_review_queue(ws, migration_dir=migration_dir)
    migration = str(queue["migration_dir"])
    legacy_root = Path(queue["legacy_root"])
    claims_by_id = {claim.claim_id: claim for claim in list_records(ws.registry_dir("claims"), ClaimRecord)}
    results_by_id = validation_results_by_id(ws)
    source_reviews_by_claim = _group_source_reviews_by_claim(
        list_records(ws.registry_dir("source_reconstruction_reviews"), SourceReconstructionReviewResultRecord)
    )
    file_scope_index = build_workspace_file_review_scope_index(ws)
    recovery_focus_index = build_legacy_recovery_focus_index(
        ws,
        topics=[str(item.get("topic") or "") for item in queue["items"]],
    )
    items = [
        _manifest_item(
            ws,
            migration,
            legacy_root,
            item,
            claims_by_id=claims_by_id,
            validation_results_by_id=results_by_id,
            source_reviews_by_claim=source_reviews_by_claim,
            file_review_scope=file_review_scope_for_topic(file_scope_index, str(item.get("topic") or "")),
            current_recovery_focus=compact_legacy_recovery_focus(
                recovery_focus_index.get(str(item.get("topic") or "")),
                migration_active_claim_id=str(item.get("active_claim_id") or ""),
            ),
        )
        for item in queue["items"]
    ]
    progress = _progress(items)
    return {
        "kind": "legacy_semantic_review_manifest",
        "run_id": queue["run_id"],
        "migration_dir": migration,
        "workspace": queue["workspace"],
        "topic_count": queue["topic_count"],
        "review_item_count": queue["review_item_count"],
        "priority_counts": queue["priority_counts"],
        "review_progress": progress,
        "pending_count": progress["pending"],
        "passed_count": progress["passed"],
        "needs_revision_count": progress["needs_revision"],
        "inconclusive_count": progress["inconclusive"],
        "items": items,
        "next_actions": _next_actions(items),
        "semantic_lossless_proven": False,
        "semantic_review_required": True,
        "truth_source": "migration_manifests_and_typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _manifest_item(
    ws: WorkspacePaths,
    migration_dir: str,
    legacy_root: Path,
    item: dict[str, Any],
    *,
    claims_by_id: dict[str, ClaimRecord],
    validation_results_by_id: dict[str, Any],
    source_reviews_by_claim: dict[str, list[SourceReconstructionReviewResultRecord]],
    file_review_scope: dict[str, Any],
    current_recovery_focus: dict[str, Any],
) -> dict[str, Any]:
    topic = item["topic"]
    status = item["semantic_review_status"].removeprefix("reviewed_")
    if status == item["semantic_review_status"]:
        status = "pending"
    latest_review = item.get("latest_semantic_review", {})
    if not isinstance(latest_review, dict):
        latest_review = {}
    active_claim = claims_by_id.get(str(item.get("active_claim_id") or ""))
    repair_candidates = _repair_candidates(
        ws,
        migration_dir,
        legacy_root,
        item,
        claims_by_id=claims_by_id,
        validation_results_by_id=validation_results_by_id,
    )
    satisfied_review_actions = _satisfied_review_actions(
        legacy_root,
        topic,
        latest_review,
        active_claim,
        source_reviews_by_claim.get(str(item.get("active_claim_id") or ""), []),
    )
    followup_review_actions = _followup_review_actions(satisfied_review_actions)
    packet_cli = (
        f"aitp-v5 --base {ws.base} legacy semantic-review-packet "
        f"--migration-dir {migration_dir} --topic {topic}"
    )
    result_cli = (
        f"aitp-v5 --base {ws.base} legacy semantic-review-result "
        f"--migration-dir {migration_dir} --topic {topic} --status <passed|needs_revision|inconclusive> "
        "--legacy-ref <ref> --summary <summary>"
    )
    return {
        "topic": topic,
        "active_claim_id": item["active_claim_id"],
        "active_claim_statement_present": bool(active_claim and active_claim.statement.strip()),
        "active_claim_scope_present": bool(active_claim and active_claim.scope.strip()),
        "review_status": status,
        "review_priority": item["review_priority"],
        "review_reasons": item["review_reasons"],
        "recommended_actions": item["recommended_actions"],
        "missing_source_components": list(item.get("source_reconstruction", {}).get("missing_components", [])),
        "source_reconstruction": item.get("source_reconstruction", {}),
        "latest_semantic_review": latest_review,
        "satisfied_review_actions": satisfied_review_actions,
        "source_reconstruction_review_refs": _source_reconstruction_review_refs(
            source_reviews_by_claim.get(str(item.get("active_claim_id") or ""), [])
        ),
        "file_review_scope": file_review_scope,
        "current_recovery_focus": current_recovery_focus,
        "followup_review_actions": followup_review_actions,
        "packet_cli": packet_cli,
        "result_cli_template": result_cli,
        "packet_mcp": "aitp_v5_build_legacy_semantic_review_packet",
        "result_mcp": "aitp_v5_record_legacy_semantic_review_result",
        "repair_candidate_count": len(repair_candidates),
        "repair_candidates": repair_candidates,
        "can_update_claim_trust": False,
    }


def _progress(items: list[dict[str, Any]]) -> dict[str, int]:
    progress = {"passed": 0, "inconclusive": 0, "needs_revision": 0, "pending": 0}
    for item in items:
        progress[item["review_status"]] += 1
    return progress


def _next_actions(items: list[dict[str, Any]]) -> list[str]:
    actions = [
        f"review_packet:{item['topic']}"
        for item in items
        if item["review_status"] in {"pending", "needs_revision", "inconclusive"}
    ]
    actions.extend(
        f"followup_review:{item['topic']}:{action}"
        for item in items
        for action in item.get("followup_review_actions", [])
    )
    actions.extend(
        f"repair_candidate:{item['topic']}:{candidate['repair_type']}"
        for item in items
        for candidate in item.get("repair_candidates", [])
    )
    return actions


def _repair_candidates(
    ws: WorkspacePaths,
    migration_dir: str,
    legacy_root: Path,
    item: dict[str, Any],
    *,
    claims_by_id: dict[str, ClaimRecord],
    validation_results_by_id: dict[str, Any],
) -> list[dict[str, Any]]:
    topic = item["topic"]
    latest_review = item.get("latest_semantic_review") if isinstance(item.get("latest_semantic_review"), dict) else {}
    if latest_review.get("status") != "needs_revision":
        return []
    actions = _action_tokens(latest_review.get("remaining_actions", []))
    review_id = str(latest_review.get("review_id") or "")
    candidates: list[dict[str, Any]] = []
    active_claim = claims_by_id.get(str(item.get("active_claim_id") or ""))
    if failed_validation_result_ids(latest_review, validation_results_by_id):
        candidates.append(
            manifest_repair_candidate(
                ws,
                migration_dir,
                topic,
                review_id,
                surface="legacy_semantic_repair_apply",
                command="semantic-repair-apply",
                repair_type="validation_result_revision",
                requires_external_evidence=True,
            )
        )
    if (
        "backfill_active_claim_statement_from_legacy_state_question" in actions
        and active_claim is not None
        and not active_claim.statement.strip()
        and _legacy_state_question(legacy_root, topic)
    ):
        candidates.append(
            manifest_repair_candidate(
                ws,
                migration_dir,
                topic,
                review_id,
                surface="legacy_semantic_repair_apply",
                command="semantic-repair-apply",
                repair_type="claim_statement_backfill",
            )
        )
    missing_components = set(item.get("source_reconstruction", {}).get("missing_components", []))
    if (
        "complete_source_reconstruction" in actions
        and "reconstruction_path" in missing_components
        and _reviewed_reconstruction_refs(latest_review)
    ):
        candidates.append(
            manifest_repair_candidate(
                ws,
                migration_dir,
                topic,
                review_id,
                surface="legacy_source_reconstruction_apply",
                command="source-reconstruction-apply",
                repair_type="reconstruction_path_evidence_backfill",
            )
        )
    return candidates


def _action_tokens(raw_actions: list[str] | None) -> set[str]:
    tokens: set[str] = set()
    for action in raw_actions or []:
        text = str(action).strip()
        if not text:
            continue
        tokens.add(text)
        normalized = " ".join(text.lower().replace("_", " ").split())
        if "backfill" in normalized and "claim statement" in normalized and "research question" in normalized:
            tokens.add("backfill_active_claim_statement_from_legacy_state_question")
        if "l3" in normalized and "distilled claim" in normalized and "claim statement" in normalized:
            tokens.add("backfill_active_claim_statement_from_legacy_l3_distilled_claim")
        if "l1" in normalized and "bounded question" in normalized and "claim statement" in normalized:
            tokens.add("backfill_active_claim_statement_from_legacy_l1_bounded_question")
        if "scope" in normalized and "question contract" in normalized:
            tokens.add("backfill_active_claim_scope_from_legacy_l1_question_contract")
        if "scope" in normalized and "candidate" in normalized and "regime" in normalized:
            tokens.add("backfill_active_claim_scope_from_legacy_candidate_regime")
        if "failure" in normalized and "non success" in normalized:
            tokens.add("backfill_active_claim_failure_mode_from_legacy_l1_non_success_conditions")
        if "failure" in normalized and "legacy review" in normalized:
            tokens.add("backfill_active_claim_failure_mode_from_legacy_review")
        if "source reconstruction" in normalized or "reconstruction path" in normalized:
            tokens.add("complete_source_reconstruction")
    return tokens


def _satisfied_review_actions(
    legacy_root: Path,
    topic: str,
    latest_review: dict[str, Any],
    active_claim: ClaimRecord | None,
    source_reviews: list[SourceReconstructionReviewResultRecord],
) -> list[str]:
    if latest_review.get("status") not in {"needs_revision", "inconclusive"} or active_claim is None:
        return []
    actions = _action_tokens(latest_review.get("remaining_actions", []))
    satisfied: list[str] = []
    if "backfill_active_claim_statement_from_legacy_state_question" in actions and _text_matches(
        active_claim.statement,
        _legacy_state_question(legacy_root, topic),
    ):
        satisfied.append("backfill_active_claim_statement_from_legacy_state_question")
    if "backfill_active_claim_statement_from_legacy_l1_bounded_question" in actions and _text_matches(
        active_claim.statement,
        _reviewed_l1_bounded_question(latest_review),
    ):
        satisfied.append("backfill_active_claim_statement_from_legacy_l1_bounded_question")
    if "backfill_active_claim_statement_from_legacy_l3_distilled_claim" in actions and _text_matches(
        active_claim.statement,
        _reviewed_l3_distilled_claim(latest_review),
    ):
        satisfied.append("backfill_active_claim_statement_from_legacy_l3_distilled_claim")
    if "backfill_active_claim_scope_from_legacy_l1_question_contract" in actions and _text_matches(
        active_claim.scope,
        _reviewed_l1_scope(latest_review),
    ):
        satisfied.append("backfill_active_claim_scope_from_legacy_l1_question_contract")
    if "backfill_active_claim_scope_from_legacy_candidate_regime" in actions and _text_matches(
        active_claim.scope,
        _reviewed_candidate_scope(latest_review),
    ):
        satisfied.append("backfill_active_claim_scope_from_legacy_candidate_regime")
    if "backfill_active_claim_failure_mode_from_legacy_review" in actions and _text_matches(
        active_claim.strongest_failure_mode,
        _reviewed_failure_mode(latest_review),
    ):
        satisfied.append("backfill_active_claim_failure_mode_from_legacy_review")
    if "backfill_active_claim_failure_mode_from_legacy_l1_non_success_conditions" in actions and _text_matches(
        active_claim.strongest_failure_mode,
        _reviewed_l1_non_success_conditions(latest_review),
    ):
        satisfied.append("backfill_active_claim_failure_mode_from_legacy_l1_non_success_conditions")
    if "record_source_reconstruction_review_result" in actions and source_reviews:
        satisfied.append("record_source_reconstruction_review_result")
    return _unique(satisfied)


def _group_source_reviews_by_claim(
    records: list[SourceReconstructionReviewResultRecord],
) -> dict[str, list[SourceReconstructionReviewResultRecord]]:
    grouped: dict[str, list[SourceReconstructionReviewResultRecord]] = {}
    for record in records:
        grouped.setdefault(record.claim_id, []).append(record)
    return grouped


def _source_reconstruction_review_refs(
    records: list[SourceReconstructionReviewResultRecord],
) -> list[str]:
    return [f"source-reconstruction-review:{record.result_id}" for record in records]


def _followup_review_actions(satisfied_review_actions: list[str]) -> list[str]:
    if not satisfied_review_actions:
        return []
    return ["record_followup_semantic_review_result_for_satisfied_actions"]


def _reviewed_reconstruction_refs(latest_review: dict[str, Any]) -> list[str]:
    return [
        ref
        for ref in (str(value).strip() for value in latest_review.get("reviewed_legacy_refs", []))
        if ref.startswith(("legacy_candidate:", "legacy_l3_process:"))
    ]


def _legacy_state_question(legacy_root: Path, topic: str) -> str:
    legacy_topic = legacy_root / topic
    if not (legacy_topic / "state.md").exists():
        return ""
    return scan_legacy_topic(legacy_topic).question


def _reviewed_l1_scope(latest_review: dict[str, Any]) -> str:
    for path in _reviewed_paths(latest_review, prefixes=("legacy_l1:",)):
        frontmatter, body = read_md(path)
        scope = _frontmatter_text(frontmatter.get("scope_boundaries"))
        if scope:
            return scope
        scope = _markdown_section(body, "Scope Boundaries")
        if scope:
            return scope
    return ""


def _reviewed_l1_non_success_conditions(latest_review: dict[str, Any]) -> str:
    for path in _reviewed_paths(latest_review, prefixes=("legacy_l1:",)):
        frontmatter, body = read_md(path)
        failure_mode = _frontmatter_text(frontmatter.get("non_success_conditions"))
        if failure_mode:
            return failure_mode
        failure_mode = _frontmatter_text(frontmatter.get("failure_conditions"))
        if failure_mode:
            return failure_mode
        failure_mode = _markdown_section(body, "Non-Success Conditions")
        if failure_mode:
            return failure_mode
    return ""


def _reviewed_l1_bounded_question(latest_review: dict[str, Any]) -> str:
    for path in _reviewed_paths(latest_review, prefixes=("legacy_l1:",)):
        frontmatter, body = read_md(path)
        bounded_question = _frontmatter_text(frontmatter.get("bounded_question"))
        if bounded_question:
            return bounded_question
        bounded_question = _markdown_section(body, "Bounded Question")
        if bounded_question:
            return bounded_question
    return ""


def _reviewed_l3_distilled_claim(latest_review: dict[str, Any]) -> str:
    for path in _reviewed_paths(latest_review, prefixes=("legacy_l3_process:",)):
        frontmatter, body = read_md(path)
        distilled_claim = _frontmatter_text(frontmatter.get("distilled_claim"))
        if distilled_claim:
            return distilled_claim
        distilled_claim = _markdown_section(body, "Distilled Claim")
        if distilled_claim:
            return distilled_claim
    return ""


def _reviewed_candidate_scope(latest_review: dict[str, Any]) -> str:
    for path in _reviewed_paths(latest_review, prefixes=("legacy_candidate:",)):
        frontmatter, body = read_md(path)
        scope = _frontmatter_text(frontmatter.get("regime_of_validity"))
        if scope:
            return scope
        assumptions = _markdown_section(body, "Assumptions")
        if assumptions:
            return assumptions
    return ""


def _reviewed_failure_mode(latest_review: dict[str, Any]) -> str:
    for path in _reviewed_paths(latest_review, prefixes=("legacy_l4_review:",)):
        frontmatter, body = read_md(path)
        failure_mode = _frontmatter_text(frontmatter.get("devils_advocate"))
        if failure_mode:
            return failure_mode
        failure_mode = _markdown_section(body, "Devil's Advocate")
        if failure_mode:
            return failure_mode
    return ""


def _reviewed_paths(latest_review: dict[str, Any], *, prefixes: tuple[str, ...]) -> list[Path]:
    paths: list[Path] = []
    for ref in latest_review.get("reviewed_legacy_refs", []):
        text = str(ref)
        for prefix in prefixes:
            if text.startswith(prefix):
                path = Path(text.removeprefix(prefix))
                if path.exists():
                    paths.append(path)
    return paths


def _markdown_section(body: str, heading: str) -> str:
    lines = body.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.strip().lower() == f"## {heading}".lower():
            start = index + 1
            break
    if start is None:
        return ""
    selected: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        selected.append(line)
    return _clean_text("\n".join(selected))


def _frontmatter_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        parts = [_frontmatter_text(item) for item in value]
        return _clean_text("; ".join(part for part in parts if part))
    if isinstance(value, dict):
        parts: list[str] = []
        for key, nested in value.items():
            nested_text = _frontmatter_text(nested)
            parts.append(f"{key}: {nested_text}" if nested_text else str(key))
        return _clean_text("; ".join(parts))
    return _clean_text(str(value))


def _text_matches(current: str, expected: str) -> bool:
    current_text = _clean_text(current)
    expected_text = _clean_text(expected)
    return bool(current_text and expected_text and current_text == expected_text)


def _clean_text(value: str) -> str:
    return " ".join(str(value).split())


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
