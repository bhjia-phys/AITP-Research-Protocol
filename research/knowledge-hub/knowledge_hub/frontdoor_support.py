from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .runtime_support_matrix import build_runtime_support_matrix
from .subprocess_error_support import format_subprocess_failure


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _text_matches_canonical(path: Path, repo_root: Path, canonical_relative_path: str) -> bool:
    canonical_path = repo_root / canonical_relative_path
    if not path.exists() or not canonical_path.exists():
        return False
    return path.read_text(encoding="utf-8") == canonical_path.read_text(encoding="utf-8")


def pip_show_package(package_name: str) -> dict[str, str]:
    completed = subprocess.run(
        [sys.executable, "-m", "pip", "show", package_name],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return {}
    payload: dict[str, str] = {}
    for raw_line in completed.stdout.splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        payload[key.strip().lower()] = value.strip()
    return payload


def workspace_legacy_entrypoints(workspace_root: Path) -> list[Path]:
    return [
        path
        for path in (
            workspace_root / "AITP_COMMAND_HARNESS.md",
            workspace_root / "AITP_MCP_CONFIG.json",
            workspace_root / "aitp.md",
            workspace_root / "aitp-loop.md",
            workspace_root / "aitp-resume.md",
            workspace_root / "aitp-audit.md",
        )
        if path.exists()
    ]


def claude_legacy_command_paths() -> list[Path]:
    command_root = Path.home() / ".claude" / "commands"
    if not command_root.exists():
        return []
    return sorted(command_root.glob("aitp*.md"))


def ensure_opencode_plugin_enabled() -> dict[str, Any]:
    config_path = Path.home() / ".config" / "opencode" / "opencode.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.exists():
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        payload = {"$schema": "https://opencode.ai/config.json"}
    plugin_rows = payload.setdefault("plugin", [])
    if not isinstance(plugin_rows, list):
        plugin_rows = []
        payload["plugin"] = plugin_rows
    canonical_plugin = "aitp@git+https://github.com/bhjia-phys/AITP-Research-Protocol.git"
    if canonical_plugin not in plugin_rows:
        plugin_rows.append(canonical_plugin)
    _write_json(config_path, payload)
    return {"config_path": str(config_path), "plugin_entry": canonical_plugin}


def opencode_plugin_enabled() -> tuple[bool, Path, list[str]]:
    config_path = Path.home() / ".config" / "opencode" / "opencode.json"
    if not config_path.exists():
        return False, config_path, []
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, config_path, []
    plugin_rows = payload.get("plugin")
    if not isinstance(plugin_rows, list):
        return False, config_path, []
    normalized_rows = [str(item) for item in plugin_rows]
    enabled = any("aitp@" in item for item in normalized_rows)
    return enabled, config_path, normalized_rows


def opencode_plugin_status(*, repo_root: Path, workspace_root: Path | None = None) -> dict[str, Any]:
    config_path = Path.home() / ".config" / "opencode" / "opencode.json"
    canonical_plugin = "aitp@git+https://github.com/bhjia-phys/AITP-Research-Protocol.git"
    config_exists = config_path.exists()
    config_parse_ok = False
    plugin_list_present = False
    plugin_list_valid = False
    normalized_rows: list[str] = []
    aitp_plugin_entries: list[str] = []
    noncanonical_aitp_plugin_entries: list[str] = []

    if config_exists:
        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
            config_parse_ok = True
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict) and "plugin" in payload:
            plugin_list_present = True
            plugin_rows = payload.get("plugin")
            if isinstance(plugin_rows, list):
                plugin_list_valid = True
                normalized_rows = [str(item) for item in plugin_rows]
                aitp_plugin_entries = [
                    item for item in normalized_rows if "aitp@" in item or "AITP-Research-Protocol" in item
                ]
                noncanonical_aitp_plugin_entries = [
                    item for item in aitp_plugin_entries if item != canonical_plugin
                ]

    workspace_root = workspace_root.resolve() if workspace_root else None
    workspace_hidden_root = (workspace_root / ".opencode") if workspace_root else None
    workspace_plugin_path = workspace_hidden_root / "plugins" / "aitp.js" if workspace_hidden_root else None
    workspace_using_skill_path = (
        workspace_hidden_root / "skills" / "using-aitp" / "SKILL.md" if workspace_hidden_root else None
    )
    workspace_runtime_skill_path = (
        workspace_hidden_root / "skills" / "aitp-runtime" / "SKILL.md" if workspace_hidden_root else None
    )
    workspace_plugin_present = bool(workspace_plugin_path and workspace_plugin_path.exists())
    workspace_using_skill_present = bool(workspace_using_skill_path and workspace_using_skill_path.exists())
    workspace_runtime_skill_present = bool(workspace_runtime_skill_path and workspace_runtime_skill_path.exists())

    return {
        "config_path": str(config_path),
        "config_exists": config_exists,
        "config_parse_ok": config_parse_ok,
        "plugin_list_present": plugin_list_present,
        "plugin_list_valid": plugin_list_valid,
        "plugins": normalized_rows,
        "canonical_plugin_entry": canonical_plugin,
        "canonical_plugin_entry_present": canonical_plugin in normalized_rows,
        "aitp_plugin_entries": aitp_plugin_entries,
        "noncanonical_aitp_plugin_entries": noncanonical_aitp_plugin_entries,
        "workspace_plugin_path": str(workspace_plugin_path) if workspace_plugin_path else "",
        "workspace_using_skill_path": str(workspace_using_skill_path) if workspace_using_skill_path else "",
        "workspace_runtime_skill_path": str(workspace_runtime_skill_path) if workspace_runtime_skill_path else "",
        "workspace_plugin_present": workspace_plugin_present,
        "workspace_using_skill_present": workspace_using_skill_present,
        "workspace_runtime_skill_present": workspace_runtime_skill_present,
        "workspace_plugin_matches_canonical": bool(
            workspace_plugin_path and _text_matches_canonical(workspace_plugin_path, repo_root, ".opencode/plugins/aitp.js")
        ),
        "workspace_using_skill_matches_canonical": bool(
            workspace_using_skill_path and _text_matches_canonical(workspace_using_skill_path, repo_root, "skills/using-aitp/SKILL.md")
        ),
        "workspace_runtime_skill_matches_canonical": bool(
            workspace_runtime_skill_path and _text_matches_canonical(workspace_runtime_skill_path, repo_root, "skills/aitp-runtime/SKILL.md")
        ),
    }


