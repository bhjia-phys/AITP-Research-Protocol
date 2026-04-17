from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from .graph_analysis_tools import empty_graph_analysis
from .l1_source_intake_support import (
    l1_assumption_depth_summary_lines,
    l1_concept_graph_summary_lines,
    l1_contradiction_summary_lines,
    l1_notation_tension_lines,
    l1_reading_depth_limit_lines,
)

_ROUTE_MATCH_STOPWORDS = {
    "active",
    "branch",
    "buffer",
    "candidate",
    "current",
    "deferred",
    "follow",
    "followup",
    "hypothesis",
    "parked",
    "prior",
    "route",
    "subtopic",
    "topic",
    "watch",
}


def empty_l1_source_intake() -> dict[str, Any]:
    return {
        "source_count": 0,
        "assumption_rows": [],
        "regime_rows": [],
        "reading_depth_rows": [],
        "method_specificity_rows": [],
        "notation_rows": [],
        "contradiction_candidates": [],
        "notation_tension_candidates": [],
        "concept_graph": {
            "nodes": [],
            "edges": [],
            "hyperedges": [],
            "communities": [],
            "god_nodes": [],
        },
    }


def empty_source_intelligence(*, topic_slug: str) -> dict[str, Any]:
    return {
        "topic_slug": topic_slug,
        "summary": "No source-intelligence signals are currently recorded for this topic.",
        "canonical_source_ids": [],
        "cross_topic_match_count": 0,
        "fidelity_rows": [],
        "fidelity_summary": {
            "source_count": 0,
            "counts_by_tier": {},
            "strongest_tier": "unknown",
            "weakest_tier": "unknown",
        },
        "relevance_rows": [],
        "relevance_summary": {
            "source_count": 0,
            "counts_by_tier": {},
            "strongest_tier": "irrelevant",
            "weakest_tier": "irrelevant",
            "role_label_counts": {},
        },
        "citation_edges": [],
        "source_neighbors": [],
        "neighbor_signal_count": 0,
        "path": _truth_runtime_ref(topic_slug, "source_intelligence.json"),
        "note_path": _truth_runtime_ref(topic_slug, "source_intelligence.md"),
    }


def _zero_graph_diff() -> dict[str, Any]:
    return {
        "added": {
            "node_count": 0,
            "node_labels": [],
            "edge_count": 0,
            "edge_relations": [],
            "god_node_count": 0,
            "god_node_labels": [],
        },
        "removed": {
            "node_count": 0,
            "node_labels": [],
            "edge_count": 0,
            "edge_relations": [],
            "god_node_count": 0,
            "god_node_labels": [],
        },
    }


def _truth_runtime_ref(topic_slug: str, *parts: str) -> str:
    if not topic_slug:
        return ""
    return (Path("topics") / topic_slug / "runtime" / Path(*parts)).as_posix()


def _truth_layer_ref(topic_slug: str, layer_name: str, *parts: str) -> str:
    if not topic_slug:
        return ""
    return (Path("topics") / topic_slug / layer_name / Path(*parts)).as_posix()


def _topic_path_context(surface_root: Path) -> tuple[Path, Path, Path, str]:
    resolved = surface_root.expanduser().resolve()
    parts = resolved.parts
    if resolved.name == "runtime" and len(parts) >= 3 and parts[-3] == "topics":
        topic_folder_root = resolved.parent
        return topic_folder_root.parents[1], topic_folder_root, resolved, topic_folder_root.name
    if len(parts) >= 3 and parts[-3] == "runtime" and parts[-2] == "topics":
        return resolved.parents[2], resolved, resolved, resolved.name
    topic_slug = resolved.name
    return resolved.parents[2], resolved, resolved, topic_slug


def empty_l1_vault(*, topic_slug: str) -> dict[str, Any]:
    root = _truth_layer_ref(topic_slug, "L1", "vault")
    return {
        "vault_version": 1,
        "status": "absent",
        "topic_slug": topic_slug,
        "title": "",
        "authority_level": "non_authoritative_compiled_l1",
        "protocol_path": "intake/L1_VAULT_PROTOCOL.md",
        "root_path": root,
        "raw": {
            "manifest_path": f"{root}/raw/source-manifest.json",
            "note_path": f"{root}/raw/source-manifest.md",
            "source_count": 0,
        },
        "wiki": {
            "schema_path": f"{root}/wiki/schema.md",
            "home_page_path": f"{root}/wiki/home.md",
            "page_count": 0,
            "page_paths": [],
        },
        "output": {
            "digest_path": f"{root}/output/current-query.json",
            "digest_note_path": f"{root}/output/current-query.md",
            "flowback_log_path": f"{root}/output/flowback.jsonl",
            "flowback_note_path": f"{root}/output/flowback.md",
            "flowback_entry_count": 0,
        },
        "compatibility_refs": [],
    }


