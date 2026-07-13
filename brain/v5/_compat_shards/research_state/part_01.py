# Compatibility shard 1 for research_state.
from __future__ import annotations

import hashlib

import mimetypes

from dataclasses import asdict

from datetime import UTC, datetime

from pathlib import Path

from typing import Any

from brain.v5.evidence import record_artifact_ref, record_evidence

from brain.v5.ids import prefixed_id

from brain.v5.models import ClaimStatusRecord, ProofObligationRecord, ReferenceLocationRecord

from brain.v5.paths import WorkspacePaths

from brain.v5.references import record_reference_location

from brain.v5.store import write_record

from brain.v5.tools import record_tool_run, tool_run_payload

from brain.v5.workspace import get_claim

MATURITY_LEVELS = {
    "exploratory",
    "finite-size evidence",
    "formula-identified",
    "theorem-candidate",
    "publishable",
}

EVIDENCE_STATUSES = {"supports", "contradicts", "mixed", "inconclusive"}

def register_source(
    ws: WorkspacePaths,
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
) -> ReferenceLocationRecord:
    """Register a source/reference pointer as orientation-only context."""

    return record_reference_location(
        ws,
        topic_id=topic_id,
        claim_id=claim_id,
        connector_id=connector_id,
        location_type=location_type,
        uri=uri,
        label=label,
        source_ref=source_ref,
        external_id=external_id,
        status="located",
        summary=summary,
        metadata={**(metadata or {}), "research_state_role": "source_candidate"},
        linked_records={"claim_id": claim_id} if claim_id else {},
    )

def attach_artifact(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str,
    artifact_type: str,
    uri: str,
    summary: str,
    size_bytes: int | str | None = 0,
    metadata: dict[str, Any] | None = None,
) -> Any:
    """Attach an artifact by reference and preserve hash metadata when possible."""

    enriched = dict(metadata or {})
    if "size_bytes" in enriched:
        enriched["size_bytes"] = _normalize_size_bytes(enriched["size_bytes"])
    size_bytes = _normalize_size_bytes(size_bytes)
    local_path = _local_path_from_uri(uri)
    if local_path and local_path.exists():
        enriched.setdefault("sha256", _sha256(local_path))
        enriched.setdefault("size_bytes", local_path.stat().st_size)
        if not size_bytes:
            size_bytes = local_path.stat().st_size
    enriched.setdefault("can_update_claim_trust", False)
    return record_artifact_ref(
        ws,
        topic_id=topic_id,
        claim_id=claim_id,
        artifact_type=artifact_type,
        uri=uri,
        summary=summary,
        size_bytes=size_bytes,
        metadata=enriched,
    )

def attach_artifact_from_local_path(
    ws: WorkspacePaths,
    *,
    path: str,
    topic_id: str,
    claim_id: str,
    artifact_type: str,
    summary: str,
    metadata: dict[str, Any] | None = None,
) -> Any:
    """Inspect a local artifact file and attach it by reference."""

    local_path = Path(path).expanduser()
    if not local_path.exists():
        raise FileNotFoundError(f"artifact path does not exist: {path}")
    if not local_path.is_file():
        raise ValueError(f"artifact path must be a file: {path}")

    resolved = local_path.resolve()
    stat = resolved.stat()
    mime_type, _ = mimetypes.guess_type(str(resolved))
    enriched = dict(metadata or {})
    enriched.setdefault("capture_tool", "aitp_v5_attach_artifact_auto")
    enriched.setdefault("captured_at", datetime.now(UTC).isoformat())
    enriched.setdefault("local_path", str(resolved))
    enriched.setdefault("file_name", resolved.name)
    enriched.setdefault("file_suffix", resolved.suffix.lower())
    enriched.setdefault("mime_type", mime_type or "")
    enriched.setdefault("mtime_utc", datetime.fromtimestamp(stat.st_mtime, UTC).isoformat())
    enriched.setdefault("sha256", _sha256(resolved))
    enriched.setdefault("hash_algorithm", "sha256")
    enriched.setdefault("content_hash_basis", "local artifact file bytes")
    enriched.setdefault("can_update_claim_trust", False)

    return attach_artifact(
        ws,
        topic_id=topic_id,
        claim_id=claim_id,
        artifact_type=artifact_type,
        uri=f"file://{resolved}",
        summary=summary or f"Auto-attached local artifact: {resolved.name}.",
        size_bytes=stat.st_size,
        metadata=enriched,
    )

def get_proof_obligation(ws: WorkspacePaths, obligation_id: str) -> ProofObligationRecord:
    """Read a proof-obligation record by id."""
    from brain.v5.proof_obligations import get_proof_obligation as _get

    return _get(ws, obligation_id)

def list_proof_obligations_for_claim(ws: WorkspacePaths, claim_id: str) -> list[ProofObligationRecord]:
    """Return proof obligations linked to a claim."""
    from brain.v5.proof_obligations import list_proof_obligations_for_claim as _list

    return _list(ws, claim_id)