def claude_settings_has_expected_session_start_command(settings_path: Path, run_hook_path: Path) -> bool:
    if not settings_path.exists():
        return False
    try:
        payload = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    hooks_payload = payload.get("hooks")
    if not isinstance(hooks_payload, dict):
        return False
    session_blocks = hooks_payload.get("SessionStart")
    if not isinstance(session_blocks, list):
        return False
    command_entry = f'"{run_hook_path}" session-start'
    for block in session_blocks:
        if not isinstance(block, dict):
            continue
        if str(block.get("matcher") or "") != "startup|clear|compact":
            continue
        block_hooks = block.get("hooks")
        if not isinstance(block_hooks, list):
            continue
        for entry in block_hooks:
            if not isinstance(entry, dict):
                continue
            if (
                str(entry.get("type") or "") == "command"
                and str(entry.get("command") or "") == command_entry
                and bool(entry.get("async")) is False
            ):
                return True
    return False


def claude_hook_status(*, repo_root: Path) -> dict[str, Any]:
    base = Path.home() / ".claude"
    using_path = base / "skills" / "using-aitp" / "SKILL.md"
    runtime_path = base / "skills" / "aitp-runtime" / "SKILL.md"
    session_start_path = base / "hooks" / "session-start"
    run_hook_path = base / "hooks" / "run-hook.cmd"
    hooks_manifest_path = base / "hooks" / "hooks.json"
    settings_path = base / "settings.json"
    return {
        "using_skill_path": str(using_path),
        "runtime_skill_path": str(runtime_path),
        "session_start_hook_path": str(session_start_path),
        "hook_wrapper_path": str(run_hook_path),
        "hooks_manifest_path": str(hooks_manifest_path),
        "settings_path": str(settings_path),
        "using_skill": using_path.exists(),
        "runtime_skill": runtime_path.exists(),
        "session_start_hook": session_start_path.exists(),
        "hook_wrapper": run_hook_path.exists(),
        "hooks_manifest": hooks_manifest_path.exists(),
        "settings": settings_path.exists(),
        "using_skill_matches_canonical": _text_matches_canonical(using_path, repo_root, "skills/using-aitp/SKILL.md"),
        "runtime_skill_matches_canonical": _text_matches_canonical(runtime_path, repo_root, "skills/aitp-runtime/SKILL.md"),
        "session_start_hook_matches_canonical": _text_matches_canonical(session_start_path, repo_root, "hooks/session-start"),
        "hook_wrapper_matches_canonical": _text_matches_canonical(run_hook_path, repo_root, "hooks/run-hook.cmd"),
        "hooks_manifest_matches_canonical": _text_matches_canonical(hooks_manifest_path, repo_root, "hooks/hooks.json"),
        "settings_has_expected_session_start_command": claude_settings_has_expected_session_start_command(
            settings_path,
            run_hook_path,
        ),
    }


def codex_skill_status(*, repo_root: Path) -> dict[str, Any]:
    using_path = Path.home() / ".agents" / "skills" / "using-aitp" / "SKILL.md"
    runtime_path = Path.home() / ".agents" / "skills" / "aitp-runtime" / "SKILL.md"
    return {
        "using_skill_path": str(using_path),
        "runtime_skill_path": str(runtime_path),
        "using_skill_present": using_path.exists(),
        "runtime_skill_present": runtime_path.exists(),
        "using_skill_matches_canonical": _text_matches_canonical(using_path, repo_root, "skills/using-aitp/SKILL.md"),
        "runtime_skill_matches_canonical": _text_matches_canonical(runtime_path, repo_root, "skills/aitp-runtime/SKILL.md"),
    }


def runtime_convergence_summary(doctor_payload: dict[str, Any]) -> dict[str, Any]:
    matrix = doctor_payload.get("runtime_support_matrix") or {}
    runtime_rows = matrix.get("runtimes") or {}
    status_by_runtime = {
        runtime: str((row or {}).get("status") or "unknown")
        for runtime, row in runtime_rows.items()
    }
    front_door_runtimes = ["codex", *list(matrix.get("parity_targets") or [])]
    ready_runtimes = [runtime for runtime, status in status_by_runtime.items() if status == "ready"]
    non_ready_runtimes = [runtime for runtime, status in status_by_runtime.items() if status != "ready"]
    return {
        "baseline_runtime": str(matrix.get("baseline_runtime") or ""),
        "front_door_runtimes": front_door_runtimes,
        "front_door_runtimes_converged": all(status_by_runtime.get(runtime) == "ready" for runtime in front_door_runtimes),
        "status_by_runtime": status_by_runtime,
        "ready_runtimes": ready_runtimes,
        "non_ready_runtimes": non_ready_runtimes,
        "specialized_lanes": list(matrix.get("specialized_lanes") or []),
    }


def control_plane_contracts(service: Any) -> dict[str, dict[str, str]]:
    paths = {
        "unified_architecture": service.repo_root / "docs" / "AITP_UNIFIED_RESEARCH_ARCHITECTURE.md",
        "architecture_vision": service.repo_root / "docs" / "V142_ARCHITECTURE_VISION.md",
        "paired_backend_contract": service.kernel_root
        / "canonical"
        / "backends"
        / "THEORETICAL_PHYSICS_PAIRED_BACKEND_CONTRACT.md",
        "paired_backend_maintenance_protocol": service.kernel_root
        / "canonical"
        / "L2_PAIRED_BACKEND_MAINTENANCE_PROTOCOL.md",
    }
    return {
        name: {"path": str(path), "status": "present" if path.exists() else "missing"}
        for name, path in paths.items()
    }


