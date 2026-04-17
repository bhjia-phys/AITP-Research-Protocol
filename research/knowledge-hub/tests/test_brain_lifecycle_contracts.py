from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from tests_support import copy_canonical_tree, make_temp_kernel
from knowledge_hub.aitp_service import AITPService
from knowledge_hub.decision_point_handler import emit_decision_point, resolve_decision_point
from knowledge_hub.decision_trace_handler import record_decision_trace
from knowledge_hub.session_chronicle_handler import (
    append_chronicle_action,
    append_chronicle_problem,
    finalize_chronicle,
    render_chronicle_markdown,
    start_chronicle,
)


class BrainLifecycleContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.package_root = PACKAGE_ROOT
        self.repo_root = Path(__file__).resolve().parents[3]
        self.fixture = make_temp_kernel("aitp-brain-lifecycle-")
        self.kernel_root = self.fixture.kernel_root
        copy_canonical_tree(self.package_root, self.kernel_root)

        kernel_schema_root = self.kernel_root / "schemas"
        kernel_schema_root.mkdir(parents=True, exist_ok=True)
        for schema_path in (self.package_root / "schemas").glob("*.json"):
            shutil.copyfile(schema_path, kernel_schema_root / schema_path.name)

        runtime_schema_root = self.kernel_root / "runtime" / "schemas"
        runtime_schema_root.mkdir(parents=True, exist_ok=True)
        for schema_path in (self.package_root / "runtime" / "schemas").glob("*.json"):
            shutil.copyfile(schema_path, runtime_schema_root / schema_path.name)

        shutil.copytree(
            self.package_root / "runtime" / "scripts",
            self.kernel_root / "runtime" / "scripts",
            dirs_exist_ok=True,
        )

        self.service = AITPService(kernel_root=self.kernel_root, repo_root=self.repo_root)

    def tearDown(self) -> None:
        self.fixture.cleanup()

    def _prepare_first_run_kernel(self) -> None:
        for dirname in ("source-layer", "intake", "feedback", "consultation", "validation"):
            (self.kernel_root / dirname).mkdir(parents=True, exist_ok=True)
        for name in (
            "closed_loop_policies.json",
            "research_mode_profiles.json",
            "CONTROL_NOTE_CONTRACT.md",
            "DECLARATIVE_RUNTIME_CONTRACTS.md",
            "DEFERRED_RUNTIME_CONTRACTS.md",
            "INNOVATION_DIRECTION_TEMPLATE.md",
            "PROGRESSIVE_DISCLOSURE_PROTOCOL.md",
        ):
            target = self.kernel_root / "runtime" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.package_root / "runtime" / name, target)
        for path in self.package_root.iterdir():
            if path.is_file() and path.suffix == ".md":
                shutil.copy2(path, self.kernel_root / path.name)

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            "-m",
            "knowledge_hub.aitp_cli",
            "--kernel-root",
            str(self.kernel_root),
            "--repo-root",
            str(self.repo_root),
            *args,
        ]
        return subprocess.run(
            command,
            cwd=self.package_root,
            capture_output=True,
            text=True,
            check=False,
        )

    def _write_runtime_state(
        self,
        topic_slug: str = "demo-topic",
        *,
        run_id: str = "2026-03-13-demo",
        updated_at: str = "2026-04-17T12:00:00+08:00",
    ) -> Path:
        runtime_root = self.kernel_root / "topics" / topic_slug / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "latest_run_id": run_id,
                    "resume_stage": "L3",
                    "updated_at": updated_at,
                    "summary": f"Runtime summary for {topic_slug}.",
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
        *,
        run_id: str = "2026-03-13-demo",
    ) -> None:
        feedback_root = self.kernel_root / "topics" / topic_slug / "L3" / "runs" / run_id
        feedback_root.mkdir(parents=True, exist_ok=True)
        (feedback_root / "candidate_ledger.jsonl").write_text(
            json.dumps(
                {
                    "candidate_id": "candidate:demo-candidate",
                    "candidate_type": "concept",
                    "title": "Demo Promoted Concept",
                    "summary": "A bounded demo concept for lifecycle testing.",
                    "topic_slug": topic_slug,
                    "run_id": run_id,
                    "origin_refs": [
                        {
                            "id": "paper:demo-source",
                            "layer": "L0",
                            "object_type": "source",
                            "path": f"topics/{topic_slug}/L0/source_index.jsonl",
                            "title": "Demo Source",
                            "summary": "Public source entry for lifecycle testing.",
                        }
                    ],
                    "question": "Can this candidate be promoted into the configured L2 backend?",
                    "assumptions": ["The example remains bounded and non-scientific."],
                    "proposed_validation_route": "bounded-smoke",
                    "intended_l2_targets": ["concept:demo-promoted-concept"],
                    "status": "ready_for_validation",
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )

        l0_root = self.kernel_root / "topics" / topic_slug / "L0"
        l0_root.mkdir(parents=True, exist_ok=True)
        (l0_root / "source_index.jsonl").write_text(
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

    def _write_tpkn_backend_card(self) -> None:
        backends_root = self.kernel_root / "canonical" / "backends"
        backends_root.mkdir(parents=True, exist_ok=True)
        (backends_root / "theoretical-physics-knowledge-network.json").write_text(
            json.dumps(
                {
                    "$schema": "../../schemas/l2-backend.schema.json",
                    "backend_id": "backend:theoretical-physics-knowledge-network",
                    "title": "Theoretical Physics Knowledge Network",
                    "backend_type": "mixed_local_library",
                    "status": "active",
                    "root_paths": ["__TPKN_REPO_ROOT__"],
                    "purpose": ["Test backend card for lifecycle promotion flows."],
                    "artifact_granularity": "One typed unit at a time.",
                    "source_policy": {
                        "requires_l0_registration": True,
                        "allows_direct_canonical_promotion": False,
                        "allows_auto_canonical_promotion": True,
                        "auto_promotion_domains": ["theory-formal"],
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
                    "canonical_targets": ["concept"],
                    "retrieval_hints": ["Read generated indexes before writeback."],
                    "notes": "Lifecycle test card.",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (backends_root / "backend_index.jsonl").write_text(
            json.dumps(
                {
                    "backend_id": "backend:theoretical-physics-knowledge-network",
                    "title": "Theoretical Physics Knowledge Network",
                    "backend_type": "mixed_local_library",
                    "status": "active",
                    "card_path": "canonical/backends/theoretical-physics-knowledge-network.json",
                    "canonical_targets": ["concept"],
                    "allows_auto_canonical_promotion": True,
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )

    def _write_fake_tpkn_repo(self) -> Path:
        tpkn_root = self.fixture.temp_root / "tpkn"
        for relative in (
            "docs",
            "schema",
            "scripts",
            "sources",
            "units/concepts",
            "edges",
            "indexes",
            "portal",
            "human-mirror",
        ):
            (tpkn_root / relative).mkdir(parents=True, exist_ok=True)
        for name in ("PROTOCOLS.md", "L2_RETRIEVAL_PROTOCOL.md", "OBJECT_MODEL.md", "L2_BRIDGE_PROTOCOL.md"):
            (tpkn_root / "docs" / name).write_text("# Demo\n", encoding="utf-8")
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
            "\n".join(
                [
                    "from pathlib import Path",
                    "import sys",
                    "",
                    "ROOT = Path(__file__).resolve().parents[1]",
                    "(ROOT / 'indexes').mkdir(exist_ok=True)",
                    "if len(sys.argv) > 1 and sys.argv[1] == 'check':",
                    "    raise SystemExit(0)",
                    "if len(sys.argv) > 1 and sys.argv[1] == 'build':",
                    "    (ROOT / 'indexes' / 'unit_index.jsonl').write_text('', encoding='utf-8')",
                    "    raise SystemExit(0)",
                    "raise SystemExit(1)",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return tpkn_root

    def _write_active_topics_registry(
        self,
        *,
        focused_topic_slug: str,
        rows: list[dict[str, object]],
    ) -> None:
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "active_topics.json").write_text(
            json.dumps(
                {
                    "registry_version": 1,
                    "focused_topic_slug": focused_topic_slug,
                    "updated_at": "2026-04-17T12:00:00+08:00",
                    "updated_by": "test",
                    "source": "test",
                    "topics": rows,
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    # Happy path

    def test_cli_brain_lifecycle_bootstrap_loop_status_promote_complete_sequence(self) -> None:
        self._prepare_first_run_kernel()

        bootstrap = self._run_cli(
            "bootstrap",
            "--topic",
            "Demo Topic",
            "--statement",
            "What is the bounded demo question?",
            "--json",
        )
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stderr)
        bootstrap_payload = json.loads(bootstrap.stdout)
        topic_slug = bootstrap_payload["topic_slug"]

        loop = self._run_cli(
            "loop",
            "--topic-slug",
            topic_slug,
            "--human-request",
            "Continue the first bounded route.",
            "--max-auto-steps",
            "0",
            "--json",
        )
        self.assertEqual(loop.returncode, 0, msg=loop.stderr)

        status = self._run_cli(
            "status",
            "--topic-slug",
            topic_slug,
            "--json",
        )
        self.assertEqual(status.returncode, 0, msg=status.stderr)
        self.assertTrue(Path(json.loads(status.stdout)["runtime_protocol_note_path"]).exists())

        self._write_runtime_state(topic_slug)
        self._write_candidate(topic_slug)
        self._write_tpkn_backend_card()
        tpkn_root = self._write_fake_tpkn_repo()

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

        request = self._run_cli(
            "request-promotion",
            "--topic-slug",
            topic_slug,
            "--candidate-id",
            "candidate:demo-candidate",
            "--backend-id",
            "backend:theoretical-physics-knowledge-network",
            "--json",
        )
        self.assertEqual(request.returncode, 0, msg=request.stderr)

        approve = self._run_cli(
            "approve-promotion",
            "--topic-slug",
            topic_slug,
            "--candidate-id",
            "candidate:demo-candidate",
            "--json",
        )
        self.assertEqual(approve.returncode, 0, msg=approve.stderr)

        promote = self._run_cli(
            "promote",
            "--topic-slug",
            topic_slug,
            "--candidate-id",
            "candidate:demo-candidate",
            "--target-backend-root",
            str(tpkn_root),
            "--domain",
            "demo-domain",
            "--subdomain",
            "demo-subdomain",
            "--json",
        )
        self.assertEqual(promote.returncode, 0, msg=promote.stderr)

        complete = self._run_cli(
            "complete-topic",
            "--topic-slug",
            topic_slug,
            "--json",
        )
        self.assertEqual(complete.returncode, 0, msg=complete.stderr or complete.stdout)
        completion_payload = json.loads(complete.stdout)
        self.assertEqual(completion_payload["status"], "promoted")
        self.assertTrue(Path(completion_payload["topic_completion_path"]).exists())

    def test_session_chronicle_markdown_contains_all_required_sections(self) -> None:
        self._write_runtime_state()
        decision = emit_decision_point(
            "demo-topic",
            "Do we need an operator review before promotion?",
            [
                {"label": "yes", "description": "Pause and wait for review."},
                {"label": "no", "description": "Continue with bounded execution."},
            ],
            True,
            phase="promotion",
            trigger_rule="promotion_gate",
            kernel_root=self.kernel_root,
        )
        trace = record_decision_trace(
            "demo-topic",
            "Selected the benchmark-first route.",
            "benchmark-first",
            "It keeps the bounded evidence chain explicit.",
            ["topics/demo-topic/runtime/topic_state.json"],
            kernel_root=self.kernel_root,
        )
        chronicle_id = start_chronicle("demo-topic", kernel_root=self.kernel_root)
        append_chronicle_action(
            chronicle_id,
            "Run the bounded benchmark-first route",
            "The first benchmark artifact was recorded.",
            artifacts_created=["topics/demo-topic/L3/runs/2026-03-13-demo/candidate_ledger.jsonl"],
            decision_trace_refs=[trace["decision_trace"]["id"]],
            kernel_root=self.kernel_root,
        )
        append_chronicle_problem(
            chronicle_id,
            "Promotion review is still pending.",
            resolution="Leave it as an explicit open decision point.",
            still_open=True,
            kernel_root=self.kernel_root,
        )
        finalize_chronicle(
            chronicle_id,
            "The bounded benchmark route is closed and ready for promotion review.",
            ["Resolve the promotion review.", "Decide whether the next route should branch."],
            "Closed the benchmark-focused session while preserving the next operator-facing step.",
            kernel_root=self.kernel_root,
        )

        markdown = render_chronicle_markdown(chronicle_id, kernel_root=self.kernel_root)
        for heading in (
            "## Summary",
            "## Starting State",
            "## Actions Taken",
            "## Decisions Made",
            "## Problems Encountered",
            "## Ending State",
            "## Next Steps",
            "## Open Decision Points",
        ):
            self.assertIn(heading, markdown)
        self.assertIn(decision["decision_point"]["id"], markdown)
        self.assertIn(trace["decision_trace"]["id"], markdown)

    def test_multi_topic_scheduler_selects_ready_topic_and_reports_blocked_topics(self) -> None:
        for topic_slug, updated_at in (
            ("alpha-topic", "2026-04-17T10:00:00+08:00"),
            ("beta-topic", "2026-04-17T11:00:00+08:00"),
            ("gamma-topic", "2026-04-17T09:00:00+08:00"),
        ):
            self._write_runtime_state(topic_slug, updated_at=updated_at)

        self._write_active_topics_registry(
            focused_topic_slug="alpha-topic",
            rows=[
                {
                    "topic_slug": "alpha-topic",
                    "status": "ready",
                    "priority": 1,
                    "last_activity": "2026-04-17T10:00:00+08:00",
                    "runtime_root": "topics/alpha-topic/runtime",
                    "lane": "code_method",
                    "focus_state": "focused",
                    "projection_status": "missing",
                    "blocked_by": [],
                    "blocked_by_details": [],
                    "summary": "Focused ready topic.",
                },
                {
                    "topic_slug": "beta-topic",
                    "status": "ready",
                    "priority": 3,
                    "last_activity": "2026-04-17T11:00:00+08:00",
                    "runtime_root": "topics/beta-topic/runtime",
                    "lane": "formal_theory",
                    "focus_state": "background",
                    "projection_status": "missing",
                    "blocked_by": [],
                    "blocked_by_details": [],
                    "summary": "Higher-priority ready topic.",
                },
                {
                    "topic_slug": "gamma-topic",
                    "status": "ready",
                    "priority": 9,
                    "last_activity": "2026-04-17T09:00:00+08:00",
                    "runtime_root": "topics/gamma-topic/runtime",
                    "lane": "code_method",
                    "focus_state": "background",
                    "projection_status": "missing",
                    "blocked_by": ["beta-topic"],
                    "blocked_by_details": [
                        {"topic_slug": "beta-topic", "reason": "Need the prerequisite route first."}
                    ],
                    "summary": "Dependency-blocked topic.",
                },
            ],
        )

        payload = self.service.select_next_topic(updated_by="scheduler-test")

        self.assertEqual(payload["selected_topic_slug"], "beta-topic")
        skipped = {row["topic_slug"]: row["reason"] for row in payload["skipped_topics"]}
        self.assertEqual(skipped["gamma-topic"], "dependency_blocked")

    # Boundary conditions

    def test_session_chronicle_marks_open_decision_points_none_when_all_are_resolved(self) -> None:
        self._write_runtime_state()
        decision = emit_decision_point(
            "demo-topic",
            "Should the next route stay on the current topic?",
            [
                {"label": "stay", "description": "Keep the route on the current topic."},
                {"label": "branch", "description": "Open a bounded follow-up topic."},
            ],
            False,
            phase="routing",
            trigger_rule="custom",
            kernel_root=self.kernel_root,
        )
        resolve_decision_point(
            "demo-topic",
            str(decision["decision_point"]["id"]),
            0,
            comment="Keep the next route on the current topic.",
            kernel_root=self.kernel_root,
        )
        chronicle_id = start_chronicle("demo-topic", kernel_root=self.kernel_root)
        finalize_chronicle(
            chronicle_id,
            "The route remains on the current topic.",
            ["Continue the current topic."],
            "No unresolved decision points remain after the routing choice.",
            kernel_root=self.kernel_root,
        )

        markdown = render_chronicle_markdown(chronicle_id, kernel_root=self.kernel_root)
        self.assertIn("## Open Decision Points", markdown)
        self.assertIn("- None.", markdown)

    def test_multi_topic_scheduler_prefers_focused_topic_when_priority_and_activity_tie(self) -> None:
        for topic_slug in ("alpha-topic", "beta-topic"):
            self._write_runtime_state(topic_slug, updated_at="2026-04-17T12:00:00+08:00")

        self._write_active_topics_registry(
            focused_topic_slug="alpha-topic",
            rows=[
                {
                    "topic_slug": "alpha-topic",
                    "status": "ready",
                    "priority": 2,
                    "last_activity": "2026-04-17T12:00:00+08:00",
                    "runtime_root": "topics/alpha-topic/runtime",
                    "lane": "formal_theory",
                    "focus_state": "focused",
                    "projection_status": "missing",
                    "blocked_by": [],
                    "blocked_by_details": [],
                    "summary": "Focused topic.",
                },
                {
                    "topic_slug": "beta-topic",
                    "status": "ready",
                    "priority": 2,
                    "last_activity": "2026-04-17T12:00:00+08:00",
                    "runtime_root": "topics/beta-topic/runtime",
                    "lane": "formal_theory",
                    "focus_state": "background",
                    "projection_status": "missing",
                    "blocked_by": [],
                    "blocked_by_details": [],
                    "summary": "Background topic.",
                },
            ],
        )

        payload = self.service.select_next_topic(updated_by="scheduler-test")
        self.assertEqual(payload["selected_topic_slug"], "alpha-topic")
        self.assertIn("focused_topic_bonus", payload["selection_reason"])

    # Error handling

    def test_complete_topic_still_requires_startup_contract_before_promotion(self) -> None:
        self._write_runtime_state()

        completed = self._run_cli(
            "complete-topic",
            "--topic-slug",
            "demo-topic",
            "--json",
        )

        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["gate_kind"], "startup_contract_missing")
        self.assertTrue(payload["blocked"])

    def test_render_chronicle_markdown_raises_for_missing_chronicle(self) -> None:
        with self.assertRaises(FileNotFoundError):
            render_chronicle_markdown("chronicle:missing-demo", kernel_root=self.kernel_root)

    def test_multi_topic_scheduler_raises_when_all_topics_are_ineligible(self) -> None:
        self._write_runtime_state("paused-topic")
        self._write_runtime_state("blocked-topic")

        self._write_active_topics_registry(
            focused_topic_slug="paused-topic",
            rows=[
                {
                    "topic_slug": "paused-topic",
                    "status": "paused",
                    "priority": 4,
                    "last_activity": "2026-04-17T12:00:00+08:00",
                    "runtime_root": "topics/paused-topic/runtime",
                    "lane": "code_method",
                    "focus_state": "focused",
                    "projection_status": "missing",
                    "blocked_by": [],
                    "blocked_by_details": [],
                    "summary": "Paused topic.",
                },
                {
                    "topic_slug": "blocked-topic",
                    "status": "ready",
                    "priority": 5,
                    "last_activity": "2026-04-17T11:00:00+08:00",
                    "runtime_root": "topics/blocked-topic/runtime",
                    "lane": "formal_theory",
                    "focus_state": "background",
                    "projection_status": "missing",
                    "blocked_by": ["paused-topic"],
                    "blocked_by_details": [
                        {"topic_slug": "paused-topic", "reason": "Need the paused prerequisite first."}
                    ],
                    "summary": "Blocked topic.",
                },
            ],
        )

        with self.assertRaisesRegex(FileNotFoundError, "No scheduler-eligible topics"):
            self.service.select_next_topic(updated_by="scheduler-test")


if __name__ == "__main__":
    unittest.main()
