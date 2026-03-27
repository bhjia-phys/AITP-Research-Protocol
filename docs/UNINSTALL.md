# Uninstall

Remove the AITP adapter assets you installed.

If you also installed the runtime itself, remove it with:

```bash
python -m pip uninstall aitp-kernel
```

If you installed with `pip install -e research/knowledge-hub`, this is the
package you want to uninstall.

## General rule

There are two install modes:

- preferred native install for the runtime platform;
- compatibility install via `aitp install-agent`.

Uninstall the assets that match the mode you actually used. Do not assume that
every platform writes the same files.

The commands below use POSIX-style `rm`. On Windows, remove the same paths with
PowerShell `Remove-Item -Recurse -Force` or with File Explorer.

## OpenClaw

```bash
rm -rf ~/.openclaw/skills/using-aitp
rm -rf ~/.openclaw/skills/aitp-runtime
```

Also remove any `aitp` MCP bridge entry from your OpenClaw configuration.

## Codex

If you installed through native skill discovery:

```bash
rm ~/.agents/skills/aitp
```

Optionally also remove the cloned repo if you no longer want the local source:

```bash
rm -rf ~/.codex/aitp
```

If you used `aitp install-agent` instead:

```bash
rm -rf /path/to/theory-workspace/.agents/skills/using-aitp
rm -rf /path/to/theory-workspace/.agents/skills/aitp-runtime
```

Also remove any `aitp` MCP registration if you added one.

## Claude Code

Plugin-managed install:

Use the Claude Code plugin manager to uninstall or disable the `aitp` plugin.

If your Claude environment keeps a local plugin checkout, remove that local
plugin directory as well.

Compatibility install:

```bash
rm -rf /path/to/theory-workspace/.claude/skills/using-aitp
rm -rf /path/to/theory-workspace/.claude/skills/aitp-runtime
rm -f /path/to/theory-workspace/.claude/hooks/session-start
rm -f /path/to/theory-workspace/.claude/hooks/run-hook.cmd
rm -f /path/to/theory-workspace/.claude/hooks/hooks.json
rm -f /path/to/theory-workspace/.claude/settings.json
```

If you merged the compatibility hook into an existing Claude settings file
instead of removing the whole generated file, delete only the AITP
`SessionStart` hook block.

## OpenCode

Plugin-managed install:

Remove `aitp@git+https://github.com/bhjia-phys/AITP-Research-Protocol.git`
from the `plugin` array in `opencode.json`, then restart OpenCode.

Compatibility install:

```bash
rm -rf /path/to/theory-workspace/.opencode/skills/using-aitp
rm -rf /path/to/theory-workspace/.opencode/skills/aitp-runtime
rm -f /path/to/theory-workspace/.opencode/plugins/aitp.js
```

Also remove any `aitp` MCP entry from the OpenCode configuration file.

Legacy `/aitp*` command bundles are no longer the default install path. If you
still have them from an older AITP install, remove them manually so they do not
compete with the plugin-first route.
