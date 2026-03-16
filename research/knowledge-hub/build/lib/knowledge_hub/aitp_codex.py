from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from typing import Any

from .aitp_service import AITPService


def _emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Codex through the AITP runtime wrapper")
    parser.add_argument("--kernel-root")
    parser.add_argument("--repo-root")

    topic_group = parser.add_mutually_exclusive_group(required=True)
    topic_group.add_argument("--topic-slug")
    topic_group.add_argument("--topic")

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
    files = bootstrap["files"]
    capability_report_path = payload["capability_audit"]["capability_report_path"]
    trust_report_path = (
        payload["trust_audit"]["trust_report_path"] if payload.get("trust_audit") else "(missing)"
    )
    control_note_path = bootstrap["topic_state"].get("pointers", {}).get("control_note_path") or "(missing)"

    lines = [
        "Use the installed `aitp-runtime` skill and stay inside AITP.",
        f"Topic slug: `{topic_slug}`",
        f"Run id: `{run_id}`",
        f"Human request: {loop_state['human_request']}",
        f"Runtime root: `{bootstrap['runtime_root']}`",
        "",
        "Start by reading these artifacts:",
        f"- `{files['agent_brief']}`",
        f"- `{files['operator_console']}`",
        f"- `{files['conformance_report']}`",
        f"- `{payload['loop_state_path']}`",
        f"- `{capability_report_path}`",
        f"- `{trust_report_path}`",
        f"- `{control_note_path}`",
        "",
        "Current AITP state:",
        f"- conformance: `{loop_state['exit_conformance']}`",
        f"- capability: `{loop_state['capability_status']}`",
        f"- trust: `{loop_state['trust_status']}`",
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

    payload = service.run_topic_loop(
        topic_slug=args.topic_slug,
        topic=args.topic,
        statement=args.statement,
        run_id=args.run_id,
        control_note=args.control_note,
        updated_by=args.updated_by,
        human_request=args.task,
        skill_queries=args.skill_query,
        max_auto_steps=args.max_auto_steps,
    )
    prompt = build_codex_prompt(payload)

    result = {
        "topic_slug": payload["topic_slug"],
        "run_id": payload.get("run_id"),
        "loop_state_path": payload["loop_state_path"],
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
