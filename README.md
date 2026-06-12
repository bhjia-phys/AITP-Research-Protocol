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
| Host integration | Priority hosts are ready for Codex, Claude Code, and Kimi Code through v5 MCP/hook/adapter surfaces and production-loop audits; `aitp-v5 adapter bridge-targets` / `aitp_v5_get_runtime_bridge_target_manifest` now expose MCP-first host bridge targets with CLI fallback templates; `aitp-v5 adapter payload-profiles` / `aitp_v5_get_runtime_payload_profiles` expose the read-only runtime payload profile catalog directly; `aitp-v5 adapter record-ref-lookup <refs...>` / `aitp_v5_lookup_record_refs` expose a read-only typed-store existence check for canonical refs without source support, validation, evidence creation, or claim-trust authority; `aitp-v5 adapter curated-rag-chunk <chunk-id>` / `aitp_v5_get_curated_rag_chunk` expose read-only curated RAG chunk/document identity, hashes, source URI, and anchor metadata before any promotion draft; `runtime_payload_profiles` tells hosts how to turn benchmark adapter runs and primitive tool lifecycle completions into AITP `tool_run_record` provenance without creating validation/trust, now includes `catalog_version`, `profile_count`, `profile_index`, `capture_policy`, and `host_usage_policy` metadata for metadata-only host reads, controlled adapter auto-capture, explicit primitive-tool capture, diagnostics, and no-trust exclusions; Hakimi auto-configures a WorkFrame-scoped typed session bridge that can read `process_graph_slice`, compile `moment_policy.decisions` into required call obligations, read/inspect the runtime payload profile catalog as AITP-owned metadata, look up reviewed source/reference record refs as typed-existence-only metadata, inspect individual curated RAG chunk identities/anchors/hashes, automatically request bounded curated RAG `heuristic_context` for background-oriented turns, request the read-only `literature_source_review_handoff` only from explicit no-trust literature review cues, inspect read-only `literature_comparison_draft` packets for bounded `source.compare_literature` planning, and expose model-facing AITP write-bridge execution for curated RAG corpus ingestion, exploratory records, research routes, source assets, auto-captured local source assets, auto-captured code state, auto-captured local artifacts, proof obligations, validation contracts/results, human checkpoints, and non-mutating trust preflight instead of duplicating the schema |
| OpenCode | Adapter/plugin surfaces exist, but OpenCode remains deferred until its hook model and packaging path stabilize |
| Goal continuation | Implemented: local `.aitp/surfaces/goal_continuation/` JSON+Markdown packets capture objective, commit range, changed files, tests, smoke commands, readiness, next actions, and blocking backlog |
| Literature intake | Implemented conservative intake, source-review handoff, and read-only comparison draft: references are orientation-only, evidence/sensemaking are guarded suggestions, trust updates stay forbidden without preflight/checkpoints, `aitp-v5 literature source-review-handoff` / `aitp_v5_build_literature_source_review_handoff` composes literature intake, record-ref lookup, source-stack coverage, and source reconstruction review into a read-only host packet, and `aitp-v5 literature comparison-draft` / `aitp_v5_build_literature_comparison_draft` scaffolds source-set dimensions, agreement/disagreement/missing-evidence sections, allowed next entrypoints, forbidden uses, and the `source.compare_literature` next action without creating comparison records, evidence, validation, writes, final-gate satisfaction, or claim-trust authority |
| Theory research state | Implemented minimal conservative surface: `research-state register-source`, `attach-artifact`, `attach-artifact-auto`, `update-claim-status`, `create-proof-obligation`, `classify-event`, and `bounded-evidence` connect literature/results/artifacts/Fisherd-style runs to typed records without claim-trust promotion. `attach-artifact` is the stable artifact pointer write surface for benchmark logs, validation outputs, patches, plots, JSON results, and generated files; `attach-artifact-auto` lets AITP compute local artifact file metadata before writing the same artifact record |
| Typed process graph | Implemented first read-only slice: `aitp-v5 graph slice <session-id>` and `aitp_v5_get_process_graph_slice` compile typed records into orientation-only nodes, edges, source backtrace, `source_asset_index`, `source_stack_coverage`, `source_reconstruction_review`, relation neighborhoods, route state, provenance gaps, open obligations, trust-boundary reasons, recommended research moments, and a host-agnostic `moment_policy.decisions` list with `required_now`, `required_before_trust_change`, lifecycle trigger phases/conditions, split record/exploration entrypoints, and a host-facing `entrypoints` summary. The same policy is also exposed directly through `aitp-v5 graph moment-policy <session-id>` / `aitp_v5_get_host_agnostic_moment_policy` |
| Exploratory research graph | Implemented first typed record: `aitp-v5 exploration record` and `aitp_v5_record_exploratory_record` capture source assets, question decomposition, relation-path brainstorming, backtrace steps, and steering checkpoints as orientation-only graph records. Theory-facing fields now preserve why-question decomposition, relation-path questions, definition/derivation/source backtrace questions, backtrace targets, and original-question guards without updating claim trust |
| Research route state | Implemented first typed record: `aitp-v5 route record` and `aitp_v5_record_research_route` capture live routes, abandoned/blocked routes, branches, failed-attempt lessons, pivots, checkpoint links, and next actions as orientation-only process graph records. Route state can steer agents and preserve nonlinear research continuity, but it is not evidence, validation, or claim-trust authority |
| Canonical source assets | Implemented first typed record and projection: `aitp-v5 asset register` / `aitp_v5_register_source_asset` and `aitp-v5 asset capture-auto` / `aitp_v5_capture_source_asset_auto` assign orientation-only identities, local file hashes, version anchors, duplicate-hash diagnostics, and source/code/artifact links to papers, lectures, notes, code repositories, snapshots, datasets, and generated artifacts; `process_graph_slice.source_asset_index[]` exposes that canonical source asset state to hosts without creating a second store |
| Source/code/tool provenance automation | Implemented first automations: `aitp-v5 asset capture-auto` and `aitp_v5_capture_source_asset_auto` capture local source file hash/size/mtime/MIME-ish metadata into canonical source asset records, `aitp-v5 code state auto` and `aitp_v5_capture_code_state_auto` capture git HEAD, branch/upstream, dirty status, diff hash, optional patch artifacts, and linked topic/claim/session refs, `aitp-v5 tool run capture-auto` / `aitp_v5_capture_tool_run_auto` captures local tool transcript/result hash, size, mtime, MIME-ish metadata, and bounded preview into a `tool_run_record`, and `aitp-v5 research-state attach-artifact-auto` / `aitp_v5_attach_artifact_auto` captures local artifact hash/size/mtime/MIME-ish metadata into an `artifact_record` without treating it as evidence, validation, or trust |
| Curated heuristic RAG | Implemented first read/write contract surface, file-backed manifest lane, Hakimi automatic consumption path, read-only chunk lookup, and read-only promotion draft surface: `aitp-v5 adapter curated-rag-corpus` / `aitp_v5_get_curated_rag_corpus` exposes either the default fixture catalog or `.aitp/curated_rag/corpus.json`, `aitp-v5 adapter curated-rag-search <query>` / `aitp_v5_search_curated_rag_corpus` returns deterministic lexical retrieval as `heuristic_context`, `aitp-v5 adapter curated-rag-chunk <chunk-id>` / `aitp_v5_get_curated_rag_chunk` returns the exact chunk/document ids, hashes, source URI, version anchor, promotion path, and forbidden uses, `aitp-v5 curated-rag ingest --path ...` / `aitp_v5_ingest_curated_rag_corpus` creates or refreshes `.aitp/curated_rag/corpus.json` plus `.aitp/curated_rag/indexes/lexical_index.json`, and `aitp-v5 adapter curated-rag-promotion-draft <chunk-id>` / `aitp_v5_draft_curated_rag_promotion` returns a constrained draft for source-asset, reference-location, evidence, validation, and trust-preflight writes. The file-backed lane derives `lexical_file_backed` index metadata, manifest hashes, and stale-index diagnostics from `.aitp/curated_rag/indexes/lexical_index.json` when present. Hakimi now detects conceptual scaffolding, literature orientation, derivation scaffolding, method selection, and source-backtrace turns, calls this AITP-owned retrieval surface with a small limit, injects chunk ids/document ids/hashes into ContextPacks as `heuristic_context` / `orientation_only`, and can inspect one chunk's canonical identity/anchor/hash before asking for a promotion draft. Corpus/chunks/chunk lookups/ingestion results and promotion drafts remain orientation-only background/planning surfaces; they cannot satisfy evidence, validation, claim-trust, `trust_apply`, or final-gate requirements unless a host explicitly executes the normal AITP source/evidence/validation records |
| QSGW cockpit | Implemented first surface: `aitp-v5 status qsgw-cockpit` writes a topic-local final/diagnostic lane manifest, plot guard, and dashboard dry-run from typed records plus `research/librpa` report/script scans; it also discovers downstream `*_lane_manifest_current.json` and `*_aitp_intake_current.jsonl` files without treating them as trust updates |

