# Human Interaction Protocol

Domain: Interaction (H-Plane)
Authority: subordinate to AITP SPEC S5.
Merges: COMMUNICATION_CONTRACT.md, CLARIFICATION_PROTOCOL.md,
DECISION_POINT_PROTOCOL.md, runtime/CONTROL_NOTE_CONTRACT.md,
runtime/INNOVATION_DIRECTION_TEMPLATE.md.

---

## H1. Role

The Human plane provides structured interaction points where the human
researcher steers, approves, corrects, or pauses the system at any layer.

Human guidance is not a protocol failure (Charter Article 8). The system is
designed for genuine human-AI research collaboration.

## H2. Interaction Types

### Checkpoint
- The system pauses for human review.
- The human may inspect state, modify artifacts, or approve continuation.
- Checkpoints are triggered by: mode transitions, L4 execution plans,
  promotion decisions, stuckness escalation.

### Steering
- The human changes research direction, scope, or assumptions.
- Delivered through: control notes, innovation direction updates,
  operator console edits.
- The system treats steering as a first-class input, not an anomaly.

### Approval
- The human approves an action that the system cannot auto-execute.
- Required for: L2 promotion (always), L4 execution plans (when not
  pre-approved), high-impact decisions.

### Override
- The human overrides a system recommendation.
- For example: acknowledging stuckness and choosing to continue,
  rejecting an auto-advance, or forcing a mode transition.
- Override is recorded in the decision trace.

### Clarification
- The system requests clarification when the research question is vague.
- Currently implemented as a one-shot model: the system either produces
  `needs_clarification` or `approved_for_execution`.
- Multi-round clarification (up to 3 rounds) is a future enhancement.

## H3. Communication Contract

### Agent-to-Human
The system communicates with the human through:
- **Operator console** — immediate execution contract (do now / do not / escalate).
- **Topic dashboard** — current state at a glance.
- **Popup gates** — blocking questions that require a choice.
- **Session chronicle** — narrative summary at session end.

### Human-to-Agent
The human communicates through:
- **Natural language** — the primary interface.
- **Control notes** — structured direction changes.
- **Innovation direction** — scope and novelty updates.
- **Artifact edits** — direct edits to L0-L4 or runtime artifacts.
- **Popup responses** — choices on blocking questions.

### Principle
All communication should be in plain language. Protocol jargon should not be
exposed to the human unless the human explicitly requests technical detail.

## H4. Decision Points

When the system needs human input, it creates a decision point:

| Field | Purpose |
|-------|---------|
| `decision_id` | Stable identifier |
| `trigger_rule` | What created this decision |
| `phase` | Current research phase |
| `question` | What needs to be answered |
| `options` | Possible choices with descriptions |
| `blocking` | Whether other work is blocked |
| `status` | unresolved / resolved / expired |

### Trigger Rules

Trigger rules use an open vocabulary. The following are recommended tags that
the system uses by convention:

| Trigger | When |
|---------|------|
| `direction_ambiguity` | Research direction is unclear |
| `validation_route_selection` | Multiple validation paths exist |
| `promotion_gate` | Candidate ready for L2 promotion |
| `execution_plan_approval` | L4 execution plan needs approval |
| `stuckness_escalation` | System is stuck and needs human input |
| `scope_change` | Research scope needs adjustment |
| `contradiction_resolution` | Contradiction needs human judgment |
| `capability_gap` | Missing capability blocks progress |
| `clarification_request` | Research question is underspecified |
| `followup_return` | Child topic has results to reintegrate |
| `novelty_direction_choice` | Human must choose novelty level |
| `checkpoint_resolution` | Operator checkpoint needs resolution |

Custom trigger rules may be added by adapters or control notes as long as
they are descriptive and recorded in the decision trace.

### Popup Gate Protocol

At the start of every topic interaction:
1. Check for active popups.
2. If active, STOP all other work and present to human.
3. Human chooses an option.
4. System resolves the popup and records the choice.
5. Only after resolution may work continue.

Popup handling is platform-specific:
- Claude Code: AskUserQuestion tool with structured options.
- OpenCode: question tool or numbered Markdown list.
- Other: natural-language text with numbered options.

## H5. Control Note Contract

A control note is a human-authored directive that overrides heuristic routing.

Fields:
- `directive` — what the human wants (redirect, pause, scope change, etc.).
  Currently enforced.
- `summary` — brief description of the directive. Currently parsed.
- `rationale` — why (optional but encouraged). Not yet enforced.
- `scope` — which topic(s) the note applies to. Not yet enforced.
- `created_at` — timestamp. Not yet enforced.

Control notes are stored at:
`runtime/topics/<topic_slug>/runtime/control_note.md`

When a control note is present, the Brain loads it before selecting the next
action. Control notes take priority over heuristic routing.

## H6. Innovation Direction Template

The human may update the innovation direction at any time. Recommended fields:

- `novelty_level`: incremental / moderate / breakthrough,
- `scope`: expansion / maintenance / contraction,
- `acceptance_criteria`: updated validation standards,
- `forbidden_directions`: what NOT to pursue.

The template provides guidance but fields are not strictly enforced.
Adapters and implementations may use these fields as hints for routing
decisions.

Innovation direction is stored at:
`runtime/topics/<topic_slug>/runtime/innovation_direction.md`

## H7. Layer-Transition Checkpoints

The system should ask the human only when the answer materially changes:
- the layer jump,
- the execution lane,
- the trust boundary,
- the cost or resource profile.

Ordinary bounded work continues automatically. Meaningful transitions may
ask one bounded route-changing question. Those questions become durable
checkpoint artifacts, not chat-only interruptions.

## H8. Human Edit Rights

The human may edit any layer at any time:
- L0: add or remove sources,
- L1: refine source-bound understanding,
- L2: correct or refine reusable memory,
- L3: reshape questions, conjectures, and next actions,
- L4: tighten adjudication criteria,
- Runtime: clarify operator-facing intent.

All edits are treated as first-class inputs. The system should detect changes
and incorporate them into the next routing cycle.

## H9. Implementation Status

### Currently implemented
- Decision points with open-vocabulary trigger rules.
- Control note parsing (directive and summary fields).
- Operator console rendering.
- Topic dashboard rendering.
- Session chronicle generation.
- Popup gate detection and payload building (in aitp_service.py).

### Not yet implemented
- Popup gate handling in H-plane handlers (checkpoint handler, h_plane_support).
- Control note validation of rationale/scope/created_at fields.
- Innovation direction template field enforcement.
- Clarification round limit enforcement (multi-round model).
- Human edit detection and automatic re-routing.
- Popup gate at the start of every topic interaction (see B6).

## H10. What H Should Not Do

- Replace protocol discipline with human authority alone.
- Allow human edits to bypass validation without recording the override.
- Present all decisions as equally urgent (triage matters).
- Expose protocol jargon unnecessarily.
- Treat human silence as implicit approval.
