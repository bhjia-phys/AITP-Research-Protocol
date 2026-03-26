# Install Codex Adapter

Codex should use AITP through native skill discovery, not through wrappers.

## Prerequisites

- Git
- Codex CLI
- Python 3.10+

## Install the AITP runtime

From the repository root:

```bash
python -m pip install -e research/knowledge-hub
aitp doctor
```

## Preferred install

Follow the repository-native instructions in [`.codex/INSTALL.md`](../.codex/INSTALL.md).

The public Codex path is:

1. clone the repo;
2. expose `skills/` through `~/.agents/skills/aitp`;
3. restart Codex.

That gives Codex the same outer shape as Superpowers: skill discovery first,
then `using-aitp` decides whether the session must enter AITP.

## Compatibility install

If you want workspace-local copied skills instead of a symlink:

```bash
aitp install-agent --agent codex --scope project --target-root /path/to/theory-workspace
```

This now writes only:

- `.agents/skills/using-aitp/`
- `.agents/skills/aitp-runtime/`
- `.agents/skills/aitp-runtime/AITP_MCP_SETUP.md`

It no longer writes `aitp-codex` or workspace wrapper binaries by default.

## Verify

Codex should now be able to:

- auto-trigger `using-aitp` for natural-language theory requests;
- treat `继续这个 topic` as current-topic continuation before asking for a slug;
- translate steering language into durable AITP steering updates;
- follow `runtime_protocol.generated.md` after routing succeeds.

## Manual fallback

If bootstrap does not fire, use:

```bash
aitp session-start "<task>"
```

## Remove

See [`docs/UNINSTALL.md`](UNINSTALL.md).
