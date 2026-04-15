from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .topic_truth_root_support import compatibility_projection_path


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


def _nonempty_set(values: list[object] | None) -> set[str]:
    return {str(value).strip() for value in (values or []) if str(value).strip()}


def _normalize_nearby_variants(rows: list[dict[str, str]] | None) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for row in rows or []:
        label = str(row.get("label") or "").strip()
        relation = str(row.get("relation") or "").strip()
        verdict = str(row.get("verdict") or "").strip()
        notes = str(row.get("notes") or "").strip()
        if not label or not relation or not verdict:
            continue
        normalized.append(
            {
                "label": label,
                "relation": relation,
                "verdict": verdict,
                "notes": notes,
            }
        )
    return normalized


def _normalize_and_validate_inputs(
    self,
    *,
    candidate: dict[str, Any],
    runtime_policy: dict[str, Any],
    formal_theory_role: str,
    statement_graph_role: str,
    definition_trust_tier: str | None,
    target_statement_id: str | None,
    statement_graph_parents: list[str] | None,
    statement_graph_children: list[str] | None,
    informal_statement: str | None,
    formal_target: str | None,
    faithfulness_status: str,
    faithfulness_strategy: str | None,
    faithfulness_notes: str | None,
    comparator_audit_status: str,
    comparator_risks: list[str] | None,
    nearby_variants: list[dict[str, str]] | None,
    comparator_notes: str | None,
    provenance_kind: str,
    attribution_requirements: list[str] | None,
    provenance_sources: list[str] | None,
    provenance_notes: str | None,
    prerequisite_closure_status: str,
    lean_prerequisite_ids: list[str] | None,
    supporting_obligation_ids: list[str] | None,
    formalization_blockers: list[str] | None,
    prerequisite_notes: str | None,
) -> dict[str, Any]:
    trust_policy = runtime_policy.get("formal_theory_trust_boundary_policy") or {}
    faithfulness_policy = runtime_policy.get("faithfulness_policy") or {}
    comparator_policy = runtime_policy.get("comparator_audit_policy") or {}
    provenance_policy = runtime_policy.get("provenance_review_policy") or {}
    prerequisite_policy = runtime_policy.get("prerequisite_closure_policy") or {}

    normalized_role = str(formal_theory_role or "").strip() or "trusted_target"
    normalized_statement_graph_role = str(statement_graph_role or "").strip()
    if not normalized_statement_graph_role:
        raise ValueError("statement_graph_role is required")

    trusted_roles = _nonempty_set(trust_policy.get("trusted_roles"))
    intermediate_roles = _nonempty_set(trust_policy.get("intermediate_roles"))
    supporting_roles = _nonempty_set(trust_policy.get("supporting_roles"))
    known_roles = trusted_roles | intermediate_roles | supporting_roles
    if _as_bool(trust_policy.get("enabled")) and known_roles and normalized_role not in known_roles:
        raise ValueError("formal_theory_role must match the configured trust-boundary policy roles.")

    allowed_faithfulness_statuses = _nonempty_set(faithfulness_policy.get("allowed_statuses"))
    normalized_faithfulness_status = str(faithfulness_status or "").strip() or "pending"
    if (
        _as_bool(faithfulness_policy.get("enabled"))
        and allowed_faithfulness_statuses
        and normalized_faithfulness_status not in allowed_faithfulness_statuses
    ):
        raise ValueError("faithfulness_status is not allowed by faithfulness_policy")

    allowed_comparator_statuses = _nonempty_set(comparator_policy.get("allowed_statuses"))
    normalized_comparator_status = str(comparator_audit_status or "").strip() or "pending"
    if (
        _as_bool(comparator_policy.get("enabled"))
        and allowed_comparator_statuses
        and normalized_comparator_status not in allowed_comparator_statuses
    ):
        raise ValueError("comparator_audit_status is not allowed by comparator_audit_policy")

    allowed_provenance_kinds = _nonempty_set(provenance_policy.get("allowed_provenance_kinds"))
    normalized_provenance_kind = str(provenance_kind or "").strip() or "generated_from_scratch"
    if (
        _as_bool(provenance_policy.get("enabled"))
        and allowed_provenance_kinds
        and normalized_provenance_kind not in allowed_provenance_kinds
    ):
        raise ValueError("provenance_kind is not allowed by provenance_review_policy")

    allowed_prerequisite_statuses = _nonempty_set(prerequisite_policy.get("allowed_statuses"))
    normalized_prerequisite_status = str(prerequisite_closure_status or "").strip() or "pending"
    if (
        _as_bool(prerequisite_policy.get("enabled"))
        and allowed_prerequisite_statuses
        and normalized_prerequisite_status not in allowed_prerequisite_statuses
    ):
        raise ValueError("prerequisite_closure_status is not allowed by prerequisite_closure_policy")

    return {
        "candidate_type": str(candidate.get("candidate_type") or ""),
        "trust_policy": trust_policy,
        "faithfulness_policy": faithfulness_policy,
        "comparator_policy": comparator_policy,
        "provenance_policy": provenance_policy,
        "prerequisite_policy": prerequisite_policy,
        "trusted_roles": trusted_roles,
        "intermediate_roles": intermediate_roles,
        "supporting_roles": supporting_roles,
        "normalized_role": normalized_role,
        "normalized_statement_graph_role": normalized_statement_graph_role,
        "normalized_faithfulness_status": normalized_faithfulness_status,
        "normalized_comparator_status": normalized_comparator_status,
        "normalized_provenance_kind": normalized_provenance_kind,
        "normalized_prerequisite_status": normalized_prerequisite_status,
        "normalized_definition_trust_tier": str(definition_trust_tier or "").strip(),
        "normalized_target_statement_id": (
            str(target_statement_id or "").strip()
            or str(formal_target or "").strip()
            or str((candidate.get("intended_l2_targets") or [""])[0] or "").strip()
            or str(candidate.get("candidate_id") or "")
        ),
        "normalized_parents": self._dedupe_strings(statement_graph_parents),
        "normalized_children": self._dedupe_strings(statement_graph_children),
        "normalized_attribution_requirements": self._dedupe_strings(attribution_requirements),
        "normalized_provenance_sources": self._dedupe_strings(provenance_sources),
        "normalized_lean_prerequisite_ids": self._dedupe_strings(lean_prerequisite_ids),
        "normalized_supporting_obligation_ids": self._dedupe_strings(supporting_obligation_ids),
        "normalized_formalization_blockers": self._dedupe_strings(formalization_blockers),
        "normalized_comparator_risks": self._dedupe_strings(comparator_risks),
        "normalized_nearby_variants": _normalize_nearby_variants(nearby_variants),
        "comparator_goal": str(comparator_policy.get("comparator_goal") or "").strip(),
        "normalized_faithfulness_strategy": str(faithfulness_strategy or "").strip(),
        "normalized_faithfulness_notes": str(faithfulness_notes or "").strip(),
        "normalized_informal_statement": str(informal_statement or "").strip()
        or str(candidate.get("summary") or "").strip(),
        "normalized_formal_target": str(formal_target or "").strip(),
        "normalized_comparator_notes": str(comparator_notes or "").strip(),
        "normalized_provenance_notes": str(provenance_notes or "").strip(),
        "normalized_prerequisite_notes": str(prerequisite_notes or "").strip(),
    }


