# Phase 92 Summary

Status: implemented on `main`

## Goal

Normalize runtime-root serialization for active-topics/current-topic state while
keeping scheduler and compatibility projections backward-compatible.

## What Landed

- new helper module:
  `research/knowledge-hub/knowledge_hub/runtime_path_support.py`
- `aitp_service.py` now writes repo-relative `runtime_root` values for
  `current_topic` and `active_topics`
- scheduler loading and current-topic projection remain compatible with older
  absolute-path rows

## Outcome

Phase `92` is complete.
`v1.53` now has runtime path normalization in production code.
