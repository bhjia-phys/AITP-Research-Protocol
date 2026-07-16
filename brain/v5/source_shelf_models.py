"""Public data contracts for the disposable physics source shelf."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import version
from typing import Any


SOURCE_SHELF_SCHEMA_VERSION = 1
SOURCE_SHELF_READER_VERSION = f"pypdf:{version('pypdf')};utf8-text:1"
SOURCE_SHELF_EXTRACTOR_VERSION = "aitp-physics-blocks:1"


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
    reader_version: str = SOURCE_SHELF_READER_VERSION
    extractor_version: str = SOURCE_SHELF_EXTRACTOR_VERSION


@dataclass(frozen=True)
class SourceShelfSourcePin:
    source_asset_ref: str
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


@dataclass(frozen=True)
class SourcePassage:
    passage_id: str
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
