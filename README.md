<p align="center">
  <img src="plugins/aitp-research-protocol/assets/icon.svg" alt="AITP icon" width="128" height="128">
</p>

# AITP - AI Research Graph Kernel For Physics

AITP is a local research graph kernel for theoretical and computational
physics. It gives AI agents and human researchers a shared, typed memory of
claims, sources, derivations, code runs, validation results, failed routes,
domain experience, and trust boundaries.

The long-term goal is to make AITP the AI-facing research memory layer: agents
can retrieve the right slice of prior knowledge, methods, literature, and
experience through explicit context interfaces instead of relying on chat
history, hidden model memory, or ungrounded retrieval snippets.

AITP is not a chatbot, a generic note app, an automatic theorem prover, or a
plain RAG index. It is a truth-preserving substrate for scientific work: context
can orient an agent, but only typed evidence, validation, and promotion records
can support trusted research memory.

## At A Glance

| Question | Answer |
|----------|--------|
| Current version | AITP 1.0.0, implementation generation v5 |
| Primary identity | Local research graph kernel and AI research memory layer |
| Active implementation | [`brain/v5/`](brain/v5/) |
| Source of truth | Typed records under `<topics-root>/.aitp/` |
| Context model | Compile bounded context packs from the graph for each task |
| Experience model | Domain experience packs and curated literature context sit above the memory kernel |
| Main agent entrypoint | MCP server at [`brain/v5/native_mcp.py`](brain/v5/native_mcp.py) |
| Best default install | Project-scope install with [`scripts/aitp-pm.py`](scripts/aitp-pm.py) |
| Codex path | Repository-backed plugin at [`plugins/aitp-research-protocol/`](plugins/aitp-research-protocol/) |
| Codex 1.0 plan | [`docs/CODEX_APP_1_0_PLAN.md`](docs/CODEX_APP_1_0_PLAN.md) |
| Health checks | `scripts/aitp-pm.py status` and `scripts/aitp-pm.py doctor` |
| Trust rule | Summaries, RAG, dashboards, and domain packs orient agents; typed evidence and validation carry trust |

## Choose An Install Path

| If you want... | Use this path | Why |
|----------------|---------------|-----|
| One research workspace shared by Codex, Claude Code, and Kimi Code | Project-scope install | Keeps MCP config, skills, hooks, and topics root local to that workspace |
| Codex App access with a visible local plugin | Codex plugin | Installs a Codex plugin package with first-run setup tools |
| AITP available across your whole user account | User-scope install | Writes host config under user-level agent directories |
| A custom or unsupported host | Manual MCP setup | Point the host directly at `brain/v5/native_mcp.py` |

For research work, project scope is the safest default. It avoids surprising
global config changes and makes every agent point at the same topics root.

## Quick Start

### Project-Scope Install

```bash
git clone https://github.com/bhjia-phys/AITP-Research-Protocol.git
cd AITP-Research-Protocol

uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py install \
  --agent all \
  --scope project \
  --target-root /absolute/path/to/workspace \
  --topics-root /absolute/path/to/workspace/research/aitp-topics

uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py status

uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py doctor
```

Then restart Codex, Claude Code, Kimi Code, or any other configured host so it
reloads project-local MCP and skill files.

### Codex Plugin

```bash
codex plugin marketplace add .agents/plugins
codex plugin add aitp-research-protocol@aitp-local
codex plugin list --marketplace aitp-local
```

On first use, the plugin starts in setup mode if it cannot find an AITP
checkout. Codex can then call:

- `aitp_config_status`
- `aitp_suggest_config`
- `aitp_configure(repo_root="...", topics_root="...")`

After `aitp_configure` succeeds, restart Codex or open a new thread. Codex
should enter through the plugin skills, read compact AITP context first, and
expand to deeper `aitp_v5_*` tools only when the research step needs them.

### Success Signals

- `doctor` reports no blocking install issues.
- `status` lists the installed agent and scope you expect.
- The host exposes the `aitp` MCP server or AITP plugin tools after restart.
- AITP records are written under the configured topics root, not into the plugin
  cache.

## Positioning And Goal

AITP is designed around a human-in-the-loop research loop, but its core
positioning is broader than workflow control. It is the persistent research
graph that lets AI agents reuse prior scientific work without confusing memory,
retrieval, evidence, validation, and trust.

