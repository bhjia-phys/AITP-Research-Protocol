from __future__ import annotations

import json


def _write_legacy_l2(base):
    l2 = base / "research" / "aitp-topics" / "L2"
    (l2 / "entries").mkdir(parents=True)
    (l2 / "graph" / "nodes").mkdir(parents=True)
    (l2 / "graph" / "edges").mkdir(parents=True)
    (l2 / "graph" / "steps").mkdir(parents=True)
    (l2 / "graph" / "towers").mkdir(parents=True)
    (l2 / "index.md").write_text(
        "---\nkind: global_l2_index\n---\n# Global L2 Index\n",
        encoding="utf-8",
    )
    (l2 / "entries" / "INDEX.md").write_text("# Entries\n", encoding="utf-8")
    (l2 / "entries" / "claim-headwing.md").write_text(
        "---\n"
        "entry_id: claim-headwing\n"
        "role: claim\n"
        "status: verified\n"
        "lane: [code_method, formal_theory]\n"
        "---\n"
        "# Headwing Claim\n",
        encoding="utf-8",
    )
    (l2 / "entries" / "method-runner.md").write_text(
        "---\n"
        "entry_id: method-runner\n"
        "role: method\n"
        "status: unverified\n"
        "lane: [code_method]\n"
        "---\n"
        "# Runner Method\n",
        encoding="utf-8",
    )
    (l2 / "graph" / "index.html").write_text("<html>L2 graph</html>", encoding="utf-8")
    (l2 / "graph" / "nodes" / "claim-headwing.md").write_text("# Node\n", encoding="utf-8")
    (l2 / "graph" / "edges" / "e-headwing-method.md").write_text("# Edge\n", encoding="utf-8")
    (l2 / "graph" / "steps" / "s1.md").write_text("# Step\n", encoding="utf-8")
    (l2 / "graph" / "towers" / "tower.md").write_text("# Tower\n", encoding="utf-8")
    return l2


def test_legacy_l2_graph_manifest_scans_entries_graph_and_obsidian_targets(tmp_path):
    from brain.v5.legacy_l2_graph import build_legacy_l2_graph_manifest
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    l2 = _write_legacy_l2(tmp_path)

    payload = build_legacy_l2_graph_manifest(ws, legacy_l2_dir=l2)

    assert require_valid_public_surface("legacy_l2_graph_manifest", payload) == payload
    assert payload["kind"] == "legacy_l2_graph_manifest"
    assert payload["legacy_shape"] == "global_l2_graph"
    assert payload["typed_migration_status"] == "needs_typed_l2_migration"
    assert payload["counts"]["entries"] == 2
    assert payload["counts"]["graph_nodes"] == 1
    assert payload["counts"]["graph_edges"] == 1
    assert payload["counts"]["graph_steps"] == 1
    assert payload["counts"]["graph_towers"] == 1
    assert payload["entries_by_role"] == {"claim": 1, "method": 1}
    assert payload["entries_by_status"] == {"unverified": 1, "verified": 1}
    assert payload["migration_worklist_status"] == "pending_typed_migration"
    assert payload["work_item_count"] == 6
    assert payload["work_item_counts_by_kind"] == {
        "entry": 2,
        "graph_edge": 1,
        "graph_node": 1,
        "graph_step": 1,
        "graph_tower": 1,
    }
    assert payload["migration_work_items"][0] == {
        "work_item_id": "legacy_l2_entry:claim-headwing",
        "work_item_kind": "entry",
        "legacy_id": "claim-headwing",
        "role": "claim",
        "status": "verified",
        "source_path": str(l2 / "entries" / "claim-headwing.md"),
        "recommended_target_surface": "memory_entry_record",
        "migration_action": "review_and_promote_into_typed_l2_memory",
        "can_update_claim_trust": False,
    }
    assert any(
        item["work_item_id"] == "legacy_l2_graph_edge:e-headwing-method"
        and item["recommended_target_surface"] == "object_relation_record"
        for item in payload["migration_work_items"]
    )
    assert payload["obsidian_view_maturity"] == {
        "status": "core_legacy_views_available",
        "core_views_available": True,
        "available_targets": ["index.md", "entries/INDEX.md", "graph/index.html"],
        "missing_core_targets": [],
    }
    assert "entries/INDEX.md" in payload["obsidian_view_targets"]
    assert "graph/index.html" in payload["obsidian_view_targets"]
    assert payload["next_actions"] == [
        "migrate_legacy_l2_entries_into_memory_records",
        "migrate_legacy_l2_graph_edges_into_object_relations",
        "rebuild_l2_obsidian_view_from_typed_graph",
        "keep_legacy_l2_orientation_only_until_typed_migration",
    ]
    assert payload["orientation_only"] is True
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False


