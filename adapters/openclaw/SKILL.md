---
name: aitp-runtime
description: Reference for running AITP from OpenClaw. All topic work uses MCP tools (mcp__aitp__aitp_*).
---

# AITP Runtime For OpenClaw

## Stage flow (v4.0)

```
L0 (discover) → L1 (read → frame) → L3 (flexible workspace) → L4 (validate) → L2 (knowledge)
```

L5 (writing) removed in v4.0. L2 is the endpoint.

## Key tools

| Phase | Tool | When |
|-------|------|------|
| Start | `aitp_bootstrap_topic` | Create new topic |
| L0 | `aitp_register_source` | Register each source |
| L0 | `aitp_advance_to_l1` | After source registry passes gate |
| L1 | `aitp_advance_to_l3` | After all L1 artifacts pass gate |
| L3 | `aitp_switch_l3_activity` | Switch between activities |
| L3 | `aitp_submit_candidate` | Submit claim for validation |
| L4 | `aitp_submit_l4_review` | Submit adversarial review |
| L4 | `aitp_return_to_l3_from_l4` | Return to L3 after validation |
| L2 | `aitp_request_promotion` → `aitp_resolve_promotion_gate` → `aitp_promote_candidate` | Promote to L2 |

Retreat: `aitp_retreat_to_l0`, `aitp_retreat_to_l1`.

## Rules

- Always call `aitp_get_execution_brief` first to check gate status.
- Use `AskUserQuestion` for all human decisions.
- All protocol actions go through MCP tools — do not edit topic files directly.
