"""Source reconstruction command hints for legacy semantic review worklists."""

from __future__ import annotations

from typing import Any


def source_reconstruction_review_command(
    action: str,
    item: dict[str, Any],
    *,
    review_id: str,
    workspace: str,
    migration_dir: str,
) -> dict[str, Any]:
    command = {
        "action": action,
        "latest_review_id": review_id,
        "cli": (
            f"aitp-v5 --base {workspace} legacy source-reconstruction-review "
            f"--migration-dir {migration_dir} --topic {item['topic']}"
        ),
        "mcp": "aitp_v5_build_legacy_source_reconstruction_review_packet",
        "surface": "legacy_source_reconstruction_review_packet",
        "effect": "orientation_only",
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    source_review_refs = [
        str(ref) for ref in item.get("source_reconstruction_review_refs", []) if str(ref)
    ]
    if source_review_refs:
        command["source_reconstruction_review_refs"] = source_review_refs
    return command