The target architecture has four layers:

1. **Research graph kernel.** The canonical `.aitp` store preserves typed
   records for sources, claims, formulas, objects, evidence, code state, tool
   runs, validations, checkpoints, and trust updates.
2. **Context compiler.** Agent-facing tools expose bounded context packs,
   execution briefs, relation maps, source stacks, dashboards, and review
   packets derived from the graph.
3. **Domain experience packs.** Specialized packs, such as LibRPA/GW and
   first-principles workflows, encode proven workflows, common failure modes,
   validation recipes, provenance checks, and tool conventions.
4. **Literature and note knowledge layer.** Local PDFs, papers, notebooks, and
   curated corpora provide source-backed orientation for quantum field theory,
   quantum gravity, topological order, computational physics, and other domains.

The basic research loop remains:

1. A human or agent works on a theoretical-physics problem.
2. Durable research moments are written into a typed graph.
3. Agents read compiled context from that graph through MCP or CLI tools before
   acting.
4. Evidence, validation, proof gaps, route changes, and human decisions stay
   distinguishable.
5. Trust or long-term memory promotion only happens after explicit checks.

The protocol tries to enforce one central distinction:

```text
context and orientation != evidence
tool execution != validation
summary != truth
claim status != proof
```

This makes AITP useful for long-running research where intermediate process
matters: literature reading, derivations, numerical checks, code-method
development, failed routes, benchmark provenance, and final synthesis.

## Current Implementation

The current release is **AITP 1.0.0**. Its implementation generation is
**v5**. The active code is under [`brain/v5/`](brain/v5/).

AITP v5 implements this positioning through four implementation layers:

1. **Typed research graph** stored on disk under a workspace-local `.aitp/`
   directory.
2. **Derived context surfaces** such as context packs, active-claim focus,
   execution briefs, relation maps, process graph slices, source audits, note
   outlines, domain recommendations, and recording navigation state.
3. **Agent-facing MCP server** at
   [`brain/v5/native_mcp.py`](brain/v5/native_mcp.py), exposing `aitp_v5_*`
   tools for reading and writing graph records.
4. **CLI, plugin, and installer utilities** for diagnostics, fallback operations, and
   project setup.

The normal architecture is:

```text
human / Codex / Claude Code / Kimi Code / Hakimi / other agent
        |
        v
Codex skills / MCP tools: compact context -> aitp_v5_* expansion
        |
        v
AITP v5 typed records under <topics-root>/.aitp/
        |
        v
derived briefs, graph slices, audits, relation maps, summaries
```

The typed records are the source of truth. Briefs, dashboards, process graph
slices, summaries, domain packs, curated RAG views, and audits are derived or
orientation surfaces. They are useful for navigation and domain steering, but
they do not update trust by themselves.

Legacy L0-L4 Markdown tools are read-only by default in 1.0.0. Historical files
and legacy servers remain for audit, migration, rollback, and tests, but normal
research writes must go through `aitp_v5_*` typed tools. Setting
`AITP_LEGACY_ENABLE_WRITES=1` is an explicit migration-debug escape hatch, not a
normal runtime mode.

## What AITP Can Do Today

AITP v5 currently supports:

- project and topic initialization
- topic, session, claim, and claim-status records
- source and reference-location records
- source assets, artifacts, hashes, and output locations
- physics objects, definitions, notation, relations, equations, and assumptions
- code state, tool recipes, tool runs, and execution provenance
- evidence records linked to claims, sources, artifacts, and tool runs
- validation contracts and validation results
- proof obligations and unresolved theory gaps
- route choices, pivots, blocked attempts, and exploratory reasoning
- human checkpoints and checkpoint decisions
- trust preflight, trust update records, and memory-promotion packets
- read-only execution briefs, claim relation maps, graph slices, and audits
- progressive recording navigation for deciding where a durable moment belongs
- domain-conditioned tool and validation recommendations
- curated RAG manifests for heuristic literature and note orientation
- project-scope adapter installs for Codex, Claude Code, and Kimi Code
- a repository-backed Codex plugin with first-run configuration tools
- migration and recovery audits for older AITP topic stores

AITP is strongest when the research question has durable structure:

- formal or derivation-heavy theoretical work,
- numerical/model claims that require provenance and validation,
- scientific-code method development,
- literature-to-claim reconstruction,
- long projects that need handoff between sessions or agents.

## What AITP Does Not Do

AITP deliberately does not:

- prove physics claims automatically,
- decide final scientific truth without evidence and validation,
- record every chat turn or every tool call,
- promote summaries into trusted memory by default,
- treat RAG chunks or retrieved PDFs as evidence without source-linked records,
- let a domain experience pack bypass validation or human checkpoints,
- replace human judgment at theory or trust boundaries,
- guarantee that every host application fires lifecycle hooks perfectly.

The kernel is a truth-preserving substrate. The host agent still has to do the
research work and call the right tools at the right moments.

## Research Graph Layout

A workspace normally has a topics root:

```text
<workspace>/research/aitp-topics/
```

The canonical AITP store is:

```text
<workspace>/research/aitp-topics/.aitp/
```

The v5 store is organized like this:

```text
.aitp/
|-- topics/        topic-local runtime views and dashboards
|-- contexts/      research context records
|-- registry/      typed graph records
|-- runtime/       sessions and runtime state
|-- memory/        promoted scoped research memory
|-- surfaces/      generated read-only views and review packets
|-- tools/         tool metadata and tool surfaces
|-- curated_rag/   optional heuristic literature and note context
|-- source_blobs/  topic-scoped local copies of acquired source files
|-- migrations/    migration audits and old-store accounting
`-- schemas/       schema and contract material
```

The core graph records live under `registry/`. Important record families include
`claims`, `evidence`, `reference_locations`, `source_assets`,
`physics_objects`, `object_relations`, `code_states`, `tool_recipes`,
`tool_runs`, `validation_contracts`, `validation_results`,
`proof_obligations`, `research_runs`, `research_run_events`, `checkpoints`,
`promotion_packets`, and `trust_updates`.

### Source PDF acquisition

`aitp-v5 asset register` remains metadata-only for normal URLs and arXiv
identifiers. To make a paper available for later local reading, use:

```text
aitp-v5 asset acquire-pdf --topic <topic-id> --url <http/https/file-url> --title <title>
aitp-v5 asset acquire-arxiv --topic <topic-id> --arxiv-id <arxiv-id> --title <title>
```

Successful acquisitions copy the PDF into
`.aitp/source_blobs/<topic_id>/<asset_id>/original.pdf` and write the local
path, source URL, final URL, SHA-256, MIME type, file size, and acquisition time
back to the typed `source_asset` record. Failed acquisitions still write an
honest orientation-only `source_asset` record with `acquisition_status=failed`
and `failure_reason`; they do not pretend that a local PDF exists.

For existing local files, `aitp-v5 asset capture-auto` still records the
original path by default. Add `--copy-to-store` when the file should also be
copied into the v5 blob store.

Source assets are source identities only. They are not evidence records and
cannot update claim trust; evidence, validation, and promotion remain separate
typed operations.

More detail: `docs/v5-source-asset-pdf-acquisition.md`.

## How Agents Should Use AITP

AITP should be used as a progressive, read-first protocol. The agent should
classify the research process before choosing graph actions: setup, new topic
exploration, existing topic continuation, literature discussion, derivation,
code/numerical work, synthesis/writing, or closeout.

For status questions or old-topic recovery, agents should usually read only:

1. find the topic/session/claim,
2. read the compact context pack or active-claim focus when available,
3. read the execution brief and claim relation map only when support,
   validation, blockers, or next actions matter,
4. summarize current support, limits, blockers, and next valid actions without
   treating summaries as evidence.

For active research, agents should write only at durable moments:

- a reusable source or source location was identified,
- a tool/code run produced research-relevant output,
- an artifact, report, table, plot, log, or raw dump was produced,
- a result, anomaly, contradiction, negative result, or failed check appeared,
- a proof gap, validation gap, missing provenance, or route blocker was found,
- a route was selected, pivoted, abandoned, or split,
- claim scope/status changed or needs review,
- a human checkpoint or promotion decision is needed,
- a session-end handoff creates durable future context,
- a note or paper draft uses a new source that must be registered.

The recommended recording flow is:

```text
classify recording candidate
        |
        v
