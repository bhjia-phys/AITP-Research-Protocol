# AITP Research Protocol — Project Memory

This repository implements the AITP (AI Theoretical Physics) research protocol as a
FastMCP-based MCP server. It provides tools for AI coding agents to conduct
structured theoretical physics research with formal validation.

## Architecture

- `brain/mcp_server.py` — Main MCP server. ~49 @mcp.tool() functions implement the
  AITP protocol (L0-L4 layers). Uses FastMCP + PyYAML with file-based persistence
  (Markdown + YAML frontmatter).
- `brain/state_model.py` — Gate evaluation logic, artifact templates, stage
  definitions (L0, L1, L3, L4), required frontmatter fields, and heading
  contracts. Also defines the knowledge graph types (nodes, edges, towers) and
  the domain skill registry (`DOMAIN_SKILL_REGISTRY`, `resolve_domain_prerequisites`).
- `skills/` — Stage-specific skill Markdown files loaded by agents, plus domain
  skills (e.g., `skill-librpa.md`) that are injected as prerequisites by the
  execution brief when the topic matches a domain pattern.
- `schemas/` — JSON Schema definitions for protocol objects.
- `contracts/` — Protocol contract definitions.
- `adapters/` — Platform-specific adapters (OpenClaw, Codex).
- `templates/` — File templates for topics and artifacts.

## Domain Skill System

The execution brief includes a `domain_prerequisites` field. Domain skills are
detected via three mechanisms (in priority order):

1. **Contract-based**: `contracts/domain-manifest.<domain_id>.json` in the topic
   directory. The manifest declares the domain's operations, invariants, and
   routing. This is the primary mechanism — content-driven, not slug-dependent.
2. **State frontmatter**: `domains: [abacus-librpa]` in `state.md` frontmatter.
3. **Legacy slug fallback**: pattern matching on topic slug (for pre-existing topics).

The agent must load domain skills BEFORE the stage skill. Domain skills encode
domain-specific conventions, invariants, routing, and validation requirements.

To add a new domain: add an entry to `DOMAIN_ID_TO_SKILL` in `state_model.py`
and create the corresponding skill file in `skills/`. To register a topic with
a domain: copy the domain manifest into the topic's `contracts/` or add
`domains` to `state.md` frontmatter.

## Key Conventions

- **Topic storage**: All state is Markdown files with YAML frontmatter. No JSON
  databases, no SQL.
- **Topics root**: Set via `AITP_TOPICS_ROOT` env var. Each topic is a directory
  with `state.md` as the entry point.
- **Gate model**: Each stage (L0, L1, L3, L4) has required artifacts with
  required frontmatter fields and required Markdown headings. Missing any = blocked.
- **Tool return types**: Tools return `dict` or `_GateResult` (dict subclass).
  `_GateResult.__str__` returns its message for human display.
- **Popup gates**: Tools that require human decisions return popup_gate dicts for
  the agent to render as user prompts.
- **Human-facing output stability**: `docs/AITP_SPEC.md` defines the stable
  output spine for chat reports, session summaries, replay packets, and review
  views. Preserve the spine: core claim, verified content, uncertainty/failure
  modes, records, next actions, and long-term-memory candidates/non-promotable
  content. Add new diagnostics only as optional sections or appendices unless a
  major protocol version and migration note are provided.
- **Record lifecycle (rehome/supersede/audit-routing)**: typed records are
  append-only and never hard-deleted. Misrouted, superseded, voided, or duplicate
  records are marked inactive via `lifecycle_event` provenance + optional
  frontmatter fields, and the relation-map filters them out of the active
  conclusion. See `docs/record-lifecycle.md` and
  `docs/superpowers/specs/2026-06-19-record-lifecycle-design.md`.

## Development

- Install: `pip install fastmcp pyyaml`
- Run: `python brain/mcp_server.py`
- Test: `pytest tests/`
- The MCP server is configured in each workspace's `.mcp.json`

## AITP v5 Runtime Hooks

- v5 hook metadata is generated from typed adapter packets under
  `runtime_hook_protocols` and `runtime_hook_installation`.
- v5 adapter CLI dispatch lives in `brain/v5/cli_adapters.py`; keep
  `brain/v5/cli.py` as the parser/thin command router rather than adding more
  adapter branches there.
- v5 hook bridge Markdown rendering lives in `brain/v5/hook_bridge_markdown.py`;
  keep `brain/v5/hook_install_templates.py` focused on payload construction and
  file writes so hook installation does not regress into a large template
  module.
- v5 hook installation fixture contracts live in
  `brain/v5/hook_install_contracts.py`; keep host installation payload
  contracts out of `hook_protocol_contracts.py`.
- v5 runtime entrypoint catalog data and CLI sample arguments live in
  `brain/v5/runtime_entrypoint_catalog.py`; keep
  `brain/v5/runtime_entrypoints.py` focused on copy/validation helpers.
- Codex can materialize explicit guard-call instructions with
  `aitp-v5 adapter hook-bridge codex <session-id> --output <path>`.
