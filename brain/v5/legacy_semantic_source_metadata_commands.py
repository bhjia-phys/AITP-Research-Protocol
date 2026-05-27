"""Command hints for source metadata repair actions in legacy semantic reviews."""

from __future__ import annotations

from typing import Any


def requests_source_metadata_repair(normalized_action: str) -> bool:
    repair_word = any(
        token in normalized_action
        for token in ("repair", "resolve", "mismatch", "correct", "canonical")
    )
    metadata_word = any(
        token in normalized_action
        for token in ("doi", "bibliograph", "citation", "source metadata")
    )
    return repair_word and metadata_word


def source_metadata_repair_command(
    action: str,
    item: dict[str, Any],
    *,
    review_id: str,
    workspace: str,
) -> dict[str, Any]:
    return {
        "action": action,
        "latest_review_id": review_id,
        "cli": (
            f"aitp-v5 --base {workspace} reference location record --topic {item['topic']} "
            f"--claim {item['active_claim_id']} --connector <connector_id> "
            "--type external_literature --uri <canonical-uri-or-doi> "
            "--label <corrected-source-label> --source-ref <corrected-source-ref> "
            "--status located --summary <source metadata repair basis>"
        ),
        "mcp": "aitp_v5_record_reference_location",
        "surface": "reference_location_record",
        "effect": "typed_record_write",
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
    }