def _compute_blocking_reasons(normalized: dict[str, Any]) -> list[str]:
    blocking_reasons: list[str] = []

    if _as_bool(normalized["trust_policy"].get("enabled")):
        if normalized["trusted_roles"] and normalized["normalized_role"] not in normalized["trusted_roles"]:
            if normalized["normalized_role"] in normalized["intermediate_roles"]:
                blocking_reasons.append("formal_theory_role_is_intermediate_theory")
            elif normalized["normalized_role"] in normalized["supporting_roles"]:
                blocking_reasons.append("formal_theory_role_is_supporting_context")
            else:
                blocking_reasons.append("formal_theory_role_not_trusted_target")

    required_faithfulness_roles = _nonempty_set(normalized["faithfulness_policy"].get("default_required_for_roles"))
    blocking_faithfulness_statuses = _nonempty_set(normalized["faithfulness_policy"].get("blocking_statuses"))
    if normalized["normalized_role"] in required_faithfulness_roles:
        if not normalized["normalized_faithfulness_strategy"]:
            blocking_reasons.append("missing_faithfulness_strategy")
        if normalized["normalized_faithfulness_status"] in blocking_faithfulness_statuses:
            blocking_reasons.append("faithfulness_review_pending")

    required_comparator_roles = _nonempty_set(normalized["comparator_policy"].get("required_for_roles"))
    if normalized["normalized_role"] in required_comparator_roles:
        if normalized["normalized_comparator_status"] == "failed":
            blocking_reasons.append("comparator_audit_failed")
        elif normalized["normalized_comparator_status"] != "passed":
            blocking_reasons.append("comparator_audit_not_passed")

    if _as_bool(normalized["provenance_policy"].get("enabled")):
        if not normalized["normalized_attribution_requirements"]:
            blocking_reasons.append("missing_attribution_requirements")
        if (
            normalized["normalized_provenance_kind"]
            in {"retrieved_existing_formalization", "adapted_existing_formalization", "mixed"}
            and not normalized["normalized_provenance_sources"]
        ):
            blocking_reasons.append("missing_provenance_sources")

    required_prerequisite_roles = _nonempty_set(normalized["prerequisite_policy"].get("default_required_for_roles"))
    blocking_prerequisite_statuses = _nonempty_set(normalized["prerequisite_policy"].get("blocking_statuses"))
    if normalized["normalized_role"] in required_prerequisite_roles:
        if normalized["normalized_prerequisite_status"] in blocking_prerequisite_statuses:
            blocking_reasons.append("prerequisite_closure_incomplete")
    if normalized["normalized_formalization_blockers"]:
        blocking_reasons.append("formalization_blockers_present")

    return blocking_reasons


