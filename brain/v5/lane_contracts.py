"""Typed lane contracts for compute topics.

Promotes the cockpit's lane discipline (forbidden/preferred roots, final
allowlist, final-evidence rules, default lane) from a generated JSON surface
into auditable, rehome-able typed records. Lane contracts constrain how
downstream plotting/reporting treats rows and which roots may feed final
evidence; they cannot update claim trust.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.models import LaneContractRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_valid_records, write_record


def record_lane_contract(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    campaign: str = "",
    claim_id: str = "",
    forbidden_roots: list[str] | None = None,
    preferred_clean_roots: list[str] | None = None,
    final_allowlist: list[str] | None = None,
    final_rules: list[str] | None = None,
    default_lane: str = "diagnostic",
    trust_update_forbidden: bool = False,
    notes: list[str] | None = None,
    metadata: dict | None = None,
) -> LaneContractRecord:
    """Record (or idempotently overwrite) a lane contract for a topic+campaign.

    The contract id is derived from ``topic_id`` + ``campaign`` + the root/
    allowlist content, so recording the same contract twice overwrites the same
    file rather than creating duplicates.
    """

    basis = ":".join(
        [
            topic_id,
            campaign,
            "forbidden:" + "|".join(forbidden_roots or []),
            "allow:" + "|".join(final_allowlist or []),
        ]
    )
    contract_id = prefixed_id("lane-contract", basis, max_slug=64)
    record = LaneContractRecord(
        contract_id=contract_id,
        topic_id=topic_id,
        campaign=campaign,
        claim_id=claim_id,
        forbidden_roots=forbidden_roots or [],
        preferred_clean_roots=preferred_clean_roots or [],
        final_allowlist=final_allowlist or [],
        final_rules=final_rules or [],
        default_lane=default_lane,
        trust_update_forbidden=trust_update_forbidden,
        notes=notes or [],
        lifecycle_status="active",
        metadata=metadata or {},
    )
    write_record(
        ws.registry_dir("lane_contracts") / f"{contract_id}.md",
        record,
        body=_render_body(record),
    )
    return record


def list_lane_contracts_for_topic(ws: WorkspacePaths, topic_id: str) -> list[LaneContractRecord]:
    """Active lane contracts for a topic (most-recent last)."""

    return [
        contract
        for contract in list_valid_records(ws.registry_dir("lane_contracts"), LaneContractRecord)
        if contract.topic_id == topic_id and contract.lifecycle_status == "active"
    ]


def get_effective_lane_contract(ws: WorkspacePaths, topic_id: str) -> LaneContractRecord | None:
    """Return the last active lane contract for a topic, or None."""

    contracts = list_lane_contracts_for_topic(ws, topic_id)
    return contracts[-1] if contracts else None


def lane_contract_payload(record: LaneContractRecord) -> dict[str, Any]:
    return {
        "ok": True,
        **asdict(record),
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _render_body(record: LaneContractRecord) -> str:
    lines = [f"# Lane Contract: `{record.topic_id}`", ""]
    if record.campaign:
        lines.append(f"Campaign: `{record.campaign}`")
    if record.forbidden_roots:
        lines.append("## Forbidden roots")
        for root in record.forbidden_roots:
            lines.append(f"- `{root}`")
    if record.preferred_clean_roots:
        lines.append("## Preferred clean roots")
        for root in record.preferred_clean_roots:
            lines.append(f"- `{root}`")
    if record.final_allowlist:
        lines.append("## Final allowlist")
        for slug in record.final_allowlist:
            lines.append(f"- `{slug}`")
    if record.final_rules:
        lines.append("## Final-evidence rules")
        for rule in record.final_rules:
            lines.append(f"- {rule}")
    lines.append("")
    lines.append(f"Default lane: `{record.default_lane}`")
    if record.trust_update_forbidden:
        lines.append("Trust update: **forbidden** by this contract.")
    lines.append("")
    lines.append("_Orientation-only lane discipline; cannot update claim trust._")
    return "\n".join(lines)
