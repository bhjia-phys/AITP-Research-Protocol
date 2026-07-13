import json

import pytest

from brain.v5.models import ClaimRecord, SourceAssetRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import (
    INDEX_SCHEMA_VERSION,
    IndexIntegrityError,
    build_query_index,
    current_canonical_watermark,
    load_query_index,
    query_index_is_fresh,
)
from brain.v5.research_retrieval import ResearchQuery, query_records
from brain.v5.store import write_record


def _seed_index_workspace(tmp_path, order):
    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    records = {
        "claim": (
            "claims",
            "claim-1",
            ClaimRecord(
                claim_id="claim-1",
                topic_id="topic-1",
                statement="Head and wing corrections improve convergence.",
                evidence_profile="numerical_validation",
                confidence_state="candidate",
                active_uncertainty="Higher-k validation remains open.",
            ),
            "# Claim\n",
        ),
        "source": (
            "source_assets",
            "source-1",
            SourceAssetRecord(
                asset_id="source-1",
                topic_id="topic-1",
                claim_id="claim-1",
                asset_type="paper",
                uri="arxiv:2601.00001",
                title="Head and wing convergence study",
                content_hash="paper-bytes-sha",
                hash_algorithm="sha256",
            ),
            "# Source\n",
        ),
    }
    for key in order:
        family, record_id, record, body = records[key]
        write_record(ws.registry_dir(family) / f"{record_id}.md", record, body=body)
    return ws


def test_query_index_is_deterministic_across_insertion_order(tmp_path):
    left = _seed_index_workspace(tmp_path / "left", ["claim", "source"])
    right = _seed_index_workspace(tmp_path / "right", ["source", "claim"])

    left_report = build_query_index(left)
    right_report = build_query_index(right)
    left_loaded = load_query_index(left)
    right_loaded = load_query_index(right)

    assert left_report.manifest.content_hash == right_report.manifest.content_hash
    assert left_report.manifest.canonical_watermark == right_report.manifest.canonical_watermark
    assert left_report.manifest.family_counts == {"claims": 1, "source_assets": 1}
    assert left_loaded.record_refs == ("claim:claim-1", "source_asset:source-1")
    assert right_loaded.record_refs == left_loaded.record_refs
    assert left_report.indexed_count == 2
    assert left_report.malformed_count == 0


def test_query_index_refuses_to_publish_a_concurrent_canonical_snapshot(tmp_path, monkeypatch):
    import brain.v5.query_index as query_index

    ws = _seed_index_workspace(tmp_path, ["claim", "source"])
    index_dir = ws.root / "indexes"
    sentinels = {
        name: f"old-{name}\n"
        for name in (
            "record_documents.json",
            "lexical_index.json",
            "issues.json",
            "manifest.json",
        )
    }
    for name, content in sentinels.items():
        (index_dir / name).write_text(content, encoding="utf-8")
    tokens = iter(("state-before-scan", "state-after-scan"))
    monkeypatch.setattr(query_index, "canonical_state_token", lambda _ws: next(tokens))

    with pytest.raises(RuntimeError, match="changed while query index was built"):
        build_query_index(ws)

    assert {
        name: (index_dir / name).read_text(encoding="utf-8")
        for name in sentinels
    } == sentinels


def test_query_reports_stale_partial_coverage_after_canonical_change(tmp_path):
    ws = _seed_index_workspace(tmp_path, ["claim", "source"])
    build_query_index(ws)
    new_claim = ClaimRecord(
        claim_id="claim-2",
        topic_id="topic-1",
        statement="A newly recorded convergence result.",
        evidence_profile="numerical_validation",
        confidence_state="candidate",
        active_uncertainty="Independent reproduction remains open.",
    )
    write_record(ws.registry_dir("claims") / "claim-2.md", new_claim, body="# New claim\n")

    result = query_records(ws, ResearchQuery(text="nonexistent phrase"))
    exact = query_records(ws, ResearchQuery(exact_refs=("claim:claim-2",)))

    assert result.index_status == "stale"
    assert result.coverage.exhaustive is False
    assert result.coverage.can_claim_no_result is False
    assert "absolute no-result" in result.coverage.reason
    assert exact.items[0].record_ref == "claim:claim-2"
    assert exact.items[0].exact_score == 100


def test_query_index_includes_context_topic_and_session_special_paths(tmp_path):
    from brain.v5.workspace import bind_session, create_context, create_topic

    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    assert (ws.root / "indexes").is_dir()
    create_context(ws, "formal-theory", title="Formal Theory")
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum Gravity")
    bind_session(ws, "s1", topic_id="qg", context_id="formal-theory")

    report = build_query_index(ws)
    loaded = load_query_index(ws)

    assert report.manifest.family_counts == {"contexts": 1, "sessions": 1, "topics": 1}
    assert loaded.record_refs == ("context:formal-theory", "session:s1", "topic:qg")
    assert (ws.root / "indexes").is_dir()


def test_query_index_load_rejects_tampered_derived_documents(tmp_path):
    ws = _seed_index_workspace(tmp_path, ["claim", "source"])
    report = build_query_index(ws)
    path = ws.root / "indexes" / report.manifest.document_file
    documents = json.loads(path.read_text(encoding="utf-8"))
    documents[0]["title"] = "tampered"
    path.write_text(json.dumps(documents), encoding="utf-8")

    with pytest.raises(IndexIntegrityError, match="manifest content hash"):
        load_query_index(ws)


def test_query_index_watermark_accounts_for_malformed_canonical_files(tmp_path):
    from brain.v5.markdown import write_md

    ws = _seed_index_workspace(tmp_path, ["claim"])
    write_md(
        ws.registry_dir("claims") / "bad.md",
        {"topic_id": "topic-1", "kind": "claim"},
        "# Missing id\n",
    )

    report = build_query_index(ws)

    assert report.malformed_count == 1
    assert report.manifest.canonical_watermark == current_canonical_watermark(ws)
def test_lexical_terms_preserve_identifiers_and_add_natural_language_components():
    from brain.v5.query_index import lexical_terms

    terms = set(lexical_terms("target-spin-chain fit_inverse_size LibRPA.GW"))

    assert "target-spin-chain" in terms
    assert {"target", "spin", "chain"}.issubset(terms)
    assert "fit_inverse_size" in terms
    assert {"fit", "inverse", "size"}.issubset(terms)
    assert "librpa.gw" in terms
    assert {"librpa", "gw"}.issubset(terms)


def test_index_freshness_includes_index_schema_version(tmp_path):
    from dataclasses import replace

    ws = _seed_index_workspace(tmp_path, ["claim", "source"])
    report = build_query_index(ws)

    assert report.manifest.index_schema_version == INDEX_SCHEMA_VERSION
    assert query_index_is_fresh(ws, report.manifest) is True
    assert query_index_is_fresh(
        ws,
        replace(report.manifest, index_schema_version=INDEX_SCHEMA_VERSION - 1),
    ) is False
