# Repository guidance

- This repository contains only the lightweight AITP Research Memory product.
- Keep runtime code under `src/aitp/`.
- Keep the installable Codex bundle under `plugins/aitp-research-memory/`.
- Preserve the four command groups: `init`, `enter`, `record`, and `note`.
- Do not add a database, vector index, MCP server, mandatory hook, background daemon, migration layer, or compatibility implementation.
- Run `pytest -q` and validate both bundled Skills before committing.