The curated RAG general-layer roadmap now has a focused plan at
[`docs/superpowers/plans/2026-06-12-theory-curated-rag-general-layer.md`](docs/superpowers/plans/2026-06-12-theory-curated-rag-general-layer.md).
It treats open lecture/review shelves as object-discovery and source-backtrace
orientation only, with hybrid, formula-aware, graph-oriented retrieval planned
as sidecar indexes that cannot bypass AITP promotion gates.

## Remaining AITP / Hakimi Integration Roadmap

The current integration already records much of the scientific process as typed
graph and memory state: routes, exploratory reasoning, source assets, reference
locations, provenance gaps, tool runs, artifacts, validation contracts/results,
source reconstruction reviews, checkpoints, and trust-preflight packets. Hakimi
can consume those records as WorkFrame and ResearchAction context without
becoming the canonical store.

The next planning frontier is to make AITP a better canonical substrate for a
bounded Hakimi `/autoresearch` run. In that mode, a user sets a concrete
research question and Hakimi may drive the research loop automatically, but AITP
must still own the durable record boundaries and final evidence/trust status.
The remaining AITP-facing work is:

1. Add explicit operator provenance to new run/action records. The operator may
   be `human`, `hakimi`, `kimi`, `codex`, `claude`, `mcp:<server>`,
   `tool:<name>`, or a future subagent id. Operator metadata records who
   performed or normalized a step; it does not itself increase trust.
2. Promote the read-only `literature_comparison_draft` lane into reviewed typed
   literature comparison units or comparison records. These records should
   preserve source refs, dimensions, agreement/disagreement, missing evidence,
   limitations, and recommended next actions while remaining
   orientation/evidence candidates until source support, validation, and trust
   preflight are satisfied.
3. Define an AITP-owned `/autoresearch` run packet surface for hosts: objective,
   research question, status, operator trail, AITP slice cursors, actions
   attempted, evidence refs, validation refs, open gaps, terminal answer state,
   and whether supporting records were written into AITP.
4. Expose final answer audit packets with stable terminal states such as
   `answered_with_validated_support`, `answered_with_conditional_support`,
   `blocked_needs_human`, `negative_or_inconclusive`, and `draft_only`.
5. Harden the graph projection/index layer after those typed surfaces stabilize,
   so hosts can query neighborhoods, route state, evidence dependencies,
   provenance gaps, and validation/trust prerequisites without inventing a
   parallel graph database.

AITP should not add a silent `trust apply` path for Hakimi automation. Any
trust-changing conclusion must remain a typed AITP trust/preflight/checkpoint
workflow with explicit evidence and validation status.

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
- Treat `aitp_v5_preflight_trust_update` payload hints as non-mutating
  trust-boundary drafts. A host such as Hakimi may execute
  `aitp-v5 trust preflight` and record the returned token/result as policy
  evidence, but that evidence is not `trust apply` and does not update claim
  trust.
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
- Treat `runtime_bridge_target_manifest` as the canonical host target table for
  AITP reads, writes, and preflight. It names the preferred MCP tool, CLI
  fallback template, public surface, state effect, and MCP invocation contract
  for each host operation: JSON-object args, `base` as the workspace argument,
  snake_case payload keys, JSON-object result payloads, and CLI fallback when
  MCP is unavailable or fails. Read targets also declare `mcp_arguments` so
  hosts know that `readProcessGraphSlice` / `readMomentPolicy` require
  `base` and `session_id`, accept `claim_id` and `limit`, and that
  `readRuntimePayloadProfiles` has no required payload. It excludes
  `trust_apply`, remains
  orientation-only, and cannot update claim trust.