- Codex can materialize a native-ish stdin-runner installation fixture with
  `aitp-v5 adapter install-hooks codex <session-id> --output .codex/AITP_V5_HOOKS.json`.
  The fixture writes a Codex bridge plus sidecar and points `pre_tool` and
  `post_tool` at `hooks/aitp_v5_adapter_event_runner.py` with a declared repo
  `cwd`; `pre_tool` returns typed policy decisions, while `post_tool` persists
  hook trace records under `.aitp/runtime/hook_trace_events.jsonl`. It is
  runtime metadata only and keeps `summary_inputs_trusted=false`.
- Codex can also merge AITP v5 lifecycle hooks into an existing Codex
  `hooks.json` file with
  `aitp-v5 adapter install-hooks codex <session-id> --settings .codex/hooks.json`.
  The installer preserves existing events, adds idempotent `PreToolUse` and
  `PostToolUse` command hooks, writes the bridge sidecar, and validates the same
  `codex_hook_installation` public surface. The generated hooks file is runtime
  metadata only; typed kernel records remain authoritative.
- OpenCode can materialize plugin bridge instructions with
  `aitp-v5 adapter hook-bridge opencode <session-id> --output .opencode/AITP_V5_PLUGIN_BRIDGE.md`.
- OpenCode can materialize a native-ish stdin-runner plugin fixture with
  `aitp-v5 adapter install-hooks opencode <session-id> --output .opencode/AITP_V5_PLUGIN_HOOKS.json`.
  The fixture writes an OpenCode plugin bridge plus sidecar and points
  `plugin_hooks.pre_tool` and `plugin_hooks.post_tool` at
  `hooks/aitp_v5_adapter_event_runner.py` with a declared repo `cwd`;
  `pre_tool` returns typed policy decisions, while `post_tool` persists hook
  trace records under `.aitp/runtime/hook_trace_events.jsonl`. It is runtime
  metadata only and keeps `summary_inputs_trusted=false`.
- OpenCode can install a real project-local plugin file with
  `aitp-v5 adapter install-hooks opencode <session-id> --plugin .opencode/plugins/aitp-v5.js`.
  The generated plugin subscribes to `tool.execute.before` and
  `tool.execute.after`, calls `hooks/aitp_v5_adapter_event_runner.py` through
  cwd-independent argv using the active Python interpreter and absolute runner
  path, blocks through the typed `pre_tool_policy_decision`, and persists
  post-tool trace events without treating the plugin file as a truth source.
  Tests import the generated JavaScript module with Node and invoke both
  lifecycle handlers.
- Installed runtime hook files can be inspected with
  `aitp-v5 adapter install-audit <runtime> <args>` or
  `aitp_v5_audit_hook_installation`. The audit checks supplied Codex
  `hooks.json`, Claude Code settings, OpenCode plugin files, or generated
  fixtures for expected AITP runner tokens and returns the contracted
  `runtime_hook_installation_audit` surface. It is read-only and
  orientation-only.
- Default workspace-local runtime hook paths can be discovered with
  `aitp-v5 adapter install-paths` or
  `aitp_v5_discover_hook_install_paths`. The returned
  `runtime_hook_installation_paths` surface lists preferred and alternate
  Codex/Claude Code/Kimi Code/OpenCode install targets plus matching install/audit
  commands. It is convention metadata, not kernel state.
- Runtime hook smoke coverage can be reviewed with
  `aitp-v5 adapter smoke-coverage` or
  `aitp_v5_report_hook_smoke_coverage`. The returned
  `runtime_hook_smoke_coverage` surface is orientation-only and lists
  test-backed Codex/Claude Code/Kimi Code/OpenCode hook smoke checks, dynamic
  host-readiness coverage, and remaining real interactive lifecycle-event gaps.
- Dynamic host readiness can be checked with
  `aitp-v5 adapter host-readiness <runtime>` or
  `aitp_v5_audit_runtime_host_readiness`. The returned
  `runtime_host_readiness_audit` launches the local host command (`codex`,
  `claude`, `kimi`, or `opencode` by default), optionally audits the installed
  hook file, and can directly smoke Claude/Kimi `SessionStart` refresh. It is
  runtime evidence only, remains orientation-only, and cannot update claim
  trust.
- Dynamic lifecycle probing can be checked with
  `aitp-v5 adapter host-lifecycle <runtime>` or
  `aitp_v5_audit_runtime_host_lifecycle`. The returned
  `runtime_host_lifecycle_audit` runs a supplied host command, compares
  `.aitp/runtime/hook_trace_events.jsonl` before/after, and scans stdout/stderr
  for AITP hook output kinds. It remains orientation-only and is evidence about
  that invocation, not a global guarantee about all future host UI/session
  modes.
- Codex native `hooks.json` installation now writes command strings with the
  active Python interpreter and an absolute
  `hooks/aitp_v5_adapter_event_runner.py` path. Tests execute those commands
  from a temporary user workspace cwd, so Codex hooks no longer rely on the host
  process starting in the AITP repository root.
- Claude Code can materialize native hook settings with
  `aitp-v5 adapter hook-settings claude-code <session-id> --output .claude/settings.local.json`.
