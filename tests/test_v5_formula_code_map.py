from __future__ import annotations

from dataclasses import replace

import pytest


RELATION_TYPES = (
    "implemented_by",
    "controlled_by_parameter",
    "approximated_by",
    "discretized_by",
    "normalizes_as",
    "produces_observable",
    "validated_by",
)


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="formula-code-test", host="pytest")


def _write(ws, family, record):
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.record_repository import RecordRepository

    result = RecordRepository(ws, actor=_actor()).write(family, record)
    return PinnedRecordRef(result.record_ref, result.content_hash, result.revision)


def _revise_code(ws, record, prior_ref):
    from brain.v5.record_repository import RecordRepository, WritePolicy

    return RecordRepository(ws, actor=_actor()).write(
        "code_states",
        record,
        body=(
            "# Code State\n\n"
            f"Repository: `{record.repo_id}`\n\n"
            f"Commit: `{record.upstream_commit}`\n"
        ),
        policy=WritePolicy(mode="revision", expected_hash=prior_ref.content_hash),
    )


def _revise_source(ws, record, prior_ref):
    from brain.v5.record_repository import RecordRepository, WritePolicy

    return RecordRepository(ws, actor=_actor()).write(
        "reference_locations",
        record,
        body=f"# Reference Location\n\n{record.label}\n",
        policy=WritePolicy(mode="revision", expected_hash=prior_ref.content_hash),
    )


def _revise_relation(ws, record, prior_ref):
    from brain.v5.record_repository import RecordRepository, WritePolicy

    return RecordRepository(ws, actor=_actor()).write(
        "object_relations",
        record,
        body=f"# Formula-Code Relation\n\n{record.statement}\n",
        policy=WritePolicy(mode="revision", expected_hash=prior_ref.content_hash),
    )


def _fixture(tmp_path):
    from brain.v5.execution_models import CodeStateRecord, ExecutionBaselineRecord
    from brain.v5.execution_writers import record_code_state_v2
    from brain.v5.models import ArtifactRecord
    from brain.v5.physics_objects import record_physics_object
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.research_state import register_source
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa", context_id="gw-methods", title="LibRPA")
    create_topic(ws, "other-topic", context_id="formal-theory", title="Other")
    claim = create_claim(
        ws,
        topic_id="librpa",
        statement="The correlation self-energy implementation matches the reviewed formula.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="formula-code mapping review",
    )
    formula = record_physics_object(
        ws,
        topic_id="librpa",
        object_type="formula",
        name="correlation self-energy",
        definition="Sigma_c = i G W_c in the reviewed frequency convention.",
        notation="Sigma_c(iw)",
        assumptions=["imaginary-frequency contour", "RPA screening"],
    )
    formula_ref = pin_current_record(ws, f"physics_object:{formula.object_id}")
    code = CodeStateRecord(
        code_state_id="librpa-code-reviewed",
        repo_id="LibRPA",
        upstream_remote="origin",
        upstream_branch="main",
        upstream_commit="a" * 40,
        local_branch="codex/formula-map",
        worktree_path="/work/LibRPA",
        dirty=False,
        linked_records={"topic_id": "librpa", "claim_id": claim.claim_id},
    )
    code_write = record_code_state_v2(ws, code, actor=_actor())
    code_ref = pin_current_record(ws, code_write.record_ref)
    source = register_source(
        ws,
        topic_id="librpa",
        claim_id=claim.claim_id,
        uri="https://example.invalid/librpa-method.pdf",
        label="LibRPA method note",
    )
    source_ref = pin_current_record(ws, f"reference_location:{source.location_id}")
    test_artifact = ArtifactRecord(
        artifact_id="sigma-c-regression-test",
        topic_id="librpa",
        claim_id=claim.claim_id,
        artifact_type="test_report",
        uri="file:///work/LibRPA/tests/sigma_c.json",
        summary="Pinned regression test for the self-energy kernel.",
        content_hash="b" * 64,
        hash_algorithm="sha256",
    )
    test_ref = _write(ws, "artifacts", test_artifact)
    baseline = ExecutionBaselineRecord(
        baseline_id="librpa-sigma-c-baseline",
        topic_id="librpa",
        claim_id=claim.claim_id,
        run_ref="tool_run:librpa-sigma-c-run",
        frozen_dependencies={"nodes": []},
        code_state_ref=code_ref.record_ref,
        code_state_hash=code_ref.content_hash,
        code_state_revision=code_ref.revision,
        status="active",
        created_at="2026-07-15T03:00:00+00:00",
    )
    baseline_ref = _write(ws, "execution_baselines", baseline)
    return {
        "ws": ws,
        "claim": claim,
        "formula": formula,
        "formula_ref": formula_ref,
        "code": code,
        "code_ref": code_ref,
        "source_ref": source_ref,
        "test_ref": test_ref,
        "baseline_ref": baseline_ref,
    }


