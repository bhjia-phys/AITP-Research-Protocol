from __future__ import annotations

import json
import shutil
import sys
import unittest
from pathlib import Path



def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from tests_support import copy_kernel_schema_files, make_temp_kernel  # noqa: E402
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
        self.fixture = make_temp_kernel("aitp-phase6-")
        self.temp_root = self.fixture.temp_root
        self.kernel_root = self.fixture.kernel_root
        copy_kernel_schema_files(
            self.package_root,
            self.kernel_root,
            "decision-point.schema.json",
            "decision-trace.schema.json",
            "session-chronicle.schema.json",
        )

        topic_root = self.kernel_root / "topics" / "demo-topic" / "runtime"
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
        self.fixture.cleanup()

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
            ["topics/demo-topic/runtime/topic_state.json"],
            context="Benchmark disagreement still exists for the larger-system lane.",
            output_refs=["topics/demo-topic/runtime/benchmarks/run-001.json"],
            kernel_root=self.kernel_root,
        )
        second = record_decision_trace(
            "demo-topic",
            "Deferred the larger-system lane until the benchmark is stable.",
            "defer",
            "The benchmark surface is not stable enough yet.",
            ["topics/demo-topic/runtime/benchmarks/run-001.json"],
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
            ["topics/demo-topic/runtime/topic_state.json"],
            kernel_root=self.kernel_root,
        )

        chronicle_id = start_chronicle("demo-topic", kernel_root=self.kernel_root)
        append_chronicle_action(
            chronicle_id,
            "Run the bounded small-system lane",
            "The exact benchmark route was reproduced.",
            artifacts_created=["topics/demo-topic/runtime/benchmarks/run-001.json"],
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

if __name__ == "__main__":
    unittest.main()
