from __future__ import annotations

from dataclasses import asdict
import json

import pytest


QG_NOTE = br"""# Semiclassical entropy

Definition 1. Generalized entropy is
\[S_{\rm gen}=A/(4G_N)+S_{\rm bulk}.\]

Assumption A1. The bulk state is semiclassical near the candidate surface.

Caveat. This formula alone does not establish a fixed-theory microscopic count.
"""


def _review_and_promote(base, ws, candidate, checkpoint_id):
    from brain.v5 import mcp_tools
    from tests.test_v5_knowledge_promotion import _review_checkpoint

    checkpoint = _review_checkpoint(
        ws,
        candidate,
        checkpoint_id=checkpoint_id,
    )
    reviewed = mcp_tools.aitp_v5_knowledge_record_review(
        str(base),
        payload_json=json.dumps(
            {
                "candidate": asdict(candidate),
                "checkpoint_ref": asdict(checkpoint),
                "decision": "approve",
            }
        ),
    )
    return mcp_tools.aitp_v5_knowledge_promote_candidate(
        str(base),
        payload_json=json.dumps(
            {
                "candidate": asdict(candidate),
                "decision_ref": reviewed["result"]["pinned_ref"],
            }
        ),
    )


def test_gate3_qft_qg_fixture_vertical_preserves_framework_and_speculation(tmp_path):
    from brain.v5 import mcp_tools
    from brain.v5.knowledge_candidates import KnowledgeCandidate
    from brain.v5.physics_knowledge_models import PhysicsAssertionRecord, PhysicsObjectRecord
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.query_index import build_query_index
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository
    from brain.v5.source_shelf import SourceShelfBuildRequest, build_source_shelf
    from tests.test_v5_source_shelf import _acquired_asset, _setup_topic

    ws = _setup_topic(tmp_path)
    asset, _blob, location = _acquired_asset(
        ws,
        name="gate3-qg-note",
        content=QG_NOTE,
    )
    source_ref = f"source_asset:{asset.asset_id}"
    location_ref = f"reference_location:{location.location_id}"
    shelf = build_source_shelf(
        ws,
        SourceShelfBuildRequest(
            topic_id="qg",
            source_asset_refs=(source_ref,),
            curation_rationale="Fixture-only QG source shelf for M3 acceptance.",
            max_passage_chars=1600,
        ),
    )
    actor = RecordActor(actor_type="tool", actor_id="gate3-qg-e2e", host="pytest")
    repository = RecordRepository(ws, actor=actor)
    subject = repository.write(
        "physics_objects",
        PhysicsObjectRecord(
            object_id="gate3-generalized-entropy",
            topic_id="qg",
            object_type="entropy_functional",
            name="Generalized entropy",
            definition="Stable object identity reviewed separately from sourced assertions.",
            notation="S_gen",
        ),
    )
    grounded = KnowledgeCandidate(
        candidate_id="gate3-qg-generalized-entropy-definition",
        content_kinds=("definition",),
        statement="S_gen equals area over four G_N plus bulk entropy.",
        topic_id="qg",
        subject_ref=subject.record_ref,
        grounding_pins=(
            pin_current_record(ws, source_ref),
            pin_current_record(ws, location_ref),
        ),
        framework="semiclassical gravity",
        regime="island formula",
        conventions=("positive-area-term",),
    )
    promoted_grounded = _review_and_promote(
        tmp_path,
        ws,
        grounded,
        "gate3-grounded-review",
    )
    insight = KnowledgeCandidate(
        candidate_id="gate3-qg-ensemble-analogy",
        content_kinds=("analogy",),
        statement="The saddle sum may organize an ensemble-averaging analogy.",
        topic_id="qg",
        framework="semiclassical gravity",
        regime="island formula",
    )
    promoted_insight = _review_and_promote(
        tmp_path,
        ws,
        insight,
        "gate3-insight-review",
    )
    wrong_framework = repository.write(
        "physics_assertions",
        PhysicsAssertionRecord(
            assertion_id="gate3-aqft-generalized-entropy-collision",
            object_ref=subject.record_ref,
            topic_id="qg",
            predicate="comparison_only",
            value="Generalized entropy is compared to local algebra entropy.",
            expression="S=-Tr(rho log rho)",
            framework="algebraic QFT",
            regime="continuum local net",
            conventions=["opposite-comparison-convention"],
            review_status="reviewed",
        ),
    )
    build_query_index(ws)

    query = mcp_tools.aitp_v5_knowledge_query(
        str(tmp_path),
        payload_json=json.dumps(
            {
                "query": {
                    "text": "generalized entropy area bulk saddle ensemble",
                    "formula": "S_gen=A/(4G_N)+S_bulk",
                    "topic_id": "qg",
                    "framework": "semiclassical gravity",
                    "regime": "island formula",
                    "intent": "insight",
                    "max_results": 8,
                },
                "source_shelf_generation": shelf.manifest.generation,
                "source_shelf_topic_id": "qg",
            }
        ),
    )
    context = mcp_tools.aitp_v5_knowledge_compile_context(
        str(tmp_path),
        payload_json=json.dumps(
            {
                "request": {
                    "query_text": "generalized entropy area bulk saddle ensemble",
                    "formula": "S_gen=A/(4G_N)+S_bulk",
                    "topic_id": "qg",
                    "framework": "semiclassical gravity",
                    "regime": "island formula",
                    "intent": "insight",
                    "mode": "normal",
                    "source_shelf_generation": shelf.manifest.generation,
                    "source_shelf_topic_id": "qg",
                }
            }
        ),
    )

    query_refs = {hit["record_ref"] for hit in query["result"]["hits"]}
    context_entries = {
        entry["record_ref"]: entry for entry in context["result"]["entries"]
    }
    grounded_ref = promoted_grounded["result"]["pinned_ref"]["record_ref"]
    insight_ref = promoted_insight["result"]["pinned_ref"]["record_ref"]
    assert grounded_ref in query_refs
    assert wrong_framework.record_ref not in query_refs
    assert query["result"]["coverage"]["excluded_scope"]["wrong_framework_excluded"] >= 1
    assert grounded_ref in context_entries
    assert insight_ref in context_entries
    assert context_entries[grounded_ref]["grounding_state"] == "reviewed_grounded"
    assert context_entries[insight_ref]["grounding_state"] == "speculative_non_evidence"
    assert context_entries[insight_ref]["speculation_level"]
    assert context["result"]["orientation_only"] is True
    assert context["can_update_claim_trust"] is False
    assert repository.list("evidence").records == ()
    assert repository.list("trust_updates").records == ()