def test_legacy_l2_graph_manifest_cli_mcp_and_runtime_surface(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_build_legacy_l2_graph_manifest
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    l2 = _write_legacy_l2(tmp_path)

    assert main(["--base", str(tmp_path), "legacy", "l2-graph-manifest", "--legacy-l2-dir", str(l2)]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_build_legacy_l2_graph_manifest(str(tmp_path), legacy_l2_dir=str(l2))

    assert cli_payload["kind"] == "legacy_l2_graph_manifest"
    assert cli_payload["counts"]["entries"] == 2
    assert mcp_payload["kind"] == "legacy_l2_graph_manifest"
    assert runtime_entrypoints()["legacy_l2_graph_manifest"] == {
        "cli": "aitp-v5 legacy l2-graph-manifest <args>",
        "mcp": "aitp_v5_build_legacy_l2_graph_manifest",
        "surface": "legacy_l2_graph_manifest",
    }


def test_legacy_l2_typed_migration_packet_groups_review_targets(tmp_path):
    from brain.v5.legacy_l2_graph import build_legacy_l2_typed_migration_packet
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    l2 = _write_legacy_l2(tmp_path)

    packet = build_legacy_l2_typed_migration_packet(ws, legacy_l2_dir=l2)

    assert require_valid_public_surface("legacy_l2_typed_migration_packet", packet) == packet
    assert packet["kind"] == "legacy_l2_typed_migration_packet"
    assert packet["legacy_l2_dir"] == str(l2)
    assert packet["typed_migration_status"] == "needs_review"
    assert packet["work_item_count"] == 6
    assert packet["truth_source"] == "legacy_l2_filesystem"
    assert packet["summary_inputs_trusted"] is False
    assert packet["orientation_only"] is True
    assert packet["can_update_kernel_state"] is False
    assert packet["can_update_claim_trust"] is False
    assert packet["review_groups"]["memory_entry_record"]["count"] == 3
    assert packet["review_groups"]["physics_object_record"]["count"] == 1
    assert packet["review_groups"]["object_relation_record"]["count"] == 1
    assert packet["review_groups"]["sensemaking_report_record"]["count"] == 1
    assert packet["review_groups"]["memory_entry_record"]["sample_work_items"][0]["legacy_id"] == "claim-headwing"
    assert packet["review_groups"]["object_relation_record"]["review_questions"] == [
        "Does the legacy edge encode a real load-bearing relation, or only an index hyperlink?",
        "Which typed object or memory records should become the relation endpoints after review?",
    ]
    assert packet["recommended_commands"]["memory_entry_record"]["effect"] == "review_only"
    assert packet["recommended_commands"]["object_relation_record"]["effect"] == "typed_record_write_after_review"
    assert packet["next_actions"] == [
        "review_legacy_l2_memory_entry_candidates",
        "review_legacy_l2_graph_nodes_for_physics_objects",
        "review_legacy_l2_graph_edges_for_object_relations",
        "review_legacy_l2_steps_for_sensemaking_reports",
        "review_legacy_l2_towers_for_memory_entries",
        "record_legacy_semantic_review_result_for_l2",
        "keep_legacy_l2_orientation_only_until_reviewed",
    ]


def test_legacy_l2_typed_migration_packet_uses_full_worklist_not_manifest_sample(tmp_path):
    from brain.v5.legacy_l2_graph import build_legacy_l2_typed_migration_packet
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    l2 = _write_legacy_l2(tmp_path)
    for index in range(2, 121):
        (l2 / "graph" / "steps" / f"s{index:03d}.md").write_text(
            f"# Step {index}\n",
            encoding="utf-8",
        )

    packet = build_legacy_l2_typed_migration_packet(ws, legacy_l2_dir=l2)

    assert packet["work_item_count"] == 125
    assert packet["work_item_counts_by_kind"] == {
        "entry": 2,
        "graph_edge": 1,
        "graph_node": 1,
        "graph_step": 120,
        "graph_tower": 1,
    }
    assert packet["review_groups"]["memory_entry_record"]["count"] == 3
    assert packet["review_groups"]["sensemaking_report_record"]["count"] == 120
    assert packet["review_groups"]["physics_object_record"]["count"] == 1
    assert packet["review_groups"]["object_relation_record"]["count"] == 1


def test_legacy_l2_typed_migration_packet_cli_mcp_and_runtime_surface(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_build_legacy_l2_typed_migration_packet
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    l2 = _write_legacy_l2(tmp_path)

    assert main([
        "--base",
        str(tmp_path),
        "legacy",
        "l2-typed-migration-packet",
        "--legacy-l2-dir",
        str(l2),
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_build_legacy_l2_typed_migration_packet(str(tmp_path), legacy_l2_dir=str(l2))

    assert cli_payload["kind"] == "legacy_l2_typed_migration_packet"
    assert cli_payload["review_groups"]["memory_entry_record"]["count"] == 3
    assert mcp_payload["kind"] == "legacy_l2_typed_migration_packet"
    assert runtime_entrypoints()["legacy_l2_typed_migration_packet"] == {
        "cli": "aitp-v5 legacy l2-typed-migration-packet <args>",
        "mcp": "aitp_v5_build_legacy_l2_typed_migration_packet",
        "surface": "legacy_l2_typed_migration_packet",
    }


def test_legacy_l2_typed_migration_packet_cli_compact_progress(tmp_path, capsys):
    from brain.v5.cli import main

    l2 = _write_legacy_l2(tmp_path)
    for index in range(2, 121):
        (l2 / "graph" / "steps" / f"s{index:03d}.md").write_text(
            f"# Step {index}\n",
            encoding="utf-8",
        )

    assert main([
        "--base",
        str(tmp_path),
        "legacy",
        "l2-typed-migration-packet",
        "--legacy-l2-dir",
        str(l2),
        "--compact",
    ]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["kind"] == "legacy_l2_typed_migration_packet_progress"
    assert payload["source_surface"] == "legacy_l2_typed_migration_packet"
    assert payload["legacy_l2_dir"] == str(l2)
    assert payload["typed_migration_status"] == "needs_review"
    assert payload["work_item_count"] == 125
    assert payload["work_item_counts_by_kind"] == {
        "entry": 2,
        "graph_edge": 1,
        "graph_node": 1,
        "graph_step": 120,
        "graph_tower": 1,
    }
    assert payload["review_group_counts"] == {
        "memory_entry_record": 3,
        "object_relation_record": 1,
        "physics_object_record": 1,
        "sensemaking_report_record": 120,
    }
    assert payload["next_action_count"] == 7
    assert payload["next_action_refs"] == [
        "review_legacy_l2_memory_entry_candidates",
        "review_legacy_l2_graph_nodes_for_physics_objects",
        "review_legacy_l2_graph_edges_for_object_relations",
        "review_legacy_l2_steps_for_sensemaking_reports",
        "review_legacy_l2_towers_for_memory_entries",
    ]
    assert payload["top_review_group_surfaces"] == [
        "memory_entry_record",
        "object_relation_record",
        "physics_object_record",
        "sensemaking_report_record",
    ]
    assert payload["semantic_lossless_proven"] is False
    assert payload["truth_source"] == "legacy_l2_filesystem"
    assert payload["summary_inputs_trusted"] is False
    assert payload["orientation_only"] is True
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False