def _relation(data, relation_type="implemented_by"):
    from brain.v5.formula_code_contracts import FormulaCodeRelation

    return FormulaCodeRelation(
        topic_id="librpa",
        claim_id=data["claim"].claim_id,
        relation_type=relation_type,
        statement="The reviewed self-energy formula maps to the LibRPA sigma_c kernel.",
        formula_ref=data["formula_ref"],
        code_state_ref=data["code_ref"],
        module="src/gw/self_energy.cpp",
        function="build_sigma_c",
        parameter="nfreq",
        output="sigma_c_matrix",
        normalization="1 / N_k",
        scope=("topic:librpa", f"claim:{data['claim'].claim_id}"),
        assumptions=("imaginary-frequency contour",),
        source_refs=(data["source_ref"],),
        test_refs=(data["test_ref"],),
        accepted_baseline_ref=data["baseline_ref"],
        known_failures=("frequency-grid mismatch changes the discretized integral",),
        applicability_boundary="LibRPA main branch at the pinned commit and RPA screening only.",
    )


@pytest.mark.parametrize("relation_type", RELATION_TYPES)
def test_formula_code_relation_types_use_exact_object_relation_metadata(tmp_path, relation_type):
    from brain.v5.formula_code_map import record_formula_code_relation
    from brain.v5.models import ObjectRelationRecord
    from brain.v5.pinned_record_refs import get_record_version

    data = _fixture(tmp_path)
    result = record_formula_code_relation(
        data["ws"],
        _relation(data, relation_type),
        actor=_actor(),
    )
    stored = get_record_version(
        data["ws"],
        {"record_ref": result.record_ref, "content_hash": result.content_hash, "revision": result.revision},
    ).record

    assert isinstance(stored, ObjectRelationRecord)
    assert stored.relation_type == relation_type
    assert stored.subject_id == data["formula"].object_id
    assert stored.object_id == data["code"].code_state_id
    assert stored.status == "reviewed"
    assert stored.metadata["schema_version"] == "formula-code-relation/v1"
    assert stored.metadata["formula_ref"]["content_hash"] == data["formula_ref"].content_hash
    assert stored.metadata["code_state_ref"]["revision"] == data["code_ref"].revision
    assert stored.metadata["test_refs"][0]["record_ref"] == data["test_ref"].record_ref
    assert stored.metadata["accepted_baseline_ref"]["record_ref"] == data["baseline_ref"].record_ref


def test_relation_rejects_stale_code_ref_and_foreign_scope(tmp_path):
    from brain.v5.formula_code_map import record_formula_code_relation
    from brain.v5.pinned_record_refs import pin_current_record

    data = _fixture(tmp_path)
    stale = data["code_ref"]
    revised = replace(data["code"], known_divergence="reviewed source changed")
    _revise_code(data["ws"], revised, stale)

    with pytest.raises(ValueError, match="code state ref is stale"):
        record_formula_code_relation(data["ws"], _relation(data), actor=_actor())

    current = pin_current_record(data["ws"], stale.record_ref)
    with pytest.raises(ValueError, match="foreign formula topic|topic and claim scope"):
        record_formula_code_relation(
            data["ws"],
            replace(
                _relation({**data, "code_ref": current}),
                topic_id="other-topic",
                scope=("topic:other-topic", f"claim:{data['claim'].claim_id}"),
            ),
            actor=_actor(),
        )


