from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="derivation-migration-test", host="pytest")


def _legacy(root):
    anchor = root / "L1" / "derivation_anchor_map.md"
    derivation = root / "L3" / "derive" / "active_derivation.md"
    trace = root / "L3" / "trace-derivation" / "active_trace.md"
    run = root / "L3" / "runs" / "run-001" / "derivation_records.md"
    for path in (anchor, derivation, trace, run):
        path.parent.mkdir(parents=True, exist_ok=True)
    anchor.write_text("# Anchors\n\nEq. (2.1) fixes the convention.\n", encoding="utf-8")
    derivation.write_text(
        "# Active Derivation\n\nD1: Define Z_n.\nD2: Continue n to one.\n",
        encoding="utf-8",
    )
    trace.write_text("# Trace\n\nThe source trace still has an open gap.\n", encoding="utf-8")
    run.write_text("# Run Derivation\n\nA finite check was attempted.\n", encoding="utf-8")
    return anchor, derivation, trace, run


def _workspace(tmp_path):
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum gravity")
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="A legacy derivation requires reviewed structural mapping.",
        evidence_profile="formal_derivation",
        confidence_state="review_blocked",
        active_uncertainty="Legacy step segmentation is unresolved.",
    )
    return ws, claim


def _checkpoint(ws, claim, candidate):
    from brain.v5.derivation_migration import derivation_migration_apply_payload_hash
    from brain.v5.execution_models import HumanCheckpointRecord
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.record_repository import RecordRepository

    checkpoint = HumanCheckpointRecord(
        checkpoint_id="legacy-derivation-apply",
        topic_id="qg",
        claim_id=claim.claim_id,
        reason="Approve exact legacy derivation candidate mapping.",
        requested_by="migration-review",
        options=["approve", "reject"],
        status="decided",
        decision="approve",
        rationale="The exact source bytes and unresolved mappings were reviewed.",
        decided_by="human-reviewer",
        decision_verified=True,
        decision_verification="hmac_sha256_v1",
        decision_receipt_hash=f"sha256:{'b' * 64}",
        decision_receipt_nonce="nonce-1",
        can_authorize_trust=True,
        action="apply_derivation_migration",
        payload_hash=derivation_migration_apply_payload_hash(
            candidate,
            candidate.unresolved_mappings,
            _mapped_chain(candidate, claim.claim_id),
        ),
        target_scope_refs=["topic:qg", f"claim:{claim.claim_id}"],
    )
    result = RecordRepository(ws, actor=_actor()).write("checkpoints", checkpoint)
    return PinnedRecordRef(result.record_ref, result.content_hash, result.revision)


def _mapped_chain(candidate, claim_id):
    from brain.v5.derivation_models import DerivationChainRecord

    return DerivationChainRecord(
        chain_id=candidate.proposed_chain_id,
        topic_id="qg",
        claim_id=claim_id,
        title="Reviewed legacy derivation candidate",
        target="Map the legacy text into inspectable steps without claiming closure.",
        assumptions=["legacy assumptions require explicit mapping"],
        conventions=["legacy conventions preserved verbatim"],
        framework="legacy formal derivation candidate",
        regime="migration review only",
        open_gaps=list(candidate.unresolved_mappings),
        status="draft",
    )


def _apply_request(candidate, checkpoint_ref, claim_id, *, resolved=True):
    from brain.v5.derivation_contracts import ReviewedDerivationMigrationApply

    return ReviewedDerivationMigrationApply(
        candidate_id=candidate.candidate_id,
        source_relative_path=candidate.source_relative_path,
        expected_source_sha256=candidate.source_sha256,
        checkpoint_ref=checkpoint_ref,
        resolved_mappings=(candidate.unresolved_mappings if resolved else ()),
        chain=_mapped_chain(candidate, claim_id),
    )


def test_legacy_derivation_dry_run_preserves_path_hash_text_and_writes_nothing(tmp_path):
    from brain.v5.derivation_migration import migrate_legacy_derivation_candidates
    from brain.v5.record_repository import RecordRepository

    ws, claim = _workspace(tmp_path / "ws")
    _anchor, derivation, _trace, _run = _legacy(tmp_path / "legacy")

    result = migrate_legacy_derivation_candidates(
        ws,
        tmp_path / "legacy",
        topic_id="qg",
        claim_id=claim.claim_id,
    )

    assert result["applied"] is False
    assert result["candidate_count"] == 4
    candidate = next(
        item for item in result["candidates"]
        if item.source_relative_path == "L3/derive/active_derivation.md"
    )
    raw = derivation.read_bytes()
    assert candidate.source_sha256 == hashlib.sha256(raw).hexdigest()
    assert candidate.original_text == raw.decode("utf-8")
    assert candidate.unresolved_mappings
    repository = RecordRepository(ws, actor=_actor())
    assert repository.list("derivation_chains").records == ()
    assert repository.list("derivation_steps").records == ()
    assert repository.list("derivation_reviews").records == ()