- Treat `runtime_payload_profiles` as the canonical host-event-to-write
  contract. The catalog maps Hakimi benchmark adapter runs and primitive tool
  lifecycle completions to `recordToolRun` / `aitp_v5_record_tool_run`
  payloads so runtime execution outcomes become AITP tool-run provenance, not
  validation results or claim-trust updates. Its
  `catalog_version=aitp.v5.runtime_payload_profiles.v1`, `profile_count`, and
  `profile_index` let hosts verify that the profile array they parsed is the
  canonical AITP catalog order.
- Treat each runtime payload profile's `capture_policy` as AITP-owned host
  guidance for when a host may write the payload. Benchmark adapter capture is
  controlled-auto and scoped to one adapter run; primitive tool lifecycle
  capture is explicit-request only, keyed by one `tool_call_id`. Both require a
  configured bridge plus topic/claim scope, skip rather than fabricate missing
  scope, forbid bulk auto-capture, and cannot record validation or mutate claim
  trust.
- Treat `runtime_payload_profiles` as a directly queryable read-only runtime
  surface as well as adapter-packet metadata. Hosts may call
  `aitp-v5 adapter payload-profiles` or `aitp_v5_get_runtime_payload_profiles`,
  or discover the same surface through the `readRuntimePayloadProfiles` bridge
  target. The catalog remains profile metadata only and cannot update claim
  trust; a host-side parser may reject tampered no-trust flags, but it still
  does not become evidence, validation, or trust authority.
- Treat `runtime_payload_profiles.host_usage_policy` as the catalog-level host
  usage contract. Hosts may use the read surface for payload construction,
  capture-policy diagnostics, and bridge-readiness diagnostics only. The same
  policy explicitly forbids evidence support, validation results, claim-trust
  updates, `trust_apply`, and bulk auto-capture; it also carries
  `records_validation_result=false`, `claim_trust_mutation=none`,
  `summary_inputs_trusted=false`, and `can_update_claim_trust=false`.
- Treat `curated_rag_corpus` and `curated_rag_search_result` as heuristic
  background context only. Hosts may use retrieved chunks to frame concepts,
  orient a literature/source backtrace, choose a derivation method, or decide
  what to inspect next. They must not use retrieved text as evidence support,
  validation, claim-trust update input, `trust_apply`, or final-gate
  satisfaction without first promoting the relevant source passage through
  normal AITP `source_asset`, `reference_location`, evidence, validation, and
  trust-preflight records.
- Treat `curated_rag_chunk` as a read-only identity/anchor/hash lookup for one
  retrieved chunk. It may tell a host which document/chunk/source URI/version
  anchor/content hashes should be reviewed before promotion, and it may repeat
  the safe promotion path, but `lookup_creates_records=false` and the lookup is
  not evidence, validation, source support, final-gate satisfaction, or
  claim-trust authority.
- Treat `curated_rag_ingest_result` as a manifest/index write report only.
  `aitp-v5 curated-rag ingest --path ...` and
  `aitp_v5_ingest_curated_rag_corpus` may create or refresh the local curated
  RAG corpus and lexical index under `.aitp/curated_rag`, but the resulting
  corpus/document refs remain heuristic context refs, not evidence,
  validation, trust updates, or final-gate satisfaction.
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
- Treat `aitp_v5_capture_source_asset_auto` as the source-file analogue of
  code-state auto capture. A host may pass a local PDF, lecture note, code
  snapshot, dataset, or generated file path, and AITP will compute the
  content hash, size, mtime, inferred asset type, and version metadata before
  writing the same canonical `source_asset_record`. The resulting record is
  still orientation-only provenance, not evidence or validation.
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
  `required_before_trust_change`. Their `payload_hints[]` are AITP-owned draft
  shapes for the next host write, such as source-asset auto-capture,
  code-state capture, tool-run, validation-contract/result, source-asset,
  reference-location, or artifact records. Hosts must replace placeholders
  with real local provenance before calling the entrypoint. Each hint also
  carries `draft_schema` metadata with required fields, placeholder field
  paths, placeholder values, and `host_must_resolve` paths so hosts can tell
  which local values must be supplied before execution. The draft and schema
  themselves cannot update claim trust.
- Treat auto-captured code-state records as provenance records, not validation
  results. A dirty diff hash or patch artifact explains what code state was
  used; it does not prove the result correct.
- Treat auto-captured tool-run records as provenance records, not evidence or
  validation promotion. AITP may compute transcript/result file hash, size,
  mtime, MIME-ish metadata, and a bounded preview, but a host must still create
  explicit evidence and validation records before using that run for trust.
- Treat `aitp_v5_attach_artifact_auto` as the local-artifact analogue of source
  and tool-run auto capture. A host may pass a benchmark log, validation output,
  patch, plot, JSON result, or generated file path, and AITP will compute the
  artifact hash, size, mtime, MIME-ish metadata, local path, and file identity
  before writing the canonical `artifact_record`. The resulting artifact ref is
  provenance by reference only; it is not evidence, validation, or claim-trust
  authority.
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
  path for configured sessions, not as a new authority. It should write or
  preflight through AITP and record scoped action evidence; a trust-preflight
  result such as `aitp:trust_preflight:<token>` is policy evidence only, not an
  applied trust update. If the bridge is not configured, the host must fail
  closed.
- Treat Hakimi source reconstruction review result writes as calls into AITP's
  canonical `record_source_reconstruction_review_result` surface. The host may
  pass reviewed components and typed basis refs, but the resulting
  `source_reconstruction_review_result_record` remains an AITP record and still
  cannot update claim trust.
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
   `source_asset_index`, source-asset auto-capture, and code-state automation
   slices: the kernel now records duplicate-hash diagnostics, projects source
   asset hash/version/ref status into graph slices, and can auto-capture local
   source files plus git code state, but stronger local PDF/lecture/code
   snapshot indexing and source-stack queries still need to keep a backtrace
   focused on the original physics question.
