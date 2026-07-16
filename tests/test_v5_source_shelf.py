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
    assert first.manifest.source_pins[0].topic_id == "qg"
    assert first.manifest.source_pins[0].content_hash == asset.content_hash
    assert first.manifest.source_pins[0].acquired_at == asset.acquired_at
    assert first.manifest.source_pins[0].source_location_pins[0].record_ref == (
        f"reference_location:{location.location_id}"
    )
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
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)

    def add_text_page(text):
        page = writer.add_blank_page(width=612, height=792)
        page[NameObject("/Resources")] = DictionaryObject(
            {
                NameObject("/Font"): DictionaryObject(
                    {NameObject("/F1"): font_ref}
                )
            }
        )
        stream = DecodedStreamObject()
        stream.set_data(b"BT /F1 12 Tf 72 700 Td (" + text + b") Tj ET")
        page[NameObject("/Contents")] = writer._add_object(stream)

    add_text_page(b"1 Semiclassical Setup")
    add_text_page(
        b"Definition 7. PDF page anchor. Equation 4.2. Caveat. PDF extraction."
    )
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
    assert passage.page_start == passage.page_end == 2
    assert passage.section == "Semiclassical Setup"
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


def test_source_shelf_load_rejects_issue_generation_after_blob_is_restored(tmp_path):
    from brain.v5.source_shelf import SourceShelfStaleError, build_source_shelf, load_source_shelf

    ws = _setup_topic(tmp_path)
    content = b"Definition 1. The exact source becomes available later.\n"
    asset, blob, _ = _acquired_asset(
        ws,
        name="restored-after-build",
        content=content,
    )
    blob.unlink()
    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))
    assert [issue.code for issue in report.issues] == ["source_blob_missing"]
    blob.write_bytes(content)

    with pytest.raises(SourceShelfStaleError, match="source.*changed|issue.*changed"):
        load_source_shelf(ws, report.manifest.generation)


def test_source_shelf_load_rejects_issue_only_source_after_location_revision(tmp_path):
    from dataclasses import replace

    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository, WritePolicy
    from brain.v5.source_shelf import SourceShelfStaleError, build_source_shelf, load_source_shelf

    ws = _setup_topic(tmp_path)
    asset, blob, location = _acquired_asset(
        ws,
        name="issue-only-location-revision",
        content=b"Definition 1. The blob remains unavailable.\n",
    )
    blob.unlink()
    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))
    location_ref = f"reference_location:{location.location_id}"
    pin = pin_current_record(ws, location_ref)
    RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="issue-location-test", host="pytest"),
    ).write(
        "reference_locations",
        replace(location, summary="Location revised while source remains unavailable."),
        body="# Revised issue-only source location\n",
        policy=WritePolicy(mode="revision", expected_hash=pin.content_hash),
    )

    with pytest.raises(SourceShelfStaleError, match="location|issue state changed"):
        load_source_shelf(ws, report.manifest.generation)


def test_source_shelf_load_rejects_issue_generation_after_location_is_added(tmp_path):
    from brain.v5.references import record_reference_location
    from brain.v5.source_shelf import SourceShelfStaleError, build_source_shelf, load_source_shelf

    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="located-after-build",
        content=b"Definition 1. A precise location is added later.\n",
        add_location=False,
    )
    source_ref = f"source_asset:{asset.asset_id}"
    report = build_source_shelf(ws, _request(source_ref))
    assert [issue.code for issue in report.issues] == ["missing_source_location"]
    record_reference_location(
        ws,
        topic_id="qg",
        connector_id="local-test",
        location_type="note",
        uri=asset.uri,
        label="added-location",
        source_ref=source_ref,
    )

    with pytest.raises(SourceShelfStaleError, match="source_pin_changed|location"):
        load_source_shelf(ws, report.manifest.generation)


def test_source_shelf_reports_cross_topic_location_for_requested_source(tmp_path):
    from brain.v5.references import record_reference_location
    from brain.v5.source_shelf import build_source_shelf

    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="cross-topic-location",
        content=b"Definition 1. Cross-topic pointers are not valid local locations.\n",
        add_location=False,
    )
    source_ref = f"source_asset:{asset.asset_id}"
    record_reference_location(
        ws,
        topic_id="foreign-topic",
        connector_id="local-test",
        location_type="note",
        uri=asset.uri,
        label="wrong-topic-location",
        source_ref=source_ref,
    )

    report = build_source_shelf(ws, _request(source_ref))

    assert report.incomplete_coverage is True
    assert {issue.code for issue in report.issues} == {
        "missing_source_location",
        "source_location_topic_mismatch",
    }


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


