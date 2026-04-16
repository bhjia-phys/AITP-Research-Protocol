from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .bundle_support import LEGACY_PACKAGE_DISTRIBUTION_NAMES, PACKAGE_DISTRIBUTION_NAME
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


def _looks_like_python_command(command: str) -> bool:
    name = Path(str(command or "")).name.lower()
    return name.startswith(("python", "pypy")) or name in {"py", "py.exe"}


def _resolve_python_command() -> list[str]:
    if _looks_like_python_command(sys.executable):
        return [sys.executable]

    discovered = shutil.which("python") or shutil.which("python3")
    if discovered:
        return [discovered]

    py_launcher = shutil.which("py")
    if py_launcher:
        return [py_launcher, "-3"]

    return [sys.executable] if sys.executable else ["python"]


def pip_show_package(package_name: str) -> dict[str, str]:
    completed = subprocess.run(
        [*_resolve_python_command(), "-m", "pip", "show", package_name],
        check=False,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
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


def _installed_package_payload(service: Any) -> tuple[str, dict[str, str], bool]:
    package_names = (
        tuple(service._package_distribution_names())
        if hasattr(service, "_package_distribution_names")
        else (PACKAGE_DISTRIBUTION_NAME, *LEGACY_PACKAGE_DISTRIBUTION_NAMES)
    )
    for package_name in package_names:
        payload = service._pip_show_package(package_name)
        if payload:
            return package_name, payload, package_name != PACKAGE_DISTRIBUTION_NAME
    return PACKAGE_DISTRIBUTION_NAME, {}, False


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
    session_start_python_path = base / "hooks" / "session-start.py"
    run_hook_path = base / "hooks" / "run-hook.cmd"
    hooks_manifest_path = base / "hooks" / "hooks.json"
    settings_path = base / "settings.json"
    return {
        "using_skill_path": str(using_path),
        "runtime_skill_path": str(runtime_path),
        "session_start_hook_path": str(session_start_path),
        "session_start_python_hook_path": str(session_start_python_path),
        "hook_wrapper_path": str(run_hook_path),
        "hooks_manifest_path": str(hooks_manifest_path),
        "settings_path": str(settings_path),
        "using_skill": using_path.exists(),
        "runtime_skill": runtime_path.exists(),
        "session_start_hook": session_start_path.exists(),
        "session_start_python_hook": session_start_python_path.exists(),
        "hook_wrapper": run_hook_path.exists(),
        "hooks_manifest": hooks_manifest_path.exists(),
        "settings": settings_path.exists(),
        "using_skill_matches_canonical": _text_matches_canonical(using_path, repo_root, "skills/using-aitp/SKILL.md"),
        "runtime_skill_matches_canonical": _text_matches_canonical(runtime_path, repo_root, "skills/aitp-runtime/SKILL.md"),
        "session_start_hook_matches_canonical": _text_matches_canonical(session_start_path, repo_root, "hooks/session-start"),
        "session_start_python_hook_matches_canonical": _text_matches_canonical(
            session_start_python_path,
            repo_root,
            "hooks/session-start.py",
        ),
        "hook_wrapper_matches_canonical": _text_matches_canonical(run_hook_path, repo_root, "hooks/run-hook.cmd"),
        "hooks_manifest_matches_canonical": _text_matches_canonical(hooks_manifest_path, repo_root, "hooks/hooks.json"),
        "settings_has_expected_session_start_command": claude_settings_has_expected_session_start_command(
            settings_path,
            run_hook_path,
        ),
    }


def _extract_claude_mcp_servers(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    wrapped = payload.get("mcpServers")
    if isinstance(wrapped, dict):
        return {
            str(name): value
            for name, value in wrapped.items()
            if isinstance(value, dict)
        }
    return {}


def _normalize_claude_mcp_entry(entry: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(entry, dict):
        return None
    command = entry.get("command")
    if isinstance(command, list):
        command_parts = [str(part) for part in command if str(part)]
        if not command_parts:
            return None
        resolved_command = command_parts[0]
        resolved_args = command_parts[1:]
    elif command:
        resolved_command = str(command)
        resolved_args = []
    else:
        return None

    raw_args = entry.get("args")
    if isinstance(raw_args, list):
        resolved_args = [*resolved_args, *[str(part) for part in raw_args]]

    raw_env = entry.get("env")
    if not isinstance(raw_env, dict):
        raw_env = entry.get("environment")
    resolved_env = {
        str(key): str(value)
        for key, value in (raw_env.items() if isinstance(raw_env, dict) else [])
    }
    return {
        "command": resolved_command,
        "args": resolved_args,
        "env": resolved_env,
    }


def claude_mcp_status(service: Any, *, workspace_root: Path | None = None) -> dict[str, Any]:
    user_config_path = Path.home() / ".claude.json"
    workspace_root = workspace_root.resolve() if workspace_root else service.repo_root.resolve()
    project_config_path = workspace_root / ".mcp.json"
    expected_entry = _normalize_claude_mcp_entry(service._claude_mcp_entry()) or {}

    user_config_exists = user_config_path.exists()
    user_config_parse_ok = False
    user_server_present = False
    user_server_matches = False
    if user_config_exists:
        try:
            user_payload = json.loads(user_config_path.read_text(encoding="utf-8"))
            user_config_parse_ok = isinstance(user_payload, dict)
        except json.JSONDecodeError:
            user_payload = {}
        user_entry = _extract_claude_mcp_servers(user_payload if isinstance(user_payload, dict) else {}).get("aitp")
        user_server_present = isinstance(user_entry, dict)
        user_server_matches = _normalize_claude_mcp_entry(user_entry) == expected_entry

    project_config_exists = project_config_path.exists()
    project_config_parse_ok = False
    project_server_present = False
    project_server_matches = False
    if project_config_exists:
        try:
            project_payload = json.loads(project_config_path.read_text(encoding="utf-8"))
            project_config_parse_ok = isinstance(project_payload, dict)
        except json.JSONDecodeError:
            project_payload = {}
        project_entry = _extract_claude_mcp_servers(project_payload if isinstance(project_payload, dict) else {}).get("aitp")
        project_server_present = isinstance(project_entry, dict)
        project_server_matches = _normalize_claude_mcp_entry(project_entry) == expected_entry

    effective_scope = ""
    effective_config_path = ""
    if user_server_matches:
        effective_scope = "user"
        effective_config_path = str(user_config_path)
    elif project_server_matches:
        effective_scope = "project"
        effective_config_path = str(project_config_path)

    return {
        "user_config_path": str(user_config_path),
        "project_config_path": str(project_config_path),
        "user_config_exists": user_config_exists,
        "user_config_parse_ok": user_config_parse_ok,
        "user_mcp_server_present": user_server_present,
        "user_mcp_server_matches_canonical": user_server_matches,
        "project_config_exists": project_config_exists,
        "project_config_parse_ok": project_config_parse_ok,
        "project_mcp_server_present": project_server_present,
        "project_mcp_server_matches_canonical": project_server_matches,
        "structured_tool_access_present": user_server_present or project_server_present,
        "structured_tool_access_matches_canonical": user_server_matches or project_server_matches,
        "effective_scope": effective_scope,
        "effective_config_path": effective_config_path,
        "expected_command": str(expected_entry.get("command") or ""),
        "expected_args": list(expected_entry.get("args") or []),
        "expected_env": dict(expected_entry.get("env") or {}),
    }


def codex_skill_status(*, repo_root: Path) -> dict[str, Any]:
    receipt_path = Path.home() / ".codex" / "aitp_bootstrap_receipt.json"
    receipt_exists = receipt_path.exists()
    receipt_parse_ok = False
    receipt_matches_expected = False
    if receipt_exists:
        try:
            receipt_payload = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt_parse_ok = isinstance(receipt_payload, dict)
        except json.JSONDecodeError:
            receipt_payload = {}
        if isinstance(receipt_payload, dict):
            receipt_matches_expected = (
                str(receipt_payload.get("receipt_kind") or "").strip() == "codex_bootstrap_receipt"
                and str(receipt_payload.get("entrypoint") or "").strip() == "aitp-codex"
                and str(receipt_payload.get("bootstrap_mode") or "").strip() == "aitp_codex_entrypoint"
            )
    using_path = Path.home() / ".agents" / "skills" / "using-aitp" / "SKILL.md"
    runtime_path = Path.home() / ".agents" / "skills" / "aitp-runtime" / "SKILL.md"
    return {
        "using_skill_path": str(using_path),
        "runtime_skill_path": str(runtime_path),
        "bootstrap_receipt_path": str(receipt_path),
        "using_skill_present": using_path.exists(),
        "runtime_skill_present": runtime_path.exists(),
        "using_skill_matches_canonical": _text_matches_canonical(using_path, repo_root, "skills/using-aitp/SKILL.md"),
        "runtime_skill_matches_canonical": _text_matches_canonical(runtime_path, repo_root, "skills/aitp-runtime/SKILL.md"),
        "bootstrap_receipt_present": receipt_exists,
        "bootstrap_receipt_parse_ok": receipt_parse_ok,
        "bootstrap_receipt_matches_expected": receipt_matches_expected,
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
    front_door_ready_runtimes = [runtime for runtime in front_door_runtimes if status_by_runtime.get(runtime) == "ready"]
    front_door_non_ready_runtimes = [runtime for runtime in front_door_runtimes if status_by_runtime.get(runtime) != "ready"]
    return {
        "baseline_runtime": str(matrix.get("baseline_runtime") or ""),
        "front_door_runtimes": front_door_runtimes,
        "front_door_runtimes_converged": all(status_by_runtime.get(runtime) == "ready" for runtime in front_door_runtimes),
        "status_by_runtime": status_by_runtime,
        "ready_runtimes": ready_runtimes,
        "non_ready_runtimes": non_ready_runtimes,
        "front_door_ready_runtimes": front_door_ready_runtimes,
        "front_door_non_ready_runtimes": front_door_non_ready_runtimes,
        "specialized_lanes": list(matrix.get("specialized_lanes") or []),
    }


def strict_l0_l1_summary(doctor_payload: dict[str, Any]) -> dict[str, Any]:
    matrix = doctor_payload.get("runtime_support_matrix") or {}
    codex_row = (matrix.get("runtimes") or {}).get("codex") or {}
    surface_checks = codex_row.get("surface_checks") or {}
    service_gate_surfaces = [
        "work_topic",
        "prepare_verification",
        "assess_topic_completion",
        "prepare_statement_compilation",
        "prepare_lean_bridge",
        "select_lean_bridge_export_target",
        "run_lean_bridge_export_check",
        "update_followup_return_packet",
        "reintegrate_followup_subtopic",
    ]
    blockers: list[str] = []
    if str(codex_row.get("status") or "") != "ready":
        blockers.append("codex_frontdoor_not_ready")
    if not bool(surface_checks.get("bootstrap_receipt_present")):
        blockers.append("codex_bootstrap_receipt_missing")
    elif not bool(surface_checks.get("bootstrap_receipt_parse_ok")):
        blockers.append("codex_bootstrap_receipt_invalid")
    elif not bool(surface_checks.get("bootstrap_receipt_matches_expected")):
        blockers.append("codex_bootstrap_receipt_stale")
    return {
        "status": "pass" if not blockers else "fail",
        "baseline_runtime": str(matrix.get("baseline_runtime") or ""),
        "codex_status": str(codex_row.get("status") or "unknown"),
        "front_door_converged": bool((doctor_payload.get("runtime_convergence") or {}).get("front_door_runtimes_converged")),
        "service_gate_surfaces": service_gate_surfaces,
        "service_gate_surface_count": len(service_gate_surfaces),
        "blockers": blockers,
        "summary": (
            "Current Codex front-door constraints are hard enough for L0-L1 topic work."
            if not blockers
            else "Codex can still bypass part of the intended L0-L1 AITP entry contract."
        ),
    }


def deep_execution_parity_summary(doctor_payload: dict[str, Any]) -> dict[str, Any]:
    matrix = doctor_payload.get("runtime_support_matrix") or {}
    deep_execution = matrix.get("deep_execution_parity") or {}
    runtime_rows = deep_execution.get("runtimes") or {}
    status_by_runtime = {
        runtime: str((row or {}).get("status") or "unknown")
        for runtime, row in runtime_rows.items()
    }
    baseline_runtime = str(deep_execution.get("baseline_runtime") or "")
    parity_targets = list(deep_execution.get("parity_targets") or [])
    verified_targets = [runtime for runtime in parity_targets if status_by_runtime.get(runtime) == "parity_verified"]
    pending_targets = [runtime for runtime in parity_targets if status_by_runtime.get(runtime) != "parity_verified"]
    blocked_targets = [runtime for runtime in parity_targets if status_by_runtime.get(runtime) == "front_door_blocked"]
    ready_for_probe_targets = [
        runtime
        for runtime in parity_targets
        if status_by_runtime.get(runtime) in {"probe_pending", "probe_available", "parity_verified"}
    ]
    return {
        "baseline_runtime": baseline_runtime,
        "baseline_status": status_by_runtime.get(baseline_runtime, "unknown"),
        "parity_targets": parity_targets,
        "parity_targets_converged": bool(parity_targets) and not pending_targets,
        "status_by_runtime": status_by_runtime,
        "verified_targets": verified_targets,
        "pending_targets": pending_targets,
        "blocked_targets": blocked_targets,
        "ready_for_probe_targets": ready_for_probe_targets,
        "deferred_lanes": list(deep_execution.get("deferred_lanes") or []),
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
        else service._workspace_root_from_target_root(None)
    )
    package_name, pip_payload, is_legacy_distribution = _installed_package_payload(service)
    editable_location = str(pip_payload.get("editable project location") or "").strip()
    version = str(pip_payload.get("version") or "").strip()
    canonical_package_root = str(service._canonical_package_root().resolve())
    package_repair_command = (
        "python -m pip install -e research/knowledge-hub"
        if service._has_repo_checkout()
        else f"python -m pip install {PACKAGE_DISTRIBUTION_NAME}"
    )
    stale_cli = bool(editable_location) and Path(editable_location).resolve() != service._canonical_package_root().resolve()
    if not version and not editable_location:
        package_status = "not_installed"
    elif stale_cli:
        package_status = "stale_editable_install"
    elif editable_location and is_legacy_distribution:
        package_status = "legacy_editable_install"
    elif editable_location:
        package_status = "canonical_editable_install"
    elif is_legacy_distribution:
        package_status = "legacy_installed"
    else:
        package_status = "installed"
    codex_skill_status_payload = service._codex_skill_status()
    claude_hook_status_payload = service._claude_hook_status()
    claude_mcp_status_payload = service._claude_mcp_status(workspace_path)
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
    if package_status == "not_installed":
        issues.append("package_not_installed")
    elif package_status in {"legacy_installed", "legacy_editable_install"}:
        issues.append("legacy_package_install")
    if stale_cli:
        issues.append("stale_cli")
    if legacy_entrypoints:
        issues.append("legacy_workspace_entrypoints_present")
    runtime_support_matrix = build_runtime_support_matrix(
        codex_path=codex_path,
        openclaw_path=openclaw_path,
        mcporter_path=mcporter_path,
        workspace_root=str(workspace_path),
        codex_skill_status=codex_skill_status_payload,
        claude_hook_status=claude_hook_status_payload,
        claude_mcp_status=claude_mcp_status_payload,
        legacy_claude_commands=legacy_claude_commands,
        opencode_status=opencode_status,
    )
    codex_runtime_status = str(runtime_support_matrix["runtimes"]["codex"]["status"])
    if codex_runtime_status in {"missing", "partial"}:
        issues.append("codex_skill_surface_incomplete")
    elif codex_runtime_status == "stale":
        issues.append("codex_skill_surface_stale")

    claude_runtime_status = str(runtime_support_matrix["runtimes"]["claude_code"]["status"])
    if claude_runtime_status in {"missing", "partial"}:
        issues.append("claude_frontdoor_surface_incomplete")
    elif claude_runtime_status == "stale":
        issues.append("claude_frontdoor_surface_stale")

    opencode_runtime_status = str(runtime_support_matrix["runtimes"]["opencode"]["status"])
    if opencode_runtime_status == "missing":
        issues.append("opencode_plugin_surface_missing")
    elif opencode_runtime_status == "partial":
        issues.append("opencode_plugin_surface_incomplete")
    elif opencode_runtime_status == "stale":
        issues.append("opencode_plugin_surface_stale")
    runtime_convergence = runtime_convergence_summary({"runtime_support_matrix": runtime_support_matrix})
    deep_execution_parity = deep_execution_parity_summary({"runtime_support_matrix": runtime_support_matrix})
    overall_status = "clean" if not issues else "mixed_install"
    payload = {
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
            "name": package_name,
            "version": version,
            "status": package_status,
            "editable_project_location": editable_location,
            "canonical_package_root": canonical_package_root,
            "matches_canonical": package_name == PACKAGE_DISTRIBUTION_NAME and not stale_cli and bool(editable_location),
            "legacy_distribution_names": list(LEGACY_PACKAGE_DISTRIBUTION_NAMES),
            "repair_command": package_repair_command,
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
        "claude_mcp_surface": {
            **claude_mcp_status_payload,
        },
        "opencode_plugin_surface": {
            **opencode_status,
        },
        "legacy_workspace_entrypoints": [str(path) for path in legacy_entrypoints],
        "runtime_support_matrix": runtime_support_matrix,
        "runtime_convergence": runtime_convergence,
        "deep_execution_parity": deep_execution_parity,
        "full_convergence_repair": {
            "status": "none_required" if overall_status == "clean" else "recommended",
            "command": (
                package_repair_command
                if package_status == "not_installed"
                else f'aitp migrate-local-install --workspace-root "{workspace_path}" --json'
            ),
            "followup_command": "aitp doctor --json",
            "doc_path": "docs/INSTALL.md" if package_status == "not_installed" else "docs/MIGRATE_LOCAL_INSTALL.md",
        },
        "layer_roots": layer_status,
        "protocol_contracts": {
            name: {"path": str(path), "status": "present" if path.exists() else "missing"}
            for name, path in contract_paths.items()
        },
        "control_plane_contracts": control_plane_contracts(service),
        "control_plane_surfaces": control_plane_surfaces(),
    }
    payload["strict_l0_l1"] = strict_l0_l1_summary(payload)
    return payload


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

    package_name, pip_before, _ = _installed_package_payload(service)
    editable_location = str(pip_before.get("editable project location") or "").strip()
    canonical_package_root = service._canonical_package_root().resolve()
    pip_actions: list[dict[str, Any]] = []
    if (
        package_name != PACKAGE_DISTRIBUTION_NAME
        or not editable_location
        or Path(editable_location).resolve() != canonical_package_root
    ):
        for uninstall_name in (PACKAGE_DISTRIBUTION_NAME, *LEGACY_PACKAGE_DISTRIBUTION_NAMES):
            uninstall_cmd = [sys.executable, "-m", "pip", "uninstall", "-y", uninstall_name]
            uninstall_run = subprocess.run(
                uninstall_cmd,
                check=False,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
            )
            pip_actions.append(
                {
                    "step": f"uninstall_{uninstall_name.replace('-', '_')}",
                    "command": uninstall_cmd,
                    "returncode": uninstall_run.returncode,
                    "stdout": uninstall_run.stdout.strip(),
                    "stderr": uninstall_run.stderr.strip(),
                }
            )
        install_cmd = [sys.executable, "-m", "pip", "install", "-e", str(canonical_package_root)]
        install_run = subprocess.run(
            install_cmd,
            check=False,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
        )
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
                "step": "install_canonical_aitp",
                "command": install_cmd,
                "returncode": install_run.returncode,
                "stdout": install_run.stdout.strip(),
                "stderr": install_run.stderr.strip(),
            }
        )

    refreshed_agents = agents or ["codex", "claude-code", "opencode"]
    installed_assets: list[dict[str, str]] = []
    for agent in refreshed_agents:
        install_mcp = with_mcp or agent == "claude-code"
        installed_assets.extend(
            service.install_agent(
                agent=agent,
                scope="user",
                force=True,
                install_mcp=install_mcp,
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
