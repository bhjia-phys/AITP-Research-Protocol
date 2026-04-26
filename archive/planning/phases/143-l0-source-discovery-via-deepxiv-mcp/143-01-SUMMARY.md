# Phase 143 Summary

Status: implemented in working tree

## Goal

Add the missing bounded `L0` search -> evaluate -> register bridge so operators
can start from a natural-language query without widening `L0` into a general
literature-automation layer.

## What Landed

- `source-layer/scripts/discover_and_register.py`
  - thin provider-aware bridge with explicit fallback chain
  - durable discovery receipts under `source-layer/topics/<topic_slug>/discoveries/`
  - bounded candidate evaluation before registration
  - canonical registration routed back through `register_arxiv_source.py`
- `source-layer/scripts/register_arxiv_source.py`
  - reusable registration function
  - explicit `metadata_json` / override support so isolated acceptance can stay offline and still use the same registration path
- `runtime/scripts/run_l0_source_discovery_acceptance.py`
  - isolated acceptance for the new discovery lane
- documentation updates across `L0_SOURCE_LAYER.md`, `source-layer/README.md`,
  `README.md`, `runtime/README.md`, and `runtime/AITP_TEST_RUNBOOK.md`
- test coverage in:
  - `tests/test_source_discovery_contracts.py`
  - `tests/test_runtime_scripts.py`

## Outcome

Phase `143` now closes the missing pre-registration entry lane for `L0` while
keeping the architectural boundary explicit:

- search remains an external provider dependency
- evaluation remains durable and inspectable
- registration still uses the existing Layer 0 source-of-truth path
