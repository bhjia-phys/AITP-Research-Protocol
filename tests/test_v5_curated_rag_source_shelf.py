from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


def _drop_fields(value, names):
    if isinstance(value, dict):
        for key in list(value):
            if key in names:
                value.pop(key)
            else:
                _drop_fields(value[key], names)
    elif isinstance(value, list):
        for item in value:
            _drop_fields(item, names)


def _strip_named_shelf_fields(value):
    if isinstance(value, dict):
        for key in list(value):
            if "source_shelf" in str(key) or "source_passage" in str(key):
                value.pop(key)
            else:
                _strip_named_shelf_fields(value[key])
    elif isinstance(value, list):
        for item in value:
            _strip_named_shelf_fields(item)


def _built_shelf(tmp_path):
    from brain.v5.source_shelf import build_source_shelf
    from tests.test_v5_source_shelf import (
        PHYSICS_NOTE,
        _acquired_asset,
        _request,
        _setup_topic,
    )

    ws = _setup_topic(tmp_path)
    asset, blob, location = _acquired_asset(
        ws,
        name="curated-rag-adapter",
        content=PHYSICS_NOTE.encode("utf-8"),
    )
    source_ref = f"source_asset:{asset.asset_id}"
    report = build_source_shelf(ws, _request(source_ref))
    return ws, report, source_ref, blob, location


def test_curated_rag_catalog_adapts_exact_source_shelf_generation(tmp_path):
    from brain.v5.curated_rag_contracts import (
        require_valid_curated_rag_corpus,
        validate_curated_rag_corpus,
    )
    from brain.v5.curated_rag_corpus import curated_rag_corpus
    from brain.v5.query_index import current_canonical_watermark

    ws, report, source_ref, _blob, location = _built_shelf(tmp_path)
    before = current_canonical_watermark(ws)

    catalog = curated_rag_corpus(
        ws,
        source_shelf_generation=report.manifest.generation,
        topic_id="qg",
    )

    assert require_valid_curated_rag_corpus(catalog, base=ws) == catalog
    assert not validate_curated_rag_corpus(catalog).ok
    assert catalog["truth_source"] == "canonical_source_records_via_source_shelf"
    assert catalog["corpus_id"].endswith(report.manifest.generation)
    assert catalog["document_count"] == len(report.manifest.source_pins) == 1
    assert catalog["chunk_count"] == len(report.shelf.passages) > 0
    assert catalog["index_policy"]["active_index_mode"] == "lexical_source_shelf"
    assert catalog["index_policy"]["derived_from"] == "source_shelf_generation"
    assert catalog["index_policy"]["source_shelf_generation"] == report.manifest.generation
    assert catalog["index_policy"]["source_shelf_topic_id"] == "qg"
    expected_manifest = json.loads(json.dumps(asdict(report.manifest)))
    assert catalog["index_policy"]["source_shelf_manifest"] == expected_manifest
    assert catalog["index_policy"]["requested_source_asset_refs"] == [source_ref]
    assert catalog["index_policy"]["indexed_source_asset_refs"] == [source_ref]
    assert catalog["index_policy"]["source_shelf_issues"] == []

    document = catalog["documents"][0]
    assert document["version_anchor"]["source_shelf_generation"] == report.manifest.generation
    assert document["version_anchor"]["source_asset_ref"] == source_ref
    assert document["version_anchor"]["source_content_hash"] == report.manifest.source_pins[0].content_hash
    assert document["version_anchor"]["source_location_pins"][0]["record_ref"] == (
        f"reference_location:{location.location_id}"
    )
    assert {chunk["anchor"]["source_passage_id"] for chunk in catalog["chunks"]} == {
        passage.passage_id for passage in report.shelf.passages
    }
    assert all(chunk["orientation_only"] for chunk in catalog["chunks"])
    assert all(not chunk["can_update_claim_trust"] for chunk in catalog["chunks"])
    assert current_canonical_watermark(ws) == before
    assert not (ws.root / "curated_rag" / "corpus.json").exists()


