# AITP v1.37-v1.42 Remediation Matrix

Baseline: `bd98af5` (`feat(v1.36): Phase 42-46 - source intelligence, intake, exploration carrier, Windows fix`)

Execution rule for this remediation branch:

- Treat this matrix as the controlling preflight artifact for `codex/aitp-v137-v142-remediation`.
- Status meanings:
  - `missing`: not present in a milestone-closing form on top of `bd98af5`
  - `partial`: some surface exists, but the milestone gate is not honestly met
  - `present`: implemented and usable on the verified local reference branch
- The user asked to keep pushing forward, so this matrix is agent-drafted from repo truth plus the verified local reference implementation in the sibling workspace.

## Matrix

| Milestone | Scope | Status on `bd98af5` | Target for remediation |
| --- | --- | --- | --- |
| Preflight | Human/audit control artifact for `v1.37`-`v1.42` redo | missing | created here as the controlling matrix |
| M0 | Service/CLI hotspot extraction and line-budget closure | missing | port verified helper extraction set, then finish topic lifecycle/status + CLI family extraction |
| M1 / v1.37a | research loop, `L3` decomposition, `L4 -> L0/L1/L3` backedges, negative-result durability, human-readable runtime surfaces | partial | align with verified local reference implementation and keep non-mocked runtime proofs |
| M2 / v1.37b | source fidelity, reading depth, degraded mode, first analytical validation family | partial | align with verified local reference implementation and real-topic acceptance |
| M3 / v1.38 | `L2` knowledge growth, retrieval, compilation, staging behavior | partial | align with verified local reference implementation and L2 regression suite |
| M4 / v1.39 | collaborator memory, research judgment, mode learning | partial | align with verified local reference implementation and runtime-state durability |
| M5 / v1.40 | exploration routing, multi-route runtime, human-facing surfaces, template library | partial | align with verified local reference implementation and route-selection/runtime tests |
| M6 / v1.41 | paired backend maturity, theory synthesis, lifecycle verification | partial | align with verified local reference implementation and lifecycle-verification tests |
| M7 / v1.42 | reliability, onboarding, `L5`, E2E closure, real-topic-backed examples | partial | align with verified local reference implementation, then replace synthetic example assets with real-topic-backed coverage where required |

## Evidence Used

- `bd98af5` worktree baseline:
  - `research/knowledge-hub/knowledge_hub/aitp_service.py`: 14889 lines
  - `research/knowledge-hub/knowledge_hub/aitp_cli.py`: 1259 lines
  - `python -m pytest research/knowledge-hub/tests/test_aitp_cli.py -q` -> `27 passed`
- Verified local reference workspace:
  - `python -m unittest discover -s research/knowledge-hub/tests -v` -> `229 tests`, `OK`
  - helper extraction set present under `research/knowledge-hub/knowledge_hub/`

## Review Packet Template

Each milestone closeout on this remediation branch must record:

1. changed production paths
2. changed tests
3. commands run
4. durable artifacts created
5. why the milestone is not schema-only, not test-only, and not mock-only
