# AITP - AI Theoretical Physicist Protocol

> Pursue truth, not fame.

AITP is a research protocol and runtime harness for AI-assisted theoretical
physics. It is meant to let a human researcher talk naturally with an agent while
important scientific state is written into typed, replayable records: claims,
definitions, objects, relations, evidence, tool runs, validation results,
human checkpoints, and long-term memory.

The current implementation direction is **AITP v5**: a typed kernel under
`brain/v5/` with CLI, MCP, host adapters, hooks, summaries, and review surfaces
kept as thin layers over kernel records.

## Current Status

AITP v5 is at **kernel-ready / content-backlog** status. The typed kernel,
public contracts, CLI/MCP surfaces, Codex/Claude Code/Kimi Code host paths,
vNext control-plane surfaces, literature-intake assistant, source-stack and
source-reconstruction review surfaces, L2/Obsidian views, workspace replay, and
goal-continuation audit packets are implemented and covered by the focused v5
test suite. This does **not** mean all migrated research content is
semantically reviewed or that claim trust can be updated from orientation
surfaces.

| Area | Status |
|------|--------|
| Typed research records | Implemented: topics, sessions, claims, evidence, source assets, code state, tool recipes/runs, references, physics objects, object relations, sensemaking, validation, checkpoints, promotion packets, L2 memory |
| Trust discipline | Implemented: summaries are orientation-only, validation gates trust, high-risk promotion needs evidence, passed validation, failure modes, and human review checkpoints |
| Long-term memory | Implemented core: L2 memory entries, promotion packets, memory audits, failure-mode audits, trust audits, Obsidian review views |
| Replay and review | Implemented core: session summaries, workspace summaries, workspace replay packets, source reconstruction audits |
| Legacy migration | Implemented generic migration plus curated v5 migration for priority legacy topics, coverage, semantic-review, repair, source-reconstruction, human-checkpoint, and Obsidian worklist surfaces; the real legacy semantic review backlog remains blocking |
| Host integration | Priority hosts are ready for Codex, Claude Code, and Kimi Code through v5 MCP/hook/adapter surfaces and production-loop audits; Hakimi now auto-configures a WorkFrame-scoped typed session bridge that can read `process_graph_slice`, compile it into context, and expose model-facing AITP write-bridge execution for exploratory records, source assets, proof obligations, validation contracts/results, and human checkpoints instead of duplicating the schema |
| OpenCode | Adapter/plugin surfaces exist, but OpenCode remains deferred until its hook model and packaging path stabilize |
| Goal continuation | Implemented: local `.aitp/surfaces/goal_continuation/` JSON+Markdown packets capture objective, commit range, changed files, tests, smoke commands, readiness, next actions, and blocking backlog |
| Literature intake | Implemented conservative intake: references are orientation-only, evidence/sensemaking are guarded suggestions, and trust updates stay forbidden without preflight/checkpoints |
| Theory research state | Implemented minimal conservative surface: `research-state register-source`, `attach-artifact`, `update-claim-status`, `create-proof-obligation`, `classify-event`, and `bounded-evidence` connect literature/results/artifacts/Fisherd-style runs to typed records without claim-trust promotion |
| Typed process graph | Implemented first read-only slice: `aitp-v5 graph slice <session-id>` and `aitp_v5_get_process_graph_slice` compile typed records into orientation-only nodes, edges, source backtrace, relation neighborhoods, open obligations, trust-boundary reasons, recommended research moments, and a host-agnostic moment policy for when to record, brainstorm/backtrace, or stop at a trust boundary |
| Exploratory research graph | Implemented first typed record: `aitp-v5 exploration record` and `aitp_v5_record_exploratory_record` capture source assets, question decomposition, relation-path brainstorming, backtrace steps, and steering checkpoints as orientation-only graph records |
| Canonical source assets | Implemented first typed record: `aitp-v5 asset register` and `aitp_v5_register_source_asset` assign orientation-only identities, hashes, version anchors, and source/code/artifact links to papers, lectures, notes, code repositories, snapshots, datasets, and generated artifacts |
| QSGW cockpit | Implemented first surface: `aitp-v5 status qsgw-cockpit` writes a topic-local final/diagnostic lane manifest, plot guard, and dashboard dry-run from typed records plus `research/librpa` report/script scans; it also discovers downstream `*_lane_manifest_current.json` and `*_aitp_intake_current.jsonl` files without treating them as trust updates |

