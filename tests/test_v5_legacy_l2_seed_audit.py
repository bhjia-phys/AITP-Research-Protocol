from __future__ import annotations

import json

import pytest

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
    assert payload["open_review_group_count"] == 2
    assert payload["reviewed_group_count"] == 0
    assert payload["terminal_review_group_count"] == 0
    assert payload["review_status_counts"] == {"pending": 2}
    assert payload["review_decision_counts"] == {"pending": 2}
    assert payload["global_l2_seed_count"] == 1
    assert payload["topic_scope_mismatch_count"] == 2
    assert "global_l2_topic_reassignment_required" in payload["review_group_blocking_class_counts"]
    assert "topic_scope_alignment_required" in payload["review_group_blocking_class_counts"]
    top = payload["review_groups"][0]
    assert top["target_topic_id"] == "qsgw-headwing-update-librpa"
    assert top["semantic_mix_detected"] is False
    assert top["semantic_subgroup_count"] == 1
    assert top["semantic_subgroups"][0]["source_family"] == "claim"
    assert top["semantic_subgroups"][0]["source_object_id"] == "claim-headwing"
    assert top["sample_entries"][0]["requires_semantic_l2_reassignment"] is True
    assert top["sample_entries"][0]["topic_scope_mismatch"] is True
    assert top["sample_entries"][0]["source_family"] == "claim"
    assert top["sample_entries"][0]["source_object_id"] == "claim-headwing"
    assert top["review_actions"][0]["mcp"] == "aitp_v5_build_canonical_legacy_l2_seed_review_worklist"
    assert top["review_actions"][1]["mcp"] == "aitp_v5_record_legacy_l2_seed_group_review_result"
    assert top["review_status"] == "pending"
    assert top["review_decision"] == "pending"
    assert top["latest_review_result"] == {}
    assert top["terminal_review_recorded"] is False
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


def test_canonical_legacy_l2_seed_review_worklist_surfaces_semantic_subgroups(tmp_path):
    from brain.v5.cli_legacy_l2_progress import compact_canonical_legacy_l2_seed_review_worklist
    from brain.v5.legacy_l2_seed_audit import build_canonical_legacy_l2_seed_review_worklist

    ws = init_workspace(tmp_path)
    entries = ws.root / "memory" / "l2" / "entries"
    for object_id, body in (
        ("system-h2o-water", "# H2O\n"),
        ("system-si-bulk", "# Si\n"),
    ):
        entry_id = f"memory-legacy-l2-l2-entries-{object_id}"
        write_md(
            entries / f"{entry_id}.md",
            {
                "kind": "memory_entry",
                "entry_id": entry_id,
                "topic_id": "L2",
                "source_topic_id": "L2",
                "source_claim_id": "claim-l2",
                "memory_kind": "legacy_l2_entry:system",
                "scope": "legacy global L2 system seed",
                "source_packet_id": f"legacy_l2:D:/aitp/L2/entries/{object_id}.md",
                "status": "legacy_seed",
            },
            body,
        )

    payload = build_canonical_legacy_l2_seed_review_worklist(ws, group_limit=10, sample_limit=10)
    group = payload["review_groups"][0]

    assert group["memory_role"] == "system"
    assert group["semantic_mix_detected"] is True
    assert group["semantic_subgroup_count"] == 2
    assert group["source_family_counts"] == {"system": 2}
    assert "semantic_subgroup_split_required" in group["blocking_classes"]
    assert group["review_focus"][0] == "split_mixed_seed_group_by_source_object_before_terminal_review"
    assert [item["source_object_id"] for item in group["semantic_subgroups"]] == [
        "system-h2o-water",
        "system-si-bulk",
    ]
    assert group["semantic_subgroups"][0]["review_hint"] == "review_system_object_for_topic_reassignment_or_archive"
    assert require_valid_public_surface("canonical_legacy_l2_seed_review_worklist", payload) == payload

    compact = compact_canonical_legacy_l2_seed_review_worklist(payload)
    assert compact["top_group_semantic_mix_detected"] == [True]
    assert compact["top_group_semantic_subgroup_counts"] == [2]
    assert compact["top_group_semantic_subgroups"] == [
        ["system:system-h2o-water:1", "system:system-si-bulk:1"]
    ]
    assert compact["top_group_semantic_subgroup_review_progress"] == [
        ["system:system-h2o-water:pending/pending", "system:system-si-bulk:pending/pending"]
    ]


