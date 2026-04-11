# Uninstall

Remove the AITP adapter assets you installed.

If you also installed the runtime itself, remove it with:

```bash
python -m pip uninstall aitp-kernel
```

Contributor/local-dev editable installs still uninstall through the same `aitp`
entrypoint because the editable package now publishes as `aitp-kernel`.

## General rule

There are two install modes:

- preferred native install for the runtime platform;
- compatibility install via `aitp install-agent`.

Today that still means:

- Claude Code: plugin skeleton plus runtime install
- OpenCode: plugin-first repo install
- Codex: native skill discovery plus runtime install

None of these should require a custom `/aitp` command bundle for normal use.

Uninstall the assets that match the mode you actually used. Do not assume that
every platform writes the same files.

If your machine is in a mixed state rather than a clean canonical install, do
not start with uninstall. First inspect or converge the install through:

- [`docs/MIGRATE_LOCAL_INSTALL.md`](MIGRATE_LOCAL_INSTALL.md)

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