The latest real readiness audit reports:

- `completion_status = kernel_ready_content_backlog`
- `kernel_capability_status = ready_for_priority_hosts`
- `blocking_gaps = ["legacy_semantic_review_backlog"]`
- legacy semantic review progress: `needs_revision = 16`, `inconclusive = 2`,
  `passed = 0`
- source reconstruction backlog: `incomplete_claim_count = 3`
- `can_update_claim_trust = false`
- `semantic_lossless_proven = false`

The practical rule is:

- Use v5 for real research workflows now.
- Treat typed v5 records as the authority.
- Treat process graph slices as local navigation/compilation aids, not as new
  truth records.
- Treat host-agnostic moment policy as read-only process guidance; it explains
  when typed records, brainstorming/backtrace, or trust preflight are needed,
  but it cannot update kernel state or claim trust.
- Treat exploratory records as canonical process records for navigation,
  brainstorming, and backtrace continuity, but not as evidence or validation.
- Treat source asset records as canonical identities for raw papers, lectures,
  notes, code snapshots, datasets, and generated artifacts; they orient source
  backtrace and provenance, but they do not update claim trust by themselves.
- Treat Hakimi bridge smoke tests as downstream contract checks: they show that
  an AITP-shaped slice, moment policy, and write CLI contract can be consumed by
  Hakimi without making Hakimi a second source of truth. They are not a
  substitute for running the real AITP CLI/MCP against a topic store.
- Treat Hakimi's automatic session bridge as runtime wiring, not as a new
  authority: it resolves the AITP `--base` path from the current Hakimi Agent
  cwd when the call is made, reads only WorkFrames with explicit
  `aitp:session:<id>` scope, and can be disabled or replaced by host-provided
  bridges.
- Treat Hakimi's `ResearchAction.execute_aitp_write_bridge` as a host execution
  path for configured sessions, not as a new authority. It should write through
  AITP and record scoped action evidence; if the bridge is not configured, the
  host must fail closed.
- Treat generated summaries, replay packets, README text, adapter packets, and
  Obsidian views as orientation surfaces.
- Do not call the whole migration complete until the legacy semantic review
  backlog is reviewed and repaired from typed review results.

## Remaining Work

The remaining work is content and deployment hardening, not a missing core v5
kernel capability:

1. Resolve the real legacy semantic review backlog. Each `needs_revision` or
   `inconclusive` topic needs typed review/repair basis; archive accounting is
   not semantic proof.
2. Clear source-reconstruction inconclusive items for the remaining active
   claims.
3. Continue qsgw/librpa topic hardening from the lightweight "research
   cockpit" surface: run `aitp-v5 status qsgw-cockpit` to materialize the
   topic-local lane manifest, plot guard, and dashboard dry-run. The cockpit now
   detects downstream lane/intake files, so the remaining work is to make actual
   result refresh scripts emit guarded result candidates and make final plot
   scripts fail closed on non-final rows. Final outputs require final-usable
   provenance; diagnostic outputs may carry assumptions only when labeled.
4. Keep literature intake conservative: record references as orientation-only,
   record evidence only with explicit claim, status, source refs, and scoped
   output, and route trust changes through preflight/checkpoints.
5. Use the theory `research-state` surface for bounded numerical results and
   proof obligations: attach result artifacts by reference, record tool-run
   provenance, write scoped evidence, append claim maturity/status, and keep
   publishable/trust changes behind validation and human gates.
6. Harden the source-store contract beyond the first `SourceAssetRecord` slice:
   add ingestion/de-duplication policy, stronger local PDF/lecture/code snapshot
   indexing, and source-stack queries that can keep a backtrace focused on the
   original physics question.
7. Harden the Hakimi runtime bridge against real topic stores. Hakimi sessions
   now auto-configure a dynamic AITP CLI bridge, consume process graph slices
   through explicit WorkFrame scope, compile them into context packs before
   research-context injection, and expose write-bridge hints and execution for
   exploratory records, proof obligations, human checkpoints, source assets,
   and validation records. Hakimi also has an opt-in real CLI smoke that creates
   a temporary AITP topic store, reads a real `process_graph_slice`, writes a
   proof obligation and checkpoint, and verifies the resulting `.aitp` records
   when `HAKIMI_AITP_REAL_CLI_SMOKE=1`, `AITP_V5_REPO`, and `AITP_V5_PYTHON`
   point at a working AITP Python environment. Richer MCP-first execution and
   strict validation/checkpoint enforcement still need the next runtime
   integration slice.
