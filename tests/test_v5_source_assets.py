from __future__ import annotations


PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


def test_source_asset_record_is_canonical_orientation_asset(tmp_path):
    import hashlib

    from brain.v5.contracts import validate_source_asset_record
    from brain.v5.mcp_tools import aitp_v5_register_source_asset
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.source_assets import register_source_asset, source_asset_payload
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="theory", title="Quantum gravity algebra")
    lecture = tmp_path / "lecture.md"
    lecture.write_text("von Neumann algebra notes\n", encoding="utf-8")
    expected_hash = hashlib.sha256(lecture.read_bytes()).hexdigest()

    record = register_source_asset(
        ws,
        topic_id="qg",
        claim_id="claim-qg-mipt",
        asset_type="lecture",
        uri=str(lecture),
        title="Operator algebra lecture notes",
        version_anchor={"local_revision": "draft-1"},
        source_kind="local_notes",
        summary="Raw lecture notes used for definition backtrace.",
        source_refs=["note:operator-algebra"],
        linked_records={"claim_id": "claim-qg-mipt"},
    )
    payload = source_asset_payload(record)

    assert payload["kind"] == "source_asset"
    assert payload["content_hash"] == expected_hash
    assert payload["hash_algorithm"] == "sha256"
    assert payload["metadata"]["duplicate_hash_diagnostics"]["duplicate_hash"] is False
    assert payload["orientation_only"] is True
    assert payload["can_update_claim_trust"] is False
    assert validate_source_asset_record(payload).ok is True
    assert require_valid_public_surface("source_asset_record", payload) == payload

    mcp_payload = aitp_v5_register_source_asset(
        str(tmp_path),
        topic_id="qg",
        claim_id="claim-qg-mipt",
        asset_type="paper",
        uri="arxiv:2601.00001",
        title="Algebraic observer source",
        version_anchor={"arxiv_version": "v1"},
        source_kind="literature",
        summary="Raw paper identity for source backtrace.",
    )

    assert mcp_payload["kind"] == "source_asset"
    assert mcp_payload["asset_type"] == "paper"
    assert mcp_payload["orientation_only"] is True
    assert mcp_payload["can_update_claim_trust"] is False
    assert not list((tmp_path / ".aitp" / "source_blobs").rglob("original.pdf"))

    duplicate_file = tmp_path / "lecture-copy.md"
    duplicate_file.write_text("von Neumann algebra notes\n", encoding="utf-8")
    duplicate = register_source_asset(
        ws,
        topic_id="qg",
        claim_id="claim-qg-mipt",
        asset_type="lecture",
        uri=str(duplicate_file),
        title="Operator algebra lecture notes copy",
        source_kind="local_notes",
    )

    diagnostics = duplicate.metadata["duplicate_hash_diagnostics"]
    assert diagnostics["duplicate_hash"] is True
    assert record.asset_id in diagnostics["duplicate_asset_ids"]