def test_source_shelf_load_rejects_false_complete_coverage(tmp_path):
    from brain.v5.source_shelf import (
        SourceShelfIntegrityError,
        build_source_shelf,
        load_source_shelf,
    )

    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="false-complete",
        content=b"Definition 1. This passage intentionally has no location.\n",
        add_location=False,
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
    payload["incomplete_coverage"] = False
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SourceShelfIntegrityError, match="coverage"):
        load_source_shelf(ws, report.manifest.generation)


def test_source_shelf_rejects_silently_omitted_requested_source(tmp_path):
    from dataclasses import replace

    from brain.v5.source_shelf import SourceShelfIntegrityError, build_source_shelf
    from brain.v5.source_shelf_storage import (
        hash_json,
        publish_source_shelf,
        shelf_generation_basis,
    )

    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="complete-source",
        content=b"Definition 1. This requested source is present.\n",
    )
    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))
    requested = report.manifest.requested_source_asset_refs + (
        "source_asset:silently-omitted",
    )
    basis = shelf_generation_basis(
        topic_id=report.manifest.topic_id,
        requested_source_asset_refs=requested,
        source_pins=report.manifest.source_pins,
        curation_rationale=report.manifest.curation_rationale,
        reader_version=report.manifest.reader_version,
        extractor_version=report.manifest.extractor_version,
        max_passage_chars=report.manifest.max_passage_chars,
        incomplete_coverage=report.manifest.incomplete_coverage,
        passages_hash=report.manifest.passages_hash,
        issues_hash=report.manifest.issues_hash,
    )
    forged_manifest = replace(
        report.manifest,
        generation=hash_json(basis),
        requested_source_asset_refs=requested,
    )

    with pytest.raises(SourceShelfIntegrityError, match="requested source"):
        publish_source_shelf(
            ws,
            replace(report.shelf, manifest=forged_manifest),
        )


def test_source_shelf_rejects_manifest_topic_different_from_source_topic(tmp_path):
    from dataclasses import replace

    import brain.v5.source_shelf as source_shelf

    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="topic-binding",
        content=b"Definition 1. Topic-local source authority.\n",
    )
    report = source_shelf.build_source_shelf(
        ws,
        _request(f"source_asset:{asset.asset_id}"),
    )
    foreign = replace(
        report.shelf,
        manifest=replace(report.manifest, topic_id="foreign-topic"),
    )

    with pytest.raises(
        (source_shelf.SourceShelfIntegrityError, source_shelf.SourceShelfStaleError),
        match="topic",
    ):
        source_shelf._require_current_sources(ws, foreign)


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


def test_source_shelf_load_normalizes_invalid_utf8_json_diagnostic(tmp_path):
    from brain.v5.source_shelf import (
        SourceShelfIntegrityError,
        build_source_shelf,
        load_source_shelf,
    )

    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="invalid-json-encoding",
        content=b"Definition 1. Derived JSON must be valid UTF-8.\n",
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
    manifest_path.write_bytes(b"\xff\xfe\x00")

    with pytest.raises(SourceShelfIntegrityError, match="cannot load source shelf manifest"):
        load_source_shelf(ws, report.manifest.generation)


def test_source_shelf_load_rejects_invalid_manifest_scalar_type(tmp_path):
    from brain.v5.source_shelf import (
        SourceShelfIntegrityError,
        build_source_shelf,
        load_source_shelf,
    )

    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="malformed-scalar",
        content=b"Definition 1. Scalar contracts are typed.\n",
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
    payload["max_passage_chars"] = "1600"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SourceShelfIntegrityError, match="max_passage_chars"):
        load_source_shelf(ws, report.manifest.generation)


def test_source_shelf_loader_rejects_string_instead_of_json_array(tmp_path):
    from brain.v5.source_shelf import SourceShelfIntegrityError, build_source_shelf
    from brain.v5.source_shelf_storage import _manifest_from_dict, _passage_from_dict

    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="array-contract",
        content=b"Equation 1. Array fields remain arrays.\n",
    )
    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))
    passage_row = asdict(report.shelf.passages[0])
    passage_row["anchor_kinds"] = "equation"
    manifest_row = asdict(report.manifest)
    manifest_row["requested_source_asset_refs"] = "source_asset:not-an-array"

    with pytest.raises(SourceShelfIntegrityError, match="passage is malformed"):
        _passage_from_dict(passage_row)
    with pytest.raises(SourceShelfIntegrityError, match="manifest is malformed"):
        _manifest_from_dict(manifest_row)


