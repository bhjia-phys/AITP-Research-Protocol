# Mode Envelope Protocol

Domain: Interaction
Authority: subordinate to AITP SPEC S6.
Merges: AITP_MODE_ENVELOPE_PROTOCOL.md, AITP_TRANSITION_AND_BACKEDGE_PROTOCOL.md,
MODE_AND_LAYER_OPERATING_MODEL.md.

---

## ME1. Role

The mode envelope is the Brain's built-in research workflow engine. Each mode
represents a distinct cognitive activity in physics research. The mode determines
which layers the agent works in, what transitions are allowed, and what
writeback is required.

The three modes correspond to the core research cycle:
- **explore** — discover literature, find ideas, record observations
- **learn** — study deeply, verify known results through derivation/experiment
- **implement** — pursue new ideas, produce novel results

L2 promotion is NOT a separate mode. It is an operation triggered within
`learn` or `implement` when candidates pass validation.

## ME2. Three Modes

### explore

Purpose: Discover literature, find ideas, record observations.

| Property | Value |
|----------|-------|
| Foreground layers | L0, L1, L3 |
| L3 focus | L3-I (ideation) |
| Allowed backedges | None |
| Required writeback | Source registrations, L1 notes, L3-I idea records |
| Forbidden shortcuts | Formal candidates, L4 execution, L2 promotion |
| Human checkpoint | On scope change or direction ambiguity |
| Entry conditions | Default mode for new topics |
| Exit conditions | At least one idea recorded in L3-I |

### learn

Purpose: Deep study of specific literature, verification of known results.

| Property | Value |
|----------|-------|
| Foreground layers | L0, L1, L3, L4 |
| L3 focus | L3-P (planning), L3-A (analysis) |
| Allowed backedges | L4 -> L3-A (revision needed), L3-A -> L1 (need more source) |
| Required writeback | L3-P plans, L3-A candidates, L4 validation results |
| Forbidden shortcuts | L4 -> L2 (must return through L3-R) |
| Human checkpoint | On derivation approval, on numerical experiment plan |
| Entry conditions | At least one idea or source identified |
| Exit conditions | Known results verified or gap identified |

The L3↔L4 loop is the core mechanism: L3-P creates a derivation/reproduction
plan, L3-A executes it, L4 validates, results return through L3-R. Verified
knowledge can promote to L2.

### implement

Purpose: Pursue new ideas, produce novel results.

| Property | Value |
|----------|-------|
| Foreground layers | L3, L4 |
| L3 focus | L3-I -> L3-P -> L3-A (full pipeline) |
| Allowed backedges | L4 -> L3-A (revision), L3-A -> L3-P (replan), L3-P -> L3-I (idea refinement) |
| Required writeback | L3-I refined idea, L3-P plan, L3-A candidates with evidence |
| Forbidden shortcuts | L4 -> L2 (must return through L3-R) |
| Human checkpoint | On novel conclusion, on L2 promotion decision |
| Entry conditions | Concrete idea ready for execution |
| Exit conditions | Novel conclusion recorded in L3, or idea disproven |

The L3↔L4 loop drives discovery: L3-I ideas are upgraded to executable form,
L3-P plans the approach, L3-A executes, L4 validates. New conclusions stay in
L3 for human review before any L2 promotion.

## ME3. Submodes

Some modes have submodes that refine execution behavior:

### learn submodes

- `derivation` — focused analytical derivation and proof verification
- `numerical` — focused numerical reproduction and benchmark verification

### implement submodes

- `code` — implementing algorithms or computational methods
- `formal` — formalizing proofs or mathematical structures
- `experimental` — numerical experiments to test new hypotheses

Submodes do not change the mode's foreground layers or backedge rules. They
shape action type preferences and tool selection within the existing envelope.

## ME4. Context-Refocusing Engine

When the agent detects that the current mode selection context is stale or
the topic state has significantly changed since the last mode selection:

1. Compute a context-refocusing score based on:
   - elapsed actions since last mode selection,
   - changes to topic state (new sources, new candidates, completed validations),
   - control note changes,
   - research judgment signals (momentum, stuckness, surprise).

2. If the score exceeds the refocusing threshold, re-evaluate the mode from
   the full context rather than incrementally from the previous mode.

3. Record the refocusing decision in the decision trace.

The context-refocusing engine prevents mode selection from drifting away from
the actual topic state during long sessions.

## ME5. Transition Graph

```
explore -> learn -> implement -> explore
  ^          |          |
  |          v          v
  +----------+----------+
       (backward transitions)
```

Valid forward transitions:
- `explore -> learn` (idea discovered, ready to study deeply)
- `learn -> implement` (understanding sufficient, ready for new work)
- `implement -> explore` (results suggest new questions)

Valid backward transitions (require explicit reason and writeback):
- `learn -> explore` (need more source material or broader context)
- `implement -> learn` (implementation revealed knowledge gap)
- `implement -> explore` (results suggest different direction entirely)

Invalid transitions (never allowed):
- `explore -> implement` (must pass through learn first)
- Any transition without writeback from the departing mode

## ME6. Mode Envelope Fields

Every mode envelope contains:

```
mode: <mode_name>
foreground_layers: [L0, L1, ...]
L3_focus: [sub-plane(s)]
allowed_backedges: [(from, to, reason_required), ...]
required_writeback: [artifact_type, ...]
forbidden_shortcuts: [action_type, ...]
human_checkpoint_policy: <when human approval is required>
entry_conditions: [condition, ...]
exit_conditions: [condition, ...]
```

## ME7. Mode Inference

The Brain infers the current mode from:
- topic state (what has been accomplished),
- action type (what is being attempted),
- control note directives (if present),
- research mode profiles (learned patterns),
- runtime contract (`runtime_protocol.generated.json`).

When inference is ambiguous, the Brain defaults to `explore` mode for new
topics and `learn` mode for topics with established sources.

## ME8. Control Axes

The mode is one axis in the six-axis control plane:

| Axis | Role | Determined By |
|------|------|--------------|
| `runtime_mode` | Core driver | Mode envelope (explore/learn/implement) |
| `transition_posture` | Core driver | Current transition direction |
| `layer` | Where | Current action target |
| `L3_subplane` | L3 detail | ideation / planning / analysis / result / distillation |
| `lane` | Domain | formal_theory / model_numeric / code_and_materials |
| `task_type` | Intent | open_exploration / conjecture_attempt / target_driven |

Only `runtime_mode` and `transition_posture` are core behavioral drivers.

## ME9. Backedge Protocol

Backward transitions (backedges) are allowed but regulated:

1. The agent must state why the backward transition is needed.
2. The agent must produce writeback from the current mode before transitioning.
3. The transition is recorded in the decision trace.
4. Repeated backedges on the same action trigger stuckness detection.

## ME10. Implementation Status

### Currently implemented
- Three modes with foreground layer definitions.
- Submodes for learn and implement.
- Context-refocusing engine.
- Runtime contract mode-based action preferences.
- Research mode profiles feeding into mode selection.

### Not yet implemented
- Transition graph enforcement (preventing invalid transitions).
- Mode envelope validation at task materialization.
- L3-I and L3-P integration with mode dispatch.

## ME11. What Mode Envelopes Should Not Do

- Allow arbitrary mode jumps.
- Skip validation steps by mode manipulation.
- Treat mode transitions as a substitute for research progress.
- Keep the agent in a comfortable mode (explore) indefinitely.
- Allow mode transitions without writeback from the departing mode.
- Treat L2 promotion as a mode (it is an operation, not a research phase).