- Claude Code can also merge AITP v5 hooks into an existing settings file with
  `aitp-v5 adapter install-hooks claude-code <session-id> --settings .claude/settings.local.json`;
  this preserves existing hook entries and avoids duplicate AITP hook commands.
- Kimi Code can materialize or merge native TOML hook config with
  `aitp-v5 adapter hook-settings kimi-code <session-id> --output .kimi/AITP_V5_HOOKS.toml`
  and
  `aitp-v5 adapter install-hooks kimi-code <session-id> --settings .kimi/config.toml`.
- Claude Code and Kimi Code host installers now emit `SessionStart`,
  `PreToolUse`, and `PostToolUse` lifecycle commands with absolute hook script
  paths and the active Python interpreter. Their `SessionStart` commands call
  `refresh_workspace_startup_views`, regenerating a lightweight workspace
  summary, interaction worklist, and current-session topic status as
  orientation-only startup context, then return compact
  `workspace_refresh_progress` to avoid large chat payloads. Full
  replay/source-stack/L2/source reconstruction refresh remains explicit through
  `refresh_workspace_views`.
  Tests execute the generated `session-start` commands from a temporary user
  workspace cwd.
- `hooks/aitp_v5_claude_hook.py` reads Claude Code hook JSON from stdin. Its
  `PreToolUse` path maps destructive, remote, and expensive Bash commands to a
  v5 typed policy block and returns Claude `permissionDecision=deny`. It also
  recognizes AITP MCP/kernel entrypoints: direct unqualified
  `aitp_v5_apply_trust_update` calls are denied until a typed preflight source
  and `trust-preflight-*` token are present, while typed writes such as
  `aitp_v5_record_evidence` are logged as their v5 actions. Its `PostToolUse`
  path persists process trace events through `.aitp/runtime/hook_trace_events.jsonl`.
- `hooks/aitp_v5_kimi_hook.py` reads Kimi hook JSON from stdin and mirrors the
  Claude Code lifecycle bridge for Kimi Code TOML hooks. Generated Kimi hooks
  follow the official `[[hooks]]` config shape and keep config files as runtime
  metadata, not research truth.
- Shared context-aware pre-tool policy is exposed through
  `aitp-v5 policy pre-tool <args>` and `aitp_v5_evaluate_pre_tool_policy`.
  It returns the contracted `pre_tool_policy_decision` public surface with
  `truth_source=typed_records`, `summary_inputs_trusted=false`, and no authority
  to mutate kernel state or claim trust. It includes machine-readable
  `policy_reasons` so reviewers and adapters can inspect policy IDs/severities
  without parsing free-form messages. It now covers validation, L2 promotion,
  and summary-sourced
  `record_code_state`/`record_evidence`/`record_tool_run`/`execute_tool`/
  `register_tool_recipe`/`record_reference_location`/`record_physics_object`/
  `record_object_relation`/`record_sensemaking_report`/
  `ingest_subagent_result`/
  `create_validation_contract`/`record_validation_result`/
  `request_human_checkpoint`/
  `decide_human_checkpoint`/`create_promotion_packet`/
  `apply_promotion_packet` trust-changing attempts through the same CLI/MCP
  entrypoint. For `risk_level=rigorous` or `risk_level=adversarial`,
  `execute_tool` and `record_tool_run` must carry at least one typed
  `validation_contract_id` for the active claim before the pre-tool policy will
  allow the action. For high-risk `execute_tool`, the supplied validation
  contract must also bind the current `recipe_id` and `executor_id`; for
  high-risk `record_tool_run`, it must bind the current `recipe_id`.
  Built-in safe executors now include `formula_code_invariant_check`, which
  checks explicit formula refs, code refs, expected relations, observed
  relations, and matched/failed/missing status for formula-code translation
  work; `librpa_gw_run_metadata_check`, which records and checks frequency-grid
  and basis-cutoff metadata from versioned LibRPA/GW input/output artifacts;
  and `failure_mode_basis_check`, which checks that every named failure mode
  has explicit review basis. FQHE and LibRPA/GW domain packs recommend
  failure-mode review basis recipes; the LibRPA/GW pack also recommends
  `recipe-librpa-gw-formula-code-invariant` and
  `recipe-librpa-gw-run-metadata-diagnostic`.
  Execution brief evidence coverage includes both required action-budget
  outputs and additional typed outputs already supported by evidence records,
  so a later session can see a recorded `failure_mode_review_basis` without
  trusting summary prose.
  After a high-risk tool run, `record_validation_result` can persist whether
  the run satisfied the bound contract's required evidence outputs; status
  aliases such as `pass` and `partial_pass` normalize to canonical `passed` and
  `partial`. Partial results let agents record broad-contract progress without
  creating narrow throwaway contracts, including explicit
  `covered_failure_modes`, but they do not satisfy promotion gates. Passed
  results cannot omit required outputs or carry observed failure modes.
  High-risk `record_evidence` that cites `tool_run_ids` must also cite passed
  `validation_result_ids` for those runs before it can support trust-relevant
  claim state. Promotion packets now also carry `validation_result_ids` typed
  links: packet creation and L2 application reject tool-derived evidence unless
  passed validation results cover every cited tool run, and the shared pre-tool
  policy hard-blocks rigorous/adversarial promotion attempts that omit or
  mismatch those links. Pre-tool policy calls also carry `known_failure_modes`
  and block promotion-packet creation until at least one failure mode is named,
  so agents cannot treat evidence attachment alone as enough for L2 memory
  promotion. When the active claim has `strongest_failure_mode`, the supplied
  failure modes must cover that recorded risk before the policy allows packet
  creation. For rigorous/adversarial promotion with such recorded claim risk,
  the pre-tool policy also requires an approved
  `failure_mode_review_checkpoint_id` from the typed failure-mode review flow
  plus a passed `failure_mode_review_result_id` linked to that checkpoint.
  Execution briefs expose active claim L2 memory entries
  as orientation-only `known_context.memory_entries`; typed memory records under
  `memory/l2/entries` remain authoritative. Code-method memory brief entries
  include `code_state_ids` derived from linked evidence tool runs so version
  provenance stays visible without making the brief a truth source. Memory
  entries preserve `validation_result_ids` from promotion packets, and memory
  briefs expose those ids as orientation-only links back to typed validation
  records. Memory brief entries also include `failure_mode_review_checkpoint_id` and
  `failure_mode_review_result_id` when those typed links exist on the promoted
  memory entry. The
  execution-brief contract lives in `brain/v5/brief_contracts.py` and validates
  memory entries as orientation-only payloads with list-shaped refs.