7. Harden the Hakimi runtime bridge against real topic stores. Hakimi sessions
   now auto-configure a dynamic AITP bridge, consume process graph slices
   through explicit WorkFrame scope, compile `moment_policy.decisions` into
   ContextPack call obligations before research-context injection, preserve the
   cached AITP context when no fresh slice is available, run soft final-gate
   checks over unhandled required calls, and expose write-bridge hints and
   MCP-first execution with CLI fallback for exploratory records, research
   routes, proof obligations, human checkpoints, trust preflight, source
   assets, auto-captured local source assets, auto-captured code state, and
   validation records.
   Hakimi also has an opt-in real CLI smoke that creates
   a temporary AITP topic store, reads a real `process_graph_slice`, writes a
   proof obligation and checkpoint, and verifies the resulting `.aitp` records
   when `HAKIMI_AITP_REAL_CLI_SMOKE=1`, `AITP_V5_REPO`, and `AITP_V5_PYTHON`
   point at a working AITP Python environment. The first strict AITP preflight
   bridge is implemented as a non-mutating policy-evidence call. The
   MCP-first bridge target manifest is implemented and gives hosts canonical
   MCP tool names, invocation args, result shape, and CLI fallback templates.
   Runtime payload profiles now give Hakimi canonical benchmark-adapter-run and
   primitive-tool-lifecycle to `tool_run_record` mappings. Hakimi process graph
   reads, writes, and preflight execution can now call the AITP MCP tools first
   and fall back to the CLI bridge; richer evidence write-back still needs
   later runtime integration slices. `trust apply` remains an AITP-owned future
   boundary for hosts.
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
| `aitp-v5 adapter bridge-targets` | MCP-first host bridge target manifest with CLI fallback templates and no claim-trust mutation authority |
| `aitp-v5 graph slice <session-id>` | Read-only typed process graph slice for local agent compilation |
| `aitp-v5 graph moment-policy <session-id>` | Read-only host-agnostic policy for when to record, brainstorm, backtrace, or stop at trust boundaries |
| `aitp-v5 literature source-review-handoff` | Read-only literature/source handoff packet for source-review planning without evidence, validation, writes, final-gate, or trust authority |
| `aitp-v5 literature comparison-draft` | Read-only source-set comparison draft packet for explicit `source.compare_literature` planning without creating comparison records, evidence, validation, writes, final-gate, or trust authority |
| `aitp-v5 exploration record` | Orientation-only typed record for brainstorming, backtrace, source-asset, and steering continuity |
| `aitp-v5 route record` | Orientation-only typed record for live routes, failed routes, branches, pivots, checkpoint links, and nonlinear research continuity |
| `aitp-v5 run research start` | Canonical research-run ledger record for a user/runtime-started objective and question, with operator attribution and no claim-trust authority |
| `aitp-v5 run research update` | Update the canonical research-run phase/status, terminal answer state, AITP refs, action refs, and stop reason while appending a process event |
| `aitp-v5 run event record` | Append a canonical research-run event for context refresh, action selection, checkpoints, answer drafting, blocking, or stop provenance |
| `aitp-v5 asset register` | Orientation-only canonical identity for raw papers, lectures, notes, code snapshots, datasets, and generated artifacts |
| `aitp-v5 code state auto` | Auto-capture git HEAD, branch/upstream, dirty status, diff hash, optional patch artifact, and linked topic/claim/session refs |
| `aitp-v5 research-state attach-artifact` | Attach a benchmark log, validation output, patch, plot, JSON result, or generated file by reference as an artifact record with hash/size metadata when local |
| `aitp-v5 research-state attach-artifact-auto` | Auto-attach a local benchmark log, validation output, patch, plot, JSON result, or generated file as an artifact record with hash/size/mtime/MIME-ish metadata |
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
`run research start`, `run research update`, `run event record`,
`research-state attach-artifact`, `research-state attach-artifact-auto`,
`checkpoint request`,
`research-state create-proof-obligation`,
`validation contract create`, `validation result record`, and
`source reconstruction-review-result`, plus `trust preflight`. If the
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
| `runtime_bridge_target_manifest` | `aitp-v5 adapter bridge-targets` | `aitp_v5_get_runtime_bridge_target_manifest` | `runtime_bridge_target_manifest` |
| `runtime_payload_profiles` | `aitp-v5 adapter payload-profiles` | `aitp_v5_get_runtime_payload_profiles` | `runtime_payload_profiles` |
| `record_ref_lookup` | `aitp-v5 adapter record-ref-lookup <refs...>` | `aitp_v5_lookup_record_refs` | `record_ref_lookup` |
| `curated_rag_corpus` | `aitp-v5 adapter curated-rag-corpus` | `aitp_v5_get_curated_rag_corpus` | `curated_rag_corpus` |
| `curated_rag_search` | `aitp-v5 adapter curated-rag-search <query> <args>` | `aitp_v5_search_curated_rag_corpus` | `curated_rag_search_result` |
| `curated_rag_chunk` | `aitp-v5 adapter curated-rag-chunk <chunk-id>` | `aitp_v5_get_curated_rag_chunk` | `curated_rag_chunk` |
| `curated_rag_promotion_draft` | `aitp-v5 adapter curated-rag-promotion-draft <chunk-id> <args>` | `aitp_v5_draft_curated_rag_promotion` | `curated_rag_promotion_draft` |
| `ingest_curated_rag_corpus` | `aitp-v5 curated-rag ingest <args>` | `aitp_v5_ingest_curated_rag_corpus` | `curated_rag_ingest_result` |
| `record_evidence` | `aitp-v5 evidence record <args>` | `aitp_v5_record_evidence` | `evidence_record` |
| `record_tool_run` | `aitp-v5 tool run record <args>` | `aitp_v5_record_tool_run` | `tool_run_record` |
| `capture_tool_run_auto` | `aitp-v5 tool run capture-auto <args>` | `aitp_v5_capture_tool_run_auto` | `tool_run_record` |
| `record_reference_location` | `aitp-v5 reference location record <args>` | `aitp_v5_record_reference_location` | `reference_location_record` |
| `record_validation_result` | `aitp-v5 validation result record <args>` | `aitp_v5_record_validation_result` | `validation_result_record` |
| `record_source_reconstruction_review_result` | `aitp-v5 source reconstruction-review-result <args>` | `aitp_v5_record_source_reconstruction_review_result` | `source_reconstruction_review_result_record` |
| `record_exploratory_record` | `aitp-v5 exploration record <args>` | `aitp_v5_record_exploratory_record` | `exploratory_record` |
| `record_research_route` | `aitp-v5 route record <args>` | `aitp_v5_record_research_route` | `research_route_record` |
| `start_research_run` | `aitp-v5 run research start <args>` | `aitp_v5_start_research_run` | `research_run_record` |
| `update_research_run` | `aitp-v5 run research update <args>` | `aitp_v5_update_research_run` | `research_run_record` |
| `record_research_run_event` | `aitp-v5 run event record <args>` | `aitp_v5_record_research_run_event` | `research_run_event_record` |
| `register_source_asset` | `aitp-v5 asset register <args>` | `aitp_v5_register_source_asset` | `source_asset_record` |
| `capture_source_asset_auto` | `aitp-v5 asset capture-auto <args>` | `aitp_v5_capture_source_asset_auto` | `source_asset_record` |
| `capture_code_state_auto` | `aitp-v5 code state auto <args>` | `aitp_v5_capture_code_state_auto` | `code_state_record` |
| `attach_artifact` | `aitp-v5 research-state attach-artifact <args>` | `aitp_v5_attach_artifact` | `artifact_record` |
| `attach_artifact_auto` | `aitp-v5 research-state attach-artifact-auto <args>` | `aitp_v5_attach_artifact_auto` | `artifact_record` |
| `create_proof_obligation` | `aitp-v5 research-state create-proof-obligation <args>` | `aitp_v5_create_proof_obligation` | `proof_obligation_record` |
| `update_proof_obligation` | `aitp-v5 research-state update-proof-obligation <args>` | `aitp_v5_update_proof_obligation` | `proof_obligation_record` |
| `create_validation_contract` | `aitp-v5 validation contract create <args>` | `aitp_v5_create_validation_contract` | `validation_contract_record` |
| `request_human_checkpoint` | `aitp-v5 checkpoint request <args>` | `aitp_v5_request_human_checkpoint` | `human_checkpoint_record` |
| `decide_human_checkpoint` | `aitp-v5 checkpoint decide <args>` | `aitp_v5_decide_human_checkpoint` | `human_checkpoint_record` |
| `trust_preflight` | `aitp-v5 trust preflight <args>` | `aitp_v5_preflight_trust_update` | `trust_update_preflight` |

