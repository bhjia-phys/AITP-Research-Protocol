from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_executable_text(path: Path, text: str) -> None:
    _write_text(path, text)
    try:
        path.chmod(path.stat().st_mode | 0o111)
    except OSError:
        pass


def agent_hidden_root(
    *,
    target_root: str | None,
    scope: str,
    hidden_dir: str,
    user_root: Path,
    project_root: Path,
) -> Path:
    if target_root:
        target_path = Path(target_root)
        if target_path.name == hidden_dir:
            return target_path
        return target_path / hidden_dir
    if scope == "project":
        return project_root
    return user_root


def openclaw_skill_target(service: Any, *, scope: str, target_root: str | None) -> Path:
    if target_root:
        target_path = Path(target_root)
        if target_path.name == "aitp-runtime" or target_path.parent.name == "skills":
            return target_path
        return target_path / "skills" / "aitp-runtime"
    if scope == "project":
        return service.repo_root / "skills" / "aitp-runtime"
    return Path.home() / ".openclaw" / "skills" / "aitp-runtime"


def install_codex_mcp(service: Any, *, force: bool, mcp_profile: str = "full") -> list[dict[str, str]]:
    codex = shutil.which("codex")
    if codex is None:
        raise FileNotFoundError("Codex CLI is not installed or not on PATH.")

    server_name = service._mcp_server_name(mcp_profile)
    get_cmd = [codex, "mcp", "get", server_name]
    exists = subprocess.run(get_cmd, check=False, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if exists.returncode == 0:
        if not force:
            return [{"agent": "codex", "path": str(Path.home() / ".codex" / "config.toml"), "kind": "mcp-server"}]
        subprocess.run(
            [codex, "mcp", "remove", server_name],
            check=False,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
        )

    add_cmd = [codex, "mcp", "add", server_name]
    for key, value in service._mcp_environment(mcp_profile=mcp_profile).items():
        add_cmd.extend(["--env", f"{key}={value}"])
    add_cmd.extend(["--", *service._resolve_aitp_mcp_command()])
    service._run(add_cmd)
    return [{"agent": "codex", "path": str(Path.home() / ".codex" / "config.toml"), "kind": "mcp-server"}]


def install_openclaw_mcp(
    service: Any,
    *,
    force: bool,
    scope: str,
    mcp_profile: str = "full",
) -> list[dict[str, str]]:
    mcporter = shutil.which("mcporter")
    if mcporter is None:
        raise FileNotFoundError("mcporter is not installed or not on PATH.")

    server_name = service._mcp_server_name(mcp_profile)
    if force:
        subprocess.run(
            [mcporter, "config", "remove", server_name],
            check=False,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
        )

    command = [mcporter, "config", "add", server_name, "--command", service._resolve_aitp_mcp_command()[0]]
    for arg in service._resolve_aitp_mcp_command()[1:]:
        command.extend(["--arg", arg])
    for key, value in service._mcp_environment(mcp_profile=mcp_profile).items():
        command.extend(["--env", f"{key}={value}"])
    command.extend(["--scope", "home" if scope == "user" else "project"])
    service._run(command)
    return [{"agent": "openclaw", "path": f"mcporter:{scope}:{server_name}", "kind": "mcp-server"}]


def install_opencode_mcp(
    service: Any,
    *,
    force: bool,
    scope: str,
    target_root: str | None,
    mcp_profile: str = "full",
) -> list[dict[str, str]]:
    server_name = service._mcp_server_name(mcp_profile)
    if target_root:
        base = agent_hidden_root(
            target_root=target_root,
            scope=scope,
            hidden_dir=".opencode",
            user_root=Path.home() / ".config" / "opencode",
            project_root=service.repo_root / ".opencode",
        )
        sidecar_path = base / "AITP_MCP_CONFIG.json"
        project_config_path = base / "opencode.json"
        mcp_payload = {"mcp": {server_name: service._opencode_mcp_entry(mcp_profile=mcp_profile)}}
        service._write_json_file(sidecar_path, mcp_payload)
        if project_config_path.exists():
            project_payload = json.loads(project_config_path.read_text(encoding="utf-8"))
        else:
            project_payload = {"$schema": "https://opencode.ai/config.json"}
        mcp_config = project_payload.setdefault("mcp", {})
        mcp_config[server_name] = service._opencode_mcp_entry(mcp_profile=mcp_profile)
        service._write_json_file(project_config_path, project_payload)
        return [
            {"agent": "opencode", "path": str(sidecar_path), "kind": "mcp-config"},
            {"agent": "opencode", "path": str(project_config_path), "kind": "mcp-config"},
        ]

    if scope == "project":
        config_path = service.repo_root / ".opencode" / "opencode.json"
    else:
        config_path = Path.home() / ".config" / "opencode" / "opencode.json"

    if config_path.exists():
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        payload = {"$schema": "https://opencode.ai/config.json"}

    mcp_payload = payload.setdefault("mcp", {})
    if server_name in mcp_payload and not force:
        raise FileExistsError(f"Refusing to overwrite existing OpenCode MCP server at {config_path}")
    mcp_payload[server_name] = service._opencode_mcp_entry(mcp_profile=mcp_profile)
    service._write_json_file(config_path, payload)
    return [{"agent": "opencode", "path": str(config_path), "kind": "mcp-config"}]


def install_claude_mcp(
    service: Any,
    *,
    force: bool,
    scope: str,
    target_root: str | None,
    mcp_profile: str = "full",
) -> list[dict[str, str]]:
    server_name = service._mcp_server_name(mcp_profile)
    if target_root:
        target_path = Path(target_root)
        fake_home = target_path.parent if target_path.name == ".claude" else target_path
        if scope == "project":
            config_path = fake_home / ".mcp.json"
        else:
            config_path = fake_home / ".claude.json"
    elif scope == "project":
        config_path = service.repo_root / ".mcp.json"
    else:
        config_path = Path.home() / ".claude.json"

    if config_path.exists():
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object in {config_path}")
    else:
        payload = {}

    mcp_payload = payload.setdefault("mcpServers", {})
    if not isinstance(mcp_payload, dict):
        raise ValueError(f"Expected `mcpServers` object in {config_path}")
    if server_name in mcp_payload and not force:
        raise FileExistsError(f"Refusing to overwrite existing Claude Code MCP server at {config_path}")

    mcp_payload[server_name] = service._claude_mcp_entry(mcp_profile=mcp_profile)
    service._write_json_file(config_path, payload)
    return [{"agent": "claude-code", "path": str(config_path), "kind": "mcp-config"}]


def opencode_plugin_template() -> str:
    return r"""/**
 * AITP plugin for OpenCode
 *
 * Injects the using-aitp bootstrap and registers the local AITP skills path.
 */

import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const extractAndStripFrontmatter = (content) => {
  const match = content.match(/^---\\n([\\s\\S]*?)\\n---\\n([\\s\\S]*)$/);
  if (!match) return { frontmatter: {}, content };

  const frontmatterStr = match[1];
  const body = match[2];
  const frontmatter = {};

  for (const line of frontmatterStr.split('\\n')) {
    const colonIdx = line.indexOf(':');
    if (colonIdx > 0) {
      const key = line.slice(0, colonIdx).trim();
      const value = line.slice(colonIdx + 1).trim().replace(/^[\"']|[\"']$/g, '');
      frontmatter[key] = value;
    }
  }

  return { frontmatter, content: body };
};

const resolveSkillsDir = () => {
  const candidates = [
    path.resolve(__dirname, '../../skills'),
    path.resolve(__dirname, '../skills'),
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(path.join(candidate, 'using-aitp', 'SKILL.md'))) {
      return candidate;
    }
  }
  return candidates[0];
};

const getBootstrapContent = () => {
  const skillsDir = resolveSkillsDir();
  const skillPath = path.join(skillsDir, 'using-aitp', 'SKILL.md');
  if (!fs.existsSync(skillPath)) return null;

  const fullContent = fs.readFileSync(skillPath, 'utf8');
  const { content } = extractAndStripFrontmatter(fullContent);
  const toolMapping = `**Tool Mapping for OpenCode:**\\n- \`TodoWrite\` -> \`todowrite\`\\n- \`Skill\` tool -> OpenCode's native \`skill\` tool\\n- File operations and shell calls -> native OpenCode tools\\n\\n**AITP skills location:**\\n\`${skillsDir}\``;

  return `<EXTREMELY_IMPORTANT>\\nYou are in an AITP-enabled OpenCode session.\\n\\n**IMPORTANT: The using-aitp skill content is included below and is already loaded. Do not load using-aitp again.**\\n\\n${content}\\n\\n${toolMapping}\\n</EXTREMELY_IMPORTANT>`;
};

export const AITPPlugin = async () => {
  const skillsDir = resolveSkillsDir();

  return {
    config: async (config) => {
      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];
      if (!config.skills.paths.includes(skillsDir)) {
        config.skills.paths.push(skillsDir);
      }
    },

    'experimental.chat.system.transform': async (_input, output) => {
      const bootstrap = getBootstrapContent();
      if (bootstrap) {
        (output.system ||= []).push(bootstrap);
      }
    }
  };
};

export default AITPPlugin;
"""


def install_opencode_plugin(
    service: Any,
    *,
    scope: str,
    target_root: str | None,
    force: bool,
) -> list[dict[str, str]]:
    base = agent_hidden_root(
        target_root=target_root,
        scope=scope,
        hidden_dir=".opencode",
        user_root=Path.home() / ".config" / "opencode",
        project_root=service.repo_root / ".opencode",
    )
    plugin_root = base / "plugins"
    plugin_root.mkdir(parents=True, exist_ok=True)
    plugin_path = plugin_root / "aitp.js"
    if plugin_path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {plugin_path}")
    _write_text(
        plugin_path,
        service._canonical_repo_asset_text(
            ".opencode/plugins/aitp.js",
            fallback_text=opencode_plugin_template(),
        ),
    )
    return [{"agent": "opencode", "path": str(plugin_path), "kind": "plugin"}]


def claude_session_start_hook_template() -> str:
    return """#!/usr/bin/env bash
# SessionStart hook for AITP

set -euo pipefail

SCRIPT_DIR=\"$(cd \"$(dirname \"$0\")\" && pwd)\"
PLUGIN_ROOT=\"$(cd \"${SCRIPT_DIR}/..\" && pwd)\"
SKILL_PATH=\"${PLUGIN_ROOT}/skills/using-aitp/SKILL.md\"

if [ -f \"$SKILL_PATH\" ]; then
    using_aitp_content=$(cat \"$SKILL_PATH\")
else
    using_aitp_content=\"Error reading using-aitp skill from ${SKILL_PATH}\"
fi

escape_for_json() {
    local s=\"$1\"
    s=\"${s//\\\\/\\\\\\\\}\"
    s=\"${s//\\\"/\\\\\\\"}\"
    s=\"${s//$'\\n'/\\\\n}\"
    s=\"${s//$'\\r'/\\\\r}\"
    s=\"${s//$'\\t'/\\\\t}\"
    printf '%s' \"$s\"
}

using_aitp_escaped=$(escape_for_json \"$using_aitp_content\")
session_context=\"<EXTREMELY_IMPORTANT>\\nYou are in an AITP-enabled Claude Code session.\\n\\n**Below is the full content of the using-aitp skill. It is already loaded. Do not load using-aitp again.**\\n\\n${using_aitp_escaped}\\n</EXTREMELY_IMPORTANT>\"

if [ -n \"${CLAUDE_PLUGIN_ROOT:-}\" ]; then
  printf '{\\n  \"hookSpecificOutput\": {\\n    \"hookEventName\": \"SessionStart\",\\n    \"additionalContext\": \"%s\"\\n  }\\n}\\n' \"$session_context\"
else
  printf '{\\n  \"additional_context\": \"%s\"\\n}\\n' \"$session_context\"
fi

exit 0
"""


def claude_session_start_python_hook_template() -> str:
    return """#!/usr/bin/env python
\"\"\"Claude Code SessionStart hook for AITP.\"\"\"

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    plugin_root = Path(os.environ.get(\"CLAUDE_PLUGIN_ROOT\") or (script_dir / \"..\")).resolve()
    skill_path = plugin_root / \"skills\" / \"using-aitp\" / \"SKILL.md\"

    if skill_path.exists():
        using_aitp_content = skill_path.read_text(encoding=\"utf-8\")
    else:
        using_aitp_content = f\"Error reading using-aitp skill from {skill_path}\"

    session_context = (
        \"<EXTREMELY_IMPORTANT>\\n\"
        \"You are in an AITP-enabled Claude Code session.\\n\\n\"
        \"**Below is the full content of the using-aitp skill. It is already loaded. Do not load using-aitp again.**\\n\\n\"
        f\"{using_aitp_content}\\n\"
        \"</EXTREMELY_IMPORTANT>\"
    )

    if os.environ.get(\"CLAUDE_PLUGIN_ROOT\"):
        payload = {
            \"hookSpecificOutput\": {
                \"hookEventName\": \"SessionStart\",
                \"additionalContext\": session_context,
            }
        }
    else:
        payload = {\"additional_context\": session_context}

    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write(\"\\n\")
    return 0


if __name__ == \"__main__\":
    raise SystemExit(main())
"""


def claude_hook_wrapper_template() -> str:
    return """: << 'CMDBLOCK'
@echo off
if \"%~1\"==\"\" (
    echo run-hook.cmd: missing script name >&2
    exit /b 1
)

set \"HOOK_DIR=%~dp0\"
set \"PYTHON_HOOK=%HOOK_DIR%%~1.py\"

if exist \"%PYTHON_HOOK%\" (
    if defined AITP_PYTHON (
        \"%AITP_PYTHON%\" \"%PYTHON_HOOK%\" %2 %3 %4 %5 %6 %7 %8 %9
        exit /b %ERRORLEVEL%
    )

    where python >NUL 2>NUL
    if %ERRORLEVEL% equ 0 (
        python \"%PYTHON_HOOK%\" %2 %3 %4 %5 %6 %7 %8 %9
        exit /b %ERRORLEVEL%
    )

    where py >NUL 2>NUL
    if %ERRORLEVEL% equ 0 (
        py -3 \"%PYTHON_HOOK%\" %2 %3 %4 %5 %6 %7 %8 %9
        exit /b %ERRORLEVEL%
    )
)

if exist \"C:\\Program Files\\Git\\bin\\bash.exe\" (
    \"C:\\Program Files\\Git\\bin\\bash.exe\" \"%HOOK_DIR%%~1\" %2 %3 %4 %5 %6 %7 %8 %9
    exit /b %ERRORLEVEL%
)
if exist \"C:\\Program Files (x86)\\Git\\bin\\bash.exe\" (
    \"C:\\Program Files (x86)\\Git\\bin\\bash.exe\" \"%HOOK_DIR%%~1\" %2 %3 %4 %5 %6 %7 %8 %9
    exit /b %ERRORLEVEL%
)

where bash >nul 2>nul
if %ERRORLEVEL% equ 0 (
    bash \"%HOOK_DIR%%~1\" %2 %3 %4 %5 %6 %7 %8 %9
    exit /b %ERRORLEVEL%
)

exit /b 0
CMDBLOCK

SCRIPT_DIR=\"$(cd \"$(dirname \"$0\")\" && pwd)\"
SCRIPT_NAME=\"$1\"
shift
exec bash \"${SCRIPT_DIR}/${SCRIPT_NAME}\" \"$@\"
"""


def claude_hooks_manifest_template() -> str:
    payload = {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|clear|compact",
                    "hooks": [
                        {
                            "type": "command",
                            "command": '"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd" session-start',
                            "async": False,
                        }
                    ],
                }
            ]
        }
    }
    return json.dumps(payload, ensure_ascii=True, indent=2) + "\n"


