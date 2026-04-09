# AITP Kernel

This folder contains the installable public AITP kernel.

It is the repo-local source-of-truth behind:

- `aitp`
- `aitp-mcp`
- the repository `skills/` bootstrap surfaces
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
```

For a Windows-native smoke test from a fresh clone, the repo-local launchers do
not require WSL or a copied global `aitp` shim:

```cmd
scripts\aitp-local.cmd doctor
```

The public runtime defaults to the repo-local kernel root:

- `research/knowledge-hub`

So a normal standalone clone does not need the original private integration
workspace just to run `aitp`.
On Windows, the local launchers inject `research\knowledge-hub` onto
`PYTHONPATH`, so the repo can run natively even before you choose a permanent
Python install layout.

`aitp doctor` should also report the fixed layer roots and key contract files so
you can verify that the standalone install is structurally complete.
That protocol report now includes the deeper proof/gap/fusion/verification
governance surfaces in addition to the layer map and routing basics.
Topic-completion and regression-governed promotion are part of that public
surface rather than topic-local convention.

## Core Commands

```bash
aitp bootstrap --topic "<topic>" --statement "<statement>"
aitp session-start "<task>"
aitp resume --topic-slug <topic_slug> --human-request "<task>"
aitp loop --topic-slug <topic_slug> --human-request "<task>" --skill-query "<capability gap>"
aitp current-topic
aitp audit --topic-slug <topic_slug> --phase exit
aitp ci-check --topic-slug <topic_slug>
aitp baseline --topic-slug <topic_slug> --run-id <run_id> --title "<baseline title>" --reference "<source>" --agreement-criterion "<criterion>"
aitp atomize --topic-slug <topic_slug> --run-id <run_id> --method-title "<method title>"
aitp operation-init --topic-slug <topic_slug> --run-id <run_id> --title "<operation>" --kind numerical
aitp operation-update --topic-slug <topic_slug> --run-id <run_id> --operation "<operation>" --baseline-status passed
aitp trust-audit --topic-slug <topic_slug> --run-id <run_id>
aitp capability-audit --topic-slug <topic_slug>
aitp coverage-audit --topic-slug <topic_slug> --candidate-id <candidate_id> --source-section <section> --covered-section <section>
aitp formal-theory-audit --topic-slug <topic_slug> --candidate-id <candidate_id> --formal-theory-role trusted_target --statement-graph-role target_statement
aitp request-promotion --topic-slug <topic_slug> --candidate-id <candidate_id>
aitp approve-promotion --topic-slug <topic_slug> --candidate-id <candidate_id>
aitp promote --topic-slug <topic_slug> --candidate-id <candidate_id> --target-backend-root <tpkn_root>
aitp auto-promote --topic-slug <topic_slug> --candidate-id <candidate_id> --target-backend-root <tpkn_root>
aitp install-agent --agent all --scope user
```

`aitp session-start "<task>"` still writes a durable startup contract under
`runtime/topics/<topic_slug>/session_start.contract.json` plus the human-readable
`session_start.generated.md`, but outer agent UX should treat that as internal
routing state. The first user-facing runtime checklist remains
`runtime_protocol.generated.md`.

## Fixed Layout

```text
research/knowledge-hub/
  LAYER_MAP.md
  ROUTING_POLICY.md
  COMMUNICATION_CONTRACT.md
  AUTONOMY_AND_OPERATOR_MODEL.md
  L2_CONSULTATION_PROTOCOL.md
  RESEARCH_EXECUTION_GUARDRAILS.md
  PROOF_OBLIGATION_PROTOCOL.md
  GAP_RECOVERY_PROTOCOL.md
  FAMILY_FUSION_PROTOCOL.md
  VERIFICATION_BRIDGE_PROTOCOL.md
  SEMI_FORMAL_THEORY_PROTOCOL.md
  FORMAL_THEORY_AUTOMATION_WORKFLOW.md
  SECTION_FORMALIZATION_PROTOCOL.md
  FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md
  TOPIC_COMPLETION_PROTOCOL.md
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
- `L2`: long-term reusable knowledge and execution projections
- `L3`: exploratory conclusions and candidate reusable material
- `L4`: planning, execution, validation, and adjudication

