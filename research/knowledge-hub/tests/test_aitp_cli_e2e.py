from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from tests_support import copy_canonical_tree, copy_kernel_schema_files, copy_runtime_schema_files, make_temp_kernel


class AITPCLIE2ETests(unittest.TestCase):
    def setUp(self) -> None:
        self.package_root = Path(__file__).resolve().parents[1]
        self.repo_root = Path(__file__).resolve().parents[3]
        self.fixture = make_temp_kernel("aitp-cli-e2e-")
        self.kernel_root = self.fixture.kernel_root
        copy_canonical_tree(self.package_root, self.kernel_root)
        for schema_path in (self.package_root / "schemas").iterdir():
            if schema_path.is_file():
                copy_kernel_schema_files(self.package_root, self.kernel_root, schema_path.name)
        copy_runtime_schema_files(
            self.package_root,
            self.kernel_root,
            "progressive-disclosure-runtime-bundle.schema.json",
        )

    def tearDown(self) -> None:
        self.fixture.cleanup()

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

    def _prepare_first_run_kernel(self) -> None:
        for dirname in ("source-layer", "intake", "feedback", "consultation", "validation"):
            (self.kernel_root / dirname).mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            self.package_root / "runtime" / "scripts",
            self.kernel_root / "runtime" / "scripts",
            dirs_exist_ok=True,
        )
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
        exploration_window = self.package_root / "exploration_window.json"
        if exploration_window.exists():
            shutil.copy2(exploration_window, self.kernel_root / "exploration_window.json")

    def _write_topic_state(
        self,
        topic_slug: str,
        *,
        updated_at: str,
        latest_run_id: str,
        resume_stage: str = "L3",
    ) -> Path:
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "updated_at": updated_at,
                    "latest_run_id": latest_run_id,
                    "resume_stage": resume_stage,
                    "summary": f"Summary for {topic_slug}.",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return runtime_root

    def test_stage_negative_result_human_output_and_writeback(self) -> None:
        completed = self._run_cli(
            "stage-negative-result",
            "--title",
            "Portability route failed",
            "--summary",
            "The larger-system extrapolation failed.",
            "--failure-kind",
            "regime_mismatch",
        )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn("status: staged", completed.stdout)
        self.assertIn("entry id: staging:portability-route-failed", completed.stdout)
        self.assertNotIn("{", completed.stdout)
        self.assertTrue(
            (self.kernel_root / "canonical" / "staging" / "entries" / "staging--portability-route-failed.json").exists()
        )

    def test_hello_cli_json_path_returns_welcome_when_no_topic_exists(self) -> None:
        self._prepare_first_run_kernel()

        completed = self._run_cli(
            "hello",
            "--json",
        )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["mode"], "welcome")
        self.assertTrue(str(payload["install"]["overall_status"]))
        self.assertIn("aitp bootstrap", payload["suggested_command"])

    def test_hello_cli_json_path_uses_current_topic_when_available(self) -> None:
        self._prepare_first_run_kernel()

        bootstrap = self._run_cli(
            "bootstrap",
            "--topic",
            "Demo topic",
            "--statement",
            "What is the first bounded question?",
            "--json",
        )
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stderr)

        completed = self._run_cli(
            "hello",
            "--json",
        )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["mode"], "current_topic")
        self.assertEqual(payload["topic_slug"], "demo-topic")
        self.assertEqual(payload["status"]["topic_slug"], "demo-topic")
        self.assertTrue(Path(payload["status"]["runtime_protocol_note_path"]).exists())

    def test_help_cli_human_paths(self) -> None:
        core = self._run_cli("help")
        self.assertEqual(core.returncode, 0, msg=core.stderr)
        self.assertIn("AITP Help", core.stdout)
        self.assertIn("Core commands", core.stdout)
        self.assertIn("session-start", core.stdout)
        self.assertIn("consult-l2", core.stdout)
        self.assertNotIn("new-topic", core.stdout)

        expanded = self._run_cli("help", "--all")
        self.assertEqual(expanded.returncode, 0, msg=expanded.stderr)
        self.assertIn("AITP Help", expanded.stdout)
        self.assertIn("All registered commands", expanded.stdout)
        self.assertIn("Topic lifecycle", expanded.stdout)
        self.assertIn("new-topic", expanded.stdout)
        self.assertIn("doctor", expanded.stdout)

    def test_steer_topic_text_cli_json_path_materializes_direction(self) -> None:
        self._write_topic_state(
            "demo-topic",
            updated_at="2026-04-13T10:00:00+08:00",
            latest_run_id="run-001",
        )

        completed = self._run_cli(
            "steer-topic",
            "--topic-slug",
            "demo-topic",
            "--text",
            "继续这个 topic，方向改成 modular bootstrap constraints",
            "--json",
        )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["detected"])
        self.assertEqual(payload["decision"], "redirect")
        self.assertEqual(payload["direction"], "modular bootstrap constraints")
        self.assertTrue((self.kernel_root / payload["innovation_direction_path"]).exists())
        self.assertTrue((self.kernel_root / payload["control_note_path"]).exists())

    def test_first_run_bootstrap_loop_status_cli_flow(self) -> None:
        self._prepare_first_run_kernel()

        bootstrap = self._run_cli(
            "bootstrap",
            "--topic",
            "Jones Chapter 4 finite-dimensional backbone",
            "--statement",
            "Start from the finite-dimensional backbone and record the first honest closure target.",
            "--json",
        )
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stderr)
        bootstrap_payload = json.loads(bootstrap.stdout)
        topic_slug = bootstrap_payload["topic_slug"]
        self.assertEqual(topic_slug, "jones-chapter-4-finite-dimensional-backbone")
        self.assertTrue(Path(bootstrap_payload["files"]["topic_state"]).exists())
        self.assertTrue(Path(bootstrap_payload["files"]["runtime_protocol"]).exists())
        self.assertIn("next_action_hint", bootstrap_payload)

        loop = self._run_cli(
            "loop",
            "--topic-slug",
            topic_slug,
            "--human-request",
            "Continue with the first bounded route and stop before expensive execution.",
            "--max-auto-steps",
            "1",
            "--json",
        )
        self.assertEqual(loop.returncode, 0, msg=loop.stderr)
        loop_payload = json.loads(loop.stdout)
        self.assertEqual(loop_payload["topic_slug"], topic_slug)
        self.assertEqual(loop_payload["load_profile"], "light")
        self.assertEqual(
            (loop_payload["entry_audit"]["conformance_state"] or {}).get("overall_status"),
            "pass",
        )
        self.assertEqual(
            (loop_payload["exit_audit"]["conformance_state"] or {}).get("overall_status"),
            "pass",
        )
        self.assertTrue(Path(loop_payload["loop_state_path"]).exists())
        self.assertTrue(Path(loop_payload["runtime_protocol"]["runtime_protocol_path"]).exists())

        status = self._run_cli(
            "status",
            "--topic-slug",
            topic_slug,
            "--json",
        )
        self.assertEqual(status.returncode, 0, msg=status.stderr)
        status_payload = json.loads(status.stdout)
        self.assertEqual(status_payload["topic_slug"], topic_slug)
        self.assertEqual(status_payload["load_profile"], "light")
        self.assertTrue(bool(status_payload["selected_action_id"]))
        self.assertTrue(bool(status_payload["selected_action_type"]))
        self.assertTrue(Path(status_payload["runtime_protocol_path"]).exists())
        self.assertTrue(Path(status_payload["runtime_protocol_note_path"]).exists())

        status_human = self._run_cli(
            "status",
            "--topic-slug",
            topic_slug,
        )
        self.assertEqual(status_human.returncode, 0, msg=status_human.stderr)
        self.assertIn("AITP Status", status_human.stdout)
        self.assertIn("Topic:", status_human.stdout)
        self.assertIn("Machine view: aitp status --topic-slug", status_human.stdout)

        next_human = self._run_cli(
            "next",
            "--topic-slug",
            topic_slug,
        )
        self.assertEqual(next_human.returncode, 0, msg=next_human.stderr)
        self.assertIn("AITP Next", next_human.stdout)
        self.assertIn("Do:", next_human.stdout)
        self.assertIn("Machine view: aitp next --topic-slug", next_human.stdout)

        status_full = self._run_cli(
            "status",
            "--topic-slug",
            topic_slug,
            "--full",
        )
        self.assertEqual(status_full.returncode, 0, msg=status_full.stderr)
        self.assertIn("# Topic dashboard", status_full.stdout)

    def test_first_run_acceptance_can_continue_into_source_registration(self) -> None:
        script_path = self.package_root / "runtime" / "scripts" / "run_first_run_topic_acceptance.py"

        with tempfile.TemporaryDirectory() as tmpdir:
            work_root = Path(tmpdir)
            tar_path = work_root / "source.tar"
            tex_path = work_root / "paper.tex"
            tex_path.write_text("\\\\documentclass{article}\\n\\\\begin{document}demo\\\\end{document}\\n", encoding="utf-8")
            with tarfile.open(tar_path, "w") as archive:
                archive.add(tex_path, arcname="paper.tex")

            metadata_path = work_root / "metadata.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "arxiv_id": "2401.00001v2",
                        "title": "Topological Order and Anyon Condensation",
                        "summary": "A direct match for topological order and anyon condensation discovery.",
                        "published": "2024-01-03T00:00:00Z",
                        "updated": "2024-01-05T00:00:00Z",
                        "authors": ["Primary Author", "Secondary Author"],
                        "identifier": "https://arxiv.org/abs/2401.00001v2",
                        "abs_url": "https://arxiv.org/abs/2401.00001v2",
                        "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                        "source_url": tar_path.as_uri(),
                    },
                    ensure_ascii=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "--package-root",
                    str(self.package_root),
                    "--repo-root",
                    str(self.repo_root),
                    "--register-arxiv-id",
                    "2401.00001v2",
                    "--registration-metadata-json",
                    str(metadata_path),
                    "--json",
                ],
                cwd=self.package_root,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIn("discover_and_register.py", payload["status"]["selected_action_summary"])
        self.assertIn("register_arxiv_source.py", payload["status"]["selected_action_summary"])
        self.assertEqual(payload["registration"]["download_status"], "downloaded")
        self.assertEqual(payload["registration"]["extraction_status"], "extracted")
        self.assertTrue(Path(payload["registration"]["layer0_source_json"]).exists())
        self.assertIn("status_after_registration", payload)
        self.assertGreaterEqual(
            int(
                (
                    (payload["status_after_registration"].get("active_research_contract") or {})
                    .get("l1_source_intake")
                    or {}
                ).get("source_count")
                or 0
            ),
            1,
        )
        post_registration_summary = str(payload["status_after_registration"].get("selected_action_summary") or "")
        self.assertNotIn("discover_and_register.py", post_registration_summary)
        self.assertNotIn("register_arxiv_source.py", post_registration_summary)

    def test_record_collaborator_memory_json_and_human_paths(self) -> None:
        human = self._run_cli(
            "record-collaborator-memory",
            "--preference",
            "prefer bounded benchmark-first routes",
        )
        self.assertEqual(human.returncode, 0, msg=human.stderr)
        self.assertIn("memory kind: collaborator_memory", human.stdout)
        self.assertNotIn("{", human.stdout)

        machine = self._run_cli(
            "show-collaborator-memory",
            "--json",
        )
        self.assertEqual(machine.returncode, 0, msg=machine.stderr)
        payload = json.loads(machine.stdout)
        self.assertEqual(payload["collaborator_memory"]["memory_kind"], "collaborator_memory")
        self.assertIn(
            "prefer bounded benchmark-first routes",
            payload["collaborator_memory"]["preferences"],
        )

    def test_record_taste_and_taste_profile_cli_paths(self) -> None:
        runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        runtime_root.mkdir(parents=True, exist_ok=True)
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

        recorded = self._run_cli(
            "record-taste",
            "--topic-slug",
            "demo-topic",
            "--kind",
            "formalism",
            "--summary",
            "Prefer operator-algebra notation first.",
            "--formalism",
            "operator_algebra",
            "--json",
        )
        self.assertEqual(recorded.returncode, 0, msg=recorded.stderr)
        recorded_payload = json.loads(recorded.stdout)
        self.assertEqual(recorded_payload["research_taste_entry"]["taste_kind"], "formalism")
        self.assertTrue(Path(recorded_payload["research_taste_entries_path"]).exists())

        profiled = self._run_cli(
            "taste-profile",
            "--topic-slug",
            "demo-topic",
            "--json",
        )
        self.assertEqual(profiled.returncode, 0, msg=profiled.stderr)
        profile_payload = json.loads(profiled.stdout)
        self.assertEqual(profile_payload["research_taste"]["status"], "available")
        self.assertEqual(profile_payload["research_taste"]["formalism_preferences"], ["operator_algebra"])
        self.assertTrue(Path(profile_payload["research_taste_path"]).exists())
        self.assertTrue(Path(profile_payload["research_taste_note_path"]).exists())

    def test_record_negative_result_and_scratch_log_cli_paths(self) -> None:
        runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        runtime_root.mkdir(parents=True, exist_ok=True)
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

        recorded = self._run_cli(
            "record-negative-result",
            "--topic-slug",
            "demo-topic",
            "--summary",
            "The portability extrapolation failed outside the bounded regime.",
            "--failure-kind",
            "regime_mismatch",
            "--json",
        )
        self.assertEqual(recorded.returncode, 0, msg=recorded.stderr)
        recorded_payload = json.loads(recorded.stdout)
        self.assertEqual(recorded_payload["scratchpad_entry"]["entry_kind"], "negative_result")
        self.assertTrue(Path(recorded_payload["scratchpad_entries_path"]).exists())

        scratch_log = self._run_cli(
            "scratch-log",
            "--topic-slug",
            "demo-topic",
            "--json",
        )
        self.assertEqual(scratch_log.returncode, 0, msg=scratch_log.stderr)
        scratch_payload = json.loads(scratch_log.stdout)
        self.assertEqual(scratch_payload["scratchpad"]["status"], "active")
        self.assertEqual(scratch_payload["scratchpad"]["negative_result_count"], 1)
        self.assertTrue(Path(scratch_payload["scratchpad_path"]).exists())
        self.assertTrue(Path(scratch_payload["scratchpad_note_path"]).exists())

    def test_status_json_exposes_source_intelligence(self) -> None:
        runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "run-001",
                    "resume_stage": "L1",
                    "research_mode": "formal_derivation",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "Show the runtime source intelligence.",
                    "decision_surface": {
                        "selected_action_id": "action:demo-topic:read",
                        "decision_source": "heuristic",
                    },
                },
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
                    "summary": "Inspect the runtime source-intelligence summary.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                },
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        demo_source_root = self.kernel_root / "source-layer" / "topics" / "demo-topic"
        demo_source_root.mkdir(parents=True, exist_ok=True)
        (demo_source_root / "source_index.jsonl").write_text(
            json.dumps(
                {
                    "source_id": "paper:demo-source",
                    "source_type": "paper",
                    "title": "Demo source",
                    "summary": "Demo summary with a shared reference.",
                    "references": ["doi:10-1000/shared"],
                    "canonical_source_id": "source_identity:doi:10-1000-demo",
                    "provenance": {
                        "abs_url": "https://example.org/demo",
                    },
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        neighbor_source_root = self.kernel_root / "source-layer" / "topics" / "neighbor-topic"
        neighbor_source_root.mkdir(parents=True, exist_ok=True)
        (neighbor_source_root / "source_index.jsonl").write_text(
            json.dumps(
                {
                    "source_id": "paper:neighbor-source",
                    "source_type": "paper",
                    "title": "Neighbor source",
                    "summary": "Neighbor summary with the same shared reference.",
                    "references": ["doi:10-1000/shared"],
                    "canonical_source_id": "source_identity:doi:10-1000-neighbor",
                    "provenance": {
                        "abs_url": "https://example.org/neighbor",
                    },
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )

        completed = self._run_cli(
            "status",
            "--topic-slug",
            "demo-topic",
            "--json",
        )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["source_intelligence"]["canonical_source_ids"][0], "source_identity:doi:10-1000-demo")
        self.assertEqual(payload["source_intelligence"]["cross_topic_match_count"], 1)
        self.assertEqual(payload["source_intelligence"]["source_neighbors"][0]["relation_kind"], "shared_reference")
        self.assertEqual(payload["source_intelligence"]["fidelity_summary"]["strongest_tier"], "peer_reviewed")
        self.assertEqual(
            payload["active_research_contract"]["l1_source_intake"]["method_specificity_rows"][0]["method_family"],
            "unspecified_method",
        )
        self.assertEqual(
            payload["active_research_contract"]["l1_source_intake"]["method_specificity_rows"][0]["specificity_tier"],
            "low",
        )

    def test_status_json_exposes_research_judgment_signals(self) -> None:
        runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        runtime_root.mkdir(parents=True, exist_ok=True)
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
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "Continue the derivation route.",
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
        collaborator_memory_path = self.kernel_root / "runtime" / "collaborator_memory.jsonl"
        collaborator_memory_path.parent.mkdir(parents=True, exist_ok=True)
        collaborator_memory_path.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "memory_id": "collab-stuckness-demo",
                            "recorded_at": "2026-04-11T10:00:00+08:00",
                            "memory_kind": "stuckness",
                            "summary": "The derivation keeps stalling at the sign-convention merge point.",
                            "topic_slug": "demo-topic",
                            "run_id": "run-001",
                            "tags": ["formal-theory"],
                            "related_topic_slugs": ["demo-topic"],
                            "updated_by": "human",
                        },
                        ensure_ascii=True,
                    ),
                    json.dumps(
                        {
                            "memory_id": "collab-surprise-demo",
                            "recorded_at": "2026-04-11T10:05:00+08:00",
                            "memory_kind": "surprise",
                            "summary": "The weak-coupling route unexpectedly preserved the target symmetry.",
                            "topic_slug": "demo-topic",
                            "run_id": "run-001",
                            "tags": ["analytical"],
                            "related_topic_slugs": ["demo-topic"],
                            "updated_by": "human",
                        },
                        ensure_ascii=True,
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        feedback_root = self.kernel_root / "feedback" / "topics" / "demo-topic" / "runs" / "run-001"
        feedback_root.mkdir(parents=True, exist_ok=True)
        (feedback_root / "strategy_memory.jsonl").write_text(
            json.dumps(
                {
                    "strategy_id": "strategy:demo-proof",
                    "timestamp": "2026-04-11T09:00:00+08:00",
                    "topic_slug": "demo-topic",
                    "run_id": "run-001",
                    "strategy_type": "verification_guardrail",
                    "summary": "Check sign conventions before combining derivation branches.",
                    "outcome": "helpful",
                    "confidence": 0.81,
                    "lane": "formal_theory",
                    "reuse_conditions": ["combining derivation branches", "sign conventions"],
                    "do_not_apply_when": [],
                    "input_context": {},
                    "evidence_refs": [],
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )

        completed = self._run_cli(
            "status",
            "--topic-slug",
            "demo-topic",
            "--json",
        )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["research_judgment"]["status"], "signals_active")
        self.assertEqual(payload["research_judgment"]["stuckness"]["status"], "active")
        self.assertEqual(payload["research_judgment"]["surprise"]["status"], "active")
        self.assertEqual(payload["topic_synopsis"]["runtime_focus"]["momentum_status"], "queued")

    def test_layer_graph_command_uses_real_service_path(self) -> None:
        runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "run-001",
                    "resume_stage": "L3",
                    "last_materialized_stage": "L4",
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
                    "human_request": "Continue the bounded proof review after the returned result.",
                    "decision_surface": {
                        "selected_action_id": "action:demo-topic:return",
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
                    "action_id": "action:demo-topic:return",
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

        completed = self._run_cli(
            "layer-graph",
            "--topic-slug",
            "demo-topic",
            "--json",
        )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["layer_graph"]["current_node_id"], "L3-R")
        self.assertEqual(payload["layer_graph"]["return_law"]["required_return_node"], "L3-R")
        self.assertTrue(Path(payload["layer_graph_path"]).exists())
        self.assertTrue(Path(payload["layer_graph_note_path"]).exists())

    def test_analytical_review_cli_writes_artifact_and_becomes_primary_bundle_surface(self) -> None:
        runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "run-001",
                    "resume_stage": "L3",
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
                    "human_request": "Run an analytical review for the active topic.",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        feedback_root = self.kernel_root / "feedback" / "topics" / "demo-topic" / "runs" / "run-001"
        feedback_root.mkdir(parents=True, exist_ok=True)
        (feedback_root / "candidate_ledger.jsonl").write_text(
            json.dumps(
                {
                    "candidate_id": "candidate:demo-candidate",
                    "candidate_type": "concept",
                    "title": "Demo Analytical Concept",
                    "summary": "A bounded concept for analytical-review testing.",
                    "topic_slug": "demo-topic",
                    "run_id": "run-001",
                    "origin_refs": [],
                    "question": "Does the analytical route stay source-backed?",
                    "assumptions": ["Weak-coupling regime only."],
                    "proposed_validation_route": "analytical",
                    "intended_l2_targets": ["concept:demo-analytical-concept"],
                    "status": "ready_for_validation",
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        source_root = self.kernel_root / "source-layer" / "topics" / "demo-topic"
        source_root.mkdir(parents=True, exist_ok=True)
        (source_root / "source_index.jsonl").write_text(
            json.dumps(
                {
                    "source_id": "paper:demo-source",
                    "source_type": "paper",
                    "title": "Demo source",
                    "summary": "Demo summary for analytical review.",
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )

        reviewed = self._run_cli(
            "analytical-review",
            "--topic-slug",
            "demo-topic",
            "--candidate-id",
            "candidate:demo-candidate",
            "--check",
            "source_cross_reference=intro-vs-appendix:passed:Cross-referenced source sections agree on the bounded limit.",
            "--source-anchor",
            "paper:demo-source#sec:intro",
            "--assumption",
            "assumption:weak-coupling-regime",
            "--regime-note",
            "Weak-coupling only.",
            "--reading-depth",
            "targeted",
            "--json",
        )
        self.assertEqual(reviewed.returncode, 0, msg=reviewed.stderr)
        reviewed_payload = json.loads(reviewed.stdout)
        self.assertEqual(reviewed_payload["overall_status"], "ready")
        review_path = Path(reviewed_payload["paths"]["analytical_review"])
        self.assertTrue(review_path.exists())
        review_payload = json.loads(review_path.read_text(encoding="utf-8"))
        self.assertEqual(review_payload["checks"][0]["kind"], "source_cross_reference")
        self.assertEqual(review_payload["checks"][0]["source_anchors"], ["paper:demo-source#sec:intro"])
        self.assertEqual(review_payload["checks"][0]["assumption_refs"], ["assumption:weak-coupling-regime"])
        self.assertEqual(review_payload["checks"][0]["regime_note"], "Weak-coupling only.")
        self.assertEqual(review_payload["checks"][0]["reading_depth"], "targeted")

        verified = self._run_cli(
            "verify",
            "--topic-slug",
            "demo-topic",
            "--mode",
            "analytical",
            "--json",
        )
        self.assertEqual(verified.returncode, 0, msg=verified.stderr)
        bundle_path = runtime_root / "validation_review_bundle.active.json"
        self.assertTrue(bundle_path.exists())
        bundle_payload = json.loads(bundle_path.read_text(encoding="utf-8"))
        self.assertEqual(bundle_payload["validation_mode"], "analytical")
        self.assertEqual(bundle_payload["primary_review_kind"], "analytical_review")

    def test_seed_l2_direction_and_consult_l2_cli_json_path(self) -> None:
        seeded = self._run_cli(
            "seed-l2-direction",
            "--direction",
            "tfim-benchmark-first",
            "--json",
        )
        self.assertEqual(seeded.returncode, 0, msg=seeded.stderr)
        seed_payload = json.loads(seeded.stdout)
        self.assertEqual(seed_payload["direction"], "tfim-benchmark-first")

        consulted = self._run_cli(
            "consult-l2",
            "--query-text",
            "TFIM exact diagonalization benchmark workflow",
            "--retrieval-profile",
            "l3_candidate_formation",
            "--max-primary-hits",
            "2",
            "--json",
        )
        self.assertEqual(consulted.returncode, 0, msg=consulted.stderr)
        consult_payload = json.loads(consulted.stdout)
        primary_ids = {row["id"] for row in consult_payload["primary_hits"]}
        expanded_ids = {row["id"] for row in consult_payload["expanded_hits"]}
        self.assertEqual(consult_payload["retrieval_profile"], "l3_candidate_formation")
        self.assertIn("physical_picture:tfim-weak-coupling-benchmark-intuition", primary_ids | expanded_ids)
        self.assertIn("traversal_summary", consult_payload)
        self.assertGreaterEqual(consult_payload["traversal_summary"]["max_depth_reached"], 1)

    def test_consult_l2_can_write_protocol_artifacts_via_cli(self) -> None:
        seeded = self._run_cli(
            "seed-l2-direction",
            "--direction",
            "tfim-benchmark-first",
            "--json",
        )
        self.assertEqual(seeded.returncode, 0, msg=seeded.stderr)

        consulted = self._run_cli(
            "consult-l2",
            "--query-text",
            "Benchmark-first validation",
            "--retrieval-profile",
            "l1_provisional_understanding",
            "--topic-slug",
            "demo-topic",
            "--stage",
            "L3",
            "--run-id",
            "run-001",
            "--record-consultation",
            "--json",
        )
        self.assertEqual(consulted.returncode, 0, msg=consulted.stderr)
        consult_payload = json.loads(consulted.stdout)
        consultation = consult_payload["consultation"]
        self.assertTrue(Path(consultation["consultation_request_path"]).exists())
        self.assertTrue(Path(consultation["consultation_result_path"]).exists())
        self.assertTrue(Path(consultation["consultation_application_path"]).exists())
        result_payload = json.loads(Path(consultation["consultation_result_path"]).read_text(encoding="utf-8"))
        self.assertEqual(result_payload["retrieval_summary"]["max_depth_reached"], 2)

    def test_compile_l2_map_and_audit_l2_hygiene_cli_json_path(self) -> None:
        seeded = self._run_cli(
            "seed-l2-direction",
            "--direction",
            "tfim-benchmark-first",
            "--json",
        )
        self.assertEqual(seeded.returncode, 0, msg=seeded.stderr)

        compiled = self._run_cli(
            "compile-l2-map",
            "--json",
        )
        self.assertEqual(compiled.returncode, 0, msg=compiled.stderr)
        compile_payload = json.loads(compiled.stdout)
        self.assertTrue(Path(compile_payload["json_path"]).exists())
        self.assertTrue(Path(compile_payload["markdown_path"]).exists())
        self.assertGreaterEqual(compile_payload["payload"]["summary"]["total_units"], 9)

        hygiene = self._run_cli(
            "audit-l2-hygiene",
            "--json",
        )
        self.assertEqual(hygiene.returncode, 0, msg=hygiene.stderr)
        hygiene_payload = json.loads(hygiene.stdout)
        self.assertTrue(Path(hygiene_payload["json_path"]).exists())
        self.assertTrue(Path(hygiene_payload["markdown_path"]).exists())
        self.assertGreaterEqual(hygiene_payload["payload"]["summary"]["total_units"], 9)

    def test_compile_l2_graph_report_cli_json_path(self) -> None:
        seeded = self._run_cli(
            "seed-l2-direction",
            "--direction",
            "tfim-benchmark-first",
            "--json",
        )
        self.assertEqual(seeded.returncode, 0, msg=seeded.stderr)

        reported = self._run_cli(
            "compile-l2-graph-report",
            "--json",
        )
        self.assertEqual(reported.returncode, 0, msg=reported.stderr)
        report_payload = json.loads(reported.stdout)
        self.assertTrue(Path(report_payload["json_path"]).exists())
        self.assertTrue(Path(report_payload["markdown_path"]).exists())
        self.assertTrue(Path(report_payload["navigation_index_path"]).exists())
        self.assertGreaterEqual(report_payload["navigation_page_count"], 9)
        self.assertEqual(report_payload["payload"]["hub_units"][0]["unit_id"], "workflow:tfim-benchmark-workflow")

    def test_compile_l2_knowledge_report_cli_json_path(self) -> None:
        unique_suffix = self.kernel_root.parent.name
        provisional_title = f"Phase138 test compiled note {unique_suffix}"
        contradiction_title = f"Phase138 test contradiction {unique_suffix}"
        seeded = self._run_cli(
            "seed-l2-direction",
            "--direction",
            "tfim-benchmark-first",
            "--json",
        )
        self.assertEqual(seeded.returncode, 0, msg=seeded.stderr)

        staged = self._run_cli(
            "stage-l2-provisional",
            "--topic-slug",
            "demo-topic",
            "--entry-kind",
            "workflow_draft",
            "--title",
            provisional_title,
            "--summary",
            "A provisional reusable workflow draft for the benchmark-first route.",
            "--json",
        )
        self.assertEqual(staged.returncode, 0, msg=staged.stderr)

        first = self._run_cli(
            "compile-l2-knowledge-report",
            "--json",
        )
        self.assertEqual(first.returncode, 0, msg=first.stderr)
        first_payload = json.loads(first.stdout)
        self.assertTrue(Path(first_payload["json_path"]).exists())
        self.assertTrue(Path(first_payload["markdown_path"]).exists())
        self.assertGreaterEqual(first_payload["payload"]["summary"]["canonical_row_count"], 9)
        self.assertGreaterEqual(first_payload["payload"]["summary"]["staging_row_count"], 1)
        self.assertIn("added_count", first_payload["payload"]["change_summary"])
        self.assertIn("previous_report_found", first_payload["payload"]["change_summary"])
        self.assertEqual(
            first_payload["payload"]["knowledge_rows"][-1]["authority_level"],
            "non_authoritative_staging",
        )

        negative = self._run_cli(
            "stage-negative-result",
            "--title",
            contradiction_title,
            "--summary",
            "The provisional benchmark route failed outside the bounded regime.",
            "--failure-kind",
            "regime_mismatch",
            "--json",
        )
        self.assertEqual(negative.returncode, 0, msg=negative.stderr)

        second = self._run_cli(
            "compile-l2-knowledge-report",
            "--json",
        )
        self.assertEqual(second.returncode, 0, msg=second.stderr)
        second_payload = json.loads(second.stdout)
        self.assertTrue(second_payload["payload"]["change_summary"]["previous_report_found"])
        self.assertGreaterEqual(second_payload["payload"]["change_summary"]["added_count"], 1)
        self.assertGreaterEqual(second_payload["payload"]["summary"]["contradiction_row_count"], 1)
        self.assertIn("workspace_staging_manifest", second_payload["supporting_artifacts"])

    def test_compile_source_catalog_cli_json_path(self) -> None:
        topic_a_root = self.kernel_root / "source-layer" / "topics" / "topic-a"
        topic_b_root = self.kernel_root / "source-layer" / "topics" / "topic-b"
        topic_a_root.mkdir(parents=True, exist_ok=True)
        topic_b_root.mkdir(parents=True, exist_ok=True)
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
            "\n".join(
                [
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

        completed = self._run_cli(
            "compile-source-catalog",
            "--json",
        )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(Path(payload["json_path"]).exists())
        self.assertTrue(Path(payload["markdown_path"]).exists())
        self.assertEqual(payload["payload"]["summary"]["multi_topic_source_count"], 1)
        self.assertEqual(payload["payload"]["sources"][0]["canonical_source_id"], "source_identity:doi:10-1000-shared-paper")

    def test_trace_source_citations_and_compile_source_family_cli_json_path(self) -> None:
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

        traced = self._run_cli(
            "trace-source-citations",
            "--canonical-source-id",
            "source_identity:doi:10-1000-shared-paper",
            "--json",
        )
        self.assertEqual(traced.returncode, 0, msg=traced.stderr)
        trace_payload = json.loads(traced.stdout)
        self.assertTrue(Path(trace_payload["json_path"]).exists())
        self.assertTrue(Path(trace_payload["markdown_path"]).exists())
        self.assertEqual(trace_payload["payload"]["summary"]["incoming_link_count"], 1)

        family = self._run_cli(
            "compile-source-family",
            "--source-type",
            "paper",
            "--json",
        )
        self.assertEqual(family.returncode, 0, msg=family.stderr)
        family_payload = json.loads(family.stdout)
        self.assertTrue(Path(family_payload["json_path"]).exists())
        self.assertTrue(Path(family_payload["markdown_path"]).exists())
        self.assertEqual(family_payload["payload"]["summary"]["multi_topic_source_count"], 1)

    def test_export_and_import_source_bibtex_cli_json_path(self) -> None:
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

        exported = self._run_cli(
            "export-source-bibtex",
            "--canonical-source-id",
            "source_identity:doi:10-1000-shared-paper",
            "--include-neighbors",
            "--json",
        )
        self.assertEqual(exported.returncode, 0, msg=exported.stderr)
        export_payload = json.loads(exported.stdout)
        self.assertTrue(Path(export_payload["json_path"]).exists())
        self.assertTrue(Path(export_payload["markdown_path"]).exists())
        self.assertTrue(Path(export_payload["bibtex_path"]).exists())
        self.assertEqual(export_payload["payload"]["summary"]["entry_count"], 2)

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

        imported = self._run_cli(
            "import-bibtex-sources",
            "--topic-slug",
            "demo-topic",
            "--bibtex-path",
            str(bib_path),
            "--json",
        )
        self.assertEqual(imported.returncode, 0, msg=imported.stderr)
        import_payload = json.loads(imported.stdout)
        self.assertTrue(Path(import_payload["json_path"]).exists())
        self.assertTrue(Path(import_payload["markdown_path"]).exists())
        self.assertTrue(Path(import_payload["source_index_path"]).exists())
        self.assertEqual(import_payload["payload"]["summary"]["imported_entry_count"], 1)

    def test_sync_l1_graph_export_to_theoretical_physics_brain_cli_json_path(self) -> None:
        export_root = self.kernel_root / "intake" / "topics" / "demo-topic" / "vault" / "wiki" / "concept-graph"
        export_root.mkdir(parents=True, exist_ok=True)
        (export_root / "manifest.json").write_text(
            json.dumps(
                {
                    "kind": "obsidian_concept_graph_export",
                    "topic_slug": "demo-topic",
                    "root_path": "intake/topics/demo-topic/vault/wiki/concept-graph",
                    "index_path": "intake/topics/demo-topic/vault/wiki/concept-graph/index.md",
                    "summary": {
                        "node_note_count": 1,
                        "community_folder_count": 1,
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (export_root / "index.md").write_text("# Concept Graph\n", encoding="utf-8")
        note_dir = export_root / "topological-order-cluster"
        note_dir.mkdir(parents=True, exist_ok=True)
        (note_dir / "index.md").write_text("# Cluster\n", encoding="utf-8")
        (note_dir / "topological-order.md").write_text("# Topological order\n", encoding="utf-8")

        brain_root = self.kernel_root.parent / "brain"
        backends_root = self.kernel_root / "canonical" / "backends"
        backends_root.mkdir(parents=True, exist_ok=True)
        (backends_root / "theoretical-physics-brain.json").write_text(
            json.dumps(
                {
                    "backend_id": "backend:theoretical-physics-brain",
                    "title": "Theoretical Physics Brain",
                    "backend_type": "human_note_library",
                    "status": "active",
                    "root_paths": [str(brain_root)],
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
                    "backend_id": "backend:theoretical-physics-brain",
                    "title": "Theoretical Physics Brain",
                    "backend_type": "human_note_library",
                    "status": "active",
                    "card_path": "canonical/backends/theoretical-physics-brain.json",
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )

        synced = self._run_cli(
            "sync-l1-graph-export-to-theoretical-physics-brain",
            "--topic-slug",
            "demo-topic",
            "--json",
        )
        self.assertEqual(synced.returncode, 0, msg=synced.stderr)
        sync_payload = json.loads(synced.stdout)
        self.assertTrue(Path(sync_payload["receipt_path"]).exists())
        self.assertTrue((brain_root / "90 AITP Imports" / "concept-graphs" / "demo-topic" / "index.md").exists())
        self.assertEqual(sync_payload["summary"]["mirrored_file_count"], 4)

    def test_topics_and_current_topic_commands_use_real_service_paths(self) -> None:
        self._write_topic_state(
            "alpha-topic",
            updated_at="2026-04-11T10:00:00+08:00",
            latest_run_id="alpha-run",
        )
        self._write_topic_state(
            "beta-topic",
            updated_at="2026-04-11T11:00:00+08:00",
            latest_run_id="beta-run",
        )

        topics = self._run_cli("topics", "--json")
        self.assertEqual(topics.returncode, 0, msg=topics.stderr)
        topics_payload = json.loads(topics.stdout)
        self.assertEqual(topics_payload["topic_count"], 2)
        self.assertEqual(
            {row["topic_slug"] for row in topics_payload["topics"]},
            {"alpha-topic", "beta-topic"},
        )
        self.assertTrue(Path(topics_payload["active_topics_path"]).exists())
        self.assertTrue(Path(topics_payload["active_topics_note_path"]).exists())

        focused = self._run_cli("focus-topic", "--topic-slug", "beta-topic", "--json")
        self.assertEqual(focused.returncode, 0, msg=focused.stderr)
        focused_payload = json.loads(focused.stdout)
        self.assertEqual(focused_payload["status"], "focused")
        self.assertEqual(focused_payload["focused_topic_slug"], "beta-topic")

        current = self._run_cli("current-topic", "--json")
        self.assertEqual(current.returncode, 0, msg=current.stderr)
        current_payload = json.loads(current.stdout)
        self.assertEqual(current_payload["current_topic"]["topic_slug"], "beta-topic")
        self.assertEqual(current_payload["current_topic"]["runtime_root"], "runtime/topics/beta-topic")
        self.assertTrue((self.kernel_root / "runtime" / "current_topic.json").exists())
        self.assertTrue((self.kernel_root / "runtime" / "current_topic.md").exists())

    def test_multi_topic_management_commands_use_real_service_paths(self) -> None:
        self._write_topic_state(
            "alpha-topic",
            updated_at="2026-04-11T10:00:00+08:00",
            latest_run_id="alpha-run",
        )
        self._write_topic_state(
            "beta-topic",
            updated_at="2026-04-11T11:00:00+08:00",
            latest_run_id="beta-run",
        )

        focused = self._run_cli("focus-topic", "--topic-slug", "alpha-topic", "--json")
        self.assertEqual(focused.returncode, 0, msg=focused.stderr)
        self.assertEqual(json.loads(focused.stdout)["focused_topic_slug"], "alpha-topic")

        paused = self._run_cli("pause-topic", "--topic-slug", "alpha-topic", "--json")
        self.assertEqual(paused.returncode, 0, msg=paused.stderr)
        paused_payload = json.loads(paused.stdout)
        self.assertEqual(paused_payload["status"], "paused")
        self.assertEqual(paused_payload["focused_topic_slug"], "beta-topic")

        resumed = self._run_cli("resume-topic", "--topic-slug", "alpha-topic", "--json")
        self.assertEqual(resumed.returncode, 0, msg=resumed.stderr)
        resumed_payload = json.loads(resumed.stdout)
        self.assertEqual(resumed_payload["status"], "ready")
        self.assertEqual(resumed_payload["focused_topic_slug"], "alpha-topic")

        blocked = self._run_cli(
            "block-topic",
            "--topic-slug",
            "alpha-topic",
            "--blocked-by",
            "beta-topic",
            "--reason",
            "Need beta first",
            "--json",
        )
        self.assertEqual(blocked.returncode, 0, msg=blocked.stderr)
        blocked_payload = json.loads(blocked.stdout)
        self.assertEqual(blocked_payload["status"], "dependency_blocked")
        self.assertEqual(blocked_payload["blocked_by"], ["beta-topic"])
        self.assertEqual(blocked_payload["focused_topic_slug"], "beta-topic")

        unblocked = self._run_cli(
            "unblock-topic",
            "--topic-slug",
            "alpha-topic",
            "--blocked-by",
            "beta-topic",
            "--json",
        )
        self.assertEqual(unblocked.returncode, 0, msg=unblocked.stderr)
        unblocked_payload = json.loads(unblocked.stdout)
        self.assertEqual(unblocked_payload["status"], "dependency_cleared")
        self.assertEqual(unblocked_payload["blocked_by"], [])

        reblocked = self._run_cli(
            "block-topic",
            "--topic-slug",
            "alpha-topic",
            "--blocked-by",
            "beta-topic",
            "--reason",
            "Need beta first",
            "--json",
        )
        self.assertEqual(reblocked.returncode, 0, msg=reblocked.stderr)

        cleared = self._run_cli(
            "clear-topic-dependencies",
            "--topic-slug",
            "alpha-topic",
            "--json",
        )
        self.assertEqual(cleared.returncode, 0, msg=cleared.stderr)
        cleared_payload = json.loads(cleared.stdout)
        self.assertEqual(cleared_payload["status"], "dependencies_cleared")
        self.assertEqual(cleared_payload["blocked_by"], [])

    def test_prune_compat_surfaces_command_uses_real_service_path(self) -> None:
        topic_root = self._write_topic_state(
            "demo-topic",
            updated_at="2026-04-11T12:00:00+08:00",
            latest_run_id="demo-run",
        )
        (topic_root / "topic_dashboard.md").write_text("# Dashboard\n", encoding="utf-8")
        (topic_root / "runtime_protocol.generated.md").write_text("# Runtime protocol\n", encoding="utf-8")
        (topic_root / "agent_brief.md").write_text("# Brief\n", encoding="utf-8")
        (topic_root / "operator_console.md").write_text("# Console\n", encoding="utf-8")
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "current_topic.json").write_text(
            json.dumps({"topic_slug": "demo-topic"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (runtime_root / "current_topic.md").write_text("# Current topic\n", encoding="utf-8")

        pruned = self._run_cli(
            "prune-compat-surfaces",
            "--topic-slug",
            "demo-topic",
            "--json",
        )

        self.assertEqual(pruned.returncode, 0, msg=pruned.stderr)
        payload = json.loads(pruned.stdout)
        self.assertEqual(payload["status"], "pruned")
        self.assertEqual(
            {row["surface"] for row in payload["removed_surfaces"]},
            {"agent_brief", "operator_console", "current_topic_note"},
        )
        self.assertFalse((topic_root / "agent_brief.md").exists())
        self.assertFalse((topic_root / "operator_console.md").exists())
        self.assertFalse((runtime_root / "current_topic.md").exists())


if __name__ == "__main__":
    unittest.main()