def test_curated_rag_source_shelf_search_and_chunk_preserve_exact_provenance(tmp_path):
    from brain.v5.curated_rag_contracts import (
        require_valid_curated_rag_chunk,
        require_valid_curated_rag_search_result,
    )
    from brain.v5.curated_rag_corpus import (
        read_curated_rag_chunk,
        search_curated_rag_corpus,
    )

    ws, report, source_ref, _blob, location = _built_shelf(tmp_path)
    generation = report.manifest.generation
    search = search_curated_rag_corpus(
        "generalized entropy assumption caveat",
        base=ws,
        limit=3,
        source_shelf_generation=generation,
        topic_id="qg",
    )

    assert require_valid_curated_rag_search_result(search, base=ws) == search
    assert 0 < search["result_count"] <= 3
    assert search["index_mode"] == "lexical_source_shelf"
    assert search["source_shelf_generation"] == generation
    assert search["coverage"]["requested_source_asset_refs"] == [source_ref]
    assert search["coverage"]["indexed_source_asset_refs"] == [source_ref]
    assert search["coverage"]["incomplete"] is False
    assert search["can_claim_no_result"] is False
    first = search["results"][0]
    assert first["anchor"]["source_asset_ref"] == source_ref
    assert first["anchor"]["source_content_hash"] == report.manifest.source_pins[0].content_hash
    assert first["anchor"]["source_record_content_hash"] == (
        report.manifest.source_pins[0].record_content_hash
    )
    assert first["anchor"]["source_record_revision"] == (
        report.manifest.source_pins[0].record_revision
    )
    assert f"reference_location:{location.location_id}" in first["anchor"][
        "source_location_refs"
    ]
    assert first["anchor"]["source_location_pins"][0]["content_hash"] == (
        report.manifest.source_pins[0].source_location_pins[0].content_hash
    )

    chunk = read_curated_rag_chunk(
        first["chunk_id"],
        base=ws,
        source_shelf_generation=generation,
        topic_id="qg",
    )
    assert require_valid_curated_rag_chunk(chunk, base=ws) == chunk
    assert chunk["truth_source"] == "canonical_source_records_via_source_shelf"
    assert chunk["source_shelf_generation"] == generation
    assert chunk["chunk"]["anchor"] == first["anchor"]
    assert chunk["lookup_creates_records"] is False
    assert chunk["can_update_claim_trust"] is False

    no_match = search_curated_rag_corpus(
        "term-that-does-not-occur-anywhere",
        base=ws,
        source_shelf_generation=generation,
        topic_id="qg",
    )
    assert no_match["result_count"] == 0
    assert no_match["can_claim_no_result"] is False


def test_curated_rag_source_shelf_adapter_rejects_wrong_topic_and_stale_bytes(tmp_path):
    from brain.v5.curated_rag_corpus import curated_rag_corpus, read_curated_rag_chunk
    from brain.v5.source_shelf_models import SourceShelfStaleError

    ws, report, _source_ref, blob, _location = _built_shelf(tmp_path)
    generation = report.manifest.generation
    catalog = curated_rag_corpus(
        ws,
        source_shelf_generation=generation,
        topic_id="qg",
    )
    chunk_id = catalog["chunks"][0]["chunk_id"]

    with pytest.raises(ValueError, match="topic_id.*required"):
        curated_rag_corpus(
            ws,
            source_shelf_generation=generation,
        )

    with pytest.raises(ValueError, match="topic"):
        curated_rag_corpus(
            ws,
            source_shelf_generation=generation,
            topic_id="foreign-topic",
        )

    blob.write_bytes(b"changed after source shelf publication")
    with pytest.raises(SourceShelfStaleError):
        read_curated_rag_chunk(
            chunk_id,
            base=ws,
            source_shelf_generation=generation,
            topic_id="qg",
        )


def test_source_shelf_rag_helpers_are_not_public_bypass_surfaces():
    import brain.v5.curated_rag_source_shelf as adapter

    assert not hasattr(adapter, "source_shelf_curated_rag_catalog")
    assert not hasattr(adapter, "search_source_shelf_curated_rag")
    assert not hasattr(adapter, "read_source_shelf_curated_rag_chunk")


