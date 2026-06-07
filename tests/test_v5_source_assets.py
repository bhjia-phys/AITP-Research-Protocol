from __future__ import annotations


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
    assert validate_runtime_entrypoints() == []


def _invoke(argv, capsys):
    from brain.v5.cli import main

    assert main(argv) == 0
    return __import__("json").loads(capsys.readouterr().out)
