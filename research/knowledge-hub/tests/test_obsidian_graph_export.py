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

from knowledge_hub.obsidian_graph_export import materialize_obsidian_concept_graph_export


class ObsidianGraphExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.kernel_root = Path(self._tmpdir.name)
        self.source_kernel = Path(__file__).resolve().parents[1]
        (self.kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki").mkdir(parents=True, exist_ok=True)
        shutil.copytree(self.source_kernel / "schemas", self.kernel_root / "schemas", dirs_exist_ok=True)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_materialize_obsidian_concept_graph_export_writes_community_folders_and_wikilinks(self) -> None:
        result = materialize_obsidian_concept_graph_export(
            kernel_root=self.kernel_root,
            topic_slug="demo-topic",
            source_rows=[
                {
                    "source_id": "paper:anyon-condensation",
                    "source_type": "paper",
                    "title": "Anyon condensation paper",
                    "summary": "Topological order supports the bounded condensation route.",
                    "provenance": {
                        "abs_url": "https://example.org/anyon-condensation",
                    },
                },
                {
                    "source_id": "note:operator-algebra",
                    "source_type": "local_note",
                    "title": "Operator algebra note",
                    "summary": "Operator-sector comparison note for the same cluster.",
                    "provenance": {
                        "absolute_path": "C:/notes/operator-algebra.md",
                    },
                },
            ],
            l1_source_intake={
                "concept_graph": {
                    "nodes": [
                        {
                            "source_id": "paper:anyon-condensation",
                            "source_title": "Anyon condensation paper",
                            "source_type": "paper",
                            "node_id": "concept:topological-order",
                            "label": "Topological order",
                            "node_type": "concept",
                        },
                        {
                            "source_id": "paper:anyon-condensation",
                            "source_title": "Anyon condensation paper",
                            "source_type": "paper",
                            "node_id": "concept:anyon-condensation",
                            "label": "Anyon condensation",
                            "node_type": "concept",
                        },
                        {
                            "source_id": "note:operator-algebra",
                            "source_title": "Operator algebra note",
                            "source_type": "local_note",
                            "node_id": "concept:topological-order-operator",
                            "label": "Topological order",
                            "node_type": "concept",
                        },
                    ],
                    "edges": [
                        {
                            "source_id": "paper:anyon-condensation",
                            "edge_id": "edge:1",
                            "from_id": "concept:anyon-condensation",
                            "relation": "special_case_of",
                            "to_id": "concept:topological-order",
                        }
                    ],
                    "hyperedges": [
                        {
                            "source_id": "paper:anyon-condensation",
                            "hyperedge_id": "hyperedge:1",
                            "relation": "supports",
                            "node_ids": ["concept:topological-order", "concept:anyon-condensation"],
                        }
                    ],
                    "communities": [
                        {
                            "source_id": "paper:anyon-condensation",
                            "community_id": "community-topological-order-paper",
                            "label": "Topological order cluster",
                            "node_ids": ["concept:topological-order", "concept:anyon-condensation"],
                        },
                        {
                            "source_id": "note:operator-algebra",
                            "community_id": "community-topological-order-note",
                            "label": "Topological order cluster",
                            "node_ids": ["concept:topological-order-operator"],
                        },
                    ],
                    "god_nodes": [
                        {
                            "source_id": "paper:anyon-condensation",
                            "node_id": "concept:topological-order",
                            "label": "Topological order",
                        }
                    ],
                }
            },
            updated_by="test-suite",
            relativize=lambda path: path.relative_to(self.kernel_root).as_posix(),
        )

        manifest_path = Path(result["manifest_path"])
        index_path = Path(result["index_path"])
        community_index = self.kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "concept-graph" / "topological-order-cluster" / "index.md"
        topological_note = self.kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "concept-graph" / "topological-order-cluster" / "topological-order.md"
        anyon_note = self.kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "concept-graph" / "topological-order-cluster" / "anyon-condensation.md"

        self.assertTrue(manifest_path.exists())
        self.assertTrue(index_path.exists())
        self.assertTrue(community_index.exists())
        self.assertTrue(topological_note.exists())
        self.assertTrue(anyon_note.exists())

        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest_payload["summary"]["node_note_count"], 2)
        self.assertEqual(manifest_payload["summary"]["community_folder_count"], 1)
        self.assertEqual(manifest_payload["summary"]["community_page_count"], 1)

        index_text = index_path.read_text(encoding="utf-8")
        community_text = community_index.read_text(encoding="utf-8")
        topological_text = topological_note.read_text(encoding="utf-8")
        anyon_text = anyon_note.read_text(encoding="utf-8")

        self.assertIn("page_type: concept_graph_index", index_text)
        self.assertIn("[[concept-graph/topological-order-cluster/topological-order|Topological order]]", index_text)
        self.assertIn("[[concept-graph/topological-order-cluster/anyon-condensation|Anyon condensation]]", index_text)
        self.assertIn("page_type: concept_graph_community", community_text)
        self.assertIn("[[concept-graph/topological-order-cluster/topological-order|Topological order]]", community_text)
        self.assertIn("[[concept-graph/topological-order-cluster/anyon-condensation|Anyon condensation]]", community_text)
        self.assertIn("source_count: 2", topological_text)
        self.assertIn("Topological order supports the bounded condensation route.", topological_text)
        self.assertIn("https://example.org/anyon-condensation", anyon_text)
        self.assertIn("[[concept-graph/topological-order-cluster/anyon-condensation|Anyon condensation]]", topological_text)
        self.assertIn("This node `special_case_of` [[concept-graph/topological-order-cluster/topological-order|Topological order]]", anyon_text)
        self.assertIn("[[concept-graph/topological-order-cluster/anyon-condensation|Anyon condensation]] `special_case_of` this node", topological_text)
        self.assertIn("This node participates in `supports` with [[concept-graph/topological-order-cluster/topological-order|Topological order]]", anyon_text)

    def test_materialize_obsidian_concept_graph_export_keeps_unclustered_nodes_in_dedicated_folder(self) -> None:
        result = materialize_obsidian_concept_graph_export(
            kernel_root=self.kernel_root,
            topic_slug="demo-topic",
            source_rows=[],
            l1_source_intake={
                "concept_graph": {
                    "nodes": [
                        {
                            "source_id": "paper:single-observable",
                            "source_title": "Single observable paper",
                            "source_type": "paper",
                            "node_id": "observable:edge-current",
                            "label": "Edge current",
                            "node_type": "observable",
                        }
                    ],
                    "edges": [],
                    "hyperedges": [],
                    "communities": [],
                    "god_nodes": [],
                }
            },
            updated_by="test-suite",
            relativize=lambda path: path.relative_to(self.kernel_root).as_posix(),
        )

        manifest_payload = json.loads(Path(result["manifest_path"]).read_text(encoding="utf-8"))
        unclustered_index = self.kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "concept-graph" / "unclustered" / "index.md"
        unclustered_note = self.kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "concept-graph" / "unclustered" / "edge-current.md"

        self.assertTrue(unclustered_index.exists())
        self.assertTrue(unclustered_note.exists())
        self.assertEqual(manifest_payload["summary"]["community_folder_count"], 1)
        self.assertEqual(manifest_payload["summary"]["community_page_count"], 1)
        self.assertEqual(manifest_payload["communities"][0]["label"], "Unclustered")
        self.assertIn("[[concept-graph/unclustered/edge-current|Edge current]]", unclustered_index.read_text(encoding="utf-8"))

    def test_materialize_obsidian_concept_graph_export_lists_multi_community_node_in_each_community_overview(self) -> None:
        result = materialize_obsidian_concept_graph_export(
            kernel_root=self.kernel_root,
            topic_slug="demo-topic",
            source_rows=[
                {
                    "source_id": "paper:multi-community",
                    "source_type": "paper",
                    "title": "Multi-community paper",
                    "summary": "A node that lives in two graph communities.",
                    "provenance": {
                        "abs_url": "https://example.org/multi-community",
                    },
                }
            ],
            l1_source_intake={
                "concept_graph": {
                    "nodes": [
                        {
                            "source_id": "paper:multi-community",
                            "source_title": "Multi-community paper",
                            "source_type": "paper",
                            "node_id": "concept:modular-tensor-category",
                            "label": "Modular tensor category",
                            "node_type": "concept",
                        }
                    ],
                    "edges": [],
                    "hyperedges": [],
                    "communities": [
                        {
                            "source_id": "paper:multi-community",
                            "community_id": "community-category-theory",
                            "label": "Category theory cluster",
                            "node_ids": ["concept:modular-tensor-category"],
                        },
                        {
                            "source_id": "paper:multi-community",
                            "community_id": "community-topological-order",
                            "label": "Topological order cluster",
                            "node_ids": ["concept:modular-tensor-category"],
                        },
                    ],
                    "god_nodes": [],
                }
            },
            updated_by="test-suite",
            relativize=lambda path: path.relative_to(self.kernel_root).as_posix(),
        )

        manifest_payload = json.loads(Path(result["manifest_path"]).read_text(encoding="utf-8"))
        primary_note = self.kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "concept-graph" / "category-theory-cluster" / "modular-tensor-category.md"
        category_index = self.kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "concept-graph" / "category-theory-cluster" / "index.md"
        topological_index = self.kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "concept-graph" / "topological-order-cluster" / "index.md"

        self.assertTrue(primary_note.exists())
        self.assertTrue(category_index.exists())
        self.assertTrue(topological_index.exists())
        self.assertEqual(manifest_payload["summary"]["node_note_count"], 1)
        self.assertEqual(manifest_payload["summary"]["community_folder_count"], 2)
        self.assertEqual(manifest_payload["summary"]["community_page_count"], 2)
        self.assertIn("[[concept-graph/category-theory-cluster/modular-tensor-category|Modular tensor category]]", category_index.read_text(encoding="utf-8"))
        self.assertIn("[[concept-graph/category-theory-cluster/modular-tensor-category|Modular tensor category]]", topological_index.read_text(encoding="utf-8"))
        self.assertIn("Communities: `Category theory cluster, Topological order cluster`", primary_note.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