8. Update downstream theory workspaces to the latest v5 kernel and regenerate
   topic-local runtime handoff files where needed.
9. Revisit OpenCode after its host hook model is stable enough for the same
   production-loop guarantees as Codex, Claude Code, and Kimi Code.

## Why AITP Exists

Plain agent chat is useful, but it is not enough for serious theory work:

- Chat context is volatile.
- A confident answer is not a validation result.
- A summary is not evidence.
- A claim without source, definition, failure mode, and validation cannot safely
  become long-term memory.
- A future session should know what was verified, what was only hypothesized,
  and what would falsify the claim.

AITP adds a protocol layer around the agent:

| Direct agent chat | Agent with AITP |
|-------------------|-----------------|
| Conversation history is the main memory | Typed records are durable memory |
| Agent may blur claim, evidence, and summary | Claim, evidence, validation, and uncertainty are separate records |
| "Looks right" can become sticky | Trust changes require validation and checkpoints |
| Later sessions depend on recall | Later sessions resume from execution briefs and replay packets |
| Long-term notes may drift | L2 memory keeps provenance, scope, validation links, and failure modes |

## Research Workflow

The intended user experience is still natural:

> "I want to understand whether the sigma-z OTOC in the Haldane-Shastry point is
> a reliable chaos diagnostic. Continue from the old topic if it exists."

The agent should then:

1. Load `using-aitp` / AITP runtime guidance.
2. Restore or create the v5 topic, session, and active claim.
3. Read the execution brief to recover current state and risk level.
4. Record typed scientific structure: definitions, objects, relations,
   assumptions, evidence, code state, and failure modes.
5. Create validation contracts before relying on numerical or symbolic tools.
6. Record tool runs and validation results.
7. Keep strong conclusions as hypotheses until validation and human checkpoints
   justify promotion.
8. Promote only scoped, validated results into L2 memory.
9. Generate summaries, replay packets, and review views for orientation.

In short: talk naturally, but make the science durable.

## Stable Human Output

AITP now treats human-facing research output as a stable protocol surface. Chat
reports, session summaries, replay packets, Obsidian review views, and
adapter-rendered research reports should keep this spine:

1. Core claim or current focus.
2. Verified or validated content.
3. Hypotheses, uncertainty, and known failure modes.
4. AITP records written or referenced.
5. Next actions.
6. Long-term memory candidates and content that must not be promoted.

Future versions may add optional sections or appendices, but they should not
rename, remove, reorder, or change the meaning of that spine without a major
protocol-version change and a migration note. This is specified in
[`docs/AITP_SPEC.md`](docs/AITP_SPEC.md).

## Truth Rules

AITP v5 keeps a hard distinction between truth sources and orientation surfaces.

**Authoritative:**

- typed v5 kernel records under `<topics-root>/.aitp/`
- validation contracts and validation results
- evidence records linked to sources, code states, tool runs, and validation
- human checkpoint records
- promotion packets and L2 memory entries

**Orientation-only:**

- generated session/workspace summaries
- workspace replay packets
- Obsidian review views
- README and planning docs
- adapter packets and bridge files
- external note pointers and reference locations by themselves

Reference locations help you find things; they are not evidence until a typed
record says what was used and how.

## v5 Kernel Surfaces

The v5 kernel is exposed through several thin surfaces:

| Surface | Purpose |
|---------|---------|
| `python -m brain.v5.cli ...` | Local CLI for kernel operations |
| `brain/v5/native_mcp.py` | MCP entrypoint for Codex, Claude Code, Kimi Code, and other MCP hosts |
| `brain/v5/mcp_tools.py` | MCP tool wrappers over kernel functions |
| `brain/v5/public_surfaces.py` | Contracted public payload validators |
| `aitp-v5 graph slice <session-id>` | Read-only typed process graph slice for local agent compilation |
| `aitp-v5 exploration record` | Orientation-only typed record for brainstorming, backtrace, source-asset, and steering continuity |
| `aitp-v5 asset register` | Orientation-only canonical identity for raw papers, lectures, notes, code snapshots, datasets, and generated artifacts |
| `brain/v5/adapter_*` | Host adapter packets, bridge runners, and install/audit helpers |
| `hooks/aitp_v5_*` | Host lifecycle hooks and event runners |
| `<topics-root>/.aitp/surfaces/` | Generated orientation outputs such as summaries and review views |