def test_relation_rejects_baseline_for_a_different_code_state(tmp_path):
    from brain.v5.execution_models import ExecutionBaselineRecord
    from brain.v5.formula_code_map import record_formula_code_relation

    data = _fixture(tmp_path)
    other_baseline = ExecutionBaselineRecord(
        baseline_id="foreign-code-baseline",
        topic_id="librpa",
        claim_id=data["claim"].claim_id,
        run_ref="tool_run:other",
        frozen_dependencies={"nodes": []},
        code_state_ref="code_state:other-code",
        code_state_hash="c" * 64,
        code_state_revision=1,
        status="active",
    )
    other_ref = _write(data["ws"], "execution_baselines", other_baseline)

    with pytest.raises(ValueError, match="same exact code state"):
        record_formula_code_relation(
            data["ws"],
            replace(_relation(data), accepted_baseline_ref=other_ref),
            actor=_actor(),
        )


def test_relation_rejects_unscoped_or_wrong_family_source_and_test_refs(tmp_path):
    from brain.v5.formula_code_map import record_formula_code_relation
    from brain.v5.models import ReferenceLocationRecord

    data = _fixture(tmp_path)
    unscoped_source = ReferenceLocationRecord(
        location_id="unscoped-method-note",
        topic_id="",
        connector_id="manual",
        location_type="source",
        uri="https://example.invalid/unscoped.pdf",
        label="Unscoped note",
        claim_id="",
    )
    unscoped_ref = _write(data["ws"], "reference_locations", unscoped_source)

    with pytest.raises(ValueError, match="source ref must have explicit topic scope"):
        record_formula_code_relation(
            data["ws"],
            replace(_relation(data), source_refs=(unscoped_ref,)),
            actor=_actor(),
        )

    with pytest.raises(ValueError, match="test ref must pin an artifact or validation result"):
        record_formula_code_relation(
            data["ws"],
            replace(_relation(data), test_refs=(data["formula_ref"],)),
            actor=_actor(),
        )


def test_capsule_revalidates_review_status_and_baseline_code_binding(tmp_path):
    from brain.v5.execution_models import ExecutionBaselineRecord
    from brain.v5.formula_code_contracts import CodeEditCapsuleRequest
    from brain.v5.formula_code_map import (
        build_code_edit_execution_capsule,
        record_formula_code_relation,
    )
    from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record

    data = _fixture(tmp_path)
    written = record_formula_code_relation(data["ws"], _relation(data), actor=_actor())
    relation_ref = PinnedRecordRef(written.record_ref, written.content_hash, written.revision)
    relation = get_record_version(data["ws"], relation_ref).record
    _revise_relation(data["ws"], replace(relation, status="hypothesis"), relation_ref)

    with pytest.raises(ValueError, match="must remain reviewed"):
        build_code_edit_execution_capsule(
            data["ws"],
            CodeEditCapsuleRequest(
                relation_ref=pin_current_record(data["ws"], relation_ref.record_ref),
                topic_id="librpa",
                claim_id=data["claim"].claim_id,
            ),
        )

    data = _fixture(tmp_path / "baseline-tamper")
    written = record_formula_code_relation(data["ws"], _relation(data), actor=_actor())
    relation_ref = PinnedRecordRef(written.record_ref, written.content_hash, written.revision)
    relation = get_record_version(data["ws"], relation_ref).record
    other_baseline = ExecutionBaselineRecord(
        baseline_id="tampered-code-baseline",
        topic_id="librpa",
        claim_id=data["claim"].claim_id,
        run_ref="tool_run:other",
        frozen_dependencies={"nodes": []},
        code_state_ref="code_state:other-code",
        code_state_hash="c" * 64,
        code_state_revision=1,
        status="active",
    )
    other_ref = _write(data["ws"], "execution_baselines", other_baseline)
    metadata = dict(relation.metadata)
    metadata["accepted_baseline_ref"] = {
        "record_ref": other_ref.record_ref,
        "content_hash": other_ref.content_hash,
        "revision": other_ref.revision,
    }
    revised = _revise_relation(
        data["ws"],
        replace(relation, metadata=metadata),
        relation_ref,
    )

    with pytest.raises(ValueError, match="same exact code state"):
        build_code_edit_execution_capsule(
            data["ws"],
            CodeEditCapsuleRequest(
                relation_ref=PinnedRecordRef(
                    revised.record_ref,
                    revised.content_hash,
                    revised.revision,
                ),
                topic_id="librpa",
                claim_id=data["claim"].claim_id,
            ),
        )