def _string_list(values: Any) -> list[str]:
    if isinstance(values, (str, bytes)):
        values = [values]
    if not isinstance(values, list):
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in values:
        text = str(raw or "").strip()
        if text and text not in seen:
            seen.add(text)
            normalized.append(text)
    return normalized


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _relativize_path(path: Path, *, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _match_tokens(*values: Any) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip().lower()
        if not text:
            continue
        for raw_token in re.split(r"[^a-z0-9]+", text):
            token = raw_token.strip()
            if len(token) < 3 or token in _ROUTE_MATCH_STOPWORDS or token in seen:
                continue
            seen.add(token)
            tokens.append(token)
    return tokens


def _best_unique_route_match(
    hypothesis: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    text_builder: Callable[[dict[str, Any]], str],
) -> dict[str, Any] | None:
    if not rows:
        return None
    if len(rows) == 1:
        return rows[0]
    tokens = _match_tokens(
        hypothesis.get("hypothesis_id"),
        hypothesis.get("label"),
        hypothesis.get("summary"),
        hypothesis.get("route_target_summary"),
    )
    if not tokens:
        return None
    scores: list[int] = []
    for row in rows:
        haystack = text_builder(row)
        scores.append(sum(1 for token in tokens if token in haystack))
    best_score = max(scores)
    if best_score <= 0 or scores.count(best_score) != 1:
        return None
    return rows[scores.index(best_score)]


def _match_hypotheses_to_rows(
    hypotheses: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    *,
    text_builder: Callable[[dict[str, Any]], str],
) -> dict[str, dict[str, Any]]:
    matches: dict[str, dict[str, Any]] = {}
    remaining = list(rows)
    for hypothesis in hypotheses:
        match = _best_unique_route_match(hypothesis, remaining, text_builder=text_builder)
        if match is None:
            continue
        hypothesis_id = str(hypothesis.get("hypothesis_id") or "").strip()
        if not hypothesis_id:
            continue
        matches[hypothesis_id] = match
        remaining = [row for row in remaining if row is not match]
    if len(hypotheses) == 1 and len(rows) == 1:
        hypothesis_id = str(hypotheses[0].get("hypothesis_id") or "").strip()
        if hypothesis_id and hypothesis_id not in matches:
            matches[hypothesis_id] = rows[0]
    return matches


def _buffer_reactivation_context(runtime_surface_root: Path) -> tuple[set[str], str, set[str]]:
    kernel_root, _, runtime_root, topic_slug = _topic_path_context(runtime_surface_root)
    source_index_path = kernel_root / "topics" / topic_slug / "L0" / "source_index.jsonl"
    if not source_index_path.exists():
        source_index_path = kernel_root / "source-layer" / "topics" / topic_slug / "source_index.jsonl"
    source_rows = _read_jsonl(source_index_path)
    source_ids = {
        str(row.get("source_id") or "").strip()
        for row in source_rows
        if str(row.get("source_id") or "").strip()
    }
    source_text = " ".join(
        _string_list(
            [str(row.get("title") or "") for row in source_rows]
            + [str(row.get("summary") or "") for row in source_rows]
        )
    ).lower()
    child_topics = {
        str(row.get("child_topic_slug") or "").strip()
        for row in _read_jsonl(runtime_root / "followup_subtopics.jsonl")
        if str(row.get("child_topic_slug") or "").strip()
    }
    return source_ids, source_text, child_topics


def _buffer_entry_ready_for_reactivation(
    entry: dict[str, Any],
    *,
    source_ids: set[str],
    source_text: str,
    child_topics: set[str],
) -> bool:
    conditions = entry.get("reactivation_conditions") or {}
    source_id_rules = {
        str(value).strip()
        for value in (conditions.get("source_ids_any") or [])
        if str(value).strip()
    }
    if source_id_rules and source_ids.intersection(source_id_rules):
        return True
    text_rules = [
        str(value).strip().lower()
        for value in (conditions.get("text_contains_any") or [])
        if str(value).strip()
    ]
    if text_rules and any(rule in source_text for rule in text_rules):
        return True
    child_topic_rules = {
        str(value).strip()
        for value in (conditions.get("child_topics_any") or [])
        if str(value).strip()
    }
    if child_topic_rules and child_topics.intersection(child_topic_rules):
        return True
    return not source_id_rules and not text_rules and not child_topic_rules


def _reactivation_condition_summary(entry: dict[str, Any]) -> str:
    conditions = entry.get("reactivation_conditions") or {}
    parts: list[str] = []
    source_ids_any = _string_list(conditions.get("source_ids_any") or [])
    text_contains_any = _string_list(conditions.get("text_contains_any") or [])
    child_topics_any = _string_list(conditions.get("child_topics_any") or [])
    if source_ids_any:
        parts.append(f"source ids any: {', '.join(source_ids_any)}")
    if text_contains_any:
        parts.append(f"text contains any: {', '.join(text_contains_any)}")
    if child_topics_any:
        parts.append(f"child topics any: {', '.join(child_topics_any)}")
    if not parts:
        return "No explicit reactivation conditions are declared."
    return "; ".join(parts)


def _followup_return_packet_path(runtime_surface_root: Path, row: dict[str, Any]) -> Path | None:
    explicit = str(row.get("return_packet_path") or "").strip()
    if explicit:
        return Path(explicit)
    child_topic_slug = str(row.get("child_topic_slug") or "").strip()
    if not child_topic_slug:
        return None
    _, topic_folder_root, _, _ = _topic_path_context(runtime_surface_root)
    return topic_folder_root.parent / child_topic_slug / "followup_return_packet.json"


def _followup_condition_summary(row: dict[str, Any], packet: dict[str, Any] | None) -> str:
    if packet:
        parts: list[str] = []
        expected_return_route = str(packet.get("expected_return_route") or "").strip()
        acceptable_shapes = _string_list(packet.get("acceptable_return_shapes") or [])
        reentry_targets = _string_list(packet.get("reentry_targets") or row.get("reentry_targets") or [])
        if expected_return_route:
            parts.append(f"expected return route: {expected_return_route}")
        if acceptable_shapes:
            parts.append(f"acceptable return shapes: {', '.join(acceptable_shapes)}")
        if reentry_targets:
            parts.append(f"reentry targets: {', '.join(reentry_targets)}")
        if parts:
            return "; ".join(parts)
    query = str(row.get("query") or "").strip()
    if query:
        return f"Await child-topic return for `{query}` before parent reintegration."
    return "No explicit follow-up return packet is currently recorded."


def _followup_return_status(packet: dict[str, Any] | None, row: dict[str, Any]) -> str:
    packet_status = str((packet or {}).get("return_status") or "").strip()
    row_status = str(row.get("status") or "").strip()
    normalized_status = packet_status or row_status
    unresolved_statuses = set(
        _string_list((packet or {}).get("unresolved_return_statuses") or [])
    ) or {"pending_reentry", "returned_with_gap", "returned_unresolved"}
    if normalized_status in {"recovered_units", "resolved_gap_update"}:
        return "reentry_ready"
    if normalized_status in unresolved_statuses and normalized_status != "pending_reentry":
        return normalized_status
    if normalized_status == "reintegrated":
        return "reintegrated"
    if normalized_status:
        return "waiting"
    return "missing_contract"


def _route_reentry_ready_count(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if str(row.get("reentry_status") or "").strip() == "reentry_ready")


def _buffer_entry_match_text(row: dict[str, Any]) -> str:
    return " ".join(
        str(value or "").strip().lower()
        for value in (
            row.get("entry_id"),
            row.get("source_candidate_id") or row.get("candidate_id"),
            row.get("title"),
            row.get("summary"),
            row.get("reason"),
            row.get("notes"),
        )
        if str(value or "").strip()
    )


def _followup_row_match_text(row: dict[str, Any]) -> str:
    return " ".join(
        str(value or "").strip().lower()
        for value in (
            row.get("child_topic_slug"),
            row.get("query"),
            row.get("source_id"),
            row.get("arxiv_id"),
            row.get("status"),
        )
        if str(value or "").strip()
    )


def build_route_reentry_payload(
    *,
    topic_slug: str,
    competing_hypotheses: list[dict[str, Any]],
    topic_root: Path,
) -> dict[str, Any]:
    kernel_root, _, runtime_root, _ = _topic_path_context(topic_root)
    deferred_hypotheses = hypotheses_for_route(competing_hypotheses, route_kind="deferred_buffer")
    followup_hypotheses = hypotheses_for_route(competing_hypotheses, route_kind="followup_subtopic")

    deferred_buffer = _read_json(runtime_root / "deferred_candidates.json") or {}
    deferred_entries = [
        row
        for row in (deferred_buffer.get("entries") or [])
        if isinstance(row, dict)
    ]
    deferred_matches = _match_hypotheses_to_rows(
        deferred_hypotheses,
        deferred_entries,
        text_builder=_buffer_entry_match_text,
    )
    source_ids, source_text, child_topics = _buffer_reactivation_context(runtime_root)
    deferred_routes: list[dict[str, Any]] = []
    for hypothesis in deferred_hypotheses:
        hypothesis_id = str(hypothesis.get("hypothesis_id") or "").strip()
        entry = deferred_matches.get(hypothesis_id)
        support_ref = _relativize_path(runtime_root / "deferred_candidates.json", root=kernel_root)
        if entry is None:
            deferred_routes.append(
                {
                    "hypothesis_id": hypothesis_id,
                    "label": str(hypothesis.get("label") or ""),
                    "status": str(hypothesis.get("status") or ""),
                    "route_kind": "deferred_buffer",
                    "reentry_status": "missing_contract",
                    "linked_record_id": "",
                    "reentry_summary": f"No uniquely matched deferred-buffer entry is recorded for `{hypothesis.get('label') or hypothesis_id}` yet.",
                    "condition_summary": "No durable deferred-buffer contract is linked to this parked hypothesis.",
                    "target_ref": str(hypothesis.get("route_target_ref") or ""),
                    "support_ref": support_ref,
                }
            )
            continue
        reentry_status = str(entry.get("status") or "buffered").strip() or "buffered"
        if reentry_status == "buffered":
            if _buffer_entry_ready_for_reactivation(
                entry,
                source_ids=source_ids,
                source_text=source_text,
                child_topics=child_topics,
            ):
                reentry_status = "reentry_ready"
            else:
                reentry_status = "waiting"
        reactivation_candidate = entry.get("reactivation_candidate") or {}
        if reentry_status == "reentry_ready":
            reactivation_candidate_id = str(reactivation_candidate.get("candidate_id") or "").strip()
            if reactivation_candidate_id:
                reentry_summary = (
                    f"`{hypothesis.get('label') or hypothesis_id}` is re-entry-ready as `{reactivation_candidate_id}`."
                )
            else:
                reentry_summary = (
                    f"`{hypothesis.get('label') or hypothesis_id}` is re-entry-ready, but no explicit reactivation candidate is declared."
                )
        elif reentry_status == "reactivated":
            reentry_summary = f"`{hypothesis.get('label') or hypothesis_id}` has already been marked reactivated in the deferred buffer."
        elif reentry_status == "dismissed":
            reentry_summary = f"`{hypothesis.get('label') or hypothesis_id}` has been dismissed from the deferred buffer."
        else:
            reentry_summary = f"`{hypothesis.get('label') or hypothesis_id}` is still waiting in the deferred buffer."
        deferred_routes.append(
            {
                "hypothesis_id": hypothesis_id,
                "label": str(hypothesis.get("label") or ""),
                "status": str(hypothesis.get("status") or ""),
                "route_kind": "deferred_buffer",
                "reentry_status": reentry_status,
                "linked_record_id": str(entry.get("entry_id") or ""),
                "reentry_summary": reentry_summary,
                "condition_summary": _reactivation_condition_summary(entry),
                "target_ref": str(hypothesis.get("route_target_ref") or ""),
                "support_ref": support_ref,
            }
        )

    followup_rows = _read_jsonl(runtime_root / "followup_subtopics.jsonl")
    followup_matches = _match_hypotheses_to_rows(
        followup_hypotheses,
        followup_rows,
        text_builder=_followup_row_match_text,
    )
    followup_routes: list[dict[str, Any]] = []
    for hypothesis in followup_hypotheses:
        hypothesis_id = str(hypothesis.get("hypothesis_id") or "").strip()
        row = followup_matches.get(hypothesis_id)
        if row is None:
            followup_routes.append(
                {
                    "hypothesis_id": hypothesis_id,
                    "label": str(hypothesis.get("label") or ""),
                    "status": str(hypothesis.get("status") or ""),
                    "route_kind": "followup_subtopic",
                    "reentry_status": "missing_contract",
                    "linked_record_id": "",
                    "reentry_summary": f"No uniquely matched follow-up child route is recorded for `{hypothesis.get('label') or hypothesis_id}` yet.",
                    "condition_summary": "No durable follow-up return packet is linked to this parked hypothesis.",
                    "target_ref": str(hypothesis.get("route_target_ref") or ""),
                    "support_ref": str(hypothesis.get("route_target_ref") or ""),
                }
            )
            continue
        packet_path = _followup_return_packet_path(runtime_root, row)
        packet = _read_json(packet_path) if packet_path is not None else None
        reentry_status = _followup_return_status(packet, row)
        child_topic_slug = str(row.get("child_topic_slug") or "").strip()
        if reentry_status == "reentry_ready":
            reentry_summary = (
                str((packet or {}).get("return_summary") or "").strip()
                or f"`{child_topic_slug or hypothesis.get('label') or hypothesis_id}` has returned and is ready for parent-topic reintegration."
            )
        elif reentry_status in {"returned_with_gap", "returned_unresolved"}:
            reentry_summary = (
                str((packet or {}).get("return_summary") or "").strip()
                or f"`{child_topic_slug or hypothesis.get('label') or hypothesis_id}` returned with unresolved work that still needs parent-side writeback."
            )
        elif reentry_status == "reintegrated":
            reentry_summary = f"`{child_topic_slug or hypothesis.get('label') or hypothesis_id}` is already marked reintegrated."
        elif reentry_status == "missing_contract":
            reentry_summary = f"`{child_topic_slug or hypothesis.get('label') or hypothesis_id}` is missing a durable follow-up return packet."
        else:
            reentry_summary = f"`{child_topic_slug or hypothesis.get('label') or hypothesis_id}` is still waiting to return bounded follow-up results."
        followup_routes.append(
            {
                "hypothesis_id": hypothesis_id,
                "label": str(hypothesis.get("label") or ""),
                "status": str(hypothesis.get("status") or ""),
                "route_kind": "followup_subtopic",
                "reentry_status": reentry_status,
                "linked_record_id": child_topic_slug,
                "reentry_summary": reentry_summary,
                "condition_summary": _followup_condition_summary(row, packet),
                "target_ref": str(hypothesis.get("route_target_ref") or ""),
                "support_ref": _relativize_path(packet_path, root=kernel_root) if packet_path is not None else str(hypothesis.get("route_target_ref") or ""),
            }
        )

    all_rows = deferred_routes + followup_routes
    return {
        "reentry_ready_count": _route_reentry_ready_count(all_rows),
        "deferred_routes": deferred_routes,
        "followup_routes": followup_routes,
    }


def build_route_handoff_payload(
    *,
    topic_slug: str,
    competing_hypotheses: list[dict[str, Any]],
    route_activation: dict[str, Any],
    route_reentry: dict[str, Any],
) -> dict[str, Any]:
    del topic_slug
    active_local_hypothesis_id = str(route_activation.get("active_local_hypothesis_id") or "")
    active_local_action_summary = str(route_activation.get("active_local_action_summary") or "").strip()
    active_local_action_ref = str(route_activation.get("active_local_action_ref") or "").strip()

    parked_hypotheses = [
        row
        for row in competing_hypotheses
        if str(row.get("route_kind") or "").strip() in {"deferred_buffer", "followup_subtopic"}
    ]
    route_reentry_index = {
        str(row.get("hypothesis_id") or "").strip(): row
        for row in (route_reentry.get("deferred_routes") or []) + (route_reentry.get("followup_routes") or [])
        if isinstance(row, dict) and str(row.get("hypothesis_id") or "").strip()
    }
    ordered_reentry_rows = [
        route_reentry_index[hypothesis_id]
        for hypothesis_id in [str(row.get("hypothesis_id") or "").strip() for row in parked_hypotheses]
        if hypothesis_id in route_reentry_index
    ]
    ready_rows = [
        row
        for row in ordered_reentry_rows
        if str(row.get("reentry_status") or "").strip() == "reentry_ready"
    ]
    primary_candidate = ready_rows[0] if ready_rows else None
    primary_candidate_id = str((primary_candidate or {}).get("hypothesis_id") or "")
    primary_candidate_label = str((primary_candidate or {}).get("label") or primary_candidate_id)

    handoff_candidates: list[dict[str, Any]] = []
    keep_parked_routes: list[dict[str, Any]] = []
    for row in ordered_reentry_rows:
        hypothesis_id = str(row.get("hypothesis_id") or "").strip()
        route_kind = str(row.get("route_kind") or "").strip()
        reentry_status = str(row.get("reentry_status") or "").strip()
        base_payload = {
            "hypothesis_id": hypothesis_id,
            "label": str(row.get("label") or ""),
            "status": str(row.get("status") or ""),
            "route_kind": route_kind,
            "reentry_status": reentry_status,
            "condition_summary": str(row.get("condition_summary") or ""),
            "target_ref": str(row.get("target_ref") or ""),
            "support_ref": str(row.get("support_ref") or ""),
        }
        if hypothesis_id and hypothesis_id == primary_candidate_id:
            handoff_summary = (
                f"`{primary_candidate_label}` is the bounded next parked-route handoff candidate once the current local action yields."
            )
            handoff_candidates.append(
                {
                    **base_payload,
                    "handoff_status": "handoff_candidate",
                    "handoff_summary": handoff_summary,
                }
            )
            continue
        if reentry_status == "reentry_ready" and primary_candidate_id:
            handoff_summary = (
                f"`{row.get('label') or hypothesis_id}` is re-entry-ready but remains parked because `{primary_candidate_label}` already occupies the bounded handoff lane."
            )
        else:
            handoff_summary = (
                f"`{row.get('label') or hypothesis_id}` remains parked because its re-entry status is `{reentry_status or 'waiting'}`."
            )
        keep_parked_routes.append(
            {
                **base_payload,
                "handoff_status": "keep_parked",
                "handoff_summary": handoff_summary,
            }
        )

    return {
        "active_local_hypothesis_id": active_local_hypothesis_id,
        "active_local_action_summary": active_local_action_summary,
        "active_local_action_ref": active_local_action_ref,
        "primary_handoff_candidate_id": primary_candidate_id,
        "handoff_candidate_count": len(handoff_candidates),
        "handoff_candidates": handoff_candidates,
        "keep_parked_routes": keep_parked_routes,
    }


def build_route_choice_payload(
    *,
    topic_slug: str,
    topic_status_explainability: dict[str, Any] | None,
    route_activation: dict[str, Any],
    route_handoff: dict[str, Any],
) -> dict[str, Any]:
    del topic_slug
    explainability = topic_status_explainability or {}
    current_route_choice = explainability.get("current_route_choice") or {}
    active_local_hypothesis_id = str(route_activation.get("active_local_hypothesis_id") or "")
    active_local_action_summary = str(route_activation.get("active_local_action_summary") or "").strip()
    active_local_action_ref = str(route_activation.get("active_local_action_ref") or "").strip()
    current_route_choice_ref = str(current_route_choice.get("next_action_decision_note_path") or active_local_action_ref or "").strip()
    primary_handoff_candidate = None
    for row in route_handoff.get("handoff_candidates") or []:
        if isinstance(row, dict):
            primary_handoff_candidate = row
            break
    primary_handoff_candidate_id = str(route_handoff.get("primary_handoff_candidate_id") or "")

    stay_local_option = {
        "hypothesis_id": active_local_hypothesis_id,
        "option_kind": "stay_local",
        "option_summary": (
            f"Stay on `{active_local_hypothesis_id}` while the current bounded action remains active."
            if active_local_hypothesis_id
            else "No active local hypothesis is currently declared."
        ),
        "target_ref": active_local_action_ref,
    }
    yield_to_handoff_option = {
        "hypothesis_id": primary_handoff_candidate_id,
        "option_kind": "yield_to_handoff",
        "option_summary": (
            str((primary_handoff_candidate or {}).get("handoff_summary") or "").strip()
            or (
                f"Yield to `{primary_handoff_candidate_id}` once the current local route finishes its bounded action."
                if primary_handoff_candidate_id
                else "No handoff candidate is currently available."
            )
        ),
        "target_ref": str((primary_handoff_candidate or {}).get("target_ref") or ""),
    }

    if active_local_hypothesis_id:
        choice_status = "stay_local"
        choice_summary = (
            f"Stay on `{active_local_hypothesis_id}` for the current bounded step."
            + (
                f" `{primary_handoff_candidate_id}` remains the next parked-route handoff candidate."
                if primary_handoff_candidate_id
                else ""
            )
        )
    elif primary_handoff_candidate_id:
        choice_status = "yield_to_handoff"
        choice_summary = f"Yield to `{primary_handoff_candidate_id}` because no active local hypothesis is currently declared."
    else:
        choice_status = "no_choice"
        choice_summary = "No bounded route choice is currently available."

    return {
        "choice_status": choice_status,
        "choice_summary": choice_summary,
        "active_local_hypothesis_id": active_local_hypothesis_id,
        "primary_handoff_candidate_id": primary_handoff_candidate_id,
        "current_route_choice_ref": current_route_choice_ref,
        "stay_local_option": stay_local_option,
        "yield_to_handoff_option": yield_to_handoff_option,
    }


def build_route_transition_gate_payload(
    *,
    topic_slug: str,
    route_choice: dict[str, Any],
    operator_checkpoint: dict[str, Any] | None,
) -> dict[str, Any]:
    del topic_slug
    route_choice = route_choice or {}
    operator_checkpoint = operator_checkpoint or {}
    choice_status = str(route_choice.get("choice_status") or "").strip()
    checkpoint_status = str(operator_checkpoint.get("status") or "").strip()
    active_local_hypothesis_id = str(route_choice.get("active_local_hypothesis_id") or "").strip()
    primary_handoff_candidate_id = str(route_choice.get("primary_handoff_candidate_id") or "").strip()
    current_route_choice_ref = str(route_choice.get("current_route_choice_ref") or "").strip()
    stay_local_option = route_choice.get("stay_local_option") or {}
    yield_to_handoff_option = route_choice.get("yield_to_handoff_option") or {}
    transition_target_ref = str(yield_to_handoff_option.get("target_ref") or "").strip()
    checkpoint_note_path = str(
        operator_checkpoint.get("note_path") or operator_checkpoint.get("path") or ""
    ).strip()

    if primary_handoff_candidate_id and checkpoint_status == "requested":
        transition_status = "checkpoint_required"
        gate_kind = "operator_checkpoint"
        gate_artifact_ref = checkpoint_note_path
        transition_summary = (
            f"Yielding to `{primary_handoff_candidate_id}` requires resolving the active operator checkpoint first."
        )
    elif primary_handoff_candidate_id and choice_status == "yield_to_handoff":
        transition_status = "available"
        gate_kind = "handoff_candidate_ready"
        gate_artifact_ref = transition_target_ref or current_route_choice_ref
        transition_summary = (
            f"Yielding to `{primary_handoff_candidate_id}` is currently available on the bounded route surface."
        )
    elif primary_handoff_candidate_id:
        transition_status = "blocked"
        gate_kind = "current_route_choice"
        gate_artifact_ref = current_route_choice_ref or str(stay_local_option.get("target_ref") or "").strip()
        transition_summary = (
            f"Yielding to `{primary_handoff_candidate_id}` is currently blocked because the bounded route choice stays local"
            + (f" on `{active_local_hypothesis_id}`." if active_local_hypothesis_id else ".")
        )
    else:
        transition_status = "blocked"
        gate_kind = "no_handoff_candidate"
        gate_artifact_ref = current_route_choice_ref or str(stay_local_option.get("target_ref") or "").strip()
        transition_summary = "No bounded handoff candidate is currently available, so route transition stays blocked."

    return {
        "transition_status": transition_status,
        "choice_status": choice_status,
        "checkpoint_status": checkpoint_status or "none",
        "active_local_hypothesis_id": active_local_hypothesis_id,
        "primary_handoff_candidate_id": primary_handoff_candidate_id,
        "gate_kind": gate_kind,
        "gate_artifact_ref": gate_artifact_ref,
        "transition_target_ref": transition_target_ref,
        "transition_summary": transition_summary,
    }


def build_route_transition_intent_payload(
    *,
    topic_slug: str,
    route_choice: dict[str, Any],
    route_transition_gate: dict[str, Any],
) -> dict[str, Any]:
    del topic_slug
    route_choice = route_choice or {}
    route_transition_gate = route_transition_gate or {}
    stay_local_option = route_choice.get("stay_local_option") or {}
    yield_to_handoff_option = route_choice.get("yield_to_handoff_option") or {}
    source_hypothesis_id = str(route_choice.get("active_local_hypothesis_id") or "").strip()
    target_hypothesis_id = str(route_choice.get("primary_handoff_candidate_id") or "").strip()
    source_route_ref = str(
        stay_local_option.get("target_ref")
        or route_choice.get("current_route_choice_ref")
        or route_transition_gate.get("gate_artifact_ref")
        or ""
    ).strip()
    target_route_ref = str(
        yield_to_handoff_option.get("target_ref")
        or route_transition_gate.get("transition_target_ref")
        or ""
    ).strip()
    gate_status = str(route_transition_gate.get("transition_status") or "").strip()
    gate_artifact_ref = str(route_transition_gate.get("gate_artifact_ref") or "").strip()

    if target_hypothesis_id and gate_status == "available":
        intent_status = "ready"
        intent_summary = (
            f"Transition intent is ready: yield from `{source_hypothesis_id or 'no_active_local_route'}`"
            f" to `{target_hypothesis_id}` on the bounded next step."
        )
    elif target_hypothesis_id and gate_status == "checkpoint_required":
        intent_status = "checkpoint_held"
        intent_summary = (
            f"Transition intent is checkpoint-held: `{target_hypothesis_id}` is the bounded next target once"
            f" `{gate_artifact_ref or 'the active operator checkpoint'}` is resolved."
        )
    elif target_hypothesis_id:
        intent_status = "proposed"
        intent_summary = (
            f"Transition intent is proposed: keep `{source_hypothesis_id or 'the current local lane'}` active for now,"
            f" then yield to `{target_hypothesis_id}` once the bounded gate clears."
        )
    else:
        intent_status = "none"
        intent_summary = "No bounded source-to-target route transition intent is currently declared."

    return {
        "intent_status": intent_status,
        "gate_status": gate_status or "blocked",
        "source_hypothesis_id": source_hypothesis_id,
        "target_hypothesis_id": target_hypothesis_id,
        "source_route_ref": source_route_ref,
        "target_route_ref": target_route_ref,
        "gate_artifact_ref": gate_artifact_ref,
        "intent_summary": intent_summary,
    }


def _transition_receipt_matches_intent(
    latest_transition: dict[str, Any],
    route_transition_intent: dict[str, Any],
) -> bool:
    if not latest_transition:
        return False
    target_hypothesis_id = str(route_transition_intent.get("target_hypothesis_id") or "").strip().lower()
    target_route_ref = str(route_transition_intent.get("target_route_ref") or "").strip().lower()
    evidence_refs = _string_list(latest_transition.get("evidence_refs") or [])
    if target_route_ref and any(target_route_ref in str(ref or "").strip().lower() for ref in evidence_refs):
        return True
    haystack = " ".join(
        str(value or "").strip().lower()
        for value in (
            latest_transition.get("transition_id"),
            latest_transition.get("event_kind"),
            latest_transition.get("reason"),
            latest_transition.get("candidate_id"),
            *evidence_refs,
        )
        if str(value or "").strip()
    )
    return bool(target_hypothesis_id and target_hypothesis_id in haystack)


def build_route_transition_receipt_payload(
    *,
    topic_slug: str,
    route_transition_intent: dict[str, Any],
    transition_history: dict[str, Any] | None,
) -> dict[str, Any]:
    route_transition_intent = route_transition_intent or {}
    transition_history = transition_history or {}
    source_hypothesis_id = str(route_transition_intent.get("source_hypothesis_id") or "").strip()
    target_hypothesis_id = str(route_transition_intent.get("target_hypothesis_id") or "").strip()
    intent_status = str(route_transition_intent.get("intent_status") or "").strip()
    latest_transition = transition_history.get("latest_transition") or {}
    receipt_artifact_ref = str(
        transition_history.get("note_path")
        or transition_history.get("path")
        or (_truth_runtime_ref(topic_slug, "transition_history.md") if topic_slug else "")
    ).strip()
    matched = _transition_receipt_matches_intent(latest_transition, route_transition_intent)

    if target_hypothesis_id and matched:
        receipt_status = "recorded"
        receipt_summary = (
            f"Transition receipt recorded: `{source_hypothesis_id or 'no_active_local_route'}` -> `{target_hypothesis_id}`"
            f" is logged in `{receipt_artifact_ref or '(missing)'}`."
        )
    elif target_hypothesis_id:
        receipt_status = "pending"
        receipt_summary = (
            f"Transition receipt is still pending for `{source_hypothesis_id or 'no_active_local_route'}` -> `{target_hypothesis_id}`."
            f" The durable receipt surface remains `{receipt_artifact_ref or '(missing)'}`."
        )
    else:
        receipt_status = "none"
        receipt_summary = "No bounded route-transition receipt is currently applicable."

    return {
        "receipt_status": receipt_status,
        "intent_status": intent_status or "none",
        "source_hypothesis_id": source_hypothesis_id,
        "target_hypothesis_id": target_hypothesis_id,
        "receipt_transition_id": str(latest_transition.get("transition_id") or "").strip(),
        "receipt_artifact_ref": receipt_artifact_ref,
        "receipt_recorded_at": str(latest_transition.get("recorded_at") or "").strip(),
        "receipt_summary": receipt_summary,
    }


def build_route_transition_resolution_payload(
    *,
    topic_slug: str,
    route_transition_intent: dict[str, Any],
    route_transition_receipt: dict[str, Any],
    route_activation: dict[str, Any],
) -> dict[str, Any]:
    del topic_slug
    route_transition_intent = route_transition_intent or {}
    route_transition_receipt = route_transition_receipt or {}
    route_activation = route_activation or {}
    source_hypothesis_id = str(
        route_transition_receipt.get("source_hypothesis_id")
        or route_transition_intent.get("source_hypothesis_id")
        or ""
    ).strip()
    target_hypothesis_id = str(
        route_transition_receipt.get("target_hypothesis_id")
        or route_transition_intent.get("target_hypothesis_id")
        or ""
    ).strip()
    active_local_hypothesis_id = str(route_activation.get("active_local_hypothesis_id") or "").strip()
    intent_status = str(route_transition_intent.get("intent_status") or route_transition_receipt.get("intent_status") or "none").strip()
    receipt_status = str(route_transition_receipt.get("receipt_status") or "none").strip()

    if not source_hypothesis_id and not target_hypothesis_id:
        active_route_alignment = "not_applicable"
    elif active_local_hypothesis_id and active_local_hypothesis_id == target_hypothesis_id:
        active_route_alignment = "target_active"
    elif active_local_hypothesis_id and active_local_hypothesis_id == source_hypothesis_id:
        active_route_alignment = "source_active"
    elif active_local_hypothesis_id:
        active_route_alignment = "other_active"
    else:
        active_route_alignment = "no_local_active"

    if receipt_status == "recorded":
        resolution_status = "resolved"
        if active_route_alignment == "target_active":
            resolution_summary = (
                f"Transition resolved onto `{target_hypothesis_id}` and the target route is now the active local route."
            )
        elif active_route_alignment == "no_local_active":
            resolution_summary = (
                f"Transition receipt is recorded for `{source_hypothesis_id or 'no_active_local_route'}` -> `{target_hypothesis_id}`,"
                " but no active local route is currently declared."
            )
        else:
            resolution_summary = (
                f"Transition receipt is recorded for `{source_hypothesis_id or 'no_active_local_route'}` -> `{target_hypothesis_id}`,"
                f" with current active-route alignment `{active_route_alignment}`."
            )
    elif intent_status != "none" or target_hypothesis_id:
        resolution_status = "pending"
        resolution_summary = (
            f"Transition resolution remains pending for `{source_hypothesis_id or 'no_active_local_route'}` -> `{target_hypothesis_id or '(none)'}`"
            f" while active-route alignment is `{active_route_alignment}`."
        )
    else:
        resolution_status = "none"
        resolution_summary = "No bounded route-transition resolution is currently applicable."

    return {
        "resolution_status": resolution_status,
        "intent_status": intent_status or "none",
        "receipt_status": receipt_status,
        "active_local_hypothesis_id": active_local_hypothesis_id,
        "source_hypothesis_id": source_hypothesis_id,
        "target_hypothesis_id": target_hypothesis_id,
        "active_route_alignment": active_route_alignment,
        "resolution_artifact_ref": str(
            route_transition_receipt.get("receipt_artifact_ref")
            or route_transition_intent.get("gate_artifact_ref")
            or route_transition_intent.get("target_route_ref")
            or ""
        ).strip(),
        "resolution_summary": resolution_summary,
    }


def build_route_transition_discrepancy_payload(
    *,
    topic_slug: str,
    route_transition_resolution: dict[str, Any],
    route_transition_receipt: dict[str, Any],
) -> dict[str, Any]:
    del topic_slug
    route_transition_resolution = route_transition_resolution or {}
    route_transition_receipt = route_transition_receipt or {}
    resolution_status = str(route_transition_resolution.get("resolution_status") or "none").strip()
    receipt_status = str(route_transition_resolution.get("receipt_status") or route_transition_receipt.get("receipt_status") or "none").strip()
    intent_status = str(route_transition_resolution.get("intent_status") or route_transition_receipt.get("intent_status") or "none").strip()
    active_route_alignment = str(route_transition_resolution.get("active_route_alignment") or "not_applicable").strip()
    target_hypothesis_id = str(route_transition_resolution.get("target_hypothesis_id") or route_transition_receipt.get("target_hypothesis_id") or "").strip()
    resolution_artifact_ref = str(route_transition_resolution.get("resolution_artifact_ref") or "").strip()
    receipt_artifact_ref = str(route_transition_receipt.get("receipt_artifact_ref") or "").strip()

    if resolution_status == "resolved" and active_route_alignment != "target_active":
        discrepancy_status = "present"
        discrepancy_kind = "resolved_without_target_active"
        severity = "attention"
        discrepancy_summary = (
            f"Transition resolution is marked resolved for `{target_hypothesis_id or '(missing target)'}`,"
            f" but active-route alignment is `{active_route_alignment}` instead of `target_active`."
        )
    elif receipt_status == "recorded" and not target_hypothesis_id:
        discrepancy_status = "present"
        discrepancy_kind = "recorded_receipt_without_target"
        severity = "attention"
        discrepancy_summary = "Transition receipt is recorded, but no bounded target hypothesis is currently declared."
    else:
        discrepancy_status = "none"
        discrepancy_kind = "none"
        severity = "none"
        discrepancy_summary = (
            f"No bounded route-transition discrepancy is currently recorded."
            if intent_status == "none" and receipt_status == "none"
            else "No bounded route-transition discrepancy is currently recorded for the active handoff state."
        )

    discrepancy_artifact_refs = [
        ref
        for ref in (resolution_artifact_ref, receipt_artifact_ref)
        if str(ref).strip()
    ]

    return {
        "discrepancy_status": discrepancy_status,
        "discrepancy_kind": discrepancy_kind,
        "severity": severity,
        "resolution_status": resolution_status,
        "intent_status": intent_status,
        "receipt_status": receipt_status,
        "active_route_alignment": active_route_alignment,
        "target_hypothesis_id": target_hypothesis_id,
        "discrepancy_artifact_refs": discrepancy_artifact_refs,
        "discrepancy_summary": discrepancy_summary,
    }


def build_route_transition_repair_payload(
    *,
    topic_slug: str,
    route_transition_discrepancy: dict[str, Any],
    route_transition_resolution: dict[str, Any],
    route_activation: dict[str, Any],
) -> dict[str, Any]:
    del topic_slug
    route_transition_discrepancy = route_transition_discrepancy or {}
    route_transition_resolution = route_transition_resolution or {}
    route_activation = route_activation or {}
    discrepancy_status = str(route_transition_discrepancy.get("discrepancy_status") or "none").strip()
    discrepancy_kind = str(route_transition_discrepancy.get("discrepancy_kind") or "none").strip()
    active_local_hypothesis_id = str(
        route_activation.get("active_local_hypothesis_id")
        or route_transition_resolution.get("active_local_hypothesis_id")
        or ""
    ).strip()
    target_hypothesis_id = str(
        route_transition_discrepancy.get("target_hypothesis_id")
        or route_transition_resolution.get("target_hypothesis_id")
        or ""
    ).strip()
    active_route_alignment = str(
        route_transition_resolution.get("active_route_alignment")
        or route_transition_discrepancy.get("active_route_alignment")
        or "not_applicable"
    ).strip()
    artifact_refs = [
        str(item).strip()
        for item in (route_transition_discrepancy.get("discrepancy_artifact_refs") or [])
        if str(item).strip()
    ]

    if discrepancy_status != "present":
        repair_status = "none_required"
        repair_kind = "none"
        repair_summary = "No bounded route-transition repair is currently required."
    elif discrepancy_kind == "resolved_without_target_active":
        repair_status = "recommended"
        if active_route_alignment == "source_active":
            repair_kind = "confirm_target_activation_or_downgrade_resolution"
            repair_summary = (
                f"Either activate `{target_hypothesis_id or '(missing target)'}` as the current local route,"
                f" or downgrade the resolved handoff while `{active_local_hypothesis_id or '(missing active route)'}` remains active."
            )
        elif active_route_alignment == "no_local_active":
            repair_kind = "redeclare_active_target_or_downgrade_resolution"
            repair_summary = (
                f"Either redeclare `{target_hypothesis_id or '(missing target)'}` as the active local route,"
                " or downgrade the resolved handoff because no local route is currently active."
            )
        else:
            repair_kind = "review_active_route_alignment"
            repair_summary = (
                f"Review why active-route alignment is `{active_route_alignment}` while the resolved handoff targets"
                f" `{target_hypothesis_id or '(missing target)'}`."
            )
    elif discrepancy_kind == "recorded_receipt_without_target":
        repair_status = "recommended"
        repair_kind = "restore_missing_target_or_cancel_receipt"
        repair_summary = "Restore the missing target hypothesis metadata or cancel the stale recorded receipt."
    else:
        repair_status = "recommended"
        repair_kind = "review_transition_discrepancy"
        repair_summary = "Review the bounded transition discrepancy and reconcile the affected route artifacts."

    primary_repair_ref = artifact_refs[0] if artifact_refs else ""
    return {
        "repair_status": repair_status,
        "discrepancy_status": discrepancy_status,
        "discrepancy_kind": discrepancy_kind,
        "active_local_hypothesis_id": active_local_hypothesis_id,
        "target_hypothesis_id": target_hypothesis_id,
        "active_route_alignment": active_route_alignment,
        "repair_kind": repair_kind,
        "primary_repair_ref": primary_repair_ref,
        "repair_artifact_refs": artifact_refs,
        "repair_summary": repair_summary,
    }


def build_route_transition_escalation_payload(
    *,
    topic_slug: str,
    route_transition_repair: dict[str, Any],
    operator_checkpoint: dict[str, Any],
) -> dict[str, Any]:
    del topic_slug
    route_transition_repair = route_transition_repair or {}
    operator_checkpoint = operator_checkpoint or {}
    repair_status = str(route_transition_repair.get("repair_status") or "none_required").strip()
    repair_kind = str(route_transition_repair.get("repair_kind") or "none").strip()
    primary_repair_ref = str(route_transition_repair.get("primary_repair_ref") or "").strip()
    checkpoint_status = str(operator_checkpoint.get("status") or "cancelled").strip()
    checkpoint_kind = str(operator_checkpoint.get("checkpoint_kind") or "").strip()
    checkpoint_ref = str(
        operator_checkpoint.get("note_path") or operator_checkpoint.get("path") or ""
    ).strip()

    if repair_status != "recommended":
        escalation_status = "none"
        escalation_summary = (
            f"No bounded route-transition escalation is currently required because repair status is"
            f" `{repair_status or 'none_required'}`."
        )
    elif checkpoint_status == "requested":
        escalation_status = "checkpoint_active"
        escalation_summary = (
            f"Bounded route-transition repair `{repair_kind or '(missing)'}` is already escalated through"
            f" the active operator checkpoint `{checkpoint_kind or 'human_checkpoint'}` at"
            f" `{checkpoint_ref or '(missing)'}`."
        )
    else:
        escalation_status = "checkpoint_recommended"
        escalation_summary = (
            f"Bounded route-transition repair `{repair_kind or '(missing)'}` should escalate into an"
            f" operator checkpoint before deeper execution continues."
        )
        if checkpoint_status and checkpoint_status != "cancelled":
            escalation_summary += f" The latest checkpoint status is `{checkpoint_status}`."

    return {
        "escalation_status": escalation_status,
        "repair_status": repair_status,
        "repair_kind": repair_kind,
        "primary_repair_ref": primary_repair_ref,
        "checkpoint_status": checkpoint_status or "cancelled",
        "checkpoint_kind": checkpoint_kind,
        "checkpoint_ref": checkpoint_ref,
        "escalation_summary": escalation_summary,
    }


def build_route_transition_clearance_payload(
    *,
    topic_slug: str,
    route_transition_escalation: dict[str, Any],
    operator_checkpoint: dict[str, Any],
) -> dict[str, Any]:
    del topic_slug
    route_transition_escalation = route_transition_escalation or {}
    operator_checkpoint = operator_checkpoint or {}
    escalation_status = str(route_transition_escalation.get("escalation_status") or "none").strip()
    repair_status = str(route_transition_escalation.get("repair_status") or "none_required").strip()
    checkpoint_status = str(
        operator_checkpoint.get("status")
        or route_transition_escalation.get("checkpoint_status")
        or "cancelled"
    ).strip()
    checkpoint_kind = str(
        operator_checkpoint.get("checkpoint_kind")
        or route_transition_escalation.get("checkpoint_kind")
        or ""
    ).strip()
    checkpoint_ref = str(
        operator_checkpoint.get("note_path")
        or operator_checkpoint.get("path")
        or route_transition_escalation.get("checkpoint_ref")
        or ""
    ).strip()
    followthrough_ref = str(route_transition_escalation.get("primary_repair_ref") or "").strip()
    has_checkpoint_lifecycle = bool(checkpoint_kind)

    if escalation_status == "none":
        clearance_status = "none"
        clearance_kind = "none"
        followthrough_ref = ""
        clearance_summary = (
            f"No bounded route-transition clearance is currently required because escalation status is"
            f" `{escalation_status or 'none'}`."
        )
    elif checkpoint_status == "requested" and has_checkpoint_lifecycle:
        clearance_status = "blocked_on_checkpoint"
        clearance_kind = "checkpoint_requested"
        clearance_summary = (
            f"Bounded route-transition follow-through remains blocked on the active operator checkpoint"
            f" `{checkpoint_kind or 'human_checkpoint'}` at `{checkpoint_ref or '(missing)'}`."
        )
    elif checkpoint_status == "answered" and has_checkpoint_lifecycle:
        clearance_status = "cleared"
        clearance_kind = "checkpoint_answered"
        clearance_summary = (
            f"The operator checkpoint `{checkpoint_kind or 'human_checkpoint'}` has been answered, so bounded"
            f" follow-through can resume from `{followthrough_ref or checkpoint_ref or '(missing)'}`."
        )
    elif checkpoint_status == "cancelled" and has_checkpoint_lifecycle:
        clearance_status = "cleared"
        clearance_kind = "checkpoint_cancelled"
        clearance_summary = (
            f"The latest operator checkpoint `{checkpoint_kind or 'human_checkpoint'}` is cancelled, so it no"
            f" longer blocks bounded follow-through. Re-evaluate `{followthrough_ref or checkpoint_ref or '(missing)'}`"
            " explicitly on the next bounded step."
        )
    elif checkpoint_status == "superseded" and has_checkpoint_lifecycle:
        clearance_status = "awaiting_checkpoint"
        clearance_kind = "checkpoint_superseded"
        clearance_summary = (
            f"The previous operator checkpoint `{checkpoint_kind or 'human_checkpoint'}` was superseded, so"
            f" bounded follow-through is not yet cleared. Re-open the active checkpoint lane before trusting"
            f" `{followthrough_ref or checkpoint_ref or '(missing)'}`."
        )
    else:
        clearance_status = "awaiting_checkpoint"
        clearance_kind = "checkpoint_not_opened"
        clearance_summary = (
            f"Transition escalation remains active, but no durable checkpoint lifecycle has cleared it yet."
            f" Open or resolve the next operator checkpoint before bounded follow-through resumes from"
            f" `{followthrough_ref or '(missing)'}`."
        )

    return {
        "clearance_status": clearance_status,
        "clearance_kind": clearance_kind,
        "escalation_status": escalation_status,
        "repair_status": repair_status,
        "checkpoint_status": checkpoint_status or "cancelled",
        "checkpoint_kind": checkpoint_kind,
        "checkpoint_ref": checkpoint_ref,
        "followthrough_ref": followthrough_ref,
        "clearance_summary": clearance_summary,
    }


def build_route_transition_followthrough_payload(
    *,
    topic_slug: str,
    route_transition_clearance: dict[str, Any],
) -> dict[str, Any]:
    del topic_slug
    route_transition_clearance = route_transition_clearance or {}
    clearance_status = str(route_transition_clearance.get("clearance_status") or "none").strip()
    clearance_kind = str(route_transition_clearance.get("clearance_kind") or "none").strip()
    escalation_status = str(route_transition_clearance.get("escalation_status") or "none").strip()
    repair_status = str(route_transition_clearance.get("repair_status") or "none_required").strip()
    checkpoint_status = str(route_transition_clearance.get("checkpoint_status") or "cancelled").strip()
    checkpoint_ref = str(route_transition_clearance.get("checkpoint_ref") or "").strip()
    followthrough_ref = str(route_transition_clearance.get("followthrough_ref") or "").strip()

    if clearance_status == "none":
        followthrough_status = "none"
        followthrough_kind = "none"
        followthrough_ref = ""
        followthrough_summary = "No bounded route-transition follow-through is currently applicable."
    elif clearance_status == "awaiting_checkpoint":
        followthrough_status = "held_by_clearance"
        followthrough_kind = "awaiting_checkpoint"
        followthrough_summary = (
            f"Bounded route-transition follow-through is still held until the next operator checkpoint clears."
            f" Do not resume `{followthrough_ref or '(missing)'}` yet."
        )
    elif clearance_status == "blocked_on_checkpoint":
        followthrough_status = "held_by_clearance"
        followthrough_kind = "blocked_on_checkpoint"
        followthrough_summary = (
            f"Bounded route-transition follow-through remains blocked by `{checkpoint_ref or '(missing checkpoint ref)'}`."
            f" Do not resume `{followthrough_ref or '(missing)'}` until that checkpoint is resolved."
        )
    elif followthrough_ref:
        followthrough_status = "ready"
        followthrough_kind = "resume_from_followthrough_ref"
        followthrough_summary = (
            f"Bounded route-transition follow-through is ready. Resume from `{followthrough_ref}` on the next"
            " bounded step."
        )
    else:
        followthrough_status = "missing_followthrough_ref"
        followthrough_kind = "clearance_without_ref"
        followthrough_summary = (
            f"Transition clearance is `{clearance_status}`, but no authoritative follow-through ref is currently"
            " recorded. Reconstruct the bounded next step explicitly before resuming."
        )

    return {
        "followthrough_status": followthrough_status,
        "followthrough_kind": followthrough_kind,
        "clearance_status": clearance_status,
        "clearance_kind": clearance_kind,
        "escalation_status": escalation_status,
        "repair_status": repair_status,
        "checkpoint_status": checkpoint_status,
        "checkpoint_ref": checkpoint_ref,
        "followthrough_ref": followthrough_ref,
        "followthrough_summary": followthrough_summary,
    }


def build_route_transition_resumption_payload(
    *,
    topic_slug: str,
    route_transition_followthrough: dict[str, Any],
    route_transition_resolution: dict[str, Any],
    route_activation: dict[str, Any],
    transition_history: dict[str, Any] | None,
) -> dict[str, Any]:
    del topic_slug
    route_transition_followthrough = route_transition_followthrough or {}
    route_transition_resolution = route_transition_resolution or {}
    route_activation = route_activation or {}
    transition_history = transition_history or {}
    followthrough_status = str(route_transition_followthrough.get("followthrough_status") or "none").strip()
    target_hypothesis_id = str(route_transition_resolution.get("target_hypothesis_id") or "").strip()
    active_route_alignment = str(route_transition_resolution.get("active_route_alignment") or "not_applicable").strip()
    active_local_hypothesis_id = str(
        route_activation.get("active_local_hypothesis_id")
        or route_transition_resolution.get("active_local_hypothesis_id")
        or ""
    ).strip()
    active_local_action_ref = str(route_activation.get("active_local_action_ref") or "").strip()
    followthrough_ref = str(route_transition_followthrough.get("followthrough_ref") or "").strip()
    transition_note_ref = str(
        transition_history.get("note_path") or transition_history.get("path") or ""
    ).strip()
    latest_transition = transition_history.get("latest_transition") or {}
    transition_recorded = False
    if latest_transition:
        transition_haystack = " ".join(
            str(latest_transition.get(key) or "").strip().lower()
            for key in ("transition_id", "event_kind", "reason")
            if str(latest_transition.get(key) or "").strip()
        )
        transition_recorded = (
            "route_" in transition_haystack
            or "route-" in transition_haystack
            or "resume" in transition_haystack
        )

    if target_hypothesis_id and active_route_alignment == "target_active":
        resumption_status = "resumed"
        resumption_kind = "target_route_active"
        resumption_ref = active_local_action_ref or followthrough_ref
        resumption_summary = (
            f"Bounded transition resumption is already visible: `{target_hypothesis_id}` is the active local"
            f" route and the authoritative current-route ref is `{resumption_ref or '(missing)'}`."
        )
    elif (
        followthrough_status == "none"
        and active_local_hypothesis_id
        and transition_recorded
        and (not target_hypothesis_id or target_hypothesis_id == active_local_hypothesis_id)
    ):
        target_hypothesis_id = target_hypothesis_id or active_local_hypothesis_id
        active_route_alignment = "target_active"
        resumption_status = "resumed"
        resumption_kind = "target_route_active"
        resumption_ref = active_local_action_ref or transition_note_ref
        resumption_summary = (
            f"Bounded transition resumption is already visible: `{active_local_hypothesis_id}` is active and"
            f" transition history is recorded at `{transition_note_ref or '(missing)'}`."
        )
    elif followthrough_status == "none":
        resumption_status = "none"
        resumption_kind = "none"
        resumption_ref = ""
        followthrough_ref = ""
        resumption_summary = "No bounded route-transition resumption is currently applicable."
    elif followthrough_status != "ready":
        resumption_status = "waiting_followthrough"
        resumption_kind = "followthrough_held"
        resumption_ref = followthrough_ref
        resumption_summary = (
            f"Bounded transition resumption is waiting because follow-through status is"
            f" `{followthrough_status or '(missing)'}`. Do not treat `{followthrough_ref or '(missing)'}` as resumed yet."
        )
    else:
        resumption_status = "pending"
        resumption_kind = "ready_not_resumed"
        resumption_ref = followthrough_ref
        resumption_summary = (
            f"Bounded transition follow-through is ready at `{followthrough_ref or '(missing)'}`, but the target"
            f" route `{target_hypothesis_id or '(missing target)'}` is not yet active on the current bounded route."
        )

    return {
        "resumption_status": resumption_status,
        "resumption_kind": resumption_kind,
        "followthrough_status": followthrough_status,
        "active_route_alignment": active_route_alignment,
        "active_local_hypothesis_id": active_local_hypothesis_id,
        "target_hypothesis_id": target_hypothesis_id,
        "followthrough_ref": followthrough_ref,
        "resumption_ref": resumption_ref,
        "resumption_summary": resumption_summary,
    }


def build_route_transition_commitment_payload(
    *,
    topic_slug: str,
    route_transition_resumption: dict[str, Any],
    route_activation: dict[str, Any],
    competing_hypotheses: list[dict[str, Any]],
) -> dict[str, Any]:
    del topic_slug
    route_transition_resumption = route_transition_resumption or {}
    route_activation = route_activation or {}
    competing_hypotheses = competing_hypotheses or []
    resumption_status = str(route_transition_resumption.get("resumption_status") or "none").strip()
    resumption_kind = str(route_transition_resumption.get("resumption_kind") or "none").strip()
    active_local_hypothesis_id = str(
        route_transition_resumption.get("active_local_hypothesis_id")
        or route_activation.get("active_local_hypothesis_id")
        or ""
    ).strip()
    resumption_ref = str(route_transition_resumption.get("resumption_ref") or "").strip()
    active_local_action_ref = str(route_activation.get("active_local_action_ref") or "").strip()

    active_row = next(
        (
            row
            for row in competing_hypotheses
            if str(row.get("hypothesis_id") or "").strip() == active_local_hypothesis_id
        ),
        {},
    )
    route_kind = str(active_row.get("route_kind") or "").strip()
    route_target_ref = str(active_row.get("route_target_ref") or "").strip()
    deferred_commitment_ref = route_target_ref.lower()

    if resumption_status == "none":
        commitment_status = "none"
        commitment_kind = "none"
        commitment_ref = ""
        commitment_summary = "No bounded route-transition commitment is currently applicable."
    elif resumption_status != "resumed":
        commitment_status = "waiting_resumption"
        commitment_kind = "resumption_not_ready"
        commitment_ref = resumption_ref
        commitment_summary = (
            f"Bounded route-transition commitment is waiting because resumption status is"
            f" `{resumption_status or '(missing)'}`."
        )
    elif route_kind == "current_topic" and "deferred_candidates.json" in deferred_commitment_ref:
        commitment_status = "pending_commitment"
        commitment_kind = "active_route_not_yet_committed"
        commitment_ref = route_target_ref or active_local_action_ref or resumption_ref
        commitment_summary = (
            f"`{active_local_hypothesis_id or '(missing active route)'}` is active after resumption, but its"
            f" durable route ref still points at deferred-buffer state `{commitment_ref or '(missing)'}`."
            " Reconcile that route artifact before treating the lane as durably committed."
        )
    elif route_kind == "current_topic":
        commitment_status = "committed"
        commitment_kind = "current_topic_committed"
        commitment_ref = active_local_action_ref or route_target_ref or resumption_ref
        commitment_summary = (
            f"`{active_local_hypothesis_id or '(missing active route)'}` is now the durable committed bounded lane."
            f" The authoritative commitment ref is `{commitment_ref or '(missing)'}`."
        )
    elif active_local_hypothesis_id:
        commitment_status = "pending_commitment"
        commitment_kind = "active_route_not_yet_committed"
        commitment_ref = route_target_ref or active_local_action_ref or resumption_ref
        commitment_summary = (
            f"`{active_local_hypothesis_id}` is active after resumption, but it is still classified as"
            f" route kind `{route_kind or '(missing)'}` rather than `current_topic`."
            f" Reconcile `{commitment_ref or '(missing)'}` before treating the route as durably committed."
        )
    else:
        commitment_status = "pending_commitment"
        commitment_kind = "missing_active_route_projection"
        commitment_ref = resumption_ref
        commitment_summary = (
            f"Route resumption is visible, but no active local route projection is currently recorded."
            f" Reconstruct the committed bounded lane from `{resumption_ref or '(missing)'}` explicitly."
        )

    return {
        "commitment_status": commitment_status,
        "commitment_kind": commitment_kind,
        "resumption_status": resumption_status,
        "resumption_kind": resumption_kind,
        "active_local_hypothesis_id": active_local_hypothesis_id,
        "route_kind": route_kind,
        "route_target_ref": route_target_ref,
        "resumption_ref": resumption_ref,
        "commitment_ref": commitment_ref,
        "commitment_summary": commitment_summary,
    }


def _route_truth_surface_kind(ref: str, *, topic_slug: str) -> str:
    normalized = str(ref or "").strip().lower().replace("\\", "/")
    if not normalized:
        return "missing"
    if "deferred_candidates.json" in normalized:
        return "deferred_buffer"
    if "followup_" in normalized:
        return "followup_subtopic"
    if "transition_history" in normalized:
        return "transition_history"
    if topic_slug and f"topics/{topic_slug}/runtime/" in normalized:
        return "current_topic_surface"
    # Legacy layout fallback: runtime/topics/<slug>/...
    if topic_slug and f"runtime/topics/{topic_slug}/" in normalized:
        return "current_topic_surface"
    if "topics/" in normalized and "/runtime/" in normalized:
        return "other_topic_surface"
    return "external_or_unknown"


def build_route_transition_authority_payload(
    *,
    topic_slug: str,
    route_transition_commitment: dict[str, Any],
    route_activation: dict[str, Any],
) -> dict[str, Any]:
    route_transition_commitment = route_transition_commitment or {}
    route_activation = route_activation or {}
    commitment_status = str(route_transition_commitment.get("commitment_status") or "none").strip()
    commitment_kind = str(route_transition_commitment.get("commitment_kind") or "none").strip()
    active_local_hypothesis_id = str(
        route_transition_commitment.get("active_local_hypothesis_id")
        or route_activation.get("active_local_hypothesis_id")
        or ""
    ).strip()
    route_kind = str(route_transition_commitment.get("route_kind") or "").strip()
    route_target_ref = str(route_transition_commitment.get("route_target_ref") or "").strip()
    commitment_ref = str(route_transition_commitment.get("commitment_ref") or "").strip()
    active_local_action_ref = str(route_activation.get("active_local_action_ref") or "").strip()
    authority_ref = active_local_action_ref or commitment_ref or route_target_ref
    route_target_surface_kind = _route_truth_surface_kind(route_target_ref, topic_slug=topic_slug)
    authority_surface_kind = _route_truth_surface_kind(authority_ref, topic_slug=topic_slug)

    if commitment_status == "none":
        authority_status = "none"
        authority_kind = "none"
        authority_ref = ""
        authority_summary = "No bounded route-transition authority is currently applicable."
    elif commitment_status != "committed":
        authority_status = "waiting_commitment"
        authority_kind = "commitment_not_ready"
        authority_ref = commitment_ref or authority_ref
        authority_summary = (
            f"Bounded route-transition authority is waiting because commitment status is"
            f" `{commitment_status or '(missing)'}`."
        )
    elif route_kind != "current_topic":
        authority_status = "pending_authority"
        authority_kind = "route_not_current_topic"
        authority_summary = (
            f"`{active_local_hypothesis_id or '(missing active route)'}` is committed, but its route kind is still"
            f" `{route_kind or '(missing)'}` rather than `current_topic`. Reconcile"
            f" `{commitment_ref or route_target_ref or '(missing)'}` before treating the bounded truth surface"
            " as authoritative."
        )
    elif not route_target_ref:
        authority_status = "pending_authority"
        authority_kind = "missing_authority_projection"
        authority_summary = (
            f"`{active_local_hypothesis_id or '(missing active route)'}` is committed, but no durable"
            " current-topic route target ref is currently recorded. Keep the commitment visible, but do not"
            " treat authority as closed until a bounded truth surface is written explicitly."
        )
    elif (
        route_target_surface_kind != "current_topic_surface"
        or authority_surface_kind != "current_topic_surface"
    ):
        authority_status = "pending_authority"
        authority_kind = "authority_ref_not_current_topic"
        authority_summary = (
            f"`{active_local_hypothesis_id or '(missing active route)'}` is committed, but its authority refs are"
            f" not yet aligned on current-topic truth surfaces: route target"
            f" `{route_target_ref or '(missing)'}` => `{route_target_surface_kind}`, authority ref"
            f" `{authority_ref or '(missing)'}` => `{authority_surface_kind}`."
        )
    elif not active_local_hypothesis_id:
        authority_status = "pending_authority"
        authority_kind = "missing_authority_projection"
        authority_summary = (
            "Bounded route-transition commitment is visible, but no active local hypothesis is currently"
            " projected. Rebuild the current-topic truth surface before treating authority as closed."
        )
    else:
        authority_status = "authoritative"
        authority_kind = "current_topic_authoritative"
        authority_summary = (
            f"`{active_local_hypothesis_id}` is durably committed and now authoritative across the current-topic"
            f" truth surfaces. Route target `{route_target_ref}` and authority ref"
            f" `{authority_ref or '(missing)'}` both remain on the bounded current-topic lane."
        )

    return {
        "authority_status": authority_status,
        "authority_kind": authority_kind,
        "commitment_status": commitment_status,
        "commitment_kind": commitment_kind,
        "active_local_hypothesis_id": active_local_hypothesis_id,
        "route_kind": route_kind,
        "route_target_ref": route_target_ref,
        "commitment_ref": commitment_ref,
        "authority_ref": authority_ref,
        "authority_summary": authority_summary,
    }


def _default_hypothesis_route_kind(*, status: str) -> str:
    if status == "excluded":
        return "excluded"
    if status == "watch":
        return "deferred_buffer"
    return "current_topic"


def _default_hypothesis_route_summary(*, label: str, route_kind: str) -> str:
    if route_kind == "deferred_buffer":
        return f"Park `{label}` in the deferred buffer until bounded reactivation conditions are met."
    if route_kind == "followup_subtopic":
        return f"Route `{label}` into a bounded follow-up subtopic instead of widening the current topic."
    if route_kind == "excluded":
        return f"Keep `{label}` excluded with no active branch route."
    return f"Keep `{label}` on the current topic branch."


def _default_hypothesis_route_ref(*, topic_slug: str, route_kind: str) -> str:
    if not topic_slug:
        return ""
    if route_kind == "deferred_buffer":
        return _truth_runtime_ref(topic_slug, "deferred_candidates.json")
    if route_kind == "followup_subtopic":
        return _truth_runtime_ref(topic_slug, "followup_subtopics.jsonl")
    if route_kind == "current_topic":
        return _truth_runtime_ref(topic_slug, "research_question.contract.md")
    return ""


def normalize_competing_hypotheses(rows: Any, *, topic_slug: str = "") -> list[dict[str, Any]]:
    allowed_statuses = {"leading", "active", "watch", "excluded"}
    allowed_route_kinds = {"current_topic", "deferred_buffer", "followup_subtopic", "excluded"}
    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, row in enumerate(rows or [], start=1):
        if not isinstance(row, dict):
            continue
        hypothesis_id = str(
            row.get("hypothesis_id")
            or row.get("label")
            or row.get("summary")
            or f"hypothesis:{index}"
        ).strip()
        if not hypothesis_id:
            hypothesis_id = f"hypothesis:{index}"
        if hypothesis_id in seen_ids:
            continue
        seen_ids.add(hypothesis_id)
        status = str(row.get("status") or "active").strip().lower()
        if status not in allowed_statuses:
            status = "active"
        label = str(row.get("label") or row.get("summary") or hypothesis_id).strip() or hypothesis_id
        summary = str(row.get("summary") or label).strip() or label
        route_kind = str(row.get("route_kind") or "").strip().lower()
        if status == "excluded":
            route_kind = "excluded"
        elif route_kind not in allowed_route_kinds:
            route_kind = _default_hypothesis_route_kind(status=status)
        route_target_summary = str(row.get("route_target_summary") or "").strip() or _default_hypothesis_route_summary(
            label=label,
            route_kind=route_kind,
        )
        route_target_ref = str(row.get("route_target_ref") or "").strip() or _default_hypothesis_route_ref(
            topic_slug=topic_slug,
            route_kind=route_kind,
        )
        evidence_refs = _string_list(row.get("evidence_refs") or [])
        exclusion_notes = _string_list(row.get("exclusion_notes") or [])
        normalized.append(
            {
                "hypothesis_id": hypothesis_id,
                "label": label,
                "status": status,
                "summary": summary,
                "route_kind": route_kind,
                "route_target_summary": route_target_summary,
                "route_target_ref": route_target_ref,
                "evidence_refs": evidence_refs,
                "evidence_ref_count": len(evidence_refs),
                "exclusion_notes": exclusion_notes,
            }
        )
    return normalized


def leading_competing_hypothesis(hypotheses: list[dict[str, Any]]) -> dict[str, Any] | None:
    for status in ("leading", "active", "watch", "excluded"):
        for row in hypotheses:
            if str(row.get("status") or "").strip() == status:
                return row
    return None


def active_branch_hypothesis(hypotheses: list[dict[str, Any]]) -> dict[str, Any] | None:
    for status in ("leading", "active", "watch"):
        for row in hypotheses:
            if str(row.get("route_kind") or "").strip() == "current_topic" and str(row.get("status") or "").strip() == status:
                return row
    return leading_competing_hypothesis(hypotheses)


def hypotheses_for_route(hypotheses: list[dict[str, Any]], *, route_kind: str) -> list[dict[str, Any]]:
    return [
        row
        for row in hypotheses
        if str(row.get("route_kind") or "").strip() == route_kind
    ]


def _parked_route_obligation_rows(hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for route_kind in ("deferred_buffer", "followup_subtopic"):
        for row in hypotheses_for_route(hypotheses, route_kind=route_kind):
            rows.append(
                {
                    "hypothesis_id": str(row.get("hypothesis_id") or ""),
                    "label": str(row.get("label") or ""),
                    "status": str(row.get("status") or ""),
                    "route_kind": route_kind,
                    "obligation_summary": str(row.get("route_target_summary") or ""),
                    "target_ref": str(row.get("route_target_ref") or ""),
                }
            )
    return rows


def build_route_activation_payload(
    *,
    topic_slug: str,
    competing_hypotheses: list[dict[str, Any]],
    topic_status_explainability: dict[str, Any] | None = None,
) -> dict[str, Any]:
    explainability = topic_status_explainability or {}
    next_bounded_action = explainability.get("next_bounded_action") or {}
    current_route_choice = explainability.get("current_route_choice") or {}
    current_branch: dict[str, Any] = {}
    for status in ("leading", "active", "watch"):
        current_branch = next(
            (
                row
                for row in competing_hypotheses
                if str(row.get("route_kind") or "").strip() == "current_topic"
                and str(row.get("status") or "").strip() == status
            ),
            {},
        )
        if current_branch:
            break
    deferred_obligations = _parked_route_obligation_rows(
        hypotheses_for_route(competing_hypotheses, route_kind="deferred_buffer")
    )
    followup_obligations = _parked_route_obligation_rows(
        hypotheses_for_route(competing_hypotheses, route_kind="followup_subtopic")
    )
    all_parked_obligations = deferred_obligations + followup_obligations
    active_local_action_summary = str(
        next_bounded_action.get("summary")
        or current_route_choice.get("selected_action_summary")
        or current_branch.get("route_target_summary")
        or "No active current-topic route is currently declared."
    ).strip()
    active_local_action_ref = str(
        current_route_choice.get("next_action_decision_note_path")
        or (_truth_runtime_ref(topic_slug, "action_queue.jsonl") if topic_slug else "")
    ).strip()
    return {
        "active_local_hypothesis_id": str(current_branch.get("hypothesis_id") or ""),
        "active_local_action_summary": active_local_action_summary,
        "active_local_action_ref": active_local_action_ref,
        "parked_route_count": len(all_parked_obligations),
        "deferred_obligations": deferred_obligations,
        "followup_obligations": followup_obligations,
    }


def append_competing_hypotheses_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    hypotheses = normalize_competing_hypotheses(
        payload.get("competing_hypotheses") or [],
        topic_slug=str(payload.get("topic_slug") or ""),
    )
    lines.extend(
        [
            "",
            "## Competing hypotheses",
            "",
            f"- Count: `{len(hypotheses)}`",
            "",
        ]
    )
    if not hypotheses:
        lines.append("- No explicit competing hypotheses are currently recorded.")
        return
    for row in hypotheses:
        lines.append(
            f"- `{row.get('hypothesis_id') or '(missing)'}` status=`{row.get('status') or 'active'}` route=`{row.get('route_kind') or 'current_topic'}` evidence_refs=`{row.get('evidence_ref_count') or 0}`"
        )
        lines.append(f"  label: {row.get('label') or '(missing)'}")
        lines.append(f"  summary: {row.get('summary') or '(missing)'}")
        lines.append(f"  route target: {row.get('route_target_summary') or '(none)'}")
        lines.append(f"  route ref: `{row.get('route_target_ref') or '(none)'}`")
        evidence_refs = row.get("evidence_refs") or []
        lines.append(f"  evidence refs: `{', '.join(evidence_refs) or '(none)'}`")
        exclusion_notes = row.get("exclusion_notes") or []
        lines.append(f"  exclusion notes: {', '.join(exclusion_notes) or '(none)'}")


def append_route_activation_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    route_activation = payload.get("route_activation") or {}
    if not route_activation:
        return
    lines.extend(
        [
            "",
            "## Route activation",
            "",
            f"- Active local hypothesis: `{route_activation.get('active_local_hypothesis_id') or '(none recorded)'}`",
            f"- Active local action: {route_activation.get('active_local_action_summary') or '(none recorded)'}",
            f"- Active local action ref: `{route_activation.get('active_local_action_ref') or '(none)'}`",
            f"- Parked route count: `{route_activation.get('parked_route_count') or 0}`",
            "",
            "### Deferred obligations",
            "",
        ]
    )
    for row in route_activation.get("deferred_obligations") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('hypothesis_id') or '(missing)'}` status=`{row.get('status') or '(missing)'}`: {row.get('obligation_summary') or '(missing)'}"
            )
            lines.append(f"  target ref: `{row.get('target_ref') or '(none)'}`")
        else:
            lines.append(f"- {row}")
    lines.extend(["", "### Follow-up obligations", ""])
    for row in route_activation.get("followup_obligations") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('hypothesis_id') or '(missing)'}` status=`{row.get('status') or '(missing)'}`: {row.get('obligation_summary') or '(missing)'}"
            )
            lines.append(f"  target ref: `{row.get('target_ref') or '(none)'}`")
        else:
            lines.append(f"- {row}")