def test_legacy_l2_seed_group_review_result_records_terminal_group_review(tmp_path):
    from brain.v5.legacy_l2_seed_audit import (
        build_canonical_legacy_l2_seed_review_worklist,
        record_legacy_l2_seed_group_review_result,
    )

    ws = init_workspace(tmp_path)
    entry_id = "memory-legacy-l2-topic-a-l2-entries-claim-headwing"
    write_md(
        ws.root / "memory" / "l2" / "entries" / f"{entry_id}.md",
        {
            "kind": "memory_entry",
            "entry_id": entry_id,
            "topic_id": "topic-a",
            "source_topic_id": "topic-a",
            "source_claim_id": "claim-headwing",
            "memory_kind": "legacy_l2_entry:claim",
            "scope": "topic:topic-a",
            "status": "legacy_seed",
        },
        "# Legacy seed\n",
    )
    before = build_canonical_legacy_l2_seed_review_worklist(ws, group_limit=10, sample_limit=10)
    group_id = before["review_groups"][0]["group_id"]

    result = record_legacy_l2_seed_group_review_result(
        ws,
        group_id=group_id,
        status="passed",
        decision="archive",
        summary="Reviewed as archive-only legacy orientation; do not promote.",
        reviewed_seed_entry_ids=[entry_id],
        remaining_actions=["no_promotion_required"],
    )
    after = build_canonical_legacy_l2_seed_review_worklist(ws, group_limit=10, sample_limit=10)

    assert result.kind == "legacy_l2_seed_group_review_result"
    assert result.group_id == group_id
    assert result.topic_id == "topic-a"
    assert result.decision == "archive"
    assert (ws.registry_dir("legacy_l2_seed_group_reviews") / f"{result.review_id}.md").exists()
    assert after["legacy_seed_count"] == 1
    assert after["review_group_count"] == 1
    assert after["open_review_group_count"] == 0
    assert after["reviewed_group_count"] == 1
    assert after["terminal_review_group_count"] == 1
    assert after["review_status_counts"] == {"passed": 1}
    assert after["review_decision_counts"] == {"archive": 1}
    assert after["review_group_blocking_class_counts"] == {}
    assert after["next_actions"] == ["no_canonical_legacy_l2_seed_review_needed"]
    reviewed = after["review_groups"][0]
    assert reviewed["review_status"] == "passed"
    assert reviewed["review_decision"] == "archive"
    assert reviewed["latest_review_result"]["review_id"] == result.review_id
    assert reviewed["terminal_review_recorded"] is True
    assert require_valid_public_surface(
        "legacy_l2_seed_group_review_result_record",
        {"ok": True, **result.__dict__},
    ) == {"ok": True, **result.__dict__}
    assert require_valid_public_surface("canonical_legacy_l2_seed_review_worklist", after) == after


