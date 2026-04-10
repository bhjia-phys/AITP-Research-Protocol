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

from knowledge_hub.l2_hygiene import materialize_workspace_hygiene_report


class L2HygieneTests(unittest.TestCase):
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
        updated_at: str = "2026-04-05T00:00:00+08:00",
        tags: list[str] | None = None,
        dependencies: list[str] | None = None,
        related_units: list[str] | None = None,
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
            "updated_at": updated_at,
            "topic_completion_status": "promotion-ready",
            "tags": tags or [],
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
            "dependencies": dependencies or [],
            "related_units": related_units or [],
            "payload": {},
        }
        (target_dir / f"{unit_id.split(':', 1)[1]}.json").write_text(
            json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_materialize_workspace_hygiene_report_handles_empty_store(self) -> None:
        result = materialize_workspace_hygiene_report(self.kernel_root)
        payload = result["payload"]
        self.assertEqual(payload["summary"]["total_units"], 0)
        self.assertTrue(payload["summary"]["empty_canonical_store"])
        self.assertEqual(payload["summary"]["total_findings"], 0)
        self.assertTrue(Path(result["json_path"]).exists())
        self.assertTrue(Path(result["markdown_path"]).exists())
        markdown = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("No canonical units were found", markdown)

    def test_materialize_workspace_hygiene_report_surfaces_bounded_findings(self) -> None:
        self._write_unit(
            "concepts",
            "concept:old-summary",
            "concept",
            "Old summary",
            "Old summary",
            updated_at="2024-01-01T00:00:00+08:00",
            tags=["legacy"],
        )
        self._write_unit(
            "methods",
            "method:green-method",
            "method",
            "Green method",
            "Reusable method for green transport.",
            tags=["green", "transport"],
            dependencies=["concept:old-summary"],
        )
        self._write_unit(
            "workflows",
            "workflow:green-workflow",
            "workflow",
            "Green workflow",
            "Reusable workflow for green transport calculations.",
            tags=["green", "transport"],
        )
        self._write_unit(
            "warning-notes",
            "warning_note:scope-warning",
            "warning_note",
            "Scope warning",
            "Warn about scope drift.",
            related_units=["method:green-method"],
        )
        self._write_unit(
            "claim-cards",
            "claim_card:claim-a",
            "claim_card",
            "Claim A",
            "First claim summary.",
            tags=["conflict"],
        )
        self._write_unit(
            "claim-cards",
            "claim_card:claim-b",
            "claim_card",
            "Claim B",
            "Second claim summary.",
            tags=["conflict"],
        )
        (self.canonical_root / "edges.jsonl").write_text(
            json.dumps({"source": "claim_card:claim-a", "relation": "contradicts", "target": "claim_card:claim-b"})
            + "\n",
            encoding="utf-8",
        )

        result = materialize_workspace_hygiene_report(self.kernel_root)
        payload = result["payload"]

        self.assertEqual(payload["summary"]["total_units"], 6)
        self.assertGreaterEqual(payload["summary"]["total_findings"], 5)
        self.assertEqual(payload["summary"]["status"], "needs_review")
        self.assertTrue(payload["stale_summary_candidates"])
        self.assertTrue(payload["missing_bridge_candidates"])
        self.assertEqual(payload["contradiction_findings"][0]["relation"], "contradicts")
        self.assertTrue(any(row["unit_id"] == "workflow:green-workflow" for row in payload["orphaned_units"]))
        self.assertTrue(any(row["unit_id"] == "method:green-method" for row in payload["weakly_connected_units"]))

        markdown = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("## Stale Summary Candidates", markdown)
        self.assertIn("## Missing Bridge Candidates", markdown)
        self.assertIn("## Contradiction Findings", markdown)
        self.assertIn("workflow:green-workflow", markdown)
