# Compatibility shard 1 for curated_legacy_migration.
from __future__ import annotations

from dataclasses import dataclass, field

from pathlib import Path

from typing import Any

from brain.v5.evidence import record_legacy_unchecked_evidence

from brain.v5.legacy_bridge import migrate_legacy_topic_to_v5, scan_legacy_topic

from brain.v5.markdown import write_md

from brain.v5.paths import WorkspacePaths

from brain.v5.research_state import attach_artifact, create_proof_obligation, update_claim_status

from brain.v5.sensemaking import record_sensemaking_report

from brain.v5.validation import create_validation_contract

from brain.v5.workspace import bind_session, create_claim, create_context, create_topic

@dataclass(frozen=True)
class CuratedArtifactSpec:
    path: str
    artifact_type: str
    summary: str

@dataclass(frozen=True)
class CuratedEvidenceSpec:
    evidence_type: str
    status: str
    summary: str
    supports_outputs: list[str] = field(default_factory=list)
    artifact_paths: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class CuratedObligationSpec:
    statement: str
    obligation_type: str
    status: str
    next_action: str
    required_evidence: list[str] = field(default_factory=list)
    proof_strategy: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class CuratedTopicSpec:
    topic_id: str
    context_id: str
    session_id: str
    title: str
    claim_statement: str
    evidence_profile: str
    confidence_state: str
    active_uncertainty: str
    maturity_level: str
    claim_status: str
    scope: str
    risk: str
    next_action: str
    assumptions: list[str]
    open_gaps: list[str]
    non_claims: str = ""
    strongest_failure_mode: str = ""
    artifacts: list[CuratedArtifactSpec] = field(default_factory=list)
    evidence: list[CuratedEvidenceSpec] = field(default_factory=list)
    obligations: list[CuratedObligationSpec] = field(default_factory=list)
    validation_checks: list[str] = field(default_factory=list)
    validation_failure_modes: list[str] = field(default_factory=list)
    validation_outputs: list[str] = field(default_factory=list)
    sensemaking_title: str = ""
    sensemaking_summary: str = ""
    next_actions: list[str] = field(default_factory=list)