def append_route_reentry_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    route_reentry = payload.get("route_reentry") or {}
    if not route_reentry:
        return
    lines.extend(
        [
            "",
            "## Route re-entry",
            "",
            f"- Re-entry-ready count: `{route_reentry.get('reentry_ready_count') or 0}`",
            "",
            "### Deferred routes",
            "",
        ]
    )
    for row in route_reentry.get("deferred_routes") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('hypothesis_id') or '(missing)'}` reentry_status=`{row.get('reentry_status') or '(missing)'}`: {row.get('reentry_summary') or '(missing)'}"
            )
            lines.append(f"  conditions: {row.get('condition_summary') or '(missing)'}")
            lines.append(f"  target ref: `{row.get('target_ref') or '(none)'}`")
            lines.append(f"  support ref: `{row.get('support_ref') or '(none)'}`")
        else:
            lines.append(f"- {row}")
    lines.extend(["", "### Follow-up routes", ""])
    for row in route_reentry.get("followup_routes") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('hypothesis_id') or '(missing)'}` reentry_status=`{row.get('reentry_status') or '(missing)'}`: {row.get('reentry_summary') or '(missing)'}"
            )
            lines.append(f"  conditions: {row.get('condition_summary') or '(missing)'}")
            lines.append(f"  target ref: `{row.get('target_ref') or '(none)'}`")
            lines.append(f"  support ref: `{row.get('support_ref') or '(none)'}`")
        else:
            lines.append(f"- {row}")


def append_route_handoff_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    route_handoff = payload.get("route_handoff") or {}
    if not route_handoff:
        return
    lines.extend(
        [
            "",
            "## Route handoff",
            "",
            f"- Active local hypothesis: `{route_handoff.get('active_local_hypothesis_id') or '(none recorded)'}`",
            f"- Active local action: {route_handoff.get('active_local_action_summary') or '(none recorded)'}",
            f"- Active local action ref: `{route_handoff.get('active_local_action_ref') or '(none)'}`",
            f"- Primary handoff candidate: `{route_handoff.get('primary_handoff_candidate_id') or '(none)'}`",
            f"- Handoff candidate count: `{route_handoff.get('handoff_candidate_count') or 0}`",
            "",
            "### Handoff candidates",
            "",
        ]
    )
    for row in route_handoff.get("handoff_candidates") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('hypothesis_id') or '(missing)'}` handoff_status=`{row.get('handoff_status') or '(missing)'}` reentry_status=`{row.get('reentry_status') or '(missing)'}`: {row.get('handoff_summary') or '(missing)'}"
            )
            lines.append(f"  conditions: {row.get('condition_summary') or '(missing)'}")
            lines.append(f"  target ref: `{row.get('target_ref') or '(none)'}`")
            lines.append(f"  support ref: `{row.get('support_ref') or '(none)'}`")
        else:
            lines.append(f"- {row}")
    lines.extend(["", "### Keep parked", ""])
    for row in route_handoff.get("keep_parked_routes") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('hypothesis_id') or '(missing)'}` handoff_status=`{row.get('handoff_status') or '(missing)'}` reentry_status=`{row.get('reentry_status') or '(missing)'}`: {row.get('handoff_summary') or '(missing)'}"
            )
            lines.append(f"  conditions: {row.get('condition_summary') or '(missing)'}")
            lines.append(f"  target ref: `{row.get('target_ref') or '(none)'}`")
            lines.append(f"  support ref: `{row.get('support_ref') or '(none)'}`")
        else:
            lines.append(f"- {row}")


