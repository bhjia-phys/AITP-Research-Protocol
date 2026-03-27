# Installing AITP for Codex

Enable AITP in Codex through native skill discovery. Clone once, then symlink the skills directory.

## Prerequisites

- Git
- Codex CLI

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/bhjia-phys/AITP-Research-Protocol.git ~/.codex/aitp
   ```

2. Install the runtime CLI:

   ```bash
   python -m pip install -e ~/.codex/aitp/research/knowledge-hub
   ```

3. Create the skills symlink:

   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/aitp/skills ~/.agents/skills/aitp
   ```

   Windows (PowerShell):

   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
   cmd /c mklink /J "$env:USERPROFILE\.agents\skills\aitp" "$env:USERPROFILE\.codex\aitp\skills"
   ```

4. Restart Codex.

## Verify

Ask for a theory task in natural language, for example:

- `继续这个 topic，方向改成 modular bootstrap`
- `开一个新 topic：Topological phases from modular data，先做问题定义和验证路线`

Codex should load `using-aitp` automatically and route the task into AITP before substantial work.

This is the normal user path. `aitp session-start "<task>"` is only the manual
fallback when native bootstrap is unavailable.

## Manual fallback

If bootstrap does not fire, use:

```bash
aitp session-start "<task>"
```

## Updating

```bash
cd ~/.codex/aitp && git pull
python -m pip install -e ~/.codex/aitp/research/knowledge-hub
```

## Uninstalling

```bash
rm ~/.agents/skills/aitp
```

If you also want to remove the editable runtime install or any compatibility
assets, follow [`../docs/UNINSTALL.md`](../docs/UNINSTALL.md).