def test_legacy_l2_seed_review_treats_all_terminal_subgroups_as_terminal_group(tmp_path):
    from brain.v5.legacy_l2_seed_audit import (
        build_canonical_legacy_l2_seed_review_worklist,
        record_legacy_l2_seed_group_review_result,
    )

    ws = init_workspace(tmp_path)
    entries = ws.root / "memory" / "l2" / "entries"
    entry_ids: dict[str, str] = {}
    for object_id in ("claim-alpha", "claim-beta"):
        for suffix in ("entry", "node"):
            entry_id = f"memory-legacy-l2-l2-{suffix}-{object_id}"
            entry_ids[f"{object_id}:{suffix}"] = entry_id
            write_md(
                entries / f"{entry_id}.md",
                {
                    "kind": "memory_entry",
                    "entry_id": entry_id,
                    "topic_id": "L2",
                    "source_topic_id": "L2",
                    "source_claim_id": "claim-l2",
                    "memory_kind": f"legacy_l2_{suffix}:claim",
                    "scope": "topic:qsgw-headwing-update-librpa",
                    "source_packet_id": f"legacy_l2:D:/aitp/L2/{suffix}s/{object_id}.md",
                    "status": "legacy_seed",
                },
                f"# {object_id}\n",
            )

    before = build_canonical_legacy_l2_seed_review_worklist(ws, group_limit=10, sample_limit=10)
    group = before["review_groups"][0]
    group_id = group["group_id"]
    all_seed_ids = [entry["entry_id"] for entry in group["sample_entries"]]

    record_legacy_l2_seed_group_review_result(
        ws,
        group_id=group_id,
        status="needs_revision",
        decision="needs_topic_alignment",
        summary="Group-level review keeps this mixed legacy L2 group orientation-only until each semantic subgroup is reviewed.",
        reviewed_seed_entry_ids=all_seed_ids,
        remaining_actions=["split_semantic_subgroups_before_terminal_review"],
    )
    for object_id in ("claim-alpha", "claim-beta"):
        record_legacy_l2_seed_group_review_result(
            ws,
            group_id=group_id,
            status="passed",
            decision="already_represented",
            summary=f"{object_id} is already represented by canonical typed records; this closes only the legacy seed.",
            source_family="claim",
            source_object_id=object_id,
            reviewed_seed_entry_ids=[
                entry_ids[f"{object_id}:entry"],
                entry_ids[f"{object_id}:node"],
            ],
            reviewed_typed_refs=[f"claim:{object_id}:canonical"],
            remaining_actions=[f"keep_{object_id}_legacy_seed_orientation_only"],
        )

    after = build_canonical_legacy_l2_seed_review_worklist(ws, group_limit=10, sample_limit=10)
    reviewed = after["review_groups"][0]

    assert after["open_review_group_count"] == 0
    assert after["terminal_review_group_count"] == 1
    assert after["semantic_subgroup_reviewed_count"] == 2
    assert after["semantic_subgroup_terminal_review_count"] == 2
    assert after["semantic_subgroup_open_review_count"] == 0
    assert after["review_group_blocking_class_counts"] == {}
    assert after["next_actions"] == ["no_canonical_legacy_l2_seed_review_needed"]
    assert reviewed["latest_review_result"]["decision"] == "needs_topic_alignment"
    assert reviewed["review_status"] == "needs_revision"
    assert reviewed["review_decision"] == "needs_topic_alignment"
    assert reviewed["terminal_review_recorded"] is True
    assert reviewed["terminal_review_basis"] == "semantic_subgroups"
    assert all(subgroup["terminal_review_recorded"] for subgroup in reviewed["semantic_subgroups"])
    assert require_valid_public_surface("canonical_legacy_l2_seed_review_worklist", after) == after


