---
name: aitp-protocol
version: "0.5.0"
implementation_generation: "v5"
protocol_scope: "typed research graph, progressive recording, trust-controlled agent workflow"
implementation_entrypoint: "brain/v5/native_mcp.py"
cli_entrypoint: "python -m brain.v5.cli"
legacy_stage_model: "orientation-only"
description: Current operating manual for AITP v5. Agents work through typed records, progressive navigation, evidence, validation, and human checkpoints; legacy L0-L4 stage files are migration context only.
---

# AITP Protocol 0.5.0 - Typed Research Graph Operating Manual

AITP 0.5.0 is the v5 typed-record protocol for human-in-the-loop theoretical-physics research. It replaces the old L0-L4 stage machine as the active execution contract.

The current source of truth is the typed graph under `<topics-root>/.aitp/`, not legacy topic `state.md` frontmatter, not stage gates, not summaries, and not host runtime logs.

## Non-Negotiable Boundary

```text
typed records are truth candidates
briefs, summaries, dashboards, hooks, and RAG are orientation
trust changes require evidence, validation, scope, and human gates
legacy L0-L4 files are migration material only
```

Agents must not advance research by manually editing topic state files. State-changing work goes through v5 MCP tools or the v5 CLI fallback.

## Active Architecture

```text
human / agent / Hakimi
        |
        v
AITP v5 MCP tools: aitp_v5_*
        |
        v
<topics-root>/.aitp/ typed records
        |
        v
execution brief, relation map, process graph, recording navigation, audits
```

The active implementation entrypoint is:

```text
brain/v5/native_mcp.py
```

MCP hosts must not use these legacy entrypoints for current research:

```text
brain/native_mcp.py
brain/mcp_server.py
```

Those files may remain in the repository for rollback, tests, and migration, but they are not the current agent-facing protocol.

## Canonical Store Layout

A workspace normally uses:

```text
<workspace>/research/aitp-topics/.aitp/
```

Important areas:

```text
.aitp/
|-- registry/      claims, evidence, sources, artifacts, tools, validation, checkpoints, trust
|-- topics/        topic-local views and runtime dashboards derived from records
|-- runtime/       sessions, bindings, hook traces, runtime state
|-- contexts/      reusable research context records
|-- memory/        evidence-backed promoted memory
|-- surfaces/      generated read-only views and review packets
|-- tools/         tool metadata and executor surfaces
|-- curated_rag/   optional heuristic background corpus
|-- migrations/    legacy-store accounting and review packets
`-- schemas/       schemas and public surface contracts
```

## Current Research Workflow

AITP 0.5.0 is a read-first, progressive-disclosure workflow.

### 1. Classify the User Intent

Choose the lightest path that preserves truth:

| Intent | Default AITP behavior | Write only when |
|---|---|---|
| Generic old-knowledge Q&A | No AITP unless tied to an existing topic/claim/source | The answer changes durable project knowledge |
| Prior-topic status | Read recovery/audit surfaces, brief, relation map | User asks for handoff or resolves a checkpoint |
| Exploratory discussion | Read topic context if known; otherwise stay conversational | A durable question, route, source, result, or gap emerges |
| Active continuation | Restore session and claim context | Durable source/artifact/evidence/validation/route/checkpoint appears |
| Final synthesis or trust action | Run relation map and trust/promotion preflight | Required evidence, validation, and human gate are present |

Do not create a topic, claim, session, or memory entry merely because an idea is interesting.

### 2. Locate The Current Graph Position

Use read-only tools first:

```text
aitp_v5_build_workspace_recording_audit
aitp_v5_get_execution_brief
aitp_v5_get_claim_relation_map
aitp_v5_get_process_graph_slice   # only when the next action needs full context
```

The agent should know at least:

- topic id,
- session id,
- active claim id,
- current claim status and uncertainty,
- evidence and validation coverage,
- blockers and forbidden actions,
- next valid actions.

### 3. Record Only Durable Moments

AITP is not a transcript logger. Record when a research-relevant fact changed or became durable:

- reusable source identity or source location,
- source asset, note, artifact, table, figure, raw dump, report, or patch,
- tool/code run with research-relevant output,
- evidence, anomaly, contradiction, failed check, or negative result,
- validation contract or validation result,
- proof obligation or unresolved theory gap,
- route selection, pivot, abandonment, or split,
- human checkpoint request/decision,
- claim status/scope update,
- promotion or trust preflight result,
- session-end handoff that future agents must recover.

Do not record generic explanations, unaccepted brainstorming, repeated summaries, file inspections with no research information, or setup failures unrelated to the scientific claim.

### 4. Use Progressive Recording Navigation

For durable moments, do not guess the write tool. Navigate:

```text
aitp_v5_classify_recording_candidate
aitp_v5_get_recording_navigation_state
aitp_v5_expand_recording_slot
<typed write or preflight tool named by the slot expansion>
aitp_v5_verify_recording_effect
```

The first navigation response should be shallow: current topic/session/claim, first-level slots, blockers, and recommended moments. Expand exactly one slot at a time. Deep write tools appear only at the leaf layer.

### 5. Keep Trust Separate From Activity

A source location is not evidence. A tool run is not validation. A summary is not proof. A failed application run is not automatically a failed algorithmic claim.

Before claim confidence, memory promotion, or final reusable conclusion:

```text
aitp_v5_get_claim_relation_map
aitp_v5_audit_l2_memory_context
aitp_v5_trust_preflight / corresponding trust preflight surface
human checkpoint when required
```

Trust updates must cite typed evidence, typed validation or explicit bounded justification, known failure modes, and scope.

## Typed Record Families

Common durable write targets include:

| Research moment | Typed record family |
|---|---|
| Claim or status | claim, claim_status, trust_update |
| Source/paper/note location | source_asset, reference_location, registered_source |
| Artifact/report/table/plot/log | artifact |
| Physics definition/object | physics_object |
| Equation/relation/assumption | object_relation |
| Code version or patch state | code_state |
| Tool recipe/run/output | tool_recipe, tool_run |
| Scientific support/negative result | evidence |
| Required check | validation_contract |
| Check result | validation_result |
| Open theorem/review gap | proof_obligation |
| Route choice or pivot | exploration, route, sensemaking_report |
| Human decision | checkpoint |
| Long-term reusable memory | promotion_packet, memory_entry |

## Legacy L0-L4 Handling

Legacy L0/L1/L3/L4 directories, `state.md`, legacy `brain/cli`, and legacy MCP aliases are historical and migration surfaces.

They may be read for orientation, provenance recovery, or migration accounting. They must not be used as the active execution contract for new research.

When old content matters:

1. discover it through v5 legacy/audit tools,
2. preserve source paths and hashes,
3. import or reference it as orientation-only unless reviewed,
4. create typed v5 records for any durable claim, evidence, validation, or memory,
5. keep legacy L2 seeds quarantined until reviewed and promoted.

## Host Integration Rules

- Codex, Claude Code, Kimi Code, Hakimi, and other hosts should use the same project-scope AITP repo and topics root.
- MCP config must point to `brain/v5/native_mcp.py`.
- The `aitp-v5` CLI wrapper is for diagnostics and fallback operations, not the MCP server command.
- Hooks may refresh orientation or enforce pre-tool policy. Hooks cannot update claim trust or promote memory by themselves.
- Host summaries and RAG are advisory. They are not accepted evidence unless backed by typed records.

## Strict Version Contract

AITP 0.5.0 expects:

```text
release version: 0.5.0
implementation generation: v5
MCP server: aitp-v5-brain
MCP server version: 0.5.0
canonical entrypoint: brain/v5/native_mcp.py
legacy entrypoints in active configs: forbidden
normal tool prefix: aitp_v5_*
legacy alias tools: discovery/bootstrap compatibility only
```

`aitp-pm doctor` should fail when project installs point at legacy MCP entrypoints, when the protocol metadata does not declare v5 implementation, or when recorded installs are not aligned with the current package version.

## Current Completion Boundary

The v5 infrastructure is usable: typed records, MCP tools, CLI fallback, recording navigator, relation maps, migration audits, and project-scope installs are active.

A migrated workspace may still have `review_required` legacy L2 seed work. That means old imported memory is quarantined as orientation-only; it does not block the v5 runtime, but it does block treating those seeds as trusted claim support.
