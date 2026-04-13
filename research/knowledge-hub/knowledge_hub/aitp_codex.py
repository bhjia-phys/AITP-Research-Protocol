from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

from .aitp_service import AITPService


def _emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _trim_steering_fragment(value: str) -> str:
    cleaned = str(value or "").strip()
    cleaned = re.sub(r"^[\s\"'“”‘’`]+", "", cleaned)
    cleaned = re.split(
        r"(?:\n|[，,;；]\s*(?:并且|并|然后|同时)|[，,;；]\s*(?:and then|and|then)\b)",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return cleaned.strip(" \t\r\n.,;:!?\"'`，。；：！？“”‘’")


def extract_topic_direction_change(task: str) -> str | None:
    raw_task = str(task or "").strip()
    if not raw_task:
        return None

    patterns = (
        r"方向(?:改成|改为|变成|换成|换为|转成|转为)\s*[:：]?\s*(?P<direction>.+)",
        r"(?:转向|聚焦到|聚焦于|重点放到|重点放在)\s*[:：]?\s*(?P<direction>.+)",
        r"(?:focus on|redirect to|shift to|move to|change direction to|direction changed to)\s+(?P<direction>.+)",
    )
    for pattern in patterns:
        match = re.search(pattern, raw_task, flags=re.IGNORECASE)
        if not match:
            continue
        direction = _trim_steering_fragment(match.group("direction"))
        if direction:
            return direction
    return None


def apply_topic_steering(
    service: AITPService,
    *,
    topic_slug: str,
    task: str,
    run_id: str | None,
    updated_by: str,
    innovation_direction: str | None = None,
    steering_decision: str = "continue",
) -> tuple[str, dict[str, Any] | None, str | None]:
    resolved_direction = innovation_direction or extract_topic_direction_change(task)
    if not resolved_direction:
        return task, None, None

    normalized_task = f"Continue the topic under updated innovation direction: {resolved_direction}"
    payload = service.steer_topic(
        topic_slug=topic_slug,
        innovation_direction=resolved_direction,
        decision=steering_decision,
        run_id=run_id,
        updated_by=updated_by,
        summary=normalized_task,
        human_request=task,
    )
    return normalized_task, payload, payload.get("control_note_path")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Codex through the AITP runtime wrapper")
    parser.add_argument("--kernel-root", type=Path)
    parser.add_argument("--repo-root", type=Path)

    topic_group = parser.add_mutually_exclusive_group(required=False)
    topic_group.add_argument("--topic-slug")
    topic_group.add_argument("--topic")
    topic_group.add_argument("--current-topic", action="store_true")
    topic_group.add_argument("--latest-topic", action="store_true")

    parser.add_argument("--statement")
    parser.add_argument("--run-id")
    parser.add_argument("--control-note")
    parser.add_argument("--updated-by", default="aitp-codex")
    parser.add_argument("--skill-query", action="append", default=[])
    parser.add_argument("--max-auto-steps", type=int, default=4)
    parser.add_argument("--model")
    parser.add_argument("--profile")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("task", help="Human request to continue through Codex")
    return parser


def _service_from_args(args: argparse.Namespace) -> AITPService:
    kwargs: dict[str, Any] = {}
    if args.kernel_root:
        kwargs["kernel_root"] = args.kernel_root
    if args.repo_root:
        kwargs["repo_root"] = args.repo_root
    return AITPService(**kwargs)


def build_codex_prompt(payload: dict[str, Any]) -> str:
    topic_slug = payload["topic_slug"]
    run_id = payload.get("run_id") or "(missing)"
    bootstrap = payload["bootstrap"]
    loop_state = payload["loop_state"]
    session_start = payload.get("session_start") or {}
    files = bootstrap["files"]
    capability_report_path = payload["capability_audit"]["capability_report_path"]
    trust_report_path = (
        payload["trust_audit"]["trust_report_path"] if payload.get("trust_audit") else "(missing)"
    )
    pointers = bootstrap["topic_state"].get("pointers", {})
    control_note_path = pointers.get("control_note_path") or "(missing)"
    innovation_direction_path = pointers.get("innovation_direction_path") or "(missing)"
    innovation_decisions_path = pointers.get("innovation_decisions_path") or "(missing)"
    session_start_note_path = session_start.get("session_start_note_path") or "(missing)"
    session_start_contract_path = session_start.get("session_start_contract_path") or "(missing)"
    human_interaction_posture = session_start.get("human_interaction_posture") or {}
    autonomy_posture = session_start.get("autonomy_posture") or {}
    theory_context_injection = session_start.get("theory_context_injection") or {}
    injected_theory_fragments = [
        row
        for row in theory_context_injection.get("fragments") or []
        if str((row or {}).get("delivery_status") or "").strip() == "inject_now"
    ]
    runtime_protocol_note_path = (
        ((session_start.get("artifacts") or {}).get("runtime_protocol_note_path"))
        or (payload.get("runtime_protocol") or {}).get("runtime_protocol_note_path")
        or bootstrap["runtime_root"] + "/runtime_protocol.generated.md"
    )
    startup_artifacts = [
        session_start_note_path,
        runtime_protocol_note_path,
        session_start_contract_path,
        files["agent_brief"],
        files["operator_console"],
        files["conformance_report"],
        payload["loop_state_path"],
        capability_report_path,
        trust_report_path,
        innovation_direction_path,
        innovation_decisions_path,
        control_note_path,
        *[str(row.get("path") or "(missing)") for row in injected_theory_fragments],
    ]

    lines = [
        "Use the installed `aitp-runtime` skill and stay inside AITP.",
        f"Topic slug: `{topic_slug}`",
        f"Run id: `{run_id}`",
        f"Human request: {loop_state['human_request']}",
        f"Runtime root: `{bootstrap['runtime_root']}`",
        "",
        "Start by reading these artifacts:",
    ]
    lines.extend([f"- `{item}`" for item in startup_artifacts])
    if injected_theory_fragments:
        lines.extend(["", "Theory context injection:"])
        lines.extend(
            f"- [{row.get('kind') or 'theory_context'}] {row.get('summary') or '(missing)'}"
            for row in injected_theory_fragments
        )
    lines.extend(
        [
            "",
            "Current AITP state:",
            f"- conformance: `{loop_state['exit_conformance']}`",
            f"- capability: `{loop_state['capability_status']}`",
            f"- trust: `{loop_state['trust_status']}`",
            "",
            "Human interaction posture:",
            f"- requires human input now: `{str(bool(human_interaction_posture.get('requires_human_input_now'))).lower()}`",
            f"- summary: {human_interaction_posture.get('summary') or '(missing)'}",
            f"- next action: {human_interaction_posture.get('next_action') or '(missing)'}",
            "",
            "Autonomous continuation:",
            f"- mode: `{autonomy_posture.get('mode') or '(missing)'}`",
            f"- summary: {autonomy_posture.get('summary') or '(missing)'}",
            f"- applied auto-step budget: `{autonomy_posture.get('applied_max_auto_steps') if autonomy_posture.get('applied_max_auto_steps') is not None else '(none)'}`",
            "",
            "Session-start rule:",
            "- do not skip the durable session-start contract; it is the authoritative translation of the user's chat request into routing, current-topic resolution, and immediate startup order",
            "",
            "Steering rule:",
            "- if innovation direction or control note was auto-materialized from the human request, treat those durable files as the authoritative translation of that request before touching the queue",
            "",
            "Hard rules:",
            "- treat runtime and validation artifacts as source of truth",
            (
                f"- do not trust or promote reusable operations until `aitp trust-audit --topic-slug {topic_slug} "
                f"--run-id {run_id}` passes"
            ),
            "- if you change reusable operations, update the operation manifest and rerun trust-audit",
            f"- close with `aitp audit --topic-slug {topic_slug} --phase exit`",
            "",
            f"Continue the task now: {loop_state['human_request']}",
        ]
    )
    return "\n".join(lines)


def invoke_codex(
    *,
    prompt: str,
    repo_root: str,
    kernel_root: str,
    model: str | None,
    profile: str | None,
) -> int:
    codex = shutil.which("codex")
    if codex is None:
        raise FileNotFoundError("Codex CLI is not installed or not on PATH.")

    command = [codex, "exec", "--cd", repo_root]
    if model:
        command.extend(["--model", model])
    if profile:
        command.extend(["--profile", profile])
    command.append(prompt)

    env = os.environ.copy()
    env.setdefault("AITP_KERNEL_ROOT", kernel_root)
    env.setdefault("AITP_REPO_ROOT", repo_root)
    completed = subprocess.run(command, check=False, env=env)
    return completed.returncode


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    service = _service_from_args(args)
    session = service.start_chat_session(
        task=args.task,
        explicit_topic_slug=args.topic_slug,
        explicit_topic=args.topic,
        explicit_current_topic=args.current_topic,
        explicit_latest_topic=args.latest_topic,
        statement=args.statement,
        run_id=args.run_id,
        control_note=args.control_note,
        updated_by=args.updated_by,
        skill_queries=args.skill_query,
        max_auto_steps=args.max_auto_steps,
    )
    routing = session["routing"]
    payload = session["loop_payload"]
    prompt = build_codex_prompt(payload)

    result = {
        "topic_slug": payload["topic_slug"],
        "run_id": payload.get("run_id"),
        "routing": routing,
        "loop_state_path": payload["loop_state_path"],
        "session_start_contract_path": session.get("session_start_contract_path"),
        "session_start_note_path": session.get("session_start_note_path"),
        "capability_report_path": payload["capability_audit"]["capability_report_path"],
        "trust_report_path": payload["trust_audit"]["trust_report_path"] if payload.get("trust_audit") else None,
        "prompt": prompt,
    }
    if args.dry_run:
        _emit(result, args.json)
        return 0

    if args.json:
        _emit(result, True)
    return invoke_codex(
        prompt=prompt,
        repo_root=str(service.repo_root),
        kernel_root=str(service.kernel_root),
        model=args.model,
        profile=args.profile,
    )


if __name__ == "__main__":
    raise SystemExit(main())
