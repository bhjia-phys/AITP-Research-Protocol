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
| Host integration | Priority hosts are ready for Codex, Claude Code, and Kimi Code through v5 MCP/hook/adapter surfaces and production-loop audits; Hakimi now auto-configures a WorkFrame-scoped typed session bridge that can read `process_graph_slice`, compile `moment_policy.decisions` into required call obligations, and expose model-facing AITP write-bridge execution for exploratory records, research routes, source assets, auto-captured code state, proof obligations, validation contracts/results, and human checkpoints instead of duplicating the schema |
| OpenCode | Adapter/plugin surfaces exist, but OpenCode remains deferred until its hook model and packaging path stabilize |
| Goal continuation | Implemented: local `.aitp/surfaces/goal_continuation/` JSON+Markdown packets capture objective, commit range, changed files, tests, smoke commands, readiness, next actions, and blocking backlog |
| Literature intake | Implemented conservative intake: references are orientation-only, evidence/sensemaking are guarded suggestions, and trust updates stay forbidden without preflight/checkpoints |
| Theory research state | Implemented minimal conservative surface: `research-state register-source`, `attach-artifact`, `update-claim-status`, `create-proof-obligation`, `classify-event`, and `bounded-evidence` connect literature/results/artifacts/Fisherd-style runs to typed records without claim-trust promotion. `attach-artifact` is the stable artifact pointer write surface for benchmark logs, validation outputs, patches, plots, JSON results, and generated files |
| Typed process graph | Implemented first read-only slice: `aitp-v5 graph slice <session-id>` and `aitp_v5_get_process_graph_slice` compile typed records into orientation-only nodes, edges, source backtrace, `source_asset_index`, `source_stack_coverage`, `source_reconstruction_review`, relation neighborhoods, route state, provenance gaps, open obligations, trust-boundary reasons, recommended research moments, and a host-agnostic `moment_policy.decisions` list with `required_now`, `required_before_trust_change`, lifecycle trigger phases/conditions, split record/exploration entrypoints, and a host-facing `entrypoints` summary. The same policy is also exposed directly through `aitp-v5 graph moment-policy <session-id>` / `aitp_v5_get_host_agnostic_moment_policy` |
| Exploratory research graph | Implemented first typed record: `aitp-v5 exploration record` and `aitp_v5_record_exploratory_record` capture source assets, question decomposition, relation-path brainstorming, backtrace steps, and steering checkpoints as orientation-only graph records. Theory-facing fields now preserve why-question decomposition, relation-path questions, definition/derivation/source backtrace questions, backtrace targets, and original-question guards without updating claim trust |
| Research route state | Implemented first typed record: `aitp-v5 route record` and `aitp_v5_record_research_route` capture live routes, abandoned/blocked routes, branches, failed-attempt lessons, pivots, checkpoint links, and next actions as orientation-only process graph records. Route state can steer agents and preserve nonlinear research continuity, but it is not evidence, validation, or claim-trust authority |
| Canonical source assets | Implemented first typed record and projection: `aitp-v5 asset register` and `aitp_v5_register_source_asset` assign orientation-only identities, hashes, version anchors, duplicate-hash diagnostics, and source/code/artifact links to papers, lectures, notes, code repositories, snapshots, datasets, and generated artifacts; `process_graph_slice.source_asset_index[]` exposes that canonical source asset state to hosts without creating a second store |
| Source/code provenance automation | Implemented first automation: `aitp-v5 code state auto` and `aitp_v5_capture_code_state_auto` capture git HEAD, branch/upstream, dirty status, diff hash, optional patch artifacts, and linked topic/claim/session refs without requiring a host to hand-fill code-state fields |
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
- Treat research route records as local nonlinear process state: they preserve
  live routes, failed routes, branch/pivot rationale, checkpoint links, and next
  actions, but they are not evidence or validation and cannot update claim
  trust.
