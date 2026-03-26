# AITP for OpenCode

OpenCode should use AITP through a plugin, not through `/aitp` command bundles.

## Installation

Add this to `opencode.json`:

```json
{
  "plugin": ["aitp@git+https://github.com/bhjia-phys/AITP-Research-Protocol.git"]
}
```

Restart OpenCode.

## What the plugin does

1. Registers the repository `skills/` directory through the `config` hook.
2. Injects `using-aitp` through `experimental.chat.system.transform`.

The result should feel like natural-language-first AITP routing rather than explicit command invocation.
