from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

import sys


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub import mcp_server


def _parse(result: str) -> dict:
    data = json.loads(result)
    if not isinstance(data, dict):
        raise AssertionError("mcp result must be JSON object")
    return data


class _HubStubSuccess:
    def ingest_sources(self, sources: list[str], source_kind: str = "auto") -> dict:
        return {
            "ingested": len(sources),
            "failed": 0,
            "documents": [{"doc_id": "d1", "kind": source_kind}],
            "failures": [],
        }

    def query(
        self,
        question: str,
        top_k: int = 6,
        include_zotero: bool = True,
        max_claims: int = 3,
        min_local_score: float = 0.0,
    ) -> dict:
        return {
            "query_id": "q-test",
            "question": question,
            "answer": "answer",
            "claims": [
                {
                    "claim_id": "claim-01",
                    "text": "sample claim text.",
                    "evidence_refs": ["local:d1:c001"],
                    "confidence": "medium",
                }
            ],
            "citations": [
                {
                    "source_type": "local",
                    "ref_id": "local:d1:c001",
                    "title": "Doc",
                    "snippet": "snippet",
                    "metadata": {"score": 1},
                }
            ],
            "created_at": "2026-02-19T00:00:00+00:00",
            "top_k": top_k,
            "include_zotero": include_zotero,
            "max_claims": max_claims,
            "min_local_score": min_local_score,
        }

    def get_provenance(self, query_id: str) -> dict:
        return {"query_id": query_id, "answer": "stored"}

    def export_obsidian(
        self,
        query_id: str,
        note_title: str,
        vault_path: str | None = None,
        output_subdir: str = "07 Knowledge Hub",
    ) -> dict:
        return {
            "query_id": query_id,
            "note_path": f"/tmp/{note_title}.md",
            "vault_path": vault_path,
            "output_subdir": output_subdir,
        }

    def refresh_index(self, force_rebuild: bool = False) -> dict:
        return {
            "zotero_status": {"status": "ok"},
            "rebuild": {"requested": force_rebuild},
        }


class _HubStubFailure:
    def ingest_sources(self, sources: list[str], source_kind: str = "auto") -> dict:
        raise RuntimeError("ingest boom")

    def query(
        self,
        question: str,
        top_k: int = 6,
        include_zotero: bool = True,
        max_claims: int = 3,
        min_local_score: float = 0.0,
    ) -> dict:
        raise RuntimeError("query boom")

    def get_provenance(self, query_id: str) -> dict:
        raise RuntimeError("provenance boom")

    def export_obsidian(
        self,
        query_id: str,
        note_title: str,
        vault_path: str | None = None,
        output_subdir: str = "07 Knowledge Hub",
    ) -> dict:
        raise RuntimeError("export boom")

    def refresh_index(self, force_rebuild: bool = False) -> dict:
        raise RuntimeError("refresh boom")


class MCPServerToolTests(unittest.TestCase):
    def test_hub_tools_return_success_payloads(self) -> None:
        with patch.object(mcp_server, "hub", _HubStubSuccess()):
            ingest = _parse(
                mcp_server.hub_ingest_sources(["a", "b"], source_kind="inline")
            )
            query = _parse(
                mcp_server.hub_query(
                    "What is this?",
                    top_k=4,
                    include_zotero=False,
                    max_claims=2,
                    min_local_score=0.4,
                )
            )
            provenance = _parse(mcp_server.hub_get_provenance("q-test"))
            exported = _parse(mcp_server.hub_export_obsidian("q-test", "Demo Note"))
            refreshed = _parse(mcp_server.hub_refresh_index(force_rebuild=True))

        self.assertEqual(ingest["status"], "success")
        self.assertEqual(ingest["ingested"], 2)

        self.assertEqual(query["status"], "success")
        self.assertEqual(query["query_id"], "q-test")
        self.assertEqual(query["max_claims"], 2)
        self.assertEqual(query["min_local_score"], 0.4)

        self.assertEqual(provenance["status"], "success")
        self.assertEqual(provenance["record"]["query_id"], "q-test")

        self.assertEqual(exported["status"], "success")
        self.assertTrue(exported["note_path"].endswith("Demo Note.md"))

        self.assertEqual(refreshed["status"], "success")
        self.assertTrue(refreshed["rebuild"]["requested"])

    def test_hub_tools_return_error_shape_when_exceptions_occur(self) -> None:
        with patch.object(mcp_server, "hub", _HubStubFailure()):
            results = [
                _parse(mcp_server.hub_ingest_sources(["x"])),
                _parse(mcp_server.hub_query("x")),
                _parse(mcp_server.hub_get_provenance("x")),
                _parse(mcp_server.hub_export_obsidian("x", "y")),
                _parse(mcp_server.hub_refresh_index()),
            ]

        for result in results:
            self.assertEqual(result["status"], "error")
            self.assertIn("boom", result["error"])
            self.assertIn("Traceback", result["traceback"])


if __name__ == "__main__":
    unittest.main()
