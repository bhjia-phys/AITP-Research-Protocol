"""Research authority records for conventions, sectors, datasets, and code paths."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.models import AuthorityRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_valid_records, write_record

AUTHORITY_TYPES = {
    "sector_authority",
    "statistics_convention",
    "formula_convention",
    "dataset_authority",
    "code_path_authority",
}

AUTHORITY_STATUSES = {
    "research_authority_not_trust_promotion",
    "candidate",
    "active",
    "superseded",
    "rejected",
}


def record_authority(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    authority_type: str,
    authority_statement: str,
    work_package: str = "",
    claim_id: str = "",
    scope: dict[str, Any] | None = None,
    generator_set: str = "",
    closure_envelope: str = "",
    evidence_refs: list[str] | None = None,
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    linked_records: dict[str, Any] | None = None,
    limitations: list[str] | None = None,
    status: str = "research_authority_not_trust_promotion",
) -> AuthorityRecord:
    """Record the currently adopted research authority without changing trust."""

    if authority_type not in AUTHORITY_TYPES:
        raise ValueError(f"authority_type must be one of {sorted(AUTHORITY_TYPES)}")
    if status not in AUTHORITY_STATUSES:
        raise ValueError(f"status must be one of {sorted(AUTHORITY_STATUSES)}")
    authority_id = prefixed_id(
        "authority",
        f"{topic_id}:{authority_type}:{work_package}:{authority_statement}",
        max_slug=80,
    )
    record = AuthorityRecord(
        authority_id=authority_id,
        topic_id=topic_id,
        authority_type=authority_type,
        authority_statement=authority_statement,
        work_package=work_package,
        claim_id=claim_id,
        scope=scope or {},
        generator_set=generator_set,
        closure_envelope=closure_envelope,
        evidence_refs=evidence_refs or [],
        source_refs=source_refs or [],
        artifact_ids=artifact_ids or [],
        linked_records=linked_records or {},
        limitations=limitations or [],
        status=status,
    )
    write_record(
        ws.registry_dir("authorities") / f"{authority_id}.md",
        record,
        body=_authority_body(record),
    )
    return record


def list_authorities_for_topic(
    ws: WorkspacePaths,
    topic_id: str,
    *,
    authority_type: str = "",
    work_package: str = "",
    include_inactive: bool = False,
) -> list[AuthorityRecord]:
    authorities = [
        record
        for record in list_valid_records(ws.registry_dir("authorities"), AuthorityRecord)
        if record.topic_id == topic_id
    ]
    if authority_type:
        authorities = [record for record in authorities if record.authority_type == authority_type]
    if work_package:
        authorities = [record for record in authorities if record.work_package == work_package]
    if not include_inactive:
        authorities = [
            record
            for record in authorities
            if record.status not in {"superseded", "rejected"}
        ]
    return authorities


def authority_record_payload(record: AuthorityRecord) -> dict[str, Any]:
    return {"ok": True, **asdict(record)}


def authority_registry_payload(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    authority_type: str = "",
    work_package: str = "",
    include_inactive: bool = False,
) -> dict[str, Any]:
    records = list_authorities_for_topic(
        ws,
        topic_id,
        authority_type=authority_type,
        work_package=work_package,
        include_inactive=include_inactive,
    )
    return {
        "ok": True,
        "kind": "authority_registry",
        "topic_id": topic_id,
        "authority_type_filter": authority_type,
        "work_package_filter": work_package,
        "include_inactive": include_inactive,
        "authority_count": len(records),
        "authorities": [asdict(record) for record in records],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _authority_body(record: AuthorityRecord) -> str:
    limitations = "\n".join(f"- {item}" for item in record.limitations) or "- None"
    evidence = "\n".join(f"- {item}" for item in record.evidence_refs) or "- None"
    sources = "\n".join(f"- {item}" for item in record.source_refs) or "- None"
    return (
        f"# Authority: {record.authority_type}\n\n"
        f"{record.authority_statement}\n\n"
        f"Work package: `{record.work_package or 'unscoped'}`\n\n"
        f"Status: `{record.status}`\n\n"
        "## Limitations\n\n"
        f"{limitations}\n\n"
        "## Evidence Refs\n\n"
        f"{evidence}\n\n"
        "## Source Refs\n\n"
        f"{sources}\n"
    )