def _write_review_artifacts(
    self,
    *,
    topic_slug: str,
    resolved_run_id: str,
    candidate_id: str,
    updated_by: str,
    normalized: dict[str, Any],
    blocking_reasons: list[str],
) -> tuple[dict[str, Path], dict[str, dict[str, Any]], str]:
    updated_at = _now_iso()
    packet_paths = self._theory_packet_paths(topic_slug, resolved_run_id, candidate_id)
    overall_status = "ready" if not blocking_reasons else "blocked"
    candidate_type = normalized["candidate_type"]

    faithfulness_review = {
        "schema_version": 1,
        "topic_slug": topic_slug,
        "run_id": resolved_run_id,
        "candidate_id": candidate_id,
        "candidate_type": candidate_type,
        "formal_theory_role": normalized["normalized_role"],
        "statement_graph_role": normalized["normalized_statement_graph_role"],
        "target_statement_id": normalized["normalized_target_statement_id"],
        "statement_graph_parents": normalized["normalized_parents"],
        "statement_graph_children": normalized["normalized_children"],
        "informal_statement": normalized["normalized_informal_statement"],
        "formal_target": normalized["normalized_formal_target"],
        "status": normalized["normalized_faithfulness_status"],
        "strategy": normalized["normalized_faithfulness_strategy"],
        "notes": normalized["normalized_faithfulness_notes"],
        "updated_at": updated_at,
        "updated_by": updated_by,
    }
    comparator_audit_record = {
        "schema_version": 1,
        "topic_slug": topic_slug,
        "run_id": resolved_run_id,
        "candidate_id": candidate_id,
        "candidate_type": candidate_type,
        "formal_theory_role": normalized["normalized_role"],
        "status": normalized["normalized_comparator_status"],
        "goal": normalized["comparator_goal"],
        "nearby_variants": normalized["normalized_nearby_variants"],
        "risks": normalized["normalized_comparator_risks"],
        "notes": normalized["normalized_comparator_notes"],
        "updated_at": updated_at,
        "updated_by": updated_by,
    }
    provenance_review = {
        "schema_version": 1,
        "topic_slug": topic_slug,
        "run_id": resolved_run_id,
        "candidate_id": candidate_id,
        "candidate_type": candidate_type,
        "provenance_kind": normalized["normalized_provenance_kind"],
        "attribution_requirements": normalized["normalized_attribution_requirements"],
        "provenance_sources": normalized["normalized_provenance_sources"],
        "notes": normalized["normalized_provenance_notes"],
        "updated_at": updated_at,
        "updated_by": updated_by,
    }
    prerequisite_closure_review = {
        "schema_version": 1,
        "topic_slug": topic_slug,
        "run_id": resolved_run_id,
        "candidate_id": candidate_id,
        "candidate_type": candidate_type,
        "formal_theory_role": normalized["normalized_role"],
        "status": normalized["normalized_prerequisite_status"],
        "lean_prerequisite_ids": normalized["normalized_lean_prerequisite_ids"],
        "supporting_obligation_ids": normalized["normalized_supporting_obligation_ids"],
        "formalization_blockers": normalized["normalized_formalization_blockers"],
        "notes": normalized["normalized_prerequisite_notes"],
        "updated_at": updated_at,
        "updated_by": updated_by,
    }
    _write_json(packet_paths["faithfulness_review"], faithfulness_review)
    _write_json(packet_paths["comparator_audit_record"], comparator_audit_record)
    _write_json(packet_paths["provenance_review"], provenance_review)
    _write_json(packet_paths["prerequisite_closure_review"], prerequisite_closure_review)

    formal_theory_review = {
        "schema_version": 1,
        "topic_slug": topic_slug,
        "run_id": resolved_run_id,
        "candidate_id": candidate_id,
        "candidate_type": candidate_type,
        "formal_theory_role": normalized["normalized_role"],
        "statement_graph_role": normalized["normalized_statement_graph_role"],
        "target_statement_id": normalized["normalized_target_statement_id"],
        "statement_graph_parents": normalized["normalized_parents"],
        "statement_graph_children": normalized["normalized_children"],
        "faithfulness_status": normalized["normalized_faithfulness_status"],
        "comparator_audit_status": normalized["normalized_comparator_status"],
        "comparator_risks": normalized["normalized_comparator_risks"],
        "nearby_variants": normalized["normalized_nearby_variants"],
        "provenance_kind": normalized["normalized_provenance_kind"],
        "prerequisite_closure_status": normalized["normalized_prerequisite_status"],
        "overall_status": overall_status,
        "blocking_reasons": blocking_reasons,
        "attribution_requirements": normalized["normalized_attribution_requirements"],
        "provenance_sources": normalized["normalized_provenance_sources"],
        "lean_prerequisite_ids": normalized["normalized_lean_prerequisite_ids"],
        "supporting_obligation_ids": normalized["normalized_supporting_obligation_ids"],
        "formalization_blockers": normalized["normalized_formalization_blockers"],
        "faithfulness_review_path": self._relativize(packet_paths["faithfulness_review"]),
        "comparator_audit_record_path": self._relativize(packet_paths["comparator_audit_record"]),
        "provenance_review_path": self._relativize(packet_paths["provenance_review"]),
        "prerequisite_closure_review_path": self._relativize(packet_paths["prerequisite_closure_review"]),
        "formal_theory_review_path": self._relativize(packet_paths["formal_theory_review"]),
        "updated_at": updated_at,
        "updated_by": updated_by,
    }
    if normalized["normalized_definition_trust_tier"]:
        formal_theory_review["definition_trust_tier"] = normalized["normalized_definition_trust_tier"]
    if normalized["normalized_faithfulness_strategy"]:
        formal_theory_review["faithfulness_strategy"] = normalized["normalized_faithfulness_strategy"]
    if normalized["normalized_faithfulness_notes"]:
        formal_theory_review["faithfulness_notes"] = normalized["normalized_faithfulness_notes"]
    if normalized["normalized_informal_statement"]:
        formal_theory_review["informal_statement"] = normalized["normalized_informal_statement"]
    if normalized["normalized_formal_target"]:
        formal_theory_review["formal_target"] = normalized["normalized_formal_target"]
    if normalized["comparator_goal"]:
        formal_theory_review["comparator_goal"] = normalized["comparator_goal"]
    if normalized["normalized_comparator_notes"]:
        formal_theory_review["comparator_notes"] = normalized["normalized_comparator_notes"]
    if normalized["normalized_provenance_notes"]:
        formal_theory_review["provenance_notes"] = normalized["normalized_provenance_notes"]
    if normalized["normalized_prerequisite_notes"]:
        formal_theory_review["prerequisite_notes"] = normalized["normalized_prerequisite_notes"]
    _write_json(packet_paths["formal_theory_review"], formal_theory_review)

    return packet_paths, {
        "faithfulness_review": faithfulness_review,
        "comparator_audit_record": comparator_audit_record,
        "provenance_review": provenance_review,
        "prerequisite_closure_review": prerequisite_closure_review,
        "formal_theory_review": formal_theory_review,
    }, overall_status