For legacy workspaces whose topic store is
`<workspace>/research/aitp-topics`, the canonical v5 kernel store is
`<workspace>/research/aitp-topics/.aitp/`. A workspace-root
`<workspace>/.aitp/` may exist for older local tooling or host UI state, but it
is not the v5 topic/claim/evidence store and should not be used as the
execution contract.

Hakimi's current bridge calls the same CLI surface with structured arguments:
`aitp-v5 --base <base> graph slice <session-id>`, `exploration record`, `asset
register`, `checkpoint request`, `research-state create-proof-obligation`,
`validation contract create`, and `validation result record`. If the
`aitp-v5` console command is not installed in a local environment, use the
equivalent module invocation shown below.

The downstream Hakimi real CLI smoke is opt-in so Hakimi unit tests do not
depend on Python packages. To run it from the Hakimi checkout after installing
AITP dependencies:

```bash
HAKIMI_AITP_REAL_CLI_SMOKE=1 \
AITP_V5_REPO=/path/to/AITP-Research-Protocol \
AITP_V5_PYTHON=/path/to/python \
pnpm -C packages/agent-core vitest run test/aitp/real-cli-smoke.e2e.test.ts
```

For a quick CLI check:

```bash
python -m brain.v5.cli --help
python -m brain.v5.cli adapter --help
```

## Quick Start: v5 Kernel

Use module invocation if the `aitp-v5` console command is not installed:

```bash
python -m brain.v5.cli init /path/to/workspace

python -m brain.v5.cli --base /path/to/workspace topic create fqhe \
  --context topological-order \
  --title "FQHE"

python -m brain.v5.cli --base /path/to/workspace claim create \
  --topic fqhe \
  --statement "Finite-size counting identifies the edge sector." \
  --evidence-profile toy_numeric \
  --confidence-state hypothesis \
  --uncertainty "finite-size artifact may mimic counting"

python -m brain.v5.cli --base /path/to/workspace session bind s1 \
  --topic fqhe \
  --context topological-order \
  --claim <claim-id>

python -m brain.v5.cli --base /path/to/workspace brief s1
```

In normal use, a host agent calls the MCP tools and follows the execution brief;
you do not need to type every record command by hand.

## MCP Setup

Register the v5 native MCP entrypoint in the host:

```json
{
  "mcpServers": {
    "aitp": {
      "command": "python",
      "args": [
        "/path/to/AITP-Research-Protocol/brain/v5/native_mcp.py"
      ]
    }
  }
}
```

The legacy MCP server (`brain/mcp_server.py`) remains in the repository for the
older L0-L4 Markdown protocol, but new research workflows should prefer the v5
typed kernel.

The v5 native MCP entrypoint may expose compatibility aliases named
`aitp_list_topics`, `aitp_get_execution_brief`, and `aitp_bootstrap_topic`.
These aliases are for legacy discovery/bootstrap only. A research turn should
use `aitp_v5_get_execution_brief(base=<workspace>, session_id=<session-id>)` as
its execution contract. If an older topic only has a legacy slug, first migrate
or bind it into v5 typed records with `aitp_v5_migrate_curated_legacy_topic_to_v5`
or `aitp_v5_migrate_legacy_topic_to_v5`.

## Project-Scope Multi-Host Install

For a real theory workspace, keep the priority host adapters installed together:
`claude-code`, `kimi-code`, and `codex` should share the same AITP repo,
topics root, and project target root. This avoids one host resuming from a
different MCP endpoint or topic store than the others.

Preferred project-scope install:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py install \
  --agent all \
  --scope project \
  --target-root /path/to/theory-workspace \
  --topics-root /path/to/theory-workspace/research/aitp-topics
```

Windows example for the Theoretical-Physics workspace:

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py install --agent all --scope project --target-root F:/AI_Workspace/Theoretical-Physics --topics-root F:/AI_Workspace/Theoretical-Physics/research/aitp-topics
```

