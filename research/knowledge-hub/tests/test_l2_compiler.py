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

from knowledge_hub.l2_compiler import materialize_workspace_memory_map


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

    def _write_unit(self, relative_dir: str, unit_id: str, unit_type: str, title: str, summary: str) -> None:
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
