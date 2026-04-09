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


if __name__ == "__main__":
    unittest.main()