def test_source_shelf_loader_rejects_wrong_typed_location_pin_ref(tmp_path):
    from dataclasses import replace

    from brain.v5.source_shelf import SourceShelfIntegrityError, build_source_shelf
    from brain.v5.source_shelf_storage import _validate_manifest_contract

    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="typed-location-ref",
        content=b"Definition 1. Location pins use their exact record family.\n",
    )
    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))
    source_pin = report.manifest.source_pins[0]
    location_pin = source_pin.source_location_pins[0]
    malformed_pin = replace(
        source_pin,
        source_location_pins=(
            replace(location_pin, record_ref="claim:not-a-reference-location"),
        ),
    )

    with pytest.raises(SourceShelfIntegrityError, match="location pin identity"):
        _validate_manifest_contract(
            replace(report.manifest, source_pins=(malformed_pin,))
        )


def test_source_shelf_build_request_rejects_malformed_field_types(tmp_path):
    from brain.v5.source_shelf import SourceShelfBuildRequest, build_source_shelf

    ws = _setup_topic(tmp_path)

    with pytest.raises(TypeError, match="source_asset_refs"):
        build_source_shelf(
            ws,
            SourceShelfBuildRequest(
                topic_id="qg",
                source_asset_refs="source_asset:split-into-characters",
                curation_rationale="Reject malformed request fields.",
            ),
        )
    with pytest.raises(TypeError, match="topic_id"):
        build_source_shelf(
            ws,
            SourceShelfBuildRequest(
                topic_id=None,
                source_asset_refs=(),
                curation_rationale="Reject malformed request fields.",
            ),
        )
    with pytest.raises(TypeError, match="max_passage_chars"):
        build_source_shelf(
            ws,
            SourceShelfBuildRequest(
                topic_id="qg",
                source_asset_refs=(),
                curation_rationale="Reject malformed request fields.",
                max_passage_chars=True,
            ),
        )


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


def test_source_shelf_extracts_from_the_exact_hashed_byte_snapshot(tmp_path, monkeypatch):
    import brain.v5.source_shelf as source_shelf

    ws = _setup_topic(tmp_path)
    original = b"# Exact Bytes\n\nDefinition 1. Receipted source bytes.\n"
    transient = b"# Exact Bytes\n\nDefinition 9. Transient unreceipted bytes.\n"
    asset, blob, _ = _acquired_asset(
        ws,
        name="snapshot-race",
        content=original,
    )
    real_extract = source_shelf.extract_source_passages

    def racing_extract(source_bytes, *, source_suffix, max_passage_chars):
        blob.write_bytes(transient)
        try:
            return real_extract(
                source_bytes,
                source_suffix=source_suffix,
                max_passage_chars=max_passage_chars,
            )
        finally:
            blob.write_bytes(original)

    monkeypatch.setattr(source_shelf, "extract_source_passages", racing_extract)

    report = source_shelf.build_source_shelf(
        ws,
        _request(f"source_asset:{asset.asset_id}"),
    )

    joined = "\n".join(item.text for item in report.shelf.passages)
    assert "Receipted source bytes" in joined
    assert "Transient unreceipted bytes" not in joined


def test_source_shelf_load_rejects_revised_reference_location(tmp_path):
    from dataclasses import replace

    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository, WritePolicy
    from brain.v5.source_shelf import SourceShelfStaleError, build_source_shelf, load_source_shelf

    ws = _setup_topic(tmp_path)
    asset, _blob, location = _acquired_asset(
        ws,
        name="location-revision",
        content=b"Definition 1. Exact location must remain current.\n",
    )
    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))
    location_ref = f"reference_location:{location.location_id}"
    pin = pin_current_record(ws, location_ref)
    RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="location-revision-test", host="pytest"),
    ).write(
        "reference_locations",
        replace(location, summary="Revised after shelf publication."),
        body="# Revised location\n",
        policy=WritePolicy(mode="revision", expected_hash=pin.content_hash),
    )

    with pytest.raises(SourceShelfStaleError, match="source_location"):
        load_source_shelf(ws, report.manifest.generation)


