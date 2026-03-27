from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.decision_point_handler import (  # noqa: E402
    check_blocking_decision_points,
    emit_decision_point,
    get_all_decision_points,
    list_pending_decision_points,
    resolve_decision_point,
)
from knowledge_hub.decision_trace_handler import get_decision_traces, query_traces, record_decision_trace  # noqa: E402
from knowledge_hub.session_chronicle_handler import (  # noqa: E402
    append_chronicle_action,
    append_chronicle_problem,
    finalize_chronicle,
    get_latest_chronicle,
    render_chronicle_markdown,
    start_chronicle,
)


class Phase6ProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.package_root = Path(__file__).resolve().parents[1]
        self.repo_root = Path(__file__).resolve().parents[3]
        self.temp_root = Path(tempfile.mkdtemp(prefix="aitp-phase6-"))
        self.kernel_root = self.temp_root / "kernel"
        (self.kernel_root / "schemas").mkdir(parents=True, exist_ok=True)
        for name in (
            "decision-point.schema.json",
            "decision-trace.schema.json",
            "session-chronicle.schema.json",
        ):
            source = self.package_root / "schemas" / name
            target = self.kernel_root / "schemas" / name
            target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

        topic_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        topic_root.mkdir(parents=True, exist_ok=True)
        (topic_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "resume_stage": "L3",
                    "summary": "Benchmark reproduction is complete; the larger-system lane is pending.",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root)

    def test_phase6_schemas_are_valid_and_mirrored(self) -> None:
        root_names = (
            "decision-point.schema.json",
            "decision-trace.schema.json",
            "session-chronicle.schema.json",
        )
        for name in root_names:
            public_path = self.repo_root / "schemas" / name
            kernel_path = self.package_root / "schemas" / name
            public_payload = json.loads(public_path.read_text(encoding="utf-8"))
            kernel_payload = json.loads(kernel_path.read_text(encoding="utf-8"))
            jsonschema.Draft7Validator.check_schema(public_payload)
            self.assertEqual(public_payload, kernel_payload)

        valid_payload = {
            "id": "dp:demo-route-choice",
            "topic_slug": "demo-topic",
            "phase": "routing",
            "layer_context": {"current_layer": "L3"},
            "question": "Which bounded route should run first?",
            "options": [
                {"label": "small-system", "description": "Close the exact benchmark first."},
                {"label": "larger-system", "description": "Push directly to larger finite-size scans."},
            ],
            "blocking": False,
            "created_at": "2026-03-28T00:00:00+00:00",
        }
        jsonschema.validate(
            instance=valid_payload,
            schema=json.loads((self.repo_root / "schemas" / "decision-point.schema.json").read_text(encoding="utf-8")),
        )
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(
                instance={"id": "dp:bad", "blocking": "not-a-bool"},
                schema=json.loads((self.repo_root / "schemas" / "decision-point.schema.json").read_text(encoding="utf-8")),
            )

    def test_decision_point_emit_resolve_list_and_blocking_filter(self) -> None:
        first = emit_decision_point(
            "demo-topic",
            "Clarify the first bounded route?",
            [
                {"label": "small-system", "description": "Close the exact benchmark first."},
                {"label": "larger-system", "description": "Move directly to larger sizes."},
            ],
            False,
            phase="clarification",
            trigger_rule="direction_ambiguity",
            kernel_root=self.kernel_root,
        )
        second = emit_decision_point(
            "demo-topic",
            "Should promotion wait for the operator?",
            [
                {"label": "wait", "description": "Pause for explicit review."},
                {"label": "continue", "description": "Keep the bounded loop moving."},
            ],
            True,
            phase="promotion",
            trigger_rule="promotion_gate",
            decision_id="dp:demo-promotion-choice",
            kernel_root=self.kernel_root,
        )

        pending = list_pending_decision_points("demo-topic", kernel_root=self.kernel_root)
        self.assertEqual(len(pending), 2)
        blocking = check_blocking_decision_points("demo-topic", kernel_root=self.kernel_root)
        self.assertEqual([row["id"] for row in blocking], ["dp:demo-promotion-choice"])

        with self.assertRaises(FileExistsError):
            emit_decision_point(
                "demo-topic",
                "Should promotion wait for the operator?",
                [
                    {"label": "wait", "description": "Pause for explicit review."},
                    {"label": "continue", "description": "Keep the bounded loop moving."},
                ],
                True,
                decision_id="dp:demo-promotion-choice",
                kernel_root=self.kernel_root,
            )

        resolved = resolve_decision_point(
            "demo-topic",
            str(first["decision_point"]["id"]),
            0,
            comment="Start from the smallest exact system.",
            kernel_root=self.kernel_root,
        )
        self.assertEqual(resolved["decision_trace"]["decision_point_ref"], first["decision_point"]["id"])
        self.assertTrue(Path(resolved["decision_trace_path"]).exists())
        self.assertEqual(len(get_all_decision_points("demo-topic", kernel_root=self.kernel_root)), 2)
        self.assertEqual(len(list_pending_decision_points("demo-topic", kernel_root=self.kernel_root)), 1)

        with self.assertRaises(ValueError):
            resolve_decision_point(
                "demo-topic",
                str(first["decision_point"]["id"]),
                1,
                comment="Duplicate resolution should fail.",
                kernel_root=self.kernel_root,
            )

        operator_console = Path(second["operator_console_path"]).read_text(encoding="utf-8")
        self.assertIn("## Pending Decision Points", operator_console)
        self.assertIn("dp:demo-promotion-choice", operator_console)

    def test_decision_trace_record_query_and_related_linkage(self) -> None:
        first = record_decision_trace(
            "demo-topic",
            "Selected the exact benchmark lane first.",
            "small-system",
            "The exact benchmark must close before larger-system inference.",
            ["runtime/topics/demo-topic/topic_state.json"],
            context="Benchmark disagreement still exists for the larger-system lane.",
            output_refs=["runtime/topics/demo-topic/benchmarks/run-001.json"],
            kernel_root=self.kernel_root,
        )
        second = record_decision_trace(
            "demo-topic",
            "Deferred the larger-system lane until the benchmark is stable.",
            "defer",
            "The benchmark surface is not stable enough yet.",
            ["runtime/topics/demo-topic/benchmarks/run-001.json"],
            related_traces=[first["decision_trace"]["id"]],
            would_change_if="A larger exact benchmark closes the disagreement.",
            kernel_root=self.kernel_root,
        )

        traces = get_decision_traces("demo-topic", kernel_root=self.kernel_root)
        self.assertEqual(len(traces), 2)
        second_payload = next(item for item in traces if item["id"] == second["decision_trace"]["id"])
        self.assertEqual(second_payload["related_traces"], [first["decision_trace"]["id"]])

        hits = query_traces("demo-topic", "small-system inference", kernel_root=self.kernel_root)
        self.assertGreaterEqual(len(hits), 1)
        self.assertEqual(hits[0]["id"], first["decision_trace"]["id"])

    def test_session_chronicle_start_append_finalize_latest_and_markdown(self) -> None:
        unresolved = emit_decision_point(
            "demo-topic",
            "Do we need an operator review before promotion?",
            [
                {"label": "yes", "description": "Pause and wait for review."},
                {"label": "no", "description": "Continue with bounded execution."},
            ],
            True,
            phase="promotion",
            trigger_rule="promotion_gate",
            decision_id="dp:demo-review-gate",
            kernel_root=self.kernel_root,
        )
        trace = record_decision_trace(
            "demo-topic",
            "Selected the small-system lane for the first bounded pass.",
            "small-system",
            "It gives the cleanest exact baseline.",
            ["runtime/topics/demo-topic/topic_state.json"],
            kernel_root=self.kernel_root,
        )

        chronicle_id = start_chronicle("demo-topic", kernel_root=self.kernel_root)
        append_chronicle_action(
            chronicle_id,
            "Run the bounded small-system lane",
            "The exact benchmark route was reproduced.",
            artifacts_created=["runtime/topics/demo-topic/benchmarks/run-001.json"],
            decision_trace_refs=[trace["decision_trace"]["id"]],
            kernel_root=self.kernel_root,
        )
        append_chronicle_problem(
            chronicle_id,
            "The larger-system lane is still underdefined.",
            resolution="Carry the ambiguity forward as a pending operator checkpoint.",
            still_open=True,
            kernel_root=self.kernel_root,
        )
        finalized = finalize_chronicle(
            chronicle_id,
            "The benchmark lane is closed; the larger-system route and promotion review remain open.",
            ["Resolve the promotion gate.", "Design the larger-system lane."],
            "Closed the current benchmark-focused session and left the next bounded route explicit.",
            kernel_root=self.kernel_root,
        )

        latest = get_latest_chronicle("demo-topic", kernel_root=self.kernel_root)
        self.assertIsNotNone(latest)
        self.assertEqual(latest["id"], chronicle_id)
        self.assertIn("dp:demo-review-gate", latest["open_decision_points"])
        self.assertIn("session_end", latest)

        markdown = render_chronicle_markdown(chronicle_id, kernel_root=self.kernel_root)
        self.assertIn("## Summary", markdown)
        self.assertIn(trace["decision_trace"]["id"], markdown)
        self.assertIn("Selected the small-system lane for the first bounded pass.", markdown)
        self.assertIn("dp:demo-review-gate: Do we need an operator review before promotion? [UNRESOLVED]", markdown)
        self.assertTrue(Path(finalized["markdown_path"]).exists())
        self.assertTrue(Path(unresolved["path"]).exists())

    def test_pre_commit_validator_accepts_valid_and_rejects_invalid_phase6_json(self) -> None:
        validator = self.repo_root / "hooks" / "pre-commit-validate-schemas"
        valid_dir = self.temp_root / "decision_points"
        valid_dir.mkdir(parents=True, exist_ok=True)
        valid_path = valid_dir / "dp__demo.json"
        valid_path.write_text(
            json.dumps(
                {
                    "id": "dp:demo-route-choice",
                    "topic_slug": "demo-topic",
                    "phase": "routing",
                    "layer_context": {"current_layer": "L3"},
                    "question": "Which bounded route should run first?",
                    "options": [
                        {"label": "small-system", "description": "Close the exact benchmark first."},
                        {"label": "larger-system", "description": "Push directly to larger finite-size scans."},
                    ],
                    "blocking": False,
                    "created_at": "2026-03-28T00:00:00+00:00",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        invalid_path = valid_dir / "dp__bad.json"
        invalid_path.write_text(
            json.dumps(
                {
                    "id": "dp:demo-bad",
                    "topic_slug": "demo-topic",
                    "phase": "routing",
                    "layer_context": {"current_layer": "L3"},
                    "question": "Broken decision point",
                    "options": [{"label": "only", "description": "Too few options"}],
                    "blocking": "not-a-bool",
                    "created_at": "2026-03-28T00:00:00+00:00",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        good = subprocess.run([sys.executable, str(validator), str(valid_path)], capture_output=True, text=True)
        bad = subprocess.run([sys.executable, str(validator), str(invalid_path)], capture_output=True, text=True)

        self.assertEqual(good.returncode, 0, msg=good.stderr)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("pre-commit-validate-schemas", bad.stderr)


if __name__ == "__main__":
    unittest.main()
