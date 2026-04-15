#!/usr/bin/env python
"""Shared bounded acceptance harness for deep-execution runtime parity."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from run_first_run_topic_acceptance import (
    KERNEL_ROOT,
    LOOP_REQUEST,
    REPO_ROOT,
    TOPIC_SLUG,
    TOPIC_STATEMENT,
    TOPIC_TITLE,
    check,
    ensure_exists,
    prepare_first_run_kernel,
    run_cli_json,
)


ENTRY_SURFACES = {
    "codex": "native `using-aitp` skill discovery",
    "claude_code": "Claude SessionStart bootstrap",
    "opencode": "OpenCode plugin bootstrap",
}
BOUNDED_SESSION_START_TASK = f"Start a new topic: {TOPIC_TITLE}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", choices=sorted(ENTRY_SURFACES), required=True)
    parser.add_argument("--package-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--json", action="store_true")
    return parser


def acceptance_command(runtime: str) -> str:
    return f"python research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py --runtime {runtime} --json"


def expected_artifacts(topic_slug: str) -> list[str]:
    return [
        f"topics/{topic_slug}/runtime/topic_state.json",
        f"topics/{topic_slug}/runtime/loop_state.json",
        f"topics/{topic_slug}/runtime/runtime_protocol.generated.json",
        f"topics/{topic_slug}/runtime/runtime_protocol.generated.md",
        f"status --topic-slug {topic_slug} --json -> selected_action_id",
    ]


def posture_contract_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    human_interaction_posture = payload.get("human_interaction_posture") or {}
    autonomy_posture = payload.get("autonomy_posture") or {}
    return {
        "human_interaction_posture_present": bool(human_interaction_posture),
        "autonomy_posture_present": bool(autonomy_posture),
        "requires_human_input_now": human_interaction_posture.get("requires_human_input_now"),
        "autonomy_mode": autonomy_posture.get("mode"),
        "applied_max_auto_steps": autonomy_posture.get("applied_max_auto_steps"),
    }


def pending_probe_payload(runtime: str) -> dict[str, Any]:
    return {
        "report_kind": "runtime_deep_execution_parity",
        "runtime": runtime,
        "baseline_runtime": "codex",
        "status": "probe_pending",
        "entry_surface": ENTRY_SURFACES[runtime],
        "acceptance_command": acceptance_command(runtime),
        "expected_artifacts": expected_artifacts(TOPIC_SLUG),
        "checked_artifacts": [],
        "blockers": ["runtime_specific_probe_not_implemented"],
        "notes": [
            "The shared parity harness exists now, but this runtime-specific deep-execution probe has not landed yet.",
            "Use the Codex baseline report as the current artifact bar until the dedicated probe is implemented.",
        ],
    }


def _run_process_json(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RuntimeError(f"{' '.join(command)} failed: {detail}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        preview = completed.stdout[:400].strip()
        raise RuntimeError(f"{' '.join(command)} did not emit valid JSON: {preview}") from exc


def _install_claude_project_assets(*, package_root: Path, repo_root: Path, project_root: Path) -> dict[str, Any]:
    return run_cli_json(
        package_root=package_root,
        kernel_root=package_root,
        repo_root=repo_root,
        args=[
            "install-agent",
            "--agent",
            "claude-code",
            "--scope",
            "project",
            "--target-root",
            str(project_root),
            "--no-mcp",
            "--json",
        ],
    )


def _install_opencode_project_assets(*, package_root: Path, repo_root: Path, project_root: Path) -> dict[str, Any]:
    return run_cli_json(
        package_root=package_root,
        kernel_root=package_root,
        repo_root=repo_root,
        args=[
            "install-agent",
            "--agent",
            "opencode",
            "--scope",
            "project",
            "--target-root",
            str(project_root),
            "--no-mcp",
            "--json",
        ],
    )


def _run_claude_session_start_bootstrap(*, claude_root: Path) -> tuple[dict[str, Any], str]:
    env = {
        **os.environ,
        "CLAUDE_PLUGIN_ROOT": str(claude_root),
        "AITP_PYTHON": sys.executable,
    }
    wrapper_path = claude_root / "hooks" / "run-hook.cmd"
    python_hook_path = claude_root / "hooks" / "session-start.py"

    if os.name == "nt" and wrapper_path.exists():
        return (
            _run_process_json(["cmd", "/c", str(wrapper_path), "session-start"], env=env),
            str(wrapper_path),
        )

    return (
        _run_process_json([sys.executable, str(python_hook_path)], env=env),
        str(python_hook_path),
    )


def _run_opencode_plugin_bootstrap(*, plugin_path: Path) -> tuple[dict[str, Any], str]:
    node_path = shutil.which("node")
    if not node_path:
        raise FileNotFoundError("Node.js is required to execute the OpenCode plugin probe.")

    node_script = """