def install_claude_session_start_hook(
    service: Any,
    *,
    scope: str,
    target_root: str | None,
    force: bool,
) -> list[dict[str, str]]:
    base = agent_hidden_root(
        target_root=target_root,
        scope=scope,
        hidden_dir=".claude",
        user_root=Path.home() / ".claude",
        project_root=service.repo_root / ".claude",
    )
    hook_root = base / "hooks"
    hook_root.mkdir(parents=True, exist_ok=True)

    session_start_path = hook_root / "session-start"
    if session_start_path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {session_start_path}")
    _write_executable_text(
        session_start_path,
        service._canonical_repo_asset_text(
            "hooks/session-start",
            fallback_text=claude_session_start_hook_template(),
        ),
    )

    session_start_python_path = hook_root / "session-start.py"
    if session_start_python_path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {session_start_python_path}")
    _write_text(
        session_start_python_path,
        service._canonical_repo_asset_text(
            "hooks/session-start.py",
            fallback_text=claude_session_start_python_hook_template(),
        ),
    )

    run_hook_path = hook_root / "run-hook.cmd"
    if run_hook_path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {run_hook_path}")
    _write_text(
        run_hook_path,
        service._canonical_repo_asset_text(
            "hooks/run-hook.cmd",
            fallback_text=claude_hook_wrapper_template(),
        ),
    )

    hooks_json_path = hook_root / "hooks.json"
    if hooks_json_path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {hooks_json_path}")
    _write_text(
        hooks_json_path,
        service._canonical_repo_asset_text(
            "hooks/hooks.json",
            fallback_text=claude_hooks_manifest_template(),
        ),
    )

    settings_path = base / "settings.json"
    if settings_path.exists():
        payload = json.loads(settings_path.read_text(encoding="utf-8"))
    else:
        payload = {}

    command_entry = f'"{run_hook_path}" session-start'
    desired_block = {
        "matcher": "startup|clear|compact",
        "hooks": [{"type": "command", "command": command_entry, "async": False}],
    }
    hooks_payload = payload.setdefault("hooks", {})
    session_blocks = hooks_payload.setdefault("SessionStart", [])
    filtered_blocks = []
    for block in session_blocks:
        block_hooks = block.get("hooks") or []
        commands = {
            str(entry.get("command") or "")
            for entry in block_hooks
            if isinstance(entry, dict)
        }
        if command_entry in commands:
            continue
        filtered_blocks.append(block)
    filtered_blocks.append(desired_block)
    hooks_payload["SessionStart"] = filtered_blocks
    service._write_json_file(settings_path, payload)

    return [
        {"agent": "claude-code", "path": str(session_start_path), "kind": "hook"},
        {"agent": "claude-code", "path": str(session_start_python_path), "kind": "hook-python"},
        {"agent": "claude-code", "path": str(run_hook_path), "kind": "hook-wrapper"},
        {"agent": "claude-code", "path": str(hooks_json_path), "kind": "hook-manifest"},
        {"agent": "claude-code", "path": str(settings_path), "kind": "hook-config"},
    ]


