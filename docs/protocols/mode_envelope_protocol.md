# Mode Envelope Protocol

Domain: Interaction
Authority: subordinate to AITP SPEC S6.
Merges: AITP_MODE_ENVELOPE_PROTOCOL.md, AITP_TRANSITION_AND_BACKEDGE_PROTOCOL.md,
MODE_AND_LAYER_OPERATING_MODEL.md.

---

## ME1. Role

The mode envelope constrains what the agent may do at any given moment. Each
mode defines foreground layers, allowed transitions, required writeback,
forbidden shortcuts, and human checkpoint policy.

Mode transitions follow a directed graph, not arbitrary jumps.

## ME2. Four Modes

### discussion

Purpose: Literature survey, Q&A, source exploration.

| Property | Value |
|----------|-------|
| Foreground layers | L0, L1, L3 |
| Allowed backedges | None |
| Required writeback | Source registrations, L1 analysis |
| Forbidden shortcuts | Candidate claims, promotion, L4 execution |
| Human checkpoint | On scope change or direction ambiguity |
| Entry conditions | Default mode for new topics |
| Exit conditions | Research question scoped, sources registered |

### explore

Purpose: Active research, hypothesis formation, candidate creation.

| Property | Value |
|----------|-------|
| Foreground layers | L0, L1, L2, L3 |
| Allowed backedges | L3-A -> L1 (need more source analysis) |
| Required writeback | Candidate claims with evidence levels |
| Forbidden shortcuts | Promotion, L4 execution without plan |
| Human checkpoint | On contradiction detection, on scope expansion |
| Entry conditions | Research question scoped, at least one source registered |
| Exit conditions | At least one candidate formed or gap identified |

### verify

Purpose: Validation and checking of candidates.

| Property | Value |
|----------|-------|
| Foreground layers | L2, L3, L4 |
| Allowed backedges | L4 -> L3-A (revision needed), L3-R -> L3-A (reformulation) |
| Required writeback | Trust audit, validation results, gap records |
| Forbidden shortcuts | L4 -> L2 (must return through L3-R) |
| Human checkpoint | On execution plan approval, on stuckness |
| Entry conditions | At least one candidate in L3 |
| Exit conditions | Validation complete (pass or fail), result routed |

### promote

Purpose: L2 promotion pipeline.

| Property | Value |
|----------|-------|
| Foreground layers | L2, L3 |
| Allowed backedges | L3-D -> L3-A (revision needed) |
| Required writeback | Promotion trace, L2 unit writes |
| Forbidden shortcuts | Skipping promotion stages |
| Human checkpoint | Always at stage 4 (L2 write) |
| Entry conditions | Candidate passed validation |
| Exit conditions | Promotion complete or candidate rejected |

## ME3. Submodes

Some modes have submodes that refine the execution behavior within the mode:

### verify submodes

- `iterative_verify` — cyclic validation where each pass refines the candidate
  based on previous validation results. Used when analytical and numerical
  validation must iterate to convergence.

### explore submodes

- `literature` — focused literature survey mode within explore. Prioritizes L0/L1
  operations and source discovery over candidate creation.

Submodes do not change the mode's foreground layers or backedge rules. They
shape action type preferences within the existing envelope.

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
discussion -> explore -> verify -> promote -> discussion
     ^           |          |          |
     |           v          v          v
     +-----------+----------+----------+
              (backward transitions)
```

Valid forward transitions:
- `discussion -> explore`
- `explore -> verify`
- `verify -> promote`
- `promote -> discussion`

Valid backward transitions (require explicit reason and writeback):
- `explore -> discussion` (need more source work)
- `verify -> explore` (candidate needs revision)
- `promote -> verify` (candidate needs more validation)

Invalid transitions (never allowed):
- `discussion -> verify` (skip candidate formation)
- `discussion -> promote` (skip both candidate formation and validation)
- `explore -> promote` (skip validation)
- `verify -> discussion` (should go through explore first)

## ME6. Mode Envelope Fields

Every mode envelope contains:

```
mode: <mode_name>
foreground_layers: [L0, L1, ...]
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

When inference is ambiguous, the Brain defaults to `explore` mode, which is
the most broadly applicable mode for active research. The most conservative
option (`discussion`) is the default for brand-new topics only.

## ME8. Control Axes

The mode is one axis in the six-axis control plane:

| Axis | Role | Determined By |
|------|------|--------------|
| `runtime_mode` | Core driver | Mode envelope |
| `transition_posture` | Core driver | Current transition direction |
| `layer` | Where | Current action target |
| `L3_subplane` | L3 detail | L3-A / L3-R / L3-D |
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
- Four modes with foreground layer definitions.
- Submodes (iterative_verify, literature).
- Context-refocusing engine.
- Runtime contract mode-based action preferences.
- Research mode profiles feeding into mode selection.

### Not yet implemented
- Transition graph enforcement (preventing invalid transitions).
- Mode envelope validation at task materialization.

## ME11. What Mode Envelopes Should Not Do

- Allow arbitrary mode jumps.
- Skip validation steps by mode manipulation.
- Treat mode transitions as a substitute for research progress.
- Keep the agent in a comfortable mode (discussion) indefinitely.
- Allow mode transitions without writeback from the departing mode.