def migrate_curated_legacy_topic_to_v5(
    ws: WorkspacePaths,
    topic_dir: str | Path,
    *,
    context_id: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    """Migrate one known legacy topic and add curated v5 records."""

    root = Path(topic_dir)
    summary = scan_legacy_topic(root)
    spec = _spec_for_topic(summary.topic_slug)
    if context_id:
        spec = _replace(spec, context_id=context_id)
    if session_id:
        spec = _replace(spec, session_id=session_id)

    generic = migrate_legacy_topic_to_v5(
        ws,
        root,
        context_id=spec.context_id,
        session_id=f"{spec.session_id}-legacy-preserve",
    )

    create_context(ws, spec.context_id, title=spec.context_id)
    create_topic(ws, spec.topic_id, context_id=spec.context_id, title=spec.title)
    claim = create_claim(
        ws,
        topic_id=spec.topic_id,
        statement=spec.claim_statement,
        evidence_profile=spec.evidence_profile,
        confidence_state=spec.confidence_state,
        active_uncertainty=spec.active_uncertainty,
        scope=spec.scope,
        non_claims=spec.non_claims,
        strongest_failure_mode=spec.strongest_failure_mode,
    )

    artifact_by_path, missing_artifacts = _attach_curated_artifacts(ws, root, spec, claim.claim_id)
    evidence_ids = _record_curated_evidence(ws, spec, claim.claim_id, artifact_by_path)

    contract = create_validation_contract(
        ws,
        topic_id=spec.topic_id,
        claim_id=claim.claim_id,
        required_checks=spec.validation_checks,
        failure_modes=spec.validation_failure_modes,
        required_evidence_outputs=spec.validation_outputs,
        validator_role="curated_legacy_migration_review",
    )

    obligation_ids = []
    for obligation in spec.obligations:
        record = create_proof_obligation(
            ws,
            topic_id=spec.topic_id,
            claim_id=claim.claim_id,
            statement=obligation.statement,
            obligation_type=obligation.obligation_type,
            status=obligation.status,
            maturity_level=spec.maturity_level,
            next_action=obligation.next_action,
            required_evidence=obligation.required_evidence,
            proof_strategy=obligation.proof_strategy,
            failure_modes=obligation.failure_modes,
            evidence_refs=evidence_ids,
            artifact_ids=list(artifact_by_path.values()),
        )
        obligation_ids.append(record.obligation_id)

    status = update_claim_status(
        ws,
        topic_id=spec.topic_id,
        claim_id=claim.claim_id,
        maturity_level=spec.maturity_level,
        claim_status=spec.claim_status,
        scope=spec.scope,
        risk=spec.risk,
        next_action=spec.next_action,
        assumptions=spec.assumptions,
        open_gaps=spec.open_gaps,
        evidence_refs=evidence_ids,
        artifact_ids=list(artifact_by_path.values()),
        human_gate_required=True,
    )

    report = record_sensemaking_report(
        ws,
        topic_id=spec.topic_id,
        claim_id=claim.claim_id,
        title=spec.sensemaking_title or "Curated legacy-to-v5 migration",
        summary=spec.sensemaking_summary,
        evidence_refs=evidence_ids,
        open_questions=spec.open_gaps,
        next_actions=spec.next_actions,
        validation_status="migration_orientation",
    )

    bind_session(
        ws,
        spec.session_id,
        topic_id=spec.topic_id,
        context_id=spec.context_id,
        active_claim=claim.claim_id,
        active_route="curated_legacy_migration",
        interaction_profile="collaborator",
    )
    index_path = _write_curated_index(
        ws,
        spec=spec,
        claim_id=claim.claim_id,
        status_id=status.status_id,
        contract_id=contract.contract_id,
        evidence_ids=evidence_ids,
        artifact_ids=list(artifact_by_path.values()),
        obligation_ids=obligation_ids,
        report_id=report.report_id,
        missing_artifacts=missing_artifacts,
        generic_result=generic,
    )

    written = _merge_written_records(
        generic.get("written_records", {}),
        {
            "topics": [spec.topic_id],
            "claims": [claim.claim_id],
            "evidence": evidence_ids,
            "reference_locations": [],
            "sensemaking_reports": [report.report_id],
            "trace_events": [],
            "memory_entries": [],
            "artifacts": list(artifact_by_path.values()),
            "claim_statuses": [status.status_id],
            "proof_obligations": obligation_ids,
            "validation_contracts": [contract.contract_id],
            "indexes": [str(index_path)],
        },
    )

    return {
        "kind": "legacy_topic_migration_result",
        "topic_id": spec.topic_id,
        "context_id": spec.context_id,
        "session_id": spec.session_id,
        "active_claim_id": claim.claim_id,
        "written_records": written,
        "preserved_source_refs": generic.get("preserved_source_refs", []),
        "curation": {
            "claim_status_id": status.status_id,
            "validation_contract_id": contract.contract_id,
            "proof_obligation_ids": obligation_ids,
            "sensemaking_report_id": report.report_id,
            "artifact_ids": list(artifact_by_path.values()),
            "missing_artifacts": missing_artifacts,
            "index_path": str(index_path),
            "legacy_preservation_session_id": f"{spec.session_id}-legacy-preserve",
        },
        "summary_inputs_trusted": False,
    }

def known_curated_legacy_topics() -> list[str]:
    return sorted(_CURATED_SPECS)

def _replace(spec: CuratedTopicSpec, **changes: Any) -> CuratedTopicSpec:
    data = dict(spec.__dict__)
    data.update(changes)
    return CuratedTopicSpec(**data)

def _attach_curated_artifacts(
    ws: WorkspacePaths,
    topic_root: Path,
    spec: CuratedTopicSpec,
    claim_id: str,
) -> tuple[dict[str, str], list[str]]:
    artifact_by_path: dict[str, str] = {}
    missing: list[str] = []
    for item in spec.artifacts:
        path = _resolve_path(topic_root, item.path)
        if not path.exists():
            missing.append(str(path))
            continue
        artifact = attach_artifact(
            ws,
            topic_id=spec.topic_id,
            claim_id=claim_id,
            artifact_type=item.artifact_type,
            uri=path.as_posix(),
            summary=item.summary,
            metadata={
                "migration_role": "curated_legacy_evidence",
                "legacy_topic_path": topic_root.as_posix(),
            },
        )
        artifact_by_path[item.path] = artifact.artifact_id
    return artifact_by_path, missing

def _record_curated_evidence(
    ws: WorkspacePaths,
    spec: CuratedTopicSpec,
    claim_id: str,
    artifact_by_path: dict[str, str],
) -> list[str]:
    evidence_ids: list[str] = []
    for item in spec.evidence:
        artifact_ids = [artifact_by_path[path] for path in item.artifact_paths if path in artifact_by_path]
        evidence = record_legacy_unchecked_evidence(
            ws,
            topic_id=spec.topic_id,
            claim_id=claim_id,
            evidence_type=item.evidence_type,
            status=item.status,
            summary=item.summary,
            supports_outputs=item.supports_outputs,
            source_refs=item.source_refs,
            artifact_ids=artifact_ids,
        )
        evidence_ids.append(evidence.evidence_id)
    return evidence_ids

def _write_curated_index(
    ws: WorkspacePaths,
    *,
    spec: CuratedTopicSpec,
    claim_id: str,
    status_id: str,
    contract_id: str,
    evidence_ids: list[str],
    artifact_ids: list[str],
    obligation_ids: list[str],
    report_id: str,
    missing_artifacts: list[str],
    generic_result: dict[str, Any],
) -> Path:
    path = ws.topic_dir(spec.topic_id) / "indexes" / "legacy_v5_curated_migration.md"
    body = "\n".join(
        [
            f"# Curated Legacy v5 Migration: {spec.topic_id}",
            "",
            "This index is generated by `brain.v5.curated_legacy_migration`.",
            "It is a migration/control-plane artifact and does not promote the claim to L2.",
            "",
            f"Active claim: `{claim_id}`",
            f"Claim status: `{status_id}`",
            f"Validation contract: `{contract_id}`",
            f"Sensemaking report: `{report_id}`",
            "",
            "## Evidence Records",
            *[f"- `{item}`" for item in evidence_ids],
            "",
            "## Artifact Records",
            *[f"- `{item}`" for item in artifact_ids],
            "",
            "## Proof Obligations",
            *[f"- `{item}`" for item in obligation_ids],
            "",
            "## Missing Artifacts",
            *([f"- `{item}`" for item in missing_artifacts] or ["- none"]),
            "",
            "## Legacy Preservation",
            f"Generic migration active claim: `{generic_result.get('active_claim_id', '')}`",
            "Generic migration records preserve legacy sources, candidates, and process notes as untrusted evidence.",
            "",
        ]
    )
    write_md(
        path,
        {
            "kind": "legacy_v5_curated_migration_index",
            "topic_id": spec.topic_id,
            "claim_id": claim_id,
            "status_id": status_id,
            "validation_contract_id": contract_id,
            "summary_inputs_trusted": False,
        },
        body,
    )
    return path

def _merge_written_records(base: dict[str, Any], extra: dict[str, list[str]]) -> dict[str, list[str]]:
    required = [
        "topics",
        "claims",
        "evidence",
        "reference_locations",
        "sensemaking_reports",
        "trace_events",
        "memory_entries",
    ]
    merged: dict[str, list[str]] = {}
    for key in required:
        merged[key] = _unique([*(base.get(key) or []), *(extra.get(key) or [])])
    for key, values in extra.items():
        if key not in merged:
            merged[key] = _unique(values)
    return merged

def _resolve_path(topic_root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return topic_root / path

def _unique(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            out.append(value)
            seen.add(value)
    return out