read first-level recording navigation state
        |
        v
expand exactly one slot
        |
        v
call the named typed write/preflight tool, or in Codex compact mode call aitp_v5_codex_record_apply
        |
        v
verify the recording effect, using the apply result in compact Codex mode
```

This keeps the graph useful without making the agent write on every internal
thought step.

For literature and note-writing work, AITP separates source layers:
`source_asset` identifies a source, `reference_location` records exact pages,
sections, equations, figures, URLs, or local-note locations, artifacts preserve
reading notes or drafts, and `evidence` is created only when the source is tied
to a specific AITP claim. Source identity alone must not be promoted into
claim support.

## Using AITP After Install

For Codex plugin users, start a new Codex thread after plugin setup and ask to
use AITP for the current physics topic. If the plugin is still in setup mode,
Codex should call `aitp_config_status`, ask for the missing paths, then call
`aitp_configure`.

For project-scope adapter installs, open the target workspace in the host agent.
The installed gateway skills tell the agent to read AITP context first and then
call `aitp_v5_*` MCP tools for durable records.

The normal use pattern is:

1. Classify the request intensity and research process.
2. Find or create the topic/session/claim only when the work has a durable
   objective.
3. Read compact context first, then relation maps, process graph, source stack,
   or trust audits only when needed.
4. Do the research work in the host agent.
5. Record only durable sources, artifacts, evidence, validation results, proof
   gaps, route changes, and human decisions.
6. Run status, source reconstruction, relation-map, or trust-audit tools before
   treating a result as trusted context.

When MCP is unavailable, use the CLI layer below as a diagnostic and fallback
surface. Do not manually edit `.aitp/registry` records as a substitute for typed
tools.

## MCP Tool Layer

The MCP server entrypoint is:

```text
brain/v5/native_mcp.py
```

MCP hosts should run that file directly. Do not point MCP at `aitp-v5` or at the
legacy servers.

If a host accidentally calls a legacy write tool such as
`aitp_bootstrap_topic`, `aitp_submit_candidate`, or `aitp_promote_candidate`,
the legacy stdio/HTTP wrappers return a JSON-RPC error instead of writing old
`state.md`, L0, L1, L3, L4, or legacy L2 files. Legacy read tools may still be
used for orientation and migration discovery.

Generic MCP config shape:

```json
{
  "mcpServers": {
    "aitp": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "pyyaml",
        "--with",
        "jsonschema",
        "--with",
        "fastmcp",
        "python",
        "/absolute/path/to/AITP-Research-Protocol/brain/v5/native_mcp.py"
      ],
      "cwd": "/absolute/path/to/AITP-Research-Protocol",
      "env": {
        "AITP_TOPICS_ROOT": "/absolute/path/to/workspace/research/aitp-topics"
      }
    }
  }
}
```

Different hosts use slightly different config keys. The installer writes the
correct project-local files for supported hosts.

## CLI Layer

The CLI is useful for diagnostics, smoke tests, scripted fallback operations,
and local inspection.

Use it from the repository root:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python -m brain.v5.cli --help
```

Common commands:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python -m brain.v5.cli init /path/to/workspace/research/aitp-topics

uv run --with pyyaml --with jsonschema --with fastmcp \
  python -m brain.v5.cli --base /path/to/workspace/research/aitp-topics brief <session-id>

uv run --with pyyaml --with jsonschema --with fastmcp \
  python -m brain.v5.cli --base /path/to/workspace/research/aitp-topics relation-map <session-id>

uv run --with pyyaml --with jsonschema --with fastmcp \
  python -m brain.v5.cli --base /path/to/workspace/research/aitp-topics workspace recording-audit

uv run --with pyyaml --with jsonschema --with fastmcp \
  python -m brain.v5.cli --base /path/to/workspace/research/aitp-topics recording navigation-state <session-id>