Hosts can query `runtime_bridge_target_manifest` directly instead of
hard-coding the operation-to-entrypoint map. Each target names a Hakimi-facing
operation such as `recordEvidence`, `captureSourceAssetAuto`,
`captureCodeStateAuto`, `attachArtifactAuto`, or
`preflightTrustUpdate`, and process-ledger write targets such as
`startResearchRun`, `updateResearchRun`, and `recordResearchRunEvent`.
Each target names its canonical AITP entrypoint key, preferred MCP tool, CLI
fallback template, public surface, and state effect. Read targets also
carry `mcp_arguments` for host runtime calls: `readProcessGraphSlice` and
`readMomentPolicy` require `base` plus `session_id` and accept `claim_id` plus
`limit`, `readRuntimePayloadProfiles` has no required arguments,
`readCuratedRagCorpus` accepts optional `base`,
`searchCuratedRagCorpus` requires `query` with optional `base` and `limit`,
`readCuratedRagChunk` requires `chunk_id` with optional `base`,
`draftCuratedRagPromotion` requires `chunk_id` with optional `base`,
`topic_id`, `claim_id`, `connector_id`, and `promotion_intent`,
`readLiteratureSourceReviewHandoff` requires `base`, `session_id`, `uri`,
`label`, `short_summary`, and `detected_relevance` with optional
`external_id`, `optional_claim_id`, `scoped_output`, and `reviewed_refs`, and
`lookupRecordRefs` requires `base` plus `refs`. The
manifest is derived from `runtime_entrypoints()`, has
`preferred_transport=mcp`, keeps `fallback_transport=cli`, and explicitly
excludes `trust_apply`.

Research-run records are the AITP-owned process ledger for bounded runtime
research modes such as Hakimi `/autoresearch`. `research_run_record` stores the
objective, research question, operator trail, status, phase, AITP slice refs,
action/source/evidence/validation refs, stop reason, and terminal answer state.
`research_run_event_record` stores the ordered process events that explain how
the runtime reached that state. These records can update the kernel process
state, but they explicitly keep `summary_inputs_trusted=false`,
`orientation_only=true`, and `can_update_claim_trust=false`. They do not
validate evidence, satisfy final gates, or promote claim trust; those remain
separate AITP source/evidence/validation/trust-preflight surfaces.

Hakimi may request `readLiteratureSourceReviewHandoff` during WorkFrame context
preparation only from an explicit host cue that repeats the no-trust/no-write
flags. That cue is downstream runtime metadata: it does not create an AITP
record, prove source support, record validation, satisfy final gates, execute a
write, infer payload values, or update claim trust. The canonical packet remains
the AITP `literature_source_review_handoff` read surface returned by the
runtime target.

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
or validation-result records. For `aitp_v5_preflight_trust_update`, the hint
uses `record_action=preflight_trust_update` and drafts the action/session/topic/
claim/source/evidence fields for `trust preflight`, while keeping
`summary_inputs_trusted=false` and `can_update_claim_trust=false`. These hints
also carry `draft_schema` metadata: required field names, placeholder field
paths, placeholder values, `host_must_resolve`, `field_case=snake_case`, and
the same no-trust flags. They are not canonical truth and cannot update claim
trust; they keep hosts from inventing payload shapes while AITP remains the
authority for the actual record.
Hakimi compiles these decisions
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
before a trust change or final gate. Gaps may also carry `payload_hints[]` for
the concrete typed record that should repair the gap: `asset capture-auto`,
`code state auto`, `record_tool_run`, `create_validation_contract`,
`record_validation_result`, `attach_artifact_auto`, `attach_artifact`,
`register_source_asset`, or `record_reference_location`.
These hints are canonical AITP guidance for host write drafts, not canonical
truth records; placeholders must be resolved by the host at execution time and
AITP still validates/stores the resulting record. Their `draft_schema`
identifies exactly which draft paths are placeholders and must be resolved by
the host before the write bridge is called.

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

When that worklist recommends `record_source_reconstruction_review_result`,
Hakimi can now call the same canonical CLI entrypoint through its write bridge.
AITP still validates the reviewed components and basis refs and stores the
result as orientation-only review evidence with `can_update_claim_trust=false`.

When a trust-boundary decision recommends `aitp_v5_preflight_trust_update`,
Hakimi can call `aitp-v5 trust preflight` through its bridge and record the
returned `trust_update_preflight` token as scoped policy evidence. This closes
the preflight loop only; Hakimi does not call `trust apply` or mutate AITP
claim trust.

`runtime_payload_profiles` is the adjacent host-event payload contract. Its
profiles tell a host runtime how to turn a benchmark adapter event or primitive
tool lifecycle completion into a `recordToolRun` /
`aitp_v5_record_tool_run` payload. The mapped records are provenance for what
ran, with `summary_inputs_trusted=false` and `can_update_claim_trust=false`;
they do not create a `validation_result_record`, satisfy a validation contract
by themselves, or change claim trust. The catalog now carries
`catalog_version=aitp.v5.runtime_payload_profiles.v1`, `profile_count`, and
`profile_index` beside the `profiles[]` array so hosts can parse the public
surface as a stable typed catalog instead of inferring profile identity from
README prose.

