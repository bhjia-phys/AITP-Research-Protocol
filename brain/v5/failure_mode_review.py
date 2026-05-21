"""Read-only failure-mode physical adequacy review packets."""

from __future__ import annotations

from brain.v5.checkpoints import request_human_checkpoint
from brain.v5.failure_mode_audit import audit_failure_mode_coverage
from brain.v5.models import HumanCheckpointRecord
from brain.v5.workspace import WorkspacePaths


def build_failure_mode_review_packet(ws: WorkspacePaths, *, claim_id: str) -> dict:
    """Return review questions for physically assessing recorded failure modes."""

    audit = audit_failure_mode_coverage(ws, claim_id=claim_id)
    review_items = _review_items(audit)
    recommended_actions = list(audit["recommended_actions"])
    if review_items:
        recommended_actions.append("review_physical_adequacy_of_failure_modes")
    return {
        "ok": True,
        "kind": "failure_mode_review_packet",
        "claim_id": audit["claim_id"],
        "topic_id": audit["topic_id"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "review_scope": "physical_adequacy_before_promotion",
        "coverage_status": audit["coverage_status"],
        "requires_human_or_adversarial_review": bool(review_items),
        "review_items": review_items,
        "recommended_actions": _unique(recommended_actions),
    }


def request_failure_mode_review_checkpoint(ws: WorkspacePaths, *, claim_id: str) -> HumanCheckpointRecord:
    """Create a typed human checkpoint from the failure-mode review packet."""

    packet = build_failure_mode_review_packet(ws, claim_id=claim_id)
    modes = [item["failure_mode"] for item in packet["review_items"] if item["coverage"] != "covered_by_promotion_packet"]
    reason = "Review physical adequacy before promotion."
    if modes:
        reason = f"{reason} Modes requiring review: {', '.join(modes)}."
    return request_human_checkpoint(
        ws,
        topic_id=packet["topic_id"],
        claim_id=packet["claim_id"],
        reason=reason,
        requested_by="failure_mode_review_packet",
        options=["approve_failure_mode_review", "revise_failure_modes"],
    )


def _review_items(audit: dict) -> list[dict]:
    modes: dict[str, dict] = {}
    for mode in [audit["strongest_failure_mode"]] if audit["strongest_failure_mode"].strip() else []:
        _add_source(modes, mode, "claim.strongest_failure_mode")
    for mode in audit["validation_contract_failure_modes"]:
        _add_source(modes, mode, "validation_contract.failure_modes")
    for mode in audit["promotion_packet_failure_modes"]:
        _add_source(modes, mode, "promotion_packet.known_failure_modes")

    uncovered = set(audit["uncovered_claim_failure_modes"]) | set(audit["uncovered_validation_failure_modes"])
    items = []
    for mode, item in modes.items():
        sources = item["sources"]
        if mode in uncovered:
            coverage = "uncovered"
        elif sources == ["promotion_packet.known_failure_modes"]:
            coverage = "promotion_packet_only"
        else:
            coverage = "covered_by_promotion_packet"
        items.append(
            {
                "failure_mode": mode,
                "sources": sources,
                "coverage": coverage,
                "review_questions": _questions_for(mode, coverage),
            }
        )
    return items


def _add_source(modes: dict[str, dict], mode: str, source: str) -> None:
    clean = mode.strip()
    if not clean:
        return
    item = modes.setdefault(clean, {"sources": []})
    if source not in item["sources"]:
        item["sources"].append(source)


def _questions_for(mode: str, coverage: str) -> list[str]:
    return [
        f"What concrete calculation, derivation, or literature result would make {mode} visible rather than assumed away?",
        f"Could {mode} mimic the claimed result while passing the current validation checks?",
        f"Is the current coverage label '{coverage}' physically adequate for L2 promotion?",
    ]


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
