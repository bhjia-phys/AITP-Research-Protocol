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
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = REPO_ROOT / "deploy" / "templates"
INSTALL_DIR = Path.home() / ".aitp"
RECORD_PATH = INSTALL_DIR / "install-record.json"

AGENT_CHOICES = ("claude-code", "kimi-code", "all")
SCOPE_CHOICES = ("user", "project")

# ---------------------------------------------------------------------------
# CLI wrapper registration (avoids pip install -e .)
# ---------------------------------------------------------------------------


def _find_path_dir() -> Path | None:
    """Find a writable directory already in PATH where we can place a wrapper."""
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)

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

    for c in candidates:
        try:
            c_resolved = c.resolve()
            if c_resolved.exists() and str(c_resolved) in [Path(p).resolve().as_posix() for p in path_dirs if p]:
                if os.access(str(c_resolved), os.W_OK):
                    return c_resolved
        except OSError:
            continue

    # Fallback: first writable dir in PATH
    for p in path_dirs:
        try:
            pp = Path(p).resolve()
            if pp.exists() and os.access(str(pp), os.W_OK):
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


# ---------------------------------------------------------------------------
# Template & variable helpers
# ---------------------------------------------------------------------------


def _build_variables(topics_root: str | None = None, target_root: str | None = None) -> dict:
    return {
        "REPO_ROOT": str(REPO_ROOT).replace("\\", "/"),
        "TOPICS_ROOT": (topics_root or "").replace("\\", "/"),
        "TARGET_ROOT": (target_root or "").replace("\\", "/"),
        "USER_HOME": str(Path.home()).replace("\\", "/"),
        "CLAUDE_USER_DIR": str(Path.home() / ".claude").replace("\\", "/"),
        "KIMI_USER_DIR": str(Path.home() / ".kimi").replace("\\", "/"),
        "AGENTS_SKILLS_DIR": str(Path.home() / ".agents" / "skills").replace("\\", "/"),
    }


def _fill(text: str, variables: dict) -> str:
    for k, v in variables.items():
        text = text.replace("{{" + k + "}}", v)
    return text


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
    """Add or remove AITP hooks from Claude Code settings.json."""
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            settings = {}
    else:
        settings = {}

    hooks_dir = variables["CLAUDE_USER_DIR"].replace("\\", "/") + "/hooks"
    aitp_hooks = {
        "SessionStart": [
            {
                "matcher": "startup|clear|compact",
                "hooks": [
                    {
                        "type": "command",
                        "command": f'"{hooks_dir}/run-hook.cmd" session-start',
                        "async": False,
                    }
                ],
            }
        ],
        "UserPromptSubmit": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": f'python "{hooks_dir}/aitp-keyword-router.py"',
                        "async": False,
                    }
                ],
            }
        ],
        "PreToolUse": [
            {
                "matcher": "Write|Edit",
                "hooks": [
                    {
                        "type": "command",
                        "command": f'python "{hooks_dir}/aitp-routing-guard.py"',
                        "async": False,
                    }
                ],
            }
        ],
    }

    existing_hooks = settings.setdefault("hooks", {})

    def _normalize(cmd: str) -> str:
        return cmd.replace("\\", "/").lower()

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
                    _normalize(h.get("command", "")) in aitp_cmds for h in block.get("hooks", [])
                )
            ]
            filtered.extend(aitp_entries)
            existing_hooks[event_name] = filtered

    _atomic_write(settings_path, json.dumps(settings, indent=2, ensure_ascii=False))


def _write_mcp_json(mcp_path: Path, repo_root: str, topics_root: str = "", remove: bool = False) -> None:
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
        entry = {
            "command": "python",
            "args": [f"{repo_root}/brain/mcp_server.py"],
            "cwd": repo_root,
        }
        if topics_root:
            entry["env"] = {"AITP_TOPICS_ROOT": topics_root}
        servers["aitp"] = entry

    if data:
        _atomic_write(mcp_path, json.dumps(data, indent=2, ensure_ascii=False))
    elif mcp_path.exists():
        mcp_path.unlink()