- Treat host-agnostic moment policy as read-only process guidance; it explains
  when typed records, brainstorming/backtrace, or trust preflight are needed,
  but it cannot update kernel state or claim trust.
- Treat `moment_policy.decisions[]` lifecycle fields as orientation-only trigger
  policy derived from typed records. They are not canonical truth records; a
  host may use them to decide when to call AITP entrypoints or final gates, but
  successful typed writes and trust preflight remain the authority.
- Treat exploratory-record reasoning fields as local theory-process handles.
  `reasoning_moves`, `backtrace_targets`, `relation_path_questions`,
  `definition_boundary_questions`, `derivation_backtrace_questions`,
  `source_dependency_questions`, and `original_question_guard` help hosts
  preserve nonlinear theoretical-physics thinking without promoting the
  exploration to evidence or claim trust.
- Treat downstream prompt rendering of those theory-process handles as a host
  projection. Hakimi now renders normalized theory reasoning into its WorkFrame
  reminder and ContextPack XML so a model can actually see the local
  brainstorm/backtrace constraints, but that rendering is not an AITP trust
  update and does not create a second canonical store.
- Treat `moment_policy.decisions[].entrypoints` as the host-facing call surface
  summary. Hakimi may compile it into blocking/current-turn call obligations,
  but the policy remains derived from AITP typed records and contracts.
- Treat route moments as process-continuity guidance unless AITP explicitly
  marks a trust boundary. Recording a route choice, failed-route lesson, or
  pivot checkpoint should make the agent less forgetful without turning route
  notes into final-gate blockers by default.
- Treat Hakimi final-gate checks over those call obligations as downstream host
  enforcement. They can force a status downgrade or require a recorded blocker,
  but they still do not mutate AITP trust or replace AITP preflight.
- Treat exploratory records as canonical process records for navigation,
  brainstorming, and backtrace continuity, but not as evidence or validation.
- Treat source asset records as canonical identities for raw papers, lectures,
  notes, code snapshots, datasets, and generated artifacts; they orient source
  backtrace and provenance, but they do not update claim trust by themselves.
- Treat `process_graph_slice.source_asset_index[]` as the read-only source
  asset projection for hosts. It carries asset ids, source kinds, URIs, hashes,
  hash status, version anchors, reference locations, linked artifact/code
  refs, duplicate diagnostics, and related provenance gap ids, but it remains
  orientation-only and cannot update claim trust.
- Treat `process_graph_slice.source_stack_coverage` as the read-only source
  stack coverage projection for hosts. It carries current claim coverage over
  required evidence outputs, source reconstruction components, review status,
  and next actions, but it is still derived guidance: it cannot update claim
  trust and does not become a final-gate blocker unless an explicit AITP
  trust/final prerequisite says so.
- Treat `process_graph_slice.source_reconstruction_review` as the read-only
  review worklist projection for hosts. It carries review status, review result
  refs, missing components, review packet commands, and remaining actions for
  source reconstruction, but it is still orientation-only guidance and cannot
  update claim trust.
- Treat `provenance_gaps[]` in process graph slices as orientation-only capture
  reminders. Missing source locations, source hashes, code state, tool runs, or
  benchmark artifacts should be fixed before reusing a ref as evidence,
  validation, benchmark basis, memory, or checked conclusion, but they are not
  final-gate blockers unless AITP explicitly marks `final_gate_required` or
  `required_before_trust_change`.
- Treat auto-captured code-state records as provenance records, not validation
  results. A dirty diff hash or patch artifact explains what code state was
  used; it does not prove the result correct.
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
6. Harden the source-store contract beyond the first `SourceAssetRecord`,
   `source_asset_index`, and code-state automation slices: the kernel now
   records duplicate-hash diagnostics, projects source asset hash/version/ref
   status into graph slices, and can auto-capture git code state, but stronger
   local PDF/lecture/code snapshot indexing and source-stack queries still
   need to keep a backtrace focused on the original physics question.
