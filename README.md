# AITP Research Memory

AITP is a lightweight, local-first research memory for theoretical physics. It keeps readable Markdown records beside the research itself. There is no database, vector index, MCP server, mandatory hook, migration layer, or hidden service.

## Install the Codex plugin

From the shell:

```bash
codex plugin marketplace add /home/bhjia/physics/repo/AITP-Research-Memory
codex plugin add aitp-research-memory@aitp-memory
```

Start a new Codex CLI session. In the Codex input box:

```text
$aitp
$aitp initialize this blank research repository
$aitp record the durable result from this conversation
$aitp write a theory note from the existing records
```

Use `/skills` to inspect the installed Skills. `$aitp` is the explicit Skill entrypoint; `/aitp` is not a Codex slash command.

## Research workflow

```text
aitp init
    Initialize one blank repository as one research Topic.

aitp enter
    Recover source-linked recorded state, unresolved failures, and next action.

aitp record prepare/save
    Record an observation, result, failure, decision, source, code change,
    reproducible run, or closeout through its CLI template.

aitp note prepare/save
    Write a working Note or theory Note from pinned research evidence.
```

For ad hoc reading, Codex uses the filesystem and `rg`; there is no `aitp search`.

## Develop the standalone CLI

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pytest -q
```

The Python package and Codex plugin expose the same memory contracts.
