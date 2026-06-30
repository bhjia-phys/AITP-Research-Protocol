"""Read-only note-outline compiler for recorded research structure."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.authorities import list_authorities_for_topic
from brain.v5.models import (
    ArtifactRecord,
    ClaimRecord,
    ClaimStatusRecord,
    EvidenceRecord,
    ObjectRelationRecord,
    PhysicsObjectRecord,
    ProofObligationRecord,
    SensemakingReportRecord,
    SourceAssetRecord,
    ToolRunRecord,
    ValidationResultRecord,
)
from brain.v5.objective_graph import build_objective_graph
from brain.v5.paths import WorkspacePaths
from brain.v5.recovery_session import recover_session_binding_for_read
from brain.v5.research_distillation import build_research_distillation_candidates
from brain.v5.store import list_valid_records


def compile_note_outline(
    ws: WorkspacePaths,
    session_id: str,
    *,
    style: str = "jhep",
    candidate_limit: int = 8,
) -> dict[str, Any]:
    """Compile typed records into a publication-note outline readiness surface.

    This is a second-layer planning surface.  It can explain which typed
    records are enough to draft a section and which are still missing, but it
    does not write notes, create L2 memory, create skills, or update claim
    trust.
    """

    recovered = recover_session_binding_for_read(ws, session_id)
    session = recovered.session
    topic_id = session.topic_id
    objective_graph = build_objective_graph(ws, session.session_id)
    distillation = build_research_distillation_candidates(ws, session.session_id, limit=candidate_limit)
    records = _topic_records(ws, topic_id)
    outline_style = _normalize_style(style)
    templates = _templates_for_topic(topic_id, records, style=outline_style)
    sections = [
        _section_payload(template, topic_id=topic_id, active_claim_id=session.active_claim, records=records)
        for template in templates
    ]
    ready = [section for section in sections if section["readiness_state"] == "draftable"]
    blocked = [section for section in sections if section["readiness_state"] != "draftable"]
    payload = {
        "ok": True,
        "kind": "note_outline",
        "outline_id": f"note-outline:{topic_id}:{session.session_id}:{outline_style}",
        "topic_id": topic_id,
        "session_id": session.session_id,
        "requested_session_id": recovered.requested_session_id,
        "recovery_selection_source": recovered.recovery_selection_source,
        "style": outline_style,
        "active_claim_id": session.active_claim,
        "sections": sections,
        "section_count": len(sections),
        "compile_summary": {
            "draftable_sections": len(ready),
            "needs_records_sections": len(blocked),
            "draftability_state": "draftable_with_gaps" if ready else "needs_first_layer_records",
            "record_counts": _record_counts(records),
        },
        "source_records": _source_records(session.session_id, objective_graph, distillation, records),
        "next_valid_actions": _next_valid_actions(blocked, distillation),
        "required_record_policy": _required_record_policy(),
        "note_boundary": {
            "does_not_write_note": True,
            "does_not_create_skills": True,
            "does_not_create_l2_memory": True,
            "does_not_update_claim_trust": True,
            "requires_human_review_before_publication": True,
            "compile_is_not_summary": (
                "The outline is a typed-record coverage check for note sections, "
                "not a trusted physics conclusion."
            ),
        },
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    payload["markdown"] = _render_markdown(payload)
    return payload


def _topic_records(ws: WorkspacePaths, topic_id: str) -> dict[str, list[Any]]:
    return {
        "claims": _topic_filter(list_valid_records(ws.registry_dir("claims"), ClaimRecord), topic_id),
        "claim_statuses": _topic_filter(list_valid_records(ws.registry_dir("claim_statuses"), ClaimStatusRecord), topic_id),
        "proof_obligations": _topic_filter(list_valid_records(ws.registry_dir("proof_obligations"), ProofObligationRecord), topic_id),
        "authorities": list_authorities_for_topic(ws, topic_id),
        "physics_objects": _topic_filter(list_valid_records(ws.registry_dir("physics_objects"), PhysicsObjectRecord), topic_id),
        "object_relations": _topic_filter(list_valid_records(ws.registry_dir("object_relations"), ObjectRelationRecord), topic_id),
        "sensemaking_reports": _topic_filter(
            list_valid_records(ws.registry_dir("sensemaking_reports"), SensemakingReportRecord),
            topic_id,
        ),
        "source_assets": _topic_filter(list_valid_records(ws.registry_dir("source_assets"), SourceAssetRecord), topic_id),
        "artifacts": _topic_filter(list_valid_records(ws.registry_dir("artifacts"), ArtifactRecord), topic_id),
        "tool_runs": _topic_filter(list_valid_records(ws.registry_dir("tool_runs"), ToolRunRecord), topic_id),
        "evidence": _topic_filter(list_valid_records(ws.registry_dir("evidence"), EvidenceRecord), topic_id),
        "validation_results": _topic_filter(list_valid_records(ws.registry_dir("validation_results"), ValidationResultRecord), topic_id),
    }


def _topic_filter(records: list[Any], topic_id: str) -> list[Any]:
    return [record for record in records if getattr(record, "topic_id", "") == topic_id]


def _normalize_style(style: str) -> str:
    clean = (style or "jhep").strip().lower().replace("_", "-")
    return clean if clean in {"jhep", "research-note", "method-note"} else "jhep"


def _templates_for_topic(topic_id: str, records: dict[str, list[Any]], *, style: str) -> list[dict[str, Any]]:
    if style == "method-note":
        return _method_note_templates()
    if _looks_like_hidden_symmetry_topic(topic_id, records):
        return _hidden_symmetry_templates()
    return _generic_jhep_templates()


def _looks_like_hidden_symmetry_topic(topic_id: str, records: dict[str, list[Any]]) -> bool:
    text = _topic_text(topic_id, records)
    if "quantum-chaos-long-range-spin-chains" in topic_id:
        return True
    strong_tokens = ("hidden symmetry", "hidden-symmetry", "yangian", "haldane-shastry", "commutant", "schur")
    if any(token in text for token in strong_tokens):
        return True
    return "alpha" in text and ("spin chain" in text or "spin-chain" in text or "motif" in text)


def _hidden_symmetry_templates() -> list[dict[str, Any]]:
    return [
        _tpl("problem_scope", "Problem, Scope, And Claim Boundary", ["claims", "source_assets"], ["scope", "claim", "boundary"]),
        _tpl("model_conventions", "Model, Sectors, And Statistics Conventions", ["physics_objects", "authorities"], ["sector", "statistics", "generator", "model"]),
        _tpl("algebraic_method", "Algebraic Method And Closure Route", ["object_relations", "sensemaking_reports"], ["commutant", "closure", "schur", "operator"]),
        _tpl("generic_alpha", "Generic Alpha Structure", ["claims", "object_relations"], ["generic", "alpha"]),
        _tpl("alpha_2", "Alpha=2 Sector", ["authorities", "object_relations"], ["alpha=2", "alpha2", "hs", "sector"]),
        _tpl("alpha_infinity", "Alpha=Infinity Limit", ["claims", "source_assets"], ["infinity", "infinite", "free", "limit"], strict_keywords=True),
        _tpl("level_statistics", "Level Statistics And Finite Certificates", ["artifacts", "tool_runs"], ["level", "statistics", "finite", "certificate"]),
        _tpl("limitations", "Limitations, Failure Modes, And Open Proof Gaps", ["proof_obligations", "claim_statuses"], ["proof", "gap", "failure", "open"]),
        _tpl("appendices", "Appendices And Reproducibility Index", ["source_assets", "artifacts"], ["appendix", "reproduc", "artifact", "source"]),
    ]


def _generic_jhep_templates() -> list[dict[str, Any]]:
    return [
        _tpl("problem_scope", "Problem, Scope, And Claims", ["claims", "source_assets"], ["scope", "claim", "question"]),
        _tpl("model_conventions", "Model And Conventions", ["physics_objects", "authorities"], ["model", "definition", "convention"]),
        _tpl("method", "Method And Derivation Path", ["object_relations", "sensemaking_reports"], ["method", "derivation", "route"]),
        _tpl("results", "Recorded Results", ["artifacts", "evidence"], ["result", "observable", "bound"]),
        _tpl("validation", "Validation And Failure Modes", ["validation_results", "proof_obligations"], ["validation", "failure", "gap"]),
        _tpl("reuse", "Reusable Workflow Or Physics Fragment", ["sensemaking_reports", "source_assets"], ["workflow", "reuse", "fragment"]),
        _tpl("limitations", "Limitations And Non-Claims", ["claim_statuses", "proof_obligations"], ["limitation", "non-claim", "open"]),
        _tpl("appendices", "Appendices And Reproducibility Index", ["source_assets", "artifacts"], ["appendix", "reproduc", "artifact"]),
    ]


def _method_note_templates() -> list[dict[str, Any]]:
    return [
        _tpl("scope", "Scope And Reuse Boundary", ["claims", "source_assets"], ["scope", "reuse", "boundary"]),
        _tpl("inputs", "Inputs, Sources, And Code State", ["source_assets", "artifacts"], ["input", "source", "code"]),
        _tpl("procedure", "Procedure", ["sensemaking_reports", "tool_runs"], ["procedure", "method", "run"]),
        _tpl("checks", "Checks And Stop Rules", ["validation_results", "proof_obligations"], ["check", "stop", "failure"]),
        _tpl("outputs", "Outputs And Interpretation", ["artifacts", "evidence"], ["output", "result", "interpretation"]),
    ]


def _tpl(
    section_id: str,
    title: str,
    required_record_types: list[str],
    keywords: list[str],
    *,
    strict_keywords: bool = False,
) -> dict[str, Any]:
    return {
        "section_id": section_id,
        "title": title,
        "required_record_types": required_record_types,
        "keywords": keywords,
        "strict_keywords": strict_keywords,
    }


def _section_payload(
    template: dict[str, Any],
    *,
    topic_id: str,
    active_claim_id: str,
    records: dict[str, list[Any]],
) -> dict[str, Any]:
    record_refs: dict[str, list[str]] = {}
    source_refs: list[str] = []
    evidence_refs: list[str] = []
    missing: list[str] = []
    for record_type in template["required_record_types"]:
        matched = _matching_records(
            record_type,
            records.get(record_type, []),
            template["keywords"],
            active_claim_id,
            strict_keywords=bool(template.get("strict_keywords")),
        )
        refs = [_record_ref(record_type, record) for record in matched]
        if refs:
            record_refs[record_type] = refs
            for record in matched:
                source_refs.extend(_record_source_refs(record))
                evidence_refs.extend(_record_evidence_refs(record))
        else:
            missing.append(record_type)
            record_refs[record_type] = []
    claim_ids = _claim_ids(record_refs, records)
    return {
        "section_id": template["section_id"],
        "title": template["title"],
        "purpose": _purpose(template["section_id"]),
        "readiness_state": "draftable" if not missing else "needs_records",
        "record_refs": record_refs,
        "source_refs": _dedupe(source_refs),
        "evidence_refs": _dedupe(evidence_refs),
        "claim_ids": claim_ids or ([active_claim_id] if active_claim_id else []),
        "missing_requirements": missing,
        "recommended_record_actions": _section_actions(topic_id, template, missing),
        "trust_boundary": "Section outline only; draft from typed records and validate claims separately.",
        "orientation_only": True,
    }


def _matching_records(
    record_type: str,
    records: list[Any],
    keywords: list[str],
    active_claim_id: str,
    *,
    strict_keywords: bool = False,
) -> list[Any]:
    if not records:
        return []
    active = [record for record in records if getattr(record, "claim_id", "") == active_claim_id and active_claim_id]
    pool = active or records
    keyed = [record for record in pool if _has_keyword(record, keywords)]
    if keyed:
        return keyed[:6]
    if strict_keywords:
        return []
    if record_type in {"claims", "claim_statuses", "proof_obligations", "authorities", "source_assets", "artifacts"}:
        return pool[:6]
    return []


def _has_keyword(record: Any, keywords: list[str]) -> bool:
    text = _record_text(record).lower()
    return any(keyword.lower() in text for keyword in keywords)


def _record_text(record: Any) -> str:
    data = asdict(record) if hasattr(record, "__dataclass_fields__") else {}
    values: list[str] = []
    for value in data.values():
        if isinstance(value, (str, int, float, bool)):
            values.append(str(value))
        elif isinstance(value, list):
            values.extend(str(item) for item in value)
        elif isinstance(value, dict):
            values.extend(str(item) for item in value.values())
    return " ".join(values)


def _record_ref(record_type: str, record: Any) -> str:
    ids = {
        "claims": "claim_id",
        "claim_statuses": "status_id",
        "proof_obligations": "obligation_id",
        "authorities": "authority_id",
        "physics_objects": "object_id",
        "object_relations": "relation_id",
        "sensemaking_reports": "report_id",
        "source_assets": "asset_id",
        "artifacts": "artifact_id",
        "tool_runs": "run_id",
        "evidence": "evidence_id",
        "validation_results": "result_id",
    }
    prefixes = {
        "claims": "claim",
        "claim_statuses": "claim_status",
        "proof_obligations": "proof_obligation",
        "authorities": "authority",
        "physics_objects": "physics_object",
        "object_relations": "object_relation",
        "sensemaking_reports": "sensemaking_report",
        "source_assets": "source_asset",
        "artifacts": "artifact",
        "tool_runs": "tool_run",
        "evidence": "evidence",
        "validation_results": "validation_result",
    }
    record_id = str(getattr(record, ids[record_type], ""))
    return f"{prefixes[record_type]}:{record_id}" if record_id else f"{prefixes[record_type]}:unknown"


def _record_source_refs(record: Any) -> list[str]:
    refs = list(getattr(record, "source_refs", []) or [])
    if getattr(record, "kind", "") == "source_asset":
        refs.append(f"source_asset:{record.asset_id}")
    return refs


def _record_evidence_refs(record: Any) -> list[str]:
    refs = list(getattr(record, "evidence_refs", []) or [])
    if getattr(record, "kind", "") == "evidence":
        refs.append(f"evidence:{record.evidence_id}")
    return refs


def _claim_ids(record_refs: dict[str, list[str]], records: dict[str, list[Any]]) -> list[str]:
    ids: list[str] = []
    for record_type in record_refs:
        for record in records.get(record_type, []):
            claim_id = getattr(record, "claim_id", "")
            if claim_id:
                ids.append(claim_id)
    return _dedupe(ids)


def _section_actions(topic_id: str, template: dict[str, Any], missing: list[str]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    for record_type in missing:
        actions.append(
            {
                "action": "complete_first_layer_records",
                "topic_id": topic_id,
                "record_type": record_type,
                "reason": f"{template['section_id']} lacks {record_type} support.",
            }
        )
    return actions


def _purpose(section_id: str) -> str:
    purposes = {
        "problem_scope": "State the research question without widening claim scope.",
        "model_conventions": "Collect definitions, sectors, conventions, and adopted authorities.",
        "algebraic_method": "Expose the derivation route and semantic relation chain.",
        "generic_alpha": "Separate generic-alpha structure from special-point evidence.",
        "alpha_2": "Record the special alpha=2/HS sector boundary.",
        "alpha_infinity": "Record the limiting case without extrapolating beyond sources.",
        "level_statistics": "Attach finite diagnostic or numerical records to claims.",
        "limitations": "Preserve open proof gaps, failure modes, and non-claims.",
        "appendices": "Index artifacts, sources, and reproducibility material by reference.",
    }
    return purposes.get(section_id, "Organize recorded material without changing claim trust.")


def _source_records(
    session_id: str,
    objective_graph: dict[str, Any],
    distillation: dict[str, Any],
    records: dict[str, list[Any]],
) -> dict[str, Any]:
    return {
        "sessions": [session_id],
        "derived_surfaces": ["objective_graph", "research_distillation_candidates"],
        "objective_graph_source_records": objective_graph.get("source_records") or {},
        "distillation_candidate_ids": [
            str(candidate.get("candidate_id") or "")
            for candidate in distillation.get("candidates", [])
            if isinstance(candidate, dict)
        ],
        "typed_record_refs": {
            record_type: [_record_ref(record_type, record) for record in items]
            for record_type, items in records.items()
            if items
        },
    }


def _next_valid_actions(blocked_sections: list[dict[str, Any]], distillation: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for section in blocked_sections[:8]:
        actions.extend(section.get("recommended_record_actions") or [])
    for action in distillation.get("next_valid_actions") or []:
        actions.append({"action": "review_distillation_candidate", "reason": str(action)})
    if not actions:
        actions.append({"action": "human_review_note_outline", "reason": "All section record gates are draftable."})
    return actions[:12]


def _required_record_policy() -> list[dict[str, Any]]:
    return [
        {
            "gate": "first_layer_records_before_outline",
            "required": ["claims", "source_assets", "artifacts or sensemaking_reports"],
            "reason": "The outline may only organize material already captured as typed records.",
        },
        {
            "gate": "authority_before_convention",
            "required": ["authority_record for sector/statistics/formula conventions"],
            "reason": "A convention used across sections needs an explicit authority boundary.",
        },
        {
            "gate": "validation_before_result_claim",
            "required": ["validation_result or proof_obligation/failure boundary"],
            "reason": "A section can be drafted with gaps, but cannot be treated as validated support.",
        },
    ]


def _record_counts(records: dict[str, list[Any]]) -> dict[str, int]:
    return {key: len(value) for key, value in records.items()}


def _topic_text(topic_id: str, records: dict[str, list[Any]]) -> str:
    parts = [topic_id]
    for items in records.values():
        parts.extend(_record_text(record) for record in items[:8])
    return " ".join(parts).lower()


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Note Outline: {payload['topic_id']}",
        "",
        f"Style: `{payload['style']}`",
        "",
    ]
    for section in payload["sections"]:
        mark = "draftable" if section["readiness_state"] == "draftable" else "needs records"
        lines.append(f"## {section['title']} ({mark})")
        if section["missing_requirements"]:
            lines.append("Missing: " + ", ".join(section["missing_requirements"]))
        else:
            lines.append("Record refs: " + ", ".join(_flatten_record_refs(section["record_refs"])[:8]))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _flatten_record_refs(record_refs: dict[str, list[str]]) -> list[str]:
    out: list[str] = []
    for refs in record_refs.values():
        out.extend(refs)
    return out