```

If you have linked the Node wrapper from `package.json`, `aitp-v5` is a shorter
alias for the same v5 CLI. The repository-local `uv run ... python -m
brain.v5.cli` form is the most explicit and portable.

## Install

Prerequisites:

- Git
- Python 3.10 or newer
- `uv` recommended for dependency isolation
- at least one supported host agent if you want automatic agent wiring:
  Codex, Claude Code, or Kimi Code

Clone the repository:

```bash
git clone https://github.com/bhjia-phys/AITP-Research-Protocol.git
cd AITP-Research-Protocol
```

### Recommended: Project-Scope Install

Project-scope install keeps AITP configuration inside one research workspace.
This is the safest mode for reproducible research and multi-agent use.

Use this when a workspace such as `/absolute/path/to/workspace` owns the actual
research files and should also own its AITP topics root.

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py install \
  --agent all \
  --scope project \
  --target-root /absolute/path/to/workspace \
  --topics-root /absolute/path/to/workspace/research/aitp-topics
```

This installs workspace-local adapter files such as:

- `.mcp.json`
- `.codex/skills/...`
- `.codex/mcp.json`
- `.codex/config.toml`
- `.codex/hooks/...` and `.codex/hooks.json`
- `.claude/...`
- `.kimi/...`
- `.kimi-code/...`

The exact files depend on the selected agent and the host's conventions.

Default project hooks are deliberately lightweight:

- Claude Code and Codex get `aitp-keyword-router.py` and
  `aitp-routing-guard.py`.
- The keyword router is only an orientation reminder; it never writes AITP state.
- The routing guard blocks direct `Write`, `Edit`, and `MultiEdit` writes into
  AITP state stores until typed v5 routing has been confirmed.
- `aitp-v5-hook.py`, `aitp-v5-claude-hook.py`, `aitp-v5-kimi-hook.py`, and
  `aitp-v5-adapter-event-runner.py` are session-bound bridge assets. They are
  not enabled by the default project install because they require a concrete v5
  session id and must not update claim trust.
- Kimi and Kimi Code project installs write skills and MCP config by default.
  Kimi hook TOML should be generated only when the installed host supports
  project `[[hooks]]`, using workspace-local `.kimi/config.toml` or
  `.kimi-code/config.toml`.

Project-scope install does **not** register a global `aitp` wrapper. It keeps
host configuration local to the target workspace.

To install only one host, change `--agent all` to `--agent codex`,
`--agent claude-code`, or `--agent kimi-code`.

### Optional: User-Scope Install

User-scope install writes into user-level agent config locations. Use it only if
you intentionally want AITP available globally for that host account. A bare
install defaults to user scope.

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py install \
  --agent codex \
  --scope user \
  --topics-root /absolute/path/to/workspace/research/aitp-topics
```

User scope may register a global `aitp` package-manager wrapper when possible.
For shared or sensitive research machines, prefer project scope.

### Verify Install

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py status

uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py doctor
```

`status` reads `~/.aitp/install-record.json` and reports recorded installs.
`doctor` checks Python dependencies, the 1.0.0/v5 version contract, v5 server
files, topics root health, MCP entrypoints, project-scope consistency, and
common stale-residue problems.

After installing or changing MCP config, restart the host agent so it reloads
its MCP servers and skills.

For direct host checks:

- Codex: `codex mcp get aitp`
- Claude Code: inspect the project `.mcp.json` or configured Claude MCP entry.
- Kimi Code: inspect `.kimi-code/mcp.json` and `.kimi/mcp.json` if both paths
  exist on the machine.

### Optional: Codex Plugin

The repository also ships a local Codex plugin at
[`plugins/aitp-research-protocol/`](plugins/aitp-research-protocol/). The plugin
wraps the v5 MCP server and gateway skills in a Codex plugin package. This is
the friendliest Codex App route, but it is still local: the plugin needs an
AITP checkout and writes research records to a configured topics root.

<p>
  <img src="plugins/aitp-research-protocol/assets/icon.svg" alt="AITP Research Protocol plugin icon" width="96" height="96">
</p>

Install the repo-local marketplace once:

```bash
codex plugin marketplace add .agents/plugins
codex plugin add aitp-research-protocol@aitp-local
codex plugin list --marketplace aitp-local
```

On first use, if the plugin cannot find an AITP checkout, it starts in setup
mode instead of failing. Setup mode exposes `aitp_config_status`,
`aitp_suggest_config`, and `aitp_configure`, so Codex can ask for:

- the local `AITP-Research-Protocol` checkout path,
- the topics root where AITP should store records.