- Session summaries generated by `write_session_summary` include active L2
  memory entry ids and validation-result ids in `source_records`, findings, and
  progress views as orientation-only resumption links. Edited summary files do
  not update typed memory or validation records; `read_summary_orientation`
  always returns `truth_source=false` and `can_update_kernel_state=false`.
- Workspace summaries generated by `write_workspace_summary` provide a
  workspace-level `overview.md` across active session bindings, active claims,
  promoted L2 memory entries, and validation-result links. The public surface is
  `workspace_summary_bundle`; it is orientation-only and regenerated from typed
  records.
- For deeper review than the compact execution brief, agents can call
  `aitp-v5 memory audit --claim <claim-id>` or
  `aitp_v5_audit_l2_memory_context`. This returns the contracted
  `l2_memory_audit` public surface, derived only from typed records, linking
  each active memory entry to its promotion packet, human checkpoint decision,
  evidence refs, validation result refs, code-state refs, and linked
  failure-mode review result basis refs while keeping `summary_inputs_trusted=false`
  and `can_update_kernel_state=false`.
- Agents can call `aitp-v5 source reconstruction-audit --claim <claim-id>` or
  `aitp_v5_audit_source_reconstruction` to check whether a claim has a
  reconstructable typed source stack: definitions, assumptions/scope,
  source-location coverage, object-relation dependency graph, explicit
  reconstruction-path evidence, and failure conditions. The contracted
  `source_reconstruction_audit` surface is read-only, uses only typed records,
  keeps `summary_inputs_trusted=false`, and cannot update claim trust.
- Agents can call `aitp-v5 source reconstruction-manifest` or
  `aitp_v5_build_source_reconstruction_manifest` to batch those audits across
  active claims. The contracted `source_reconstruction_manifest` surface lists
  complete/incomplete counts, aggregate missing-component counts, per-claim
  missing components, direct next-action commands, and recommended record types
  for source-stack closeout. It is orientation-only, handles empty
  legacy-import claim statements without rejecting the backlog, and cannot
  update kernel state or claim trust.
- Agents can call `aitp-v5 legacy source-reconstruction-plan` or
  `aitp_v5_build_legacy_source_reconstruction_plan` to derive a read-only
  reconstruction-path evidence backfill plan from the latest typed
  `needs_revision` legacy semantic review. The guarded apply surface,
  `aitp-v5 legacy source-reconstruction-apply` or
  `aitp_v5_apply_legacy_source_reconstruction_repair`, can write a narrow
  `source_reconstruction` evidence record with
  `supports_outputs=["reconstruction_path"]` when reviewed L3/candidate refs
  exist. It can update typed evidence coverage but cannot update claim trust or
  prove semantic losslessness.
- Agents can call `aitp-v5 summary replay` or
  `aitp_v5_write_workspace_replay_packet` for an orientation-only
  `workspace_replay_packet` across active sessions. It lists active claims,
  confidence states, evidence-output gaps, source-reconstruction gaps,
  linked memory/validation ids, and next actions from typed execution briefs.
  It is a lightweight long-term resumption surface, not a truth source, and
  cannot update kernel state or claim trust.
- Agents can call `aitp-v5 memory obsidian-view` or
  `aitp_v5_write_l2_obsidian_view` to generate an orientation-only Markdown
  review view for active L2 memory entries. The generated notes list memory
  scope, evidence refs, validation refs, and known failure modes, but keep
  `truth_source=false`; typed memory/audit records remain authoritative.
- Agents can call `aitp-v5 legacy l2-graph-manifest` or
  `aitp_v5_build_legacy_l2_graph_manifest` to inspect a legacy global `L2/`
  index/graph before typed migration. The manifest counts legacy entries,
  graph nodes/edges/steps/towers, records Obsidian view targets, and recommends
  typed L2 memory/object-relation migration while keeping the legacy graph
  orientation-only and unable to update trust.
