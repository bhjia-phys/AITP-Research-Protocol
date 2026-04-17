from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


def _bootstrap_path() -> Path:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    return package_root


def _load_runtime_script_module(module_name: str, relative_path: str):
    package_root = _bootstrap_path()
    target_path = package_root / relative_path
    if str(target_path.parent) not in sys.path:
        sys.path.insert(0, str(target_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, target_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {target_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_bootstrap_path()

from knowledge_hub.runtime_bundle_support import runtime_protocol_markdown  # noqa: E402
from knowledge_hub.runtime_read_path_support import empty_l1_vault, empty_source_intelligence  # noqa: E402


class RuntimePathHygieneContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[3]
        cls.orchestrator_contract_support = _load_runtime_script_module(
            "aitp_orchestrator_contract_support_hygiene_test",
            "runtime/scripts/orchestrator_contract_support.py",
        )

    def test_repo_gitignore_declares_local_generated_runtime_surfaces(self) -> None:
        gitignore_text = (self.repo_root / ".gitignore").read_text(encoding="utf-8")

        for snippet in (
            "research/knowledge-hub/runtime/current_topic.json",
            "research/knowledge-hub/runtime/current_topic.md",
            "research/knowledge-hub/runtime/theory_metrics/",
            "research/knowledge-hub/canonical/compiled/",
            "research/knowledge-hub/canonical/hygiene/",
            "research/knowledge-hub/canonical/index.jsonl",
            "research/knowledge-hub/canonical/edges.jsonl",
            "research/knowledge-hub/canonical/staging/entries/",
            "research/knowledge-hub/canonical/staging/staging_index.jsonl",
            "research/knowledge-hub/canonical/staging/workspace_staging_manifest.json",
            "research/knowledge-hub/canonical/staging/workspace_staging_manifest.md",
            "research/knowledge-hub/topics/",
        ):
            self.assertIn(snippet, gitignore_text)

    def test_local_generated_runtime_surfaces_are_not_git_tracked(self) -> None:
        local_only_paths = (
            "research/knowledge-hub/runtime/current_topic.json",
            "research/knowledge-hub/runtime/current_topic.md",
            "research/knowledge-hub/runtime/theory_metrics/analysis.latest.json",
            "research/knowledge-hub/runtime/theory_metrics/analysis.latest.md",
            "research/knowledge-hub/runtime/theory_metrics/theory_operations.jsonl",
            "research/knowledge-hub/canonical/compiled/workspace_graph_report.json",
            "research/knowledge-hub/canonical/compiled/workspace_graph_report.md",
            "research/knowledge-hub/canonical/compiled/workspace_knowledge_report.json",
            "research/knowledge-hub/canonical/compiled/workspace_knowledge_report.md",
            "research/knowledge-hub/canonical/compiled/workspace_memory_map.json",
            "research/knowledge-hub/canonical/compiled/workspace_memory_map.md",
            "research/knowledge-hub/canonical/compiled/derived_navigation/index.md",
            "research/knowledge-hub/canonical/index.jsonl",
            "research/knowledge-hub/canonical/edges.jsonl",
            "research/knowledge-hub/canonical/staging/entries/demo-topic-workflow-draft-1b93bab2.json",
            "research/knowledge-hub/canonical/staging/staging_index.jsonl",
            "research/knowledge-hub/canonical/staging/workspace_staging_manifest.json",
            "research/knowledge-hub/canonical/staging/workspace_staging_manifest.md",
        )

        for relative_path in local_only_paths:
            completed = subprocess.run(
                ["git", "ls-files", "--error-unmatch", "--", relative_path],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(
                completed.returncode,
                0,
                msg=f"Expected `{relative_path}` to remain local-only, but git still tracks it.",
            )

    def test_runtime_read_path_defaults_use_topic_truth_root_refs(self) -> None:
        source_intelligence = empty_source_intelligence(topic_slug="demo-topic")
        l1_vault = empty_l1_vault(topic_slug="demo-topic")

        self.assertEqual(
            source_intelligence["path"],
            "topics/demo-topic/runtime/source_intelligence.json",
        )
        self.assertEqual(
            source_intelligence["note_path"],
            "topics/demo-topic/runtime/source_intelligence.md",
        )
        self.assertEqual(
            l1_vault["root_path"],
            "topics/demo-topic/L1/vault",
        )
        self.assertEqual(
            l1_vault["wiki"]["home_page_path"],
            "topics/demo-topic/L1/vault/wiki/home.md",
        )

    def test_runtime_protocol_markdown_uses_topic_truth_root_refs(self) -> None:
        payload = {
            "topic_slug": "demo-topic",
            "updated_at": "2026-04-15T00:00:00+08:00",
            "updated_by": "test",
            "bundle_kind": "progressive_disclosure_runtime_bundle",
            "$schema": "runtime/schemas/progressive-disclosure-runtime-bundle.schema.json",
            "human_request": "continue this topic",
            "resume_stage": "L3",
            "last_materialized_stage": "L3",
            "research_mode": "toy_model",
            "load_profile": "light",
            "runtime_mode": "explore",
            "active_submode": None,
            "topic_synopsis": {
                "path": "topics/demo-topic/runtime/topic_synopsis.json",
                "runtime_focus": {},
                "truth_sources": {
                    "topic_state_path": "topics/demo-topic/runtime/topic_state.json",
                    "research_question_contract_path": "topics/demo-topic/runtime/research_question.contract.json",
                    "next_action_surface_path": "topics/demo-topic/runtime/action_queue.jsonl",
                    "human_need_surface_path": "topics/demo-topic/runtime/operator_checkpoint.active.json",
                    "dependency_registry_path": "topics/demo-topic/runtime/topic_state.json",
                    "promotion_readiness_path": "topics/demo-topic/runtime/promotion_readiness.md",
                    "promotion_gate_path": None,
                },
            },
            "pending_decisions": {},
            "minimal_execution_brief": {},
            "active_research_contract": {},
            "idea_packet": {},
            "operator_checkpoint": {},
            "promotion_readiness": {},
            "validation_review_bundle": {},
            "open_gap_summary": {},
            "strategy_memory": {},
            "source_intelligence": {},
            "graph_analysis": {},
            "theory_context_injection": {},
            "loop_detection": {},
            "protocol_manifest": {},
            "control_plane": {},
            "topic_skill_projection": {},
            "topic_completion": {},
            "statement_compilation": {},
            "lean_bridge": {},
            "must_read_now": [],
            "active_hard_constraints": [],
            "escalation_triggers": [],
            "may_defer_until_trigger": [],
            "recommended_protocol_slices": [],
            "python_runtime_scope": [
                "Materialize durable state.",
            ],
            "agent_required_read_order": [
                "topics/demo-topic/runtime/topic_dashboard.md",
            ],
            "priority_rules": [
                {
                    "source": "runtime_truth_model",
                    "rule": "Prefer truth-root runtime surfaces.",
                }
            ],
            "reproducibility_expectations": [],
            "note_expectations": [],
            "backend_bridges": [],
            "promotion_gate": {},
            "delivery_rule": "",
            "editable_protocol_surfaces": [],
            "action_queue_surface": {},
            "decision_surface": {},
            "pending_actions": [],
            "mode_envelope": {"mode": "explore"},
            "transition_posture": {"transition_kind": "boundary_hold", "requires_human_checkpoint": False, "triggered_by": []},
            "h_plane": {"overall_status": "steady", "steering": {}, "checkpoint": {}, "approval": {}},
            "autonomy_posture": {
                "mode": "continuous_bounded_loop",
                "can_continue_without_human": True,
                "requested_max_auto_steps": None,
                "applied_max_auto_steps": None,
                "budget_reason": "",
                "summary": "Continue bounded work.",
            },
            "human_interaction_posture": {
                "overall_status": "steady",
                "requires_human_input_now": False,
                "steering_status": "none",
                "checkpoint_status": "cancelled",
                "approval_status": "not_requested",
                "summary": "No active human checkpoint is currently blocking the bounded loop.",
                "next_action": "Continue the bounded loop.",
            },
        }

        note_text = runtime_protocol_markdown(payload)

        self.assertIn("Primary human render: `topics/demo-topic/runtime/topic_dashboard.md`", note_text)
        self.assertIn("JSON path: `topics/demo-topic/runtime/transition_history.json`", note_text)
        self.assertIn("Note path: `topics/demo-topic/runtime/transition_history.md`", note_text)

    def test_orchestrator_queue_meta_uses_topic_truth_root_refs(self) -> None:
        enriched = self.orchestrator_contract_support.enrich_queue_meta(
            {},
            topic_slug="demo-topic",
            runtime_contract={"runtime_mode": "explore"},
            operator_checkpoint={"status": "requested"},
            append_policy_reason="checkpoint active",
        )

        self.assertEqual(
            enriched["runtime_contract_path"],
            "topics/demo-topic/runtime/runtime_protocol.generated.json",
        )
        self.assertEqual(
            enriched["operator_checkpoint_path"],
            "topics/demo-topic/runtime/operator_checkpoint.active.json",
        )

    def test_checked_in_contract_docs_reference_topic_truth_root(self) -> None:
        steering_doc = (
            self.repo_root
            / "docs"
            / "HUMAN_IDEA_AI_EXECUTION_STEERING_PROTOCOL_VNEXT.md"
        ).read_text(encoding="utf-8")
        workflow_doc = (
            self.repo_root
            / "docs"
            / "AITP_GSD_WORKFLOW_CONTRACT.md"
        ).read_text(encoding="utf-8")

        self.assertIn("`topics/<topic_slug>/runtime/idea_packet.json`", steering_doc)
        self.assertIn("`topics/<topic_slug>/runtime/operator_checkpoint.active.md`", steering_doc)
        self.assertIn("`topics/<topic_slug>/L3/runs/<run_id>/strategy_memory.jsonl`", steering_doc)
        self.assertIn("`topics/<topic_slug>/runtime/**`", workflow_doc)
        self.assertIn("`topics/<topic_slug>/L4/**`", workflow_doc)

    def test_top_level_protocol_docs_make_markdown_human_authority_explicit(self) -> None:
        steering_doc = (
            self.repo_root
            / "docs"
            / "HUMAN_IDEA_AI_EXECUTION_STEERING_PROTOCOL_VNEXT.md"
        ).read_text(encoding="utf-8")
        workflow_doc = (
            self.repo_root
            / "docs"
            / "AITP_GSD_WORKFLOW_CONTRACT.md"
        ).read_text(encoding="utf-8")
        project_index = (
            self.repo_root
            / "docs"
            / "PROJECT_INDEX.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Markdown is the human authority", steering_doc)
        self.assertIn("JSON remains the machine-facing companion", steering_doc)
        self.assertIn("topic-owned truth root", workflow_doc)
        self.assertIn("TOPIC_TRUTH_ROOT_CONTRACT.md", project_index)

    def test_install_docs_make_local_kernel_and_public_repo_boundary_explicit(self) -> None:
        install_doc = (self.repo_root / "docs" / "INSTALL.md").read_text(encoding="utf-8")
        quickstart_doc = (self.repo_root / "docs" / "QUICKSTART.md").read_text(encoding="utf-8")
        migration_doc = (self.repo_root / "docs" / "MIGRATE_LOCAL_INSTALL.md").read_text(encoding="utf-8")
        project_index = (self.repo_root / "docs" / "PROJECT_INDEX.md").read_text(encoding="utf-8")

        self.assertIn("`~/.aitp/kernel`", install_doc)
        self.assertIn("repo itself should stay project code, protocol, and public docs only", install_doc)
        self.assertIn("`--kernel-root <path>`", quickstart_doc)
        self.assertIn("`~/.aitp/kernel`", migration_doc)
        self.assertIn("local-only compatibility projection", project_index.lower())

    def test_active_runtime_contract_docs_follow_truth_root_and_markdown_authority(self) -> None:
        checks = {
            self.repo_root / "research" / "knowledge-hub" / "runtime" / "PROGRESSIVE_DISCLOSURE_PROTOCOL.md": [
                "topics/<topic_slug>/runtime/runtime_protocol.generated.json",
                "Markdown is the human authority",
                "JSON remains the machine-facing companion",
            ],
            self.repo_root / "research" / "knowledge-hub" / "runtime" / "INNOVATION_DIRECTION_TEMPLATE.md": [
                "topics/<topic_slug>/runtime/innovation_direction.md",
            ],
            self.repo_root / "research" / "knowledge-hub" / "runtime" / "DECLARATIVE_RUNTIME_CONTRACTS.md": [
                "topics/<topic_slug>/L3/runs/<run_id>/next_actions.contract.json",
                "topics/<topic_slug>/runtime/next_action_decision.contract.json",
                "topics/<topic_slug>/runtime/deferred_candidates.json",
                "topics/<topic_slug>/runtime/runtime_protocol.generated.json",
                "topics/my-topic/runtime/runtime_protocol.generated.md",
                "topics/my-topic/consultation/consultation_index.jsonl",
            ],
            self.repo_root / "research" / "knowledge-hub" / "runtime" / "DEFERRED_RUNTIME_CONTRACTS.md": [
                "topics/<topic_slug>/runtime/deferred_candidates.json",
                "topics/<topic_slug>/runtime/followup_subtopics.jsonl",
            ],
            self.repo_root / "research" / "knowledge-hub" / "runtime" / "CONTROL_NOTE_CONTRACT.md": [
                "topics/my-topic/L3/runs/2026-03-15-run/next_actions.md",
            ],
            self.repo_root / "research" / "knowledge-hub" / "runtime" / "README.md": [
                "topics/<topic_slug>/runtime/topic_state.json",
                "topics/<topic_slug>/L4/runs/<run_id>/execution_notes/codex_session.json",
                "topics/<topic_slug>/L1/vault/raw|wiki|output",
                "topics/<topic_slug>/runtime/innovation_direction.md",
            ],
        }

        legacy_snippets = (
            "runtime/topics/<topic_slug>/",
            "feedback/topics/<topic_slug>/",
            "validation/topics/<topic_slug>/",
            "consultation/topics/<topic_slug>/",
            "source-layer/topics/<topic_slug>/",
            "intake/topics/<topic_slug>/",
        )

        for path, required_snippets in checks.items():
            text = path.read_text(encoding="utf-8")
            for snippet in required_snippets:
                self.assertIn(snippet, text, msg=f"Expected `{snippet}` in {path}")
            for legacy in legacy_snippets:
                self.assertNotIn(legacy, text, msg=f"Unexpected legacy snippet `{legacy}` in {path}")

    def test_core_runtime_surfaces_do_not_publish_legacy_topic_root_refs(self) -> None:
        checks = {
            self.repo_root / "research" / "knowledge-hub" / "knowledge_hub" / "graph_analysis_tools.py": [
                "topics/{topic_slug}/runtime/graph_analysis.json",
                "topics/{topic_slug}/runtime/graph_analysis.md",
            ],
            self.repo_root / "research" / "knowledge-hub" / "runtime" / "scripts" / "interaction_surface_support.py": [
                "topics/{topic_state['topic_slug']}/runtime/operator_console.md",
                "topics/{topic_state['topic_slug']}/runtime/interaction_state.json",
            ],
            self.repo_root / "research" / "knowledge-hub" / "runtime" / "scripts" / "decide_next_action.py": [
                "topics/{topic_state['topic_slug']}/runtime/{NEXT_ACTION_DECISION_CONTRACT_FILENAME}",
            ],
            self.repo_root / "research" / "knowledge-hub" / "knowledge_hub" / "exploration_session_support.py": [
                "topics/<topic_slug>/runtime/topic_state.json",
                "topics/<topic_slug>/runtime/operator_checkpoint.active.md",
            ],
            self.repo_root / "research" / "knowledge-hub" / "knowledge_hub" / "runtime_support_matrix.py": [
                "topics/<topic_slug>/runtime/topic_state.json",
                "topics/<topic_slug>/runtime/runtime_protocol.generated.md",
            ],
            self.repo_root / "research" / "knowledge-hub" / "knowledge_hub" / "kernel_templates.py": [
                "topics/<topic_slug>/runtime/runtime_protocol.generated.md",
            ],
            self.repo_root / "research" / "knowledge-hub" / "knowledge_hub" / "literature_intake_support.py": [
                "topics/{resolved_topic_slug}/L1/vault/wiki/source-intake.md",
            ],
            self.repo_root / "research" / "knowledge-hub" / "knowledge_hub" / "mode_envelope_support.py": [
                "topics/{topic_slug}/L1/vault/wiki/source-intake.md",
                "topics/{topic_slug}/L1/vault/wiki/open-questions.md",
                "topics/{topic_slug}/L1/vault/wiki/runtime-bridge.md",
            ],
            self.repo_root / "docs" / "QUICKSTART.md": [
                "topics/jones-chapter-4-finite-dimensional-backbone/runtime/",
            ],
            self.repo_root / "docs" / "MULTI_TOPIC_RUNTIME.md": [
                "topics/<topic_slug>/runtime/topic_dashboard.md",
            ],
            self.repo_root / "research" / "knowledge-hub" / "runtime" / "scripts" / "run_mode_enforcement_acceptance.py": [
                "topics/{topic_slug}/runtime/control_note.md",
                "topics/demo-discussion/runtime/operator_checkpoint.active.md",
                "topics/demo-verify/runtime/execution_task.md",
                "topics/demo-literature/L1/vault/wiki/source-intake.md",
            ],
            self.repo_root / "research" / "knowledge-hub" / "runtime" / "scripts" / "run_runtime_parity_acceptance.py": [
                "topics/{topic_slug}/runtime/topic_state.json",
                "topics/{topic_slug}/runtime/runtime_protocol.generated.md",
            ],
            self.repo_root / "research" / "knowledge-hub" / "runtime" / "scripts" / "run_scrpa_thesis_topic_acceptance.py": [
                "topics/{topic_slug}/runtime/topic_dashboard.md",
                "topics/{topic_slug}/runtime/research_question.contract.md",
                "topics/{topic_slug}/runtime/topic_synopsis.json",
            ],
        }

        for path, required_snippets in checks.items():
            text = path.read_text(encoding="utf-8")
            for snippet in required_snippets:
                self.assertIn(snippet, text, msg=f"Expected `{snippet}` in {path}")
            self.assertNotIn("runtime/topics/<topic_slug>/", text, msg=f"Unexpected legacy split-root path in {path}")


if __name__ == "__main__":
    unittest.main()