def test_cli_and_mcp_capture_source_asset_auto_from_local_file(tmp_path, capsys):
    import hashlib
    from pathlib import Path

    from brain.v5.mcp_tools import aitp_v5_capture_source_asset_auto
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="theory", title="Quantum gravity source stack")
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="The derivation depends on the local notes.",
        evidence_profile="source_backtrace",
        confidence_state="hypothesis",
        active_uncertainty="source file identity not captured",
    )
    source_file = tmp_path / "operator-algebra-notes.md"
    source_file.write_text("# Operator algebra notes\n\nDefinition backtrace.\n", encoding="utf-8")
    expected_hash = hashlib.sha256(source_file.read_bytes()).hexdigest()

    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "asset",
            "capture-auto",
            "--path",
            str(source_file),
            "--topic",
            "qg",
            "--claim",
            claim.claim_id,
            "--summary",
            "Local source notes for the derivation.",
        ],
        capsys,
    )
    mcp_payload = aitp_v5_capture_source_asset_auto(
        str(tmp_path),
        path=str(source_file),
        topic_id="qg",
        claim_id=claim.claim_id,
        title="Operator algebra notes",
    )
    copied_payload = aitp_v5_capture_source_asset_auto(
        str(tmp_path),
        path=str(source_file),
        topic_id="qg",
        claim_id=claim.claim_id,
        title="Operator algebra notes stored copy",
        copy_to_store=True,
    )

    assert payload["ok"] is True
    assert payload["kind"] == "source_asset"
    assert payload["asset_type"] == "note"
    assert payload["title"] == "operator algebra notes"
    assert payload["uri"].startswith("file://")
    assert payload["content_hash"] == expected_hash
    assert payload["hash_algorithm"] == "sha256"
    assert payload["source_kind"] == "local_file_auto"
    assert payload["metadata"]["capture_tool"] == "aitp_v5_capture_source_asset_auto"
    assert payload["metadata"]["size_bytes"] == source_file.stat().st_size
    assert payload["version_anchor"]["sha256"] == expected_hash
    assert payload["linked_records"]["claim_id"] == claim.claim_id
    assert payload["orientation_only"] is True
    assert payload["can_update_claim_trust"] is False
    assert mcp_payload["asset_id"].startswith("source-asset-qg-")
    assert mcp_payload["title"] == "Operator algebra notes"
    assert copied_payload["metadata"]["original_local_path"] == str(source_file.resolve())
    assert copied_payload["metadata"]["local_path"] != str(source_file.resolve())
    assert copied_payload["metadata"]["blob_path"].startswith("source_blobs/qg/")
    assert copied_payload["metadata"]["acquisition_status"] == "succeeded"
    assert copied_payload["metadata"]["acquisition_kind"] == "local_copy"
    assert Path(copied_payload["metadata"]["local_path"]).read_bytes() == source_file.read_bytes()


def test_acquire_pdf_source_asset_from_file_url_copies_into_topic_blob_store(tmp_path, capsys):
    import hashlib
    from pathlib import Path

    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="theory", title="Quantum gravity source stack")
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="The derivation depends on a local PDF.",
        evidence_profile="source_backtrace",
        confidence_state="hypothesis",
        active_uncertainty="PDF identity not captured",
    )
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(PDF_BYTES)
    expected_hash = hashlib.sha256(PDF_BYTES).hexdigest()

    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "asset",
            "acquire-pdf",
            "--url",
            pdf.resolve().as_uri(),
            "--topic",
            "qg",
            "--claim",
            claim.claim_id,
            "--title",
            "Local PDF Source",
            "--summary",
            "Acquired PDF for later text extraction.",
        ],
        capsys,
    )

    local_path = Path(payload["metadata"]["local_path"])
    assert payload["ok"] is True
    assert payload["kind"] == "source_asset"
    assert payload["asset_type"] == "paper"
    assert payload["uri"] == pdf.resolve().as_uri()
    assert payload["content_hash"] == expected_hash
    assert payload["hash_algorithm"] == "sha256"
    assert payload["metadata"]["acquisition_status"] == "succeeded"
    assert payload["metadata"]["acquisition_kind"] == "pdf"
    assert payload["metadata"]["source_scheme"] == "file"
    assert payload["metadata"]["source_local_path"] == str(pdf.resolve())
    assert payload["metadata"]["blob_path"].startswith("source_blobs/qg/")
    assert payload["metadata"]["mime_type"] == "application/pdf"
    assert payload["metadata"]["size_bytes"] == len(PDF_BYTES)
    assert local_path.exists()
    assert local_path.read_bytes() == PDF_BYTES
    assert local_path.name == "original.pdf"
    assert local_path.resolve().is_relative_to((tmp_path / ".aitp" / "source_blobs").resolve())
    assert payload["orientation_only"] is True
    assert payload["can_update_claim_trust"] is False