- Agents can call `aitp-v5 legacy l2-obsidian-view` or
  `aitp_v5_write_legacy_l2_obsidian_view` to write a derived
  orientation-only Obsidian view under `.aitp/surfaces/legacy_l2_obsidian`.
  The view lists legacy entries and graph counts for browsing/triage, keeps
  `truth_source=false`, reports `memory_entry_count=0`, and requires typed L2
  migration before any trust update.
- Agents can call `aitp-v5 summary refresh` or
  `aitp_v5_refresh_workspace_views` as a single host-startup refresh point.
  It regenerates the workspace summary, replay packet, and active-session L2
  Obsidian view in a contracted `workspace_refresh_bundle`, remains
  orientation-only, and cannot update kernel state or claim trust.
  Claude/Kimi SessionStart hooks call the lighter startup refresh and return
  compact `workspace_refresh_progress` with topic-status handoff paths instead
  of dumping full `topic_status_bundles`; the full files are still written on
  disk.
- Agents can write goal continuation audit packets via `aitp-v5 goal write` or
  `aitp_v5_write_goal_continuation`. Each packet is written to
  `.aitp/surfaces/goal_continuation/` as JSON+Markdown and contains the
  objective, changed files, test results, smoke commands, readiness outcome,
  next actions, trust boundary, and blocking backlog. Future sessions can read
  the latest packet via `aitp-v5 goal latest` or `aitp_v5_read_latest_goal_continuation`
  to reconstruct context without chat history. These packets are orientation-only.
  Use repeated CLI args (`--changed-file`, `--test-run`, `--next-action`,
  `--audit-command`) and JSON args (`--commits-json`,
  `--changed-file-stats-json`) for audit handoffs; comma-separated legacy args
  are only for simple values. Stored `latest.json` packets must themselves pass
  the public `goal_continuation_packet` contract.
- Agents can call the theory research-state surface when a project produces a
  real source, result file, Fisherd/remote run, or theorem/proof gap. The CLI
  entrypoints are `aitp-v5 research-state register-source`,
  `attach-artifact`, `update-claim-status`, `create-proof-obligation`,
  `classify-event`, and `bounded-evidence`; MCP wrappers are
  `aitp_v5_register_source`, `aitp_v5_attach_artifact`,
  `aitp_v5_update_claim_status`, `aitp_v5_create_proof_obligation`,
  `aitp_v5_classify_research_event`, and
  `aitp_v5_record_bounded_numerical_evidence`. This surface composes
  reference locations, artifact refs, tool runs, scoped evidence, append-only
  claim maturity/status, and proof obligations. It cannot update claim trust,
  cannot promote L2 memory, and must keep finite numerical results scoped to
  explicit outputs such as `finite_L_H4_motif_formula_check_L10_L12`.
- Agents can call `aitp-v5 interaction preview <session-id>` or
  `aitp_v5_preview_interaction_recording` before or during a natural research
  conversation. The contracted `interaction_recording_preview` is read-only
  and derived from the typed execution brief. It reports whether the current
  session can stay lightweight, which records are recommended rather than
  required, which trust-changing records are deferred, and which triggers make
  the workflow heavier. It keeps `summary_inputs_trusted=false` and cannot
  update kernel state or claim trust.
- Agents can call `aitp-v5 legacy migration-audit` or
  `aitp_v5_audit_legacy_migration_coverage` against a completed
  `legacy-v5-lossless-*` migration run. The audit proves file accounting,
  archive-reference coverage, Markdown readability, and per-topic coverage
  status, but it must keep `semantic_lossless_proven=false` and
  `semantic_review_required=true`; semantic correctness of old physics content
  requires human/v5 review, not manifest accounting alone.
- Agents can call `aitp-v5 legacy semantic-review-queue` or
  `aitp_v5_build_legacy_semantic_review_queue` against the same migration run
  to turn accounting coverage into per-topic review work items. Each item
  reports legacy shape, active claim id, typed/archive coverage counts,
  source-reconstruction status, review priority, review reasons, and
  recommended actions. The queue is orientation-only and cannot update kernel
  state or claim trust; it operationalizes semantic review without proving it.
- Agents can call `aitp-v5 legacy semantic-review-result` or
  `aitp_v5_record_legacy_semantic_review_result` to persist a per-topic
  `legacy_semantic_review_result_record` after actual review. The record stores
  status, summary, reviewed legacy refs, reviewed typed refs,
  evidence/validation refs, remaining actions, and an optional checkpoint id.
  The semantic review queue reads these records back as
  `semantic_review_status`; the result record cannot update claim trust.
