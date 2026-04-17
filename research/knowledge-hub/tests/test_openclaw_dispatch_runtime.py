from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


def _load_module(module_name: str, relative_path: str):
    repo_root = Path(__file__).resolve().parents[3]
    target_path = repo_root / relative_path
    if str(target_path.parent) not in sys.path:
        sys.path.insert(0, str(target_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, target_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {target_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DispatchRuntimeControllerActionTests(unittest.TestCase):
    def test_runtime_controller_script_routes_to_expected_service_methods(self) -> None:
        module = _load_module(
            "aitp_dispatch_runtime_controller_action_test",
            "research/adapters/openclaw/scripts/dispatch_runtime_controller_action.py",
        )
        recorded_calls: list[tuple[str, dict]] = []

        class FakeService:
            def __init__(self, **kwargs):  # noqa: ANN003
                self.init_kwargs = kwargs

            def assess_topic_completion(self, **kwargs):  # noqa: ANN003
                recorded_calls.append(("assess_topic_completion", kwargs))
                return {"status": "ok", "action": "assess_topic_completion"}

            def prepare_lean_bridge(self, **kwargs):  # noqa: ANN003
                recorded_calls.append(("prepare_lean_bridge", kwargs))
                return {"status": "ok", "action": "prepare_lean_bridge"}

            def auto_promote_candidate(self, **kwargs):  # noqa: ANN003
                recorded_calls.append(("auto_promote_candidate", kwargs))
                return {"status": "ok", "action": "auto_promote_candidate"}

            def apply_candidate_split_contract(self, **kwargs):  # noqa: ANN003
                recorded_calls.append(("apply_candidate_split_contract", kwargs))
                return {"status": "ok", "action": "apply_candidate_split_contract"}

            def reactivate_deferred_candidates(self, **kwargs):  # noqa: ANN003
                recorded_calls.append(("reactivate_deferred_candidate", kwargs))
                return {"status": "ok", "action": "reactivate_deferred_candidate"}

            def spawn_followup_subtopics(self, **kwargs):  # noqa: ANN003
                recorded_calls.append(("spawn_followup_subtopics", kwargs))
                return {"status": "ok", "action": "spawn_followup_subtopics"}

            def reintegrate_followup_subtopic(self, **kwargs):  # noqa: ANN003
                recorded_calls.append(("reintegrate_followup_subtopic", kwargs))
                return {"status": "ok", "action": "reintegrate_followup_subtopic"}

        module.AITPService = FakeService
        module.resolve_topic_slug = lambda value: value or "demo-topic"

        test_cases = [
            (
                "assess_topic_completion",
                [
                    "dispatch_runtime_controller_action.py",
                    "--topic-slug",
                    "demo-topic",
                    "--action-type",
                    "assess_topic_completion",
                    "--run-id",
                    "2026-03-13-demo",
                ],
                {"topic_slug": "demo-topic", "run_id": "2026-03-13-demo", "updated_by": "openclaw"},
            ),
            (
                "prepare_lean_bridge",
                [
                    "dispatch_runtime_controller_action.py",
                    "--topic-slug",
                    "demo-topic",
                    "--action-type",
                    "prepare_lean_bridge",
                    "--run-id",
                    "2026-03-13-demo",
                    "--candidate-id",
                    "candidate:demo",
                ],
                {
                    "topic_slug": "demo-topic",
                    "run_id": "2026-03-13-demo",
                    "candidate_id": "candidate:demo",
                    "updated_by": "openclaw",
                },
            ),
            (
                "auto_promote_candidate",
                [
                    "dispatch_runtime_controller_action.py",
                    "--topic-slug",
                    "demo-topic",
                    "--action-type",
                    "auto_promote_candidate",
                    "--run-id",
                    "2026-03-13-demo",
                    "--candidate-id",
                    "candidate:demo",
                    "--backend-id",
                    "backend:tpkn",
                ],
                {
                    "topic_slug": "demo-topic",
                    "candidate_id": "candidate:demo",
                    "run_id": "2026-03-13-demo",
                    "promoted_by": "openclaw",
                    "backend_id": "backend:tpkn",
                    "target_backend_root": None,
                    "domain": None,
                    "subdomain": None,
                    "source_id": None,
                    "source_section": None,
                    "source_section_title": None,
                    "notes": None,
                },
            ),
        ]

        for expected_method, argv, expected_kwargs in test_cases:
            with self.subTest(action=expected_method):
                buffer = io.StringIO()
                with mock.patch.object(sys, "argv", argv):
                    with contextlib.redirect_stdout(buffer):
                        exit_code = module.main()
                self.assertEqual(exit_code, 0)
                self.assertEqual(recorded_calls[-1][0], expected_method)
                self.assertEqual(recorded_calls[-1][1], expected_kwargs)
                self.assertEqual(json.loads(buffer.getvalue())["action"], expected_method)


class DispatchActionQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.runtime_root = Path(self._tmpdir.name) / "topics" / "demo-topic" / "runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.module = _load_module(
            "aitp_dispatch_action_queue_test",
            "research/adapters/openclaw/scripts/dispatch_action_queue.py",
        )
        self.module.resolve_topic_slug = lambda value: value or "demo-topic"
        self.module.topic_runtime_root = lambda topic_slug: self.runtime_root

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_allowlist_covers_formal_runtime_controller_actions(self) -> None:
        for action_type in sorted(self.module.RUNTIME_CONTROLLER_ACTIONS):
            with self.subTest(action_type=action_type):
                self.assertEqual(self.module.normalize_dispatch_target(None, action_type), action_type)
                self.assertIn(action_type, self.module.ALLOWLIST)

    def test_dispatch_queue_bridges_action_type_without_handler(self) -> None:
        queue_path = self.runtime_root / "action_queue.jsonl"
        queue_path.write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:topic-completion",
                    "status": "pending",
                    "auto_runnable": True,
                    "action_type": "assess_topic_completion",
                    "handler": None,
                    "handler_args": {"run_id": "2026-03-13-demo"},
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        (self.runtime_root / "next_action_decision.json").write_text(
            json.dumps(
                {
                    "selected_action": {"action_id": "action:demo-topic:topic-completion"},
                    "auto_dispatch_allowed": True,
                    "decision_mode": "auto",
                    "reason": "test",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        calls: list[dict[str, object]] = []

        def fake_run(command, **kwargs):  # noqa: ANN001, ANN003
            calls.append({"command": list(command), "stdin": kwargs.get("stdin")})
            return mock.Mock(returncode=0, stdout="", stderr="")

        buffer = io.StringIO()
        with mock.patch.object(self.module.subprocess, "run", side_effect=fake_run):
            with mock.patch.object(
                sys,
                "argv",
                [
                    "dispatch_action_queue.py",
                    "--topic-slug",
                    "demo-topic",
                    "--max-actions",
                    "1",
                    "--updated-by",
                    "openclaw-test",
                ],
            ):
                with contextlib.redirect_stdout(buffer):
                    exit_code = self.module.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(calls), 2)
        commands = [call["command"] for call in calls]
        self.assertEqual(commands[0][0], sys.executable)
        self.assertEqual(commands[1][0], sys.executable)
        self.assertIn("dispatch_runtime_controller_action.py", commands[0][1])
        self.assertIn("--action-type", commands[0])
        self.assertIn("assess_topic_completion", commands[0])
        self.assertIn("orchestrate_topic.py", commands[1][1])
        self.assertTrue(all(call["stdin"] is subprocess.DEVNULL for call in calls))
        queue_row = json.loads(queue_path.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(queue_row["status"], "completed")
        receipts_path = self.runtime_root / "action_receipts.jsonl"
        self.assertTrue(receipts_path.exists())
        receipt_rows = [json.loads(line) for line in receipts_path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(receipt_rows[0]["handler_key"], "assess_topic_completion")


class DispatchExecutionTaskTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.runtime_root = Path(self._tmpdir.name) / "topics" / "demo-topic" / "runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.module = _load_module(
            "aitp_dispatch_execution_task_test",
            "research/adapters/openclaw/scripts/dispatch_execution_task.py",
        )
        self.module.resolve_topic_slug = lambda value: value or "demo-topic"
        self.module.topic_runtime_root = lambda topic_slug: self.runtime_root
        self.module.KNOWLEDGE_ROOT = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_dispatch_execution_task_refuses_when_human_confirmation_is_still_required(self) -> None:
        (self.runtime_root / "execution_task.json").write_text(
            json.dumps(
                {
                    "task_id": "demo-task",
                    "route_id": "route:demo-topic:benchmark",
                    "run_id": "run-001",
                    "result_writeback_path": "validation/topics/demo-topic/runs/run-001/returned_execution_result.json",
                    "result_template_path": "validation/templates/execution-result.template.json",
                    "executor_kind": "codex_cli",
                    "assigned_runtime": "codex",
                    "needs_human_confirm": True,
                    "auto_dispatch_allowed": True,
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        with self.assertRaises(SystemExit) as ctx:
            with mock.patch.object(
                sys,
                "argv",
                [
                    "dispatch_execution_task.py",
                    "--topic-slug",
                    "demo-topic",
                ],
            ):
                self.module.main()

        self.assertIn("requires human confirmation", str(ctx.exception))


class ExternalSkillDiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self._tmpdir.name)
        self.module = _load_module(
            "aitp_discover_external_skills_test",
            "research/adapters/openclaw/scripts/discover_external_skills.py",
        )

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_discovery_degrades_when_npx_is_missing(self) -> None:
        with mock.patch.object(self.module.subprocess, "run", side_effect=FileNotFoundError("npx missing")):
            with mock.patch.object(
                sys,
                "argv",
                [
                    "discover_external_skills.py",
                    "--query",
                    "operator algebra theorem packaging",
                    "--output-dir",
                    str(self.output_dir),
                ],
            ):
                exit_code = self.module.main()

        self.assertEqual(exit_code, 0)
        payload = json.loads((self.output_dir / "skill_discovery.json").read_text(encoding="utf-8"))
        report = (self.output_dir / "skill_recommendations.md").read_text(encoding="utf-8")
        self.assertEqual(payload["overall_status"], "degraded")
        self.assertEqual(payload["queries"][0]["status"], "unavailable")
        self.assertEqual(payload["queries"][0]["error_kind"], "command_not_found")
        self.assertIn("## Limitations", report)
        self.assertIn("operator algebra theorem packaging", report)

    def test_discovery_marks_ready_when_command_succeeds(self) -> None:
        completed = mock.Mock(
            returncode=0,
            stdout="demo/repo@operator-skill 12 installs\n└ https://example.test/catalog\n",
            stderr="",
        )
        recorded: dict[str, object] = {}

        def fake_run(command, **kwargs):  # noqa: ANN001, ANN003
            recorded["command"] = list(command)
            recorded["stdin"] = kwargs.get("stdin")
            return completed

        with mock.patch.object(self.module.subprocess, "run", side_effect=fake_run):
            with mock.patch.object(
                sys,
                "argv",
                [
                    "discover_external_skills.py",
                    "--query",
                    "operator algebra theorem packaging",
                    "--output-dir",
                    str(self.output_dir),
                ],
            ):
                exit_code = self.module.main()

        self.assertEqual(exit_code, 0)
        payload = json.loads((self.output_dir / "skill_discovery.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["overall_status"], "ready")
        self.assertEqual(payload["queries"][0]["status"], "completed")
        self.assertEqual(payload["queries"][0]["candidates"][0]["skill_name"], "operator-skill")
        self.assertEqual(recorded["command"], ["npx", "--yes", "skills", "find", "operator algebra theorem packaging"])
        self.assertIs(recorded["stdin"], subprocess.DEVNULL)


class OpenClawLoopSurfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.runtime_root = Path(self._tmpdir.name) / "topics" / "demo-topic" / "runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_aitp_loop_detaches_subprocess_stdin_for_runtime_children(self) -> None:
        module = _load_module(
            "aitp_loop_test",
            "research/adapters/openclaw/scripts/aitp_loop.py",
        )
        module.topic_runtime_root = lambda topic_slug: self.runtime_root

        decision_calls = iter(
            [
                {
                    "selected_action": {"action_id": "action:demo"},
                    "auto_dispatch_allowed": True,
                    "decision_source": "entry",
                    "decision_mode": "auto",
                },
                {
                    "selected_action": {"action_id": "action:done", "action_type": "assess_topic_completion"},
                    "decision_source": "exit",
                    "decision_mode": "auto",
                },
            ]
        )
        module.load_next_action_decision = lambda runtime_root: next(decision_calls)
        module.read_jsonl = lambda path: []  # noqa: ARG005
        module.read_json = lambda path: (  # noqa: ARG005
            {"overall_status": "pass"}
            if path.name in {"conformance_state.json", "trust_audit.json"}
            else {"overall_status": "ready"}
            if path.name == "capability_registry.json"
            else {"latest_run_id": "run-001", "summary": "Demo summary"}
            if path.name == "topic_state.json"
            else {}
        )
        module.write_json = lambda path, payload: None  # noqa: ARG005
        module.append_jsonl = lambda path, payload: None  # noqa: ARG005

        calls: list[dict[str, object]] = []

        def fake_run(command, **kwargs):  # noqa: ANN001, ANN003
            calls.append({"command": list(command), "stdin": kwargs.get("stdin")})
            return mock.Mock(returncode=0, stdout="", stderr="")

        with mock.patch.object(module.subprocess, "run", side_effect=fake_run):
            with mock.patch.object(
                sys,
                "argv",
                [
                    "aitp_loop.py",
                    "--topic-slug",
                    "demo-topic",
                    "--updated-by",
                    "openclaw-test",
                    "--max-steps",
                    "1",
                ],
            ):
                exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(calls), 3)
        self.assertIn("orchestrate_topic.py", str(calls[0]["command"]))
        self.assertIn("dispatch_action_queue.py", str(calls[1]["command"]))
        self.assertIn("audit_topic_conformance.py", str(calls[2]["command"]))
        self.assertTrue(all(call["stdin"] is subprocess.DEVNULL for call in calls))

    def test_heartbeat_bridge_detaches_loop_subprocess_stdin(self) -> None:
        module = _load_module(
            "aitp_heartbeat_bridge_test",
            "research/adapters/openclaw/scripts/heartbeat_bridge.py",
        )
        module.STOP_PATH = Path(self._tmpdir.name) / "STOP"
        module.HEARTBEAT_STATE_PATH = Path(self._tmpdir.name) / "heartbeat_state.json"
        module.HEARTBEAT_HISTORY_PATH = Path(self._tmpdir.name) / "heartbeat_history.jsonl"
        module.topic_runtime_root = lambda topic_slug: self.runtime_root
        module.read_json = lambda path: {}  # noqa: ARG005
        module.write_heartbeat = lambda payload, append_history: None  # noqa: ARG005

        recorded: dict[str, object] = {}

        def fake_run(command, **kwargs):  # noqa: ANN001, ANN003
            recorded["command"] = list(command)
            recorded["stdin"] = kwargs.get("stdin")
            return mock.Mock(returncode=0, stdout="", stderr="")

        with mock.patch.object(module.subprocess, "run", side_effect=fake_run):
            with mock.patch.object(
                sys,
                "argv",
                [
                    "heartbeat_bridge.py",
                    "--topic-slug",
                    "demo-topic",
                    "--updated-by",
                    "openclaw-heartbeat-test",
                ],
            ):
                exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertIn("aitp_loop.py", str(recorded["command"]))
        self.assertIs(recorded["stdin"], subprocess.DEVNULL)

    def test_topic_runner_detaches_loop_subprocess_stdin(self) -> None:
        module = _load_module(
            "aitp_topic_runner_test",
            "research/adapters/openclaw/scripts/aitp_topic_runner.py",
        )
        recorded: dict[str, object] = {}

        def fake_run(command, **kwargs):  # noqa: ANN001, ANN003
            recorded["command"] = list(command)
            recorded["stdin"] = kwargs.get("stdin")
            return mock.Mock(returncode=0, stdout="", stderr="")

        with mock.patch.object(module.subprocess, "run", side_effect=fake_run):
            with mock.patch.object(
                sys,
                "argv",
                [
                    "aitp_topic_runner.py",
                    "--topic-slug",
                    "demo-topic",
                    "--dispatch-auto",
                    "--max-auto-actions",
                    "2",
                ],
            ):
                exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertIn("aitp_loop.py", str(recorded["command"]))
        self.assertIs(recorded["stdin"], subprocess.DEVNULL)