def test_legacy_l2_seed_group_review_result_records_semantic_subgroup_boundary(tmp_path):
    from brain.v5.cli_legacy_l2_progress import compact_canonical_legacy_l2_seed_review_worklist
    from brain.v5.legacy_l2_seed_audit import (
        build_canonical_legacy_l2_seed_review_worklist,
        record_legacy_l2_seed_group_review_result,
    )

    ws = init_workspace(tmp_path)
    entries = ws.root / "memory" / "l2" / "entries"
    entry_ids: dict[str, str] = {}
    for object_id in ("system-h2o-water", "system-si-bulk"):
        entry_id = f"memory-legacy-l2-l2-entries-{object_id}"
        entry_ids[object_id] = entry_id
        write_md(
            entries / f"{entry_id}.md",
            {
                "kind": "memory_entry",
                "entry_id": entry_id,
                "topic_id": "L2",
                "source_topic_id": "L2",
                "source_claim_id": "claim-l2",
                "memory_kind": "legacy_l2_entry:system",
                "scope": "legacy global L2 system seed",
                "source_packet_id": f"legacy_l2:D:/aitp/L2/entries/{object_id}.md",
                "status": "legacy_seed",
            },
            f"# {object_id}\n",
        )

    before = build_canonical_legacy_l2_seed_review_worklist(ws, group_limit=10, sample_limit=10)
    group = before["review_groups"][0]

    with pytest.raises(ValueError, match="reviewed semantic subgroup"):
        record_legacy_l2_seed_group_review_result(
            ws,
            group_id=group["group_id"],
            status="needs_revision",
            decision="needs_source_reconstruction",
            summary="This intentionally cites the Si seed while claiming to review H2O.",
            source_family="system",
            source_object_id="system-h2o-water",
            reviewed_seed_entry_ids=[entry_ids["system-si-bulk"]],
        )

    result = record_legacy_l2_seed_group_review_result(
        ws,
        group_id=group["group_id"],
        status="needs_revision",
        decision="needs_source_reconstruction",
        summary="H2O system subgroup needs source reconstruction before terminal archive, reassign, or promotion.",
        source_family="system",
        source_object_id="system-h2o-water",
        reviewed_seed_entry_ids=[entry_ids["system-h2o-water"]],
        remaining_actions=["decide_h2o_topic_reassignment_or_archive"],
    )
    after = build_canonical_legacy_l2_seed_review_worklist(ws, group_limit=10, sample_limit=10)
    reviewed_group = after["review_groups"][0]
    reviewed_subgroup = next(
        subgroup
        for subgroup in reviewed_group["semantic_subgroups"]
        if subgroup["source_object_id"] == "system-h2o-water"
    )

    assert result.source_family == "system"
    assert result.source_object_id == "system-h2o-water"
    assert reviewed_group["latest_review_result"] == {}
    assert reviewed_group["review_status"] == "pending"
    assert reviewed_group["semantic_subgroup_reviewed_count"] == 1
    assert reviewed_group["semantic_subgroup_open_review_count"] == 1
    assert reviewed_group["semantic_subgroup_terminal_review_count"] == 0
    assert reviewed_subgroup["review_status"] == "needs_revision"
    assert reviewed_subgroup["review_decision"] == "needs_source_reconstruction"
    assert reviewed_subgroup["latest_review_result"]["review_id"] == result.review_id
    assert reviewed_subgroup["latest_review_result"]["source_family"] == "system"
    assert reviewed_subgroup["latest_review_result"]["source_object_id"] == "system-h2o-water"
    assert reviewed_subgroup["latest_review_result"]["reviewed_seed_entry_ids"] == [entry_ids["system-h2o-water"]]
    assert reviewed_group["terminal_review_recorded"] is False
    assert after["semantic_subgroup_reviewed_count"] == 1
    assert after["semantic_subgroup_open_review_count"] == 1
    assert after["semantic_subgroup_terminal_review_count"] == 0
    assert after["semantic_subgroup_review_status_counts"] == {"needs_revision": 1}
    assert after["semantic_subgroup_review_decision_counts"] == {"needs_source_reconstruction": 1}
    compact = compact_canonical_legacy_l2_seed_review_worklist(after)
    assert compact["semantic_subgroup_reviewed_count"] == 1
    assert compact["semantic_subgroup_open_review_count"] == 1
    assert compact["top_group_semantic_subgroup_review_progress"][0][0] == (
        "system:system-h2o-water:needs_revision/needs_source_reconstruction"
    )
    assert require_valid_public_surface(
        "legacy_l2_seed_group_review_result_record",
        {"ok": True, **result.__dict__},
    ) == {"ok": True, **result.__dict__}


