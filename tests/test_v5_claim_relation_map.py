from __future__ import annotations

import json
from pathlib import Path


def _setup_h2o_si_runtime_failure_workspace(
    tmp_path: Path,
    *,
    next_action: str = "Reproduce Si thiele baseline with the same executable, then rerun ridge.",
):
    from brain.v5.evidence import record_evidence
    from brain.v5.research_state import update_claim_status
    from brain.v5.tools import record_tool_run
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "qsgw-ac-error-molecules", context_id="librpa", title="QSGW AC error molecules")
    claim = create_claim(
        ws,
        topic_id="qsgw-ac-error-molecules",
        statement="For H2O one-iteration LibRPA QSGW diagnostics, ridge-regularized Pade reduces analytic-continuation error amplification compared with Thiele Pade.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="Cross-system Si gap and analytic-continuation behavior are not yet tested.",
    )
    h2o_support = record_evidence(
        ws,
        topic_id="qsgw-ac-error-molecules",
        claim_id=claim.claim_id,
        evidence_type="bounded_numerical_replay",
        status="supports_scoped_claim",
        summary="H2O dump plus one-iteration C++ replay support that ridge reduces AC error amplification. Failure mode remains ridge bias, and the executable path is recorded only as provenance.",
        supports_outputs=["h2o_ac_error_amplification_reduction"],
        source_refs=["artifact:h2o-dump", "tool_run:h2o-one-iteration-replay", "local:/tmp/executable/path"],
    )
    gap_limit = record_evidence(
        ws,
        topic_id="qsgw-ac-error-molecules",
        claim_id=claim.claim_id,
        evidence_type="gap_audit",
        status="mixed",
        summary="H2O gap audit limits the claim: strong ridge parameters may change the gap.",
        supports_outputs=["gap_bias_boundary"],
        source_refs=["artifact:h2o-gap-audit"],
    )
    si_run = record_tool_run(
        ws,
        recipe_id="si-g0w0-pade-baseline",
        tool_family="remote_numerics",
        tool_name="slurm-librpa",
        topic_id="qsgw-ac-error-molecules",
        claim_id=claim.claim_id,
        inputs={"system": "Si", "baseline": "thiele"},
        outputs={
            "job_id": "2023865",
            "failure_scope": "application/runtime",
            "failure_stage": "pre_ac",
            "failure_reason": "ScaLAPACK Wc executable path failed before analytic continuation",
        },
        evidence_status="failed",
        source_refs=["slurm:2023865"],
    )
    si_failure = record_evidence(
        ws,
        topic_id="qsgw-ac-error-molecules",
        claim_id=claim.claim_id,
        evidence_type="runtime_failure",
        status="negative",
        summary="Si job 2023865 failed before analytic continuation because of ScaLAPACK Wc / executable path; this falsifies application, not the ridge algorithm.",
        supports_outputs=["si_runtime_attempt"],
        tool_run_ids=[si_run.run_id],
        source_refs=["slurm:2023865"],
    )
    update_claim_status(
        ws,
        topic_id="qsgw-ac-error-molecules",
        claim_id=claim.claim_id,
        maturity_level="finite-size evidence",
        claim_status="hypothesis_with_runtime_blocker",
        scope="H2O one-iteration replay supports AC amplification reduction; Si cross-system test has not entered AC.",
        risk="Si runtime failure can be mistaken for algorithm evidence",
        next_action=next_action,
        open_gaps=[
            "Si task target is cross-system gap and AC comparison, but current Si result is a runtime failure before AC.",
            "Strong ridge parameters may alter the gap and need separate audit.",
        ],
        evidence_refs=[h2o_support.evidence_id, gap_limit.evidence_id, si_failure.evidence_id],
    )
    bind_session(
        ws,
        "qsgw-si-recovery",
        topic_id="qsgw-ac-error-molecules",
        context_id="librpa",
        active_claim=claim.claim_id,
    )
    return ws, claim, h2o_support, gap_limit, si_failure, si_run


