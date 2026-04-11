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


class _TopicCreationStubService(AITPService):
    def orchestrate(self, **kwargs):  # noqa: ANN003
        topic_slug = kwargs.get("topic_slug") or "demo-topic"
        if not kwargs.get("topic_slug"):
            topic = str(kwargs.get("topic") or "demo-topic")
            topic_slug = topic.lower().replace(" ", "-")
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "latest_run_id": "2026-04-04-bootstrap",
                    "resume_stage": "L1",
                    "summary": f"New topic {topic_slug}",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return {
            "topic_slug": topic_slug,
            "runtime_root": str(runtime_root),
            "topic_state": json.loads((runtime_root / "topic_state.json").read_text(encoding="utf-8")),
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
        self.service = AITPService(kernel_root=self.kernel_root, repo_root=self.repo_root)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _make_opencode_status(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "config_path": "C:/Users/demo/AppData/Roaming/opencode/opencode.json",
            "config_exists": True,
            "config_parse_ok": True,
            "plugin_list_present": True,
            "plugin_list_valid": True,
            "plugins": ["aitp@git+https://github.com/bhjia-phys/AITP-Research-Protocol.git"],
            "canonical_plugin_entry": "aitp@git+https://github.com/bhjia-phys/AITP-Research-Protocol.git",
            "canonical_plugin_entry_present": True,
            "aitp_plugin_entries": ["aitp@git+https://github.com/bhjia-phys/AITP-Research-Protocol.git"],
            "noncanonical_aitp_plugin_entries": [],
            "workspace_plugin_path": "",
            "workspace_using_skill_path": "",
            "workspace_runtime_skill_path": "",
            "workspace_plugin_present": False,
            "workspace_using_skill_present": False,
            "workspace_runtime_skill_present": False,
            "workspace_plugin_matches_canonical": False,
            "workspace_using_skill_matches_canonical": False,
            "workspace_runtime_skill_matches_canonical": False,
        }
        payload.update(overrides)
        return payload

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

    def _prepare_l2_graph_kernel(self) -> None:
        shutil.copyfile(
            self.package_root / "canonical" / "canonical-unit.schema.json",
            self.kernel_root / "canonical" / "canonical-unit.schema.json",
        )
        shutil.copyfile(
            self.package_root / "canonical" / "retrieval_profiles.json",
            self.kernel_root / "canonical" / "retrieval_profiles.json",
        )

    def _write_available_projection(
        self,
        *,
        topic_slug: str,
        lane: str,
        summary: str,
        required_first_routes: list[str] | None = None,
    ) -> None:
        runtime_root = self._write_runtime_state(topic_slug=topic_slug, run_id="run-001")
        (runtime_root / "topic_synopsis.json").write_text(
            json.dumps(
                {
                    "id": f"topic_synopsis:{topic_slug}",
                    "topic_slug": topic_slug,
                    "title": topic_slug.replace("-", " ").title(),
                    "question": "Demo question",
                    "lane": lane,
                    "load_profile": "light",
                    "status": "active",
                    "runtime_focus": {
                        "summary": summary,
                        "why_this_topic_is_here": summary,
                        "resume_stage": "L3",
                        "last_materialized_stage": "L3",
                        "next_action_id": "action:demo:01",
                        "next_action_type": "inspect_runtime",
                        "next_action_summary": summary,
                        "human_need_status": "none",
                        "human_need_kind": "none",
                        "human_need_summary": "No active human checkpoint is currently blocking the bounded loop.",
                        "blocker_summary": [],
                        "last_evidence_kind": "none",
                        "last_evidence_summary": "No durable evidence-return artifact is currently recorded for this topic.",
                        "dependency_status": "clear",
                        "dependency_summary": "No active topic dependencies.",
                        "promotion_status": "not_ready",
                    },
                    "truth_sources": {
                        "topic_state_path": f"runtime/topics/{topic_slug}/topic_state.json",
                        "research_question_contract_path": f"runtime/topics/{topic_slug}/research_question.contract.json",
                        "next_action_surface_path": f"runtime/topics/{topic_slug}/action_queue.jsonl",
                        "human_need_surface_path": None,
                        "dependency_registry_path": "runtime/active_topics.json",
                        "promotion_readiness_path": f"runtime/topics/{topic_slug}/promotion_readiness.json",
                        "promotion_gate_path": None,
                    },
                    "next_action_summary": summary,
                    "open_gap_summary": "No explicit gap packet is currently open.",
                    "pending_decision_count": 0,
                    "knowledge_packet_paths": [],
                    "updated_at": "2026-04-04T10:00:00+08:00",
                    "updated_by": "test",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "topic_skill_projection.active.json").write_text(
            json.dumps(
                {
                    "id": f"topic_skill_projection:{topic_slug}",
                    "topic_slug": topic_slug,
                    "source_topic_slug": topic_slug,
                    "run_id": "run-001",
                    "title": f"{topic_slug} projection",
                    "summary": summary,
                    "lane": lane,
                    "status": "available",
                    "status_reason": "Projection is available.",
                    "candidate_id": f"candidate:{topic_slug}-projection",
                    "intended_l2_target": f"topic_skill_projection:{topic_slug}",
                    "entry_signals": [f"lane={lane}"],
                    "required_first_reads": [f"runtime/topics/{topic_slug}/research_question.contract.md"],
                    "required_first_routes": required_first_routes or [],
                    "benchmark_first_rules": [],
                    "operator_checkpoint_rules": [],
                    "operation_trust_requirements": [],
                    "strategy_guidance": [],
                    "forbidden_proxies": [],
                    "derived_from_artifacts": [],
                    "updated_at": "2026-04-04T10:00:00+08:00",
                    "updated_by": "test",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "topic_skill_projection.active.md").write_text(
            f"# {topic_slug} projection\n",
            encoding="utf-8",
        )

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

    def _write_theoretical_physics_brain_backend_card(self, *, allows_auto: bool = True) -> Path:
        backends_root = self.kernel_root / "canonical" / "backends"
        backends_root.mkdir(parents=True, exist_ok=True)
        card_path = backends_root / "theoretical-physics-brain.json"
        card_payload = {
            "$schema": "../../schemas/l2-backend.schema.json",
            "backend_id": "backend:theoretical-physics-brain",
            "title": "Theoretical Physics Brain",
            "backend_type": "human_note_library",
            "status": "active",
            "root_paths": ["__THEORETICAL_PHYSICS_BRAIN_ROOT__"],
            "purpose": ["Test backend card for paired-backend audit flows."],
            "artifact_granularity": "One note at a time.",
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
            "retrieval_hints": ["Keep aligned with backend:theoretical-physics-knowledge-network."],
            "notes": "Test paired with backend:theoretical-physics-knowledge-network.",
        }
        card_path.write_text(json.dumps(card_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        index_path = backends_root / "backend_index.jsonl"
        rows = []
        if index_path.exists():
            rows = [json.loads(line) for line in index_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        rows = [row for row in rows if row.get("backend_id") != "backend:theoretical-physics-brain"]
        rows.append(
            {
                "backend_id": "backend:theoretical-physics-brain",
                "title": "Theoretical Physics Brain",
                "backend_type": "human_note_library",
                "status": "active",
                "card_path": "canonical/backends/theoretical-physics-brain.json",
                "canonical_targets": card_payload["canonical_targets"],
                "allows_auto_canonical_promotion": allows_auto,
            }
        )
        index_path.write_text(
            "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in rows),
            encoding="utf-8",
        )
        return card_path

    def _write_theoretical_physics_pairing_docs(self) -> None:
        backends_root = self.kernel_root / "canonical" / "backends"
        backends_root.mkdir(parents=True, exist_ok=True)
        (backends_root / "THEORETICAL_PHYSICS_PAIRED_BACKEND_CONTRACT.md").write_text(
            "# Pair contract\n\noperator-primary\nmachine-primary\nno silent hierarchy\n",
            encoding="utf-8",
        )
        (backends_root / "THEORETICAL_PHYSICS_BACKEND_PAIRING.md").write_text(
            "# Pairing\n\nbackend debt\ndrift audit\ndownstream L2\n",
            encoding="utf-8",
        )
        canonical_root = self.kernel_root / "canonical"
        canonical_root.mkdir(parents=True, exist_ok=True)
        (canonical_root / "L2_PAIRED_BACKEND_MAINTENANCE_PROTOCOL.md").write_text(
            "# Maintenance\n\ndrift audit\nbackend debt\nrebuild\n",
            encoding="utf-8",
        )

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
        self.assertEqual(payload["research_judgment"]["status"], "steady")
        self.assertEqual(payload["research_judgment"]["momentum"]["status"], "queued")
        self.assertEqual(payload["decision_surface"]["momentum_status"], "queued")
        self.assertEqual(payload["decision_surface"]["stuckness_status"], "none")
        self.assertEqual(payload["decision_surface"]["surprise_status"], "none")
        self.assertEqual(payload["topic_skill_projection"]["status"], "not_applicable")
        self.assertEqual(payload["topic_completion"]["status"], "not_assessed")
        self.assertEqual(payload["lean_bridge"]["status"], "empty")
        self.assertEqual(payload["validation_review_bundle"]["status"], "not_materialized")
        self.assertEqual(payload["validation_review_bundle"]["primary_review_kind"], "validation_contract")
        self.assertEqual(
            payload["topic_synopsis"]["runtime_focus"]["summary"],
            "Stage `L3`; next `Inspect the current runtime state.`; human need `none`; last evidence `none`.",
        )
        self.assertEqual(
            payload["topic_synopsis"]["truth_sources"]["topic_state_path"],
            "runtime/topics/demo-topic/topic_state.json",
        )
        self.assertEqual(
            payload["topic_synopsis"]["truth_sources"]["next_action_surface_path"],
            "runtime/topics/demo-topic/action_queue_contract.generated.json",
        )
        self.assertEqual(payload["minimal_execution_brief"]["selected_action_id"], "action:demo-topic:01")
        self.assertEqual(
            payload["minimal_execution_brief"]["selected_action_summary"],
            payload["topic_synopsis"]["runtime_focus"]["next_action_summary"],
        )
        self.assertEqual(payload["minimal_execution_brief"]["queue_source"], "heuristic")
        self.assertEqual(payload["load_profile"], "light")
        self.assertEqual(len(payload["must_read_now"]), 2)
        self.assertEqual(payload["must_read_now"][0]["path"], "runtime/topics/demo-topic/topic_dashboard.md")
        self.assertEqual(payload["must_read_now"][1]["path"], "runtime/topics/demo-topic/research_question.contract.md")
        self.assertEqual(payload["minimal_execution_brief"]["open_next"], "runtime/topics/demo-topic/topic_dashboard.md")
        self.assertFalse(any(row["path"].endswith("operator_console.md") for row in payload["must_read_now"]))
        self.assertFalse(any(row["path"] == "RESEARCH_EXECUTION_GUARDRAILS.md" for row in payload["must_read_now"]))
        self.assertTrue(
            any(
                row["path"] == "runtime/topics/demo-topic/topic_synopsis.json"
                and row["trigger"] == "runtime_truth_audit"
                for row in payload["may_defer_until_trigger"]
            )
        )
        self.assertEqual(payload["escalation_triggers"][1]["trigger"], "promotion_intent")
        self.assertTrue(any(row["trigger"] == "decision_override_present" for row in payload["escalation_triggers"]))
        self.assertTrue(any(row["trigger"] == "runtime_truth_audit" for row in payload["escalation_triggers"]))
        self.assertTrue(any(row["slice"] == "current_execution_lane" for row in payload["recommended_protocol_slices"]))
        self.assertTrue(any(row["slice"] == "runtime_truth_details" for row in payload["recommended_protocol_slices"]))
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
        self.assertIn("## Validation review bundle", note_text)
        self.assertIn("## Promotion readiness", note_text)
        self.assertIn("## Open gap summary", note_text)
        self.assertIn("## Strategy memory", note_text)
        self.assertIn("## Research judgment", note_text)
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

    def test_record_collaborator_memory_writes_runtime_ledger_and_note(self) -> None:
        payload = self.service.record_collaborator_memory(
            memory_kind="preference",
            summary="Prefer bounded operator-algebra routes before broader numerical detours.",
            details="This is collaborator-side route taste, not canonical scientific truth.",
            topic_slug="demo-topic",
            run_id="2026-04-09-demo",
            tags=["operator-algebra", "bounded-route"],
            related_topic_slugs=["demo-topic", "operator-algebra-notes"],
            updated_by="human",
        )

        path = Path(payload["collaborator_memory_path"])
        note_path = Path(payload["collaborator_memory_note_path"])
        self.assertTrue(path.exists())
        self.assertTrue(note_path.exists())
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["memory_kind"], "preference")
        self.assertEqual(rows[0]["topic_slug"], "demo-topic")
        self.assertEqual(rows[0]["storage_layer"], "runtime")
        self.assertEqual(rows[0]["canonical_status"], "separate_from_scientific_memory")
        note_text = note_path.read_text(encoding="utf-8")
        self.assertIn("not canonical scientific memory", note_text)
        self.assertIn("operator-algebra", note_text)

    def test_get_collaborator_memory_filters_by_topic_and_stays_runtime_side(self) -> None:
        self.service.record_collaborator_memory(
            memory_kind="preference",
            summary="Prefer the theorem-facing route for this topic family.",
            topic_slug="demo-topic",
            tags=["formal-theory"],
            updated_by="human",
        )
        self.service.record_collaborator_memory(
            memory_kind="trajectory",
            summary="The benchmark topic already consumed the broad numerical detour.",
            topic_slug="other-topic",
            related_topic_slugs=["demo-topic"],
            tags=["benchmark"],
            updated_by="human",
        )

        payload = self.service.get_collaborator_memory(topic_slug="demo-topic", limit=5)

        self.assertEqual(payload["status"], "available")
        self.assertEqual(payload["memory_domain"], "collaborator")
        self.assertEqual(payload["storage_layer"], "runtime")
        self.assertEqual(payload["canonical_status"], "separate_from_scientific_memory")
        self.assertEqual(payload["matching_count"], 2)
        self.assertEqual(len(payload["entries"]), 2)
        self.assertTrue(any(row["topic_slug"] == "demo-topic" for row in payload["entries"]))
        self.assertTrue(any("demo-topic" in row["related_topic_slugs"] for row in payload["entries"]))

    def test_topic_status_surfaces_collaborator_profile(self) -> None:
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
                    "human_request": "Continue the theorem-facing route.",
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
                    "summary": "Continue the theorem-facing proof review.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

        self.service.record_collaborator_memory(
            memory_kind="preference",
            summary="Prefer theorem-facing routes before broad numerical detours.",
            topic_slug="demo-topic",
            tags=["formal-theory"],
            updated_by="human",
        )
        self.service.record_collaborator_memory(
            memory_kind="working_style",
            summary="Keep the active route narrow and operator-visible.",
            topic_slug="demo-topic",
            tags=["bounded-route"],
            updated_by="human",
        )
        self.service.record_collaborator_memory(
            memory_kind="trajectory",
            summary="The last session narrowed the topic to the theorem-facing route.",
            topic_slug="demo-topic",
            related_topic_slugs=["operator-algebra-notes"],
            updated_by="human",
        )

        payload = self.service.topic_status(topic_slug="demo-topic")

        self.assertEqual(payload["collaborator_profile"]["status"], "available")
        self.assertEqual(payload["collaborator_profile"]["preference_count"], 1)
        self.assertEqual(payload["collaborator_profile"]["working_style_count"], 1)
        self.assertEqual(payload["collaborator_profile"]["trajectory_count"], 1)
        self.assertIn("theorem-facing", payload["collaborator_profile"]["summary"])
        self.assertTrue((self.kernel_root / payload["collaborator_profile"]["path"]).exists())
        self.assertTrue((self.kernel_root / payload["collaborator_profile"]["note_path"]).exists())
        self.assertTrue(any(row["path"].endswith("collaborator_profile.active.md") for row in payload["must_read_now"]))

    def test_topic_status_surfaces_research_trajectory(self) -> None:
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
                    "human_request": "Continue the theorem-facing route.",
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
                    "summary": "Continue the theorem-facing proof review.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        sibling_runtime_root = self.kernel_root / "runtime" / "topics" / "operator-algebra-notes"
        sibling_runtime_root.mkdir(parents=True, exist_ok=True)
        (sibling_runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "operator-algebra-notes",
                    "latest_run_id": "2026-03-02-notes",
                    "resume_stage": "L1",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.kernel_root / "runtime" / "topic_index.jsonl").write_text(
            "\n".join(
                [
                    json.dumps(
                        {"topic_slug": "operator-algebra-notes", "updated_at": "2026-04-10T08:00:00+08:00"},
                        ensure_ascii=True,
                    ),
                    json.dumps(
                        {"topic_slug": "demo-topic", "updated_at": "2026-04-11T08:00:00+08:00"},
                        ensure_ascii=True,
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        self.service.record_collaborator_memory(
            memory_kind="trajectory",
            summary="The last session narrowed the topic to the theorem-facing route.",
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
            related_topic_slugs=["operator-algebra-notes"],
            updated_by="human",
        )
        self.service.record_collaborator_memory(
            memory_kind="trajectory",
            summary="Earlier notes already ruled out the broad numerical detour.",
            topic_slug="operator-algebra-notes",
            run_id="2026-03-02-notes",
            related_topic_slugs=["demo-topic"],
            updated_by="human",
        )

        payload = self.service.topic_status(topic_slug="demo-topic")

        self.assertEqual(payload["research_trajectory"]["status"], "available")
        self.assertEqual(payload["research_trajectory"]["trajectory_count"], 2)
        self.assertEqual(payload["research_trajectory"]["latest_run_id"], "2026-03-13-demo")
        self.assertIn("theorem-facing", payload["research_trajectory"]["summary"])
        self.assertIn("operator-algebra-notes", payload["research_trajectory"]["recent_related_topic_slugs"])
        self.assertTrue((self.kernel_root / payload["research_trajectory"]["path"]).exists())
        self.assertTrue((self.kernel_root / payload["research_trajectory"]["note_path"]).exists())
        self.assertTrue(any(row["path"].endswith("research_trajectory.active.md") for row in payload["must_read_now"]))

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

    def test_topic_status_surfaces_mode_learning(self) -> None:
        runtime_root = self._write_runtime_state()
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "2026-03-13-demo",
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
                    "human_request": "Resume the bounded benchmark route.",
                    "action_queue_surface": {
                        "queue_source": "heuristic",
                    },
                    "decision_surface": {
                        "decision_mode": "continue_unfinished",
                        "decision_source": "heuristic",
                        "decision_contract_status": "missing",
                        "control_note_path": None,
                        "selected_action_id": "action:demo-topic:bench",
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
                    "action_id": "action:demo-topic:bench",
                    "status": "pending",
                    "action_type": "benchmark_review",
                    "summary": "Run the benchmark-first bounded route before broad theory detours.",
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
            strategy_type="resource_plan",
            summary="Prefer the benchmark-first route when the bounded task is still measurement-heavy.",
            outcome="helpful",
            confidence=0.88,
            lane="code_method",
            reuse_conditions=["benchmark-first", "measurement-heavy"],
            updated_by="aitp-cli",
        )
        self.service.record_strategy_memory(
            topic_slug="demo-topic",
            run_id="2026-03-10-demo",
            strategy_type="scope_control",
            summary="Avoid switching into theorem-first derivation before the benchmark baseline stabilizes.",
            outcome="harmful",
            confidence=0.77,
            lane="formal_theory",
            do_not_apply_when=["benchmark baseline is still unstable"],
            updated_by="aitp-cli",
        )

        payload = self.service.topic_status(topic_slug="demo-topic")

        self.assertEqual(payload["mode_learning"]["status"], "available")
        self.assertEqual(payload["mode_learning"]["preferred_lane"], "code_method")
        self.assertEqual(payload["mode_learning"]["helpful_pattern_count"], 1)
        self.assertEqual(payload["mode_learning"]["harmful_pattern_count"], 1)
        self.assertIn("benchmark-first route", payload["mode_learning"]["summary"])
        self.assertTrue((self.kernel_root / payload["mode_learning"]["path"]).exists())
        self.assertTrue((self.kernel_root / payload["mode_learning"]["note_path"]).exists())
        self.assertTrue(any(row["path"].endswith("mode_learning.active.md") for row in payload["must_read_now"]))

    def test_topic_status_surfaces_research_judgment_signals(self) -> None:
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
                    "human_request": "Continue the derivation review but stay honest about what is stuck.",
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
        self.service.record_collaborator_memory(
            memory_kind="stuckness",
            summary="The derivation keeps stalling at the sign-convention merge point.",
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
            tags=["formal-theory"],
            updated_by="human",
        )
        self.service.record_collaborator_memory(
            memory_kind="surprise",
            summary="The weak-coupling route unexpectedly preserved the target symmetry.",
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
            tags=["analytical"],
            updated_by="human",
        )

        payload = self.service.topic_status(topic_slug="demo-topic")

        self.assertEqual(payload["research_judgment"]["status"], "signals_active")
        self.assertEqual(payload["research_judgment"]["momentum"]["status"], "queued")
        self.assertEqual(payload["research_judgment"]["stuckness"]["status"], "active")
        self.assertEqual(payload["research_judgment"]["surprise"]["status"], "active")
        self.assertEqual(payload["topic_synopsis"]["runtime_focus"]["momentum_status"], "queued")
        self.assertEqual(payload["topic_synopsis"]["runtime_focus"]["stuckness_status"], "active")
        self.assertEqual(payload["topic_synopsis"]["runtime_focus"]["surprise_status"], "active")
        self.assertIn("stuckness `active`", payload["topic_synopsis"]["runtime_focus"]["judgment_summary"])
        self.assertTrue((self.kernel_root / payload["research_judgment"]["path"]).exists())
        self.assertTrue((self.kernel_root / payload["research_judgment"]["note_path"]).exists())
        self.assertTrue(any(row["path"].endswith("research_judgment.active.md") for row in payload["must_read_now"]))

    def test_topic_status_surfaces_research_taste(self) -> None:
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
                    "human_request": "Continue the bounded theorem-facing route and preserve the useful intuition.",
                    "action_queue_surface": {
                        "queue_source": "heuristic",
                    },
                    "decision_surface": {
                        "decision_mode": "continue_unfinished",
                        "decision_source": "heuristic",
                        "decision_contract_status": "missing",
                        "control_note_path": None,
                        "selected_action_id": "action:demo-topic:taste",
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
                    "action_id": "action:demo-topic:taste",
                    "status": "pending",
                    "action_type": "proof_review",
                    "summary": "Keep the theorem-facing route bounded and source-backed.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

        self.service.record_research_taste(
            topic_slug="demo-topic",
            taste_kind="formalism",
            summary="Prefer operator-algebra notation before widening the route.",
            formalisms=["operator_algebra"],
            updated_by="human",
        )
        self.service.record_research_taste(
            topic_slug="demo-topic",
            taste_kind="intuition",
            summary="Keep the bounded weak-coupling picture as intuition, not as proof.",
            updated_by="human",
        )
        self.service.record_collaborator_memory(
            memory_kind="surprise",
            summary="The bounded route unexpectedly preserved the target symmetry.",
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
            tags=["analytical"],
            updated_by="human",
        )

        payload = self.service.topic_status(topic_slug="demo-topic")

        self.assertEqual(payload["research_taste"]["status"], "available")
        self.assertEqual(payload["research_taste"]["formalism_preferences"], ["operator_algebra"])
        self.assertEqual(payload["research_taste"]["intuition_signal_count"], 1)
        self.assertEqual(payload["research_taste"]["surprise_handling"]["status"], "active")
        self.assertTrue((self.kernel_root / payload["research_taste"]["path"]).exists())
        self.assertTrue((self.kernel_root / payload["research_taste"]["note_path"]).exists())
        self.assertTrue(any(row["path"].endswith("research_taste.active.md") for row in payload["must_read_now"]))

    def test_topic_status_surfaces_scratchpad(self) -> None:
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
                    "human_request": "Keep the failed route visible and continue the bounded proof review.",
                    "action_queue_surface": {
                        "queue_source": "heuristic",
                    },
                    "decision_surface": {
                        "decision_mode": "continue_unfinished",
                        "decision_source": "heuristic",
                        "decision_contract_status": "missing",
                        "control_note_path": None,
                        "selected_action_id": "action:demo-topic:scratch",
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
                    "action_id": "action:demo-topic:scratch",
                    "status": "pending",
                    "action_type": "proof_review",
                    "summary": "Continue the bounded proof review after the failed portability route.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

        self.service.record_scratch_note(
            topic_slug="demo-topic",
            entry_kind="route_comparison",
            summary="Compare the theorem-facing and benchmark-first routes before retrying the proof.",
            updated_by="human",
        )
        self.service.record_negative_result(
            topic_slug="demo-topic",
            summary="The portability extrapolation failed outside the bounded regime.",
            failure_kind="regime_mismatch",
            updated_by="human",
        )

        payload = self.service.topic_status(topic_slug="demo-topic")

        self.assertEqual(payload["scratchpad"]["status"], "active")
        self.assertEqual(payload["scratchpad"]["entry_count"], 2)
        self.assertEqual(payload["scratchpad"]["negative_result_count"], 1)
        self.assertEqual(payload["scratchpad"]["route_comparison_count"], 1)
        self.assertTrue((self.kernel_root / payload["scratchpad"]["path"]).exists())
        self.assertTrue((self.kernel_root / payload["scratchpad"]["note_path"]).exists())
        self.assertTrue(any(row["path"].endswith("scratchpad.active.md") for row in payload["must_read_now"]))

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
        self.assertTrue(Path(payload["validation_review_bundle_path"]).exists())
        self.assertTrue(Path(payload["validation_review_bundle_note_path"]).exists())
        self.assertTrue(Path(payload["research_judgment_path"]).exists())
        self.assertTrue(Path(payload["research_judgment_note_path"]).exists())
        self.assertTrue(Path(payload["gap_map_path"]).exists())
        self.assertTrue(Path(payload["topic_completion_path"]).exists())
        self.assertTrue(Path(payload["lean_bridge_path"]).exists())
        self.assertEqual(payload["research_question_contract"]["research_mode"], "formal_derivation")
        self.assertTrue(payload["research_question_contract"]["source_basis_refs"])
        self.assertTrue(payload["research_question_contract"]["interpretation_focus"])
        self.assertTrue(payload["research_question_contract"]["open_ambiguities"])
        self.assertEqual(payload["validation_contract"]["validation_mode"], "formal")
        self.assertTrue(payload["validation_contract"]["primary_review_bundle_path"].endswith("validation_review_bundle.active.json"))
        self.assertEqual(payload["idea_packet"]["status"], "approved_for_execution")
        self.assertEqual(payload["operator_checkpoint"]["status"], "cancelled")
        self.assertIn("topic_state_explainability", payload)
        self.assertEqual(payload["validation_contract"]["status"], "deferred")
        self.assertTrue(payload["open_gap_summary"]["requires_l0_return"])
        dashboard_text = Path(payload["topic_dashboard_path"]).read_text(encoding="utf-8")
        review_text = Path(payload["validation_review_bundle_note_path"]).read_text(encoding="utf-8")
        gap_text = Path(payload["gap_map_path"]).read_text(encoding="utf-8")
        self.assertIn("Idea packet", dashboard_text)
        self.assertIn("operator_checkpoint.active.md", dashboard_text)
        self.assertIn("## Validation review bundle", dashboard_text)
        self.assertIn("## Last evidence return", dashboard_text)
        self.assertIn("## Active human need", dashboard_text)
        self.assertIn("return to L0", dashboard_text)
        self.assertIn("Primary L4 review surface", review_text)
        self.assertIn("return to L0", gap_text)

    def test_ensure_topic_shell_surfaces_uses_analytical_validation_for_theory_synthesis(self) -> None:
        runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "run-001",
                    "resume_stage": "L1",
                    "research_mode": "theory_synthesis",
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
                    "human_request": "Synthesize the cross-paper theory route.",
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

        self.assertEqual(payload["research_question_contract"]["research_mode"], "theory_synthesis")
        self.assertEqual(payload["validation_contract"]["validation_mode"], "analytical")

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

    def test_ensure_topic_shell_surfaces_persists_source_backed_l1_intake(self) -> None:
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
                    "human_request": "Recover the bounded theorem route from the thesis source.",
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
                    "action_type": "proof_review",
                    "summary": "Extract the first bounded proof obligation from the thesis source.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

        source_root = self.kernel_root / "source-layer" / "topics" / "demo-topic"
        source_root.mkdir(parents=True, exist_ok=True)
        thesis_path = self.root / "inputs" / "demo-source.tex"
        thesis_path.parent.mkdir(parents=True, exist_ok=True)
        thesis_path.write_text(
            "\\section{Bounded closure}\n"
            "We assume fractional occupations remain bounded in the weak coupling limit at zero temperature.\n"
            "This gives the first theorem-facing closure target.\n",
            encoding="utf-8",
        )
        (source_root / "source_index.jsonl").write_text(
            json.dumps(
                {
                    "source_id": "thesis:demo-source",
                    "source_type": "thesis",
                    "title": "Bounded closure thesis",
                    "summary": (
                        "We assume fractional occupations remain bounded in the weak coupling limit at zero temperature. "
                        "This gives the first theorem-facing closure target."
                    ),
                    "provenance": {
                        "absolute_path": str(thesis_path),
                    },
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        snapshot_root = source_root / "sources" / "thesis-demo-source"
        snapshot_root.mkdir(parents=True, exist_ok=True)
        (snapshot_root / "snapshot.md").write_text(
            "# Snapshot\n\n"
            "## Preview\n"
            "We assume fractional occupations remain bounded in the weak coupling limit at zero temperature.\n",
            encoding="utf-8",
        )

        payload = self.service.ensure_topic_shell_surfaces(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )

        l1_source_intake = payload["research_question_contract"]["l1_source_intake"]
        self.assertEqual(l1_source_intake["source_count"], 1)
        self.assertEqual(l1_source_intake["assumption_rows"][0]["source_id"], "thesis:demo-source")
        self.assertEqual(l1_source_intake["assumption_rows"][0]["reading_depth"], "full_read")
        self.assertTrue(any(row["regime"] == "weak coupling" for row in l1_source_intake["regime_rows"]))
        self.assertTrue(any(row["regime"] == "zero temperature" for row in l1_source_intake["regime_rows"]))
        self.assertEqual(l1_source_intake["method_specificity_rows"][0]["method_family"], "formal_derivation")
        self.assertEqual(l1_source_intake["method_specificity_rows"][0]["specificity_tier"], "high")
        research_note = Path(payload["research_question_contract_note_path"]).read_text(encoding="utf-8")
        self.assertIn("## L1 source intake", research_note)
        self.assertIn("## Source-backed assumptions", research_note)
        self.assertIn("## Reading depth", research_note)
        self.assertIn("## Method specificity", research_note)

    def test_ensure_topic_shell_surfaces_persists_l1_conflict_candidates(self) -> None:
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
                    "human_request": "Resolve the conflicting bounded derivation assumptions.",
                    "decision_surface": {
                        "selected_action_id": "action:demo-topic:conflict",
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
                    "action_id": "action:demo-topic:conflict",
                    "status": "pending",
                    "action_type": "manual_followup",
                    "summary": "Adjudicate the contradiction and notation mismatch between the active sources.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

        source_root = self.kernel_root / "source-layer" / "topics" / "demo-topic"
        source_root.mkdir(parents=True, exist_ok=True)
        source_rows = [
            {
                "source_id": "paper:weak-coupling",
                "source_type": "paper",
                "title": "Weak-coupling closure",
                "summary": (
                    "We assume the closure remains controlled in the weak coupling limit. "
                    "H denotes the diagonal generator."
                ),
                "provenance": {
                    "abs_url": "https://example.org/weak",
                },
            },
            {
                "source_id": "paper:strong-coupling",
                "source_type": "paper",
                "title": "Strong-coupling closure",
                "summary": (
                    "We assume the same closure target only in the strong coupling limit. "
                    "K denotes the diagonal generator."
                ),
                "provenance": {
                    "abs_url": "https://example.org/strong",
                },
            },
        ]
        (source_root / "source_index.jsonl").write_text(
            "\n".join(json.dumps(row, ensure_ascii=True) for row in source_rows) + "\n",
            encoding="utf-8",
        )

        payload = self.service.ensure_topic_shell_surfaces(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )

        l1_source_intake = payload["research_question_contract"]["l1_source_intake"]
        self.assertEqual(len(l1_source_intake["notation_rows"]), 2)
        self.assertEqual(len(l1_source_intake["contradiction_candidates"]), 1)
        self.assertEqual(len(l1_source_intake["notation_tension_candidates"]), 1)
        self.assertEqual(len(l1_source_intake["method_specificity_rows"]), 2)
        self.assertEqual(
            l1_source_intake["contradiction_candidates"][0]["detail"],
            "strong coupling vs weak coupling",
        )
        self.assertEqual(
            l1_source_intake["notation_tension_candidates"][0]["meaning"],
            "the diagonal generator",
        )
        self.assertIn(
            "Contradiction candidate: strong coupling vs weak coupling",
            json.dumps(payload["research_question_contract"]["open_ambiguities"]),
        )
        self.assertTrue(
            any(
                "Method-specificity limits still apply" in item
                for item in payload["research_question_contract"]["open_ambiguities"]
            )
        )

    def test_topic_status_surfaces_source_intelligence_read_path(self) -> None:
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
                    "human_request": "Inspect the runtime source-intelligence surface.",
                    "decision_surface": {
                        "selected_action_id": "action:demo-topic:read",
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
                    "action_id": "action:demo-topic:read",
                    "status": "pending",
                    "action_type": "inspect_resume_state",
                    "summary": "Inspect the source-intelligence summary before proceeding.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

        demo_source_root = self.kernel_root / "source-layer" / "topics" / "demo-topic"
        demo_source_root.mkdir(parents=True, exist_ok=True)
        (demo_source_root / "source_index.jsonl").write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "source_id": "paper:demo-source",
                            "source_type": "paper",
                            "title": "Demo runtime source",
                            "summary": "Runtime source summary with shared reference context.",
                            "references": ["doi:10-1000/shared"],
                            "canonical_source_id": "source_identity:doi:10-1000-demo",
                            "provenance": {
                                "abs_url": "https://example.org/demo",
                            },
                        },
                        ensure_ascii=True,
                    )
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        neighbor_source_root = self.kernel_root / "source-layer" / "topics" / "neighbor-topic"
        neighbor_source_root.mkdir(parents=True, exist_ok=True)
        (neighbor_source_root / "source_index.jsonl").write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "source_id": "paper:neighbor-source",
                            "source_type": "paper",
                            "title": "Neighbor runtime source",
                            "summary": "Neighbor source summary with shared reference context.",
                            "references": ["doi:10-1000/shared"],
                            "canonical_source_id": "source_identity:doi:10-1000-neighbor",
                            "provenance": {
                                "abs_url": "https://example.org/neighbor",
                            },
                        },
                        ensure_ascii=True,
                    )
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        status_payload = self.service.topic_status(topic_slug="demo-topic")

        self.assertIn("source_intelligence", status_payload)
        self.assertEqual(status_payload["source_intelligence"]["canonical_source_ids"][0], "source_identity:doi:10-1000-demo")
        self.assertEqual(status_payload["source_intelligence"]["cross_topic_match_count"], 1)
        self.assertEqual(status_payload["source_intelligence"]["citation_edges"][0]["target_ref"], "doi:10-1000/shared")
        self.assertEqual(status_payload["source_intelligence"]["source_neighbors"][0]["relation_kind"], "shared_reference")
        self.assertEqual(status_payload["source_intelligence"]["fidelity_summary"]["strongest_tier"], "peer_reviewed")
        self.assertEqual(status_payload["source_intelligence"]["fidelity_rows"][0]["fidelity_tier"], "peer_reviewed")
        self.assertEqual(
            status_payload["active_research_contract"]["l1_source_intake"]["method_specificity_rows"][0]["method_family"],
            "unspecified_method",
        )
        self.assertEqual(
            status_payload["active_research_contract"]["l1_source_intake"]["method_specificity_rows"][0]["specificity_tier"],
            "low",
        )
        dashboard_text = (self.kernel_root / "runtime" / "topics" / "demo-topic" / "topic_dashboard.md").read_text(encoding="utf-8")
        self.assertIn("## Source intelligence", dashboard_text)
        self.assertIn("## Source fidelity", dashboard_text)
        protocol_text = Path(status_payload["runtime_protocol_note_path"]).read_text(encoding="utf-8")
        self.assertIn("## Source intelligence", protocol_text)
        self.assertIn("peer_reviewed", protocol_text)
        self.assertIn("## Method specificity", protocol_text)

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
        analytical_payload = self.service.prepare_verification(
            topic_slug="demo-topic",
            mode="analytical",
        )
        self.assertEqual(analytical_payload["verification_mode"], "analytical")
        self.assertEqual(analytical_payload["validation_contract"]["validation_mode"], "analytical")
        self.assertIn("limiting cases", analytical_payload["validation_contract"]["verification_focus"])

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
        self.assertEqual(bundle["runtime_mode"], "discussion")
        self.assertIsNone(bundle["active_submode"])
        self.assertEqual(bundle["mode_envelope"]["mode"], "discussion")
        self.assertTrue(bundle["transition_posture"]["requires_human_checkpoint"])
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

    def test_execution_lane_confirmation_checkpoint_created_before_dispatch(self) -> None:
        runtime_root = self._write_runtime_state()
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "run the bounded benchmark lane",
                    "decision_surface": {
                        "decision_mode": "continue_unfinished",
                        "decision_source": "heuristic",
                        "decision_contract_status": "missing",
                        "control_note_path": None,
                        "selected_action_id": "action:demo-topic:dispatch",
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
                    "action_id": "action:demo-topic:dispatch",
                    "status": "pending",
                    "action_type": "await_execution_result",
                    "summary": "Run `runtime/topics/demo-topic/execution_task.json` in the external `codex_cli` lane and write the returned result artifact.",
                    "auto_runnable": False,
                    "queue_source": "runtime_appended",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "execution_task.json").write_text(
            json.dumps(
                {
                    "task_id": "demo-task",
                    "validation_note": "runtime/topics/demo-topic/validation_contract.active.md",
                    "candidate_id": "candidate:demo-candidate",
                    "surface": "numerical",
                    "status": "planned",
                    "input_artifacts": [],
                    "planned_outputs": [],
                    "pass_conditions": ["Write the returned result artifact."],
                    "failure_signals": ["Returned result is missing."],
                    "assigned_runtime": "codex",
                    "executor_kind": "codex_cli",
                    "result_artifacts": [],
                    "summary": "Demo execution task",
                    "needs_human_confirm": True,
                    "auto_dispatch_allowed": False,
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.ensure_topic_shell_surfaces(topic_slug="demo-topic", updated_by="test")

        self.assertEqual(payload["operator_checkpoint"]["status"], "requested")
        self.assertEqual(payload["operator_checkpoint"]["checkpoint_kind"], "execution_lane_confirmation")
        self.assertIn("confirm the execution lane", payload["operator_checkpoint"]["question"].lower())

    def test_execute_auto_actions_stops_when_operator_checkpoint_is_requested(self) -> None:
        runtime_root = self._write_runtime_state()
        queue_path = runtime_root / "action_queue.jsonl"
        queue_path.write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:01",
                    "status": "pending",
                    "action_type": "skill_discovery",
                    "summary": "Find a bounded external skill.",
                    "auto_runnable": True,
                    "handler_args": {"queries": ["demo query"]},
                    "queue_source": "heuristic",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "operator_checkpoint.active.json").write_text(
            json.dumps(
                {
                    "checkpoint_id": "checkpoint:demo-topic:dispatch",
                    "topic_slug": "demo-topic",
                    "run_id": "2026-03-13-demo",
                    "checkpoint_kind": "execution_lane_confirmation",
                    "status": "requested",
                    "note_path": "runtime/topics/demo-topic/operator_checkpoint.active.md",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service._execute_auto_actions(
            topic_slug="demo-topic",
            updated_by="test",
            max_auto_steps=1,
            default_skill_queries=["demo query"],
        )

        self.assertEqual(payload["executed"], [])
        self.assertTrue(payload["checkpoint_blocking"])
        self.assertEqual(payload["checkpoint_kind"], "execution_lane_confirmation")
        queue_row = json.loads(queue_path.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(queue_row["status"], "pending")

    def test_execute_auto_actions_stops_on_backedge_transition_contract(self) -> None:
        runtime_root = self._write_runtime_state()
        queue_path = runtime_root / "action_queue.jsonl"
        queue_path.write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:01",
                    "status": "pending",
                    "action_type": "skill_discovery",
                    "summary": "Consult memory before continuing the bounded route.",
                    "auto_runnable": True,
                    "handler_args": {"queries": ["demo query"]},
                    "queue_source": "heuristic",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "Continue carefully and consult memory if needed.",
                    "decision_surface": {
                        "decision_mode": "continue_unfinished",
                        "decision_source": "heuristic",
                        "selected_action_id": "action:demo-topic:01",
                    },
                    "action_queue_surface": {
                        "queue_source": "heuristic",
                    },
                    "human_edit_surfaces": [],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service._execute_auto_actions(
            topic_slug="demo-topic",
            updated_by="test",
            max_auto_steps=1,
            default_skill_queries=["demo query"],
        )

        self.assertEqual(payload["executed"], [])
        self.assertTrue(payload["transition_blocking"])
        self.assertEqual(payload["transition_kind"], "backedge_transition")
        self.assertEqual(payload["runtime_mode"], "explore")
        queue_row = json.loads(queue_path.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(queue_row["status"], "pending")

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
        runtime_root = self._write_runtime_state()
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "task_type": "open_exploration",
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L3",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
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
        self.assertEqual(payload["sections"]["control_plane"]["status"]["status"], "present")
        self.assertEqual(payload["sections"]["control_plane"]["task_type"]["detail"], "open_exploration")
        self.assertEqual(payload["sections"]["control_plane"]["layer"]["detail"], "L3")
        self.assertEqual(payload["sections"]["control_plane"]["mode"]["detail"], "explore")
        self.assertIn(payload["sections"]["control_plane"]["h_plane"]["detail"], {"answered", "cancelled", "requested"})
        self.assertEqual(payload["sections"]["h_plane"]["status"]["status"], "present")
        self.assertEqual(payload["sections"]["runtime"]["idea_packet.json"]["status"], "present")
        self.assertEqual(payload["sections"]["runtime"]["operator_checkpoint.active.json"]["status"], "present")
        self.assertEqual(payload["sections"]["runtime"]["operator_checkpoints.jsonl"]["status"], "present")
        self.assertIn(payload["sections"]["runtime"]["topic_synopsis.json"]["status"], {"present", "missing"})
        self.assertIn(
            payload["sections"]["runtime"]["validation_review_bundle.active.json"]["status"],
            {"present", "missing"},
        )

    def test_paired_backend_audit_reports_theoretical_pair(self) -> None:
        runtime_root = self._write_runtime_state()
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L3",
                    "backend_bridges": [
                        {
                            "backend_id": "backend:theoretical-physics-brain",
                            "title": "Theoretical Physics Brain",
                            "backend_type": "human_note_library",
                            "status": "active",
                            "card_status": "present",
                            "card_path": "canonical/backends/theoretical-physics-brain.json",
                            "backend_root": "/tmp/brain",
                            "artifact_kinds": ["formal_theory_note"],
                            "canonical_targets": ["concept", "theorem_card"],
                            "l0_registration_script": "source-layer/scripts/register_local_note_source.py",
                            "source_count": 1,
                        },
                        {
                            "backend_id": "backend:theoretical-physics-knowledge-network",
                            "title": "Theoretical Physics Knowledge Network",
                            "backend_type": "mixed_local_library",
                            "status": "active",
                            "card_status": "present",
                            "card_path": "canonical/backends/theoretical-physics-knowledge-network.json",
                            "backend_root": "/tmp/tpkn",
                            "artifact_kinds": ["typed_unit"],
                            "canonical_targets": ["concept", "theorem_card"],
                            "l0_registration_script": "source-layer/scripts/register_local_note_source.py",
                            "source_count": 1,
                        },
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self._write_theoretical_physics_brain_backend_card()
        self._write_tpkn_backend_card()
        self._write_theoretical_physics_pairing_docs()

        payload = self.service.paired_backend_audit(topic_slug="demo-topic")

        self.assertEqual(payload["topic_slug"], "demo-topic")
        self.assertEqual(payload["pairing_status"], "paired_active")
        self.assertEqual(payload["operator_primary_backend_id"], "backend:theoretical-physics-brain")
        self.assertEqual(payload["machine_primary_backend_id"], "backend:theoretical-physics-knowledge-network")
        self.assertEqual(payload["drift_status"], "audit_required")
        self.assertEqual(payload["backend_debt_status"], "unassessed")
        self.assertTrue(payload["semantic_separation"]["consultation"]["distinct_from_sync"])
        self.assertTrue(payload["semantic_separation"]["promotion"]["distinct_from_sync"])
        self.assertTrue(payload["semantic_separation"]["sync"]["uses_maintenance_protocol"])

    def test_h_plane_audit_reports_redirect_pause_checkpoint_and_pending_approval(self) -> None:
        runtime_root = self._write_runtime_state()
        (runtime_root / "control_note.md").write_text(
            "---\n"
            "directive: human_redirect\n"
            "summary: Redirect toward low-energy effective theory.\n"
            "---\n",
            encoding="utf-8",
        )
        (runtime_root / "innovation_direction.md").write_text("# Direction\n", encoding="utf-8")
        (runtime_root / "innovation_decisions.jsonl").write_text(
            json.dumps(
                {
                    "decision": "redirect",
                    "direction": "low-energy effective theory",
                    "summary": "Redirect toward low-energy effective theory.",
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "operator_checkpoint.active.json").write_text(
            json.dumps(
                {
                    "status": "requested",
                    "checkpoint_kind": "scope_ambiguity",
                    "active": True,
                    "note_path": "runtime/topics/demo-topic/operator_checkpoint.active.md",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "operator_checkpoint.active.md").write_text("# Checkpoint\n", encoding="utf-8")
        (runtime_root / "promotion_gate.json").write_text(
            json.dumps(
                {
                    "status": "pending_human_approval",
                    "candidate_id": "candidate:demo-candidate",
                    "backend_id": "backend:theoretical-physics-knowledge-network",
                    "note_path": "runtime/topics/demo-topic/promotion_gate.md",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "promotion_gate.md").write_text("# Promotion gate\n", encoding="utf-8")
        (self.kernel_root / "runtime" / "active_topics.json").write_text(
            json.dumps(
                {
                    "registry_version": 1,
                    "focused_topic_slug": "demo-topic",
                    "updated_at": "2026-04-11T02:30:00+08:00",
                    "updated_by": "test",
                    "source": "test",
                    "topics": [
                        {
                            "topic_slug": "demo-topic",
                            "status": "active",
                            "operator_status": "paused",
                            "priority": 0,
                            "last_activity": "2026-04-11T02:30:00+08:00",
                            "runtime_root": str(runtime_root),
                            "lane": "formal_theory",
                            "resume_stage": "L3",
                            "run_id": "2026-03-13-demo",
                            "projection_status": "missing",
                            "projection_note_path": None,
                            "blocked_by": [],
                            "blocked_by_details": [],
                            "focus_state": "focused",
                            "summary": "Paused for human steering.",
                            "human_request": "",
                        }
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.h_plane_audit(topic_slug="demo-topic")

        self.assertEqual(payload["steering"]["status"], "active_redirect")
        self.assertEqual(payload["checkpoint"]["status"], "requested")
        self.assertEqual(payload["approval"]["status"], "pending_human_approval")
        self.assertEqual(payload["registry"]["focus_state"], "focused")
        self.assertEqual(payload["registry"]["operator_status"], "paused")

    def test_seed_l2_direction_materializes_mvp_graph_units(self) -> None:
        self._prepare_l2_graph_kernel()
        payload = self.service.seed_l2_direction(
            direction="tfim-benchmark-first",
            updated_by="test-suite",
        )

        self.assertEqual(payload["direction"], "tfim-benchmark-first")
        self.assertGreaterEqual(payload["unit_count"], 9)
        self.assertTrue(
            (self.kernel_root / "canonical" / "physical-pictures" / "physical_picture--tfim-weak-coupling-benchmark-intuition.json").exists()
        )

    def test_consult_l2_returns_seeded_physical_picture(self) -> None:
        self._prepare_l2_graph_kernel()
        self.service.seed_l2_direction(
            direction="tfim-benchmark-first",
            updated_by="test-suite",
        )

        payload = self.service.consult_l2(
            query_text="TFIM exact diagonalization benchmark workflow",
            retrieval_profile="l3_candidate_formation",
            max_primary_hits=2,
        )

        ids = {row["id"] for row in payload["primary_hits"]}
        expanded_ids = {row["id"] for row in payload["expanded_hits"]}
        self.assertEqual(payload["retrieval_profile"], "l3_candidate_formation")
        self.assertIn("physical_picture:tfim-weak-coupling-benchmark-intuition", expanded_ids | ids)
        self.assertIn("traversal_paths", payload)
        self.assertIn("traversal_summary", payload)

    def test_consult_l2_can_record_durable_consultation_artifacts(self) -> None:
        self._prepare_l2_graph_kernel()
        self._write_runtime_state(topic_slug="demo-topic", run_id="run-001")
        payload = self.service.seed_l2_direction(
            direction="tfim-benchmark-first",
            updated_by="test-suite",
        )
        self.assertEqual(payload["direction"], "tfim-benchmark-first")

        consult_payload = self.service.consult_l2(
            query_text="Benchmark-first validation",
            retrieval_profile="l1_provisional_understanding",
            topic_slug="demo-topic",
            stage="L3",
            run_id="run-001",
            updated_by="test-suite",
            record_consultation=True,
        )

        consultation = consult_payload["consultation"]
        request_path = Path(consultation["consultation_request_path"])
        result_path = Path(consultation["consultation_result_path"])
        application_path = Path(consultation["consultation_application_path"])
        index_path = Path(consultation["consultation_index_path"])
        for path in (request_path, result_path, application_path, index_path):
            self.assertTrue(path.exists())
        result_payload = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertIn("retrieval_summary", result_payload)
        self.assertIn("traversal_paths", result_payload)
        self.assertEqual(result_payload["retrieval_summary"]["max_depth_reached"], 2)
        projection_log = (
            self.kernel_root / "feedback" / "topics" / "demo-topic" / "runs" / "run-001" / "l2_consultation_log.jsonl"
        )
        self.assertTrue(projection_log.exists())

    def test_compile_l2_workspace_map_reports_seeded_physical_picture(self) -> None:
        self._prepare_l2_graph_kernel()
        self.service.seed_l2_direction(
            direction="tfim-benchmark-first",
            updated_by="test-suite",
        )

        payload = self.service.compile_l2_workspace_map()

        self.assertTrue(Path(payload["json_path"]).exists())
        self.assertTrue(Path(payload["markdown_path"]).exists())
        self.assertIn("physical_picture", payload["payload"]["summary"]["unit_types_present"])

    def test_compile_l2_graph_report_materializes_navigation_outputs(self) -> None:
        self._prepare_l2_graph_kernel()
        self.service.seed_l2_direction(
            direction="tfim-benchmark-first",
            updated_by="test-suite",
        )

        payload = self.service.compile_l2_graph_report()

        self.assertTrue(Path(payload["json_path"]).exists())
        self.assertTrue(Path(payload["markdown_path"]).exists())
        self.assertTrue(Path(payload["navigation_index_path"]).exists())
        self.assertGreaterEqual(payload["navigation_page_count"], 9)
        self.assertEqual(payload["payload"]["hub_units"][0]["unit_id"], "workflow:tfim-benchmark-workflow")

    def test_compile_source_catalog_materializes_cross_topic_reuse(self) -> None:
        topic_a_root = self.kernel_root / "source-layer" / "topics" / "topic-a"
        topic_b_root = self.kernel_root / "source-layer" / "topics" / "topic-b"
        topic_a_root.mkdir(parents=True, exist_ok=True)
        topic_b_root.mkdir(parents=True, exist_ok=True)
        (topic_a_root / "source_index.jsonl").write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "source_id": "paper:shared-a",
                            "source_type": "paper",
                            "title": "Shared paper",
                            "summary": "Shared source summary.",
                            "canonical_source_id": "source_identity:doi:10-1000-shared-paper",
                            "references": ["doi:10-1000-neighbor-paper"],
                        },
                        ensure_ascii=True,
                    )
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (topic_b_root / "source_index.jsonl").write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "source_id": "paper:shared-b",
                            "source_type": "paper",
                            "title": "Shared paper mirror",
                            "summary": "Shared source summary in another topic.",
                            "canonical_source_id": "source_identity:doi:10-1000-shared-paper",
                            "references": [],
                        },
                        ensure_ascii=True,
                    ),
                    json.dumps(
                        {
                            "source_id": "paper:neighbor",
                            "source_type": "paper",
                            "title": "Neighbor paper",
                            "summary": "Neighbor source summary.",
                            "canonical_source_id": "source_identity:doi:10-1000-neighbor-paper",
                            "references": [],
                        },
                        ensure_ascii=True,
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.compile_source_catalog()

        self.assertTrue(Path(payload["json_path"]).exists())
        self.assertTrue(Path(payload["markdown_path"]).exists())
        self.assertEqual(payload["payload"]["summary"]["multi_topic_source_count"], 1)
        self.assertEqual(payload["payload"]["sources"][0]["canonical_source_id"], "source_identity:doi:10-1000-shared-paper")

    def test_trace_source_citations_materializes_bounded_traversal(self) -> None:
        topic_a_root = self.kernel_root / "source-layer" / "topics" / "topic-a"
        topic_b_root = self.kernel_root / "source-layer" / "topics" / "topic-b"
        topic_c_root = self.kernel_root / "source-layer" / "topics" / "topic-c"
        for root in (topic_a_root, topic_b_root, topic_c_root):
            root.mkdir(parents=True, exist_ok=True)
        (topic_a_root / "source_index.jsonl").write_text(
            json.dumps(
                {
                    "source_id": "paper:shared-a",
                    "source_type": "paper",
                    "title": "Shared paper",
                    "summary": "Shared source summary.",
                    "canonical_source_id": "source_identity:doi:10-1000-shared-paper",
                    "references": ["doi:10-1000-neighbor-paper"],
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (topic_b_root / "source_index.jsonl").write_text(
            json.dumps(
                {
                    "source_id": "paper:shared-b",
                    "source_type": "paper",
                    "title": "Shared paper mirror",
                    "summary": "Same paper in another topic.",
                    "canonical_source_id": "source_identity:doi:10-1000-shared-paper",
                    "references": [],
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (topic_c_root / "source_index.jsonl").write_text(
            json.dumps(
                {
                    "source_id": "paper:neighbor",
                    "source_type": "paper",
                    "title": "Neighbor paper",
                    "summary": "Neighbor source summary.",
                    "canonical_source_id": "source_identity:doi:10-1000-neighbor-paper",
                    "references": ["doi:10-1000-shared-paper"],
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.trace_source_citations(
            canonical_source_id="source_identity:doi:10-1000-shared-paper",
        )

        self.assertTrue(Path(payload["json_path"]).exists())
        self.assertTrue(Path(payload["markdown_path"]).exists())
        self.assertEqual(payload["payload"]["summary"]["outgoing_link_count"], 1)
        self.assertEqual(payload["payload"]["summary"]["incoming_link_count"], 1)

    def test_export_source_bibtex_materializes_bounded_bundle(self) -> None:
        topic_a_root = self.kernel_root / "source-layer" / "topics" / "topic-a"
        topic_b_root = self.kernel_root / "source-layer" / "topics" / "topic-b"
        for root in (topic_a_root, topic_b_root):
            root.mkdir(parents=True, exist_ok=True)
        (topic_a_root / "source_index.jsonl").write_text(
            json.dumps(
                {
                    "source_id": "paper:shared-a",
                    "source_type": "paper",
                    "title": "Shared paper",
                    "summary": "Shared source summary.",
                    "canonical_source_id": "source_identity:doi:10-1000-shared-paper",
                    "references": ["doi:10-1000-neighbor-paper"],
                    "provenance": {
                        "doi": "10.1000/shared-paper",
                        "authors": ["Ada Lovelace"],
                        "year": "1937",
                        "journal": "Journal of Shared Papers",
                        "abs_url": "https://doi.org/10.1000/shared-paper",
                    },
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (topic_b_root / "source_index.jsonl").write_text(
            json.dumps(
                {
                    "source_id": "paper:neighbor",
                    "source_type": "paper",
                    "title": "Neighbor paper",
                    "summary": "Neighbor source summary.",
                    "canonical_source_id": "source_identity:doi:10-1000-neighbor-paper",
                    "references": ["doi:10-1000-shared-paper"],
                    "provenance": {
                        "doi": "10.1000/neighbor-paper",
                        "authors": ["Emmy Noether"],
                        "year": "1941",
                        "journal": "Neighbor Letters",
                        "abs_url": "https://doi.org/10.1000/neighbor-paper",
                    },
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.export_source_bibtex(
            canonical_source_id="source_identity:doi:10-1000-shared-paper",
            include_neighbors=True,
        )

        self.assertTrue(Path(payload["json_path"]).exists())
        self.assertTrue(Path(payload["markdown_path"]).exists())
        self.assertTrue(Path(payload["bibtex_path"]).exists())
        self.assertEqual(payload["payload"]["summary"]["entry_count"], 2)
        self.assertEqual(payload["payload"]["summary"]["included_neighbor_count"], 1)

    def test_import_bibtex_sources_materializes_import_report(self) -> None:
        bib_path = self.kernel_root / "imports" / "demo-import.bib"
        bib_path.parent.mkdir(parents=True, exist_ok=True)
        bib_path.write_text(
            "\n".join(
                [
                    "@article{new-paper,",
                    "  title = {New imported paper},",
                    "  author = {Chen Ning Yang and Emmy Noether},",
                    "  year = {1942},",
                    "  doi = {10.1000/new-imported-paper},",
                    "  url = {https://doi.org/10.1000/new-imported-paper},",
                    "  abstract = {Imported from BibTeX.}",
                    "}",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        payload = self.service.import_bibtex_sources(
            topic_slug="demo-topic",
            bibtex_path=str(bib_path),
            updated_by="unit-test",
        )

        self.assertTrue(Path(payload["json_path"]).exists())
        self.assertTrue(Path(payload["markdown_path"]).exists())
        self.assertTrue(Path(payload["source_index_path"]).exists())
        self.assertEqual(payload["payload"]["summary"]["imported_entry_count"], 1)

    def test_compile_source_family_materializes_family_reuse_report(self) -> None:
        topic_a_root = self.kernel_root / "source-layer" / "topics" / "topic-a"
        topic_b_root = self.kernel_root / "source-layer" / "topics" / "topic-b"
        for root in (topic_a_root, topic_b_root):
            root.mkdir(parents=True, exist_ok=True)
        (topic_a_root / "source_index.jsonl").write_text(
            json.dumps(
                {
                    "source_id": "paper:shared-a",
                    "source_type": "paper",
                    "title": "Shared paper",
                    "summary": "Shared source summary.",
                    "canonical_source_id": "source_identity:doi:10-1000-shared-paper",
                    "references": [],
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (topic_b_root / "source_index.jsonl").write_text(
            json.dumps(
                {
                    "source_id": "paper:shared-b",
                    "source_type": "paper",
                    "title": "Shared paper mirror",
                    "summary": "Same paper in another topic.",
                    "canonical_source_id": "source_identity:doi:10-1000-shared-paper",
                    "references": [],
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.compile_source_family(source_type="paper")

        self.assertTrue(Path(payload["json_path"]).exists())
        self.assertTrue(Path(payload["markdown_path"]).exists())
        self.assertEqual(payload["payload"]["summary"]["multi_topic_source_count"], 1)

    def test_audit_l2_hygiene_reports_seeded_direction_artifacts(self) -> None:
        self._prepare_l2_graph_kernel()
        self.service.seed_l2_direction(
            direction="tfim-benchmark-first",
            updated_by="test-suite",
        )

        payload = self.service.audit_l2_hygiene()

        self.assertTrue(Path(payload["json_path"]).exists())
        self.assertTrue(Path(payload["markdown_path"]).exists())
        self.assertGreaterEqual(payload["payload"]["summary"]["total_units"], 9)
        self.assertIn(payload["payload"]["summary"]["status"], {"clean", "needs_review"})

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

    def test_doctor_reports_control_plane_contracts_and_operator_surfaces(self) -> None:
        docs_root = self.repo_root / "docs"
        docs_root.mkdir(parents=True, exist_ok=True)
        (docs_root / "AITP_UNIFIED_RESEARCH_ARCHITECTURE.md").write_text("# architecture\n", encoding="utf-8")
        (docs_root / "V142_ARCHITECTURE_VISION.md").write_text("# vision\n", encoding="utf-8")
        backends_root = self.kernel_root / "canonical" / "backends"
        backends_root.mkdir(parents=True, exist_ok=True)
        (backends_root / "THEORETICAL_PHYSICS_PAIRED_BACKEND_CONTRACT.md").write_text(
            "# paired backend contract\n",
            encoding="utf-8",
        )

        payload = self.service.ensure_cli_installed()

        self.assertEqual(payload["control_plane_contracts"]["unified_architecture"]["status"], "present")
        self.assertEqual(payload["control_plane_contracts"]["architecture_vision"]["status"], "present")
        self.assertEqual(payload["control_plane_contracts"]["paired_backend_contract"]["status"], "present")
        self.assertEqual(
            payload["control_plane_surfaces"]["doctor_json"]["command"],
            "aitp doctor --json",
        )
        self.assertEqual(
            payload["control_plane_surfaces"]["status"]["command"],
            "aitp status --topic-slug <topic_slug>",
        )
        self.assertEqual(
            payload["control_plane_surfaces"]["capability_audit"]["command"],
            "aitp capability-audit --topic-slug <topic_slug>",
        )
        self.assertEqual(
            payload["control_plane_surfaces"]["paired_backend_audit"]["command"],
            "aitp paired-backend-audit --topic-slug <topic_slug>",
        )
        self.assertEqual(
            payload["control_plane_surfaces"]["h_plane_audit"]["command"],
            "aitp h-plane-audit --topic-slug <topic_slug>",
        )

    def test_doctor_reports_runtime_support_matrix_for_ready_baseline_and_targets(self) -> None:
        codex_status = {
            "using_skill_path": "C:\\Users\\demo\\.agents\\skills\\using-aitp\\SKILL.md",
            "runtime_skill_path": "C:\\Users\\demo\\.agents\\skills\\aitp-runtime\\SKILL.md",
            "using_skill_present": True,
            "runtime_skill_present": True,
            "using_skill_matches_canonical": True,
            "runtime_skill_matches_canonical": True,
        }
        claude_status = {
            "using_skill_path": "C:\\Users\\demo\\.claude\\skills\\using-aitp\\SKILL.md",
            "runtime_skill_path": "C:\\Users\\demo\\.claude\\skills\\aitp-runtime\\SKILL.md",
            "session_start_hook_path": "C:\\Users\\demo\\.claude\\hooks\\session-start",
            "session_start_python_hook_path": "C:\\Users\\demo\\.claude\\hooks\\session-start.py",
            "hook_wrapper_path": "C:\\Users\\demo\\.claude\\hooks\\run-hook.cmd",
            "hooks_manifest_path": "C:\\Users\\demo\\.claude\\hooks\\hooks.json",
            "settings_path": "C:\\Users\\demo\\.claude\\settings.json",
            "using_skill": True,
            "runtime_skill": True,
            "session_start_hook": True,
            "session_start_python_hook": True,
            "hook_wrapper": True,
            "hooks_manifest": True,
            "settings": True,
            "using_skill_matches_canonical": True,
            "runtime_skill_matches_canonical": True,
            "session_start_hook_matches_canonical": True,
            "session_start_python_hook_matches_canonical": True,
            "hook_wrapper_matches_canonical": True,
            "hooks_manifest_matches_canonical": True,
            "settings_has_expected_session_start_command": True,
        }
        with patch.object(
            self.service,
            "_pip_show_package",
            return_value={
                "version": "0.4.0",
                "editable project location": str(self.service._canonical_package_root()),
            },
        ):
            with patch.object(self.service, "_codex_skill_status", return_value=codex_status):
                with patch.object(self.service, "_claude_hook_status", return_value=claude_status):
                    with patch.object(
                        self.service,
                        "_opencode_plugin_status",
                        return_value=self._make_opencode_status(),
                    ):
                        with patch.object(self.service, "_workspace_legacy_entrypoints", return_value=[]):
                            with patch.object(self.service, "_claude_legacy_command_paths", return_value=[]):
                                with patch(
                                    "knowledge_hub.aitp_service.shutil.which",
                                    side_effect=lambda name: {
                                        "aitp": "C:\\temp\\aitp.exe",
                                        "aitp-mcp": "C:\\temp\\aitp-mcp.exe",
                                        "codex": "C:\\temp\\codex.exe",
                                        "openclaw": "C:\\temp\\openclaw.exe",
                                        "mcporter": "C:\\temp\\mcporter.exe",
                                    }.get(name, ""),
                                ):
                                    payload = self.service.ensure_cli_installed(workspace_root=str(self.root))

        matrix = payload["runtime_support_matrix"]
        self.assertEqual(matrix["baseline_runtime"], "codex")
        self.assertEqual(matrix["parity_targets"], ["claude_code", "opencode"])
        self.assertEqual(matrix["specialized_lanes"], ["openclaw"])
        self.assertEqual(matrix["runtimes"]["codex"]["status"], "ready")
        self.assertEqual(matrix["runtimes"]["codex"]["maturity_class"], "baseline")
        self.assertEqual(matrix["runtimes"]["claude_code"]["status"], "ready")
        self.assertEqual(matrix["runtimes"]["claude_code"]["maturity_class"], "parity_target")
        self.assertEqual(matrix["runtimes"]["opencode"]["status"], "ready")
        self.assertEqual(matrix["runtimes"]["openclaw"]["maturity_class"], "specialized_lane")
        self.assertTrue(matrix["runtimes"]["claude_code"]["surface_checks"]["settings_has_expected_session_start_command"])
        self.assertEqual(matrix["runtimes"]["codex"]["remediation"]["status"], "none_required")
        self.assertEqual(matrix["runtimes"]["claude_code"]["remediation"]["status"], "none_required")
        self.assertEqual(matrix["runtimes"]["opencode"]["remediation"]["status"], "none_required")
        deep_execution = matrix["deep_execution_parity"]
        self.assertEqual(deep_execution["baseline_runtime"], "codex")
        self.assertEqual(deep_execution["parity_targets"], ["claude_code", "opencode"])
        self.assertEqual(deep_execution["deferred_lanes"], ["openclaw"])
        self.assertEqual(deep_execution["runtimes"]["codex"]["status"], "baseline_ready")
        self.assertEqual(deep_execution["runtimes"]["codex"]["baseline_relationship"], "baseline")
        self.assertEqual(deep_execution["runtimes"]["claude_code"]["status"], "probe_pending")
        self.assertEqual(deep_execution["runtimes"]["opencode"]["status"], "probe_pending")
        self.assertEqual(deep_execution["runtimes"]["openclaw"]["status"], "deferred")
        self.assertIn("run_runtime_parity_acceptance.py", deep_execution["runtimes"]["codex"]["acceptance_command"])
        self.assertEqual(payload["deep_execution_parity"]["baseline_status"], "baseline_ready")
        self.assertFalse(payload["deep_execution_parity"]["parity_targets_converged"])
        self.assertEqual(payload["deep_execution_parity"]["pending_targets"], ["claude_code", "opencode"])
        self.assertTrue(payload["runtime_convergence"]["front_door_runtimes_converged"])
        self.assertEqual(payload["full_convergence_repair"]["status"], "none_required")

    def test_doctor_runtime_support_matrix_reports_partial_front_doors_honestly(self) -> None:
        codex_status = {
            "using_skill_path": "C:\\Users\\demo\\.agents\\skills\\using-aitp\\SKILL.md",
            "runtime_skill_path": "C:\\Users\\demo\\.agents\\skills\\aitp-runtime\\SKILL.md",
            "using_skill_present": True,
            "runtime_skill_present": True,
            "using_skill_matches_canonical": True,
            "runtime_skill_matches_canonical": True,
        }
        claude_status = {
            "using_skill_path": "C:\\Users\\demo\\.claude\\skills\\using-aitp\\SKILL.md",
            "runtime_skill_path": "C:\\Users\\demo\\.claude\\skills\\aitp-runtime\\SKILL.md",
            "session_start_hook_path": "C:\\Users\\demo\\.claude\\hooks\\session-start",
            "session_start_python_hook_path": "C:\\Users\\demo\\.claude\\hooks\\session-start.py",
            "hook_wrapper_path": "C:\\Users\\demo\\.claude\\hooks\\run-hook.cmd",
            "hooks_manifest_path": "C:\\Users\\demo\\.claude\\hooks\\hooks.json",
            "settings_path": "C:\\Users\\demo\\.claude\\settings.json",
            "using_skill": True,
            "runtime_skill": False,
            "session_start_hook": False,
            "session_start_python_hook": False,
            "hook_wrapper": False,
            "hooks_manifest": False,
            "settings": False,
            "using_skill_matches_canonical": True,
            "runtime_skill_matches_canonical": False,
            "session_start_hook_matches_canonical": False,
            "session_start_python_hook_matches_canonical": False,
            "hook_wrapper_matches_canonical": False,
            "hooks_manifest_matches_canonical": False,
            "settings_has_expected_session_start_command": False,
        }
        with patch.object(
            self.service,
            "_pip_show_package",
            return_value={
                "version": "0.4.0",
                "editable project location": str(self.service._canonical_package_root()),
            },
        ):
            with patch.object(self.service, "_codex_skill_status", return_value=codex_status):
                with patch.object(self.service, "_claude_hook_status", return_value=claude_status):
                    with patch.object(
                        self.service,
                        "_opencode_plugin_status",
                        return_value=self._make_opencode_status(
                            config_exists=False,
                            config_parse_ok=False,
                            plugin_list_present=False,
                            plugin_list_valid=False,
                            plugins=[],
                            canonical_plugin_entry_present=False,
                            aitp_plugin_entries=[],
                        ),
                    ):
                        with patch.object(self.service, "_workspace_legacy_entrypoints", return_value=[]):
                            with patch.object(
                                self.service,
                                "_claude_legacy_command_paths",
                                return_value=[Path("C:/Users/demo/.claude/commands/aitp.md")],
                            ):
                                with patch(
                                    "knowledge_hub.aitp_service.shutil.which",
                                    side_effect=lambda name: {
                                        "aitp": "C:\\temp\\aitp.exe",
                                        "codex": "C:\\temp\\codex.exe",
                                    }.get(name, ""),
                                ):
                                    payload = self.service.ensure_cli_installed(workspace_root=str(self.root))

        matrix = payload["runtime_support_matrix"]["runtimes"]
        self.assertEqual(matrix["codex"]["status"], "ready")
        self.assertEqual(matrix["claude_code"]["status"], "stale")
        self.assertIn("legacy_claude_commands_present", matrix["claude_code"]["issues"])
        self.assertEqual(matrix["claude_code"]["remediation"]["command"], "aitp install-agent --agent claude-code --scope user")
        self.assertEqual(matrix["opencode"]["status"], "missing")
        self.assertIn("opencode_config_missing", matrix["opencode"]["issues"])
        self.assertEqual(matrix["opencode"]["remediation"]["status"], "required")
        self.assertEqual(matrix["openclaw"]["status"], "missing")
        deep_execution = payload["runtime_support_matrix"]["deep_execution_parity"]["runtimes"]
        self.assertEqual(deep_execution["codex"]["status"], "baseline_ready")
        self.assertEqual(deep_execution["claude_code"]["status"], "front_door_blocked")
        self.assertEqual(deep_execution["opencode"]["status"], "front_door_blocked")
        self.assertIn("front_door_status:stale", deep_execution["claude_code"]["blockers"])
        self.assertIn("front_door_status:missing", deep_execution["opencode"]["blockers"])
        self.assertEqual(payload["deep_execution_parity"]["blocked_targets"], ["claude_code", "opencode"])
        self.assertIn("claude_hook_surface_stale", payload["issues"])
        self.assertIn("opencode_plugin_surface_missing", payload["issues"])
        self.assertFalse(payload["runtime_convergence"]["front_door_runtimes_converged"])

    def test_doctor_runtime_support_matrix_reports_stale_claude_surfaces(self) -> None:
        codex_status = {
            "using_skill_path": "C:\\Users\\demo\\.agents\\skills\\using-aitp\\SKILL.md",
            "runtime_skill_path": "C:\\Users\\demo\\.agents\\skills\\aitp-runtime\\SKILL.md",
            "using_skill_present": True,
            "runtime_skill_present": True,
            "using_skill_matches_canonical": True,
            "runtime_skill_matches_canonical": True,
        }
        claude_status = {
            "using_skill_path": "C:\\Users\\demo\\.claude\\skills\\using-aitp\\SKILL.md",
            "runtime_skill_path": "C:\\Users\\demo\\.claude\\skills\\aitp-runtime\\SKILL.md",
            "session_start_hook_path": "C:\\Users\\demo\\.claude\\hooks\\session-start",
            "session_start_python_hook_path": "C:\\Users\\demo\\.claude\\hooks\\session-start.py",
            "hook_wrapper_path": "C:\\Users\\demo\\.claude\\hooks\\run-hook.cmd",
            "hooks_manifest_path": "C:\\Users\\demo\\.claude\\hooks\\hooks.json",
            "settings_path": "C:\\Users\\demo\\.claude\\settings.json",
            "using_skill": True,
            "runtime_skill": True,
            "session_start_hook": True,
            "session_start_python_hook": True,
            "hook_wrapper": True,
            "hooks_manifest": True,
            "settings": True,
            "using_skill_matches_canonical": True,
            "runtime_skill_matches_canonical": True,
            "session_start_hook_matches_canonical": False,
            "session_start_python_hook_matches_canonical": True,
            "hook_wrapper_matches_canonical": True,
            "hooks_manifest_matches_canonical": True,
            "settings_has_expected_session_start_command": False,
        }
        with patch.object(
            self.service,
            "_pip_show_package",
            return_value={
                "version": "0.4.0",
                "editable project location": str(self.service._canonical_package_root()),
            },
        ):
            with patch.object(self.service, "_codex_skill_status", return_value=codex_status):
                with patch.object(self.service, "_claude_hook_status", return_value=claude_status):
                    with patch.object(
                        self.service,
                        "_opencode_plugin_status",
                        return_value=self._make_opencode_status(),
                    ):
                        with patch.object(self.service, "_workspace_legacy_entrypoints", return_value=[]):
                            with patch.object(self.service, "_claude_legacy_command_paths", return_value=[]):
                                with patch(
                                    "knowledge_hub.aitp_service.shutil.which",
                                    side_effect=lambda name: {
                                        "aitp": "C:\\temp\\aitp.exe",
                                        "codex": "C:\\temp\\codex.exe",
                                    }.get(name, ""),
                                ):
                                    payload = self.service.ensure_cli_installed(workspace_root=str(self.root))

        claude_row = payload["runtime_support_matrix"]["runtimes"]["claude_code"]
        self.assertEqual(claude_row["status"], "stale")
        self.assertIn("session_start_hook_matches_canonical_stale", claude_row["issues"])
        self.assertIn("settings_session_start_command_mismatch", claude_row["issues"])
        self.assertEqual(claude_row["remediation"]["doc_path"], "docs/INSTALL_CLAUDE_CODE.md")
        self.assertEqual(claude_row["remediation"]["status"], "required")

    def test_doctor_runtime_support_matrix_reports_ready_opencode_compatibility_surface(self) -> None:
        codex_status = {
            "using_skill_path": "C:\\Users\\demo\\.agents\\skills\\using-aitp\\SKILL.md",
            "runtime_skill_path": "C:\\Users\\demo\\.agents\\skills\\aitp-runtime\\SKILL.md",
            "using_skill_present": True,
            "runtime_skill_present": True,
            "using_skill_matches_canonical": True,
            "runtime_skill_matches_canonical": True,
        }
        claude_status = {
            "using_skill_path": "C:\\Users\\demo\\.claude\\skills\\using-aitp\\SKILL.md",
            "runtime_skill_path": "C:\\Users\\demo\\.claude\\skills\\aitp-runtime\\SKILL.md",
            "session_start_hook_path": "C:\\Users\\demo\\.claude\\hooks\\session-start",
            "session_start_python_hook_path": "C:\\Users\\demo\\.claude\\hooks\\session-start.py",
            "hook_wrapper_path": "C:\\Users\\demo\\.claude\\hooks\\run-hook.cmd",
            "hooks_manifest_path": "C:\\Users\\demo\\.claude\\hooks\\hooks.json",
            "settings_path": "C:\\Users\\demo\\.claude\\settings.json",
            "using_skill": True,
            "runtime_skill": True,
            "session_start_hook": True,
            "session_start_python_hook": True,
            "hook_wrapper": True,
            "hooks_manifest": True,
            "settings": True,
            "using_skill_matches_canonical": True,
            "runtime_skill_matches_canonical": True,
            "session_start_hook_matches_canonical": True,
            "session_start_python_hook_matches_canonical": True,
            "hook_wrapper_matches_canonical": True,
            "hooks_manifest_matches_canonical": True,
            "settings_has_expected_session_start_command": True,
        }
        with patch.object(
            self.service,
            "_pip_show_package",
            return_value={
                "version": "0.4.0",
                "editable project location": str(self.service._canonical_package_root()),
            },
        ):
            with patch.object(self.service, "_codex_skill_status", return_value=codex_status):
                with patch.object(self.service, "_claude_hook_status", return_value=claude_status):
                    with patch.object(
                        self.service,
                        "_opencode_plugin_status",
                        return_value=self._make_opencode_status(
                            config_exists=False,
                            config_parse_ok=False,
                            plugin_list_present=False,
                            plugin_list_valid=False,
                            plugins=[],
                            canonical_plugin_entry_present=False,
                            aitp_plugin_entries=[],
                            workspace_plugin_path="D:/theory/.opencode/plugins/aitp.js",
                            workspace_using_skill_path="D:/theory/.opencode/skills/using-aitp/SKILL.md",
                            workspace_runtime_skill_path="D:/theory/.opencode/skills/aitp-runtime/SKILL.md",
                            workspace_plugin_present=True,
                            workspace_using_skill_present=True,
                            workspace_runtime_skill_present=True,
                            workspace_plugin_matches_canonical=True,
                            workspace_using_skill_matches_canonical=True,
                            workspace_runtime_skill_matches_canonical=True,
                        ),
                    ):
                        with patch.object(self.service, "_workspace_legacy_entrypoints", return_value=[]):
                            with patch.object(self.service, "_claude_legacy_command_paths", return_value=[]):
                                with patch(
                                    "knowledge_hub.aitp_service.shutil.which",
                                    side_effect=lambda name: {
                                        "aitp": "C:\\temp\\aitp.exe",
                                        "codex": "C:\\temp\\codex.exe",
                                    }.get(name, ""),
                                ):
                                    payload = self.service.ensure_cli_installed(workspace_root=str(self.root))

        opencode_row = payload["runtime_support_matrix"]["runtimes"]["opencode"]
        self.assertEqual(opencode_row["status"], "ready")
        self.assertIn("Workspace-local compatibility bootstrap is present", " ".join(opencode_row["notes"]))
        self.assertEqual(opencode_row["remediation"]["status"], "recommended")
        self.assertIn("aitp migrate-local-install", opencode_row["remediation"]["command"])

    def test_doctor_runtime_support_matrix_reports_partial_opencode_workspace_install(self) -> None:
        codex_status = {
            "using_skill_path": "C:\\Users\\demo\\.agents\\skills\\using-aitp\\SKILL.md",
            "runtime_skill_path": "C:\\Users\\demo\\.agents\\skills\\aitp-runtime\\SKILL.md",
            "using_skill_present": True,
            "runtime_skill_present": True,
            "using_skill_matches_canonical": True,
            "runtime_skill_matches_canonical": True,
        }
        claude_status = {
            "using_skill_path": "C:\\Users\\demo\\.claude\\skills\\using-aitp\\SKILL.md",
            "runtime_skill_path": "C:\\Users\\demo\\.claude\\skills\\aitp-runtime\\SKILL.md",
            "session_start_hook_path": "C:\\Users\\demo\\.claude\\hooks\\session-start",
            "session_start_python_hook_path": "C:\\Users\\demo\\.claude\\hooks\\session-start.py",
            "hook_wrapper_path": "C:\\Users\\demo\\.claude\\hooks\\run-hook.cmd",
            "hooks_manifest_path": "C:\\Users\\demo\\.claude\\hooks\\hooks.json",
            "settings_path": "C:\\Users\\demo\\.claude\\settings.json",
            "using_skill": True,
            "runtime_skill": True,
            "session_start_hook": True,
            "session_start_python_hook": True,
            "hook_wrapper": True,
            "hooks_manifest": True,
            "settings": True,
            "using_skill_matches_canonical": True,
            "runtime_skill_matches_canonical": True,
            "session_start_hook_matches_canonical": True,
            "session_start_python_hook_matches_canonical": True,
            "hook_wrapper_matches_canonical": True,
            "hooks_manifest_matches_canonical": True,
            "settings_has_expected_session_start_command": True,
        }
        with patch.object(
            self.service,
            "_pip_show_package",
            return_value={
                "version": "0.4.0",
                "editable project location": str(self.service._canonical_package_root()),
            },
        ):
            with patch.object(self.service, "_codex_skill_status", return_value=codex_status):
                with patch.object(self.service, "_claude_hook_status", return_value=claude_status):
                    with patch.object(
                        self.service,
                        "_opencode_plugin_status",
                        return_value=self._make_opencode_status(
                            config_exists=False,
                            config_parse_ok=False,
                            plugin_list_present=False,
                            plugin_list_valid=False,
                            plugins=[],
                            canonical_plugin_entry_present=False,
                            aitp_plugin_entries=[],
                            workspace_plugin_path="D:/theory/.opencode/plugins/aitp.js",
                            workspace_using_skill_path="D:/theory/.opencode/skills/using-aitp/SKILL.md",
                            workspace_runtime_skill_path="D:/theory/.opencode/skills/aitp-runtime/SKILL.md",
                            workspace_plugin_present=True,
                            workspace_using_skill_present=False,
                            workspace_runtime_skill_present=True,
                            workspace_plugin_matches_canonical=True,
                            workspace_using_skill_matches_canonical=False,
                            workspace_runtime_skill_matches_canonical=True,
                        ),
                    ):
                        with patch.object(self.service, "_workspace_legacy_entrypoints", return_value=[]):
                            with patch.object(self.service, "_claude_legacy_command_paths", return_value=[]):
                                with patch(
                                    "knowledge_hub.aitp_service.shutil.which",
                                    side_effect=lambda name: {
                                        "aitp": "C:\\temp\\aitp.exe",
                                        "codex": "C:\\temp\\codex.exe",
                                    }.get(name, ""),
                                ):
                                    payload = self.service.ensure_cli_installed(workspace_root=str(self.root))

        opencode_row = payload["runtime_support_matrix"]["runtimes"]["opencode"]
        self.assertEqual(opencode_row["status"], "partial")
        self.assertIn("workspace_using_skill_missing", opencode_row["issues"])
        self.assertIn("aitp migrate-local-install", opencode_row["remediation"]["command"])

    def test_doctor_runtime_support_matrix_reports_stale_opencode_config(self) -> None:
        codex_status = {
            "using_skill_path": "C:\\Users\\demo\\.agents\\skills\\using-aitp\\SKILL.md",
            "runtime_skill_path": "C:\\Users\\demo\\.agents\\skills\\aitp-runtime\\SKILL.md",
            "using_skill_present": True,
            "runtime_skill_present": True,
            "using_skill_matches_canonical": True,
            "runtime_skill_matches_canonical": True,
        }
        claude_status = {
            "using_skill_path": "C:\\Users\\demo\\.claude\\skills\\using-aitp\\SKILL.md",
            "runtime_skill_path": "C:\\Users\\demo\\.claude\\skills\\aitp-runtime\\SKILL.md",
            "session_start_hook_path": "C:\\Users\\demo\\.claude\\hooks\\session-start",
            "session_start_python_hook_path": "C:\\Users\\demo\\.claude\\hooks\\session-start.py",
            "hook_wrapper_path": "C:\\Users\\demo\\.claude\\hooks\\run-hook.cmd",
            "hooks_manifest_path": "C:\\Users\\demo\\.claude\\hooks\\hooks.json",
            "settings_path": "C:\\Users\\demo\\.claude\\settings.json",
            "using_skill": True,
            "runtime_skill": True,
            "session_start_hook": True,
            "session_start_python_hook": True,
            "hook_wrapper": True,
            "hooks_manifest": True,
            "settings": True,
            "using_skill_matches_canonical": True,
            "runtime_skill_matches_canonical": True,
            "session_start_hook_matches_canonical": True,
            "session_start_python_hook_matches_canonical": True,
            "hook_wrapper_matches_canonical": True,
            "hooks_manifest_matches_canonical": True,
            "settings_has_expected_session_start_command": True,
        }
        with patch.object(
            self.service,
            "_pip_show_package",
            return_value={
                "version": "0.4.0",
                "editable project location": str(self.service._canonical_package_root()),
            },
        ):
            with patch.object(self.service, "_codex_skill_status", return_value=codex_status):
                with patch.object(self.service, "_claude_hook_status", return_value=claude_status):
                    with patch.object(
                        self.service,
                        "_opencode_plugin_status",
                        return_value=self._make_opencode_status(
                            plugins=["aitp@git+ssh://old-private-repo"],
                            canonical_plugin_entry_present=False,
                            aitp_plugin_entries=["aitp@git+ssh://old-private-repo"],
                            noncanonical_aitp_plugin_entries=["aitp@git+ssh://old-private-repo"],
                        ),
                    ):
                        with patch.object(self.service, "_workspace_legacy_entrypoints", return_value=[]):
                            with patch.object(self.service, "_claude_legacy_command_paths", return_value=[]):
                                with patch(
                                    "knowledge_hub.aitp_service.shutil.which",
                                    side_effect=lambda name: {
                                        "aitp": "C:\\temp\\aitp.exe",
                                        "codex": "C:\\temp\\codex.exe",
                                    }.get(name, ""),
                                ):
                                    payload = self.service.ensure_cli_installed(workspace_root=str(self.root))

        opencode_row = payload["runtime_support_matrix"]["runtimes"]["opencode"]
        self.assertEqual(opencode_row["status"], "stale")
        self.assertIn("noncanonical_aitp_plugin_entries_present", opencode_row["issues"])
        self.assertEqual(opencode_row["remediation"]["status"], "required")
        self.assertIn("aitp migrate-local-install", opencode_row["remediation"]["command"])

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
        self.assertIn("runtime_support_matrix", payload)
        self.assertIn("runtime_convergence", payload)
        self.assertEqual(payload["package"]["status"], "stale_editable_install")
        self.assertEqual(payload["package"]["name"], "aitp")
        self.assertEqual(payload["full_convergence_repair"]["status"], "recommended")

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
        self.assertIn("runtime_convergence_before", result)
        self.assertIn("runtime_convergence_after", result)
        uninstall_steps = [row["step"] for row in result["pip_actions"]]
        self.assertIn("uninstall_aitp", uninstall_steps)
        self.assertIn("uninstall_aitp_kernel", uninstall_steps)

    def test_migrate_local_install_reports_runtime_convergence_before_and_after(self) -> None:
        workspace_root = self.root / "Theoretical-Physics"
        workspace_root.mkdir(parents=True, exist_ok=True)

        before = {
            "overall_status": "mixed_install",
            "runtime_support_matrix": {
                "baseline_runtime": "codex",
                "parity_targets": ["claude_code", "opencode"],
                "specialized_lanes": ["openclaw"],
                "runtimes": {
                    "codex": {"status": "ready"},
                    "claude_code": {"status": "partial"},
                    "opencode": {"status": "missing"},
                    "openclaw": {"status": "missing"},
                },
            },
        }
        after = {
            "overall_status": "clean",
            "runtime_support_matrix": {
                "baseline_runtime": "codex",
                "parity_targets": ["claude_code", "opencode"],
                "specialized_lanes": ["openclaw"],
                "runtimes": {
                    "codex": {"status": "ready"},
                    "claude_code": {"status": "ready"},
                    "opencode": {"status": "ready"},
                    "openclaw": {"status": "missing"},
                },
            },
        }

        def fake_install_agent(*, agent: str, scope: str = "user", target_root: str | None = None, force: bool = True, install_mcp: bool = True):
            return {"installed": [{"agent": agent, "path": f"/tmp/{agent}", "kind": "skill"}]}

        with patch.object(self.service, "ensure_cli_installed", side_effect=[before, after]):
            with patch.object(self.service, "_pip_show_package", return_value={"version": "0.4.0", "editable project location": str(self.service._canonical_package_root())}):
                with patch.object(self.service, "install_agent", side_effect=fake_install_agent):
                    with patch.object(self.service, "_ensure_opencode_plugin_enabled", return_value={"config_path": "C:\\temp\\opencode.json", "plugin_entry": "aitp@git+https://github.com/bhjia-phys/AITP-Research-Protocol.git"}):
                        result = self.service.migrate_local_install(
                            workspace_root=str(workspace_root),
                            agents=["codex", "claude-code", "opencode"],
                            with_mcp=False,
                        )

        self.assertFalse(result["runtime_convergence_before"]["front_door_runtimes_converged"])
        self.assertEqual(
            result["runtime_convergence_before"]["status_by_runtime"],
            {"codex": "ready", "claude_code": "partial", "opencode": "missing", "openclaw": "missing"},
        )
        self.assertTrue(result["runtime_convergence_after"]["front_door_runtimes_converged"])
        self.assertEqual(result["runtime_convergence_after"]["ready_runtimes"], ["codex", "claude_code", "opencode"])

    def test_doctor_prefers_legacy_distribution_when_primary_package_missing(self) -> None:
        workspace_root = self.root / "Theoretical-Physics"
        workspace_root.mkdir(parents=True, exist_ok=True)

        def fake_pip_show(name: str) -> dict[str, str]:
            if name == "aitp":
                return {}
            if name == "aitp-kernel":
                return {"version": "0.4.0"}
            return {}

        with patch.object(self.service, "_pip_show_package", side_effect=fake_pip_show):
            with patch("knowledge_hub.aitp_service.shutil.which", side_effect=lambda name: "C:\\temp\\aitp.exe" if name == "aitp" else ""):
                payload = self.service.ensure_cli_installed(workspace_root=str(workspace_root))

        self.assertEqual(payload["package"]["name"], "aitp-kernel")
        self.assertEqual(payload["package"]["status"], "legacy_installed")
        self.assertIn("legacy_package_install", payload["issues"])

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

    def test_active_topic_record_prefers_topic_synopsis_runtime_focus_summary(self) -> None:
        topic_slug = "synopsis-topic"
        topic_root = self.kernel_root / "runtime" / "topics" / topic_slug
        topic_root.mkdir(parents=True, exist_ok=True)
        (topic_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "latest_run_id": "2026-04-04-synopsis",
                    "resume_stage": "L3",
                    "summary": "State summary should not win.",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (topic_root / "topic_synopsis.json").write_text(
            json.dumps(
                {
                    "id": f"topic_synopsis:{topic_slug}",
                    "topic_slug": topic_slug,
                    "title": "Synopsis Topic",
                    "question": "What should the registry show?",
                    "lane": "code_method",
                    "load_profile": "light",
                    "status": "active",
                    "runtime_focus": {
                        "summary": "Synopsis-owned runtime summary.",
                        "why_this_topic_is_here": "The topic is following the bounded synopsis route.",
                        "resume_stage": "L3",
                        "last_materialized_stage": "L3",
                        "next_action_id": "action:synopsis-topic:01",
                        "next_action_type": "inspect_runtime",
                        "next_action_summary": "Inspect the synopsis truth model.",
                        "human_need_status": "none",
                        "human_need_kind": "none",
                        "human_need_summary": "No active human checkpoint is currently blocking the bounded loop.",
                        "blocker_summary": [],
                        "last_evidence_kind": "none",
                        "last_evidence_summary": "No durable evidence-return artifact is currently recorded for this topic.",
                        "dependency_status": "clear",
                        "dependency_summary": "No active topic dependencies.",
                        "promotion_status": "not_ready",
                    },
                    "truth_sources": {
                        "topic_state_path": f"runtime/topics/{topic_slug}/topic_state.json",
                        "research_question_contract_path": f"runtime/topics/{topic_slug}/research_question.contract.json",
                        "next_action_surface_path": f"runtime/topics/{topic_slug}/action_queue.jsonl",
                        "human_need_surface_path": None,
                        "dependency_registry_path": "runtime/active_topics.json",
                        "promotion_readiness_path": f"runtime/topics/{topic_slug}/promotion_readiness.json",
                        "promotion_gate_path": None,
                    },
                    "next_action_summary": "This older synopsis string should not win once runtime_focus exists.",
                    "open_gap_summary": "No explicit gap packet is currently open.",
                    "pending_decision_count": 0,
                    "knowledge_packet_paths": [],
                    "updated_at": "2026-04-04T10:00:00+08:00",
                    "updated_by": "test",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        record = self.service._build_active_topic_record(topic_slug=topic_slug)

        self.assertIsNotNone(record)
        self.assertEqual(record["summary"], "Synopsis-owned runtime summary.")

    def test_topic_synopsis_runtime_focus_preserves_fallback_shape(self) -> None:
        payload = self.service._topic_synopsis_runtime_focus(
            topic_state={"resume_stage": "L3", "last_materialized_stage": "L1"},
            topic_status_explainability={
                "next_bounded_action": {
                    "action_id": "action:demo-topic:01",
                    "action_type": "inspect_runtime",
                    "summary": "Inspect the persisted runtime truth.",
                },
                "active_human_need": {},
                "last_evidence_return": {},
                "blocker_summary": ["Need a tighter benchmark."],
            },
            dependency_state={},
            promotion_readiness={},
        )

        self.assertEqual(
            payload["summary"],
            "Stage `L3`; next `Inspect the persisted runtime truth.`; human need `none`; last evidence `none`.",
        )
        self.assertEqual(payload["next_action_id"], "action:demo-topic:01")
        self.assertEqual(payload["next_action_type"], "inspect_runtime")
        self.assertEqual(payload["promotion_status"], "not_ready")
        self.assertEqual(payload["blocker_summary"], ["Need a tighter benchmark."])
        self.assertEqual(payload["dependency_summary"], "No dependency state recorded.")
        self.assertEqual(payload["momentum_status"], "queued")
        self.assertEqual(payload["stuckness_status"], "none")
        self.assertEqual(payload["surprise_status"], "none")
        self.assertIn("Momentum `queued`", payload["judgment_summary"])

    def test_get_current_topic_memory_prefers_registry_focus_and_projects_compatibility_file(self) -> None:
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        focused_topic = "registry-topic"
        focused_runtime_root = runtime_root / "topics" / focused_topic
        focused_runtime_root.mkdir(parents=True, exist_ok=True)
        (focused_runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": focused_topic,
                    "latest_run_id": "2026-04-04-registry",
                    "resume_stage": "L3",
                    "summary": "Registry-backed focus topic.",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "active_topics.json").write_text(
            json.dumps(
                {
                    "registry_version": 1,
                    "focused_topic_slug": focused_topic,
                    "updated_at": "2026-04-04T10:00:00+08:00",
                    "updated_by": "registry-test",
                    "source": "test",
                    "topics": [
                        {
                            "topic_slug": focused_topic,
                            "status": "blocked",
                            "priority": 0,
                            "last_activity": "2026-04-04T10:00:00+08:00",
                            "runtime_root": str(focused_runtime_root),
                            "lane": "code_method",
                            "resume_stage": "L3",
                            "run_id": "2026-04-04-registry",
                            "projection_status": "missing",
                            "projection_note_path": None,
                            "blocked_by": [],
                            "focus_state": "focused",
                            "summary": "Registry focus summary.",
                            "human_request": "continue this topic",
                        }
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.get_current_topic_memory()

        self.assertEqual(payload["topic_slug"], focused_topic)
        self.assertEqual(payload["source"], "active-topics-registry")
        self.assertEqual(payload["summary"], "Registry focus summary.")
        projected_payload = json.loads((runtime_root / "current_topic.json").read_text(encoding="utf-8"))
        self.assertEqual(projected_payload["topic_slug"], focused_topic)

    def test_explore_materializes_lightweight_session_without_topic_bootstrap(self) -> None:
        payload = self.service.explore(
            task="Speculate about a benchmark-first route for a new toy model without opening a full topic yet.",
            updated_by="test",
        )

        session_path = Path(payload["exploration_session_path"])
        note_path = Path(payload["exploration_session_note_path"])
        self.assertTrue(session_path.exists())
        self.assertTrue(note_path.exists())
        self.assertEqual(payload["status"], "lightweight_open")
        self.assertTrue(payload["topic_bootstrap_skipped"])
        self.assertEqual(payload["artifact_count"], 2)
        self.assertEqual(payload["artifact_footprint"]["quick_exploration_artifact_count"], 2)
        self.assertGreater(payload["artifact_footprint"]["reference_full_topic_artifact_count"], 2)
        self.assertIn("topic_dashboard.md", json.dumps(payload["artifact_footprint"]["avoided_full_topic_artifacts"]))
        self.assertIsNone(payload["current_topic_slug"])
        self.assertIn("aitp session-start", payload["promotion_paths"]["promote_to_new_topic_command"])
        self.assertFalse((self.kernel_root / "runtime" / "topics").exists())

    def test_explore_uses_current_topic_context_without_rebootstrap(self) -> None:
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        remembered_topic = "demo-topic"
        remembered_runtime_root = runtime_root / "topics" / remembered_topic
        remembered_runtime_root.mkdir(parents=True, exist_ok=True)
        (remembered_runtime_root / "topic_state.json").write_text(
            json.dumps({"topic_slug": remembered_topic, "resume_stage": "L3"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (runtime_root / "current_topic.json").write_text(
            json.dumps(
                {
                    "topic_slug": remembered_topic,
                    "current_topic_note_path": "runtime/current_topic.md",
                    "summary": "Continue the bounded benchmark lane.",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "current_topic.md").write_text("# Current topic\n", encoding="utf-8")

        payload = self.service.explore(
            task="Sketch a low-cost speculative branch before committing to a full loop.",
            updated_by="test",
        )

        self.assertEqual(payload["current_topic_slug"], remembered_topic)
        self.assertTrue(payload["topic_bootstrap_skipped"])
        self.assertEqual(payload["must_read_now"][0]["path"], "runtime/current_topic.md")
        self.assertIn("--current-topic", payload["promotion_paths"]["promote_to_current_topic_command"])

    def test_promote_exploration_materializes_request_and_bounded_session_start(self) -> None:
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        remembered_topic = "demo-topic"
        remembered_runtime_root = runtime_root / "topics" / remembered_topic
        remembered_runtime_root.mkdir(parents=True, exist_ok=True)
        (remembered_runtime_root / "topic_state.json").write_text(
            json.dumps({"topic_slug": remembered_topic, "resume_stage": "L3"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (runtime_root / "current_topic.json").write_text(
            json.dumps({"topic_slug": remembered_topic, "current_topic_note_path": "runtime/current_topic.md"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (runtime_root / "current_topic.md").write_text("# Current topic\n", encoding="utf-8")

        service = _SteeringLoopStubService(kernel_root=self.kernel_root, repo_root=self.repo_root)
        explore_payload = service.explore(
            task="Sketch a low-cost speculative branch before committing to a full loop.",
            updated_by="test",
        )

        promotion_payload = service.promote_exploration(
            exploration_id=explore_payload["exploration_id"],
            updated_by="test",
        )

        self.assertTrue(Path(promotion_payload["promotion_request_path"]).exists())
        self.assertTrue(Path(promotion_payload["promotion_request_note_path"]).exists())
        self.assertEqual(promotion_payload["target_mode"], "current_topic")
        self.assertEqual(promotion_payload["promoted_session"]["routing"]["route"], "explicit_current_topic")
        self.assertEqual(promotion_payload["promoted_session"]["topic_slug"], remembered_topic)
        self.assertTrue(Path(promotion_payload["promoted_session"]["session_start_contract_path"]).exists())

    def test_build_current_topic_memory_payload_prefers_topic_synopsis_runtime_focus_summary(self) -> None:
        topic_slug = "current-synopsis-topic"
        topic_root = self.kernel_root / "runtime" / "topics" / topic_slug
        topic_root.mkdir(parents=True, exist_ok=True)
        (topic_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "latest_run_id": "2026-04-04-current",
                    "resume_stage": "L4",
                    "summary": "Fallback state summary.",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (topic_root / "topic_synopsis.json").write_text(
            json.dumps(
                {
                    "id": f"topic_synopsis:{topic_slug}",
                    "topic_slug": topic_slug,
                    "title": "Current Synopsis Topic",
                    "question": "Which summary should current-topic project?",
                    "lane": "toy_numeric",
                    "load_profile": "light",
                    "status": "active",
                    "runtime_focus": {
                        "summary": "Current-topic summary should come from synopsis runtime_focus.",
                        "why_this_topic_is_here": "This topic is still in a bounded numerical route.",
                        "resume_stage": "L4",
                        "last_materialized_stage": "L4",
                        "next_action_id": "action:current-synopsis-topic:01",
                        "next_action_type": "review_validation",
                        "next_action_summary": "Review the validation artifacts.",
                        "human_need_status": "none",
                        "human_need_kind": "none",
                        "human_need_summary": "No active human checkpoint is currently blocking the bounded loop.",
                        "blocker_summary": [],
                        "last_evidence_kind": "validation_evidence",
                        "last_evidence_summary": "Validation evidence artifacts are present.",
                        "dependency_status": "clear",
                        "dependency_summary": "No active topic dependencies.",
                        "promotion_status": "not_ready",
                    },
                    "truth_sources": {
                        "topic_state_path": f"runtime/topics/{topic_slug}/topic_state.json",
                        "research_question_contract_path": f"runtime/topics/{topic_slug}/research_question.contract.json",
                        "next_action_surface_path": f"runtime/topics/{topic_slug}/action_queue.jsonl",
                        "human_need_surface_path": None,
                        "dependency_registry_path": "runtime/active_topics.json",
                        "promotion_readiness_path": f"runtime/topics/{topic_slug}/promotion_readiness.json",
                        "promotion_gate_path": None,
                    },
                    "next_action_summary": "Older current-topic fallback.",
                    "open_gap_summary": "No explicit gap packet is currently open.",
                    "pending_decision_count": 0,
                    "knowledge_packet_paths": [],
                    "updated_at": "2026-04-04T11:00:00+08:00",
                    "updated_by": "test",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service._build_current_topic_memory_payload(
            topic_slug=topic_slug,
            updated_by="test",
            source="test",
        )

        self.assertEqual(payload["summary"], "Current-topic summary should come from synopsis runtime_focus.")

    def test_build_current_topic_memory_payload_includes_collaborator_profile_when_present(self) -> None:
        topic_slug = "profile-topic"
        topic_root = self.kernel_root / "runtime" / "topics" / topic_slug
        topic_root.mkdir(parents=True, exist_ok=True)
        (topic_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "latest_run_id": "2026-04-11-profile",
                    "resume_stage": "L3",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (topic_root / "collaborator_profile.active.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "status": "available",
                    "summary": "Prefer theorem-facing routes and keep the scope bounded.",
                    "path": f"runtime/topics/{topic_slug}/collaborator_profile.active.json",
                    "note_path": f"runtime/topics/{topic_slug}/collaborator_profile.active.md",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (topic_root / "collaborator_profile.active.md").write_text("# Collaborator profile\n", encoding="utf-8")

        payload = self.service._build_current_topic_memory_payload(
            topic_slug=topic_slug,
            updated_by="test",
            source="test",
        )

        self.assertEqual(payload["collaborator_profile_status"], "available")
        self.assertIn("theorem-facing", payload["collaborator_profile_summary"])
        self.assertTrue(payload["collaborator_profile_path"].endswith("collaborator_profile.active.json"))

    def test_build_current_topic_memory_payload_includes_research_trajectory_when_present(self) -> None:
        topic_slug = "trajectory-topic"
        topic_root = self.kernel_root / "runtime" / "topics" / topic_slug
        topic_root.mkdir(parents=True, exist_ok=True)
        (topic_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "latest_run_id": "2026-04-11-trajectory",
                    "resume_stage": "L3",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (topic_root / "research_trajectory.active.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "status": "available",
                    "summary": "Recent trajectory keeps the bounded derivation route active.",
                    "path": f"runtime/topics/{topic_slug}/research_trajectory.active.json",
                    "note_path": f"runtime/topics/{topic_slug}/research_trajectory.active.md",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (topic_root / "research_trajectory.active.md").write_text("# Research trajectory\n", encoding="utf-8")

        payload = self.service._build_current_topic_memory_payload(
            topic_slug=topic_slug,
            updated_by="test",
            source="test",
        )

        self.assertEqual(payload["research_trajectory_status"], "available")
        self.assertIn("bounded derivation route", payload["research_trajectory_summary"])
        self.assertTrue(payload["research_trajectory_path"].endswith("research_trajectory.active.json"))

    def test_build_current_topic_memory_payload_includes_mode_learning_when_present(self) -> None:
        topic_slug = "mode-topic"
        topic_root = self.kernel_root / "runtime" / "topics" / topic_slug
        topic_root.mkdir(parents=True, exist_ok=True)
        (topic_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "latest_run_id": "2026-04-11-mode",
                    "resume_stage": "L3",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (topic_root / "mode_learning.active.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "status": "available",
                    "summary": "Mode learning favors the benchmark-first route for this topic.",
                    "path": f"runtime/topics/{topic_slug}/mode_learning.active.json",
                    "note_path": f"runtime/topics/{topic_slug}/mode_learning.active.md",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (topic_root / "mode_learning.active.md").write_text("# Mode learning\n", encoding="utf-8")

        payload = self.service._build_current_topic_memory_payload(
            topic_slug=topic_slug,
            updated_by="test",
            source="test",
        )

        self.assertEqual(payload["mode_learning_status"], "available")
        self.assertIn("benchmark-first route", payload["mode_learning_summary"])
        self.assertTrue(payload["mode_learning_path"].endswith("mode_learning.active.json"))

    def test_remember_current_topic_writes_active_topics_registry_and_bootstraps_known_topics(self) -> None:
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        topic_index_path = runtime_root / "topic_index.jsonl"
        topic_index_path.write_text(
            json.dumps({"topic_slug": "older-topic", "updated_at": "2026-04-03T08:00:00+08:00"}, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        for topic_slug, updated_at in (("older-topic", "2026-04-03T08:00:00+08:00"), ("focused-topic", "2026-04-04T09:00:00+08:00")):
            topic_runtime_root = runtime_root / "topics" / topic_slug
            topic_runtime_root.mkdir(parents=True, exist_ok=True)
            (topic_runtime_root / "topic_state.json").write_text(
                json.dumps(
                    {
                        "topic_slug": topic_slug,
                        "updated_at": updated_at,
                        "latest_run_id": f"{topic_slug}-run",
                        "resume_stage": "L3",
                        "summary": f"Summary for {topic_slug}.",
                    },
                    ensure_ascii=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

        payload = self.service.remember_current_topic(
            topic_slug="focused-topic",
            updated_by="registry-test",
            source="test",
            human_request="continue focused topic",
        )

        registry_payload = json.loads((runtime_root / "active_topics.json").read_text(encoding="utf-8"))
        self.assertEqual(registry_payload["focused_topic_slug"], "focused-topic")
        topic_slugs = {row["topic_slug"] for row in registry_payload["topics"]}
        self.assertEqual(topic_slugs, {"older-topic", "focused-topic"})
        focused_row = next(row for row in registry_payload["topics"] if row["topic_slug"] == "focused-topic")
        self.assertEqual(focused_row["focus_state"], "focused")
        self.assertEqual(focused_row["priority"], 0)
        self.assertEqual(focused_row["runtime_root"], "runtime/topics/focused-topic")
        self.assertEqual(payload["topic_slug"], "focused-topic")
        self.assertEqual(payload["runtime_root"], "runtime/topics/focused-topic")
        projected_payload = json.loads((runtime_root / "current_topic.json").read_text(encoding="utf-8"))
        self.assertEqual(projected_payload["runtime_root"], "runtime/topics/focused-topic")
        current_topic_note = (runtime_root / "current_topic.md").read_text(encoding="utf-8")
        self.assertIn("Runtime root: `runtime/topics/focused-topic`", current_topic_note)
        self.assertTrue((runtime_root / "active_topics.md").exists())

    def test_select_next_topic_prefers_priority_then_focus_and_reports_skips(self) -> None:
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        rows = [
            {
                "topic_slug": "focused-low",
                "status": "ready",
                "priority": 1,
                "last_activity": "2026-04-04T10:00:00+08:00",
                "runtime_root": "runtime/topics/focused-low",
                "lane": "code_method",
                "focus_state": "focused",
                "projection_status": "missing",
                "blocked_by": [],
                "summary": "Focused topic",
            },
            {
                "topic_slug": "priority-high",
                "status": "ready",
                "priority": 3,
                "last_activity": "2026-04-04T09:00:00+08:00",
                "runtime_root": "runtime/topics/priority-high",
                "lane": "formal_theory",
                "focus_state": "background",
                "projection_status": "missing",
                "blocked_by": [],
                "summary": "High priority topic",
            },
            {
                "topic_slug": "paused-topic",
                "status": "paused",
                "priority": 10,
                "last_activity": "2026-04-04T11:00:00+08:00",
                "runtime_root": "runtime/topics/paused-topic",
                "lane": "code_method",
                "focus_state": "background",
                "projection_status": "missing",
                "blocked_by": [],
                "summary": "Paused topic",
            },
            {
                "topic_slug": "dependency-topic",
                "status": "ready",
                "priority": 9,
                "last_activity": "2026-04-04T12:00:00+08:00",
                "runtime_root": "runtime/topics/dependency-topic",
                "lane": "code_method",
                "focus_state": "background",
                "projection_status": "missing",
                "blocked_by": ["other-topic"],
                "summary": "Dependency blocked topic",
            },
        ]
        for row in rows:
            topic_runtime_root = self.kernel_root / str(row["runtime_root"])
            topic_runtime_root.mkdir(parents=True, exist_ok=True)
            (topic_runtime_root / "topic_state.json").write_text(
                json.dumps(
                    {
                        "topic_slug": row["topic_slug"],
                        "latest_run_id": f"{row['topic_slug']}-run",
                        "resume_stage": "L3",
                    },
                    ensure_ascii=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        (runtime_root / "active_topics.json").write_text(
            json.dumps(
                {
                    "registry_version": 1,
                    "focused_topic_slug": "focused-low",
                    "updated_at": "2026-04-04T12:30:00+08:00",
                    "updated_by": "scheduler-test",
                    "source": "test",
                    "topics": rows,
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.select_next_topic(updated_by="scheduler-test")

        self.assertEqual(payload["selected_topic_slug"], "priority-high")
        self.assertIn("highest_priority=3", payload["selection_reason"])
        skipped = {row["topic_slug"]: row["reason"] for row in payload["skipped_topics"]}
        self.assertEqual(skipped["paused-topic"], "paused")
        self.assertEqual(skipped["dependency-topic"], "dependency_blocked")

    def test_run_topic_loop_without_explicit_topic_uses_scheduler_selection(self) -> None:
        service = _LoopStubService(kernel_root=self.kernel_root, repo_root=self.repo_root)
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        selected_root = runtime_root / "topics" / "scheduled-topic"
        selected_root.mkdir(parents=True, exist_ok=True)
        (selected_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "scheduled-topic",
                    "latest_run_id": "2026-04-04-scheduled",
                    "resume_stage": "L3",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "active_topics.json").write_text(
            json.dumps(
                {
                    "registry_version": 1,
                    "focused_topic_slug": "scheduled-topic",
                    "updated_at": "2026-04-04T13:00:00+08:00",
                    "updated_by": "scheduler-test",
                    "source": "test",
                    "topics": [
                        {
                            "topic_slug": "scheduled-topic",
                            "status": "ready",
                            "priority": 1,
                            "last_activity": "2026-04-04T13:00:00+08:00",
                            "runtime_root": str(selected_root),
                            "lane": "code_method",
                            "focus_state": "focused",
                            "projection_status": "missing",
                            "blocked_by": [],
                            "summary": "Scheduled topic",
                        }
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = service.run_topic_loop(
            human_request="continue the best topic",
            max_auto_steps=0,
            updated_by="scheduler-test",
        )

        self.assertEqual(payload["topic_slug"], "scheduled-topic")
        self.assertEqual(payload["scheduler"]["selected_topic_slug"], "scheduled-topic")

    def test_list_active_topics_reports_effective_status_and_focus(self) -> None:
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        topic_root = runtime_root / "topics" / "demo-topic"
        topic_root.mkdir(parents=True, exist_ok=True)
        (topic_root / "topic_state.json").write_text(
            json.dumps({"topic_slug": "demo-topic", "latest_run_id": "run", "resume_stage": "L3"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (runtime_root / "active_topics.json").write_text(
            json.dumps(
                {
                    "registry_version": 1,
                    "focused_topic_slug": "demo-topic",
                    "updated_at": "2026-04-04T14:00:00+08:00",
                    "updated_by": "test",
                    "source": "test",
                    "topics": [
                        {
                            "topic_slug": "demo-topic",
                            "status": "blocked",
                            "operator_status": "paused",
                            "priority": 0,
                            "last_activity": "2026-04-04T14:00:00+08:00",
                            "runtime_root": str(topic_root),
                            "lane": "code_method",
                            "focus_state": "focused",
                            "projection_status": "missing",
                            "blocked_by": [],
                            "summary": "Paused topic",
                        }
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.list_active_topics(updated_by="test")

        self.assertEqual(payload["focused_topic_slug"], "demo-topic")
        self.assertEqual(payload["topics"][0]["effective_status"], "paused")

    def test_list_active_topics_materializes_protocol_native_topic_family_reuse_surface(self) -> None:
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        self._write_available_projection(
            topic_slug="code-family-topic",
            lane="code_method",
            summary="Validated reusable benchmark-first code-method route.",
            required_first_routes=["Close the benchmark-first route before broader workflow claims."],
        )
        self._write_available_projection(
            topic_slug="formal-family-topic",
            lane="formal_theory",
            summary="Validated reusable theorem-facing formal-theory route.",
            required_first_routes=["Read the theorem-facing route before reusing the proof lane."],
        )
        self._write_runtime_state(topic_slug="blocked-topic", run_id="run-blocked")
        (runtime_root / "topics" / "blocked-topic" / "topic_skill_projection.active.json").write_text(
            json.dumps(
                {
                    "id": "topic_skill_projection:blocked-topic",
                    "topic_slug": "blocked-topic",
                    "lane": "code_method",
                    "status": "blocked",
                    "summary": "Blocked projection should not enter family reuse.",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "active_topics.json").write_text(
            json.dumps(
                {
                    "registry_version": 1,
                    "focused_topic_slug": "code-family-topic",
                    "updated_at": "2026-04-04T14:00:00+08:00",
                    "updated_by": "test",
                    "source": "test",
                    "topics": [
                        {
                            "topic_slug": "code-family-topic",
                            "status": "active",
                            "operator_status": "",
                            "priority": 0,
                            "last_activity": "2026-04-04T14:00:00+08:00",
                            "runtime_root": str(runtime_root / "topics" / "code-family-topic"),
                            "lane": "code_method",
                            "focus_state": "focused",
                            "projection_status": "available",
                            "projection_note_path": "runtime/topics/code-family-topic/topic_skill_projection.active.md",
                            "blocked_by": [],
                            "summary": "Code family route.",
                        },
                        {
                            "topic_slug": "formal-family-topic",
                            "status": "active",
                            "operator_status": "",
                            "priority": 0,
                            "last_activity": "2026-04-04T14:10:00+08:00",
                            "runtime_root": str(runtime_root / "topics" / "formal-family-topic"),
                            "lane": "formal_theory",
                            "focus_state": "background",
                            "projection_status": "available",
                            "projection_note_path": "runtime/topics/formal-family-topic/topic_skill_projection.active.md",
                            "blocked_by": [],
                            "summary": "Formal family route.",
                        },
                        {
                            "topic_slug": "blocked-topic",
                            "status": "active",
                            "operator_status": "",
                            "priority": 0,
                            "last_activity": "2026-04-04T14:20:00+08:00",
                            "runtime_root": str(runtime_root / "topics" / "blocked-topic"),
                            "lane": "code_method",
                            "focus_state": "background",
                            "projection_status": "blocked",
                            "projection_note_path": None,
                            "blocked_by": [],
                            "summary": "Blocked route.",
                        },
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.list_active_topics(updated_by="test")

        reuse = payload["topic_family_reuse"]
        self.assertEqual(reuse["surface_kind"], "topic_family_reuse")
        self.assertEqual(reuse["family_count"], 2)
        families_by_lane = {row["lane"]: row for row in reuse["families"]}
        self.assertEqual(families_by_lane["code_method"]["topic_slugs"], ["code-family-topic"])
        self.assertEqual(families_by_lane["formal_theory"]["topic_slugs"], ["formal-family-topic"])
        self.assertTrue(Path(payload["topic_family_reuse_path"]).exists())
        self.assertTrue(Path(payload["topic_family_reuse_note_path"]).exists())
        note_text = Path(payload["topic_family_reuse_note_path"]).read_text(encoding="utf-8")
        self.assertIn("protocol-native route reuse", note_text)
        self.assertNotIn("blocked-topic", note_text)

    def test_pause_topic_moves_focus_to_next_eligible_topic(self) -> None:
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        for topic_slug in ("alpha-topic", "beta-topic"):
            topic_root = runtime_root / "topics" / topic_slug
            topic_root.mkdir(parents=True, exist_ok=True)
            (topic_root / "topic_state.json").write_text(
                json.dumps({"topic_slug": topic_slug, "latest_run_id": "run", "resume_stage": "L3"}, ensure_ascii=True, indent=2) + "\n",
                encoding="utf-8",
            )
        (runtime_root / "active_topics.json").write_text(
            json.dumps(
                {
                    "registry_version": 1,
                    "focused_topic_slug": "alpha-topic",
                    "updated_at": "2026-04-04T14:00:00+08:00",
                    "updated_by": "test",
                    "source": "test",
                    "topics": [
                        {
                            "topic_slug": "alpha-topic",
                            "status": "ready",
                            "operator_status": "",
                            "priority": 1,
                            "last_activity": "2026-04-04T14:00:00+08:00",
                            "runtime_root": str(runtime_root / "topics" / "alpha-topic"),
                            "lane": "code_method",
                            "focus_state": "focused",
                            "projection_status": "missing",
                            "blocked_by": [],
                            "summary": "Alpha",
                        },
                        {
                            "topic_slug": "beta-topic",
                            "status": "ready",
                            "operator_status": "",
                            "priority": 0,
                            "last_activity": "2026-04-04T13:00:00+08:00",
                            "runtime_root": str(runtime_root / "topics" / "beta-topic"),
                            "lane": "formal_theory",
                            "focus_state": "background",
                            "projection_status": "missing",
                            "blocked_by": [],
                            "summary": "Beta",
                        },
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.pause_topic(topic_slug="alpha-topic", updated_by="test", human_request="暂停 alpha-topic")

        self.assertEqual(payload["status"], "paused")
        self.assertEqual(payload["focused_topic_slug"], "beta-topic")
        registry_payload = json.loads((runtime_root / "active_topics.json").read_text(encoding="utf-8"))
        alpha_row = next(row for row in registry_payload["topics"] if row["topic_slug"] == "alpha-topic")
        self.assertEqual(alpha_row["operator_status"], "paused")

    def test_resume_topic_focuses_the_resumed_topic(self) -> None:
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        topic_root = runtime_root / "topics" / "alpha-topic"
        topic_root.mkdir(parents=True, exist_ok=True)
        (topic_root / "topic_state.json").write_text(
            json.dumps({"topic_slug": "alpha-topic", "latest_run_id": "run", "resume_stage": "L3"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (runtime_root / "active_topics.json").write_text(
            json.dumps(
                {
                    "registry_version": 1,
                    "focused_topic_slug": "alpha-topic",
                    "updated_at": "2026-04-04T14:00:00+08:00",
                    "updated_by": "test",
                    "source": "test",
                    "topics": [
                        {
                            "topic_slug": "alpha-topic",
                            "status": "blocked",
                            "operator_status": "paused",
                            "priority": 0,
                            "last_activity": "2026-04-04T14:00:00+08:00",
                            "runtime_root": str(topic_root),
                            "lane": "code_method",
                            "focus_state": "focused",
                            "projection_status": "missing",
                            "blocked_by": [],
                            "summary": "Alpha",
                        }
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.resume_topic(topic_slug="alpha-topic", updated_by="test", human_request="恢复 alpha-topic")

        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["focused_topic_slug"], "alpha-topic")
        registry_payload = json.loads((runtime_root / "active_topics.json").read_text(encoding="utf-8"))
        alpha_row = next(row for row in registry_payload["topics"] if row["topic_slug"] == "alpha-topic")
        self.assertEqual(alpha_row["operator_status"], "ready")

    def test_route_codex_chat_request_detects_multi_topic_management_intents(self) -> None:
        topic_index_path = self.kernel_root / "runtime" / "topic_index.jsonl"
        topic_index_path.parent.mkdir(parents=True, exist_ok=True)
        topic_index_path.write_text(
            json.dumps({"topic_slug": "alpha-topic", "updated_at": "2026-04-04T10:00:00+08:00"}, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        alpha_root = self.kernel_root / "runtime" / "topics" / "alpha-topic"
        alpha_root.mkdir(parents=True, exist_ok=True)
        (alpha_root / "topic_state.json").write_text(
            json.dumps({"topic_slug": "alpha-topic", "latest_run_id": "run", "resume_stage": "L3"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (self.kernel_root / "runtime" / "current_topic.json").write_text(
            json.dumps({"topic_slug": "alpha-topic"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

        list_route = self.service.route_codex_chat_request(task="现在有哪些课题？")
        pause_route = self.service.route_codex_chat_request(task="暂停 alpha-topic")
        resume_route = self.service.route_codex_chat_request(task="恢复 alpha-topic")
        focus_route = self.service.route_codex_chat_request(task="切换到 alpha-topic")

        self.assertEqual(list_route["route"], "request_list_active_topics")
        self.assertEqual(pause_route["route"], "request_pause_topic")
        self.assertEqual(resume_route["route"], "request_resume_topic")
        self.assertEqual(focus_route["route"], "request_focus_topic")

    def test_start_chat_session_handles_topic_management_routes_without_running_loop(self) -> None:
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        topic_root = runtime_root / "topics" / "alpha-topic"
        topic_root.mkdir(parents=True, exist_ok=True)
        (topic_root / "topic_state.json").write_text(
            json.dumps({"topic_slug": "alpha-topic", "latest_run_id": "run", "resume_stage": "L3"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (runtime_root / "active_topics.json").write_text(
            json.dumps(
                {
                    "registry_version": 1,
                    "focused_topic_slug": "alpha-topic",
                    "updated_at": "2026-04-04T14:00:00+08:00",
                    "updated_by": "test",
                    "source": "test",
                    "topics": [
                        {
                            "topic_slug": "alpha-topic",
                            "status": "ready",
                            "operator_status": "",
                            "priority": 0,
                            "last_activity": "2026-04-04T14:00:00+08:00",
                            "runtime_root": str(topic_root),
                            "lane": "code_method",
                            "focus_state": "focused",
                            "projection_status": "missing",
                            "blocked_by": [],
                            "summary": "Alpha",
                        }
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.start_chat_session(task="现在有哪些课题？", updated_by="test")

        self.assertEqual(payload["routing"]["route"], "request_list_active_topics")
        self.assertIn("topic_management", payload)
        self.assertNotIn("loop_state_path", payload)

    def test_new_topic_keeps_existing_registry_rows_and_adds_new_topic(self) -> None:
        service = _TopicCreationStubService(kernel_root=self.kernel_root, repo_root=self.repo_root)
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        existing_root = runtime_root / "topics" / "existing-topic"
        existing_root.mkdir(parents=True, exist_ok=True)
        (existing_root / "topic_state.json").write_text(
            json.dumps({"topic_slug": "existing-topic", "latest_run_id": "old-run", "resume_stage": "L3"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (runtime_root / "active_topics.json").write_text(
            json.dumps(
                {
                    "registry_version": 1,
                    "focused_topic_slug": "existing-topic",
                    "updated_at": "2026-04-04T14:00:00+08:00",
                    "updated_by": "test",
                    "source": "test",
                    "topics": [
                        {
                            "topic_slug": "existing-topic",
                            "status": "ready",
                            "operator_status": "",
                            "priority": 0,
                            "last_activity": "2026-04-04T14:00:00+08:00",
                            "runtime_root": str(existing_root),
                            "lane": "code_method",
                            "focus_state": "focused",
                            "projection_status": "missing",
                            "blocked_by": [],
                            "summary": "Existing topic",
                        }
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = service.new_topic(
            topic="Fresh Topic",
            question="Open a bounded new topic",
            updated_by="test",
            human_request="开一个新课题：Fresh Topic",
        )

        self.assertEqual(payload["topic_slug"], "fresh-topic")
        registry_payload = json.loads((runtime_root / "active_topics.json").read_text(encoding="utf-8"))
        topic_slugs = {row["topic_slug"] for row in registry_payload["topics"]}
        self.assertEqual(topic_slugs, {"existing-topic", "fresh-topic"})
        self.assertEqual(registry_payload["focused_topic_slug"], "fresh-topic")

    def test_set_and_clear_topic_dependency_updates_registry_details(self) -> None:
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        for topic_slug in ("alpha-topic", "beta-topic"):
            topic_root = runtime_root / "topics" / topic_slug
            topic_root.mkdir(parents=True, exist_ok=True)
            (topic_root / "topic_state.json").write_text(
                json.dumps({"topic_slug": topic_slug, "latest_run_id": "run", "resume_stage": "L3"}, ensure_ascii=True, indent=2) + "\n",
                encoding="utf-8",
            )
        (runtime_root / "active_topics.json").write_text(
            json.dumps(
                {
                    "registry_version": 1,
                    "focused_topic_slug": "alpha-topic",
                    "updated_at": "2026-04-04T15:00:00+08:00",
                    "updated_by": "test",
                    "source": "test",
                    "topics": [
                        {
                            "topic_slug": "alpha-topic",
                            "status": "ready",
                            "operator_status": "",
                            "priority": 0,
                            "last_activity": "2026-04-04T15:00:00+08:00",
                            "runtime_root": str(runtime_root / "topics" / "alpha-topic"),
                            "lane": "code_method",
                            "focus_state": "focused",
                            "projection_status": "missing",
                            "blocked_by": [],
                            "blocked_by_details": [],
                            "summary": "Alpha",
                        },
                        {
                            "topic_slug": "beta-topic",
                            "status": "ready",
                            "operator_status": "",
                            "priority": 0,
                            "last_activity": "2026-04-04T14:00:00+08:00",
                            "runtime_root": str(runtime_root / "topics" / "beta-topic"),
                            "lane": "formal_theory",
                            "focus_state": "background",
                            "projection_status": "missing",
                            "blocked_by": [],
                            "blocked_by_details": [],
                            "summary": "Beta",
                        },
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        blocked = self.service.set_topic_dependency(
            topic_slug="alpha-topic",
            blocked_by_topic_slug="beta-topic",
            reason="Need the bounded Jones route first.",
            updated_by="test",
        )
        self.assertEqual(blocked["status"], "dependency_blocked")
        self.assertEqual(blocked["blocked_by"], ["beta-topic"])
        self.assertEqual(blocked["blocked_by_details"][0]["reason"], "Need the bounded Jones route first.")

        cleared = self.service.clear_topic_dependency(
            topic_slug="alpha-topic",
            blocked_by_topic_slug="beta-topic",
            updated_by="test",
        )
        self.assertEqual(cleared["status"], "dependency_cleared")
        self.assertEqual(cleared["blocked_by"], [])

    def test_topic_status_and_dashboard_expose_dependency_state(self) -> None:
        self._write_runtime_state()
        runtime_root = self.kernel_root / "runtime"
        registry_root = runtime_root / "topics" / "demo-topic"
        (runtime_root / "active_topics.json").write_text(
            json.dumps(
                {
                    "registry_version": 1,
                    "focused_topic_slug": "demo-topic",
                    "updated_at": "2026-04-04T15:00:00+08:00",
                    "updated_by": "test",
                    "source": "test",
                    "topics": [
                        {
                            "topic_slug": "demo-topic",
                            "status": "ready",
                            "operator_status": "",
                            "priority": 0,
                            "last_activity": "2026-04-04T15:00:00+08:00",
                            "runtime_root": str(registry_root),
                            "lane": "code_method",
                            "focus_state": "focused",
                            "projection_status": "missing",
                            "blocked_by": ["other-topic"],
                            "blocked_by_details": [
                                {"topic_slug": "other-topic", "reason": "Need the prerequisite benchmark first."}
                            ],
                            "summary": "Demo",
                        }
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        shell_payload = self.service.ensure_topic_shell_surfaces(topic_slug="demo-topic", updated_by="test")
        status_payload = self.service.topic_status(topic_slug="demo-topic", updated_by="test")
        dashboard_text = Path(shell_payload["topic_dashboard_path"]).read_text(encoding="utf-8")

        self.assertEqual(status_payload["dependency_state"]["status"], "dependency_blocked")
        self.assertIn("other-topic", status_payload["dependency_state"]["blocked_by"])
        self.assertIn("## Dependencies", dashboard_text)
        self.assertIn("Need the prerequisite benchmark first.", dashboard_text)

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

    def test_route_codex_chat_request_projection_hint_does_not_override_current_topic(self) -> None:
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        self._write_runtime_state(topic_slug="alpha-topic", run_id="run-alpha")
        self._write_available_projection(
            topic_slug="beta-topic",
            lane="code_method",
            summary="Validated reusable benchmark-first code-method route for bounded algorithm implementation.",
            required_first_routes=["Close the benchmark-first route before broader workflow claims."],
        )
        (runtime_root / "current_topic.json").write_text(
            json.dumps({"topic_slug": "alpha-topic"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (runtime_root / "active_topics.json").write_text(
            json.dumps(
                {
                    "registry_version": 1,
                    "focused_topic_slug": "alpha-topic",
                    "updated_at": "2026-04-04T10:00:00+08:00",
                    "updated_by": "test",
                    "source": "test",
                    "topics": [
                        {
                            "topic_slug": "alpha-topic",
                            "status": "ready",
                            "operator_status": "",
                            "priority": 0,
                            "last_activity": "2026-04-04T10:00:00+08:00",
                            "runtime_root": str(runtime_root / "topics" / "alpha-topic"),
                            "lane": "formal_theory",
                            "resume_stage": "L3",
                            "run_id": "run-alpha",
                            "projection_status": "missing",
                            "projection_note_path": None,
                            "blocked_by": [],
                            "focus_state": "focused",
                            "summary": "Alpha current topic.",
                        },
                        {
                            "topic_slug": "beta-topic",
                            "status": "active",
                            "operator_status": "",
                            "priority": 0,
                            "last_activity": "2026-04-04T11:00:00+08:00",
                            "runtime_root": str(runtime_root / "topics" / "beta-topic"),
                            "lane": "code_method",
                            "resume_stage": "L3",
                            "run_id": "run-001",
                            "projection_status": "available",
                            "projection_note_path": "runtime/topics/beta-topic/topic_skill_projection.active.md",
                            "blocked_by": [],
                            "focus_state": "background",
                            "summary": "Reusable benchmark-first code route.",
                        },
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        routing = self.service.route_codex_chat_request(
            task="I want the benchmark-first code method implementation route.",
        )

        self.assertEqual(routing["route"], "implicit_current_topic")
        self.assertEqual(routing["topic_slug"], "alpha-topic")
        self.assertEqual(routing["projection_routing"]["matched_topic_slug"], "beta-topic")
        self.assertFalse(routing["projection_routing"]["used"])

    def test_route_codex_chat_request_projection_hint_can_select_topic_without_current_focus(self) -> None:
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        self._write_runtime_state(topic_slug="alpha-topic", run_id="run-alpha")
        self._write_available_projection(
            topic_slug="beta-topic",
            lane="formal_theory",
            summary="Validated reusable theorem-facing formal-theory route for operator algebra derivation.",
            required_first_routes=["Read the formal theorem route before reusing the proof lane."],
        )
        (runtime_root / "active_topics.json").write_text(
            json.dumps(
                {
                    "registry_version": 1,
                    "focused_topic_slug": "",
                    "updated_at": "2026-04-04T10:00:00+08:00",
                    "updated_by": "test",
                    "source": "test",
                    "topics": [
                        {
                            "topic_slug": "alpha-topic",
                            "status": "ready",
                            "operator_status": "",
                            "priority": 0,
                            "last_activity": "2026-04-04T12:00:00+08:00",
                            "runtime_root": str(runtime_root / "topics" / "alpha-topic"),
                            "lane": "toy_model",
                            "resume_stage": "L3",
                            "run_id": "run-alpha",
                            "projection_status": "missing",
                            "projection_note_path": None,
                            "blocked_by": [],
                            "focus_state": "background",
                            "summary": "Alpha topic.",
                        },
                        {
                            "topic_slug": "beta-topic",
                            "status": "active",
                            "operator_status": "",
                            "priority": 0,
                            "last_activity": "2026-04-04T11:00:00+08:00",
                            "runtime_root": str(runtime_root / "topics" / "beta-topic"),
                            "lane": "formal_theory",
                            "resume_stage": "L3",
                            "run_id": "run-001",
                            "projection_status": "available",
                            "projection_note_path": "runtime/topics/beta-topic/topic_skill_projection.active.md",
                            "blocked_by": [],
                            "focus_state": "background",
                            "summary": "Reusable theorem route.",
                        },
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        routing = self.service.route_codex_chat_request(
            task="I want the theorem-facing formal proof route with operator algebra structure.",
        )

        self.assertEqual(routing["route"], "projection_matched_topic")
        self.assertEqual(routing["topic_slug"], "beta-topic")
        self.assertTrue(routing["projection_routing"]["used"])
        self.assertEqual(routing["projection_routing"]["decision"], "selected_projection_match")

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
        self.assertIn("collaborator_profile_note_path", session_contract["artifacts"])
        self.assertIn("research_trajectory_note_path", session_contract["artifacts"])
        self.assertIn("mode_learning_note_path", session_contract["artifacts"])
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

    def test_audit_analytical_review_writes_durable_artifact_and_updates_candidate(self) -> None:
        self._write_runtime_state()
        self._write_candidate(
            candidate_type="concept",
            intended_l2_target="concept:demo-analytical-concept",
            title="Demo Analytical Concept",
        )

        payload = self.service.audit_analytical_review(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            checks=[
                {
                    "kind": "limiting_case",
                    "label": "weak-coupling",
                    "status": "passed",
                    "notes": "Matches the known free limit from the source.",
                },
                {
                    "kind": "dimensional_consistency",
                    "label": "gap-scaling",
                    "status": "passed",
                    "notes": "Units remain dimensionless after rescaling.",
                },
            ],
            source_anchors=["paper:demo-source#sec:intro"],
            assumption_refs=["assumption:weak-coupling-regime"],
            regime_note="Bounded to the weak-coupling regime recorded in the source.",
            reading_depth="targeted",
            summary="Analytical checks stay consistent with the source-backed weak-coupling route.",
        )

        analytical_review_path = Path(payload["paths"]["analytical_review"])
        self.assertTrue(analytical_review_path.exists())
        review_payload = json.loads(analytical_review_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["overall_status"], "ready")
        self.assertEqual(review_payload["overall_status"], "ready")
        self.assertEqual(review_payload["reading_depth"], "targeted")
        self.assertEqual(review_payload["source_anchors"], ["paper:demo-source#sec:intro"])
        self.assertEqual(review_payload["checks"][0]["kind"], "limiting_case")

        candidate_rows = [
            json.loads(line)
            for line in (
                self.kernel_root
                / "feedback"
                / "topics"
                / "demo-topic"
                / "runs"
                / "2026-03-13-demo"
                / "candidate_ledger.jsonl"
            ).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(candidate_rows[0]["analytical_review_overall_status"], "ready")
        self.assertIn("analytical_review", candidate_rows[0]["theory_packet_refs"])

    def test_ensure_topic_shell_surfaces_materializes_primary_validation_review_bundle(self) -> None:
        self._write_runtime_state()
        self._write_candidate(
            candidate_type="theorem_card",
            intended_l2_target="theorem:demo-topological-theorem",
            title="Demo Topological Theorem",
        )
        self.service.audit_theory_coverage(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            source_sections=["sec:intro"],
            covered_sections=["sec:intro"],
            equation_labels=["eq:1"],
            notation_bindings=[{"symbol": "H", "meaning": "Hamiltonian"}],
            derivation_nodes=["def:h", "eq:1"],
            agent_votes=[{"role": "skeptic", "verdict": "no_major_gap", "notes": ""}],
            consensus_status="unanimous",
            critical_unit_recall=1.0,
            missing_anchor_count=0,
            skeptic_major_gap_count=0,
        )
        self.service.audit_formal_theory(
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
            provenance_kind="adapted_existing_formalization",
            attribution_requirements=["Preserve upstream theorem citation."],
            provenance_sources=["physlib:demo/theorem.lean@abc1234"],
            prerequisite_closure_status="closed",
            lean_prerequisite_ids=["physlib:chern-number"],
            supporting_obligation_ids=["proof_obligation:demo-topological-theorem"],
        )

        payload = self.service.ensure_topic_shell_surfaces(
            topic_slug="demo-topic",
            updated_by="test",
        )

        review_bundle = payload["validation_review_bundle"]
        self.assertEqual(review_bundle["primary_review_kind"], "formal_theory_review")
        self.assertEqual(review_bundle["status"], "ready")
        artifact_kinds = {row["artifact_kind"] for row in review_bundle["specialist_artifacts"]}
        self.assertIn("formal_theory_review", artifact_kinds)
        self.assertIn("coverage_ledger", artifact_kinds)
        review_note = Path(payload["validation_review_bundle_note_path"]).read_text(encoding="utf-8")
        self.assertIn("formal_theory_review", review_note)

    def test_prepare_verification_analytical_uses_analytical_review_as_primary_bundle(self) -> None:
        self._write_runtime_state()
        self._write_candidate(
            candidate_type="concept",
            intended_l2_target="concept:demo-analytical-concept",
            title="Demo Analytical Concept",
        )
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
        self.service.audit_analytical_review(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            checks=[
                {
                    "kind": "limiting_case",
                    "label": "weak-coupling",
                    "status": "passed",
                    "notes": "Matches the source-backed limit.",
                }
            ],
            source_anchors=["paper:demo-source#sec:intro"],
            assumption_refs=["assumption:weak-coupling-regime"],
            regime_note="Weak-coupling only.",
            reading_depth="targeted",
        )

        verification_payload = self.service.prepare_verification(
            topic_slug="demo-topic",
            mode="analytical",
        )

        review_bundle_path = (
            self.kernel_root / "runtime" / "topics" / "demo-topic" / "validation_review_bundle.active.json"
        )
        review_note_path = (
            self.kernel_root / "runtime" / "topics" / "demo-topic" / "validation_review_bundle.active.md"
        )
        review_bundle = json.loads(review_bundle_path.read_text(encoding="utf-8"))
        self.assertEqual(verification_payload["validation_contract"]["validation_mode"], "analytical")
        self.assertEqual(review_bundle["validation_mode"], "analytical")
        self.assertEqual(review_bundle["primary_review_kind"], "analytical_review")
        artifact_kinds = {row["artifact_kind"] for row in review_bundle["specialist_artifacts"]}
        self.assertIn("analytical_review", artifact_kinds)
        self.assertIn("coverage_ledger", artifact_kinds)
        self.assertIn("analytical_review", review_note_path.read_text(encoding="utf-8"))

    def test_render_validation_review_bundle_markdown_lists_entrypoints_and_artifacts(self) -> None:
        markdown = self.service._render_validation_review_bundle_markdown(
            {
                "topic_slug": "demo-topic",
                "run_id": "2026-04-04-demo",
                "status": "blocked",
                "primary_review_kind": "formal_theory_review",
                "validation_mode": "formal",
                "promotion_readiness_status": "not_ready",
                "topic_completion_status": "not_assessed",
                "promotion_gate_status": "not_requested",
                "summary": "Primary L4 review surface is blocked on a formal audit.",
                "entrypoints": {
                    "validation_contract_path": "runtime/topics/demo-topic/validation.contract.json",
                    "validation_contract_note_path": "runtime/topics/demo-topic/validation.contract.md",
                    "promotion_readiness_path": "runtime/topics/demo-topic/promotion_readiness.json",
                    "promotion_readiness_note_path": "runtime/topics/demo-topic/promotion_readiness.md",
                    "topic_completion_path": "runtime/topics/demo-topic/topic_completion.json",
                    "topic_completion_note_path": "runtime/topics/demo-topic/topic_completion.md",
                    "gap_map_path": "runtime/topics/demo-topic/gap_map.md",
                    "promotion_gate_path": None,
                },
                "candidate_ids": ["candidate:demo-candidate"],
                "blockers": ["formal_theory_review=not_ready"],
                "specialist_artifacts": [
                    {
                        "artifact_kind": "formal_theory_review",
                        "candidate_id": "candidate:demo-candidate",
                        "status": "not_ready",
                        "path": "validation/topics/demo-topic/runs/2026-04-04-demo/theory-packets/candidate-demo-candidate/formal_theory_review.json",
                    }
                ],
            }
        )

        self.assertIn("# Validation review bundle", markdown)
        self.assertIn("validation_contract_path", markdown)
        self.assertIn("candidate:demo-candidate", markdown)
        self.assertIn("formal_theory_review=not_ready", markdown)
        self.assertIn("formal_theory_review", markdown)

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
        runtime_root = self._write_runtime_state(topic_slug=topic_slug)
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "Select exactly one validation route for the current topic.",
                    "decision_surface": {
                        "decision_mode": "continue_unfinished",
                        "decision_source": "heuristic",
                        "selected_action_id": "action:demo-topic:generic:01",
                    },
                    "action_queue_surface": {"queue_source": "heuristic"},
                    "human_edit_surfaces": [],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
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
                    "summary": "Select exactly one validation route for the current topic.",
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
        self.assertIn("session-start.py", installed_paths)
        self.assertIn("run-hook.cmd", installed_paths)
        self.assertIn("hooks.json", installed_paths)
        self.assertIn("settings.json", installed_paths)
        claude_using_skill_path = claude_target / ".claude" / "skills" / "using-aitp" / "SKILL.md"
        claude_skill_path = claude_target / ".claude" / "skills" / "aitp-runtime" / "SKILL.md"
        claude_hook_path = claude_target / ".claude" / "hooks" / "session-start"
        claude_python_hook_path = claude_target / ".claude" / "hooks" / "session-start.py"
        claude_run_hook_path = claude_target / ".claude" / "hooks" / "run-hook.cmd"
        claude_hooks_json_path = claude_target / ".claude" / "hooks" / "hooks.json"
        claude_settings_path = claude_target / ".claude" / "settings.json"
        canonical_claude_hook = (self.package_root.parent.parent / "hooks" / "session-start").read_text(encoding="utf-8")
        canonical_claude_python_hook = (self.package_root.parent.parent / "hooks" / "session-start.py").read_text(encoding="utf-8")
        canonical_claude_run_hook = (self.package_root.parent.parent / "hooks" / "run-hook.cmd").read_text(encoding="utf-8")
        canonical_claude_hooks_json = (self.package_root.parent.parent / "hooks" / "hooks.json").read_text(encoding="utf-8")
        self.assertTrue(claude_using_skill_path.exists())
        self.assertTrue(claude_skill_path.exists())
        self.assertTrue(claude_hook_path.exists())
        self.assertTrue(claude_python_hook_path.exists())
        self.assertTrue(claude_run_hook_path.exists())
        self.assertTrue(claude_hooks_json_path.exists())
        self.assertTrue(claude_settings_path.exists())
        self.assertEqual(claude_using_skill_path.read_text(encoding="utf-8"), canonical_using_skill)
        self.assertEqual(claude_skill_path.read_text(encoding="utf-8"), canonical_runtime_skill)
        self.assertEqual(claude_hook_path.read_text(encoding="utf-8"), canonical_claude_hook)
        self.assertEqual(claude_python_hook_path.read_text(encoding="utf-8"), canonical_claude_python_hook)
        self.assertEqual(claude_run_hook_path.read_text(encoding="utf-8"), canonical_claude_run_hook)
        self.assertEqual(claude_hooks_json_path.read_text(encoding="utf-8"), canonical_claude_hooks_json)
        settings_payload = json.loads(claude_settings_path.read_text(encoding="utf-8"))
        self.assertIn("SessionStart", settings_payload["hooks"])
        self.assertFalse((claude_target / ".claude" / "commands").exists())
