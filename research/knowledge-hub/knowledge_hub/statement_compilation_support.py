from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

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


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    compatibility_path = compatibility_projection_path(path)
    if compatibility_path is not None and compatibility_path != path:
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        compatibility_path.write_text(text, encoding="utf-8")


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _slugify(text: str) -> str:
    lowered = re.sub(r"[^a-z0-9]+", "-", str(text or "").lower())
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "statement"


def _statement_kind(candidate_type: str) -> str:
    normalized = str(candidate_type or "").strip().lower()
    mapping = {
        "definition_card": "definition",
        "notation_card": "definition",
        "assumption_card": "axiom",
        "regime_card": "axiom",
        "theorem_card": "theorem",
        "claim_card": "conjecture",
        "proof_fragment": "lemma",
        "derivation_step": "lemma",
        "derivation_object": "theorem",
        "equation_card": "theorem",
        "bridge": "theorem",
        "equivalence_map": "theorem",
    }
    return mapping.get(normalized, "definition")


def _signature_for_kind(statement_kind: str) -> str:
    if statement_kind == "definition":
        return "(ctx : FormalContext) : FormalObject"
    if statement_kind == "axiom":
        return "(ctx : FormalContext) : Prop"
    if statement_kind in {"theorem", "lemma", "conjecture"}:
        return "(ctx : FormalContext) : Prop"
    return "(ctx : FormalContext) : FormalObject"


def _assistant_targets(row: dict[str, Any]) -> list[dict[str, str]]:
    targets = [
        {
            "assistant": "lean4",
            "kind": "proof_assistant",
            "status": "candidate_target",
            "reason": "Current AITP formal-theory export already has a bounded Lean bridge.",
        },
        {
            "assistant": "symbolic_checker",
            "kind": "verifier",
            "status": "candidate_target",
            "reason": "Statement-compilation should stay verifier-aware without being tied to one proof assistant.",
        },
    ]
    route = str(row.get("proposed_validation_route") or "").strip().lower()
    if any(token in route for token in ("numeric", "numerical", "benchmark", "simulation")):
        targets.append(
            {
                "assistant": "numerical_validator",
                "kind": "verifier",
                "status": "candidate_target",
                "reason": "The declared validation route still depends on numerical agreement checks.",
            }
        )
    return targets


def _source_anchor_ids(row: dict[str, Any], structure_map: dict[str, Any]) -> list[str]:
    anchors = [str(item.get("id") or "").strip() for item in row.get("origin_refs") or [] if str(item.get("id") or "").strip()]
    anchors.extend(
        [
            str(section.get("section_id") or "").strip()
            for section in structure_map.get("sections") or []
            if str(section.get("section_id") or "").strip()
        ]
    )
    deduped: list[str] = []
    seen: set[str] = set()
    for item in anchors:
        if item and item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def _dependency_ids(
    self,
    row: dict[str, Any],
    derivation_graph: dict[str, Any],
) -> list[str]:
    return self._dedupe_strings(
        [str(node.get("id") or "").strip() for node in derivation_graph.get("nodes") or []]
        + list(row.get("supporting_regression_question_ids") or [])
        + list(row.get("supporting_oracle_ids") or [])
        + list(row.get("supporting_regression_run_ids") or [])
    )