The plugin saves this to `~/.aitp/codex-plugin-config.json`. After
configuration, restart Codex or open a new thread. The plugin launcher sets
`AITP_MCP_SURFACE=codex` by default, so Codex sees a compact facade:
`aitp_v5_codex_enter`, `aitp_v5_codex_expand`,
`aitp_v5_codex_recording_step`, `aitp_v5_codex_record_apply`,
`aitp_v5_codex_literature_step`, and `aitp_v5_codex_closeout`. Set
`AITP_MCP_SURFACE=full` only for kernel
development or maintenance sessions that need the complete `aitp_v5_*` surface.

The plugin resolves paths in this order:

1. `AITP_REPO_ROOT` and `AITP_TOPICS_ROOT` environment variables.
2. `~/.aitp/codex-plugin-config.json`.
3. `~/.aitp/install-record.json` from `scripts/aitp-pm.py install`.
4. `vendor/AITP-Research-Protocol` inside the plugin directory.
5. The current working directory or one of its parents.

Remove the plugin with:

```bash
codex plugin remove aitp-research-protocol@aitp-local
```

That removes the Codex plugin registration and cache. It does not delete the
AITP repository checkout, the topics root, or adapter files installed by
`scripts/aitp-pm.py`; use the uninstall commands below for those.

## Update

Use `update` when the checkout already contains the code you want and you only
need to redeploy recorded host files:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py update
```

Use `upgrade` when you want the package manager to pull the latest repository
changes and redeploy recorded installs:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py upgrade
```

If the working tree has local changes, `upgrade` stops unless you pass
`--force`, which stashes before pulling. Run `doctor` after update or upgrade.

## Uninstall

Use the package manager whenever possible. It removes generated host files that
AITP recorded during install and updates `~/.aitp/install-record.json`.

Project-scope uninstall:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py uninstall \
  --agent all \
  --scope project \
  --target-root /absolute/path/to/workspace
```

User-scope uninstall:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py uninstall \
  --agent all \
  --scope user
```

Then verify:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py status
```

Uninstall does not delete the AITP repository checkout or the topics root that
contains research records. Delete those manually only when you are sure they are
no longer needed. Manual cleanup notes are in
[`docs/UNINSTALL.md`](docs/UNINSTALL.md).

## Hakimi And Other Harnesses

AITP can be used by a specialized research harness or by a general coding
agent.

For Hakimi-style integration:

- Hakimi owns the live work loop and workframes.
- AITP owns durable scientific records and trust boundaries.
- Hakimi should read AITP context through MCP, write durable moments through
  typed AITP tools, and avoid maintaining a parallel scientific truth layer.

For a generic agent harness:

- expose only a small AITP entry surface at startup,
- let the agent discover deeper graph structure progressively,
- use read tools for navigation and context,
- use typed write tools only at durable research moments,
- run trust preflight before confidence or memory-promotion changes.

Hooks can help with routing reminders, direct-write guards, session start,
pre-tool policy, post-tool trace capture, or stop-time handoffs, but hooks are
runtime metadata. They should not be treated as scientific evidence or trusted
memory by themselves, and they must not update claim trust.

## Codex App 1.0 Direction

AITP 1.0 specializes the Codex App path around a small default surface and
progressive expansion. The full plan is
[`docs/CODEX_APP_1_0_PLAN.md`](docs/CODEX_APP_1_0_PLAN.md).

The target layers are:

- typed research graph and provenance records;
- compact agent context over that graph;
- process-mode routing for new topics, continuation, literature reading,
  derivation, numerical work, writing, synthesis, and closeout;
- progressive MCP exposure: setup, entry, read expansion, guided recording, and
  trust/promotion gates;
- Codex skills as the reliable control plane;
- hooks as optional reminders, guards, and trace capture;
- note and paper writing that registers web/literature references into the
  correct source, location, evidence, physics-object, validation, and trust
  layers.

This direction preserves the same boundary: AITP records research truth through
typed records, not through unverified summaries, web snippets, hook traces, or
hidden agent memory.

### Codex Hooks And Closeout

Codex App hooks are helpers, not the research control plane. The default
project hooks may detect AITP-looking prompts and block direct writes into AITP
state stores, but they must not create evidence, validation, memory, trust
updates, or promotion records.

Use the Codex facade for session lifecycle:

- `aitp_v5_codex_enter` at the start or when a discussion becomes research;
- `aitp_v5_codex_recording_step` when a durable moment appears;
- `aitp_v5_codex_literature_step` when a paper, web source, or local note enters
  reusable context;
- `aitp_v5_codex_closeout` when the session needs a handoff.

`aitp_v5_codex_closeout` previews by default. It writes a quiet checkpoint only
when called with `apply=true`, and that checkpoint still cannot update claim
trust.

Quiet checkpoint is a process record, not a complete research package. Every
quiet checkpoint preview/apply and Codex closeout now returns
`record_completeness_audit`. Agents must inspect it before telling the user that
"AITP was recorded." The audit reports `recorded_slots`,
`missing_recommended_slots`, `recommended_next_records`, `trust_boundary`, and
`requires_user_confirmation`.

For code or numerical work, "record AITP" means at least checking whether the
closeout needs:

- `artifact` for durable PDF/report/note/plot/data/log outputs;
- `code_state` for changed files, scripts, worktree-dependent results, or repo
  paths;
- `validation_result` or a validation-gap record when commands were run or the
  closeout states a validation boundary.

Missing slots are plan-only recommendations. They do not auto-create evidence,
validation, or trust promotion. If the audit says a durable package is
incomplete, the agent should report the missing slots or fill them through the
existing typed write tools and user-confirmed gates. Trust promotion still
requires separate preflight and the explicit human gate.

## Repository Map

```text
AITP-Research-Protocol/
|-- brain/v5/              current typed kernel, CLI, MCP tools, adapters
|-- brain/mcp_server.py    legacy L0-L4 MCP server, read-only by default
|-- deploy/                host templates and agent-facing skill material
|-- docs/                  protocol docs, install notes, historical designs
|-- hooks/                 lifecycle hook runners and guards
|-- scripts/               installer, maintenance, migration helpers
|-- tests/                 v5 and compatibility tests
|-- bin/aitp-v5.mjs        optional Node CLI wrapper
`-- package.json           optional package metadata for the CLI wrapper
```