7. Harden the Hakimi runtime bridge against real topic stores. Hakimi sessions
   now auto-configure a dynamic AITP CLI bridge, consume process graph slices
   through explicit WorkFrame scope, compile `moment_policy.decisions` into
   ContextPack call obligations before research-context injection, preserve the
   cached AITP context when no fresh slice is available, run soft final-gate
   checks over unhandled required calls, and expose write-bridge hints and
   execution for exploratory records, research routes, proof obligations, human
   checkpoints, source assets, auto-captured code state, and validation records.
   Hakimi also has an opt-in real CLI smoke that creates
   a temporary AITP topic store, reads a real `process_graph_slice`, writes a
   proof obligation and checkpoint, and verifies the resulting `.aitp` records
   when `HAKIMI_AITP_REAL_CLI_SMOKE=1`, `AITP_V5_REPO`, and `AITP_V5_PYTHON`
   point at a working AITP Python environment. Richer MCP-first execution and
   MCP-first execution, strict AITP preflight/checkpoint enforcement, and richer
   evidence write-back still need later runtime integration slices.
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
| `aitp-v5 graph moment-policy <session-id>` | Read-only host-agnostic policy for when to record, brainstorm, backtrace, or stop at trust boundaries |
| `aitp-v5 exploration record` | Orientation-only typed record for brainstorming, backtrace, source-asset, and steering continuity |
| `aitp-v5 route record` | Orientation-only typed record for live routes, failed routes, branches, pivots, checkpoint links, and nonlinear research continuity |
| `aitp-v5 asset register` | Orientation-only canonical identity for raw papers, lectures, notes, code snapshots, datasets, and generated artifacts |
| `aitp-v5 code state auto` | Auto-capture git HEAD, branch/upstream, dirty status, diff hash, optional patch artifact, and linked topic/claim/session refs |
| `aitp-v5 research-state attach-artifact` | Attach a benchmark log, validation output, patch, plot, JSON result, or generated file by reference as an artifact record with hash/size metadata when local |
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
`aitp-v5 --base <base> graph slice <session-id>`, `graph moment-policy`,
`exploration record`, `route record`, `asset register`, `code state auto`,
`research-state attach-artifact`, `checkpoint request`,
`research-state create-proof-obligation`,
`validation contract create`, and `validation result record`. If the
`aitp-v5` console command is not installed in a local environment, use the
equivalent module invocation shown below.

The canonical runtime entrypoint contract is defined by
`brain/v5/runtime_entrypoints.py` and covered by
`tests/test_v5_runtime_entrypoints.py`. Hakimi and other hosts should consume
these names as the stable bridge contract, not infer names from README prose:

| Contract key | CLI template | MCP tool | Surface |
|--------------|--------------|----------|---------|
| `process_graph_slice` | `aitp-v5 graph slice <session-id>` | `aitp_v5_get_process_graph_slice` | `process_graph_slice` |
| `host_agnostic_moment_policy` | `aitp-v5 graph moment-policy <session-id>` | `aitp_v5_get_host_agnostic_moment_policy` | `host_agnostic_moment_policy` |
| `record_evidence` | `aitp-v5 evidence record <args>` | `aitp_v5_record_evidence` | `evidence_record` |
| `record_tool_run` | `aitp-v5 tool run record <args>` | `aitp_v5_record_tool_run` | `tool_run_record` |
| `record_reference_location` | `aitp-v5 reference location record <args>` | `aitp_v5_record_reference_location` | `reference_location_record` |
| `record_validation_result` | `aitp-v5 validation result record <args>` | `aitp_v5_record_validation_result` | `validation_result_record` |
| `record_exploratory_record` | `aitp-v5 exploration record <args>` | `aitp_v5_record_exploratory_record` | `exploratory_record` |
| `record_research_route` | `aitp-v5 route record <args>` | `aitp_v5_record_research_route` | `research_route_record` |
| `register_source_asset` | `aitp-v5 asset register <args>` | `aitp_v5_register_source_asset` | `source_asset_record` |
| `capture_code_state_auto` | `aitp-v5 code state auto <args>` | `aitp_v5_capture_code_state_auto` | `code_state_record` |
| `attach_artifact` | `aitp-v5 research-state attach-artifact <args>` | `aitp_v5_attach_artifact` | `artifact_record` |
| `create_proof_obligation` | `aitp-v5 research-state create-proof-obligation <args>` | `aitp_v5_create_proof_obligation` | `proof_obligation_record` |
| `update_proof_obligation` | `aitp-v5 research-state update-proof-obligation <args>` | `aitp_v5_update_proof_obligation` | `proof_obligation_record` |
| `create_validation_contract` | `aitp-v5 validation contract create <args>` | `aitp_v5_create_validation_contract` | `validation_contract_record` |
| `request_human_checkpoint` | `aitp-v5 checkpoint request <args>` | `aitp_v5_request_human_checkpoint` | `human_checkpoint_record` |
| `decide_human_checkpoint` | `aitp-v5 checkpoint decide <args>` | `aitp_v5_decide_human_checkpoint` | `human_checkpoint_record` |