Project-scope installs write runtime assets under the workspace-local host
surfaces such as `.claude/`, `.kimi/`, `.codex/`, and `.mcp.json`. They should
not require user-global MCP files or a global `aitp` command wrapper. Use
user-scope installs only when a user explicitly wants global host wiring.

Keep the three priority hosts consistent. When updating a theory workspace,
run `scripts/aitp-pm.py update --agent all ...`, not one host at a time, unless
you are intentionally debugging a single adapter. Codex, Claude Code, and Kimi
Code skills should all describe the same v5-native rule: typed session brief
first, legacy aliases only for discovery/migration, and trust changes only via
v5 gates.

After installing or updating, verify the install record:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py status
```

The project records for `claude-code:project`, `kimi-code:project`, and
`codex:project` should all be present and should report the same `REPO_ROOT`,
`TOPICS_ROOT`, and `TARGET_ROOT`. The package manager rejects project installs
that would drift from an existing project install record.

## Host Adapters

| Host | Current path | Notes |
|------|--------------|-------|
| Codex | `brain/v5/native_mcp.py` plus `adapter install-hooks codex` | v5 adapter and hook fixture surfaces exist. Codex one-click packaging is still less mature than the kernel path. See [`docs/INSTALL_CODEX.md`](docs/INSTALL_CODEX.md). |
| Claude Code | `adapter install-hooks claude-code` | Can generate or merge v5 lifecycle settings. See [`docs/INSTALL_CLAUDE_CODE.md`](docs/INSTALL_CLAUDE_CODE.md). |
| Kimi Code | `adapter install-hooks kimi-code` | Can generate or merge TOML hook config. Current project installs use `.kimi/`; newer Kimi Code installs may also use `.kimi-code/`. See [`docs/INSTALL_KIMI_CODE.md`](docs/INSTALL_KIMI_CODE.md). |
| OpenCode | `adapter install-hooks opencode` | Plugin/bridge surfaces exist, but this track is optional for the current planning cycle. |

Useful adapter commands:

```bash
python -m brain.v5.cli --base /path/to/workspace adapter install-paths
python -m brain.v5.cli --base /path/to/workspace adapter smoke-coverage

python -m brain.v5.cli --base /path/to/workspace adapter install-hooks codex s1 \
  --settings .codex/hooks.json

python -m brain.v5.cli --base /path/to/workspace adapter install-hooks claude-code s1 \
  --settings .claude/settings.local.json

python -m brain.v5.cli --base /path/to/workspace adapter install-hooks kimi-code s1 \
  --settings /path/to/workspace/.kimi/config.toml

python -m brain.v5.cli --base /path/to/workspace adapter install-hooks kimi-code s1 \
  --settings /path/to/workspace/.kimi-code/config.toml

python -m brain.v5.cli --base /path/to/workspace adapter install-audit claude-code \
  --settings .claude/settings.local.json