def _build_proof_holes(
    *,
    row: dict[str, Any],
    structure_map: dict[str, Any],
    notation_table: dict[str, Any],
    derivation_graph: dict[str, Any],
    regression_gate: dict[str, Any],
    declaration_id: str,
    source_anchor_ids: list[str],
    assistant_targets: list[dict[str, str]],
) -> list[dict[str, Any]]:
    verifier_targets = [str(item.get("assistant") or "").strip() for item in assistant_targets if str(item.get("assistant") or "").strip()]
    holes: list[dict[str, Any]] = []

    for section in structure_map.get("sections") or []:
        if str(section.get("status") or "").strip() == "missing":
            section_id = str(section.get("section_id") or "(missing)").strip()
            holes.append(
                {
                    "hole_id": f"{declaration_id}:missing-section:{_slugify(section_id)}",
                    "category": "source_section_recovery",
                    "status": "open",
                    "claim": f"Recover the missing source section `{section_id}` before proof repair continues.",
                    "source_anchor_ids": [section_id],
                    "required_artifacts": [section_id],
                    "verifier_targets": verifier_targets,
                    "close_condition": "A durable source section anchor exists and the section boundary is no longer source-cited-only.",
                }
            )

    if str(notation_table.get("status") or "").strip() != "captured":
        holes.append(
            {
                "hole_id": f"{declaration_id}:notation-capture",
                "category": "notation_capture",
                "status": "open",
                "claim": "Complete the notation table before verifier-guided proof repair.",
                "source_anchor_ids": source_anchor_ids,
                "required_artifacts": ["notation_table.json"],
                "verifier_targets": verifier_targets,
                "close_condition": "Notation bindings are explicit enough to compile a declaration without symbol ambiguity.",
            }
        )

    if str(derivation_graph.get("status") or "").strip() != "captured":
        holes.append(
            {
                "hole_id": f"{declaration_id}:derivation-capture",
                "category": "derivation_capture",
                "status": "open",
                "claim": "Complete the derivation graph before verifier-guided proof repair.",
                "source_anchor_ids": source_anchor_ids,
                "required_artifacts": ["derivation_graph.json"],
                "verifier_targets": verifier_targets,
                "close_condition": "The derivation spine is explicit enough to map proof steps onto the declaration skeleton.",
            }
        )

    for blocker in regression_gate.get("blocking_reasons") or []:
        text = str(blocker).strip()
        if text:
            holes.append(
                {
                    "hole_id": f"{declaration_id}:regression:{_slugify(text)}",
                    "category": "regression_gate",
                    "status": "open",
                    "claim": f"Regression blocker: {text}",
                    "source_anchor_ids": source_anchor_ids,
                    "required_artifacts": list(row.get("supporting_regression_question_ids") or []),
                    "verifier_targets": verifier_targets,
                    "close_condition": "The regression blocker is resolved with durable supporting evidence.",
                }
            )

    for blocker in row.get("promotion_blockers") or []:
        text = str(blocker).strip()
        if text:
            holes.append(
                {
                    "hole_id": f"{declaration_id}:candidate-blocker:{_slugify(text)}",
                    "category": "candidate_blocker",
                    "status": "open",
                    "claim": text,
                    "source_anchor_ids": source_anchor_ids,
                    "required_artifacts": [str(row.get("candidate_id") or "")],
                    "verifier_targets": verifier_targets,
                    "close_condition": "The candidate blocker is cleared without widening the bounded family.",
                }
            )

    if bool(row.get("split_required")):
        holes.append(
            {
                "hole_id": f"{declaration_id}:split-before-repair",
                "category": "scope_split",
                "status": "open",
                "claim": "Split the candidate into narrower statement families before proof repair.",
                "source_anchor_ids": source_anchor_ids,
                "required_artifacts": [str(row.get("candidate_id") or "")],
                "verifier_targets": verifier_targets,
                "close_condition": "The repair target is a bounded theorem/definition family instead of a mixed candidate.",
            }
        )

    if bool(row.get("cited_recovery_required")):
        holes.append(
            {
                "hole_id": f"{declaration_id}:cited-recovery",
                "category": "cited_recovery",
                "status": "open",
                "claim": "Return to L0 and recover cited prerequisites before proof repair.",
                "source_anchor_ids": source_anchor_ids,
                "required_artifacts": list(row.get("followup_gap_ids") or []) or [str(row.get("candidate_id") or "")],
                "verifier_targets": verifier_targets,
                "close_condition": "The statement family no longer depends on uncaptured cited background.",
            }
        )

    return holes


