---
name: aitp-runtime
description: Enter the AITP runtime from OpenClaw so topic work remains auditable, resumable, and governed by the AITP charter.
---

# AITP Runtime For OpenClaw

Use this skill when the task belongs inside AITP rather than a free-form note
workflow. All protocol actions go through MCP tools (`mcp__aitp__aitp_*`) —
OpenClaw cannot directly edit topic files.

## Stage flow

```
L0 (discover: register sources, fill source_registry.md)
 → L1 (read/frame: read sources, frame question, fill 5 L1 artifacts)
 → L3 (derive: ideation → planning → analysis → integration → distillation)
 → L4 (validate: consistency checks, boundary cases)
 → L2 (promote: human-approved trusted knowledge)
 → L5 (write: paper draft with full provenance)
```

## Start here

1. `aitp_bootstrap_topic` — create a new topic (starts at L0)
2. `aitp_register_source` — register sources (papers, datasets, code, experiments, etc.)
3. `aitp_advance_to_l1` — transition to reading and framing after L0 gate passes

If the idea is still vague after routing, ask clarification questions before
full execution. Tighten `scope`, `assumptions`, and `target_claims` first.

## Key tools

| Phase | Tool | When |
|-------|------|------|
| L0 | `aitp_register_source` | Register each source |
| L0 | `aitp_advance_to_l1` | After source registry passes gate |
| L1 | `aitp_advance_to_l3` | After all L1 artifacts pass gate |
| L3 | `aitp_advance_l3_subplane` | Move between subplanes |
| L3 | `aitp_submit_candidate` | After distillation |
| L4 | `aitp_create_validation_contract` | Define physics checks |
| L4 | `aitp_submit_l4_review` | Submit adjudication |
| L4 | `aitp_return_to_l3_from_l4` | Return to L3 after L4 |
| L2 | `aitp_request_promotion` → `aitp_resolve_promotion_gate` → `aitp_promote_candidate` | Promote claim |
| L5 | `aitp_advance_to_l5` | After flow_notebook.tex exists |

Retreat tools: `aitp_retreat_to_l0` (L1/L3→L0), `aitp_retreat_to_l1` (L3→L1), `aitp_return_from_l5` (L5→L3).

## Hard rules

- Use `AskUserQuestion` popup for ALL human decision points — never type options as plain text.
- Always call `aitp_get_execution_brief` first to check gate status.
- If conformance fails, the run does not count as AITP work.
- Do not present exploratory output as validated reusable knowledge.
- Treat human checkpoints as decision points, not disposable chat state.
