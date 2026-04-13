# Receipt: Phase 174 Formal Real-Topic Dialogue Proof

## Replay commands

```bash
python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "formal_real_topic_dialogue_acceptance_script_runs_on_isolated_work_root" -q
python research/knowledge-hub/runtime/scripts/run_formal_real_topic_dialogue_acceptance.py --json
```

## Observed results

- `pytest-formal-real-topic-dialogue.txt`: `1 passed, 77 deselected in 4.16s`
- `formal-real-topic-dialogue-acceptance.json`: `status = success`

## Key facts

- Fresh topic slug: `fresh-jones-finite-dimensional-factor-closure`
- Research mode: `formal_derivation`
- Interaction-state artifact present
- Research-question contract present
- Consultation ids include: `theorem:jones-ch4-finite-product`

## Raw artifacts

- `.planning/phases/174-formal-theory-real-topic-natural-language-dialogue-proof/evidence/pytest-formal-real-topic-dialogue.txt`
- `.planning/phases/174-formal-theory-real-topic-natural-language-dialogue-proof/evidence/formal-real-topic-dialogue-acceptance.json`
