# Compatibility shard 2 for lane_exemplars.
from __future__ import annotations

def record_qft_qg_source_reconstruction_exemplar(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str = "",
    run_id: str = "",
    status: str = "accepted",
) -> LaneExemplarRecord:
    """Record the built-in QFT/QG semi-formal source-reconstruction exemplar."""

    return record_lane_exemplar(
        ws,
        topic_id=topic_id,
        lane="semi_formal_theory",
        title="QFT/QG source-reconstruction workflow",
        summary=(
            "Turn QFT or quantum-gravity papers, notes, and PDF-derived chunks into source-anchored "
            "concepts, equations, assumptions, and review results before any claim-supporting evidence "
            "or long-term memory promotion is allowed."
        ),
        claim_id=claim_id,
        run_id=run_id,
        gates_demonstrated=[
            "source_asset_intake",
            "reference_location_anchoring",
            "physics_object_extraction",
            "cross_source_comparison",
            "source_reconstruction_review",
            "checkpointed_promotion_boundary",
        ],
        artifact_refs=[
            "surface:literature_source_extraction_candidates",
            "surface:literature_corpus_extraction_artifact",
            "surface:literature_source_set_readiness",
            "surface:source_reconstruction_audit",
            "surface:source_reconstruction_review_packet",
            "surface:source_reconstruction_review_result_record",
        ],
        domain_pack_refs=["formal_theory", "qft_literature", "quantum_gravity_literature"],
        context_profile_refs=[
            "paper_learning",
            "paired_paper_learning",
            "multi_paper_learning_route",
            "source_reconstruction",
            "derivation_check",
            "group_meeting_report",
            "closeout",
        ],
        skill_refs=[
            "qft-literature-skill",
            "quantum-gravity-literature-skill",
        ],
        surface_refs=[
            "source_asset_record",
            "reference_location_record",
            "physics_object_record",
            "object_relation_record",
            "proof_obligation_record",
            "curated_rag_search_result",
            "curated_rag_chunk",
            "literature_reading_route",
            "literature_source_extraction_candidates",
            "literature_corpus_extraction_artifact",
            "literature_source_set_readiness",
            "literature_comparison_draft",
            "source_reconstruction_audit",
            "source_reconstruction_manifest",
            "source_reconstruction_review_packet",
            "source_reconstruction_review_result_record",
            "failure_mode_audit",
            "claim_trust_audit",
            "human_checkpoint_record",
        ],
        validation_surface_refs=[
            "source_reconstruction_review_result_record",
            "validation_contract_record",
            "validation_result_record",
            "failure_mode_review_result_record",
            "human_checkpoint_record",
            "claim_trust_audit",
        ],
        workflow_steps=[
            {
                "step_id": "register_or_bind_sources",
                "entrypoint": "aitp-v5 literature record-candidate <args>",
                "purpose": "Register PDFs, notes, or corpus roots as source candidates before using their content.",
            },
            {
                "step_id": "record_exact_anchors",
                "entrypoint": "aitp-v5 reference location record <args>",
                "purpose": "Create page, section, equation, or theorem anchors for every source-dependent claim component.",
            },
            {
                "step_id": "extract_objects_and_relations",
                "entrypoint": "aitp-v5 literature source-extraction <args>",
                "purpose": "Draft definitions, concepts, equations, assumptions, and dependency candidates as orientation only.",
            },
            {
                "step_id": "audit_source_set_readiness",
                "entrypoint": "aitp-v5 literature source-set-readiness <args>",
                "purpose": "Check whether the source set is broad, anchored, and scoped enough for synthesis.",
            },
            {
                "step_id": "compare_and_reconstruct",
                "entrypoint": "aitp-v5 literature comparison-draft <args>",
                "purpose": "Separate source results, conventions, framework assumptions, interpretations, and open directions.",
            },
            {
                "step_id": "review_source_reconstruction",
                "entrypoint": "aitp-v5 source reconstruction-review --claim <claim-id>",
                "purpose": "Build the review packet and record a review result before source-derived evidence is trusted.",
            },
            {
                "step_id": "audit_before_promotion",
                "entrypoint": "aitp-v5 trust audit --claim <claim-id>",
                "purpose": "Require validation, failure-mode coverage, and human checkpoint where broad QG claims are promoted.",
            },
        ],
        failure_modes=[
            {
                "failure_id": "notation_or_normalization_collision",
                "signals": ["field normalization differs", "metric signature differs", "operator symbol reused"],
                "required_basis": ["reference_location_record", "physics_object_record", "notation_map"],
            },
            {
                "failure_id": "renormalization_scheme_mismatch",
                "signals": ["scheme not named", "scale dependence hidden", "regularization convention omitted"],
                "required_basis": ["source equations", "proof_obligation_record", "validation_result_record"],
            },
            {
                "failure_id": "speculation_promoted_as_source_result",
                "signals": ["proposal language treated as established", "interpretation treated as theorem"],
                "required_basis": ["reference_location_record", "claim scope", "human_checkpoint_record"],
            },
            {
                "failure_id": "framework_mismatch",
                "signals": ["AdS argument applied to de Sitter", "large-N assumption hidden", "semiclassical limit omitted"],
                "required_basis": ["object_relation_record", "assumption table", "literature_comparison_draft"],
            },
            {
                "failure_id": "cross_paper_dependency_gap",
                "signals": ["definition lineage unclear", "paper B assumes paper A without a source anchor"],
                "required_basis": ["dependency map", "source_reconstruction_review_result_record"],
            },
            {
                "failure_id": "summary_only_understanding",
                "signals": ["no page or equation anchors", "concept map has no source refs"],
                "required_basis": ["source_asset_record", "reference_location_record", "record_ref_lookup"],
            },
        ],
        forbidden_uses=[
            "Treating retrieved chunks, PDF summaries, or literature notes as evidence without exact anchors.",
            "Promoting an interpretive quantum-gravity synthesis as a source result.",
            "Calling a derivation proved while proof obligations, assumptions, or convention mismatches remain open.",
            "Updating claim trust from source-reconstruction packets without review, validation, and required checkpoint links.",
        ],
        can_say=[
            "Which QFT/QG source anchors, concepts, relations, and proof obligations still need review.",
            "Whether a source set is ready for bounded synthesis or only orientation.",
            "Which parts are source results, interpretations, open directions, or unresolved framework assumptions.",
        ],
        cannot_say=[
            "That the AI understands the physics in the proof-level sense.",
            "That a literature summary or RAG chunk is claim evidence.",
            "That a broad quantum-gravity interpretation is promotable without a checkpointed review path.",
        ],
        required_next_records=[
            "source_asset_record",
            "reference_location_record",
            "physics_object_record",
            "object_relation_record",
            "proof_obligation_record",
            "source_reconstruction_review_result_record",
            "validation_result_record",
            "evidence_record",
            "human_checkpoint_record",
        ],
        promotion_blockers=[
            "missing exact reference_location_ids for key source claims",
            "source_reconstruction_review_status not passed",
            "uncovered convention, framework, or speculation-boundary failure mode",
            "missing human checkpoint for broad QG interpretation or L2 promotion",
            "summary-only or RAG-only support path",
        ],
        trust_boundary=(
            "Accepted semi-formal workflow exemplar only; it helps reconstruct QFT/QG source stacks but "
            "cannot prove a derivation, validate an interpretation, update claim trust, or promote memory "
            "without typed anchors, review results, validation, and required checkpoint decisions."
        ),
        source_refs=[
            "domain_pack:formal_theory",
            "domain_pack:qft_literature",
            "domain_pack:quantum_gravity_literature",
            "connector:qft_literature",
            "connector:quantum_gravity_literature",
            "docs:AITP_RESEARCH_BRAIN_ROADMAP.md#workstream-d",
            "surface:source_reconstruction_review_packet",
        ],
        status=status,
    )