def test_claim_relation_map_separates_runtime_failure_from_algorithm_failure(tmp_path):
    from brain.v5.claim_relation_map import build_claim_relation_map
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim, h2o_support, gap_limit, si_failure, si_run = _setup_h2o_si_runtime_failure_workspace(tmp_path)

    relation_map = build_claim_relation_map(ws, "qsgw-si-recovery")

    assert require_valid_public_surface("claim_relation_map", relation_map) == relation_map
    assert relation_map["claim_id"] == claim.claim_id
    assert [entry["record_id"] for entry in relation_map["supported_by"]] == [h2o_support.evidence_id]
    assert gap_limit.evidence_id in {entry["record_id"] for entry in relation_map["limited_by"]}
    assert si_failure.evidence_id in {entry["record_id"] for entry in relation_map["not_tested_by"]}
    assert si_run.run_id in {entry["record_id"] for entry in relation_map["not_tested_by"]}
    assert relation_map["contradicted_by"] == []
    assert any("runtime/application failures" in item for item in relation_map["current_conclusion"]["cannot_say"])
    assert any("ScaLAPACK" in item for item in relation_map["current_blockers"])
    assert relation_map["next_valid_actions"] == [
        "Reproduce Si thiele baseline with the same executable, then rerun ridge."
    ]
    assert relation_map["trust_update_allowed"] is False
    assert relation_map["can_update_claim_trust"] is False


def test_claim_relation_map_recovers_active_claim_from_topic_state_for_fresh_session(tmp_path):
    from brain.v5.claim_relation_map import build_claim_relation_map
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import bind_session

    ws, claim, h2o_support, gap_limit, si_failure, _ = _setup_h2o_si_runtime_failure_workspace(tmp_path)
    bind_session(
        ws,
        "fresh-qsgw-session",
        topic_id="qsgw-ac-error-molecules",
        context_id="librpa",
    )
    topic_state = {
        "kind": "topic_state",
        "topic_id": "qsgw-ac-error-molecules",
        "session_id": "qsgw-si-recovery",
        "context_id": "librpa",
        "active_claim_id": claim.claim_id,
    }
    (ws.topic_dir("qsgw-ac-error-molecules") / "runtime" / "topic_state.json").write_text(
        json.dumps(topic_state),
        encoding="utf-8",
    )

    relation_map = build_claim_relation_map(ws, "fresh-qsgw-session")

    assert require_valid_public_surface("claim_relation_map", relation_map) == relation_map
    assert relation_map["requested_session_id"] == "fresh-qsgw-session"
    assert relation_map["session_id"] == "qsgw-si-recovery"
    assert relation_map["recovery_selection_source"] == "runtime_topic_state"
    assert relation_map["claim_id"] == claim.claim_id
    assert [entry["record_id"] for entry in relation_map["supported_by"]] == [h2o_support.evidence_id]
    assert gap_limit.evidence_id in {entry["record_id"] for entry in relation_map["limited_by"]}
    assert si_failure.evidence_id in {entry["record_id"] for entry in relation_map["not_tested_by"]}
    assert any("runtime/application failures" in item for item in relation_map["current_conclusion"]["cannot_say"])


