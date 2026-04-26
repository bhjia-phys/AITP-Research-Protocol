# Install Codex Adapter

> **Status:** Codex adapter assets exist in `adapters/` and `deploy/templates/`,
> but Codex is not yet integrated into the `aitp-pm.py` one-click installer.
> For now, use manual setup below.

## Manual setup

Codex uses AITP through native skill discovery.

Copy the AITP skills into Codex's skill directories:

**Linux/macOS:**
```bash
cp -r deploy/templates/claude-code/using-aitp.md ~/.agents/skills/using-aitp/SKILL.md
cp -r deploy/templates/claude-code/aitp-runtime.md ~/.agents/skills/aitp-runtime/SKILL.md
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills\using-aitp"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills\aitp-runtime"
Copy-Item deploy\templates\claude-code\using-aitp.md "$env:USERPROFILE\.agents\skills\using-aitp\SKILL.md"
Copy-Item deploy\templates\claude-code\aitp-runtime.md "$env:USERPROFILE\.agents\skills\aitp-runtime\SKILL.md"
```

Also register the AITP MCP server in your Codex MCP configuration.

## Verify

Check that skills are discoverable:
```bash
ls ~/.agents/skills/using-aitp/
ls ~/.agents/skills/aitp-runtime/
```

## Remove

See [UNINSTALL.md](UNINSTALL.md).