def test_acquire_arxiv_source_asset_uses_downloaded_pdf_bytes_without_network(tmp_path, monkeypatch):
    import hashlib
    from pathlib import Path

    import brain.v5.source_assets as source_assets
    from brain.v5.mcp_tools import aitp_v5_acquire_arxiv_source_asset
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="theory", title="Quantum gravity source stack")

    def fake_download(source_url, *, tmp_path, timeout_seconds, max_bytes):
        tmp_path.write_bytes(PDF_BYTES)
        return source_assets._PdfFetchResult(
            temp_path=tmp_path,
            requested_url=source_url,
            source_url=source_url,
            final_url=source_url,
            mime_type="application/pdf",
            http_status=200,
        )

    monkeypatch.setattr(source_assets, "_download_pdf_to_temp", fake_download)

    payload = aitp_v5_acquire_arxiv_source_asset(
        str(tmp_path),
        topic_id="qg",
        arxiv_id="https://arxiv.org/abs/2401.12345v1",
        title="Mock arXiv Paper",
        claim_id="claim-qg",
    )

    expected_hash = hashlib.sha256(PDF_BYTES).hexdigest()
    local_path = Path(payload["metadata"]["local_path"])
    assert payload["ok"] is True
    assert payload["uri"] == "https://arxiv.org/pdf/2401.12345v1.pdf"
    assert payload["content_hash"] == expected_hash
    assert payload["version_anchor"]["arxiv_id"] == "2401.12345v1"
    assert payload["version_anchor"]["sha256"] == expected_hash
    assert payload["metadata"]["arxiv_id"] == "2401.12345v1"
    assert payload["metadata"]["acquisition_kind"] == "arxiv_pdf"
    assert payload["metadata"]["http_status"] == 200
    assert local_path.read_bytes() == PDF_BYTES
    assert payload["orientation_only"] is True
    assert payload["can_update_claim_trust"] is False


def test_acquire_pdf_failure_records_honest_failed_source_asset(tmp_path, monkeypatch):
    import brain.v5.source_assets as source_assets
    from brain.v5.source_assets import acquire_pdf_source_asset
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="theory", title="Quantum gravity source stack")

    def failing_download(source_url, *, tmp_path, timeout_seconds, max_bytes):
        raise RuntimeError("mock download failure")

    monkeypatch.setattr(source_assets, "_download_pdf_to_temp", failing_download)

    record = acquire_pdf_source_asset(
        ws,
        topic_id="qg",
        url="https://example.org/paper.pdf",
        title="Unavailable PDF",
        claim_id="claim-qg",
    )

    assert record.content_hash == ""
    assert record.hash_algorithm == ""
    assert record.metadata["acquisition_status"] == "failed"
    assert "mock download failure" in record.metadata["failure_reason"]
    assert "local_path" not in record.metadata
    assert record.orientation_only is True
    assert record.can_update_claim_trust is False


def test_acquire_pdf_file_uri_outside_topics_root_is_failed_not_hashed(tmp_path):
    from brain.v5.source_assets import acquire_pdf_source_asset
    from brain.v5.workspace import create_topic, init_workspace

    base = tmp_path / "topics"
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(PDF_BYTES)
    ws = init_workspace(base)
    create_topic(ws, "qg", context_id="theory", title="Quantum gravity source stack")

    record = acquire_pdf_source_asset(
        ws,
        topic_id="qg",
        url=outside.resolve().as_uri(),
        title="Outside PDF",
        claim_id="claim-qg",
    )

    assert record.metadata["acquisition_status"] == "failed"
    assert "topics root" in record.metadata["failure_reason"]
    assert record.content_hash == ""
    assert record.hash_algorithm == ""
    assert "local_path" not in record.metadata


