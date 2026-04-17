from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .topic_truth_root_support import compatibility_projection_path
from .tpkn_bridge import choose_source_row


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    compatibility_path = compatibility_projection_path(path)
    if compatibility_path is not None and compatibility_path != path:
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        compatibility_path.write_text(rendered, encoding="utf-8")


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "aitp-topic"


def _normalize_candidate_support_fields(
    self,
    *,
    candidate: dict[str, Any],
    supporting_regression_question_ids: list[str] | None,
    supporting_oracle_ids: list[str] | None,
    supporting_regression_run_ids: list[str] | None,
    promotion_blockers: list[str] | None,
    split_required: bool | None,
    cited_recovery_required: bool | None,
    followup_gap_ids: list[str] | None,
) -> dict[str, Any]:
    return {
        "candidate_question_ids": self._dedupe_strings(
            supporting_regression_question_ids
            if supporting_regression_question_ids is not None
            else list(candidate.get("supporting_regression_question_ids") or [])
        ),
        "candidate_oracle_ids": self._dedupe_strings(
            supporting_oracle_ids
            if supporting_oracle_ids is not None
            else list(candidate.get("supporting_oracle_ids") or [])
        ),
        "candidate_regression_run_ids": self._dedupe_strings(
            supporting_regression_run_ids
            if supporting_regression_run_ids is not None
            else list(candidate.get("supporting_regression_run_ids") or [])
        ),
        "candidate_promotion_blockers": self._dedupe_strings(
            promotion_blockers
            if promotion_blockers is not None
            else list(candidate.get("promotion_blockers") or [])
        ),
        "candidate_split_required": _as_bool(split_required)
        if split_required is not None
        else _as_bool(candidate.get("split_required")),
        "candidate_cited_recovery_required": _as_bool(cited_recovery_required)
        if cited_recovery_required is not None
        else _as_bool(candidate.get("cited_recovery_required")),
        "candidate_followup_gap_ids": self._dedupe_strings(
            followup_gap_ids
            if followup_gap_ids is not None
            else list(candidate.get("followup_gap_ids") or [])
        ),
    }


def _normalize_source_sections(
    self,
    *,
    candidate_id: str,
    source_sections: list[str] | None,
    covered_sections: list[str] | None,
) -> tuple[list[str], list[str], list[dict[str, str]]]:
    canonical_source_sections = self._dedupe_strings(source_sections or [])
    canonical_covered_sections = self._dedupe_strings(covered_sections or canonical_source_sections)
    if not canonical_source_sections and canonical_covered_sections:
        canonical_source_sections = list(canonical_covered_sections)
    if not canonical_source_sections:
        canonical_source_sections = [f"{_slugify(candidate_id)}/overview"]
        canonical_covered_sections = list(canonical_source_sections)

    covered_lookup = set(canonical_covered_sections)
    section_statuses = [
        {
            "section_id": section_id,
            "status": "covered" if section_id in covered_lookup else "missing",
        }
        for section_id in canonical_source_sections
    ]
    existing_ids = {row["section_id"] for row in section_statuses}
    for section_id in canonical_covered_sections:
        if section_id not in existing_ids:
            section_statuses.append({"section_id": section_id, "status": "covered"})
    return canonical_source_sections, canonical_covered_sections, section_statuses


