# RUNBOOK: Phase 174 Formal Real-Topic Dialogue Proof

## Purpose

Replay the formal-theory real natural-language dialogue proof on an isolated
work root.

## Commands

From repo root:

```bash
python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "formal_real_topic_dialogue_acceptance_script_runs_on_isolated_work_root" -q
python research/knowledge-hub/runtime/scripts/run_formal_real_topic_dialogue_acceptance.py --json
```

## Expected success markers

- topic slug: `fresh-jones-finite-dimensional-factor-closure`
- `interaction_state.json` exists on the fresh topic runtime root
- `research_question.contract.json` exists on the fresh topic runtime root
- canonical theorem mirror exists for `theorem:jones-ch4-finite-product`
- `consult-l2` still surfaces `theorem:jones-ch4-finite-product`

## Current success boundary

This phase proves steering fidelity for the already-closed bounded formal lane.
It does not claim that the whole formal-theory domain is solved through
dialogue.
