from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import pytest


PHYSICS_NOTE = r"""# Semiclassical Setup

Nearby prose fixes the regime before the formal statements below.

Definition 1 (Generalized entropy). The quantity is
\[ S_{\rm gen}=A/(4G_N)+S_{\rm out}. \tag{2.1} \]

Symbols: $A$ is the area and $G_N$ is Newton's constant.

Assumption A1. The state is semiclassical near the candidate surface.

Theorem 2 (Island extremum). A stationary surface obeys $\delta S_{\rm gen}=0$.

Derivation step 1. Vary the area term while holding the asymptotic source fixed.

Figure 3: Competing extremal surfaces in the two saddles.

Caveat. The argument does not establish dominance beyond the stated regime.

Bibliography: [W1] Example Author, Example Result.
"""


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="source-shelf-test", host="pytest")


def _setup_topic(tmp_path: Path):
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum gravity")
    return ws


def _acquired_asset(
    ws,
    *,
    name: str,
    content: bytes,
    suffix: str = ".md",
    access_disposition: str = "open_access",
    storage_permission: str = "private_topic_store_authorized",
    add_location: bool = True,
):
    from brain.v5.references import record_reference_location
    from brain.v5.source_acquisition import (
        record_source_acquisition_decision,
        record_source_acquisition_receipt,
    )
    from brain.v5.source_asset_acquisition_bindings import source_acquisition_metadata
    from brain.v5.source_assets import register_source_asset

    blob = ws.source_blob_dir("qg", name) / f"original{suffix}"
    blob.parent.mkdir(parents=True, exist_ok=True)
    blob.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    canonical_uri = f"https://example.test/{name}{suffix}"
    now = datetime.now(UTC).isoformat()
    decision = record_source_acquisition_decision(
        ws,
        topic_id="qg",
        canonical_uri=canonical_uri,
        dedup_key=f"test:{name}",
        action="allow",
        policy_basis="test fixture",
        access_disposition=access_disposition,
        storage_permission=storage_permission,
        connector_id="local-test",
        collector_id="source-shelf-test",
        decided_at=now,
        actor=_actor(),
    )
    receipt = record_source_acquisition_receipt(
        ws,
        topic_id="qg",
        decision_ref=decision.pinned_ref,
        canonical_uri=canonical_uri,
        dedup_key=f"test:{name}",
        status="succeeded",
        byte_sha256=digest,
        hash_algorithm="sha256",
        byte_length=len(content),
        stored_uri=blob.resolve().as_uri(),
        connector_id="local-test",
        collector_id="source-shelf-test",
        acquired_at=now,
        errors=[],
        actor=_actor(),
    )
    metadata = {
        "local_path": str(blob.resolve()),
        "mime_type": "application/pdf" if suffix == ".pdf" else "text/markdown",
        **source_acquisition_metadata(
            decision,
            receipt,
            acquisition_state="acquired",
            eligible=True,
        ),
    }
    asset = register_source_asset(
        ws,
        topic_id="qg",
        asset_type="paper" if suffix == ".pdf" else "note",
        uri=canonical_uri,
        title=name,
        content_hash=digest,
        hash_algorithm="sha256",
        acquired_at=now,
        source_kind="test_fixture",
        metadata=metadata,
    )
    location = None
    if add_location:
        location = record_reference_location(
            ws,
            topic_id="qg",
            connector_id="local-test",
            location_type="paper" if suffix == ".pdf" else "note",
            uri=canonical_uri,
            label=name,
            source_ref=f"source_asset:{asset.asset_id}",
        )
    return asset, blob, location


def _request(*refs: str, max_passage_chars: int = 1600):
    from brain.v5.source_shelf import SourceShelfBuildRequest

    return SourceShelfBuildRequest(
        topic_id="qg",
        source_asset_refs=tuple(refs),
        curation_rationale="Recover exact formal statements for a bounded theory discussion.",
        max_passage_chars=max_passage_chars,
    )


def test_source_shelf_builds_deterministic_physics_aware_generation(tmp_path):
    from brain.v5.source_shelf import build_source_shelf, load_source_shelf

    ws = _setup_topic(tmp_path)
    asset, _blob, location = _acquired_asset(
        ws,
        name="island-note",
        content=PHYSICS_NOTE.encode("utf-8"),
    )
    ref = f"source_asset:{asset.asset_id}"

    first = build_source_shelf(ws, _request(ref))
    second = build_source_shelf(ws, _request(ref))
    loaded = load_source_shelf(ws, first.manifest.generation)

    assert first.manifest.generation == second.manifest.generation
    assert first.manifest.passage_count == len(first.shelf.passages) > 0
    assert first.manifest.source_pins[0].source_asset_ref == ref
    assert first.manifest.source_pins[0].content_hash == asset.content_hash
    assert first.manifest.source_pins[0].acquired_at == asset.acquired_at
    assert first.manifest.reader_version
    assert first.manifest.extractor_version
    assert first.incomplete_coverage is False
    assert first.issues == ()
    assert loaded == first.shelf
    assert all(p.orientation_only and not p.can_update_claim_trust for p in loaded.passages)
    assert all(
        f"reference_location:{location.location_id}" in p.source_location_refs
        for p in loaded.passages
    )

    joined = "\n".join(p.text for p in loaded.passages)
    for expected in (
        "Definition 1",
        "tag{2.1}",
        "Symbols:",
        "Assumption A1",
        "Theorem 2",
        "Derivation step 1",
        "Figure 3",
        "Caveat.",
        "Bibliography:",
        "Nearby prose",
    ):
        assert expected in joined
    kinds = {kind for passage in loaded.passages for kind in passage.anchor_kinds}
    assert {
        "definition",
        "equation",
        "symbols",
        "assumption",
        "theorem",
        "derivation_step",
        "figure_caption",
        "caveat",
        "bibliography",
    } <= kinds
    assert {p.section for p in loaded.passages} == {"Semiclassical Setup"}


def test_source_shelf_changed_canonical_source_creates_new_generation(tmp_path):
    from brain.v5.source_shelf import build_source_shelf

    ws = _setup_topic(tmp_path)
    first_asset, _first_blob, _ = _acquired_asset(
        ws,
        name="version-one",
        content=b"# Result\n\nDefinition 1. First version.\n",
    )
    second_asset, _second_blob, _ = _acquired_asset(
        ws,
        name="version-two",
        content=b"# Result\n\nDefinition 1. Corrected second version.\n",
    )

    first = build_source_shelf(ws, _request(f"source_asset:{first_asset.asset_id}"))
    second = build_source_shelf(ws, _request(f"source_asset:{second_asset.asset_id}"))

    assert first.manifest.generation != second.manifest.generation
    assert first.manifest.source_pins[0].content_hash != second.manifest.source_pins[0].content_hash


def test_source_shelf_reports_metadata_only_asset_without_reading_uri(tmp_path):
    from brain.v5.source_assets import register_source_asset
    from brain.v5.source_shelf import build_source_shelf

    ws = _setup_topic(tmp_path)
    asset = register_source_asset(
        ws,
        topic_id="qg",
        asset_type="paper",
        uri="https://example.test/metadata-only",
        title="Metadata only",
        metadata={
            "acquisition_state": "metadata_only",
            "shelf_eligible": False,
            "access_license_disposition": "not_checked",
            "storage_permission": "not_requested",
        },
    )

    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))

    assert report.shelf.passages == ()
    assert report.incomplete_coverage is True
    assert [issue.code for issue in report.issues] == ["source_not_shelf_eligible"]


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        ("missing", "source_blob_missing"),
        ("changed", "source_bytes_changed"),
        ("unsupported", "unsupported_source_format"),
        ("restricted", "source_access_restricted"),
    ],
)
def test_source_shelf_fails_closed_with_explicit_source_issue(tmp_path, mutation, expected_code):
    from brain.v5.source_shelf import build_source_shelf

    ws = _setup_topic(tmp_path)
    suffix = ".bin" if mutation == "unsupported" else ".md"
    access = "license_restricted" if mutation == "restricted" else "open_access"
    asset, blob, _ = _acquired_asset(
        ws,
        name=mutation,
        content=b"Definition 1. Exact bytes.\n",
        suffix=suffix,
        access_disposition=access,
    )
    if mutation == "missing":
        blob.unlink()
    elif mutation == "changed":
        blob.write_bytes(b"Definition 1. Mutated after acquisition.\n")

    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))

    assert report.shelf.passages == ()
    assert report.incomplete_coverage is True
    assert [issue.code for issue in report.issues] == [expected_code]


def test_source_shelf_rejects_encrypted_pdf(tmp_path):
    from pypdf import PdfWriter

    from brain.v5.source_shelf import build_source_shelf

    ws = _setup_topic(tmp_path)
    pdf_path = tmp_path / "encrypted.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.encrypt("secret")
    with pdf_path.open("wb") as handle:
        writer.write(handle)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="encrypted",
        content=pdf_path.read_bytes(),
        suffix=".pdf",
    )

    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))

    assert report.shelf.passages == ()
    assert [issue.code for issue in report.issues] == ["encrypted_source"]


