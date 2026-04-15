# Installing AITP for OpenCode

OpenCode should load AITP through a plugin, not through a command bundle.

## Prerequisites

- OpenCode installed locally

## Installation

Before plugin bootstrap, complete the shared kernel install:

```bash
python -m pip install aitp-kernel
aitp --version
```

Add AITP to the `plugin` array in your `opencode.json`:

```json
{
  "plugin": ["aitp@git+https://github.com/bhjia-phys/AITP-Research-Protocol.git"]
}
```

Restart OpenCode. The plugin registers the AITP skills path and injects `using-aitp` at session start.

That is the normal user path. OpenCode should enter AITP from natural-language
requests, not from a `/aitp` command ritual.

Ordinary topic work should stay in a light runtime profile by default and only
expand when benchmark mismatch, scope change, promotion intent, or explicit
deep checking makes the full runtime necessary.

## Verify

First verify the shared kernel and plugin state:

```bash
aitp doctor
aitp doctor --json
```

The OpenCode row should be `ready` in
`runtime_support_matrix.runtimes.opencode`.

For the bounded deep-execution parity probe, run:

```bash
python research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py --runtime opencode --json
```

That probe validates the plugin hooks plus downstream bounded AITP artifacts.
It is intentionally not the same thing as full live OpenCode parity closure.

Ask OpenCode for a theory task in natural language, for example:

- `继续这个 topic，方向改成 effective field theory`
- `读这篇论文并建立验证路线`

OpenCode should enter AITP before doing substantial work.

When AITP says a human choice is required, inspect the active surface with:

```bash
aitp interaction --topic-slug <topic_slug> --json
```

If the active surface is a formal decision point, resolve it with:

```bash
aitp resolve-decision --topic-slug <topic_slug> --decision-id <decision_id> --option <index> --comment "<why>"
aitp resolve-checkpoint --topic-slug <topic_slug> --option <index> --comment "<why>"
```

After the OpenCode row is `ready`, use the shared first-run guide:

- [`../docs/QUICKSTART.md`](../docs/QUICKSTART.md)

## Manual fallback

If bootstrap is unavailable, use:

```bash
aitp session-start "<task>"
```

If you are migrating from an older AITP setup, remove any legacy `/aitp*`
command bundles so the plugin-first path is the only default entry.

## Updating

```bash
python -m pip install --upgrade aitp-kernel
```

Restart OpenCode after a new package or plugin install.

## Uninstalling

Remove `aitp@git+https://github.com/bhjia-phys/AITP-Research-Protocol.git`
from the `plugin` array in `opencode.json`, then restart OpenCode.

If you also want to remove compatibility assets or the runtime package
install, follow [`../docs/UNINSTALL.md`](../docs/UNINSTALL.md).