def test_legacy_curated_rag_import_does_not_require_pdf_stack():
    code = textwrap.dedent(
        """
        import importlib.abc
        import sys

        class BlockPypdf(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname == "pypdf" or fullname.startswith("pypdf."):
                    raise ModuleNotFoundError("pypdf blocked by compatibility test")
                return None

        sys.meta_path.insert(0, BlockPypdf())
        from brain.v5.curated_rag_corpus import curated_rag_corpus
        assert curated_rag_corpus()["kind"] == "curated_rag_corpus"
        """
    )

    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(Path(__file__).resolve().parents[1]),
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


def test_source_shelf_rag_rejects_unbounded_passage_work(tmp_path, monkeypatch):
    import brain.v5.curated_rag_source_shelf as adapter
    from brain.v5.curated_rag_corpus import curated_rag_corpus

    ws, report, _source_ref, _blob, _location = _built_shelf(tmp_path)
    monkeypatch.setattr(adapter, "_MAX_PASSAGES", 0, raising=False)
    monkeypatch.setattr(
        adapter,
        "load_source_shelf",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("full shelf load must occur after budget preflight")
        ),
    )

    with pytest.raises(ValueError, match="bounded passage budget"):
        curated_rag_corpus(
            ws,
            source_shelf_generation=report.manifest.generation,
            topic_id="qg",
        )


def test_source_shelf_rag_rejects_unbounded_text_bytes(tmp_path, monkeypatch):
    import brain.v5.curated_rag_source_shelf as adapter
    from brain.v5.curated_rag_corpus import curated_rag_corpus

    ws, report, _source_ref, _blob, _location = _built_shelf(tmp_path)
    monkeypatch.setattr(adapter, "_MAX_TEXT_BYTES", 0)

    with pytest.raises(ValueError, match="bounded text-byte budget"):
        curated_rag_corpus(
            ws,
            source_shelf_generation=report.manifest.generation,
            topic_id="qg",
        )


def test_source_shelf_rag_bounds_source_bytes_before_blob_read(tmp_path, monkeypatch):
    import brain.v5.source_shelf as source_shelf
    from brain.v5.curated_rag_corpus import curated_rag_corpus
    from brain.v5.source_shelf_models import SourceShelfStaleError

    ws, report, _source_ref, _blob, _location = _built_shelf(tmp_path)
    monkeypatch.setattr(source_shelf, "_MAX_SOURCE_BYTES", 0)
    monkeypatch.setattr(
        source_shelf,
        "read_bounded_bytes",
        lambda _path, _limit: (_ for _ in ()).throw(
            AssertionError("oversized source blob must not be read")
        ),
    )

    with pytest.raises(SourceShelfStaleError, match="source_blob_too_large"):
        curated_rag_corpus(
            ws,
            source_shelf_generation=report.manifest.generation,
            topic_id="qg",
        )


def test_source_shelf_rag_rejects_source_that_grows_after_stat(tmp_path, monkeypatch):
    import brain.v5.source_shelf as source_shelf
    from brain.v5.curated_rag_corpus import curated_rag_corpus
    from brain.v5.source_shelf_models import SourceShelfStaleError

    ws, report, _source_ref, _blob, _location = _built_shelf(tmp_path)
    monkeypatch.setattr(source_shelf, "read_bounded_bytes", lambda _path, _limit: None)

    with pytest.raises(SourceShelfStaleError, match="source_blob_too_large"):
        curated_rag_corpus(
            ws,
            source_shelf_generation=report.manifest.generation,
            topic_id="qg",
        )


def test_bounded_source_reader_never_returns_oversized_bytes(tmp_path):
    from brain.v5.source_shelf_bounded_io import read_bounded_bytes

    source = tmp_path / "growing-source.bin"
    source.write_bytes(b"abcdef")

    assert read_bounded_bytes(source, 4, chunk_size=2) is None
    assert read_bounded_bytes(source, 6, chunk_size=2) == b"abcdef"


