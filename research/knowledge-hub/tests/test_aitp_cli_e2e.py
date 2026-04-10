from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class AITPCLIE2ETests(unittest.TestCase):
    def setUp(self) -> None:
        self.package_root = Path(__file__).resolve().parents[1]
        self.repo_root = Path(__file__).resolve().parents[3]
        self._tmpdir = tempfile.TemporaryDirectory()
        self.kernel_root = Path(self._tmpdir.name) / "kernel"
        shutil.copytree(self.package_root / "canonical", self.kernel_root / "canonical", dirs_exist_ok=True)
        shutil.copytree(self.package_root / "schemas", self.kernel_root / "schemas", dirs_exist_ok=True)
        (self.kernel_root / "runtime" / "schemas").mkdir(parents=True, exist_ok=True)
        bundle_schema = self.package_root / "runtime" / "schemas" / "progressive-disclosure-runtime-bundle.schema.json"
        (self.kernel_root / "runtime" / "schemas" / bundle_schema.name).write_text(
            bundle_schema.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            "-m",
            "knowledge_hub.aitp_cli",
            "--kernel-root",
            str(self.kernel_root),
            "--repo-root",
            str(self.repo_root),
            *args,
        ]
        return subprocess.run(
            command,
            cwd=self.package_root,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_stage_negative_result_human_output_and_writeback(self) -> None:
        completed = self._run_cli(
            "stage-negative-result",
            "--title",
            "Portability route failed",
            "--summary",
            "The larger-system extrapolation failed.",
            "--failure-kind",
            "regime_mismatch",
        )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn("status: staged", completed.stdout)
        self.assertIn("entry id: staging:portability-route-failed", completed.stdout)
        self.assertNotIn("{", completed.stdout)
        self.assertTrue(
            (self.kernel_root / "canonical" / "staging" / "entries" / "staging--portability-route-failed.json").exists()
        )

    def test_record_collaborator_memory_json_and_human_paths(self) -> None:
        human = self._run_cli(
            "record-collaborator-memory",
            "--preference",
            "prefer bounded benchmark-first routes",
        )
        self.assertEqual(human.returncode, 0, msg=human.stderr)
        self.assertIn("memory kind: collaborator_memory", human.stdout)
        self.assertNotIn("{", human.stdout)

        machine = self._run_cli(
            "show-collaborator-memory",
            "--json",
        )
        self.assertEqual(machine.returncode, 0, msg=machine.stderr)
        payload = json.loads(machine.stdout)
        self.assertEqual(payload["collaborator_memory"]["memory_kind"], "collaborator_memory")
        self.assertIn(
            "prefer bounded benchmark-first routes",
            payload["collaborator_memory"]["preferences"],
        )

    def test_status_json_exposes_source_intelligence(self) -> None:
        runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "run-001",
                    "resume_stage": "L1",
                    "research_mode": "formal_derivation",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "Show the runtime source intelligence.",
                    "decision_surface": {
                        "selected_action_id": "action:demo-topic:read",
                        "decision_source": "heuristic",
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "action_queue.jsonl").write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:read",
                    "status": "pending",
                    "action_type": "inspect_resume_state",
                    "summary": "Inspect the runtime source-intelligence summary.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                },
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        demo_source_root = self.kernel_root / "source-layer" / "topics" / "demo-topic"
        demo_source_root.mkdir(parents=True, exist_ok=True)
        (demo_source_root / "source_index.jsonl").write_text(
            json.dumps(
                {
                    "source_id": "paper:demo-source",
                    "source_type": "paper",
                    "title": "Demo source",
                    "summary": "Demo summary with a shared reference.",
                    "references": ["doi:10-1000/shared"],
                    "canonical_source_id": "source_identity:doi:10-1000-demo",
                    "provenance": {
                        "abs_url": "https://example.org/demo",
                    },
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        neighbor_source_root = self.kernel_root / "source-layer" / "topics" / "neighbor-topic"
        neighbor_source_root.mkdir(parents=True, exist_ok=True)
        (neighbor_source_root / "source_index.jsonl").write_text(
            json.dumps(
                {
                    "source_id": "paper:neighbor-source",
                    "source_type": "paper",
                    "title": "Neighbor source",
                    "summary": "Neighbor summary with the same shared reference.",
                    "references": ["doi:10-1000/shared"],
                    "canonical_source_id": "source_identity:doi:10-1000-neighbor",
                    "provenance": {
                        "abs_url": "https://example.org/neighbor",
                    },
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )

        completed = self._run_cli(
            "status",
            "--topic-slug",
            "demo-topic",
            "--json",
        )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["source_intelligence"]["canonical_source_ids"][0], "source_identity:doi:10-1000-demo")
        self.assertEqual(payload["source_intelligence"]["cross_topic_match_count"], 1)
        self.assertEqual(payload["source_intelligence"]["source_neighbors"][0]["relation_kind"], "shared_reference")


if __name__ == "__main__":
    unittest.main()