The current filesystem keeps the `validation/` directory name for continuity,
but the public `L4` role is broader than a narrow pass/fail checker.

Cross-layer protocol surfaces:

- `consultation/`
- `runtime/`
- `schemas/`

`L2_CONSULTATION_PROTOCOL.md` now includes the human-facing versus AI-facing
consultation output contract, so consultation remains operator-usable without
becoming a second promotion path.

Runtime-facing control notes:

- `runtime/PROGRESSIVE_DISCLOSURE_PROTOCOL.md`

Deeper governance contracts surfaced through `aitp doctor`:

- `RESEARCH_EXECUTION_GUARDRAILS.md`
- `PROOF_OBLIGATION_PROTOCOL.md`
- `GAP_RECOVERY_PROTOCOL.md`
- `FAMILY_FUSION_PROTOCOL.md`
- `VERIFICATION_BRIDGE_PROTOCOL.md`
- `SEMI_FORMAL_THEORY_PROTOCOL.md`
- `FORMAL_THEORY_AUTOMATION_WORKFLOW.md`
- `SECTION_FORMALIZATION_PROTOCOL.md`
- `FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md`
- `TOPIC_COMPLETION_PROTOCOL.md`

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
It should also surface the global research-flow guardrails that ban proxy
success signals and require explicit research contracts for non-trivial work.
External runtimes should consume its trigger semantics from the JSON bundle and
its schema contract rather than scraping markdown prose.

The layer contracts above remain the higher-priority governance surface.
External backends such as a separate formal-theory knowledge network, a
software repository, or a result store should enter through the documented
`L2` backend bridge rather than through hidden path assumptions.
When proof-grade theory work is active, deeper protocol slices should expose
proof obligations, unresolved-gap routing, multi-source family fusion, the
semi-formal trust boundary, and the selected verification bridge explicitly
instead of collapsing them into one opaque prompt.

The current runtime shell now also materializes:

- `runtime/topics/<topic_slug>/topic_completion.json|md`
- `runtime/topics/<topic_slug>/lean_bridge.active.json|md`
- `runtime/topics/<child_topic_slug>/followup_return_packet.json|md`
- `runtime/topics/<topic_slug>/followup_reintegration.jsonl|md`
- `runtime/topics/<topic_slug>/followup_gap_writeback.jsonl|md`

and Lean-ready exports now carry local `proof_obligations.json` and
`proof_state.json` artifacts for each candidate packet.

Layer 2 now has two governed writeback paths:

1. Human-reviewed `L2`:
   - `aitp request-promotion ...`
   - human `aitp approve-promotion ...` or `aitp reject-promotion ...`
   - `aitp promote ...`
2. Theory-formal `L2_auto`:
   - `aitp coverage-audit ...`
   - `aitp formal-theory-audit ...`
   - `aitp auto-promote ...`

