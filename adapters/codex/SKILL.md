---
name: aitp-runtime
description: Reference note for the Codex adapter surface; Codex should enter `using-aitp` at session start and keep Phase 6 decision records current during topic work.
---

# Codex Adapter Reference

The public Codex path is skill-discovery-first:

1. let Codex load repository `skills/` and enter `using-aitp` before any substantive theory response;
2. if the user starts from a vague idea, run the clarification sub-protocol before normal `L0→L1→L3→L4→L2→L5` execution;
3. all protocol actions go through MCP tools (`mcp__aitp__aitp_*`) — Codex cannot directly edit topic files.

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

During Codex-driven topic work:

1. keep `L1/question_contract.md` and `L0/source_registry.md` current before deep execution;
2. if ambiguity remains, ask up to 3 clarification rounds with 1-3 questions per round;
3. use `AskUserQuestion` popup for all human decision points — never type options as plain text;
4. treat "AITP pause" as a question to the human in chat, not as a background process or hidden controller;
5. always call `aitp_get_execution_brief` first to check gate status before taking any action.
