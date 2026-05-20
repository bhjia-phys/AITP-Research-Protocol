"""Bounded subagent packet generation for AITP v5."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from brain.v5.evidence import record_evidence
from brain.v5.ids import prefixed_id
from brain.v5.models import EvidenceRecord, SensemakingReportRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.sensemaking import record_sensemaking_report


@dataclass
class SubagentPacket:
    packet_id: str
    packet_type: str
    claim_id: str
    claim_statement: str
    risk_level: str
    risk_signals: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    code_state_refs: list[str] = field(default_factory=list)
    expected_output: str = ""
    allowed_return_records: list[str] = field(default_factory=lambda: ["evidence", "proposal"])
    excluded_context_note: str = "No unrelated topic history included."

    def to_payload(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SubagentIngestionResult:
    packet_id: str
    packet_type: str
    evidence: EvidenceRecord
    proposal: SensemakingReportRecord
    direct_trust_mutation: bool = False
    l2_promotion_allowed: bool = False
    kind: str = "subagent_result_ingestion"

    def to_payload(self) -> dict:
        return {
            "kind": self.kind,
            "packet_id": self.packet_id,
            "packet_type": self.packet_type,
            "direct_trust_mutation": self.direct_trust_mutation,
            "l2_promotion_allowed": self.l2_promotion_allowed,
            "evidence": asdict(self.evidence),
            "proposal": asdict(self.proposal),
        }


def plan_subagent_packets(
    brief: dict,
    *,
    evidence_refs: list[str] | None = None,
    code_state_refs: list[str] | None = None,
) -> list[SubagentPacket]:
    """Build bounded subagent task packets when risk warrants delegation."""

    risk = brief.get("risk_assessment", {})
    risk_level = risk.get("level", "guided")
    if risk_level == "fluid":
        return []

    claim_id = brief.get("current_focus", {}).get("active_claim", "")
    claim_statement = brief.get("current_focus", {}).get("claim_statement", "")
    signal_kinds = [signal.get("kind", "") for signal in risk.get("signals", []) if signal.get("kind")]
    packets: list[SubagentPacket] = []

    def add(packet_type: str, expected_output: str) -> None:
        packet_id = prefixed_id("packet", f"{packet_type}:{claim_id}:{expected_output}", max_slug=64)
        packets.append(
            SubagentPacket(
                packet_id=packet_id,
                packet_type=packet_type,
                claim_id=claim_id,
                claim_statement=claim_statement,
                risk_level=risk_level,
                risk_signals=signal_kinds,
                evidence_refs=evidence_refs or [],
                code_state_refs=code_state_refs or [],
                expected_output=expected_output,
            )
        )

    if risk_level == "adversarial" or any(kind in signal_kinds for kind in ("claim_importance", "physics_anomaly")):
        add("CriticPacket", "counterargument_or_falsification_path")

    if any(kind in signal_kinds for kind in ("reproducibility_risk", "compute_cost")):
        add("ReproducerPacket", "minimal_reproduction_plan")

    if "formula_to_code_risk" in signal_kinds:
        add("CodeReviewerPacket", "formula_code_invariant_review")

    if "literature_conflict" in signal_kinds:
        add("LiteratureScoutPacket", "cited_conflict_map")

    interaction_role = brief.get("interaction_profile", {}).get("profile", {}).get("role")
    if interaction_role == "teacher" and risk_level in {"guided", "rigorous", "adversarial"}:
        add("TeacherAssistantPacket", "prerequisite_and_misconception_map")

    return _dedupe_by_type(packets)


def ingest_subagent_result(
    ws: WorkspacePaths,
    packet: SubagentPacket | dict[str, Any],
    *,
    topic_id: str,
    result_payload: dict[str, Any],
) -> SubagentIngestionResult:
    """Map a bounded auditor result into evidence plus a non-mutating proposal."""

    packet_payload = _packet_payload(packet)
    _reject_trust_mutation_payload(result_payload)
    summary = _required_text(result_payload, "summary")
    critique_summary = str(result_payload.get("critique_summary") or summary)
    status = str(result_payload.get("status") or "raises_risk")
    source_refs = [f"subagent_packet:{packet_payload['packet_id']}"]
    source_refs.extend(str(ref) for ref in packet_payload.get("evidence_refs", []))
    source_refs.extend(str(ref) for ref in packet_payload.get("code_state_refs", []))

    evidence = record_evidence(
        ws,
        topic_id=topic_id,
        claim_id=packet_payload["claim_id"],
        evidence_type=_evidence_type_for_packet(packet_payload["packet_type"]),
        status=status,
        summary=critique_summary,
        supports_outputs=_supports_outputs_for_packet(packet_payload["packet_type"]),
        source_refs=source_refs,
    )
    proposal = record_sensemaking_report(
        ws,
        topic_id=topic_id,
        claim_id=packet_payload["claim_id"],
        title=f"{packet_payload['packet_type']} result: {packet_payload['packet_id']}",
        summary=summary,
        evidence_refs=[evidence.evidence_id],
        open_questions=_string_list(result_payload.get("open_questions")),
        next_actions=_string_list(
            result_payload.get("proposed_next_actions")
            or result_payload.get("next_actions")
        ),
    )
    return SubagentIngestionResult(
        packet_id=packet_payload["packet_id"],
        packet_type=packet_payload["packet_type"],
        evidence=evidence,
        proposal=proposal,
    )


def _dedupe_by_type(packets: list[SubagentPacket]) -> list[SubagentPacket]:
    seen = set()
    result = []
    for packet in packets:
        if packet.packet_type in seen:
            continue
        seen.add(packet.packet_type)
        result.append(packet)
    return result


_TRUST_MUTATION_KEYS = {
    "claim_update",
    "confidence_state",
    "direct_claim_patch",
    "l2_promotion",
    "memory_entry",
    "promotion_packet",
    "trust_update",
}


def _packet_payload(packet: SubagentPacket | dict[str, Any]) -> dict[str, Any]:
    payload = packet.to_payload() if isinstance(packet, SubagentPacket) else dict(packet)
    required = ("packet_id", "packet_type", "claim_id", "claim_statement")
    missing = [key for key in required if not isinstance(payload.get(key), str) or not payload.get(key)]
    if missing:
        raise ValueError(f"subagent packet missing required fields: {', '.join(missing)}")
    return payload


def _reject_trust_mutation_payload(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("subagent result payload must be a mapping")
    blocked = sorted(key for key in _TRUST_MUTATION_KEYS if key in payload)
    if blocked:
        raise ValueError(f"subagent result cannot mutate trust state directly: {', '.join(blocked)}")


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"subagent result {key} must be a non-empty string")
    return value.strip()


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("subagent result list fields must be lists of strings")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError("subagent result list fields must contain non-empty strings")
    return [item.strip() for item in value]


def _evidence_type_for_packet(packet_type: str) -> str:
    return {
        "CriticPacket": "subagent_critique",
        "ReproducerPacket": "subagent_reproduction_plan",
        "LiteratureScoutPacket": "subagent_literature_audit",
        "CodeReviewerPacket": "subagent_formula_code_audit",
        "TeacherAssistantPacket": "subagent_teaching_diagnostic",
    }.get(packet_type, "subagent_result")


def _supports_outputs_for_packet(packet_type: str) -> list[str]:
    if packet_type == "CriticPacket":
        return ["counterargument_or_falsification_path", "evidence_or_provenance"]
    if packet_type == "ReproducerPacket":
        return ["evidence_or_provenance", "minimal_check"]
    if packet_type in {"CodeReviewerPacket", "LiteratureScoutPacket"}:
        return ["evidence_or_provenance", "failure_mode"]
    return ["evidence_or_provenance"]
