"""Bounded subagent packet generation for AITP v5."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from brain.v5.ids import prefixed_id


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


def _dedupe_by_type(packets: list[SubagentPacket]) -> list[SubagentPacket]:
    seen = set()
    result = []
    for packet in packets:
        if packet.packet_type in seen:
            continue
        seen.add(packet.packet_type)
        result.append(packet)
    return result
