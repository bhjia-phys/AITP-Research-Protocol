"""Public data contracts for the disposable physics source shelf."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Any


SOURCE_SHELF_SCHEMA_VERSION = 3
try:
    _PYPDF_READER_VERSION = version("pypdf")
except PackageNotFoundError:
    # pypdf is a declared dependency, but a missing reader must not kill
    # unrelated MCP/CLI startup; PDF extraction still fails closed at use.
    _PYPDF_READER_VERSION = "unavailable"
SOURCE_SHELF_READER_VERSION = f"pypdf:{_PYPDF_READER_VERSION};utf8-text:1"
SOURCE_SHELF_EXTRACTOR_VERSION = "aitp-physics-blocks:3"


class SourceShelfIntegrityError(RuntimeError):
    """A derived shelf generation does not match its manifest."""


class SourceShelfStaleError(RuntimeError):
    """Canonical source authority or bytes changed after shelf publication."""


@dataclass(frozen=True)
class SourceShelfBuildRequest:
    topic_id: str
    source_asset_refs: tuple[str, ...]
    curation_rationale: str
    max_passage_chars: int = 4000


def validate_source_shelf_build_request(request) -> None:
    if not isinstance(request, SourceShelfBuildRequest):
        raise TypeError("request must be SourceShelfBuildRequest")
    if not isinstance(request.topic_id, str):
        raise TypeError("topic_id must be a string")
    if not isinstance(request.source_asset_refs, tuple) or any(
        not isinstance(item, str) for item in request.source_asset_refs
    ):
        raise TypeError("source_asset_refs must be a tuple of strings")
    if not isinstance(request.curation_rationale, str):
        raise TypeError("curation_rationale must be a string")
    if isinstance(request.max_passage_chars, bool) or not isinstance(
        request.max_passage_chars, int
    ):
        raise TypeError("max_passage_chars must be an integer")
    if not request.topic_id.strip():
        raise ValueError("topic_id is required")
    if any(not item.strip() for item in request.source_asset_refs):
        raise ValueError("source_asset_refs must not contain empty refs")
    if len(set(request.source_asset_refs)) != len(request.source_asset_refs):
        raise ValueError("source_asset_refs must not contain duplicates")
    if not request.curation_rationale.strip():
        raise ValueError("curation_rationale is required")
    if request.max_passage_chars < 256 or request.max_passage_chars > 20000:
        raise ValueError("max_passage_chars must be between 256 and 20000")


@dataclass(frozen=True)
class SourceShelfLocationPin:
    record_ref: str
    content_hash: str
    revision: int | None
    topic_id: str
    source_asset_ref: str


@dataclass(frozen=True)
class SourceShelfSourcePin:
    source_asset_ref: str
    topic_id: str
    record_content_hash: str
    record_revision: int | None
    canonical_uri: str
    local_uri: str
    content_hash: str
    acquired_at: str
    access_disposition: str
    storage_permission: str
    acquisition_decision_ref: dict[str, Any]
    acquisition_receipt_ref: dict[str, Any]
    source_location_pins: tuple[SourceShelfLocationPin, ...]


@dataclass(frozen=True)
class SourcePassage:
    passage_id: str
    ordinal: int
    source_asset_ref: str
    source_content_hash: str
    canonical_uri: str
    local_uri: str
    page_start: int | None
    page_end: int | None
    section: str
    anchor_kinds: tuple[str, ...]
    anchor_labels: tuple[str, ...]
    source_location_refs: tuple[str, ...]
    text: str
    text_hash: str
    orientation_only: bool = True
    can_update_claim_trust: bool = False


@dataclass(frozen=True)
class SourceShelfIssue:
    code: str
    source_asset_ref: str
    detail: str
    source_location_pins: tuple[SourceShelfLocationPin, ...] = ()


@dataclass(frozen=True)
class SourceShelfManifest:
    schema_version: int
    generation: str
    topic_id: str
    requested_source_asset_refs: tuple[str, ...]
    source_pins: tuple[SourceShelfSourcePin, ...]
    curation_rationale: str
    reader_version: str
    extractor_version: str
    max_passage_chars: int
    passage_count: int
    issue_count: int
    incomplete_coverage: bool
    passages_hash: str
    issues_hash: str
    passage_file: str = "passages.json"
    issues_file: str = "issues.json"
    orientation_only: bool = True
    can_update_claim_trust: bool = False


@dataclass(frozen=True)
class SourceShelf:
    manifest: SourceShelfManifest
    passages: tuple[SourcePassage, ...]
    issues: tuple[SourceShelfIssue, ...]


@dataclass(frozen=True)
class SourceShelfBuildReport:
    manifest: SourceShelfManifest
    shelf: SourceShelf
    checked_count: int
    indexed_count: int
    incomplete_coverage: bool
    issues: tuple[SourceShelfIssue, ...]
    summary_inputs_trusted: bool = False
    orientation_only: bool = True
    can_update_claim_trust: bool = False