def record_toy_numeric_finite_size_exemplar(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str = "",
    run_id: str = "",
    status: str = "accepted",
) -> LaneExemplarRecord:
    """Record the built-in toy-numeric finite-size and negative-control exemplar."""

    return record_lane_exemplar(
        ws,
        topic_id=topic_id,
        lane="toy_numeric",
        title="Toy numeric finite-size and negative-control workflow",
        summary=(
            "Use a fully specified toy model, finite-size or cutoff scan, explicit negative controls, "
            "versioned artifacts, and validation results to support only bounded numerical claims."
        ),
        claim_id=claim_id,
        run_id=run_id,
        gates_demonstrated=[
            "model_definition_scope",
            "finite_size_scan",
            "negative_control_check",
            "artifact_and_seed_provenance",
            "validation_result_gate",
            "bounded_claim_status",
        ],
        artifact_refs=[
            "surface:bounded_numerical_evidence_bundle",
            "surface:artifact_record",
            "surface:tool_run_record",
            "surface:validation_result_record",
            "surface:claim_status_record",
        ],
        domain_pack_refs=["toy_numerics"],
        context_profile_refs=[
            "derivation_check",
            "group_meeting_report",
            "closeout",
        ],
        skill_refs=[],
        surface_refs=[
            "bounded_numerical_evidence_bundle",
            "artifact_record",
            "tool_recipe_record",
            "tool_run_record",
            "tool_executor_catalog",
            "validation_contract_record",
            "validation_result_record",
            "failure_mode_audit",
            "claim_trust_audit",
            "claim_status_record",
            "proof_obligation_record",
        ],
        validation_surface_refs=[
            "pre_tool_policy_decision",
            "validation_contract_record",
            "validation_result_record",
            "failure_mode_audit",
            "claim_trust_audit",
        ],
        workflow_steps=[
            {
                "step_id": "define_model_and_scope",
                "entrypoint": "aitp-v5 research-state create-proof-obligation <args>",
                "purpose": "Fix Hamiltonian, parameters, symmetry sector, boundary conditions, and bounded claim scope.",
            },
            {
                "step_id": "record_recipe_and_artifacts",
                "entrypoint": "aitp-v5 tool recipe register <args>",
                "purpose": "Version the toy-model recipe, inputs, seeds, and output artifact contract before comparison.",
            },
            {
                "step_id": "run_metric_or_scalar_check",
                "entrypoint": "aitp-v5 tool execute metric_table_check <args>",
                "purpose": "Check finite-size tables or single observables with explicit expected values and tolerances.",
            },
            {
                "step_id": "record_bounded_evidence_bundle",
                "entrypoint": "aitp-v5 research-state bounded-evidence <args>",
                "purpose": "Compose artifact, tool-run, evidence, and claim-status records for the bounded result.",
            },
            {
                "step_id": "record_validation_result",
                "entrypoint": "aitp-v5 validation result record <args>",
                "purpose": "Persist passed, partial, or failed validation before the result can support a claim.",
            },
            {
                "step_id": "audit_before_promotion",
                "entrypoint": "aitp-v5 trust audit --claim <claim-id>",
                "purpose": "Confirm finite-size, sector, tolerance, and negative-control failure modes before promotion.",
            },
        ],
        failure_modes=[
            {
                "failure_id": "finite_size_overclaim",
                "signals": ["N<=k result stated as all-N theorem", "cutoff trend extrapolated without proof"],
                "required_basis": ["claim_status_record", "proof_obligation_record", "validation_result_record"],
            },
            {
                "failure_id": "sector_or_symmetry_mismatch",
                "signals": ["wrong particle number", "wrong momentum sector", "symmetry block omitted"],
                "required_basis": ["model definition", "input manifest", "metric_table_check"],
            },
            {
                "failure_id": "negative_control_missing",
                "signals": ["no trivial case", "no perturbed control", "no known-failure benchmark"],
                "required_basis": ["tool_run_record", "artifact_record", "validation_contract_record"],
            },
            {
                "failure_id": "tolerance_cherry_pick",
                "signals": ["tolerance chosen after seeing result", "single point replaces table trend"],
                "required_basis": ["tool_recipe_record", "validation_contract_record", "tool_executor_catalog"],
            },
            {
                "failure_id": "artifact_or_seed_gap",
                "signals": ["missing seed", "missing input hash", "plot without data table"],
                "required_basis": ["artifact_record", "tool_run_record", "bounded_numerical_evidence_bundle"],
            },
        ],
        forbidden_uses=[
            "Treating finite-size or cutoff evidence as a theorem without a scoped proof obligation.",
            "Promoting a plot-only result without the underlying data artifact and validation result.",
            "Using a passing scalar tolerance check as broad evidence when the failure mode requires a table scan.",
            "Updating claim trust from a toy exemplar without passed validation and explicit bounded scope.",
        ],
        can_say=[
            "Which bounded numerical result, finite-size scope, and artifacts were recorded.",
            "Which negative controls and tolerance checks remain missing.",
            "Whether the result supports a scoped claim or only motivates a proof obligation.",
        ],
        cannot_say=[
            "That a finite-size pattern proves the infinite-size theorem.",
            "That a plotted trend is evidence without artifact and validation records.",
            "That a toy model result transfers to the full physical system without a scoped bridge claim.",
        ],
        required_next_records=[
            "tool_recipe_record",
            "tool_run_record",
            "artifact_record",
            "bounded_numerical_evidence_bundle",
            "validation_contract_record",
            "validation_result_record",
            "claim_status_record",
            "proof_obligation_record",
        ],
        promotion_blockers=[
            "missing finite-size or cutoff scope",
            "missing negative-control check",
            "missing passed validation_result_ids for cited tool_run_ids",
            "plot-only artifact path",
            "theorem-like claim without proof_obligation_record",
        ],
        trust_boundary=(
            "Accepted toy-numeric workflow exemplar only; it supports bounded numerical workflow reuse but "
            "cannot prove a theorem, update claim trust, or promote memory without scoped evidence, artifacts, "
            "passed validation, and open proof-obligation handling."
        ),
        source_refs=[
            "domain_pack:toy_numerics",
            "executor:metric_table_check",
            "executor:scalar_tolerance_check",
            "surface:bounded_numerical_evidence_bundle",
            "docs:AITP_RESEARCH_BRAIN_ROADMAP.md#workstream-d",
        ],
        status=status,
    )