def test_edit_capsule_is_bounded_exact_and_stale_code_blocks_reproducibility(tmp_path):
    from brain.v5.formula_code_contracts import CodeEditCapsuleRequest
    from brain.v5.formula_code_map import (
        build_code_edit_execution_capsule,
        record_formula_code_relation,
    )
    from brain.v5.pinned_record_refs import PinnedRecordRef

    data = _fixture(tmp_path)
    written = record_formula_code_relation(data["ws"], _relation(data), actor=_actor())
    relation_ref = PinnedRecordRef(written.record_ref, written.content_hash, written.revision)
    request = CodeEditCapsuleRequest(
        relation_ref=relation_ref,
        topic_id="librpa",
        claim_id=data["claim"].claim_id,
    )

    ready = build_code_edit_execution_capsule(data["ws"], request)

    assert ready["status"] == "ready"
    assert ready["reproducible"] is True
    assert ready["formula"]["notation"] == "Sigma_c(iw)"
    assert ready["code"]["module"] == "src/gw/self_energy.cpp"
    assert ready["code"]["function"] == "build_sigma_c"
    assert ready["code"]["commit"] == "a" * 40
    assert ready["parameter"]["name"] == "nfreq"
    assert ready["tests"][0]["record_ref"] == data["test_ref"].record_ref
    assert ready["accepted_baseline"]["record_ref"] == data["baseline_ref"].record_ref
    assert relation_ref.record_ref in ready["exact_expansion_refs"]
    assert ready["can_update_claim_trust"] is False

    _revise_code(
        data["ws"],
        replace(data["code"], known_divergence="new unreviewed edit"),
        data["code_ref"],
    )
    stale = build_code_edit_execution_capsule(data["ws"], request)

    assert stale["status"] == "stale_code_state"
    assert stale["reproducible"] is False
    assert stale["baseline_claims_allowed"] is False
    assert stale["orientation_only"] is False
    assert "code state changed after relation review" in stale["blocking_reasons"]


def test_capsule_without_baseline_is_editable_but_not_reproducible(tmp_path):
    from brain.v5.formula_code_contracts import CodeEditCapsuleRequest
    from brain.v5.formula_code_map import (
        build_code_edit_execution_capsule,
        record_formula_code_relation,
    )
    from brain.v5.pinned_record_refs import PinnedRecordRef

    data = _fixture(tmp_path)
    written = record_formula_code_relation(
        data["ws"],
        replace(_relation(data), accepted_baseline_ref=None),
        actor=_actor(),
    )
    capsule = build_code_edit_execution_capsule(
        data["ws"],
        CodeEditCapsuleRequest(
            relation_ref=PinnedRecordRef(
                written.record_ref,
                written.content_hash,
                written.revision,
            ),
            topic_id="librpa",
            claim_id=data["claim"].claim_id,
        ),
    )

    assert capsule["status"] == "ready_for_edit"
    assert capsule["ok"] is True
    assert capsule["can_execute_edit"] is True
    assert capsule["reproducible"] is False
    assert capsule["baseline_claims_allowed"] is False
    assert capsule["orientation_only"] is False
    assert capsule["limitations"] == ["no accepted baseline is pinned"]