Hosts can now read the same catalog without building a full adapter packet:
`aitp-v5 adapter payload-profiles` and `aitp_v5_get_runtime_payload_profiles`
return the public `runtime_payload_profiles` surface directly, and
`runtime_bridge_target_manifest.targets[]` includes the read-only
`readRuntimePayloadProfiles` operation. This keeps payload-profile discovery in
the same MCP-first target table as `readProcessGraphSlice` and
`readMomentPolicy` while preserving `claim_trust_mutation=none`. Hakimi now has
a typed reader for this surface and uses it only as AITP-owned payload metadata;
the reader does not write records, record evidence, create validation results,
or mutate claim trust.

The catalog-level `host_usage_policy` makes that host boundary explicit.
Runtime hosts may use the read surface for payload construction,
capture-policy diagnostics, and bridge-readiness diagnostics. They must not use
the catalog as evidence support, a validation result, a claim-trust update,
`trust_apply`, or a bulk auto-capture permission. The policy repeats the
no-trust flags at catalog scope so host parsers can fail closed if the public
profile surface is tampered with.

`curated_rag_corpus` is the adjacent lightweight knowledge shelf for selected
papers, lectures, notes, reviews, textbooks, personal explanations, and code
documentation that should help an agent reason. Without a workspace corpus it
returns the contract-first fixture catalog. When `.aitp/curated_rag/corpus.json`
exists, AITP normalizes that file-backed manifest into the same public surface
with stable document/chunk ids, source URI, version anchors, content hashes,
domain/topic hints, and no-trust flags. The active index mode is
`lexical_fixture` for the fixture and `lexical_file_backed` for workspace
manifests. If `.aitp/curated_rag/indexes/lexical_index.json` exists, AITP
compares its `manifest_hash` with the current document/chunk manifest and
reports `fresh` or `stale` diagnostics; if no index file exists, the lexical
retrieval is derived in memory. Future BM25 or embedding indexes should remain
derived from canonical corpus/chunk records and report stale-index diagnostics
when hashes or version anchors drift.

`curated_rag_search_result` returns retrieved chunks with
`result_role=heuristic_context`, `read_surface_effect=orientation_only`,
`records_validation_result=false`, `claim_trust_mutation=none`,
`summary_inputs_trusted=false`, `can_update_claim_trust=false`, and
`requires_promotion_for_claim_support=true`. Retrieved chunks can suggest
terminology, methods, examples, or source-backtrace directions. If a chunk
becomes claim-relevant, the host must escalate through the ordinary AITP source
and validation path instead of treating RAG retrieval as claim support.

`curated_rag_chunk` is the narrow read-only lookup for one selected chunk before
promotion. Given a `chunk_id`, it returns the canonical chunk and document ids,
source URI, version anchor, document/chunk content hashes, promotion path, and
forbidden uses. The lookup is intentionally not a promotion writer:
`state_effect=read_only`, `retrieval_role=heuristic_context`,
`read_surface_effect=orientation_only`, `lookup_creates_records=false`, and the
promotion boundary keeps `lookup_is_evidence=false`,
`lookup_records_validation_result=false`,
`lookup_satisfies_final_gate=false`, and
`lookup_can_update_claim_trust=false`. Hosts should use it to verify exactly
which source slice they are about to review, then call the separate promotion
draft or normal source/evidence/validation entrypoints only after explicit
review.

`curated_rag_promotion_draft` is the read-only escalation surface for that
decision. Given a `chunk_id`, it returns the chunk/document identity, content
hashes, anchor metadata, missing `topic_id`/`claim_id` context, and draft-only
operations for `registerSourceAsset`, `recordReferenceLocation`,
`recordEvidence`, `createValidationContract`, and `preflightTrustUpdate`.
Every operation carries `draft_only=true`, `creates_record_now=false`, and
`claim_support_created=false`. The same draft now includes
`promotion_write_sequence`, an AITP-owned dependency map that names each
ordered step, its future output ref pattern, the prior refs that must already
exist, and which later stages consume those refs. Each sequence step carries
`requires_explicit_execute_call=true`, `executes_write_now=false`,
`records_validation_result=false`, and `claim_trust_mutation=none`; it is a
bridge-execution checklist, not a runner. The surface itself has
`state_effect=read_only`, `draft_creates_records=false`,
`records_validation_result=false`, `claim_trust_mutation=none`, and
`can_update_claim_trust=false`. It is a controlled construction sheet, not a
promotion writer.