- Agents can call `aitp-v5 legacy semantic-repair-plan` or
  `aitp_v5_build_legacy_semantic_repair_plan` to derive a read-only repair plan
  from typed `needs_revision` legacy semantic review results. Agents can then
  call `aitp-v5 legacy semantic-repair-apply` or
  `aitp_v5_apply_legacy_semantic_repair` for narrow repairs such as
  `claim_statement_backfill`, `claim_scope_backfill`, and
  `claim_failure_mode_backfill`. Repairs require the matching review id, use
  reviewed legacy refs as their basis, can recover an empty statement from a
  reviewed L3 distillation's `distilled_claim` when the review action requests
  it, can recover an empty statement from an L1 question contract's
  `bounded_question` when the review action requests it, and can recover scope
  either from a legacy candidate's `regime_of_validity` or from an L1 question
  contract's `scope_boundaries`. Source selection follows the typed review
  action, so an L1 scope action is not allowed to be satisfied by candidate
  assumptions merely because both refs were reviewed. Claim failure modes can be
  recovered from L4 review basis or from L1 `Non-Success Conditions` when the
  review action requests that source. Frontmatter values are normalized before
  becoming proposed claim text, including YAML lists and maps, so repairs do not
  write Python collection reprs into claim statements, scopes, or failure modes.
  Failed validation-result follow-up is not a mechanical apply repair:
  `validation_result_revision` candidates are marked
  `external_evidence_required` with required action
  `record_revised_validation_result_before_semantic_pass`, because they need a
  repaired or replaced run and a new typed validation result before semantic
  pass.
  They update only the migrated claim and topic ledger, and write a durable
  `legacy_semantic_repair` record. The repair apply surface may update kernel
  content state, but it cannot update claim trust or prove semantic
  losslessness.
- Agents can call `aitp-v5 memory failure-modes --claim <claim-id>` or
  `aitp_v5_audit_failure_mode_coverage` for a read-only
  `failure_mode_audit` surface. It reports active uncertainty,
  `strongest_failure_mode`, validation-contract failure modes,
  promotion-packet known failure modes, reviewed failure modes,
  validation-result coverage, failure-mode review result basis refs, uncovered
  failure modes, and review actions from typed records only. Full passed
  validation covers contract failure modes; partial validation covers only
  explicit `covered_failure_modes` or unambiguous checked-output coverage,
  never summary prose. The audit cannot update kernel state or claim trust.
- Agents can call `aitp-v5 memory failure-mode-review --claim <claim-id>` or
  `aitp_v5_build_failure_mode_review_packet` to turn that typed audit into a
  read-only `failure_mode_review_packet`. It lists per-mode source labels,
  coverage labels, and physical adequacy questions for human/adversarial review
  before promotion; it cannot update kernel state or claim trust.
- Agents can call `aitp-v5 memory request-failure-mode-review --claim
  <claim-id>` or `aitp_v5_request_failure_mode_review_checkpoint` to create a
  typed `human_checkpoint_record` from that packet. Adapter pre-tool mapping
  treats the wrapper as `request_human_checkpoint`, so it inherits summary
  source blocking; the checkpoint is durable review state, not a trust update.
  High-risk promotion should pass the approved checkpoint as
  `--failure-mode-review-checkpoint` / `failure_mode_review_checkpoint_id` and
  the passed result as `--failure-mode-review-result` /
  `failure_mode_review_result_id`; promotion packets, resulting L2 memory
  entries, and `l2_memory_audit` preserve both ids for provenance review.
- Agents can call `aitp-v5 memory failure-mode-review-result --claim
  <claim-id> --checkpoint <checkpoint-id> ...` or
  `aitp_v5_record_failure_mode_review_result` after an approved failure-mode
  review checkpoint. The resulting contracted
  `failure_mode_review_result_record` persists the actual review basis:
  reviewed failure modes plus literature/tool/evidence/validation/reference
  citations. External/literature `basis_refs` are labels, while local typed refs
  must resolve to same-topic/claim records. It keeps
  `summary_inputs_trusted=false` and `can_update_claim_trust=false`.
- To audit a claim confidence state directly, agents can call
  `aitp-v5 trust audit --claim <claim-id>` or
  `aitp_v5_audit_claim_trust`. This returns the contracted
  `claim_trust_audit` public surface, derived only from typed records, showing
  supporting/challenging evidence refs, passed/failed validation results, L2
  memory entry ids, code-state ids, durable `trust_update_record_ids`, support
  state, and review actions while keeping `summary_inputs_trusted=false`,
  `can_update_kernel_state=false`, and `can_update_claim_trust=false`.
- Each trust apply attempt writes a contracted `trust_update_record` under the
  typed registry. Agents can retrieve it through
  `aitp-v5 trust update-record <update-id>` or
  `aitp_v5_get_trust_update_record`; the record is the authoritative mutation
  history, not the generated audit or summary text.
- Generated Codex and OpenCode bridge payloads include a
  `pre_tool_policy_entrypoint` pointing to that shared surface, so runtime
  adapters can wire validation/promotion pre-tool checks without reimplementing
  policy logic. They also carry `gate_protocols` generated from
  `runtime_gate_protocols`, so bridge files expose code-state, record
  evidence/tool-run, execute-tool, tool-recipe, reference-location, physics-object/
  object-relation, sensemaking-report, subagent-ingestion,
  validation-contract, human-checkpoint request/decision,
  promotion-packet creation/application, and validate/promote sequences as
  machine-readable payload and rendered Markdown.