def test_gate3_missing_and_stale_sources_fail_closed(tmp_path):
    from brain.v5 import mcp_tools
    from brain.v5.source_assets import register_source_asset
    from brain.v5.source_shelf import SourceShelfBuildRequest, build_source_shelf
    from brain.v5.source_shelf_models import SourceShelfStaleError
    from tests.test_v5_source_shelf import _acquired_asset, _setup_topic

    ws = _setup_topic(tmp_path)
    missing = register_source_asset(
        ws,
        topic_id="qg",
        asset_type="paper",
        uri="https://example.test/gate3-metadata-only",
        title="Metadata-only source",
        metadata={"acquisition_state": "metadata_only", "shelf_eligible": False},
    )
    missing_report = build_source_shelf(
        ws,
        SourceShelfBuildRequest(
            topic_id="qg",
            source_asset_refs=(f"source_asset:{missing.asset_id}",),
            curation_rationale="Exercise explicit missing-source coverage.",
        ),
    )
    assert missing_report.incomplete_coverage is True
    assert missing_report.issues[0].code == "source_not_shelf_eligible"

    asset, blob, _location = _acquired_asset(
        ws,
        name="gate3-stale-source",
        content=QG_NOTE,
    )
    stale_report = build_source_shelf(
        ws,
        SourceShelfBuildRequest(
            topic_id="qg",
            source_asset_refs=(f"source_asset:{asset.asset_id}",),
            curation_rationale="Exercise source-byte revalidation.",
        ),
    )
    blob.write_bytes(QG_NOTE + b"\nChanged after publication.\n")

    with pytest.raises(SourceShelfStaleError):
        mcp_tools.aitp_v5_knowledge_get_source_shelf(
            str(tmp_path),
            payload_json=json.dumps(
                {"generation": stale_report.manifest.generation}
            ),
        )
