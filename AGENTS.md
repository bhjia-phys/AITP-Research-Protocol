# Repository guidance

- The `ledger-core` branch is the stable single-Topic evidence-ledger baseline.
- Follow the stage order in `docs/roadmap.md`. The M0.5 slim-core gate has passed; M0.6 is the active stage (`docs/m0.6-init-adopt.md`, `docs/m0.6-bootstrap.md`, `docs/m0.6-suite.md`).
- Keep one canonical runtime implementation: `plugins/aitp-research-protocol/scripts/vendor/aitp/`; do not hand-maintain a copied plugin runtime.
- Keep each Python module below 400 nonblank lines, and keep the total canonical runtime within the cumulative budget in `docs/roadmap.md` (~2,000 lines maximum; M0.6 ends ≤ 1,100).
- Keep the installable Codex bundle under `plugins/aitp-research-protocol/`.
- Preserve the core command groups and contracts: `init`, `enter`, `record`, and `note`. Later commands (`show`, `list`, `check`, `compile`, `catalog`, `link`) are additive and must not weaken the core contracts.
- Cross-topic and compiled-artifact features must consume ledger records through the public parser and must never rewrite source records.
- Cross-Topic links require explicit human-confirmed save; inferred links remain drafts.
- Default to no index: `rg` over Markdown is the query path. Permit a derived cache only after a benchmark demonstrates the need; it must be disposable and rebuildable.
- Skill distillation must preserve provenance and require explicit human approval before publication.
- Do not add a required vector service, MCP server, hook, or background daemon.
- Keep physical reasoning, synthesis, literature judgment, and collaboration policy in Skills and reviewed artifacts; Python is for deterministic I/O, validation, projection, and benchmarks.
- Agent behavior conformance is measured by the external suite described in `docs/roadmap.md`; the runtime never tries to enforce research behavior.
- Documentation must stay inside the trust model: auditable and tamper-evident, never tamper-proof.
- Legacy stores (v5 registries, PROJECT_MEMORY-style memory files, session archives) are preservation evidence; bootstrap them lazily per the M0.6 plan instead of migrating their contents.
- Run the unchanged ledger tests plus stage-specific tests before committing.