def _normalize_notation_rows(notation_bindings: list[dict[str, str]] | None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for binding in notation_bindings or []:
        symbol = str(binding.get("symbol") or "").strip()
        meaning = str(binding.get("meaning") or "").strip()
        if symbol and meaning:
            rows.append({"symbol": symbol, "meaning": meaning})
    return rows


def _normalize_derivation_rows(
    self,
    *,
    derivation_nodes: list[str] | None,
    derivation_edges: list[dict[str, str]] | None,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    node_rows = [{"id": node, "label": node} for node in self._dedupe_strings(derivation_nodes or [])]
    edge_rows: list[dict[str, str]] = []
    for edge in derivation_edges or []:
        source = str(edge.get("source") or "").strip()
        target = str(edge.get("target") or "").strip()
        relation = str(edge.get("relation") or "").strip() or "depends_on"
        if source and target:
            edge_rows.append({"source": source, "target": target, "relation": relation})
    return node_rows, edge_rows


def _normalize_votes(
    *,
    agent_votes: list[dict[str, str]] | None,
    consensus_status: str,
) -> list[dict[str, str]]:
    normalized_votes: list[dict[str, str]] = []
    for row in agent_votes or []:
        role = str(row.get("role") or "").strip()
        verdict = str(row.get("verdict") or "").strip()
        if not role or not verdict:
            continue
        normalized_votes.append(
            {
                "role": role,
                "verdict": verdict,
                "notes": str(row.get("notes") or "").strip(),
            }
        )
    if normalized_votes:
        return normalized_votes
    return [
        {"role": "structure", "verdict": "covered", "notes": ""},
        {"role": "skeptic", "verdict": "no_major_gap", "notes": ""},
        {"role": "adjudicator", "verdict": consensus_status, "notes": ""},
    ]


def _compute_coverage_status_and_score(
    *,
    canonical_source_sections: list[str],
    canonical_covered_sections: list[str],
    section_statuses: list[dict[str, str]],
    critical_unit_recall: float,
    missing_anchor_count: int,
    skeptic_major_gap_count: int,
    consensus_status: str,
) -> tuple[str, float]:
    coverage_status = (
        "pass"
        if canonical_source_sections
        and all(row["status"] == "covered" for row in section_statuses if row["section_id"] in canonical_source_sections)
        and missing_anchor_count == 0
        and skeptic_major_gap_count == 0
        and critical_unit_recall >= 0.95
        and consensus_status in {"unanimous", "majority"}
        else "needs_revision"
    )
    coverage_score = round(
        max(
            0.0,
            min(
                1.0,
                (
                    (len(canonical_covered_sections) / max(1, len(canonical_source_sections))) * 0.5
                    + critical_unit_recall * 0.35
                    + (0.15 if skeptic_major_gap_count == 0 else 0.0)
                ),
            ),
        ),
        3,
    )
    return coverage_status, coverage_score


def _build_theory_packet_artifacts(
    self,
    *,
    topic_slug: str,
    resolved_run_id: str,
    candidate_id: str,
    candidate: dict[str, Any],
    source_id: str,
    updated_by: str,
    equation_labels: list[str] | None,
    section_statuses: list[dict[str, str]],
    canonical_source_sections: list[str],
    canonical_covered_sections: list[str],
    notation_rows: list[dict[str, str]],
    derivation_node_rows: list[dict[str, str]],
    derivation_edge_rows: list[dict[str, str]],
    normalized_votes: list[dict[str, str]],
    consensus_status: str,
    critical_unit_recall: float,
    missing_anchor_count: int,
    skeptic_major_gap_count: int,
    coverage_status: str,
    coverage_score: float,
    notes: str | None,
) -> tuple[dict[str, Path], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    packet_paths = self._theory_packet_paths(topic_slug, resolved_run_id, candidate_id)
    structure_map = {
        "candidate_id": candidate_id,
        "candidate_type": str(candidate.get("candidate_type") or ""),
        "source_id": source_id,
        "title": str(candidate.get("title") or candidate_id),
        "updated_at": _now_iso(),
        "updated_by": updated_by,
        "sections": section_statuses,
        "equation_labels": self._dedupe_strings(equation_labels or []),
    }
    coverage_ledger = {
        "candidate_id": candidate_id,
        "candidate_type": str(candidate.get("candidate_type") or ""),
        "source_section_count": len(canonical_source_sections),
        "covered_section_count": len(canonical_covered_sections),
        "missing_section_count": len([row for row in section_statuses if row["status"] == "missing"]),
        "missing_anchor_count": missing_anchor_count,
        "critical_unit_recall": critical_unit_recall,
        "skeptic_major_gap_count": skeptic_major_gap_count,
        "consensus_status": consensus_status,
        "coverage_score": coverage_score,
        "status": coverage_status,
        "ready_for_auto_promotion": coverage_status == "pass",
        "updated_at": _now_iso(),
        "updated_by": updated_by,
        "notes": notes or "",
    }
    notation_table = {
        "candidate_id": candidate_id,
        "source_id": source_id,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
        "status": "captured" if notation_rows else "pending",
        "bindings": notation_rows,
    }
    derivation_graph = {
        "candidate_id": candidate_id,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
        "status": "captured" if derivation_node_rows or derivation_edge_rows else "pending",
        "nodes": derivation_node_rows,
        "edges": derivation_edge_rows,
    }
    agent_consensus = {
        "candidate_id": candidate_id,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
        "consensus_status": consensus_status,
        "status": "ready" if consensus_status in {"unanimous", "majority"} else "blocked",
        "agents": normalized_votes,
        "skeptic_major_gap_count": skeptic_major_gap_count,
        "notes": notes or "",
    }
    return packet_paths, structure_map, coverage_ledger, notation_table, derivation_graph, agent_consensus


def _build_regression_context(
    self,
    *,
    topic_slug: str,
    resolved_run_id: str,
    candidate_id: str,
    updated_by: str,
    candidate: dict[str, Any],
    support_fields: dict[str, Any],
    coverage_status: str,
    agent_consensus: dict[str, Any],
    topic_completion_status: str | None,
    notes: str | None,
) -> tuple[str, dict[str, Any]]:
    resolved_topic_completion_status = self._derive_topic_completion_status(
        requested_status=topic_completion_status or str(candidate.get("topic_completion_status") or ""),
        coverage_status=coverage_status,
        supporting_regression_question_ids=support_fields["candidate_question_ids"],
        supporting_oracle_ids=support_fields["candidate_oracle_ids"],
        supporting_regression_run_ids=support_fields["candidate_regression_run_ids"],
        promotion_blockers=support_fields["candidate_promotion_blockers"],
        split_required=support_fields["candidate_split_required"],
        cited_recovery_required=support_fields["candidate_cited_recovery_required"],
    )
    regression_gate = self._build_regression_gate(
        topic_slug=topic_slug,
        run_id=resolved_run_id,
        candidate_id=candidate_id,
        updated_by=updated_by,
        coverage_status=coverage_status,
        consensus_status=str(agent_consensus.get("status") or "blocked"),
        topic_completion_status=resolved_topic_completion_status,
        supporting_regression_question_ids=support_fields["candidate_question_ids"],
        supporting_oracle_ids=support_fields["candidate_oracle_ids"],
        supporting_regression_run_ids=support_fields["candidate_regression_run_ids"],
        promotion_blockers=support_fields["candidate_promotion_blockers"],
        split_required=support_fields["candidate_split_required"],
        cited_recovery_required=support_fields["candidate_cited_recovery_required"],
        followup_gap_ids=support_fields["candidate_followup_gap_ids"],
        notes=notes or "",
    )
    return resolved_topic_completion_status, regression_gate


def _persist_coverage_audit(
    self,
    *,
    topic_slug: str,
    resolved_run_id: str,
    candidate_id: str,
    candidate: dict[str, Any],
    packet_paths: dict[str, Path],
    structure_map: dict[str, Any],
    coverage_ledger: dict[str, Any],
    notation_table: dict[str, Any],
    derivation_graph: dict[str, Any],
    agent_consensus: dict[str, Any],
    regression_gate: dict[str, Any],
    support_fields: dict[str, Any],
    resolved_topic_completion_status: str,
) -> None:
    _write_json(packet_paths["structure_map"], structure_map)
    _write_json(packet_paths["coverage_ledger"], coverage_ledger)
    _write_json(packet_paths["notation_table"], notation_table)
    _write_json(packet_paths["derivation_graph"], derivation_graph)
    _write_json(packet_paths["agent_consensus"], agent_consensus)
    _write_json(packet_paths["regression_gate"], regression_gate)

    updated_candidate = dict(candidate)
    updated_candidate["supporting_regression_question_ids"] = support_fields["candidate_question_ids"]
    updated_candidate["supporting_oracle_ids"] = support_fields["candidate_oracle_ids"]
    updated_candidate["supporting_regression_run_ids"] = support_fields["candidate_regression_run_ids"]
    updated_candidate["promotion_blockers"] = support_fields["candidate_promotion_blockers"]
    updated_candidate["split_required"] = support_fields["candidate_split_required"]
    updated_candidate["cited_recovery_required"] = support_fields["candidate_cited_recovery_required"]
    updated_candidate["followup_gap_ids"] = support_fields["candidate_followup_gap_ids"]
    updated_candidate["topic_completion_status"] = resolved_topic_completion_status
    self._replace_candidate_row(topic_slug, resolved_run_id, candidate_id, updated_candidate)


def audit_theory_coverage(
    self,
    *,
    topic_slug: str,
    candidate_id: str,
    run_id: str | None = None,
    updated_by: str = "aitp-cli",
    source_sections: list[str] | None = None,
    covered_sections: list[str] | None = None,
    equation_labels: list[str] | None = None,
    notation_bindings: list[dict[str, str]] | None = None,
    derivation_nodes: list[str] | None = None,
    derivation_edges: list[dict[str, str]] | None = None,
    agent_votes: list[dict[str, str]] | None = None,
    consensus_status: str = "unanimous",
    critical_unit_recall: float = 1.0,
    missing_anchor_count: int = 0,
    skeptic_major_gap_count: int = 0,
    supporting_regression_question_ids: list[str] | None = None,
    supporting_oracle_ids: list[str] | None = None,
    supporting_regression_run_ids: list[str] | None = None,
    promotion_blockers: list[str] | None = None,
    split_required: bool | None = None,
    cited_recovery_required: bool | None = None,
    followup_gap_ids: list[str] | None = None,
    topic_completion_status: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    resolved_run_id = self._resolve_run_id(topic_slug, run_id)
    if not resolved_run_id:
        raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")
    if critical_unit_recall < 0.0 or critical_unit_recall > 1.0:
        raise ValueError("critical_unit_recall must be between 0.0 and 1.0")
    if missing_anchor_count < 0 or skeptic_major_gap_count < 0:
        raise ValueError("missing-anchor-count and skeptic-major-gap-count must be non-negative")

    candidate = self._load_candidate(topic_slug, resolved_run_id, candidate_id)
    source_rows = _read_jsonl(self.kernel_root / "topics" / topic_slug / "L0" / "source_index.jsonl")
    source_row = choose_source_row(source_rows=source_rows, candidate=candidate)
    source_id = str((source_row or {}).get("source_id") or "") or f"source:{_slugify(candidate_id)}"
    support_fields = _normalize_candidate_support_fields(
        self,
        candidate=candidate,
        supporting_regression_question_ids=supporting_regression_question_ids,
        supporting_oracle_ids=supporting_oracle_ids,
        supporting_regression_run_ids=supporting_regression_run_ids,
        promotion_blockers=promotion_blockers,
        split_required=split_required,
        cited_recovery_required=cited_recovery_required,
        followup_gap_ids=followup_gap_ids,
    )
    canonical_source_sections, canonical_covered_sections, section_statuses = _normalize_source_sections(
        self,
        candidate_id=candidate_id,
        source_sections=source_sections,
        covered_sections=covered_sections,
    )
    notation_rows = _normalize_notation_rows(notation_bindings)
    derivation_node_rows, derivation_edge_rows = _normalize_derivation_rows(
        self,
        derivation_nodes=derivation_nodes,
        derivation_edges=derivation_edges,
    )
    normalized_votes = _normalize_votes(agent_votes=agent_votes, consensus_status=consensus_status)
    coverage_status, coverage_score = _compute_coverage_status_and_score(
        canonical_source_sections=canonical_source_sections,
        canonical_covered_sections=canonical_covered_sections,
        section_statuses=section_statuses,
        critical_unit_recall=critical_unit_recall,
        missing_anchor_count=missing_anchor_count,
        skeptic_major_gap_count=skeptic_major_gap_count,
        consensus_status=consensus_status,
    )
    packet_paths, structure_map, coverage_ledger, notation_table, derivation_graph, agent_consensus = _build_theory_packet_artifacts(
        self,
        topic_slug=topic_slug,
        resolved_run_id=resolved_run_id,
        candidate_id=candidate_id,
        candidate=candidate,
        source_id=source_id,
        updated_by=updated_by,
        equation_labels=equation_labels,
        section_statuses=section_statuses,
        canonical_source_sections=canonical_source_sections,
        canonical_covered_sections=canonical_covered_sections,
        notation_rows=notation_rows,
        derivation_node_rows=derivation_node_rows,
        derivation_edge_rows=derivation_edge_rows,
        normalized_votes=normalized_votes,
        consensus_status=consensus_status,
        critical_unit_recall=critical_unit_recall,
        missing_anchor_count=missing_anchor_count,
        skeptic_major_gap_count=skeptic_major_gap_count,
        coverage_status=coverage_status,
        coverage_score=coverage_score,
        notes=notes,
    )
    resolved_topic_completion_status, regression_gate = _build_regression_context(
        self,
        topic_slug=topic_slug,
        resolved_run_id=resolved_run_id,
        candidate_id=candidate_id,
        updated_by=updated_by,
        candidate=candidate,
        support_fields=support_fields,
        coverage_status=coverage_status,
        agent_consensus=agent_consensus,
        topic_completion_status=topic_completion_status,
        notes=notes,
    )
    _persist_coverage_audit(
        self,
        topic_slug=topic_slug,
        resolved_run_id=resolved_run_id,
        candidate_id=candidate_id,
        candidate=candidate,
        packet_paths=packet_paths,
        structure_map=structure_map,
        coverage_ledger=coverage_ledger,
        notation_table=notation_table,
        derivation_graph=derivation_graph,
        agent_consensus=agent_consensus,
        regression_gate=regression_gate,
        support_fields=support_fields,
        resolved_topic_completion_status=resolved_topic_completion_status,
    )
    return {
        "topic_slug": topic_slug,
        "run_id": resolved_run_id,
        "candidate_id": candidate_id,
        "coverage_status": coverage_status,
        "coverage_score": coverage_score,
        "regression_gate_status": regression_gate["status"],
        "topic_completion_status": resolved_topic_completion_status,
        "ready_for_auto_promotion": coverage_ledger["ready_for_auto_promotion"],
        "paths": {key: str(value) for key, value in packet_paths.items() if key != "root"},
        "artifacts": {
            "structure_map": structure_map,
            "coverage_ledger": coverage_ledger,
            "notation_table": notation_table,
            "derivation_graph": derivation_graph,
            "agent_consensus": agent_consensus,
            "regression_gate": regression_gate,
        },
    }
