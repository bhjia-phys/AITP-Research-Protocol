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
