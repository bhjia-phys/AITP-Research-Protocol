from __future__ import annotations

import json

from brain.v5.markdown import write_md
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def test_canonical_legacy_l2_seed_audit_scans_seed_entries(tmp_path):
    from brain.v5.legacy_l2_seed_audit import audit_canonical_legacy_l2_seeds

    ws = init_workspace(tmp_path)
    entries = ws.root / "memory" / "l2" / "entries"
    write_md(
        entries / "memory-legacy-l2-topic-a-l2-entries-claim-headwing.md",
        {
            "kind": "memory_entry",
            "entry_id": "memory-legacy-l2-topic-a-l2-entries-claim-headwing",
            "topic_id": "topic-a",
            "source_topic_id": "topic-a",
            "source_claim_id": "claim-headwing",
            "memory_kind": "legacy_l2_entry:claim",
            "source_packet_id": "legacy_l2:D:/aitp/L2/entries/claim-headwing.md",
            "status": "legacy_seed",
        },
        "# Legacy seed\n",
    )
    write_md(
        entries / "memory-active.md",
        {
            "kind": "memory_entry",
            "entry_id": "memory-active",
            "topic_id": "topic-a",
            "source_topic_id": "topic-a",
            "source_claim_id": "claim-active",
            "memory_kind": "scoped_claim",
            "source_packet_id": "packet-active",
            "status": "active",
        },
        "# Active memory\n",
    )

    payload = audit_canonical_legacy_l2_seeds(ws)

    assert payload["kind"] == "canonical_legacy_l2_seed_audit"
    assert payload["total_memory_file_count"] == 2
    assert payload["legacy_seed_count"] == 1
    assert payload["active_legacy_seed_count"] == 0
    assert payload["legacy_seed_topic_count"] == 1
    assert payload["status_counts"] == {"legacy_seed": 1}
    assert payload["memory_kind_counts"] == {"legacy_l2_entry:claim": 1}
    assert payload["sample_entries"][0]["requires_semantic_l2_reassignment"] is True
    assert payload["sample_entries"][0]["source_path"] == "D:/aitp/L2/entries/claim-headwing.md"
    assert payload["quarantine_status"] == "canonical_legacy_l2_seeds_require_review"
    assert "promote_only_reviewed_items_through_evidence_backed_promotion_packets" in payload["next_actions"]
    assert require_valid_public_surface("canonical_legacy_l2_seed_audit", payload) == payload


def test_canonical_legacy_l2_seed_audit_detects_active_seed_leak(tmp_path):
    from brain.v5.legacy_l2_seed_audit import audit_canonical_legacy_l2_seeds

    ws = init_workspace(tmp_path)
    write_md(
        ws.root / "memory" / "l2" / "entries" / "memory-legacy-l2-topic-a-l2-entries-claim-headwing.md",
        {
            "kind": "memory_entry",
            "entry_id": "memory-legacy-l2-topic-a-l2-entries-claim-headwing",
            "topic_id": "topic-a",
            "source_topic_id": "topic-a",
            "source_claim_id": "claim-headwing",
            "memory_kind": "legacy_l2_entry:claim",
            "status": "active",
        },
        "# Active legacy seed\n",
    )

    payload = audit_canonical_legacy_l2_seeds(ws)

    assert payload["active_legacy_seed_count"] == 1
    assert payload["quarantine_status"] == "active_seed_leak_detected"
    assert payload["next_actions"][0] == "demote_or_quarantine_active_legacy_l2_seed_entries_before_agent_recovery"


def test_canonical_legacy_l2_seed_audit_cli_mcp_and_runtime_surface(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.cli_legacy_l2_progress import compact_canonical_legacy_l2_seed_audit
    from brain.v5.mcp_tools import aitp_v5_audit_canonical_legacy_l2_seeds
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    ws = init_workspace(tmp_path)
    write_md(
        ws.root / "memory" / "l2" / "entries" / "memory-legacy-l2-topic-a-l2-entries-claim-headwing.md",
        {
            "kind": "memory_entry",
            "entry_id": "memory-legacy-l2-topic-a-l2-entries-claim-headwing",
            "topic_id": "topic-a",
            "source_topic_id": "topic-a",
            "source_claim_id": "claim-headwing",
            "memory_kind": "legacy_l2_entry:claim",
            "status": "legacy_seed",
        },
        "# Legacy seed\n",
    )

    assert main(["--base", str(tmp_path), "legacy", "l2-seed-audit", "--sample-limit", "1"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_audit_canonical_legacy_l2_seeds(str(tmp_path), sample_limit=1)
    compact = compact_canonical_legacy_l2_seed_audit(cli_payload)

    assert cli_payload["kind"] == "canonical_legacy_l2_seed_audit"
    assert cli_payload["legacy_seed_count"] == 1
    assert mcp_payload["kind"] == "canonical_legacy_l2_seed_audit"
    assert compact["kind"] == "canonical_legacy_l2_seed_audit_progress"
    assert compact["legacy_seed_count"] == 1
    assert runtime_entrypoints()["canonical_legacy_l2_seed_audit"] == {
        "cli": "aitp-v5 legacy l2-seed-audit <args>",
        "mcp": "aitp_v5_audit_canonical_legacy_l2_seeds",
        "surface": "canonical_legacy_l2_seed_audit",
    }
    assert validate_runtime_entrypoints() == []