def update_claim_status(
    ws: WorkspacePaths,
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
    human_gate_required: bool = True,
) -> ClaimStatusRecord:
    """Append a claim-status observation without changing the claim record."""

    _require_known_claim(ws, claim_id, topic_id=topic_id)
    _require_maturity(maturity_level)
    basis = f"{topic_id}:{claim_id}:{maturity_level}:{claim_status}:{scope}:{next_action}"
    status_id = prefixed_id("claim-status", basis, max_slug=76)
    record = ClaimStatusRecord(
        status_id=status_id,
        topic_id=topic_id,
        claim_id=claim_id,
        maturity_level=maturity_level,
        claim_status=claim_status,
        scope=scope,
        risk=risk,
        next_action=next_action,
        assumptions=assumptions or [],
        open_gaps=open_gaps or [],
        source_refs=source_refs or [],
        evidence_refs=evidence_refs or [],
        artifact_ids=artifact_ids or [],
        human_gate_required=human_gate_required,
        can_update_claim_trust=False,
    )
    write_record(
        ws.registry_dir("claim_statuses") / f"{status_id}.md",
        record,
        body=(
            "# Claim Status\n\n"
            f"Claim: `{claim_id}`\n\n"
            f"Maturity: `{maturity_level}`\n\n"
            f"Scope: {scope}\n\n"
            f"Next action: {next_action}\n"
        ),
    )
    return record

def update_proof_obligation(
    ws: WorkspacePaths,
    *,
    obligation_id: str,
    topic_id: str = "",
    claim_id: str = "",
    statement: str = "",
    obligation_type: str = "",
    status: str = "",
    maturity_level: str = "",
    next_action: str = "",
    required_evidence: list[str] | None = None,
    proof_strategy: list[str] | None = None,
    failure_modes: list[str] | None = None,
    source_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    replace_lists: bool = False,
) -> ProofObligationRecord:
    """Refine an existing proof obligation without changing claim trust."""
    from brain.v5.proof_obligations import update_proof_obligation as _update

    return _update(
        ws,
        obligation_id=obligation_id,
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
        replace_lists=replace_lists,
    )

def create_proof_obligation(
    ws: WorkspacePaths,
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
    human_gate_required: bool = True,
) -> ProofObligationRecord:
    """Record a theorem/proof obligation as a first-class open gap."""
    from brain.v5.proof_obligations import create_proof_obligation as _create

    return _create(
        ws,
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
        human_gate_required=human_gate_required,
    )

def classify_research_event(
    *,
    topic_id: str,
    event_summary: str,
    claim_id: str = "",
    event_kind: str = "",
    source_uri: str = "",
) -> dict[str, Any]:
    """Classify a research event into conservative next typed-record actions."""

    text = " ".join([event_kind, event_summary, source_uri]).lower()
    candidate_types: list[str] = []
    recommended = "needs_human_review"
    needs_claim = False
    if any(token in text for token in ("arxiv", "doi", "paper", "literature", "reference")):
        candidate_types.append("reference_location")
        recommended = "record_source"
    if any(token in text for token in ("json", "fisherd", "result", "hash", "log", "stdout")):
        candidate_types.extend(["artifact", "tool_run"])
        if claim_id:
            candidate_types.append("evidence")
            recommended = "record_bounded_numerical_evidence"
        else:
            needs_claim = True
            recommended = "record_artifact_then_bind_claim"
    if any(token in text for token in ("proof", "theorem", "obligation", "open gap", "not proved")):
        candidate_types.append("proof_obligation")
        recommended = "create_proof_obligation" if claim_id else "needs_claim_binding"
        needs_claim = needs_claim or not bool(claim_id)
    has_failure_signal = any(token in text for token in ("fail", "failed", "mismatch", "contradict", "negative control"))
    has_negative_failure_context = any(token in text for token in ("zero mismatch", "zero h4 motif mismatch", "no mismatch", "mismatch_groups\": 0"))
    if has_failure_signal and not has_negative_failure_context:
        candidate_types.append("failure_mode")
        recommended = "record_sensemaking_or_validation_result"
    if not candidate_types:
        candidate_types.append("sensemaking_report")
    risk_notes = [
        "classification is orientation-only",
        "do not update claim trust from this classifier",
    ]
    if needs_claim:
        risk_notes.append("claim binding required before evidence can be recorded")
    return {
        "ok": True,
        "kind": "research_event_classification",
        "topic_id": topic_id,
        "claim_id": claim_id,
        "event_kind": event_kind or "unknown",
        "event_summary": event_summary,
        "source_uri": source_uri,
        "candidate_record_types": _unique(candidate_types),
        "recommended_action": recommended,
        "needs_claim_binding": needs_claim,
        "needs_human_gate": recommended in {"needs_human_review", "needs_claim_binding"},
        "risk_notes": risk_notes,
        "trust_update_forbidden": True,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }
