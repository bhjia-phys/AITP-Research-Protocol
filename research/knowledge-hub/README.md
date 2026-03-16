# AITP Runtime Package

This folder contains the minimal installable runtime for the public AITP
repository.

It is the runtime layer behind:

- `aitp`
- `aitp-mcp`
- `aitp-codex`

The repository remains protocol-first, but this package now makes a fresh clone
actually runnable.

## Quick Start

From the repository root:

```bash
python -m pip install -e research/knowledge-hub
aitp doctor
aitp --help
aitp-codex --help
```

The public runtime defaults to the repo-local kernel root:

- `research/knowledge-hub`

So a normal standalone clone does not need the original private integration
workspace just to run `aitp`.

## Core Commands

```bash
aitp bootstrap --topic "<topic>" --statement "<statement>"
aitp resume --topic-slug <topic_slug> --human-request "<task>"
aitp loop --topic-slug <topic_slug> --human-request "<task>" --skill-query "<capability gap>"
aitp-codex --topic-slug <topic_slug> "<task>"
aitp audit --topic-slug <topic_slug> --phase exit
aitp ci-check --topic-slug <topic_slug>
aitp baseline --topic-slug <topic_slug> --run-id <run_id> --title "<baseline title>" --reference "<source>" --agreement-criterion "<criterion>"
aitp atomize --topic-slug <topic_slug> --run-id <run_id> --method-title "<method title>"
aitp operation-init --topic-slug <topic_slug> --run-id <run_id> --title "<operation>" --kind numerical
aitp operation-update --topic-slug <topic_slug> --run-id <run_id> --operation "<operation>" --baseline-status passed
aitp trust-audit --topic-slug <topic_slug> --run-id <run_id>
aitp capability-audit --topic-slug <topic_slug>
aitp install-agent --agent all --scope user
```

## Package Layout

```text
research/knowledge-hub/
  setup.py
  requirements.txt
  knowledge_hub/
    aitp_cli.py
    aitp_codex.py
    aitp_mcp_server.py
    aitp_service.py
  runtime/
  source-layer/
  consultation/
  validation/
  tests/
```

## Runtime Rule

AITP should not hide research control logic inside Python when a durable
contract file is sufficient.

- Python remains responsible for state materialization, audits, and explicit handler execution.
- Research routing, layer delivery, and queue overrides should prefer durable protocol artifacts.
- Each bootstrap or loop materializes:
  - `runtime/topics/<topic_slug>/runtime_protocol.generated.json`
  - `runtime/topics/<topic_slug>/runtime_protocol.generated.md`

Agents should read that runtime bundle before acting on heuristic queue rows.

## Validation

Run the bundled tests:

```bash
python -m unittest discover -s research/knowledge-hub/tests -v
```