For theory-formal `L2_auto`, coverage and consensus are necessary but not
sufficient.
Auto-promotion should also remain blocked until the candidate has a ready
`formal_theory_review.json` plus regression-backed, blocker-clear,
split/gap-honest, semi-formal theory packets.

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
python research/knowledge-hub/runtime/scripts/run_witten_topological_phases_formal_closure_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_jones_chapter4_finite_product_formal_closure_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_scrpa_thesis_topic_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_tfim_benchmark_code_method_acceptance.py --json
```

The Witten acceptance script is the bounded real-topic closure check for the
current semi-formal theory runtime lane: it seeds a real Lecture Two theorem
candidate, runs coverage + formal-theory review, dispatches the reviewed
controller actions for `topic_completion` and `lean_bridge`, and then validates
`L2_auto` writeback into a disposable TPKN copy while keeping Lean export as a
downstream bridge rather than the primary meaning of `L2` success.

The Jones Chapter 4 acceptance script is the bounded formal-theory acceptance
for the current Jones benchmark topic: it reuses the active
`jones-von-neumann-algebras` topic, seeds a new Chapter 4 finite-dimensional
finite-product candidate around the compile-checked theorem packet, runs
coverage + formal-theory review, records theorem-facing strategy memory,
compiles a formal-theory `topic_skill_projection`, human-promotes that
projection into `units/topic-skill-projections/`, dispatches the reviewed
controller actions for `topic_completion`, `lean_bridge`, and
`auto_promote_candidate`, and verifies that both the projection and the theorem
packet stay honest about still missing the stronger algebra-level product
theorem and the later whole-book routes.

The scRPA thesis acceptance script is a real-topic shell acceptance for the
formal-theory lane: it opens a topic from the master's-thesis scRPA chapter,
introduction, abstract, and conclusion, verifies that the topic lands in the
formal-theory lane, stays in the light runtime profile, materializes the new
projection surfaces, and keeps the first honest next step at the thesis-to-L0
source-recovery boundary instead of pretending numerical closure already
exists.

The TFIM code-method acceptance script is the bounded code-backed benchmark
lane: it runs the public exact-diagonalization helper on the tiny TFIM config,
opens a `code_method` topic around that workflow, records a baseline-gated
coding operation plus strategy memory, compiles a `topic_skill_projection`, and
verifies that operation trust and runtime surfaces stay inside AITP instead of
turning into an untracked coding side quest.

That same public TFIM lane is now the first seeded internal `L2` direction.
The seed makes `canonical/index.jsonl` and `canonical/edges.jsonl` non-empty
and gives AITP a bounded reusable graph containing the benchmark substrate,
benchmark-first validation concept, exact-diagonalization method, workflow,
validation pattern, warning note, bridge, claim card, and route capsule.

Use:

- `aitp seed-l2-demo`
- `aitp consult-l2 --query "TFIM exact diagonalization benchmark workflow"`
- `aitp stage-l2-insight --title "..." --summary "..."`
- `aitp stage-topic-distillation --topic-slug "<topic>"`
- `aitp consult-l2 --topic-slug "<topic>" --query "..." --include-staging`

The lightweight staging path is the low-friction intake surface for reusable
insight candidates discovered during discussion, reading, or early route
exploration. It records provisional memory under `canonical/staging/` without
pretending that the entry is already canonical `L2`.

`stage-topic-distillation` is the first topic-driven memory-growth bridge for
`v1.29`: it reads the active topic's `L3-D`-adjacent candidate and evidence
surfaces, then stages provisional reusable memory without hand-authoring
canonical unit JSON.

`L0` now surfaces source-fidelity classes in the runtime projection so the
system can distinguish peer-reviewed, preprint, thesis, formal-reference,
informal, and code-artifact evidence instead of treating all sources as
equivalent.

`L0` also surfaces first citation-graph signals such as arXiv ids,
BibTeX/DOI-like metadata, and whether a source row already carries explicit
references. This is still only a baseline signal, not a full literature graph.

`aitp verify --mode analytic` is the first bounded physics-grade analytic
validation preset. It does not replace derivations or numerics; it forces the
runtime contract to ask for limiting-case, dimensional, symmetry, and
self-consistency checks explicitly.

`aitp stage-negative-result` is the first explicit failed-route retention path.
It records a provisional `negative_result` staging entry with failure kind,
failed route, and next implication so abandoned directions do not silently
disappear.

`record-collaborator-memory` and `show-collaborator-memory` are the first
explicit collaborator-memory surfaces. They are stored outside canonical `L2`
so personal preferences and long-horizon concerns do not get confused with
scientific truth.

Staging is therefore not just a scratch inbox.
It is the first step of a wiki-like compilation loop:

- capture a reusable insight candidate,
- link it to existing units,
- mark contradictions or warning posture explicitly,
- summarize what new knowledge was added,
- and only later promote it into canonical `L2` if review and validation
  justify that step.

`topic_skill_projection` is reusable execution memory. When the lane is
`formal_theory`, that means the projection tells the next agent what theorem-
facing artifacts to read and what bounded route is safe to reuse; it is not a
theorem certificate and it does not stand in for proof closure.

## AITP And GSD

This repository may be developed with `GSD`, but active research topics still
belong to `AITP`.

Use `GSD` when the job is changing this repository itself: runtime code, docs,
tests, adapters, packaging, and acceptance scripts.

Use `AITP` when the job is advancing a topic, even when that topic includes
code, benchmarks, or method validation.

The explicit coexistence rule is documented here:

- `../docs/AITP_GSD_WORKFLOW_CONTRACT.md`
