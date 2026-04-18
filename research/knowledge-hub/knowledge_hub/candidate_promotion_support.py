from __future__ import annotations

import json
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .runtime_projection_handler import append_transition_history
from .runtime_schema_promotion_bridge import collect_runtime_schema_context
from .l2_graph import materialize_canonical_index
from .tpkn_bridge import (
    build_supporting_question_oracle_unit,
    build_supporting_regression_question_unit,
    build_tpkn_unit,
    choose_merge_target,
    choose_source_row,
    derive_tpkn_unit_id,
    ensure_source_manifest,
    find_collision_rows,
    load_unit_index_rows,
    map_aitp_candidate_type,
    merge_tpkn_unit,
    run_tpkn_checks,
    unit_path_for,
    write_json as write_external_json,
)


_TPKN_TO_CANONICAL_UNIT_TYPE = {
    "bridge": "bridge",
    "claim": "claim_card",
    "concept": "concept",
    "method": "method",
    "physical_picture": "physical_picture",
    "proof_fragment": "proof_fragment",
    "theorem": "theorem_card",
    "topic_skill_projection": "topic_skill_projection",
    "warning": "warning_note",
    "workflow": "workflow",
}

_CANONICAL_DIR_BY_TYPE = {
    "atomic_note": "atomic-notes",
    "bridge": "bridges",
    "caveat_card": "caveat-cards",
    "claim_card": "claim-cards",
    "concept": "concepts",
    "definition_card": "definition-cards",
    "derivation_object": "derivation-objects",
    "derivation_step": "derivation-steps",
    "equation_card": "equation-cards",
    "equivalence_map": "equivalence-maps",
    "example_card": "example-cards",
    "assumption_card": "assumption-cards",
    "regime_card": "regime-cards",
    "method": "methods",
    "negative_result": "negative-results",
    "notation_card": "notation-cards",
    "physical_picture": "physical-pictures",
    "proof_fragment": "proof-fragments",
    "symbol_binding": "symbol-bindings",
    "theorem_card": "theorem-cards",
    "topic_skill_projection": "topic-skill-projections",
    "validation_pattern": "validation-patterns",
    "warning_note": "warning-notes",
    "workflow": "workflows",
}


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "aitp-topic"


def _bounded_slug(text: str, *, max_length: int = 48) -> str:
    slug = _slugify(text)
    if len(slug) <= max_length:
        return slug
    digest = hashlib.sha1(slug.encode("utf-8")).hexdigest()[:8]
    head = slug[: max(8, max_length - len(digest) - 1)].rstrip("-")
    return f"{head}-{digest}"


def _canonical_mirror_path(kernel_root: Path, *, unit_id: str, unit_type: str) -> Path:
    slug = unit_id.split(":", 1)[1]
    return kernel_root / "canonical" / _CANONICAL_DIR_BY_TYPE[unit_type] / f"{unit_type}--{slug}.json"


