# Repository guidance

- The `ledger-core` branch is the stable single-Topic evidence-ledger baseline.
- Keep ledger-core runtime code under `src/aitp/`.
- Keep the installable Codex bundle under `plugins/aitp-research-protocol/`.
- Preserve the core command groups and contracts: `init`, `enter`, `record`, and `note`.
- Research-graph features must consume ledger-core records through its public parser and must not rewrite source records.
- Cross-Topic links require explicit save; inferred links remain proposals.
- A local SQLite/FTS index is permitted only as a disposable derived cache with deterministic JSONL fallback.
- Skill distillation must preserve provenance and require explicit human approval before publication.
- Do not add a required vector service, MCP server, hook, or background daemon.
- Run the unchanged ledger tests plus graph-specific tests before committing.
