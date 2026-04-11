# AITP test runbook

Use this runbook for the next honest AITP tests.

## 1. Platform gate

Check the host and chat surfaces first:

```bash
openclaw status
openclaw channels status --probe --json
systemctl --user status openclaw-gateway.service --no-pager
```

Pass condition:
- gateway running
- Feishu probe healthy
- intended agent/session visible

## 2. Kernel gate

Check that the kernel itself is healthy:

```bash
aitp doctor
aitp state --topic-slug <topic_slug>
aitp capability-audit --topic-slug <topic_slug>
```

Pass condition:
- CLI installed
- runtime state readable
- capability audit not obviously broken

## 3. Single-step loop smoke test

Run one bounded step only:

```bash
aitp loop \
  --topic-slug <topic_slug> \
  --updated-by manual-smoke \
  --max-auto-steps 1 \
  --json
```

Pass condition:
- `runtime/topics/<topic_slug>/loop_state.json` updates
- conformance remains truthful
- no fake scientific success is claimed

## 4. Heartbeat semantic test

The heartbeat policy should now prefer:

```bash
aitp loop --updated-by openclaw-heartbeat --max-auto-steps 1 --json
```

Test either by:
- waiting for the scheduled heartbeat,
- or manually sending the configured heartbeat prompt through the bound chat surface.

Pass condition:
- heartbeat follows `HEARTBEAT.md`
- if AITP is selected, it follows `HEARTBEAT_AITP.md`
- ack stays short and truthful

## 5. Feishu end-to-end test

From Feishu DM, ask for:
- a small runtime read
- one bounded execution step

Suggested checks:
- read `loop_state`
- run the generic OpenClaw plugin smoke script:
  - `research/adapters/openclaw/scripts/run_openclaw_plugin_smoke.sh`

Pass condition:
- transport works
- runtime state is readable
- bounded OpenClaw/AITP handoff is truthful

## 6. L2 backend bridge test: note-library backend

Pick one real note from a backend that you have already registered under
`canonical/backends/`.

For the public formal-theory example route, you can run:

```bash
research/knowledge-hub/runtime/scripts/run_formal_theory_backend_smoke.sh
```

That script creates one temporary external formal-theory note backend, realizes
the public example backend card against it, registers one note into `L0`, and
runs one bounded `aitp loop`.

Register it into `L0`:

```bash
python3 research/knowledge-hub/source-layer/scripts/register_local_note_source.py \
  --topic-slug <topic_slug> \
  --path "<absolute-note-path>" \
  --registered-by backend-bridge-smoke
```

Then run one bounded loop step that explicitly mentions the backend:

```bash
aitp loop \
  --topic-slug <topic_slug> \
  --human-request "Use the registered human-note backend as a bounded knowledge bridge, but keep all conclusions operator-visible." \
  --max-auto-steps 1 \
  --json
```

Pass condition:
- note is registered in `L0`
- runtime artifacts remain operator-visible
- no direct folder-level canonicalization happens

## 7. L2 backend bridge test: software backend

Do not start with heavy execution.
Start with docs/tests/method context.

Use a registered software backend card from `canonical/backends/`.

Goal:
- seed one `method`, `workflow`, or `validation_pattern` candidate from software knowledge
- keep reproducibility paths explicit

Pass condition:
- AITP can reference the backend coherently
- no black-box code claims
- paths to code/tests/results remain durable

For the public toy-model numeric starter route, you can run:

```bash
research/knowledge-hub/runtime/scripts/run_toy_model_numeric_backend_smoke.sh
```

That script creates one temporary external toy-model backend, runs a tiny
public TFIM exact-diagonalization helper on a fixed config, registers the
generated run note into `L0`, and runs one bounded `aitp loop`.

## 8. Exit gate

Close with:

```bash
aitp audit --topic-slug <topic_slug> --phase exit
```

The run only counts if exit conformance is still honest.

## 9. Real-topic acceptance: scRPA thesis lane

Use this when you want a real formal-theory topic acceptance that starts from
the master's-thesis scRPA material instead of a synthetic smoke payload.

```bash
python research/knowledge-hub/runtime/scripts/run_scrpa_thesis_topic_acceptance.py --json
```

Pass condition:
- the topic lands in the `formal_theory` lane
- the runtime stays in the `light` profile
- `topic_synopsis.json`, `pending_decisions.json`, and `promotion_readiness.json` are materialized
- the topic remains honest about still needing thesis-grounded source/candidate tightening before any stronger closure claim

## 10. Real-topic acceptance: Jones Chapter 4 finite-product lane

Use this when you want a real formal-theory acceptance pass on the active Jones
benchmark topic rather than on a disposable synthetic theorem card.

```bash
python research/knowledge-hub/runtime/scripts/run_jones_chapter4_finite_product_formal_closure_acceptance.py --json
```

