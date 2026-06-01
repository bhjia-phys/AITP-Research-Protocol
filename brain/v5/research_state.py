"""Conservative research-state helpers for theory projects.

These helpers compose existing typed records into a small physics-facing surface.
They do not mutate claim trust, topic_state, or L2 memory.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from pathlib import Path
from typing import Any

from brain.v5.evidence import record_artifact_ref, record_evidence
from brain.v5.ids import prefixed_id
from brain.v5.models import ClaimStatusRecord, ProofObligationRecord, ReferenceLocationRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.references import record_reference_location
from brain.v5.store import write_record
from brain.v5.tools import record_tool_run
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
    size_bytes: int = 0,
    metadata: dict[str, Any] | None = None,
) -> Any:
    """Attach an artifact by reference and preserve hash metadata when possible."""

    enriched = dict(metadata or {})
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

    _require_known_claim(ws, claim_id, topic_id=topic_id)
    _require_maturity(maturity_level)
    basis = f"{topic_id}:{claim_id}:{obligation_type}:{statement}:{next_action}"
    obligation_id = prefixed_id("proof-obligation", basis, max_slug=76)
    record = ProofObligationRecord(
        obligation_id=obligation_id,
        topic_id=topic_id,
        claim_id=claim_id,
        statement=statement,
        obligation_type=obligation_type,
        status=status,
        maturity_level=maturity_level,
        next_action=next_action,
        required_evidence=required_evidence or [],
        proof_strategy=proof_strategy or [],
        failure_modes=failure_modes or [],
        source_refs=source_refs or [],
        evidence_refs=evidence_refs or [],
        artifact_ids=artifact_ids or [],
        human_gate_required=human_gate_required,
        can_update_claim_trust=False,
    )
    write_record(
        ws.registry_dir("proof_obligations") / f"{obligation_id}.md",
        record,
        body=(
            "# Proof Obligation\n\n"
            f"{statement}\n\n"
            f"Claim: `{claim_id}`\n\n"
            f"Status: `{status}`\n"
        ),
    )
    return record


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


def record_bounded_numerical_evidence(
    ws: WorkspacePaths,
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
) -> dict[str, Any]:
    """Record a finite/run-bounded numerical result without trust promotion."""

    _require_known_claim(ws, claim_id, topic_id=topic_id)
    if status not in EVIDENCE_STATUSES:
        raise ValueError(f"unsupported evidence status: {status}")
    if not supports_outputs:
        raise ValueError("bounded numerical evidence requires at least one scoped output")
    metadata = {
        "scope": scope,
        "bounded_evidence": True,
        "machine": machine,
        "remote_root": remote_root,
        "command": command,
    }
    artifact = attach_artifact(
        ws,
        topic_id=topic_id,
        claim_id=claim_id,
        artifact_type=artifact_type,
        uri=artifact_uri,
        summary=artifact_summary,
        metadata=metadata,
    )
    run_inputs = dict(inputs or {})
    run_outputs = dict(outputs or {})
    run_env = dict(environment or {})
    if command:
        run_inputs.setdefault("command", command)
    if machine:
        run_env.setdefault("machine", machine)
    if remote_root:
        run_env.setdefault("remote_root", remote_root)
    run_outputs.setdefault("artifact_uri", artifact_uri)
    run_outputs.setdefault("artifact_id", artifact.artifact_id)
    run_outputs.setdefault("bounded_scope", scope)
    run = record_tool_run(
        ws,
        recipe_id=recipe_id,
        tool_family=tool_family,
        tool_name=tool_name,
        topic_id=topic_id,
        claim_id=claim_id,
        inputs=run_inputs,
        outputs=run_outputs,
        environment=run_env,
        evidence_status=status,
        artifact_ids=[artifact.artifact_id],
        source_refs=source_refs or [],
    )
    evidence_summary = f"{artifact_summary} Scope: {scope}"
    evidence = record_evidence(
        ws,
        topic_id=topic_id,
        claim_id=claim_id,
        evidence_type=evidence_type,
        status=status,
        summary=evidence_summary,
        supports_outputs=supports_outputs,
        source_refs=source_refs or [artifact_uri],
        tool_run_ids=[run.run_id],
        artifact_ids=[artifact.artifact_id],
    )
    claim_status = update_claim_status(
        ws,
        topic_id=topic_id,
        claim_id=claim_id,
        maturity_level="finite-size evidence",
        claim_status="bounded_numerical_evidence_recorded",
        scope=scope,
        risk="finite-size evidence only; no theorem or trust promotion",
        next_action=next_action,
        assumptions=assumptions or [],
        open_gaps=open_gaps or ["human gate required before trust update or L2 promotion"],
        source_refs=source_refs or [artifact_uri],
        evidence_refs=[evidence.evidence_id],
        artifact_ids=[artifact.artifact_id],
        human_gate_required=True,
    )
    classification = classify_research_event(
        topic_id=topic_id,
        claim_id=claim_id,
        event_kind="bounded_numerical_result",
        event_summary=artifact_summary,
        source_uri=artifact_uri,
    )
    return {
        "ok": True,
        "kind": "bounded_numerical_evidence_bundle",
        "topic_id": topic_id,
        "claim_id": claim_id,
        "artifact": asdict(artifact),
        "tool_run": asdict(run),
        "evidence": asdict(evidence),
        "claim_status": asdict(claim_status),
        "classification": classification,
        "component_ids": {
            "artifact_id": artifact.artifact_id,
            "tool_run_id": run.run_id,
            "evidence_id": evidence.evidence_id,
            "claim_status_id": claim_status.status_id,
        },
        "supports_outputs": list(supports_outputs),
        "human_gate_required": True,
        "trust_update_forbidden": True,
        "can_update_claim_trust": False,
        "summary_inputs_trusted": False,
    }


def _require_known_claim(ws: WorkspacePaths, claim_id: str, *, topic_id: str) -> None:
    claim = get_claim(ws, claim_id)
    if claim.topic_id != topic_id:
        raise ValueError(f"claim {claim_id} belongs to topic {claim.topic_id}, not {topic_id}")


def _require_maturity(maturity_level: str) -> None:
    if maturity_level not in MATURITY_LEVELS:
        raise ValueError(f"maturity_level must be one of {sorted(MATURITY_LEVELS)}")


def _local_path_from_uri(uri: str) -> Path | None:
    if uri.startswith("file://"):
        return Path(uri[7:])
    path = Path(uri)
    if path.exists():
        return path
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = str(item)
        if key and key not in seen:
            out.append(key)
            seen.add(key)
    return out