def append_route_choice_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    route_choice = payload.get("route_choice") or {}
    if not route_choice:
        return
    lines.extend(
        [
            "",
            "## Route choice",
            "",
            f"- Choice status: `{route_choice.get('choice_status') or '(missing)'}`",
            f"- Active local hypothesis: `{route_choice.get('active_local_hypothesis_id') or '(none)'}`",
            f"- Primary handoff candidate: `{route_choice.get('primary_handoff_candidate_id') or '(none)'}`",
            f"- Current route-choice ref: `{route_choice.get('current_route_choice_ref') or '(none)'}`",
            "",
            route_choice.get("choice_summary") or "(missing)",
            "",
            "### Stay local",
            "",
        ]
    )
    stay_local = route_choice.get("stay_local_option") or {}
    lines.append(
        f"- `{stay_local.get('hypothesis_id') or '(none)'}` option_kind=`{stay_local.get('option_kind') or '(missing)'}`: {stay_local.get('option_summary') or '(missing)'}"
    )
    lines.append(f"  target ref: `{stay_local.get('target_ref') or '(none)'}`")
    lines.extend(["", "### Yield to handoff", ""])
    yield_option = route_choice.get("yield_to_handoff_option") or {}
    lines.append(
        f"- `{yield_option.get('hypothesis_id') or '(none)'}` option_kind=`{yield_option.get('option_kind') or '(missing)'}`: {yield_option.get('option_summary') or '(missing)'}"
    )
    lines.append(f"  target ref: `{yield_option.get('target_ref') or '(none)'}`")