def test_changed_source_pin_blocks_capsule_without_calling_it_orientation(tmp_path):
    from brain.v5.formula_code_contracts import CodeEditCapsuleRequest
    from brain.v5.formula_code_map import (
        build_code_edit_execution_capsule,
        record_formula_code_relation,
    )
    from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version

    data = _fixture(tmp_path)
    written = record_formula_code_relation(data["ws"], _relation(data), actor=_actor())
    source = get_record_version(data["ws"], data["source_ref"]).record
    _revise_source(
        data["ws"],
        replace(source, label="Revised LibRPA method note"),
        data["source_ref"],
    )

    capsule = build_code_edit_execution_capsule(
        data["ws"],
        CodeEditCapsuleRequest(
            relation_ref=PinnedRecordRef(
                written.record_ref,
                written.content_hash,
                written.revision,
            ),
            topic_id="librpa",
            claim_id=data["claim"].claim_id,
        ),
    )

    assert capsule["status"] == "blocked"
    assert capsule["ok"] is False
    assert capsule["orientation_only"] is False
    assert capsule["reproducible"] is False
    assert any(
        reason.startswith("source ref changed after relation review:")
        for reason in capsule["blocking_reasons"]
    )


def test_formula_code_compact_brief_exposes_edit_location_and_boundary(tmp_path):
    from brain.v5.formula_code_map import record_formula_code_relation
    from brain.v5.physics_objects import object_relation_brief_payload
    from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version

    data = _fixture(tmp_path)
    written = record_formula_code_relation(data["ws"], _relation(data), actor=_actor())
    relation = get_record_version(
        data["ws"],
        PinnedRecordRef(written.record_ref, written.content_hash, written.revision),
    ).record

    brief = object_relation_brief_payload(relation)

    assert brief["formula_code"] == {
        "module": "src/gw/self_energy.cpp",
        "function": "build_sigma_c",
        "parameter": "nfreq",
        "output": "sigma_c_matrix",
        "applicability_boundary": "LibRPA main branch at the pinned commit and RPA screening only.",
        "code_state_ref": data["code_ref"].record_ref,
    }


def test_foreign_topic_capsule_requires_bridge_and_target_revalidation(tmp_path, monkeypatch):
    from brain.v5.execution_scope_policy import ExecutionScopeDecision
    from brain.v5.formula_code_contracts import CodeEditCapsuleRequest
    from brain.v5.formula_code_map import (
        build_code_edit_execution_capsule,
        record_formula_code_relation,
    )
    from brain.v5.pinned_record_refs import PinnedRecordRef

    data = _fixture(tmp_path)
    written = record_formula_code_relation(data["ws"], _relation(data), actor=_actor())
    relation_ref = PinnedRecordRef(written.record_ref, written.content_hash, written.revision)
    request = CodeEditCapsuleRequest(
        relation_ref=relation_ref,
        topic_id="other-topic",
        claim_id="target-claim",
    )

    blocked = build_code_edit_execution_capsule(data["ws"], request)
    assert blocked["status"] == "scope_blocked"
    assert blocked["can_execute_edit"] is False

    monkeypatch.setattr(
        "brain.v5.formula_code_map.assess_execution_scope",
        lambda *args, **kwargs: ExecutionScopeDecision(
            operation="use_formula_code_relation",
            consumer_scope=("topic:other-topic", "claim:target-claim"),
            dependency_refs=(relation_ref,),
            decision="allowed",
            same_scope_dependency_refs=(),
            foreign_dependency_refs=(relation_ref,),
            accepted_revalidation_refs=(),
            reasons=("reviewed bridge permits orientation",),
            checked_refs=(relation_ref.record_ref,),
            read_errors=(),
        ),
    )
    bridged = build_code_edit_execution_capsule(data["ws"], request)

    assert bridged["status"] == "orientation_only"
    assert bridged["requires_target_revalidation"] is True
    assert bridged["can_execute_edit"] is False
    assert bridged["baseline_claims_allowed"] is False
    assert bridged["can_update_claim_trust"] is False


