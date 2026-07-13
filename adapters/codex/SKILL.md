---
name: aitp-runtime
description: Compatibility pointer for the Codex AITP v5 runtime; canonical Codex skills and plugin assets live under deploy/codex and plugins/aitp-research-protocol.
---

# AITP V5 For Codex

Codex is the default interactive research host. Use these canonical assets:

- MCP entrypoint: `brain/v5/native_mcp.py`
- compact tools: `aitp_v5_codex_*`
- runtime skill: `deploy/codex/skills/aitp-runtime.md`
- gateway skill: `deploy/codex/skills/using-aitp.md`
- plugin package: `plugins/aitp-research-protocol/`

Start with `aitp_v5_codex_autoroute`, restore bounded state with
`aitp_v5_codex_enter`, expand one needed context family with
`aitp_v5_codex_expand`, and use the guided recording/closeout facades only at
durable research moments.

Legacy L0-L4 files are read/migration context only. Do not enable legacy writes
or treat adapter text, summaries, RAG output, or Skills as scientific evidence.