def control_plane_surfaces() -> dict[str, dict[str, str]]:
    return {
        "doctor_json": {
            "command": "aitp doctor --json",
            "status": "present",
            "detail": "Inspect install readiness, governance docs, and runtime parity.",
        },
        "status": {
            "command": "aitp status --topic-slug <topic_slug>",
            "status": "present",
            "detail": "Inspect the topic shell, runtime contract, and control-plane truth.",
        },
        "layer_graph": {
            "command": "aitp layer-graph --topic-slug <topic_slug>",
            "status": "present",
            "detail": "Inspect the iterative layer graph, L3 subplanes, and L4 return law.",
        },
        "next": {
            "command": "aitp next --topic-slug <topic_slug>",
            "status": "present",
            "detail": "Inspect the next bounded action and required reads.",
        },
        "capability_audit": {
            "command": "aitp capability-audit --topic-slug <topic_slug>",
            "status": "present",
            "detail": "Inspect integrated runtime, control-plane, and capability state.",
        },
        "paired_backend_audit": {
            "command": "aitp paired-backend-audit --topic-slug <topic_slug>",
            "status": "present",
            "detail": "Inspect paired-backend alignment, drift semantics, and backend debt.",
        },
        "h_plane_audit": {
            "command": "aitp h-plane-audit --topic-slug <topic_slug>",
            "status": "present",
            "detail": "Inspect steering, checkpoints, registry focus, and approval state.",
        },
    }