def _merge_kimi_config_toml(config_path: Path, repo_root: str, remove: bool = False) -> None:
    """Add or remove [mcp.servers.aitp] section from Kimi Code config.toml."""
    if not config_path.exists():
        if not remove:
            content = ""
        else:
            return
    else:
        content = config_path.read_text(encoding="utf-8")

    section_header = '[mcp.servers.aitp]'
    section_block = (
        f'{section_header}\n'
        f'command = "python"\n'
        f'args = ["{repo_root}/brain/mcp_server.py"]\n'
    )

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


# ---------------------------------------------------------------------------
# Deploy: Claude Code
# ---------------------------------------------------------------------------

# Source hooks (in repo) → deployed name. Auto-discovered from hooks/.
_HOOK_COPIES = [
    (f"hooks/{p.name}", p.stem.replace("_", "-") + ".py")
    for p in sorted((REPO_ROOT / "hooks").glob("*.py"))
    if p.name != "__init__.py"
]

# Template files → deployed name. Auto-discovered from deploy/templates/claude-code/.
# Non-skill, non-markdown files (cmd, sh, json, py — excluding skill files).
_HOOK_TEMPLATES = [
    (f"claude-code/{p.name}", p.stem.replace("_", "-") + p.suffix if p.suffix == ".py" else p.name)
    for p in sorted((TEMPLATES_DIR / "claude-code").iterdir())
    if p.suffix in (".cmd", ".sh", ".json", ".py")
    and "using-aitp" not in p.stem
    and "aitp-runtime" not in p.stem
    and "aitp-mcp-setup" not in p.stem
]

_SKILL_TEMPLATES = [
    (f"claude-code/{p.name}", f"{p.stem}/SKILL.md")
    for p in sorted((TEMPLATES_DIR / "claude-code").iterdir())
    if p.suffix == ".md" and p.name.startswith("using-aitp") or p.name.startswith("aitp-runtime")
] + [
    (f"claude-code/{p.name}", f"aitp-runtime/{p.name.upper()}")
    for p in sorted((TEMPLATES_DIR / "claude-code").iterdir())
    if p.suffix == ".md" and p.name.startswith("aitp-mcp-setup")
]

_KIMI_SKILL_TEMPLATES = [
    ("kimi-code/using-aitp.md", "using-aitp/SKILL.md"),
    ("kimi-code/aitp-runtime.md", "aitp-runtime/SKILL.md"),
]


