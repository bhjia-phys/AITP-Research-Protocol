from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .topic_truth_root_support import compatibility_projection_path


def _read_json(path: Path) -> dict[str, Any] | None:
    target = path
    if not target.exists():
        compatibility_path = compatibility_projection_path(path)
        if compatibility_path is None or not compatibility_path.exists():
            return None
        target = compatibility_path
    return json.loads(target.read_text(encoding="utf-8"))


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


def _lean_kind_from_statement_kind(statement_kind: str) -> str:
    normalized = str(statement_kind or "").strip().lower()
    if normalized == "definition":
        return "def"
    if normalized == "axiom":
        return "axiom"
    if normalized == "lemma":
        return "lemma"
    if normalized in {"theorem", "conjecture"}:
        return "theorem"
    return "def"


def _proof_obligations_from_repair_plan(repair_plan: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for hole in repair_plan.get("proof_holes") or []:
        rows.append(
            {
                "obligation_id": str(hole.get("hole_id") or "(missing)"),
                "category": str(hole.get("category") or "proof_hole"),
                "status": "blocked" if str(hole.get("status") or "open") == "open" else str(hole.get("status") or "blocked"),
                "claim": str(hole.get("claim") or "(missing)"),
                "prerequisite_ids": [str(item) for item in (hole.get("required_artifacts") or []) if str(item).strip()],
                "equation_labels": [],
                "source_anchor_ids": [str(item) for item in (hole.get("source_anchor_ids") or []) if str(item).strip()],
                "required_logical_move": "Follow the explicit proof-repair plan and close the hole through verifier-guided repair.",
                "expected_output_statement": str(hole.get("close_condition") or "Close the proof hole with durable verifier-backed evidence."),
            }
        )
    return rows


def _build_proof_obligation_rows(
    *,
    row: dict[str, Any],
    structure_map: dict[str, Any],
    notation_table: dict[str, Any],
    derivation_graph: dict[str, Any],
    regression_gate: dict[str, Any],
    current_candidate_id: str,
    dependency_ids: list[str],
    equation_labels: list[str],
) -> list[dict[str, Any]]:
    proof_obligation_rows: list[dict[str, Any]] = []
    for section in structure_map.get("sections") or []:
        if str(section.get("status") or "") == "missing":
            section_id = str(section.get("section_id") or "(missing)")
            proof_obligation_rows.append(
                {
                    "obligation_id": f"proof_obligation:{_slugify(current_candidate_id)}:section:{_slugify(section_id)}",
                    "category": "source_section_recovery",
                    "status": "source-cited-only",
                    "claim": f"Recover the missing source section `{section_id}` before Lean export.",
                    "prerequisite_ids": [section_id],
                    "equation_labels": equation_labels,
                    "source_anchor_ids": [section_id],
                    "required_logical_move": "Return to L0 and ingest the cited section so the omitted derivation can be grounded.",
                    "expected_output_statement": f"The theorem family regains a grounded section-level derivation for `{section_id}`.",
                }
            )
    if str(notation_table.get("status") or "") != "captured":
        proof_obligation_rows.append(
            {
                "obligation_id": f"proof_obligation:{_slugify(current_candidate_id)}:notation-capture",
                "category": "notation_capture",
                "status": "blocked",
                "claim": "Complete the notation table before Lean export.",
                "prerequisite_ids": dependency_ids,
                "equation_labels": equation_labels,
                "source_anchor_ids": [],
                "required_logical_move": "Bind every non-trivial symbol to an explicit meaning and regime.",
                "expected_output_statement": "Notation bindings are complete enough for declaration-level formalization.",
            }
        )
    if str(derivation_graph.get("status") or "") != "captured":
        proof_obligation_rows.append(
            {
                "obligation_id": f"proof_obligation:{_slugify(current_candidate_id)}:derivation-capture",
                "category": "derivation_capture",
                "status": "blocked",
                "claim": "Complete the derivation graph before Lean export.",
                "prerequisite_ids": dependency_ids,
                "equation_labels": equation_labels,
                "source_anchor_ids": [],
                "required_logical_move": "Decompose the derivation into explicit nodes and edges instead of leaving the proof spine implicit.",
                "expected_output_statement": "The derivation graph exposes the ordered proof spine used by the target declaration.",
            }
        )
    for blocker in row.get("promotion_blockers") or []:
        text = str(blocker).strip()
        if text:
            proof_obligation_rows.append(
                {
                    "obligation_id": f"proof_obligation:{_slugify(current_candidate_id)}:blocker:{_slugify(text)[:40]}",
                    "category": "candidate_blocker",
                    "status": "blocked",
                    "claim": text,
                    "prerequisite_ids": dependency_ids,
                    "equation_labels": equation_labels,
                    "source_anchor_ids": [],
                    "required_logical_move": "Resolve the declared candidate blocker before exporting this family into Lean.",
                    "expected_output_statement": "The candidate blocker is cleared without widening scope or hiding missing steps.",
                }
            )
    if _as_bool(row.get("split_required")):
        proof_obligation_rows.append(
            {
                "obligation_id": f"proof_obligation:{_slugify(current_candidate_id)}:split-before-export",
                "category": "scope_split",
                "status": "blocked",
                "claim": "Split the candidate into narrower formal units before Lean export.",
                "prerequisite_ids": [current_candidate_id],
                "equation_labels": equation_labels,
                "source_anchor_ids": [],
                "required_logical_move": "Emit a candidate split contract and export only bounded children.",
                "expected_output_statement": "The Lean bridge targets a bounded theorem/definition family rather than a mixed candidate.",
            }
        )
    if _as_bool(row.get("cited_recovery_required")):
        proof_obligation_rows.append(
            {
                "obligation_id": f"proof_obligation:{_slugify(current_candidate_id)}:cited-recovery",
                "category": "cited_recovery",
                "status": "source-cited-only",
                "claim": "Return to L0 for cited-source recovery before Lean export.",
                "prerequisite_ids": [current_candidate_id],
                "equation_labels": equation_labels,
                "source_anchor_ids": [],
                "required_logical_move": "Ingest the cited prerequisite source and route the recovered units back through L1/L3/L4.",
                "expected_output_statement": "The proof family no longer depends on uncaptured cited background.",
            }
        )
    for item in regression_gate.get("blocking_reasons") or []:
        text = str(item).strip()
        if text:
            proof_obligation_rows.append(
                {
                    "obligation_id": f"proof_obligation:{_slugify(current_candidate_id)}:regression:{_slugify(text)[:40]}",
                    "category": "regression_gate",
                    "status": "blocked",
                    "claim": f"Regression gate: {text}",
                    "prerequisite_ids": list(row.get("supporting_regression_question_ids") or []),
                    "equation_labels": equation_labels,
                    "source_anchor_ids": [],
                    "required_logical_move": "Repair the regression-backed blocker rather than bypassing the gate.",
                    "expected_output_statement": "The regression gate passes with explicit supporting evidence.",
                }
            )
    for item in row.get("followup_gap_ids") or []:
        text = str(item).strip()
        if text:
            proof_obligation_rows.append(
                {
                    "obligation_id": f"proof_obligation:{_slugify(current_candidate_id)}:gap:{_slugify(text)}",
                    "category": "followup_gap",
                    "status": "deferred",
                    "claim": f"Open follow-up gap: {text}",
                    "prerequisite_ids": [text],
                    "equation_labels": equation_labels,
                    "source_anchor_ids": [text],
                    "required_logical_move": "Re-enter L0 and resolve the open gap before claiming a proof-grade export.",
                    "expected_output_statement": "The referenced open gap is either recovered or explicitly routed as future work.",
                }
            )
    return proof_obligation_rows


def _materialize_candidate_packet(
    self,
    *,
    topic_slug: str,
    run_id: str,
    row: dict[str, Any],
    updated_by: str,
) -> dict[str, Any]:
    current_candidate_id = str(row.get("candidate_id") or "").strip()
    packet_paths = self._lean_bridge_packet_paths(topic_slug, run_id, current_candidate_id)
    statement_paths = self._statement_compilation_packet_paths(topic_slug, run_id, current_candidate_id)
    theory_packet_paths = self._theory_packet_paths(topic_slug, run_id, current_candidate_id)
    coverage_ledger = _read_json(theory_packet_paths["coverage_ledger"]) or {}
    structure_map = _read_json(theory_packet_paths["structure_map"]) or {}
    notation_table = _read_json(theory_packet_paths["notation_table"]) or {}
    derivation_graph = _read_json(theory_packet_paths["derivation_graph"]) or {}
    regression_gate = _read_json(theory_packet_paths["regression_gate"]) or {}
    statement_compilation = _read_json(statement_paths["json"]) or {}
    proof_repair_plan = _read_json(statement_paths["repair_plan"]) or {}
    namespace = f"AITP.{self._slug_to_camel(topic_slug)}"
    primary_declaration = ((statement_compilation.get("declarations") or [{}])[0]) if statement_compilation else {}
    compiled_identifier = str(primary_declaration.get("identifier") or "").strip()
    declaration_kind = (
        _lean_kind_from_statement_kind(str(primary_declaration.get("statement_kind") or ""))
        if compiled_identifier
        else self._lean_declaration_kind(str(row.get("candidate_type") or ""))
    )
    declaration_name = compiled_identifier.rsplit(".", 1)[-1] if compiled_identifier else _slugify(str(row.get("title") or current_candidate_id)).replace("-", "_")
    if not re.match(r"^[A-Za-z_]", declaration_name):
        declaration_name = f"decl_{declaration_name}"
    dependency_ids = self._dedupe_strings(
        list(statement_compilation.get("dependency_ids") or [])
        or (
            [str(node.get("id") or "").strip() for node in derivation_graph.get("nodes") or []]
            + list(row.get("supporting_regression_question_ids") or [])
            + list(row.get("supporting_oracle_ids") or [])
            + list(row.get("supporting_regression_run_ids") or [])
        )
    )
    equation_labels = self._dedupe_strings(list(coverage_ledger.get("equation_labels") or []))
    proof_obligation_rows = _proof_obligations_from_repair_plan(proof_repair_plan)
    if not proof_obligation_rows:
        proof_obligation_rows = _build_proof_obligation_rows(
            row=row,
            structure_map=structure_map,
            notation_table=notation_table,
            derivation_graph=derivation_graph,
            regression_gate=regression_gate,
            current_candidate_id=current_candidate_id,
            dependency_ids=dependency_ids,
            equation_labels=equation_labels,
        )
    proof_obligations = self._dedupe_strings([f"{item['status']}: {item['claim']}" for item in proof_obligation_rows])
    status_counts: dict[str, int] = {}
    for proof_row in proof_obligation_rows:
        proof_status = str(proof_row.get("status") or "blocked")
        status_counts[proof_status] = status_counts.get(proof_status, 0) + 1
    status = "ready" if not proof_obligation_rows else "needs_refinement"
    statement_text = str(
        primary_declaration.get("natural_language_statement")
        or statement_compilation.get("title")
        or row.get("summary")
        or row.get("question")
        or row.get("title")
        or current_candidate_id
    )
    lean_skeleton_lines = [
        "import Mathlib",
        "",
        f"namespace {namespace}",
        "",
        f"{declaration_kind} {declaration_name} : Prop := by",
        "  sorry",
        "",
        "end " + namespace,
    ]
    proof_obligations_payload = {
        "bridge_version": 1,
        "topic_slug": topic_slug,
        "run_id": run_id,
        "candidate_id": current_candidate_id,
        "obligations": proof_obligation_rows,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    proof_state_payload = {
        "bridge_version": 1,
        "topic_slug": topic_slug,
        "run_id": run_id,
        "candidate_id": current_candidate_id,
        "status": status,
        "obligation_count": len(proof_obligation_rows),
        "status_counts": status_counts,
        "obligation_ids": [item["obligation_id"] for item in proof_obligation_rows],
        "dependency_ids": dependency_ids,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    packet_payload = {
        "$schema": "https://aitp.local/schemas/lean-ready-packet.schema.json",
        "bridge_version": 1,
        "topic_slug": topic_slug,
        "run_id": run_id,
        "candidate_id": current_candidate_id,
        "candidate_type": str(row.get("candidate_type") or ""),
        "status": status,
        "namespace": namespace,
        "declaration_kind": declaration_kind,
        "declaration_name": declaration_name,
        "statement_text": statement_text,
        "dependency_ids": dependency_ids,
        "equation_labels": equation_labels,
        "regression_gate_status": str(regression_gate.get("status") or "not_audited"),
        "notation_bindings": list(statement_compilation.get("notation_bindings") or notation_table.get("bindings") or []),
        "proof_obligations": proof_obligations,
        "proof_obligation_count": len(proof_obligation_rows),
        "proof_obligations_path": self._relativize(packet_paths["proof_obligations"]),
        "proof_state_path": self._relativize(packet_paths["proof_state"]),
        "statement_compilation_path": self._relativize(statement_paths["json"]),
        "proof_repair_plan_path": self._relativize(statement_paths["repair_plan"]),
        "theory_packet_refs": {
            "coverage_ledger": self._relativize(theory_packet_paths["coverage_ledger"]),
            "structure_map": self._relativize(theory_packet_paths["structure_map"]),
            "notation_table": self._relativize(theory_packet_paths["notation_table"]),
            "derivation_graph": self._relativize(theory_packet_paths["derivation_graph"]),
            "regression_gate": self._relativize(theory_packet_paths["regression_gate"]),
        },
        "lean_skeleton_lines": lean_skeleton_lines,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    _write_json(packet_paths["proof_obligations"], proof_obligations_payload)
    _write_text(
        packet_paths["proof_obligations_note"],
        self._render_proof_obligations_markdown(proof_obligation_rows),
    )
    _write_json(packet_paths["proof_state"], proof_state_payload)
    _write_text(
        packet_paths["proof_state_note"],
        self._render_proof_state_markdown(proof_state_payload),
    )
    _write_json(packet_paths["json"], packet_payload)
    _write_text(packet_paths["note"], self._render_lean_bridge_packet_markdown(packet_payload))
    return {
        "summary_row": {
            "candidate_id": current_candidate_id,
            "candidate_type": str(row.get("candidate_type") or ""),
            "declaration_kind": declaration_kind,
            "status": status,
            "proof_obligation_count": len(proof_obligation_rows),
            "packet_path": self._relativize(packet_paths["json"]),
            "packet_note_path": self._relativize(packet_paths["note"]),
            "proof_obligations_path": self._relativize(packet_paths["proof_obligations"]),
            "proof_state_path": self._relativize(packet_paths["proof_state"]),
        },
        "is_ready": status == "ready",
    }


def materialize_lean_bridge(
    self,
    *,
    topic_slug: str,
    run_id: str | None,
    candidate_rows: list[dict[str, Any]],
    updated_by: str,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    selected_rows = candidate_rows
    if candidate_id:
        selected_rows = [
            row for row in candidate_rows if str(row.get("candidate_id") or "").strip() == candidate_id
        ]

    packets: list[dict[str, Any]] = []
    ready_packet_count = 0
    for row in selected_rows:
        current_candidate_id = str(row.get("candidate_id") or "").strip()
        if not current_candidate_id or not run_id:
            continue
        if str(row.get("candidate_type") or "").strip() == "topic_skill_projection":
            continue
        packet_result = _materialize_candidate_packet(
            self,
            topic_slug=topic_slug,
            run_id=run_id,
            row=row,
            updated_by=updated_by,
        )
        packets.append(packet_result["summary_row"])
        if packet_result["is_ready"]:
            ready_packet_count += 1

    active_paths = self._lean_bridge_active_paths(topic_slug)
    if not packets:
        status = "empty"
        summary = "No candidate packet is available for Lean-ready export yet."
    elif ready_packet_count == len(packets):
        status = "ready"
        summary = "All selected packets are Lean-ready at the current shell level."
    else:
        status = "needs_refinement"
        summary = "At least one selected packet still carries proof obligations before Lean export."
    payload = {
        "$schema": "https://aitp.local/schemas/lean-bridge-active.schema.json",
        "bridge_version": 1,
        "topic_slug": topic_slug,
        "run_id": run_id or "",
        "status": status,
        "packet_count": len(packets),
        "ready_packet_count": ready_packet_count,
        "needs_refinement_count": max(len(packets) - ready_packet_count, 0),
        "packets": packets,
        "summary": summary,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    _write_json(active_paths["json"], payload)
    _write_text(active_paths["note"], self._render_lean_bridge_index_markdown(payload))
    return {
        **payload,
        "lean_bridge_path": str(active_paths["json"]),
        "lean_bridge_note_path": str(active_paths["note"]),
    }
