# AITP for Codex

Codex already has native skill discovery. AITP uses that directly.

## Quick install

First install the public runtime:

```bash
python -m pip install aitp-kernel
aitp install-agent --agent codex --scope user
```

If you want the repo-backed contributor path instead, tell Codex:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/bhjia-phys/AITP-Research-Protocol/main/.codex/INSTALL.md
```

## How it works

- Codex discovers `skills/using-aitp/SKILL.md` through `~/.agents/skills/aitp`.
- `using-aitp` acts as the gatekeeper for topic continuation, paper learning, derivation planning, steering updates, and validation work.
- Once AITP claims the task, Codex follows `aitp-runtime` and the runtime bundle.

The point is not to make the user memorize wrapper commands. The point is to
make Codex enter the research protocol before it starts answering like a chat
assistant.

## User experience target

The user should just speak naturally. They should not need to learn `aitp-codex`, wrappers, or command bundles.

Manual fallback remains:

```bash
aitp session-start "<task>"
```

For the shared install verification and first-run proof, use:

- [`INSTALL.md`](INSTALL.md)
- [`QUICKSTART.md`](QUICKSTART.md)