- Runtime adapters can consume those generated bridge `gate_protocols` through
  `brain/v5/adapter_runtime.py::evaluate_bridge_gate_pre_tool_policy`, which
  verifies the bridge sequence and then delegates to the shared typed-record
  pre-tool policy surface. `evaluate_bridge_lifecycle_event` provides the thin
  adapter-neutral lifecycle wrapper for pre-tool events, and
  `evaluate_platform_pre_tool_event` normalizes Codex/OpenCode pre-tool payloads
  into that same typed decision path. The normalizer is exposed through
  `aitp-v5 adapter pre-tool-event <runtime> <session-id> ...` and
  `aitp_v5_evaluate_adapter_pre_tool_event`, returning the contracted
  `pre_tool_policy_decision` surface. Generated Codex/OpenCode bridge payloads
  advertise this as `pre_tool_event_entrypoint` so runtime adapters can discover
  the correct CLI/MCP invocation without prose scraping. The bridge entrypoints
  also advertise machine-readable `pre_tool_policy_entrypoint.input_schema` and
  `pre_tool_event_entrypoint.platform_event_schema`, including `risk_level`,
  optional `evidence_refs`, optional `validation_contract_ids`, optional `tool_run_ids`, optional
  `validation_result_ids`, optional `recipe_id`, optional
  `executor_id`, optional `human_checkpoint_id`, optional `checkpoint_id`, and
  optional nested `packet` input, while typed kernel records remain the
  authority. Runtime event normalizers read link fields from that nested
  `packet` input as well as from top-level tool input.
- Bridge materializers write a machine-readable JSON sidecar beside the generated
  Markdown and return its `payload_path`; runtime hook runners should use
  `adapter pre-tool-event --bridge-path <payload-path> --event-json <json>` to
  consume the bridge payload without treating generated Markdown as a truth
  source. Generated bridge payloads also carry `pre_tool_event_runner.argv` with
  the concrete runtime/session/sidecar invocation and a `<platform-event-json>`
  placeholder. `hooks/aitp_v5_adapter_event_runner.py` is the host-facing stdin
  bridge for that path: it reads platform event JSON from stdin, validates the
  generated runner/sidecar, fills runtime/session/pre-tool defaults, and returns
  the same typed `pre_tool_policy_decision` plus hook exit code. Generated
  bridge sidecars advertise that host-facing command in
  `pre_tool_event_runner.stdin_runner.argv` or
  `plugin_bridge.pre_tool_event_runner.stdin_runner.argv`.
- Adapter packet `runtime_gate_protocols.record_code_state`,
  `runtime_gate_protocols.record_evidence`,
  `runtime_gate_protocols.record_tool_run`,
  `runtime_gate_protocols.execute_tool`,
  `runtime_gate_protocols.register_tool_recipe`,
  `runtime_gate_protocols.record_reference_location`,
  `runtime_gate_protocols.record_physics_object`,
  `runtime_gate_protocols.record_object_relation`,
  `runtime_gate_protocols.record_sensemaking_report`,
  `runtime_gate_protocols.ingest_subagent_result`,
  `runtime_gate_protocols.create_validation_contract`,
  `runtime_gate_protocols.record_validation_result`,
  `runtime_gate_protocols.request_human_checkpoint`,
  `runtime_gate_protocols.decide_human_checkpoint`,
  `runtime_gate_protocols.create_promotion_packet`,
  `runtime_gate_protocols.apply_promotion_packet`,
  `runtime_gate_protocols.validate_claim`, and
  `runtime_gate_protocols.promote_to_l2` explicitly sequence
  `evaluate_pre_tool_policy` before the trust-relevant action and require
  `policy_reasons` as the machine-readable routing field.
- `record_gate_coverage_audit` is exposed through
  `aitp-v5 adapter record-gate-audit` and
  `aitp_v5_audit_record_gate_coverage`; it reports all runtime record
  protocols, all runtime gate protocols, gated record actions, ungated record
  actions, and extra non-record gates from the adapter protocol registry.
- Shared pre-tool policy carries `risk_level` and optional
  `human_checkpoint_id`; for adversarial risk, trust-changing actions are
  hard-blocked unless that checkpoint resolves to a decided typed
  `HumanCheckpointRecord` with `decision=approve` for the active claim.
  Rigorous/adversarial tool execution additionally requires an explicitly
  linked open `ValidationContractRecord` bound to the concrete tool recipe and
  executor, so expensive or correctness-critical numerical/formula-code checks
  cannot run as trust-relevant work without a typed validation plan for that
  tool path.
- Claude Code `PreToolUse` uses that shared policy for code-state provenance,
  tool-recipe registration, reference-location pointers, physics-object/relation graph writes,
  sensemaking reports, validation, human-checkpoint request/decision, promotion-packet
  creation/application, and L2 promotion MCP calls: it
  resolves the typed claim, cited evidence refs, and linked or requested code
  states, then reuses `evaluate_policy` before the tool runs.
- Trust-changing confidence updates use a request-bound preflight proof token:
  `preflight_trust_update` emits `preflight_token`/`preflight_proof`, and
  `apply_trust_update` refuses otherwise policy-allowed mutations unless the
  request carries the matching token.
- Hook trace events are durable process history only. They do not create
  evidence, memory, validation, or claim-confidence records.