def test_curated_rag_source_shelf_adapter_reports_unindexed_resolved_source(tmp_path):
    from brain.v5.curated_rag_contracts import require_valid_curated_rag_corpus
    from brain.v5.curated_rag_corpus import curated_rag_corpus, search_curated_rag_corpus
    from brain.v5.source_shelf import build_source_shelf
    from tests.test_v5_source_shelf import _acquired_asset, _request, _setup_topic

    ws = _setup_topic(tmp_path)
    asset, _blob, _location = _acquired_asset(
        ws,
        name="unsupported-rag-source",
        content=b"opaque source bytes",
        suffix=".bin",
    )
    source_ref = f"source_asset:{asset.asset_id}"
    report = build_source_shelf(ws, _request(source_ref))
    catalog = curated_rag_corpus(
        ws,
        source_shelf_generation=report.manifest.generation,
        topic_id="qg",
    )

    assert require_valid_curated_rag_corpus(catalog, base=ws) == catalog
    assert catalog["document_count"] == 0
    assert catalog["chunk_count"] == 0
    policy = catalog["index_policy"]
    assert policy["requested_source_asset_refs"] == [source_ref]
    assert policy["resolved_source_asset_refs"] == [source_ref]
    assert policy["indexed_source_asset_refs"] == []
    assert policy["unindexed_source_asset_refs"] == [source_ref]
    assert policy["source_shelf_incomplete_coverage"] is True
    assert policy["source_shelf_issues"][0]["code"] == "unsupported_source_format"

    search = search_curated_rag_corpus(
        "opaque source",
        base=ws,
        source_shelf_generation=report.manifest.generation,
        topic_id="qg",
    )
    assert search["result_count"] == 0
    assert search["coverage"]["unindexed_source_asset_refs"] == [source_ref]
    assert search["coverage"]["incomplete"] is True
    assert search["can_claim_no_result"] is False


def test_curated_rag_source_shelf_excludes_passages_without_exact_location(tmp_path):
    from brain.v5.curated_rag_contracts import require_valid_curated_rag_corpus
    from brain.v5.curated_rag_corpus import curated_rag_corpus, search_curated_rag_corpus
    from brain.v5.source_shelf import build_source_shelf
    from tests.test_v5_source_shelf import (
        PHYSICS_NOTE,
        _acquired_asset,
        _request,
        _setup_topic,
    )

    ws = _setup_topic(tmp_path)
    asset, _blob, _location = _acquired_asset(
        ws,
        name="rag-source-without-location",
        content=PHYSICS_NOTE.encode("utf-8"),
        add_location=False,
    )
    source_ref = f"source_asset:{asset.asset_id}"
    report = build_source_shelf(ws, _request(source_ref))
    catalog = curated_rag_corpus(
        ws,
        source_shelf_generation=report.manifest.generation,
        topic_id="qg",
    )

    assert require_valid_curated_rag_corpus(catalog, base=ws) == catalog
    assert catalog["document_count"] == 0
    assert catalog["chunk_count"] == 0
    assert catalog["index_policy"]["indexed_source_asset_refs"] == []
    assert catalog["index_policy"]["unindexed_source_asset_refs"] == [source_ref]
    assert {issue["code"] for issue in catalog["index_policy"]["source_shelf_issues"]} == {
        "missing_source_location"
    }
    search = search_curated_rag_corpus(
        "generalized entropy",
        base=ws,
        source_shelf_generation=report.manifest.generation,
        topic_id="qg",
    )
    assert search["result_count"] == 0
    assert search["can_claim_no_result"] is False


