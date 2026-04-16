from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from jsonschema import Draft202012Validator


def _load_module(module_name: str, relative_path: str):
    kernel_root = Path(__file__).resolve().parents[1]
    target_path = kernel_root / relative_path
    spec = importlib.util.spec_from_file_location(module_name, target_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {target_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SourceDiscoveryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel_root = Path(__file__).resolve().parents[1]
        self.repo_root = self.kernel_root.parents[1]
        self.module = _load_module(
            "discover_and_register_module",
            "source-layer/scripts/discover_and_register.py",
        )
        self.register_module = _load_module(
            "register_arxiv_source_module",
            "source-layer/scripts/register_arxiv_source.py",
        )
        self.enrich_module = _load_module(
            "enrich_with_deepxiv_module",
            "source-layer/scripts/enrich_with_deepxiv.py",
        )
        self.graph_module = _load_module(
            "build_concept_graph_module",
            "source-layer/scripts/build_concept_graph.py",
        )

    def _metadata_override(self) -> dict[str, object]:
        return {
            "arxiv_id": "2401.00001v2",
            "title": "Topological Order and Anyon Condensation",
            "summary": "A direct match for topological order and anyon condensation discovery.",
            "published": "2024-01-03T00:00:00Z",
            "updated": "2024-01-05T00:00:00Z",
            "authors": ["Primary Author", "Secondary Author"],
            "identifier": "https://arxiv.org/abs/2401.00001v2",
            "abs_url": "https://arxiv.org/abs/2401.00001v2",
            "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
            "source_url": "https://example.invalid/2401.00001v2.tar",
        }

    def _discovery_candidate(self) -> dict[str, object]:
        return {
            "provider": "search_results_json",
            "provider_position": 0,
            "arxiv_id": "2401.00001v2",
            "title": "Topological Order and Anyon Condensation",
            "summary": "A direct match for topological order and anyon condensation discovery.",
            "published": "2024-01-03T00:00:00Z",
            "updated": "2024-01-04T00:00:00Z",
            "authors": ["Primary Author", "Secondary Author"],
            "identifier": "https://arxiv.org/abs/2401.00001v2",
            "abs_url": "https://arxiv.org/abs/2401.00001v2",
            "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
            "source_url": "https://example.invalid/2401.00001v2.tar",
            "provider_score": 0.91,
            "raw": {},
        }

    def test_register_arxiv_source_defaults_to_contentful_acquisition(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            knowledge_root = Path(tmpdir) / "kernel"
            with mock.patch.object(self.register_module, "fetch_url", side_effect=OSError("offline fixture")):
                registration = self.register_module.register_arxiv_source(
                    knowledge_root=knowledge_root,
                    topic_slug="demo-topic",
                    arxiv_id="2401.00001v2",
                    registered_by="unit-test",
                    metadata_override=self._metadata_override(),
                    skip_enrichment=True,
                    skip_graph_build=True,
                )

            self.assertEqual(registration["download_status"], "failed")
            self.assertEqual(registration["extraction_status"], "skipped")
            snapshot_text = registration["layer0_snapshot"].read_text(encoding="utf-8")
            self.assertIn("Source bundle download: failed", snapshot_text)

    def test_register_arxiv_source_persists_relevance_tier_and_role_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            knowledge_root = Path(tmpdir) / "kernel"
            metadata_override = {
                **self._metadata_override(),
                "title": "A Review of Topological Order and Anyon Condensation",
                "summary": "A foundational review of topological order and anyon condensation for current operator-algebra routes.",
            }

            registration = self.register_module.register_arxiv_source(
                knowledge_root=knowledge_root,
                topic_slug="demo-topic",
                arxiv_id="2401.00001v2",
                registered_by="unit-test",
                metadata_override=metadata_override,
                download_source=False,
                skip_enrichment=True,
                skip_graph_build=True,
            )

            source_payload = json.loads(registration["layer0_source_json"].read_text(encoding="utf-8"))
            intake_payload = json.loads((registration["intake_projection_root"] / "source.json").read_text(encoding="utf-8"))
            public_schema = json.loads((self.repo_root / "schemas" / "source-item.schema.json").read_text(encoding="utf-8"))
            runtime_schema = json.loads((self.kernel_root / "schemas" / "source-item.schema.json").read_text(encoding="utf-8"))

            Draft202012Validator(public_schema).validate(source_payload)
            Draft202012Validator(runtime_schema).validate(intake_payload)
            self.assertEqual(source_payload["relevance_tier"], "must_read")
            self.assertIn("review", source_payload["role_labels"])
            self.assertIn("foundational", source_payload["role_labels"])
            self.assertEqual(intake_payload["relevance_tier"], "must_read")
            self.assertIn("review", intake_payload["role_labels"])

    def test_register_arxiv_source_uses_short_stable_source_directory_slug_for_long_titles(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            knowledge_root = Path(tmpdir) / "kernel"
            metadata_override = {
                "arxiv_id": "2401.00001v2",
                "title": (
                    "Measurement-induced algebraic transitions and observer algebras with "
                    "long-form bounded operator-structure notes for Windows path stress"
                ),
                "summary": "A long-title fixture for Windows path stress.",
                "published": "2024-01-03T00:00:00Z",
                "updated": "2024-01-05T00:00:00Z",
                "authors": ["Primary Author"],
                "identifier": "https://arxiv.org/abs/2401.00001v2",
                "abs_url": "https://arxiv.org/abs/2401.00001v2",
                "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                "source_url": "https://arxiv.org/e-print/2401.00001v2",
            }

            registration = self.register_module.register_arxiv_source(
                knowledge_root=knowledge_root,
                topic_slug="measurement-induced-algebraic-transition-and-observer-algebras",
                arxiv_id="2401.00001v2",
                registered_by="unit-test",
                metadata_override=metadata_override,
                download_source=False,
                skip_enrichment=True,
                skip_graph_build=True,
            )

            source_slug = registration["source_slug"]
            self.assertRegex(source_slug, r"^paper-2401-00001-[0-9a-f]{8}$")
            self.assertLessEqual(len(source_slug), 25)
            self.assertEqual(registration["layer0_source_root"].name, source_slug)
            self.assertEqual(
                registration["layer0_source_root"].relative_to(knowledge_root).as_posix(),
                f"source-layer/topics/measurement-induced-algebraic-transition-and-observer-algebras/sources/{source_slug}",
            )

    def test_register_arxiv_source_refreshes_runtime_status_surfaces_when_topic_runtime_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            knowledge_root = Path(tmpdir) / "kernel"
            shutil.copytree(self.kernel_root / "schemas", knowledge_root / "schemas", dirs_exist_ok=True)
            shutil.copytree(self.kernel_root / "runtime" / "schemas", knowledge_root / "runtime" / "schemas", dirs_exist_ok=True)
            shutil.copytree(self.kernel_root / "runtime" / "scripts", knowledge_root / "runtime" / "scripts", dirs_exist_ok=True)
            for name in (
                "closed_loop_policies.json",
                "research_mode_profiles.json",
                "CONTROL_NOTE_CONTRACT.md",
                "DECLARATIVE_RUNTIME_CONTRACTS.md",
                "DEFERRED_RUNTIME_CONTRACTS.md",
                "INNOVATION_DIRECTION_TEMPLATE.md",
                "PROGRESSIVE_DISCLOSURE_PROTOCOL.md",
            ):
                target = knowledge_root / "runtime" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.kernel_root / "runtime" / name, target)
            runtime_root = knowledge_root / "runtime" / "topics" / "demo-topic"
            runtime_root.mkdir(parents=True, exist_ok=True)
            (runtime_root / "topic_state.json").write_text(
                json.dumps(
                    {
                        "topic_slug": "demo-topic",
                        "resume_stage": "L3",
                        "latest_run_id": "run-001",
                        "research_mode": "exploratory_general",
                        "updated_at": "2026-04-14T00:00:00+08:00",
                    },
                    ensure_ascii=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (knowledge_root / "runtime").mkdir(parents=True, exist_ok=True)
            (knowledge_root / "runtime" / "current_topic.json").write_text(
                json.dumps({"topic_slug": "demo-topic"}, ensure_ascii=True, indent=2) + "\n",
                encoding="utf-8",
            )
            metadata_override = self._metadata_override()

            registration = self.register_module.register_arxiv_source(
                knowledge_root=knowledge_root,
                topic_slug="demo-topic",
                arxiv_id="2401.00001v2",
                registered_by="unit-test",
                metadata_override=metadata_override,
                download_source=False,
                skip_enrichment=True,
                skip_graph_build=True,
            )

            runtime_status_sync = registration["runtime_status_sync"]
            self.assertEqual(runtime_status_sync["status"], "refreshed")
            self.assertGreaterEqual(int(runtime_status_sync["source_count"] or 0), 1)
            self.assertTrue(Path(runtime_status_sync["runtime_protocol_path"]).exists())
            self.assertTrue(Path(runtime_status_sync["runtime_protocol_note_path"]).exists())

            refreshed_topic_state = json.loads((runtime_root / "topic_state.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(int(refreshed_topic_state.get("source_count") or 0), 1)
            self.assertEqual(
                str(((refreshed_topic_state.get("layer_status") or {}).get("L0") or {}).get("status") or ""),
                "present",
            )
            self.assertGreaterEqual(
                int((((refreshed_topic_state.get("layer_status") or {}).get("L0") or {}).get("source_count") or 0)),
                1,
            )
            current_topic_payload = json.loads((knowledge_root / "runtime" / "current_topic.json").read_text(encoding="utf-8"))
            self.assertEqual(current_topic_payload["topic_slug"], "demo-topic")
            active_topics_payload = json.loads((knowledge_root / "runtime" / "active_topics.json").read_text(encoding="utf-8"))
            self.assertEqual(active_topics_payload["focused_topic_slug"], "demo-topic")

    def test_register_arxiv_source_cli_defaults_to_download_with_metadata_only_opt_out(self) -> None:
        parser = self.register_module.build_parser()

        default_args = parser.parse_args(
            ["--topic-slug", "demo-topic", "--arxiv-id", "2401.00001v2"]
        )
        self.assertTrue(default_args.download_source)

        metadata_only_args = parser.parse_args(
            [
                "--topic-slug",
                "demo-topic",
                "--arxiv-id",
                "2401.00001v2",
                "--metadata-only",
            ]
        )
        self.assertFalse(metadata_only_args.download_source)

        compatibility_args = parser.parse_args(
            [
                "--topic-slug",
                "demo-topic",
                "--arxiv-id",
                "2401.00001v2",
                "--download-source",
            ]
        )
        self.assertTrue(compatibility_args.download_source)

    def test_discovery_bridge_defaults_to_contentful_forwarding(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            knowledge_root = Path(tmpdir) / "kernel"
            captured: dict[str, object] = {}

            def fake_register_arxiv_source(**kwargs):
                captured.update(kwargs)
                source_root = (
                    kwargs["knowledge_root"]
                    / "source-layer"
                    / "topics"
                    / kwargs["topic_slug"]
                    / "sources"
                    / "paper-topological-order-and-anyon-condensation-2401-00001"
                )
                source_root.mkdir(parents=True, exist_ok=True)
                source_json = source_root / "source.json"
                source_json.write_text("{}\n", encoding="utf-8")
                snapshot = source_root / "snapshot.md"
                snapshot.write_text("# snapshot\n", encoding="utf-8")
                return {
                    "layer0_source_json": source_json,
                    "layer0_snapshot": snapshot,
                    "intake_projection_root": None,
                    "download_status": "downloaded",
                    "extraction_status": "extracted",
                    "download_error": "",
                    "enrichment_status": "skipped",
                    "enrichment_receipt_path": None,
                    "enrichment_error": "",
                    "graph_build_status": "skipped",
                    "concept_graph_path": None,
                    "concept_graph_relative_path": "",
                    "graph_receipt_path": None,
                    "graph_error": "",
                }

            with (
                mock.patch.object(
                    self.module,
                    "execute_provider",
                    return_value=(
                        {"provider": "search_results_json", "result_count": 1},
                        [self._discovery_candidate()],
                    ),
                ),
                mock.patch.object(
                    self.module,
                    "load_register_module",
                    return_value=SimpleNamespace(register_arxiv_source=fake_register_arxiv_source),
                ),
            ):
                self.module.discover_and_register(
                    knowledge_root=knowledge_root,
                    topic_slug="demo-topic",
                    query="topological order anyon condensation",
                    provider_chain=["search_results_json"],
                    search_results_json=None,
                    max_results=5,
                    deepxiv_bin="deepxiv",
                    preferred_arxiv_id="",
                    select_index=0,
                    registered_by="unit-test",
                    force=False,
                    skip_intake_projection=True,
                    skip_enrichment=True,
                    skip_graph_build=True,
                )

            self.assertTrue(captured["download_source"])

    def test_discovery_bridge_cli_defaults_to_download_with_metadata_only_opt_out(self) -> None:
        parser = self.module.build_parser()

        default_args = parser.parse_args(["--topic-slug", "demo-topic", "--query", "anyon condensation"])
        self.assertTrue(default_args.download_source)

        metadata_only_args = parser.parse_args(
            [
                "--topic-slug",
                "demo-topic",
                "--query",
                "anyon condensation",
                "--metadata-only",
            ]
        )
        self.assertFalse(metadata_only_args.download_source)

        compatibility_args = parser.parse_args(
            [
                "--topic-slug",
                "demo-topic",
                "--query",
                "anyon condensation",
                "--download-source",
            ]
        )
        self.assertTrue(compatibility_args.download_source)

    def test_discovery_bridge_selects_and_registers_offline_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            work_root = Path(tmpdir)
            kernel_root = work_root / "kernel"
            search_results_path = work_root / "search-results.json"
            search_results_path.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "arxiv_id": "2401.00002v1",
                                "title": "Irrelevant benchmark note",
                                "summary": "Numerical benchmark only.",
                                "published": "2024-01-02T00:00:00Z",
                                "updated": "2024-01-02T00:00:00Z",
                                "authors": ["Auxiliary Author"],
                                "identifier": "https://arxiv.org/abs/2401.00002v1",
                                "abs_url": "https://arxiv.org/abs/2401.00002v1",
                                "pdf_url": "https://arxiv.org/pdf/2401.00002.pdf",
                                "source_url": "https://arxiv.org/e-print/2401.00002v1",
                                "score": 0.25,
                            },
                            {
                                "arxiv_id": "2401.00001v2",
                                "title": "Topological Order and Anyon Condensation",
                                "summary": "A direct match for topological order and anyon condensation discovery.",
                                "published": "2024-01-03T00:00:00Z",
                                "updated": "2024-01-04T00:00:00Z",
                                "authors": ["Primary Author", "Secondary Author"],
                                "identifier": "https://arxiv.org/abs/2401.00001v2",
                                "abs_url": "https://arxiv.org/abs/2401.00001v2",
                                "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                                "source_url": "https://arxiv.org/e-print/2401.00001v2",
                                "score": 0.91,
                            },
                        ]
                    },
                    ensure_ascii=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            payload = self.module.discover_and_register(
                knowledge_root=kernel_root,
                topic_slug="demo-topic",
                query="topological order anyon condensation",
                provider_chain=["search_results_json"],
                search_results_json=search_results_path,
                max_results=5,
                deepxiv_bin="deepxiv",
                preferred_arxiv_id="",
                select_index=0,
                registered_by="unit-test",
                download_source=False,
                force=False,
                skip_intake_projection=False,
            )

            self.assertEqual(payload["status"], "registered")
            self.assertEqual(payload["selected_provider"], "search_results_json")
            self.assertEqual(payload["selected_candidate"]["arxiv_id"], "2401.00001v2")
            self.assertTrue(payload["query_path"].exists())
            self.assertTrue(payload["candidate_evaluation_path"].exists())
            self.assertTrue(payload["registration_receipt_path"].exists())
            self.assertTrue(payload["layer0_source_json"].exists())
            self.assertIsNotNone(payload["intake_projection_root"])

            layer0_payload = json.loads(payload["layer0_source_json"].read_text(encoding="utf-8"))
            self.assertEqual(layer0_payload["provenance"]["arxiv_id"], "2401.00001v2")
            self.assertEqual(layer0_payload["title"], "Topological Order and Anyon Condensation")

    def test_source_discovery_docs_and_acceptance_are_documented(self) -> None:
        kernel_readme = (self.kernel_root / "README.md").read_text(encoding="utf-8")
        runtime_readme = (self.kernel_root / "runtime" / "README.md").read_text(encoding="utf-8")
        runbook = (self.kernel_root / "runtime" / "AITP_TEST_RUNBOOK.md").read_text(encoding="utf-8")
        l0_doc = (self.kernel_root / "L0_SOURCE_LAYER.md").read_text(encoding="utf-8")
        intake_runbook = (self.kernel_root / "intake" / "ARXIV_FIRST_SOURCE_INTAKE.md").read_text(encoding="utf-8")
        source_layer_readme = (self.kernel_root / "source-layer" / "README.md").read_text(encoding="utf-8")
        notice = (self.repo_root / "NOTICE").read_text(encoding="utf-8")

        self.assertIn("discover_and_register.py", kernel_readme)
        self.assertIn("run_l0_source_discovery_acceptance.py", kernel_readme)
        self.assertIn("run_l0_source_enrichment_acceptance.py", kernel_readme)
        self.assertIn("run_l0_source_concept_graph_acceptance.py", kernel_readme)
        self.assertIn("run_l0_source_discovery_acceptance.py", runtime_readme)
        self.assertIn("run_l0_source_enrichment_acceptance.py", runtime_readme)
        self.assertIn("run_l0_source_concept_graph_acceptance.py", runtime_readme)
        self.assertIn("run_l0_source_discovery_acceptance.py", runbook)
        self.assertIn("run_l0_source_enrichment_acceptance.py", runbook)
        self.assertIn("run_l0_source_concept_graph_acceptance.py", runbook)
        self.assertIn("discoveries/", l0_doc)
        self.assertIn("discover_and_register.py", l0_doc)
        self.assertIn("enrich_with_deepxiv.py", l0_doc)
        self.assertIn("build_concept_graph.py", l0_doc)
        self.assertIn("--metadata-only", intake_runbook)
        self.assertNotIn("--download-source", intake_runbook)
        self.assertIn("discover_and_register.py", source_layer_readme)
        self.assertIn("enrich_with_deepxiv.py", source_layer_readme)
        self.assertIn("build_concept_graph.py", source_layer_readme)
        self.assertIn("search_results_json", source_layer_readme)
        self.assertIn("DeepXiv SDK", notice)
        self.assertIn("Graphify", notice)

    def test_acceptance_script_mentions_discovery_evaluation_and_registration(self) -> None:
        script = (
            self.kernel_root / "runtime" / "scripts" / "run_l0_source_discovery_acceptance.py"
        ).read_text(encoding="utf-8")

        self.assertIn("discover_and_register.py", script)
        self.assertIn("candidate_evaluation_path", script)
        self.assertIn("layer0_source_json", script)
        self.assertIn("search_results_json", script)
        self.assertIn("enrichment_receipt", script)
        self.assertIn("concept_graph", script)

    def test_enrich_with_deepxiv_updates_registered_source_and_intake_projection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            knowledge_root = Path(tmpdir) / "kernel"
            metadata_override = {
                "arxiv_id": "2401.00001v2",
                "title": "Topological Order and Anyon Condensation",
                "summary": "A direct match for topological order and anyon condensation discovery.",
                "published": "2024-01-03T00:00:00Z",
                "updated": "2024-01-05T00:00:00Z",
                "authors": ["Primary Author", "Secondary Author"],
                "identifier": "https://arxiv.org/abs/2401.00001v2",
                "abs_url": "https://arxiv.org/abs/2401.00001v2",
                "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                "source_url": "https://arxiv.org/e-print/2401.00001v2",
            }
            registration = self.register_module.register_arxiv_source(
                knowledge_root=knowledge_root,
                topic_slug="demo-topic",
                arxiv_id="2401.00001v2",
                registered_by="unit-test",
                metadata_override=metadata_override,
            )

            enrichment = self.enrich_module.enrich_registered_source(
                knowledge_root=knowledge_root,
                topic_slug="demo-topic",
                source_id=registration["source_id"],
                enriched_by="unit-test",
                enrichment_override={
                    "paper": {
                        "tldr": "A bounded TLDR for topological order and anyon condensation.",
                        "keywords": ["topological order", "anyon condensation", "operator algebra"],
                        "github_url": "https://github.com/example/topological-order",
                        "sections": [
                            {
                                "name": "Introduction",
                                "idx": 0,
                                "tldr": "Introduces the topological order route.",
                                "token_count": 180,
                            },
                            {
                                "name": "Condensation mechanism",
                                "idx": 1,
                                "tldr": "Defines the anyon condensation mechanism.",
                                "token_count": 320,
                            },
                        ],
                    }
                },
            )

            source_payload = json.loads(registration["layer0_source_json"].read_text(encoding="utf-8"))
            intake_payload = json.loads((registration["intake_projection_root"] / "source.json").read_text(encoding="utf-8"))

            self.assertEqual(enrichment["status"], "enriched")
            self.assertEqual(
                source_payload["provenance"]["deepxiv_tldr"],
                "A bounded TLDR for topological order and anyon condensation.",
            )
            self.assertEqual(
                intake_payload["provenance"]["deepxiv_keywords"],
                ["topological order", "anyon condensation", "operator algebra"],
            )
            self.assertEqual(source_payload["provenance"]["deepxiv_sections"][0]["name"], "Introduction")
            self.assertEqual(source_payload["provenance"]["deepxiv_sections"][1]["token_count"], 320)
            self.assertEqual(
                source_payload["provenance"]["deepxiv_github_url"],
                "https://github.com/example/topological-order",
            )
            self.assertTrue(Path(enrichment["receipt_path"]).exists())
            self.assertEqual(Path(enrichment["source_json_path"]), registration["layer0_source_json"])

    def test_build_concept_graph_writes_graph_and_updates_registered_source_locator(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            knowledge_root = Path(tmpdir) / "kernel"
            metadata_override = {
                "arxiv_id": "2401.00001v2",
                "title": "Topological Order and Anyon Condensation",
                "summary": "A direct match for topological order and anyon condensation discovery.",
                "published": "2024-01-03T00:00:00Z",
                "updated": "2024-01-05T00:00:00Z",
                "authors": ["Primary Author", "Secondary Author"],
                "identifier": "https://arxiv.org/abs/2401.00001v2",
                "abs_url": "https://arxiv.org/abs/2401.00001v2",
                "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                "source_url": "https://arxiv.org/e-print/2401.00001v2",
            }
            registration = self.register_module.register_arxiv_source(
                knowledge_root=knowledge_root,
                topic_slug="demo-topic",
                arxiv_id="2401.00001v2",
                registered_by="unit-test",
                metadata_override=metadata_override,
                enrichment_override={
                    "paper": {
                        "tldr": "A bounded TLDR for topological order and anyon condensation.",
                        "keywords": ["topological order", "anyon condensation", "operator algebra"],
                        "sections": [
                            {"name": "Introduction", "idx": 0, "tldr": "Intro", "token_count": 180},
                            {"name": "Condensation mechanism", "idx": 1, "tldr": "Mechanism", "token_count": 320},
                        ],
                    }
                },
                skip_graph_build=True,
            )

            graph = self.graph_module.build_concept_graph_for_registered_source(
                knowledge_root=knowledge_root,
                topic_slug="demo-topic",
                source_id=registration["source_id"],
                built_by="unit-test",
                graph_override={
                    "nodes": [
                        {"node_id": "concept:topological-order", "label": "Topological order", "node_type": "concept", "confidence_tier": "EXTRACTED", "confidence_score": 0.95},
                        {"node_id": "concept:anyon-condensation", "label": "Anyon condensation", "node_type": "concept", "confidence_tier": "EXTRACTED", "confidence_score": 0.93},
                    ],
                    "edges": [
                        {"edge_id": "edge-topological-order-special-case-anyon-condensation", "from_id": "concept:anyon-condensation", "relation": "special_case_of", "to_id": "concept:topological-order", "evidence_refs": ["source-layer/topics/demo-topic/sources/paper-topological-order-and-anyon-condensation-2401-00001/source.json"], "notes": "offline fixture"}
                    ],
                    "hyperedges": [
                        {"hyperedge_id": "hyperedge-condensation-route", "relation": "supports", "node_ids": ["concept:topological-order", "concept:anyon-condensation"], "evidence_refs": ["source-layer/topics/demo-topic/sources/paper-topological-order-and-anyon-condensation-2401-00001/source.json"], "notes": "offline fixture"}
                    ],
                    "communities": [
                        {"community_id": "community-topological-order", "label": "Topological order cluster", "node_ids": ["concept:topological-order", "concept:anyon-condensation"]}
                    ],
                    "god_nodes": ["concept:topological-order"],
                },
            )

            source_payload = json.loads(registration["layer0_source_json"].read_text(encoding="utf-8"))
            intake_payload = json.loads((registration["intake_projection_root"] / "source.json").read_text(encoding="utf-8"))
            graph_payload = json.loads(Path(graph["concept_graph_path"]).read_text(encoding="utf-8"))

            self.assertEqual(graph["status"], "built")
            self.assertTrue(Path(graph["concept_graph_path"]).exists())
            self.assertTrue(Path(graph["receipt_path"]).exists())
            self.assertEqual(graph_payload["god_nodes"], ["concept:topological-order"])
            self.assertEqual(graph_payload["nodes"][0]["node_type"], "concept")
            self.assertEqual(graph_payload["edges"][0]["relation"], "special_case_of")
            self.assertEqual(source_payload["locator"]["concept_graph_path"], graph["concept_graph_relative_path"])
            self.assertEqual(intake_payload["locator"]["concept_graph_path"], graph["concept_graph_relative_path"])

    def test_register_arxiv_source_can_run_integrated_enrichment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            knowledge_root = Path(tmpdir) / "kernel"
            metadata_override = {
                "arxiv_id": "2401.00001v2",
                "title": "Topological Order and Anyon Condensation",
                "summary": "A direct match for topological order and anyon condensation discovery.",
                "published": "2024-01-03T00:00:00Z",
                "updated": "2024-01-05T00:00:00Z",
                "authors": ["Primary Author", "Secondary Author"],
                "identifier": "https://arxiv.org/abs/2401.00001v2",
                "abs_url": "https://arxiv.org/abs/2401.00001v2",
                "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                "source_url": "https://arxiv.org/e-print/2401.00001v2",
            }

            registration = self.register_module.register_arxiv_source(
                knowledge_root=knowledge_root,
                topic_slug="demo-topic",
                arxiv_id="2401.00001v2",
                registered_by="unit-test",
                metadata_override=metadata_override,
                enrichment_override={
                    "paper": {
                        "tldr": "Integrated enrichment summary.",
                        "keywords": ["topological order", "anyon condensation"],
                        "sections": [
                            {"name": "Introduction", "idx": 0, "tldr": "Intro", "token_count": 120}
                        ],
                    }
                },
            )

            source_payload = json.loads(registration["layer0_source_json"].read_text(encoding="utf-8"))
            self.assertEqual(registration["enrichment_status"], "enriched")
            self.assertTrue(Path(registration["enrichment_receipt_path"]).exists())
            self.assertEqual(source_payload["provenance"]["deepxiv_tldr"], "Integrated enrichment summary.")

    def test_register_arxiv_source_can_run_integrated_concept_graph_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            knowledge_root = Path(tmpdir) / "kernel"
            metadata_override = {
                "arxiv_id": "2401.00001v2",
                "title": "Topological Order and Anyon Condensation",
                "summary": "A direct match for topological order and anyon condensation discovery.",
                "published": "2024-01-03T00:00:00Z",
                "updated": "2024-01-05T00:00:00Z",
                "authors": ["Primary Author", "Secondary Author"],
                "identifier": "https://arxiv.org/abs/2401.00001v2",
                "abs_url": "https://arxiv.org/abs/2401.00001v2",
                "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                "source_url": "https://arxiv.org/e-print/2401.00001v2",
            }

            registration = self.register_module.register_arxiv_source(
                knowledge_root=knowledge_root,
                topic_slug="demo-topic",
                arxiv_id="2401.00001v2",
                registered_by="unit-test",
                metadata_override=metadata_override,
                enrichment_override={
                    "paper": {
                        "tldr": "Integrated enrichment summary.",
                        "keywords": ["topological order", "anyon condensation"],
                        "sections": [{"name": "Introduction", "idx": 0, "tldr": "Intro", "token_count": 120}],
                    }
                },
                graph_override={
                    "nodes": [
                        {"node_id": "concept:topological-order", "label": "Topological order", "node_type": "concept", "confidence_tier": "EXTRACTED", "confidence_score": 0.95}
                    ],
                    "edges": [],
                    "hyperedges": [],
                    "communities": [{"community_id": "community-topological-order", "label": "Topological order cluster", "node_ids": ["concept:topological-order"]}],
                    "god_nodes": ["concept:topological-order"],
                },
            )

            source_payload = json.loads(registration["layer0_source_json"].read_text(encoding="utf-8"))
            self.assertEqual(registration["graph_build_status"], "built")
            self.assertTrue(Path(registration["concept_graph_path"]).exists())
            self.assertTrue(Path(registration["graph_receipt_path"]).exists())
            self.assertIn("concept_graph_path", source_payload["locator"])

    def test_discovery_bridge_can_run_integrated_graph_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            work_root = Path(tmpdir)
            kernel_root = work_root / "kernel"
            search_results_path = work_root / "search-results.json"
            search_results_path.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "arxiv_id": "2401.00001v2",
                                "title": "Topological Order and Anyon Condensation",
                                "summary": "A direct match for topological order and anyon condensation discovery.",
                                "published": "2024-01-03T00:00:00Z",
                                "updated": "2024-01-04T00:00:00Z",
                                "authors": ["Primary Author", "Secondary Author"],
                                "identifier": "https://arxiv.org/abs/2401.00001v2",
                                "abs_url": "https://arxiv.org/abs/2401.00001v2",
                                "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                                "source_url": "https://arxiv.org/e-print/2401.00001v2",
                                "score": 0.91,
                            },
                        ]
                    },
                    ensure_ascii=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            payload = self.module.discover_and_register(
                knowledge_root=kernel_root,
                topic_slug="demo-topic",
                query="topological order anyon condensation",
                provider_chain=["search_results_json"],
                search_results_json=search_results_path,
                max_results=5,
                deepxiv_bin="deepxiv",
                preferred_arxiv_id="",
                select_index=0,
                registered_by="unit-test",
                download_source=False,
                force=False,
                skip_intake_projection=False,
                enrichment_override={
                    "paper": {
                        "tldr": "Discovery-path enrichment summary.",
                        "keywords": ["topological order", "anyon condensation"],
                        "sections": [{"name": "Introduction", "idx": 0, "tldr": "Intro", "token_count": 120}],
                    }
                },
                graph_override={
                    "nodes": [
                        {"node_id": "concept:topological-order", "label": "Topological order", "node_type": "concept", "confidence_tier": "EXTRACTED", "confidence_score": 0.95}
                    ],
                    "edges": [],
                    "hyperedges": [],
                    "communities": [{"community_id": "community-topological-order", "label": "Topological order cluster", "node_ids": ["concept:topological-order"]}],
                    "god_nodes": ["concept:topological-order"],
                },
            )

            layer0_payload = json.loads(payload["layer0_source_json"].read_text(encoding="utf-8"))
            self.assertEqual(payload["graph_build_status"], "built")
            self.assertTrue(payload["graph_receipt_path"].exists())
            self.assertEqual(layer0_payload["locator"]["concept_graph_path"], payload["concept_graph_relative_path"])

    def test_discovery_bridge_can_run_integrated_post_registration_enrichment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            work_root = Path(tmpdir)
            kernel_root = work_root / "kernel"
            search_results_path = work_root / "search-results.json"
            search_results_path.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "arxiv_id": "2401.00001v2",
                                "title": "Topological Order and Anyon Condensation",
                                "summary": "A direct match for topological order and anyon condensation discovery.",
                                "published": "2024-01-03T00:00:00Z",
                                "updated": "2024-01-04T00:00:00Z",
                                "authors": ["Primary Author", "Secondary Author"],
                                "identifier": "https://arxiv.org/abs/2401.00001v2",
                                "abs_url": "https://arxiv.org/abs/2401.00001v2",
                                "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                                "source_url": "https://arxiv.org/e-print/2401.00001v2",
                                "score": 0.91,
                            },
                        ]
                    },
                    ensure_ascii=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            payload = self.module.discover_and_register(
                knowledge_root=kernel_root,
                topic_slug="demo-topic",
                query="topological order anyon condensation",
                provider_chain=["search_results_json"],
                search_results_json=search_results_path,
                max_results=5,
                deepxiv_bin="deepxiv",
                preferred_arxiv_id="",
                select_index=0,
                registered_by="unit-test",
                download_source=False,
                force=False,
                skip_intake_projection=False,
                enrichment_override={
                    "paper": {
                        "tldr": "Discovery-path enrichment summary.",
                        "keywords": ["topological order", "anyon condensation"],
                        "sections": [
                            {"name": "Introduction", "idx": 0, "tldr": "Intro", "token_count": 120}
                        ],
                    }
                },
            )

            layer0_payload = json.loads(payload["layer0_source_json"].read_text(encoding="utf-8"))
            self.assertEqual(payload["enrichment_status"], "enriched")
            self.assertTrue(payload["enrichment_receipt_path"].exists())
            self.assertEqual(layer0_payload["provenance"]["deepxiv_tldr"], "Discovery-path enrichment summary.")


if __name__ == "__main__":
    unittest.main()
