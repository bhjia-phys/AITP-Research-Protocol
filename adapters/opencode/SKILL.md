---
name: aitp-opencode-adapter
description: Reference for the bounded OpenCode AITP v5 Skill registration and lifecycle-plugin surfaces.
---

# AITP V5 For OpenCode

OpenCode has two separate integration assets:

1. `deploy/templates/opencode/aitp-plugin.js` registers the packaged Skill path
   with OpenCode discovery. It does not inject Skill bodies, `MEMORY.md`, legacy
   stage guidance, or research context into the system prompt.
2. The v5 host installer generates `.opencode/plugins/aitp-v5.js`, which owns
   `tool.execute.before` and `tool.execute.after` and delegates to the shared
   pre/post-tool runner.

The bootstrap therefore registers the packaged Skill path without becoming a
context or scientific-trust source. Bounded research context is compiled and
delivered through the v5 context lifecycle.

Connect the OpenCode MCP configuration to `brain/v5/native_mcp.py` and expose
the typed `aitp_v5_*` tools. When an exact session is already known, begin with
`aitp_v5_get_execution_brief`; when only a topic/workspace is known, begin with
`aitp_v5_build_workspace_recovery_audit`, then expand only the record families
needed by the active research question.

## Install And Audit

Connect OpenCode to `brain/v5/native_mcp.py`, then install the project-local
lifecycle plugin for an already bound AITP session:

```text
python -m brain.v5.cli --base <workspace> adapter install-hooks opencode <session-id> --plugin .opencode/plugins/aitp-v5.js
python -m brain.v5.cli --base <workspace> adapter install-audit opencode --plugin .opencode/plugins/aitp-v5.js
python -m brain.v5.cli --base <workspace> adapter host-readiness opencode --plugin .opencode/plugins/aitp-v5.js
```

If an old plugin injects a complete Skill, a complete memory body, or legacy
stage guidance, the audit returns a conflict. Replacement requires the exact
current-content-bound reviewed plan id; the installer never replaces such a
configuration automatically.

## Lifecycle Boundary

OpenCode automatically exposes only pre/post-tool events after installation. It
does not expose an owned SessionStart, prompt-submit, or session-end event in the
current v5 matrix. On the first relevant research turn, call
`begin_research_turn` for the existing session binding. At the end, call
`plan_session_closeout`; applying closeout remains separately reviewed.

Pre-tool handling may block through the typed policy decision. Post-tool
handling writes runtime trace or delegates one validated bounded research
moment. The plugin cannot update evidence or claim trust, rebind a topic, accept
a baseline, install a Skill, or apply closeout.

## Research Use

Use v5 autoroute/entry, exact expansion, recording, and closeout operations.
Treat plugin output, summaries, RAG, Skill instructions, and legacy L0-L4 files
as orientation rather than scientific evidence. A working `opencode` command is
not a readiness claim; the project-local plugin must also pass installation and
lifecycle audits.