def _deploy_claude_code(
    scope: str, target_root: Path | None, variables: dict, remove: bool = False
) -> list[str]:
    """Install or uninstall AITP for Claude Code. Returns list of deployed/removed paths."""
    if scope == "user":
        base = Path(variables["CLAUDE_USER_DIR"])
    else:
        base = target_root / ".claude" if target_root else Path.cwd() / ".claude"

    hooks_dir = base / "hooks"
    skills_dir = base / "skills"
    deployed: list[str] = []

    if remove:
        # Remove hook files
        for _, dst_name in _HOOK_COPIES + _HOOK_TEMPLATES:
            p = hooks_dir / dst_name
            if p.exists():
                p.unlink()
                deployed.append(f"- {p}")

        # Remove skill files
        for _, dst_rel in _SKILL_TEMPLATES:
            p = skills_dir / dst_rel
            if p.exists():
                p.unlink()
                deployed.append(f"- {p}")

        # Clean empty dirs
        for d in [skills_dir / "using-aitp", skills_dir / "aitp-runtime", skills_dir, hooks_dir]:
            try:
                if d.exists() and not list(d.iterdir()):
                    d.rmdir()
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

        # Remove project .mcp.json
        if scope == "project":
            mcp_path = (target_root or Path.cwd()) / ".mcp.json"
            _write_mcp_json(mcp_path, variables["REPO_ROOT"], variables.get("TOPICS_ROOT", ""), remove=True)
            deployed.append(f"~ {mcp_path} (aitp entry removed)")

        return deployed

    # --- Install ---
    print(f"  Deploying hooks to {hooks_dir}/")
    hooks_dir.mkdir(parents=True, exist_ok=True)

    # Copy repo hooks with repo-path injection
    for src_rel, dst_name in _HOOK_COPIES:
        src = REPO_ROOT / src_rel
        if not src.exists():
            print(f"    WARNING: source not found: {src_rel}")
            continue
        content = src.read_text(encoding="utf-8")
        if "from brain." in content or "import brain." in content:
            inject = f'sys.path.insert(0, r"{variables["REPO_ROOT"]}")\n'
            if inject.strip() not in content:
                content = content.replace(
                    "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))",
                    f'sys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n{inject}',
                )
        dst = hooks_dir / dst_name
        _atomic_write(dst, content)
        deployed.append(str(dst))

    # Generate from templates
    for tmpl_rel, dst_name in _HOOK_TEMPLATES:
        content = _read_template(tmpl_rel)
        if content is None:
            print(f"    WARNING: template not found: {tmpl_rel}")
            continue
        dst = hooks_dir / dst_name
        _atomic_write(dst, _fill(content, variables))
        deployed.append(str(dst))

    print(f"  Deploying skills to {skills_dir}/")
    for tmpl_rel, dst_rel in _SKILL_TEMPLATES:
        content = _read_template(tmpl_rel)
        if content is None:
            print(f"    WARNING: template not found: {tmpl_rel}")
            continue
        dst = skills_dir / dst_rel
        _atomic_write(dst, _fill(content, variables))
        deployed.append(str(dst))

    # Merge settings.json
    if scope == "user":
        settings_path = base / "settings.json"
        _merge_claude_settings(settings_path, variables)
        deployed.append(f"{settings_path} (hooks merged)")
    else:
        # Project scope: write settings.json with hooks
        settings_path = base / "settings.json"
        hooks_dir_str = str(base / "hooks").replace("\\", "/")
        project_settings = {
            "hooks": {
                "SessionStart": [
                    {
                        "matcher": "startup|clear|compact",
                        "hooks": [
                            {
                                "type": "command",
                                "command": f'"{hooks_dir_str}/run-hook.cmd" session-start',
                                "async": False,
                            }
                        ],
                    }
                ],
            }
        }
        _atomic_write(settings_path, json.dumps(project_settings, indent=2, ensure_ascii=False))
        deployed.append(str(settings_path))

        # Write .mcp.json for project
        mcp_path = (target_root or Path.cwd()) / ".mcp.json"
        _write_mcp_json(mcp_path, variables["REPO_ROOT"], variables.get("TOPICS_ROOT", ""))
        deployed.append(str(mcp_path))

    return deployed


# ---------------------------------------------------------------------------
# Deploy: Kimi Code
# ---------------------------------------------------------------------------


