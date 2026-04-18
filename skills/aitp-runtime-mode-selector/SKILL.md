---
name: aitp-runtime-mode-selector
description: Select the runtime mode and active submode for a topic using semantic reasoning instead of keyword matching.
---

# AITP Runtime Mode Selector

## Environment gate

- This skill runs inside an AITP session after research mode and load profile have been classified.
- Load this skill when `aitp_run_topic_loop` or `aitp_resume_topic` is about to select the runtime mode.

## Classification task

### Runtime mode

Choose between three runtime modes:

| Mode | When to choose |
|------|---------------|
| `explore` | The topic is gathering information, surveying literature, or brainstorming. No bounded target yet; the goal is to map the landscape. |
| `learn` | The topic has a bounded question and is building understanding toward answering it. Reading papers, running initial calculations, constructing mental models. |
| `implement` | The topic has a clear plan and is executing: running calculations, writing derivations, producing artifacts, or conducting validation rounds. |

### Active submode

Choose between six submodes (only one active at a time):

| Submode | When to choose |
|---------|---------------|
| `derivation` | Active formal derivation work: proving theorems, expanding identities, closing proof obligations. |
| `numerical` | Active computation: running ab initio codes, solving lattice models, performing numerical analysis. |
| `literature` | Active literature intake: reading papers, extracting claims, building citation networks. |
| `code` | Active code development: writing scripts, fixing bugs, building tooling. |
| `formal` | Active formalization work: translating informal proofs to formal systems, checking type theory, Lean proofs. |
| `experimental` | Active experimental work: setting up and running physical or computational experiments. |

## Reasoning priority

1. **Topic state**: Check `topic_state.json` for the current phase. Early phases → `explore`. Middle → `learn`. Late with clear plan → `implement`.
2. **Research mode signal**: `formal_derivation` → likely `implement` with `derivation` or `formal` submode. `first_principles` → likely `implement` with `numerical` submode. `exploratory_general` → likely `explore` or `learn`.
3. **Human request**: What did the user just ask for? "Run the calculation" → `implement` + `numerical`. "Read this paper" → `learn` + `literature`. "I think the proof goes like this" → `implement` + `derivation`.
4. **Transition posture**: If the topic just entered a new phase (e.g., from intake to execution), upgrade the mode accordingly. The transition rules in `mode_envelope_data.json` provide deterministic guidance for allowed transitions.
5. **Default**: `explore` with no submode.

## Recording the classification

Record both mode and submode in one call each:

```
aitp_record_classification(
    topic_slug=<current topic>,
    classification_type="runtime_mode",
    value=<"explore" or "learn" or "implement">,
    rationale=<1-2 sentence explanation>,
    signals_used=<list of signals>,
    source="ai_reasoning"
)

aitp_record_classification(
    topic_slug=<current topic>,
    classification_type="active_submode",
    value=<submode string or "none">,
    rationale=<1-2 sentence explanation>,
    signals_used=<list of signals>,
    source="ai_reasoning"
)
```

## Hard rules

- Do not use keyword or substring matching on the human request.
- Mode transitions must respect the deterministic rules in `mode_envelope_support.py` (forbidden shortcuts, layer permissions). These are mechanical checks, not AI decisions.
- Record both mode and submode before the loop step executes.
- If the topic is still in an early phase with no clear direction, prefer `explore` with no submode.