def test_compact_review_worklist_uses_sample_limit_for_reviewed_semantic_subgroups(tmp_path):
    from brain.v5.cli_legacy_l2_progress import compact_canonical_legacy_l2_seed_review_worklist
    from brain.v5.legacy_l2_seed_audit import (
        build_canonical_legacy_l2_seed_review_worklist,
        record_legacy_l2_seed_group_review_result,
    )

    ws = init_workspace(tmp_path)
    entries = ws.root / "memory" / "l2" / "entries"
    entry_ids: dict[str, str] = {}
    object_ids = [
        "system-a",
        "system-b",
        "system-c",
        "system-d",
        "system-e",
        "system-n2-dinitrogen",
    ]
    for object_id in object_ids:
        entry_id = f"memory-legacy-l2-l2-entries-{object_id}"
        entry_ids[object_id] = entry_id
        write_md(
            entries / f"{entry_id}.md",
            {
                "kind": "memory_entry",
                "entry_id": entry_id,
                "topic_id": "L2",
                "source_topic_id": "L2",
                "source_claim_id": "claim-l2",
                "memory_kind": "legacy_l2_entry:system",
                "scope": "legacy global L2 system seed",
                "source_packet_id": f"legacy_l2:D:/aitp/L2/entries/{object_id}.md",
                "status": "legacy_seed",
            },
            f"# {object_id}\n",
        )

    before = build_canonical_legacy_l2_seed_review_worklist(ws, group_limit=10, sample_limit=10)
    group = before["review_groups"][0]
    for object_id in object_ids:
        record_legacy_l2_seed_group_review_result(
            ws,
            group_id=group["group_id"],
            status="needs_revision",
            decision="needs_topic_alignment",
            summary=f"{object_id} subgroup has been reviewed but compact defaults may hide later reviewed subgroups.",
            source_family="system",
            source_object_id=object_id,
            reviewed_seed_entry_ids=[entry_ids[object_id]],
            remaining_actions=[f"keep_{object_id}_orientation_only_until_typed_import"],
        )
    after = build_canonical_legacy_l2_seed_review_worklist(ws, group_limit=10, sample_limit=10)

    compact_default = compact_canonical_legacy_l2_seed_review_worklist(after)
    compact_expanded = compact_canonical_legacy_l2_seed_review_worklist(after, sample_limit=10)

    assert "system:system-n2-dinitrogen:needs_revision/needs_topic_alignment" not in (
        compact_default["top_group_semantic_subgroup_review_progress"][0]
    )
    assert "system:system-n2-dinitrogen:needs_revision/needs_topic_alignment" in (
        compact_expanded["top_group_semantic_subgroup_review_progress"][0]
    )
    assert "system:system-n2-dinitrogen:1" in compact_expanded["top_group_semantic_subgroups"][0]


def test_legacy_l2_seed_group_review_result_surfaces_open_reviewed_groups_first(tmp_path):
    from brain.v5.legacy_l2_seed_audit import (
        build_canonical_legacy_l2_seed_review_worklist,
        record_legacy_l2_seed_group_review_result,
    )

    ws = init_workspace(tmp_path)
    entries = ws.root / "memory" / "l2" / "entries"
    for topic, claim, priority_scope in (
        ("topic-high", "claim-high", "topic:wrong-topic"),
        ("topic-low", "claim-low", "topic:topic-low"),
    ):
        entry_id = f"memory-legacy-l2-{topic}-l2-entries-{claim}"
        write_md(
            entries / f"{entry_id}.md",
            {
                "kind": "memory_entry",
                "entry_id": entry_id,
                "topic_id": topic,
                "source_topic_id": topic,
                "source_claim_id": claim,
                "memory_kind": "legacy_l2_entry:claim",
                "scope": priority_scope,
                "status": "legacy_seed",
            },
            "# Legacy seed\n",
        )

    before = build_canonical_legacy_l2_seed_review_worklist(ws, group_limit=10, sample_limit=10)
    low_group = next(group for group in before["review_groups"] if group["source_claim_id"] == "claim-low")
    high_group = next(group for group in before["review_groups"] if group["source_claim_id"] == "claim-high")

    record_legacy_l2_seed_group_review_result(
        ws,
        group_id=low_group["group_id"],
        status="needs_revision",
        decision="needs_topic_alignment",
        summary="Non-terminal review confirms this group still needs topic alignment before any promotion or archive decision.",
        reviewed_seed_entry_ids=[low_group["sample_entries"][0]["entry_id"]],
        remaining_actions=["resolve_target_topic_before_terminal_decision"],
    )
    after = build_canonical_legacy_l2_seed_review_worklist(ws, group_limit=10, sample_limit=10)

    assert after["open_review_group_count"] == 2
    assert after["reviewed_group_count"] == 1
    assert after["terminal_review_group_count"] == 0
    assert after["review_groups"][0]["group_id"] == low_group["group_id"]
    assert after["review_groups"][0]["review_status"] == "needs_revision"
    assert after["review_groups"][0]["terminal_review_recorded"] is False
    assert after["review_groups"][1]["group_id"] == high_group["group_id"]