def _deploy_kimi_code(
    scope: str, target_root: Path | None, variables: dict, remove: bool = False
) -> list[str]:
    """Install or uninstall AITP for Kimi Code."""
    # Kimi Code scans ~/.agents/skills/ for skills
    skills_dir = Path.home() / ".agents" / "skills"

    # MCP config lives in ~/.kimi/ (both user and project scope use user-level config for now)
    mcp_base = Path.home() / ".kimi"

    deployed: list[str] = []

    if remove:
        # Remove skill files from ~/.agents/skills/
        for _, dst_rel in _KIMI_SKILL_TEMPLATES:
            p = skills_dir / dst_rel
            if p.exists():
                p.unlink()
                deployed.append(f"- {p}")

        # Clean empty dirs
        for d in [skills_dir / "using-aitp", skills_dir / "aitp-runtime"]:
            try:
                if d.exists() and not list(d.iterdir()):
                    d.rmdir()
            except OSError:
                pass

        # mcp.json
        mcp_path = mcp_base / "mcp.json"
        _write_mcp_json(mcp_path, variables["REPO_ROOT"], remove=True)
        deployed.append(f"~ {mcp_path} (aitp entry removed)")

        # config.toml
        config_path = mcp_base / "config.toml"
        _merge_kimi_config_toml(config_path, variables["REPO_ROOT"], remove=True)
        deployed.append(f"~ {config_path} ([mcp.servers.aitp] removed)")

        return deployed

    # --- Install ---
    print(f"  Deploying skills to {skills_dir}/")
    skills_dir.mkdir(parents=True, exist_ok=True)
    for tmpl_rel, dst_rel in _KIMI_SKILL_TEMPLATES:
        content = _read_template(tmpl_rel)
        if content is None:
            print(f"    WARNING: template not found: {tmpl_rel}")
            continue
        dst = skills_dir / dst_rel
        _atomic_write(dst, _fill(content, variables))
        deployed.append(str(dst))

    # mcp.json
    mcp_path = mcp_base / "mcp.json"
    _write_mcp_json(mcp_path, variables["REPO_ROOT"], variables.get("TOPICS_ROOT", ""))
    deployed.append(f"{mcp_path} (aitp entry written)")

    # config.toml
    config_path = mcp_base / "config.toml"
    _merge_kimi_config_toml(config_path, variables["REPO_ROOT"])
    deployed.append(f"{config_path} ([mcp.servers.aitp] merged)")

    return deployed


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_install(args) -> None:
    agents = AGENT_CHOICES[:-1] if args.agent == "all" else [args.agent]
    scope = args.scope or "user"
    target_root = Path(args.target_root) if args.target_root else None

    topics_root = args.topics_root or _detect_topics_root()
    if not topics_root:
        topics_root = _prompt_topics_root()

    variables = _build_variables(topics_root)
    record = _load_record()

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
        else:
            print(f"  Unknown agent: {agent}")
            continue

        key = _record_key(agent, scope)
        record["installs"][key] = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "package_version": pkg_ver,
            "variables": {k: v for k, v in variables.items()},
            "files": paths,
        }

        for p in paths:
            print(f"  + {p}")
        print(f"  Done. {len(paths)} items deployed.")

    _save_record(record)
    print(f"\nInstall record saved to {RECORD_PATH}")

    # Register 'aitp' CLI wrapper
    wrapper = _register_cli()
    if wrapper:
        print(f"  CLI registered: {wrapper}")
    else:
        print("  WARNING: could not auto-register 'aitp' command (no writable PATH dir found)")


def cmd_uninstall(args) -> None:
    agents = AGENT_CHOICES[:-1] if args.agent == "all" else [args.agent]
    scope = args.scope or "user"
    target_root = Path(args.target_root) if args.target_root else None

    record = _load_record()
    variables = _build_variables()

    for agent in agents:
        print(f"\n=== Uninstalling AITP for {agent} ({scope} scope) ===")
        if agent == "claude-code":
            paths = _deploy_claude_code(scope, target_root, variables, remove=True)
        elif agent == "kimi-code":
            paths = _deploy_kimi_code(scope, target_root, variables, remove=True)
        else:
            continue

        key = _record_key(agent, scope)
        record["installs"].pop(key, None)

        for p in paths:
            print(f"  {p}")
        print(f"  Done. {len(paths)} items removed.")

    _save_record(record)
    _unregister_cli()
    print("  CLI wrapper removed.")