def test_topic_token_recovers_brief_relation_map_and_graph_from_topic_state(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.claim_relation_map import build_claim_relation_map
    from brain.v5.process_graph import build_process_graph_slice
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim, h2o_support, _, si_failure, _ = _setup_h2o_si_runtime_failure_workspace(tmp_path)
    topic_state = {
        "kind": "topic_state",
        "topic_id": "qsgw-ac-error-molecules",
        "session_id": "qsgw-si-recovery",
        "context_id": "librpa",
        "active_claim_id": claim.claim_id,
    }
    (ws.topic_dir("qsgw-ac-error-molecules") / "runtime" / "topic_state.json").write_text(
        json.dumps(topic_state),
        encoding="utf-8",
    )

    brief = build_execution_brief(ws, "topic:qsgw-ac-error-molecules")
    relation_map = build_claim_relation_map(ws, "topic:qsgw-ac-error-molecules")
    graph = build_process_graph_slice(ws, "topic:qsgw-ac-error-molecules", limit=40)

    assert require_valid_public_surface("execution_brief", brief) == brief
    assert require_valid_public_surface("claim_relation_map", relation_map) == relation_map
    assert require_valid_public_surface("process_graph_slice", graph) == graph
    for payload in (brief, relation_map, graph):
        assert payload["requested_session_id"] == "topic:qsgw-ac-error-molecules"
        assert payload["recovery_selection_source"] == "topic_token_runtime_topic_state"
    assert brief["session"]["session_id"] == "qsgw-si-recovery"
    assert brief["recovered_focus"] == {
        "requested_session_id": "topic:qsgw-ac-error-molecules",
        "recovery_selection_source": "topic_token_runtime_topic_state",
        "session_id": "qsgw-si-recovery",
        "topic_id": "qsgw-ac-error-molecules",
        "context_id": "librpa",
        "active_claim": claim.claim_id,
        "active_route": None,
        "active_cycle": None,
        "claim_statement": claim.statement,
        "confidence_state": "hypothesis",
        "evidence_profile": "code_method",
    }
    assert brief["current_focus"]["active_claim"] == claim.claim_id
    assert relation_map["claim_id"] == claim.claim_id
    assert relation_map["session_id"] == "qsgw-si-recovery"
    assert h2o_support.evidence_id in {entry["record_id"] for entry in relation_map["supported_by"]}
    assert si_failure.evidence_id in {entry["record_id"] for entry in relation_map["not_tested_by"]}
    assert graph["session_id"] == "qsgw-si-recovery"
    assert graph["topic_id"] == "qsgw-ac-error-molecules"
    assert graph["claim_id"] == claim.claim_id


def test_bare_topic_recovers_brief_relation_map_and_graph_from_topic_state(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.claim_relation_map import build_claim_relation_map
    from brain.v5.process_graph import build_process_graph_slice
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim, h2o_support, _, si_failure, _ = _setup_h2o_si_runtime_failure_workspace(tmp_path)
    topic_state = {
        "kind": "topic_state",
        "topic_id": "qsgw-ac-error-molecules",
        "session_id": "qsgw-si-recovery",
        "context_id": "librpa",
        "active_claim_id": claim.claim_id,
    }
    (ws.topic_dir("qsgw-ac-error-molecules") / "runtime" / "topic_state.json").write_text(
        json.dumps(topic_state),
        encoding="utf-8",
    )

    brief = build_execution_brief(ws, "qsgw-ac-error-molecules")
    relation_map = build_claim_relation_map(ws, "qsgw-ac-error-molecules")
    graph = build_process_graph_slice(ws, "qsgw-ac-error-molecules", limit=40)

    assert require_valid_public_surface("execution_brief", brief) == brief
    assert require_valid_public_surface("claim_relation_map", relation_map) == relation_map
    assert require_valid_public_surface("process_graph_slice", graph) == graph
    for payload in (brief, relation_map, graph):
        assert payload["requested_session_id"] == "qsgw-ac-error-molecules"
        assert payload["recovery_selection_source"] == "bare_topic_runtime_topic_state"
    assert brief["recovered_focus"]["session_id"] == "qsgw-si-recovery"
    assert brief["recovered_focus"]["active_claim"] == claim.claim_id
    assert relation_map["claim_id"] == claim.claim_id
    assert h2o_support.evidence_id in {entry["record_id"] for entry in relation_map["supported_by"]}
    assert si_failure.evidence_id in {entry["record_id"] for entry in relation_map["not_tested_by"]}
    assert graph["session_id"] == "qsgw-si-recovery"
    assert graph["claim_id"] == claim.claim_id


def test_claim_relation_map_prioritizes_runtime_blocker_next_action_over_generic_status(tmp_path):
    from brain.v5.claim_relation_map import build_claim_relation_map

    ws, *_ = _setup_h2o_si_runtime_failure_workspace(
        tmp_path,
        next_action="collect_required_evidence_or_provenance",
    )

    relation_map = build_claim_relation_map(ws, "qsgw-si-recovery")

    assert relation_map["next_valid_actions"][0] == (
        "resolve the runtime/application blocker, then rerun the same-executable "
        "Thiele baseline before interpreting ridge evidence"
    )
    assert "collect_required_evidence_or_provenance" in relation_map["next_valid_actions"]


def test_claim_relation_map_does_not_treat_scalapack_parameter_text_as_runtime_failure(tmp_path):
    from brain.v5.claim_relation_map import build_claim_relation_map
    from brain.v5.evidence import record_evidence
    from brain.v5.tools import record_tool_run

    ws, claim, *_ = _setup_h2o_si_runtime_failure_workspace(tmp_path)
    run = record_tool_run(
        ws,
        recipe_id="h2o-gap-audit",
        tool_family="hpc_slurm_plus_local_analysis",
        tool_name="compare_ac_regularization",
        topic_id="qsgw-ac-error-molecules",
        claim_id=claim.claim_id,
        inputs={"system": "H2O", "use_scalapack_gw_wc": "f"},
        outputs={"gap_shift_ev": -0.52, "status": "completed"},
        evidence_status="new_evidence",
        source_refs=["source-asset-qsgw-ac-error-molecules-h2o-gap-audit"],
    )
    reconstruction = record_evidence(
        ws,
        topic_id="qsgw-ac-error-molecules",
        claim_id=claim.claim_id,
        evidence_type="source_reconstruction",
        status="supports_reconstruction_boundary",
        summary=(
            "Recovery boundary says the Si runtime failure does not test algorithm trust; "
            "this is reconstruction context, not a failed run."
        ),
        supports_outputs=["reconstruction_path"],
        source_refs=["legacy_l0_l4:qsgw-ac-error-molecules:L1/question_contract.md"],
    )

    relation_map = build_claim_relation_map(ws, "qsgw-si-recovery")

    assert run.run_id in {entry["record_id"] for entry in relation_map["limited_by"]}
    assert run.run_id not in {entry["record_id"] for entry in relation_map["not_tested_by"]}
    assert reconstruction.evidence_id in {entry["record_id"] for entry in relation_map["limited_by"]}
    assert reconstruction.evidence_id not in {entry["record_id"] for entry in relation_map["not_tested_by"]}


def test_claim_relation_map_surfaces_key_physics_object_relations(tmp_path):
    from brain.v5.claim_relation_map import (
        build_claim_relation_map,
        compact_claim_relation_map,
        render_claim_relation_map_markdown,
    )
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(
        ws,
        "generalized-symmetries-first-principles",
        context_id="formal-theory",
        title="Generalized symmetries from first-principles methods",
    )
    claim = create_claim(
        ws,
        topic_id="generalized-symmetries-first-principles",
        statement=(
            "Can first-principles GW+DMFT Green functions expose generalized symmetry "
            "or higher-form symmetry structure in correlated materials?"
        ),
        evidence_profile="formal_theory",
        confidence_state="legacy_seed",
        active_uncertainty="No validated ab initio extraction workflow has been recorded.",
    )
    gw_dmft = record_physics_object(
        ws,
        topic_id="generalized-symmetries-first-principles",
        object_type="computational_input",
        name="GW+DMFT Green functions",
        definition="Interacting single-particle Green functions and self-energies from first-principles workflows.",
    )
    gf_zero = record_physics_object(
        ws,
        topic_id="generalized-symmetries-first-principles",
        object_type="diagnostic",
        name="Green-function zero topology diagnostics",
        definition="Topology diagnostics based on zeros, poles, or singular structures of interacting Green functions.",
    )
    generalized_symmetry = record_physics_object(
        ws,
        topic_id="generalized-symmetries-first-principles",
        object_type="interpretation_layer",
        name="Generalized symmetry interpretation",
        definition="Higher-form or generalized symmetry language used to interpret interacting topological diagnostics.",
    )
    record_object_relation(
        ws,
        topic_id="generalized-symmetries-first-principles",
        claim_id=claim.claim_id,
        relation_type="computes_diagnostic_inputs_for",
        subject_id=gw_dmft.object_id,
        object_id=gf_zero.object_id,
        statement="GW+DMFT Green functions supply candidate inputs for Green-function zero topology diagnostics.",
        status="hypothesis",
    )
    record_object_relation(
        ws,
        topic_id="generalized-symmetries-first-principles",
        claim_id=claim.claim_id,
        relation_type="interprets",
        subject_id=generalized_symmetry.object_id,
        object_id=gf_zero.object_id,
        statement=(
            "Generalized symmetry interpretation is only a proposed layer over Green-function zero topology "
            "diagnostics until an explicit ab initio extraction workflow is validated."
        ),
        failure_modes=["no validated GW+DMFT-to-generalized-symmetry extraction workflow"],
        status="hypothesis",
    )
    bind_session(
        ws,
        "generalized-recovery",
        topic_id="generalized-symmetries-first-principles",
        context_id="formal-theory",
        active_claim=claim.claim_id,
    )

    relation_map = build_claim_relation_map(ws, "generalized-recovery")
    compact = compact_claim_relation_map(relation_map)
    markdown = render_claim_relation_map_markdown(relation_map)

    assert require_valid_public_surface("claim_relation_map", relation_map) == relation_map
    assert relation_map["key_object_relations"]
    assert any("Green-function zero topology diagnostics" in item for item in relation_map["key_object_relations"])
    assert any("GW+DMFT Green functions" in item for item in compact["key_object_relations"])
    assert "Green-function zero topology diagnostics" in markdown
    assert "no validated GW+DMFT-to-generalized-symmetry extraction workflow" in relation_map["current_blockers"]


def test_claim_relation_map_surfaces_legacy_semantic_review_active_claim_divergence(tmp_path):
    from brain.v5.claim_relation_map import (
        build_claim_relation_map,
        compact_claim_relation_map,
        render_claim_relation_map_markdown,
    )
    from brain.v5.models import LegacySemanticReviewResultRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(
        ws,
        "generalized-symmetries-first-principles",
        context_id="formal-theory",
        title="Generalized symmetries from first-principles methods",
    )
    current_claim = create_claim(
        ws,
        topic_id="generalized-symmetries-first-principles",
        statement="Current recovered claim from topic_state.",
        evidence_profile="formal_theory",
        confidence_state="legacy_seed",
        active_uncertainty="Legacy migration review has not settled the active claim boundary.",
    )
    migration_review_claim = create_claim(
        ws,
        topic_id="generalized-symmetries-first-principles",
        statement="Older claim selected by a legacy migration review.",
        evidence_profile="formal_theory",
        confidence_state="legacy_seed",
        active_uncertainty="This claim should not be used as the recovered active claim.",
    )
    review = LegacySemanticReviewResultRecord(
        review_id="legacy-semantic-review-generalized-divergent-claim",
        migration_run_id="legacy-v5-lossless-accounting",
        migration_dir=str(tmp_path / "migration"),
        topic="generalized-symmetries-first-principles",
        status="needs_revision",
        summary="Review found active claim divergence and incomplete source reconstruction.",
        active_claim_id=migration_review_claim.claim_id,
        reviewed_legacy_refs=["legacy_l0:source_registry.md"],
        reviewed_typed_refs=[f"claim:{current_claim.claim_id}", f"claim:{migration_review_claim.claim_id}"],
        remaining_actions=[
            "resolve_active_claim_divergence_before_session_recovery_trust",
            "complete_source_reconstruction",
        ],
        created_at="2026-06-14T00:00:00+00:00",
    )
    write_record(
        ws.registry_dir("legacy_semantic_reviews") / f"{review.review_id}.md",
        review,
        body="# Legacy Semantic Review\n",
    )
    bind_session(
        ws,
        "generalized-recovery",
        topic_id="generalized-symmetries-first-principles",
        context_id="formal-theory",
        active_claim=current_claim.claim_id,
    )

    relation_map = build_claim_relation_map(ws, "generalized-recovery")
    compact = compact_claim_relation_map(relation_map)
    markdown = render_claim_relation_map_markdown(relation_map)

    assert require_valid_public_surface("claim_relation_map", relation_map) == relation_map
    assert relation_map["claim_id"] == current_claim.claim_id
    assert relation_map["legacy_semantic_review"]["review_id"] == review.review_id
    assert relation_map["legacy_semantic_review"]["active_claim_divergence"] is True
    assert relation_map["source_records"]["legacy_semantic_reviews"] == [review.review_id]
    assert "legacy_semantic_review_records" in relation_map["derived_from"]
    assert relation_map["current_blockers"][0] == "active_claim_divergence_requires_semantic_review"
    assert "legacy_semantic_review_needs_revision" in relation_map["current_blockers"]
    assert any(entry["record_kind"] == "legacy_semantic_review" for entry in relation_map["limited_by"])
    assert any("divergent legacy semantic review or migration" in item for item in relation_map["current_conclusion"]["cannot_say"])
    assert relation_map["next_valid_actions"][0] == (
        "resolve active-claim divergence before using legacy review for session recovery trust"
    )
    assert compact["legacy_active_claim_divergence"] is True
    assert compact["legacy_semantic_review_status"] == "needs_revision"
    assert "Legacy Semantic Review" in markdown
    assert "Active claim divergence: `True`" in markdown


def test_claim_relation_map_surfaces_pending_migration_active_claim_divergence(tmp_path):
    from brain.v5.claim_relation_map import build_claim_relation_map, compact_claim_relation_map
    from brain.v5.models import LegacySemanticReviewResultRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    topic = "gw-dmft"
    create_topic(ws, topic, context_id="formal-theory", title="GW+DMFT")
    current_claim = create_claim(
        ws,
        topic_id=topic,
        statement="Runtime topic-state claim.",
        evidence_profile="formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="Migration review is pending.",
    )
    migration_claim = create_claim(
        ws,
        topic_id=topic,
        statement="Migration coverage selected a different legacy claim.",
        evidence_profile="formal_theory",
        confidence_state="legacy_seed",
        active_uncertainty="This claim still needs semantic review.",
    )
    run = ws.root / "migrations" / "legacy-v5-lossless-test"
    run.mkdir(parents=True)
    (run / "migration_summary.json").write_text(json.dumps({
        "run_id": "legacy-v5-lossless-test",
        "workspace": str(ws.base),
        "legacy_root": str(ws.base / "research" / "aitp-topics"),
        "v5_root": str(ws.root),
        "totals": {
            "topic_count": 1,
            "legacy_file_count": 1,
            "post_legacy_file_count": 1,
            "legacy_manifest_hash_stable": True,
            "legacy_manifest_change_count": 0,
            "archive_reference_count": 0,
        },
        "topics": [{
            "topic": topic,
            "status": "ok",
            "file_count": 1,
            "accounted_file_count": 1,
            "structured_file_count": 1,
            "archive_reference_count": 0,
            "missing_expected_paths": [],
            "can_write_v5_records": True,
            "active_claim_id": migration_claim.claim_id,
            "written_records": {"claims": 1},
            "preserved_source_refs": 0,
        }],
    }), encoding="utf-8")
    (run / "verification_report.json").write_text(json.dumps({
        "run_id": "legacy-v5-lossless-test",
        "file_accounting_ok": True,
        "manifest_check": {"pre_count": 1, "post_count": 1, "missing": 0, "extra": 0, "changed": 0},
        "archive_reference_check": {
            "archive_records_checked": 0,
            "archive_records_expected": 0,
            "registry_archive_reference_count": 0,
            "problem_count": 0,
        },
        "markdown_readability_check": {"markdown_files_checked": 1, "problem_count": 0},
    }), encoding="utf-8")
    bind_session(ws, "gw-dmft-recovery", topic_id=topic, context_id="formal-theory", active_claim=current_claim.claim_id)

    relation_map = build_claim_relation_map(ws, "gw-dmft-recovery")
    compact = compact_claim_relation_map(relation_map)

    assert require_valid_public_surface("claim_relation_map", relation_map) == relation_map
    assert relation_map["claim_id"] == current_claim.claim_id
    assert relation_map["legacy_semantic_review"]["status"] == "pending"
    assert relation_map["legacy_semantic_review"]["has_review_record"] is False
    assert relation_map["legacy_semantic_review"]["migration_active_claim_id"] == migration_claim.claim_id
    assert relation_map["legacy_semantic_review"]["review_active_claim_divergence"] is False
    assert relation_map["legacy_semantic_review"]["migration_active_claim_divergence"] is True
    assert relation_map["legacy_semantic_review"]["active_claim_divergence"] is True
    assert relation_map["source_records"]["legacy_migration_topics"] == [f"legacy-v5-lossless-test:{topic}"]
    assert relation_map["current_blockers"][:2] == [
        "active_claim_divergence_requires_semantic_review",
        "legacy_semantic_review_pending",
    ]
    assert any("record legacy semantic review result" in action for action in relation_map["next_valid_actions"])
    assert compact["legacy_semantic_review_status"] == "pending"
    assert compact["legacy_active_claim_divergence"] is True

    review = LegacySemanticReviewResultRecord(
        review_id="legacy-semantic-review-gw-dmft-runtime-claim-needs-revision",
        migration_run_id="legacy-v5-lossless-test",
        migration_dir=str(run),
        topic=topic,
        status="needs_revision",
        summary="Review used the runtime claim, but migration coverage still points at another claim.",
        active_claim_id=current_claim.claim_id,
        reviewed_typed_refs=[f"claim:{current_claim.claim_id}"],
        remaining_actions=["resolve_active_claim_divergence_before_session_recovery_trust"],
        created_at="2026-06-14T00:00:00+00:00",
    )
    write_record(
        ws.registry_dir("legacy_semantic_reviews") / f"{review.review_id}.md",
        review,
        body="# Legacy Semantic Review\n",
    )

    relation_map = build_claim_relation_map(ws, "gw-dmft-recovery")

    assert relation_map["legacy_semantic_review"]["status"] == "needs_revision"
    assert relation_map["legacy_semantic_review"]["has_review_record"] is True
    assert relation_map["legacy_semantic_review"]["review_active_claim_divergence"] is False
    assert relation_map["legacy_semantic_review"]["migration_active_claim_divergence"] is True
    assert relation_map["legacy_semantic_review"]["active_claim_divergence"] is True
    assert relation_map["current_blockers"][0] == "active_claim_divergence_requires_semantic_review"


def test_claim_relation_map_prefers_claim_matched_legacy_semantic_review(tmp_path):
    from brain.v5.claim_relation_map import build_claim_relation_map
    from brain.v5.models import LegacySemanticReviewResultRecord
    from brain.v5.store import write_record
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    topic = "quantum-chaos-long-range-spin-chains"
    create_topic(ws, topic, context_id="quantum-chaos", title="Quantum chaos long-range spin chains")
    current_claim = create_claim(
        ws,
        topic_id=topic,
        statement="Current A2 proof claim.",
        evidence_profile="semi_formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="All-n theorem still open.",
    )
    old_claim = create_claim(
        ws,
        topic_id=topic,
        statement="Older finite diagnostic claim.",
        evidence_profile="numerical_diagnostics",
        confidence_state="legacy_seed",
        active_uncertainty="Superseded as the active recovery focus.",
    )
    matched = LegacySemanticReviewResultRecord(
        review_id="legacy-semantic-review-current-claim-inconclusive",
        migration_run_id="legacy-v5-lossless-test",
        migration_dir=str(tmp_path / "migration"),
        topic=topic,
        status="inconclusive",
        summary="Current claim review exposes the remaining all-n theorem boundary.",
        active_claim_id=current_claim.claim_id,
        reviewed_typed_refs=[f"claim:{current_claim.claim_id}"],
        remaining_actions=["prove_all_n_theorem"],
        created_at="2026-06-14T00:00:00+00:00",
    )
    newer_old_claim_review = LegacySemanticReviewResultRecord(
        review_id="legacy-semantic-review-old-claim-passed",
        migration_run_id="legacy-v5-lossless-test",
        migration_dir=str(tmp_path / "migration"),
        topic=topic,
        status="passed",
        summary="Broad migration accounting review for the older finite diagnostic claim.",
        active_claim_id=old_claim.claim_id,
        reviewed_typed_refs=[f"claim:{old_claim.claim_id}"],
        remaining_actions=["legacy_seeds_orientation_only"],
        created_at="2026-06-15T00:00:00+00:00",
    )
    for review in (matched, newer_old_claim_review):
        write_record(
            ws.registry_dir("legacy_semantic_reviews") / f"{review.review_id}.md",
            review,
            body="# Legacy Semantic Review\n",
        )
    bind_session(
        ws,
        "chaos-current-recovery",
        topic_id=topic,
        context_id="quantum-chaos",
        active_claim=current_claim.claim_id,
    )

    relation_map = build_claim_relation_map(ws, "chaos-current-recovery")

    assert relation_map["legacy_semantic_review"]["review_id"] == matched.review_id
    assert relation_map["legacy_semantic_review"]["status"] == "inconclusive"
    assert relation_map["legacy_semantic_review"]["review_active_claim_divergence"] is False
    assert "legacy-semantic-review-old-claim-passed" in relation_map["source_records"]["legacy_semantic_reviews"]
    assert "legacy-semantic-review-current-claim-inconclusive" in relation_map["source_records"]["legacy_semantic_reviews"]
    assert "legacy_semantic_review_inconclusive" in relation_map["current_blockers"]


def test_claim_relation_map_surfaces_same_topic_sibling_claim_boundaries(tmp_path):
    from brain.v5.claim_relation_map import (
        build_claim_relation_map,
        compact_claim_relation_map,
        render_claim_relation_map_markdown,
    )
    from brain.v5.evidence import record_evidence
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    topic = "quantum-chaos-long-range-spin-chains"
    create_topic(ws, topic, context_id="quantum-chaos", title="Quantum chaos long-range spin chains")
    active_claim = create_claim(
        ws,
        topic_id=topic,
        statement="Current A2 Schur-tail theorem claim.",
        evidence_profile="semi_formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="All-n Schur rowspace theorem remains open.",
    )
    old_numerical_claim = create_claim(
        ws,
        topic_id=topic,
        statement="Older four-diagnostic finite-size chaos-window claim.",
        evidence_profile="numerical_diagnostics",
        confidence_state="legacy_seed",
        active_uncertainty="Historical numerical line, not the active theorem focus.",
    )
    record_evidence(
        ws,
        topic_id=topic,
        claim_id=old_numerical_claim.claim_id,
        evidence_type="legacy_numerical_diagnostic",
        status="supports",
        summary="Legacy OTOC/Krylov finite-size evidence supports the older numerical claim only.",
    )
    bind_session(
        ws,
        "chaos-current-recovery",
        topic_id=topic,
        context_id="quantum-chaos",
        active_claim=active_claim.claim_id,
    )

    relation_map = build_claim_relation_map(ws, "chaos-current-recovery")
    compact = compact_claim_relation_map(relation_map)
    markdown = render_claim_relation_map_markdown(relation_map)

    assert require_valid_public_surface("claim_relation_map", relation_map) == relation_map
    assert relation_map["claim_id"] == active_claim.claim_id
    assert relation_map["supported_by"] == []
    assert relation_map["topic_claim_boundaries"]["sibling_claim_count"] == 1
    assert relation_map["topic_claim_boundaries"]["sibling_claims"][0]["claim_id"] == old_numerical_claim.claim_id
    assert relation_map["source_records"]["sibling_claims"] == [old_numerical_claim.claim_id]
    assert any(
        "cannot use sibling-claim evidence" in item
        for item in relation_map["topic_claim_boundaries"]["current_conclusion"]["cannot_say"]
    )
    assert compact["sibling_claim_count"] == 1
    assert old_numerical_claim.claim_id in markdown
    assert "Topic Claim Boundaries" in markdown


def test_claim_relation_map_is_forced_into_brief_topic_status_cli_and_mcp(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_get_claim_relation_map, aitp_v5_get_execution_brief
    from brain.v5.topic_status import write_topic_status_surfaces

    ws, claim, _, _, si_failure, _ = _setup_h2o_si_runtime_failure_workspace(tmp_path)

    assert main(["--base", str(ws.base), "relation-map", "qsgw-si-recovery"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_get_claim_relation_map(str(ws.base), session_id="qsgw-si-recovery")
    brief = aitp_v5_get_execution_brief(str(ws.base), session_id="qsgw-si-recovery")
    bundle = write_topic_status_surfaces(ws, session_id="qsgw-si-recovery")

    for payload in (cli_payload, mcp_payload, brief["claim_relation_map"], bundle["topic_state"]["claim_relation_map"]):
        assert payload["kind"] == "claim_relation_map"
        assert payload["claim_id"] == claim.claim_id
        assert si_failure.evidence_id in {entry["record_id"] for entry in payload["not_tested_by"]}
        assert payload["contradicted_by"] == []

    relation_map_path = Path(bundle["files"]["claim_relation_map"])
    session_start = Path(bundle["files"]["session_start"]).read_text(encoding="utf-8")
    assert relation_map_path.exists()
    assert "Current Relation Map" in relation_map_path.read_text(encoding="utf-8")
    assert "Cannot say" in session_start
    assert "runtime/application failures" in session_start


def test_claim_relation_map_mcp_returns_empty_map_for_malformed_session(tmp_path):
    from brain.v5.markdown import write_md
    from brain.v5.mcp_tools import aitp_v5_get_claim_relation_map
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    write_md(ws.session_path("malformed-session"), {}, "# Malformed session\n")

    payload = aitp_v5_get_claim_relation_map(str(ws.base), session_id="malformed-session")

    assert payload["kind"] == "claim_relation_map"
    assert payload["session_id"] == "malformed-session"
    assert payload["topic_id"] == "unbound-session"
    assert payload["claim_id"] == ""
    assert payload["current_conclusion"]["can_say"] == ["session binding is missing or malformed"]
    assert payload["trust_update_allowed"] is False


def test_claim_relation_map_cli_returns_empty_map_for_malformed_session(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.markdown import write_md
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    write_md(ws.session_path("malformed-session"), {}, "# Malformed session\n")

    assert main(["--base", str(ws.base), "relation-map", "malformed-session"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["kind"] == "claim_relation_map"
    assert payload["session_id"] == "malformed-session"
    assert payload["topic_id"] == "unbound-session"
    assert payload["claim_id"] == ""
    assert payload["current_conclusion"]["can_say"] == ["session binding is missing or malformed"]
    assert payload["trust_update_allowed"] is False
