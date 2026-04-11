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

That means the normal user path is:

- talk naturally about the topic;
- let the plugin route the session into AITP;
- only use `aitp session-start "<task>"` when the bootstrap surface is missing or you need an explicit fallback.

For the shared install verification and first-run proof, use:

- [`INSTALL.md`](INSTALL.md)
- [`QUICKSTART.md`](QUICKSTART.md)