def cmd_update(args) -> None:
    agents = AGENT_CHOICES[:-1] if args.agent == "all" else [args.agent]

    record = _load_record()
    if not record["installs"]:
        print("No AITP installs found. Run 'install' first.")
        return

    topics_root = args.topics_root or _detect_topics_root()
    if not topics_root:
        topics_root = _prompt_topics_root()

    variables = _build_variables(topics_root)

    pkg_file = REPO_ROOT / "package.json"
    try:
        pkg_ver = json.loads(pkg_file.read_text(encoding="utf-8")).get("version", "unknown")
    except (OSError, json.JSONDecodeError):
        pkg_ver = "unknown"

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

            print(f"\n=== Updating AITP for {agent} ({scope} scope) ===")
            if agent == "claude-code":
                paths = _deploy_claude_code(scope, target_root, variables, remove=False)
            elif agent == "kimi-code":
                paths = _deploy_kimi_code(scope, target_root, variables, remove=False)
            else:
                continue

            record["installs"][key] = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "package_version": pkg_ver,
                "variables": {k: v for k, v in variables.items()},
                "files": paths,
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
    variables = _build_variables(topics_root)

    for key in list(record["installs"]):
        agent, scope = key.split(":", 1)
        target_root = None
        if scope == "project":
            tr = record["installs"][key].get("variables", {}).get("TARGET_ROOT")
            if tr:
                target_root = Path(tr)

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
            "files": paths,
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

        # Check file drift
        files = inst.get("files", [])
        changed = 0
        missing = 0
        for f in files:
            f = f.split(" (")[0]  # Remove annotation
            p = Path(f)
            if not p.exists():
                missing += 1
                print(f"    MISSING: {f}")
            elif "(merged)" not in f and "(removed)" not in f:
                # Could compare content hash but that requires storing hashes
                pass
        if missing == 0 and changed == 0:
            print(f"    Files: all present ({len(files)} items)")


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
        for f in files:
            f = f.split(" (")[0]
            if not Path(f).exists():
                missing += 1
                print(f"    MISSING: {f}")
        if missing == 0:
            print(f"    Files: all present ({len(files)} items)")


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

    # 2. Dependencies
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

    # 3. Repo files
    print(f"\n  Repo root: {REPO_ROOT}")
    critical_files = [
        "brain/mcp_server.py",
        "brain/state_model.py",
        "brain/PROTOCOL.md",
    ]
    for f in critical_files:
        p = REPO_ROOT / f
        status = "OK" if p.exists() else "MISSING"
        if status == "MISSING":
            issues.append(f"Missing repo file: {f}")
        print(f"    {f}: {status}")

    # 4. Topics root
    topics_root = _detect_topics_root()
    print(f"\n  Topics root: {topics_root or 'NOT CONFIGURED'}")
    if not topics_root:
        issues.append("Topics root not configured")
        print("    FAIL: no topics root found")
    elif Path(topics_root).exists():
        topics = list(Path(topics_root).iterdir())
        print(f"    OK ({len([d for d in topics if d.is_dir()])} topics)")
    else:
        issues.append(f"Topics root path does not exist: {topics_root}")
        print("    FAIL: path does not exist")

    # 5. Claude Code
    print("\n  --- Claude Code ---")
    claude_dir = Path.home() / ".claude"
    settings_path = claude_dir / "settings.json"
    hooks_dir = claude_dir / "hooks"
    skills_dir = claude_dir / "skills"

    # Check hooks — auto-discovered from expected deploy set
    expected_hooks = set()
    for src_rel, dst_name in _HOOK_COPIES:
        expected_hooks.add(dst_name)
    for tmpl_rel, dst_name in _HOOK_TEMPLATES:
        expected_hooks.add(dst_name)
    for dst_name in sorted(expected_hooks):
        p = hooks_dir / dst_name
        status = "OK" if p.exists() else "MISSING"
        if status == "MISSING":
            issues.append(f"Claude Code hook missing: {dst_name}")
        print(f"    hooks/{dst_name}: {status}")

    # Check skills — auto-discovered from expected deploy set
    for src_rel, dst_rel in _SKILL_TEMPLATES:
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
            aitp_events = ["SessionStart", "UserPromptSubmit", "PreToolUse"]
            for event in aitp_events:
                has_aitp = any(
                    "aitp" in str(h.get("command", "")).lower() or
                    "run-hook" in str(h.get("command", ""))
                    for block in hooks.get(event, [])
                    for h in block.get("hooks", [])
                )
                status = "OK" if has_aitp else "NOT CONFIGURED"
                if not has_aitp:
                    issues.append(f"Claude Code {event} hook not configured")
                print(f"    settings.json hooks.{event}: {status}")
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
    for skill_file in ["using-aitp/SKILL.md", "aitp-runtime/SKILL.md"]:
        p = agents_skills_dir / skill_file
        status = "OK" if p.exists() else "MISSING"
        if status == "MISSING":
            issues.append(f"Kimi Code skill missing: {skill_file}")
        print(f"    skills/{skill_file}: {status}")

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

    # 7. Summary
    print(f"\n{'=' * 60}")
    if issues:
        print(f"  {len(issues)} issue(s) found:")
        for i, issue in enumerate(issues, 1):
            print(f"    {i}. {issue}")
        print(f"\n  Run: python scripts/aitp-pm.py install --agent all")
    else:
        print("  All checks passed. AITP is healthy.")


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
