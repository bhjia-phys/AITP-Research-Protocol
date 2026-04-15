# Progressive Disclosure Protocol

This file defines the runtime-facing progressive-disclosure rule for AITP.

The goal is not to hide complexity.
The goal is to expose complexity in the order an agent actually needs it while
preserving every hard governance constraint.

The public machine-readable contract for
`topics/<topic_slug>/runtime/runtime_protocol.generated.json` lives at:

- `runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`

## 1. Core rule

AITP runtime artifacts may defer detail, but they may not weaken or hide:

- layer semantics,
- active research-contract guardrails,
- consultation obligations,
- trust and baseline gates,
- promotion gates,
- conformance requirements,
- declared control notes or decision contracts.

This is **lossless progressive disclosure**.

## 2. Four execution tiers

Every AI-facing runtime surface should be understandable as four tiers:

1. `minimal_execution_brief`
   - what stage the agent is in,
   - what bounded action is currently selected,
   - what work is immediately allowed,
   - what work is immediately blocked,
   - which files must be opened now.
2. `trigger_rules`
   - which named situations require deeper protocol reads,
   - which files become mandatory when each trigger fires.
3. `protocol_slice`
   - the smallest deeper subset relevant to the current trigger,
   - for example consultation, promotion, capability, or queue-contract surfaces.
4. `full_governance`
   - the complete contract surface for disputes, audits, or edge cases.

## 3. Mandatory top-level fields

The top disclosure tier must always include:

- current stage,
- selected action or declared absence of one,
- immediate allowed work,
- immediate blocked work,
- visible research-flow guardrails when the work is non-trivial,
- active hard constraints,
- declared escalation triggers,
- exact deeper file paths.

If these are missing, the summary is too compressed to count as safe AITP
runtime guidance.

## 4. Canonical trigger names

Use stable trigger names when possible:

- `decision_override_present`
- `promotion_intent`
- `non_trivial_consultation`
- `capability_gap_blocker`
- `trust_missing`
- `contradiction_detected`

Projects may add more triggers, but should not rename these casually once they
are emitted in runtime artifacts.

The public runtime bundle may also expose stable deeper-slice triggers when the
relevant durable artifacts exist, for example:

- `proof_completion_review`
- `verification_route_selection`

## 5. Trigger expectations

### `decision_override_present`

Fire when a control note or decision contract overrides heuristic queue
selection.

Mandatory deeper reads:

- decision contract or control note,
- next-action decision artifact,
- generated queue contract when present.

### `promotion_intent`

Fire when the current work could create, revise, approve, or execute an `L2` or
`L2_auto` writeback.

Mandatory deeper reads:

- `promotion_gate.json` or `promotion_gate.md`,
- coverage or consensus artifacts when theory-formal,
- the selected validation or delivery surface.

### `non_trivial_consultation`

Fire when `L2` consultation materially changes terminology, candidate shape,
validation route, contradiction handling, or writeback intent.

Mandatory deeper reads:

- `L2_CONSULTATION_PROTOCOL.md`,
- topic consultation index,
- relevant consultation request/result/application artifacts.

This trigger is about consultation lookup and application only.
It does not authorize writeback.
If consultation output later supports `L2` or `L2_auto` writeback,
`promotion_intent` must also fire and its gate surfaces remain mandatory.

### `capability_gap_blocker`

Fire when missing workflows or missing backends block honest continuation.

Mandatory deeper reads:

- capability protocol,
- skill discovery artifacts,
- operator-visible queue or follow-up task surfaces.

### `trust_missing`

Fire when an operation or method is being reused without a satisfied trust gate.

Mandatory deeper reads:

- trust audit outputs,
- baseline or atomic-understanding artifacts,
- operation manifests when present.

### `contradiction_detected`

Fire when source alignment, family fusion, or validation surfaces expose an
unresolved contradiction.

Mandatory deeper reads:

- validation decision artifacts,
- conflict or contradiction records,
- relevant family or source-fusion surfaces,
- `GAP_RECOVERY_PROTOCOL.md`,
- `FAMILY_FUSION_PROTOCOL.md`.

### `proof_completion_review`

Fire when the current bounded work is proof-heavy or derivation-heavy and the
topic already has theory-packet artifacts for the active candidate.

Mandatory deeper reads:

- theory-packet `structure_map.json`,
- theory-packet `coverage_ledger.json`,
- theory-packet `notation_table.json`,
- theory-packet `derivation_graph.json`,
- theory-packet `agent_consensus.json`,
- `PROOF_OBLIGATION_PROTOCOL.md`.

### `verification_route_selection`

Fire when the current bounded work is selecting or materializing the closed-loop
validation route for execution.

Mandatory deeper reads:

- `selected_validation_route.json`,
- `execution_task.json`,
- returned execution result when present,
- `VERIFICATION_BRIDGE_PROTOCOL.md`.

## 6. JSON and markdown expectations

- `runtime_protocol.generated.md` is the operator-facing continuation surface.
- Markdown is the human authority for operator-facing continuation, review, and
  ordered read guidance.
- `runtime_protocol.generated.json` stays semantically aligned with the
  Markdown render.
- JSON remains the machine-facing companion and stable schema contract for
  executors, handlers, and replay tooling.
- The generated JSON surface should carry
  `$schema=https://aitp.local/schemas/progressive-disclosure-runtime-bundle.schema.json`
  and `bundle_kind=progressive_disclosure_runtime_bundle`.
- Markdown may reorder and summarize for readability.
- Markdown must still point to every deeper mandatory read by exact path.
- A deferred section must name the trigger that would make it mandatory.

## 7. Script boundary

Scripts may:

- materialize the top-level brief,
- compute declared trigger state from durable artifacts,
- generate projections and indexes.

Scripts may not decide:

- whether a proof is genuinely complete,
- whether two theorem families are truly identical,
- whether a gap is substantively resolved,
- whether proxy evidence is good enough to count as validation,
- whether a candidate is scientifically mature merely because it was generated.

Those judgments remain protocol-governed research work, constrained by
regression, consultation, validation, and review surfaces.
