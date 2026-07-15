"""Deterministic identity and serialized transitions for tool-run records."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.models import ToolRunRecord
from brain.v5.execution_writers import write_tool_run_compat
from brain.v5.record_envelope import canonical_record_hash
from brain.v5.record_repository import (
    RecordCollisionError,
    RecordCompareAndSwapError,
    RecordRepository,
    WritePolicy,
)


def tool_run_v1_id(
    *,
    recipe_id: str,
    tool_family: str,
    tool_name: str,
    topic_id: str,
    claim_id: str,
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    environment: dict[str, Any],
    evidence_status: str,
    source_refs: list[str],
    scientific_run_id: str,
    supersedes_run_id: str,
    lane: str,
) -> str:
    basis = ":".join(
        [
            recipe_id,
            tool_family,
            tool_name,
            topic_id,
            claim_id,
            _stable_hash(inputs),
            _stable_hash(outputs),
            _stable_hash(environment),
            evidence_status,
            _stable_hash(sorted(source_refs)),
            scientific_run_id,
            supersedes_run_id,
            lane,
        ]
    )
    return prefixed_id("tool-run", basis, max_slug=72)


def tool_run_identity(
    *,
    recipe_id: str,
    tool_family: str,
    tool_name: str,
    topic_id: str,
    claim_id: str,
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    environment: dict[str, Any],
    evidence_status: str,
    source_refs: list[str],
    scientific_run_id: str,
    supersedes_run_id: str,
    lane: str,
) -> dict[str, Any]:
    return {
        "identity_schema": "tool_run_v2",
        "recipe_id": recipe_id,
        "tool_family": tool_family,
        "tool_name": tool_name,
        "topic_id": topic_id,
        "claim_id": claim_id,
        "inputs": inputs,
        "outputs": outputs,
        "environment": environment,
        "evidence_status": evidence_status,
        "source_refs": sorted(source_refs),
        "scientific_run_id": scientific_run_id,
        "supersedes_run_id": supersedes_run_id,
        "lane": lane,
    }


def select_tool_run_id(
    repository: RecordRepository,
    *,
    v1_run_id: str,
    identity: dict[str, Any],
    legacy_v1_candidates: list[str] | None = None,
) -> str:
    for candidate in [*(legacy_v1_candidates or []), v1_run_id]:
        current = repository.read(f"tool_run:{candidate}")
        if (
            current.status == "found"
            and isinstance(current.record, ToolRunRecord)
            and _identity_from_record(current.record) == identity
        ):
            return candidate

    if _v1_identity_is_unambiguous(identity):
        current = repository.read(f"tool_run:{v1_run_id}")
        if current.status == "not_found":
            return v1_run_id
        if current.status != "found" or not isinstance(current.record, ToolRunRecord):
            raise ValueError(f"cannot resolve existing tool-run identity: {v1_run_id}")

    return _tool_run_v2_id(identity)


def create_or_merge_tool_run(
    repository: RecordRepository,
    record: ToolRunRecord,
    *,
    body: str,
) -> ToolRunRecord:
    for _ in range(8):
        current = repository.read(f"tool_run:{record.run_id}")
        if current.status == "not_found":
            try:
                write_tool_run_compat(repository, record, body=body)
                return record
            except RecordCollisionError:
                continue
        if current.status != "found" or not isinstance(current.record, ToolRunRecord):
            raise ValueError(f"cannot resolve existing tool-run identity: {record.run_id}")
        if _identity_from_record(current.record) != _identity_from_record(record):
            raise RecordCollisionError(
                f"record id {record.run_id} already exists with different immutable identity"
            )
        return merge_tool_run_links(
            repository,
            run_id=record.run_id,
            code_state_ids=record.code_state_ids,
            artifact_ids=record.artifact_ids,
        )
    raise RecordCompareAndSwapError(
        f"tool run {record.run_id} could not be created after concurrent updates"
    )


def merge_tool_run_links(
    repository: RecordRepository,
    *,
    run_id: str,
    code_state_ids: list[str] | None = None,
    artifact_ids: list[str] | None = None,
) -> ToolRunRecord:
    for _ in range(8):
        record, body, expected_hash = tool_run_revision_basis(repository, run_id)
        merged_code_states = _merge_unique(record.code_state_ids, code_state_ids or [])
        merged_artifacts = _merge_unique(record.artifact_ids, artifact_ids or [])
        if (
            merged_code_states == record.code_state_ids
            and merged_artifacts == record.artifact_ids
        ):
            return record
        record.code_state_ids = merged_code_states
        record.artifact_ids = merged_artifacts
        try:
            write_tool_run_compat(
                repository,
                record,
                body=body,
                policy=WritePolicy(mode="revision", expected_hash=expected_hash),
            )
            return record
        except RecordCompareAndSwapError:
            continue
    raise RecordCompareAndSwapError(
        f"tool run {run_id} provenance links could not be merged after concurrent updates"
    )


def tool_run_revision_basis(
    repository: RecordRepository,
    run_id: str,
) -> tuple[ToolRunRecord, str, str]:
    current = repository.read(f"tool_run:{run_id}")
    if current.status != "found" or current.record is None:
        raise ValueError(f"tool run not found: {run_id}")
    frontmatter = current.frontmatter or {}
    expected_hash = str(frontmatter.get("record_content_hash") or "")
    if not expected_hash:
        expected_hash = canonical_record_hash(frontmatter, current.body)
    return current.record, current.body, expected_hash


def require_available_successor(
    repository: RecordRepository,
    prior_run_id: str,
    proposed_run_id: str,
) -> None:
    report = repository.list("tool_runs")
    if report.malformed:
        raise ValueError(
            "cannot establish tool-run supersession while tool-run records are malformed"
        )
    conflicting = [
        run.run_id
        for run in report.records
        if getattr(run, "supersedes_run_id", "") == prior_run_id
        and run.run_id != proposed_run_id
    ]
    if conflicting:
        raise ValueError(
            f"tool run {prior_run_id} already has successor {conflicting[0]}"
        )


def require_acyclic_supersession(
    repository: RecordRepository,
    prior_run_id: str,
    proposed_run_id: str,
    *,
    topic_id: str,
    claim_id: str,
    scientific_run_id: str,
) -> None:
    visited = {proposed_run_id}
    current_id = prior_run_id
    while current_id:
        if current_id in visited:
            raise ValueError("tool-run supersession must not contain a self-edge or cycle")
        visited.add(current_id)
        current = repository.read(f"tool_run:{current_id}")
        if current.status != "found" or not isinstance(current.record, ToolRunRecord):
            raise ValueError(
                f"tool-run supersession chain is missing or malformed: {current_id}"
            )
        record = current.record
        if record.topic_id != topic_id or record.claim_id != claim_id:
            raise ValueError(
                "tool-run supersession chain must stay within the same topic and claim"
            )
        if (
            scientific_run_id
            and record.scientific_run_id
            and record.scientific_run_id != scientific_run_id
        ):
            raise ValueError(
                "tool-run supersession chain has inconsistent scientific_run_id"
            )
        current_id = record.supersedes_run_id


def _identity_from_record(record: ToolRunRecord) -> dict[str, Any]:
    return tool_run_identity(
        recipe_id=record.recipe_id,
        tool_family=record.tool_family,
        tool_name=record.tool_name,
        topic_id=record.topic_id,
        claim_id=record.claim_id,
        inputs=record.inputs,
        outputs=record.outputs,
        environment=record.environment,
        evidence_status=record.evidence_status,
        source_refs=record.source_refs,
        scientific_run_id=record.scientific_run_id,
        supersedes_run_id=record.supersedes_run_id,
        lane=record.lane,
    )


def _v1_identity_is_unambiguous(identity: dict[str, Any]) -> bool:
    scalar_fields = (
        "recipe_id",
        "tool_family",
        "tool_name",
        "topic_id",
        "claim_id",
        "evidence_status",
        "scientific_run_id",
        "supersedes_run_id",
        "lane",
    )
    return all(":" not in str(identity[field]) for field in scalar_fields)


def _tool_run_v2_id(identity: dict[str, Any]) -> str:
    basis = ":".join(
        [
            str(identity["recipe_id"]),
            str(identity["tool_family"]),
            str(identity["tool_name"]),
            str(identity["topic_id"]),
            str(identity["claim_id"]),
            "v2",
            _stable_hash(identity),
        ]
    )
    return prefixed_id("tool-run", basis, max_slug=72)


def _merge_unique(existing: list[str], incoming: list[str]) -> list[str]:
    merged = list(existing)
    for value in incoming:
        if value and value not in merged:
            merged.append(value)
    return merged


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]