def _canonical_mirror_payload(
    self,
    *,
    topic_slug: str,
    candidate_id: str,
    promoted_by: str,
    context: dict[str, Any],
    artifacts: dict[str, Any],
    unit_payload: dict[str, Any],
) -> dict[str, Any] | None:
    canonical_unit_type = _TPKN_TO_CANONICAL_UNIT_TYPE.get(str(context["mapped_type"]))
    if canonical_unit_type is None:
        return None

    candidate = context["candidate"]
    source_row = context.get("source_row") or {}
    packet_paths = context["packet_paths"]
    consultation_paths = artifacts["consultation_paths"]
    timestamp = _now_iso()
    source_artifacts = []
    locator = source_row.get("locator") or {}
    for key in ("local_path", "snapshot_path"):
        value = str(locator.get(key) or "").strip()
        if value:
            source_artifacts.append(value)

    assumptions = self._dedupe_strings(
        [str(item) for item in (candidate.get("assumptions") or []) if str(item).strip()]
    )
    if not assumptions:
        assumptions = ["Promoted from an AITP candidate through explicit backend writeback."]

    l4_checks = self._dedupe_strings(
        [
            self._relativize(self._promotion_gate_paths(topic_slug)["json"]),
            self._relativize(packet_paths["merge_report"]),
            self._relativize(Path(consultation_paths["consultation_result_path"])),
            self._relativize(packet_paths["coverage_ledger"])
            if packet_paths["coverage_ledger"].exists()
            else "",
            self._relativize(packet_paths["formal_theory_review"])
            if packet_paths["formal_theory_review"].exists()
            else "",
        ]
    )
    origin_topic_refs = self._dedupe_strings([f"topics/{topic_slug}"])
    origin_run_refs = self._dedupe_strings(
        [
            self._relativize(self._feedback_run_root(topic_slug, context["resolved_run_id"])),
            self._relativize(self._validation_run_root(topic_slug, context["resolved_run_id"])),
            self._relativize(packet_paths["root"]),
        ]
    )
    validation_receipts = self._dedupe_strings(
        [
            self._relativize(Path(consultation_paths["consultation_result_path"])),
            self._relativize(packet_paths["merge_report"]),
            self._relativize(self._promotion_gate_paths(topic_slug)["json"]),
            self._relativize(packet_paths["regression_gate"]) if packet_paths["regression_gate"].exists() else "",
            self._relativize(packet_paths["coverage_ledger"]) if packet_paths["coverage_ledger"].exists() else "",
            self._relativize(packet_paths["formal_theory_review"])
            if packet_paths["formal_theory_review"].exists()
            else "",
            self._relativize(packet_paths["analytical_review"]) if packet_paths["analytical_review"].exists() else "",
            *[
                str(path).strip()
                for path in (context["runtime_schema_context"].get("artifact_paths") or {}).values()
                if str(path).strip()
            ],
        ]
    )
    related_consultation_refs = self._dedupe_strings(
        [
            self._relativize(Path(consultation_paths["consultation_request_path"])),
            self._relativize(Path(consultation_paths["consultation_result_path"])),
            self._relativize(Path(consultation_paths["consultation_application_path"])),
            self._relativize(Path(consultation_paths["consultation_index_path"])),
        ]
    )
    applicable_topics = self._dedupe_strings([str(candidate.get("topic_slug") or "").strip(), topic_slug])
    failed_topics = self._dedupe_strings(
        [str(item) for item in (candidate.get("failed_topics") or context["regression_summary"].get("failed_topics") or [])]
    )
    regime_notes = self._dedupe_strings(
        [
            str(item) for item in (context["regression_summary"].get("blocking_reasons") or []) if str(item).strip()
        ]
        + [
            f"followup-gap:{item}"
            for item in (context["regression_summary"].get("followup_gap_ids") or [])
            if str(item).strip()
        ]
        + (
            ["split-required-before-broader-reuse"]
            if bool(context["regression_summary"].get("split_required"))
            else []
        )
        + (
            ["citation-recovery-required-before-broader-reuse"]
            if bool(context["regression_summary"].get("cited_recovery_required"))
            else []
        )
    )

    return {
        "id": context["target_unit_id"],
        "unit_type": canonical_unit_type,
        "title": str(unit_payload.get("title") or candidate.get("title") or context["target_unit_id"]),
        "summary": str(unit_payload.get("summary") or candidate.get("summary") or ""),
        "maturity": "auto_validated" if context["resolved_review_mode"] == "ai_auto" else "human_promoted",
        "created_at": timestamp,
        "updated_at": timestamp,
        "topic_completion_status": str(
            context["regression_summary"].get("topic_completion_status")
            or candidate.get("topic_completion_status")
            or "not_assessed"
        ),
        "tags": self._dedupe_strings(
            [
                str(candidate.get("candidate_type") or "").strip(),
                str(candidate.get("topic_slug") or "").strip(),
                canonical_unit_type,
                str(context["resolved_backend_id"] or "").strip(),
            ]
        ),
        "assumptions": assumptions,
        "regime": {
            "domain": str(context["default_domain"] or topic_slug),
            "approximations": self._dedupe_strings(
                [
                    f"backend promotion via {context['resolved_review_mode']}",
                    f"canonical layer {context['resolved_canonical_layer']}",
                ]
            ),
            "scale": "bounded promoted unit",
            "boundary_conditions": [
                "external backend writeback completed",
                "repo-local canonical mirror materialized",
            ],
            "exclusions": [str(item) for item in (context["regression_summary"].get("followup_gap_ids") or [])],
        },
        "scope": {
            "applies_to": [str(candidate.get("question") or candidate.get("title") or context["target_unit_id"])],
            "out_of_scope": [str(item) for item in (context["regression_summary"].get("followup_gap_ids") or [])],
        },
        "provenance": {
            "source_ids": self._dedupe_strings([str(context["resolved_source_id"] or "")]),
            "backend_refs": self._dedupe_strings([str(context["resolved_backend_id"] or "")]),
            "l1_artifacts": self._dedupe_strings(source_artifacts),
            "l3_runs": self._dedupe_strings(
                [self._relativize(self._candidate_ledger_path(topic_slug, context["resolved_run_id"]))]
            ),
            "l4_checks": l4_checks,
            "citations": self._dedupe_strings(
                [
                    str(context["resolved_source_section"] or ""),
                    str(context["resolved_source_section_title"] or ""),
                ]
            ),
        },
        "promotion": {
            "route": str(context["gate_payload"].get("route") or "L3->L4->L2"),
            "review_mode": context["resolved_review_mode"],
            "canonical_layer": context["resolved_canonical_layer"],
            "promoted_by": promoted_by,
            "promoted_at": timestamp,
            "review_status": "accepted",
            "rationale": (
                "Mirrored into repo-local canonical L2 after successful external backend promotion."
            ),
        },
        "dependencies": self._dedupe_strings(
            [
                str(item)
                for item in (candidate.get("intended_l2_targets") or [])
                if str(item).strip() and str(item).strip() != str(context["target_unit_id"])
            ]
        ),
        "origin_topic_refs": origin_topic_refs,
        "origin_run_refs": origin_run_refs,
        "validation_receipts": validation_receipts,
        "reuse_receipts": [],
        "related_consultation_refs": related_consultation_refs,
        "applicable_topics": applicable_topics,
        "failed_topics": failed_topics,
        "regime_notes": regime_notes,
        "related_units": self._dedupe_strings(
            [str(ref.get("id") or "").strip() for ref in (candidate.get("origin_refs") or [])]
        ),
        "payload": {
            "backend_unit_type": str(context["mapped_type"] or ""),
            "backend_unit_path": str(artifacts["unit_path"]),
            "backend_root": str(context["tpkn_root"]),
            "candidate_id": candidate_id,
            "candidate_type": str(candidate.get("candidate_type") or ""),
            "source_manifest_path": str(artifacts["manifest_path"]),
            "merge_report_path": self._relativize(packet_paths["merge_report"]),
            "consultation_result_path": self._relativize(
                Path(consultation_paths["consultation_result_path"])
            ),
            "review_artifacts": context["review_artifacts_payload"],
        },
    }