def ensure_cli_installed(service: Any, *, workspace_root: str | None = None) -> dict[str, Any]:
    command_path = shutil.which("aitp")
    mcp_path = shutil.which("aitp-mcp")
    codex_path = shutil.which("codex")
    openclaw_path = shutil.which("openclaw")
    mcporter_path = shutil.which("mcporter")
    workspace_path = (
        Path(workspace_root).expanduser().resolve()
        if workspace_root
        else (service.repo_root.parents[1] / "Theoretical-Physics" if (service.repo_root.parents[1] / "Theoretical-Physics").exists() else Path.cwd().resolve())
    )
    pip_payload = service._pip_show_package("aitp-kernel")
    editable_location = str(pip_payload.get("editable project location") or "").strip()
    version = str(pip_payload.get("version") or "").strip()
    canonical_package_root = str(service._canonical_package_root().resolve())
    stale_cli = bool(editable_location) and Path(editable_location).resolve() != service._canonical_package_root().resolve()
    codex_skill_status_payload = service._codex_skill_status()
    claude_hook_status_payload = service._claude_hook_status()
    opencode_status = service._opencode_plugin_status(workspace_path)
    legacy_entrypoints = service._workspace_legacy_entrypoints(workspace_path)
    legacy_claude_commands = service._claude_legacy_command_paths()
    layer_roots = {
        "L0": str(service.kernel_root / "source-layer"),
        "L1": str(service.kernel_root / "intake"),
        "L2": str(service.kernel_root / "canonical"),
        "L3": str(service.kernel_root / "feedback"),
        "L4": str(service.kernel_root / "validation"),
        "consultation": str(service.kernel_root / "consultation"),
        "runtime": str(service.kernel_root / "runtime"),
        "schemas": str(service.kernel_root / "schemas"),
    }
    layer_status = {
        name: {"path": path, "status": "present" if Path(path).exists() else "missing"}
        for name, path in layer_roots.items()
    }
    contract_paths = {
        "layer_map": service.kernel_root / "LAYER_MAP.md",
        "routing_policy": service.kernel_root / "ROUTING_POLICY.md",
        "communication_contract": service.kernel_root / "COMMUNICATION_CONTRACT.md",
        "autonomy_operator_model": service.kernel_root / "AUTONOMY_AND_OPERATOR_MODEL.md",
        "l2_consultation_protocol": service.kernel_root / "L2_CONSULTATION_PROTOCOL.md",
        "research_execution_guardrails": service.kernel_root / "RESEARCH_EXECUTION_GUARDRAILS.md",
        "proof_obligation_protocol": service.kernel_root / "PROOF_OBLIGATION_PROTOCOL.md",
        "gap_recovery_protocol": service.kernel_root / "GAP_RECOVERY_PROTOCOL.md",
        "family_fusion_protocol": service.kernel_root / "FAMILY_FUSION_PROTOCOL.md",
        "verification_bridge_protocol": service.kernel_root / "VERIFICATION_BRIDGE_PROTOCOL.md",
        "formal_theory_automation_workflow": service.kernel_root / "FORMAL_THEORY_AUTOMATION_WORKFLOW.md",
        "section_formalization_protocol": service.kernel_root / "SECTION_FORMALIZATION_PROTOCOL.md",
        "formal_theory_upstream_reference_protocol": service.kernel_root / "FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md",
        "indexing_rules": service.kernel_root / "INDEXING_RULES.md",
        "l0_source_layer": service.kernel_root / "L0_SOURCE_LAYER.md",
    }
    issues: list[str] = []
    if stale_cli:
        issues.append("stale_cli")
    if legacy_entrypoints:
        issues.append("legacy_workspace_entrypoints_present")
    if not codex_skill_status_payload["using_skill_present"] or not codex_skill_status_payload["runtime_skill_present"]:
        issues.append("codex_skill_surface_missing")
    elif not codex_skill_status_payload["using_skill_matches_canonical"] or not codex_skill_status_payload["runtime_skill_matches_canonical"]:
        issues.append("codex_skill_surface_stale")
    if not all(claude_hook_status_payload.values()):
        issues.append("claude_hook_surface_incomplete")
    if legacy_claude_commands:
        issues.append("claude_legacy_commands_present")
    runtime_support_matrix = build_runtime_support_matrix(
        codex_path=codex_path,
        openclaw_path=openclaw_path,
        mcporter_path=mcporter_path,
        codex_skill_status=codex_skill_status_payload,
        claude_hook_status=claude_hook_status_payload,
        legacy_claude_commands=legacy_claude_commands,
        opencode_status=opencode_status,
    )
    opencode_runtime_status = str(runtime_support_matrix["runtimes"]["opencode"]["status"])
    if opencode_runtime_status == "missing":
        issues.append("opencode_plugin_surface_missing")
    elif opencode_runtime_status == "partial":
        issues.append("opencode_plugin_surface_incomplete")
    elif opencode_runtime_status == "stale":
        issues.append("opencode_plugin_surface_stale")
    overall_status = "clean" if not issues else "mixed_install"
    return {
        "overall_status": overall_status,
        "issues": issues,
        "aitp": command_path,
        "aitp_mcp": mcp_path,
        "codex": codex_path,
        "openclaw": openclaw_path,
        "mcporter": mcporter_path,
        "kernel_root": str(service.kernel_root),
        "repo_root": str(service.repo_root),
        "workspace_root": str(workspace_path),
        "package": {
            "name": "aitp-kernel",
            "version": version,
            "editable_project_location": editable_location,
            "canonical_package_root": canonical_package_root,
            "matches_canonical": not stale_cli and bool(editable_location),
        },
        "command_paths": {
            "aitp": command_path or "",
            "aitp_mcp": mcp_path or "",
        },
        "codex_skill_surface": codex_skill_status_payload,
        "claude_hook_surface": {
            **claude_hook_status_payload,
            "legacy_command_paths": [str(path) for path in legacy_claude_commands],
        },
        "opencode_plugin_surface": {
            **opencode_status,
        },
        "legacy_workspace_entrypoints": [str(path) for path in legacy_entrypoints],
        "runtime_support_matrix": runtime_support_matrix,
        "layer_roots": layer_status,
        "protocol_contracts": {
            name: {"path": str(path), "status": "present" if path.exists() else "missing"}
            for name, path in contract_paths.items()
        },
        "control_plane_contracts": control_plane_contracts(service),
        "control_plane_surfaces": control_plane_surfaces(),
    }


