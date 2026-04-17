from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import sys


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.l2_compiler import materialize_workspace_graph_report, materialize_workspace_memory_map


class L2CompilerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.kernel_root = Path(self.tempdir.name)
        self.repo_kernel_root = Path(__file__).resolve().parents[1]
        self.canonical_root = self.kernel_root / "canonical"
        self.canonical_root.mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            self.repo_kernel_root / "canonical" / "canonical-unit.schema.json",
            self.canonical_root / "canonical-unit.schema.json",
        )
        shutil.copy2(
            self.repo_kernel_root / "canonical" / "retrieval_profiles.json",
            self.canonical_root / "retrieval_profiles.json",
        )
        (self.canonical_root / "index.jsonl").write_text("", encoding="utf-8")
        (self.canonical_root / "edges.jsonl").write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write_unit(
        self,
        relative_dir: str,
        unit_id: str,
        unit_type: str,
        title: str,
        summary: str,
        *,
        origin_topic_refs: list[str] | None = None,
        validation_receipts: list[str] | None = None,
        reuse_receipts: list[str] | None = None,
        applicable_topics: list[str] | None = None,
    ) -> None:
        target_dir = self.canonical_root / relative_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "id": unit_id,
            "unit_type": unit_type,
            "title": title,
            "summary": summary,
            "maturity": "stable",
            "created_at": "2026-04-05T00:00:00+08:00",
            "updated_at": "2026-04-05T00:00:00+08:00",
            "topic_completion_status": "promotion-ready",
            "tags": ["demo"],
            "assumptions": [],
            "regime": {
                "domain": "demo",
                "approximations": [],
                "scale": "demo",
                "boundary_conditions": [],
                "exclusions": [],
            },
            "scope": {
                "applies_to": ["demo"],
                "out_of_scope": [],
            },
            "provenance": {
                "source_ids": ["source:demo"],
                "l1_artifacts": [],
                "l3_runs": [],
                "l4_checks": [],
                "citations": [],
            },
            "promotion": {
                "route": "L3->L4->L2",
                "promoted_by": "test",
                "promoted_at": "2026-04-05T00:00:00+08:00",
                "review_status": "accepted",
                "rationale": "test payload",
            },
            "dependencies": [],
            "related_units": [],
            "origin_topic_refs": list(origin_topic_refs or []),
            "origin_run_refs": [],
            "validation_receipts": list(validation_receipts or []),
            "reuse_receipts": list(reuse_receipts or []),
            "related_consultation_refs": [],
            "applicable_topics": list(applicable_topics or []),
            "failed_topics": [],
            "regime_notes": [],
            "payload": {},
        }
        (target_dir / f"{unit_id.split(':', 1)[1]}.json").write_text(
            json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_materialize_workspace_memory_map_handles_empty_store(self) -> None:
        result = materialize_workspace_memory_map(self.kernel_root)
        payload = result["payload"]
        self.assertEqual(payload["summary"]["total_units"], 0)
        self.assertTrue(payload["summary"]["empty_canonical_store"])
        self.assertTrue(Path(result["json_path"]).exists())
        self.assertTrue(Path(result["markdown_path"]).exists())
        markdown = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("No canonical units were found", markdown)

    def test_materialize_workspace_memory_map_groups_units_for_consultation_and_reuse(self) -> None:
        self._write_unit("concepts", "concept:green-function", "concept", "Green function", "Core concept.")
        self._write_unit("workflows", "workflow:gw-check", "workflow", "GW check", "Reusable workflow.")
        self._write_unit("methods", "method:rpa-fit", "method", "RPA fit", "Reusable method.")
        self._write_unit("warning-notes", "warning_note:scope-trap", "warning_note", "Scope trap", "Portable warning.")
        self._write_unit(
            "validation-patterns",
            "validation_pattern:baseline-compare",
            "validation_pattern",
            "Baseline compare",
            "Reusable validation pattern.",
        )
        self._write_unit("bridges", "bridge:qft-condmat", "bridge", "QFT bridge", "Cross-topic bridge.")
        self._write_unit(
            "workflows",
            "topic_skill_projection:demo-route",
            "topic_skill_projection",
            "Demo route",
            "Reusable projection.",
        )
        (self.canonical_root / "edges.jsonl").write_text(
            json.dumps({"source": "workflow:gw-check", "relation": "warned_by", "target": "warning_note:scope-trap"})
            + "\n",
            encoding="utf-8",
        )

        result = materialize_workspace_memory_map(self.kernel_root)
        payload = result["payload"]

        self.assertEqual(payload["summary"]["total_units"], 7)
        self.assertFalse(payload["summary"]["empty_canonical_store"])
        self.assertIn("workflow", payload["summary"]["unit_types_present"])
        self.assertIn("topic_skill_projection", payload["summary"]["unit_types_present"])

        l1_entry = payload["consultation_entrypoints"]["l1_provisional_understanding"]
        l3_entry = payload["consultation_entrypoints"]["l3_candidate_formation"]
        l4_entry = payload["consultation_entrypoints"]["l4_adjudication"]
        self.assertGreaterEqual(l1_entry["available_count"], 3)
        self.assertTrue(any(unit["unit_type"] == "workflow" for unit in l1_entry["units"]))
        self.assertTrue(any(unit["unit_type"] == "method" for unit in l3_entry["units"]))
        self.assertTrue(any(unit["unit_type"] == "validation_pattern" for unit in l4_entry["units"]))

        reuse = payload["reuse_families"]
        self.assertEqual(reuse["workflows"]["count"], 1)
        self.assertEqual(reuse["methods"]["count"], 1)
        self.assertEqual(reuse["warnings"]["count"], 1)
        self.assertEqual(reuse["validation_patterns"]["count"], 1)
        self.assertEqual(reuse["bridges"]["count"], 1)
        self.assertEqual(reuse["topic_skill_projections"]["count"], 1)

        relation_summary = payload["relation_summary"]
        self.assertEqual(relation_summary["edge_count"], 1)
        self.assertEqual(relation_summary["edges_by_kind"]["warned_by"], 1)

        markdown = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("## Consultation Entry Points", markdown)
        self.assertIn("## Reuse Families", markdown)
        self.assertIn("workflow:gw-check", markdown)
        self.assertIn("topic_skill_projection:demo-route", markdown)

    def test_materialize_workspace_memory_map_writes_obsidian_l2_mirror_with_topic_linked_evidence(self) -> None:
        self._write_unit(
            "methods",
            "method:rpa-fit",
            "method",
            "RPA fit",
            "Reusable method.",
            origin_topic_refs=["topics/demo-topic"],
            validation_receipts=["topics/demo-topic/L4/runs/run-001/returned_execution_result.json"],
            reuse_receipts=["topics/other-topic/runtime/plan_reuse_context.json"],
        )

        result = materialize_workspace_memory_map(self.kernel_root)

        obsidian_root = Path(result["obsidian_root"])
        self.assertTrue(obsidian_root.exists())
        self.assertTrue((obsidian_root / "index.md").exists())
        self.assertTrue((obsidian_root / "families" / "methods").exists())

        method_page = obsidian_root / "families" / "methods" / "method--rpa-fit.md"
        self.assertTrue(method_page.exists())
        method_markdown = method_page.read_text(encoding="utf-8")
        self.assertIn("## Origin", method_markdown)
        self.assertIn("topics/demo-topic", method_markdown)
        self.assertIn("## Validated In Topics", method_markdown)
        self.assertIn("returned_execution_result.json", method_markdown)
        self.assertIn("## Reused In Topics", method_markdown)
        self.assertIn("plan_reuse_context.json", method_markdown)
        self.assertIn("## Canonical Links", method_markdown)

    def test_materialize_workspace_memory_map_writes_obsidian_family_profile_and_topic_shelves(self) -> None:
        self._write_unit(
            "concepts",
            "concept:green-function",
            "concept",
            "Green function",
            "Core concept.",
            origin_topic_refs=["topics/demo-topic"],
            applicable_topics=["demo-topic"],
        )
        self._write_unit(
            "methods",
            "method:rpa-fit",
            "method",
            "RPA fit",
            "Reusable method.",
            origin_topic_refs=["topics/demo-topic"],
            reuse_receipts=["topics/demo-topic/L3/runs/run-001/iterations/iteration-001/plan.contract.json"],
            applicable_topics=["demo-topic"],
        )
        self._write_unit(
            "workflows",
            "workflow:gw-check",
            "workflow",
            "GW check",
            "Reusable workflow.",
            origin_topic_refs=["topics/demo-topic"],
            validation_receipts=["topics/demo-topic/L4/runs/run-001/returned_execution_result.json"],
            applicable_topics=["demo-topic"],
        )

        result = materialize_workspace_memory_map(self.kernel_root)

        obsidian_root = Path(result["obsidian_root"])
        family_index = obsidian_root / "families" / "methods" / "index.md"
        profile_index = obsidian_root / "profiles" / "l3_plan_reuse_standard.md"
        idea_profile = obsidian_root / "profiles" / "l3_idea_reuse_quick.md"
        topic_index = obsidian_root / "topics" / "demo-topic.md"

        self.assertTrue(family_index.exists())
        self.assertTrue(profile_index.exists())
        self.assertTrue(idea_profile.exists())
        self.assertTrue(topic_index.exists())

        family_markdown = family_index.read_text(encoding="utf-8")
        self.assertIn("[[method--rpa-fit|RPA fit]]", family_markdown)

        profile_markdown = profile_index.read_text(encoding="utf-8")
        self.assertIn("[[families/methods/method--rpa-fit|RPA fit]]", profile_markdown)
        self.assertIn("[[families/workflows/workflow--gw-check|GW check]]", profile_markdown)

        idea_profile_markdown = idea_profile.read_text(encoding="utf-8")
        self.assertIn("[[families/concepts/concept--green-function|Green function]]", idea_profile_markdown)
        self.assertNotIn("method--rpa-fit", idea_profile_markdown)

        topic_markdown = topic_index.read_text(encoding="utf-8")
        self.assertIn("[[families/concepts/concept--green-function|Green function]]", topic_markdown)
        self.assertIn("[[families/methods/method--rpa-fit|RPA fit]]", topic_markdown)
        self.assertIn("returned_execution_result.json", topic_markdown)
        self.assertIn("plan.contract.json", topic_markdown)

    def test_materialize_workspace_memory_map_topic_shelf_splits_origin_validated_reused_and_failed_sections(self) -> None:
        self._write_unit(
            "concepts",
            "concept:green-function",
            "concept",
            "Green function",
            "Core concept.",
            origin_topic_refs=["topics/demo-topic"],
            applicable_topics=["demo-topic"],
        )
        self._write_unit(
            "workflows",
            "workflow:gw-check",
            "workflow",
            "GW check",
            "Reusable workflow.",
            validation_receipts=["topics/demo-topic/L4/runs/run-001/returned_execution_result.json"],
            applicable_topics=["demo-topic"],
        )
        self._write_unit(
            "methods",
            "method:rpa-fit",
            "method",
            "RPA fit",
            "Reusable method.",
            reuse_receipts=["topics/demo-topic/L3/runs/run-001/iterations/iteration-001/plan.contract.json"],
            applicable_topics=["demo-topic"],
        )
        self._write_unit(
            "warning-notes",
            "warning_note:scope-trap",
            "warning_note",
            "Scope trap",
            "Portable warning.",
            applicable_topics=["demo-topic"],
        )
        warning_path = self.canonical_root / "warning-notes" / "scope-trap.json"
        warning_payload = json.loads(warning_path.read_text(encoding="utf-8"))
        warning_payload["failed_topics"] = ["demo-topic"]
        warning_path.write_text(json.dumps(warning_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

        result = materialize_workspace_memory_map(self.kernel_root)

        topic_markdown = (Path(result["obsidian_root"]) / "topics" / "demo-topic.md").read_text(encoding="utf-8")
        self.assertIn("## Origin Units", topic_markdown)
        self.assertIn("## Validated In Topic", topic_markdown)
        self.assertIn("## Reused In Topic", topic_markdown)
        self.assertIn("## Failed Or Limited In Topic", topic_markdown)
        self.assertIn("[[families/concepts/concept--green-function|Green function]]", topic_markdown)
        self.assertIn("[[families/workflows/workflow--gw-check|GW check]]", topic_markdown)
        self.assertIn("[[families/methods/method--rpa-fit|RPA fit]]", topic_markdown)
        self.assertIn("[[families/warning-notes/warning_note--scope-trap|Scope trap]]", topic_markdown)

    def test_materialize_workspace_memory_map_profile_shelf_splits_core_warnings_workflows_projections_and_reuse(self) -> None:
        self._write_unit(
            "concepts",
            "concept:green-function",
            "concept",
            "Green function",
            "Core concept.",
        )
        self._write_unit(
            "warning-notes",
            "warning_note:scope-trap",
            "warning_note",
            "Scope trap",
            "Portable warning.",
        )
        self._write_unit(
            "workflows",
            "workflow:gw-check",
            "workflow",
            "GW check",
            "Reusable workflow.",
        )
        self._write_unit(
            "topic-skill-projections",
            "topic_skill_projection:demo-route",
            "topic_skill_projection",
            "Demo route",
            "Reusable projection.",
        )
        self._write_unit(
            "methods",
            "method:rpa-fit",
            "method",
            "RPA fit",
            "Reusable method.",
            reuse_receipts=["topics/demo-topic/L3/runs/run-001/iterations/iteration-001/plan.contract.json"],
        )

        result = materialize_workspace_memory_map(self.kernel_root)

        profile_markdown = (
            Path(result["obsidian_root"]) / "profiles" / "l3_plan_reuse_standard.md"
        ).read_text(encoding="utf-8")
        self.assertIn("## Core Hits", profile_markdown)
        self.assertIn("## Warnings", profile_markdown)
        self.assertIn("## Workflows", profile_markdown)
        self.assertIn("## Topic Skill Projections", profile_markdown)
        self.assertIn("## Recently Reused Units", profile_markdown)
        self.assertIn("[[families/concepts/concept--green-function|Green function]]", profile_markdown)
        self.assertIn("[[families/warning-notes/warning_note--scope-trap|Scope trap]]", profile_markdown)
        self.assertIn("[[families/workflows/workflow--gw-check|GW check]]", profile_markdown)
        self.assertIn("[[families/topic-skill-projections/topic_skill_projection--demo-route|Demo route]]", profile_markdown)
        self.assertIn("[[families/methods/method--rpa-fit|RPA fit]]", profile_markdown)

    def test_materialize_workspace_graph_report_writes_navigation_pages(self) -> None:
        self._write_unit("concepts", "concept:green-function", "concept", "Green function", "Core concept.")
        self._write_unit("workflows", "workflow:gw-check", "workflow", "GW check", "Reusable workflow.")
        self._write_unit("methods", "method:rpa-fit", "method", "RPA fit", "Reusable method.")
        self._write_unit("warning-notes", "warning_note:scope-trap", "warning_note", "Scope trap", "Portable warning.")
        (self.canonical_root / "edges.jsonl").write_text(
            "\n".join(
                [
                    json.dumps({"source": "workflow:gw-check", "relation": "uses_method", "target": "method:rpa-fit"}),
                    json.dumps({"source": "workflow:gw-check", "relation": "warned_by", "target": "warning_note:scope-trap"}),
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        result = materialize_workspace_graph_report(self.kernel_root)
        payload = result["payload"]

        self.assertTrue(Path(result["json_path"]).exists())
        self.assertTrue(Path(result["markdown_path"]).exists())
        self.assertTrue(Path(result["navigation_index_path"]).exists())
        self.assertGreaterEqual(result["navigation_page_count"], 4)
        self.assertEqual(payload["hub_units"][0]["unit_id"], "workflow:gw-check")
        self.assertEqual(payload["hub_units"][0]["degree"], 2)
        self.assertEqual(payload["summary"]["connected_unit_count"], 3)
        self.assertEqual(payload["summary"]["isolated_unit_count"], 1)

        navigation_index = Path(result["navigation_index_path"]).read_text(encoding="utf-8")
        self.assertIn("[[workflow--gw-check|GW check]]", navigation_index)

        workflow_page = Path(result["navigation_root"]) / "workflow--gw-check.md"
        self.assertTrue(workflow_page.exists())
        workflow_markdown = workflow_page.read_text(encoding="utf-8")
        self.assertIn("## Outgoing Relations", workflow_markdown)
        self.assertIn("[[method--rpa-fit|RPA fit]]", workflow_markdown)
        self.assertIn("[[warning_note--scope-trap|Scope trap]]", workflow_markdown)
