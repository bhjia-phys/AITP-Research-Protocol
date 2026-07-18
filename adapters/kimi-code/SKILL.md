---
name: aitp-runtime
description: Compatibility pointer for the Kimi Code AITP v5 adapter and project-local hook installer.
---

# AITP V5 For Kimi Code

Kimi Code can install the user-level `plugins/aitp-research-protocol-kimi/`
package for MCP launch, first-run configuration, and packaged Skill discovery.
Lifecycle hooks remain a separate project concern: `.kimi/config.toml` or
`.kimi-code/config.toml` owns the generated `SessionStart`, `PreToolUse`, and
`PostToolUse` commands backed by `hooks/aitp_v5_kimi_hook.py`.

Installing the plugin does not prove that project hooks are installed. If a
workspace already declares the same AITP MCP server or Skills manually, avoid
double registration and choose one MCP/Skill bootstrap path; audit lifecycle
hooks independently.

SessionStart prepares bounded workspace orientation. Pre/post-tool events use
the shared policy and trace/research-moment paths. Kimi Code has no owned
prompt-submit or session-end event in the current matrix, so closeout remains an
explicit `plan_session_closeout` operation.

Use typed v5 reads and writes at durable research moments. Hook output cannot
update claim trust, promote memory, accept a baseline, install a Skill, or turn
legacy L0-L4 stage files into the active lifecycle. Verify both the `kimi`
process and the workspace hook installation before reporting readiness.
