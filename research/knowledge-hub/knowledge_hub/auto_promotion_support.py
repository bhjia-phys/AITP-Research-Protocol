from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .runtime_schema_promotion_bridge import collect_runtime_schema_context
from .topic_truth_root_support import compatibility_projection_path


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


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


def _required_theory_packet_artifacts(runtime_policy: dict[str, Any]) -> tuple[str, ...]:
    values = runtime_policy.get("required_theory_packet_artifacts") or [
        "structure_map",
        "coverage_ledger",
        "notation_table",
        "derivation_graph",
        "agent_consensus",
        "regression_gate",
    ]
    return tuple(str(value).strip() for value in values if str(value).strip())


def _load_packet_summaries(packet_paths: dict[str, Path]) -> dict[str, dict[str, Any]]:
    return {
        "coverage_summary": _read_json(packet_paths["coverage_ledger"]) or {},
        "consensus_summary": _read_json(packet_paths["agent_consensus"]) or {},
        "regression_summary": _read_json(packet_paths["regression_gate"]) or {},
        "formal_theory_review": _read_json(packet_paths["formal_theory_review"]) or {},
        "structure_map": _read_json(packet_paths["structure_map"]) or {},
        "notation_table": _read_json(packet_paths["notation_table"]) or {},
        "derivation_graph": _read_json(packet_paths["derivation_graph"]) or {},
    }


def _validate_auto_promotion(
    self,
    *,
    candidate: dict[str, Any],
    resolved_backend_id: str,
    card_payload: dict[str, Any] | None,
    packet_paths: dict[str, Path],
    packet_summaries: dict[str, dict[str, Any]],
) -> None:
    if str(candidate.get("candidate_type") or "") == "topic_skill_projection":
        raise PermissionError("topic_skill_projection is human-reviewed only in v1 and may not enter L2_auto.")
    if not self._backend_allows_auto_promotion(card_payload):
        raise PermissionError(f"Backend {resolved_backend_id} does not allow auto canonical promotion.")
    if not self._backend_supports_candidate_type(card_payload, str(candidate.get("candidate_type") or "")):
        raise ValueError(
            f"Backend {resolved_backend_id} does not declare support for candidate type {candidate.get('candidate_type')}"
        )

    runtime_policy = self._load_runtime_policy().get("auto_promotion_policy") or {}
    missing = [name for name in _required_theory_packet_artifacts(runtime_policy) if not packet_paths[name].exists()]
    if missing:
        raise FileNotFoundError("Missing theory packet artifacts for auto promotion: " + ", ".join(sorted(missing)))

    coverage_summary = packet_summaries["coverage_summary"]
    consensus_summary = packet_summaries["consensus_summary"]
    regression_summary = packet_summaries["regression_summary"]
    formal_theory_review = packet_summaries["formal_theory_review"]
    source_policy = (card_payload or {}).get("source_policy") or {}

    if source_policy.get("auto_promotion_requires_coverage_audit") and str(coverage_summary.get("status") or "") != "pass":
        raise PermissionError("Auto promotion requires a passing coverage_ledger.json status.")
    if source_policy.get("auto_promotion_requires_multi_agent_consensus") and str(consensus_summary.get("status") or "") != "ready":
        raise PermissionError("Auto promotion requires a ready agent_consensus.json status.")
    if source_policy.get("auto_promotion_requires_split_clearance") and str(regression_summary.get("split_clearance_status") or "") not in {"clear", "not_applicable"}:
        raise PermissionError("Auto promotion is blocked until split clearance is explicit.")
    if source_policy.get("auto_promotion_requires_gap_honesty"):
        if list(regression_summary.get("promotion_blockers") or []):
            raise PermissionError("Auto promotion is blocked while promotion_blockers remain.")
        if _as_bool(regression_summary.get("cited_recovery_required")):
            raise PermissionError("Auto promotion is blocked while cited recovery remains required.")
    if source_policy.get("auto_promotion_requires_regression_gate") and str(regression_summary.get("status") or "") != "pass":
        raise PermissionError("Auto promotion requires a passing regression_gate.json status.")
    if str(candidate.get("candidate_type") or "") in self._theory_formal_candidate_types():
        if not packet_paths["formal_theory_review"].exists():
            raise FileNotFoundError("Missing theory packet artifacts for auto promotion: formal_theory_review")
        if str(formal_theory_review.get("overall_status") or "") != "ready":
            raise PermissionError("Auto promotion requires a ready formal_theory_review.json status.")
    runtime_schema_context = collect_runtime_schema_context(
        self,
        topic_slug=str(candidate.get("topic_slug") or ""),
        run_id=str(candidate.get("run_id") or ""),
        candidate_id=str(candidate.get("candidate_id") or ""),
    )
    if not runtime_schema_context["all_valid"]:
        raise PermissionError("Auto promotion is blocked by invalid runtime schema artifacts.")


