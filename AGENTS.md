# Repository guidance

- The `memory-core` branch is the stable single-Topic research-memory baseline.
- Keep memory-core runtime code under `src/aitp/`.
- Keep the installable Codex bundle under `plugins/aitp-research-memory/`.
- Preserve the core command groups and contracts: `init`, `enter`, `record`, and `note`.
- Research-graph features must consume memory-core records through its public parser and must not rewrite source records.
- Cross-Topic links require explicit save; inferred links remain proposals.
- A local SQLite/FTS index is permitted only as a disposable derived cache with deterministic JSONL fallback.
- Skill distillation must preserve provenance and require explicit human approval before publication.
- Do not add a required vector service, MCP server, hook, or background daemon.
- Run the unchanged memory-core tests plus graph-specific tests before committing.
