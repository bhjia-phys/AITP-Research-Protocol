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

That is the normal user path. OpenCode should enter AITP from natural-language
requests, not from a `/aitp` command ritual.

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

If you are migrating from an older AITP setup, remove any legacy `/aitp*`
command bundles so the plugin-first path is the only default entry.

## Updating

Restart OpenCode after pulling the repository or after a new plugin install.

## Uninstalling

Remove `aitp@git+https://github.com/bhjia-phys/AITP-Research-Protocol.git`
from the `plugin` array in `opencode.json`, then restart OpenCode.

If you also want to remove compatibility assets or the editable runtime
install, follow [`../docs/UNINSTALL.md`](../docs/UNINSTALL.md).