def append_route_transition_gate_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    route_transition_gate = payload.get("route_transition_gate") or {}
    if not route_transition_gate:
        return
    lines.extend(
        [
            "",
            "## Route transition gate",
            "",
            f"- Transition status: `{route_transition_gate.get('transition_status') or '(missing)'}`",
            f"- Choice status: `{route_transition_gate.get('choice_status') or '(missing)'}`",
            f"- Checkpoint status: `{route_transition_gate.get('checkpoint_status') or '(missing)'}`",
            f"- Active local hypothesis: `{route_transition_gate.get('active_local_hypothesis_id') or '(none)'}`",
            f"- Primary handoff candidate: `{route_transition_gate.get('primary_handoff_candidate_id') or '(none)'}`",
            f"- Gate kind: `{route_transition_gate.get('gate_kind') or '(missing)'}`",
            f"- Gate artifact ref: `{route_transition_gate.get('gate_artifact_ref') or '(none)'}`",
            f"- Transition target ref: `{route_transition_gate.get('transition_target_ref') or '(none)'}`",
            "",
            route_transition_gate.get("transition_summary") or "(missing)",
        ]
    )


def append_route_transition_intent_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    route_transition_intent = payload.get("route_transition_intent") or {}
    if not route_transition_intent:
        return
    lines.extend(
        [
            "",
            "## Route transition intent",
            "",
            f"- Intent status: `{route_transition_intent.get('intent_status') or '(missing)'}`",
            f"- Gate status: `{route_transition_intent.get('gate_status') or '(missing)'}`",
            f"- Source hypothesis: `{route_transition_intent.get('source_hypothesis_id') or '(none)'}`",
            f"- Target hypothesis: `{route_transition_intent.get('target_hypothesis_id') or '(none)'}`",
            f"- Source route ref: `{route_transition_intent.get('source_route_ref') or '(none)'}`",
            f"- Target route ref: `{route_transition_intent.get('target_route_ref') or '(none)'}`",
            f"- Gate artifact ref: `{route_transition_intent.get('gate_artifact_ref') or '(none)'}`",
            "",
            route_transition_intent.get("intent_summary") or "(missing)",
        ]
    )


def append_route_transition_receipt_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    route_transition_receipt = payload.get("route_transition_receipt") or {}
    if not route_transition_receipt:
        return
    lines.extend(
        [
            "",
            "## Route transition receipt",
            "",
            f"- Receipt status: `{route_transition_receipt.get('receipt_status') or '(missing)'}`",
            f"- Intent status: `{route_transition_receipt.get('intent_status') or '(missing)'}`",
            f"- Source hypothesis: `{route_transition_receipt.get('source_hypothesis_id') or '(none)'}`",
            f"- Target hypothesis: `{route_transition_receipt.get('target_hypothesis_id') or '(none)'}`",
            f"- Receipt transition id: `{route_transition_receipt.get('receipt_transition_id') or '(none)'}`",
            f"- Receipt artifact ref: `{route_transition_receipt.get('receipt_artifact_ref') or '(none)'}`",
            f"- Receipt recorded at: `{route_transition_receipt.get('receipt_recorded_at') or '(none)'}`",
            "",
            route_transition_receipt.get("receipt_summary") or "(missing)",
        ]
    )