def _packet_for_candidate(
    self,
    *,
    topic_slug: str,
    run_id: str,
    row: dict[str, Any],
    updated_by: str,
) -> dict[str, Any]:
    candidate_id = str(row.get("candidate_id") or "").strip()
    packet_paths = self._statement_compilation_packet_paths(topic_slug, run_id, candidate_id)
    theory_packet_paths = self._theory_packet_paths(topic_slug, run_id, candidate_id)
    structure_map = _read_json(theory_packet_paths["structure_map"]) or {}
    coverage_ledger = _read_json(theory_packet_paths["coverage_ledger"]) or {}
    notation_table = _read_json(theory_packet_paths["notation_table"]) or {}
    derivation_graph = _read_json(theory_packet_paths["derivation_graph"]) or {}
    regression_gate = _read_json(theory_packet_paths["regression_gate"]) or {}

    statement_kind = _statement_kind(str(row.get("candidate_type") or ""))
    namespace = f"AITP.{self._slug_to_camel(topic_slug)}"
    declaration_name = _slugify(str(row.get("title") or candidate_id)).replace("-", "_")
    if not re.match(r"^[A-Za-z_]", declaration_name):
        declaration_name = f"decl_{declaration_name}"
    identifier = f"{namespace}.{declaration_name}"
    source_anchor_ids = _source_anchor_ids(row, structure_map)
    dependency_ids = _dependency_ids(self, row, derivation_graph)
    assistant_targets = _assistant_targets(row)
    declaration_id = f"statement_compilation:{_slugify(candidate_id)}:primary"
    proof_holes = _build_proof_holes(
        row=row,
        structure_map=structure_map,
        notation_table=notation_table,
        derivation_graph=derivation_graph,
        regression_gate=regression_gate,
        declaration_id=declaration_id,
        source_anchor_ids=source_anchor_ids,
        assistant_targets=assistant_targets,
    )
    declarations = [
        {
            "declaration_id": declaration_id,
            "statement_kind": statement_kind,
            "declaration_role": "primary_statement",
            "identifier": identifier,
            "signature": _signature_for_kind(statement_kind),
            "natural_language_statement": str(row.get("summary") or row.get("question") or row.get("title") or candidate_id),
            "dependency_ids": dependency_ids,
            "source_anchor_ids": source_anchor_ids,
            "temporary_proof_holes": [str(item.get("hole_id") or "") for item in proof_holes],
        }
    ]
    packet_status = "ready" if not proof_holes else "needs_repair"
    packet_payload = {
        "$schema": "https://aitp.local/schemas/statement-compilation-packet.schema.json",
        "compilation_version": 1,
        "topic_slug": topic_slug,
        "run_id": run_id,
        "candidate_id": candidate_id,
        "candidate_type": str(row.get("candidate_type") or ""),
        "title": str(row.get("title") or ""),
        "status": packet_status,
        "primary_statement_kind": statement_kind,
        "primary_identifier": identifier,
        "assistant_targets": assistant_targets,
        "declaration_count": len(declarations),
        "proof_hole_count": len(proof_holes),
        "dependency_ids": dependency_ids,
        "notation_bindings": list(notation_table.get("bindings") or []),
        "equation_labels": self._dedupe_strings(list(coverage_ledger.get("equation_labels") or [])),
        "declarations": declarations,
        "proof_repair_plan_path": self._relativize(packet_paths["repair_plan"]),
        "theory_packet_refs": {
            "coverage_ledger": self._relativize(theory_packet_paths["coverage_ledger"]),
            "structure_map": self._relativize(theory_packet_paths["structure_map"]),
            "notation_table": self._relativize(theory_packet_paths["notation_table"]),
            "derivation_graph": self._relativize(theory_packet_paths["derivation_graph"]),
            "regression_gate": self._relativize(theory_packet_paths["regression_gate"]),
        },
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    repair_plan_payload = {
        "$schema": "https://aitp.local/schemas/proof-repair-plan.schema.json",
        "plan_version": 1,
        "topic_slug": topic_slug,
        "run_id": run_id,
        "candidate_id": candidate_id,
        "status": packet_status,
        "compilation_path": self._relativize(packet_paths["json"]),
        "repair_stages": [
            {
                "stage_id": "statement_compilation",
                "stage_name": "statement_compilation",
                "status": "complete",
                "summary": "Informal bounded statement compiled into declaration skeletons with explicit temporary proof holes.",
            },
            {
                "stage_id": "verifier_guided_repair",
                "stage_name": "verifier_guided_repair",
                "status": "ready" if not proof_holes else "pending",
                "summary": (
                    "No open proof holes remain for the current bounded packet."
                    if not proof_holes
                    else "Use verifier feedback to close the explicit proof holes before claiming a proof-grade bridge."
                ),
            },
            {
                "stage_id": "downstream_target_selection",
                "stage_name": "downstream_target_selection",
                "status": "ready",
                "summary": "Downstream targets remain explicit and proof-assistant agnostic at the packet level.",
            },
        ],
        "proof_holes": proof_holes,
        "downstream_targets": assistant_targets,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }

    _write_json(packet_paths["json"], packet_payload)
    _write_text(packet_paths["note"], self._render_statement_compilation_packet_markdown(packet_payload))
    _write_json(packet_paths["repair_plan"], repair_plan_payload)
    _write_text(packet_paths["repair_plan_note"], self._render_proof_repair_plan_markdown(repair_plan_payload))

    return {
        "summary_row": {
            "candidate_id": candidate_id,
            "candidate_type": str(row.get("candidate_type") or ""),
            "statement_kind": statement_kind,
            "status": packet_status,
            "proof_hole_count": len(proof_holes),
            "packet_path": self._relativize(packet_paths["json"]),
            "packet_note_path": self._relativize(packet_paths["note"]),
            "repair_plan_path": self._relativize(packet_paths["repair_plan"]),
            "repair_plan_note_path": self._relativize(packet_paths["repair_plan_note"]),
        },
        "is_ready": packet_status == "ready",
    }


def materialize_statement_compilation(
    self,
    *,
    topic_slug: str,
    run_id: str,
    candidate_rows: list[dict[str, Any]],
    updated_by: str,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    selected_rows = list(candidate_rows)
    if candidate_id:
        selected_rows = [row for row in selected_rows if str(row.get("candidate_id") or "").strip() == candidate_id]

    rows: list[dict[str, Any]] = []
    ready_packet_count = 0
    for row in selected_rows:
        current_candidate_id = str(row.get("candidate_id") or "").strip()
        if not current_candidate_id:
            continue
        result = _packet_for_candidate(
            self,
            topic_slug=topic_slug,
            run_id=run_id,
            row=row,
            updated_by=updated_by,
        )
        rows.append(result["summary_row"])
        if result["is_ready"]:
            ready_packet_count += 1

    packet_count = len(rows)
    needs_repair_count = packet_count - ready_packet_count
    status = "empty" if packet_count == 0 else "ready" if needs_repair_count == 0 else "needs_repair"
    if status == "empty":
        summary = "No bounded candidate currently qualifies for statement compilation."
    elif status == "ready":
        summary = "Statement compilation is ready for all currently selected bounded candidates."
    else:
        summary = "Statement compilation succeeded, but verifier-guided proof repair still has open holes."

    active_paths = self._statement_compilation_active_paths(topic_slug)
    payload = {
        "$schema": "https://aitp.local/schemas/statement-compilation-active.schema.json",
        "compilation_version": 1,
        "topic_slug": topic_slug,
        "run_id": run_id,
        "status": status,
        "packet_count": packet_count,
        "ready_packet_count": ready_packet_count,
        "needs_repair_count": needs_repair_count,
        "packets": rows,
        "summary": summary,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    _write_json(active_paths["json"], payload)
    _write_text(active_paths["note"], self._render_statement_compilation_index_markdown(payload))
    return {
        **payload,
        "statement_compilation_path": str(active_paths["json"]),
        "statement_compilation_note_path": str(active_paths["note"]),
    }
