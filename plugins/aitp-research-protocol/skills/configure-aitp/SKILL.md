---
name: configure-aitp
description: "First-run setup assistant for the AITP Research Protocol Codex plugin: detect setup mode, ask for repo/topics paths, persist configuration, and explain when to restart Codex."
---

# Configure AITP Plugin

Use this skill when the AITP plugin is newly installed, when AITP tools are missing, or when the user asks to configure AITP.

## Setup Flow

1. Call `aitp_config_status()` if available.
2. If `configured=true`, report the resolved `repo_root` and `topics_root`.
3. If `configured=false`, ask the user for:
   - the local `AITP-Research-Protocol` checkout path,
   - the topics root where AITP should store records.
4. If the user does not have a checkout, offer to clone `https://github.com/bhjia-phys/AITP-Research-Protocol.git` into a directory they choose.
5. If the user has no preference for topics root, use `~/.aitp/topics`.
6. Call `aitp_configure(repo_root=<repo path>, topics_root=<topics path or empty>)`.
7. After success, tell the user to restart the MCP server or open a new Codex thread so full `aitp_v5_*` tools load.

## User Prompt Shape

Ask plainly:

```text
Where is your local AITP-Research-Protocol checkout, and where should AITP store topic records?
```

If the user gives only a repo path, configure `topics_root` as empty so the launcher uses `~/.aitp/topics`.

## Rules

- Do not manually edit AITP topic-state files.
- Do not continue to research operations while only setup tools are exposed.
- Do not assume the user's topics root is this machine's `F:/AI_Workspace/...`.
- Prefer the user's existing project store if they already have one.