- The vNext human-idea/AI-execution/human-steering plan is a first-class
  readiness input. Agents can call `aitp-v5 status vnext-readiness`,
  `aitp-v5 status vnext-readiness --compact`, or
  `aitp_v5_build_vnext_readiness_manifest` for the contracted
  `vnext_readiness_manifest`, which reports implemented control-plane
  workstreams, output-stability support, literature intake support, priority
  host conformance with OpenCode deferred, and remaining lane-exemplar backlog.
  Prefer `--compact` for startup and quick continuation checks so hosts do not
  dump the full lane-exemplar item list into chat context.
  `adapter final-readiness` includes this manifest but still keeps legacy
  semantic review as a separate blocking content backlog and cannot update
  claim trust.
- Human-facing reports have a stable output spine defined in `docs/AITP_SPEC.md`
  and topic-local `final_output_profile` records. Future report changes should
  be additive unless a new output version and compatibility note are recorded.
- Current-session topic status now renders `session_start.generated.md` as the
  resume-first surface for future agents: it includes the active
  `final_output_profile`, strategy-memory `next_time_rule` items, lane exemplar
  trust boundaries, and any required operator checkpoint. It remains
  orientation-only and cannot update kernel state or claim trust.
- `aitp-v5 status topic <session-id> --compact` and
  `aitp_v5_write_topic_status_surfaces_compact` should be preferred when a host
  needs only a small continuation payload; they still write the full status
  files but do not dump the complete `topic_state` JSON into chat.
- For the active QSGW/LibRPA theory workflow, prioritize a lightweight
  "research cockpit" slice over heavier bookkeeping: maintain a
  final/diagnostic lane manifest, make final plotting scripts read explicit
  final allowlists, require diagnostic plot/profile labels for assumption-based
  outputs, let refresh/status scripts emit AITP-ready intake manifests or JSONL,
  and generate compact dashboard/report dry-runs for group meetings and
  cross-session continuation. This should reduce friction, not require every
  monitor note or exploratory plot to become a typed record. It must not auto
  update trust, promote diagnostic observations, or treat unfinished,
  nonconverged, negative-gap, noiter, or contaminated-root data as final
  evidence.
- The first kernel surface for that slice is `aitp-v5 status qsgw-cockpit`
  (`aitp_v5_write_qsgw_cockpit_surfaces` for MCP). It writes
  `.aitp/topics/qsgw-headwing-update-librpa/runtime/qsgw_cockpit_manifest.json`,
  `qsgw_cockpit_dashboard.md`, and `qsgw_plot_guard.generated.md` from typed
  records plus `research/librpa/reports` and `research/librpa/scripts` scans.
  The surface is `qsgw_cockpit_bundle`, orientation-only, and explicitly forbids
  trust updates; downstream theory-workspace work should wire refresh scripts to
  emit intake JSONL/manifests and plotting scripts to read explicit lane
  allowlists.
- The cockpit also discovers downstream `*_lane_manifest_current.json` and
  `*_aitp_intake_current.jsonl` files in `research/librpa/reports`. Compact
  output reports how many downstream lane manifests/intake files/records exist
  and whether intake rows are guarded. Audit/intake JSONL by itself is still
  orientation-only; result-refresh candidates and plot-script fail-closed guards
  remain separate follow-up work unless the compact next-actions say otherwise.
- Legacy semantic review packets are read-only audit surfaces and must tolerate
  malformed legacy leftover records in unrelated registry files. They should use
  valid-record reads for packet context so a stale Markdown stub cannot crash
  topic-question backfill or semantic-review inspection. This robustness does
  not make any legacy item semantically lossless: final readiness still reports
  `legacy_semantic_review_backlog` until the typed reviews, source
  reconstruction, archive sampling, and human checkpoints actually clear.
- Goal continuation CLI supports JSON file arguments for Windows-safe audit
  writes: use `--readiness-json-file`, `--commits-json-file`, and
  `--changed-file-stats-json-file` when PowerShell would otherwise strip JSON
  quotes from inline arguments. File reads accept UTF-8 with or without BOM so
  PowerShell `Set-Content -Encoding UTF8` output is safe. The packet remains
  orientation-only and should be used to preserve commit ranges, tests, smoke
  commands, blocking backlogs, and next actions for cross-session review.

## Protocol Layer Map

| Layer | Purpose | Key Tools |
|-------|---------|-----------|
| L0 | Source discovery & ingestion | `register_source`, `list_sources`, `ingest_knowledge` |
| L1 | Reading & framing | (artifacts filled by agent) |
| L2 | Cross-topic knowledge graph | `create_l2_node`, `create_l2_edge`, `promote_candidate` |
| L3 | Derivation campaign | `advance_to_l3`, `advance_l3_subplane`, `submit_candidate` |
| L4 | Validation | `create_validation_contract`, `submit_l4_review`, research loop |
| Cross | Health & navigation | `health_check`, `list_topics`, `get_status`, `get_execution_brief` |

## Operator Rule

- Treat this repository as protocol-first.
- Python may materialize state, run audits, and execute explicit handlers.
- Research judgment should remain visible in durable artifacts rather than hidden
  heuristics.
