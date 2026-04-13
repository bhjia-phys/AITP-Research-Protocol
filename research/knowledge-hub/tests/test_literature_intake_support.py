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

from knowledge_hub.l2_graph import consult_canonical_l2
from knowledge_hub.l2_staging import materialize_workspace_staging_manifest
from knowledge_hub.literature_intake_support import (
    derive_literature_stage_payload_from_runtime_payload,
    stage_literature_units,
)


class LiteratureIntakeSupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.kernel_root = Path(self._tmpdir.name)
        self.source_kernel = Path(__file__).resolve().parents[1]
        shutil.copytree(self.source_kernel / "canonical", self.kernel_root / "canonical", dirs_exist_ok=True)
        shutil.copytree(self.source_kernel / "schemas", self.kernel_root / "schemas", dirs_exist_ok=True)
        shutil.rmtree(self.kernel_root / "canonical" / "staging", ignore_errors=True)
        (self.kernel_root / "canonical" / "staging" / "entries").mkdir(parents=True, exist_ok=True)
        (self.kernel_root / "intake" / "topics" / "demo-topic" / "vault" / "wiki").mkdir(parents=True, exist_ok=True)
        (self.kernel_root / "intake" / "topics" / "demo-topic" / "vault" / "wiki" / "home.md").write_text(
            "# Demo Home\n\nWeak-coupling literature intake bridge.\n",
            encoding="utf-8",
        )
        (self.kernel_root / "intake" / "topics" / "demo-topic" / "vault" / "wiki" / "source-intake.md").write_text(
            "# Source Intake\n\nThis paper defines a reusable weak-coupling picture and warning.\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_stage_literature_units_writes_schema_backed_staging_entries_and_manifest(self) -> None:
        payload = stage_literature_units(
            self.kernel_root,
            topic_slug="demo-topic",
            source_slug="arxiv-2501-12345",
            candidate_units=[
                {
                    "candidate_unit_type": "concept",
                    "title": "Weak-coupling bridge picture",
                    "summary": "Use the paper as a weak-coupling route picture before any stronger canonical claim.",
                    "tags": ["literature-intake", "weak-coupling"],
                    "wiki_page_paths": [
                        "intake/topics/demo-topic/vault/wiki/home.md",
                        "intake/topics/demo-topic/vault/wiki/source-intake.md",
                    ],
                },
                {
                    "candidate_unit_type": "warning_note",
                    "title": "Do not over-read the bounded paper claim",
                    "summary": "The source supports a bounded warning but not a theorem-level portability claim.",
                    "tags": ["literature-intake", "warning"],
                    "wiki_page_paths": [
                        "intake/topics/demo-topic/vault/wiki/source-intake.md",
                    ],
                },
            ],
            created_by="test-suite",
        )

        self.assertEqual(payload["topic_slug"], "demo-topic")
        self.assertEqual(payload["source_slug"], "arxiv-2501-12345")
        self.assertEqual(len(payload["entries"]), 2)
        for entry in payload["entries"]:
            self.assertEqual(entry["trust_surface"], "staging")
            self.assertTrue(entry["provenance"]["literature_intake_fast_path"])
            self.assertEqual(entry["provenance"]["source_slug"], "arxiv-2501-12345")
            self.assertTrue(entry["provenance"]["vault_wiki_paths"])

        manifest_payload = json.loads(Path(payload["manifest_json_path"]).read_text(encoding="utf-8"))
        self.assertEqual(manifest_payload["summary"]["total_entries"], 2)
        self.assertEqual(manifest_payload["summary"]["counts_by_kind"]["concept"], 1)
        self.assertEqual(manifest_payload["summary"]["counts_by_kind"]["warning_note"], 1)

        consult_payload = consult_canonical_l2(
            self.kernel_root,
            query_text="weak coupling literature intake warning",
            retrieval_profile="l1_provisional_understanding",
            include_staging=True,
        )
        staged_ids = {row["entry_id"] for row in consult_payload["staged_hits"]}
        self.assertEqual(len(staged_ids), 2)
        staged_rows = [row for row in consult_payload["staged_hits"] if row["entry_id"] in staged_ids]
        self.assertTrue(all(row["trust_surface"] == "staging" for row in staged_rows))
        self.assertTrue(any((row.get("provenance") or {}).get("literature_intake_fast_path") for row in staged_rows))

    def test_stage_literature_units_rejects_non_fast_path_unit_types(self) -> None:
        with self.assertRaises(ValueError):
            stage_literature_units(
                self.kernel_root,
                topic_slug="demo-topic",
                source_slug="arxiv-2501-12345",
                candidate_units=[
                    {
                        "candidate_unit_type": "proof_fragment",
                        "title": "Forbidden proof fragment",
                        "summary": "This should not enter the literature fast path.",
                    }
                ],
                created_by="test-suite",
            )

    def test_stage_literature_units_accepts_manual_physical_picture_entries(self) -> None:
        payload = stage_literature_units(
            self.kernel_root,
            topic_slug="demo-topic",
            source_slug="arxiv-2501-12345",
            candidate_units=[
                {
                    "candidate_unit_type": "physical_picture",
                    "title": "Weak-coupling intuition picture",
                    "summary": "Use the source as a weak-coupling intuition picture for the bounded route rather than a full theorem claim.",
                    "wiki_page_paths": [
                        "intake/topics/demo-topic/vault/wiki/home.md",
                    ],
                }
            ],
            created_by="test-suite",
        )

        self.assertEqual(payload["entry_count"], 1)
        self.assertEqual(payload["entries"][0]["candidate_unit_type"], "physical_picture")
        manifest = materialize_workspace_staging_manifest(self.kernel_root)["payload"]
        self.assertEqual(manifest["summary"]["counts_by_kind"]["physical_picture"], 1)

    def test_stage_literature_units_preserves_per_entry_source_provenance(self) -> None:
        payload = stage_literature_units(
            self.kernel_root,
            topic_slug="demo-topic",
            source_slug="batch-source",
            candidate_units=[
                {
                    "candidate_unit_type": "concept",
                    "title": "Paper A regime signal",
                    "summary": "A bounded regime signal from paper A.",
                    "source_refs": ["source:paper-a"],
                    "provenance": {
                        "source_id": "source:paper-a",
                        "source_slug": "paper-a",
                        "source_title": "Paper A",
                    },
                },
                {
                    "candidate_unit_type": "concept",
                    "title": "Paper B regime signal",
                    "summary": "A bounded regime signal from paper B.",
                    "source_refs": ["source:paper-b"],
                    "provenance": {
                        "source_id": "source:paper-b",
                        "source_slug": "paper-b",
                        "source_title": "Paper B",
                    },
                },
            ],
            created_by="test-suite",
        )

        entry_by_title = {entry["title"]: entry for entry in payload["entries"]}
        paper_a = entry_by_title["Paper A regime signal"]
        paper_b = entry_by_title["Paper B regime signal"]

        self.assertIn("source:paper-a", paper_a["tags"])
        self.assertNotIn("source:paper-b", paper_a["tags"])
        self.assertEqual(paper_a["provenance"]["source_id"], "source:paper-a")
        self.assertEqual(paper_a["provenance"]["source_slug"], "paper-a")

        self.assertIn("source:paper-b", paper_b["tags"])
        self.assertNotIn("source:paper-a", paper_b["tags"])
        self.assertEqual(paper_b["provenance"]["source_id"], "source:paper-b")
        self.assertEqual(paper_b["provenance"]["source_slug"], "paper-b")

    def test_workspace_manifest_derives_kind_from_schema_backed_staging_entries(self) -> None:
        stage_literature_units(
            self.kernel_root,
            topic_slug="demo-topic",
            source_slug="arxiv-2501-12345",
            candidate_units=[
                {
                    "candidate_unit_type": "method",
                    "title": "Paper extraction workflow",
                    "summary": "A reusable extraction method grounded in the source wiki pages.",
                    "wiki_page_paths": [
                        "intake/topics/demo-topic/vault/wiki/home.md",
                    ],
                }
            ],
            created_by="test-suite",
        )

        manifest = materialize_workspace_staging_manifest(self.kernel_root)["payload"]
        self.assertEqual(manifest["summary"]["counts_by_kind"]["method"], 1)
        self.assertTrue(any(row["entry_kind"] == "method" for row in manifest["entries"]))

    def test_derive_literature_stage_payload_covers_assumptions_regimes_notation_and_tension(self) -> None:
        payload = derive_literature_stage_payload_from_runtime_payload(
            topic_slug="demo-topic",
            runtime_payload={
                "active_research_contract": {
                    "l1_source_intake": {
                        "assumption_rows": [
                            {
                                "source_id": "paper:weak-coupling",
                                "source_title": "Weak coupling closure",
                                "source_type": "paper",
                                "assumption": "Fractional occupations remain bounded in weak coupling.",
                                "reading_depth": "full_read",
                                "evidence_excerpt": "We assume the occupations remain bounded.",
                            }
                        ],
                        "regime_rows": [
                            {
                                "source_id": "paper:weak-coupling",
                                "source_title": "Weak coupling closure",
                                "source_type": "paper",
                                "regime": "weak coupling",
                                "reading_depth": "full_read",
                                "evidence_excerpt": "The derivation is restricted to weak coupling.",
                            }
                        ],
                        "reading_depth_rows": [],
                        "method_specificity_rows": [],
                        "notation_rows": [
                            {
                                "source_id": "paper:weak-coupling",
                                "source_title": "Weak coupling closure",
                                "source_type": "paper",
                                "symbol": "K",
                                "meaning": "the diagonal generator",
                                "reading_depth": "full_read",
                                "evidence_excerpt": "K denotes the diagonal generator.",
                            }
                        ],
                        "contradiction_candidates": [],
                        "notation_tension_candidates": [
                            {
                                "source_id": "paper:weak-coupling",
                                "source_title": "Weak coupling closure",
                                "source_type": "paper",
                                "reading_depth": "full_read",
                                "against_source_id": "paper:strong-coupling",
                                "against_source_title": "Strong coupling closure",
                                "against_source_type": "paper",
                                "against_reading_depth": "full_read",
                                "meaning": "the diagonal generator",
                                "existing_symbol": "K",
                                "incoming_symbol": "D",
                            }
                        ],
                    },
                    "l1_vault": {
                        "wiki": {
                            "page_paths": [
                                "intake/topics/demo-topic/vault/wiki/home.md",
                                "intake/topics/demo-topic/vault/wiki/source-intake.md",
                            ]
                        }
                    },
                }
            },
        )

        candidate_types = [row["candidate_unit_type"] for row in payload["candidate_units"]]
        self.assertIn("claim_card", candidate_types)
        self.assertIn("concept", candidate_types)
        self.assertIn("warning_note", candidate_types)
        self.assertTrue(any("assumption" in row["title"].lower() for row in payload["candidate_units"]))
        self.assertTrue(any("notation" in row["title"].lower() for row in payload["candidate_units"]))
        self.assertTrue(any("regime" in row["title"].lower() for row in payload["candidate_units"]))

    def test_derive_literature_stage_payload_adds_graph_analysis_units(self) -> None:
        payload = derive_literature_stage_payload_from_runtime_payload(
            topic_slug="demo-topic",
            runtime_payload={
                "active_research_contract": {
                    "l1_source_intake": {
                        "assumption_rows": [],
                        "regime_rows": [],
                        "reading_depth_rows": [],
                        "method_specificity_rows": [],
                        "notation_rows": [],
                        "contradiction_candidates": [],
                        "notation_tension_candidates": [],
                        "concept_graph": {
                            "nodes": [
                                {
                                    "source_id": "paper:anyon-condensation",
                                    "source_title": "Anyon condensation paper",
                                    "source_type": "paper",
                                    "node_id": "concept:topological-order",
                                    "label": "Topological order",
                                    "node_type": "concept",
                                    "confidence_tier": "EXTRACTED",
                                    "confidence_score": 0.95,
                                },
                                {
                                    "source_id": "note:operator-algebra",
                                    "source_title": "Operator algebra note",
                                    "source_type": "local_note",
                                    "node_id": "concept:topological-order-operator",
                                    "label": "Topological order",
                                    "node_type": "concept",
                                    "confidence_tier": "EXTRACTED",
                                    "confidence_score": 0.91,
                                },
                            ],
                            "edges": [],
                            "hyperedges": [],
                            "communities": [
                                {
                                    "source_id": "paper:anyon-condensation",
                                    "community_id": "community-topological-order",
                                    "label": "Topological order cluster",
                                    "node_ids": ["concept:topological-order"],
                                },
                                {
                                    "source_id": "note:operator-algebra",
                                    "community_id": "community-topological-order-operator",
                                    "label": "Topological order cluster",
                                    "node_ids": ["concept:topological-order-operator"],
                                },
                            ],
                            "god_nodes": [
                                {
                                    "source_id": "paper:anyon-condensation",
                                    "node_id": "concept:topological-order",
                                    "label": "Topological order",
                                },
                                {
                                    "source_id": "note:operator-algebra",
                                    "node_id": "concept:topological-order-operator",
                                    "label": "Topological order",
                                },
                            ],
                        },
                    },
                    "l1_vault": {
                        "wiki": {
                            "page_paths": [
                                "intake/topics/demo-topic/vault/wiki/home.md",
                                "intake/topics/demo-topic/vault/wiki/source-intake.md",
                            ]
                        }
                    },
                }
            },
        )

        candidate_types = [row["candidate_unit_type"] for row in payload["candidate_units"]]
        self.assertIn("physical_picture", candidate_types)
        self.assertIn("workflow", candidate_types)
        self.assertTrue(any("Topological order" in row["title"] for row in payload["candidate_units"]))
        self.assertTrue(any("graph-analysis" in (row.get("tags") or []) for row in payload["candidate_units"]))

    def test_derive_literature_stage_payload_adds_graph_diff_units(self) -> None:
        payload = derive_literature_stage_payload_from_runtime_payload(
            topic_slug="demo-topic",
            runtime_payload={
                "graph_analysis": {
                    "summary": {
                        "connection_count": 1,
                        "question_count": 1,
                        "history_length": 2,
                    },
                    "connections": [],
                    "questions": [],
                    "diff": {
                        "added": {
                            "node_count": 2,
                            "node_labels": ["Anyon condensation", "Operator algebra sector"],
                            "edge_count": 0,
                            "edge_relations": [],
                            "god_node_count": 1,
                            "god_node_labels": ["Anyon condensation"],
                        },
                        "removed": {
                            "node_count": 1,
                            "node_labels": ["Topological order"],
                            "edge_count": 0,
                            "edge_relations": [],
                            "god_node_count": 1,
                            "god_node_labels": ["Topological order"],
                        },
                    },
                },
                "active_research_contract": {
                    "l1_source_intake": {
                        "assumption_rows": [],
                        "regime_rows": [],
                        "reading_depth_rows": [],
                        "method_specificity_rows": [],
                        "notation_rows": [],
                        "contradiction_candidates": [],
                        "notation_tension_candidates": [],
                        "concept_graph": {
                            "nodes": [],
                            "edges": [],
                            "hyperedges": [],
                            "communities": [],
                            "god_nodes": [],
                        },
                    },
                    "l1_vault": {
                        "wiki": {
                            "page_paths": [
                                "intake/topics/demo-topic/vault/wiki/home.md",
                                "intake/topics/demo-topic/vault/wiki/source-intake.md",
                            ]
                        }
                    },
                },
            },
        )

        candidate_types = [row["candidate_unit_type"] for row in payload["candidate_units"]]
        self.assertIn("claim_card", candidate_types)
        self.assertIn("warning_note", candidate_types)
        self.assertTrue(any("Graph diff surfaced" in row["title"] for row in payload["candidate_units"]))
        self.assertTrue(any("Graph diff retired" in row["title"] for row in payload["candidate_units"]))
        self.assertTrue(any("graph-diff" in (row.get("tags") or []) for row in payload["candidate_units"]))

    def test_derive_literature_stage_payload_skips_generic_notation_and_weak_method_rows(self) -> None:
        payload = derive_literature_stage_payload_from_runtime_payload(
            topic_slug="demo-topic",
            runtime_payload={
                "active_research_contract": {
                    "l1_source_intake": {
                        "assumption_rows": [],
                        "regime_rows": [],
                        "reading_depth_rows": [],
                        "method_specificity_rows": [
                            {
                                "source_id": "paper:noise-paper",
                                "source_title": "Noise paper",
                                "source_type": "paper",
                                "method_family": "unspecified_method",
                                "specificity_tier": "surface_hint",
                                "reading_depth": "preview_only",
                                "evidence_excerpt": "We studied several cases.",
                            },
                            {
                                "source_id": "paper:real-paper",
                                "source_title": "Real paper",
                                "source_type": "paper",
                                "method_family": "tensor_network",
                                "specificity_tier": "explicit",
                                "reading_depth": "full_read",
                                "evidence_excerpt": "We use a tensor-network transfer-matrix construction.",
                            },
                        ],
                        "notation_rows": [
                            {
                                "source_id": "paper:noise-paper",
                                "source_title": "Noise paper",
                                "source_type": "paper",
                                "symbol": "classes",
                                "meaning": "classes",
                                "reading_depth": "preview_only",
                                "evidence_excerpt": "The classes considered are broad.",
                            },
                            {
                                "source_id": "paper:real-paper",
                                "source_title": "Real paper",
                                "source_type": "paper",
                                "symbol": "K",
                                "meaning": "the transfer kernel",
                                "reading_depth": "full_read",
                                "evidence_excerpt": "K denotes the transfer kernel.",
                            },
                        ],
                        "contradiction_candidates": [],
                        "notation_tension_candidates": [],
                        "concept_graph": {
                            "nodes": [],
                            "edges": [],
                            "hyperedges": [],
                            "communities": [],
                            "god_nodes": [],
                        },
                    },
                    "l1_vault": {
                        "wiki": {
                            "page_paths": [
                                "intake/topics/demo-topic/vault/wiki/source-intake.md",
                            ]
                        }
                    },
                }
            },
        )

        titles = [row["title"] for row in payload["candidate_units"]]
        self.assertIn("Real paper tensor_network method signal", titles)
        self.assertIn("Real paper notation `K`", titles)
        self.assertNotIn("Noise paper unspecified_method method signal", titles)
        self.assertNotIn("Noise paper notation `classes`", titles)

    def test_derive_literature_stage_payload_adds_shared_community_bridge_units(self) -> None:
        payload = derive_literature_stage_payload_from_runtime_payload(
            topic_slug="demo-topic",
            runtime_payload={
                "active_research_contract": {
                    "l1_source_intake": {
                        "assumption_rows": [],
                        "regime_rows": [],
                        "reading_depth_rows": [],
                        "method_specificity_rows": [],
                        "notation_rows": [],
                        "contradiction_candidates": [],
                        "notation_tension_candidates": [],
                        "concept_graph": {
                            "nodes": [
                                {
                                    "source_id": "paper:anyon-condensation",
                                    "source_title": "Anyon condensation paper",
                                    "source_type": "paper",
                                    "node_id": "concept:anyon-condensation",
                                    "label": "Anyon condensation",
                                    "node_type": "concept",
                                    "confidence_tier": "EXTRACTED",
                                    "confidence_score": 0.95,
                                },
                                {
                                    "source_id": "note:operator-algebra",
                                    "source_title": "Operator algebra note",
                                    "source_type": "local_note",
                                    "node_id": "concept:operator-sector",
                                    "label": "Operator algebra sector",
                                    "node_type": "concept",
                                    "confidence_tier": "EXTRACTED",
                                    "confidence_score": 0.91,
                                },
                            ],
                            "edges": [],
                            "hyperedges": [],
                            "communities": [
                                {
                                    "source_id": "paper:anyon-condensation",
                                    "community_id": "community-topological-order-paper",
                                    "label": "Topological order cluster",
                                    "node_ids": ["concept:anyon-condensation"],
                                },
                                {
                                    "source_id": "note:operator-algebra",
                                    "community_id": "community-topological-order-note",
                                    "label": "Topological order cluster",
                                    "node_ids": ["concept:operator-sector"],
                                },
                            ],
                            "god_nodes": [
                                {
                                    "source_id": "paper:anyon-condensation",
                                    "node_id": "concept:anyon-condensation",
                                    "label": "Anyon condensation",
                                },
                                {
                                    "source_id": "note:operator-algebra",
                                    "node_id": "concept:operator-sector",
                                    "label": "Operator algebra sector",
                                },
                            ],
                        },
                    },
                    "l1_vault": {
                        "wiki": {
                            "page_paths": [
                                "intake/topics/demo-topic/vault/wiki/home.md",
                                "intake/topics/demo-topic/vault/wiki/source-intake.md",
                            ]
                        }
                    },
                }
            },
        )

        candidate_types = [row["candidate_unit_type"] for row in payload["candidate_units"]]
        self.assertIn("physical_picture", candidate_types)
        self.assertIn("workflow", candidate_types)
        self.assertTrue(any("Topological order cluster" in row["title"] for row in payload["candidate_units"]))
        self.assertTrue(any(row.get("provenance", {}).get("graph_analysis_kind") == "shared_community_bridge" for row in payload["candidate_units"]))

    def test_derive_literature_stage_payload_adds_shared_hyperedge_pattern_units(self) -> None:
        payload = derive_literature_stage_payload_from_runtime_payload(
            topic_slug="demo-topic",
            runtime_payload={
                "active_research_contract": {
                    "l1_source_intake": {
                        "assumption_rows": [],
                        "regime_rows": [],
                        "reading_depth_rows": [],
                        "method_specificity_rows": [],
                        "notation_rows": [],
                        "contradiction_candidates": [],
                        "notation_tension_candidates": [],
                        "concept_graph": {
                            "nodes": [
                                {
                                    "source_id": "paper:anyon-condensation",
                                    "source_title": "Anyon condensation paper",
                                    "source_type": "paper",
                                    "node_id": "theorem:condensation-criterion",
                                    "label": "Condensation criterion",
                                    "node_type": "theorem",
                                    "confidence_tier": "EXTRACTED",
                                    "confidence_score": 0.95,
                                },
                                {
                                    "source_id": "paper:anyon-condensation",
                                    "source_title": "Anyon condensation paper",
                                    "source_type": "paper",
                                    "node_id": "approximation:weak-coupling",
                                    "label": "Weak coupling",
                                    "node_type": "approximation",
                                    "confidence_tier": "EXTRACTED",
                                    "confidence_score": 0.91,
                                },
                                {
                                    "source_id": "paper:anyon-condensation",
                                    "source_title": "Anyon condensation paper",
                                    "source_type": "paper",
                                    "node_id": "concept:anyon-condensation",
                                    "label": "Anyon condensation",
                                    "node_type": "concept",
                                    "confidence_tier": "EXTRACTED",
                                    "confidence_score": 0.92,
                                },
                                {
                                    "source_id": "note:operator-algebra",
                                    "source_title": "Operator algebra note",
                                    "source_type": "local_note",
                                    "node_id": "theorem:sector-criterion",
                                    "label": "Sector decomposition criterion",
                                    "node_type": "theorem",
                                    "confidence_tier": "EXTRACTED",
                                    "confidence_score": 0.94,
                                },
                                {
                                    "source_id": "note:operator-algebra",
                                    "source_title": "Operator algebra note",
                                    "source_type": "local_note",
                                    "node_id": "approximation:finite-index",
                                    "label": "Finite-index assumption",
                                    "node_type": "approximation",
                                    "confidence_tier": "EXTRACTED",
                                    "confidence_score": 0.9,
                                },
                                {
                                    "source_id": "note:operator-algebra",
                                    "source_title": "Operator algebra note",
                                    "source_type": "local_note",
                                    "node_id": "concept:operator-sector",
                                    "label": "Operator algebra sector",
                                    "node_type": "concept",
                                    "confidence_tier": "EXTRACTED",
                                    "confidence_score": 0.89,
                                },
                            ],
                            "edges": [],
                            "hyperedges": [
                                {
                                    "source_id": "paper:anyon-condensation",
                                    "hyperedge_id": "hyperedge:paper-supports",
                                    "relation": "supports",
                                    "node_ids": [
                                        "theorem:condensation-criterion",
                                        "approximation:weak-coupling",
                                        "concept:anyon-condensation",
                                    ],
                                },
                                {
                                    "source_id": "note:operator-algebra",
                                    "hyperedge_id": "hyperedge:note-supports",
                                    "relation": "supports",
                                    "node_ids": [
                                        "theorem:sector-criterion",
                                        "approximation:finite-index",
                                        "concept:operator-sector",
                                    ],
                                },
                            ],
                            "communities": [],
                            "god_nodes": [],
                        },
                    },
                    "l1_vault": {
                        "wiki": {
                            "page_paths": [
                                "intake/topics/demo-topic/vault/wiki/home.md",
                                "intake/topics/demo-topic/vault/wiki/source-intake.md",
                            ]
                        }
                    },
                }
            },
        )

        candidate_types = [row["candidate_unit_type"] for row in payload["candidate_units"]]
        self.assertIn("physical_picture", candidate_types)
        self.assertIn("workflow", candidate_types)
        self.assertTrue(any("supports pattern (approximation + concept + theorem)" in row["title"] for row in payload["candidate_units"]))
        self.assertTrue(any(row.get("provenance", {}).get("graph_analysis_kind") == "shared_hyperedge_pattern_bridge" for row in payload["candidate_units"]))


if __name__ == "__main__":
    unittest.main()
