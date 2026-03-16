---
name: aitp-runtime
description: Route substantial research work through the installed `aitp` CLI so Codex follows the AITP charter and protocol surface.
---

# AITP Runtime

## Required entry

1. Start topic work with `aitp bootstrap ...`, `aitp resume ...`, or `aitp loop ...`.
2. Read the generated `runtime_protocol.generated.md`, `agent_brief.md`,
   `operator_console.md`, and `conformance_report.md`.
3. Register reusable operations when needed.
4. End with `aitp audit --topic-slug <topic_slug> --phase exit`.

## Hard rules

- If conformance fails, the run does not count as AITP work.
- Prefer durable control notes and contracts over hidden heuristics.
- Do not treat a new method as trusted before the relevant gates are satisfied.