def test_curated_rag_source_shelf_retrieval_contract_binds_coverage_and_document(tmp_path):
    from brain.v5.curated_rag_contracts import (
        validate_curated_rag_chunk,
        validate_curated_rag_search_result,
    )
    from brain.v5.curated_rag_corpus import (
        read_curated_rag_chunk,
        search_curated_rag_corpus,
    )
    from brain.v5.source_shelf_storage import hash_json, source_passage_id

    ws, report, _source_ref, _blob, _location = _built_shelf(tmp_path)
    generation = report.manifest.generation
    search = search_curated_rag_corpus(
        "generalized entropy",
        base=ws,
        source_shelf_generation=generation,
        topic_id="qg",
    )

    tampered_search = deepcopy(search)
    tampered_search["coverage"]["indexed_source_asset_refs"] = []
    assert not validate_curated_rag_search_result(tampered_search, base=ws).ok

    tampered_search = deepcopy(search)
    tampered_search["index_mode"] = "lexical_file_backed"
    assert not validate_curated_rag_search_result(tampered_search, base=ws).ok

    stripped_search = deepcopy(search)
    _drop_fields(
        stripped_search,
        {"source_shelf_generation", "source_shelf_topic_id", "source_shelf_manifest"},
    )
    stripped_search["corpus_id"] = "forged.file-backed.corpus"
    stripped_search["results"][0]["text"] += " stripped-marker forgery"
    assert not validate_curated_rag_search_result(stripped_search).ok

    relabeled_search = deepcopy(search)
    _strip_named_shelf_fields(relabeled_search)
    relabeled_search["index_mode"] = "lexical_file_backed"
    relabeled_search["corpus_id"] = "forged.file-backed.corpus"
    relabeled_search["results"][0]["text"] += " relabeled shelf forgery"
    assert not validate_curated_rag_search_result(relabeled_search).ok

    tampered_search = deepcopy(search)
    tampered_search["results"][0]["text"] += " altered after retrieval"
    assert not validate_curated_rag_search_result(tampered_search, base=ws).ok

    tampered_search = deepcopy(search)
    result = tampered_search["results"][0]
    result["text"] += " coherently rehashed"
    result["anchor"]["text_hash"] = hashlib.sha256(
        result["text"].encode("utf-8")
    ).hexdigest()
    result["content_hash"] = f"sha256:{result['anchor']['text_hash']}"
    assert not validate_curated_rag_search_result(tampered_search, base=ws).ok

    chunk = read_curated_rag_chunk(
        search["results"][0]["chunk_id"],
        base=ws,
        source_shelf_generation=generation,
        topic_id="qg",
    )
    tampered_chunk = deepcopy(chunk)
    replacement_hash = "0" * 64
    tampered_chunk["document"]["version_anchor"][
        "source_content_hash"
    ] = replacement_hash
    tampered_chunk["document"]["content_hash"] = f"sha256:{replacement_hash}"
    tampered_chunk["chunk"]["anchor"]["source_content_hash"] = replacement_hash
    assert not validate_curated_rag_chunk(tampered_chunk, base=ws).ok

    tampered_chunk = deepcopy(chunk)
    tampered_chunk["index_mode"] = "lexical_file_backed"
    assert not validate_curated_rag_chunk(tampered_chunk, base=ws).ok

    stripped_chunk = deepcopy(chunk)
    _drop_fields(
        stripped_chunk,
        {"source_shelf_generation", "source_shelf_topic_id", "source_shelf_manifest"},
    )
    stripped_chunk["truth_source"] = "curated_rag_chunk_manifest"
    stripped_chunk["corpus_id"] = "forged.file-backed.corpus"
    stripped_chunk["chunk"]["text"] += " stripped-marker forgery"
    assert not validate_curated_rag_chunk(stripped_chunk).ok

    relabeled_chunk = deepcopy(chunk)
    _strip_named_shelf_fields(relabeled_chunk)
    relabeled_chunk["index_mode"] = "lexical_file_backed"
    relabeled_chunk["truth_source"] = "curated_rag_chunk_manifest"
    relabeled_chunk["corpus_id"] = "forged.file-backed.corpus"
    relabeled_chunk["chunk"]["text"] += " relabeled shelf forgery"
    assert not validate_curated_rag_chunk(relabeled_chunk).ok

    tampered_chunk = deepcopy(chunk)
    item = tampered_chunk["chunk"]
    anchor = item["anchor"]
    item["text"] += " fully coherent forged passage"
    anchor["text_hash"] = hashlib.sha256(item["text"].encode("utf-8")).hexdigest()
    item["content_hash"] = f"sha256:{anchor['text_hash']}"
    anchor["source_passage_id"] = source_passage_id(
        source_asset_ref=anchor["source_asset_ref"],
        source_content_hash=anchor["source_content_hash"],
        page_start=anchor["page_start"],
        page_end=anchor["page_end"],
        section=anchor["section"],
        ordinal=anchor["source_passage_ordinal"],
        text_hash=anchor["text_hash"],
    )
    assert not validate_curated_rag_chunk(tampered_chunk, base=ws).ok

    tampered_chunk = deepcopy(chunk)
    tampered_chunk["chunk"]["anchor"]["source_location_refs"] = [
        "reference_location:invented"
    ]
    assert not validate_curated_rag_chunk(tampered_chunk, base=ws).ok

    tampered_chunk = deepcopy(chunk)
    tampered_chunk["coverage"]["source_shelf_passage_count"] += 1
    assert not validate_curated_rag_chunk(tampered_chunk, base=ws).ok

    tampered_chunk = deepcopy(chunk)
    tampered_chunk["coverage"]["indexed_passage_count"] += 1
    assert not validate_curated_rag_chunk(tampered_chunk, base=ws).ok

    tampered_chunk = deepcopy(chunk)
    tampered_chunk["coverage"]["indexed_passage_count"] += 1
    coverage_basis = {
        key: value
        for key, value in tampered_chunk["coverage"].items()
        if key != "coverage_hash"
    }
    tampered_chunk["coverage"]["coverage_hash"] = hash_json(coverage_basis)
    assert not validate_curated_rag_chunk(tampered_chunk, base=ws).ok


