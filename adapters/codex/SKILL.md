---
name: aitp-runtime
description: Reference for running AITP from Codex. All topic work uses MCP tools.
---

# AITP Runtime For Codex

## Stage flow (v4.0)

```
L0 (discover) → L1 (read → frame) → L3 (flexible workspace) → L4 (validate) → L2 (knowledge)
```

L5 removed in v4.0. L2 is the endpoint.

## Key tools

| Phase | Tool |
|-------|------|
| L0 | `aitp_bootstrap_topic`, `aitp_register_source`, `aitp_advance_to_l1` |
| L1 | `aitp_parse_source_toc`, `aitp_write_section_intake`, `aitp_advance_to_l3` |
| L3 | `aitp_switch_l3_activity`, `aitp_submit_candidate`, `aitp_submit_idea` |
| L4 | `aitp_submit_l4_review`, `aitp_return_to_l3_from_l4` |
| L2 | `aitp_request_promotion`, `aitp_promote_candidate` |

Retreat: `aitp_retreat_to_l0`, `aitp_retreat_to_l1`.

Always call `aitp_get_execution_brief` before deciding what to do.
