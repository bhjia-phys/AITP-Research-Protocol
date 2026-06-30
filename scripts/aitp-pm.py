#!/usr/bin/env python3
"""AITP Package Manager — install, update, upgrade, uninstall, and diagnose AITP agent deployments.

Usage:
    aitp install                          # 一键安装（自动检测 topics-root）
    aitp install --agent claude-code      # 仅安装 Claude Code
    aitp install --scope project          # 安装到项目级
    aitp uninstall                        # 一键卸载
    aitp update                           # 重新同步所有已安装 agent（不拉代码）
    aitp upgrade                          # git pull + 自动重新部署
    aitp upgrade --force                  # 自动 stash 本地改动后升级
    aitp status                           # 查看安装状态
    aitp doctor                           # 健康检查

All flags are optional — running bare `aitp install` / `aitp uninstall` just works.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from copy import deepcopy
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
TEMPLATES_DIR = REPO_ROOT / "deploy" / "templates"
INSTALL_DIR = Path.home() / ".aitp"
RECORD_PATH = INSTALL_DIR / "install-record.json"
EXPECTED_PACKAGE_VERSION = "1.0.0"
EXPECTED_IMPLEMENTATION = "v5"
MCP_ENTRYPOINT = "brain/v5/native_mcp.py"
LEGACY_MCP_ENTRYPOINTS = ("brain/native_mcp.py", "brain/mcp_server.py")

AGENTS = ("claude-code", "kimi-code", "codex")
AGENT_CHOICES = (*AGENTS, "all")
SCOPE_CHOICES = ("user", "project")

from brain.v5.hook_python import stable_python_executable

# ---------------------------------------------------------------------------
# CLI wrapper registration (avoids pip install -e .)
# ---------------------------------------------------------------------------


def _find_path_dir() -> Path | None:
    """Find a writable directory already in PATH where we can place a wrapper."""
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    path_dir_keys = set()
    for p in path_dirs:
        if not p:
            continue
        try:
            path_dir_keys.add(str(Path(p).resolve()).casefold())
        except OSError:
            continue

    # Candidate directories: where pip.exe / pip lives
    python_exe = Path(sys.executable)
    import site
    candidates = []
    # Windows: Python312\Scripts or user AppData\...\Scripts
    candidates.append(python_exe.parent / "Scripts")
    if site.getusersitepackages():
        user_base = Path(site.getusersitepackages()).parent.parent
        candidates.append(user_base / "Scripts")
    # Unix: ~/.local/bin
    candidates.append(Path.home() / ".local" / "bin")
    # The python dir itself (Unix)
    candidates.append(python_exe.parent)

    def is_durable_path_dir(path: Path) -> bool:
        text = str(path).casefold()
        return "\\uv\\cache\\builds-v0\\" not in text and "\\.tmp" not in text and "\\.codex\\tmp\\" not in text

    for c in candidates:
        try:
            c_resolved = c.resolve()
            if (
                c_resolved.exists()
                and str(c_resolved).casefold() in path_dir_keys
                and is_durable_path_dir(c_resolved)
            ):
                if os.access(str(c_resolved), os.W_OK):
                    return c_resolved
        except OSError:
            continue

    # Fallback: first writable dir in PATH
    for p in path_dirs:
        try:
            pp = Path(p).resolve()
            if pp.exists() and is_durable_path_dir(pp) and os.access(str(pp), os.W_OK):
                return pp
        except OSError:
            continue
    return None


def _register_cli() -> Path | None:
    """Create 'aitp' wrapper in a PATH-visible directory. Returns the wrapper path."""
    target_dir = _find_path_dir()
    if not target_dir:
        return None

    pm_path = REPO_ROOT / "scripts" / "aitp-pm.py"

    if sys.platform == "win32":
        wrapper = target_dir / "aitp.cmd"
        wrapper.write_text(
            f'@echo off\r\npython "{pm_path}" %*\r\n',
            encoding="utf-8",
        )
    else:
        wrapper = target_dir / "aitp"
        wrapper.write_text(
            f'#!/bin/sh\nexec python3 "{pm_path}" "$@"\n',
            encoding="utf-8",
        )
        wrapper.chmod(0o755)
    return wrapper


def _unregister_cli() -> None:
    """Remove the 'aitp' wrapper created by _register_cli."""
    target_dir = _find_path_dir()
    if not target_dir:
        return
    for name in ("aitp.cmd", "aitp"):
        p = target_dir / name
        if p.exists():
            # Only remove if it points to our repo
            try:
                content = p.read_text(encoding="utf-8")
                if str(REPO_ROOT) in content or "aitp-pm.py" in content:
                    p.unlink()
            except OSError:
                pass

# Known path patterns to detect in existing deployed files
_TOPICS_ROOT_PATTERNS = [
    r'D:/[^\s"\']+/aitp-topics',
    r'C:/[^\s"\']+/aitp-topics',
]

# ---------------------------------------------------------------------------
# Install record helpers
# ---------------------------------------------------------------------------


def _load_record() -> dict:
    if RECORD_PATH.exists():
        try:
            return json.loads(RECORD_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"version": 1, "installs": {}}


def _save_record(rec: dict) -> None:
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    _atomic_write(RECORD_PATH, json.dumps(rec, indent=2, ensure_ascii=False))


def _record_key(agent: str, scope: str) -> str:
    return f"{agent}:{scope}"


def _norm_install_value(value: str) -> str:
    return str(value or "").replace("\\", "/").rstrip("/")


def _enforce_project_install_consistency(record: dict, variables: dict) -> None:
    """Reject project installs that would drift from existing project records."""
    expected_fields = ("REPO_ROOT", "TOPICS_ROOT", "TARGET_ROOT")
    for key, inst in record.get("installs", {}).items():
        try:
            _, scope = key.split(":", 1)
        except ValueError:
            continue
        if scope != "project":
            continue
        existing_vars = inst.get("variables", {})
        for field in expected_fields:
            existing = _norm_install_value(existing_vars.get(field, ""))
            incoming = _norm_install_value(variables.get(field, ""))
            if existing and incoming and existing != incoming:
                raise SystemExit(
                    "Project install consistency violation: "
                    f"{key} has {field}={existing}, incoming {field}={incoming}. "
                    "Use one shared project target/topics root for claude-code, kimi-code, and codex."
                )


def _recorded_install_path(raw: str) -> Path | None:
    """Return the filesystem path component from an install-record entry."""
    value = str(raw or "")
    if not value or value.startswith("- stale:"):
        return None
    return Path(value.split(" (", 1)[0])


def _record_install_files(paths: list[str]) -> list[str]:
    """Keep install records to durable deployed files, not cleanup log entries."""
    return [str(path) for path in paths if not str(path).startswith("- stale:")]


def _check_mcp_json(path: Path, issues: list[str], label: str) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        issues.append(f"{label} cannot parse MCP json: {exc}")
        print(f"      {path.name}: PARSE ERROR")
        return
    servers = data.get("mcpServers", {})
    has_aitp = "aitp" in servers
    if not has_aitp:
        issues.append(f"{label} missing aitp MCP entry")
    print(f"      {path.name} aitp MCP entry: {'OK' if has_aitp else 'MISSING'}")
    if has_aitp:
        entry_text = json.dumps(servers.get("aitp", {}), sort_keys=True)
        has_v5 = _has_v5_mcp_entrypoint(entry_text)
        has_legacy = _has_legacy_mcp_entrypoint(entry_text)
        if not has_v5:
            issues.append(f"{label} aitp MCP entry does not point to {MCP_ENTRYPOINT}")
        if has_legacy:
            issues.append(f"{label} aitp MCP entry still references a legacy MCP entrypoint")
        print(f"      {path.name} v5 MCP entrypoint: {'OK' if has_v5 else 'MISSING'}")
        print(f"      {path.name} legacy MCP entrypoint: {'ABSENT' if not has_legacy else 'PRESENT'}")


def _check_agent_toml(path: Path, issues: list[str], label: str) -> None:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        issues.append(f"{label} cannot read config.toml: {exc}")
        print("      config.toml: READ ERROR")
        return
    parent_names = {p.name for p in path.parents}
    if ".kimi" in parent_names or ".kimi-code" in parent_names:
        section = "[mcp.servers.aitp]"
    else:
        section = "[mcp_servers.aitp]"
    has_section = section in content
    has_entrypoint = _has_v5_mcp_entrypoint(content)
    has_legacy = _has_legacy_mcp_entrypoint(content)
    if not (has_section and has_entrypoint):
        issues.append(f"{label} config.toml missing v5 aitp MCP config")
    if has_legacy:
        issues.append(f"{label} config.toml still references a legacy MCP entrypoint")
    status = "OK" if has_section and has_entrypoint else "NOT CONFIGURED"
    print(f"      config.toml {section}: {status}")
    print(f"      config.toml legacy MCP entrypoint: {'ABSENT' if not has_legacy else 'PRESENT'}")


def _check_claude_settings(
    path: Path,
    issues: list[str],
    label: str,
    require_mcp: bool,
) -> None:
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        issues.append(f"{label} cannot parse settings.json: {exc}")
        print("      settings.json: PARSE ERROR")
        return

    has_mcp = "aitp" in settings.get("mcpServers", {})
    if require_mcp and not has_mcp:
        issues.append(f"{label} settings.json missing aitp MCP entry")
    elif not has_mcp:
        print("      settings.json aitp MCP entry: not present (project .mcp.json expected)")
    if has_mcp or require_mcp:
        print(f"      settings.json aitp MCP entry: {'OK' if has_mcp else 'MISSING'}")

    hooks = settings.get("hooks", {})
    hook_commands = [
        str(h.get("command", ""))
        for blocks in hooks.values()
        for block in blocks
        for h in block.get("hooks", [])
    ]
    has_v5_safe_hook = any(
        token in command
        for command in hook_commands
        for token in (
            "aitp-keyword-router.py",
            "aitp-routing-guard.py",
            "aitp_v5_claude_hook.py",
        )
    )
    has_legacy_stage_hook = any(
        token in command
        for command in hook_commands
        for token in ("session-start", "aitp_get_execution_brief", "brain/mcp_server.py")
    )
    if not has_v5_safe_hook:
        issues.append(f"{label} settings.json missing v5-safe AITP hook")
    if has_legacy_stage_hook:
        issues.append(f"{label} settings.json still contains legacy stage hook command")
    print(f"      settings.json v5-safe hook: {'OK' if has_v5_safe_hook else 'NOT CONFIGURED'}")
    print(f"      settings.json legacy stage hooks: {'ABSENT' if not has_legacy_stage_hook else 'PRESENT'}")


def _check_project_local_residue(target_root: Path, issues: list[str]) -> None:
    """Detect ignored project files that can silently route hosts to old wiring."""
    checks = [
        (target_root / ".claude" / "settings.local.json", "Claude settings.local.json"),
        (target_root / ".claude" / "hooks" / "hooks.json", "Claude hooks/hooks.json"),
        (target_root / ".kimi" / "config.toml", "Kimi config.toml"),
        (target_root / ".kimi-code" / "config.toml", "Kimi Code config.toml"),
        (target_root / ".codex" / "config.toml", "Codex config.toml"),
    ]
    expected_topics = _norm_install_value(str(target_root / "research" / "aitp-topics"))
    expected_project = _norm_install_value(str(target_root))
    stale_tokens = (
        "D:/BaiduSyncdisk/Theoretical-Physics",
        "D:\\BaiduSyncdisk\\Theoretical-Physics",
        "qsgw-headwing-update-librpa-current-20260525",
        "brain/mcp_server.py",
        "brain/native_mcp.py",
        "aitp_get_execution_brief(",
    )
    for path, label in checks:
        if not path.exists() or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(f"{label} cannot be read: {exc}")
            continue
        stale_hits = [token for token in stale_tokens if token in content]
        if stale_hits:
            issues.append(f"{label} contains stale AITP/path tokens: {', '.join(stale_hits)}")
            print(f"      {label} stale tokens: PRESENT")
        elif expected_topics and "AITP_TOPICS_ROOT" in content and expected_topics not in _norm_install_value(content):
            issues.append(f"{label} has AITP_TOPICS_ROOT outside expected project topics root")
            print(f"      {label} topics root: DRIFT")
        elif expected_project and str(path).endswith("hooks.json") and expected_project not in _norm_install_value(content):
            issues.append(f"{label} hook commands do not point at project-local .claude hooks")
            print(f"      {label} project-local hooks: DRIFT")
        else:
            print(f"      {label}: OK")


def _doctor_check_recorded_installs(installs: dict, issues: list[str]) -> None:
    """Validate recorded installs and avoid stale user-scope path assumptions."""
    print("\n  --- Agent Installs (recorded) ---")
    installed_agents: set[str] = set()
    project_records: dict[str, dict] = {}

    for key, inst in sorted(installs.items()):
        try:
            agent, scope = key.split(":", 1)
        except ValueError:
            issues.append(f"Malformed install record key: {key}")
            print(f"    {key}: MALFORMED")
            continue

        installed_agents.add(agent)
        if scope == "project":
            project_records[key] = inst

        print(f"\n    {agent} ({scope})")
        variables = inst.get("variables", {})
        for field in ("REPO_ROOT", "TOPICS_ROOT", "TARGET_ROOT"):
            if variables.get(field):
                print(f"      {field}: {variables[field]}")
        package_version = str(inst.get("package_version", "unknown"))
        if package_version != EXPECTED_PACKAGE_VERSION:
            issues.append(
                f"{key} package_version is {package_version}, expected {EXPECTED_PACKAGE_VERSION}; reinstall/update project adapters"
            )
            print(f"      package_version: {package_version} (EXPECTED {EXPECTED_PACKAGE_VERSION})")
        else:
            print(f"      package_version: {package_version}")

        files = inst.get("files", [])
        missing = 0
        checked = 0
        for raw in files:
            path = _recorded_install_path(raw)
            if path is None:
                continue
            checked += 1
            if not path.exists():
                missing += 1
                issues.append(f"{agent} ({scope}) recorded file missing: {path}")
                print(f"      MISSING: {path}")
        if missing == 0:
            print(f"      Files: all present ({checked} items)")

        for raw in files:
            path = _recorded_install_path(raw)
            if path is None or not path.exists():
                continue
            if path.name in {"mcp.json", ".mcp.json"}:
                _check_mcp_json(path, issues, f"{agent} ({scope})")
            elif path.name == "config.toml":
                _check_agent_toml(path, issues, f"{agent} ({scope})")
            elif path.name == "settings.json" and ".claude" in {p.name for p in path.parents}:
                _check_claude_settings(
                    path,
                    issues,
                    f"{agent} ({scope})",
                    require_mcp=(scope == "user"),
                )

    for agent in AGENTS:
        if agent not in installed_agents:
            issues.append(f"No recorded install for {agent}")

    if project_records:
        first_target_root = ""
        for agent in AGENTS:
            if f"{agent}:project" not in project_records:
                issues.append(f"No project-scope install recorded for {agent}")

        expected_fields = ("REPO_ROOT", "TOPICS_ROOT", "TARGET_ROOT")
        baselines: dict[str, tuple[str, str]] = {}
        for key, inst in sorted(project_records.items()):
            variables = inst.get("variables", {})
            for field in expected_fields:
                value = _norm_install_value(variables.get(field, ""))
                if not value:
                    issues.append(f"{key} missing {field}")
                    continue
                if field == "TARGET_ROOT" and not first_target_root:
                    first_target_root = variables.get(field, "")
                if field not in baselines:
                    baselines[field] = (key, value)
                    continue
                base_key, base_value = baselines[field]
                if value != base_value:
                    issues.append(
                        f"Project install mismatch: {key} has {field}={value}, "
                        f"but {base_key} has {field}={base_value}"
                    )
        if not any(issue.startswith("Project install mismatch") for issue in issues):
            print("\n    Project-scope consistency: OK")
        if first_target_root:
            print("\n    Project-local residue checks:")
            _check_project_local_residue(Path(first_target_root), issues)

    print("\n  Legacy user-scope host checks: skipped (install record is authoritative).")


def _print_doctor_summary(issues: list[str]) -> None:
    print(f"\n{'=' * 60}")
    if issues:
        print(f"  {len(issues)} issue(s) found:")
        for i, issue in enumerate(issues, 1):
            print(f"    {i}. {issue}")
        print(f"\n  Run: python scripts/aitp-pm.py install --agent all")
    else:
        print("  All checks passed. AITP is healthy.")


# ---------------------------------------------------------------------------
# Template & variable helpers
# ---------------------------------------------------------------------------


def _build_variables(topics_root: str | None = None, target_root: str | None = None) -> dict:
    python_exe = stable_python_executable()
    claude_user_dir = str(Path.home() / ".claude").replace("\\", "/")
    codex_user_dir = str(Path.home() / ".codex").replace("\\", "/")
    return {
        "REPO_ROOT": str(REPO_ROOT).replace("\\", "/"),
        "TOPICS_ROOT": (topics_root or "").replace("\\", "/"),
        "TARGET_ROOT": (target_root or "").replace("\\", "/"),
        "USER_HOME": str(Path.home()).replace("\\", "/"),
        "PYTHON_EXE": python_exe.replace("\\", "/"),
        "CLAUDE_USER_DIR": claude_user_dir,
        "AITP_HOOKS_DIR": f"{claude_user_dir}/hooks",
        "KIMI_USER_DIR": str(Path.home() / ".kimi").replace("\\", "/"),
        "CODEX_USER_DIR": codex_user_dir,
        "CODEX_HOOKS_DIR": f"{codex_user_dir}/hooks",
        "CODEX_HOME_DIR": str(Path.home() / ".codex-home").replace("\\", "/"),
        "CODEX_SWITCHER_SKILLS_DIR": str(Path.home() / ".codex-switcher" / "skills").replace("\\", "/"),
        "AGENTS_SKILLS_DIR": str(Path.home() / ".agents" / "skills").replace("\\", "/"),
    }


def _fill(text: str, variables: dict) -> str:
    for k, v in variables.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def _mcp_entrypoint(repo_root: str) -> str:
    return f"{repo_root}/{MCP_ENTRYPOINT}"


def _has_v5_mcp_entrypoint(text: str) -> bool:
    return MCP_ENTRYPOINT in text.replace("\\", "/")


def _has_legacy_mcp_entrypoint(text: str) -> bool:
    normalized = text.replace("\\", "/")
    return any(entrypoint in normalized for entrypoint in LEGACY_MCP_ENTRYPOINTS)


def _v5_topics_root_for(legacy_topics_root: Path) -> Path | None:
    if legacy_topics_root.name != "aitp-topics":
        return None
    if legacy_topics_root.parent.name != "research":
        return None
    return legacy_topics_root / ".aitp" / "topics"


def _read_template(rel_path: str) -> str | None:
    p = TEMPLATES_DIR / rel_path
    return p.read_text(encoding="utf-8") if p.exists() else None


def _detect_topics_root() -> str | None:
    """Try to find topics_root from existing configs."""
    # 1. Environment variable
    env = os.environ.get("AITP_TOPICS_ROOT")
    if env:
        return env

    # 2. Previous install record
    if RECORD_PATH.exists():
        try:
            rec = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
            for inst in rec.get("installs", {}).values():
                tr = inst.get("variables", {}).get("TOPICS_ROOT")
                if tr:
                    return tr
        except (json.JSONDecodeError, OSError):
            pass

    # 3. .aitp_config.json in common locations
    for cwd in [os.getcwd(), str(Path.home())]:
        for _ in range(5):
            cfg = Path(cwd) / ".aitp_config.json"
            if cfg.exists():
                try:
                    data = json.loads(cfg.read_text(encoding="utf-8"))
                    root = data.get("topics_root")
                    if root:
                        return root if os.path.isabs(root) else str(Path(cwd) / root)
                except (json.JSONDecodeError, OSError):
                    pass
            parent = str(Path(cwd).parent)
            if parent == cwd:
                break
            cwd = parent

    # 3. Scan existing deployed hooks for path patterns
    for hook_file in [
        Path.home() / ".claude" / "hooks" / "aitp-keyword-router.py",
        Path.home() / ".claude" / "skills" / "using-aitp" / "SKILL.md",
        Path.home() / ".agents" / "skills" / "using-aitp" / "SKILL.md",
    ]:
        if hook_file.exists():
            try:
                content = hook_file.read_text(encoding="utf-8")
                for pat in _TOPICS_ROOT_PATTERNS:
                    m = re.search(pat, content)
                    if m:
                        return m.group(0)
            except OSError:
                pass

    return None


def _prompt_topics_root() -> str:
    """Interactive prompt for topics_root. Falls back to default in non-interactive mode."""
    default = str(Path.home() / "aitp-topics")
    if not sys.stdin.isatty():
        print(f"Non-interactive mode — using default topics_root: {default}")
        return default
    print(f"\nWhere should AITP research topics be stored?")
    print(f"  [default: {default}]")
    raw = input("  Path: ").strip()
    return raw if raw else default


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Config merging
# ---------------------------------------------------------------------------


def _merge_claude_settings(settings_path: Path, variables: dict, remove: bool = False) -> None:
    """Add or remove AITP hooks from Claude Code settings.json.

    Hook configuration is read from deploy/config/hooks.json — the single
    source of truth. To add a new hook event, edit hooks.json only.
    """
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            settings = {}
    else:
        settings = {}

    # Load hook configuration from deploy/config/hooks.json
    hooks_config_path = REPO_ROOT / "deploy" / "config" / "hooks.json"
    aitp_hooks: dict = {}
    if hooks_config_path.exists():
        try:
            raw = _fill(hooks_config_path.read_text(encoding="utf-8"), variables)
            config = json.loads(raw)
            aitp_hooks = config.get("hooks", {})
        except (json.JSONDecodeError, OSError):
            pass

    if not aitp_hooks:
        # Fallback: v5-safe routing guards only. Session-specific lifecycle
        # hooks require an explicit v5 session id and are not installed here.
        hooks_dir = variables.get("AITP_HOOKS_DIR", variables["CLAUDE_USER_DIR"].replace("\\", "/") + "/hooks")
        python_exe = variables.get("PYTHON_EXE", "python")
        aitp_hooks = {
            "UserPromptSubmit": [{
                "matcher": "",
                "hooks": [{
                    "type": "command",
                    "command": f'"{python_exe}" "{hooks_dir}/aitp-keyword-router.py"',
                    "async": False,
                }],
            }],
            "PreToolUse": [{
                "matcher": "Write|Edit|MultiEdit",
                "hooks": [{
                    "type": "command",
                    "command": f'"{python_exe}" "{hooks_dir}/aitp-routing-guard.py"',
                    "async": False,
                }],
            }],
        }

    existing_hooks = settings.setdefault("hooks", {})

    def _normalize(cmd: str) -> str:
        return cmd.replace("\\", "/").lower()

    def _is_aitp_lightweight_hook_command(cmd: str) -> bool:
        normalized = _normalize(cmd)
        return "aitp-keyword-router.py" in normalized or "aitp-routing-guard.py" in normalized

    if remove:
        for event_name in aitp_hooks:
            aitp_cmds = set()
            for entry in aitp_hooks[event_name]:
                for h in entry.get("hooks", []):
                    aitp_cmds.add(_normalize(h.get("command", "")))
            if event_name in existing_hooks:
                existing_hooks[event_name] = [
                    block
                    for block in existing_hooks[event_name]
                    if not any(
                        _normalize(h.get("command", "")) in aitp_cmds
                        or _is_aitp_lightweight_hook_command(h.get("command", ""))
                        for h in block.get("hooks", [])
                    )
                ]
                if not existing_hooks[event_name]:
                    del existing_hooks[event_name]
    else:
        for event_name, aitp_entries in aitp_hooks.items():
            existing = existing_hooks.get(event_name, [])
            aitp_cmds = set()
            for entry in aitp_entries:
                for h in entry.get("hooks", []):
                    aitp_cmds.add(_normalize(h.get("command", "")))
            filtered = [
                block
                for block in existing
                if not any(
                    _normalize(h.get("command", "")) in aitp_cmds
                    or _is_aitp_lightweight_hook_command(h.get("command", ""))
                    for h in block.get("hooks", [])
                )
            ]
            filtered.extend(aitp_entries)
            existing_hooks[event_name] = filtered

    # Merge AITP MCP server into settings.json (Claude Code reads MCP from here)
    if not remove:
        repo_root_var = variables["REPO_ROOT"]
        topics_root_var = variables.get("TOPICS_ROOT", "")
        mcp_entry = {
            "command": "python",
            "args": [_mcp_entrypoint(repo_root_var)],
        }
        if topics_root_var:
            mcp_entry["env"] = {"AITP_TOPICS_ROOT": topics_root_var}
        settings.setdefault("mcpServers", {})["aitp"] = mcp_entry
    else:
        settings.get("mcpServers", {}).pop("aitp", None)
        if not settings.get("mcpServers"):
            settings.pop("mcpServers", None)

    _atomic_write(settings_path, json.dumps(settings, indent=2, ensure_ascii=False))


def _write_mcp_json(
    mcp_path: Path,
    repo_root: str,
    topics_root: str = "",
    remove: bool = False,
    prefer_uv: bool = False,
) -> None:
    """Add or remove AITP MCP server entry."""
    if mcp_path.exists():
        try:
            data = json.loads(mcp_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    else:
        data = {}

    servers = data.setdefault("mcpServers", {})

    if remove:
        servers.pop("aitp", None)
        if not servers:
            del data["mcpServers"]
    else:
        if prefer_uv and shutil.which("uv"):
            entry = {
                "command": "uv",
                "args": [
                    "run",
                    "--with", "pyyaml",
                    "--with", "jsonschema",
                    "--with", "fastmcp",
                    "python",
                    _mcp_entrypoint(repo_root),
                ],
                "cwd": repo_root,
            }
        else:
            entry = {
                "command": "python",
                "args": [_mcp_entrypoint(repo_root)],
                "cwd": repo_root,
            }
        if topics_root:
            entry["env"] = {"AITP_TOPICS_ROOT": topics_root}
        servers["aitp"] = entry

    if data:
        _atomic_write(mcp_path, json.dumps(data, indent=2, ensure_ascii=False))
    elif mcp_path.exists():
        mcp_path.unlink()


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _toml_array(values: list[str]) -> str:
    return "[" + ", ".join(_toml_string(v) for v in values) + "]"


def _strip_toml_sections(content: str, section_headers: set[str]) -> str:
    lines = content.splitlines()
    out: list[str] = []
    skip = False
    for line in lines:
        stripped = line.strip()
        if stripped in section_headers:
            skip = True
            continue
        if skip and stripped.startswith("["):
            skip = False
        if not skip:
            out.append(line)
    return "\n".join(out).rstrip()


def _merge_codex_config_toml(
    config_path: Path,
    repo_root: str,
    topics_root: str = "",
    remove: bool = False,
    prefer_uv: bool = False,
) -> None:
    """Add or remove [mcp_servers.aitp] from Codex config.toml."""
    if config_path.exists():
        content = config_path.read_text(encoding="utf-8")
    elif remove:
        return
    else:
        content = ""

    content = _strip_toml_sections(
        content,
        {"[mcp_servers.aitp]", "[mcp_servers.aitp.env]"},
    )

    if remove:
        if content:
            _atomic_write(config_path, content + "\n")
        elif config_path.exists():
            config_path.unlink()
        return

    if prefer_uv and shutil.which("uv"):
        command = "uv"
        args = [
            "run",
            "--with", "pyyaml",
            "--with", "jsonschema",
            "--with", "fastmcp",
            "python",
            _mcp_entrypoint(repo_root),
        ]
    else:
        command = "python"
        args = [_mcp_entrypoint(repo_root)]

    block = [
        "[mcp_servers.aitp]",
        'type = "stdio"',
        f"command = {_toml_string(command)}",
        f"args = {_toml_array(args)}",
        f"cwd = {_toml_string(repo_root)}",
        "startup_timeout_sec = 60",
    ]
    if topics_root:
        block.extend([
            "",
            "[mcp_servers.aitp.env]",
            f"AITP_TOPICS_ROOT = {_toml_string(topics_root)}",
        ])

    new_content = (content + "\n\n" if content else "") + "\n".join(block) + "\n"
    _atomic_write(config_path, new_content)


def _merge_kimi_config_toml(
    config_path: Path,
    repo_root: str,
    topics_root: str = "",
    remove: bool = False,
    prefer_uv: bool = True,
) -> None:
    """Add or remove [mcp.servers.aitp] section from Kimi Code config.toml."""
    if not config_path.exists():
        if not remove:
            content = ""
        else:
            return
    else:
        content = config_path.read_text(encoding="utf-8")

    section_header = '[mcp.servers.aitp]'
    if prefer_uv and shutil.which("uv"):
        command = "uv"
        args = [
            "run",
            "--with", "pyyaml",
            "--with", "jsonschema",
            "--with", "fastmcp",
            "python",
            _mcp_entrypoint(repo_root),
        ]
    else:
        command = "python"
        args = [_mcp_entrypoint(repo_root)]

    section_lines = [
        section_header,
        f"command = {_toml_string(command)}",
        f"args = {_toml_array(args)}",
        f"cwd = {_toml_string(repo_root)}",
    ]
    if topics_root:
        section_lines.extend([
            "",
            "[mcp.servers.aitp.env]",
            f"AITP_TOPICS_ROOT = {_toml_string(topics_root)}",
        ])
    section_block = "\n".join(section_lines) + "\n"

    # Remove existing section
    lines = content.split("\n")
    new_lines = []
    skip = False
    for line in lines:
        if line.strip() == section_header:
            skip = True
            continue
        if skip:
            if line.startswith("[") and not line.startswith("[mcp.servers.aitp"):
                skip = False
                new_lines.append(line)
            continue
        new_lines.append(line)

    if not remove:
        # Find [mcp.servers] or [mcp] section to place after
        insert_idx = len(new_lines)
        for i, line in enumerate(new_lines):
            if line.strip().startswith("[mcp"):
                insert_idx = i + 1
                # Skip existing mcp.server.* entries
                while insert_idx < len(new_lines) and (
                    new_lines[insert_idx].strip() == ""
                    or new_lines[insert_idx].strip().startswith("command")
                    or new_lines[insert_idx].strip().startswith("args")
                    or new_lines[insert_idx].strip().startswith("[mcp.servers.")
                ):
                    if new_lines[insert_idx].strip().startswith("[mcp.servers."):
                        insert_idx += 1
                    else:
                        break
                break

        new_lines.insert(insert_idx, section_block.rstrip())

    result = "\n".join(new_lines)
    if not result.endswith("\n"):
        result += "\n"
    _atomic_write(config_path, result)


def _remove_kimi_v5_hook_block(config_path: Path) -> bool:
    """Remove session-specific Kimi v5 hooks from a generic project install."""
    if not config_path.exists():
        return False
    text = config_path.read_text(encoding="utf-8")
    begin_marker = "# BEGIN AITP V5 KIMI HOOKS"
    end_marker = "# END AITP V5 KIMI HOOKS"
    begin = text.find(begin_marker)
    if begin == -1:
        return False
    end = text.find(end_marker, begin)
    if end == -1:
        return False
    end += len(end_marker)
    cleaned = (text[:begin] + text[end:]).strip()
    if cleaned:
        cleaned += "\n"
    _atomic_write(config_path, cleaned)
    return True


# ---------------------------------------------------------------------------
# Deploy: Claude Code
# ---------------------------------------------------------------------------

# ── Auto-discovered deployment sources ───────────────────────────────────
# All deployable assets are auto-discovered — no hardcoded lists.
# To add a new skill/hook/runner/config, just drop the file in the right folder.

def _discover_deploy_skills() -> list[tuple[Path, str]]:
    """Discover all skills to deploy.

    Returns list of (source_path, deploy_rel_path) where deploy_rel_path
    is relative to the skills directory (e.g. "using-aitp/SKILL.md").

    Sources (in priority order):
      1. deploy/skills/        — gateway + curated skills (templates with {{vars}})
      2. skills/ (repo root)   — protocol skills (plain md, deployed as-is)
    """
    results: list[tuple[Path, str]] = []
    seen: set[str] = set()

    # Gateway skills from deploy/skills/ (may use template variables)
    deploy_skills_dir = REPO_ROOT / "deploy" / "skills"
    if deploy_skills_dir.is_dir():
        for p in sorted(deploy_skills_dir.glob("*.md")):
            name = p.stem
            if name not in seen:
                seen.add(name)
                results.append((p, f"{name}/SKILL.md"))

    # Legacy stage skills from repo skills/ are not deployed by default because
    # they mention L0/L1/L3/L4 and legacy tool names. Keep them available only
    # for explicit compatibility installs.
    repo_skills_dir = REPO_ROOT / "skills"
    if repo_skills_dir.is_dir() and _install_legacy_stage_skills():
        for p in sorted(repo_skills_dir.glob("*.md")):
            name = p.stem
            if name not in seen:
                seen.add(name)
                results.append((p, f"{name}/SKILL.md"))

    return results


def _install_legacy_stage_skills() -> bool:
    return os.environ.get("AITP_INSTALL_LEGACY_STAGE_SKILLS", "").lower() in {"1", "true", "yes"}


def _install_legacy_stage_hooks() -> bool:
    return os.environ.get("AITP_INSTALL_LEGACY_STAGE_HOOKS", "").lower() in {"1", "true", "yes"}


def _discover_deploy_hooks() -> list[tuple[Path, str]]:
    """Discover all hook scripts to deploy.

    Returns list of (source_path, deployed_filename).
    Sources: deploy/hooks/ (generated), hooks/ (repo root, with path injection).
    Includes .py, .cmd, and extensionless scripts.
    """
    results: list[tuple[Path, str]] = []
    seen: set[str] = set()

    # Generated hooks from deploy/hooks/
    deploy_hooks_dir = REPO_ROOT / "deploy" / "hooks"
    if deploy_hooks_dir.is_dir():
        for p in sorted(deploy_hooks_dir.iterdir()):
            if p.is_file() and p.suffix in (".py", ".cmd", ".sh"):
                dst_name = p.stem.replace("_", "-") + p.suffix if p.suffix else p.name
                if dst_name not in seen:
                    seen.add(dst_name)
                    results.append((p, dst_name))

    # Repo hooks from hooks/ (need brain path injection)
    v5_repo_hooks = {
        "aitp_v5_adapter_event_runner.py",
        "aitp_v5_claude_hook.py",
        "aitp_v5_hook.py",
        "aitp_v5_kimi_hook.py",
    }

    repo_hooks_dir = REPO_ROOT / "hooks"
    if repo_hooks_dir.is_dir():
        for p in sorted(repo_hooks_dir.iterdir()):
            if p.name == "__init__.py" or p.suffix == ".pyc":
                continue
            if p.is_file():
                if not _install_legacy_stage_hooks() and p.name not in v5_repo_hooks:
                    continue
                # .py files get underscore→hyphen rename; other files keep original name
                if p.suffix == ".py":
                    dst_name = p.stem.replace("_", "-") + ".py"
                else:
                    dst_name = p.name
                if dst_name not in seen:
                    seen.add(dst_name)
                    results.append((p, dst_name))

    return results


def _discover_deploy_runners() -> list[tuple[Path, str]]:
    """Discover runner scripts (.cmd, .sh) from deploy/runners/."""
    if not _install_legacy_stage_hooks():
        return []
    runners_dir = REPO_ROOT / "deploy" / "runners"
    if not runners_dir.is_dir():
        return []
    return [
        (p, p.name)
        for p in sorted(runners_dir.iterdir())
        if p.suffix in (".cmd", ".sh")
    ]


def _discover_deploy_config() -> list[tuple[Path, str]]:
    """Discover Claude deploy config files from deploy/config/."""
    config_dir = REPO_ROOT / "deploy" / "config"
    if not config_dir.is_dir():
        return []
    hooks_json = config_dir / "hooks.json"
    return [(hooks_json, "hooks.json")] if hooks_json.exists() else []


def _discover_workspace_skills_root() -> Path | None:
    """Find the workspace skills-shared/ directory for protocol skill sync."""
    topics_root = os.environ.get("AITP_TOPICS_ROOT",
        _detect_topics_root() or "")
    if topics_root:
        # topics_root is like D:/.../Theoretical-Physics/research/aitp-topics
        # workspace is two levels up
        ws = Path(topics_root).parent.parent
        skills_shared = ws / "skills-shared"
        if skills_shared.is_dir():
            return skills_shared
    return None


def _deploy_claude_code(
    scope: str, target_root: Path | None, variables: dict, remove: bool = False
) -> list[str]:
    """Install or uninstall AITP for Claude Code. Auto-discovers all deployable assets.

    Deploy sources (auto-discovered):
      - deploy/skills/*.md  → ~/.claude/skills/<name>/SKILL.md  (gateway skills)
      - skills/*.md         → ~/.claude/skills/<name>/SKILL.md  (protocol skills)
      - deploy/hooks/*.py   → ~/.claude/hooks/<name>.py         (generated hooks)
      - hooks/*.py          → ~/.claude/hooks/<name>.py         (repo hooks, path-injected)
      - deploy/runners/*    → ~/.claude/hooks/<name>            (shell/batch runners)
      - deploy/config/*.json → ~/.claude/hooks/<name>           (config files)

    Workspace sync (additional):
      - Protocol skills also synced to <workspace>/skills-shared/<name>.md
    """
    if scope == "user":
        base = Path(variables["CLAUDE_USER_DIR"])
    else:
        base = target_root / ".claude" if target_root else Path.cwd() / ".claude"

    hooks_dir = base / "hooks"
    skills_dir = base / "skills"
    deployed: list[str] = []

    # Discover all deployable assets
    all_skills = _discover_deploy_skills()
    all_hooks = _discover_deploy_hooks()
    all_runners = _discover_deploy_runners()
    all_configs = _discover_deploy_config()

    if remove:
        # Remove hook files
        for _, dst_name in all_hooks:
            p = hooks_dir / dst_name
            if p.exists():
                p.unlink()
                deployed.append(f"- {p}")
        for _, dst_name in all_runners:
            p = hooks_dir / dst_name
            if p.exists():
                p.unlink()
                deployed.append(f"- {p}")
        for _, dst_name in all_configs:
            p = hooks_dir / dst_name
            if p.exists():
                p.unlink()
                deployed.append(f"- {p}")

        # Remove skill dirs
        for _, dst_rel in all_skills:
            p = skills_dir / dst_rel
            if p.exists():
                p.unlink()
            # Clean parent dir if empty
            parent = p.parent
            try:
                if parent.exists() and parent != skills_dir and not list(parent.iterdir()):
                    parent.rmdir()
            except OSError:
                pass

        # Clean empty skills dir
        try:
            if skills_dir.exists() and not list(skills_dir.iterdir()):
                skills_dir.rmdir()
        except OSError:
            pass

        # Unmerge settings
        settings_path = base / "settings.json"
        if scope == "user":
            _merge_claude_settings(settings_path, variables, remove=True)
            deployed.append(f"~ {settings_path} (hooks removed)")
        else:
            if settings_path.exists():
                settings_path.unlink()
                deployed.append(f"- {settings_path}")

        if scope == "project":
            mcp_path = (target_root or Path.cwd()) / ".mcp.json"
            _write_mcp_json(mcp_path, variables["REPO_ROOT"], variables.get("TOPICS_ROOT", ""), remove=True)
            deployed.append(f"~ {mcp_path} (aitp entry removed)")

        return deployed

    # --- Install ---
    # 1. Deploy hooks (from both deploy/hooks/ and repo hooks/)
    print(f"  Deploying hooks to {hooks_dir}/")
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for src, dst_name in all_hooks:
        if not src.exists():
            print(f"    WARNING: source not found: {src}")
            continue
        content = src.read_text(encoding="utf-8")
        # Inject REPO_ROOT into hooks that import from brain
        if "from brain." in content or "import brain." in content:
            inject = f'sys.path.insert(0, r"{variables["REPO_ROOT"]}")\n'
            if inject.strip() not in content:
                content = content.replace(
                    "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))",
                    f'sys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n{inject}',
                )
        # Apply template variables
        content = _fill(content, variables)
        dst = hooks_dir / dst_name
        _atomic_write(dst, content)
        deployed.append(str(dst))

    # 2. Deploy runners (.cmd, .sh)
    for src, dst_name in all_runners:
        if not src.exists():
            continue
        content = _fill(src.read_text(encoding="utf-8"), variables)
        dst = hooks_dir / dst_name
        _atomic_write(dst, content)
        deployed.append(str(dst))

    # 3. Deploy config (.json)
    config_vars = variables
    if scope == "project":
        config_vars = {
            **variables,
            "CLAUDE_USER_DIR": str(base).replace("\\", "/"),
            "AITP_HOOKS_DIR": str(hooks_dir).replace("\\", "/"),
        }
    for src, dst_name in all_configs:
        if not src.exists():
            continue
        content = _fill(src.read_text(encoding="utf-8"), config_vars)
        dst = hooks_dir / dst_name
        _atomic_write(dst, content)
        deployed.append(str(dst))

    # 4. Deploy skills to ~/.claude/skills/<name>/SKILL.md
    print(f"  Deploying skills to {skills_dir}/")
    try:
        skills_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass  # Windows junction/mount point — directory already accessible
    for src, dst_rel in all_skills:
        if not src.exists():
            print(f"    WARNING: skill source not found: {src}")
            continue
        content = _fill(src.read_text(encoding="utf-8"), variables)
        dst = skills_dir / dst_rel
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            _atomic_write(dst, content)
            deployed.append(str(dst))
        except OSError:
            print(f"    SKIP {dst_rel} (cannot write to {dst.parent} — junction/mount point)")

    # 5. Sync v5 gateway skills to workspace skills-shared/. Legacy stage
    # skills stay in the protocol repo unless explicitly requested.
    ws_skills = _discover_workspace_skills_root()
    if ws_skills:
        deployed_ws = 0
        repo_skills_dir = REPO_ROOT / "skills"
        if repo_skills_dir.is_dir() and _install_legacy_stage_skills():
            for src in sorted(repo_skills_dir.glob("*.md")):
                dst = ws_skills / src.name
                dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
                deployed_ws += 1
        # Also sync deploy/skills/*.md as SKILL.md in subdirectories
        deploy_skills_dir = REPO_ROOT / "deploy" / "skills"
        if deploy_skills_dir.is_dir():
            for src in sorted(deploy_skills_dir.glob("*.md")):
                content = _fill(src.read_text(encoding="utf-8"), variables)
                dst_dir = ws_skills / src.stem
                dst_dir.mkdir(parents=True, exist_ok=True)
                (dst_dir / "SKILL.md").write_text(content, encoding="utf-8")
                deployed_ws += 1
        if not _install_legacy_stage_skills():
            for existing in ws_skills.iterdir():
                if existing.name.startswith(("skill-", "aitp-push-after-feature")):
                    if existing.is_dir():
                        shutil.rmtree(existing, ignore_errors=True)
                    elif existing.is_file():
                        existing.unlink()
        if deployed_ws:
            print(f"  Synced {deployed_ws} skills to workspace {ws_skills}")
            deployed.append(f"{ws_skills} ({deployed_ws} skills synced)")

    # 6. Merge settings.json
    if scope == "user":
        settings_path = base / "settings.json"
        _merge_claude_settings(settings_path, variables)
        deployed.append(f"{settings_path} (hooks merged)")
    else:
        settings_path = base / "settings.json"
        hooks_dir_str = str(base / "hooks").replace("\\", "/")
        project_vars = {
            **variables,
            "CLAUDE_USER_DIR": str(base).replace("\\", "/"),
            "AITP_HOOKS_DIR": hooks_dir_str,
        }
        # Read hook config from hooks.json (same source as user scope)
        hooks_config_path = REPO_ROOT / "deploy" / "config" / "hooks.json"
        project_hooks: dict = {}
        if hooks_config_path.exists():
            try:
                raw = _fill(hooks_config_path.read_text(encoding="utf-8"), project_vars)
                project_hooks = json.loads(raw).get("hooks", {})
            except (json.JSONDecodeError, OSError):
                pass
        if not project_hooks:
            python_exe = project_vars.get("PYTHON_EXE", "python")
            project_hooks = {
                "UserPromptSubmit": [{
                    "matcher": "",
                    "hooks": [{
                        "type": "command",
                        "command": f'"{python_exe}" "{hooks_dir_str}/aitp-keyword-router.py"',
                        "async": False,
                    }],
                }],
                "PreToolUse": [{
                    "matcher": "Write|Edit|MultiEdit",
                    "hooks": [{
                        "type": "command",
                        "command": f'"{python_exe}" "{hooks_dir_str}/aitp-routing-guard.py"',
                        "async": False,
                    }],
                }],
            }
        project_settings = {"hooks": project_hooks}
        _atomic_write(settings_path, json.dumps(project_settings, indent=2, ensure_ascii=False))
        deployed.append(str(settings_path))

        mcp_path = (target_root or Path.cwd()) / ".mcp.json"
        _write_mcp_json(
            mcp_path,
            variables["REPO_ROOT"],
            variables.get("TOPICS_ROOT", ""),
            prefer_uv=True,
        )
        deployed.append(str(mcp_path))

    # 7. Clean up stale AITP files (deployed files with no matching source)
    # Only remove files that match AITP naming patterns to avoid touching
    # skills/hooks installed by other tools.
    _AITP_HOOK_PREFIXES = ("aitp-", "hook-", "compact", "run-hook", "session-start", "stop")
    _AITP_SKILL_PREFIXES = ("aitp-", "skill-", "using-aitp")

    expected_hook_names = set()
    for _, dst_name in all_hooks:
        expected_hook_names.add(dst_name)
    for _, dst_name in all_runners:
        expected_hook_names.add(dst_name)
    for _, dst_name in all_configs:
        expected_hook_names.add(dst_name)
    for existing in hooks_dir.iterdir():
        if existing.is_file() and existing.name not in expected_hook_names:
            if existing.stem.startswith(_AITP_HOOK_PREFIXES):
                existing.unlink()
                deployed.append(f"- stale: {existing}")

    expected_skill_dirs = set()
    for _, dst_rel in all_skills:
        expected_skill_dirs.add(dst_rel.split("/")[0])
    for existing in skills_dir.iterdir():
        if existing.is_dir() and existing.name not in expected_skill_dirs:
            if existing.name.startswith(_AITP_SKILL_PREFIXES):
                shutil.rmtree(existing, ignore_errors=True)
                deployed.append(f"- stale: {existing}")

    return deployed


# ---------------------------------------------------------------------------
# Deploy: Kimi Code
# ---------------------------------------------------------------------------


def _deploy_kimi_code(
    scope: str, target_root: Path | None, variables: dict, remove: bool = False
) -> list[str]:
    """Install or uninstall AITP for Kimi Code. Auto-discovers skills."""
    if scope == "project":
        base = target_root or Path.cwd()
        targets = [
            (base / ".kimi" / "skills", base / ".kimi"),
            (base / ".kimi-code" / "skills", base / ".kimi-code"),
        ]
    else:
        # User-scope Kimi Code scans ~/.agents/skills/ for shared skills.
        targets = [(Path.home() / ".agents" / "skills", Path.home() / ".kimi")]

    # Gateway skills for Kimi Code (only the essential entry + runtime)
    gateway_skills = [
        ("using-aitp", "using-aitp/SKILL.md"),
        ("aitp-runtime", "aitp-runtime/SKILL.md"),
    ]

    deployed: list[str] = []

    if remove:
        for skills_dir, mcp_base in targets:
            for _skill_name, dst_rel in gateway_skills:
                p = skills_dir / dst_rel
                if p.exists():
                    p.unlink()
                    deployed.append(f"- {p}")
                parent = p.parent
                try:
                    if parent.exists() and parent != skills_dir and not list(parent.iterdir()):
                        parent.rmdir()
                except OSError:
                    pass

            mcp_path = mcp_base / "mcp.json"
            _write_mcp_json(mcp_path, variables["REPO_ROOT"], remove=True)
            deployed.append(f"~ {mcp_path} (aitp entry removed)")

            config_path = mcp_base / "config.toml"
            _merge_kimi_config_toml(config_path, variables["REPO_ROOT"], remove=True)
            deployed.append(f"~ {config_path} ([mcp.servers.aitp] removed)")

        return deployed

    # --- Install ---
    for skills_dir, mcp_base in targets:
        print(f"  Deploying skills to {skills_dir}/")
        try:
            skills_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass  # Windows junction/mount point
        for skill_name, dst_rel in gateway_skills:
            # Source from deploy/skills/ first, fall back to deploy/templates/
            src = REPO_ROOT / "deploy" / "skills" / f"{skill_name}.md"
            if not src.exists():
                src = TEMPLATES_DIR / "kimi-code" / f"{skill_name}.md"
            if not src.exists():
                src = TEMPLATES_DIR / "claude-code" / f"{skill_name}.md"
            if not src.exists():
                print(f"    WARNING: skill source not found: {skill_name}")
                continue
            content = _fill(src.read_text(encoding="utf-8"), variables)
            dst = skills_dir / dst_rel
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                _atomic_write(dst, content)
                deployed.append(str(dst))
            except OSError:
                print(f"    SKIP {dst_rel} (cannot write to {dst.parent} directory)")

        mcp_path = mcp_base / "mcp.json"
        _write_mcp_json(
            mcp_path,
            variables["REPO_ROOT"],
            variables.get("TOPICS_ROOT", ""),
            prefer_uv=True,
        )
        deployed.append(f"{mcp_path} (aitp entry written)")

        config_path = mcp_base / "config.toml"
        _merge_kimi_config_toml(
            config_path,
            variables["REPO_ROOT"],
            variables.get("TOPICS_ROOT", ""),
        )
        if scope == "project" and _remove_kimi_v5_hook_block(config_path):
            deployed.append(f"{config_path} (session-specific hooks removed)")
        deployed.append(f"{config_path} ([mcp.servers.aitp] merged)")

    return deployed

# ---------------------------------------------------------------------------
# Deploy: Codex App
# ---------------------------------------------------------------------------


def _discover_codex_skill_roots(scope: str, target_root: Path | None) -> list[Path]:
    """Return Codex skill roots for user or project scope.

    Codex deployments are kept in Codex-specific roots to avoid clobbering the
    shared ~/.agents/skills root used by other agents such as Kimi Code.
    """
    if scope == "project":
        base = target_root or Path.cwd()
        return [base / ".codex" / "skills"]

    candidates = [
        Path.home() / ".codex" / "skills",
        Path.home() / ".codex-home" / "skills",
        Path.home() / ".codex-switcher" / "skills",
    ]
    roots: list[Path] = []
    seen: set[Path] = set()
    for p in candidates:
        if p.exists() or p.parent.exists():
            resolved = p.resolve() if p.exists() else p
            if resolved not in seen:
                roots.append(p)
                seen.add(resolved)

    return roots or [Path.home() / ".codex" / "skills"]


def _discover_codex_gateway_skills() -> list[tuple[Path, str]]:
    skills_dir = REPO_ROOT / "deploy" / "codex" / "skills"
    if not skills_dir.is_dir():
        return []
    return [(p, p.stem) for p in sorted(skills_dir.glob("*.md"))]


def _codex_protocol_skill_preamble(skill_name: str) -> str:
    return f"""<!--
Codex app adapter override for {skill_name}.

If the upstream protocol text below mentions Claude/Kimi tool names, map them
to Codex behavior:
- AskUserQuestion: ask the user through Codex's available interaction surface.
  If no structured question tool is active, ask a concise plain-text question
  and wait for the user's answer.
- ToolSearch(query="select:AskUserQuestion", ...): skip this step. Codex app
  supplies its available tools through the active runtime.
- mcp__aitp__aitp_*: call the AITP MCP tool under the actual Codex tool name.
  If the tool is unavailable, stop and run doctor; do not emulate topic-state
  writes by manually editing AITP topic files.
- Read/Write/Grep/Glob/Bash: use Codex-equivalent file and shell tools for
  source code or registered source material, while preserving the rule that
  AITP topic-state mutation goes through AITP tools.

These adapter overrides control over conflicting platform-specific wording
inside the upstream skill body.
-->

"""


def _discover_codex_skills() -> list[tuple[Path, str, bool]]:
    """Discover Codex skill sources.

    Returns (source_path, skill_name, is_gateway). Gateway skills are
    Codex-native and replace deploy/skills copies. Protocol skills are wrapped
    with a Codex adapter preamble at deploy time.
    """
    results: list[tuple[Path, str, bool]] = []
    seen: set[str] = set()

    for src, name in _discover_codex_gateway_skills():
        results.append((src, name, True))
        seen.add(name)

    repo_skills_dir = REPO_ROOT / "skills"
    if repo_skills_dir.is_dir() and _install_legacy_stage_skills():
        for src in sorted(repo_skills_dir.glob("*.md")):
            name = src.stem
            if name in seen:
                continue
            results.append((src, name, False))
            seen.add(name)

    return results


_LIGHTWEIGHT_HOOK_SCRIPTS = ("aitp-keyword-router.py", "aitp-routing-guard.py")


def _is_aitp_lightweight_hook_command(command: str) -> bool:
    normalized = command.replace("\\", "/").casefold()
    return "aitp-keyword-router.py" in normalized or "aitp-routing-guard.py" in normalized


def _codex_lightweight_hooks_payload(variables: dict) -> dict:
    config_path = REPO_ROOT / "deploy" / "config" / "codex-hooks.json"
    if config_path.exists():
        try:
            raw = _fill(config_path.read_text(encoding="utf-8"), variables)
            payload = json.loads(raw)
            if isinstance(payload.get("hooks"), dict):
                return payload
        except (json.JSONDecodeError, OSError):
            pass

    hooks_dir = variables.get("CODEX_HOOKS_DIR", str(Path.home() / ".codex" / "hooks").replace("\\", "/"))
    python_exe = variables.get("PYTHON_EXE", stable_python_executable()).replace("\\", "/")
    return {
        "hooks": {
            "UserPromptSubmit": [{
                "matcher": "",
                "hooks": [{
                    "type": "command",
                    "command": f'"{python_exe}" "{hooks_dir}/aitp-keyword-router.py"',
                }],
            }],
            "PreToolUse": [{
                "matcher": "Write|Edit|MultiEdit",
                "hooks": [{
                    "type": "command",
                    "command": f'"{python_exe}" "{hooks_dir}/aitp-routing-guard.py"',
                }],
            }],
        }
    }


def _merge_codex_lightweight_hooks(hooks_path: Path, variables: dict, remove: bool = False) -> None:
    generated_hooks = _codex_lightweight_hooks_payload(variables).get("hooks", {})
    if hooks_path.exists():
        try:
            settings = json.loads(hooks_path.read_text(encoding="utf-8"))
            if not isinstance(settings, dict):
                settings = {}
        except (json.JSONDecodeError, OSError):
            settings = {}
    else:
        settings = {}

    existing_hooks = settings.setdefault("hooks", {})
    if not isinstance(existing_hooks, dict):
        existing_hooks = {}
        settings["hooks"] = existing_hooks

    for event_name, generated_entries in generated_hooks.items():
        current = existing_hooks.get(event_name, [])
        if not isinstance(current, list):
            current = []
        filtered = []
        for block in current:
            if not isinstance(block, dict):
                filtered.append(block)
                continue
            if any(
                _is_aitp_lightweight_hook_command(str(hook.get("command", "")))
                for hook in block.get("hooks", [])
                if isinstance(hook, dict)
            ):
                continue
            filtered.append(block)
        if remove:
            if filtered:
                existing_hooks[event_name] = filtered
            else:
                existing_hooks.pop(event_name, None)
        else:
            filtered.extend(deepcopy(generated_entries))
            existing_hooks[event_name] = filtered

    hooks_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(hooks_path, json.dumps(settings, indent=2, ensure_ascii=False) + "\n")


def _deploy_codex_lightweight_hooks(base: Path, variables: dict, remove: bool = False) -> list[str]:
    hooks_dir = base / "hooks"
    hooks_path = base / "hooks.json"
    codex_vars = {
        **variables,
        "CODEX_HOOKS_DIR": str(hooks_dir).replace("\\", "/"),
    }
    deployed: list[str] = []

    if remove:
        for name in _LIGHTWEIGHT_HOOK_SCRIPTS:
            path = hooks_dir / name
            if path.exists():
                path.unlink()
                deployed.append(f"- {path}")
        if hooks_path.exists():
            _merge_codex_lightweight_hooks(hooks_path, codex_vars, remove=True)
            deployed.append(f"~ {hooks_path} (lightweight hooks removed)")
        return deployed

    hooks_dir.mkdir(parents=True, exist_ok=True)
    for name in _LIGHTWEIGHT_HOOK_SCRIPTS:
        src = REPO_ROOT / "deploy" / "hooks" / name
        if not src.exists():
            print(f"    WARNING: hook source not found: {src}")
            continue
        content = _fill(src.read_text(encoding="utf-8"), codex_vars)
        dst = hooks_dir / name
        _atomic_write(dst, content)
        deployed.append(str(dst))

    _merge_codex_lightweight_hooks(hooks_path, codex_vars, remove=False)
    deployed.append(f"{hooks_path} (lightweight hooks merged)")
    return deployed


def _deploy_codex_app(
    scope: str, target_root: Path | None, variables: dict, remove: bool = False
) -> list[str]:
    """Install or uninstall AITP for Codex app.

    The adapter deploys Codex-native gateway skills, MCP config, and a
    lightweight hooks.json router/guard. Session-bound v5 lifecycle hooks remain
    explicit adapter installs, not default project wiring.
    """
    roots = _discover_codex_skill_roots(scope, target_root)
    skills = _discover_codex_skills()
    deployed: list[str] = []

    if not skills:
        print("  WARNING: no Codex skills found under deploy/codex/skills or skills/")
        return deployed

    if remove:
        for root in roots:
            for _, skill_name, _ in skills:
                p = root / skill_name / "SKILL.md"
                if p.exists():
                    p.unlink()
                    deployed.append(f"- {p}")
                try:
                    parent = p.parent
                    if parent.exists() and parent != root and not list(parent.iterdir()):
                        parent.rmdir()
                except OSError:
                    pass

            mcp_path = root.parent / "mcp.json"
            _write_mcp_json(
                mcp_path,
                variables["REPO_ROOT"],
                variables.get("TOPICS_ROOT", ""),
                remove=True,
                prefer_uv=True,
            )
            deployed.append(f"~ {mcp_path} (aitp entry removed)")

            config_path = root.parent / "config.toml"
            _merge_codex_config_toml(
                config_path,
                variables["REPO_ROOT"],
                variables.get("TOPICS_ROOT", ""),
                remove=True,
                prefer_uv=True,
            )
            deployed.append(f"~ {config_path} ([mcp_servers.aitp] removed)")
            deployed.extend(_deploy_codex_lightweight_hooks(root.parent, variables, remove=True))
        return deployed

    for root in roots:
        print(f"  Deploying Codex skills to {root}/")
        try:
            root.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

        for src, skill_name, is_gateway in skills:
            if not src.exists():
                print(f"    WARNING: skill source not found: {src}")
                continue
            content = src.read_text(encoding="utf-8")
            if not is_gateway:
                content = _codex_protocol_skill_preamble(skill_name) + content
            content = _fill(content, variables)
            dst = root / skill_name / "SKILL.md"
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                _atomic_write(dst, content)
                deployed.append(str(dst))
            except OSError:
                print(f"    SKIP {skill_name}/SKILL.md (cannot write to {dst.parent})")

        expected_skill_dirs = {skill_name for _, skill_name, _ in skills}
        for existing in root.iterdir():
            if existing.is_dir() and existing.name not in expected_skill_dirs:
                if existing.name.startswith(("aitp-", "skill-", "using-aitp")):
                    shutil.rmtree(existing, ignore_errors=True)
                    deployed.append(f"- stale: {existing}")

        mcp_path = root.parent / "mcp.json"
        _write_mcp_json(
            mcp_path,
            variables["REPO_ROOT"],
            variables.get("TOPICS_ROOT", ""),
            prefer_uv=True,
        )
        deployed.append(f"{mcp_path} (aitp entry written)")

        config_path = root.parent / "config.toml"
        _merge_codex_config_toml(
            config_path,
            variables["REPO_ROOT"],
            variables.get("TOPICS_ROOT", ""),
            prefer_uv=True,
        )
        deployed.append(f"{config_path} ([mcp_servers.aitp] written)")
        deployed.extend(_deploy_codex_lightweight_hooks(root.parent, variables, remove=False))

    return deployed


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_install(args) -> None:
    agents = AGENTS if args.agent == "all" else [args.agent]
    scope = args.scope or "user"
    target_root = Path(args.target_root) if args.target_root else None
    if scope == "project" and target_root is None:
        target_root = Path.cwd()

    topics_root = args.topics_root or _detect_topics_root()
    if not topics_root:
        topics_root = _prompt_topics_root()

    record = _load_record()
    variables = _build_variables(
        topics_root,
        str(target_root) if scope == "project" and target_root else None,
    )
    if scope == "project":
        _enforce_project_install_consistency(record, variables)

    pkg_file = REPO_ROOT / "package.json"
    try:
        pkg_ver = json.loads(pkg_file.read_text(encoding="utf-8")).get("version", "unknown")
    except (OSError, json.JSONDecodeError):
        pkg_ver = "unknown"

    for agent in agents:
        print(f"\n=== Installing AITP for {agent} ({scope} scope) ===")
        if agent == "claude-code":
            paths = _deploy_claude_code(scope, target_root, variables, remove=False)
        elif agent == "kimi-code":
            paths = _deploy_kimi_code(scope, target_root, variables, remove=False)
        elif agent == "codex":
            paths = _deploy_codex_app(scope, target_root, variables, remove=False)
        else:
            print(f"  Unknown agent: {agent}")
            continue

        key = _record_key(agent, scope)
        record["installs"][key] = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "package_version": pkg_ver,
            "variables": {k: v for k, v in variables.items()},
            "files": _record_install_files(paths),
        }

        for p in paths:
            print(f"  + {p}")
        print(f"  Done. {len(paths)} items deployed.")

    _save_record(record)
    print(f"\nInstall record saved to {RECORD_PATH}")

    # Register a global 'aitp' CLI wrapper only for user-scope installs.
    if scope == "user":
        wrapper = _register_cli()
        if wrapper:
            print(f"  CLI registered: {wrapper}")
        else:
            print("  WARNING: could not auto-register 'aitp' command (no writable PATH dir found)")
    else:
        print("  Project-scope install: global 'aitp' CLI wrapper not registered.")


def cmd_uninstall(args) -> None:
    agents = AGENTS if args.agent == "all" else [args.agent]
    scope = args.scope or "user"
    target_root = Path(args.target_root) if args.target_root else None
    if scope == "project" and target_root is None:
        target_root = Path.cwd()

    record = _load_record()
    variables = _build_variables(
        target_root=str(target_root) if scope == "project" and target_root else None,
    )

    for agent in agents:
        print(f"\n=== Uninstalling AITP for {agent} ({scope} scope) ===")
        if agent == "claude-code":
            paths = _deploy_claude_code(scope, target_root, variables, remove=True)
        elif agent == "kimi-code":
            paths = _deploy_kimi_code(scope, target_root, variables, remove=True)
        elif agent == "codex":
            paths = _deploy_codex_app(scope, target_root, variables, remove=True)
        else:
            continue

        key = _record_key(agent, scope)
        record["installs"].pop(key, None)

        for p in paths:
            print(f"  {p}")
        print(f"  Done. {len(paths)} items removed.")

    _save_record(record)
    if scope == "user":
        _unregister_cli()
        print("  CLI wrapper removed.")


def cmd_update(args) -> None:
    agents = AGENTS if args.agent == "all" else [args.agent]

    record = _load_record()
    if not record["installs"]:
        print("No AITP installs found. Run 'install' first.")
        return

    topics_root = args.topics_root or _detect_topics_root()
    if not topics_root:
        topics_root = _prompt_topics_root()

    pkg_file = REPO_ROOT / "package.json"
    try:
        pkg_ver = json.loads(pkg_file.read_text(encoding="utf-8")).get("version", "unknown")
    except (OSError, json.JSONDecodeError):
        pkg_ver = "unknown"

    # Backup existing files before overwriting
    backup_dir = INSTALL_DIR / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_count = 0
    for key in record["installs"]:
        for f in record["installs"][key].get("files", []):
            f = f.split(" (")[0]  # Strip annotations like "(hooks merged)"
            p = Path(f)
            if p.is_file():
                try:
                    dest = backup_dir / p.name
                    shutil.copy2(p, dest)
                    backup_count += 1
                except (OSError, PermissionError):
                    pass
    if backup_count > 0:
        print(f"Backed up {backup_count} files to {backup_dir}")

    for agent in agents:
        # Find all scopes installed for this agent
        agent_keys = [k for k in record["installs"] if k.startswith(f"{agent}:")]
        if not agent_keys:
            print(f"No {agent} installs found in record.")
            continue

        for key in agent_keys:
            _, scope = key.split(":", 1)
            target_root = None
            if scope == "project":
                inst = record["installs"][key]
                tr = inst.get("variables", {}).get("TARGET_ROOT")
                if tr:
                    target_root = Path(tr)

            variables = _build_variables(
                topics_root,
                str(target_root) if scope == "project" and target_root else None,
            )
            if scope == "project":
                _enforce_project_install_consistency(record, variables)

            print(f"\n=== Updating AITP for {agent} ({scope} scope) ===")
            if agent == "claude-code":
                paths = _deploy_claude_code(scope, target_root, variables, remove=False)
            elif agent == "kimi-code":
                paths = _deploy_kimi_code(scope, target_root, variables, remove=False)
            elif agent == "codex":
                paths = _deploy_codex_app(scope, target_root, variables, remove=False)
            else:
                continue

            record["installs"][key] = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "package_version": pkg_ver,
                "variables": {k: v for k, v in variables.items()},
                "files": _record_install_files(paths),
            }

            for p in paths:
                print(f"  ~ {p}")
            print(f"  Done. {len(paths)} items synced.")

    _save_record(record)
    print(f"\nInstall record updated at {RECORD_PATH}")


def _git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        capture_output=True, text=True, cwd=cwd or REPO_ROOT, timeout=120,
    )


def _read_version() -> str:
    try:
        return json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8")).get("version", "unknown")
    except (OSError, json.JSONDecodeError):
        return "unknown"


def _read_protocol_metadata() -> dict:
    path = REPO_ROOT / "brain" / "PROTOCOL.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    try:
        import yaml

        data = yaml.safe_load(match.group(1)) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _strict_v5_deploy_surface_issues() -> list[str]:
    """Catch agent-facing templates that still teach legacy active wiring."""
    checks = [
        {
            "path": "deploy/templates/opencode/aitp-plugin.js",
            "required": (
                "AITP 1.0.0 v5 adapter",
                "aitp_v5_get_execution_brief",
                "aitp_v5_build_workspace_recovery_audit",
                "{{REPO_ROOT}}",
                "{{TOPICS_ROOT}}",
            ),
            "forbidden": (
                "v4.1 harness adapter",
                "Stage Skills (checklist-driven",
                "AITP MCP tools are available as `aitp_*`",
                "aitp_get_execution_brief(topics_root=",
                "D:/BaiduSyncdisk",
            ),
        },
        {
            "path": "deploy/templates/claude-code/aitp-mcp-setup.md",
            "required": (
                MCP_ENTRYPOINT,
                "aitp-pm.py doctor",
                "AITP 1.0.0/v5",
            ),
            "forbidden": (
                "claude mcp add-json",
                '"args":["{{REPO_ROOT}}/brain/mcp_server.py"]',
            ),
        },
        {
            "path": "deploy/templates/claude-code/aitp_panel.py",
            "required": ("aitp_v5_get_execution_brief",),
            "forbidden": ("Use aitp_get_execution_brief for detailed instructions",),
        },
    ]
    issues: list[str] = []
    for check in checks:
        rel = str(check["path"])
        path = REPO_ROOT / rel
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(f"{rel} cannot be read for v5 deploy-surface check: {exc}")
            continue
        for token in check["required"]:
            if token not in text:
                issues.append(f"{rel} missing required v5 token: {token}")
        for token in check["forbidden"]:
            if token in text:
                issues.append(f"{rel} still contains legacy active token: {token}")
    return issues


def _strict_v5_contract_issues() -> list[str]:
    issues: list[str] = []
    package_version = _read_version()
    if package_version != EXPECTED_PACKAGE_VERSION:
        issues.append(
            f"package.json version is {package_version}, expected {EXPECTED_PACKAGE_VERSION}"
        )

    protocol = _read_protocol_metadata()
    if protocol.get("version") != EXPECTED_PACKAGE_VERSION:
        issues.append(
            f"brain/PROTOCOL.md version is {protocol.get('version')!r}, expected {EXPECTED_PACKAGE_VERSION}"
        )
    if protocol.get("implementation_generation") != EXPECTED_IMPLEMENTATION:
        issues.append(
            "brain/PROTOCOL.md must declare implementation_generation='v5'"
        )
    if protocol.get("implementation_entrypoint") != MCP_ENTRYPOINT:
        issues.append(
            f"brain/PROTOCOL.md implementation_entrypoint must be {MCP_ENTRYPOINT}"
        )
    if protocol.get("legacy_stage_model") != "orientation-only":
        issues.append(
            "brain/PROTOCOL.md must mark legacy_stage_model as orientation-only"
        )

    try:
        from brain import v5

        if getattr(v5, "__version__", None) != EXPECTED_PACKAGE_VERSION:
            issues.append(
                f"brain.v5.__version__ is {getattr(v5, '__version__', None)!r}, expected {EXPECTED_PACKAGE_VERSION}"
            )
        if getattr(v5, "PROTOCOL_IMPLEMENTATION", None) != EXPECTED_IMPLEMENTATION:
            issues.append("brain.v5.PROTOCOL_IMPLEMENTATION must be 'v5'")
    except Exception as exc:
        issues.append(f"cannot import brain.v5 for version contract: {exc}")

    try:
        from brain.v5 import native_mcp

        server_info = getattr(native_mcp, "_SERVER_INFO", {})
        if server_info.get("version") != EXPECTED_PACKAGE_VERSION:
            issues.append(
                f"native MCP serverInfo.version is {server_info.get('version')!r}, expected {EXPECTED_PACKAGE_VERSION}"
            )
        compat_aliases = getattr(native_mcp, "_COMPAT_TOOL_NAMES", set())
        if compat_aliases:
            issues.append(
                "native MCP compatibility aliases are exposed; unset AITP_V5_EXPOSE_COMPAT_ALIASES for strict v5"
            )
    except Exception as exc:
        issues.append(f"cannot import brain.v5.native_mcp for strict contract: {exc}")

    if os.environ.get("AITP_LEGACY_ENABLE_WRITES") == "1":
        issues.append(
            "AITP_LEGACY_ENABLE_WRITES=1 is set; legacy L0-L4 writes must stay disabled for normal v5 operation"
        )

    try:
        from brain import mcp_server as legacy_mcp

        if not callable(getattr(legacy_mcp, "is_legacy_write_tool", None)):
            issues.append("legacy MCP server is missing the read-only write classifier")
        elif not legacy_mcp.is_legacy_write_tool("aitp_bootstrap_topic"):
            issues.append("legacy MCP server does not classify aitp_bootstrap_topic as a blocked write tool")
        if getattr(legacy_mcp, "_legacy_writes_enabled", lambda: True)():
            issues.append("legacy MCP writes are enabled; unset AITP_LEGACY_ENABLE_WRITES")
    except Exception as exc:
        issues.append(f"cannot import legacy MCP server for read-only guard check: {exc}")

    issues.extend(_strict_v5_deploy_surface_issues())

    return issues


def cmd_upgrade(args) -> None:
    """Pull latest from remote, then re-deploy all installed agents."""
    print("AITP Upgrade — git pull + re-deploy")
    print("=" * 60)

    # --- Pre-flight checks ---
    git_check = _git("rev-parse", "--is-inside-work-tree")
    if git_check.returncode != 0:
        print("  FAIL: not a git repository (or git not found)")
        print(f"  Repo root: {REPO_ROOT}")
        return

    # Check for uncommitted changes
    dirty = _git("status", "--porcelain", "--ignore-submodules")
    if dirty.returncode == 0 and dirty.stdout.strip():
        lines = dirty.stdout.strip().split("\n")
        print(f"  WARNING: {len(lines)} uncommitted change(s) detected:")
        for line in lines[:5]:
            print(f"    {line.strip()}")
        if len(lines) > 5:
            print(f"    ... and {len(lines) - 5} more")
        if not args.force:
            print("\n  Use --force to stash changes and proceed, or commit them first.")
            return
        print("  --force: stashing changes...")
        stash = _git("stash", "push", "-m", "aitp-upgrade-auto-stash")
        if stash.returncode != 0:
            print(f"  FAIL: git stash failed: {stash.stderr.strip()}")
            return
        print("  Changes stashed.")

    old_ver = _read_version()
    old_hash = _git("rev-parse", "--short", "HEAD").stdout.strip()

    # --- Pull ---
    print(f"\n  Current: v{old_ver} ({old_hash})")
    print("  Pulling latest...")
    pull = _git("pull", "--ff-only")
    if pull.returncode != 0:
        print(f"  FAIL: git pull failed:")
        for line in pull.stderr.strip().split("\n"):
            print(f"    {line}")
        # Restore stash if we stashed
        if args.force and dirty.stdout.strip():
            print("  Restoring stashed changes...")
            _git("stash", "pop")
        return

    new_hash = _git("rev-parse", "--short", "HEAD").stdout.strip()
    new_ver = _read_version()

    if old_hash == new_hash:
        print(f"  Already up to date ({new_hash}). Nothing to upgrade.")
        return

    # Show what changed
    log = _git("log", "--oneline", f"{old_hash}..{new_hash}")
    commits = log.stdout.strip().split("\n") if log.stdout.strip() else []
    print(f"\n  Updated: v{old_ver} → v{new_ver} ({len(commits)} commit(s))")
    for c in commits[:8]:
        print(f"    {c}")
    if len(commits) > 8:
        print(f"    ... and {len(commits) - 8} more")

    # --- Install new deps if pyproject.toml changed ---
    diff = _git("diff", f"{old_hash}..{new_hash}", "--", "pyproject.toml")
    if diff.returncode == 0 and diff.stdout.strip():
        print("\n  pyproject.toml changed, re-installing dependencies...")
        dep_install = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", str(REPO_ROOT)],
            capture_output=True, text=True, timeout=300,
        )
        if dep_install.returncode == 0:
            print("  Dependencies updated.")
        else:
            print(f"  WARNING: dependency install had issues: {dep_install.stderr.strip()[:200]}")

    # --- Re-deploy ---
    record = _load_record()
    if not record["installs"]:
        print("\n  No AITP installs on record. Falling back to fresh install.")
        cmd_install(args)
        return

    topics_root = _detect_topics_root()
    if not topics_root:
        topics_root = _prompt_topics_root()

    for key in list(record["installs"]):
        agent, scope = key.split(":", 1)
        target_root = None
        if scope == "project":
            tr = record["installs"][key].get("variables", {}).get("TARGET_ROOT")
            if tr:
                target_root = Path(tr)

        variables = _build_variables(
            topics_root,
            str(target_root) if scope == "project" and target_root else None,
        )
        if scope == "project":
            _enforce_project_install_consistency(record, variables)

        print(f"\n=== Re-deploying {agent} ({scope} scope) ===")
        if agent == "claude-code":
            paths = _deploy_claude_code(scope, target_root, variables, remove=False)
        elif agent == "kimi-code":
            paths = _deploy_kimi_code(scope, target_root, variables, remove=False)
        else:
            continue

        record["installs"][key] = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "package_version": new_ver,
            "variables": {k: v for k, v in variables.items()},
            "files": _record_install_files(paths),
        }
        print(f"  Done. {len(paths)} items synced.")

    _save_record(record)

    # Restore stash if we stashed
    if args.force and dirty.stdout.strip():
        print("\n  Restoring stashed changes...")
        pop = _git("stash", "pop")
        if pop.returncode == 0:
            print("  Stashed changes restored.")
        else:
            print("  WARNING: could not restore stash. Run 'git stash pop' manually.")

    print(f"\n  Upgrade complete: v{old_ver} → v{new_ver}")
def cmd_status(args) -> None:
    record = _load_record()
    if not record["installs"]:
        print("No AITP installs on record.")
        print(f"  Record file: {RECORD_PATH}")
        return

    print(f"AITP Install Status (record at {RECORD_PATH})")
    print("=" * 60)

    for key, inst in record["installs"].items():
        agent, scope = key.split(":", 1)
        ts = inst.get("timestamp", "unknown")
        ver = inst.get("package_version", "unknown")
        print(f"\n  {agent} ({scope})")
        print(f"    Installed: {ts}")
        print(f"    Version:   {ver}")

        files = inst.get("files", [])
        missing = 0
        checked = 0
        for f in files:
            if str(f).startswith("- stale:"):
                continue
            f = f.split(" (")[0]
            checked += 1
            if not Path(f).exists():
                missing += 1
                print(f"    MISSING: {f}")
        if missing == 0:
            print(f"    Files: all present ({checked} items)")


def cmd_doctor(args) -> None:
    print("AITP Health Check")
    print("=" * 60)

    issues = []

    # 1. Python version
    py_ver = sys.version_info
    print(f"\n  Python: {py_ver.major}.{py_ver.minor}.{py_ver.micro}")
    if py_ver < (3, 10):
        issues.append("Python 3.10+ required")
        print("    FAIL: Python 3.10+ required")
    else:
        print("    OK")

    # 2. Strict v5/1.0.0 contract
    print("\n  AITP strict v5 contract:")
    strict_issues = _strict_v5_contract_issues()
    if strict_issues:
        issues.extend(strict_issues)
        print("    FAIL")
        for issue in strict_issues:
            print(f"      - {issue}")
    else:
        print(f"    OK (version {EXPECTED_PACKAGE_VERSION}, implementation {EXPECTED_IMPLEMENTATION})")

    # 3. Dependencies
    for dep in ("fastmcp", "yaml", "jsonschema"):
        try:
            __import__(dep)
            print(f"  {dep}: OK")
        except ImportError:
            # yaml is imported as pyyaml
            if dep == "yaml":
                try:
                    __import__("pyyaml")
                    print(f"  pyyaml: OK")
                    continue
                except ImportError:
                    pass
            issues.append(f"Missing dependency: {dep}")
            print(f"  {dep}: MISSING (pip install {dep})")

    # 4. Repo files
    print(f"\n  Repo root: {REPO_ROOT}")
    critical_files = [
        "brain/v5/native_mcp.py",
        "brain/v5/mcp_tools.py",
        "brain/v5/brief.py",
        "brain/v5/models.py",
        "brain/PROTOCOL.md",
    ]
    for f in critical_files:
        p = REPO_ROOT / f
        status = "OK" if p.exists() else "MISSING"
        if status == "MISSING":
            issues.append(f"Missing repo file: {f}")
        print(f"    {f}: {status}")
    legacy_files = ["brain/native_mcp.py", "brain/mcp_server.py", "brain/state_model.py"]
    for f in legacy_files:
        p = REPO_ROOT / f
        status = "present (compatibility)" if p.exists() else "absent"
        print(f"    {f}: {status}")

    # 4. Topics root
    topics_root = _detect_topics_root()
    print(f"\n  Topics root: {topics_root or 'NOT CONFIGURED'}")
    if not topics_root:
        issues.append("Topics root not configured")
        print("    FAIL: no topics root found")
    elif Path(topics_root).exists():
        topics_path = Path(topics_root)
        support_dirs = {".aitp", "L2"}
        topics = [
            d for d in topics_path.iterdir()
            if d.is_dir() and not d.name.startswith(".") and d.name not in support_dirs
        ]
        v5_topics_root = _v5_topics_root_for(topics_path)
        print(f"    OK ({len(topics)} topics)")
        # Content-level check: validate each topic's state.md
        healthy = 0
        invalid_state = 0
        broken_yaml = 0
        for topic_dir in sorted(topics):
            state_path = topic_dir / "state.md"
            if not state_path.exists():
                v5_topic_path = (v5_topics_root / topic_dir.name / "topic.md") if v5_topics_root else None
                if v5_topic_path and v5_topic_path.exists():
                    healthy += 1
                    print(f"    OK(v5): {topic_dir.name} topic.md")
                    continue
                invalid_state += 1
                issues.append(f"Topic '{topic_dir.name}': missing state.md")
                print(f"    INVALID: {topic_dir.name} — no state.md")
                continue
            try:
                text = state_path.read_text(encoding="utf-8")
                m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
                if not m:
                    invalid_state += 1
                    issues.append(f"Topic '{topic_dir.name}': state.md has no YAML frontmatter")
                    print(f"    INVALID: {topic_dir.name} — no frontmatter")
                    continue
                import yaml
                fm = yaml.safe_load(m.group(1)) or {}
                stage = fm.get("stage", "")
                posture = fm.get("posture", "")
                lane = fm.get("lane", "")
                if stage:
                    healthy += 1
                    print(f"    OK: {topic_dir.name} stage={stage} posture={posture} lane={lane}")
                else:
                    invalid_state += 1
                    issues.append(f"Topic '{topic_dir.name}': state.md missing 'stage' field")
                    print(f"    INVALID: {topic_dir.name} — no 'stage' field")
            except Exception:
                broken_yaml += 1
                issues.append(f"Topic '{topic_dir.name}': broken YAML in state.md")
                print(f"    BROKEN: {topic_dir.name} — YAML parse error")
        if healthy > 0:
            print(f"\n  Topic health: {healthy} healthy, {invalid_state} invalid, {broken_yaml} broken")
    else:
        issues.append(f"Topics root path does not exist: {topics_root}")
        print("    FAIL: path does not exist")

    record = _load_record()
    installs = record.get("installs", {})
    if installs:
        _doctor_check_recorded_installs(installs, issues)
        _print_doctor_summary(issues)
        return

    # 5. Claude Code
    print("\n  --- Claude Code ---")
    claude_dir = Path.home() / ".claude"
    settings_path = claude_dir / "settings.json"
    hooks_dir = claude_dir / "hooks"
    skills_dir = claude_dir / "skills"

    # Check hooks — auto-discovered from deploy sources
    expected_hooks = set()
    for _, dst_name in _discover_deploy_hooks():
        expected_hooks.add(dst_name)
    for _, dst_name in _discover_deploy_runners():
        expected_hooks.add(dst_name)
    for _, dst_name in _discover_deploy_config():
        expected_hooks.add(dst_name)
    for dst_name in sorted(expected_hooks):
        p = hooks_dir / dst_name
        status = "OK" if p.exists() else "MISSING"
        if status == "MISSING":
            issues.append(f"Claude Code hook missing: {dst_name}")
        print(f"    hooks/{dst_name}: {status}")

    # Check skills — auto-discovered from deploy sources
    for _, dst_rel in _discover_deploy_skills():
        p = skills_dir / dst_rel
        status = "OK" if p.exists() else "MISSING"
        if status == "MISSING":
            issues.append(f"Claude Code skill missing: {dst_rel}")
        print(f"    skills/{dst_rel}: {status}")

    # Check settings.json hooks
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            hooks = settings.get("hooks", {})
            hook_commands = [
                str(h.get("command", ""))
                for blocks in hooks.values()
                for block in blocks
                for h in block.get("hooks", [])
            ]
            has_v5_safe_hook = any(
                token in command
                for command in hook_commands
                for token in (
                    "aitp-keyword-router.py",
                    "aitp-routing-guard.py",
                    "aitp_v5_claude_hook.py",
                )
            )
            has_legacy_stage_hook = any(
                token in command
                for command in hook_commands
                for token in ("session-start", "aitp_get_execution_brief", "brain/mcp_server.py")
            )
            if not has_v5_safe_hook:
                issues.append("Claude Code v5-safe hook not configured")
            if has_legacy_stage_hook:
                issues.append("Claude Code settings.json still contains legacy stage hook command")
            print(f"    settings.json v5-safe hook: {'OK' if has_v5_safe_hook else 'NOT CONFIGURED'}")
            print(f"    settings.json legacy stage hooks: {'ABSENT' if not has_legacy_stage_hook else 'PRESENT'}")
        except (json.JSONDecodeError, OSError) as e:
            issues.append(f"Cannot parse settings.json: {e}")
            print(f"    settings.json: PARSE ERROR ({e})")
    else:
        issues.append("Claude Code settings.json not found")
        print("    settings.json: NOT FOUND")

    # 6. Kimi Code
    print("\n  --- Kimi Code ---")
    kimi_dir = Path.home() / ".kimi"
    agents_skills_dir = Path.home() / ".agents" / "skills"
    kimi_mcp = kimi_dir / "mcp.json"
    kimi_config = kimi_dir / "config.toml"

    # Check skills deployed to ~/.agents/skills/
    try:
        if agents_skills_dir.exists():
            for skill_name in ["using-aitp", "aitp-runtime"]:
                p = agents_skills_dir / skill_name / "SKILL.md"
                status = "OK" if p.exists() else "MISSING"
                if status == "MISSING":
                    issues.append(f"Kimi Code skill missing: {skill_name}/SKILL.md")
                print(f"    skills/{skill_name}/SKILL.md: {status}")
        else:
            print("    skills/: NOT FOUND (Kimi Code skills not deployed)")
    except OSError:
        print("    skills/: INACCESSIBLE (broken path, may need manual cleanup)")

    if kimi_mcp.exists():
        try:
            mcp = json.loads(kimi_mcp.read_text(encoding="utf-8"))
            has_aitp = "aitp" in mcp.get("mcpServers", {})
            status = "OK" if has_aitp else "NOT CONFIGURED"
            if not has_aitp:
                issues.append("Kimi Code mcp.json missing aitp entry")
        except (json.JSONDecodeError, OSError):
            status = "PARSE ERROR"
            issues.append("Cannot parse Kimi Code mcp.json")
        print(f"    mcp.json: {status}")
    else:
        print("    mcp.json: NOT FOUND (Kimi Code MCP not configured)")

    if kimi_config.exists():
        content = kimi_config.read_text(encoding="utf-8")
        has_aitp = "[mcp.servers.aitp]" in content
        status = "OK" if has_aitp else "NOT CONFIGURED"
        if not has_aitp:
            issues.append("Kimi Code config.toml missing [mcp.servers.aitp]")
        print(f"    config.toml [mcp.servers.aitp]: {status}")
    else:
        print("    config.toml: NOT FOUND")

    # 7. Codex App
    print("\n  --- Codex App ---")
    codex_roots = _discover_codex_skill_roots("user", None)
    required_codex_skills = ["using-aitp", "aitp-runtime"]
    found_codex_skill = {name: False for name in required_codex_skills}
    codex_mcp_ready = False
    codex_config_ready = False

    for root in codex_roots:
        root_status = "OK" if root.exists() else "NOT FOUND"
        print(f"    skill root {root}: {root_status}")
        for skill_name in required_codex_skills:
            p = root / skill_name / "SKILL.md"
            status = "OK" if p.exists() else "MISSING"
            if p.exists():
                found_codex_skill[skill_name] = True
            print(f"      {skill_name}/SKILL.md: {status}")

        mcp_path = root.parent / "mcp.json"
        if mcp_path.exists():
            try:
                data = json.loads(mcp_path.read_text(encoding="utf-8"))
                has_aitp = "aitp" in data.get("mcpServers", {})
                status = "OK" if has_aitp else "NOT CONFIGURED"
                codex_mcp_ready = codex_mcp_ready or has_aitp
            except (json.JSONDecodeError, OSError):
                status = "PARSE ERROR"
            print(f"      mcp.json: {status}")
        else:
            print("      mcp.json: NOT FOUND")

        config_path = root.parent / "config.toml"
        if config_path.exists():
            try:
                content = config_path.read_text(encoding="utf-8")
                has_aitp = "[mcp_servers.aitp]" in content
                has_v5 = _has_v5_mcp_entrypoint(content)
                has_legacy = _has_legacy_mcp_entrypoint(content)
                has_cwd = "cwd =" in content and has_v5 and not has_legacy
                status = "OK" if has_aitp and has_cwd else "NOT CONFIGURED"
                codex_config_ready = codex_config_ready or (has_aitp and has_cwd)
            except OSError:
                status = "READ ERROR"
            print(f"      config.toml [mcp_servers.aitp]: {status}")
        else:
            print("      config.toml: NOT FOUND")

    for skill_name, found in found_codex_skill.items():
        if not found:
            issues.append(f"Codex App skill missing: {skill_name}/SKILL.md")
    if not codex_config_ready:
        issues.append("Codex App config.toml missing [mcp_servers.aitp]")
    if not codex_mcp_ready:
        issues.append("Codex App compatibility mcp.json missing aitp entry")

    # 8. Summary
    _print_doctor_summary(issues)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AITP Package Manager — install, update, and manage AITP agent deployments",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # install
    p_install = sub.add_parser("install", help="Install AITP for one or more agents")
    p_install.add_argument("--agent", choices=AGENT_CHOICES, default="all")
    p_install.add_argument("--scope", choices=SCOPE_CHOICES, default=None)
    p_install.add_argument("--target-root", default=None, help="Project workspace root (for project scope)")
    p_install.add_argument("--topics-root", default=None, help="Override topics_root path")

    # uninstall
    p_uninstall = sub.add_parser("uninstall", help="Remove AITP from one or more agents")
    p_uninstall.add_argument("--agent", choices=AGENT_CHOICES, default="all")
    p_uninstall.add_argument("--scope", choices=SCOPE_CHOICES, default=None)
    p_uninstall.add_argument("--target-root", default=None)

    # update
    p_update = sub.add_parser("update", help="Re-sync AITP from repo to all installed agents")
    p_update.add_argument("--agent", choices=AGENT_CHOICES, default="all")
    p_update.add_argument("--topics-root", default=None)

    # upgrade
    p_upgrade = sub.add_parser("upgrade", help="Git pull latest + re-deploy all agents")
    p_upgrade.add_argument("--force", action="store_true", help="Stash uncommitted changes and proceed")

    # status
    sub.add_parser("status", help="Show installed agents and file drift")

    # doctor
    sub.add_parser("doctor", help="Full health check for all AITP components")

    args = parser.parse_args()

    cmd_map = {
        "install": cmd_install,
        "uninstall": cmd_uninstall,
        "update": cmd_update,
        "upgrade": cmd_upgrade,
        "status": cmd_status,
        "doctor": cmd_doctor,
    }

    cmd_map[args.command](args)


if __name__ == "__main__":
    main()