def test_source_shelf_extracts_pdf_text_with_page_anchor(tmp_path):
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    from brain.v5.source_shelf import build_source_shelf

    ws = _setup_topic(tmp_path)
    pdf_path = tmp_path / "formal-result.pdf"
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {NameObject("/F1"): writer._add_object(font)}
            )
        }
    )
    stream = DecodedStreamObject()
    stream.set_data(
        b"BT /F1 12 Tf 72 700 Td "
        b"(Definition 7. PDF page anchor. Equation 4.2. Caveat. PDF extraction.) Tj ET"
    )
    page[NameObject("/Contents")] = writer._add_object(stream)
    with pdf_path.open("wb") as handle:
        writer.write(handle)
    asset, _blob, location = _acquired_asset(
        ws,
        name="formal-result",
        content=pdf_path.read_bytes(),
        suffix=".pdf",
    )

    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))

    assert report.incomplete_coverage is False
    assert len(report.shelf.passages) == 1
    passage = report.shelf.passages[0]
    assert passage.page_start == passage.page_end == 1
    assert "Definition 7" in passage.text
    assert "definition" in passage.anchor_kinds
    assert "equation" in passage.anchor_kinds
    assert "caveat" in passage.anchor_kinds
    assert passage.source_location_refs == (
        f"reference_location:{location.location_id}",
    )


def test_source_shelf_requires_exact_reference_location_but_retains_passage(tmp_path):
    from brain.v5.source_shelf import build_source_shelf

    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="unlocated",
        content=b"Definition 1. This source has no exact location record.\n",
        add_location=False,
    )

    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))

    assert report.shelf.passages
    assert report.incomplete_coverage is True
    assert [issue.code for issue in report.issues] == ["missing_source_location"]
    assert report.shelf.passages[0].source_location_refs == ()


def test_source_shelf_load_rejects_tampered_passage_component(tmp_path):
    from brain.v5.source_shelf import (
        SourceShelfIntegrityError,
        build_source_shelf,
        load_source_shelf,
    )

    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="tamper-check",
        content=b"Definition 1. Integrity matters.\n",
    )
    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))
    passage_path = (
        ws.root
        / "indexes"
        / "knowledge"
        / "source_shelf"
        / "generations"
        / report.manifest.generation
        / report.manifest.passage_file
    )
    passage_path.write_text("[]\n", encoding="utf-8")

    with pytest.raises(SourceShelfIntegrityError, match="component hash"):
        load_source_shelf(ws, report.manifest.generation)


def test_source_shelf_load_rejects_stale_source_bytes(tmp_path):
    from brain.v5.source_shelf import (
        SourceShelfStaleError,
        build_source_shelf,
        load_source_shelf,
    )

    ws = _setup_topic(tmp_path)
    asset, blob, _ = _acquired_asset(
        ws,
        name="stale-after-build",
        content=b"Definition 1. Initially receipted bytes.\n",
    )
    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))
    blob.write_bytes(b"Definition 1. Changed after shelf publication.\n")

    with pytest.raises(SourceShelfStaleError, match="source_bytes_changed"):
        load_source_shelf(ws, report.manifest.generation)


def test_source_shelf_load_rejects_manifest_trust_inflation(tmp_path):
    from brain.v5.source_shelf import (
        SourceShelfIntegrityError,
        build_source_shelf,
        load_source_shelf,
    )

    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="trust-flags",
        content=b"Definition 1. Derived context is orientation only.\n",
    )
    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))
    manifest_path = (
        ws.root
        / "indexes"
        / "knowledge"
        / "source_shelf"
        / "generations"
        / report.manifest.generation
        / "manifest.json"
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["can_update_claim_trust"] = True
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SourceShelfIntegrityError, match="trust boundary"):
        load_source_shelf(ws, report.manifest.generation)


def test_source_shelf_load_normalizes_malformed_manifest_diagnostic(tmp_path):
    from brain.v5.source_shelf import (
        SourceShelfIntegrityError,
        build_source_shelf,
        load_source_shelf,
    )

    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="malformed-manifest",
        content=b"Definition 1. Exact source pin.\n",
    )
    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))
    manifest_path = (
        ws.root
        / "indexes"
        / "knowledge"
        / "source_shelf"
        / "generations"
        / report.manifest.generation
        / "manifest.json"
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["source_pins"] = [0]
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SourceShelfIntegrityError, match="manifest is malformed"):
        load_source_shelf(ws, report.manifest.generation)


def test_source_shelf_public_types_are_json_serializable(tmp_path):
    from brain.v5.source_shelf import build_source_shelf

    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="serializable",
        content=b"Definition 1. Stable public records.\n",
    )
    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))

    payload = asdict(report)
    assert payload["manifest"]["generation"] == report.manifest.generation
    assert payload["shelf"]["manifest"]["passage_count"] == len(report.shelf.passages)