def append_route_transition_resolution_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    route_transition_resolution = payload.get("route_transition_resolution") or {}
    if not route_transition_resolution:
        return
    lines.extend(
        [
            "",
            "## Route transition resolution",
            "",
            f"- Resolution status: `{route_transition_resolution.get('resolution_status') or '(missing)'}`",
            f"- Intent status: `{route_transition_resolution.get('intent_status') or '(missing)'}`",
            f"- Receipt status: `{route_transition_resolution.get('receipt_status') or '(missing)'}`",
            f"- Active local hypothesis: `{route_transition_resolution.get('active_local_hypothesis_id') or '(none)'}`",
            f"- Source hypothesis: `{route_transition_resolution.get('source_hypothesis_id') or '(none)'}`",
            f"- Target hypothesis: `{route_transition_resolution.get('target_hypothesis_id') or '(none)'}`",
            f"- Active-route alignment: `{route_transition_resolution.get('active_route_alignment') or '(missing)'}`",
            f"- Resolution artifact ref: `{route_transition_resolution.get('resolution_artifact_ref') or '(none)'}`",
            "",
            route_transition_resolution.get("resolution_summary") or "(missing)",
        ]
    )


def append_route_transition_discrepancy_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    route_transition_discrepancy = payload.get("route_transition_discrepancy") or {}
    if not route_transition_discrepancy:
        return
    lines.extend(
        [
            "",
            "## Route transition discrepancy",
            "",
            f"- Discrepancy status: `{route_transition_discrepancy.get('discrepancy_status') or '(missing)'}`",
            f"- Discrepancy kind: `{route_transition_discrepancy.get('discrepancy_kind') or '(missing)'}`",
            f"- Severity: `{route_transition_discrepancy.get('severity') or '(missing)'}`",
            f"- Resolution status: `{route_transition_discrepancy.get('resolution_status') or '(missing)'}`",
            f"- Intent status: `{route_transition_discrepancy.get('intent_status') or '(missing)'}`",
            f"- Receipt status: `{route_transition_discrepancy.get('receipt_status') or '(missing)'}`",
            f"- Active-route alignment: `{route_transition_discrepancy.get('active_route_alignment') or '(missing)'}`",
            f"- Target hypothesis: `{route_transition_discrepancy.get('target_hypothesis_id') or '(none)'}`",
            f"- Artifact refs: `{', '.join(route_transition_discrepancy.get('discrepancy_artifact_refs') or []) or '(none)'}`",
            "",
            route_transition_discrepancy.get("discrepancy_summary") or "(missing)",
        ]
    )


def append_route_transition_repair_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    route_transition_repair = payload.get("route_transition_repair") or {}
    if not route_transition_repair:
        return
    lines.extend(
        [
            "",
            "## Route transition repair",
            "",
            f"- Repair status: `{route_transition_repair.get('repair_status') or '(missing)'}`",
            f"- Discrepancy status: `{route_transition_repair.get('discrepancy_status') or '(missing)'}`",
            f"- Discrepancy kind: `{route_transition_repair.get('discrepancy_kind') or '(missing)'}`",
            f"- Active local hypothesis: `{route_transition_repair.get('active_local_hypothesis_id') or '(none)'}`",
            f"- Target hypothesis: `{route_transition_repair.get('target_hypothesis_id') or '(none)'}`",
            f"- Active-route alignment: `{route_transition_repair.get('active_route_alignment') or '(missing)'}`",
            f"- Repair kind: `{route_transition_repair.get('repair_kind') or '(missing)'}`",
            f"- Primary repair ref: `{route_transition_repair.get('primary_repair_ref') or '(none)'}`",
            f"- Repair artifact refs: `{', '.join(route_transition_repair.get('repair_artifact_refs') or []) or '(none)'}`",
            "",
            route_transition_repair.get("repair_summary") or "(missing)",
        ]
    )


def append_route_transition_escalation_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    route_transition_escalation = payload.get("route_transition_escalation") or {}
    if not route_transition_escalation:
        return
    lines.extend(
        [
            "",
            "## Route transition escalation",
            "",
            f"- Escalation status: `{route_transition_escalation.get('escalation_status') or '(missing)'}`",
            f"- Repair status: `{route_transition_escalation.get('repair_status') or '(missing)'}`",
            f"- Repair kind: `{route_transition_escalation.get('repair_kind') or '(missing)'}`",
            f"- Primary repair ref: `{route_transition_escalation.get('primary_repair_ref') or '(none)'}`",
            f"- Checkpoint status: `{route_transition_escalation.get('checkpoint_status') or '(missing)'}`",
            f"- Checkpoint kind: `{route_transition_escalation.get('checkpoint_kind') or '(none)'}`",
            f"- Checkpoint ref: `{route_transition_escalation.get('checkpoint_ref') or '(none)'}`",
            "",
            route_transition_escalation.get("escalation_summary") or "(missing)",
        ]
    )


def append_route_transition_clearance_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    route_transition_clearance = payload.get("route_transition_clearance") or {}
    if not route_transition_clearance:
        return
    lines.extend(
        [
            "",
            "## Route transition clearance",
            "",
            f"- Clearance status: `{route_transition_clearance.get('clearance_status') or '(missing)'}`",
            f"- Clearance kind: `{route_transition_clearance.get('clearance_kind') or '(missing)'}`",
            f"- Escalation status: `{route_transition_clearance.get('escalation_status') or '(missing)'}`",
            f"- Repair status: `{route_transition_clearance.get('repair_status') or '(missing)'}`",
            f"- Checkpoint status: `{route_transition_clearance.get('checkpoint_status') or '(missing)'}`",
            f"- Checkpoint kind: `{route_transition_clearance.get('checkpoint_kind') or '(none)'}`",
            f"- Checkpoint ref: `{route_transition_clearance.get('checkpoint_ref') or '(none)'}`",
            f"- Follow-through ref: `{route_transition_clearance.get('followthrough_ref') or '(none)'}`",
            "",
            route_transition_clearance.get("clearance_summary") or "(missing)",
        ]
    )


def append_route_transition_followthrough_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    route_transition_followthrough = payload.get("route_transition_followthrough") or {}
    if not route_transition_followthrough:
        return
    lines.extend(
        [
            "",
            "## Route transition follow-through",
            "",
            f"- Follow-through status: `{route_transition_followthrough.get('followthrough_status') or '(missing)'}`",
            f"- Follow-through kind: `{route_transition_followthrough.get('followthrough_kind') or '(missing)'}`",
            f"- Clearance status: `{route_transition_followthrough.get('clearance_status') or '(missing)'}`",
            f"- Clearance kind: `{route_transition_followthrough.get('clearance_kind') or '(missing)'}`",
            f"- Escalation status: `{route_transition_followthrough.get('escalation_status') or '(missing)'}`",
            f"- Repair status: `{route_transition_followthrough.get('repair_status') or '(missing)'}`",
            f"- Checkpoint status: `{route_transition_followthrough.get('checkpoint_status') or '(missing)'}`",
            f"- Checkpoint ref: `{route_transition_followthrough.get('checkpoint_ref') or '(none)'}`",
            f"- Follow-through ref: `{route_transition_followthrough.get('followthrough_ref') or '(none)'}`",
            "",
            route_transition_followthrough.get("followthrough_summary") or "(missing)",
        ]
    )


def append_route_transition_resumption_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    route_transition_resumption = payload.get("route_transition_resumption") or {}
    if not route_transition_resumption:
        return
    lines.extend(
        [
            "",
            "## Route transition resumption",
            "",
            f"- Resumption status: `{route_transition_resumption.get('resumption_status') or '(missing)'}`",
            f"- Resumption kind: `{route_transition_resumption.get('resumption_kind') or '(missing)'}`",
            f"- Follow-through status: `{route_transition_resumption.get('followthrough_status') or '(missing)'}`",
            f"- Active-route alignment: `{route_transition_resumption.get('active_route_alignment') or '(missing)'}`",
            f"- Active local hypothesis: `{route_transition_resumption.get('active_local_hypothesis_id') or '(none)'}`",
            f"- Target hypothesis: `{route_transition_resumption.get('target_hypothesis_id') or '(none)'}`",
            f"- Follow-through ref: `{route_transition_resumption.get('followthrough_ref') or '(none)'}`",
            f"- Resumption ref: `{route_transition_resumption.get('resumption_ref') or '(none)'}`",
            "",
            route_transition_resumption.get("resumption_summary") or "(missing)",
        ]
    )


def append_route_transition_commitment_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    route_transition_commitment = payload.get("route_transition_commitment") or {}
    if not route_transition_commitment:
        return
    lines.extend(
        [
            "",
            "## Route transition commitment",
            "",
            f"- Commitment status: `{route_transition_commitment.get('commitment_status') or '(missing)'}`",
            f"- Commitment kind: `{route_transition_commitment.get('commitment_kind') or '(missing)'}`",
            f"- Resumption status: `{route_transition_commitment.get('resumption_status') or '(missing)'}`",
            f"- Resumption kind: `{route_transition_commitment.get('resumption_kind') or '(missing)'}`",
            f"- Active local hypothesis: `{route_transition_commitment.get('active_local_hypothesis_id') or '(none)'}`",
            f"- Route kind: `{route_transition_commitment.get('route_kind') or '(missing)'}`",
            f"- Route target ref: `{route_transition_commitment.get('route_target_ref') or '(none)'}`",
            f"- Resumption ref: `{route_transition_commitment.get('resumption_ref') or '(none)'}`",
            f"- Commitment ref: `{route_transition_commitment.get('commitment_ref') or '(none)'}`",
            "",
            route_transition_commitment.get("commitment_summary") or "(missing)",
        ]
    )


def append_route_transition_authority_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    route_transition_authority = payload.get("route_transition_authority") or {}
    if not route_transition_authority:
        return
    lines.extend(
        [
            "",
            "## Route transition authority",
            "",
            f"- Authority status: `{route_transition_authority.get('authority_status') or '(missing)'}`",
            f"- Authority kind: `{route_transition_authority.get('authority_kind') or '(missing)'}`",
            f"- Commitment status: `{route_transition_authority.get('commitment_status') or '(missing)'}`",
            f"- Commitment kind: `{route_transition_authority.get('commitment_kind') or '(missing)'}`",
            f"- Active local hypothesis: `{route_transition_authority.get('active_local_hypothesis_id') or '(none)'}`",
            f"- Route kind: `{route_transition_authority.get('route_kind') or '(missing)'}`",
            f"- Route target ref: `{route_transition_authority.get('route_target_ref') or '(none)'}`",
            f"- Commitment ref: `{route_transition_authority.get('commitment_ref') or '(none)'}`",
            f"- Authority ref: `{route_transition_authority.get('authority_ref') or '(none)'}`",
            "",
            route_transition_authority.get("authority_summary") or "(missing)",
        ]
    )


def append_l1_source_intake_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    l1_source_intake = payload.get("l1_source_intake") or {}
    lines.extend(
        [
            "",
            "## L1 source intake",
            "",
            f"- Source count: `{l1_source_intake.get('source_count') or 0}`",
            "",
            "## L1 intake summary",
            "",
        ]
    )
    for row in l1_assumption_depth_summary_lines(l1_source_intake) or ["(none)"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Source-backed assumptions",
            "",
        ]
    )
    for row in l1_source_intake.get("assumption_rows") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` [{row.get('reading_depth') or 'skim'}]: "
                f"{row.get('assumption') or '(missing)'}"
            )
            if row.get("evidence_excerpt"):
                lines.append(f"  evidence: {row.get('evidence_excerpt')}")
            if row.get("evidence_sentence_ids"):
                lines.append(f"  sentence ids: {', '.join(row.get('evidence_sentence_ids') or [])}")
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Source-backed regimes", ""])
    for row in l1_source_intake.get("regime_rows") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` [{row.get('reading_depth') or 'skim'}]: "
                f"{row.get('regime') or '(missing)'}"
            )
            if row.get("evidence_excerpt"):
                lines.append(f"  evidence: {row.get('evidence_excerpt')}")
            if row.get("evidence_sentence_ids"):
                lines.append(f"  sentence ids: {', '.join(row.get('evidence_sentence_ids') or [])}")
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Reading depth", ""])
    for row in l1_source_intake.get("reading_depth_rows") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` => `{row.get('reading_depth') or 'skim'}` "
                f"(basis: `{row.get('basis') or 'summary_only'}`)"
            )
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Method specificity", ""])
    for row in l1_source_intake.get("method_specificity_rows") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` [{row.get('reading_depth') or 'skim'}]: "
                f"`{row.get('method_family') or '(missing)'}` / `{row.get('specificity_tier') or '(missing)'}`"
            )
            if row.get("evidence_excerpt"):
                lines.append(f"  evidence: {row.get('evidence_excerpt')}")
            if row.get("evidence_sentence_ids"):
                lines.append(f"  sentence ids: {', '.join(row.get('evidence_sentence_ids') or [])}")
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Reading-depth limits", ""])
    for row in l1_reading_depth_limit_lines(l1_source_intake) or ["(none)"]:
        lines.append(f"- {row}")
    lines.extend(["", "## Contradiction candidates", ""])
    for row in l1_contradiction_summary_lines(l1_source_intake) or ["(none)"]:
        lines.append(f"- {row}")
    lines.extend(["", "## Notation-alignment tension", ""])
    for row in l1_notation_tension_lines(l1_source_intake) or ["(none)"]:
        lines.append(f"- {row}")
    lines.extend(["", "## Concept graph", ""])
    for row in l1_concept_graph_summary_lines(l1_source_intake) or ["(none)"]:
        lines.append(f"- {row}")


