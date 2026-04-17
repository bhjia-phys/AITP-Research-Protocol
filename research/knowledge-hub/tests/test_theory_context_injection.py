from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from knowledge_hub import theory_context_injection  # noqa: E402


class _StubService:
    def __init__(self, kernel_root: Path) -> None:
        self.kernel_root = kernel_root

    def _runtime_root(self, topic_slug: str) -> Path:
        return self.kernel_root / "topics" / topic_slug / "runtime"

    def _relativize(self, path: Path) -> str:
        return path.relative_to(self.kernel_root).as_posix()


class TheoryContextInjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.kernel_root = Path(self._tmpdir.name)
        self.service = _StubService(self.kernel_root)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_build_prerequisite_fragment_handles_long_fresh_topic_names(self) -> None:
        kernel_root = (
            Path(self._tmpdir.name)
            / "windows-path-margin"
            / "fresh-formal-positive-l2"
        )
        service = _StubService(kernel_root)
        topic_slug = "fresh-jones-finite-dimensional-factor-closure"
        candidate_id = "candidate:jones-ch4-finite-product"
        formal_review_path = (
            kernel_root
            / "validation"
            / "topics"
            / topic_slug
            / "runs"
            / "run-001"
            / "theory-packets"
            / "candidate-jones-ch4-finite-product"
            / "formal_theory_review.json"
        )
        prerequisite_path = (
            kernel_root
            / "validation"
            / "topics"
            / topic_slug
            / "runs"
            / "run-001"
            / "theory-packets"
            / "candidate-jones-ch4-finite-product"
            / "prerequisite_closure_review.json"
        )
        formal_review_path.parent.mkdir(parents=True, exist_ok=True)
        formal_review_path.write_text(
            json.dumps(
                {
                    "prerequisite_closure_status": "closed",
                    "lean_prerequisite_ids": [
                        "AITP.Jones2015.jonesFiniteDimensionalTypeIClassificationTheoremPacket"
                    ],
                    "prerequisite_notes": "Fresh-topic prerequisite closure is ready.",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        prerequisite_path.write_text(
            json.dumps(
                {
                    "status": "closed",
                    "lean_prerequisite_ids": [
                        "AITP.Jones2015.jonesFiniteDimensionalBlockCentralizerFiberPiTypeIPacket"
                    ],
                    "notes": "Secondary prerequisite packet is ready.",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = theory_context_injection._build_prerequisite_fragment(
            service,
            topic_slug=topic_slug,
            candidate_id=candidate_id,
            formal_theory_review_path=formal_review_path,
            prerequisite_closure_review_path=prerequisite_path,
            target_paths=["topics/demo-topic/runtime/statement_compilation.active.md"],
        )

        self.assertIsNotNone(payload)
        self.assertTrue((kernel_root / payload["json_path"]).exists())
        self.assertTrue((kernel_root / payload["path"]).exists())
        self.assertLessEqual(len(str(kernel_root / payload["json_path"])), 259)
        self.assertLessEqual(len(str(kernel_root / payload["path"])), 259)