import { pathToFileURL } from 'url';

const pluginPath = process.argv[1];
const mod = await import(pathToFileURL(pluginPath).href);
const factory = mod.default || mod.AITPPlugin;
const plugin = await factory();
const config = {};
await plugin.config(config);
const output = {};
await plugin['experimental.chat.system.transform']({}, output);
console.log(JSON.stringify({
  config,
  output,
  hasConfigHook: typeof plugin.config === 'function',
  hasTransformHook: typeof plugin['experimental.chat.system.transform'] === 'function'
}, null, 2));
""".strip()
    return (
        _run_process_json([node_path, "--input-type=module", "-e", node_script, str(plugin_path)]),
        node_path,
    )


def claude_probe_payload(*, package_root: Path, repo_root: Path, work_root: Path) -> dict[str, Any]:
    project_root = work_root / "claude-workspace"
    project_root.mkdir(parents=True, exist_ok=True)
    install_payload = _install_claude_project_assets(
        package_root=package_root,
        repo_root=repo_root,
        project_root=project_root,
    )
    claude_root = project_root / ".claude"
    bootstrap_payload, bootstrap_command_path = _run_claude_session_start_bootstrap(claude_root=claude_root)

    hook_output = bootstrap_payload.get("hookSpecificOutput") or {}
    additional_context = str(
        hook_output.get("additionalContext")
        or bootstrap_payload.get("additional_context")
        or ""
    )
    hook_event_name = str(hook_output.get("hookEventName") or "SessionStart")

    check(hook_event_name == "SessionStart", "Claude bootstrap should report the SessionStart hook event")
    check("using-aitp" in additional_context, "Claude bootstrap should inject the using-aitp skill content")
    check(
        "AITP-enabled Claude Code session" in additional_context,
        "Claude bootstrap should identify the Claude Code SessionStart context",
    )

    kernel_root = work_root / "kernel"
    prepare_first_run_kernel(package_root, kernel_root)

    session_start_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "session-start",
            "--statement",
            TOPIC_STATEMENT,
            "--max-auto-steps",
            "1",
            "--load-profile",
            "light",
            "--json",
            BOUNDED_SESSION_START_TASK,
        ],
    )
    status_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "status",
            "--topic-slug",
            TOPIC_SLUG,
            "--json",
        ],
    )

    check(session_start_payload["topic_slug"] == TOPIC_SLUG, "Claude session-start should create the expected topic slug")
    check(status_payload["topic_slug"] == TOPIC_SLUG, "Claude status should stay on the expected topic")
    check(
        session_start_payload["routing"]["route"] == "request_new_topic",
        "Claude SessionStart probe should open the bounded topic through natural-language routing",
    )
    check(
        session_start_payload["load_profile"] == "light",
        "Claude bounded probe should stay in the light runtime profile",
    )
    check(bool(status_payload.get("selected_action_id")), "Claude status should expose the next bounded action")
    check(
        bool((session_start_payload.get("session_start") or {}).get("human_interaction_posture")),
        "Claude session-start should surface the human-interaction posture contract",
    )
    check(
        bool((session_start_payload.get("session_start") or {}).get("autonomy_posture")),
        "Claude session-start should surface the autonomy posture contract",
    )
    check(
        bool(status_payload.get("human_interaction_posture")),
        "Claude status should surface the human-interaction posture contract",
    )
    check(
        bool(status_payload.get("autonomy_posture")),
        "Claude status should surface the autonomy posture contract",
    )

    checked_artifacts = [
        {"label": "claude_using_skill", "path": str(claude_root / "skills" / "using-aitp" / "SKILL.md"), "status": "present"},
        {"label": "claude_runtime_skill", "path": str(claude_root / "skills" / "aitp-runtime" / "SKILL.md"), "status": "present"},
        {"label": "claude_session_start_hook", "path": str(claude_root / "hooks" / "session-start"), "status": "present"},
        {"label": "claude_session_start_python_hook", "path": str(claude_root / "hooks" / "session-start.py"), "status": "present"},
        {"label": "claude_hook_wrapper", "path": str(claude_root / "hooks" / "run-hook.cmd"), "status": "present"},
        {"label": "claude_settings", "path": str(claude_root / "settings.json"), "status": "present"},
        {"label": "topic_state", "path": str(Path(session_start_payload["loop_payload"]["bootstrap"]["files"]["topic_state"])), "status": "present"},
        {"label": "session_runtime_protocol", "path": str(Path(session_start_payload["runtime_protocol_path"])), "status": "present"},
        {"label": "loop_state", "path": str(Path(session_start_payload["loop_state_path"])), "status": "present"},
        {"label": "session_start_contract", "path": str(Path(session_start_payload["session_start_contract_path"])), "status": "present"},
        {"label": "session_start_note", "path": str(Path(session_start_payload["session_start_note_path"])), "status": "present"},
        {"label": "current_topic_memory", "path": str(Path(session_start_payload["current_topic_memory_path"])), "status": "present"},
        {"label": "status_runtime_protocol", "path": str(Path(status_payload["runtime_protocol_path"])), "status": "present"},
        {"label": "status_runtime_protocol_note", "path": str(Path(status_payload["runtime_protocol_note_path"])), "status": "present"},
    ]
    for row in checked_artifacts:
        ensure_exists(Path(row["path"]))

    return {
        "report_kind": "runtime_deep_execution_parity",
        "runtime": "claude_code",
        "baseline_runtime": "codex",
        "status": "probe_completed_with_gap",
        "entry_surface": ENTRY_SURFACES["claude_code"],
        "acceptance_command": acceptance_command("claude_code"),
        "topic_slug": TOPIC_SLUG,
        "load_profile": session_start_payload["load_profile"],
        "expected_artifacts": expected_artifacts(TOPIC_SLUG),
        "checked_artifacts": checked_artifacts,
        "matches_codex_baseline": [
            "The supported Claude SessionStart bootstrap emits a real AITP receipt with injected using-aitp content.",
            "A bounded natural-language request reaches topic_state, loop_state, and runtime_protocol artifacts on an isolated kernel root.",
            "The bounded probe stays in the light runtime profile and preserves a selected_action_id through status.",
            "Current-topic memory plus session_start contract/note artifacts are materialized for the new topic.",
            "Claude session-start and status surfaces both expose the same human-control and autonomous-continuation posture contract family.",
        ],
        "falls_short_of_codex_baseline": [
            "The probe validates the SessionStart receipt and the downstream AITP runtime in two explicit steps rather than one live Claude Code chat turn.",
            "It does not yet prove that Claude Code always consumes the injected SessionStart context before its first substantive model action.",
        ],
        "blockers": ["live_claude_chat_turn_not_exercised"],
        "notes": [
            "This is the bounded Claude Code parity probe for v1.67.",
            "The probe is honest about the remaining gap: bootstrap receipt plus runtime artifacts are verified, but full live-Claude parity is not yet closed.",
        ],
        "work_root": str(work_root),
        "bootstrap_receipt": {
            "bootstrap_command_path": bootstrap_command_path,
            "hook_event_name": hook_event_name,
            "contains_using_aitp": "using-aitp" in additional_context,
            "contains_claude_session_banner": "AITP-enabled Claude Code session" in additional_context,
            "additional_context_preview": additional_context[:240],
        },
        "install": install_payload,
        "session_start": session_start_payload,
        "status_payload": status_payload,
        "posture_contracts": {
            "session_start": posture_contract_snapshot(session_start_payload.get("session_start") or {}),
            "status": posture_contract_snapshot(status_payload),
        },
    }


def opencode_probe_payload(*, package_root: Path, repo_root: Path, work_root: Path) -> dict[str, Any]:
    project_root = work_root / "opencode-workspace"
    project_root.mkdir(parents=True, exist_ok=True)
    install_payload = _install_opencode_project_assets(
        package_root=package_root,
        repo_root=repo_root,
        project_root=project_root,
    )
    opencode_root = project_root / ".opencode"
    plugin_path = opencode_root / "plugins" / "aitp.js"
    bootstrap_payload, bootstrap_command = _run_opencode_plugin_bootstrap(plugin_path=plugin_path)

    config_payload = bootstrap_payload.get("config") or {}
    skills_paths = list((((config_payload.get("skills") or {}).get("paths")) or []))
    output_payload = bootstrap_payload.get("output") or {}
    system_rows = list(output_payload.get("system") or [])
    system_prompt = str(system_rows[0] if system_rows else "")

    expected_skills_path = str((opencode_root / "skills").resolve())
    check(bool(bootstrap_payload.get("hasConfigHook")), "OpenCode plugin probe should expose the config hook")
    check(bool(bootstrap_payload.get("hasTransformHook")), "OpenCode plugin probe should expose the system transform hook")
    check(expected_skills_path in skills_paths, "OpenCode plugin config hook should register the installed skills path")
    check(system_rows, "OpenCode plugin transform should inject one system bootstrap payload")
    check("using-aitp" in system_prompt, "OpenCode plugin transform should inject the using-aitp skill content")
    check(
        "AITP-enabled OpenCode session" in system_prompt,
        "OpenCode plugin transform should identify the OpenCode bootstrap context",
    )
    check(
        "Tool Mapping for OpenCode" in system_prompt,
        "OpenCode plugin transform should expose the OpenCode tool-mapping note",
    )

    kernel_root = work_root / "kernel"
    prepare_first_run_kernel(package_root, kernel_root)

    session_start_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "session-start",
            "--statement",
            TOPIC_STATEMENT,
            "--max-auto-steps",
            "1",
            "--load-profile",
            "light",
            "--json",
            BOUNDED_SESSION_START_TASK,
        ],
    )
    status_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "status",
            "--topic-slug",
            TOPIC_SLUG,
            "--json",
        ],
    )

    check(session_start_payload["topic_slug"] == TOPIC_SLUG, "OpenCode session-start should create the expected topic slug")
    check(status_payload["topic_slug"] == TOPIC_SLUG, "OpenCode status should stay on the expected topic")
    check(
        session_start_payload["routing"]["route"] == "request_new_topic",
        "OpenCode plugin probe should open the bounded topic through natural-language routing",
    )
    check(
        session_start_payload["load_profile"] == "light",
        "OpenCode bounded probe should stay in the light runtime profile",
    )
    check(bool(status_payload.get("selected_action_id")), "OpenCode status should expose the next bounded action")
    check(
        bool((session_start_payload.get("session_start") or {}).get("human_interaction_posture")),
        "OpenCode session-start should surface the human-interaction posture contract",
    )
    check(
        bool((session_start_payload.get("session_start") or {}).get("autonomy_posture")),
        "OpenCode session-start should surface the autonomy posture contract",
    )
    check(
        bool(status_payload.get("human_interaction_posture")),
        "OpenCode status should surface the human-interaction posture contract",
    )
    check(
        bool(status_payload.get("autonomy_posture")),
        "OpenCode status should surface the autonomy posture contract",
    )

    checked_artifacts = [
        {"label": "opencode_using_skill", "path": str(opencode_root / "skills" / "using-aitp" / "SKILL.md"), "status": "present"},
        {"label": "opencode_runtime_skill", "path": str(opencode_root / "skills" / "aitp-runtime" / "SKILL.md"), "status": "present"},
        {"label": "opencode_plugin", "path": str(plugin_path), "status": "present"},
        {"label": "topic_state", "path": str(Path(session_start_payload["loop_payload"]["bootstrap"]["files"]["topic_state"])), "status": "present"},
        {"label": "session_runtime_protocol", "path": str(Path(session_start_payload["runtime_protocol_path"])), "status": "present"},
        {"label": "loop_state", "path": str(Path(session_start_payload["loop_state_path"])), "status": "present"},
        {"label": "session_start_contract", "path": str(Path(session_start_payload["session_start_contract_path"])), "status": "present"},
        {"label": "session_start_note", "path": str(Path(session_start_payload["session_start_note_path"])), "status": "present"},
        {"label": "current_topic_memory", "path": str(Path(session_start_payload["current_topic_memory_path"])), "status": "present"},
        {"label": "status_runtime_protocol", "path": str(Path(status_payload["runtime_protocol_path"])), "status": "present"},
        {"label": "status_runtime_protocol_note", "path": str(Path(status_payload["runtime_protocol_note_path"])), "status": "present"},
    ]
    for row in checked_artifacts:
        ensure_exists(Path(row["path"]))

    return {
        "report_kind": "runtime_deep_execution_parity",
        "runtime": "opencode",
        "baseline_runtime": "codex",
        "status": "probe_completed_with_gap",
        "entry_surface": ENTRY_SURFACES["opencode"],
        "acceptance_command": acceptance_command("opencode"),
        "topic_slug": TOPIC_SLUG,
        "load_profile": session_start_payload["load_profile"],
        "expected_artifacts": expected_artifacts(TOPIC_SLUG),
        "checked_artifacts": checked_artifacts,
        "matches_codex_baseline": [
            "The supported OpenCode plugin registers the installed AITP skills path through the real config hook.",
            "The supported OpenCode plugin injects using-aitp and tool-mapping context through the real system-transform hook.",
            "A bounded natural-language request reaches topic_state, loop_state, and runtime_protocol artifacts on an isolated kernel root.",
            "The bounded probe stays in the light runtime profile and preserves a selected_action_id through status.",
            "OpenCode session-start and status surfaces both expose the same human-control and autonomous-continuation posture contract family.",
        ],
        "falls_short_of_codex_baseline": [
            "The probe validates the plugin module hooks and the downstream AITP runtime in explicit steps rather than one live restarted OpenCode app session.",
            "It does not yet prove that OpenCode always applies both plugin hooks before its first substantive model action.",
        ],
        "blockers": ["live_opencode_chat_turn_not_exercised"],
        "notes": [
            "This is the bounded OpenCode parity probe for v1.67.",
            "The probe is honest about the remaining gap: plugin-hook receipts plus runtime artifacts are verified, but full live-OpenCode parity is not yet closed.",
        ],
        "work_root": str(work_root),
        "bootstrap_receipt": {
            "bootstrap_command": f"{bootstrap_command} --input-type=module -e <opencode-probe> {plugin_path}",
            "skills_paths": skills_paths,
            "system_prompt_count": len(system_rows),
            "contains_using_aitp": "using-aitp" in system_prompt,
            "contains_opencode_session_banner": "AITP-enabled OpenCode session" in system_prompt,
            "contains_tool_mapping": "Tool Mapping for OpenCode" in system_prompt,
            "system_prompt_preview": system_prompt[:240],
        },
        "install": install_payload,
        "session_start": session_start_payload,
        "status_payload": status_payload,
        "posture_contracts": {
            "session_start": posture_contract_snapshot(session_start_payload.get("session_start") or {}),
            "status": posture_contract_snapshot(status_payload),
        },
    }


def codex_baseline_payload(*, package_root: Path, repo_root: Path, work_root: Path) -> dict[str, Any]:
    kernel_root = work_root / "kernel"
    prepare_first_run_kernel(package_root, kernel_root)

    bootstrap_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "bootstrap",
            "--topic",
            TOPIC_TITLE,
            "--statement",
            TOPIC_STATEMENT,
            "--json",
        ],
    )
    loop_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "loop",
            "--topic-slug",
            TOPIC_SLUG,
            "--human-request",
            LOOP_REQUEST,
            "--max-auto-steps",
            "1",
            "--json",
        ],
    )
    status_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "status",
            "--topic-slug",
            TOPIC_SLUG,
            "--json",
        ],
    )

    check(bootstrap_payload["topic_slug"] == TOPIC_SLUG, "bootstrap should create the expected topic slug")
    check(loop_payload["topic_slug"] == TOPIC_SLUG, "loop should stay on the same topic")
    check(status_payload["topic_slug"] == TOPIC_SLUG, "status should read the same topic")
    check(loop_payload["load_profile"] == "light", "Codex baseline should stay in the light runtime profile")
    check(bool(status_payload.get("selected_action_id")), "status should expose the next bounded action")
    check(bool(status_payload.get("human_interaction_posture")), "Codex status should surface the human-interaction posture contract")
    check(bool(status_payload.get("autonomy_posture")), "Codex status should surface the autonomy posture contract")

    checked_artifacts = [
        {"label": "topic_state", "path": str(Path(bootstrap_payload["files"]["topic_state"])), "status": "present"},
        {"label": "bootstrap_runtime_protocol", "path": str(Path(bootstrap_payload["files"]["runtime_protocol"])), "status": "present"},
        {"label": "loop_state", "path": str(Path(loop_payload["loop_state_path"])), "status": "present"},
        {"label": "loop_runtime_protocol", "path": str(Path(loop_payload["runtime_protocol"]["runtime_protocol_path"])), "status": "present"},
        {"label": "status_runtime_protocol", "path": str(Path(status_payload["runtime_protocol_path"])), "status": "present"},
        {"label": "status_runtime_protocol_note", "path": str(Path(status_payload["runtime_protocol_note_path"])), "status": "present"},
    ]
    for row in checked_artifacts:
        ensure_exists(Path(row["path"]))

    return {
        "report_kind": "runtime_deep_execution_parity",
        "runtime": "codex",
        "baseline_runtime": "codex",
        "status": "baseline_ready",
        "entry_surface": ENTRY_SURFACES["codex"],
        "acceptance_command": acceptance_command("codex"),
        "topic_slug": TOPIC_SLUG,
        "load_profile": loop_payload["load_profile"],
        "expected_artifacts": expected_artifacts(TOPIC_SLUG),
        "checked_artifacts": checked_artifacts,
        "blockers": [],
        "notes": [
            "This is the current deep-execution baseline for v1.67.",
            "Future Claude Code and OpenCode probes should be compared against this artifact footprint and bounded-route behavior.",
        ],
        "work_root": str(work_root),
        "bootstrap": bootstrap_payload,
        "loop": loop_payload,
        "status_payload": status_payload,
        "posture_contracts": {
            "status": posture_contract_snapshot(status_payload),
        },
    }


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()

    if args.runtime == "codex":
        work_root = (
            Path(args.work_root).expanduser().resolve()
            if args.work_root
            else Path(tempfile.mkdtemp(prefix="aitp-runtime-parity-codex-")).resolve()
        )
        payload = codex_baseline_payload(package_root=package_root, repo_root=repo_root, work_root=work_root)
    elif args.runtime == "claude_code":
        work_root = (
            Path(args.work_root).expanduser().resolve()
            if args.work_root
            else Path(tempfile.mkdtemp(prefix="aitp-runtime-parity-claude-")).resolve()
        )
        payload = claude_probe_payload(package_root=package_root, repo_root=repo_root, work_root=work_root)
    elif args.runtime == "opencode":
        work_root = (
            Path(args.work_root).expanduser().resolve()
            if args.work_root
            else Path(tempfile.mkdtemp(prefix="aitp-runtime-parity-opencode-")).resolve()
        )
        payload = opencode_probe_payload(package_root=package_root, repo_root=repo_root, work_root=work_root)
    else:
        payload = pending_probe_payload(args.runtime)

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(
            "runtime parity acceptance\n"
            f"runtime: {payload['runtime']}\n"
            f"status: {payload['status']}\n"
            f"acceptance: {payload['acceptance_command']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