def _update_candidate_after_review(
    self,
    *,
    topic_slug: str,
    resolved_run_id: str,
    candidate_id: str,
    candidate: dict[str, Any],
    normalized: dict[str, Any],
    packet_paths: dict[str, Path],
    overall_status: str,
    blocking_reasons: list[str],
) -> None:
    updated_candidate = dict(candidate)
    updated_candidate["formal_theory_role"] = normalized["normalized_role"]
    updated_candidate["statement_graph_role"] = normalized["normalized_statement_graph_role"]
    updated_candidate["target_statement_id"] = normalized["normalized_target_statement_id"]
    if normalized["normalized_definition_trust_tier"]:
        updated_candidate["definition_trust_tier"] = normalized["normalized_definition_trust_tier"]
    updated_candidate["faithfulness_status"] = normalized["normalized_faithfulness_status"]
    updated_candidate["comparator_audit_status"] = normalized["normalized_comparator_status"]
    updated_candidate["provenance_kind"] = normalized["normalized_provenance_kind"]
    updated_candidate["prerequisite_closure_status"] = normalized["normalized_prerequisite_status"]
    updated_candidate["formalization_blockers"] = normalized["normalized_formalization_blockers"]
    updated_candidate["formal_theory_review_overall_status"] = overall_status
    updated_candidate["formal_theory_blocking_reasons"] = blocking_reasons
    theory_packet_refs = dict(updated_candidate.get("theory_packet_refs") or {})
    theory_packet_refs.update(
        {
            "faithfulness_review": self._relativize(packet_paths["faithfulness_review"]),
            "comparator_audit_record": self._relativize(packet_paths["comparator_audit_record"]),
            "provenance_review": self._relativize(packet_paths["provenance_review"]),
            "prerequisite_closure_review": self._relativize(packet_paths["prerequisite_closure_review"]),
            "formal_theory_review": self._relativize(packet_paths["formal_theory_review"]),
        }
    )
    updated_candidate["theory_packet_refs"] = theory_packet_refs
    self._replace_candidate_row(topic_slug, resolved_run_id, candidate_id, updated_candidate)


