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


def test_canonical_legacy_l2_seed_review_worklist_groups_global_and_mismatched_seeds(tmp_path):
    from brain.v5.legacy_l2_seed_audit import build_canonical_legacy_l2_seed_review_worklist

    ws = init_workspace(tmp_path)
    entries = ws.root / "memory" / "l2" / "entries"
    write_md(
        entries / "memory-legacy-l2-l2-entries-claim-headwing.md",
        {
            "kind": "memory_entry",
            "entry_id": "memory-legacy-l2-l2-entries-claim-headwing",
            "topic_id": "L2",
            "source_topic_id": "L2",
            "source_claim_id": "claim-l2",
            "memory_kind": "legacy_l2_entry:claim",
            "scope": "topic:qsgw-headwing-update-librpa",
            "source_packet_id": "legacy_l2:D:/aitp/L2/entries/claim-headwing.md",
            "status": "legacy_seed",
        },
        "# Legacy global seed\n",
    )
    write_md(
        entries / "memory-legacy-l2-ads-entries-claim-headwing.md",
        {
            "kind": "memory_entry",
            "entry_id": "memory-legacy-l2-ads-entries-claim-headwing",
            "topic_id": "ads-einstein-equation-solutions",
            "source_topic_id": "ads-einstein-equation-solutions",
            "source_claim_id": "claim-ads",
            "memory_kind": "legacy_l2_entry:claim",
            "scope": "topic:qsgw-headwing-update-librpa",
            "source_packet_id": "legacy_l2:D:/aitp/L2/entries/claim-headwing.md",
            "status": "legacy_seed",
        },
        "# Legacy mismatched seed\n",
    )

    payload = build_canonical_legacy_l2_seed_review_worklist(ws, group_limit=10, sample_limit=1)

    assert payload["kind"] == "canonical_legacy_l2_seed_review_worklist"
    assert payload["legacy_seed_count"] == 2
    assert payload["review_group_count"] == 2
    assert payload["global_l2_seed_count"] == 1
    assert payload["topic_scope_mismatch_count"] == 2
    assert "global_l2_topic_reassignment_required" in payload["review_group_blocking_class_counts"]
    assert "topic_scope_alignment_required" in payload["review_group_blocking_class_counts"]
    top = payload["review_groups"][0]
    assert top["target_topic_id"] == "qsgw-headwing-update-librpa"
    assert top["sample_entries"][0]["requires_semantic_l2_reassignment"] is True
    assert top["sample_entries"][0]["topic_scope_mismatch"] is True
    assert top["review_actions"][0]["mcp"] == "aitp_v5_build_canonical_legacy_l2_seed_review_worklist"
    assert "create_reviewed_promotion_packet_after_typed_evidence_exists" not in [
        action["action"] for action in top["review_actions"]
    ]
    assert "resolve_target_topic_and_claim_before_promotion" in [
        action["action"] for action in top["review_actions"]
    ]
    assert payload["promotion_policy"]["forbidden_shortcuts"] == [
        "do_not_change_legacy_seed_status_to_active",
        "do_not_treat_legacy_l2_refs_as_evidence_refs",
        "do_not_use_topic_level_passed_review_as_per_seed_trust",
    ]
    assert require_valid_public_surface("canonical_legacy_l2_seed_review_worklist", payload) == payload


def test_canonical_legacy_l2_seed_review_worklist_cli_mcp_runtime_and_compact(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.cli_legacy_l2_progress import compact_canonical_legacy_l2_seed_review_worklist
    from brain.v5.mcp_tools import aitp_v5_build_canonical_legacy_l2_seed_review_worklist
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
            "scope": "topic:topic-a",
            "status": "legacy_seed",
        },
        "# Legacy seed\n",
    )

    assert main([
        "--base",
        str(tmp_path),
        "legacy",
        "l2-seed-review-worklist",
        "--group-limit",
        "1",
        "--sample-limit",
        "1",
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_build_canonical_legacy_l2_seed_review_worklist(
        str(tmp_path),
        group_limit=1,
        sample_limit=1,
    )
    compact = compact_canonical_legacy_l2_seed_review_worklist(cli_payload)

    assert cli_payload["kind"] == "canonical_legacy_l2_seed_review_worklist"
    assert mcp_payload["kind"] == "canonical_legacy_l2_seed_review_worklist"
    assert compact["kind"] == "canonical_legacy_l2_seed_review_worklist_progress"
    assert compact["review_group_count"] == 1
    assert runtime_entrypoints()["canonical_legacy_l2_seed_review_worklist"] == {
        "cli": "aitp-v5 legacy l2-seed-review-worklist <args>",
        "mcp": "aitp_v5_build_canonical_legacy_l2_seed_review_worklist",
        "surface": "canonical_legacy_l2_seed_review_worklist",
    }
    assert validate_runtime_entrypoints() == []