The graph slice returns `moment_policy.decisions` as the typed policy surface
for hosts. Each decision carries whether it is `required_now`, which
`required_before_trust_change` prerequisites apply, which AITP `entrypoints`
should be used, and orientation-only lifecycle trigger metadata:
`lifecycle_phases`, `trigger_conditions`, `recording_threshold`,
`trust_boundary_inputs`, and `recommended_host_behavior`. These lifecycle
fields answer when a host should call AITP, brainstorm, backtrace, record, or
run a final gate, but they are policy guidance derived from typed records, not
canonical truth records themselves. Decisions also expose orientation-only
`payload_hints`: host-agnostic draft fields for the typed record that should be
written next, such as evidence, reference-location, exploratory, source-asset,
or validation-result records. These hints are not canonical truth and cannot
update claim trust; they keep hosts from inventing payload shapes while AITP
remains the authority for the actual record. Hakimi compiles these decisions
into ContextPack call obligations and now uses them in its final gate to
downgrade trust-sensitive answers when required calls are neither passed nor
explicitly blocked. Other hosts can consume the same read-only policy without
adopting Hakimi's runtime internals.

The graph slice also exposes `provenance_gaps[]`: orientation-only hints for
missing reference locations, source assets, source hashes, duplicate source
hashes, code state, tool runs, validation artifacts, and benchmark artifacts.
Those gaps compile into recommended `capture_source_or_code_provenance`
moments, but they remain process guidance by default. They only become strict
trust boundaries when the typed AITP payload explicitly says they are required
before a trust change or final gate.

The same slice now exposes `source_stack_coverage`: the scoped
`source_stack_coverage_manifest` for claims present in the slice. Hosts can see
which required outputs are still missing, which source reconstruction
components are incomplete, whether the latest source reconstruction review has
passed, and which coverage next actions AITP recommends. This is a compact
coverage/readiness projection for local action planning, not a second truth
store and not a claim-trust update.

The graph slice also exposes `source_reconstruction_review`: the scoped
`source_reconstruction_review_manifest` for the same claims. Hosts can see
pending, needs-revision, inconclusive, and passed review state, plus review
packet/result CLI hints and remaining actions. This lets a runtime surface the
actual review worklist beside coverage gaps instead of inferring review state
from a loose next-action string.

Exploratory record reasoning fields are likewise host-facing process handles:
Hakimi normalizes them into `params.theoryReasoning`, then renders them into the
injected WorkFrame reminder and ContextPack XML `<theory_reasoning>` bindings.
This makes relation-path, definition/derivation/source-backtrace, and
original-question-continuity constraints visible at the local action boundary
while keeping AITP typed records as the authority.

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
- source assets with hash, version, and duplicate-hash diagnostics
- code-state provenance, including auto-captured git HEAD, dirty diff hash, and
  optional patch artifacts
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
