# Installing AITP for OpenCode

OpenCode should load AITP through a plugin, not through a command bundle.

## Prerequisites

- OpenCode installed locally

## Installation

Add AITP to the `plugin` array in your `opencode.json`:

```json
{
  "plugin": ["aitp@git+https://github.com/bhjia-phys/AITP-Research-Protocol.git"]
}
```

Restart OpenCode. The plugin registers the AITP skills path and injects `using-aitp` at session start.

## Verify

Ask OpenCode for a theory task in natural language, for example:

- `继续这个 topic，方向改成 effective field theory`
- `读这篇论文并建立验证路线`

OpenCode should enter AITP before doing substantial work.

## Manual fallback

If bootstrap is unavailable, use:

```bash
aitp session-start "<task>"
```

## Updating

Restart OpenCode after pulling the repository or after a new plugin install.