def test_curated_rag_contract_rejects_tampered_source_shelf_provenance(tmp_path):
    from brain.v5.curated_rag_contracts import validate_curated_rag_corpus
    from brain.v5.curated_rag_corpus import curated_rag_corpus

    ws, report, _source_ref, _blob, _location = _built_shelf(tmp_path)
    catalog = curated_rag_corpus(
        ws,
        source_shelf_generation=report.manifest.generation,
        topic_id="qg",
    )

    tampered = deepcopy(catalog)
    tampered["index_policy"]["source_shelf_generation"] = "0" * 64
    assert not validate_curated_rag_corpus(tampered, base=ws).ok

    tampered = deepcopy(catalog)
    tampered["document_count"] = True
    assert not validate_curated_rag_corpus(tampered, base=ws).ok

    stripped = deepcopy(catalog)
    _drop_fields(
        stripped,
        {"source_shelf_generation", "source_shelf_topic_id", "source_shelf_manifest"},
    )
    stripped["truth_source"] = "curated_rag_corpus_catalog"
    stripped["corpus_id"] = "forged.file-backed.corpus"
    stripped["chunks"][0]["text"] += " stripped-marker forgery"
    assert not validate_curated_rag_corpus(stripped).ok

    relabeled = deepcopy(catalog)
    _strip_named_shelf_fields(relabeled)
    relabeled["truth_source"] = "curated_rag_corpus_catalog"
    relabeled["corpus_id"] = "forged.file-backed.corpus"
    relabeled["index_policy"].update(
        {
            "active_index_mode": "lexical_file_backed",
            "supported_index_modes": ["lexical_file_backed"],
            "derived_from": "curated_rag_chunk_manifest",
            "index_source": "file_backed_corpus_manifest",
            "manifest_hash": "relabeled-source-shelf",
            "index_status": "derived_in_memory",
        }
    )
    relabeled["chunks"][0]["text"] += " relabeled shelf forgery"
    assert not validate_curated_rag_corpus(relabeled).ok

    tampered = deepcopy(catalog)
    tampered["truth_source"] = "curated_rag_corpus_catalog"
    tampered["index_policy"].update(
        {
            "active_index_mode": "lexical_file_backed",
            "supported_index_modes": ["lexical_file_backed"],
            "derived_from": "curated_rag_chunk_manifest",
            "index_source": "file_backed_corpus_manifest",
            "manifest_hash": "coherent-mode-downgrade",
            "index_status": "derived_in_memory",
        }
    )
    assert not validate_curated_rag_corpus(tampered, base=ws).ok

    tampered = deepcopy(catalog)
    tampered["index_policy"].pop("source_shelf_manifest")
    assert not validate_curated_rag_corpus(tampered, base=ws).ok

    tampered = deepcopy(catalog)
    tampered["chunks"][0]["anchor"]["source_content_hash"] = "0" * 64
    assert not validate_curated_rag_corpus(tampered, base=ws).ok

    tampered = deepcopy(catalog)
    tampered["documents"][0]["version_anchor"]["source_asset_ref"] = {}
    assert not validate_curated_rag_corpus(tampered, base=ws).ok

    tampered = deepcopy(catalog)
    replacement_hash = "0" * 64
    for document in tampered["documents"]:
        document["version_anchor"]["source_content_hash"] = replacement_hash
        document["content_hash"] = f"sha256:{replacement_hash}"
    for chunk in tampered["chunks"]:
        chunk["anchor"]["source_content_hash"] = replacement_hash
    assert not validate_curated_rag_corpus(tampered, base=ws).ok

    tampered = deepcopy(catalog)
    tampered["index_policy"]["resolved_source_asset_refs"] = []
    assert not validate_curated_rag_corpus(tampered, base=ws).ok

    tampered = deepcopy(catalog)
    tampered["index_policy"]["source_shelf_issue_count"] = False
    assert not validate_curated_rag_corpus(tampered, base=ws).ok

    tampered = deepcopy(catalog)
    tampered["index_policy"]["source_shelf_issues"] = None
    assert not validate_curated_rag_corpus(tampered, base=ws).ok

    tampered = deepcopy(catalog)
    tampered["index_policy"]["requested_source_asset_refs"][0] = {}
    assert not validate_curated_rag_corpus(tampered, base=ws).ok

    tampered = deepcopy(catalog)
    tampered["index_policy"]["source_shelf_schema_version"] = True
    assert not validate_curated_rag_corpus(tampered, base=ws).ok

    tampered = deepcopy(catalog)
    invented = "source_asset:invented-without-passage"
    for key in (
        "requested_source_asset_refs",
        "resolved_source_asset_refs",
        "indexed_source_asset_refs",
    ):
        tampered["index_policy"][key].append(invented)
    assert not validate_curated_rag_corpus(tampered, base=ws).ok


