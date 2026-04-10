# AITP v1.37-v1.42 Remediation Review Packet

Branch: `codex/aitp-v137-v142-remediation`

Baseline: `bd98af5`

## Completion Summary

- `M0` completed:
  - `research/knowledge-hub/knowledge_hub/aitp_service.py` reduced from the `bd98af5` baseline size to within the declared maintainability budget.
  - `research/knowledge-hub/knowledge_hub/aitp_cli.py` reduced to within the declared maintainability budget.
  - new helper and command-family modules are present, including extracted runtime/topic support modules and `cli_compat_handler.py`.
- `M1` to `M7` completed on this remediation branch by porting the verified local reference implementation into the clean `bd98af5` worktree, then closing remediation-only gaps:
  - collaborator/runtime/multi-topic surfaces
  - `L2` compiler/staging/hygiene surfaces
  - topic replay and promotion-gate support
  - formal-theory and code-method acceptance paths
  - `L5` publication protocol surface
  - real-topic acceptance scripts and onboarding/runtime docs

## Red-Line Checks

- not schema-only: production Python, runtime scripts, docs, schemas, and tests all changed
- not test-only: new/ported helper modules and runtime code are present and exercised
- not mock-only: three real-topic acceptance scripts passed
- no synthetic `examples/demo-topic` asset was reintroduced in this remediation worktree

## Verification Evidence

- `python -m pytest research/knowledge-hub/tests -q`
  - result: `248 passed, 10 subtests passed`
- `python -m unittest discover -s research/knowledge-hub/tests -v`
  - result: `OK`
- `python research/knowledge-hub/runtime/scripts/run_scrpa_thesis_topic_acceptance.py --json`
  - result: `success`
- `python research/knowledge-hub/runtime/scripts/run_witten_topological_phases_formal_closure_acceptance.py --json`
  - result: `success`
- `python research/knowledge-hub/runtime/scripts/run_tfim_benchmark_code_method_acceptance.py --json`
  - result: `success`

## Remediation-Specific Fixes Applied

- restored a controlling remediation matrix in:
  - `docs/superpowers/plans/2026-04-10-aitp-v137-v142-remediation.md`
- added backward-compatible CLI paths for:
  - `show-collaborator-memory`
  - `record-collaborator-memory --preference`
  - `stage-negative-result`
- restored human-readable CLI output while preserving `--json`
- repaired governance docs so legacy governance regressions and current runtime architecture text agree
- fixed light-profile `must_read_now` behavior so advisory control notes do not force extra reads
- restored `topic_next.may_defer_until_trigger`
- fixed acceptance collisions from date-only TFIM topic/run stamps
- bounded operation/theory-packet/lean-bridge path fragments to avoid Windows path-length failures in the remediation worktree

## Key Durable Artifacts

- remediation matrix:
  - `docs/superpowers/plans/2026-04-10-aitp-v137-v142-remediation.md`
- this review packet:
  - `docs/superpowers/plans/2026-04-10-aitp-v137-v142-remediation-review.md`
- maintainability budget contract:
  - `research/knowledge-hub/maintainability_budgets.json`
- real-topic acceptance entrypoints:
  - `research/knowledge-hub/runtime/scripts/run_scrpa_thesis_topic_acceptance.py`
  - `research/knowledge-hub/runtime/scripts/run_witten_topological_phases_formal_closure_acceptance.py`
  - `research/knowledge-hub/runtime/scripts/run_tfim_benchmark_code_method_acceptance.py`
