from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.hub import KnowledgeHub


class KnowledgeHubCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmpdir.name)
        self.data_root = self.tmp_path / "data"
        self.vault_root = self.tmp_path / "vault"
        self.hub = KnowledgeHub(
            data_root=self.data_root,
            default_vault_path=str(self.vault_root),
        )

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_ingest_inline_source_writes_documents_store(self) -> None:
        result = self.hub.ingest_sources(
            ["Modular flow appears in Tomita-Takesaki theory."],
            source_kind="inline",
        )

        self.assertEqual(result["ingested"], 1)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["documents"][0]["kind"], "inline")

        docs = json.loads(
            (self.data_root / "documents.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(docs), 1)
        doc = next(iter(docs.values()))
        self.assertGreaterEqual(len(doc["chunks"]), 1)

    def test_ingest_file_auto_detects_file_kind(self) -> None:
        source_file = self.tmp_path / "paper.txt"
        source_file.write_text(
            "The argument flow starts from assumptions and ends with corollaries.",
            encoding="utf-8",
        )

        result = self.hub.ingest_sources([str(source_file)], source_kind="auto")
        self.assertEqual(result["ingested"], 1)
        self.assertEqual(result["documents"][0]["kind"], "file")
        self.assertEqual(result["documents"][0]["title"], "paper.txt")

    def test_query_persists_record_with_local_citations(self) -> None:
        self.hub.ingest_sources(
            ["Modular flow and modular Hamiltonian are discussed in this paragraph."],
            source_kind="inline",
        )

        record = self.hub.query("What is modular flow?", top_k=3, include_zotero=False)
        self.assertTrue(record["query_id"].startswith("q-"))
        self.assertGreaterEqual(len(record["citations"]), 1)
        self.assertTrue(all(c["source_type"] == "local" for c in record["citations"]))
        self.assertGreaterEqual(len(record.get("claims", [])), 1)

        first_meta = record["citations"][0]["metadata"]
        self.assertIn("bm25_score", first_meta)
        self.assertIn("coverage", first_meta)
        self.assertIn("phrase_hit", first_meta)

        record_path = self.data_root / "queries" / f"{record['query_id']}.json"
        self.assertTrue(record_path.exists())
        stored = json.loads(record_path.read_text(encoding="utf-8"))
        self.assertEqual(stored["question"], "What is modular flow?")

    def test_query_bm25_prefers_higher_term_signal(self) -> None:
        self.hub.ingest_sources(
            [
                "modular flow modular flow modular flow tomita takesaki",
                "modular flow appears once",
            ],
            source_kind="inline",
        )

        record = self.hub.query("modular flow", top_k=2, include_zotero=False)
        self.assertEqual(len(record["citations"]), 2)

        first_score = record["citations"][0]["metadata"]["score"]
        second_score = record["citations"][1]["metadata"]["score"]
        self.assertGreater(first_score, second_score)

    def test_query_respects_min_local_score_filter(self) -> None:
        self.hub.ingest_sources(
            [
                "modular flow modular flow modular flow with long context and stable evidence text",
                "modular flow",
            ],
            source_kind="inline",
        )

        low_threshold = self.hub.query(
            "modular flow",
            top_k=5,
            include_zotero=False,
            min_local_score=0.0,
        )
        high_threshold = self.hub.query(
            "modular flow",
            top_k=5,
            include_zotero=False,
            min_local_score=100.0,
        )

        self.assertGreaterEqual(len(low_threshold["citations"]), 1)
        self.assertEqual(len(high_threshold["citations"]), 0)

    def test_claim_quality_gate_filters_short_and_duplicate_claims(self) -> None:
        citations = [
            {
                "source_type": "local",
                "ref_id": "local:d1:c001",
                "snippet": "Modular flow generates state evolution in operator algebraic form and provides a stable inferential path for thermal interpretation.",
                "metadata": {"score": 2.1},
            },
            {
                "source_type": "local",
                "ref_id": "local:d2:c001",
                "snippet": "Modular flow generates state evolution in operator algebraic form and provides a stable inferential path for thermal interpretation.",
                "metadata": {"score": 1.9},
            },
            {
                "source_type": "local",
                "ref_id": "local:d3:c001",
                "snippet": "too short",
                "metadata": {"score": 5.0},
            },
            {
                "source_type": "local",
                "ref_id": "",
                "snippet": "This is long enough but has no reference id so it should be dropped by the claim quality gate.",
                "metadata": {"score": 5.0},
            },
        ]

        claims = self.hub._derive_claims(
            question="What is modular flow?", citations=citations, max_claims=3
        )

        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["evidence_refs"], ["local:d1:c001"])
        self.assertEqual(claims[0]["confidence"], "high")

    def test_get_provenance_raises_for_unknown_query(self) -> None:
        with self.assertRaises(FileNotFoundError):
            self.hub.get_provenance("q-not-found")

    def test_export_obsidian_creates_note_with_evidence_section(self) -> None:
        self.hub.ingest_sources(
            ["This source explains K-complexity with an evidence-first summary."],
            source_kind="inline",
        )
        record = self.hub.query("Summarize K-complexity", include_zotero=False)

        exported = self.hub.export_obsidian(
            query_id=record["query_id"],
            note_title="K-complexity: quick notes",
        )

        note_path = Path(exported["note_path"])
        self.assertTrue(note_path.exists())
        content = note_path.read_text(encoding="utf-8")
        self.assertIn("type: knowledge-hub-note", content)
        self.assertIn("## Claim Map", content)
        self.assertIn("## Evidence", content)
        self.assertIn("1. [local]", content)

    def test_refresh_index_uses_zotero_status_and_rebuild_flag(self) -> None:
        fake_status = {
            "collection_info": {"name": "zotero_library", "count": 2164},
            "status": "ok",
        }
        with patch.object(self.hub, "_get_zotero_status", return_value=fake_status):
            result = self.hub.refresh_index(force_rebuild=True)

        self.assertEqual(result["zotero_status"], fake_status)
        self.assertTrue(result["rebuild"]["requested"])


if __name__ == "__main__":
    unittest.main()
