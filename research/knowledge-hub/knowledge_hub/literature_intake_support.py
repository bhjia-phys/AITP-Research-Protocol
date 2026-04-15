from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .graph_analysis_tools import suggest_questions, surprising_connections
from .l2_graph import stage_l2_insight
from .l2_staging import materialize_workspace_staging_manifest


ALLOWED_LITERATURE_UNIT_TYPES = {
    "concept",
    "physical_picture",
    "method",
    "warning_note",
    "claim_card",
    "workflow",
}
GENERIC_NOTATION_TOKENS = {
    "class",
    "classes",
    "considered",
    "consider",
    "study",
    "studied",
    "system",
    "systems",
}
WEAK_METHOD_FAMILIES = {"unspecified_method", "unknown", "generic_method"}


def _slugify_token(value: str) -> str:
    lowered = str(value or "").strip().lower()
    normalized = "".join(ch if ch.isalnum() else "-" for ch in lowered)
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    return normalized.strip("-") or "source"


def _dedupe_strings(values: list[str] | None) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in values or []:
        value = str(item or "").strip()
        if value and value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _source_slug_from_id(source_id: str) -> str:
    return _slugify_token(source_id)


def _source_payload(*, source_id: str, source_title: str) -> dict[str, Any]:
    resolved_source_id = str(source_id or "").strip()
    resolved_source_title = str(source_title or resolved_source_id or "Current source").strip()
    return {
        "source_refs": [resolved_source_id] if resolved_source_id else [],
        "provenance": {
            "source_id": resolved_source_id,
            "source_slug": _source_slug_from_id(resolved_source_id) if resolved_source_id else "",
            "source_title": resolved_source_title,
        },
    }


def _is_generic_notation_token(value: str) -> bool:
    token = _slugify_token(value).replace("-", "_")
    return token in GENERIC_NOTATION_TOKENS


def _should_stage_method_row(*, method_family: str, specificity_tier: str) -> bool:
    normalized_family = str(method_family or "").strip().lower()
    normalized_specificity = str(specificity_tier or "").strip().lower()
    if normalized_family in WEAK_METHOD_FAMILIES:
        return False
    if normalized_specificity in {"surface_hint", "unknown"} and normalized_family in {"method", "analysis"}:
        return False
    return True


def _should_stage_notation_row(*, symbol: str, meaning: str) -> bool:
    resolved_symbol = str(symbol or "").strip()
    resolved_meaning = str(meaning or "").strip()
    if not resolved_symbol or not resolved_meaning:
        return False
    if _is_generic_notation_token(resolved_symbol):
        return False
    if _is_generic_notation_token(resolved_meaning):
        return False
    return True


def _graph_diff_labels(diff: dict[str, Any], side: str) -> list[str]:
    side_payload = diff.get(side) or {}
    return _dedupe_strings([str(item) for item in (side_payload.get("node_labels") or [])])