def audit_formal_theory(
    self,
    *,
    topic_slug: str,
    candidate_id: str,
    run_id: str | None = None,
    updated_by: str = "aitp-cli",
    formal_theory_role: str = "trusted_target",
    statement_graph_role: str = "target_statement",
    definition_trust_tier: str | None = None,
    target_statement_id: str | None = None,
    statement_graph_parents: list[str] | None = None,
    statement_graph_children: list[str] | None = None,
    informal_statement: str | None = None,
    formal_target: str | None = None,
    faithfulness_status: str = "pending",
    faithfulness_strategy: str | None = None,
    faithfulness_notes: str | None = None,
    comparator_audit_status: str = "pending",
    comparator_risks: list[str] | None = None,
    nearby_variants: list[dict[str, str]] | None = None,
    comparator_notes: str | None = None,
    provenance_kind: str = "generated_from_scratch",
    attribution_requirements: list[str] | None = None,
    provenance_sources: list[str] | None = None,
    provenance_notes: str | None = None,
    prerequisite_closure_status: str = "pending",
    lean_prerequisite_ids: list[str] | None = None,
    supporting_obligation_ids: list[str] | None = None,
    formalization_blockers: list[str] | None = None,
    prerequisite_notes: str | None = None,
) -> dict[str, Any]:
    resolved_run_id = self._resolve_run_id(topic_slug, run_id)
    if not resolved_run_id:
        raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")

    candidate = self._load_candidate(topic_slug, resolved_run_id, candidate_id)
    normalized = _normalize_and_validate_inputs(
        self,
        candidate=candidate,
        runtime_policy=self._load_runtime_policy(),
        formal_theory_role=formal_theory_role,
        statement_graph_role=statement_graph_role,
        definition_trust_tier=definition_trust_tier,
        target_statement_id=target_statement_id,
        statement_graph_parents=statement_graph_parents,
        statement_graph_children=statement_graph_children,
        informal_statement=informal_statement,
        formal_target=formal_target,
        faithfulness_status=faithfulness_status,
        faithfulness_strategy=faithfulness_strategy,
        faithfulness_notes=faithfulness_notes,
        comparator_audit_status=comparator_audit_status,
        comparator_risks=comparator_risks,
        nearby_variants=nearby_variants,
        comparator_notes=comparator_notes,
        provenance_kind=provenance_kind,
        attribution_requirements=attribution_requirements,
        provenance_sources=provenance_sources,
        provenance_notes=provenance_notes,
        prerequisite_closure_status=prerequisite_closure_status,
        lean_prerequisite_ids=lean_prerequisite_ids,
        supporting_obligation_ids=supporting_obligation_ids,
        formalization_blockers=formalization_blockers,
        prerequisite_notes=prerequisite_notes,
    )
    blocking_reasons = _compute_blocking_reasons(normalized)
    packet_paths, artifacts, overall_status = _write_review_artifacts(
        self,
        topic_slug=topic_slug,
        resolved_run_id=resolved_run_id,
        candidate_id=candidate_id,
        updated_by=updated_by,
        normalized=normalized,
        blocking_reasons=blocking_reasons,
    )
    _update_candidate_after_review(
        self,
        topic_slug=topic_slug,
        resolved_run_id=resolved_run_id,
        candidate_id=candidate_id,
        candidate=candidate,
        normalized=normalized,
        packet_paths=packet_paths,
        overall_status=overall_status,
        blocking_reasons=blocking_reasons,
    )
    return {
        "topic_slug": topic_slug,
        "run_id": resolved_run_id,
        "candidate_id": candidate_id,
        "candidate_type": normalized["candidate_type"],
        "target_statement_id": normalized["normalized_target_statement_id"],
        "overall_status": overall_status,
        "blocking_reasons": blocking_reasons,
        "paths": {
            "faithfulness_review": str(packet_paths["faithfulness_review"]),
            "comparator_audit_record": str(packet_paths["comparator_audit_record"]),
            "provenance_review": str(packet_paths["provenance_review"]),
            "prerequisite_closure_review": str(packet_paths["prerequisite_closure_review"]),
            "formal_theory_review": str(packet_paths["formal_theory_review"]),
        },
        "artifacts": artifacts,
    }