def test_reviewed_apply_writes_one_draft_chain_and_is_idempotent(tmp_path):
    from brain.v5.derivation_migration import migrate_legacy_derivation_candidates
    from brain.v5.derivation_models import DerivationChainRecord
    from brain.v5.pinned_record_refs import get_record_version
    from brain.v5.record_repository import RecordRepository

    ws, claim = _workspace(tmp_path / "ws")
    _legacy(tmp_path / "legacy")
    plan = migrate_legacy_derivation_candidates(
        ws,
        tmp_path / "legacy",
        topic_id="qg",
        claim_id=claim.claim_id,
    )
    candidate = next(
        item for item in plan["candidates"]
        if item.source_relative_path == "L3/derive/active_derivation.md"
    )
    checkpoint_ref = _checkpoint(ws, claim, candidate)
    request = _apply_request(candidate, checkpoint_ref, claim.claim_id)

    with pytest.raises(ValueError, match="apply payload does not match the reviewed checkpoint"):
        migrate_legacy_derivation_candidates(
            ws,
            tmp_path / "legacy",
            topic_id="qg",
            claim_id=claim.claim_id,
            apply_request=replace(
                request,
                chain=replace(request.chain, title="Substituted after review"),
            ),
            actor=_actor(),
        )

    applied = migrate_legacy_derivation_candidates(
        ws,
        tmp_path / "legacy",
        topic_id="qg",
        claim_id=claim.claim_id,
        apply_request=request,
        actor=_actor(),
    )
    repeated = migrate_legacy_derivation_candidates(
        ws,
        tmp_path / "legacy",
        topic_id="qg",
        claim_id=claim.claim_id,
        apply_request=request,
        actor=_actor(),
    )

    assert applied["applied"] is True
    assert repeated["applied"] is True
    assert repeated["idempotent"] is True
    chain = get_record_version(ws, applied["chain_ref"]).record
    assert isinstance(chain, DerivationChainRecord)
    assert chain.status == "draft"
    assert chain.migration_provenance["source_relative_path"] == candidate.source_relative_path
    assert chain.migration_provenance["source_sha256"] == candidate.source_sha256
    assert chain.migration_provenance["original_text"] == candidate.original_text
    assert chain.can_update_claim_trust is False
    repository = RecordRepository(ws, actor=_actor())
    assert len(repository.list("derivation_chains").records) == 1
    assert repository.list("trust_updates").records == ()


def test_apply_rejects_unresolved_mapping_and_source_hash_drift_without_writes(tmp_path):
    from brain.v5.derivation_migration import migrate_legacy_derivation_candidates
    from brain.v5.record_repository import RecordRepository

    ws, claim = _workspace(tmp_path / "ws")
    _anchor, derivation, _trace, _run = _legacy(tmp_path / "legacy")
    plan = migrate_legacy_derivation_candidates(
        ws,
        tmp_path / "legacy",
        topic_id="qg",
        claim_id=claim.claim_id,
    )
    candidate = next(
        item for item in plan["candidates"]
        if item.source_relative_path == "L3/derive/active_derivation.md"
    )
    checkpoint_ref = _checkpoint(ws, claim, candidate)

    with pytest.raises(ValueError, match="resolve every declared legacy mapping"):
        migrate_legacy_derivation_candidates(
            ws,
            tmp_path / "legacy",
            topic_id="qg",
            claim_id=claim.claim_id,
            apply_request=_apply_request(candidate, checkpoint_ref, claim.claim_id, resolved=False),
            actor=_actor(),
        )

    derivation.write_text("# Changed after review\n", encoding="utf-8")
    with pytest.raises(ValueError, match="source hash changed after review"):
        migrate_legacy_derivation_candidates(
            ws,
            tmp_path / "legacy",
            topic_id="qg",
            claim_id=claim.claim_id,
            apply_request=_apply_request(candidate, checkpoint_ref, claim.claim_id),
            actor=_actor(),
        )

    repository = RecordRepository(ws, actor=_actor())
    assert repository.list("derivation_chains").records == ()