def load_lane_exemplars(ws: WorkspacePaths, topic_id: str, *, limit: int = 6) -> dict[str, Any]:
    """Load topic-local lane exemplars for briefs and status surfaces."""

    items = [_brief_item(item) for item in _read_topic_exemplars(ws, topic_id)]
    items = items[-limit:]
    return {
        "present": bool(items),
        "items": items,
        "required_lanes": list(REQUIRED_LANES),
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }

def build_lane_exemplar_manifest(ws: WorkspacePaths) -> dict[str, Any]:
    """Return a workspace-level vNext Phase 5 lane exemplar closure manifest."""

    items = []
    topics_dir = ws.root / "topics"
    if topics_dir.exists():
        for topic_dir in sorted(path for path in topics_dir.iterdir() if path.is_dir()):
            items.extend(_read_topic_exemplars(ws, topic_dir.name))
    lane_status_counts = {lane: {} for lane in REQUIRED_LANES}
    for item in items:
        lane = str(item.get("lane") or "")
        status = str(item.get("status") or "")
        if lane in lane_status_counts and status:
            lane_status_counts[lane][status] = lane_status_counts[lane].get(status, 0) + 1
    covered_lanes = [
        lane
        for lane in REQUIRED_LANES
        if any(item.get("lane") == lane and item.get("status") == "accepted" for item in items)
    ]
    missing_lanes = [lane for lane in REQUIRED_LANES if lane not in covered_lanes]
    return {
        "kind": "lane_exemplar_manifest",
        "required_lanes": list(REQUIRED_LANES),
        "covered_lanes": covered_lanes,
        "missing_lanes": missing_lanes,
        "lane_status_counts": lane_status_counts,
        "exemplar_count": len(items),
        "items": [_brief_item(item) for item in items],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }

def _read_topic_exemplars(ws: WorkspacePaths, topic_id: str) -> list[dict[str, Any]]:
    path = _runtime_dir(ws, topic_id) / "lane_exemplars.jsonl"
    if not path.exists():
        return []
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            items.append(item)
    return items

def _brief_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "exemplar_id": str(item.get("exemplar_id") or ""),
        "topic_id": str(item.get("topic_id") or ""),
        "lane": str(item.get("lane") or ""),
        "title": str(item.get("title") or ""),
        "summary": str(item.get("summary") or ""),
        "claim_id": str(item.get("claim_id") or ""),
        "run_id": str(item.get("run_id") or ""),
        "gates_demonstrated": list(item.get("gates_demonstrated") or []),
        "artifact_refs": list(item.get("artifact_refs") or []),
        "domain_pack_refs": _list_values(item, "domain_pack_refs"),
        "context_profile_refs": _list_values(item, "context_profile_refs"),
        "skill_refs": _list_values(item, "skill_refs"),
        "surface_refs": _list_values(item, "surface_refs"),
        "validation_surface_refs": _list_values(item, "validation_surface_refs"),
        "workflow_steps": _list_values(item, "workflow_steps"),
        "failure_modes": _list_values(item, "failure_modes"),
        "forbidden_uses": _list_values(item, "forbidden_uses"),
        "can_say": _list_values(item, "can_say"),
        "cannot_say": _list_values(item, "cannot_say"),
        "required_next_records": _list_values(item, "required_next_records"),
        "promotion_blockers": _list_values(item, "promotion_blockers"),
        "trust_boundary": str(item.get("trust_boundary") or ""),
        "status": str(item.get("status") or ""),
        "orientation_only": True,
    }