```

Host hook files are runtime metadata. They may block unsafe actions or write
trace events, but they do not update scientific trust by themselves.

## Kimi Code Workspace Setup

For a theory workspace, AITP needs three Kimi assets:

1. `using-aitp` and `aitp-runtime` skills copied into the project skill
   directory.
2. An `aitp` MCP server that runs
   `brain/v5/native_mcp.py` from this repository and points
   `AITP_TOPICS_ROOT` at the workspace topic store.
3. Kimi lifecycle hooks generated by
   `adapter install-hooks kimi-code <session-id>`.

Current Kimi CLI builds and the existing AITP installer use project-local
`.kimi/config.toml` and `.kimi/skills/`. Newer Kimi Code builds document
`.kimi-code/mcp.json`, `.kimi-code/config.toml`, and `.kimi-code/skills/`.
Keep both paths in sync when a workspace must work across both builds. The
scientific authority remains the v5 typed records under
`<topics-root>/.aitp/`; Kimi config, skills, MCP JSON, and hook traces are
runtime metadata only.

## What Gets Recorded

AITP v5 can record and review:

- topics, sessions, and active claims
- risk assessments and execution briefs
- code-state provenance
- evidence records
- tool recipes, tool runs, and safe built-in executor results
- reference locations
- physics objects and object relations
- local sensemaking reports
- validation contracts and validation results
- human checkpoint requests and decisions
- failure-mode review packets and review results
- promotion packets and L2 memory entries
- trust-update records and trust audits
- source reconstruction audits
- session summaries, workspace summaries, replay packets, and Obsidian L2 views

## Validation and Promotion

AITP is deliberately conservative about trust:

- A tool run is not enough; high-risk tool-derived evidence must cite passed
  validation results.
- Partial validation can record progress, but it cannot promote a whole broad
  claim.
- Promotion packets must name known failure modes.
- If a claim has a strongest failure mode, high-risk promotion requires a
  failure-mode review checkpoint and a passed review result.
- L2 memory stores scope, evidence refs, validation refs, human checkpoint refs,
  and failure-mode context.

This is why AITP may feel heavier than a scratchpad. The weight is meant to sit
at trust boundaries, not at every sentence of exploration.

## Legacy Migration

Older AITP topic content can be audited and migrated into v5 typed records. The
migration path keeps legacy files as historical source material while moving the
long-term compatibility surface to v5 records.

Use the v5 legacy commands for audit/migration review:

```bash
python -m brain.v5.cli --base /path/to/workspace legacy --help
python -m brain.v5.cli --base /path/to/workspace legacy curated-known-topics
python -m brain.v5.cli --base /path/to/workspace legacy migrate \
  /path/to/workspace/research/aitp-topics/<legacy-topic-slug> \
  --context <context-id> \
  --session <session-id>
python -m brain.v5.cli --base /path/to/workspace legacy curated-migrate \
  /path/to/workspace/research/aitp-topics/<legacy-topic-slug>
```

`legacy migrate` is a topic-local, preservation-only migration. It writes a v5
session, legacy-seed claims/evidence/sensemaking records, and a topic-local
`legacy_v5_generic_migration.md` index. It imports only `topic/L2` if that
folder exists; it never imports a sibling or workspace-global `L2` directory
into each topic.

`curated-migrate` is for known topics whose current scientific boundary has
been hand-curated into a v5 active claim, claim status, validation contract,
evidence records, proof obligations, artifact links, and a topic-local migration
index. It does not promote the claim to L2.

Workspace-global legacy `L2` migration is a separate review surface. Use
`legacy l2-graph-manifest`, `legacy l2-typed-migration-packet`, or
`legacy l2-obsidian-view` to inspect global L2 memory before any typed L2 trust
or promotion work.

## Repository Map

```text
AITP-Research-Protocol/
|-- brain/
|   |-- v5/                 typed kernel, CLI, MCP wrappers, adapters, audits
|   `-- mcp_server.py       legacy L0-L4 MCP server
|-- hooks/                  v5 and legacy host lifecycle hooks
|-- deploy/templates/       host skill and runtime templates
|-- docs/                   install guides, protocol specs, plans, ledgers
|-- skills/                 legacy protocol skills
|-- contracts/              protocol contracts
|-- tests/                  legacy and v5 tests
`-- scripts/                install/update helpers
```

## Verification

For v5-focused development:

```powershell
$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }
pytest $files -q
python -m compileall -q brain\v5
git diff --check -- .
```

The historical full test suite includes legacy failures that are not necessarily
blockers for v5-only work. Treat the focused v5 suite as the current regression
gate unless a change touches legacy code.

## Key Docs

- [`docs/AITP_SPEC.md`](docs/AITP_SPEC.md) - protocol specification
- [`docs/INSTALL.md`](docs/INSTALL.md) - general install guide
- [`docs/INSTALL_CODEX.md`](docs/INSTALL_CODEX.md) - Codex adapter notes
- [`docs/INSTALL_CLAUDE_CODE.md`](docs/INSTALL_CLAUDE_CODE.md) - Claude Code setup
- [`docs/INSTALL_KIMI_CODE.md`](docs/INSTALL_KIMI_CODE.md) - Kimi Code setup
- [`docs/QUICKSTART.md`](docs/QUICKSTART.md) - older quickstart entrypoint
- [`docs/superpowers/progress/2026-05-20-aitp-v5-implementation-ledger.md`](docs/superpowers/progress/2026-05-20-aitp-v5-implementation-ledger.md) - v5 implementation ledger
- [`docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`](docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md) - current v5 planning source

## License

MIT. See [`LICENSE`](LICENSE).
