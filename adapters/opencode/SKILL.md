---
name: aitp-runtime
description: Reference note for the OpenCode adapter surface; the active OpenCode bootstrap now lives in `/.opencode/plugins/aitp.js` plus the repository `skills/` directory.
---

# OpenCode Adapter Reference

The public OpenCode path is now plugin-first:

1. install the plugin from `/.opencode/plugins/aitp.js` or follow `docs/INSTALL_OPENCODE.md`;
2. let the plugin inject `using-aitp` and register the repository `skills/` directory;
3. use `aitp session-start "<task>"` only as the manual fallback when plugin bootstrap is unavailable.
