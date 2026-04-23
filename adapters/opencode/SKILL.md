---
name: aitp-runtime
description: Reference note for the OpenCode adapter surface; the active OpenCode bootstrap now lives in `/.opencode/plugins/aitp.js` plus the repository `skills/` directory.
---

# OpenCode Adapter Reference

The public OpenCode path is now plugin-first:

1. install the plugin from `/.opencode/plugins/aitp.js` or follow `docs/INSTALL_OPENCODE.md`;
2. let the plugin inject `using-aitp` and register the repository `skills/` directory;
3. all protocol actions go through MCP tools (`mcp__aitp__aitp_*`) — OpenCode cannot directly edit topic files.

## Stage flow

```
L0 (discover: register sources, fill source_registry.md)
 → L1 (read/frame: read sources, frame question, fill 5 L1 artifacts)
 → L3 (derive: ideation → planning → analysis → integration → distillation)
 → L4 (validate: consistency checks, boundary cases)
 → L2 (promote: human-approved trusted knowledge)
 → L5 (write: paper draft with full provenance)
```

## Key tools

| Phase | Tool | When |
|-------|------|------|
| L0 | `aitp_register_source` | Register each source (paper, dataset, code, experiment, etc.) |
| L0 | `aitp_advance_to_l1` | After source registry passes gate |
| L1 | `aitp_advance_to_l3` | After all L1 artifacts pass gate |
| L3 | `aitp_advance_l3_subplane` | Move between subplanes (respect allowed transitions) |
| L3 | `aitp_submit_candidate` | After distillation, submit a distilled claim |
| L4 | `aitp_create_validation_contract` | Define mandatory physics checks |
| L4 | `aitp_submit_l4_review` | Submit adjudication outcome |
| L4 | `aitp_return_to_l3_from_l4` | Return to L3 after L4 (mandatory) |
| L2 | `aitp_request_promotion` → `aitp_resolve_promotion_gate` → `aitp_promote_candidate` | Promote validated claim |
| L5 | `aitp_advance_to_l5` | After flow_notebook.tex exists |

Retreat tools: `aitp_retreat_to_l0` (L1/L3→L0), `aitp_retreat_to_l1` (L3→L1), `aitp_return_from_l5` (L5→L3).

## Phase 6 behavior

During OpenCode topic work:

1. vague ideas trigger the clarification sub-protocol before `L0→L1→L3→L4→L2→L5` execution;
2. clarification should ask only the smallest useful question set and should tighten `L1/question_contract.md`;
3. use `AskUserQuestion` popup for all human decision points — never type options as plain text;
4. the adapter should treat checkpoints as normal file-backed runtime surfaces, not as a separate controller process;
5. always call `aitp_get_execution_brief` first to check gate status before taking any action.
