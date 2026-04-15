# Installing AITP for Codex

Enable AITP in Codex through native skill discovery. Install once, then let
natural-language theory work route through the gatekeeper skill.

## Prerequisites

- Git
- Codex CLI

## Installation

1. Install the public runtime:

   ```bash
   python -m pip install aitp-kernel
   aitp --version
   ```

2. Install the Codex skills:

   ```bash
   aitp install-agent --agent codex --scope user
   ```

   Windows-friendly equivalent:

   ```cmd
   scripts\aitp-local.cmd install-agent --agent codex --scope user
   ```

3. Restart Codex.

This is the current plugin-first-equivalent Codex path.

## Repo-backed contributor path

If you want repo-synced skills while changing this repository, use a local
checkout:

1. Clone the repository:

   ```bash
   git clone https://github.com/bhjia-phys/AITP-Research-Protocol.git ~/.codex/aitp
   ```

   Windows (PowerShell):

   ```powershell
   git clone https://github.com/bhjia-phys/AITP-Research-Protocol.git "$env:USERPROFILE\.codex\aitp"
   ```

2. Install the editable runtime CLI:

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

   Windows-friendly no-junction alternative:

   ```cmd
   scripts\aitp-local.cmd install-agent --agent codex --scope user
   ```

   This copies `using-aitp` and `aitp-runtime` into `%USERPROFILE%\.agents\skills`
   instead of relying on a junction. Rerun it after updates if you use this path.

4. Restart Codex.

Before you trust the install, verify it:

```bash
aitp doctor
aitp doctor --json
```

The Codex row should be `ready` in `runtime_support_matrix.runtimes.codex`.

## Verify

Ask for a theory task in natural language, for example:

- `继续这个 topic，方向改成 modular bootstrap`
- `开一个新 topic：Topological phases from modular data，先做问题定义和验证路线`

Codex should load `using-aitp` automatically and route the task into AITP before substantial work.

For ordinary topic work, AITP should stay in a light runtime profile unless a
benchmark mismatch, scope change, promotion step, or explicit full check forces
the runtime to expand.

When AITP says a human choice is required, inspect the active surface with:

```bash
aitp interaction --topic-slug <topic_slug> --json
```

If the active surface is a formal decision point, resolve it with:

```bash
aitp resolve-decision --topic-slug <topic_slug> --decision-id <decision_id> --option <index> --comment "<why>"
aitp resolve-checkpoint --topic-slug <topic_slug> --option <index> --comment "<why>"
```

This is the normal user path. `aitp session-start "<task>"` is only the manual
fallback when native bootstrap is unavailable.

After the Codex row is `ready`, use the shared first-run guide:

- [`../docs/QUICKSTART.md`](../docs/QUICKSTART.md)

## Manual fallback

If bootstrap does not fire, use:

```bash
aitp session-start "<task>"
```

## Updating

Public package path:

```bash
python -m pip install --upgrade aitp-kernel
aitp install-agent --agent codex --scope user
```

Repo-backed contributor path:

```bash
cd ~/.codex/aitp && git pull
python -m pip install -e ~/.codex/aitp/research/knowledge-hub
```

Windows (PowerShell):

```powershell
Set-Location "$env:USERPROFILE\.codex\aitp"
git pull
python -m pip install -e "$env:USERPROFILE\.codex\aitp\research\knowledge-hub"
```

## Uninstalling

```bash
rm ~/.agents/skills/aitp
```

Windows (PowerShell):

```powershell
Remove-Item "$env:USERPROFILE\.agents\skills\aitp" -Recurse -Force
```

If you also want to remove the editable runtime install or any compatibility
assets, follow [`../docs/UNINSTALL.md`](../docs/UNINSTALL.md).