def test_context_compiler_builds_exact_bounded_request_from_capsule(tmp_path):
    from brain.v5.context_compiler import context_request_for_code_edit_capsule
    from brain.v5.formula_code_contracts import CodeEditCapsuleRequest
    from brain.v5.formula_code_map import (
        build_code_edit_execution_capsule,
        record_formula_code_relation,
    )
    from brain.v5.pinned_record_refs import PinnedRecordRef

    data = _fixture(tmp_path)
    written = record_formula_code_relation(data["ws"], _relation(data), actor=_actor())
    relation_ref = PinnedRecordRef(written.record_ref, written.content_hash, written.revision)
    capsule = build_code_edit_execution_capsule(
        data["ws"],
        CodeEditCapsuleRequest(
            relation_ref=relation_ref,
            topic_id="librpa",
            claim_id=data["claim"].claim_id,
        ),
    )

    request = context_request_for_code_edit_capsule(
        "session-librpa",
        capsule,
        max_tokens=900,
        max_bytes=5000,
    )

    assert request.disclosure_level == "exact_expansion"
    assert request.exact_refs == tuple(capsule["exact_expansion_refs"])
    assert request.exact_pins == tuple(
        PinnedRecordRef(**pin) for pin in capsule["exact_expansion_pins"]
    )
    assert request.max_tokens == 900
    assert request.max_bytes == 5000


def test_exact_context_rejects_dependency_changed_after_request_build(tmp_path):
    from brain.v5.context_compiler import context_request_for_code_edit_capsule
    from brain.v5.context_compiler_retrieval import exact_disclosure_result
    from brain.v5.formula_code_contracts import CodeEditCapsuleRequest
    from brain.v5.formula_code_map import (
        build_code_edit_execution_capsule,
        record_formula_code_relation,
    )
    from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version

    data = _fixture(tmp_path)
    written = record_formula_code_relation(data["ws"], _relation(data), actor=_actor())
    capsule = build_code_edit_execution_capsule(
        data["ws"],
        CodeEditCapsuleRequest(
            relation_ref=PinnedRecordRef(
                written.record_ref,
                written.content_hash,
                written.revision,
            ),
            topic_id="librpa",
            claim_id=data["claim"].claim_id,
        ),
    )
    request = context_request_for_code_edit_capsule("session-librpa", capsule)
    source = get_record_version(data["ws"], data["source_ref"]).record
    _revise_source(
        data["ws"],
        replace(source, label="Changed after capsule compilation"),
        data["source_ref"],
    )

    with pytest.raises(ValueError, match="exact expansion pin is stale"):
        exact_disclosure_result(data["ws"], request)


@pytest.mark.parametrize(
    ("refs", "message"),
    [
        ([], "between 1 and 50 exact refs"),
        ([f"artifact:item-{index}" for index in range(51)], "between 1 and 50 exact refs"),
        (["not-a-typed-ref"], "must be typed record refs"),
    ],
)
def test_context_request_rejects_unbounded_or_untyped_capsule_refs(refs, message):
    from brain.v5.context_compiler import context_request_for_code_edit_capsule

    with pytest.raises(ValueError, match=message):
        context_request_for_code_edit_capsule(
            "session-librpa",
            {"exact_expansion_refs": refs},
        )


def test_context_request_rejects_duplicate_ref_pin_pairs():
    from brain.v5.context_compiler import context_request_for_code_edit_capsule

    pin = {
        "record_ref": "artifact:duplicate",
        "content_hash": "a" * 64,
        "revision": 1,
    }
    with pytest.raises(ValueError, match="must not contain duplicate refs"):
        context_request_for_code_edit_capsule(
            "session-librpa",
            {
                "exact_expansion_refs": ["artifact:duplicate", "artifact:duplicate"],
                "exact_expansion_pins": [pin, pin],
            },
        )