New integrations should use `brain/v5/native_mcp.py` and `brain/v5/`.
Legacy L0-L4 files remain for migration and historical interpretation only;
they are not the active 1.0.0 research workflow.

## Development Checks

For v5-focused changes:

```bash
python -m compileall -q brain/v5
pytest tests -q
git diff --check -- .
```

For narrow changes, run the focused tests that cover the touched surface first.
Some legacy tests describe older protocol behavior, so prefer v5-specific tests
when modifying v5 runtime, MCP, graph, or adapter code.

## Key Docs

- New user path: start with this README, then run `doctor`, then read the
  host-specific install note for the agent you use.
- Positioning path: read [`docs/AITP_POSITIONING.md`](docs/AITP_POSITIONING.md)
  to understand AITP as a research graph kernel, context compiler, and domain
  experience substrate.
- Protocol path: read [`docs/AITP_SPEC.md`](docs/AITP_SPEC.md) before changing
  typed-record behavior, trust rules, or human-facing output contracts.
- Cleanup path: use [`docs/UNINSTALL.md`](docs/UNINSTALL.md) before manually
  deleting generated host files.

- [`docs/AITP_POSITIONING.md`](docs/AITP_POSITIONING.md) - product and architecture positioning
- [`docs/AITP_SPEC.md`](docs/AITP_SPEC.md) - protocol specification
- [`docs/CODEX_APP_1_0_PLAN.md`](docs/CODEX_APP_1_0_PLAN.md) - Codex App 1.0 architecture and implementation plan
- [`docs/INSTALL.md`](docs/INSTALL.md) - install guide
- [`docs/UNINSTALL.md`](docs/UNINSTALL.md) - manual uninstall notes
- [`docs/INSTALL_CODEX.md`](docs/INSTALL_CODEX.md) - Codex adapter notes
- [`docs/INSTALL_CLAUDE_CODE.md`](docs/INSTALL_CLAUDE_CODE.md) - Claude Code setup
- [`docs/INSTALL_KIMI_CODE.md`](docs/INSTALL_KIMI_CODE.md) - Kimi Code setup

## License

MIT. See [`LICENSE`](LICENSE).