def _build_gate_payload(
    self,
    *,
    topic_slug: str,
    resolved_run_id: str,
    candidate_id: str,
    candidate: dict[str, Any],
    resolved_backend_id: str,
    target_backend_root: str | None,
    promoted_by: str,
    notes: str | None,
    packet_summaries: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    coverage_summary = packet_summaries["coverage_summary"]
    consensus_summary = packet_summaries["consensus_summary"]
    regression_summary = packet_summaries["regression_summary"]
    formal_theory_review = packet_summaries["formal_theory_review"]
    return {
        "topic_slug": topic_slug,
        "run_id": resolved_run_id,
        "candidate_id": candidate_id,
        "candidate_type": str(candidate.get("candidate_type") or ""),
        "title": str(candidate.get("title") or ""),
        "summary": str(candidate.get("summary") or ""),
        "route": "L3->L4_auto->L2_auto",
        "status": "approved",
        "intended_l2_targets": self._dedupe_strings(list(candidate.get("intended_l2_targets") or [])),
        "backend_id": resolved_backend_id,
        "target_backend_root": str(target_backend_root or ""),
        "review_mode": "ai_auto",
        "canonical_layer": "L2_auto",
        "coverage_status": str(coverage_summary.get("status") or "not_audited"),
        "consensus_status": str(consensus_summary.get("status") or "not_requested"),
        "regression_gate_status": str(regression_summary.get("status") or "not_audited"),
        "formal_theory_review_status": str(formal_theory_review.get("overall_status") or "not_required"),
        "topic_completion_status": str(regression_summary.get("topic_completion_status") or "not_assessed"),
        "supporting_regression_question_ids": self._dedupe_strings(
            list(regression_summary.get("supporting_regression_question_ids") or candidate.get("supporting_regression_question_ids") or [])
        ),
        "supporting_oracle_ids": self._dedupe_strings(
            list(regression_summary.get("supporting_oracle_ids") or candidate.get("supporting_oracle_ids") or [])
        ),
        "supporting_regression_run_ids": self._dedupe_strings(
            list(regression_summary.get("supporting_regression_run_ids") or candidate.get("supporting_regression_run_ids") or [])
        ),
        "promotion_blockers": self._dedupe_strings(
            list(regression_summary.get("promotion_blockers") or candidate.get("promotion_blockers") or [])
        ),
        "split_required": _as_bool(regression_summary.get("split_required")),
        "cited_recovery_required": _as_bool(regression_summary.get("cited_recovery_required")),
        "followup_gap_ids": self._dedupe_strings(
            list(regression_summary.get("followup_gap_ids") or candidate.get("followup_gap_ids") or [])
        ),
        "merge_outcome": "pending",
        "requested_by": promoted_by,
        "requested_at": _now_iso(),
        "approved_by": f"{promoted_by}:auto",
        "approved_at": _now_iso(),
        "rejected_by": None,
        "rejected_at": None,
        "promoted_by": None,
        "promoted_at": None,
        "promoted_units": [],
        "notes": notes or "",
    }


def _build_review_artifacts(self, *, packet_paths: dict[str, Path], gate_paths: dict[str, str], candidate_id: str) -> dict[str, str]:
    review_artifacts = {
        "structure_map_path": self._relativize(packet_paths["structure_map"]),
        "coverage_ledger_path": self._relativize(packet_paths["coverage_ledger"]),
        "notation_table_path": self._relativize(packet_paths["notation_table"]),
        "derivation_graph_path": self._relativize(packet_paths["derivation_graph"]),
        "agent_consensus_path": self._relativize(packet_paths["agent_consensus"]),
        "regression_gate_path": self._relativize(packet_paths["regression_gate"]),
        "promotion_gate_path": self._relativize(Path(gate_paths["promotion_gate_path"])),
        "candidate_id": candidate_id,
    }
    for key in ("faithfulness_review", "comparator_audit_record", "provenance_review", "prerequisite_closure_review", "formal_theory_review"):
        if packet_paths[key].exists():
            review_artifacts[f"{key}_path"] = self._relativize(packet_paths[key])
    return review_artifacts


def _build_auto_promotion_report(
    self,
    *,
    topic_slug: str,
    resolved_run_id: str,
    candidate_id: str,
    candidate: dict[str, Any],
    resolved_backend_id: str,
    card_path: Path | None,
    packet_summaries: dict[str, dict[str, Any]],
    promote_payload: dict[str, Any],
    promoted_by: str,
    notes: str | None,
) -> dict[str, Any]:
    structure_map = packet_summaries["structure_map"]
    notation_table = packet_summaries["notation_table"]
    derivation_graph = packet_summaries["derivation_graph"]
    return {
        "topic_slug": topic_slug,
        "run_id": resolved_run_id,
        "candidate_id": candidate_id,
        "candidate_type": str(candidate.get("candidate_type") or ""),
        "review_mode": "ai_auto",
        "canonical_layer": "L2_auto",
        "backend_id": resolved_backend_id,
        "backend_card_path": str(card_path) if card_path else None,
        "coverage_status": str(packet_summaries["coverage_summary"].get("status") or ""),
        "consensus_status": str(packet_summaries["consensus_summary"].get("status") or ""),
        "regression_gate_status": str(packet_summaries["regression_summary"].get("status") or ""),
        "formal_theory_review_status": str(packet_summaries["formal_theory_review"].get("overall_status") or "not_required"),
        "topic_completion_status": str(packet_summaries["regression_summary"].get("topic_completion_status") or ""),
        "supporting_regression_question_ids": self._dedupe_strings(
            list(packet_summaries["regression_summary"].get("supporting_regression_question_ids") or [])
        ),
        "supporting_oracle_ids": self._dedupe_strings(list(packet_summaries["regression_summary"].get("supporting_oracle_ids") or [])),
        "supporting_regression_run_ids": self._dedupe_strings(
            list(packet_summaries["regression_summary"].get("supporting_regression_run_ids") or [])
        ),
        "promotion_blockers": self._dedupe_strings(list(packet_summaries["regression_summary"].get("promotion_blockers") or [])),
        "structure_section_count": len(structure_map.get("sections") or []),
        "notation_binding_count": len(notation_table.get("bindings") or []),
        "derivation_node_count": len(derivation_graph.get("nodes") or []),
        "derivation_edge_count": len(derivation_graph.get("edges") or []),
        "merge_outcome": str(promote_payload.get("merge_outcome") or ""),
        "target_unit_id": str(promote_payload.get("target_unit_id") or ""),
        "target_unit_path": str(promote_payload.get("target_unit_path") or ""),
        "updated_at": _now_iso(),
        "updated_by": promoted_by,
        "notes": notes or "",
    }


def auto_promote_candidate(
    self,
    *,
    topic_slug: str,
    candidate_id: str,
    run_id: str | None = None,
    promoted_by: str = "aitp-cli",
    backend_id: str | None = None,
    target_backend_root: str | None = None,
    domain: str | None = None,
    subdomain: str | None = None,
    source_id: str | None = None,
    source_section: str | None = None,
    source_section_title: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    resolved_run_id = self._resolve_run_id(topic_slug, run_id)
    if not resolved_run_id:
        raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")
    candidate = self._load_candidate(topic_slug, resolved_run_id, candidate_id)
    resolved_backend_id = backend_id or "backend:theoretical-physics-knowledge-network"
    card_path, card_payload = self._load_backend_card(resolved_backend_id)
    packet_paths = self._theory_packet_paths(topic_slug, resolved_run_id, candidate_id)
    packet_summaries = _load_packet_summaries(packet_paths)

    _validate_auto_promotion(
        self,
        candidate=candidate,
        resolved_backend_id=resolved_backend_id,
        card_payload=card_payload,
        packet_paths=packet_paths,
        packet_summaries=packet_summaries,
    )

    gate_payload = _build_gate_payload(
        self,
        topic_slug=topic_slug,
        resolved_run_id=resolved_run_id,
        candidate_id=candidate_id,
        candidate=candidate,
        resolved_backend_id=resolved_backend_id,
        target_backend_root=target_backend_root,
        promoted_by=promoted_by,
        notes=notes,
        packet_summaries=packet_summaries,
    )
    gate_paths = self._write_promotion_gate(topic_slug, gate_payload)
    log_path = self._append_promotion_gate_log(
        topic_slug,
        resolved_run_id,
        {
            "event": "auto_approved",
            "candidate_id": candidate_id,
            "status": gate_payload["status"],
            "updated_by": promoted_by,
            "updated_at": gate_payload["approved_at"],
            "backend_id": resolved_backend_id,
            "target_backend_root": gate_payload["target_backend_root"],
            "coverage_status": gate_payload["coverage_status"],
            "consensus_status": gate_payload["consensus_status"],
            "notes": gate_payload["notes"],
        },
    )

    promote_payload = self.promote_candidate(
        topic_slug=topic_slug,
        candidate_id=candidate_id,
        run_id=resolved_run_id,
        promoted_by=promoted_by,
        backend_id=resolved_backend_id,
        target_backend_root=target_backend_root,
        domain=domain,
        subdomain=subdomain,
        source_id=source_id,
        source_section=source_section,
        source_section_title=source_section_title,
        notes=notes,
        review_mode="ai_auto",
        canonical_layer="L2_auto",
        review_artifact_paths=_build_review_artifacts(
            self,
            packet_paths=packet_paths,
            gate_paths=gate_paths,
            candidate_id=candidate_id,
        ),
        coverage_summary=packet_summaries["coverage_summary"],
        consensus_summary=packet_summaries["consensus_summary"],
    )

    auto_report = _build_auto_promotion_report(
        self,
        topic_slug=topic_slug,
        resolved_run_id=resolved_run_id,
        candidate_id=candidate_id,
        candidate=candidate,
        resolved_backend_id=resolved_backend_id,
        card_path=card_path,
        packet_summaries=packet_summaries,
        promote_payload=promote_payload,
        promoted_by=promoted_by,
        notes=notes,
    )
    _write_json(packet_paths["auto_promotion_report"], auto_report)

    return {
        **promote_payload,
        "auto_promotion_report_path": str(packet_paths["auto_promotion_report"]),
        "auto_promotion_report": auto_report,
        "auto_promotion_gate_log_path": log_path,
    }