def test_curated_rag_contract_requires_json_without_query_false_positive():
    from brain.v5.curated_rag_contracts import validate_curated_rag_search_result
    from brain.v5.curated_rag_corpus import search_curated_rag_corpus

    legacy = search_curated_rag_corpus("lexical_source_shelf")
    assert validate_curated_rag_search_result(legacy).ok

    python_only = deepcopy(legacy)
    python_only["extra"] = ("lexical_source_shelf",)
    assert not validate_curated_rag_search_result(python_only).ok

    cyclic = deepcopy(legacy)
    cyclic["extra"] = []
    cyclic["extra"].append(cyclic["extra"])
    assert not validate_curated_rag_search_result(cyclic).ok

    nested_tags = deepcopy(legacy)
    nested_tags["results"][0]["tags"] = [["source-shelf"]]
    assert not validate_curated_rag_search_result(nested_tags).ok

    class ExplodingDict(dict):
        def items(self):
            raise RuntimeError("must not inspect a rejected mapping subclass")

    assert not validate_curated_rag_search_result(ExplodingDict(legacy)).ok


def test_legacy_file_backed_source_shelf_tag_is_not_authority_identity(tmp_path):
    from brain.v5.curated_rag_contracts import (
        validate_curated_rag_corpus,
        validate_curated_rag_search_result,
    )
    from brain.v5.curated_rag_corpus import (
        curated_rag_corpus,
        ingest_curated_rag_corpus,
        search_curated_rag_corpus,
    )
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    note = tmp_path / "legacy-source-shelf-tag.md"
    note.write_text("A legacy file-backed note with user-controlled tags.", encoding="utf-8")
    ingest_curated_rag_corpus(
        ws,
        paths=[str(note)],
        corpus_id="aitp.curated.legacy_tag_test.v1",
        tags=["source-shelf", "adapter-review"],
    )

    catalog = curated_rag_corpus(ws)
    search = search_curated_rag_corpus("legacy file backed note", base=ws)
    assert validate_curated_rag_corpus(catalog).ok
    assert validate_curated_rag_search_result(search).ok