def install_one_agent(
    service: Any,
    agent: str,
    *,
    scope: str,
    target_root: str | None,
    force: bool,
    install_mcp: bool,
    mcp_profile: str = "full",
) -> list[dict[str, str]]:
    home = Path.home()
    installed: list[dict[str, str]] = []

    if agent == "codex":
        for base in service._codex_skill_targets(scope=scope, target_root=target_root):
            base.mkdir(parents=True, exist_ok=True)
            using_skill_base = base.parent / "using-aitp"
            using_skill_base.mkdir(parents=True, exist_ok=True)
            using_skill_path = using_skill_base / "SKILL.md"
            if using_skill_path.exists() and not force:
                raise FileExistsError(f"Refusing to overwrite {using_skill_path}")
            _write_text(
                using_skill_path,
                service._canonical_skill_text(
                    "using-aitp",
                    fallback_text=service._using_aitp_skill_template("codex"),
                ),
            )
            installed.append({"agent": agent, "path": str(using_skill_path), "kind": "skill"})

            skill_path = base / "SKILL.md"
            if skill_path.exists() and not force:
                raise FileExistsError(f"Refusing to overwrite {skill_path}")
            _write_text(
                skill_path,
                service._canonical_skill_text(
                    "aitp-runtime",
                    fallback_text=service._codex_skill_template(),
                ),
            )
            installed.append({"agent": agent, "path": str(skill_path), "kind": "skill"})

            if target_root or scope == "project":
                setup_path = base / "AITP_MCP_SETUP.md"
                _write_text(setup_path, service._codex_mcp_setup_markdown(mcp_profile=mcp_profile))
                installed.append({"agent": agent, "path": str(setup_path), "kind": "mcp-setup"})

        if install_mcp and not target_root and scope == "user":
            installed.extend(install_codex_mcp(service, force=force, mcp_profile=mcp_profile))
        return installed

    if agent == "openclaw":
        base = openclaw_skill_target(service, scope=scope, target_root=target_root)
        base.mkdir(parents=True, exist_ok=True)
        using_skill_base = base.parent / "using-aitp"
        using_skill_base.mkdir(parents=True, exist_ok=True)
        using_skill_path = using_skill_base / "SKILL.md"
        if using_skill_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite {using_skill_path}")
        _write_text(using_skill_path, service._using_aitp_skill_template("openclaw"))
        installed.append({"agent": agent, "path": str(using_skill_path), "kind": "skill"})

        skill_path = base / "SKILL.md"
        if skill_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite {skill_path}")
        _write_text(skill_path, service._openclaw_skill_template())
        installed.append({"agent": agent, "path": str(skill_path), "kind": "skill"})

        if target_root or scope == "project":
            setup_path = base / "AITP_MCP_SETUP.md"
            _write_text(setup_path, service._openclaw_mcp_setup_markdown(scope=scope, mcp_profile=mcp_profile))
            installed.append({"agent": agent, "path": str(setup_path), "kind": "mcp-setup"})

        if install_mcp and not target_root:
            installed.extend(install_openclaw_mcp(service, force=force, scope=scope, mcp_profile=mcp_profile))
        return installed

    if agent == "opencode":
        target_base = agent_hidden_root(
            target_root=target_root,
            scope=scope,
            hidden_dir=".opencode",
            user_root=home / ".config" / "opencode",
            project_root=service.repo_root / ".opencode",
        )
        skill_base = target_base / "skills" / "aitp-runtime"
        using_skill_base = target_base / "skills" / "using-aitp"
        skill_base.mkdir(parents=True, exist_ok=True)
        using_skill_base.mkdir(parents=True, exist_ok=True)

        using_skill_path = using_skill_base / "SKILL.md"
        if using_skill_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite {using_skill_path}")
        _write_text(
            using_skill_path,
            service._canonical_skill_text(
                "using-aitp",
                fallback_text=service._using_aitp_skill_template("opencode"),
            ),
        )
        installed.append({"agent": agent, "path": str(using_skill_path), "kind": "skill"})

        skill_path = skill_base / "SKILL.md"
        if skill_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite {skill_path}")
        _write_text(
            skill_path,
            service._canonical_skill_text(
                "aitp-runtime",
                fallback_text=service._opencode_skill_template(),
            ),
        )
        installed.append({"agent": agent, "path": str(skill_path), "kind": "skill"})

        setup_path = skill_base / "AITP_MCP_SETUP.md"
        if setup_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite {setup_path}")
        _write_text(
            setup_path,
            service._opencode_mcp_setup_markdown(scope=scope, target_root=target_root, mcp_profile=mcp_profile),
        )
        installed.append({"agent": agent, "path": str(setup_path), "kind": "mcp-setup"})

        installed.extend(install_opencode_plugin(service, scope=scope, target_root=target_root, force=force))

        if install_mcp:
            installed.extend(
                install_opencode_mcp(
                    service,
                    force=force,
                    scope=scope,
                    target_root=target_root,
                    mcp_profile=mcp_profile,
                )
            )
        return installed

    if agent == "claude-code":
        target_base = agent_hidden_root(
            target_root=target_root,
            scope=scope,
            hidden_dir=".claude",
            user_root=home / ".claude",
            project_root=service.repo_root / ".claude",
        )
        skill_base = target_base / "skills" / "aitp-runtime"

        skill_base.mkdir(parents=True, exist_ok=True)
        using_skill_base = skill_base.parent / "using-aitp"
        using_skill_base.mkdir(parents=True, exist_ok=True)

        using_skill_path = using_skill_base / "SKILL.md"
        if using_skill_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite {using_skill_path}")
        _write_text(
            using_skill_path,
            service._canonical_skill_text(
                "using-aitp",
                fallback_text=service._using_aitp_skill_template("claude-code"),
            ),
        )
        installed.append({"agent": agent, "path": str(using_skill_path), "kind": "skill"})

        skill_path = skill_base / "SKILL.md"
        if skill_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite {skill_path}")
        _write_text(
            skill_path,
            service._canonical_skill_text(
                "aitp-runtime",
                fallback_text=service._claude_code_skill_template(),
            ),
        )
        installed.append({"agent": agent, "path": str(skill_path), "kind": "skill"})

        setup_path = skill_base / "AITP_MCP_SETUP.md"
        if setup_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite {setup_path}")
        _write_text(
            setup_path,
            service._claude_mcp_setup_markdown(scope=scope, target_root=target_root, mcp_profile=mcp_profile),
        )
        installed.append({"agent": agent, "path": str(setup_path), "kind": "mcp-setup"})
        installed.extend(install_claude_session_start_hook(service, scope=scope, target_root=target_root, force=force))
        if install_mcp:
            installed.extend(
                install_claude_mcp(
                    service,
                    force=force,
                    scope=scope,
                    target_root=target_root,
                    mcp_profile=mcp_profile,
                )
            )
        return installed

    raise ValueError(f"Unsupported agent: {agent}")


def install_agent(
    service: Any,
    *,
    agent: str,
    scope: str = "user",
    target_root: str | None = None,
    force: bool = True,
    install_mcp: bool = True,
    mcp_profile: str = "full",
) -> dict[str, Any]:
    agent = agent.lower()
    installed: list[dict[str, str]] = []
    targets = [agent] if agent != "all" else ["codex", "openclaw", "opencode", "claude-code"]

    for target in targets:
        resolved_target_root = target_root
        if agent == "all" and target_root:
            resolved_target_root = str(Path(target_root) / target)
        installed.extend(
            install_one_agent(
                service,
                target,
                scope=scope,
                target_root=resolved_target_root,
                force=force,
                install_mcp=install_mcp,
                mcp_profile=mcp_profile,
            )
        )

    return {
        "agent": agent,
        "scope": scope,
        "mcp_profile": mcp_profile,
        "installed": installed,
    }