Downstream hosts may project this draft surface into model-visible action
suggestions when a retrieved curated RAG chunk looks claim-relevant. For
example, Hakimi can add a read-only `draft_aitp_curated_rag_promotion` binding
beside `ResearchContextPack.curatedRag.results` so the model sees which chunk
could be reviewed for promotion. That binding is still a host projection over
AITP-owned chunk ids and hashes: it does not make the chunk evidence, does not
execute any AITP write operation, and does not relax the requirement for an
explicit later source/reference/evidence/validation/trust-preflight path.
Hosts may also render the returned draft operations as a local decision tree
for possible next write-bridge calls. That rendering is downstream UI/runtime
guidance only: the AITP surface still remains read-only until a host explicitly
calls one of the normal AITP write or preflight entrypoints with reviewed
payload fields.
Hosts may additionally use `promotion_write_sequence.requires_prior_refs` to
block a selected downstream call draft when a reviewed payload is missing the
source/reference/evidence refs that AITP says must already exist. That is still
host-side readiness checking over AITP-owned policy: it does not execute the
bridge, create records, validate source support, satisfy final gates, or update
claim trust.
After a host explicitly executes one of the normal AITP write entrypoints and
receives a typed write result, it may show that result's canonical ref as a
carried-ref handoff for later `promotion_write_sequence` steps. That handoff is
downstream ergonomics over an already returned AITP record id: it may help a
model copy `source_asset:<id>`, `reference_location:<id>`, or `evidence:<id>`
into later reviewed payloads, but it does not mutate the next payload, execute
the next write, validate source support, satisfy final gates, or change claim
trust.
Hosts may also turn those carried refs into copyable reviewed-override
suggestions for a later draft. Such suggestions are still advisory host output:
the payload changes only when the model or user explicitly provides reviewed
override fields to a fresh draft action, and the resulting write still requires
the normal readiness checks and separate explicit AITP write/preflight call.
If a host adds a compact next-call pointer next to the suggestion, that pointer
is only navigation to a fresh draft action. It is not an AITP operation, not a
write authorization, and not a replacement for reviewed overrides, readiness
inspection, or explicit write/preflight execution.
If the host accepts structured carried-ref handoff objects, malformed objects
should fail closed rather than producing suggestions or pointers; explicit
canonical refs may still be accepted as user/model-provided reviewed input.
If the host renders a diagnostic taxonomy for those parse failures, the taxonomy
is still host repair guidance only. It may name the malformed field/path, but it
does not become an AITP validation result, final-gate check, write authority, or
claim-trust signal.
If the host exposes that taxonomy in a model-facing action listing, the listing
is still read-only host metadata. It does not add an AITP public surface or
permit a model to bypass fresh draft review and explicit write execution.
If a host carries this into a runtime `ContextPack` reminder, that reminder is
also downstream host navigation. It may point to taxonomy inspection, a fresh
draft, reviewed overrides, readiness inspection, and explicit execution, but it
does not authorize writes or become AITP evidence, validation, final-gate, or
trust state.
If a host additionally binds a concrete `carried_ref_handoff_failure` code/path
to a model-facing repair draft action, that binding is still downstream runtime
navigation. It may help the model call the normal fresh draft surface with
reviewed overrides, but it is not an AITP public surface, not write
authorization, not payload inference, and not evidence, validation,
source-support, final-gate, or trust state.
If a host echoes whether a carried-ref repair draft still needs reviewed
overrides, is ready for readiness inspection, passed readiness inspection, or
passed explicit-execute precheck, that echo is also downstream status
rendering. It does not authorize execution, mutate AITP state, replace the
normal readiness check, or become evidence, validation, final-gate
satisfaction, source support, or trust state.
If a host summarizes a successful explicit source asset, reference location, or
evidence write result back to the carried-ref repair path that prepared it,
that summary is likewise downstream runtime audit context over an AITP-owned
returned result. It is not an AITP public surface, not a second canonical
record, not a next-payload mutation, not a next write, and not evidence
validation, source-support proof, final-gate satisfaction, or claim-trust
authority.
If a host later compiles that summary into a continuation binding, the binding
is also downstream runtime navigation. It may carry the returned canonical ref
as candidate reviewed override input for a fresh draft, and it may also ask the
host runtime to perform a source-context review before choosing extraction,
validation, a fresh draft, or a blocker. That review candidate is still
downstream action-selection guidance, not an AITP public surface or source
support result. It must not infer chunk ids, promotion stages, payload values,
source support, validation, final gate satisfaction, or trust changes; normal
AITP lookup/write/validation/trust-preflight surfaces still own those facts.
If the host later records a source-context review outcome that chooses
extraction, validation, a fresh draft, or a blocker, that outcome is still
host-side routing metadata. It may guide the next explicit ResearchAction, but
it is not an AITP source-support result, validation result, final-gate pass,
write execution, or trust update.
If the host adds a source-context review handoff inspection or bound primitive
plan before following that outcome, that inspection is still downstream runtime
readiness metadata. It may check that the selected next action and no-trust
flags are internally consistent, but it is not an AITP public surface,
source-support result, validation result, final-gate pass, write execution, or
claim-trust update.
If a host also turns a selected decision-tree option into a prefilled
`execute_aitp_write_bridge` call draft, that draft is still downstream guidance
over AITP-owned `payload_draft` / `payload_template` fields. It may expose
placeholder diagnostics for missing source/evidence review, record ids, or
preflight scope, but it does not create records, execute preflight, satisfy
final gates, or update claim trust.
Hosts may additionally compare reviewed field overrides against the original
AITP draft payload/template before execution. Those overrides are still
host-side review proposals: they do not rewrite the AITP draft surface, do not
prove source support, and do not create source, evidence, validation, preflight,
or trust records until a normal explicit AITP entrypoint is called.
If a host renders canonical-identity alignment for a curated RAG draft, that
alignment is only a future-record map: it may show which AITP record kind and
canonical ref prefix a later explicit write result would produce, but it is not
an AITP record inventory and does not reserve or create ids.
Host placeholder-vs-concrete ref readiness inside that alignment is likewise
only local draft classification. It does not prove the referenced AITP records
exist, validate source support, or replace the explicit AITP write/preflight
entrypoint.
Even concrete-looking refs in host output should be treated as syntax-level
until an AITP-owned read, write result, validation, or trust-preflight surface
confirms the relevant record state.
`record_ref_lookup` is the narrow read-only confirmation path for this
pre-execution case: it can say that `source_asset:<id>`,
`reference_location:<id>`, or another supported typed ref exists in the AITP
store, but `status="found"` still means typed-store existence only. It does not
validate source support, create evidence, create validation, satisfy a final
gate, update claim trust, or make summary inputs trusted.
For missing `source_asset` and `reference_location` refs, the same item may
include `suggested_next_operation`, `suggested_next_entrypoint`, and
`suggested_next_surface` to point hosts toward the normal AITP write path. Those
fields are repair guidance only; they do not execute the write or weaken the
no-trust boundary.
Hosts may summarize those suggested fields in a local repair checklist for
model ergonomics, but that checklist is downstream rendering over
`record_ref_lookup`; it is not a new AITP entrypoint, validation result, trust
preflight, or write execution. A host may also name the exact later bridge
operation implied by `suggested_next_operation`, but that is a repair-action
hint only and must not alter the currently selected write/preflight call. A
host may summarize those repair operations at a draft root for readability, but
the per-ref `record_ref_lookup` items remain the source of that guidance. A
host may draft a reviewed repair call from that hint, but AITP state changes
only through the normal explicit write/preflight entrypoints.
A host-side confirmation summary over that reviewed call draft is also not an
AITP trust preflight. It may classify remaining placeholder, source-review, and
preflight-scope diagnostics, and may count repair-hinted missing refs so its
summary stays aligned with a host-rendered checklist before a pending explicit
AITP call. It still does not record validation, satisfy final gates, convert the
curated chunk into evidence, or mutate claim trust.
`literature_source_review_handoff` is the AITP-owned read-only composition
surface for literature/source review handoff. It can package a guarded
`literature_intake_suggestion`, `record_ref_lookup`, a source-stack coverage
item, and a source reconstruction review packet so a host such as Hakimi can
plan `source.review_context` with canonical AITP context. The packet carries
`read_only=true`, `requires_explicit_next_action=true`,
`records_validation_result=false`, `source_support_result=false`,
`write_executed=false`, and `claim_trust_mutation=none`; it does not create
evidence, validate source support, satisfy final gates, execute writes, or
update claim trust.
`literature_comparison_draft` is the adjacent AITP-owned read-only comparison
planning surface. It takes a session, comparison question, source refs, optional
dimensions, optional claim id, and rationale, then returns record-ref lookup,
source-set comparison dimensions, suggested agreement/disagreement/missing-
evidence/open-direction sections, recommended explicit AITP next entrypoints,
forbidden uses, and an allowed `source.compare_literature` planning call. It
keeps `draft_creates_records=false`, `bridge_called=false`,
`executes_write_now=false`, `records_validation_result=false`,
`source_support_result=false`, `write_executed=false`, and
`claim_trust_mutation=none`; it is not a literature comparison record,
evidence, validation, source-support result, final-gate result, write execution,
or trust update.
Hosts may finally wrap the reviewed/confirmed call draft in a local handoff
artifact carrying a confirmation id, diagnostic hash, exact tool-call JSON, and
non-execution provenance. That artifact is not an AITP typed record and does
not rewrite the curated RAG draft; it is only a downstream transfer envelope
for a later explicit `execute_aitp_write_bridge` call.
A reviewed `aitp_record_ref_repair_write_bridge_call_draft` may use a
repair-scoped handoff for that same transfer, but the boundary is unchanged:
the handoff creates no AITP record, records no source support or validation,
does not run trust preflight, and does not relax typed write-entrypoint
validation.
Hosts may prepare such repair drafts for missing `source_asset` as well as
missing `reference_location` refs, but that only broadens downstream draft
coverage over existing AITP write entrypoints; it does not create a repair
writer outside the normal `source_asset_record` and `reference_location_record`
surfaces.
If a host re-checks such a handoff before executing the later call, that guard
is still host-side consistency checking over the transfer envelope. It does not
replace AITP validation, trust preflight, final-gate checks, or the canonical
typed write/preflight entrypoint itself. It may also report that the selected
write operation differs from repair-hint operations, but that distinction is a
host disambiguation aid rather than AITP state.
A host may expose the same guard as a read-only readiness inspector before the
explicit execution step. That inspection can report whether the handoff,
operation, and payload match, but `bridge_called=false` remains part of the
boundary: it is not a write attempt, does not mutate the handoff, and does not
create AITP validation, evidence, source support, or trust state.
Hosts may also include a prefilled readiness-inspection call next to the
handoff artifact for model ergonomics. That call is still only a downstream
read-only helper over the host guard; it is not an AITP operation, not an
execution token, and not permission to bypass the explicit typed write or
preflight entrypoint.
If a host mirrors that availability at the curated RAG write-call draft root or
the repair-draft root, the root pointer is only a navigation aid to the nested
handoff/readiness call. It does not change the draft, reserve an AITP id, call
the bridge, or add any new AITP surface beyond the existing typed
write/preflight entrypoints.
If a host adds a model-facing summary over that root pointer and nested
readiness call, the summary is the same downstream annotation. It may help a
model distinguish inspection material from execution material, but it is not an
AITP typed record, validation, source-support record, trust preflight, or write
authorization.
If a host reuses one renderer/helper for these pointer and summary annotations,
that reuse is a host-runtime implementation detail. It does not promote the
annotation into an AITP contract or change the canonical typed write/preflight
surfaces.
If a host adds a checklist telling a caller to inspect readiness before a later
explicit bridge call, that checklist is downstream next-step guidance. It does
not authorize the write call, call the bridge, or replace AITP typed validation,
source support, trust preflight, or write-entrypoint checks.
If that checklist carries a stable host id derived from the handoff and draft
family, the id is for host navigation only. It does not reserve or mint an AITP
record id, and it does not change canonical identity rules for typed records.
If a host readiness-inspection result echoes that checklist id or item status,
the echo is read-only reporting over the host guard. It does not satisfy AITP
validation, source-support, trust-preflight, final-gate, or write-entrypoint
requirements.
Downstream guard tests may pin missing-field and tamper rejection, but they
remain host-contract tests. AITP's own write surface is still the explicit
typed entrypoint list, with non-mutating trust preflight but no `trustApply`
write target exposed to hosts.
Structured guard-failure diagnostics produced by a host are likewise
downstream diagnostics only: field/path hints and `bridge_called=false` do not
create AITP records or replace validation/preflight evidence.
Host execution-precheck summaries around guarded handoffs are the same kind of
downstream consistency status: they may say whether the host guard allowed or
blocked a bridge call, and may echo guard-verified repair-count metadata from
the handoff hash input. They are still not AITP validation, trust preflight,
evidence, final-gate state, or missing-ref repair execution.
If a host execution-precheck summary also echoes the readiness checklist's
explicit-execute item, that echo is only host path reporting. It may say that a
separate explicit execute call was observed after the guard passed, or that item
2 was not followed after a guard failure, but it still does not authorize the
write, mutate the checklist or handoff, create AITP records, validate source
support, or change claim trust.
If the host's final passed handoff guard repeats the same checklist id and item
2 status, that cross-reference is still downstream trace metadata. It links the
readiness result, execution precheck, and guard result for auditability, but it
does not mint an AITP identity, expand the write surface, authorize execution,
or replace typed write/preflight requirements.
Host remediation summaries over those diagnostics are also advisory repair
hints only. They may suggest which handoff field or explicit execute argument
to fix, but they do not mutate the handoff or perform an AITP write/preflight.
If a host centralizes those repair hints into a reusable taxonomy, that
taxonomy remains a host-runtime helper rather than an AITP contract surface.
Publishing that taxonomy in a host tool description is still model-facing
runtime guidance; it does not expose new AITP write or trust surfaces.
Publishing the same taxonomy as machine-readable host tool metadata, such as a
`ResearchAction.list_actions` section, remains the same kind of host-runtime
guidance. AITP still treats the canonical contract as the typed entrypoint,
record, evidence, validation, and trust-preflight surfaces it owns.
Even if a host adds a dedicated read-only taxonomy inspection action, that
action remains a host convenience wrapper over runtime metadata rather than an
AITP entrypoint, record, validation result, or trust operation.

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
