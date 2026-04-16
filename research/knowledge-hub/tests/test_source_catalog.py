from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.source_catalog import (
    materialize_source_catalog,
    materialize_source_citation_traversal,
    materialize_source_family_report,
)


class SourceCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.kernel_root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write_source_row(
        self,
        *,
        topic_slug: str,
        source_id: str,
        source_type: str,
        title: str,
        summary: str,
        canonical_source_id: str | None = None,
        references: list[str] | None = None,
        relevance_tier: str | None = None,
        role_labels: list[str] | None = None,
    ) -> None:
        path = self.kernel_root / "source-layer" / "topics" / topic_slug / "source_index.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        payload = {
            "source_id": source_id,
            "source_type": source_type,
            "title": title,
            "summary": summary,
            "references": list(references or []),
            "provenance": {
                "abs_url": f"https://example.org/{topic_slug}/{source_id.replace(':', '-')}",
            },
        }
        if canonical_source_id:
            payload["canonical_source_id"] = canonical_source_id
        if relevance_tier:
            payload["relevance_tier"] = relevance_tier
        if role_labels is not None:
            payload["role_labels"] = list(role_labels)
        path.write_text(existing + json.dumps(payload, ensure_ascii=True) + "\n", encoding="utf-8")

    def test_materialize_source_catalog_groups_cross_topic_reuse(self) -> None:
        self._write_source_row(
            topic_slug="topic-a",
            source_id="paper:demo-a",
            source_type="paper",
            title="Shared paper",
            summary="Shared source summary.",
            canonical_source_id="source_identity:doi:10-1000-shared-paper",
            references=["doi:10-1000-neighbor-paper"],
        )
        self._write_source_row(
            topic_slug="topic-b",
            source_id="paper:demo-b",
            source_type="paper",
            title="Shared paper copy",
            summary="Same source reused in another topic.",
            canonical_source_id="source_identity:doi:10-1000-shared-paper",
            references=["doi:10-1000-neighbor-paper"],
        )
        self._write_source_row(
            topic_slug="topic-c",
            source_id="paper:neighbor",
            source_type="paper",
            title="Neighbor paper",
            summary="Neighbor source summary.",
            canonical_source_id="source_identity:doi:10-1000-neighbor-paper",
            references=[],
        )

        result = materialize_source_catalog(self.kernel_root)
        payload = result["payload"]

        self.assertTrue(Path(result["json_path"]).exists())
        self.assertTrue(Path(result["markdown_path"]).exists())
        self.assertEqual(payload["summary"]["total_topics"], 3)
        self.assertEqual(payload["summary"]["total_source_rows"], 3)
        self.assertEqual(payload["summary"]["unique_canonical_source_count"], 2)
        self.assertEqual(payload["summary"]["multi_topic_source_count"], 1)
        self.assertEqual(payload["summary"]["linked_reference_edge_count"], 1)

        shared = payload["sources"][0]
        self.assertEqual(shared["canonical_source_id"], "source_identity:doi:10-1000-shared-paper")
        self.assertEqual(shared["topic_count"], 2)
        self.assertEqual(shared["occurrence_count"], 2)
        self.assertIn("topic-a", shared["topic_slugs"])
        self.assertIn("topic-b", shared["topic_slugs"])
        self.assertEqual(shared["linked_canonical_source_ids"][0], "source_identity:doi:10-1000-neighbor-paper")

        markdown = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("## Cross-Topic Reused Sources", markdown)
        self.assertIn("source_identity:doi:10-1000-shared-paper", markdown)
        self.assertIn("## Reference-Linked Sources", markdown)

    def test_materialize_source_catalog_handles_empty_source_layer(self) -> None:
        result = materialize_source_catalog(self.kernel_root)
        payload = result["payload"]
        self.assertTrue(payload["summary"]["empty_source_store"])
        self.assertEqual(payload["summary"]["unique_canonical_source_count"], 0)
        markdown = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("No source-layer topic indexes were found", markdown)

    def test_materialize_source_catalog_tracks_relevance_tiers_and_role_labels(self) -> None:
        self._write_source_row(
            topic_slug="topic-a",
            source_id="paper:foundational-review",
            source_type="paper",
            title="Foundational review paper",
            summary="A foundational review of the topic.",
            canonical_source_id="source_identity:doi:10-1000-foundational-review",
            relevance_tier="canonical",
            role_labels=["foundational", "review"],
        )
        self._write_source_row(
            topic_slug="topic-b",
            source_id="paper:key-result",
            source_type="paper",
            title="Modern key result paper",
            summary="A modern key result for the topic.",
            canonical_source_id="source_identity:doi:10-1000-modern-key-result",
            relevance_tier="must_read",
            role_labels=["modern_reference", "key_result"],
        )

        result = materialize_source_catalog(self.kernel_root)
        payload = result["payload"]

        self.assertEqual(payload["summary"]["relevance_summary"]["counts_by_tier"]["canonical"], 1)
        self.assertEqual(payload["summary"]["relevance_summary"]["counts_by_tier"]["must_read"], 1)
        self.assertEqual(payload["summary"]["relevance_summary"]["strongest_tier"], "canonical")
        self.assertEqual(payload["summary"]["role_label_counts"]["foundational"], 1)
        self.assertEqual(payload["summary"]["role_label_counts"]["review"], 1)
        entry = payload["sources"][0]
        self.assertEqual(entry["strongest_relevance_tier"], "canonical")
        self.assertIn("foundational", entry["role_labels"])
        self.assertIn("review", entry["role_labels"])
        markdown = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("## Relevance Summary", markdown)
        self.assertIn("canonical", markdown)
        self.assertIn("foundational", markdown)

    def test_materialize_source_citation_traversal_reports_incoming_and_outgoing_links(self) -> None:
        self._write_source_row(
            topic_slug="topic-a",
            source_id="paper:shared-a",
            source_type="paper",
            title="Shared paper",
            summary="Shared source summary.",
            canonical_source_id="source_identity:doi:10-1000-shared-paper",
            references=["doi:10-1000-neighbor-paper"],
        )
        self._write_source_row(
            topic_slug="topic-b",
            source_id="paper:shared-b",
            source_type="paper",
            title="Shared paper mirror",
            summary="Same source in another topic.",
            canonical_source_id="source_identity:doi:10-1000-shared-paper",
            references=["doi:10-1000-neighbor-paper"],
        )
        self._write_source_row(
            topic_slug="topic-c",
            source_id="paper:neighbor",
            source_type="paper",
            title="Neighbor paper",
            summary="Neighbor source summary.",
            canonical_source_id="source_identity:doi:10-1000-neighbor-paper",
            references=["doi:10-1000-shared-paper"],
        )

        result = materialize_source_citation_traversal(
            self.kernel_root,
            canonical_source_id="source_identity:doi:10-1000-shared-paper",
        )
        payload = result["payload"]

        self.assertTrue(Path(result["json_path"]).exists())
        self.assertTrue(Path(result["markdown_path"]).exists())
        self.assertEqual(payload["seed"]["canonical_source_id"], "source_identity:doi:10-1000-shared-paper")
        self.assertEqual(payload["summary"]["topic_count"], 2)
        self.assertEqual(payload["summary"]["outgoing_link_count"], 1)
        self.assertEqual(payload["summary"]["incoming_link_count"], 1)
        self.assertEqual(
            payload["outgoing_links"][0]["target_canonical_source_id"],
            "source_identity:doi:10-1000-neighbor-paper",
        )
        self.assertEqual(
            payload["incoming_links"][0]["source_canonical_source_id"],
            "source_identity:doi:10-1000-neighbor-paper",
        )
        markdown = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("## Outgoing Citation Links", markdown)
        self.assertIn("## Incoming Citation Links", markdown)

    def test_materialize_source_family_report_summarizes_reuse(self) -> None:
        self._write_source_row(
            topic_slug="topic-a",
            source_id="paper:shared-a",
            source_type="paper",
            title="Shared paper",
            summary="Shared source summary.",
            canonical_source_id="source_identity:doi:10-1000-shared-paper",
            references=["doi:10-1000-neighbor-paper"],
        )
        self._write_source_row(
            topic_slug="topic-b",
            source_id="paper:shared-b",
            source_type="paper",
            title="Shared paper mirror",
            summary="Same source in another topic.",
            canonical_source_id="source_identity:doi:10-1000-shared-paper",
            references=[],
        )
        self._write_source_row(
            topic_slug="topic-c",
            source_id="note:neighbor",
            source_type="local_note",
            title="Neighbor note",
            summary="Neighbor source summary.",
            canonical_source_id="source_identity:file:neighbor-note",
            references=[],
        )

        result = materialize_source_family_report(
            self.kernel_root,
            source_type="paper",
        )
        payload = result["payload"]

        self.assertTrue(Path(result["json_path"]).exists())
        self.assertTrue(Path(result["markdown_path"]).exists())
        self.assertEqual(payload["summary"]["canonical_source_count"], 1)
        self.assertEqual(payload["summary"]["multi_topic_source_count"], 1)
        self.assertEqual(payload["summary"]["topic_count"], 2)
        self.assertEqual(payload["sources"][0]["canonical_source_id"], "source_identity:doi:10-1000-shared-paper")
        markdown = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("## Most Reused Sources", markdown)


if __name__ == "__main__":
    unittest.main()
