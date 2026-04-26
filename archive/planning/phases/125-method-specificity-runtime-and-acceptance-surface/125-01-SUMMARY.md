# Phase 125 Summary

Status: implemented on `main`

## Goal

Expose source-backed method specificity through production L1, topic-shell,
runtime-bundle, and status paths.

## What Landed

- new `infer_method_specificity` detection in
  `research/knowledge-hub/knowledge_hub/source_intelligence.py`
- `method_specificity_rows` carried through L1 distillation, runtime payloads,
  markdown renderers, and schema contracts
- a new isolated acceptance script:
  `research/knowledge-hub/runtime/scripts/run_l1_method_specificity_acceptance.py`

## Outcome

Phase `125` is complete.
`v1.64` now has a production method-specificity surface.