def test_canonical_legacy_l2_seed_review_worklist_cli_mcp_runtime_and_compact(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.cli_legacy_l2_progress import compact_canonical_legacy_l2_seed_review_worklist
    from brain.v5.mcp_tools import (
        aitp_v5_build_canonical_legacy_l2_seed_review_worklist,
        aitp_v5_record_legacy_l2_seed_group_review_result,
    )
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    ws = init_workspace(tmp_path)
    entry_id = "memory-legacy-l2-topic-a-l2-entries-claim-headwing"
    write_md(
        ws.root / "memory" / "l2" / "entries" / f"{entry_id}.md",
        {
            "kind": "memory_entry",
            "entry_id": entry_id,
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
    group_id = cli_payload["review_groups"][0]["group_id"]
    subgroup = cli_payload["review_groups"][0]["semantic_subgroups"][0]

    assert cli_payload["kind"] == "canonical_legacy_l2_seed_review_worklist"
    assert mcp_payload["kind"] == "canonical_legacy_l2_seed_review_worklist"
    assert compact["kind"] == "canonical_legacy_l2_seed_review_worklist_progress"
    assert compact["review_group_count"] == 1
    assert compact["open_review_group_count"] == 1
    assert runtime_entrypoints()["canonical_legacy_l2_seed_review_worklist"] == {
        "cli": "aitp-v5 legacy l2-seed-review-worklist <args>",
        "mcp": "aitp_v5_build_canonical_legacy_l2_seed_review_worklist",
        "surface": "canonical_legacy_l2_seed_review_worklist",
    }
    assert runtime_entrypoints()["record_legacy_l2_seed_group_review_result"] == {
        "cli": "aitp-v5 legacy l2-seed-review-result <args>",
        "mcp": "aitp_v5_record_legacy_l2_seed_group_review_result",
        "surface": "legacy_l2_seed_group_review_result_record",
    }

    assert main([
        "--base",
        str(tmp_path),
        "legacy",
        "l2-seed-review-result",
        "--group-id",
        group_id,
        "--status",
        "passed",
        "--decision",
        "archive",
        "--summary",
        "CLI review marks this seed group archive-only.",
        "--source-family",
        subgroup["source_family"],
        "--source-object-id",
        subgroup["source_object_id"],
        "--seed-entry-id",
        entry_id,
    ]) == 0
    cli_result = json.loads(capsys.readouterr().out)
    mcp_result = aitp_v5_record_legacy_l2_seed_group_review_result(
        str(tmp_path),
        group_id=group_id,
        status="needs_revision",
        decision="needs_source_reconstruction",
        summary="MCP review records a later non-terminal revision need.",
        source_family=subgroup["source_family"],
        source_object_id=subgroup["source_object_id"],
        reviewed_seed_entry_ids=[entry_id],
    )
    assert cli_result["kind"] == "legacy_l2_seed_group_review_result"
    assert cli_result["decision"] == "archive"
    assert cli_result["source_family"] == subgroup["source_family"]
    assert cli_result["source_object_id"] == subgroup["source_object_id"]
    assert mcp_result["kind"] == "legacy_l2_seed_group_review_result"
    assert mcp_result["decision"] == "needs_source_reconstruction"
    assert mcp_result["source_family"] == subgroup["source_family"]
    assert mcp_result["source_object_id"] == subgroup["source_object_id"]
    assert validate_runtime_entrypoints() == []