def test_source_shelf_loader_recomputes_passage_semantics(tmp_path):
    from brain.v5.source_shelf import SourceShelfIntegrityError, build_source_shelf, load_source_shelf
    from brain.v5.source_shelf_storage import hash_json

    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="semantic-integrity",
        content=b"Definition 1. Original bounded passage.\n",
    )
    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))
    generation_dir = (
        ws.root
        / "indexes"
        / "knowledge"
        / "source_shelf"
        / "generations"
        / report.manifest.generation
    )
    passage_path = generation_dir / "passages.json"
    manifest_path = generation_dir / "manifest.json"
    passages = json.loads(passage_path.read_text(encoding="utf-8"))
    passages[0]["text"] = "Definition 9. Forged text with the old text hash."
    passage_path.write_text(json.dumps(passages), encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["passages_hash"] = hash_json(passages)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(SourceShelfIntegrityError, match="text_hash"):
        load_source_shelf(ws, report.manifest.generation)


def test_source_shelf_reader_versions_are_implementation_owned():
    from brain.v5.source_shelf import SourceShelfBuildRequest

    with pytest.raises(TypeError, match="reader_version"):
        SourceShelfBuildRequest(
            topic_id="qg",
            source_asset_refs=(),
            curation_rationale="Caller must not relabel the reader.",
            reader_version="unrelated-reader:999",
        )


def test_source_shelf_extracts_native_tex_formal_anchors(tmp_path):
    from brain.v5.source_shelf import build_source_shelf

    tex = r"""\section{Replica Saddles}
\begin{definition}\label{def:island}
The generalized entropy is $S_{\rm gen}$.
\end{definition}
\begin{equation}\label{eq:qes}
\delta S_{\rm gen}=0.
\end{equation}
\begin{equation}\label{eq:second-qes}
\delta^2 S_{\rm gen}>0.
\end{equation}
\begin{align}\label{eq:einstein}
G_{\mu\nu} &= 8\pi G T_{\mu\nu}.
\end{align}
\begin{gather*}\label{eq:constraint}
H\lvert\Psi\rangle=0.
\end{gather*}
\begin{multline}\label{eq:replica}
Z_n = \sum_s e^{-I_s}.
\end{multline}
\begin{theorem}\label{thm:stationary}
The candidate surface is stationary.
\end{theorem}
\begin{figure}\caption{Competing replica saddles.}\end{figure}
\begin{remark}Caveat: dominance is not established.\end{remark}
\bibitem{replica-source} Example Author.
"""
    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="formal-tex",
        content=tex.encode("utf-8"),
        suffix=".tex",
    )

    report = build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))

    assert report.incomplete_coverage is False
    assert {passage.section for passage in report.shelf.passages} == {"Replica Saddles"}
    kinds = {kind for passage in report.shelf.passages for kind in passage.anchor_kinds}
    assert {"definition", "equation", "theorem", "figure_caption", "caveat", "bibliography"} <= kinds
    labels = {label for passage in report.shelf.passages for label in passage.anchor_labels}
    assert "equation:eq:qes" in labels
    assert "equation:eq:second-qes" in labels
    assert "equation:eq:einstein" in labels
    assert "equation:eq:constraint" in labels
    assert "equation:eq:replica" in labels
    assert "definition:def:island" in labels


def test_source_shelf_retains_late_tex_label_after_bounded_split(tmp_path):
    from brain.v5.source_shelf import build_source_shelf

    tex = (
        "\\section{Long Derivation}\n"
        "\\begin{align*}\n"
        + "x_1 + x_2 + x_3 = 0 \\qquad " * 40
        + "\\label{eq:late-anchor}\n"
        "x_4 = 1.\n"
        "\\end{align*}\n"
    )
    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="long-formal-tex",
        content=tex.encode("utf-8"),
        suffix=".tex",
    )

    report = build_source_shelf(
        ws,
        _request(f"source_asset:{asset.asset_id}", max_passage_chars=256),
    )

    assert all(len(passage.text) <= 256 for passage in report.shelf.passages)
    anchored = next(
        passage
        for passage in report.shelf.passages
        if "\\label{eq:late-anchor}" in passage.text
    )
    assert "equation" in anchored.anchor_kinds
    assert "equation:eq:late-anchor" in anchored.anchor_labels


def test_source_shelf_has_production_pdf_dependency_and_no_global_current_pointer(tmp_path):
    from brain.v5.source_shelf import build_source_shelf

    manifest_path = Path(__file__).resolve().parents[1] / "aitp-manifest.json"
    deployment = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert any(str(item).startswith("pypdf") for item in deployment["pip_deps"])

    ws = _setup_topic(tmp_path)
    asset, _blob, _ = _acquired_asset(
        ws,
        name="no-global-pointer",
        content=b"Definition 1. Immutable generation only.\n",
    )
    build_source_shelf(ws, _request(f"source_asset:{asset.asset_id}"))

    assert not (
        ws.root / "indexes" / "knowledge" / "source_shelf" / "manifest.json"
    ).exists()