def test_acquire_pdf_does_not_overwrite_existing_different_blob_without_force(tmp_path):
    from pathlib import Path

    from brain.v5.source_assets import acquire_pdf_source_asset
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="theory", title="Quantum gravity source stack")
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(PDF_BYTES)

    first = acquire_pdf_source_asset(
        ws,
        topic_id="qg",
        url=pdf.resolve().as_uri(),
        title="Local PDF Source",
        claim_id="claim-qg",
    )
    blob_path = Path(first.metadata["local_path"])
    blob_path.write_bytes(b"%PDF-1.4\nchanged\n%%EOF\n")

    failed = acquire_pdf_source_asset(
        ws,
        topic_id="qg",
        url=pdf.resolve().as_uri(),
        title="Local PDF Source",
        claim_id="claim-qg",
    )
    assert failed.metadata["acquisition_status"] == "failed"
    assert "already exists with different content" in failed.metadata["failure_reason"]
    assert blob_path.read_bytes().startswith(b"%PDF-1.4\nchanged")

    refreshed = acquire_pdf_source_asset(
        ws,
        topic_id="qg",
        url=pdf.resolve().as_uri(),
        title="Local PDF Source",
        claim_id="claim-qg",
        force_refresh=True,
    )

    assert blob_path.read_bytes() == PDF_BYTES
    assert refreshed.metadata["acquisition_status"] == "succeeded"


def test_source_asset_contract_rejects_trust_mutation():
    from brain.v5.contracts import validate_source_asset_record

    payload = {
        "ok": True,
        "kind": "source_asset",
        "asset_id": "source-asset-bad",
        "topic_id": "qg",
        "asset_type": "paper",
        "uri": "arxiv:2601.00001",
        "title": "Bad trust mutation",
        "claim_id": "claim-qg",
        "label": "",
        "content_hash": "",
        "hash_algorithm": "",
        "version_anchor": {},
        "acquired_at": "",
        "source_kind": "literature",
        "summary": "",
        "source_refs": [],
        "artifact_ids": [],
        "code_state_ids": [],
        "reference_location_ids": [],
        "derived_from": [],
        "metadata": {},
        "linked_records": {},
        "orientation_only": False,
        "can_update_claim_trust": True,
    }

    result = validate_source_asset_record(payload)

    assert result.ok is False
    paths = {issue.path for issue in result.issues}
    assert "source_asset_record.orientation_only" in paths
    assert "source_asset_record.can_update_claim_trust" in paths


def test_source_asset_is_registered_for_native_mcp_and_runtime_entrypoints():
    from brain.v5.native_mcp import _TOOLS
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    assert "aitp_v5_register_source_asset" in _TOOLS
    assert "aitp_v5_capture_source_asset_auto" in _TOOLS
    assert "aitp_v5_acquire_pdf_source_asset" in _TOOLS
    assert "aitp_v5_acquire_arxiv_source_asset" in _TOOLS
    assert runtime_entrypoints()["register_source_asset"] == {
        "cli": "aitp-v5 asset register <args>",
        "mcp": "aitp_v5_register_source_asset",
        "surface": "source_asset_record",
    }
    assert runtime_entrypoints()["capture_source_asset_auto"] == {
        "cli": "aitp-v5 asset capture-auto <args>",
        "mcp": "aitp_v5_capture_source_asset_auto",
        "surface": "source_asset_record",
    }
    assert runtime_entrypoints()["acquire_pdf_source_asset"] == {
        "cli": "aitp-v5 asset acquire-pdf <args>",
        "mcp": "aitp_v5_acquire_pdf_source_asset",
        "surface": "source_asset_record",
    }
    assert runtime_entrypoints()["acquire_arxiv_source_asset"] == {
        "cli": "aitp-v5 asset acquire-arxiv <args>",
        "mcp": "aitp_v5_acquire_arxiv_source_asset",
        "surface": "source_asset_record",
    }
    assert validate_runtime_entrypoints() == []


def _invoke(argv, capsys):
    from brain.v5.cli import main

    assert main(argv) == 0
    return __import__("json").loads(capsys.readouterr().out)
