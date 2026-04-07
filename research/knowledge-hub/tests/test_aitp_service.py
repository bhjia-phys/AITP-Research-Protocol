from __future__ import annotations

import json
import shutil
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

import sys

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.aitp_service import AITPService
from knowledge_hub.aitp_codex import build_codex_prompt, build_parser as build_codex_parser


class _LoopStubService(AITPService):
    def orchestrate(self, **kwargs):  # noqa: ANN003
        topic_slug = kwargs.get("topic_slug") or "demo-topic"
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L3",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "action_queue.jsonl").write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:01",
                    "status": "pending",
                    "auto_runnable": True,
                    "action_type": "skill_discovery",
                    "handler_args": {"queries": ["finite-size benchmark"]},
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        return {
            "topic_slug": topic_slug,
            "runtime_root": str(runtime_root),
        }

    def audit(self, *, topic_slug: str, phase: str = "entry", updated_by: str = "aitp-cli"):
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "conformance_state.json").write_text(
            json.dumps({"overall_status": "pass"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return {
            "topic_slug": topic_slug,
            "phase": phase,
            "conformance_state": {"overall_status": "pass"},
        }

    def capability_audit(self, *, topic_slug: str, updated_by: str = "aitp-cli"):
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        payload = {
            "topic_slug": topic_slug,
            "overall_status": "ready",
            "sections": {"runtime": {}},
            "recommendations": [],
        }
        (runtime_root / "capability_registry.json").write_text(
            json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (runtime_root / "capability_report.md").write_text("# Capability audit\n", encoding="utf-8")
        return {
            **payload,
            "capability_registry_path": str(runtime_root / "capability_registry.json"),
            "capability_report_path": str(runtime_root / "capability_report.md"),
        }

    def audit_operation_trust(self, *, topic_slug: str, run_id: str | None = None, updated_by: str = "aitp-cli"):
        return {
            "topic_slug": topic_slug,
            "run_id": run_id or "2026-03-13-demo",
            "overall_status": "pass",
            "operations": [],
            "recommendations": [],
            "trust_audit_path": str(self.kernel_root / "validation" / "topics" / topic_slug / "runs" / "2026-03-13-demo" / "trust_audit.json"),
            "trust_report_path": str(self.kernel_root / "validation" / "topics" / topic_slug / "runs" / "2026-03-13-demo" / "trust_audit.md"),
        }

    def _discover_skills(self, *, topic_slug: str, queries: list[str], updated_by: str, agent_target: str = "openclaw"):
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        (runtime_root / "skill_discovery.json").write_text(
            json.dumps({"queries": queries}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (runtime_root / "skill_recommendations.md").write_text("# Skill recommendations\n", encoding="utf-8")
        return {
            "skill_discovery_path": str(runtime_root / "skill_discovery.json"),
            "skill_recommendations_path": str(runtime_root / "skill_recommendations.md"),
            "queries": queries,
        }


class _TailSyncLoopStubService(_LoopStubService):
    def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
        super().__init__(*args, **kwargs)
        self.orchestrate_calls = 0

    def orchestrate(self, **kwargs):  # noqa: ANN003
        self.orchestrate_calls += 1
        topic_slug = kwargs.get("topic_slug") or "demo-topic"
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L3",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        if self.orchestrate_calls == 1:
            queue_rows = [
                {
                    "action_id": "action:demo-topic:01",
                    "status": "pending",
                    "auto_runnable": True,
                    "action_type": "skill_discovery",
                    "handler_args": {"queries": ["finite-size benchmark"]},
                }
            ]
        else:
            queue_rows = [
                {
                    "action_id": "action:demo-topic:02",
                    "status": "pending",
                    "auto_runnable": False,
                    "action_type": "manual_followup",
                    "summary": "Move to the next bounded manual lane after the auto step finishes.",
                }
            ]
        (runtime_root / "action_queue.jsonl").write_text(
            "".join(
                json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n"
                for row in queue_rows
            ),
            encoding="utf-8",
        )
        return {
            "topic_slug": topic_slug,
            "runtime_root": str(runtime_root),
        }


class _SteeringLoopStubService(AITPService):
    def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
        super().__init__(*args, **kwargs)
        self.orchestrate_calls: list[dict] = []

    def orchestrate(self, **kwargs):  # noqa: ANN003
        self.orchestrate_calls.append(dict(kwargs))
        topic_slug = kwargs.get("topic_slug") or "demo-topic"
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        runtime_root.mkdir(parents=True, exist_ok=True)
        feedback_root = self.kernel_root / "feedback" / "topics" / topic_slug / "runs" / "2026-03-13-demo"
        feedback_root.mkdir(parents=True, exist_ok=True)
        (feedback_root / "next_actions.md").write_text(
            "1. Continue the current bounded lane.\n",
            encoding="utf-8",
        )
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L3",
                    "pointers": {
                        "next_actions_path": f"feedback/topics/{topic_slug}/runs/2026-03-13-demo/next_actions.md",
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "action_queue.jsonl").write_text("", encoding="utf-8")
        (runtime_root / "agent_brief.md").write_text("# Brief\n", encoding="utf-8")
        (runtime_root / "operator_console.md").write_text("# Console\n", encoding="utf-8")
        (runtime_root / "conformance_report.md").write_text("# Conformance\n", encoding="utf-8")
        return {
            "topic_slug": topic_slug,
            "runtime_root": str(runtime_root),
            "topic_state": json.loads((runtime_root / "topic_state.json").read_text(encoding="utf-8")),
            "files": {
                "agent_brief": str(runtime_root / "agent_brief.md"),
                "operator_console": str(runtime_root / "operator_console.md"),
                "conformance_report": str(runtime_root / "conformance_report.md"),
            },
        }

    def audit(self, *, topic_slug: str, phase: str = "entry", updated_by: str = "aitp-cli"):
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "conformance_state.json").write_text(
            json.dumps({"overall_status": "pass"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return {
            "topic_slug": topic_slug,
            "phase": phase,
            "conformance_state": {"overall_status": "pass"},
        }

    def capability_audit(self, *, topic_slug: str, updated_by: str = "aitp-cli"):
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        payload = {
            "topic_slug": topic_slug,
            "overall_status": "ready",
            "sections": {"runtime": {}},
            "recommendations": [],
        }
        (runtime_root / "capability_registry.json").write_text(
            json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (runtime_root / "capability_report.md").write_text("# Capability audit\n", encoding="utf-8")
        return {
            **payload,
            "capability_registry_path": str(runtime_root / "capability_registry.json"),
            "capability_report_path": str(runtime_root / "capability_report.md"),
        }


class _FollowupStubService(AITPService):
    def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
        super().__init__(*args, **kwargs)
        self.orchestrated_topics: list[str] = []

    def orchestrate(self, **kwargs):  # noqa: ANN003
        topic_slug = kwargs["topic_slug"]
        self.orchestrated_topics.append(topic_slug)
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "latest_run_id": "2026-03-13-followup",
                    "resume_stage": "L1",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        source_index_path = self.kernel_root / "source-layer" / "topics" / topic_slug / "source_index.jsonl"
        source_index_path.parent.mkdir(parents=True, exist_ok=True)
        arxiv_ids = kwargs.get("arxiv_ids") or []
        source_index_path.write_text(
            json.dumps(
                {
                    "source_id": f"paper:{arxiv_ids[0].replace('.', '-')}" if arxiv_ids else f"paper:{topic_slug}",
                    "source_type": "paper",
                    "title": f"Follow-up {arxiv_ids[0]}" if arxiv_ids else topic_slug,
                    "summary": "Follow-up source.",
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return {
            "topic_slug": topic_slug,
            "runtime_root": str(runtime_root),
        }


class AITPServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self.kernel_root = self.root / "kernel"
        self.repo_root = self.root / "repo"
        self.package_root = Path(__file__).resolve().parents[1]
        self.kernel_root.mkdir(parents=True)
        self.repo_root.mkdir(parents=True)
        (self.kernel_root / "canonical").mkdir(parents=True, exist_ok=True)
        (self.kernel_root / "schemas").mkdir(parents=True, exist_ok=True)
        (self.kernel_root / "runtime" / "schemas").mkdir(parents=True, exist_ok=True)
        for schema_path in (self.package_root / "schemas").glob("*.json"):
            shutil.copyfile(schema_path, self.kernel_root / "schemas" / schema_path.name)
        runtime_bundle_schema = self.package_root / "runtime" / "schemas" / "progressive-disclosure-runtime-bundle.schema.json"
        shutil.copyfile(
            runtime_bundle_schema,
            self.kernel_root / "runtime" / "schemas" / runtime_bundle_schema.name,
        )
        result_brief_schema = self.package_root / "runtime" / "schemas" / "result-brief.schema.json"
        shutil.copyfile(
            result_brief_schema,
            self.kernel_root / "runtime" / "schemas" / result_brief_schema.name,
        )
        self.service = AITPService(kernel_root=self.kernel_root, repo_root=self.repo_root)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _write_runtime_state(self, topic_slug: str = "demo-topic", run_id: str = "2026-03-13-demo") -> Path:
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "latest_run_id": run_id,
                    "resume_stage": "L3",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return runtime_root

    def _write_candidate(
        self,
        topic_slug: str = "demo-topic",
        run_id: str = "2026-03-13-demo",
        candidate_type: str = "concept",
        intended_l2_target: str = "concept:demo-promoted-concept",
        title: str = "Demo Promoted Concept",
    ) -> Path:
        feedback_root = self.kernel_root / "feedback" / "topics" / topic_slug / "runs" / run_id
        feedback_root.mkdir(parents=True, exist_ok=True)
        ledger_path = feedback_root / "candidate_ledger.jsonl"
        row = {
            "candidate_id": "candidate:demo-candidate",
            "candidate_type": candidate_type,
            "title": title,
            "summary": "A bounded demo concept for testing the promotion gate and external writeback.",
            "topic_slug": topic_slug,
            "run_id": run_id,
            "origin_refs": [
                {
                    "id": "paper:demo-source",
                    "layer": "L0",
                    "object_type": "source",
                    "path": "source-layer/topics/demo-topic/source_index.jsonl",
                    "title": "Demo Source",
                    "summary": "Public source entry for promotion testing.",
                }
            ],
            "question": "Can this candidate be promoted through a human approval gate into an external L2 backend?",
            "assumptions": ["The example is bounded and non-scientific."],
            "proposed_validation_route": "bounded-smoke",
            "intended_l2_targets": [intended_l2_target],
            "status": "ready_for_validation",
        }
        ledger_path.write_text(json.dumps(row, ensure_ascii=True) + "\n", encoding="utf-8")
        source_root = self.kernel_root / "source-layer" / "topics" / topic_slug
        source_root.mkdir(parents=True, exist_ok=True)
        (source_root / "source_index.jsonl").write_text(
            json.dumps(
                {
                    "source_id": "paper:demo-source",
                    "source_type": "paper",
                    "title": "Demo Source",
                    "topic_slug": topic_slug,
                    "provenance": {
                        "authors": ["Demo Author"],
                        "published": "2026-03-13T00:00:00+08:00",
                        "updated": "2026-03-13T00:00:00+08:00",
                        "abs_url": "https://example.org/demo",
                        "pdf_url": "https://example.org/demo.pdf",
                        "source_url": "https://example.org/demo.tar.gz",
                    },
                    "acquired_at": "2026-03-13T00:00:00+08:00",
                    "summary": "Demo source summary.",
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return ledger_path

    def _write_tpkn_backend_card(self, *, allows_auto: bool = True) -> Path:
        backends_root = self.kernel_root / "canonical" / "backends"
        backends_root.mkdir(parents=True, exist_ok=True)
        card_path = backends_root / "theoretical-physics-knowledge-network.json"
        card_payload = {
            "$schema": "../../schemas/l2-backend.schema.json",
            "backend_id": "backend:theoretical-physics-knowledge-network",
            "title": "Theoretical Physics Knowledge Network",
            "backend_type": "mixed_local_library",
            "status": "active",
            "root_paths": ["__TPKN_REPO_ROOT__"],
            "purpose": ["Test backend card for promotion flows."],
            "artifact_granularity": "One typed unit at a time.",
            "source_policy": {
                "requires_l0_registration": True,
                "allows_direct_canonical_promotion": False,
                "allows_auto_canonical_promotion": allows_auto,
                "auto_promotion_domains": ["theory-formal"] if allows_auto else [],
                "auto_promotion_requires_coverage_audit": True,
                "auto_promotion_requires_multi_agent_consensus": True,
                "auto_promotion_requires_regression_gate": True,
                "auto_promotion_requires_split_clearance": True,
                "auto_promotion_requires_gap_honesty": True,
                "default_source_type": "local_note",
            },
            "l0_registration": {
                "script": "source-layer/scripts/register_local_note_source.py",
                "required_provenance_fields": ["provenance.backend_id"],
                "required_locator_fields": ["locator.backend_relative_path"],
            },
            "canonical_targets": [
                "concept",
                "definition_card",
                "notation_card",
                "equation_card",
                "assumption_card",
                "regime_card",
                "theorem_card",
                "claim_card",
                "proof_fragment",
                "derivation_step",
                "derivation_object",
                "method",
                "workflow",
                "topic_skill_projection",
                "bridge",
                "example_card",
                "caveat_card",
                "equivalence_map",
                "symbol_binding",
                "validation_pattern",
                "warning_note",
            ],
            "retrieval_hints": ["Read generated indexes before writeback."],
            "notes": "Test card.",
        }
        card_path.write_text(json.dumps(card_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        (backends_root / "backend_index.jsonl").write_text(
            json.dumps(
                {
                    "backend_id": "backend:theoretical-physics-knowledge-network",
                    "title": "Theoretical Physics Knowledge Network",
                    "backend_type": "mixed_local_library",
                    "status": "active",
                    "card_path": "canonical/backends/theoretical-physics-knowledge-network.json",
                    "canonical_targets": card_payload["canonical_targets"],
                    "allows_auto_canonical_promotion": allows_auto,
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return card_path

    def _write_fake_tpkn_repo(self) -> Path:
        tpkn_root = self.root / "tpkn"
        for relative in (
            "docs",
            "schema",
            "scripts",
            "sources",
            "units/concepts",
            "units/definitions",
            "units/notations",
            "units/assumptions",
            "units/regimes",
            "units/theorems",
            "units/claims",
            "units/proof-fragments",
            "units/derivation-steps",
            "units/derivations",
            "units/methods",
            "units/topic-skill-projections",
            "units/bridges",
            "units/examples",
            "units/caveats",
            "units/equivalences",
            "units/symbol-bindings",
            "units/equations",
            "units/quantities",
            "units/models",
            "units/source-maps",
            "units/warnings",
            "edges",
            "indexes",
            "portal",
            "human-mirror",
        ):
            (tpkn_root / relative).mkdir(parents=True, exist_ok=True)
        (tpkn_root / "docs" / "PROTOCOLS.md").write_text("# Demo\n", encoding="utf-8")
        (tpkn_root / "docs" / "L2_RETRIEVAL_PROTOCOL.md").write_text("# Demo\n", encoding="utf-8")
        (tpkn_root / "docs" / "OBJECT_MODEL.md").write_text("# Demo\n", encoding="utf-8")
        (tpkn_root / "docs" / "L2_BRIDGE_PROTOCOL.md").write_text("# Demo\n", encoding="utf-8")
        (tpkn_root / "edges" / "edges.jsonl").write_text("", encoding="utf-8")
        (tpkn_root / "schema" / "unit.schema.json").write_text(
            json.dumps({"title": "demo-unit-schema"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (tpkn_root / "schema" / "source-manifest.schema.json").write_text(
            json.dumps({"title": "demo-source-schema"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (tpkn_root / "scripts" / "kb.py").write_text(
            textwrap.dedent(
                """\
                from __future__ import annotations

                import json
                import sys
                from pathlib import Path

                ROOT = Path(__file__).resolve().parents[1]
                UNIT_DIRS = {
                    "concept": ROOT / "units" / "concepts",
                    "definition": ROOT / "units" / "definitions",
                    "notation": ROOT / "units" / "notations",
                    "assumption": ROOT / "units" / "assumptions",
                    "regime": ROOT / "units" / "regimes",
                    "theorem": ROOT / "units" / "theorems",
                    "claim": ROOT / "units" / "claims",
                    "proof_fragment": ROOT / "units" / "proof-fragments",
                    "derivation_step": ROOT / "units" / "derivation-steps",
                    "derivation": ROOT / "units" / "derivations",
                    "method": ROOT / "units" / "methods",
                    "topic_skill_projection": ROOT / "units" / "topic-skill-projections",
                    "bridge": ROOT / "units" / "bridges",
                    "example": ROOT / "units" / "examples",
                    "caveat": ROOT / "units" / "caveats",
                    "equivalence": ROOT / "units" / "equivalences",
                    "symbol_binding": ROOT / "units" / "symbol-bindings",
                    "equation": ROOT / "units" / "equations",
                    "quantity": ROOT / "units" / "quantities",
                    "model": ROOT / "units" / "models",
                    "source_map": ROOT / "units" / "source-maps",
                    "warning": ROOT / "units" / "warnings",
                }
                LIST_FIELDS = {
                    "review_artifacts",
                    "merge_lineage",
                    "conflict_refs",
                    "equivalence_refs",
                }

                def read_json(path: Path) -> dict:
                    return json.loads(path.read_text(encoding="utf-8"))

                def build() -> None:
                    rows = []
                    for unit_type, unit_dir in UNIT_DIRS.items():
                        unit_dir.mkdir(parents=True, exist_ok=True)
                        for path in sorted(unit_dir.glob("*.json")):
                            payload = read_json(path)
                            rows.append(
                                {
                                    "id": payload["id"],
                                    "type": payload["type"],
                                    "title": payload["title"],
                                    "summary": payload["summary"],
                                    "path": str(path.relative_to(ROOT)),
                                    "domain": payload.get("domain"),
                                    "subdomain": payload.get("subdomain"),
                                    "tags": payload.get("tags") or [],
                                    "aliases": payload.get("aliases") or [],
                                    "dependencies": payload.get("dependencies") or [],
                                    "related_units": payload.get("related_units") or [],
                                    "formalization_status": payload.get("formalization_status"),
                                    "validation_status": payload.get("validation_status"),
                                    "maturity": payload.get("maturity"),
                                    "source_anchor_count": len(payload.get("source_anchors") or []),
                                }
                            )
                    unit_index = ROOT / "indexes" / "unit_index.jsonl"
                    unit_index.parent.mkdir(parents=True, exist_ok=True)
                    unit_index.write_text(
                        "".join(json.dumps(row, ensure_ascii=False) + "\\n" for row in rows),
                        encoding="utf-8",
                    )

                def main() -> int:
                    if len(sys.argv) < 2:
                        return 1
                    command = sys.argv[1]
                    if command == "check":
                        for unit_type, unit_dir in UNIT_DIRS.items():
                            unit_dir.mkdir(parents=True, exist_ok=True)
                            for path in sorted(unit_dir.glob("*.json")):
                                payload = read_json(path)
                                for field in LIST_FIELDS:
                                    if field in payload and not isinstance(payload[field], list):
                                        raise SystemExit(
                                            f\"ERROR: {path.relative_to(ROOT)}: field '{field}' must be a list\"
                                        )
                        return 0
                    if command == "build":
                        build()
                        return 0
                    return 1

                if __name__ == "__main__":
                    raise SystemExit(main())
                """
            ),
            encoding="utf-8",
        )
        return tpkn_root

    def test_service_accepts_string_paths(self) -> None:
        (self.repo_root / "AGENTS.md").write_text("# test\n", encoding="utf-8")
        (self.repo_root / "docs").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "docs" / "CHARTER.md").write_text("# charter\n", encoding="utf-8")
        (self.repo_root / "research" / "knowledge-hub").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "research" / "knowledge-hub" / "setup.py").write_text("# setup\n", encoding="utf-8")
        service = AITPService(
            kernel_root=str(self.kernel_root),
            repo_root=str(self.repo_root),
        )

        self.assertEqual(service.kernel_root, self.kernel_root.resolve())
        self.assertEqual(service.repo_root, self.repo_root.resolve())

    def test_scaffold_baseline_writes_expected_artifacts(self) -> None:
        payload = self.service.scaffold_baseline(
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
            title="Public finite-size benchmark baseline",
            reference="arXiv:0000.00000",
            agreement_criterion="curves agree qualitatively and peak order matches",
        )

        plan = Path(payload["paths"]["baseline_plan"])
        results = Path(payload["paths"]["baseline_results"])
        summary = Path(payload["paths"]["baseline_summary"])

        self.assertTrue(plan.exists())
        self.assertTrue(results.exists())
        self.assertTrue(summary.exists())
        rows = [json.loads(line) for line in results.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "planned")

    def test_scaffold_atomic_understanding_writes_expected_artifacts(self) -> None:
        payload = self.service.scaffold_atomic_understanding(
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
            method_title="Finite-size spectral diagnostic",
        )

        concept_map = Path(payload["paths"]["atomic_concept_map"])
        graph = Path(payload["paths"]["derivation_dependency_graph"])
        summary = Path(payload["paths"]["understanding_summary"])

        self.assertTrue(concept_map.exists())
        self.assertTrue(graph.exists())
        self.assertTrue(summary.exists())
        concept_payload = json.loads(concept_map.read_text(encoding="utf-8"))
        graph_payload = json.loads(graph.read_text(encoding="utf-8"))
        self.assertEqual(concept_payload["status"], "planned")
        self.assertEqual(graph_payload["status"], "planned")

    def test_materialize_runtime_protocol_bundle_writes_expected_artifacts(self) -> None:
        runtime_root = self._write_runtime_state()
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L3",
                    "last_materialized_stage": "L3",
                    "research_mode": "formal_derivation",
                    "backend_bridge_count": 1,
                    "backend_bridges": [
                        {
                            "backend_id": "backend:formal-theory-note-library",
                            "title": "Formal Theory Note Library",
                            "backend_type": "human_note_library",
                            "status": "active",
                            "card_path": "canonical/backends/formal-theory-note-library.json",
                            "card_status": "present",
                            "backend_root": "/tmp/formal-theory-notes",
                            "artifact_granularity": "One derivation-focused note is the atomic backend artifact.",
                            "artifact_kinds": ["formal_theory_note"],
                            "canonical_targets": ["concept", "derivation_object"],
                            "l0_registration_script": "source-layer/scripts/register_local_note_source.py",
                            "source_count": 1,
                            "source_ids": ["local_note:modular-flow-outline"],
                        }
                    ],
                    "research_mode_profile": {
                        "reproducibility_expectations": ["Keep backend provenance explicit."],
                        "note_expectations": ["Write a human-readable derivation note."],
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "run a bounded public protocol check",
                    "delivery_contract": {
                        "rule": "Outputs must cite exact artifact paths and justify the chosen layer."
                    },
                    "human_edit_surfaces": [
                        {
                            "surface": "runtime_queue_contract",
                            "path": "runtime/topics/demo-topic/action_queue_contract.generated.md",
                            "role": "editable queue contract snapshot",
                        }
                    ],
                    "action_queue_surface": {
                        "queue_source": "heuristic",
                        "declared_contract_path": None,
                        "generated_contract_path": "runtime/topics/demo-topic/action_queue_contract.generated.json",
                        "generated_contract_note_path": "runtime/topics/demo-topic/action_queue_contract.generated.md",
                    },
                    "decision_surface": {
                        "decision_mode": "continue_unfinished",
                        "decision_source": "heuristic",
                        "decision_contract_status": "missing",
                        "control_note_path": None,
                        "selected_action_id": "action:demo-topic:01",
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "agent_brief.md").write_text("# Brief\n", encoding="utf-8")
        (runtime_root / "operator_console.md").write_text("# Console\n", encoding="utf-8")
        (runtime_root / "action_queue_contract.generated.md").write_text("# Queue\n", encoding="utf-8")
        (runtime_root / "conformance_report.md").write_text("# Conformance\n", encoding="utf-8")
        (runtime_root / "promotion_gate.json").write_text(
            json.dumps(
                {
                    "status": "approved",
                    "candidate_id": "candidate:demo-candidate",
                    "candidate_type": "concept",
                    "backend_id": "backend:theoretical-physics-knowledge-network",
                    "target_backend_root": "/tmp/tpkn",
                    "approved_by": "human",
                    "promoted_units": [],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "promotion_gate.md").write_text("# Promotion gate\n", encoding="utf-8")
        (runtime_root / "action_queue.jsonl").write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:01",
                    "status": "pending",
                    "action_type": "inspect_resume_state",
                    "summary": "Inspect the current runtime state.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

        result = self.service._materialize_runtime_protocol_bundle(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
            human_request="run a bounded public protocol check",
        )

        protocol_json = Path(result["runtime_protocol_path"])
        protocol_note = Path(result["runtime_protocol_note_path"])
        self.assertTrue(protocol_json.exists())
        self.assertTrue(protocol_note.exists())
        payload = json.loads(protocol_json.read_text(encoding="utf-8"))
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "runtime"
                / "schemas"
                / "progressive-disclosure-runtime-bundle.schema.json"
            ).read_text(encoding="utf-8")
        )
        Draft202012Validator(schema).validate(payload)
        self.assertEqual(
            payload["$schema"],
            "https://aitp.local/schemas/progressive-disclosure-runtime-bundle.schema.json",
        )
        self.assertEqual(payload["bundle_kind"], "progressive_disclosure_runtime_bundle")
        self.assertEqual(payload["human_request"], "run a bounded public protocol check")
        self.assertEqual(payload["priority_rules"][0]["source"], "control_note_or_decision_contract")
        self.assertEqual(payload["action_queue_surface"]["queue_source"], "heuristic")
        self.assertEqual(payload["active_research_contract"]["question_id"], "research_question:demo-topic")
        self.assertEqual(payload["idea_packet"]["status"], "approved_for_execution")
        self.assertEqual(payload["operator_checkpoint"]["status"], "cancelled")
        self.assertEqual(payload["active_research_contract"]["template_mode"], "formal_theory")
        self.assertEqual(payload["backend_bridges"][0]["backend_id"], "backend:formal-theory-note-library")
        self.assertEqual(payload["promotion_gate"]["status"], "approved")
        self.assertEqual(payload["promotion_readiness"]["status"], "approved")
        self.assertEqual(payload["open_gap_summary"]["status"], "clear")
        self.assertEqual(payload["strategy_memory"]["status"], "absent")
        self.assertEqual(payload["topic_skill_projection"]["status"], "not_applicable")
        self.assertEqual(payload["topic_completion"]["status"], "not_assessed")
        self.assertEqual(payload["lean_bridge"]["status"], "empty")
        self.assertEqual(payload["minimal_execution_brief"]["selected_action_id"], "action:demo-topic:01")
        self.assertEqual(payload["minimal_execution_brief"]["queue_source"], "heuristic")
        self.assertEqual(payload["load_profile"], "light")
        self.assertEqual(payload["must_read_now"][0]["path"], "runtime/topics/demo-topic/topic_state.json")
        self.assertEqual(payload["must_read_now"][1]["path"], "runtime/topics/demo-topic/research_question.contract.md")
        self.assertEqual(payload["must_read_now"][2]["path"], "runtime/topics/demo-topic/control_note.md")
        self.assertEqual(payload["must_read_now"][3]["path"], "runtime/topics/demo-topic/operator_console.md")
        self.assertFalse(any(row["path"] == "RESEARCH_EXECUTION_GUARDRAILS.md" for row in payload["must_read_now"]))
        self.assertEqual(payload["escalation_triggers"][1]["trigger"], "promotion_intent")
        self.assertTrue(any(row["trigger"] == "decision_override_present" for row in payload["escalation_triggers"]))
        self.assertTrue(any(row["slice"] == "current_execution_lane" for row in payload["recommended_protocol_slices"]))
        self.assertTrue(
            any(
                row["trigger"] == "formal_theory_upstream_scan"
                and "FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md" in row["required_reads"]
                for row in payload["escalation_triggers"]
            )
        )
        self.assertTrue(
            any(
                row["slice"] == "formal_theory_living_upstreams"
                and "FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md" in row["paths"]
                for row in payload["recommended_protocol_slices"]
            )
        )
        self.assertTrue(
            any("proxy-success" in row or "missing execution evidence" in row for row in payload["active_hard_constraints"])
        )
        self.assertTrue(any("return to L0" in row for row in payload["active_hard_constraints"]))
        self.assertTrue(any("physlib" in row or "Lean community discussion" in row for row in payload["active_hard_constraints"]))
        self.assertEqual(
            payload["backend_bridges"][0]["l0_registration_script"],
            "source-layer/scripts/register_local_note_source.py",
        )
        self.assertTrue(
            any(row["surface"] == "research_question_contract" for row in payload["editable_protocol_surfaces"])
        )
        self.assertTrue(any(row["surface"] == "topic_completion" for row in payload["editable_protocol_surfaces"]))
        self.assertTrue(any(row["surface"] == "lean_bridge" for row in payload["editable_protocol_surfaces"]))
        note_text = protocol_note.read_text(encoding="utf-8")
        self.assertIn("## Active research contract", note_text)
        self.assertIn("## Promotion readiness", note_text)
        self.assertIn("## Open gap summary", note_text)
        self.assertIn("## Strategy memory", note_text)
        self.assertIn("## Topic skill projection", note_text)
        self.assertIn("## Topic completion", note_text)
        self.assertIn("## Lean bridge", note_text)
        self.assertIn("## Minimal execution brief", note_text)
        self.assertIn("## Must read now", note_text)
        self.assertIn("## Idea packet", note_text)
        self.assertIn("## Operator checkpoint", note_text)
        self.assertIn("## Escalate only when triggered", note_text)
        self.assertIn("`promotion_intent` status=`active`", note_text)
        self.assertIn("Prefer durable `next_actions.contract.json`", note_text)
        self.assertNotIn("RESEARCH_EXECUTION_GUARDRAILS.md", note_text)
        self.assertIn("backend:formal-theory-note-library", note_text)
        self.assertIn("## L2 promotion gate", note_text)

    def test_record_strategy_memory_writes_jsonl_row(self) -> None:
        self._write_runtime_state()

        payload = self.service.record_strategy_memory(
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
            strategy_type="verification_guardrail",
            summary="Check sign conventions before merging derivation branches.",
            outcome="helpful",
            confidence=0.78,
            input_context={"method_surface": "derivation"},
            evidence_refs=["validation/topics/demo-topic/runs/2026-03-13-demo/result_summary.md"],
            reuse_conditions=["multi-source derivation merge"],
            do_not_apply_when=["single-source closed derivation"],
            human_note="Keep this as a default bounded review step.",
            updated_by="human",
        )

        path = Path(payload["strategy_memory_path"])
        self.assertTrue(path.exists())
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["strategy_type"], "verification_guardrail")
        self.assertEqual(rows[0]["outcome"], "helpful")
        self.assertEqual(rows[0]["lane"], "code_method")
        self.assertIn("multi-source derivation merge", rows[0]["reuse_conditions"])

    def test_topic_status_surfaces_relevant_strategy_memory(self) -> None:
        runtime_root = self._write_runtime_state()
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L3",
                    "last_materialized_stage": "L3",
                    "research_mode": "formal_derivation",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "Continue the derivation review.",
                    "action_queue_surface": {
                        "queue_source": "heuristic",
                    },
                    "decision_surface": {
                        "decision_mode": "continue_unfinished",
                        "decision_source": "heuristic",
                        "decision_contract_status": "missing",
                        "control_note_path": None,
                        "selected_action_id": "action:demo-topic:proof",
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "action_queue.jsonl").write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:proof",
                    "status": "pending",
                    "action_type": "proof_review",
                    "summary": "Check sign conventions before combining the derivation branches.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

        self.service.record_strategy_memory(
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
            strategy_type="verification_guardrail",
            summary="Check sign conventions before combining derivation branches.",
            outcome="helpful",
            confidence=0.81,
            lane="formal_theory",
            reuse_conditions=["combining derivation branches", "sign conventions"],
            updated_by="aitp-cli",
        )

        payload = self.service.topic_status(topic_slug="demo-topic")

        self.assertEqual(payload["strategy_memory"]["status"], "available")
        self.assertGreaterEqual(payload["strategy_memory"]["relevant_count"], 1)
        self.assertTrue(payload["strategy_memory"]["guidance"])
        self.assertTrue(
            any(
                str(row.get("path") or "").endswith("strategy_memory.jsonl")
                for row in payload["must_read_now"]
            )
        )

    def test_project_topic_skill_available_for_code_method_lane(self) -> None:
        runtime_root = self._write_runtime_state(run_id="run-001")
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "run-001",
                    "resume_stage": "L3",
                    "last_materialized_stage": "L3",
                    "research_mode": "exploratory_general",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "Keep the benchmark-first code-method route bounded.",
                    "action_queue_surface": {
                        "queue_source": "heuristic",
                    },
                    "decision_surface": {
                        "decision_mode": "continue_unfinished",
                        "decision_source": "heuristic",
                        "decision_contract_status": "missing",
                        "control_note_path": None,
                        "selected_action_id": "action:demo-topic:code",
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "action_queue.jsonl").write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:code",
                    "status": "pending",
                    "action_type": "benchmark",
                    "summary": "Close the exact benchmark before broader code-method confidence.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

        self.service.scaffold_operation(
            topic_slug="demo-topic",
            run_id="run-001",
            title="TFIM exact-diagonalization benchmark workflow",
            kind="coding",
            summary="Benchmark-first code-backed route.",
        )
        self.service.update_operation(
            topic_slug="demo-topic",
            run_id="run-001",
            operation="TFIM exact-diagonalization benchmark workflow",
            baseline_status="passed",
            artifact_paths=["validation/topics/demo-topic/runs/run-001/results/benchmark.json"],
        )
        self.service.audit_operation_trust(
            topic_slug="demo-topic",
            run_id="run-001",
        )
        self.service.record_strategy_memory(
            topic_slug="demo-topic",
            run_id="run-001",
            strategy_type="verification_guardrail",
            summary="Close the exact benchmark before broader code-method confidence.",
            outcome="helpful",
            lane="code_method",
            confidence=0.82,
            evidence_refs=["validation/topics/demo-topic/runs/run-001/trust_audit.json"],
        )

        payload = self.service.project_topic_skill(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )

        projection = payload["topic_skill_projection"]
        self.assertEqual(projection["status"], "available")
        self.assertEqual(projection["lane"], "code_method")
        self.assertTrue(Path(payload["topic_skill_projection_path"]).exists())
        self.assertTrue(Path(payload["topic_skill_projection_note_path"]).exists())
        self.assertIn("benchmark-first", projection["summary"])
        candidate_rows = [
            json.loads(line)
            for line in (self.kernel_root / "feedback" / "topics" / "demo-topic" / "runs" / "run-001" / "candidate_ledger.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        projection_row = next(row for row in candidate_rows if row["candidate_type"] == "topic_skill_projection")
        self.assertEqual(projection_row["intended_l2_targets"], ["topic_skill_projection:demo-topic"])

        status_payload = self.service.topic_status(topic_slug="demo-topic")
        self.assertEqual(status_payload["topic_skill_projection"]["status"], "available")
        self.assertTrue(
            any(
                str(row.get("path") or "").endswith("topic_skill_projection.active.md")
                for row in status_payload["must_read_now"]
            )
        )

    def test_project_topic_skill_blocks_without_trust_gate(self) -> None:
        runtime_root = self._write_runtime_state(run_id="run-001")
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "run-001",
                    "resume_stage": "L3",
                    "research_mode": "exploratory_general",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.service.scaffold_operation(
            topic_slug="demo-topic",
            run_id="run-001",
            title="TFIM exact-diagonalization benchmark workflow",
            kind="coding",
        )
        self.service.record_strategy_memory(
            topic_slug="demo-topic",
            run_id="run-001",
            strategy_type="verification_guardrail",
            summary="Close the exact benchmark before broader code-method confidence.",
            outcome="helpful",
            lane="code_method",
            confidence=0.8,
        )

        payload = self.service.project_topic_skill(topic_slug="demo-topic")

        self.assertEqual(payload["topic_skill_projection"]["status"], "blocked")
        ledger_path = self.kernel_root / "feedback" / "topics" / "demo-topic" / "runs" / "run-001" / "candidate_ledger.jsonl"
        if ledger_path.exists():
            rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertFalse(any(row.get("candidate_type") == "topic_skill_projection" for row in rows))

    def test_project_topic_skill_available_for_formal_theory_lane(self) -> None:
        runtime_root = self._write_runtime_state(run_id="run-001")
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "run-001",
                    "resume_stage": "L3",
                    "research_mode": "formal_derivation",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self._write_candidate(
            topic_slug="demo-topic",
            run_id="run-001",
            candidate_type="theorem_card",
            intended_l2_target="theorem:demo-formal-target",
            title="Demo Formal Theorem",
        )
        self.service.audit_theory_coverage(
            topic_slug="demo-topic",
            run_id="run-001",
            candidate_id="candidate:demo-candidate",
            source_sections=["sec:intro"],
            covered_sections=["sec:intro"],
            consensus_status="unanimous",
            critical_unit_recall=1.0,
            missing_anchor_count=0,
            skeptic_major_gap_count=0,
            supporting_regression_question_ids=["regression_question:demo-theorem"],
            supporting_oracle_ids=["question_oracle:demo-theorem"],
            supporting_regression_run_ids=["regression_run:demo-theorem"],
            topic_completion_status="promotion-ready",
        )
        self.service.audit_formal_theory(
            topic_slug="demo-topic",
            run_id="run-001",
            candidate_id="candidate:demo-candidate",
            formal_theory_role="trusted_target",
            statement_graph_role="target_statement",
            target_statement_id="theorem:demo-formal-target",
            statement_graph_parents=["definition:demo-parent"],
            statement_graph_children=["proof_fragment:demo-child"],
            informal_statement="A bounded theorem-facing fixture for topic-skill projection gating.",
            formal_target="Demo.FormTheory.demo_target",
            faithfulness_status="reviewed",
            faithfulness_strategy="bounded theorem-facing fixture",
            comparator_audit_status="passed",
            provenance_kind="adapted_existing_formalization",
            attribution_requirements=["Preserve the bounded theorem-facing anchors."],
            provenance_sources=["physlib:demo/formal-target.lean@abc1234"],
            prerequisite_closure_status="closed",
            lean_prerequisite_ids=["physlib:demo-parent"],
            supporting_obligation_ids=["proof_obligation:demo-formal-target"],
        )
        self.service.record_strategy_memory(
            topic_slug="demo-topic",
            run_id="run-001",
            strategy_type="verification_guardrail",
            summary="Read the reviewed theorem-facing packet before reusing the formal-theory route.",
            outcome="helpful",
            lane="formal_theory",
            confidence=0.81,
            evidence_refs=[
                "validation/topics/demo-topic/runs/run-001/theory-packets/candidate-demo-candidate/formal_theory_review.json"
            ],
        )

        payload = self.service.project_topic_skill(topic_slug="demo-topic")

        projection = payload["topic_skill_projection"]
        self.assertEqual(projection["status"], "available")
        self.assertEqual(projection["lane"], "formal_theory")
        self.assertTrue(any("formal_theory_review.json" in row for row in projection["required_first_reads"]))
        candidate_rows = [
            json.loads(line)
            for line in (self.kernel_root / "feedback" / "topics" / "demo-topic" / "runs" / "run-001" / "candidate_ledger.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        projection_row = next(row for row in candidate_rows if row["candidate_type"] == "topic_skill_projection")
        self.assertEqual(projection_row["promotion_mode"], "human")
        self.assertIn("formal-theory route", projection_row["question"])
        self.assertEqual(projection_row["proposed_validation_route"], "human-reviewed formal-theory topic-skill projection promotion")
        status_payload = self.service.topic_status(topic_slug="demo-topic")
        projection_note_row = next(
            row for row in status_payload["must_read_now"] if str(row.get("path") or "").endswith("topic_skill_projection.active.md")
        )
        self.assertIn("formal-theory lane", projection_note_row["reason"])
        self.assertIn("theorem-facing route", projection_note_row["reason"])
        self.assertNotIn("benchmark-first route", projection_note_row["reason"])

    def test_project_topic_skill_blocks_for_formal_theory_without_ready_review(self) -> None:
        runtime_root = self._write_runtime_state(run_id="run-001")
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "run-001",
                    "resume_stage": "L3",
                    "research_mode": "formal_derivation",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self._write_candidate(
            topic_slug="demo-topic",
            run_id="run-001",
            candidate_type="theorem_card",
            intended_l2_target="theorem:demo-formal-target",
            title="Demo Formal Theorem",
        )
        self.service.audit_theory_coverage(
            topic_slug="demo-topic",
            run_id="run-001",
            candidate_id="candidate:demo-candidate",
            source_sections=["sec:intro"],
            covered_sections=["sec:intro"],
            consensus_status="unanimous",
            critical_unit_recall=1.0,
            missing_anchor_count=0,
            skeptic_major_gap_count=0,
            supporting_regression_question_ids=["regression_question:demo-theorem"],
            supporting_oracle_ids=["question_oracle:demo-theorem"],
            supporting_regression_run_ids=["regression_run:demo-theorem"],
            topic_completion_status="promotion-ready",
        )
        self.service.record_strategy_memory(
            topic_slug="demo-topic",
            run_id="run-001",
            strategy_type="verification_guardrail",
            summary="Do not reuse the theorem-facing route until the review ledger is ready.",
            outcome="helpful",
            lane="formal_theory",
            confidence=0.78,
        )

        payload = self.service.project_topic_skill(topic_slug="demo-topic")

        self.assertEqual(payload["topic_skill_projection"]["status"], "blocked")
        self.assertIn("formal_theory_review", payload["topic_skill_projection"]["status_reason"])
        ledger_path = self.kernel_root / "feedback" / "topics" / "demo-topic" / "runs" / "run-001" / "candidate_ledger.jsonl"
        if ledger_path.exists():
            rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertFalse(any(row.get("candidate_type") == "topic_skill_projection" for row in rows))

    def test_ensure_topic_shell_surfaces_writes_contracts_dashboard_and_gap_map(self) -> None:
        runtime_root = self._write_runtime_state()
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L1",
                    "research_mode": "formal_derivation",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "Recover the cited derivation before continuing the proof.",
                    "decision_surface": {
                        "selected_action_id": "action:demo-topic:l0",
                        "decision_source": "heuristic",
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "action_queue.jsonl").write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:l0",
                    "status": "pending",
                    "action_type": "l0_source_expansion",
                    "summary": "Recover the cited source chain and prior-work references.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.ensure_topic_shell_surfaces(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )

        self.assertTrue(Path(payload["research_question_contract_path"]).exists())
        self.assertTrue(Path(payload["validation_contract_path"]).exists())
        self.assertTrue(Path(payload["idea_packet_path"]).exists())
        self.assertTrue(Path(payload["operator_checkpoint_path"]).exists())
        self.assertTrue(Path(payload["operator_checkpoint_note_path"]).exists())
        self.assertTrue(Path(payload["operator_checkpoint_ledger_path"]).exists())
        self.assertTrue(Path(payload["topic_dashboard_path"]).exists())
        self.assertTrue(Path(payload["promotion_readiness_path"]).exists())
        self.assertTrue(Path(payload["gap_map_path"]).exists())
        self.assertTrue(Path(payload["topic_completion_path"]).exists())
        self.assertTrue(Path(payload["lean_bridge_path"]).exists())
        self.assertEqual(payload["research_question_contract"]["research_mode"], "formal_derivation")
        self.assertEqual(payload["validation_contract"]["validation_mode"], "formal")
        self.assertEqual(payload["idea_packet"]["status"], "approved_for_execution")
        self.assertEqual(payload["operator_checkpoint"]["status"], "cancelled")
        self.assertIn("topic_state_explainability", payload)
        self.assertEqual(payload["validation_contract"]["status"], "deferred")
        self.assertTrue(payload["open_gap_summary"]["requires_l0_return"])
        dashboard_text = Path(payload["topic_dashboard_path"]).read_text(encoding="utf-8")
        gap_text = Path(payload["gap_map_path"]).read_text(encoding="utf-8")
        self.assertIn("Idea packet", dashboard_text)
        self.assertIn("operator_checkpoint.active.md", dashboard_text)
        self.assertIn("## Last evidence return", dashboard_text)
        self.assertIn("## Active human need", dashboard_text)
        self.assertIn("return to L0", dashboard_text)
        self.assertIn("return to L0", gap_text)

    def test_ensure_topic_shell_surfaces_materializes_idea_packet_for_vague_topic(self) -> None:
        runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "Topological phases from modular data",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.ensure_topic_shell_surfaces(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )

        idea_packet_path = Path(payload["idea_packet_path"])
        idea_packet_note_path = Path(payload["idea_packet_note_path"])
        operator_checkpoint_path = Path(payload["operator_checkpoint_path"])
        operator_checkpoint_note_path = Path(payload["operator_checkpoint_note_path"])
        self.assertTrue(idea_packet_path.exists())
        self.assertTrue(idea_packet_note_path.exists())
        self.assertTrue(operator_checkpoint_path.exists())
        self.assertTrue(operator_checkpoint_note_path.exists())
        idea_packet = json.loads(idea_packet_path.read_text(encoding="utf-8"))
        operator_checkpoint = json.loads(operator_checkpoint_path.read_text(encoding="utf-8"))
        self.assertEqual(idea_packet["status"], "needs_clarification")
        self.assertEqual(operator_checkpoint["status"], "requested")
        self.assertEqual(operator_checkpoint["checkpoint_kind"], "scope_ambiguity")
        self.assertIn("novelty_target", idea_packet["missing_fields"])
        self.assertTrue(idea_packet["clarification_questions"])
        dashboard_text = Path(payload["topic_dashboard_path"]).read_text(encoding="utf-8")
        self.assertIn("needs_clarification", dashboard_text)
        self.assertIn("Idea packet summary", dashboard_text)
        self.assertIn("scope_ambiguity", dashboard_text)

    def test_ensure_topic_shell_surfaces_writes_result_brief(self) -> None:
        self._write_runtime_state()

        payload = self.service.ensure_topic_shell_surfaces(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )

        result_brief_path = Path(payload["result_brief_path"])
        result_brief_note_path = Path(payload["result_brief_note_path"])
        self.assertTrue(result_brief_path.exists())
        self.assertTrue(result_brief_note_path.exists())
        result_brief_payload = json.loads(result_brief_path.read_text(encoding="utf-8"))
        schema = json.loads(
            (
                self.kernel_root
                / "runtime"
                / "schemas"
                / "result-brief.schema.json"
            ).read_text(encoding="utf-8")
        )
        Draft202012Validator(schema).validate(result_brief_payload)
        result_brief_note = result_brief_note_path.read_text(encoding="utf-8")
        self.assertIn("## What Changed", result_brief_note)
        self.assertIn("## Evidence", result_brief_note)
        self.assertIn("## Scope", result_brief_note)
        self.assertIn("## What This Does Not Yet Justify", result_brief_note)

    def test_ensure_topic_shell_surfaces_result_brief_blocks_on_pending_decisions(self) -> None:
        self._write_runtime_state()

        with patch(
            "knowledge_hub.aitp_service.list_pending_decision_points",
            return_value=[{"id": "decision:demo-blocking", "blocking": True}],
        ):
            payload = self.service.ensure_topic_shell_surfaces(
                topic_slug="demo-topic",
                updated_by="aitp-cli",
            )

        result_brief_payload = json.loads(
            Path(payload["result_brief_path"]).read_text(encoding="utf-8")
        )
        self.assertEqual(result_brief_payload["interaction_class"], "checkpoint_question")
        self.assertIn("decision:demo-blocking", result_brief_payload["what_changed"])

    def test_topic_status_and_prepare_verification_surface_new_shell_fields(self) -> None:
        runtime_root = self._write_runtime_state()
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "Check the proof obligations for the active topic.",
                    "decision_surface": {
                        "selected_action_id": "action:demo-topic:proof",
                        "decision_source": "heuristic",
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "action_queue.jsonl").write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:proof",
                    "status": "pending",
                    "action_type": "manual_followup",
                    "summary": "Complete the next proof fragment review.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

        status_payload = self.service.topic_status(topic_slug="demo-topic")
        self.assertEqual(status_payload["topic_slug"], "demo-topic")
        self.assertIn("topic_state", status_payload)
        self.assertIn("topic_state_explainability", status_payload)
        self.assertIn("active_research_contract", status_payload)
        self.assertIn("idea_packet", status_payload)
        self.assertIn("operator_checkpoint", status_payload)
        self.assertIn("topic_completion", status_payload)
        self.assertIn("lean_bridge", status_payload)
        self.assertTrue(
            any(row["path"].endswith("research_question.contract.md") for row in status_payload["must_read_now"])
        )

        verification_payload = self.service.prepare_verification(
            topic_slug="demo-topic",
            mode="proof",
        )
        self.assertEqual(verification_payload["verification_mode"], "proof")
        self.assertEqual(verification_payload["validation_contract"]["validation_mode"], "formal")
        self.assertIn("proof or derivation step", verification_payload["validation_contract"]["verification_focus"])
        self.assertTrue(Path(verification_payload["runtime_protocol"]["runtime_protocol_path"]).exists())

    def test_runtime_bundle_and_session_start_require_idea_packet_when_clarification_needed(self) -> None:
        runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "Topological phases from modular data",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        protocol_paths = self.service._materialize_runtime_protocol_bundle(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
            human_request="Topological phases from modular data",
        )
        bundle = json.loads(Path(protocol_paths["runtime_protocol_path"]).read_text(encoding="utf-8"))
        self.assertEqual(bundle["idea_packet"]["status"], "needs_clarification")
        self.assertEqual(bundle["operator_checkpoint"]["status"], "requested")
        self.assertEqual(bundle["operator_checkpoint"]["checkpoint_kind"], "scope_ambiguity")
        self.assertTrue(any(row["path"].endswith("idea_packet.md") for row in bundle["must_read_now"]))
        self.assertTrue(any(row["path"].endswith("operator_checkpoint.active.md") for row in bundle["must_read_now"]))
        self.assertTrue(any("idea_packet.md" in row for row in bundle["active_hard_constraints"]))
        self.assertTrue(any("operator_checkpoint.active.md" in row for row in bundle["active_hard_constraints"]))

        session_payload = self.service._materialize_session_start_contract(
            task="Topological phases from modular data",
            routing={
                "route": "request_new_topic",
                "reason": "No durable current topic matched the request.",
                "topic_slug": "demo-topic",
                "topic": "Demo Topic",
            },
            loop_payload={
                "topic_slug": "demo-topic",
                "runtime_protocol": protocol_paths,
                "loop_state": {
                    "entry_conformance": "pass",
                    "exit_conformance": "pass",
                    "capability_status": "ready",
                    "trust_status": "pass",
                },
                "steering_artifacts": {},
                "bootstrap": {"topic_state": {"pointers": {}}},
                "current_topic_memory": {},
            },
            updated_by="aitp-session-start",
        )
        self.assertTrue(any(row["path"].endswith("idea_packet.md") for row in session_payload["must_read_now"]))
        self.assertTrue(any(row["path"].endswith("operator_checkpoint.active.md") for row in session_payload["must_read_now"]))
        self.assertTrue(any("idea_packet.md" in row for row in session_payload["hard_stops"]))
        self.assertTrue(any("operator_checkpoint.active.md" in row for row in session_payload["hard_stops"]))

    def test_session_start_blocks_on_pending_decision_blockers(self) -> None:
        runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "Continue the bounded topic lane.",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        with patch(
            "knowledge_hub.aitp_service.list_pending_decision_points",
            return_value=[
                {"id": "decision:demo-blocking", "blocking": True}
            ],
        ):
            protocol_paths = self.service._materialize_runtime_protocol_bundle(
                topic_slug="demo-topic",
                updated_by="aitp-cli",
                human_request="Continue the bounded topic lane.",
            )

        session_payload = self.service._materialize_session_start_contract(
            task="Continue the bounded topic lane.",
            routing={
                "route": "request_current_topic_reference",
                "reason": "User referenced the current topic.",
                "topic_slug": "demo-topic",
                "topic": "Demo Topic",
            },
            loop_payload={
                "topic_slug": "demo-topic",
                "runtime_protocol": protocol_paths,
                "loop_state": {
                    "entry_conformance": "pass",
                    "exit_conformance": "pass",
                    "capability_status": "ready",
                    "trust_status": "pass",
                },
                "steering_artifacts": {},
                "bootstrap": {"topic_state": {"pointers": {}}},
                "current_topic_memory": {},
            },
            updated_by="aitp-session-start",
        )
        self.assertTrue(any("pending_decisions" in row["path"] for row in session_payload["must_read_now"]))
        self.assertTrue(any("blocking pending decisions" in row for row in session_payload["hard_stops"]))
        self.assertTrue(
            any(
                "blocking pending decision" in row.get("step", "")
                for row in session_payload["linear_flow"]
            )
        )

    def test_answer_operator_checkpoint_updates_ledger_and_operator_console(self) -> None:
        runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "Topological phases from modular data",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "operator_console.md").write_text("# Console\n", encoding="utf-8")

        payload = self.service.ensure_topic_shell_surfaces(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )
        self.assertEqual(payload["operator_checkpoint"]["status"], "requested")

        answered = self.service.answer_operator_checkpoint(
            topic_slug="demo-topic",
            answer="First constrain novelty target to modular-invariant diagnostics and keep numerics out of scope.",
            updated_by="human",
        )

        self.assertEqual(answered["operator_checkpoint"]["status"], "answered")
        self.assertFalse(answered["operator_checkpoint"]["active"])
        self.assertIn("modular-invariant diagnostics", answered["operator_checkpoint"]["answer"])
        self.assertEqual(answered["topic_state_explainability"]["active_human_need"]["status"], "none")
        ledger_rows = [
            json.loads(line)
            for line in Path(payload["operator_checkpoint_ledger_path"]).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(ledger_rows[-2]["status"], "requested")
        self.assertEqual(ledger_rows[-1]["status"], "answered")
        console_text = (runtime_root / "operator_console.md").read_text(encoding="utf-8")
        self.assertIn("## Active operator checkpoint", console_text)
        self.assertIn("`answered`", console_text)

    def test_answer_operator_checkpoint_materializes_redirect_steering(self) -> None:
        runtime_root = self._write_runtime_state()
        feedback_root = self.kernel_root / "feedback" / "topics" / "demo-topic" / "runs" / "2026-03-13-demo"
        feedback_root.mkdir(parents=True, exist_ok=True)
        next_actions_path = feedback_root / "next_actions.md"
        next_actions_path.write_text("1. Continue the current bounded lane.\n", encoding="utf-8")
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L3",
                    "pointers": {
                        "next_actions_path": "feedback/topics/demo-topic/runs/2026-03-13-demo/next_actions.md",
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "Need an explicit stop/continue decision for the active topic.",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "action_queue.jsonl").write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:steer",
                    "status": "pending",
                    "action_type": "manual_followup",
                    "summary": "AITP needs a continue or branch decision before the bounded loop can proceed.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "operator_console.md").write_text("# Console\n", encoding="utf-8")

        service = _SteeringLoopStubService(kernel_root=self.kernel_root, repo_root=self.repo_root)
        payload = service.ensure_topic_shell_surfaces(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )
        self.assertEqual(payload["operator_checkpoint"]["status"], "requested")
        self.assertEqual(
            payload["operator_checkpoint"]["checkpoint_kind"],
            "stop_continue_branch_redirect_decision",
        )

        answered = service.answer_operator_checkpoint(
            topic_slug="demo-topic",
            answer="Redirect the active topic toward low-energy effective theory.",
            updated_by="human",
        )

        innovation_direction_path = runtime_root / "innovation_direction.md"
        innovation_decisions_path = runtime_root / "innovation_decisions.jsonl"
        control_note_path = runtime_root / "control_note.md"
        next_actions_contract_path = feedback_root / "next_actions.contract.json"

        self.assertTrue(answered["steering_artifacts"]["materialized"])
        self.assertEqual(answered["steering_artifacts"]["decision"], "redirect")
        self.assertTrue(innovation_direction_path.exists())
        self.assertTrue(innovation_decisions_path.exists())
        self.assertTrue(control_note_path.exists())
        self.assertTrue(next_actions_contract_path.exists())
        self.assertIn("low-energy effective theory", innovation_direction_path.read_text(encoding="utf-8"))
        self.assertIn("directive: human_redirect", control_note_path.read_text(encoding="utf-8"))
        contract_payload = json.loads(next_actions_contract_path.read_text(encoding="utf-8"))
        self.assertEqual(contract_payload["actions"][0]["action_id"], "action:demo-topic:steering:operator-redirect")
        self.assertEqual(len(service.orchestrate_calls), 1)
        self.assertTrue(
            str(service.orchestrate_calls[0].get("control_note") or "").endswith("runtime/topics/demo-topic/control_note.md")
        )
        self.assertEqual(answered["topic_state_explainability"]["active_human_need"]["status"], "none")

    def test_pending_human_promotion_gate_creates_operator_checkpoint(self) -> None:
        runtime_root = self._write_runtime_state()
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "Establish a bounded validation route and then review promotion readiness for the current topic.",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self._write_candidate()
        self.service.request_promotion(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            backend_id="backend:theoretical-physics-knowledge-network",
        )

        payload = self.service.ensure_topic_shell_surfaces(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )

        self.assertEqual(payload["operator_checkpoint"]["status"], "requested")
        self.assertEqual(payload["operator_checkpoint"]["checkpoint_kind"], "promotion_approval")
        checkpoint_note = Path(payload["operator_checkpoint_note_path"]).read_text(encoding="utf-8")
        self.assertIn("candidate:demo-candidate", checkpoint_note)
        self.assertIn("backend:theoretical-physics-knowledge-network", checkpoint_note)

    def test_operation_trust_registry_blocks_until_gate_is_satisfied(self) -> None:
        self._write_runtime_state()
        payload = self.service.scaffold_operation(
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
            title="Small-system validation backend",
            kind="numerical",
        )
        manifest = Path(payload["manifest_path"])
        summary = Path(payload["summary_path"])
        self.assertTrue(manifest.exists())
        self.assertTrue(summary.exists())

        blocked = self.service.audit_operation_trust(
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
        )
        self.assertEqual(blocked["overall_status"], "blocked")

        self.service.update_operation(
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
            operation="Small-system validation backend",
            baseline_status="passed",
            artifact_paths=["validation/topics/demo-topic/runs/2026-03-13-demo/results/benchmark.json"],
        )
        passed = self.service.audit_operation_trust(
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
        )
        self.assertEqual(passed["overall_status"], "pass")
        self.assertEqual(passed["operations"][0]["trust_ready"], True)

    def test_capability_audit_writes_registry(self) -> None:
        self._write_runtime_state()
        self.service.ensure_topic_shell_surfaces(topic_slug="demo-topic", updated_by="aitp-cli")
        self.service.scaffold_operation(
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
            title="Finite-size validation baseline",
            kind="numerical",
        )
        self.service.update_operation(
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
            operation="Finite-size validation baseline",
            baseline_status="passed",
        )
        self.service.audit_operation_trust(
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
        )

        payload = self.service.capability_audit(topic_slug="demo-topic")
        registry = Path(payload["capability_registry_path"])
        report = Path(payload["capability_report_path"])
        self.assertTrue(registry.exists())
        self.assertTrue(report.exists())
        self.assertEqual(payload["overall_status"], "ready")
        self.assertEqual(payload["sections"]["layers"]["L2"]["status"], "present")
        self.assertEqual(payload["sections"]["capabilities"]["operation_trust"]["status"], "present")
        self.assertEqual(payload["sections"]["runtime"]["idea_packet.json"]["status"], "present")
        self.assertEqual(payload["sections"]["runtime"]["operator_checkpoint.active.json"]["status"], "present")
        self.assertEqual(payload["sections"]["runtime"]["operator_checkpoints.jsonl"]["status"], "present")

    def test_status_explainability_uses_returned_execution_result(self) -> None:
        runtime_root = self._write_runtime_state()
        returned_result_path = (
            self.kernel_root
            / "validation"
            / "topics"
            / "demo-topic"
            / "runs"
            / "2026-03-13-demo"
            / "returned_execution_result.json"
        )
        returned_result_path.parent.mkdir(parents=True, exist_ok=True)
        returned_result_path.write_text(
            json.dumps(
                {
                    "result_id": "result:demo",
                    "status": "partial",
                    "summary": "Recovered the missing cited definition but left one bounded open gap.",
                    "updated_at": "2026-03-27T00:00:00+08:00",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L3",
                    "pointers": {
                        "returned_execution_result_path": "validation/topics/demo-topic/runs/2026-03-13-demo/returned_execution_result.json",
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "Continue the bounded derivation after inspecting the returned result.",
                    "decision_surface": {
                        "selected_action_id": "action:demo-topic:proof",
                        "decision_source": "heuristic",
                        "next_action_decision_note_path": "runtime/topics/demo-topic/next_action_decision.md",
                    },
                    "action_queue_surface": {
                        "queue_source": "heuristic",
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "action_queue.jsonl").write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:proof",
                    "status": "pending",
                    "action_type": "proof_review",
                    "summary": "Inspect the returned result and continue the bounded proof review.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "operator_console.md").write_text("# Console\n", encoding="utf-8")

        payload = self.service.ensure_topic_shell_surfaces(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )

        explainability = payload["topic_state_explainability"]
        self.assertEqual(explainability["last_evidence_return"]["kind"], "returned_execution_result")
        self.assertEqual(explainability["last_evidence_return"]["record_id"], "result:demo")
        self.assertIn("Recovered the missing cited definition", explainability["last_evidence_return"]["summary"])
        self.assertEqual(explainability["next_bounded_action"]["action_type"], "proof_review")
        topic_state = json.loads((runtime_root / "topic_state.json").read_text(encoding="utf-8"))
        self.assertEqual(
            topic_state["status_explainability"]["last_evidence_return"]["kind"],
            "returned_execution_result",
        )
        dashboard_text = Path(payload["topic_dashboard_path"]).read_text(encoding="utf-8")
        self.assertIn("## Why this topic is here", dashboard_text)
        self.assertIn("## Last evidence return", dashboard_text)
        self.assertIn("result:demo", dashboard_text)
        console_text = (runtime_root / "operator_console.md").read_text(encoding="utf-8")
        self.assertIn("## Topic explainability", console_text)
        self.assertIn("Recovered the missing cited definition", console_text)

    def test_doctor_reports_layer_roots_and_protocol_contracts(self) -> None:
        for filename in (
            "LAYER_MAP.md",
            "ROUTING_POLICY.md",
            "COMMUNICATION_CONTRACT.md",
            "AUTONOMY_AND_OPERATOR_MODEL.md",
            "L2_CONSULTATION_PROTOCOL.md",
            "RESEARCH_EXECUTION_GUARDRAILS.md",
            "PROOF_OBLIGATION_PROTOCOL.md",
            "GAP_RECOVERY_PROTOCOL.md",
            "FAMILY_FUSION_PROTOCOL.md",
            "VERIFICATION_BRIDGE_PROTOCOL.md",
            "FORMAL_THEORY_AUTOMATION_WORKFLOW.md",
            "SECTION_FORMALIZATION_PROTOCOL.md",
            "FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md",
            "INDEXING_RULES.md",
            "L0_SOURCE_LAYER.md",
        ):
            (self.kernel_root / filename).write_text("# present\n", encoding="utf-8")

        payload = self.service.ensure_cli_installed()

        self.assertEqual(payload["layer_roots"]["L2"]["status"], "present")
        self.assertEqual(payload["protocol_contracts"]["layer_map"]["status"], "present")
        self.assertEqual(payload["protocol_contracts"]["research_execution_guardrails"]["status"], "present")
        self.assertEqual(payload["protocol_contracts"]["proof_obligation_protocol"]["status"], "present")
        self.assertEqual(payload["protocol_contracts"]["gap_recovery_protocol"]["status"], "present")
        self.assertEqual(payload["protocol_contracts"]["family_fusion_protocol"]["status"], "present")
        self.assertEqual(payload["protocol_contracts"]["verification_bridge_protocol"]["status"], "present")
        self.assertEqual(payload["protocol_contracts"]["formal_theory_automation_workflow"]["status"], "present")
        self.assertEqual(payload["protocol_contracts"]["section_formalization_protocol"]["status"], "present")
        self.assertEqual(
            payload["protocol_contracts"]["formal_theory_upstream_reference_protocol"]["status"],
            "present",
        )

    def test_doctor_detects_mixed_install_signals(self) -> None:
        workspace_root = self.root / "Theoretical-Physics"
        workspace_root.mkdir(parents=True, exist_ok=True)
        (workspace_root / "AITP_COMMAND_HARNESS.md").write_text("legacy\n", encoding="utf-8")
        codex_using = Path.home() / ".agents" / "skills" / "using-aitp"
        codex_runtime = Path.home() / ".agents" / "skills" / "aitp-runtime"
        codex_using.mkdir(parents=True, exist_ok=True)
        codex_runtime.mkdir(parents=True, exist_ok=True)
        (codex_using / "SKILL.md").write_text(
            (self.package_root.parent.parent / "skills" / "using-aitp" / "SKILL.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (codex_runtime / "SKILL.md").write_text(
            (self.package_root.parent.parent / "skills" / "aitp-runtime" / "SKILL.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        with patch.object(self.service, "_pip_show_package", return_value={"version": "0.3.1", "editable project location": str(self.root / "old-workspace" / "research" / "knowledge-hub")}):
            with patch("knowledge_hub.aitp_service.shutil.which", side_effect=lambda name: "C:\\temp\\aitp.exe" if name == "aitp" else ""):
                payload = self.service.ensure_cli_installed(workspace_root=str(workspace_root))

        self.assertEqual(payload["overall_status"], "mixed_install")
        self.assertIn("stale_cli", payload["issues"])
        self.assertIn("legacy_workspace_entrypoints_present", payload["issues"])

    def test_migrate_local_install_moves_workspace_legacy_and_records_pip_actions(self) -> None:
        workspace_root = self.root / "Theoretical-Physics"
        workspace_root.mkdir(parents=True, exist_ok=True)
        for name in ("AITP_COMMAND_HARNESS.md", "aitp.md", "aitp-loop.md"):
            (workspace_root / name).write_text("legacy\n", encoding="utf-8")

        install_calls: list[tuple[str, bool]] = []

        def fake_install_agent(*, agent: str, scope: str = "user", target_root: str | None = None, force: bool = True, install_mcp: bool = True):
            install_calls.append((agent, install_mcp))
            return {"installed": [{"agent": agent, "path": f"/tmp/{agent}", "kind": "skill"}]}

        def fake_run(argv, check=False, capture_output=True, text=True):  # noqa: ANN001
            class Result:
                def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr

            if argv[:4] == [__import__("sys").executable, "-m", "pip", "show"]:
                return Result(
                    0,
                    "Name: aitp-kernel\nVersion: 0.3.1\nEditable project location: D:\\old-workspace\\research\\knowledge-hub\n",
                )
            if argv[:4] == [__import__("sys").executable, "-m", "pip", "uninstall"]:
                return Result(0, "uninstalled", "")
            if argv[:4] == [__import__("sys").executable, "-m", "pip", "install"]:
                return Result(0, "installed", "")
            return Result(0, "", "")

        with patch("knowledge_hub.aitp_service.subprocess.run", side_effect=fake_run):
            with patch.object(self.service, "_claude_legacy_command_paths", return_value=[]):
                with patch.object(self.service, "install_agent", side_effect=fake_install_agent):
                    with patch.object(self.service, "_ensure_opencode_plugin_enabled", return_value={"config_path": "C:\\temp\\opencode.json", "plugin_entry": "aitp@git+https://github.com/bhjia-phys/AITP-Research-Protocol.git"}):
                        result = self.service.migrate_local_install(
                            workspace_root=str(workspace_root),
                            agents=["codex", "claude-code", "opencode"],
                            with_mcp=False,
                        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["backup_log"]), 3)
        self.assertTrue((Path(result["backup_root"]) / "workspace-root-legacy" / "AITP_COMMAND_HARNESS.md").exists())
        self.assertFalse((workspace_root / "AITP_COMMAND_HARNESS.md").exists())
        self.assertIn(("codex", False), install_calls)
        self.assertIn(("claude-code", False), install_calls)
        self.assertIn(("opencode", False), install_calls)

    def test_run_topic_loop_writes_loop_state_and_executes_auto_actions(self) -> None:
        service = _LoopStubService(kernel_root=self.kernel_root, repo_root=self.repo_root)
        payload = service.run_topic_loop(
            topic_slug="demo-topic",
            human_request="find capability gaps",
            max_auto_steps=2,
        )

        loop_state_path = Path(payload["loop_state_path"])
        self.assertTrue(loop_state_path.exists())
        loop_state = json.loads(loop_state_path.read_text(encoding="utf-8"))
        self.assertEqual(loop_state["exit_conformance"], "pass")
        self.assertEqual(payload["auto_actions"]["executed"][0]["status"], "completed")
        self.assertTrue(Path(payload["runtime_protocol"]["runtime_protocol_path"]).exists())
        self.assertTrue(Path(payload["runtime_protocol"]["runtime_protocol_note_path"]).exists())

    def test_latest_topic_slug_uses_runtime_topic_index(self) -> None:
        topic_index_path = self.kernel_root / "runtime" / "topic_index.jsonl"
        topic_index_path.parent.mkdir(parents=True, exist_ok=True)
        topic_index_path.write_text(
            json.dumps(
                {
                    "topic_slug": "older-topic",
                    "updated_at": "2026-03-26T09:00:00+08:00",
                },
                ensure_ascii=True,
            )
            + "\n"
            + json.dumps(
                {
                    "topic_slug": "newer-topic",
                    "updated_at": "2026-03-26T10:00:00+08:00",
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )

        self.assertEqual(self.service.latest_topic_slug(), "newer-topic")

    def test_current_topic_slug_prefers_current_memory_before_latest(self) -> None:
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        topic_index_path = runtime_root / "topic_index.jsonl"
        topic_index_path.write_text(
            json.dumps(
                {
                    "topic_slug": "latest-topic",
                    "updated_at": "2026-03-26T10:00:00+08:00",
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        remembered_topic = "current-topic"
        remembered_runtime_root = self.kernel_root / "runtime" / "topics" / remembered_topic
        remembered_runtime_root.mkdir(parents=True, exist_ok=True)
        (remembered_runtime_root / "topic_state.json").write_text(
            json.dumps({"topic_slug": remembered_topic}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (runtime_root / "current_topic.json").write_text(
            json.dumps(
                {
                    "topic_slug": remembered_topic,
                    "updated_at": "2026-03-26T11:00:00+08:00",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        self.assertEqual(self.service.current_topic_slug(), remembered_topic)

    def test_route_codex_chat_request_detects_new_topic_from_natural_language(self) -> None:
        routing = self.service.route_codex_chat_request(
            task="帮我开一个新 topic：Topological phases from modular data，先做问题定义",
        )

        self.assertEqual(routing["route"], "request_new_topic")
        self.assertEqual(routing["topic"], "Topological phases from modular data")
        self.assertIsNone(routing["topic_slug"])

    def test_route_codex_chat_request_prefers_current_topic_reference(self) -> None:
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        remembered_topic = "demo-topic"
        remembered_runtime_root = self.kernel_root / "runtime" / "topics" / remembered_topic
        remembered_runtime_root.mkdir(parents=True, exist_ok=True)
        (remembered_runtime_root / "topic_state.json").write_text(
            json.dumps({"topic_slug": remembered_topic}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (runtime_root / "current_topic.json").write_text(
            json.dumps({"topic_slug": remembered_topic}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

        routing = self.service.route_codex_chat_request(
            task="继续这个 topic，方向改成 low-energy effective theory",
        )

        self.assertEqual(routing["route"], "request_current_topic_reference")
        self.assertEqual(routing["topic_slug"], remembered_topic)

    def test_route_codex_chat_request_matches_named_existing_slug(self) -> None:
        topic_index_path = self.kernel_root / "runtime" / "topic_index.jsonl"
        topic_index_path.parent.mkdir(parents=True, exist_ok=True)
        topic_index_path.write_text(
            json.dumps(
                {
                    "topic_slug": "topological-phases-from-modular-data",
                    "updated_at": "2026-03-26T10:00:00+08:00",
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )

        routing = self.service.route_codex_chat_request(
            task="继续 topological-phases-from-modular-data 这个 topic，先补验证",
        )

        self.assertEqual(routing["route"], "request_named_existing_topic")
        self.assertEqual(routing["topic_slug"], "topological-phases-from-modular-data")

    def test_start_chat_session_materializes_current_topic_route(self) -> None:
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        remembered_topic = "demo-topic"
        remembered_runtime_root = self.kernel_root / "runtime" / "topics" / remembered_topic
        remembered_runtime_root.mkdir(parents=True, exist_ok=True)
        (remembered_runtime_root / "topic_state.json").write_text(
            json.dumps({"topic_slug": remembered_topic}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (runtime_root / "current_topic.json").write_text(
            json.dumps({"topic_slug": remembered_topic}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

        service = _SteeringLoopStubService(kernel_root=self.kernel_root, repo_root=self.repo_root)
        payload = service.start_chat_session(
            task="继续这个 topic，方向改成 low-energy effective theory",
        )

        self.assertEqual(payload["routing"]["route"], "request_current_topic_reference")
        self.assertEqual(payload["topic_slug"], remembered_topic)
        self.assertTrue(Path(payload["loop_state_path"]).exists())
        self.assertTrue(Path(payload["current_topic_memory_path"]).exists())
        self.assertTrue(Path(payload["session_start_contract_path"]).exists())
        self.assertTrue(Path(payload["session_start_note_path"]).exists())
        session_contract = json.loads(Path(payload["session_start_contract_path"]).read_text(encoding="utf-8"))
        self.assertEqual(session_contract["routing"]["route"], "request_current_topic_reference")
        self.assertTrue(session_contract["memory_resolution"]["used_current_topic_memory"])
        self.assertIn("runtime_protocol.generated.md", Path(payload["session_start_note_path"]).read_text(encoding="utf-8"))

    def test_run_topic_loop_tail_syncs_after_budget_exhaustion(self) -> None:
        service = _TailSyncLoopStubService(kernel_root=self.kernel_root, repo_root=self.repo_root)
        payload = service.run_topic_loop(
            topic_slug="demo-topic",
            human_request="finish the last auto step and resync runtime state",
            max_auto_steps=1,
        )

        self.assertEqual(service.orchestrate_calls, 2)
        self.assertEqual(payload["auto_actions"]["remaining_pending"], 1)
        bundle = json.loads(Path(payload["runtime_protocol"]["runtime_protocol_path"]).read_text(encoding="utf-8"))
        self.assertEqual(bundle["minimal_execution_brief"]["selected_action_id"], "action:demo-topic:02")

    def test_run_topic_loop_materializes_steering_artifacts_from_human_request(self) -> None:
        service = _SteeringLoopStubService(kernel_root=self.kernel_root, repo_root=self.repo_root)
        payload = service.run_topic_loop(
            topic_slug="demo-topic",
            human_request="继续这个 topic，方向改成 low-energy effective theory",
            max_auto_steps=0,
        )

        runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        innovation_direction_path = runtime_root / "innovation_direction.md"
        innovation_decisions_path = runtime_root / "innovation_decisions.jsonl"
        control_note_path = runtime_root / "control_note.md"
        next_actions_contract_path = (
            self.kernel_root
            / "feedback"
            / "topics"
            / "demo-topic"
            / "runs"
            / "2026-03-13-demo"
            / "next_actions.contract.json"
        )

        self.assertEqual(payload["steering_artifacts"]["decision"], "redirect")
        self.assertTrue(innovation_direction_path.exists())
        self.assertTrue(innovation_decisions_path.exists())
        self.assertTrue(control_note_path.exists())
        self.assertTrue(next_actions_contract_path.exists())
        innovation_note = innovation_direction_path.read_text(encoding="utf-8")
        self.assertIn("low-energy effective theory", innovation_note)
        self.assertIn("Redirect the active topic `Demo Topic` toward `low-energy effective theory`", innovation_note)
        self.assertIn("Required deliverables: Update `runtime/topics/demo-topic/research_question.contract.md`", innovation_note)
        self.assertIn("Do not treat renamed headings, unchanged old contracts, or narrative confidence", innovation_note)
        self.assertIn("directive: human_redirect", control_note_path.read_text(encoding="utf-8"))
        self.assertTrue((self.kernel_root / "runtime" / "current_topic.json").exists())
        current_topic_payload = json.loads((self.kernel_root / "runtime" / "current_topic.json").read_text(encoding="utf-8"))
        self.assertEqual(current_topic_payload["topic_slug"], "demo-topic")
        contract_payload = json.loads(next_actions_contract_path.read_text(encoding="utf-8"))
        self.assertEqual(contract_payload["actions"][0]["action_id"], "action:demo-topic:steering:operator-redirect")
        self.assertIn("low-energy effective theory", contract_payload["actions"][0]["summary"])
        self.assertEqual(len(service.orchestrate_calls), 2)
        self.assertTrue(
            str(service.orchestrate_calls[1].get("control_note") or "").endswith("runtime/topics/demo-topic/control_note.md")
        )

    def test_materialize_steering_preserves_manual_innovation_direction_text(self) -> None:
        runtime_root = self._write_runtime_state()
        innovation_direction_path = runtime_root / "innovation_direction.md"
        innovation_direction_path.write_text(
            textwrap.dedent(
                """\
                # Innovation direction

                topic_slug: `demo-topic`
                updated_by: `human`
                updated_at: `2026-03-27T00:00:00+08:00`
                run_id: `(none)`

                ## Manual note

                - Keep the modular tensor category framing explicit.
                """
            ),
            encoding="utf-8",
        )

        payload = self.service.materialize_steering_from_human_request(
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
            human_request="继续这个 topic，方向改成 modular bootstrap constraints",
            updated_by="aitp-session-start",
        )

        self.assertTrue(payload["materialized"])
        updated_text = innovation_direction_path.read_text(encoding="utf-8")
        self.assertIn("## Manual note", updated_text)
        self.assertIn("Keep the modular tensor category framing explicit.", updated_text)
        self.assertIn("Auto-filled from the latest steering request", updated_text)
        self.assertIn("modular bootstrap constraints", updated_text)

    def test_build_codex_prompt_includes_innovation_surfaces(self) -> None:
        payload = {
            "topic_slug": "demo-topic",
            "run_id": "2026-03-13-demo",
            "loop_state_path": "runtime/topics/demo-topic/loop_state.json",
            "loop_state": {
                "human_request": "continue the topic",
                "exit_conformance": "pass",
                "capability_status": "ready",
                "trust_status": "pass",
            },
            "bootstrap": {
                "runtime_root": "runtime/topics/demo-topic",
                "files": {
                    "agent_brief": "runtime/topics/demo-topic/agent_brief.md",
                    "operator_console": "runtime/topics/demo-topic/operator_console.md",
                    "conformance_report": "runtime/topics/demo-topic/conformance_report.md",
                },
                "topic_state": {
                    "pointers": {
                        "control_note_path": "runtime/topics/demo-topic/control_note.md",
                        "innovation_direction_path": "runtime/topics/demo-topic/innovation_direction.md",
                        "innovation_decisions_path": "runtime/topics/demo-topic/innovation_decisions.jsonl",
                    }
                },
            },
            "capability_audit": {
                "capability_report_path": "runtime/topics/demo-topic/capability_report.md",
            },
            "trust_audit": {
                "trust_report_path": "validation/topics/demo-topic/runs/2026-03-13-demo/trust_audit.md",
            },
            "runtime_protocol": {
                "runtime_protocol_note_path": "runtime/topics/demo-topic/runtime_protocol.generated.md",
            },
            "session_start": {
                "session_start_contract_path": "runtime/topics/demo-topic/session_start.contract.json",
                "session_start_note_path": "runtime/topics/demo-topic/session_start.generated.md",
                "artifacts": {
                    "runtime_protocol_note_path": "runtime/topics/demo-topic/runtime_protocol.generated.md",
                },
            },
        }

        prompt = build_codex_prompt(payload)

        self.assertIn("session_start.generated.md", prompt)
        self.assertIn("innovation_direction.md", prompt)
        self.assertIn("innovation_decisions.jsonl", prompt)
        self.assertIn("authoritative translation of that request", prompt)
        self.assertIn("authoritative translation of the user's chat request", prompt)

    def test_codex_parser_accepts_latest_topic_flag(self) -> None:
        parser = build_codex_parser()
        args = parser.parse_args(["--latest-topic", "继续这个 topic，方向改成 X"])

        self.assertTrue(args.latest_topic)
        self.assertEqual(args.task, "继续这个 topic，方向改成 X")

    def test_codex_parser_accepts_current_topic_flag(self) -> None:
        parser = build_codex_parser()
        args = parser.parse_args(["--current-topic", "继续这个 topic"])

        self.assertTrue(args.current_topic)
        self.assertEqual(args.task, "继续这个 topic")

    def test_codex_parser_accepts_plain_task_without_topic_flags(self) -> None:
        parser = build_codex_parser()
        args = parser.parse_args(["继续这个 topic，方向改成 X"])

        self.assertEqual(args.task, "继续这个 topic，方向改成 X")
        self.assertFalse(args.current_topic)
        self.assertFalse(args.latest_topic)
        self.assertIsNone(args.topic_slug)
        self.assertIsNone(args.topic)

    def test_request_and_approve_promotion_gate_write_runtime_artifacts(self) -> None:
        self._write_runtime_state()
        self._write_candidate()

        requested = self.service.request_promotion(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            backend_id="backend:theoretical-physics-knowledge-network",
        )
        self.assertEqual(requested["status"], "pending_human_approval")
        self.assertTrue(Path(requested["promotion_gate_path"]).exists())
        self.assertTrue(Path(requested["promotion_gate_note_path"]).exists())

        approved = self.service.approve_promotion(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
        )
        self.assertEqual(approved["status"], "approved")
        gate_payload = json.loads(Path(approved["promotion_gate_path"]).read_text(encoding="utf-8"))
        self.assertEqual(gate_payload["approved_by"], "aitp-cli")

    def test_assess_topic_completion_reports_promoted_when_gate_is_promoted(self) -> None:
        self._write_runtime_state()
        self._write_candidate()
        self.service.audit_theory_coverage(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            source_sections=["sec:intro"],
            covered_sections=["sec:intro"],
            equation_labels=["eq:1"],
            notation_bindings=[{"symbol": "H", "meaning": "Hamiltonian"}],
            derivation_nodes=["def:h"],
            agent_votes=[{"role": "skeptic", "verdict": "no_major_gap", "notes": ""}],
            consensus_status="unanimous",
            critical_unit_recall=1.0,
            missing_anchor_count=0,
            skeptic_major_gap_count=0,
            supporting_regression_question_ids=["regression_question:demo-definition"],
            supporting_oracle_ids=["question_oracle:demo-definition"],
            supporting_regression_run_ids=["regression_run:demo-definition"],
        )
        runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        (runtime_root / "promotion_gate.json").write_text(
            json.dumps(
                {
                    "status": "promoted",
                    "candidate_id": "candidate:demo-candidate",
                    "promoted_units": ["concept:demo-promoted-concept"],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.assess_topic_completion(
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
        )

        self.assertEqual(payload["status"], "promoted")

    def test_audit_theory_coverage_writes_packet_artifacts(self) -> None:
        self._write_runtime_state()
        self._write_candidate()

        payload = self.service.audit_theory_coverage(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            source_sections=["sec:intro", "sec:result"],
            covered_sections=["sec:intro", "sec:result"],
            equation_labels=["eq:1"],
            notation_bindings=[{"symbol": "H", "meaning": "Hamiltonian"}],
            derivation_nodes=["def:h", "eq:1"],
            agent_votes=[{"role": "skeptic", "verdict": "no_major_gap", "notes": ""}],
            consensus_status="unanimous",
            critical_unit_recall=1.0,
            missing_anchor_count=0,
            skeptic_major_gap_count=0,
            supporting_regression_question_ids=["regression_question:demo-definition"],
            supporting_oracle_ids=["question_oracle:demo-definition"],
            supporting_regression_run_ids=["regression_run:demo-definition"],
        )

        self.assertEqual(payload["coverage_status"], "pass")
        self.assertEqual(payload["regression_gate_status"], "pass")
        self.assertEqual(payload["topic_completion_status"], "promotion-ready")
        self.assertTrue(Path(payload["paths"]["structure_map"]).exists())
        self.assertTrue(Path(payload["paths"]["coverage_ledger"]).exists())
        self.assertTrue(Path(payload["paths"]["notation_table"]).exists())
        self.assertTrue(Path(payload["paths"]["derivation_graph"]).exists())
        self.assertTrue(Path(payload["paths"]["agent_consensus"]).exists())
        self.assertTrue(Path(payload["paths"]["regression_gate"]).exists())

    def test_promote_candidate_merges_exact_title_collision(self) -> None:
        self._write_runtime_state()
        self._write_candidate(title="Demo Promoted Concept")
        tpkn_root = self._write_fake_tpkn_repo()
        existing_unit_path = tpkn_root / "units" / "concepts" / "existing-canonical-concept.json"
        existing_unit_path.write_text(
            json.dumps(
                {
                    "id": "concept:existing-canonical-concept",
                    "type": "concept",
                    "title": "Demo Promoted Concept",
                    "summary": "Existing canonical concept.",
                    "domain": "demo-domain",
                    "subdomain": "demo-subdomain",
                    "tags": ["concept"],
                    "aliases": [],
                    "assumptions": ["Existing assumption."],
                    "regime": "Existing regime.",
                    "scope": "Existing scope.",
                    "dependencies": [],
                    "related_units": [],
                    "source_anchors": [
                        {
                            "source_id": "paper:existing-source",
                            "section": "existing/section",
                            "notes": "Existing anchor.",
                        }
                    ],
                    "formalization_status": "candidate",
                    "validation_status": "validated",
                    "maturity": "seed",
                    "created_at": "2026-03-13",
                    "updated_at": "2026-03-13",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.service.request_promotion(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            backend_id="backend:theoretical-physics-knowledge-network",
            target_backend_root=str(tpkn_root),
        )
        self.service.approve_promotion(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
        )

        payload = self.service.promote_candidate(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            target_backend_root=str(tpkn_root),
            domain="demo-domain",
            subdomain="demo-subdomain",
        )

        self.assertEqual(payload["target_unit_id"], "concept:existing-canonical-concept")
        self.assertEqual(payload["merge_outcome"], "merged_existing")
        unit_payload = json.loads(Path(payload["target_unit_path"]).read_text(encoding="utf-8"))
        self.assertEqual(len(unit_payload["source_anchors"]), 2)

    def test_promote_candidate_writes_tpkn_unit_and_decision(self) -> None:
        self._write_runtime_state()
        self._write_candidate()
        tpkn_root = self._write_fake_tpkn_repo()
        self.service.request_promotion(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            backend_id="backend:theoretical-physics-knowledge-network",
            target_backend_root=str(tpkn_root),
        )
        self.service.approve_promotion(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
        )

        payload = self.service.promote_candidate(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            target_backend_root=str(tpkn_root),
            domain="demo-domain",
            subdomain="demo-subdomain",
        )

        unit_path = Path(payload["target_unit_path"])
        decision_path = Path(payload["promotion_decision_path"])
        consultation_result_path = Path(payload["consultation"]["consultation_result_path"])
        self.assertTrue(unit_path.exists())
        self.assertTrue(decision_path.exists())
        self.assertTrue(consultation_result_path.exists())
        unit_payload = json.loads(unit_path.read_text(encoding="utf-8"))
        self.assertEqual(unit_payload["id"], "concept:demo-promoted-concept")
        self.assertEqual(unit_payload["domain"], "demo-domain")
        self.assertIsInstance(unit_payload["review_artifacts"], list)
        self.assertIsInstance(unit_payload["merge_lineage"], list)
        decision_rows = [json.loads(line) for line in decision_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(decision_rows[-1]["verdict"], "accepted")
        gate_payload = json.loads(Path(payload["promotion_gate_path"]).read_text(encoding="utf-8"))
        self.assertEqual(gate_payload["status"], "promoted")
        candidate_rows = [
            json.loads(line)
            for line in (self.kernel_root / "feedback" / "topics" / "demo-topic" / "runs" / "2026-03-13-demo" / "candidate_ledger.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(candidate_rows[0]["status"], "promoted")

    def test_promote_topic_skill_projection_writes_tpkn_projection_unit(self) -> None:
        runtime_root = self._write_runtime_state(run_id="run-001")
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "run-001",
                    "resume_stage": "L3",
                    "research_mode": "exploratory_general",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.service.scaffold_operation(
            topic_slug="demo-topic",
            run_id="run-001",
            title="TFIM exact-diagonalization benchmark workflow",
            kind="coding",
        )
        self.service.update_operation(
            topic_slug="demo-topic",
            run_id="run-001",
            operation="TFIM exact-diagonalization benchmark workflow",
            baseline_status="passed",
            artifact_paths=["validation/topics/demo-topic/runs/run-001/results/benchmark.json"],
        )
        self.service.audit_operation_trust(topic_slug="demo-topic", run_id="run-001")
        self.service.record_strategy_memory(
            topic_slug="demo-topic",
            run_id="run-001",
            strategy_type="verification_guardrail",
            summary="Close the exact benchmark before broader code-method confidence.",
            outcome="helpful",
            lane="code_method",
            confidence=0.82,
        )
        projection_payload = self.service.project_topic_skill(topic_slug="demo-topic")
        projection_candidate = projection_payload["topic_skill_projection_candidate"]
        self.assertIsNotNone(projection_candidate)

        tpkn_root = self._write_fake_tpkn_repo()
        self.service.request_promotion(
            topic_slug="demo-topic",
            candidate_id=projection_candidate["candidate_id"],
            run_id="run-001",
            backend_id="backend:theoretical-physics-knowledge-network",
            target_backend_root=str(tpkn_root),
        )
        self.service.approve_promotion(
            topic_slug="demo-topic",
            candidate_id=projection_candidate["candidate_id"],
            run_id="run-001",
        )

        payload = self.service.promote_candidate(
            topic_slug="demo-topic",
            candidate_id=projection_candidate["candidate_id"],
            run_id="run-001",
            target_backend_root=str(tpkn_root),
            domain="demo-domain",
            subdomain="code-method",
        )

        unit_path = Path(payload["target_unit_path"])
        self.assertTrue(unit_path.exists())
        self.assertIn("topic-skill-projections", str(unit_path).replace("\\", "/"))
        unit_payload = json.loads(unit_path.read_text(encoding="utf-8"))
        self.assertEqual(unit_payload["type"], "topic_skill_projection")
        self.assertEqual(unit_payload["canonical_layer"], "L2")

    def test_auto_promote_rejects_topic_skill_projection(self) -> None:
        runtime_root = self._write_runtime_state(run_id="run-001")
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "run-001",
                    "resume_stage": "L3",
                    "research_mode": "exploratory_general",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.service.scaffold_operation(
            topic_slug="demo-topic",
            run_id="run-001",
            title="TFIM exact-diagonalization benchmark workflow",
            kind="coding",
        )
        self.service.update_operation(
            topic_slug="demo-topic",
            run_id="run-001",
            operation="TFIM exact-diagonalization benchmark workflow",
            baseline_status="passed",
        )
        self.service.audit_operation_trust(topic_slug="demo-topic", run_id="run-001")
        self.service.record_strategy_memory(
            topic_slug="demo-topic",
            run_id="run-001",
            strategy_type="verification_guardrail",
            summary="Close the exact benchmark before broader code-method confidence.",
            outcome="helpful",
            lane="code_method",
            confidence=0.82,
        )
        projection_payload = self.service.project_topic_skill(topic_slug="demo-topic")
        projection_candidate = projection_payload["topic_skill_projection_candidate"]
        self.assertIsNotNone(projection_candidate)
        self._write_tpkn_backend_card(allows_auto=True)
        tpkn_root = self._write_fake_tpkn_repo()

        with self.assertRaisesRegex(PermissionError, "human-reviewed only"):
            self.service.auto_promote_candidate(
                topic_slug="demo-topic",
                candidate_id=projection_candidate["candidate_id"],
                run_id="run-001",
                target_backend_root=str(tpkn_root),
                domain="demo-domain",
                subdomain="code-method",
            )

    def test_auto_promote_candidate_writes_l2_auto_unit_and_report(self) -> None:
        self._write_runtime_state()
        self._write_candidate()
        self._write_tpkn_backend_card(allows_auto=True)
        tpkn_root = self._write_fake_tpkn_repo()
        self.service.audit_theory_coverage(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            source_sections=["sec:intro", "sec:result"],
            covered_sections=["sec:intro", "sec:result"],
            equation_labels=["eq:1"],
            notation_bindings=[{"symbol": "H", "meaning": "Hamiltonian"}],
            derivation_nodes=["def:h", "eq:1"],
            agent_votes=[{"role": "skeptic", "verdict": "no_major_gap", "notes": ""}],
            consensus_status="unanimous",
            critical_unit_recall=1.0,
            missing_anchor_count=0,
            skeptic_major_gap_count=0,
            supporting_regression_question_ids=["regression_question:demo-definition"],
            supporting_oracle_ids=["question_oracle:demo-definition"],
            supporting_regression_run_ids=["regression_run:demo-definition"],
        )

        payload = self.service.auto_promote_candidate(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            target_backend_root=str(tpkn_root),
            domain="demo-domain",
            subdomain="demo-subdomain",
        )

        self.assertTrue(Path(payload["auto_promotion_report_path"]).exists())
        self.assertEqual(payload["merge_outcome"], "created_new")
        unit_payload = json.loads(Path(payload["target_unit_path"]).read_text(encoding="utf-8"))
        self.assertEqual(unit_payload["canonical_layer"], "L2_auto")
        self.assertEqual(unit_payload["review_mode"], "ai_auto")
        self.assertEqual(unit_payload["topic_completion_status"], "promotion-ready")
        self.assertEqual(
            unit_payload["supporting_regression_question_ids"],
            ["regression_question:demo-definition"],
        )
        self.assertEqual(
            unit_payload["supporting_oracle_ids"],
            ["question_oracle:demo-definition"],
        )
        self.assertEqual(
            unit_payload["supporting_regression_run_ids"],
            ["regression_run:demo-definition"],
        )
        self.assertFalse(unit_payload["split_required"])
        self.assertTrue((tpkn_root / "units" / "regression-questions" / "demo-definition.json").exists())
        self.assertTrue((tpkn_root / "units" / "question-oracles" / "demo-definition.json").exists())
        self.assertIsInstance(unit_payload["review_artifacts"], list)
        self.assertIn("candidate_id=candidate:demo-candidate", unit_payload["review_artifacts"])
        self.assertEqual(unit_payload["translation_readiness"], "candidate")
        self.assertIn("semi-formal AITP Layer 2 unit", unit_payload["trust_boundary"])
        self.assertIsInstance(unit_payload["semi_formal_contract"], list)
        candidate_rows = [
            json.loads(line)
            for line in (self.kernel_root / "feedback" / "topics" / "demo-topic" / "runs" / "2026-03-13-demo" / "candidate_ledger.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(candidate_rows[0]["status"], "auto_promoted")

    def test_audit_formal_theory_writes_review_artifacts_and_updates_candidate(self) -> None:
        self._write_runtime_state()
        self._write_candidate(
            candidate_type="theorem_card",
            intended_l2_target="theorem:demo-topological-theorem",
            title="Demo Topological Theorem",
        )

        payload = self.service.audit_formal_theory(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            formal_theory_role="trusted_target",
            statement_graph_role="target_statement",
            definition_trust_tier="scientific_source",
            target_statement_id="theorem:demo-topological-theorem",
            statement_graph_parents=["definition:chern-number"],
            statement_graph_children=["corollary:demo-hall-response"],
            informal_statement="A bounded theorem card for formal-theory review.",
            formal_target="Demo.Topological.demo_theorem",
            faithfulness_status="reviewed",
            faithfulness_strategy="bounded source-to-target map",
            comparator_audit_status="passed",
            comparator_risks=["Nearby weakened statement could drop a hypothesis."],
            nearby_variants=[
                {
                    "label": "demo weakened theorem",
                    "relation": "weaker_variant",
                    "verdict": "rejected",
                    "notes": "Missing the source hypothesis.",
                }
            ],
            provenance_kind="adapted_existing_formalization",
            attribution_requirements=["Preserve upstream theorem citation."],
            provenance_sources=["physlib:demo/theorem.lean@abc1234"],
            prerequisite_closure_status="closed",
            lean_prerequisite_ids=["physlib:chern-number"],
            supporting_obligation_ids=["proof_obligation:demo-topological-theorem"],
        )

        formal_review_path = Path(payload["paths"]["formal_theory_review"])
        self.assertTrue(formal_review_path.exists())
        review_payload = json.loads(formal_review_path.read_text(encoding="utf-8"))
        schemas_root = Path(__file__).resolve().parents[1] / "validation" / "schemas"
        schema = json.loads((schemas_root / "formal-theory-review.schema.json").read_text(encoding="utf-8"))
        comparator_schema = json.loads(
            (schemas_root / "comparator-audit-record.schema.json").read_text(encoding="utf-8")
        )
        registry = Registry().with_resources(
            [
                (schema["$id"], Resource.from_contents(schema)),
                (comparator_schema["$id"], Resource.from_contents(comparator_schema)),
            ]
        )
        Draft202012Validator(schema, registry=registry).validate(review_payload)
        self.assertEqual(payload["overall_status"], "ready")
        self.assertEqual(review_payload["overall_status"], "ready")
        self.assertEqual(
            review_payload["faithfulness_review_path"],
            "validation/topics/demo-topic/runs/2026-03-13-demo/theory-packets/candidate-demo-candidate/faithfulness_review.json",
        )

        candidate_rows = [
            json.loads(line)
            for line in (self.kernel_root / "feedback" / "topics" / "demo-topic" / "runs" / "2026-03-13-demo" / "candidate_ledger.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(candidate_rows[0]["formal_theory_review_overall_status"], "ready")
        self.assertIn("formal_theory_review", candidate_rows[0]["theory_packet_refs"])

    def test_auto_promote_candidate_requires_formal_theory_review_for_theory_formal_candidate_types(self) -> None:
        self._write_runtime_state()
        self._write_candidate(
            candidate_type="theorem_card",
            intended_l2_target="theorem:demo-topological-theorem",
            title="Demo Topological Theorem",
        )
        self._write_tpkn_backend_card(allows_auto=True)
        tpkn_root = self._write_fake_tpkn_repo()
        self.service.audit_theory_coverage(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            source_sections=["sec:intro"],
            covered_sections=["sec:intro"],
            consensus_status="unanimous",
            critical_unit_recall=1.0,
            missing_anchor_count=0,
            skeptic_major_gap_count=0,
            supporting_regression_question_ids=["regression_question:demo-theorem"],
            supporting_oracle_ids=["question_oracle:demo-theorem"],
            supporting_regression_run_ids=["regression_run:demo-theorem"],
        )

        with self.assertRaisesRegex(FileNotFoundError, "formal_theory_review"):
            self.service.auto_promote_candidate(
                topic_slug="demo-topic",
                candidate_id="candidate:demo-candidate",
                target_backend_root=str(tpkn_root),
                domain="demo-domain",
                subdomain="demo-subdomain",
            )

    def test_auto_promote_candidate_requires_passing_regression_gate(self) -> None:
        self._write_runtime_state()
        self._write_candidate()
        self._write_tpkn_backend_card(allows_auto=True)
        tpkn_root = self._write_fake_tpkn_repo()
        self.service.audit_theory_coverage(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            source_sections=["sec:intro"],
            covered_sections=["sec:intro"],
            consensus_status="unanimous",
            critical_unit_recall=1.0,
            missing_anchor_count=0,
            skeptic_major_gap_count=0,
        )

        with self.assertRaisesRegex(PermissionError, "regression_gate.json"):
            self.service.auto_promote_candidate(
                topic_slug="demo-topic",
                candidate_id="candidate:demo-candidate",
                target_backend_root=str(tpkn_root),
                domain="demo-domain",
                subdomain="demo-subdomain",
            )

    def test_auto_promote_candidate_blocks_on_split_or_gap_honesty(self) -> None:
        self._write_runtime_state()
        self._write_candidate()
        self._write_tpkn_backend_card(allows_auto=True)
        tpkn_root = self._write_fake_tpkn_repo()
        self.service.audit_theory_coverage(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            source_sections=["sec:intro"],
            covered_sections=["sec:intro"],
            consensus_status="unanimous",
            critical_unit_recall=1.0,
            missing_anchor_count=0,
            skeptic_major_gap_count=0,
            supporting_regression_question_ids=["regression_question:demo-definition"],
            supporting_oracle_ids=["question_oracle:demo-definition"],
            supporting_regression_run_ids=["regression_run:demo-definition"],
            promotion_blockers=["Need a narrower proof split."],
            split_required=True,
            cited_recovery_required=True,
            topic_completion_status="promotion-blocked",
        )

        with self.assertRaisesRegex(PermissionError, "split clearance"):
            self.service.auto_promote_candidate(
                topic_slug="demo-topic",
                candidate_id="candidate:demo-candidate",
                target_backend_root=str(tpkn_root),
                domain="demo-domain",
                subdomain="demo-subdomain",
            )

    def test_apply_candidate_split_contract_creates_children_and_deferred_buffer(self) -> None:
        self._write_runtime_state()
        self._write_candidate()
        run_root = self.kernel_root / "feedback" / "topics" / "demo-topic" / "runs" / "2026-03-13-demo"
        contract_path = run_root / "candidate_split.contract.json"
        contract_path.write_text(
            json.dumps(
                {
                    "contract_version": 1,
                    "splits": [
                        {
                            "source_candidate_id": "candidate:demo-candidate",
                            "reason": "The source candidate mixes a reusable definition with a still-unresolved caveat.",
                            "child_candidates": [
                                {
                                    "candidate_id": "candidate:demo-definition",
                                    "candidate_type": "definition_card",
                                    "title": "Demo Definition",
                                    "summary": "A sharp definition extracted from the wider candidate.",
                                    "origin_refs": [],
                                    "question": "Can the bounded definition be promoted independently?",
                                    "assumptions": ["Bounded example."],
                                    "proposed_validation_route": "bounded-smoke",
                                    "intended_l2_targets": ["definition:demo-definition"],
                                }
                            ],
                            "deferred_fragments": [
                                {
                                    "entry_id": "deferred:demo-caveat",
                                    "title": "Demo Caveat",
                                    "summary": "A caveat parked until a cited follow-up source is available.",
                                    "reason": "Missing source-local resolution for the caveat.",
                                    "required_l2_types": ["caveat_card"],
                                    "reactivation_conditions": {
                                        "source_ids_any": ["paper:followup-source"]
                                    },
                                    "reactivation_candidate": {
                                        "candidate_id": "candidate:demo-caveat-reactivated",
                                        "candidate_type": "caveat_card",
                                        "title": "Demo Caveat Reactivated",
                                        "summary": "Reactivated caveat candidate.",
                                        "origin_refs": [],
                                        "question": "Can the caveat now be promoted separately?",
                                        "assumptions": ["Bounded example."],
                                        "proposed_validation_route": "bounded-smoke",
                                        "intended_l2_targets": ["caveat:demo-caveat-reactivated"]
                                    }
                                }
                            ]
                        }
                    ]
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.apply_candidate_split_contract(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )

        self.assertEqual(payload["applied_source_candidates"], ["candidate:demo-candidate"])
        ledger_rows = [
            json.loads(line)
            for line in (run_root / "candidate_ledger.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        source_row = next(row for row in ledger_rows if row["candidate_id"] == "candidate:demo-candidate")
        child_row = next(row for row in ledger_rows if row["candidate_id"] == "candidate:demo-definition")
        self.assertEqual(source_row["status"], "split_into_children")
        self.assertEqual(child_row["split_parent_id"], "candidate:demo-candidate")
        deferred_payload = json.loads(
            (self.kernel_root / "runtime" / "topics" / "demo-topic" / "deferred_candidates.json").read_text(encoding="utf-8")
        )
        self.assertEqual(deferred_payload["entries"][0]["status"], "buffered")
        self.assertEqual(deferred_payload["entries"][0]["entry_id"], "deferred:demo-caveat")

    def test_apply_candidate_split_contract_preserves_existing_child_audit_fields(self) -> None:
        self._write_runtime_state()
        self._write_candidate()
        run_root = self.kernel_root / "feedback" / "topics" / "demo-topic" / "runs" / "2026-03-13-demo"
        ledger_path = run_root / "candidate_ledger.jsonl"
        existing_rows = [
            json.loads(line)
            for line in ledger_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        existing_rows.append(
            {
                "candidate_id": "candidate:demo-definition",
                "candidate_type": "definition_card",
                "title": "Demo Definition",
                "summary": "Existing audited child candidate.",
                "topic_slug": "demo-topic",
                "run_id": "2026-03-13-demo",
                "origin_refs": [],
                "question": "Can the bounded definition stay independently promotable?",
                "assumptions": ["Bounded example."],
                "proposed_validation_route": "bounded-smoke",
                "intended_l2_targets": ["definition:demo-definition"],
                "status": "ready_for_validation",
                "split_parent_id": "candidate:demo-candidate",
                "supporting_regression_question_ids": ["regression_question:demo-definition"],
                "supporting_oracle_ids": ["question_oracle:demo-definition"],
                "supporting_regression_run_ids": ["regression_run:demo-definition"],
                "formal_theory_role": "trusted_target",
                "statement_graph_role": "target_statement",
                "target_statement_id": "definition:demo-definition",
                "formal_theory_review_overall_status": "ready",
            }
        )
        ledger_path.write_text(
            "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in existing_rows),
            encoding="utf-8",
        )

        contract_path = run_root / "candidate_split.contract.json"
        contract_path.write_text(
            json.dumps(
                {
                    "contract_version": 1,
                    "splits": [
                        {
                            "source_candidate_id": "candidate:demo-candidate",
                            "reason": "Reapply the split contract with refreshed child copy.",
                            "child_candidates": [
                                {
                                    "candidate_id": "candidate:demo-definition",
                                    "candidate_type": "definition_card",
                                    "title": "Demo Definition Refreshed",
                                    "summary": "Updated child summary from the latest split contract.",
                                    "origin_refs": [],
                                    "question": "Can the refreshed bounded definition still be promoted independently?",
                                    "assumptions": ["Bounded example."],
                                    "proposed_validation_route": "bounded-smoke",
                                    "intended_l2_targets": ["definition:demo-definition"],
                                }
                            ],
                            "deferred_fragments": [],
                        }
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        self.service.apply_candidate_split_contract(topic_slug="demo-topic", updated_by="aitp-cli")

        ledger_rows = [
            json.loads(line)
            for line in ledger_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        child_row = next(row for row in ledger_rows if row["candidate_id"] == "candidate:demo-definition")
        self.assertEqual(child_row["title"], "Demo Definition Refreshed")
        self.assertEqual(child_row["summary"], "Updated child summary from the latest split contract.")
        self.assertEqual(child_row["supporting_regression_question_ids"], ["regression_question:demo-definition"])
        self.assertEqual(child_row["formal_theory_role"], "trusted_target")
        self.assertEqual(child_row["formal_theory_review_overall_status"], "ready")

    def test_reactivate_deferred_candidates_materializes_reactivated_candidate(self) -> None:
        self._write_runtime_state()
        self._write_candidate()
        run_root = self.kernel_root / "feedback" / "topics" / "demo-topic" / "runs" / "2026-03-13-demo"
        contract_path = run_root / "candidate_split.contract.json"
        contract_path.write_text(
            json.dumps(
                {
                    "contract_version": 1,
                    "splits": [
                        {
                            "source_candidate_id": "candidate:demo-candidate",
                            "reason": "Park one fragment for later reactivation.",
                            "child_candidates": [],
                            "deferred_fragments": [
                                {
                                    "entry_id": "deferred:demo-reactivation",
                                    "title": "Deferred fragment",
                                    "summary": "Wait for a follow-up source.",
                                    "reason": "The current paper is insufficient.",
                                    "reactivation_conditions": {
                                        "source_ids_any": ["paper:followup-source"]
                                    },
                                    "reactivation_candidate": {
                                        "candidate_id": "candidate:demo-reactivated",
                                        "candidate_type": "caveat_card",
                                        "title": "Demo Reactivated",
                                        "summary": "Reactivated candidate from deferred buffer.",
                                        "origin_refs": [],
                                        "question": "Can the follow-up source resolve the caveat?",
                                        "assumptions": ["Bounded example."],
                                        "proposed_validation_route": "bounded-smoke",
                                        "intended_l2_targets": ["caveat:demo-reactivated"]
                                    }
                                }
                            ]
                        }
                    ]
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.service.apply_candidate_split_contract(topic_slug="demo-topic", updated_by="aitp-cli")
        source_index_path = self.kernel_root / "source-layer" / "topics" / "demo-topic" / "source_index.jsonl"
        source_index_path.parent.mkdir(parents=True, exist_ok=True)
        source_index_path.write_text(
            json.dumps(
                {
                    "source_id": "paper:followup-source",
                    "source_type": "paper",
                    "title": "Follow-up Source",
                    "summary": "Contains the missing caveat resolution.",
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.reactivate_deferred_candidates(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )

        self.assertEqual(payload["reactivated_candidate_ids"], ["candidate:demo-reactivated"])
        ledger_rows = [
            json.loads(line)
            for line in (run_root / "candidate_ledger.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        reactivated_row = next(row for row in ledger_rows if row["candidate_id"] == "candidate:demo-reactivated")
        self.assertEqual(reactivated_row["status"], "reactivated")
        self.assertEqual(reactivated_row["reactivated_from"], "deferred:demo-reactivation")
        deferred_payload = json.loads(
            (self.kernel_root / "runtime" / "topics" / "demo-topic" / "deferred_candidates.json").read_text(encoding="utf-8")
        )
        self.assertEqual(deferred_payload["entries"][0]["status"], "reactivated")

    def test_spawn_followup_subtopics_creates_child_topics_and_runtime_ledger(self) -> None:
        service = _FollowupStubService(kernel_root=self.kernel_root, repo_root=self.repo_root)
        self._write_runtime_state()
        receipts_path = (
            self.kernel_root
            / "validation"
            / "topics"
            / "demo-topic"
            / "runs"
            / "2026-03-13-demo"
            / "literature_followup_receipts.jsonl"
        )
        receipts_path.parent.mkdir(parents=True, exist_ok=True)
        receipts_path.write_text(
            json.dumps(
                {
                    "receipt_id": "literature-followup:demo-topic:q1",
                    "topic_slug": "demo-topic",
                    "run_id": "2026-03-13-demo",
                    "query": "demo follow-up gap",
                    "parent_gap_ids": ["open_gap:demo-gap"],
                    "parent_followup_task_ids": ["followup_source_task:demo-followup"],
                    "reentry_targets": ["theorem:demo-theorem"],
                    "supporting_regression_question_ids": ["regression_question:demo-question"],
                    "target_source_type": "paper",
                    "status": "completed",
                    "matches": [
                        {"arxiv_id": "1510.07698v1", "title": "Topological Phases of Matter"}
                    ],
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = service.spawn_followup_subtopics(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )

        self.assertEqual(len(payload["spawned_subtopics"]), 1)
        child_topic_slug = payload["spawned_subtopics"][0]["child_topic_slug"]
        self.assertIn(child_topic_slug, service.orchestrated_topics)
        self.assertTrue((self.kernel_root / "runtime" / "topics" / child_topic_slug / "topic_state.json").exists())
        ledger_rows = [
            json.loads(line)
            for line in (self.kernel_root / "runtime" / "topics" / "demo-topic" / "followup_subtopics.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(ledger_rows[0]["parent_topic_slug"], "demo-topic")
        self.assertEqual(ledger_rows[0]["arxiv_id"], "1510.07698v1")
        return_packet_path = Path(ledger_rows[0]["return_packet_path"])
        self.assertTrue(return_packet_path.exists())
        return_packet = json.loads(return_packet_path.read_text(encoding="utf-8"))
        package_root = Path(__file__).resolve().parents[1]
        packet_schema = json.loads(
            (
                package_root
                / "runtime"
                / "schemas"
                / "followup-return-packet.schema.json"
            ).read_text(encoding="utf-8")
        )
        Draft202012Validator(packet_schema).validate(return_packet)
        self.assertEqual(return_packet["parent_gap_ids"], ["open_gap:demo-gap"])
        self.assertEqual(return_packet["reentry_targets"], ["theorem:demo-theorem"])
        self.assertEqual(return_packet["expected_return_route"], "L0->L1->L3->L4->L2")
        self.assertIn("recovered_units", return_packet["acceptable_return_shapes"])
        self.assertTrue(return_packet["reintegration_requirements"]["must_not_patch_parent_directly"])
        self.assertTrue((return_packet_path.with_suffix(".md")).exists())

    def test_reintegrate_followup_subtopic_writes_receipt_and_updates_parent_row(self) -> None:
        service = _FollowupStubService(kernel_root=self.kernel_root, repo_root=self.repo_root)
        self._write_runtime_state()
        receipts_path = (
            self.kernel_root
            / "validation"
            / "topics"
            / "demo-topic"
            / "runs"
            / "2026-03-13-demo"
            / "literature_followup_receipts.jsonl"
        )
        receipts_path.parent.mkdir(parents=True, exist_ok=True)
        receipts_path.write_text(
            json.dumps(
                {
                    "receipt_id": "literature-followup:demo-topic:q2",
                    "topic_slug": "demo-topic",
                    "run_id": "2026-03-13-demo",
                    "query": "recover the missing proof background",
                    "parent_gap_ids": ["open_gap:proof-background"],
                    "parent_followup_task_ids": ["followup_source_task:proof-background"],
                    "reentry_targets": ["theorem:demo-main"],
                    "supporting_regression_question_ids": ["regression_question:demo-main"],
                    "target_source_type": "paper",
                    "status": "completed",
                    "matches": [{"arxiv_id": "1510.07698v1", "title": "Topological Phases of Matter"}],
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        spawned = service.spawn_followup_subtopics(topic_slug="demo-topic", updated_by="aitp-cli")
        child_topic_slug = spawned["spawned_subtopics"][0]["child_topic_slug"]
        followup_rows = [
            json.loads(line)
            for line in (self.kernel_root / "runtime" / "topics" / "demo-topic" / "followup_subtopics.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        service.update_followup_return_packet(
            topic_slug=child_topic_slug,
            return_status="recovered_units",
            accepted_return_shape="recovered_units",
            return_summary="Recovered the missing proof background and bounded notation context.",
            return_artifact_paths=["feedback/topics/demo-topic/runs/2026-03-13-demo/candidate_ledger.jsonl"],
            updated_by="aitp-cli",
        )

        payload = service.reintegrate_followup_subtopic(
            topic_slug="demo-topic",
            child_topic_slug=child_topic_slug,
            updated_by="aitp-cli",
        )

        self.assertEqual(payload["parent_followup_status"], "reintegrated")
        self.assertTrue(Path(payload["followup_reintegration_path"]).exists())
        updated_rows = [
            json.loads(line)
            for line in (self.kernel_root / "runtime" / "topics" / "demo-topic" / "followup_subtopics.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(updated_rows[0]["status"], "reintegrated")
        reintegration_rows = [
            json.loads(line)
            for line in Path(payload["followup_reintegration_path"]).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(reintegration_rows[0]["return_status"], "recovered_units")
        self.assertEqual(reintegration_rows[0]["child_topic_completion_status"], "not_assessed")
        self.assertTrue(Path(payload["runtime_protocol"]["runtime_protocol_path"]).exists())

    def test_reintegrate_followup_subtopic_writes_gap_writeback_for_unresolved_return(self) -> None:
        service = _FollowupStubService(kernel_root=self.kernel_root, repo_root=self.repo_root)
        self._write_runtime_state()
        receipts_path = (
            self.kernel_root
            / "validation"
            / "topics"
            / "demo-topic"
            / "runs"
            / "2026-03-13-demo"
            / "literature_followup_receipts.jsonl"
        )
        receipts_path.parent.mkdir(parents=True, exist_ok=True)
        receipts_path.write_text(
            json.dumps(
                {
                    "receipt_id": "literature-followup:demo-topic:q4",
                    "topic_slug": "demo-topic",
                    "run_id": "2026-03-13-demo",
                    "query": "recover unresolved parity anomaly background",
                    "parent_gap_ids": ["open_gap:parity-anomaly"],
                    "parent_followup_task_ids": ["followup_source_task:parity-anomaly"],
                    "reentry_targets": ["theorem:demo-parity"],
                    "supporting_regression_question_ids": ["regression_question:demo-parity"],
                    "target_source_type": "paper",
                    "status": "completed",
                    "matches": [{"arxiv_id": "1510.07698v1", "title": "Topological Phases of Matter"}],
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        spawned = service.spawn_followup_subtopics(topic_slug="demo-topic", updated_by="aitp-cli")
        child_topic_slug = spawned["spawned_subtopics"][0]["child_topic_slug"]
        service.update_followup_return_packet(
            topic_slug=child_topic_slug,
            return_status="returned_with_gap",
            accepted_return_shape="still_unresolved_packet",
            return_summary="The cited parity-anomaly prerequisite remains unresolved and must go back through L0.",
            updated_by="aitp-cli",
        )

        payload = service.reintegrate_followup_subtopic(
            topic_slug="demo-topic",
            child_topic_slug=child_topic_slug,
            updated_by="aitp-cli",
        )

        self.assertEqual(payload["parent_followup_status"], "returned_with_gap")
        self.assertTrue(Path(payload["followup_gap_writeback_path"]).exists())
        writeback_rows = [
            json.loads(line)
            for line in Path(payload["followup_gap_writeback_path"]).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(writeback_rows[0]["parent_gap_ids"], ["open_gap:parity-anomaly"])
        runtime_bundle = json.loads(
            Path(payload["runtime_protocol"]["runtime_protocol_path"]).read_text(encoding="utf-8")
        )
        self.assertEqual(runtime_bundle["open_gap_summary"]["followup_gap_writeback_count"], 1)
        self.assertIn("open_gap:parity-anomaly", runtime_bundle["open_gap_summary"]["followup_gap_ids"])

    def test_update_followup_return_packet_writes_success_payload_and_schema_validates(self) -> None:
        service = _FollowupStubService(kernel_root=self.kernel_root, repo_root=self.repo_root)
        self._write_runtime_state()
        receipts_path = (
            self.kernel_root
            / "validation"
            / "topics"
            / "demo-topic"
            / "runs"
            / "2026-03-13-demo"
            / "literature_followup_receipts.jsonl"
        )
        receipts_path.parent.mkdir(parents=True, exist_ok=True)
        receipts_path.write_text(
            json.dumps(
                {
                    "receipt_id": "literature-followup:demo-topic:q3",
                    "topic_slug": "demo-topic",
                    "run_id": "2026-03-13-demo",
                    "query": "recover cited definition",
                    "parent_gap_ids": ["open_gap:cited-definition"],
                    "parent_followup_task_ids": ["followup_source_task:cited-definition"],
                    "reentry_targets": ["definition:demo-main"],
                    "supporting_regression_question_ids": ["regression_question:demo-main"],
                    "target_source_type": "paper",
                    "status": "completed",
                    "matches": [{"arxiv_id": "1510.07698v1", "title": "Topological Phases of Matter"}],
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        spawned = service.spawn_followup_subtopics(topic_slug="demo-topic", updated_by="aitp-cli")
        child_topic_slug = spawned["spawned_subtopics"][0]["child_topic_slug"]

        payload = service.update_followup_return_packet(
            topic_slug=child_topic_slug,
            return_status="resolved_gap_update",
            accepted_return_shape="resolved_gap_update",
            return_summary="Recovered the cited definition and bounded the parent reentry target.",
            child_topic_summary="The child topic now contains the cited-definition recovery path and bounded notes.",
            return_artifact_paths=["validation/topics/demo-topic/runs/2026-03-13-demo/theory-packets/candidate-demo/coverage_ledger.json"],
            updated_by="aitp-cli",
        )

        packet_schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "runtime"
                / "schemas"
                / "followup-return-packet.schema.json"
            ).read_text(encoding="utf-8")
        )
        packet_payload = json.loads(Path(payload["return_packet_path"]).read_text(encoding="utf-8"))
        Draft202012Validator(packet_schema).validate(packet_payload)
        self.assertEqual(packet_payload["return_status"], "resolved_gap_update")
        self.assertEqual(packet_payload["accepted_return_shape"], "resolved_gap_update")
        self.assertTrue(Path(payload["return_packet_note_path"]).exists())

    def test_assess_topic_completion_and_prepare_lean_bridge_write_durable_artifacts(self) -> None:
        self._write_runtime_state()
        self._write_candidate()
        self.service.audit_theory_coverage(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            source_sections=["sec:intro", "sec:result"],
            covered_sections=["sec:intro", "sec:result"],
            equation_labels=["eq:1"],
            notation_bindings=[{"symbol": "H", "meaning": "Hamiltonian"}],
            derivation_nodes=["def:h", "eq:1"],
            agent_votes=[{"role": "skeptic", "verdict": "no_major_gap", "notes": ""}],
            consensus_status="unanimous",
            critical_unit_recall=1.0,
            missing_anchor_count=0,
            skeptic_major_gap_count=0,
            supporting_regression_question_ids=["regression_question:demo-definition"],
            supporting_oracle_ids=["question_oracle:demo-definition"],
            supporting_regression_run_ids=["regression_run:demo-definition"],
        )

        completion = self.service.assess_topic_completion(topic_slug="demo-topic")
        self.assertEqual(completion["status"], "promotion-ready")
        self.assertTrue(Path(completion["topic_completion_path"]).exists())
        self.assertEqual(completion["regression_manifest"]["status"], "ready")
        self.assertTrue(any(row["check"] == "followup_return_debt_clear" and row["status"] == "pass" for row in completion["completion_gate_checks"]))
        topic_completion_schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "runtime"
                / "schemas"
                / "topic-completion.schema.json"
            ).read_text(encoding="utf-8")
        )
        Draft202012Validator(topic_completion_schema).validate(
            json.loads(Path(completion["topic_completion_path"]).read_text(encoding="utf-8"))
        )

        lean_bridge = self.service.prepare_lean_bridge(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
        )
        self.assertEqual(lean_bridge["status"], "ready")
        self.assertTrue(Path(lean_bridge["lean_bridge_path"]).exists())
        active_payload = json.loads(Path(lean_bridge["lean_bridge_path"]).read_text(encoding="utf-8"))
        self.assertEqual(active_payload["packet_count"], 1)
        packet_path = (
            self.kernel_root
            / "validation"
            / "topics"
            / "demo-topic"
            / "runs"
            / "2026-03-13-demo"
            / "lean-bridge"
            / "candidate-demo-candidate"
            / "lean_ready_packet.json"
        )
        self.assertTrue(packet_path.exists())
        packet_payload = json.loads(packet_path.read_text(encoding="utf-8"))
        self.assertEqual(packet_payload["status"], "ready")
        self.assertEqual(packet_payload["declaration_kind"], "def")
        self.assertEqual(packet_payload["notation_bindings"][0]["symbol"], "H")
        self.assertEqual(packet_payload["proof_obligation_count"], 0)
        lean_ready_schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "runtime"
                / "schemas"
                / "lean-ready-packet.schema.json"
            ).read_text(encoding="utf-8")
        )
        Draft202012Validator(lean_ready_schema).validate(packet_payload)
        self.assertTrue(
            (
                self.kernel_root
                / "validation"
                / "topics"
                / "demo-topic"
                / "runs"
                / "2026-03-13-demo"
                / "lean-bridge"
                / "candidate-demo-candidate"
                / "proof_state.json"
            ).exists()
        )

    def test_prepare_lean_bridge_marks_packet_needs_refinement_when_theory_packet_is_incomplete(self) -> None:
        self._write_runtime_state()
        self._write_candidate()

        lean_bridge = self.service.prepare_lean_bridge(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
        )

        self.assertEqual(lean_bridge["status"], "needs_refinement")
        packet_path = (
            self.kernel_root
            / "validation"
            / "topics"
            / "demo-topic"
            / "runs"
            / "2026-03-13-demo"
            / "lean-bridge"
            / "candidate-demo-candidate"
            / "lean_ready_packet.json"
        )
        packet_payload = json.loads(packet_path.read_text(encoding="utf-8"))
        self.assertGreater(packet_payload["proof_obligation_count"], 0)
        self.assertEqual(packet_payload["status"], "needs_refinement")

    def test_execute_auto_actions_supports_topic_completion_and_lean_bridge(self) -> None:
        topic_slug = "demo-topic"
        self._write_runtime_state()
        self._write_candidate()
        self.service.audit_theory_coverage(
            topic_slug=topic_slug,
            candidate_id="candidate:demo-candidate",
            source_sections=["sec:intro"],
            covered_sections=["sec:intro"],
            equation_labels=["eq:1"],
            notation_bindings=[{"symbol": "H", "meaning": "Hamiltonian"}],
            derivation_nodes=["def:h"],
            agent_votes=[{"role": "skeptic", "verdict": "no_major_gap", "notes": ""}],
            consensus_status="unanimous",
            critical_unit_recall=1.0,
            missing_anchor_count=0,
            skeptic_major_gap_count=0,
            supporting_regression_question_ids=["regression_question:demo-definition"],
            supporting_oracle_ids=["question_oracle:demo-definition"],
            supporting_regression_run_ids=["regression_run:demo-definition"],
        )
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        queue_path = runtime_root / "action_queue.jsonl"
        queue_path.write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:topic-completion",
                    "status": "pending",
                    "auto_runnable": True,
                    "action_type": "assess_topic_completion",
                    "handler_args": {"run_id": "2026-03-13-demo"},
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n"
            + json.dumps(
                {
                    "action_id": "action:demo-topic:lean-bridge",
                    "status": "pending",
                    "auto_runnable": True,
                    "action_type": "prepare_lean_bridge",
                    "handler_args": {"run_id": "2026-03-13-demo"},
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service._execute_auto_actions(
            topic_slug=topic_slug,
            updated_by="aitp-cli",
            max_auto_steps=2,
            default_skill_queries=None,
        )

        self.assertEqual(len(payload["executed"]), 2)
        self.assertEqual(payload["executed"][0]["status"], "completed")
        self.assertEqual(payload["executed"][1]["status"], "completed")
        self.assertTrue((runtime_root / "topic_completion.json").exists())
        self.assertTrue((runtime_root / "lean_bridge.active.json").exists())

    def test_execute_auto_actions_supports_generic_runtime_handler(self) -> None:
        topic_slug = "demo-topic"
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        runtime_root.mkdir(parents=True, exist_ok=True)
        handler_path = self.kernel_root / "runtime" / "scripts" / "generic_runtime_handler.py"
        handler_path.parent.mkdir(parents=True, exist_ok=True)
        handler_path.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                from __future__ import annotations

                import argparse
                import json

                parser = argparse.ArgumentParser()
                parser.add_argument("--topic-slug", required=True)
                parser.add_argument("--updated-by", required=True)
                parser.add_argument("--step", required=True)
                args = parser.parse_args()
                print(json.dumps({"topic_slug": args.topic_slug, "updated_by": args.updated_by, "step": args.step}, ensure_ascii=True))
                """
            ),
            encoding="utf-8",
        )
        queue_path = runtime_root / "action_queue.jsonl"
        queue_path.write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:generic:01",
                    "status": "pending",
                    "auto_runnable": True,
                    "action_type": "select_validation_route",
                    "handler": str(handler_path),
                    "handler_args": {"step": "select_route"},
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service._execute_auto_actions(
            topic_slug=topic_slug,
            updated_by="aitp-cli",
            max_auto_steps=1,
            default_skill_queries=None,
        )

        self.assertEqual(payload["executed"][0]["status"], "completed")
        self.assertEqual(payload["executed"][0]["result"]["payload"]["step"], "select_route")
        queue_row = json.loads(queue_path.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(queue_row["status"], "completed")

    def test_execute_auto_actions_supports_literature_followup_search(self) -> None:
        topic_slug = "demo-topic"
        run_id = "2026-03-13-demo"
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        runtime_root.mkdir(parents=True, exist_ok=True)
        handler_path = self.kernel_root / "runtime" / "scripts" / "fake_literature_followup.py"
        handler_path.parent.mkdir(parents=True, exist_ok=True)
        handler_path.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                from __future__ import annotations

                import argparse
                import json
                from pathlib import Path

                parser = argparse.ArgumentParser()
                parser.add_argument("--topic-slug", required=True)
                parser.add_argument("--run-id", required=True)
                parser.add_argument("--query", required=True)
                parser.add_argument("--priority")
                parser.add_argument("--target-source-type")
                parser.add_argument("--max-results")
                parser.add_argument("--updated-by", required=True)
                args = parser.parse_args()

                knowledge_root = Path(__file__).resolve().parents[2]
                receipts_path = (
                    knowledge_root
                    / "validation"
                    / "topics"
                    / args.topic_slug
                    / "runs"
                    / args.run_id
                    / "literature_followup_receipts.jsonl"
                )
                receipts_path.parent.mkdir(parents=True, exist_ok=True)
                payload = {
                    "topic_slug": args.topic_slug,
                    "run_id": args.run_id,
                    "query": args.query,
                    "priority": args.priority,
                    "target_source_type": args.target_source_type,
                    "max_results": args.max_results,
                    "updated_by": args.updated_by,
                    "status": "completed",
                }
                with receipts_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(payload, ensure_ascii=True) + "\\n")
                print(json.dumps(payload, ensure_ascii=True))
                """
            ),
            encoding="utf-8",
        )
        queue_path = runtime_root / "action_queue.jsonl"
        queue_path.write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:literature-followup:01",
                    "status": "pending",
                    "auto_runnable": True,
                    "action_type": "literature_followup_search",
                    "handler": str(handler_path),
                    "handler_args": {
                        "run_id": run_id,
                        "query": "hs control-path baseline",
                        "priority": "medium",
                        "target_source_type": "paper",
                        "max_results": 2,
                    },
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service._execute_auto_actions(
            topic_slug=topic_slug,
            updated_by="aitp-cli",
            max_auto_steps=1,
            default_skill_queries=None,
        )

        self.assertEqual(payload["executed"][0]["status"], "completed")
        self.assertEqual(payload["executed"][0]["result"]["receipt"]["status"], "completed")
        receipt_path = (
            self.kernel_root
            / "validation"
            / "topics"
            / topic_slug
            / "runs"
            / run_id
            / "literature_followup_receipts.jsonl"
        )
        self.assertTrue(receipt_path.exists())
        receipt_rows = [json.loads(line) for line in receipt_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(receipt_rows[0]["query"], "hs control-path baseline")
        queue_row = json.loads(queue_path.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(queue_row["status"], "completed")

    def test_install_agent_writes_bootstrap_assets(self) -> None:
        codex_target = self.root / "codex-skill"
        result = self.service.install_agent(
            agent="codex",
            scope="user",
            target_root=str(codex_target),
        )

        self.assertEqual(result["installed"][0]["kind"], "skill")
        using_skill_path = codex_target / ".agents" / "skills" / "using-aitp" / "SKILL.md"
        skill_path = codex_target / ".agents" / "skills" / "aitp-runtime" / "SKILL.md"
        setup_path = codex_target / ".agents" / "skills" / "aitp-runtime" / "AITP_MCP_SETUP.md"
        self.assertTrue(using_skill_path.exists())
        self.assertTrue(skill_path.exists())
        self.assertTrue(setup_path.exists())
        canonical_using_skill = (self.package_root.parent.parent / "skills" / "using-aitp" / "SKILL.md").read_text(encoding="utf-8")
        canonical_runtime_skill = (self.package_root.parent.parent / "skills" / "aitp-runtime" / "SKILL.md").read_text(encoding="utf-8")
        using_skill_text = using_skill_path.read_text(encoding="utf-8")
        skill_text = skill_path.read_text(encoding="utf-8")
        self.assertEqual(using_skill_text, canonical_using_skill)
        self.assertEqual(skill_text, canonical_runtime_skill)
        self.assertNotIn("aitp-codex", using_skill_text)
        self.assertNotIn("aitp-codex", skill_text)
        self.assertIn("codex mcp add aitp", setup_path.read_text(encoding="utf-8"))
        self.assertFalse(any(item["kind"] == "wrapper" for item in result["installed"]))
        self.assertFalse((codex_target / ".agents" / "bin").exists())

        openclaw_target = self.root / "openclaw-workspace"
        result = self.service.install_agent(
            agent="openclaw",
            scope="project",
            target_root=str(openclaw_target),
            install_mcp=False,
        )
        installed_paths = {Path(item["path"]).name for item in result["installed"]}
        self.assertIn("SKILL.md", installed_paths)
        self.assertIn("AITP_MCP_SETUP.md", installed_paths)
        openclaw_using_skill_path = openclaw_target / "skills" / "using-aitp" / "SKILL.md"
        openclaw_skill_path = openclaw_target / "skills" / "aitp-runtime" / "SKILL.md"
        openclaw_setup_path = openclaw_target / "skills" / "aitp-runtime" / "AITP_MCP_SETUP.md"
        self.assertTrue(openclaw_using_skill_path.exists())
        self.assertTrue(openclaw_skill_path.exists())
        self.assertTrue(openclaw_setup_path.exists())
        self.assertIn("Use this skill to decide whether the current task must be governed by AITP", openclaw_using_skill_path.read_text(encoding="utf-8"))
        self.assertIn("AITP Runtime For OpenClaw", openclaw_skill_path.read_text(encoding="utf-8"))
        self.assertIn("mcporter config add aitp", openclaw_setup_path.read_text(encoding="utf-8"))
        self.assertFalse((openclaw_target / "SKILL.md").exists())

        opencode_target = self.root / "opencode-workspace"
        result = self.service.install_agent(
            agent="opencode",
            scope="user",
            target_root=str(opencode_target),
        )
        installed_paths = {Path(item["path"]).name for item in result["installed"]}
        opencode_using_skill_path = opencode_target / ".opencode" / "skills" / "using-aitp" / "SKILL.md"
        opencode_skill_path = opencode_target / ".opencode" / "skills" / "aitp-runtime" / "SKILL.md"
        opencode_setup_path = opencode_target / ".opencode" / "skills" / "aitp-runtime" / "AITP_MCP_SETUP.md"
        opencode_plugin_path = opencode_target / ".opencode" / "plugins" / "aitp.js"
        canonical_using_skill = (self.package_root.parent.parent / "skills" / "using-aitp" / "SKILL.md").read_text(encoding="utf-8")
        canonical_runtime_skill = (self.package_root.parent.parent / "skills" / "aitp-runtime" / "SKILL.md").read_text(encoding="utf-8")
        canonical_opencode_plugin = (self.package_root.parent.parent / ".opencode" / "plugins" / "aitp.js").read_text(encoding="utf-8")
        self.assertIn("aitp.js", installed_paths)
        self.assertIn("AITP_MCP_CONFIG.json", installed_paths)
        self.assertTrue(opencode_using_skill_path.exists())
        self.assertTrue(opencode_skill_path.exists())
        self.assertTrue(opencode_setup_path.exists())
        self.assertTrue(opencode_plugin_path.exists())
        self.assertEqual(opencode_using_skill_path.read_text(encoding="utf-8"), canonical_using_skill)
        self.assertEqual(opencode_skill_path.read_text(encoding="utf-8"), canonical_runtime_skill)
        self.assertEqual(opencode_plugin_path.read_text(encoding="utf-8"), canonical_opencode_plugin)
        self.assertFalse((opencode_target / ".opencode" / "commands").exists())

        claude_target = self.root / "claude-workspace"
        result = self.service.install_agent(
            agent="claude-code",
            scope="user",
            target_root=str(claude_target),
        )
        installed_paths = {Path(item["path"]).name for item in result["installed"]}
        self.assertIn("SKILL.md", installed_paths)
        self.assertIn("AITP_MCP_SETUP.md", installed_paths)
        self.assertIn("session-start", installed_paths)
        self.assertIn("run-hook.cmd", installed_paths)
        self.assertIn("hooks.json", installed_paths)
        self.assertIn("settings.json", installed_paths)
        claude_using_skill_path = claude_target / ".claude" / "skills" / "using-aitp" / "SKILL.md"
        claude_skill_path = claude_target / ".claude" / "skills" / "aitp-runtime" / "SKILL.md"
        claude_hook_path = claude_target / ".claude" / "hooks" / "session-start"
        claude_run_hook_path = claude_target / ".claude" / "hooks" / "run-hook.cmd"
        claude_hooks_json_path = claude_target / ".claude" / "hooks" / "hooks.json"
        claude_settings_path = claude_target / ".claude" / "settings.json"
        canonical_claude_hook = (self.package_root.parent.parent / "hooks" / "session-start").read_text(encoding="utf-8")
        canonical_claude_run_hook = (self.package_root.parent.parent / "hooks" / "run-hook.cmd").read_text(encoding="utf-8")
        canonical_claude_hooks_json = (self.package_root.parent.parent / "hooks" / "hooks.json").read_text(encoding="utf-8")
        self.assertTrue(claude_using_skill_path.exists())
        self.assertTrue(claude_skill_path.exists())
        self.assertTrue(claude_hook_path.exists())
        self.assertTrue(claude_run_hook_path.exists())
        self.assertTrue(claude_hooks_json_path.exists())
        self.assertTrue(claude_settings_path.exists())
        self.assertEqual(claude_using_skill_path.read_text(encoding="utf-8"), canonical_using_skill)
        self.assertEqual(claude_skill_path.read_text(encoding="utf-8"), canonical_runtime_skill)
        self.assertEqual(claude_hook_path.read_text(encoding="utf-8"), canonical_claude_hook)
        self.assertEqual(claude_run_hook_path.read_text(encoding="utf-8"), canonical_claude_run_hook)
        self.assertEqual(claude_hooks_json_path.read_text(encoding="utf-8"), canonical_claude_hooks_json)
        settings_payload = json.loads(claude_settings_path.read_text(encoding="utf-8"))
        self.assertIn("SessionStart", settings_payload["hooks"])
        self.assertFalse((claude_target / ".claude" / "commands").exists())
