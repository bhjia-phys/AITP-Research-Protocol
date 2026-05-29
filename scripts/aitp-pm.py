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

AGENTS = ("claude-code", "kimi-code", "codex")
AGENT_CHOICES = (*AGENTS, "all")
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
        "CODEX_USER_DIR": str(Path.home() / ".codex").replace("\\", "/"),
        "CODEX_HOME_DIR": str(Path.home() / ".codex-home").replace("\\", "/"),
        "CODEX_SWITCHER_SKILLS_DIR": str(Path.home() / ".codex-switcher" / "skills").replace("\\", "/"),
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
        # Fallback: hardcoded minimum
        hooks_dir = variables["CLAUDE_USER_DIR"].replace("\\", "/") + "/hooks"
        aitp_hooks = {
            "SessionStart": [{
                "matcher": "startup|clear|compact",
                "hooks": [{
                    "type": "command",
                    "command": f'"{hooks_dir}/run-hook.cmd" session-start',
                    "async": False,
                }],
            }],
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

    # Merge AITP MCP server into settings.json (Claude Code reads MCP from here)
    if not remove:
        repo_root_var = variables["REPO_ROOT"]
        topics_root_var = variables.get("TOPICS_ROOT", "")
        mcp_entry = {
            "command": "python",
            "args": [f"{repo_root_var}/brain/native_mcp.py"],
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
                    f"{repo_root}/brain/native_mcp.py",
                ],
                "cwd": repo_root,
            }
        else:
            entry = {
                "command": "python",
                "args": [f"{repo_root}/brain/native_mcp.py"],
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
            f"{repo_root}/brain/native_mcp.py",
        ]
    else:
        command = "python"
        args = [f"{repo_root}/brain/native_mcp.py"]

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
        f'args = ["{repo_root}/brain/native_mcp.py"]\n'
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

    # Protocol skills from repo skills/ (plain, no template vars)
    repo_skills_dir = REPO_ROOT / "skills"
    if repo_skills_dir.is_dir():
        for p in sorted(repo_skills_dir.glob("*.md")):
            name = p.stem
            if name not in seen:
                seen.add(name)
                results.append((p, f"{name}/SKILL.md"))

    return results


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
    repo_hooks_dir = REPO_ROOT / "hooks"
    if repo_hooks_dir.is_dir():
        for p in sorted(repo_hooks_dir.iterdir()):
            if p.name == "__init__.py" or p.suffix == ".pyc":
                continue
            if p.is_file():
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
    runners_dir = REPO_ROOT / "deploy" / "runners"
    if not runners_dir.is_dir():
        return []
    return [
        (p, p.name)
        for p in sorted(runners_dir.iterdir())
        if p.suffix in (".cmd", ".sh")
    ]


def _discover_deploy_config() -> list[tuple[Path, str]]:
    """Discover config files (.json) from deploy/config/."""
    config_dir = REPO_ROOT / "deploy" / "config"
    if not config_dir.is_dir():
        return []
    return [
        (p, p.name)
        for p in sorted(config_dir.iterdir())
        if p.suffix == ".json"
    ]


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
    for src, dst_name in all_configs:
        if not src.exists():
            continue
        content = _fill(src.read_text(encoding="utf-8"), variables)
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

    # 5. Sync protocol skills to workspace skills-shared/ (flat .md files)
    ws_skills = _discover_workspace_skills_root()
    if ws_skills:
        deployed_ws = 0
        repo_skills_dir = REPO_ROOT / "skills"
        if repo_skills_dir.is_dir():
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
        project_vars = {**variables, "CLAUDE_USER_DIR": str(base).replace("\\", "/")}
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
            project_hooks = {
                "SessionStart": [{
                    "matcher": "startup|clear|compact",
                    "hooks": [{
                        "type": "command",
                        "command": f'"{hooks_dir_str}/run-hook.cmd" session-start',
                        "async": False,
                    }],
                }],
            }
        project_settings = {"hooks": project_hooks}
        _atomic_write(settings_path, json.dumps(project_settings, indent=2, ensure_ascii=False))
        deployed.append(str(settings_path))

        mcp_path = (target_root or Path.cwd()) / ".mcp.json"
        _write_mcp_json(mcp_path, variables["REPO_ROOT"], variables.get("TOPICS_ROOT", ""))
        deployed.append(str(mcp_path))

    # 7. Clean up stale AITP files (deployed files with no matching source)
    # Only remove files that match AITP naming patterns to avoid touching
    # skills/hooks installed by other tools.
    _AITP_HOOK_PREFIXES = ("aitp-", "hook-", "compact", "session-start", "stop")
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
    # Kimi Code scans ~/.agents/skills/ for skills (directory-per-skill format)
    skills_dir = Path.home() / ".agents" / "skills"
    mcp_base = Path.home() / ".kimi"

    # Gateway skills for Kimi Code (only the essential entry + runtime)
    gateway_skills = [
        ("using-aitp", "using-aitp/SKILL.md"),
        ("aitp-runtime", "aitp-runtime/SKILL.md"),
    ]

    deployed: list[str] = []

    if remove:
        for skill_name, dst_rel in gateway_skills:
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
            print(f"    SKIP {dst_rel} (cannot write to {dst.parent} — junction/mount point)")

    mcp_path = mcp_base / "mcp.json"
    _write_mcp_json(mcp_path, variables["REPO_ROOT"], variables.get("TOPICS_ROOT", ""))
    deployed.append(f"{mcp_path} (aitp entry written)")

    config_path = mcp_base / "config.toml"
    _merge_kimi_config_toml(config_path, variables["REPO_ROOT"])
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
    if repo_skills_dir.is_dir():
        for src in sorted(repo_skills_dir.glob("*.md")):
            name = src.stem
            if name in seen:
                continue
            results.append((src, name, False))
            seen.add(name)

    return results


def _deploy_codex_app(
    scope: str, target_root: Path | None, variables: dict, remove: bool = False
) -> list[str]:
    """Install or uninstall AITP for Codex app.

    Codex app has native skill discovery but no Claude-style hooks. The adapter
    therefore deploys Codex-native gateway skills plus wrapped protocol skills,
    and writes MCP config into both the legacy mcp.json location and Codex's
    config.toml [mcp_servers.aitp] surface.
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

    return deployed


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_install(args) -> None:
    agents = AGENTS if args.agent == "all" else [args.agent]
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
    agents = AGENTS if args.agent == "all" else [args.agent]
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

    variables = _build_variables(topics_root)

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
        "brain/native_mcp.py",
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
        topics = [d for d in Path(topics_root).iterdir() if d.is_dir()]
        print(f"    OK ({len(topics)} topics)")
        # Content-level check: validate each topic's state.md
        healthy = 0
        invalid_state = 0
        broken_yaml = 0
        for topic_dir in sorted(topics):
            state_path = topic_dir / "state.md"
            if not state_path.exists():
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
                has_cwd = "cwd =" in content and "brain/native_mcp.py" in content
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
