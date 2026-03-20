# AITP Kernel

This folder contains the installable public AITP kernel.

It is the repo-local source-of-truth behind:

- `aitp`
- `aitp-mcp`
- `aitp-codex`
- the fixed `L0-L4` protocol surfaces shipped in this repository

The repository remains protocol-first, but a fresh clone is now both readable
and runnable.
The fixed directories are public governance surfaces.
The scientific content inside them is expected to remain user-extensible so one
clone can emphasize formal theory while another emphasizes toy-model numerics or
code-backed method development.

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

`aitp doctor` should also report the fixed layer roots and key contract files so
you can verify that the standalone install is structurally complete.
That protocol report now includes the deeper proof/gap/fusion/verification
governance surfaces in addition to the layer map and routing basics.

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
aitp coverage-audit --topic-slug <topic_slug> --candidate-id <candidate_id> --source-section <section> --covered-section <section>
aitp request-promotion --topic-slug <topic_slug> --candidate-id <candidate_id>
aitp approve-promotion --topic-slug <topic_slug> --candidate-id <candidate_id>
aitp promote --topic-slug <topic_slug> --candidate-id <candidate_id> --target-backend-root <tpkn_root>
aitp auto-promote --topic-slug <topic_slug> --candidate-id <candidate_id> --target-backend-root <tpkn_root>
aitp install-agent --agent all --scope user
```

## Fixed Layout

```text
research/knowledge-hub/
  LAYER_MAP.md
  ROUTING_POLICY.md
  COMMUNICATION_CONTRACT.md
  AUTONOMY_AND_OPERATOR_MODEL.md
  L2_CONSULTATION_PROTOCOL.md
  PROOF_OBLIGATION_PROTOCOL.md
  GAP_RECOVERY_PROTOCOL.md
  FAMILY_FUSION_PROTOCOL.md
  VERIFICATION_BRIDGE_PROTOCOL.md
  INDEXING_RULES.md
  L0_SOURCE_LAYER.md
  setup.py
  requirements.txt
  schemas/
  knowledge_hub/
  source-layer/
  intake/
  canonical/
  feedback/
  consultation/
  runtime/
  validation/
  tests/
```

Formal roots:

- `L0` -> `source-layer/`
- `L1` -> `intake/`
- `L2` -> `canonical/`
- `L3` -> `feedback/`
- `L4` -> `validation/`

Public layer semantics:

- `L0`: source entry, survey, and acquisition
- `L1`: analysis and provisional understanding
- `L2`: long-term reusable knowledge
- `L3`: exploratory conclusions and candidate reusable material
- `L4`: planning, execution, validation, and adjudication

The current filesystem keeps the `validation/` directory name for continuity,
but the public `L4` role is broader than a narrow pass/fail checker.

Cross-layer protocol surfaces:

- `consultation/`
- `runtime/`
- `schemas/`

Runtime-facing control notes:

- `runtime/PROGRESSIVE_DISCLOSURE_PROTOCOL.md`

Deeper governance contracts surfaced through `aitp doctor`:

- `PROOF_OBLIGATION_PROTOCOL.md`
- `GAP_RECOVERY_PROTOCOL.md`
- `FAMILY_FUSION_PROTOCOL.md`
- `VERIFICATION_BRIDGE_PROTOCOL.md`

## Runtime Rule

AITP should not hide research control logic inside Python when a durable
contract file is sufficient.

AITP does not require one fixed Python implementation or one fixed agent
workflow. Scripts, handlers, prompts, and execution strategy may evolve, but
the contract surface must stay stable: layer semantics, runtime artifacts,
candidate and review objects, evidence traces, and backend writeback rules.

- Python remains responsible for state materialization, audits, and explicit handler execution.
- Agents may adapt execution strategy freely inside that boundary as long as the resulting artifacts remain protocol-compatible and auditable.
- Research routing, layer delivery, and queue overrides should prefer durable protocol artifacts.
- Each bootstrap or loop materializes:
  - `runtime/topics/<topic_slug>/runtime_protocol.generated.json`
  - `runtime/topics/<topic_slug>/runtime_protocol.generated.md`
  - optional `runtime/topics/<topic_slug>/promotion_gate.json`
  - optional `runtime/topics/<topic_slug>/promotion_gate.md`
  - schema contract: `runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`

Agents should read that runtime bundle before acting on heuristic queue rows.
That runtime bundle should follow the lossless progressive-disclosure rule in
`runtime/PROGRESSIVE_DISCLOSURE_PROTOCOL.md`: show the minimum sufficient
execution contract first, defer deeper details until declared triggers fire,
and never hide hard constraints.
External runtimes should consume its trigger semantics from the JSON bundle and
its schema contract rather than scraping markdown prose.

The layer contracts above remain the higher-priority governance surface.
External backends such as a separate formal-theory knowledge network, a
software repository, or a result store should enter through the documented
`L2` backend bridge rather than through hidden path assumptions.
When proof-grade theory work is active, deeper protocol slices should expose
proof obligations, unresolved-gap routing, multi-source family fusion, and the
selected verification bridge explicitly instead of collapsing them into one
opaque prompt.

Layer 2 now has two governed writeback paths:

1. Human-reviewed `L2`:
   - `aitp request-promotion ...`
   - human `aitp approve-promotion ...` or `aitp reject-promotion ...`
   - `aitp promote ...`
2. Theory-formal `L2_auto`:
   - `aitp coverage-audit ...`
   - `aitp auto-promote ...`

The current public external writeback path targets the standalone
`Theoretical-Physics-Knowledge-Network` repository through the backend card:

- `canonical/backends/theoretical-physics-knowledge-network.json`

## Validation

Run the bundled tests:

```bash
python -m unittest discover -s research/knowledge-hub/tests -v
```

Public bounded smoke tests:

```bash
research/knowledge-hub/runtime/scripts/run_formal_theory_backend_smoke.sh
research/knowledge-hub/runtime/scripts/run_tpkn_formal_promotion_smoke.sh
research/knowledge-hub/runtime/scripts/run_tpkn_formal_auto_promotion_smoke.sh
```
