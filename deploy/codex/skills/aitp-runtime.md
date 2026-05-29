---
name: aitp-runtime
description: Codex app runtime skill for continuing an AITP theoretical-physics topic through the L0-L1-L3-L4-L2 protocol loop after using-aitp has claimed the task.
---

# AITP Runtime In Codex App

## Mandatory First Step

For every AITP topic iteration, start by getting the execution brief:

```text
aitp_get_execution_brief(topics_root="{{TOPICS_ROOT}}", topic_slug=<slug>)
```

The brief is the immediate execution contract. Follow its stage, gate status,
skill hint, blocked work, and allowed work before deciding the next action.

## Stage Loop

Use this loop conceptually, with actual Codex tool names:

```text
while topic is active:
  brief = aitp_get_execution_brief(topics_root="{{TOPICS_ROOT}}", topic_slug=<slug>)

  if brief.gate_status starts with "blocked":
    repair the flagged artifact through AITP tools
    continue

  if brief.stage == "L0":
    register sources, classify source fidelity, then advance only when ready

  if brief.stage == "L1":
    build source intake, assumptions, notation, contradictions, and framing

  if brief.stage == "L3":
    work in the active subplane: ideate, plan, analyze, derive, gap-audit,
    integrate, or distill

  if brief.stage == "L4":
    validate adversarially, record checks, and return results to L3

  if promotion is requested:
    present the human gate and resolve it through AITP before any L2 write
```

## Codex-Specific Interaction Rules

- When upstream AITP skills mention `AskUserQuestion`, ask through Codex's
  available user-interaction channel. If no structured prompt tool is active,
  ask one concise plain-text question and wait.
- Skip Claude-only `ToolSearch(query="select:AskUserQuestion", ...)` steps.
- Map `mcp__aitp__aitp_*` examples to the actual AITP MCP tool names exposed in
  Codex.
- If AITP tools are unavailable, diagnose setup rather than directly editing
  topic state.

## Layer Discipline

- L0 records provenance only. It does not assert truth.
- L1 is provisional. It may contain understanding, contradictions, notation,
  and assumptions, but not trusted reusable knowledge.
- L3 is untrusted working space for ideas, derivations, numerical runs, failed
  routes, and candidate claims.
- L4 adjudicates. It validates, rejects, weakens, or returns work for repair.
- L2 is trusted reusable memory. It requires promotion discipline.

## Physics Validation Obligations

Before treating a result as strong, check whether the active lane needs:

- dimensional consistency,
- algebraic consistency,
- limiting cases and known limits,
- symmetry or Ward identity checks,
- causality, unitarity, and conservation laws where applicable,
- approximation validity and scale separation,
- numerical convergence, benchmark comparison, and error bars for computation,
- explicit mismatch or negative-result records when the result fails.

Do not bury a failed check in prose. Record it as protocol state.

## Fallback Diagnostics

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py doctor
uv run --with pyyaml --with jsonschema --with fastmcp python -m py_compile brain/mcp_server.py brain/cli/__init__.py brain/gates.py brain/state.py
```
