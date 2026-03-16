# AITP Repository Memory

This repository is the public home of the AITP research charter, protocol,
reference adapters, and the minimal installable runtime.

Key paths:

- `docs/` for charter and public design docs
- `contracts/` and `schemas/` for protocol objects
- `adapters/` for reference agent-facing assets
- `research/knowledge-hub/` for the installable `aitp` runtime package
- `research/adapters/openclaw/` for runtime-side OpenClaw adapter assets

Operator rule:

- Treat this repository as protocol-first.
- Python may materialize state, run audits, and execute explicit handlers.
- Research judgment should remain visible in durable artifacts rather than hidden heuristics.
