# Architecture

## Core stance

AITP is organized as:

1. a research charter,
2. a protocol object layer,
3. a runtime and audit surface,
4. agent adapters.

The charter is the highest public authority.
The runtime is not allowed to replace the charter with hidden heuristics.

## Four-layer research structure

The current operational research view is still L0-L4.

### L0 — Source substrate

Use L0 to register and reopen:

- papers and PDFs,
- URLs,
- transcripts,
- conversations,
- local notes,
- source snapshots.

### L1 — Intake and provisional understanding

Use L1 for:

- source-bound notes,
- provisional claims,
- extraction fragments,
- source-local ambiguity,
- intake maps.

### L2 — Canonical reusable knowledge

L2 stores reusable research objects such as:

- concepts,
- claim cards,
- derivation objects,
- methods,
- workflows,
- warnings,
- validation patterns,
- bridge notes.

L2 is the active memory surface of the system.

### L3 — Exploratory research and candidate formation

Use L3 for:

- conjectures,
- failed attempts,
- candidate derivations,
- anomalies,
- negative results,
- run-local interpretations,
- next research actions.

### L4 — Validation and adjudication

Use L4 for:

- validation plans,
- contradiction checks,
- benchmark or reproduction results,
- execution tasks,
- promotion, revise, reject, or defer decisions.

L4 is not just "execution". It is the surface that decides whether a candidate
survives explicit checking.

## Routing logic

The default non-trivial route is:

`L0 -> L1 -> L3 -> L4 -> L2`

The low-risk exception is:

`L0 -> L1 -> L2`

The runtime may not silently skip candidate formation or validation when the
protocol says they are required.

## Protocol object layer

The research layers are stabilized by explicit contracts:

- research question contracts;
- candidate claim contracts;
- derivation contracts;
- validation contracts;
- operation contracts;
- promotion or rejection contracts.

These contracts are the public interface between agents and the research state.

For non-trivial topics, the public contracts should also carry enough
research-flow structure to resist scope drift and fake completion:

- context intake,
- formalism and notation lock,
- observables,
- target claims,
- deliverables,
- acceptance tests,
- forbidden proxies,
- uncertainty markers.

AITP should borrow that discipline from stronger workflow systems without
collapsing the layer model into generic project phases.

## Runtime boundary

The runtime is intentionally narrow.

It may:

- materialize state,
- build protocol projections,
- run conformance, trust, or capability audits,
- execute explicit tool handlers.

It should not:

- invent the research workflow in hidden code,
- silently upgrade a claim,
- silently weaken research contracts into prose-only summaries,
- substitute proxy-success signals for declared validation evidence,
- replace missing contracts with unrestricted heuristics.

## Agent adapters

OpenClaw, Codex, Claude Code, and OpenCode should all be treated as protocol
executors.

They do not define AITP.
They load AITP, act through AITP, and leave auditable AITP artifacts behind.