def compute_literature_intake_stage_signature(runtime_payload: dict[str, Any]) -> str:
    active_research_contract = runtime_payload.get("active_research_contract") or {}
    signature_payload = {
        "runtime_mode": str(runtime_payload.get("runtime_mode") or "").strip(),
        "active_submode": str(runtime_payload.get("active_submode") or "").strip(),
        "l1_source_intake": active_research_contract.get("l1_source_intake") or {},
        "graph_analysis_diff": ((runtime_payload.get("graph_analysis") or {}).get("diff") or {}),
    }
    encoded = json.dumps(
        signature_payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha1(encoded).hexdigest()


def _derive_candidate_units_from_runtime_payload(
    *,
    topic_slug: str,
    runtime_payload: dict[str, Any],
) -> dict[str, Any]:
    active_research_contract = runtime_payload.get("active_research_contract") or {}
    l1_source_intake = active_research_contract.get("l1_source_intake") or {}
    l1_vault = active_research_contract.get("l1_vault") or {}
    wiki_page_paths = _dedupe_strings([str(item) for item in ((l1_vault.get("wiki") or {}).get("page_paths") or [])])

    candidate_units: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()
    source_slug = ""

    def _append_candidate(unit: dict[str, Any]) -> None:
        key = (
            str(unit.get("candidate_unit_type") or "").strip(),
            str(unit.get("title") or "").strip().lower(),
        )
        if not key[0] or not key[1] or key in seen_keys:
            return
        seen_keys.add(key)
        candidate_units.append(unit)

    for row in l1_source_intake.get("assumption_rows") or []:
        source_id = str(row.get("source_id") or "").strip()
        if not source_slug and source_id:
            source_slug = _slugify_token(source_id)
        source_title = str(row.get("source_title") or source_id or "Current source").strip()
        assumption = str(row.get("assumption") or "").strip()
        if not assumption:
            continue
        reading_depth = str(row.get("reading_depth") or "unknown").strip()
        evidence_excerpt = str(row.get("evidence_excerpt") or "").strip()
        summary = f"{source_title} makes the bounded source-side assumption: {assumption}"
        if evidence_excerpt:
            summary += f" Evidence: {evidence_excerpt}"
        _append_candidate(
            {
                "candidate_unit_type": "claim_card",
                "title": f"{source_title} assumption: {assumption[:72]}",
                "summary": summary,
                "tags": _dedupe_strings(
                    [
                        "literature-intake",
                        "source-assumption",
                        f"reading-depth:{_slugify_token(reading_depth)}",
                    ]
                ),
                "wiki_page_paths": wiki_page_paths,
                "assumptions": [assumption],
                **_source_payload(source_id=source_id, source_title=source_title),
            }
        )

    for row in l1_source_intake.get("regime_rows") or []:
        source_id = str(row.get("source_id") or "").strip()
        if not source_slug and source_id:
            source_slug = _slugify_token(source_id)
        source_title = str(row.get("source_title") or source_id or "Current source").strip()
        regime = str(row.get("regime") or "").strip()
        if not regime:
            continue
        reading_depth = str(row.get("reading_depth") or "unknown").strip()
        evidence_excerpt = str(row.get("evidence_excerpt") or "").strip()
        summary = f"{source_title} is explicitly operating in the regime `{regime}`."
        if evidence_excerpt:
            summary += f" Evidence: {evidence_excerpt}"
        _append_candidate(
            {
                "candidate_unit_type": "concept",
                "title": f"{source_title} regime: {regime}",
                "summary": summary,
                "tags": _dedupe_strings(
                    [
                        "literature-intake",
                        "regime-surface",
                        f"reading-depth:{_slugify_token(reading_depth)}",
                    ]
                ),
                "wiki_page_paths": wiki_page_paths,
                **_source_payload(source_id=source_id, source_title=source_title),
            }
        )

    for row in l1_source_intake.get("method_specificity_rows") or []:
        source_id = str(row.get("source_id") or "").strip()
        if not source_slug and source_id:
            source_slug = _slugify_token(source_id)
        source_title = str(row.get("source_title") or source_id or "Current source").strip()
        method_family = str(row.get("method_family") or "unspecified_method").strip()
        specificity_tier = str(row.get("specificity_tier") or "unknown").strip()
        if not _should_stage_method_row(method_family=method_family, specificity_tier=specificity_tier):
            continue
        reading_depth = str(row.get("reading_depth") or "unknown").strip()
        evidence_excerpt = str(row.get("evidence_excerpt") or "").strip()
        summary = (
            f"{source_title} currently reads as `{method_family}` with `{specificity_tier}` specificity "
            f"at `{reading_depth}` depth."
        )
        if evidence_excerpt:
            summary += f" Evidence: {evidence_excerpt}"
        _append_candidate(
            {
                "candidate_unit_type": "method",
                "title": f"{source_title} {method_family} method signal",
                "summary": summary,
                "tags": _dedupe_strings(
                    [
                        "literature-intake",
                        f"method-family:{_slugify_token(method_family)}",
                        f"specificity:{_slugify_token(specificity_tier)}",
                        f"reading-depth:{_slugify_token(reading_depth)}",
                    ]
                ),
                "wiki_page_paths": wiki_page_paths,
                **_source_payload(source_id=source_id, source_title=source_title),
            }
        )

    for row in l1_source_intake.get("notation_rows") or []:
        source_id = str(row.get("source_id") or "").strip()
        if not source_slug and source_id:
            source_slug = _slugify_token(source_id)
        source_title = str(row.get("source_title") or source_id or "Current source").strip()
        symbol = str(row.get("symbol") or "").strip()
        meaning = str(row.get("meaning") or "").strip()
        if not _should_stage_notation_row(symbol=symbol, meaning=meaning):
            continue
        reading_depth = str(row.get("reading_depth") or "unknown").strip()
        evidence_excerpt = str(row.get("evidence_excerpt") or "").strip()
        summary = f"In {source_title}, `{symbol}` denotes {meaning}."
        if evidence_excerpt:
            summary += f" Evidence: {evidence_excerpt}"
        _append_candidate(
            {
                "candidate_unit_type": "concept",
                "title": f"{source_title} notation `{symbol}`",
                "summary": summary,
                "tags": _dedupe_strings(
                    [
                        "literature-intake",
                        "notation-binding",
                        f"symbol:{_slugify_token(symbol)}",
                        f"reading-depth:{_slugify_token(reading_depth)}",
                    ]
                ),
                "wiki_page_paths": wiki_page_paths,
                **_source_payload(source_id=source_id, source_title=source_title),
            }
        )

    for row in l1_source_intake.get("contradiction_candidates") or []:
        source_id = str(row.get("source_id") or "").strip()
        if not source_slug and source_id:
            source_slug = _slugify_token(source_id)
        source_title = str(row.get("source_title") or source_id or "Current source").strip()
        against_source_title = str(row.get("against_source_title") or row.get("against_source_id") or "comparison source").strip()
        detail = str(row.get("detail") or "").strip()
        if not detail:
            continue
        _append_candidate(
            {
                "candidate_unit_type": "warning_note",
                "title": f"{source_title} contradiction watch against {against_source_title}",
                "summary": (
                    f"Potential contradiction detected during literature intake: {detail}. "
                    "Keep this as provisional warning memory until a later audit resolves the conflict."
                ),
                "tags": _dedupe_strings(
                    [
                        "literature-intake",
                        "contradiction-watch",
                        f"source:{_slugify_token(source_title)}",
                        f"against:{_slugify_token(against_source_title)}",
                    ]
                ),
                "wiki_page_paths": wiki_page_paths,
                **_source_payload(source_id=source_id, source_title=source_title),
            }
        )

    for row in l1_source_intake.get("notation_tension_candidates") or []:
        source_id = str(row.get("source_id") or "").strip()
        if not source_slug and source_id:
            source_slug = _slugify_token(source_id)
        source_title = str(row.get("source_title") or source_id or "Current source").strip()
        against_source_title = str(row.get("against_source_title") or row.get("against_source_id") or "comparison source").strip()
        meaning = str(row.get("meaning") or "").strip()
        existing_symbol = str(row.get("existing_symbol") or "").strip()
        incoming_symbol = str(row.get("incoming_symbol") or "").strip()
        if not meaning or not existing_symbol or not incoming_symbol:
            continue
        _append_candidate(
            {
                "candidate_unit_type": "warning_note",
                "title": f"{source_title} notation tension against {against_source_title}",
                "summary": (
                    f"Notation tension detected for `{meaning}`: existing symbol `{existing_symbol}` versus incoming symbol "
                    f"`{incoming_symbol}` between {source_title} and {against_source_title}."
                ),
                "tags": _dedupe_strings(
                    [
                        "literature-intake",
                        "notation-tension",
                        f"existing-symbol:{_slugify_token(existing_symbol)}",
                        f"incoming-symbol:{_slugify_token(incoming_symbol)}",
                    ]
                ),
                "wiki_page_paths": wiki_page_paths,
                **_source_payload(source_id=source_id, source_title=source_title),
            }
        )

    concept_graph = l1_source_intake.get("concept_graph") or {}
    for row in surprising_connections(concept_graph):
        source_ids = _dedupe_strings([str(item) for item in (row.get("source_ids") or [])])
        if not source_slug and source_ids:
            source_slug = _slugify_token(source_ids[0])
        bridge_label = str(row.get("bridge_label") or "").strip()
        source_titles = _dedupe_strings([str(item) for item in (row.get("source_titles") or [])])
        community_labels = _dedupe_strings([str(item) for item in (row.get("community_labels") or [])])
        if not bridge_label or len(source_titles) < 2:
            continue
        summary = (
            f"Concept-graph analysis links {source_titles[0]} and {source_titles[1]} through `{bridge_label}`. "
            f"{str(row.get('detail') or '').strip()}"
        ).strip()
        _append_candidate(
            {
                "candidate_unit_type": "physical_picture",
                "title": f"Graph bridge: {bridge_label}",
                "summary": summary,
                "tags": _dedupe_strings(
                    [
                        "literature-intake",
                        "graph-analysis",
                        "surprising-connection",
                        f"bridge:{_slugify_token(bridge_label)}",
                    ]
                ),
                "wiki_page_paths": wiki_page_paths,
                "notes": "This bridge is graph-derived and still requires a later human audit before canonical promotion.",
                "provenance": {
                    "graph_analysis_kind": str(row.get("kind") or "").strip() or "surprising_connection",
                    "bridge_label": bridge_label,
                    "source_ids": source_ids,
                    "community_labels": community_labels,
                },
            }
        )

    for row in suggest_questions(concept_graph):
        source_ids = _dedupe_strings([str(item) for item in (row.get("source_ids") or [])])
        if not source_slug and source_ids:
            source_slug = _slugify_token(source_ids[0])
        bridge_label = str(row.get("bridge_label") or "").strip()
        question = str(row.get("question") or "").strip()
        if not bridge_label or not question:
            continue
        _append_candidate(
            {
                "candidate_unit_type": "workflow",
                "title": f"Graph question seed: {bridge_label}",
                "summary": question,
                "tags": _dedupe_strings(
                    [
                        "literature-intake",
                        "graph-analysis",
                        "question-seed",
                        f"bridge:{_slugify_token(bridge_label)}",
                    ]
                ),
                "wiki_page_paths": wiki_page_paths,
                "notes": "This follow-up route is graph-derived and should be treated as a provisional question seed.",
                "provenance": {
                    "graph_analysis_kind": str(row.get("graph_analysis_kind") or "").strip() or "graph_question",
                    "question_type": str(row.get("question_type") or "").strip() or "bridge_question",
                    "bridge_label": bridge_label,
                    "source_ids": source_ids,
                    "community_labels": _dedupe_strings([str(item) for item in (row.get("community_labels") or [])]),
                },
            }
        )

    graph_analysis = runtime_payload.get("graph_analysis") or {}
    graph_diff = graph_analysis.get("diff") or {}
    added_labels = _graph_diff_labels(graph_diff, "added")
    removed_labels = _graph_diff_labels(graph_diff, "removed")
    if added_labels:
        _append_candidate(
            {
                "candidate_unit_type": "claim_card",
                "title": f"Graph diff surfaced: {added_labels[0]}",
                "summary": (
                    "Cross-iteration graph analysis surfaced newly active concepts: "
                    f"{', '.join(added_labels[:4])}. Keep this as a provisional claim card until the route is re-audited."
                ),
                "tags": _dedupe_strings(
                    [
                        "literature-intake",
                        "graph-analysis",
                        "graph-diff",
                        "graph-diff-added",
                    ]
                ),
                "wiki_page_paths": wiki_page_paths,
                "notes": "This staging unit was derived from graph-diff growth and still requires later human adjudication.",
                "provenance": {
                    "graph_analysis_kind": "graph_diff_added",
                },
            }
        )
    if removed_labels:
        _append_candidate(
            {
                "candidate_unit_type": "warning_note",
                "title": f"Graph diff retired: {removed_labels[0]}",
                "summary": (
                    "Cross-iteration graph analysis retired previously active concepts: "
                    f"{', '.join(removed_labels[:4])}. Treat this as a bounded warning until the route is reconciled."
                ),
                "tags": _dedupe_strings(
                    [
                        "literature-intake",
                        "graph-analysis",
                        "graph-diff",
                        "graph-diff-removed",
                    ]
                ),
                "wiki_page_paths": wiki_page_paths,
                "notes": "This warning was derived from graph-diff shrinkage and should trigger later route reconciliation.",
                "provenance": {
                    "graph_analysis_kind": "graph_diff_removed",
                },
            }
        )

    return {
        "topic_slug": topic_slug,
        "source_slug": source_slug or _slugify_token(topic_slug),
        "candidate_units": candidate_units,
    }


def stage_literature_units(
    kernel_root: Path,
    *,
    topic_slug: str,
    source_slug: str,
    candidate_units: list[dict[str, Any]],
    created_by: str = "aitp-cli",
) -> dict[str, Any]:
    resolved_kernel_root = kernel_root.resolve()
    resolved_topic_slug = str(topic_slug or "").strip()
    resolved_source_slug = str(source_slug or "").strip()
    if not resolved_topic_slug:
        raise ValueError("topic_slug is required")
    if not resolved_source_slug:
        raise ValueError("source_slug is required")
    if not candidate_units:
        raise ValueError("candidate_units must not be empty")

    entries: list[dict[str, Any]] = []
    for unit in candidate_units:
        candidate_unit_type = str(unit.get("candidate_unit_type") or unit.get("unit_type") or "").strip()
        if candidate_unit_type not in ALLOWED_LITERATURE_UNIT_TYPES:
            raise ValueError(
                f"candidate_unit_type must be one of {sorted(ALLOWED_LITERATURE_UNIT_TYPES)} for literature fast path"
            )
        title = str(unit.get("title") or "").strip()
        summary = str(unit.get("summary") or "").strip()
        if not title or not summary:
            raise ValueError("Each literature unit requires non-empty title and summary")

        wiki_page_paths = _dedupe_strings([str(item) for item in (unit.get("wiki_page_paths") or [])])
        source_refs = _dedupe_strings(
            [str(item) for item in (unit.get("source_refs") or [])]
            or wiki_page_paths
            or [f"topics/{resolved_topic_slug}/L1/vault/wiki/source-intake.md"]
        )
        integration_summary = str(unit.get("integration_summary") or "").strip() or (
            f"Staged from L1 literature intake for source `{resolved_source_slug}`."
        )
        notes = str(unit.get("notes") or "").strip() or (
            "This staging entry came from the literature-intake fast path and still requires a later full audit."
        )
        unit_provenance = unit.get("provenance") or {}
        if not isinstance(unit_provenance, dict):
            unit_provenance = {}
        unit_source_id = str(unit_provenance.get("source_id") or "").strip()
        unit_source_title = str(unit_provenance.get("source_title") or "").strip()
        unit_source_slug = (
            str(unit.get("source_slug") or unit_provenance.get("source_slug") or "").strip()
            or (_source_slug_from_id(unit_source_id) if unit_source_id else "")
            or resolved_source_slug
        )
        if unit_source_id and unit_source_id not in source_refs:
            source_refs = [unit_source_id, *source_refs]
        entry = stage_l2_insight(
            resolved_kernel_root,
            title=title,
            summary=summary,
            candidate_unit_type=candidate_unit_type,
            tags=_dedupe_strings(
                [str(item) for item in (unit.get("tags") or [])]
                + ["literature-intake", f"source:{unit_source_slug}"]
            ),
            source_refs=source_refs,
            created_by=created_by,
            assumptions=_dedupe_strings([str(item) for item in (unit.get("assumptions") or [])]),
            linked_unit_ids=_dedupe_strings([str(item) for item in (unit.get("linked_unit_ids") or [])]),
            contradicts_unit_ids=_dedupe_strings([str(item) for item in (unit.get("contradicts_unit_ids") or [])]),
            integration_summary=integration_summary,
            scope_note=str(unit.get("scope_note") or "").strip(),
            topic_slug=resolved_topic_slug,
            notes=notes,
            provenance={
                **unit_provenance,
                "literature_intake_fast_path": True,
                "source_id": unit_source_id,
                "source_title": unit_source_title,
                "source_slug": unit_source_slug,
                "vault_wiki_paths": wiki_page_paths,
            },
        )
        entries.append(entry)

    manifest = materialize_workspace_staging_manifest(resolved_kernel_root)
    return {
        "topic_slug": resolved_topic_slug,
        "source_slug": resolved_source_slug,
        "entry_count": len(entries),
        "entries": entries,
        "manifest_json_path": manifest["json_path"],
        "manifest_markdown_path": manifest["markdown_path"],
        "manifest": manifest["payload"],
    }


def derive_literature_stage_payload_from_runtime_payload(
    *,
    topic_slug: str,
    runtime_payload: dict[str, Any],
) -> dict[str, Any]:
    return _derive_candidate_units_from_runtime_payload(
        topic_slug=topic_slug,
        runtime_payload=runtime_payload,
    )
