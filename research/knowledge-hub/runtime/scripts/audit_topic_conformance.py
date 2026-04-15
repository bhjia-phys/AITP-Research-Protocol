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


def _dedupe_strings(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            deduped.append(text)
    return deduped


def _baseline_status_ready(status: str) -> bool:
    return str(status or "").strip().lower() in {
        "not_required",
        "confirmed",
        "pass",
        "passed",
        "satisfied",
        "complete",
        "completed",
    }


def _load_return_packet_status(topic_root: Path, row: dict) -> str:
    packet_path = str(row.get("return_packet_path") or "").strip()
    if not packet_path:
        return ""
    candidate = Path(packet_path)
    if not candidate.is_absolute():
        candidate = topic_root.parents[2] / candidate
    payload = read_json(candidate)
    return str((payload or {}).get("return_status") or "").strip()


def build_mechanical_completion_preflight(
    *,
    knowledge_root: Path,
    topic_root: Path,
    topic_slug: str,
    topic_state: dict | None,
    queue_rows: list[dict],
) -> dict:
    run_id = str((topic_state or {}).get("latest_run_id") or "").strip()
    topic_shell_root = topic_root.parent

    operations_root = (
        topic_shell_root / "L4" / "runs" / run_id / "operations"
        if run_id
        else None
    )
    operations: list[dict] = []
    operations_missing_baseline: list[str] = []
    if operations_root and operations_root.exists():
        for manifest_path in sorted(operations_root.glob("*/operation_manifest.json")):
            manifest = read_json(manifest_path)
            if manifest is None:
                continue
            title = str(manifest.get("title") or manifest.get("operation_id") or manifest_path.parent.name).strip()
            baseline_status = str(manifest.get("baseline_status") or "").strip() or "missing"
            ready = _baseline_status_ready(baseline_status)
            operations.append(
                {
                    "operation_id": str(manifest.get("operation_id") or "").strip(),
                    "title": title,
                    "baseline_status": baseline_status,
                    "baseline_ready": ready,
                    "manifest_path": str(manifest_path),
                }
            )
            if not ready:
                operations_missing_baseline.append(f"{title}: baseline_status={baseline_status}")

    candidate_rows = (
        read_jsonl(topic_shell_root / "L3" / "runs" / run_id / "candidate_ledger.jsonl")
        if run_id
        else []
    )
    unresolved_gap_reasons: list[str] = []
    for row in candidate_rows:
        candidate_id = str(row.get("candidate_id") or "candidate").strip()
        for blocker in row.get("promotion_blockers") or []:
            text = str(blocker or "").strip()
            if text:
                unresolved_gap_reasons.append(f"{candidate_id}: {text}")
        if row.get("split_required"):
            unresolved_gap_reasons.append(f"{candidate_id}: split required before completion")
        if row.get("cited_recovery_required"):
            unresolved_gap_reasons.append(f"{candidate_id}: cited recovery still required")
        for gap_id in row.get("followup_gap_ids") or []:
            text = str(gap_id or "").strip()
            if text:
                unresolved_gap_reasons.append(text)
        for gap_id in row.get("parent_gap_ids") or []:
            text = str(gap_id or "").strip()
            if text:
                unresolved_gap_reasons.append(text)

    followup_rows = read_jsonl(topic_root / "followup_subtopics.jsonl")
    reintegration_rows = read_jsonl(topic_root / "followup_reintegration.jsonl")
    reintegrated_children = {
        str(row.get("child_topic_slug") or "").strip()
        for row in reintegration_rows
        if str(row.get("child_topic_slug") or "").strip()
    }
    pending_followups: list[str] = []
    for row in queue_rows:
        if str(row.get("status") or "").strip() != "pending":
            continue
        if str(row.get("action_type") or "").strip() == "manual_followup":
            pending_followups.append(
                str(row.get("summary") or row.get("action_id") or "pending manual follow-up").strip()
            )
    for row in followup_rows:
        child_topic_slug = str(row.get("child_topic_slug") or "").strip()
        if not child_topic_slug or child_topic_slug in reintegrated_children:
            continue
        row_status = str(row.get("status") or "").strip()
        return_status = _load_return_packet_status(topic_root, row)
        if row_status == "returned_with_gap" or return_status == "returned_with_gap":
            unresolved_gap_reasons.append(f"{child_topic_slug}: returned from follow-up with unresolved gaps")
            pending_followups.append(f"{child_topic_slug}: follow-up return still unresolved")
            continue
        if row_status == "reintegrated":
            continue
        pending_followups.append(f"{child_topic_slug}: follow-up child topic not yet reintegrated")

    followup_gap_writeback_rows = read_jsonl(topic_root / "followup_gap_writeback.jsonl")
    for row in followup_gap_writeback_rows:
        child_topic_slug = str(row.get("child_topic_slug") or "followup-child").strip()
        summary = str(row.get("summary") or "").strip()
        unresolved_gap_reasons.append(
            f"{child_topic_slug}: {summary}" if summary else f"{child_topic_slug}: follow-up gap writeback remains open"
        )

    unresolved_gap_reasons = _dedupe_strings(unresolved_gap_reasons)
    pending_followups = _dedupe_strings(pending_followups)
    checks = [
        {
            "code": "operations_baseline_confirmed",
            "status": "pass" if not operations_missing_baseline else "fail",
            "summary": (
                "All discovered operation manifests have a mechanically accepted baseline status."
                if not operations_missing_baseline
                else "At least one operation manifest still lacks a confirmed baseline."
            ),
        },
        {
            "code": "unresolved_gaps_clear",
            "status": "pass" if not unresolved_gap_reasons else "fail",
            "summary": (
                "No unresolved candidate or follow-up gap debt is currently recorded."
                if not unresolved_gap_reasons
                else "At least one explicit gap or blocker remains open."
            ),
        },
        {
            "code": "pending_followups_clear",
            "status": "pass" if not pending_followups else "fail",
            "summary": (
                "No pending manual or child follow-up work remains."
                if not pending_followups
                else "At least one follow-up path is still pending."
            ),
        },
    ]
    blocking_reasons = _dedupe_strings(operations_missing_baseline + unresolved_gap_reasons + pending_followups)
    status = "pass" if all(item["status"] == "pass" for item in checks) else "blocked"
    return {
        "status": status,
        "llm_audit_eligible": status == "pass",
        "run_id": run_id,
        "operation_count": len(operations),
        "unresolved_gap_count": len(unresolved_gap_reasons),
        "pending_followup_count": len(pending_followups),
        "checks": checks,
        "blocking_reasons": blocking_reasons,
        "operations": operations,
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
    preflight = state.get("mechanical_completion_preflight") or {}
    if preflight:
        lines.extend(
            [
                "",
                "## Mechanical completion preflight",
                "",
                f"- Status: `{preflight.get('status') or 'unknown'}`",
                f"- LLM audit eligible: `{str(bool(preflight.get('llm_audit_eligible'))).lower()}`",
                f"- Operation count: `{preflight.get('operation_count') or 0}`",
                f"- Unresolved gap count: `{preflight.get('unresolved_gap_count') or 0}`",
                f"- Pending follow-up count: `{preflight.get('pending_followup_count') or 0}`",
                "",
            ]
        )
        for item in preflight.get("checks") or []:
            lines.append(f"- [{item['status']}] `{item['code']}` {item.get('summary') or '(missing)' }")
        blocking_reasons = list(preflight.get("blocking_reasons") or [])
        lines.extend(["", "### Blocking reasons", ""])
        for item in blocking_reasons or ["(none)"]:
            lines.append(f"- {item}")
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
    parser.add_argument("--knowledge-root")
    parser.add_argument("--topic-slug", required=True)
    parser.add_argument("--phase", choices=["entry", "exit"], default="entry")
    parser.add_argument("--updated-by", default="codex")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    knowledge_root = (
        Path(args.knowledge_root).expanduser().resolve()
        if args.knowledge_root
        else Path(__file__).resolve().parents[2]
    )
    topic_root = knowledge_root / "topics" / args.topic_slug / "runtime"

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

    mechanical_completion_preflight = build_mechanical_completion_preflight(
        knowledge_root=knowledge_root,
        topic_root=topic_root,
        topic_slug=args.topic_slug,
        topic_state=topic_state,
        queue_rows=queue_rows,
    )

    overall_status = (
        "pass"
        if all(item["status"] == "pass" for item in checks)
        and mechanical_completion_preflight.get("status") == "pass"
        else "fail"
    )
    payload = {
        "topic_slug": args.topic_slug,
        "phase": args.phase,
        "updated_at": now_iso(),
        "updated_by": args.updated_by,
        "overall_status": overall_status,
        "checks": checks,
        "mechanical_completion_preflight": mechanical_completion_preflight,
    }

    write_json(topic_root / "conformance_state.json", payload)
    write_text(topic_root / "conformance_report.md", build_report(payload))
    print(f"Conformance audit {overall_status} for {args.topic_slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
