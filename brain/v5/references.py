"""Reference and note location records for AITP v5."""

from __future__ import annotations

from brain.v5.ids import prefixed_id
from brain.v5.models import ReferenceLocationRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_valid_records, write_record


def record_reference_location(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    connector_id: str,
    location_type: str,
    uri: str,
    label: str,
    claim_id: str = "",
    source_ref: str = "",
    external_id: str = "",
    status: str = "located",
    summary: str = "",
    metadata: dict | None = None,
    linked_records: dict | None = None,
) -> ReferenceLocationRecord:
    """Record where an external source or note lives without treating it as evidence."""

    location_id = prefixed_id(
        "reference-location",
        f"{topic_id}:{claim_id}:{connector_id}:{location_type}:{uri}",
        max_slug=64,
    )
    record = ReferenceLocationRecord(
        location_id=location_id,
        topic_id=topic_id,
        claim_id=claim_id,
        connector_id=connector_id,
        location_type=location_type,
        uri=uri,
        label=label,
        source_ref=source_ref,
        external_id=external_id,
        status=status,
        summary=summary,
        metadata=metadata or {},
        linked_records=linked_records or {},
    )
    body = "\n".join(
        [
            f"# Reference Location: {label}",
            "",
            summary or "Pointer to an external source or note. This record is orientation-only, not evidence by itself.",
            "",
            f"URI: `{uri}`",
        ]
    )
    write_record(
        ws.registry_dir("reference_locations") / f"{location_id}.md",
        record,
        body=body,
    )
    return record


def list_reference_locations_for_claim(ws: WorkspacePaths, claim_id: str) -> list[ReferenceLocationRecord]:
    """Return orientation-only reference locations linked to a claim."""

    return [
        location
        for location in list_valid_records(ws.registry_dir("reference_locations"), ReferenceLocationRecord)
        if location.claim_id == claim_id
    ]


def reference_location_brief_payload(location: ReferenceLocationRecord) -> dict:
    return {
        "location_id": location.location_id,
        "connector_id": location.connector_id,
        "location_type": location.location_type,
        "uri": location.uri,
        "label": location.label,
        "source_ref": location.source_ref,
        "orientation_only": location.orientation_only,
    }
