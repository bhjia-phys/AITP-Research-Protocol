#!/usr/bin/env python3
"""Audit whether a topic currently satisfies the AITP runtime contract."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, code: str, description: str) -> dict:
    return {
        "code": code,
        "description": description,
        "status": "pass" if condition else "fail",
    }


def build_report(state: dict) -> str:
    lines = [
        "# Topic conformance report",
        "",
        f"- Topic slug: `{state['topic_slug']}`",
        f"- Phase: `{state['phase']}`",
        f"- Updated at: `{state['updated_at']}`",
        f"- Updated by: `{state['updated_by']}`",
        f"- Overall status: `{state['overall_status']}`",
        "",
        "## Checks",
        "",
    ]
    for item in state["checks"]:
        lines.append(f"- [{item['status']}] `{item['code']}` {item['description']}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A passed report means the topic is operating through the AITP runtime contract.",
            "- It does not certify scientific correctness by itself.",
            "",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-slug", required=True)
    parser.add_argument("--phase", choices=["entry", "exit"], default="entry")
    parser.add_argument("--updated-by", default="codex")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    knowledge_root = Path(__file__).resolve().parents[2]
    topic_root = knowledge_root / "runtime" / "topics" / args.topic_slug

    topic_state = read_json(topic_root / "topic_state.json")
    interaction_state = read_json(topic_root / "interaction_state.json")
    action_queue_text = (topic_root / "action_queue.jsonl").read_text(encoding="utf-8") if (topic_root / "action_queue.jsonl").exists() else ""
    queue_rows = read_jsonl(topic_root / "action_queue.jsonl")
    agent_brief_path = topic_root / "agent_brief.md"
    operator_console_path = topic_root / "operator_console.md"
    resume_path = topic_root / "resume.md"
    unfinished_work = read_json(topic_root / "unfinished_work.json")
    next_action_decision = read_json(topic_root / "next_action_decision.json")
    unfinished_work_note_path = topic_root / "unfinished_work.md"
    next_action_decision_note_path = topic_root / "next_action_decision.md"
    action_queue_contract_generated = read_json(topic_root / "action_queue_contract.generated.json")
    action_queue_contract_generated_note_path = topic_root / "action_queue_contract.generated.md"

    checks = [
        check(topic_state is not None, "topic_state_present", "topic_state.json exists and is readable."),
        check(resume_path.exists(), "resume_present", "resume.md exists."),
        check(bool(action_queue_text.strip()), "action_queue_present", "action_queue.jsonl exists and is non-empty."),
        check(agent_brief_path.exists(), "agent_brief_present", "agent_brief.md exists."),
        check(interaction_state is not None, "interaction_state_present", "interaction_state.json exists and is readable."),
        check(operator_console_path.exists(), "operator_console_present", "operator_console.md exists."),
        check(unfinished_work is not None, "unfinished_work_present", "unfinished_work.json exists and is readable."),
        check(unfinished_work_note_path.exists(), "unfinished_work_note_present", "unfinished_work.md exists."),
        check(
            next_action_decision is not None,
            "next_action_decision_present",
            "next_action_decision.json exists and is readable.",
        ),
        check(
            next_action_decision_note_path.exists(),
            "next_action_decision_note_present",
            "next_action_decision.md exists.",
        ),
        check(
            action_queue_contract_generated is not None,
            "action_queue_contract_generated_present",
            "action_queue_contract.generated.json exists and is readable.",
        ),
        check(
            action_queue_contract_generated_note_path.exists(),
            "action_queue_contract_generated_note_present",
            "action_queue_contract.generated.md exists.",
        ),
    ]

    if topic_state is not None:
        checks.extend(
            [
                check(
                    bool(topic_state.get("resume_stage")),
                    "resume_stage_declared",
                    "topic_state.json declares a resume stage.",
                ),
                check(
                    bool(topic_state.get("pointers")),
                    "layer_pointers_present",
                    "topic_state.json exposes layer pointers.",
                ),
                check(
                    bool(topic_state.get("research_mode")),
                    "research_mode_declared",
                    "topic_state.json declares the active research mode.",
                ),
                check(
                    bool(topic_state.get("active_executor_kind")),
                    "executor_kind_declared",
                    "topic_state.json declares the active executor kind.",
                ),
            ]
        )

        pointers = topic_state.get("pointers") or {}
        result_manifest_ref = str(pointers.get("result_manifest_path") or "").strip()
        trajectory_ref = str(pointers.get("trajectory_log_path") or "").strip()
        failure_ref = str(pointers.get("failure_classification_path") or "").strip()
        if result_manifest_ref:
            checks.extend(
                [
                    check(
                        bool(trajectory_ref),
                        "trajectory_log_declared",
                        "A result-manifested closed-loop run declares a trajectory log pointer.",
                    ),
                    check(
                        bool(failure_ref),
                        "failure_classification_declared",
                        "A result-manifested closed-loop run declares a failure-classification pointer.",
                    ),
                ]
            )

    if interaction_state is not None:
        checks.extend(
            [
                check(
                    bool(interaction_state.get("human_request")),
                    "human_request_declared",
                    "interaction_state.json records the human-facing request.",
                ),
                check(
                    bool(interaction_state.get("human_edit_surfaces")),
                    "human_edit_surfaces_present",
                    "interaction_state.json exposes editable surfaces by layer.",
                ),
                check(
                    bool(interaction_state.get("delivery_contract")),
                    "delivery_contract_present",
                    "interaction_state.json declares the delivery contract.",
                ),
                check(
                    bool(interaction_state.get("capability_adaptation", {}).get("protocol_path")),
                    "capability_protocol_declared",
                    "interaction_state.json points to the skill-adaptation protocol.",
                ),
                check(
                    bool(interaction_state.get("decision_surface", {}).get("next_action_decision_path")),
                    "decision_surface_declared",
                    "interaction_state.json declares the decision-surface artifacts.",
                ),
                check(
                    bool(interaction_state.get("action_queue_surface", {}).get("generated_contract_path")),
                    "action_queue_surface_declared",
                    "interaction_state.json declares the generated action-queue contract snapshot.",
                ),
            ]
        )

    if next_action_decision is not None:
        selected_action_id = str(
            ((next_action_decision.get("selected_action") or {}).get("action_id") or "")
        ).strip()
        queue_action_ids = {str(row.get("action_id") or "").strip() for row in queue_rows}
        checks.extend(
            [
                check(
                    bool(next_action_decision.get("policy", {}).get("default_mode")),
                    "decision_policy_declared",
                    "next_action_decision.json declares the decision policy.",
                ),
                check(
                    bool(next_action_decision.get("decision_mode")),
                    "decision_mode_declared",
                    "next_action_decision.json declares the active decision mode.",
                ),
                check(
                    not selected_action_id or selected_action_id in queue_action_ids,
                    "decision_action_resolves",
                    "Selected decision action resolves to an action_queue entry when present.",
                ),
            ]
        )

    overall_status = "pass" if all(item["status"] == "pass" for item in checks) else "fail"
    payload = {
        "topic_slug": args.topic_slug,
        "phase": args.phase,
        "updated_at": now_iso(),
        "updated_by": args.updated_by,
        "overall_status": overall_status,
        "checks": checks,
    }

    write_json(topic_root / "conformance_state.json", payload)
    write_text(topic_root / "conformance_report.md", build_report(payload))
    print(f"Conformance audit {overall_status} for {args.topic_slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
