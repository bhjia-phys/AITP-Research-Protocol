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
| Typed research records | Implemented: topics, sessions, claims, evidence, code state, tool recipes/runs, references, physics objects, object relations, sensemaking, validation, checkpoints, promotion packets, L2 memory |
| Trust discipline | Implemented: summaries are orientation-only, validation gates trust, high-risk promotion needs evidence, passed validation, failure modes, and human review checkpoints |
| Long-term memory | Implemented core: L2 memory entries, promotion packets, memory audits, failure-mode audits, trust audits, Obsidian review views |
| Replay and review | Implemented core: session summaries, workspace summaries, workspace replay packets, source reconstruction audits |
| Legacy migration | Implemented migration, coverage, semantic-review, repair, source-reconstruction, human-checkpoint, and Obsidian worklist surfaces; the real legacy semantic review backlog remains blocking |
| Host integration | Priority hosts are ready for Codex, Claude Code, and Kimi Code through v5 MCP/hook/adapter surfaces and production-loop audits |
| OpenCode | Adapter/plugin surfaces exist, but OpenCode remains deferred until its hook model and packaging path stabilize |
| Goal continuation | Implemented: local `.aitp/surfaces/goal_continuation/` JSON+Markdown packets capture objective, commit range, changed files, tests, smoke commands, readiness, next actions, and blocking backlog |
| Literature intake | Implemented conservative intake: references are orientation-only, evidence/sensemaking are guarded suggestions, and trust updates stay forbidden without preflight/checkpoints |
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
5. Update downstream theory workspaces to the latest v5 kernel and regenerate
   topic-local runtime handoff files where needed.
6. Revisit OpenCode after its host hook model is stable enough for the same
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

- typed v5 kernel records under `.aitp/`
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
| `brain/v5/adapter_*` | Host adapter packets, bridge runners, and install/audit helpers |
| `hooks/aitp_v5_*` | Host lifecycle hooks and event runners |
| `.aitp/surfaces/` | Generated orientation outputs such as summaries and review views |

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

## Host Adapters

| Host | Current path | Notes |
|------|--------------|-------|
| Codex | `brain/v5/native_mcp.py` plus `adapter install-hooks codex` | v5 adapter and hook fixture surfaces exist. Codex one-click packaging is still less mature than the kernel path. See [`docs/INSTALL_CODEX.md`](docs/INSTALL_CODEX.md). |
| Claude Code | `adapter install-hooks claude-code` | Can generate or merge v5 lifecycle settings. See [`docs/INSTALL_CLAUDE_CODE.md`](docs/INSTALL_CLAUDE_CODE.md). |
| Kimi Code | `adapter install-hooks kimi-code` | Can generate or merge TOML hook config and use explicit MCP/skills loading. See [`docs/INSTALL_KIMI_CODE.md`](docs/INSTALL_KIMI_CODE.md). |
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
  --settings .kimi/config.toml

python -m brain.v5.cli --base /path/to/workspace adapter install-audit claude-code \
  --settings .claude/settings.local.json
```

Host hook files are runtime metadata. They may block unsafe actions or write
trace events, but they do not update scientific trust by themselves.

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
```

## Repository Map

```text
AITP-Research-Protocol/
├── brain/
│   ├── v5/                 typed kernel, CLI, MCP wrappers, adapters, audits
│   └── mcp_server.py       legacy L0-L4 MCP server
├── hooks/                  v5 and legacy host lifecycle hooks
├── deploy/templates/       host skill and runtime templates
├── docs/                   install guides, protocol specs, plans, ledgers
├── skills/                 legacy protocol skills
├── contracts/              protocol contracts
├── tests/                  legacy and v5 tests
└── scripts/                install/update helpers
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
