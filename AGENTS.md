# Repository guidance

- The `ledger-core` branch is the stable single-Topic evidence-ledger baseline.
- Complete the M0.5 slim-core gate before adding research-graph runtime code.
- Keep one canonical runtime implementation; do not hand-maintain a copied plugin runtime.
- Keep each Python module below 400 nonblank lines.
- Keep the installable Codex bundle under `plugins/aitp-research-protocol/`.
- Preserve the core command groups and contracts: `init`, `enter`, `record`, and `note`.
- Research-graph features must consume ledger-core records through its public parser and must not rewrite source records.
- Cross-Topic links require explicit save; inferred links remain proposals.
- Implement deterministic JSONL first. Permit SQLite/FTS only after a benchmark demonstrates the need, and only as a disposable derived cache.
- Skill distillation must preserve provenance and require explicit human approval before publication.
- Do not add a required vector service, MCP server, hook, or background daemon.
- Keep physical reasoning, synthesis, and collaboration policy in Skills and reviewed artifacts; Python is for deterministic I/O, validation, projection, and benchmarks.
- Run the unchanged ledger tests plus graph-specific tests before committing.