def migrate_local_install(
    service: Any,
    *,
    workspace_root: str,
    backup_root: str | None = None,
    agents: list[str] | None = None,
    with_mcp: bool = False,
) -> dict[str, Any]:
    workspace_path = Path(workspace_root).expanduser().resolve()
    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    resolved_backup_root = (
        Path(backup_root).expanduser().resolve()
        if backup_root
        else (workspace_path / "archive" / "aitp-local-migration" / timestamp).resolve()
    )
    resolved_backup_root.mkdir(parents=True, exist_ok=True)

    before = service.ensure_cli_installed(workspace_root=str(workspace_path))
    backup_log: list[dict[str, str]] = []
    for path in service._workspace_legacy_entrypoints(workspace_path):
        backup_log.append(service._backup_and_move(path, resolved_backup_root, "workspace-root-legacy"))
    for path in service._claude_legacy_command_paths():
        backup_log.append(service._backup_and_move(path, resolved_backup_root, "claude-legacy-commands"))

    pip_before = service._pip_show_package("aitp-kernel")
    editable_location = str(pip_before.get("editable project location") or "").strip()
    canonical_package_root = service._canonical_package_root().resolve()
    pip_actions: list[dict[str, Any]] = []
    if not editable_location or Path(editable_location).resolve() != canonical_package_root:
        uninstall_cmd = [sys.executable, "-m", "pip", "uninstall", "-y", "aitp-kernel"]
        uninstall_run = subprocess.run(uninstall_cmd, check=False, capture_output=True, text=True)
        pip_actions.append(
            {
                "step": "uninstall_old_aitp_kernel",
                "command": uninstall_cmd,
                "returncode": uninstall_run.returncode,
                "stdout": uninstall_run.stdout.strip(),
                "stderr": uninstall_run.stderr.strip(),
            }
        )
        install_cmd = [sys.executable, "-m", "pip", "install", "-e", str(canonical_package_root)]
        install_run = subprocess.run(install_cmd, check=False, capture_output=True, text=True)
        if install_run.returncode != 0:
            raise RuntimeError(
                format_subprocess_failure(
                    install_cmd,
                    returncode=install_run.returncode,
                    stdout=install_run.stdout,
                    stderr=install_run.stderr,
                    context="migrate-local-install pip install",
                )
            )
        pip_actions.append(
            {
                "step": "install_canonical_aitp_kernel",
                "command": install_cmd,
                "returncode": install_run.returncode,
                "stdout": install_run.stdout.strip(),
                "stderr": install_run.stderr.strip(),
            }
        )

    refreshed_agents = agents or ["codex", "claude-code", "opencode"]
    installed_assets: list[dict[str, str]] = []
    for agent in refreshed_agents:
        installed_assets.extend(
            service.install_agent(
                agent=agent,
                scope="user",
                force=True,
                install_mcp=with_mcp,
            )["installed"]
        )
    opencode_plugin_update = service._ensure_opencode_plugin_enabled()
    after = service.ensure_cli_installed(workspace_root=str(workspace_path))
    return {
        "status": "success",
        "workspace_root": str(workspace_path),
        "backup_root": str(resolved_backup_root),
        "backup_log": backup_log,
        "pip_before": pip_before,
        "pip_actions": pip_actions,
        "installed_assets": installed_assets,
        "opencode_plugin_update": opencode_plugin_update,
        "doctor_before": before,
        "runtime_convergence_before": service._runtime_convergence_summary(before),
        "doctor_after": after,
        "runtime_convergence_after": service._runtime_convergence_summary(after),
    }