Pass condition:
- the active `jones-von-neumann-algebras` topic gets a new bounded Chapter 4 candidate run
- `coverage_ledger.json`, `formal_theory_review.json`, `proof_obligations.json`, and `proof_state.json` are materialized for that candidate
- `topic_skill_projection.active.json|md` is materialized and surfaced through runtime status as a `formal_theory` projection
- the projection is human-promoted into `units/topic-skill-projections/`
- the Lean bridge packet is `ready`
- `promotion_gate.json` ends in `promoted` and the promoted unit lands in `L2_auto`
- the resulting packet stays honest about not yet proving the stronger algebra-level product theorem or the later whole-book routes

## 11. Real-topic acceptance: code-backed benchmark-first lane

Use this when you want a real code-backed topic acceptance that keeps a tiny
exact benchmark in front of broader workflow claims.

```bash
python research/knowledge-hub/runtime/scripts/run_tfim_benchmark_code_method_acceptance.py --json
```

Pass condition:
- the topic lands in the `code_method` lane
- the runtime stays in the `light` profile
- a coding operation manifest exists and passes the baseline-first trust audit
- run-local strategy memory is recorded and surfaced through runtime status

## 12. Isolated acceptance: L2 MVP direction

Use this when you want a bounded proof that the MVP `L2` memory surface is
operational without mutating repo runtime state.

```bash
python research/knowledge-hub/runtime/scripts/run_l2_mvp_direction_acceptance.py --json
```

Pass condition:
- the TFIM MVP direction is seeded through production CLI
- `consult-l2` returns the seeded `physical_picture`
- `compile-l2-map` writes `workspace_memory_map.json|md`
- `compile-l2-graph-report` writes `workspace_graph_report.json|md`
- `compile-l2-graph-report` writes `derived_navigation/index.md`
- `audit-l2-hygiene` writes `workspace_hygiene_report.json|md`
- the acceptance runs on an isolated temp kernel root

## 13. Isolated acceptance: source catalog and citation reuse

Use this when you want a bounded proof that the Layer 0 source-reuse surface is
operational without mutating repo runtime state.

```bash
python research/knowledge-hub/runtime/scripts/run_source_catalog_acceptance.py --json
```

Pass condition:
- `compile-source-catalog` writes `source_catalog.json|md`
- `trace-source-citations` writes one bounded traversal artifact
- `compile-source-family` writes one family reuse artifact
- `export-source-bibtex` writes one bounded `.bib` export artifact
- `import-bibtex-sources` writes one bounded Layer 0 import report and source row
- `status --json` surfaces source fidelity for the active topic
- the acceptance runs on an isolated temp kernel root

## 14. Isolated acceptance: analytical review and research judgment

## 13.5. Isolated acceptance: L1 method specificity

Use this when you want one bounded proof that source-backed method specificity
is visible through the real runtime status surface.

```bash
python research/knowledge-hub/runtime/scripts/run_l1_method_specificity_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `method_specificity_rows` inside `l1_source_intake`
- at least one `formal_derivation` or `numerical_benchmark` row appears
- `research_question.contract.md` includes a `## Method specificity` section
- the runtime protocol note also includes `## Method specificity`
- the acceptance runs on an isolated temp kernel root

## 14. Isolated acceptance: analytical review and research judgment

Use this when you want one bounded proof that analytical review and
research-judgment runtime surfaces are both live through production CLI.

```bash
python research/knowledge-hub/runtime/scripts/run_analytical_judgment_surface_acceptance.py --json
```

Pass condition:
- `analytical-review` writes a durable `analytical_review.json`
- `verify --mode analytical` makes `analytical_review` the primary review bundle surface
- `status --json` surfaces `research_judgment.active.json|md`
- runtime focus exposes `momentum`, `stuckness`, and `surprise`
- the acceptance runs on an isolated temp kernel root

## 15. Isolated acceptance: collaborator continuity

Use this when you want one bounded proof that collaborator continuity surfaces
are live through production CLI restart paths.

```bash
python research/knowledge-hub/runtime/scripts/run_collaborator_continuity_acceptance.py --json
```

Pass condition:
- `focus-topic` materializes current-topic compatibility state
- `status --json` surfaces `collaborator_profile.active.json|md`
- `status --json` surfaces `research_trajectory.active.json|md`
- `status --json` surfaces `mode_learning.active.json|md`
- `current-topic --json` exposes continuity summaries for all three surfaces
- `session-start --json` carries continuity note paths into session-start artifacts
- the acceptance runs on an isolated temp kernel root

## 16. Isolated acceptance: quick exploration

Use this when you want one bounded proof that lightweight exploration is a
first-class path and can promote into normal topic work explicitly.

```bash
python research/knowledge-hub/runtime/scripts/run_quick_exploration_acceptance.py --json
```

Pass condition:
- `explore --json` writes `runtime/explorations/<exploration_id>/explore_session.json|md`
- quick exploration reports a lighter artifact footprint than full topic bootstrap
- `promote-exploration --current-topic --json` writes `promotion_request.json|md`
- promotion materializes a bounded `session-start` contract for the target topic
- the acceptance runs on an isolated temp kernel root
