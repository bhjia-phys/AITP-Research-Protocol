"""MCP-facing wrappers for conservative research-state helpers."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.research_state import (
    attach_artifact,
    classify_research_event,
    create_proof_obligation,
    record_bounded_numerical_evidence,
    register_source,
    update_claim_status,
)
from brain.v5.workspace import init_workspace


def _ws(base: str):
    return init_workspace(Path(base))


def aitp_v5_register_source(
    base: str,
    *,
    topic_id: str,
    uri: str,
    label: str,
    connector_id: str = "manual",
    location_type: str = "source",
    claim_id: str = "",
    external_id: str = "",
    summary: str = "",
    source_ref: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict:
    record = register_source(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        uri=uri,
        label=label,
        connector_id=connector_id,
        location_type=location_type,
        external_id=external_id,
        summary=summary,
        source_ref=source_ref,
        metadata=metadata,
    )
    return require_valid_public_surface("reference_location_record", {"ok": True, **asdict(record)})


def aitp_v5_attach_artifact(
    base: str,
    *,
    topic_id: str,
    claim_id: str,
    artifact_type: str,
    uri: str,
    summary: str,
    size_bytes: int = 0,
    metadata: dict[str, Any] | None = None,
) -> dict:
    record = attach_artifact(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        artifact_type=artifact_type,
        uri=uri,
        summary=summary,
        size_bytes=size_bytes,
        metadata=metadata,
    )
    return require_valid_public_surface("artifact_record", {"ok": True, **asdict(record)})


def aitp_v5_update_claim_status(
    base: str,
    *,
    topic_id: str,
    claim_id: str,
    maturity_level: str,
    claim_status: str,
    scope: str,
    risk: str,
    next_action: str,
    assumptions: list[str] | None = None,
    open_gaps: list[str] | None = None,
    source_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
) -> dict:
    record = update_claim_status(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        maturity_level=maturity_level,
        claim_status=claim_status,
        scope=scope,
        risk=risk,
        next_action=next_action,
        assumptions=assumptions,
        open_gaps=open_gaps,
        source_refs=source_refs,
        evidence_refs=evidence_refs,
        artifact_ids=artifact_ids,
    )
    return require_valid_public_surface("claim_status_record", {"ok": True, **asdict(record)})


def aitp_v5_create_proof_obligation(
    base: str,
    *,
    topic_id: str,
    claim_id: str,
    statement: str,
    obligation_type: str,
    status: str,
    maturity_level: str,
    next_action: str,
    required_evidence: list[str] | None = None,
    proof_strategy: list[str] | None = None,
    failure_modes: list[str] | None = None,
    source_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
) -> dict:
    record = create_proof_obligation(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        statement=statement,
        obligation_type=obligation_type,
        status=status,
        maturity_level=maturity_level,
        next_action=next_action,
        required_evidence=required_evidence,
        proof_strategy=proof_strategy,
        failure_modes=failure_modes,
        source_refs=source_refs,
        evidence_refs=evidence_refs,
        artifact_ids=artifact_ids,
    )
    return require_valid_public_surface("proof_obligation_record", {"ok": True, **asdict(record)})


def aitp_v5_classify_research_event(
    *,
    topic_id: str,
    event_summary: str,
    claim_id: str = "",
    event_kind: str = "",
    source_uri: str = "",
) -> dict:
    return require_valid_public_surface(
        "research_event_classification",
        classify_research_event(
            topic_id=topic_id,
            claim_id=claim_id,
            event_summary=event_summary,
            event_kind=event_kind,
            source_uri=source_uri,
        ),
    )


def aitp_v5_record_bounded_numerical_evidence(
    base: str,
    *,
    topic_id: str,
    claim_id: str,
    artifact_uri: str,
    artifact_summary: str,
    supports_outputs: list[str],
    scope: str,
    status: str = "supports",
    artifact_type: str = "result_json",
    evidence_type: str = "bounded_numerical_evidence",
    recipe_id: str = "fisherd-bounded-numerical-audit",
    tool_family: str = "remote_numerics",
    tool_name: str = "fisherd",
    command: str = "",
    machine: str = "",
    remote_root: str = "",
    inputs: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
    environment: dict[str, Any] | None = None,
    source_refs: list[str] | None = None,
    assumptions: list[str] | None = None,
    open_gaps: list[str] | None = None,
    next_action: str = "human_review_before_trust_update",
) -> dict:
    payload = record_bounded_numerical_evidence(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        artifact_uri=artifact_uri,
        artifact_summary=artifact_summary,
        supports_outputs=supports_outputs,
        scope=scope,
        status=status,
        artifact_type=artifact_type,
        evidence_type=evidence_type,
        recipe_id=recipe_id,
        tool_family=tool_family,
        tool_name=tool_name,
        command=command,
        machine=machine,
        remote_root=remote_root,
        inputs=inputs,
        outputs=outputs,
        environment=environment,
        source_refs=source_refs,
        assumptions=assumptions,
        open_gaps=open_gaps,
        next_action=next_action,
    )
    return require_valid_public_surface("bounded_numerical_evidence_bundle", payload)