def _materialize_canonical_mirror(
    self,
    *,
    topic_slug: str,
    candidate_id: str,
    promoted_by: str,
    context: dict[str, Any],
    artifacts: dict[str, Any],
    unit_payload: dict[str, Any],
) -> dict[str, Any]:
    payload = _canonical_mirror_payload(
        self,
        topic_slug=topic_slug,
        candidate_id=candidate_id,
        promoted_by=promoted_by,
        context=context,
        artifacts=artifacts,
        unit_payload=unit_payload,
    )
    if payload is None:
        return {"path": None, "unit_id": None, "unit_type": None}

    mirror_path = _canonical_mirror_path(
        self.kernel_root,
        unit_id=str(payload["id"]),
        unit_type=str(payload["unit_type"]),
    )
    _write_json(mirror_path, payload)
    materialize_canonical_index(self.kernel_root)
    return {
        "path": str(mirror_path),
        "unit_id": str(payload["id"]),
        "unit_type": str(payload["unit_type"]),
    }


def _resolve_promotion_context(
    self,
    *,
    topic_slug: str,
    candidate_id: str,
    run_id: str | None,
    backend_id: str | None,
    target_backend_root: str | None,
    domain: str | None,
    subdomain: str | None,
    source_id: str | None,
    source_section: str | None,
    source_section_title: str | None,
    review_mode: str | None,
    canonical_layer: str | None,
    review_artifact_paths: dict[str, str] | None,
    coverage_summary: dict[str, Any] | None,
    consensus_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    gate_payload = self._load_promotion_gate(topic_slug)
    if gate_payload is None:
        raise FileNotFoundError(f"Promotion gate missing for topic {topic_slug}")
    if str(gate_payload.get("candidate_id") or "") != candidate_id:
        raise ValueError(f"Promotion gate candidate mismatch: expected {gate_payload.get('candidate_id')}, got {candidate_id}")
    if str(gate_payload.get("status") or "") != "approved":
        raise PermissionError("Layer 2 promotion requires an approved promotion_gate.json status.")

    resolved_run_id = self._resolve_run_id(topic_slug, run_id or str(gate_payload.get("run_id") or ""))
    if not resolved_run_id:
        raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")
    candidate = self._load_candidate(topic_slug, resolved_run_id, candidate_id)
    runtime_blockers = self._candidate_runtime_blockers(
        topic_slug,
        resolved_run_id,
        candidate,
    )
    if runtime_blockers:
        raise PermissionError(
            "Promotion is blocked until the candidate satisfies the required L3 derivation, L2 comparison, and theory-packet surfaces: "
            + "; ".join(runtime_blockers)
        )

    resolved_backend_id = backend_id or str(gate_payload.get("backend_id") or "") or "backend:theoretical-physics-knowledge-network"
    resolved_review_mode = review_mode or str(gate_payload.get("review_mode") or "human")
    resolved_canonical_layer = canonical_layer or str(
        gate_payload.get("canonical_layer") or ("L2_auto" if resolved_review_mode == "ai_auto" else "L2")
    )

    tpkn_root, card_path, card_payload = self._resolve_tpkn_root(
        backend_id=resolved_backend_id,
        target_backend_root=target_backend_root or str(gate_payload.get("target_backend_root") or ""),
    )
    if card_payload is None and resolved_backend_id:
        card_path, card_payload = self._load_backend_card(resolved_backend_id)

    candidate_type = str(candidate.get("candidate_type") or "")
    mapped_type = map_aitp_candidate_type(candidate_type)
    if not self._backend_supports_candidate_type(card_payload, candidate_type):
        raise ValueError(f"Backend {resolved_backend_id} does not declare support for candidate type {candidate_type}")

    source_rows = _read_jsonl(self.kernel_root / "topics" / topic_slug / "L0" / "source_index.jsonl")
    source_row = choose_source_row(source_rows=source_rows, candidate=candidate)
    resolved_source_id = source_id or str((source_row or {}).get("source_id") or "") or f"source:{_slugify(candidate_id)}"
    resolved_source_section = source_section or "aitp/promoted-candidate"
    resolved_source_section_title = source_section_title or str(candidate.get("title") or candidate_id)

    default_domain = _slugify(domain or topic_slug)
    default_subdomain = _slugify(subdomain or mapped_type)
    collision_rows = find_collision_rows(
        tpkn_root=tpkn_root,
        candidate_title=str(candidate.get("title") or ""),
        candidate_summary=str(candidate.get("summary") or ""),
        candidate_tags=[candidate_type, str(candidate.get("topic_slug") or "")],
        candidate_aliases=[],
        domain=default_domain,
        target_type=mapped_type,
    )

    requested_unit_id = derive_tpkn_unit_id(candidate, mapped_type)
    existing_tpkn_ids = {str(row.get("id") or "") for row in load_unit_index_rows(tpkn_root)}
    merge_target = choose_merge_target(
        collision_rows=collision_rows,
        requested_unit_id=requested_unit_id,
        candidate_title=str(candidate.get("title") or ""),
        target_type=mapped_type,
    )
    equivalence_refs = [
        str(row.get("id") or "")
        for row in collision_rows
        if str(row.get("id") or "") and str(row.get("id") or "") != str((merge_target or {}).get("id") or "")
    ]
    target_unit_id = str((merge_target or {}).get("id") or requested_unit_id)
    merge_outcome = "merged_existing" if merge_target else ("created_with_neighbors" if equivalence_refs else "created_new")
    merge_lineage = {
        "strategy": merge_outcome,
        "candidate_id": candidate_id,
        "collision_scan_count": len(collision_rows),
        "selected_match_id": str((merge_target or {}).get("id") or ""),
    }

    packet_paths = self._theory_packet_paths(topic_slug, resolved_run_id, candidate_id)
    review_artifacts_payload = dict(review_artifact_paths or {})
    review_artifacts_payload.setdefault("candidate_id", candidate_id)
    review_artifacts_payload.setdefault("promotion_gate_path", self._relativize(self._promotion_gate_paths(topic_slug)["json"]))
    if packet_paths["regression_gate"].exists():
        review_artifacts_payload.setdefault("regression_gate_path", self._relativize(packet_paths["regression_gate"]))
    if packet_paths["merge_report"].exists():
        review_artifacts_payload.setdefault("merge_report_path", self._relativize(packet_paths["merge_report"]))

    regression_summary = _read_json(packet_paths["regression_gate"]) or {
        "status": str(gate_payload.get("regression_gate_status") or "not_audited"),
        "topic_completion_status": str(
            candidate.get("topic_completion_status") or gate_payload.get("topic_completion_status") or "not_assessed"
        ),
        "supporting_regression_question_ids": self._dedupe_strings(
            list(candidate.get("supporting_regression_question_ids") or gate_payload.get("supporting_regression_question_ids") or [])
        ),
        "supporting_oracle_ids": self._dedupe_strings(
            list(candidate.get("supporting_oracle_ids") or gate_payload.get("supporting_oracle_ids") or [])
        ),
        "supporting_regression_run_ids": self._dedupe_strings(
            list(candidate.get("supporting_regression_run_ids") or gate_payload.get("supporting_regression_run_ids") or [])
        ),
        "promotion_blockers": self._dedupe_strings(
            list(candidate.get("promotion_blockers") or gate_payload.get("promotion_blockers") or [])
        ),
        "split_clearance_status": "blocked" if bool(candidate.get("split_required")) else "clear",
        "promotion_blockers_cleared": not (
            list(candidate.get("promotion_blockers") or []) or bool(candidate.get("cited_recovery_required"))
        ),
    }
    runtime_schema_context = collect_runtime_schema_context(
        self,
        topic_slug=topic_slug,
        run_id=resolved_run_id,
        candidate_id=candidate_id,
    )

    return {
        "gate_payload": gate_payload,
        "resolved_run_id": resolved_run_id,
        "candidate": candidate,
        "resolved_backend_id": resolved_backend_id,
        "resolved_review_mode": resolved_review_mode,
        "resolved_canonical_layer": resolved_canonical_layer,
        "tpkn_root": tpkn_root,
        "card_path": card_path,
        "card_payload": card_payload,
        "mapped_type": mapped_type,
        "source_row": source_row,
        "resolved_source_id": resolved_source_id,
        "resolved_source_section": resolved_source_section,
        "resolved_source_section_title": resolved_source_section_title,
        "default_domain": default_domain,
        "default_subdomain": default_subdomain,
        "collision_rows": collision_rows,
        "requested_unit_id": requested_unit_id,
        "existing_tpkn_ids": existing_tpkn_ids,
        "merge_target": merge_target,
        "equivalence_refs": equivalence_refs,
        "target_unit_id": target_unit_id,
        "merge_outcome": merge_outcome,
        "merge_lineage": merge_lineage,
        "packet_paths": packet_paths,
        "review_artifacts_payload": review_artifacts_payload,
        "regression_summary": regression_summary,
        "runtime_schema_context": runtime_schema_context,
        "coverage_summary": coverage_summary,
        "consensus_summary": consensus_summary,
    }


def _materialize_tpkn_artifacts(
    self,
    *,
    topic_slug: str,
    candidate_id: str,
    promoted_by: str,
    notes: str | None,
    context: dict[str, Any],
) -> dict[str, Any]:
    candidate = context["candidate"]
    gate_payload = context["gate_payload"]
    incoming_unit_payload = build_tpkn_unit(
        candidate=candidate,
        unit_id=context["target_unit_id"],
        target_type=context["mapped_type"],
        domain=context["default_domain"],
        subdomain=context["default_subdomain"],
        source_id=context["resolved_source_id"],
        source_section=context["resolved_source_section"],
        source_anchor_notes=(
            f"AITP promoted candidate {candidate_id} from topic {topic_slug}; "
            + (
                "keep upstream auto-adjudication artifacts for full provenance."
                if context["resolved_review_mode"] == "ai_auto"
                else "keep upstream validation and approval artifacts for full provenance."
            )
        ),
        existing_tpkn_ids=context["existing_tpkn_ids"],
        canonical_layer=context["resolved_canonical_layer"],
        review_mode=context["resolved_review_mode"],
        promotion_route=str(gate_payload.get("route") or "L3->L4->L2"),
        review_artifacts=context["review_artifacts_payload"],
        coverage=context["coverage_summary"],
        consensus=context["consensus_summary"],
        regression_gate=context["regression_summary"],
        merge_lineage=context["merge_lineage"],
        conflict_status="none",
        equivalence_refs=context["equivalence_refs"],
    )
    unit_path = unit_path_for(context["tpkn_root"], context["mapped_type"], context["target_unit_id"])
    if context["merge_target"] and unit_path.exists():
        existing_payload = _read_json(unit_path)
        if existing_payload is None:
            raise FileNotFoundError(f"Existing merge target is missing on disk: {unit_path}")
        unit_payload = merge_tpkn_unit(existing_unit=existing_payload, incoming_unit=incoming_unit_payload)
    else:
        unit_payload = incoming_unit_payload

    manifest_path, created_manifest = ensure_source_manifest(
        tpkn_root=context["tpkn_root"],
        source_row=context["source_row"],
        source_id=context["resolved_source_id"],
        source_section=context["resolved_source_section"],
        source_section_title=context["resolved_source_section_title"],
        source_section_summary=str(candidate.get("summary") or context["resolved_source_section_title"]),
    )
    merge_report = {
        "candidate_id": candidate_id,
        "target_unit_id": context["target_unit_id"],
        "target_unit_type": context["mapped_type"],
        "merge_outcome": context["merge_outcome"],
        "requested_unit_id": context["requested_unit_id"],
        "selected_collision": context["merge_target"] or {},
        "collision_rows": context["collision_rows"],
        "equivalence_refs": context["equivalence_refs"],
        "review_mode": context["resolved_review_mode"],
        "canonical_layer": context["resolved_canonical_layer"],
        "updated_at": _now_iso(),
        "updated_by": promoted_by,
    }
    _write_json(context["packet_paths"]["merge_report"], merge_report)
    write_external_json(unit_path, unit_payload)

    supporting_unit_paths: list[Path] = []
    question_ids = list(unit_payload.get("supporting_regression_question_ids") or [])
    oracle_ids = list(unit_payload.get("supporting_oracle_ids") or [])
    for question_id in question_ids:
        question_path = unit_path_for(context["tpkn_root"], "regression_question", question_id)
        matching_oracle_id = next(
            (
                oracle_id
                for oracle_id in oracle_ids
                if oracle_id.split(":", 1)[-1] == question_id.split(":", 1)[-1]
            ),
            oracle_ids[0] if oracle_ids else None,
        )
        question_payload = build_supporting_regression_question_unit(
            unit_id=question_id,
            domain=context["default_domain"],
            source_id=context["resolved_source_id"],
            source_section=context["resolved_source_section"],
            source_anchor_notes=(
                f"AITP generated this supporting regression surface while promoting {candidate_id} "
                f"for topic {topic_slug}."
            ),
            promoted_unit_id=context["target_unit_id"],
            promoted_unit_title=str(unit_payload.get("title") or candidate.get("title") or context["target_unit_id"]),
            topic_slug=topic_slug,
            oracle_id=matching_oracle_id,
        )
        existing_question_payload = _read_json(question_path)
        if existing_question_payload is None or str(existing_question_payload.get("validation_status") or "") == "generated-support":
            write_external_json(question_path, question_payload)
        supporting_unit_paths.append(question_path)

    for oracle_id in oracle_ids:
        oracle_path = unit_path_for(context["tpkn_root"], "question_oracle", oracle_id)
        matching_question_id = next(
            (
                question_id
                for question_id in question_ids
                if question_id.split(":", 1)[-1] == oracle_id.split(":", 1)[-1]
            ),
            question_ids[0] if question_ids else "",
        )
        oracle_payload = build_supporting_question_oracle_unit(
            unit_id=oracle_id,
            domain=context["default_domain"],
            source_id=context["resolved_source_id"],
            source_section=context["resolved_source_section"],
            source_anchor_notes=(
                f"AITP generated this supporting oracle while promoting {candidate_id} "
                f"for topic {topic_slug}."
            ),
            promoted_unit_id=context["target_unit_id"],
            promoted_unit_title=str(unit_payload.get("title") or candidate.get("title") or context["target_unit_id"]),
            regression_question_id=matching_question_id,
            topic_slug=topic_slug,
        )
        existing_oracle_payload = _read_json(oracle_path)
        if existing_oracle_payload is None or str(existing_oracle_payload.get("validation_status") or "") == "generated-support":
            write_external_json(oracle_path, oracle_payload)
        supporting_unit_paths.append(oracle_path)

    check_results = run_tpkn_checks(
        context["tpkn_root"],
        scoped_paths=[unit_path, manifest_path, *supporting_unit_paths],
    )

    context_ref = {
        "id": candidate_id,
        "layer": "L3",
        "object_type": "candidate",
        "path": self._relativize(self._candidate_ledger_path(topic_slug, context["resolved_run_id"])),
        "title": str(candidate.get("title") or candidate_id),
        "summary": str(candidate.get("summary") or ""),
    }
    retrieved_refs = [
        {
            "id": str(row.get("id") or ""),
            "layer": "L2",
            "object_type": f"tpkn_{row.get('type') or 'unit'}",
            "path": str(row.get("path") or ""),
            "title": str(row.get("title") or row.get("id") or ""),
            "summary": str(row.get("summary") or ""),
        }
        for row in context["collision_rows"]
    ]
    consultation_paths = self._record_l2_consultation(
        topic_slug=topic_slug,
        stage="L4",
        run_id=context["resolved_run_id"],
        consultation_slug=_bounded_slug(f"tpkn-promotion-{candidate_id.lower().replace(':', '-')}"),
        context_ref=context_ref,
        purpose="Consult the external formal-theory backend before L2 promotion to detect collisions and keep writeback explicit.",
        query_text=(
            f"Check TPKN collisions and source-anchor compatibility before promoting {candidate_id} "
            f"as {context['mapped_type']}:{context['target_unit_id'].split(':', 1)[-1]}."
        ),
        requested_unit_types=[str(candidate.get("candidate_type") or "")],
        retrieved_refs=retrieved_refs,
        result_summary=(
            f"Found {len(retrieved_refs)} nearby TPKN objects before unit promotion; merge outcome={context['merge_outcome']}."
            if retrieved_refs
            else f"No obvious TPKN collision was found before unit promotion; merge outcome={context['merge_outcome']}."
        ),
        effect_on_work=(
            f"Created or updated `{context['target_unit_id']}` in the configured TPKN backend and recorded the collision scan."
        ),
        outcome="candidate_narrowed" if retrieved_refs else "no_change",
        projection_paths=[
            self._relativize(self._candidate_ledger_path(topic_slug, context["resolved_run_id"])),
            self._relativize(self._promotion_gate_paths(topic_slug)["json"]),
            self._relativize(self._promotion_gate_paths(topic_slug)["note"]),
            self._relativize(context["packet_paths"]["merge_report"]),
        ],
        requested_by=promoted_by,
        produced_by=promoted_by,
        written_by=promoted_by,
        retrieval_profile="tpkn-unit-index-and-source-anchor-scan",
    )
    return {
        "unit_path": unit_path,
        "unit_payload": unit_payload,
        "manifest_path": manifest_path,
        "created_manifest": created_manifest,
        "check_results": check_results,
        "consultation_paths": consultation_paths,
    }


def _record_promotion_and_finalize(
    self,
    *,
    topic_slug: str,
    candidate_id: str,
    promoted_by: str,
    notes: str | None,
    context: dict[str, Any],
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    gate_payload = context["gate_payload"]
    candidate = context["candidate"]
    promoted_at = _now_iso()
    decision_id = f"decision:{candidate_id.lower().replace(':', '-')}-tpkn-promotion"
    decision_row = {
        "decision_id": decision_id,
        "candidate_id": candidate_id,
        "route": str(gate_payload.get("route") or "L3->L4->L2"),
        "verdict": "accepted",
        "promoted_units": [context["target_unit_id"]],
        "fallback_targets": [],
        "evidence_refs": self._dedupe_strings(
            [
                self._relativize(self._candidate_ledger_path(topic_slug, context["resolved_run_id"])),
                self._relativize(self._promotion_gate_paths(topic_slug)["json"]),
                self._relativize(Path(artifacts["consultation_paths"]["consultation_result_path"])),
                self._relativize(context["packet_paths"]["merge_report"]),
                str(artifacts["unit_path"]),
                str(artifacts["manifest_path"]),
            ]
        ),
        "decided_by": promoted_by,
        "decided_at": promoted_at,
        "review_mode": context["resolved_review_mode"],
        "canonical_layer": context["resolved_canonical_layer"],
        "coverage_status": str((context["coverage_summary"] or {}).get("status") or gate_payload.get("coverage_status") or "not_audited"),
        "consensus_status": str((context["consensus_summary"] or {}).get("status") or gate_payload.get("consensus_status") or "not_requested"),
        "regression_gate_status": str(
            context["regression_summary"].get("status") or gate_payload.get("regression_gate_status") or "not_audited"
        ),
        "merge_outcome": context["merge_outcome"],
        "merge_target_unit": str((context["merge_target"] or {}).get("id") or ""),
        "reason": notes
        or (
            "Promoted after theory auto-adjudication and an explicit TPKN backend collision scan."
            if context["resolved_review_mode"] == "ai_auto"
            else "Promoted after explicit human approval and an explicit TPKN backend collision scan."
        ),
    }
    decisions_path = self._validation_run_root(topic_slug, context["resolved_run_id"]) / "promotion_decisions.jsonl"
    decision_rows = _read_jsonl(decisions_path)
    decision_rows = [row for row in decision_rows if row.get("decision_id") != decision_id]
    decision_rows.append(decision_row)
    _write_jsonl(decisions_path, decision_rows)

    updated_candidate = dict(candidate)
    updated_candidate["status"] = "auto_promoted" if context["resolved_review_mode"] == "ai_auto" else "promoted"
    updated_candidate["promotion_mode"] = context["resolved_review_mode"]
    updated_candidate["promoted_units"] = [context["target_unit_id"]]
    self._replace_candidate_row(topic_slug, context["resolved_run_id"], candidate_id, updated_candidate)

    gate_payload["status"] = "promoted"
    gate_payload["promotion_stage"] = "promoted"
    gate_payload["backend_id"] = context["resolved_backend_id"]
    gate_payload["target_backend_root"] = str(context["tpkn_root"])
    gate_payload["review_mode"] = context["resolved_review_mode"]
    gate_payload["canonical_layer"] = context["resolved_canonical_layer"]
    gate_payload["coverage_status"] = str((context["coverage_summary"] or {}).get("status") or gate_payload.get("coverage_status") or "not_audited")
    gate_payload["consensus_status"] = str((context["consensus_summary"] or {}).get("status") or gate_payload.get("consensus_status") or "not_requested")
    gate_payload["regression_gate_status"] = str(
        context["regression_summary"].get("status") or gate_payload.get("regression_gate_status") or "not_audited"
    )
    gate_payload["topic_completion_status"] = str(
        context["regression_summary"].get("topic_completion_status") or gate_payload.get("topic_completion_status") or "not_assessed"
    )
    gate_payload["supporting_regression_question_ids"] = self._dedupe_strings(
        list(context["regression_summary"].get("supporting_regression_question_ids") or gate_payload.get("supporting_regression_question_ids") or [])
    )
    gate_payload["supporting_oracle_ids"] = self._dedupe_strings(
        list(context["regression_summary"].get("supporting_oracle_ids") or gate_payload.get("supporting_oracle_ids") or [])
    )
    gate_payload["supporting_regression_run_ids"] = self._dedupe_strings(
        list(context["regression_summary"].get("supporting_regression_run_ids") or gate_payload.get("supporting_regression_run_ids") or [])
    )
    gate_payload["promotion_blockers"] = self._dedupe_strings(
        list(context["regression_summary"].get("promotion_blockers") or gate_payload.get("promotion_blockers") or [])
    )
    gate_payload["split_required"] = bool(
        context["regression_summary"].get("split_required")
        if "split_required" in context["regression_summary"]
        else gate_payload.get("split_required")
    )
    gate_payload["cited_recovery_required"] = bool(
        context["regression_summary"].get("cited_recovery_required")
        if "cited_recovery_required" in context["regression_summary"]
        else gate_payload.get("cited_recovery_required")
    )
    gate_payload["merge_outcome"] = context["merge_outcome"]
    gate_payload["promoted_by"] = promoted_by
    gate_payload["promoted_at"] = promoted_at
    gate_payload["promoted_units"] = [context["target_unit_id"]]
    gate_payload["notes"] = notes or gate_payload.get("notes") or ""
    gate_paths = self._write_promotion_gate(topic_slug, gate_payload)
    log_path = self._append_promotion_gate_log(
        topic_slug,
        context["resolved_run_id"],
        {
            "event": "promoted",
            "candidate_id": candidate_id,
            "status": gate_payload["status"],
            "updated_by": promoted_by,
            "updated_at": promoted_at,
            "promoted_units": [context["target_unit_id"]],
            "backend_id": context["resolved_backend_id"],
            "target_backend_root": str(context["tpkn_root"]),
            "review_mode": context["resolved_review_mode"],
            "canonical_layer": context["resolved_canonical_layer"],
            "merge_outcome": context["merge_outcome"],
            "notes": gate_payload.get("notes") or "",
        },
    )
    append_transition_history(
        topic_slug,
        {
            "run_id": context["resolved_run_id"],
            "event_kind": "promoted",
            "from_layer": str(gate_payload.get("source_layer") or "L4"),
            "to_layer": str(gate_payload.get("canonical_layer") or "L2"),
            "reason": str(gate_payload.get("notes") or f"Promotion completed into {gate_payload.get('canonical_layer') or 'L2'}."),
            "evidence_refs": [
                self._relativize(self._promotion_gate_paths(topic_slug)["json"]),
                self._relativize(self._promotion_gate_paths(topic_slug)["note"]),
                self._relativize(decisions_path),
                self._relativize(context["packet_paths"]["merge_report"]),
            ],
            "candidate_id": candidate_id,
            "recorded_at": promoted_at,
            "recorded_by": promoted_by,
        },
        kernel_root=self.kernel_root,
    )

    return {
        "decision_path": decisions_path,
        "gate_paths": gate_paths,
        "log_path": log_path,
    }


def promote_candidate(
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
    review_mode: str | None = None,
    canonical_layer: str | None = None,
    review_artifact_paths: dict[str, str] | None = None,
    coverage_summary: dict[str, Any] | None = None,
    consensus_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = _resolve_promotion_context(
        self,
        topic_slug=topic_slug,
        candidate_id=candidate_id,
        run_id=run_id,
        backend_id=backend_id,
        target_backend_root=target_backend_root,
        domain=domain,
        subdomain=subdomain,
        source_id=source_id,
        source_section=source_section,
        source_section_title=source_section_title,
        review_mode=review_mode,
        canonical_layer=canonical_layer,
        review_artifact_paths=review_artifact_paths,
        coverage_summary=coverage_summary,
        consensus_summary=consensus_summary,
    )
    artifacts = _materialize_tpkn_artifacts(
        self,
        topic_slug=topic_slug,
        candidate_id=candidate_id,
        promoted_by=promoted_by,
        notes=notes,
        context=context,
    )
    canonical_mirror = _materialize_canonical_mirror(
        self,
        topic_slug=topic_slug,
        candidate_id=candidate_id,
        promoted_by=promoted_by,
        context=context,
        artifacts=artifacts,
        unit_payload=artifacts["unit_payload"],
    )
    finalized = _record_promotion_and_finalize(
        self,
        topic_slug=topic_slug,
        candidate_id=candidate_id,
        promoted_by=promoted_by,
        notes=notes,
        context=context,
        artifacts=artifacts,
    )
    return {
        "topic_slug": topic_slug,
        "run_id": context["resolved_run_id"],
        "candidate_id": candidate_id,
        "backend_id": context["resolved_backend_id"],
        "backend_card_path": str(context["card_path"]) if context["card_path"] else None,
        "target_backend_root": str(context["tpkn_root"]),
        "target_unit_id": context["target_unit_id"],
        "target_unit_path": str(artifacts["unit_path"]),
        "source_manifest_path": str(artifacts["manifest_path"]),
        "source_manifest_created": artifacts["created_manifest"],
        "promotion_decision_path": str(finalized["decision_path"]),
        "promotion_gate_log_path": finalized["log_path"],
        "merge_report_path": str(context["packet_paths"]["merge_report"]),
        "merge_outcome": context["merge_outcome"],
        "canonical_mirror_path": canonical_mirror["path"],
        "canonical_mirror_unit_id": canonical_mirror["unit_id"],
        "canonical_mirror_unit_type": canonical_mirror["unit_type"],
        "tpkn_check": artifacts["check_results"]["check"],
        "tpkn_build": artifacts["check_results"]["build"],
        "consultation": artifacts["consultation_paths"],
        **finalized["gate_paths"],
    }
