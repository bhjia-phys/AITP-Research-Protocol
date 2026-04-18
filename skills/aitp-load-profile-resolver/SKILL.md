---
name: aitp-load-profile-resolver
description: Determine whether a topic should use the full or light runtime load profile, using semantic reasoning instead of regex matching.
---

# AITP Load Profile Resolver

## Environment gate

- This skill runs inside an AITP session, typically at session-start or resume.
- Research mode should already be classified before this skill is invoked.

## Classification task

Choose between two load profiles:

| Profile | When to choose |
|---------|---------------|
| `full` | The topic requires deep runtime infrastructure: full action queue materialization, detailed trust audits, promotion candidates, multi-step validation loops, or subtopic decomposition. Typical for `formal_derivation` and `first_principles` topics with bounded research questions. |
| `light` | The topic is exploratory, early-stage, or does not yet have a well-bounded question. The runtime stays minimal: topic state, operator console, research question contract, control note. No full queue materialization or trust audit scaffolding. |

## Reasoning priority

1. **Explicit request**: If the user said "full profile", "deep dive", "full runtime", or explicitly requested comprehensive infrastructure, choose `full`.
2. **Research mode signal**: `formal_derivation` and `first_principles` topics with bounded questions usually need `full`. `exploratory_general` and early `toy_model` topics often work with `light`.
3. **Question boundedness**: Is the research question well-scoped with clear target claims and a validation route? Yes → `full`. No or still being scoped → `light`.
4. **Topic maturity**: A topic that has already produced multiple action rounds or has L2 promotion candidates should use `full`.
5. **Default**: Choose `light`. Upgrading later is cheap; running `full` prematurely wastes resources.

## Recording the classification

After reasoning, call the MCP tool:

```
aitp_record_classification(
    topic_slug=<current topic>,
    classification_type="load_profile",
    value=<"full" or "light">,
    rationale=<1-2 sentence explanation>,
    signals_used=<list of signals>,
    source="ai_reasoning"
)
```

## Hard rules

- Do not use regex matching or keyword scanning on the human request text.
- The profile can be upgraded from `light` to `full` at any point; record a new classification when this happens.
- Never downgrade from `full` to `light` within the same session without explicit user direction.