def append_l1_vault_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    l1_vault = payload.get("l1_vault") or {}
    raw = l1_vault.get("raw") or {}
    wiki = l1_vault.get("wiki") or {}
    output = l1_vault.get("output") or {}
    lines.extend(
        [
            "",
            "## L1 vault",
            "",
            f"- Status: `{l1_vault.get('status') or '(missing)'}`",
            f"- Root path: `{l1_vault.get('root_path') or '(missing)'}`",
            f"- Protocol path: `{l1_vault.get('protocol_path') or '(missing)'}`",
            "",
            "## L1 vault raw layer",
            "",
            f"- Manifest JSON: `{raw.get('manifest_path') or '(missing)'}`",
            f"- Manifest note: `{raw.get('note_path') or '(missing)'}`",
            f"- Source count: `{raw.get('source_count') or 0}`",
            "",
            "## L1 vault wiki layer",
            "",
            f"- Schema page: `{wiki.get('schema_path') or '(missing)'}`",
            f"- Home page: `{wiki.get('home_page_path') or '(missing)'}`",
            f"- Page count: `{wiki.get('page_count') or 0}`",
            "",
            "## L1 vault output layer",
            "",
            f"- Digest JSON: `{output.get('digest_path') or '(missing)'}`",
            f"- Digest note: `{output.get('digest_note_path') or '(missing)'}`",
            f"- Flowback log: `{output.get('flowback_log_path') or '(missing)'}`",
            f"- Flowback entries: `{output.get('flowback_entry_count') or 0}`",
            "",
            "## L1 vault compatibility refs",
            "",
        ]
    )
    for row in l1_vault.get("compatibility_refs") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('kind') or '(missing)'}` status=`{row.get('status') or 'missing'}` path=`{row.get('path') or '(missing)'}`"
            )
        else:
            lines.append(f"- {row}")


def append_source_intelligence_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    lines.extend(
        [
            "",
            "## Source intelligence",
            "",
            f"- JSON path: `{payload.get('path') or '(missing)'}`",
            f"- Note path: `{payload.get('note_path') or '(missing)'}`",
            f"- Canonical source ids: `{', '.join(payload.get('canonical_source_ids') or []) or '(none)'}`",
            f"- Citation edge count: `{len(payload.get('citation_edges') or [])}`",
            f"- Neighbor signal count: `{payload.get('neighbor_signal_count') or 0}`",
            f"- Cross-topic matches: `{payload.get('cross_topic_match_count') or 0}`",
            "",
            payload.get("summary") or "(missing)",
        ]
    )
    fidelity_summary = payload.get("fidelity_summary") or {}
    relevance_summary = payload.get("relevance_summary") or {}
    lines.extend(
        [
            "",
            "## Source fidelity",
            "",
            f"- Strongest tier: `{fidelity_summary.get('strongest_tier') or 'unknown'}`",
            f"- Weakest tier: `{fidelity_summary.get('weakest_tier') or 'unknown'}`",
            f"- Counts by tier: `{', '.join(f'{key}={value}' for key, value in (fidelity_summary.get('counts_by_tier') or {}).items()) or '(none)'}`",
            "",
            "## Source relevance",
            "",
            f"- Strongest tier: `{relevance_summary.get('strongest_tier') or 'irrelevant'}`",
            f"- Weakest tier: `{relevance_summary.get('weakest_tier') or 'irrelevant'}`",
            f"- Counts by tier: `{', '.join(f'{key}={value}' for key, value in (relevance_summary.get('counts_by_tier') or {}).items()) or '(none)'}`",
            f"- Role labels: `{', '.join(f'{key}={value}' for key, value in (relevance_summary.get('role_label_counts') or {}).items()) or '(none)'}`",
        ]
    )
    if payload.get("source_neighbors"):
        lines.extend(["", "### Neighbor highlights", ""])
        for row in (payload.get("source_neighbors") or [])[:6]:
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` ~ `{row.get('neighbor_source_id') or '(missing)'}` "
                f"via `{row.get('relation_kind') or '(missing)'}`"
            )


def append_graph_analysis_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    summary = payload.get("summary") or {}
    diff = payload.get("diff") or _zero_graph_diff()
    lines.extend(
        [
            "",
            "## Graph analysis",
            "",
            f"- JSON path: `{payload.get('path') or '(missing)'}`",
            f"- Note path: `{payload.get('note_path') or '(missing)'}`",
            f"- History path: `{payload.get('history_path') or '(missing)'}`",
            f"- Connection count: `{summary.get('connection_count') or 0}`",
            f"- Question count: `{summary.get('question_count') or 0}`",
            f"- History length: `{summary.get('history_length') or 0}`",
            "",
            "## Graph connections",
            "",
        ]
    )
    for row in payload.get("connections") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('kind') or '(missing)'}` `{row.get('bridge_label') or '(missing)'}`: "
                f"{row.get('detail') or '(missing)'}"
            )
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Graph question seeds", ""])
    for row in payload.get("questions") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('question_type') or '(missing)'}` `{row.get('bridge_label') or '(missing)'}`: "
                f"{row.get('question') or '(missing)'}"
            )
        else:
            lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Graph diff",
            "",
            f"- Added nodes: `{(diff.get('added') or {}).get('node_count') or 0}`",
            f"- Removed nodes: `{(diff.get('removed') or {}).get('node_count') or 0}`",
            f"- Added labels: `{', '.join((diff.get('added') or {}).get('node_labels') or []) or '(none)'}`",
            f"- Removed labels: `{', '.join((diff.get('removed') or {}).get('node_labels') or []) or '(none)'}`",
        ]
    )


def normalized_graph_analysis(
    *,
    topic_slug: str,
    shell_surfaces: dict[str, Any],
    relativize: Callable[[Path], str],
) -> dict[str, Any]:
    payload = dict(shell_surfaces.get("graph_analysis") or empty_graph_analysis(topic_slug=topic_slug))
    if shell_surfaces.get("graph_analysis_path"):
        payload["path"] = relativize(Path(shell_surfaces["graph_analysis_path"]))
    if shell_surfaces.get("graph_analysis_note_path"):
        payload["note_path"] = relativize(Path(shell_surfaces["graph_analysis_note_path"]))
    if shell_surfaces.get("graph_analysis_history_path"):
        payload["history_path"] = relativize(Path(shell_surfaces["graph_analysis_history_path"]))
    payload.setdefault("connections", [])
    payload.setdefault("questions", [])
    payload.setdefault("diff", _zero_graph_diff())
    payload.setdefault("summary", {"connection_count": 0, "question_count": 0, "history_length": 0})
    return payload


def normalized_source_intelligence(
    *,
    topic_slug: str,
    shell_surfaces: dict[str, Any],
    relativize: Callable[[Path], str],
) -> dict[str, Any]:
    payload = dict(shell_surfaces.get("source_intelligence") or empty_source_intelligence(topic_slug=topic_slug))
    if shell_surfaces.get("source_intelligence_path"):
        payload["path"] = relativize(Path(shell_surfaces["source_intelligence_path"]))
    if shell_surfaces.get("source_intelligence_note_path"):
        payload["note_path"] = relativize(Path(shell_surfaces["source_intelligence_note_path"]))
    payload.setdefault("relevance_rows", [])
    payload.setdefault(
        "relevance_summary",
        {
            "source_count": 0,
            "counts_by_tier": {},
            "strongest_tier": "irrelevant",
            "weakest_tier": "irrelevant",
            "role_label_counts": {},
        },
    )
    return payload


def build_active_research_contract_payload(
    *,
    research_contract: dict[str, Any],
    validation_contract: dict[str, Any],
    shell_surfaces: dict[str, Any],
    relativize: Callable[[Path], str],
) -> dict[str, Any]:
    runtime_surface_root = Path(shell_surfaces["research_question_contract_path"]).parent
    topic_slug = str(research_contract.get("topic_slug") or "").strip()
    if not topic_slug:
        topic_slug = (
            runtime_surface_root.parent.name
            if runtime_surface_root.name == "runtime"
            else runtime_surface_root.name
        )
    competing_hypotheses = normalize_competing_hypotheses(
        research_contract.get("competing_hypotheses") or [],
        topic_slug=topic_slug,
    )
    leading_hypothesis = leading_competing_hypothesis(competing_hypotheses) or {}
    current_branch = active_branch_hypothesis(competing_hypotheses) or {}
    deferred_branch_hypotheses = hypotheses_for_route(competing_hypotheses, route_kind="deferred_buffer")
    followup_branch_hypotheses = hypotheses_for_route(competing_hypotheses, route_kind="followup_subtopic")
    route_activation = build_route_activation_payload(
        topic_slug=topic_slug,
        competing_hypotheses=competing_hypotheses,
        topic_status_explainability=shell_surfaces.get("topic_state_explainability") or {},
    )
    route_reentry = build_route_reentry_payload(
        topic_slug=topic_slug,
        competing_hypotheses=competing_hypotheses,
        topic_root=runtime_surface_root,
    )
    route_handoff = build_route_handoff_payload(
        topic_slug=topic_slug,
        competing_hypotheses=competing_hypotheses,
        route_activation=route_activation,
        route_reentry=route_reentry,
    )
    route_choice = build_route_choice_payload(
        topic_slug=topic_slug,
        topic_status_explainability=shell_surfaces.get("topic_state_explainability") or {},
        route_activation=route_activation,
        route_handoff=route_handoff,
    )
    route_transition_gate = build_route_transition_gate_payload(
        topic_slug=topic_slug,
        route_choice=route_choice,
        operator_checkpoint=shell_surfaces.get("operator_checkpoint") or {},
    )
    route_transition_intent = build_route_transition_intent_payload(
        topic_slug=topic_slug,
        route_choice=route_choice,
        route_transition_gate=route_transition_gate,
    )
    route_transition_receipt = build_route_transition_receipt_payload(
        topic_slug=topic_slug,
        route_transition_intent=route_transition_intent,
        transition_history=_read_json(runtime_surface_root / "transition_history.json") or {
            "path": _truth_runtime_ref(topic_slug, "transition_history.json"),
            "note_path": _truth_runtime_ref(topic_slug, "transition_history.md"),
            "latest_transition": {},
        },
    )
    route_transition_resolution = build_route_transition_resolution_payload(
        topic_slug=topic_slug,
        route_transition_intent=route_transition_intent,
        route_transition_receipt=route_transition_receipt,
        route_activation=route_activation,
    )
    route_transition_discrepancy = build_route_transition_discrepancy_payload(
        topic_slug=topic_slug,
        route_transition_resolution=route_transition_resolution,
        route_transition_receipt=route_transition_receipt,
    )
    operator_checkpoint = shell_surfaces.get("operator_checkpoint") or {}
    route_transition_repair = build_route_transition_repair_payload(
        topic_slug=topic_slug,
        route_transition_discrepancy=route_transition_discrepancy,
        route_transition_resolution=route_transition_resolution,
        route_activation=route_activation,
    )
    route_transition_escalation = build_route_transition_escalation_payload(
        topic_slug=topic_slug,
        route_transition_repair=route_transition_repair,
        operator_checkpoint=operator_checkpoint,
    )
    route_transition_clearance = build_route_transition_clearance_payload(
        topic_slug=topic_slug,
        route_transition_escalation=route_transition_escalation,
        operator_checkpoint=operator_checkpoint,
    )
    route_transition_followthrough = build_route_transition_followthrough_payload(
        topic_slug=topic_slug,
        route_transition_clearance=route_transition_clearance,
    )
    route_transition_resumption = build_route_transition_resumption_payload(
        topic_slug=topic_slug,
        route_transition_followthrough=route_transition_followthrough,
        route_transition_resolution=route_transition_resolution,
        route_activation=route_activation,
        transition_history=_read_json(runtime_surface_root / "transition_history.json") or {},
    )
    route_transition_commitment = build_route_transition_commitment_payload(
        topic_slug=topic_slug,
        route_transition_resumption=route_transition_resumption,
        route_activation=route_activation,
        competing_hypotheses=competing_hypotheses,
    )
    route_transition_authority = build_route_transition_authority_payload(
        topic_slug=topic_slug,
        route_transition_commitment=route_transition_commitment,
        route_activation=route_activation,
    )
    return {
        "question_id": str(research_contract.get("question_id") or ""),
        "title": str(research_contract.get("title") or ""),
        "status": str(research_contract.get("status") or ""),
        "template_mode": str(research_contract.get("template_mode") or ""),
        "research_mode": str(research_contract.get("research_mode") or ""),
        "validation_mode": str(validation_contract.get("validation_mode") or ""),
        "target_layers": [str(item) for item in (research_contract.get("target_layers") or []) if str(item).strip()],
        "question": str(research_contract.get("question") or ""),
        "competing_hypothesis_count": len(competing_hypotheses),
        "leading_hypothesis_id": str(leading_hypothesis.get("hypothesis_id") or ""),
        "active_branch_hypothesis_id": str(current_branch.get("hypothesis_id") or ""),
        "deferred_branch_hypothesis_ids": [
            str(row.get("hypothesis_id") or "")
            for row in deferred_branch_hypotheses
            if str(row.get("hypothesis_id") or "").strip()
        ],
        "followup_branch_hypothesis_ids": [
            str(row.get("hypothesis_id") or "")
            for row in followup_branch_hypotheses
            if str(row.get("hypothesis_id") or "").strip()
        ],
        "route_activation": route_activation,
        "route_reentry": route_reentry,
        "route_handoff": route_handoff,
        "route_choice": route_choice,
        "route_transition_gate": route_transition_gate,
        "route_transition_intent": route_transition_intent,
        "route_transition_receipt": route_transition_receipt,
        "route_transition_resolution": route_transition_resolution,
        "route_transition_discrepancy": route_transition_discrepancy,
        "route_transition_repair": route_transition_repair,
        "route_transition_escalation": route_transition_escalation,
        "route_transition_clearance": route_transition_clearance,
        "route_transition_followthrough": route_transition_followthrough,
        "route_transition_resumption": route_transition_resumption,
        "route_transition_commitment": route_transition_commitment,
        "route_transition_authority": route_transition_authority,
        "competing_hypotheses": competing_hypotheses,
        "l1_source_intake": research_contract.get("l1_source_intake") or empty_l1_source_intake(),
        "l1_vault": research_contract.get("l1_vault") or empty_l1_vault(topic_slug=topic_slug),
        "path": relativize(Path(shell_surfaces["research_question_contract_path"])),
        "note_path": relativize(Path(shell_surfaces["research_question_contract_note_path"])),
    }
