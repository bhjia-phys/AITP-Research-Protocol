---
name: aitp-runtime
description: Compatibility note for manually connecting OpenClaw to AITP v5; no dedicated OpenClaw lifecycle installer is release-supported.
---

# AITP V5 For OpenClaw

OpenClaw is not a default AITP research host and currently has no dedicated v5
lifecycle installer or verified automatic hook path. A manual integration may
connect only to:

- MCP entrypoint: `brain/v5/native_mcp.py`
- typed tools: `aitp_v5_*`

Such an integration must use bounded v5 recovery/context reads and explicit
typed writes. It must not enable legacy L0-L4 writes, auto-promote trust, install
Skills, or claim host lifecycle support that has not passed a host fixture.

Use Codex for the supported default interactive workflow.
